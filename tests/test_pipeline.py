"""Tests for Pipeline orchestrator and CLI."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.workflow.pipeline import (
    ConstraintResult,
    ConstraintScope,
    ConstraintViolation,
    Pipeline,
    PipelineResult,
    _check_constraints,
    _discover_packs,
)

ROOT = Path(__file__).resolve().parent.parent
INSTANCE_DIR = ROOT / "doc-loop-vibe-coding"


# ── Pipeline construction ────────────────────────────────────────────────


class TestPipelineConstruction:
    """Pipeline can be created from explicit dirs or auto-discovered."""

    def test_from_explicit_dirs(self):
        p = Pipeline(
            pack_dirs=[str(INSTANCE_DIR)],
            project_root=str(ROOT),
            dry_run=True,
        )
        assert p.pack_context is not None
        assert p.rule_config is not None

    def test_from_project_auto_discover(self):
        p = Pipeline.from_project(ROOT, dry_run=True)
        assert p.pack_context is not None
        # Should discover at least the official instance pack
        names = [m.name for m in p.pack_context.manifests]
        assert "doc-loop-vibe-coding" in names

    def test_info_returns_pack_details(self):
        p = Pipeline(
            pack_dirs=[str(INSTANCE_DIR)],
            project_root=str(ROOT),
            dry_run=True,
        )
        info = p.info()
        assert "packs" in info
        assert len(info["packs"]) >= 1
        assert info["packs"][0]["name"] == "doc-loop-vibe-coding"
        assert "merged_intents" in info
        assert "merged_gates" in info

    def test_pack_context_property(self):
        p = Pipeline.from_project(ROOT, dry_run=True)
        ctx = p.pack_context
        assert len(ctx.merged_intents) > 0
        assert len(ctx.merged_gates) > 0

    def test_rule_config_property(self):
        p = Pipeline.from_project(ROOT, dry_run=True)
        rc = p.rule_config
        assert len(rc.keyword_map) > 0
        assert len(rc.platform_intents) > 0


# ── Pipeline.process() ───────────────────────────────────────────────────


class TestPipelineProcess:
    """Pipeline.process() runs the full PDP → PEP chain."""

    def test_process_returns_pipeline_result(self):
        p = Pipeline.from_project(ROOT, dry_run=True)
        result = p.process("这个功能是什么意思？")
        assert isinstance(result, PipelineResult)
        assert "intent_result" in result.envelope
        assert "execution_status" in result.execution

    def test_process_question_produces_inform_gate(self):
        p = Pipeline.from_project(ROOT, dry_run=True)
        result = p.process("这个功能是什么意思？")
        intent = result.envelope["intent_result"]["intent"]
        gate = result.envelope["gate_decision"]["gate_level"]
        assert intent == "question"
        assert gate == "inform"

    def test_process_correction_produces_review_gate(self):
        p = Pipeline.from_project(ROOT, dry_run=True)
        result = p.process("请修复这个 bug")
        intent = result.envelope["intent_result"]["intent"]
        gate = result.envelope["gate_decision"]["gate_level"]
        assert intent == "correction"
        assert gate == "review"

    def test_process_scope_change_produces_approve_gate(self):
        p = Pipeline.from_project(ROOT, dry_run=True)
        result = p.process("我想变更整个项目的 scope")
        intent = result.envelope["intent_result"]["intent"]
        gate = result.envelope["gate_decision"]["gate_level"]
        assert intent == "scope-change"
        assert gate == "approve"

    def test_process_generates_audit_events(self):
        p = Pipeline.from_project(ROOT, dry_run=True, audit=True)
        result = p.process("这是一个问题")
        assert len(result.audit_events) >= 1
        event_types = [e["event_type"] for e in result.audit_events]
        assert "input_received" in event_types
        assert "intent_classified" in event_types

    def test_process_no_audit_when_disabled(self):
        p = Pipeline.from_project(ROOT, dry_run=True, audit=False)
        result = p.process("测试输入")
        assert result.audit_events == []

    def test_process_pack_info_populated(self):
        p = Pipeline.from_project(ROOT, dry_run=True)
        result = p.process("测试")
        assert "packs" in result.pack_info
        assert len(result.pack_info["packs"]) >= 1

    def test_to_dict_excludes_rsm(self):
        p = Pipeline.from_project(ROOT, dry_run=True)
        result = p.process("测试")
        d = result.to_dict()
        assert "_rsm" not in d["execution"]
        # Should be JSON-serializable
        json.dumps(d, ensure_ascii=False, default=str)


# ── Constraint checking ──────────────────────────────────────────────────


class TestConstraintChecking:
    """Pipeline.check_constraints() inspects project state."""

    def test_check_constraints_on_real_project(self):
        p = Pipeline.from_project(ROOT, dry_run=True)
        result = p.check_constraints()
        assert isinstance(result, ConstraintResult)
        # Our project has planning-gate docs, so no C5 violation
        c5_violations = [v for v in result.violations if v.constraint == "C5"]
        assert len(c5_violations) == 0

    def test_check_constraints_files_to_reread(self):
        p = Pipeline.from_project(ROOT, dry_run=True)
        result = p.check_constraints()
        # Should find at least checklist and phase map
        assert any("Checklist" in f for f in result.files_to_reread)

    def test_check_constraints_c5_violation(self, tmp_path):
        """C5 triggers when no planning-gate documents exist."""
        result = _check_constraints(tmp_path)
        c5 = [v for v in result.violations if v.constraint == "C5"]
        assert len(c5) == 1
        assert c5[0].severity == "block"
        assert result.has_violations

    def test_check_constraints_no_violation_with_gate(self, tmp_path):
        """No C5 violation when planning-gate directory has a .md file."""
        gate_dir = tmp_path / "design_docs" / "stages" / "planning-gate"
        gate_dir.mkdir(parents=True)
        (gate_dir / "some-gate.md").write_text("# Gate", encoding="utf-8")
        result = _check_constraints(tmp_path)
        c5 = [v for v in result.violations if v.constraint == "C5"]
        assert len(c5) == 0

    def test_check_constraints_finds_approved_gate_without_checkpoint(self, tmp_path):
        gate_dir = tmp_path / "design_docs" / "stages" / "planning-gate"
        gate_dir.mkdir(parents=True)
        gate_file = gate_dir / "approved-gate.md"
        gate_file.write_text(
            "# Planning Gate\n\n- Status: **APPROVED**\n",
            encoding="utf-8",
        )

        result = _check_constraints(tmp_path)

        assert result.active_planning_gate == (
            "design_docs/stages/planning-gate/approved-gate.md"
        )

    def test_check_constraints_ignores_gate_readme_for_active_gate(self, tmp_path):
        gate_dir = tmp_path / "design_docs" / "stages" / "planning-gate"
        gate_dir.mkdir(parents=True)
        (gate_dir / "README.md").write_text(
            "# README\n\n- Status: **APPROVED**\n",
            encoding="utf-8",
        )

        result = _check_constraints(tmp_path)

        assert result.active_planning_gate == ""

    def test_check_constraints_treats_em_dash_checkpoint_gate_as_empty(self, tmp_path):
        pack_dir = tmp_path / "test-pack"
        pack_dir.mkdir()
        (pack_dir / "pack-manifest.json").write_text(
            '{"name": "test", "version": "0.1", "kind": "project-local"}',
            encoding="utf-8",
        )

        gate_dir = tmp_path / "design_docs" / "stages" / "planning-gate"
        gate_dir.mkdir(parents=True)
        (gate_dir / "closed.md").write_text(
            "# Planning Gate\n\n- Status: **COMPLETED**\n",
            encoding="utf-8",
        )

        checkpoint_dir = tmp_path / ".codex" / "checkpoints"
        checkpoint_dir.mkdir(parents=True)
        (checkpoint_dir / "latest.md").write_text(
            "# Checkpoint — 2026-04-10\n"
            "## Current Phase\n"
            "Phase 35\n"
            "## Active Planning Gate\n"
            "—\n"
            "## Current Todo\n"
            "(no todos)\n"
            "## Pending User Decision\n"
            "(none)\n"
            "## Direction Candidates\n"
            "(none)\n"
            "## Key Context Files\n"
            "- a.md\n",
            encoding="utf-8",
        )

        result = _check_constraints(tmp_path)
        assert result.active_planning_gate == ""

    def test_check_constraints_reports_runtime_scope_boundary(self, tmp_path):
        result = _check_constraints(tmp_path)

        assert [scope.constraint for scope in result.machine_checked_constraints] == [
            "C4",
            "C5",
        ]
        assert {scope.constraint for scope in result.instruction_layer_constraints} == {
            "C1",
            "C2",
            "C3",
            "C6",
            "C7",
            "C8",
        }
        assert result.runtime_enforcement_summary.startswith(
            "Runtime currently machine-checks C4, C5."
        )

    def test_check_constraints_reads_checkpoint_file_path(self, tmp_path, monkeypatch):
        pack_dir = tmp_path / "test-pack"
        pack_dir.mkdir()
        (pack_dir / "pack-manifest.json").write_text(
            '{"name": "test", "version": "0.1", "kind": "project-local"}',
            encoding="utf-8",
        )

        checkpoint_dir = tmp_path / ".codex" / "checkpoints"
        checkpoint_dir.mkdir(parents=True)
        checkpoint_path = checkpoint_dir / "latest.md"
        checkpoint_path.write_text(
            "# Checkpoint — 2026-04-10\n"
            "## Current Phase\n"
            "Phase 35\n"
            "## Active Planning Gate\n"
            "(none)\n"
            "## Current Todo\n"
            "(no todos)\n"
            "## Pending User Decision\n"
            "(none)\n"
            "## Direction Candidates\n"
            "(none)\n"
            "## Key Context Files\n"
            "- a.md\n",
            encoding="utf-8",
        )

        gate_dir = tmp_path / "design_docs" / "stages" / "planning-gate"
        gate_dir.mkdir(parents=True)
        (gate_dir / "closed.md").write_text(
            "# Planning Gate\n\n- Status: **COMPLETED**\n",
            encoding="utf-8",
        )

        captured: dict[str, Path] = {}

        def _fake_read_checkpoint(path: Path) -> dict[str, object]:
            captured["path"] = path
            return {
                "phase": "Phase 35",
                "planning_gate": "",
                "todos": [],
                "pending_decision": "",
                "direction_candidates": [],
                "key_files": ["a.md"],
            }

        monkeypatch.setattr(
            "src.workflow.checkpoint.read_checkpoint",
            _fake_read_checkpoint,
        )

        _check_constraints(tmp_path)

        assert captured["path"] == checkpoint_path

    def test_constraint_result_to_dict(self):
        result = ConstraintResult(
            violations=[ConstraintViolation("C5", "test", "block")],
            files_to_reread=["a.md"],
            current_phase="Phase 22",
            machine_checked_constraints=[
                ConstraintScope(
                    constraint="C4",
                    enforcement="machine-checked",
                    rationale="state files",
                )
            ],
            instruction_layer_constraints=[
                ConstraintScope(
                    constraint="C1",
                    enforcement="instruction-layer",
                    rationale="conversation policy",
                )
            ],
        )
        d = result.to_dict()
        assert d["has_blocking"] is True
        assert len(d["violations"]) == 1
        assert d["machine_checked_constraints"][0]["constraint"] == "C4"
        assert d["instruction_layer_constraints"][0]["constraint"] == "C1"
        assert "machine-checks C4" in d["runtime_enforcement_summary"]


# ── Pack discovery ───────────────────────────────────────────────────────


class TestPackDiscovery:
    """_discover_packs finds manifests in the project tree."""

    def test_discover_real_project(self):
        results = _discover_packs(ROOT)
        manifest_names = [p.name for p, _ in results]
        assert "pack-manifest.json" in manifest_names

    def test_discover_with_config(self, tmp_path):
        """If .codex/platform.json specifies pack_dirs, use them."""
        # Create a pack dir
        pack_dir = tmp_path / "my-pack"
        pack_dir.mkdir()
        (pack_dir / "pack-manifest.json").write_text(
            json.dumps({"name": "test", "version": "0.1", "kind": "project-local"}),
            encoding="utf-8",
        )
        # Create config
        config_dir = tmp_path / ".codex"
        config_dir.mkdir()
        (config_dir / "platform.json").write_text(
            json.dumps({"pack_dirs": ["my-pack"]}),
            encoding="utf-8",
        )
        results = _discover_packs(tmp_path)
        assert len(results) == 1
        assert results[0][0].name == "pack-manifest.json"

    def test_discover_codex_packs_dir(self, tmp_path):
        """Convention: .codex/packs/*.pack.json."""
        packs_dir = tmp_path / ".codex" / "packs"
        packs_dir.mkdir(parents=True)
        (packs_dir / "local.pack.json").write_text(
            json.dumps({"name": "local", "version": "1", "kind": "project-local"}),
            encoding="utf-8",
        )
        results = _discover_packs(tmp_path)
        assert len(results) == 1


# ── CLI ──────────────────────────────────────────────────────────────────


class TestCLI:
    """CLI commands via python -m src."""

    def test_cli_help(self):
        result = subprocess.run(
            [sys.executable, "-m", "src", "--help"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        assert result.returncode == 0
        assert "process" in result.stdout

    def test_cli_info(self):
        result = subprocess.run(
            [sys.executable, "-m", "src", "info"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "packs" in data

    def test_cli_process(self):
        result = subprocess.run(
            [sys.executable, "-m", "src", "process", "这是一个问题"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "envelope" in data
        assert "execution" in data

    def test_cli_validate(self):
        result = subprocess.run(
            [sys.executable, "-m", "src", "validate"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        # Should pass for our project (has planning-gate docs)
        assert result.returncode == 0

    def test_cli_unknown_command(self):
        result = subprocess.run(
            [sys.executable, "-m", "src", "nonexistent"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        assert result.returncode == 1
