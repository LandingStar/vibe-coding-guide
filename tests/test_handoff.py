"""Tests for handoff_builder + PEP handoff integration (Phase 9)."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from src.subagent import handoff_builder

_HANDOFF_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs" / "specs" / "handoff.schema.json"
)
_HANDOFF_SCHEMA = json.loads(_HANDOFF_SCHEMA_PATH.read_text(encoding="utf-8"))


def _sample_envelope() -> dict:
    return {
        "decision_id": "env-001",
        "intent_result": {"intent": "correction", "confidence": "high"},
        "gate_decision": {"gate_level": "review"},
    }


def _sample_delegation() -> dict:
    return {
        "delegate": True,
        "mode": "supervisor-worker",
        "scope_summary": "Fix typo in README.",
        "allow_handoff": True,
        "requires_review": False,
        "contract_hints": {
            "suggested_task": "Fix typo.",
            "out_of_scope": ["Do not rewrite entire file."],
        },
    }


def _sample_contract() -> dict:
    return {
        "contract_id": "contract-abc123",
        "task": "Fix typo.",
        "mode": "worker",
        "scope": "Fix typo in README line 42.",
        "allowed_artifacts": ["README.md"],
        "required_refs": ["docs/README.md"],
        "acceptance": ["Typo fixed."],
        "verification": ["Run tests."],
        "out_of_scope": ["Do not rewrite entire file."],
        "report_schema": "subagent-report",
    }


def _sample_report(status: str = "completed") -> dict:
    return {
        "report_id": "report-xyz789",
        "contract_id": "contract-abc123",
        "status": status,
        "changed_artifacts": ["README.md"],
        "verification_results": ["All tests pass."],
    }


class TestHandoffBuilder:
    def test_schema_valid(self):
        handoff = handoff_builder.build(
            _sample_envelope(), _sample_delegation(),
            _sample_contract(), _sample_report(),
        )
        jsonschema.validate(handoff, _HANDOFF_SCHEMA)

    def test_handoff_id_pattern(self):
        handoff = handoff_builder.build(
            _sample_envelope(), _sample_delegation(),
            _sample_contract(), _sample_report(),
        )
        assert handoff["handoff_id"].startswith("handoff-")

    def test_roles(self):
        handoff = handoff_builder.build(
            _sample_envelope(), _sample_delegation(),
            _sample_contract(), _sample_report(),
        )
        assert handoff["from_role"] == "main-ai"
        assert handoff["to_role"] == "worker-ai"

    def test_requires_review_changes_to_role(self):
        delegation = _sample_delegation()
        delegation["requires_review"] = True
        handoff = handoff_builder.build(
            _sample_envelope(), delegation,
            _sample_contract(), _sample_report(),
        )
        assert handoff["to_role"] == "human-reviewer"
        jsonschema.validate(handoff, _HANDOFF_SCHEMA)

    def test_completed_report_applied_state(self):
        handoff = handoff_builder.build(
            _sample_envelope(), _sample_delegation(),
            _sample_contract(), _sample_report("completed"),
        )
        assert handoff["current_gate_state"] == "applied"

    def test_partial_report_waiting_review(self):
        handoff = handoff_builder.build(
            _sample_envelope(), _sample_delegation(),
            _sample_contract(), _sample_report("partial"),
        )
        assert handoff["current_gate_state"] == "waiting_review"
        jsonschema.validate(handoff, _HANDOFF_SCHEMA)

    def test_blocked_report_rejected(self):
        handoff = handoff_builder.build(
            _sample_envelope(), _sample_delegation(),
            _sample_contract(), _sample_report("blocked"),
        )
        assert handoff["current_gate_state"] == "rejected"
        jsonschema.validate(handoff, _HANDOFF_SCHEMA)

    def test_open_items_from_report(self):
        report = _sample_report()
        report["unresolved_items"] = ["Issue A", "Issue B"]
        handoff = handoff_builder.build(
            _sample_envelope(), _sample_delegation(),
            _sample_contract(), report,
        )
        assert handoff["open_items"] == ["Issue A", "Issue B"]
        assert any("unresolved" in r.lower() for r in handoff["intake_requirements"])
        jsonschema.validate(handoff, _HANDOFF_SCHEMA)

    def test_unique_ids(self):
        ids = set()
        for _ in range(20):
            h = handoff_builder.build(
                _sample_envelope(), _sample_delegation(),
                _sample_contract(), _sample_report(),
            )
            ids.add(h["handoff_id"])
        assert len(ids) == 20


# ---------- PEP handoff integration ----------

from src.pdp.decision_envelope import build_envelope
from src.pep.executor import Executor
from src.subagent import contract_factory, report_validator
from src.subagent.stub_worker import StubWorkerBackend


class TestPepHandoffIntegration:
    """PEP executor generates handoff when allow_handoff is True."""

    def _make_executor(self, *, dry_run=True, handoff_dir=None):
        return Executor(
            dry_run=dry_run,
            worker=StubWorkerBackend(),
            contract_factory=contract_factory,
            report_validator=report_validator,
            handoff_dir=handoff_dir,
        )

    def test_handoff_in_result_when_allowed(self):
        """When delegation has allow_handoff=True, result includes handoff."""
        # Force allow_handoff on the delegation decision.
        envelope = build_envelope("请修正这个拼写错误")
        if envelope.get("delegation_decision"):
            envelope["delegation_decision"]["allow_handoff"] = True

        executor = self._make_executor()
        result = executor.execute(envelope)

        assert result["execution_status"] == "delegated"
        assert "handoff" in result
        jsonschema.validate(result["handoff"], _HANDOFF_SCHEMA)

    def test_no_handoff_when_not_allowed(self):
        """Default delegation (allow_handoff=False/missing) has no handoff."""
        envelope = build_envelope("请修正拼写错误")
        executor = self._make_executor()
        result = executor.execute(envelope)

        assert result["execution_status"] == "delegated"
        assert "handoff" not in result

    def test_dry_run_no_file(self, tmp_path):
        """Dry-run mode builds handoff but does not write to disk."""
        envelope = build_envelope("修正文档错误")
        if envelope.get("delegation_decision"):
            envelope["delegation_decision"]["allow_handoff"] = True

        executor = self._make_executor(dry_run=True, handoff_dir=tmp_path)
        result = executor.execute(envelope)

        assert "handoff" in result
        # No file should be created in dry-run mode.
        assert list(tmp_path.glob("*.json")) == []

    def test_non_dry_run_persists_file(self, tmp_path):
        """Non-dry-run mode writes handoff JSON to disk."""
        envelope = build_envelope("修正拼写错误")
        if envelope.get("delegation_decision"):
            envelope["delegation_decision"]["allow_handoff"] = True

        executor = self._make_executor(dry_run=False, handoff_dir=tmp_path)
        result = executor.execute(envelope)

        assert "handoff" in result
        files = list(tmp_path.glob("handoff-*.json"))
        assert len(files) == 1

        # Persisted file should match the result and pass schema validation.
        persisted = json.loads(files[0].read_text(encoding="utf-8"))
        assert persisted["handoff_id"] == result["handoff"]["handoff_id"]
        jsonschema.validate(persisted, _HANDOFF_SCHEMA)

    def test_handoff_log_entries(self):
        """Dry-run handoff produces a handoff-built log entry."""
        envelope = build_envelope("修正文档中的错误")
        if envelope.get("delegation_decision"):
            envelope["delegation_decision"]["allow_handoff"] = True

        executor = self._make_executor()
        executor.execute(envelope)

        actions = [e["action"] for e in executor.log.entries]
        assert "handoff-built" in actions
