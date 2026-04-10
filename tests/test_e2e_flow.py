"""End-to-end tests: input → PDP → PEP → verify full pipeline."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from src.pdp import decision_envelope
from src.pep.executor import Executor

SPECS_DIR = Path(__file__).resolve().parent.parent / "docs" / "specs"


def _load_schema(name: str) -> dict:
    with open(SPECS_DIR / name) as f:
        return json.load(f)


INTENT_SCHEMA = _load_schema("intent-classification-result.schema.json")
GATE_SCHEMA = _load_schema("gate-decision-result.schema.json")
ENVELOPE_SCHEMA = _load_schema("pdp-decision-envelope.schema.json")


class TestEndToEnd:
    """End-to-end pipeline: user input → PDP → PEP → verify."""

    def test_question_fast_path(self):
        """A question should get inform gate and be applied (dry-run)."""
        envelope = decision_envelope.build_envelope("What is the status?")
        executor = Executor(dry_run=True)
        result = executor.execute(envelope)

        assert envelope["intent_result"]["intent"] == "question"
        assert envelope["gate_decision"]["gate_level"] == "inform"
        assert result["execution_status"] == "dry-run"
        assert len(executor.log.entries) == 1

    def test_correction_review_path(self):
        """A correction should get review gate and be queued."""
        envelope = decision_envelope.build_envelope("Please fix the wrong value")
        executor = Executor(dry_run=True)
        result = executor.execute(envelope)

        assert envelope["intent_result"]["intent"] == "correction"
        assert envelope["gate_decision"]["gate_level"] == "review"
        assert result["execution_status"] == "waiting_review"

    def test_scope_change_approve_path(self):
        """A scope change should get approve gate and be escalated."""
        envelope = decision_envelope.build_envelope(
            "expand scope to include all modules"
        )
        executor = Executor(dry_run=True)
        result = executor.execute(envelope)

        assert envelope["gate_decision"]["gate_level"] == "approve"
        # approve gate triggers escalation to human_reviewer
        assert result["execution_status"] in ("waiting_review", "escalated")

    def test_unknown_input(self):
        """Gibberish input should be classified as unknown."""
        envelope = decision_envelope.build_envelope("asdfghjkl qwerty")
        executor = Executor(dry_run=True)
        result = executor.execute(envelope)

        assert envelope["intent_result"]["intent"] == "unknown"
        # unknown + low confidence triggers escalation to main_agent
        assert result["execution_status"] in ("waiting_review", "re-evaluate")

    def test_full_pipeline_schema_compliance(self):
        """Verify the full pipeline output conforms to all schemas."""
        inputs = [
            "What is this?",
            "fix the error",
            "change scope to everything",
            "审核通过",
            "reject this",
            "",
        ]
        for text in inputs:
            envelope = decision_envelope.build_envelope(text)

            # Validate sub-structures
            jsonschema.validate(envelope["intent_result"], INTENT_SCHEMA)
            jsonschema.validate(envelope["gate_decision"], GATE_SCHEMA)

            # Validate envelope structure
            required = ENVELOPE_SCHEMA["required"]
            for field in required:
                assert field in envelope, (
                    f"Missing required field: {field} for input: {text!r}"
                )

            # Execute through PEP
            executor = Executor(dry_run=True)
            result = executor.execute(envelope)
            assert "execution_status" in result
            assert "envelope_id" in result

    def test_action_log_accumulates(self):
        """Action log should accumulate entries across multiple executions."""
        executor = Executor(dry_run=True)
        for text in ["What?", "fix bug", "change scope"]:
            envelope = decision_envelope.build_envelope(text)
            executor.execute(envelope)

        # Each execution produces at least 1 log entry; escalation may add more
        assert len(executor.log.entries) >= 3
        log_json = executor.log.to_json()
        assert len(log_json) >= 3
        for entry in log_json:
            assert "log_id" in entry
            assert "timestamp" in entry
            assert "envelope_id" in entry
            assert "action" in entry

    def test_non_dry_run_inform_applies(self):
        """In non-dry-run mode, inform gate should produce 'applied' status."""
        envelope = decision_envelope.build_envelope("What is this?")
        executor = Executor(dry_run=False)
        result = executor.execute(envelope)

        assert result["execution_status"] == "applied"
