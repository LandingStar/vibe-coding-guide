"""Tests for InstructionsGenerator (Slice 3)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from src.pack.context_builder import ContextBuilder, PackContext
from src.pack.manifest_loader import PackManifest, load_dict
from src.workflow.instructions_generator import (
    InstructionsGenerator,
    generate_instructions,
    generate_instructions_from_project,
)


# ── Fixtures ─────────────────────────────────────────────────────────────


def _make_manifest(**overrides) -> PackManifest:
    base = {
        "name": "test-pack",
        "version": "1.0.0",
        "kind": "official-instance",
    }
    base.update(overrides)
    return load_dict(base)


def _build_context(*manifests: PackManifest) -> PackContext:
    builder = ContextBuilder()
    for m in manifests:
        builder.add_pack(m, ".")
    return builder.build()


# ── Header ───────────────────────────────────────────────────────────────


class TestHeader:
    def test_single_pack(self):
        ctx = _build_context(_make_manifest(name="my-pack", version="2.0"))
        gen = InstructionsGenerator(ctx)
        result = gen.generate()
        assert "**my-pack**" in result
        assert "v2.0" in result
        assert "official-instance" in result

    def test_multiple_packs(self):
        m1 = _make_manifest(name="pack-a", version="1.0", kind="official-instance")
        m2 = _make_manifest(name="pack-b", version="2.0", kind="project-local")
        ctx = _build_context(m1, m2)
        result = InstructionsGenerator(ctx).generate()
        assert "pack-a" in result
        assert "pack-b" in result

    def test_scope_included(self):
        ctx = _build_context(_make_manifest(scope="My test scope"))
        result = InstructionsGenerator(ctx).generate()
        assert "My test scope" in result


# ── Document Types ───────────────────────────────────────────────────────


class TestDocumentTypes:
    def test_document_types_listed(self):
        ctx = _build_context(
            _make_manifest(document_types=["checklist", "phase-map", "planning-gate"])
        )
        result = InstructionsGenerator(ctx).generate()
        assert "`checklist`" in result
        assert "`phase-map`" in result
        assert "`planning-gate`" in result
        assert "Document Types" in result

    def test_empty_doc_types_omitted(self):
        ctx = _build_context(_make_manifest(document_types=[]))
        result = InstructionsGenerator(ctx).generate()
        assert "Document Types" not in result


# ── Intents ──────────────────────────────────────────────────────────────


class TestIntents:
    def test_intents_listed(self):
        ctx = _build_context(
            _make_manifest(intents=["question", "correction", "approval"])
        )
        result = InstructionsGenerator(ctx).generate()
        assert "`question`" in result
        assert "`correction`" in result
        assert "`approval`" in result
        assert "Recognized Intents" in result

    def test_empty_intents_omitted(self):
        ctx = _build_context(_make_manifest(intents=[]))
        result = InstructionsGenerator(ctx).generate()
        assert "Recognized Intents" not in result


# ── Gates ────────────────────────────────────────────────────────────────


class TestGates:
    def test_gates_listed_with_descriptions(self):
        ctx = _build_context(
            _make_manifest(gates=["inform", "review", "approve"])
        )
        result = InstructionsGenerator(ctx).generate()
        assert "`inform`" in result
        assert "`review`" in result
        assert "`approve`" in result
        assert "Gate Levels" in result
        # Should include descriptions for known gates
        assert "Low-impact" in result
        assert "High-impact" in result

    def test_custom_gate_no_description(self):
        ctx = _build_context(_make_manifest(gates=["custom-gate"]))
        result = InstructionsGenerator(ctx).generate()
        assert "`custom-gate`" in result


# ── Constraints ──────────────────────────────────────────────────────────


class TestConstraints:
    def test_constraints_from_dict(self):
        rules = {
            "constraints": {
                "C1": "Never terminate conversation",
                "C2": "Always reference documents",
            }
        }
        ctx = _build_context(_make_manifest(rules=rules))
        result = InstructionsGenerator(ctx).generate()
        assert "**C1**" in result
        assert "Never terminate conversation" in result
        assert "**C2**" in result
        assert "Constraints (MUST obey)" in result

    def test_constraints_from_list(self):
        rules = {
            "constraints": [
                {"id": "C1", "description": "No termination"},
                {"id": "C2", "description": "Doc references required"},
            ]
        }
        ctx = _build_context(_make_manifest(rules=rules))
        result = InstructionsGenerator(ctx).generate()
        assert "**C1**" in result
        assert "No termination" in result

    def test_constraints_with_severity(self):
        rules = {
            "constraints": {
                "C1": {"description": "Never end", "severity": "block"},
            }
        }
        ctx = _build_context(_make_manifest(rules=rules))
        result = InstructionsGenerator(ctx).generate()
        assert "[block]" in result
        assert "Never end" in result

    def test_no_rules_no_constraints_section(self):
        ctx = _build_context(_make_manifest())
        result = InstructionsGenerator(ctx).generate()
        assert "Constraints" not in result


# ── Rules ────────────────────────────────────────────────────────────────


class TestRules:
    def test_additional_rules_rendered(self):
        rules = {
            "constraints": {"C1": "test"},
            "workflow": {
                "max_slices": 5,
                "auto_writeback": True,
            },
        }
        ctx = _build_context(_make_manifest(rules=rules))
        result = InstructionsGenerator(ctx).generate()
        assert "### workflow" in result
        assert "max_slices" in result

    def test_behavioral_rules_in_constraints(self):
        rules = {
            "behavioral_rules": [
                "Always ask before deleting files",
                "Never skip tests",
            ]
        }
        ctx = _build_context(_make_manifest(rules=rules))
        result = InstructionsGenerator(ctx).generate()
        assert "Always ask before deleting files" in result
        assert "Never skip tests" in result

    def test_conversation_progression_contract_section_rendered(self):
        rules = {
            "conversation_progression": {
                "termination_requires_user_permission": True,
                "final_reply_requires_forward_question": True,
                "question_must_include_analysis": True,
                "structured_confirmation_tool": "askQuestions",
                "structured_confirmation_required_for": ["choice", "approval"],
                "phase_completion_requires_next_direction": True,
                "allowed_non_question_endings": ["user explicitly allows ending"],
            }
        }
        ctx = _build_context(_make_manifest(rules=rules))
        result = InstructionsGenerator(ctx).generate()
        assert "Conversation Progression Contract" in result
        assert "askQuestions" in result

    def test_external_skill_interaction_contract_section_rendered(self):
        rules = {
            "external_skill_interaction": {
                "model_may_initiate_when_rules_allow": True,
                "slash_is_explicit_route_not_only_surface": True,
                "automatic_stop_signal": "blocked",
                "non_blocked_results_may_continue": True,
                "result_payload_may_be_skill_specific": True,
                "authority_transfer_requires_primitives": ["handoff", "escalation"],
                "reference_implementation_family": "project-handoff-*",
                "companion_distribution_rule": "authority-to-shipped-copies-drift-check",
            }
        }
        ctx = _build_context(_make_manifest(rules=rules))
        result = InstructionsGenerator(ctx).generate()
        assert "External Skill Interaction Contract" in result
        assert "project-handoff-*" in result
        assert "blocked" in result
        assert "handoff, escalation" in result
        assert "authority -> shipped copies consistency" in result


# ── Always On ────────────────────────────────────────────────────────────


class TestAlwaysOn:
    def test_always_on_files_listed(self, tmp_path):
        # Create mock always_on files
        (tmp_path / "SKILL.md").write_text("skill content")
        (tmp_path / "refs").mkdir()
        (tmp_path / "refs" / "workflow.md").write_text("workflow content")

        m = _make_manifest(always_on=["SKILL.md", "refs/workflow.md"])
        builder = ContextBuilder()
        builder.add_pack(m, str(tmp_path))
        ctx = builder.build()

        result = InstructionsGenerator(ctx).generate()
        assert "Always-On Context" in result
        assert "`SKILL.md`" in result
        assert "`refs/workflow.md`" in result


# ── Convenience Functions ────────────────────────────────────────────────


class TestConvenienceFunctions:
    def test_generate_instructions_function(self):
        ctx = _build_context(
            _make_manifest(
                name="func-test",
                document_types=["checklist"],
                intents=["question"],
                gates=["inform"],
            )
        )
        result = generate_instructions(ctx)
        assert "func-test" in result
        assert "`checklist`" in result
        assert "`question`" in result
        assert "`inform`" in result

    def test_generate_from_project(self):
        """Test project-level generation with real project root."""
        root = Path(__file__).parent.parent
        result = generate_instructions_from_project(root)
        # Should contain the official-instance pack
        assert "doc-loop-vibe-coding" in result
        assert "Document Types" in result
        assert "Conversation Progression Contract" in result


# ── CLI ──────────────────────────────────────────────────────────────────


class TestCLI:
    def test_generate_instructions_cli(self):
        """Test the CLI command outputs instructions to stdout."""
        root = Path(__file__).parent.parent
        result = subprocess.run(
            [sys.executable, "-m", "src", "generate-instructions"],
            capture_output=True,
            text=True,
            cwd=str(root),
        )
        assert result.returncode == 0
        assert "Governance Instructions" in result.stdout
        assert "doc-loop-vibe-coding" in result.stdout

    def test_generate_instructions_cli_output_file(self, tmp_path):
        """Test the CLI command writes to a file."""
        root = Path(__file__).parent.parent
        out_file = tmp_path / "generated.md"
        result = subprocess.run(
            [
                sys.executable, "-m", "src",
                "generate-instructions",
                "--output", str(out_file),
            ],
            capture_output=True,
            text=True,
            cwd=str(root),
        )
        assert result.returncode == 0
        assert out_file.exists()
        content = out_file.read_text(encoding="utf-8")
        assert "Governance Instructions" in content
