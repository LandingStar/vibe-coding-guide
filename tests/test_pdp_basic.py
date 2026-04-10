"""Tests for PDP core: intent classifier, gate resolver, decision envelope."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from src.pdp import intent_classifier, gate_resolver, decision_envelope

SPECS_DIR = Path(__file__).resolve().parent.parent / "docs" / "specs"


def _load_schema(name: str) -> dict:
    with open(SPECS_DIR / name) as f:
        return json.load(f)


INTENT_SCHEMA = _load_schema("intent-classification-result.schema.json")
GATE_SCHEMA = _load_schema("gate-decision-result.schema.json")
ENVELOPE_SCHEMA = _load_schema("pdp-decision-envelope.schema.json")


# --- Intent Classifier ---

class TestIntentClassifier:
    def test_question(self):
        result = intent_classifier.classify("What is this?")
        assert result["intent"] == "question"
        assert result["confidence"] in ("high", "medium", "low")

    def test_approval(self):
        result = intent_classifier.classify("审核通过")
        assert result["intent"] == "approval"

    def test_rejection(self):
        result = intent_classifier.classify("reject this proposal")
        assert result["intent"] == "rejection"

    def test_scope_change_high_impact(self):
        result = intent_classifier.classify("Please change scope to include more")
        assert result["intent"] == "scope-change"
        assert result.get("high_impact") is True

    def test_unknown_for_empty(self):
        result = intent_classifier.classify("")
        assert result["intent"] == "unknown"

    def test_unknown_for_gibberish(self):
        result = intent_classifier.classify("xyzzy foobar baz")
        assert result["intent"] == "unknown"

    def test_schema_compliance(self):
        result = intent_classifier.classify("fix the bug please")
        jsonschema.validate(result, INTENT_SCHEMA)

    def test_schema_compliance_unknown(self):
        result = intent_classifier.classify("")
        jsonschema.validate(result, INTENT_SCHEMA)


# --- Gate Resolver ---

class TestGateResolver:
    def test_low_impact_inform(self):
        intent_result = {"intent": "question", "confidence": "high"}
        gate = gate_resolver.resolve(intent_result)
        assert gate["gate_level"] == "inform"
        assert gate["review_state_entry"] == "proposed"

    def test_medium_impact_review(self):
        intent_result = {"intent": "correction", "confidence": "medium"}
        gate = gate_resolver.resolve(intent_result)
        assert gate["gate_level"] == "review"
        assert gate["review_state_entry"] == "waiting_review"

    def test_high_impact_approve(self):
        intent_result = {"intent": "scope-change", "confidence": "high",
                         "high_impact": True}
        gate = gate_resolver.resolve(intent_result)
        assert gate["gate_level"] == "approve"
        assert gate["review_state_entry"] == "waiting_review"

    def test_high_impact_never_inform(self):
        intent_result = {"intent": "question", "confidence": "high",
                         "high_impact": True}
        gate = gate_resolver.resolve(intent_result)
        assert gate["gate_level"] != "inform"

    def test_schema_compliance(self):
        intent_result = {"intent": "approval", "confidence": "high"}
        gate = gate_resolver.resolve(intent_result)
        jsonschema.validate(gate, GATE_SCHEMA)


# --- Decision Envelope ---

class TestDecisionEnvelope:
    def test_basic_envelope(self):
        envelope = decision_envelope.build_envelope("What is the current status?")
        assert "decision_id" in envelope
        assert "timestamp" in envelope
        assert "input_summary" in envelope
        assert "intent_result" in envelope
        assert "gate_decision" in envelope
        assert "rationale" in envelope

    def test_envelope_intent_is_question(self):
        envelope = decision_envelope.build_envelope("What is this?")
        assert envelope["intent_result"]["intent"] == "question"
        assert envelope["gate_decision"]["gate_level"] == "inform"

    def test_envelope_high_impact(self):
        envelope = decision_envelope.build_envelope("change scope to everything")
        assert envelope["gate_decision"]["gate_level"] == "approve"

    def test_envelope_schema_compliance(self):
        """Validate the full envelope against the master schema."""
        envelope = decision_envelope.build_envelope("fix the error in the code")
        # Validate sub-structures individually
        jsonschema.validate(envelope["intent_result"], INTENT_SCHEMA)
        jsonschema.validate(envelope["gate_decision"], GATE_SCHEMA)
        # Validate envelope structure (without $ref resolution, check required fields)
        required = ENVELOPE_SCHEMA["required"]
        for field in required:
            assert field in envelope, f"Missing required field: {field}"
        # Check no extra top-level keys
        allowed = set(ENVELOPE_SCHEMA["properties"].keys())
        for key in envelope:
            assert key in allowed, f"Unexpected field: {key}"

    def test_input_summary_truncation(self):
        long_text = "a" * 500
        envelope = decision_envelope.build_envelope(long_text)
        assert len(envelope["input_summary"]) <= 203  # 200 + "..."
