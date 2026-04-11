"""Tests for MCP governance tools layer."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.mcp.tools import GovernanceTools

ROOT = Path(__file__).resolve().parent.parent


class TestGovernanceDecide:
    """governance_decide tool tests."""

    def test_decide_allow_on_valid_project(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.governance_decide("这是什么意思？")
        assert result["decision"] == "ALLOW"
        assert result["intent"] == "question"
        assert result["gate"] == "inform"
        assert "envelope" in result
        assert "execution" in result

    def test_decide_block_on_missing_planning_gate(self, tmp_path):
        """Should BLOCK when no planning-gate directory exists."""
        # Create minimal pack structure
        pack_dir = tmp_path / "test-pack"
        pack_dir.mkdir()
        (pack_dir / "pack-manifest.json").write_text(
            json.dumps({
                "name": "test",
                "version": "0.1",
                "kind": "project-local",
            }),
            encoding="utf-8",
        )
        tools = GovernanceTools(tmp_path, dry_run=True)
        result = tools.governance_decide("实现新功能")
        assert result["decision"] == "BLOCK"
        assert "C5" in result["constraint_violated"]
        assert "required_action" in result

    def test_decide_correction_is_review(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.governance_decide("请修复这个 bug")
        assert result["decision"] == "ALLOW"
        assert result["intent"] == "correction"
        assert result["gate"] == "review"

    def test_decide_has_audit_count(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.governance_decide("测试")
        assert "audit_event_count" in result
        assert result["audit_event_count"] >= 1

    def test_decide_has_pack_info(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.governance_decide("测试")
        assert "pack_info" in result
        assert "packs" in result["pack_info"]
        assert "external_skill_interaction_contract" in result["pack_info"]
        assert (
            result["pack_info"]["external_skill_interaction_contract"]["automatic_stop_signal"]
            == "blocked"
        )

    def test_decide_result_json_serializable(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.governance_decide("测试输入")
        # Must be JSON-serializable for MCP transport
        json.dumps(result, ensure_ascii=False, default=str)


class TestCheckConstraints:
    """check_constraints tool tests."""

    def test_check_constraints_real_project(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.check_constraints()
        assert "violations" in result
        assert "has_blocking" in result
        assert "files_to_reread" in result

    def test_check_constraints_no_blocking_on_valid_project(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.check_constraints()
        assert result["has_blocking"] is False

    def test_check_constraints_finds_key_files(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.check_constraints()
        reread = result["files_to_reread"]
        assert any("Checklist" in f for f in reread)

    def test_check_constraints_includes_checkpoint_file(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.check_constraints()
        assert ".codex/checkpoints/latest.md" in result["files_to_reread"]

    def test_check_constraints_reports_runtime_scope_boundary(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.check_constraints()
        assert result["machine_checked_constraints"][0]["constraint"] == "C4"
        assert any(
            item["constraint"] == "C1"
            for item in result["instruction_layer_constraints"]
        )
        assert result["runtime_enforcement_summary"].startswith(
            "Runtime currently machine-checks C4, C5."
        )


class TestGetNextAction:
    """get_next_action tool tests."""

    def test_next_action_has_instruction(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.get_next_action()
        assert "instruction" in result
        assert "files_to_reread" in result
        assert isinstance(result["instruction"], str)
        assert len(result["instruction"]) > 0

    def test_next_action_has_phase_info(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.get_next_action()
        assert "current_phase" in result
        assert "runtime_enforcement_summary" in result

    def test_next_action_blocked_project(self, tmp_path):
        """When constraints are violated, instruction says BLOCKED."""
        tools = GovernanceTools(tmp_path, dry_run=True)
        result = tools.get_next_action()
        assert "BLOCKED" in result["instruction"]
        assert result["ask_user"] is False

    def test_next_action_treats_em_dash_planning_gate_as_no_active_gate(self, tmp_path):
        pack_dir = tmp_path / "test-pack"
        pack_dir.mkdir()
        (pack_dir / "pack-manifest.json").write_text(
            json.dumps({
                "name": "test-pack",
                "version": "0.1",
                "kind": "project-local",
            }),
            encoding="utf-8",
        )

        gate_dir = tmp_path / "design_docs" / "stages" / "planning-gate"
        gate_dir.mkdir(parents=True)
        (gate_dir / "closed.md").write_text(
            "# Planning Gate\n\n- Status: **COMPLETED**\n",
            encoding="utf-8",
        )

        cp_dir = tmp_path / ".codex" / "checkpoints"
        cp_dir.mkdir(parents=True)
        (cp_dir / "latest.md").write_text(
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

        tools = GovernanceTools(tmp_path, dry_run=True)
        result = tools.get_next_action()
        assert result["active_planning_gate"] == ""
        assert result["ask_user"] is True
        assert result["instruction"].startswith("No active planning gate found.")
        assert result["interaction_contract"]["structured_confirmation_tool"] == "askQuestions"
        assert "analysis or recommendation first" in result["question_instruction"]


class TestWritebackNotify:
    """writeback_notify tool tests."""

    def test_writeback_notify_returns_recommendation(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.writeback_notify("Phase 22 Slice 1 completed")
        assert "phase_completed" in result
        assert "auto_next" in result
        assert "instruction" in result["auto_next"]
        assert "files_to_update" in result["auto_next"]
        assert result["ask_user"] is True
        assert result["interaction_contract"]["structured_confirmation_tool"] == "askQuestions"
        assert "analysis or recommendation first" in result["question_instruction"]
        assert result["safe_stop_writeback_bundle"]["bundle_name"] == "safe-stop-writeback"
        assert ".codex/checkpoints/latest.md" in result["safe_stop_writeback_bundle"]["files_to_update"]
        assert ".codex/checkpoints/latest.md" in result["auto_next"]["files_to_update"]

    def test_writeback_notify_includes_pending_gates(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.writeback_notify("test phase")
        # Our project has pending planning gates
        assert "pending_gates" in result["auto_next"]

    def test_writeback_notify_json_serializable(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.writeback_notify("test")
        json.dumps(result, ensure_ascii=False, default=str)

    def test_writeback_notify_only_returns_explicit_open_status_gates(self, tmp_path):
        pack_dir = tmp_path / "test-pack"
        pack_dir.mkdir()
        (pack_dir / "pack-manifest.json").write_text(
            json.dumps({
                "name": "test-pack",
                "version": "0.1",
                "kind": "project-local",
            }),
            encoding="utf-8",
        )

        gate_dir = tmp_path / "design_docs" / "stages" / "planning-gate"
        gate_dir.mkdir(parents=True)
        (gate_dir / "approved.md").write_text(
            "# Planning Gate\n\n- Status: **APPROVED**\n",
            encoding="utf-8",
        )
        (gate_dir / "closed.md").write_text(
            "# Planning Gate\n\n- Status: **CLOSED**\n",
            encoding="utf-8",
        )
        (gate_dir / "legacy-no-status.md").write_text(
            "# Planning Gate Candidate\n\nlegacy doc without status\n",
            encoding="utf-8",
        )
        (gate_dir / "README.md").write_text(
            "# README\n\n- Status: **APPROVED**\n",
            encoding="utf-8",
        )

        tools = GovernanceTools(tmp_path, dry_run=True)
        result = tools.writeback_notify("test phase")

        assert result["auto_next"]["pending_gates"] == ["approved.md"]

    def test_writeback_notify_updates_checkpoint_when_live(self, tmp_path):
        pack_dir = tmp_path / "test-pack"
        pack_dir.mkdir()
        (pack_dir / "pack-manifest.json").write_text(
            json.dumps({
                "name": "test-pack",
                "version": "0.1",
                "kind": "project-local",
            }),
            encoding="utf-8",
        )

        gate_dir = tmp_path / "design_docs" / "stages" / "planning-gate"
        gate_dir.mkdir(parents=True)
        (gate_dir / "approved.md").write_text(
            "# Planning Gate\n\n- Status: **APPROVED**\n",
            encoding="utf-8",
        )

        cp_dir = tmp_path / ".codex" / "checkpoints"
        cp_dir.mkdir(parents=True)
        (cp_dir / "latest.md").write_text(
            "# Checkpoint — 2026-04-10\n"
            "## Current Phase\n"
            "Phase 27\n"
            "## Active Planning Gate\n"
            "design_docs/stages/planning-gate/approved.md\n"
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

        tools = GovernanceTools(tmp_path, dry_run=False)
        tools.writeback_notify("Phase 28: remediation completed")

        from src.workflow.checkpoint import read_checkpoint

        data = read_checkpoint(cp_dir / "latest.md")
        assert data["phase"] == "Phase 28: remediation completed"
        assert data["planning_gate"] == ""

    def test_writeback_notify_exposes_safe_stop_bundle_contract(self, tmp_path):
        pack_dir = tmp_path / "test-pack"
        pack_dir.mkdir()
        (pack_dir / "pack-manifest.json").write_text(
            json.dumps({
                "name": "test-pack",
                "version": "0.1",
                "kind": "project-local",
            }),
            encoding="utf-8",
        )

        design_docs = tmp_path / "design_docs"
        design_docs.mkdir(parents=True)
        (design_docs / "direction-candidates-after-phase-35.md").write_text(
            "# Direction\n",
            encoding="utf-8",
        )

        gate_dir = design_docs / "stages" / "planning-gate"
        gate_dir.mkdir(parents=True)

        cp_dir = tmp_path / ".codex" / "checkpoints"
        cp_dir.mkdir(parents=True)
        (cp_dir / "latest.md").write_text(
            "# Checkpoint — 2026-04-12\n"
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

        tools = GovernanceTools(tmp_path, dry_run=True)
        result = tools.writeback_notify("test safe stop")

        bundle = result["safe_stop_writeback_bundle"]
        required_keys = {step["key"] for step in bundle["required_steps"]}
        assert "generate-canonical-handoff" in required_keys
        assert "sync-direction-candidates" in required_keys
        assert "design_docs/direction-candidates-after-phase-35.md" in bundle["files_to_update"]


class TestGetInfo:
    """get_pack_info tool tests."""

    def test_get_info_returns_packs(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.get_info()
        assert "packs" in result
        assert len(result["packs"]) >= 1
        assert result["packs"][0]["name"] == "doc-loop-vibe-coding"

    def test_get_info_has_merged_fields(self):
        tools = GovernanceTools(ROOT, dry_run=True)
        result = tools.get_info()
        assert "merged_intents" in result
        assert "merged_gates" in result
        assert "merged_document_types" in result
        assert "external_skill_interaction_contract" in result
        assert result["external_skill_interaction_contract"]["reference_implementation"]["family"] == "project-handoff-*"

    def test_get_info_refreshes_after_manifest_change(self, tmp_path):
        gate_dir = tmp_path / "design_docs" / "stages" / "planning-gate"
        gate_dir.mkdir(parents=True)
        (gate_dir / "gate.md").write_text(
            "# Planning Gate\n\n- Status: **ACTIVE**\n",
            encoding="utf-8",
        )

        cp_dir = tmp_path / ".codex" / "checkpoints"
        cp_dir.mkdir(parents=True)
        (cp_dir / "latest.md").write_text(
            "# Checkpoint — 2026-04-11\n"
            "## Current Phase\n"
            "Phase 35\n"
            "## Active Planning Gate\n"
            "design_docs/stages/planning-gate/gate.md\n"
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

        pack_dir = tmp_path / "test-pack"
        pack_dir.mkdir()
        manifest_path = pack_dir / "pack-manifest.json"
        manifest = {
            "name": "test-pack",
            "version": "0.1.0",
            "kind": "official-instance",
            "scope": "Test pack",
            "provides": ["prompts"],
            "document_types": [],
            "intents": ["question"],
            "gates": ["inform"],
            "always_on": [],
            "on_demand": [],
            "depends_on": [],
            "overrides": [],
            "prompts": [],
            "templates": [],
            "validators": [],
            "checks": [],
            "scripts": [],
            "triggers": [],
        }
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        tools = GovernanceTools(tmp_path, dry_run=True)
        first = tools.get_info()
        assert first["packs"][0]["version"] == "0.1.0"
        assert "correction" not in first["merged_intents"]

        manifest["version"] = "0.2.0"
        manifest["intents"] = ["question", "correction"]
        manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

        second = tools.get_info()
        assert second["packs"][0]["version"] == "0.2.0"
        assert "correction" in second["merged_intents"]
