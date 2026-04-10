"""Tests for the full PDP decision chain including delegation,
escalation, and precedence resolution."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from src.pdp import (
    decision_envelope,
    delegation_resolver,
    escalation_resolver,
    precedence_resolver,
)

SPECS_DIR = Path(__file__).resolve().parent.parent / "docs" / "specs"


def _load_schema(name: str) -> dict:
    with open(SPECS_DIR / name) as f:
        return json.load(f)


DELEGATION_SCHEMA = _load_schema("delegation-decision-result.schema.json")
ESCALATION_SCHEMA = _load_schema("escalation-decision-result.schema.json")
PRECEDENCE_SCHEMA = _load_schema("precedence-resolution-result.schema.json")
INTENT_SCHEMA = _load_schema("intent-classification-result.schema.json")
GATE_SCHEMA = _load_schema("gate-decision-result.schema.json")


# --- Delegation Resolver ---

class TestDelegationResolver:
    def test_inform_gate_returns_none(self):
        intent = {"intent": "question", "confidence": "high"}
        gate = {"gate_level": "inform", "review_state_entry": "proposed",
                "rationale": "test"}
        assert delegation_resolver.resolve(intent, gate) is None

    def test_delegatable_intent(self):
        intent = {"intent": "correction", "confidence": "medium"}
        gate = {"gate_level": "review", "review_state_entry": "waiting_review",
                "rationale": "test"}
        result = delegation_resolver.resolve(intent, gate)
        assert result["delegate"] is True
        assert result["mode"] == "supervisor-worker"
        assert result["worker_only"] is True

    def test_non_delegatable_intent(self):
        intent = {"intent": "approval", "confidence": "high"}
        gate = {"gate_level": "review", "review_state_entry": "waiting_review",
                "rationale": "test"}
        result = delegation_resolver.resolve(intent, gate)
        assert result["delegate"] is False
        assert "rejection_reason" in result

    def test_approve_gate_requires_review(self):
        intent = {"intent": "correction", "confidence": "high"}
        gate = {"gate_level": "approve", "review_state_entry": "waiting_review",
                "rationale": "test"}
        result = delegation_resolver.resolve(intent, gate)
        assert result["delegate"] is True
        assert result["requires_review"] is True
        assert result.get("review_gate_level") == "approve"

    def test_schema_compliance_delegate_true(self):
        intent = {"intent": "correction", "confidence": "medium"}
        gate = {"gate_level": "review", "review_state_entry": "waiting_review",
                "rationale": "test"}
        result = delegation_resolver.resolve(intent, gate)
        jsonschema.validate(result, DELEGATION_SCHEMA)

    def test_schema_compliance_delegate_false(self):
        intent = {"intent": "approval", "confidence": "high"}
        gate = {"gate_level": "review", "review_state_entry": "waiting_review",
                "rationale": "test"}
        result = delegation_resolver.resolve(intent, gate)
        jsonschema.validate(result, DELEGATION_SCHEMA)


# --- Escalation Resolver ---

class TestEscalationResolver:
    def test_no_trigger(self):
        intent = {"intent": "question", "confidence": "high"}
        gate = {"gate_level": "inform", "review_state_entry": "proposed",
                "rationale": "test"}
        result = escalation_resolver.resolve(intent, gate)
        assert result["escalate"] is False

    def test_low_confidence_triggers(self):
        intent = {"intent": "question", "confidence": "low"}
        gate = {"gate_level": "review", "review_state_entry": "waiting_review",
                "rationale": "test"}
        result = escalation_resolver.resolve(intent, gate)
        assert result["escalate"] is True
        assert result["target_authority"] == "main_agent"

    def test_high_impact_triggers_human(self):
        intent = {"intent": "scope-change", "confidence": "high",
                  "high_impact": True}
        gate = {"gate_level": "approve", "review_state_entry": "waiting_review",
                "rationale": "test"}
        result = escalation_resolver.resolve(intent, gate)
        assert result["escalate"] is True
        assert result["target_authority"] == "human_reviewer"

    def test_ambiguous_triggers(self):
        intent = {"intent": "ambiguous", "confidence": "low",
                  "alternatives": [{"intent": "question", "confidence": "low"}]}
        gate = {"gate_level": "review", "review_state_entry": "waiting_review",
                "rationale": "test"}
        result = escalation_resolver.resolve(intent, gate)
        assert result["escalate"] is True

    def test_schema_compliance_escalate(self):
        intent = {"intent": "scope-change", "confidence": "high",
                  "high_impact": True}
        gate = {"gate_level": "approve", "review_state_entry": "waiting_review",
                "rationale": "test"}
        result = escalation_resolver.resolve(intent, gate)
        jsonschema.validate(result, ESCALATION_SCHEMA)

    def test_schema_compliance_no_escalate(self):
        intent = {"intent": "question", "confidence": "high"}
        gate = {"gate_level": "inform", "review_state_entry": "proposed",
                "rationale": "test"}
        result = escalation_resolver.resolve(intent, gate)
        jsonschema.validate(result, ESCALATION_SCHEMA)


# --- Precedence Resolver ---

class TestPrecedenceResolver:
    def test_empty_rules(self):
        assert precedence_resolver.resolve([]) is None

    def test_single_rule(self):
        rules = [{"rule_id": "r1", "layer": "platform"}]
        result = precedence_resolver.resolve(rules)
        assert result["winning_rule"] == "r1"
        assert result["adoption_layer"] == "platform"

    def test_project_local_wins(self):
        rules = [
            {"rule_id": "r-platform", "layer": "platform"},
            {"rule_id": "r-local", "layer": "project-local"},
            {"rule_id": "r-instance", "layer": "instance"},
        ]
        result = precedence_resolver.resolve(rules)
        assert result["winning_rule"] == "r-local"
        assert result["adoption_layer"] == "project-local"

    def test_conflicts_detected(self):
        rules = [
            {"rule_id": "r1", "layer": "platform"},
            {"rule_id": "r2", "layer": "project-local"},
        ]
        result = precedence_resolver.resolve(rules)
        assert len(result["conflicts"]) > 0

    def test_schema_compliance(self):
        rules = [
            {"rule_id": "gate-default", "layer": "platform"},
            {"rule_id": "gate-override", "layer": "project-local"},
        ]
        result = precedence_resolver.resolve(rules)
        jsonschema.validate(result, PRECEDENCE_SCHEMA)


# --- Full Envelope with All Optional Fields ---

class TestFullEnvelope:
    def test_correction_has_delegation(self):
        envelope = decision_envelope.build_envelope("fix this bug please")
        assert "delegation_decision" in envelope
        assert envelope["delegation_decision"]["delegate"] is True
        jsonschema.validate(
            envelope["delegation_decision"], DELEGATION_SCHEMA
        )

    def test_scope_change_has_escalation(self):
        envelope = decision_envelope.build_envelope(
            "change scope to include everything"
        )
        assert "escalation_decision" in envelope
        assert envelope["escalation_decision"]["escalate"] is True
        jsonschema.validate(
            envelope["escalation_decision"], ESCALATION_SCHEMA
        )

    def test_question_no_delegation(self):
        """Inform gate should not produce delegation_decision."""
        envelope = decision_envelope.build_envelope("What is this?")
        assert "delegation_decision" not in envelope

    def test_with_precedence_rules(self):
        rules = [
            {"rule_id": "default-gate", "layer": "platform"},
            {"rule_id": "custom-gate", "layer": "project-local"},
        ]
        envelope = decision_envelope.build_envelope(
            "fix the error", active_rules=rules
        )
        assert "precedence_resolution" in envelope
        assert envelope["precedence_resolution"]["winning_rule"] == "custom-gate"
        jsonschema.validate(
            envelope["precedence_resolution"], PRECEDENCE_SCHEMA
        )

    def test_full_envelope_all_schemas(self):
        """Comprehensive: build envelope with all optional fields and validate."""
        rules = [
            {"rule_id": "r1", "layer": "platform"},
            {"rule_id": "r2", "layer": "project-local"},
        ]
        # "fix" triggers correction → delegation + review gate
        envelope = decision_envelope.build_envelope(
            "fix the error", active_rules=rules
        )

        # Required fields
        for field in ["decision_id", "timestamp", "input_summary",
                      "intent_result", "gate_decision", "rationale"]:
            assert field in envelope

        # Validate sub-structures against schemas
        jsonschema.validate(envelope["intent_result"], INTENT_SCHEMA)
        jsonschema.validate(envelope["gate_decision"], GATE_SCHEMA)

        if "delegation_decision" in envelope:
            jsonschema.validate(
                envelope["delegation_decision"], DELEGATION_SCHEMA
            )
        if "escalation_decision" in envelope:
            jsonschema.validate(
                envelope["escalation_decision"], ESCALATION_SCHEMA
            )
        if "precedence_resolution" in envelope:
            jsonschema.validate(
                envelope["precedence_resolution"], PRECEDENCE_SCHEMA
            )
