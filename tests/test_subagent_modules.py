"""Tests for contract_factory and report_validator (Slice B)."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from src.subagent import contract_factory, report_validator

# ---------- contract_factory tests ----------

_CONTRACT_SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "docs" / "specs" / "subagent-contract.schema.json"
)
_CONTRACT_SCHEMA = json.loads(_CONTRACT_SCHEMA_PATH.read_text(encoding="utf-8"))


def _sample_delegation_decision() -> dict:
    return {
        "delegate": True,
        "mode": "supervisor-worker",
        "scope_summary": "Fix a typo in README.",
        "contract_hints": {
            "suggested_task": "Fix typo on line 42.",
            "out_of_scope": [
                "Do not rewrite entire file.",
            ],
        },
    }


class TestContractFactory:
    def test_returns_valid_contract(self):
        contract = contract_factory.build(_sample_delegation_decision())
        jsonschema.validate(contract, _CONTRACT_SCHEMA)

    def test_contract_id_pattern(self):
        contract = contract_factory.build(_sample_delegation_decision())
        assert contract["contract_id"].startswith("contract-")

    def test_task_from_hints(self):
        contract = contract_factory.build(_sample_delegation_decision())
        assert contract["task"] == "Fix typo on line 42."

    def test_mode_mapping(self):
        contract = contract_factory.build(_sample_delegation_decision())
        assert contract["mode"] == "worker"

    def test_scope_from_decision(self):
        contract = contract_factory.build(_sample_delegation_decision())
        assert contract["scope"] == "Fix a typo in README."

    def test_out_of_scope(self):
        contract = contract_factory.build(_sample_delegation_decision())
        assert "Do not rewrite entire file." in contract["out_of_scope"]

    def test_defaults_when_no_hints(self):
        decision = {"delegate": True}
        contract = contract_factory.build(decision)
        jsonschema.validate(contract, _CONTRACT_SCHEMA)
        assert contract["task"] == "Perform delegated work."

    def test_unique_ids(self):
        d = _sample_delegation_decision()
        ids = {contract_factory.build(d)["contract_id"] for _ in range(20)}
        assert len(ids) == 20


# ---------- report_validator tests ----------

def _valid_report(contract_id: str = "contract-abc123") -> dict:
    return {
        "report_id": "report-001",
        "contract_id": contract_id,
        "status": "completed",
        "changed_artifacts": ["README.md"],
        "verification_results": ["All tests pass"],
    }


class TestReportValidator:
    def test_valid_report(self):
        result = report_validator.validate(_valid_report())
        assert result["valid"] is True
        assert result["errors"] == []

    def test_missing_required_field(self):
        report = _valid_report()
        del report["status"]
        result = report_validator.validate(report)
        assert result["valid"] is False
        assert any("status" in e for e in result["errors"])

    def test_invalid_status_enum(self):
        report = _valid_report()
        report["status"] = "invalid-status"
        result = report_validator.validate(report)
        assert result["valid"] is False

    def test_bad_report_id_pattern(self):
        report = _valid_report()
        report["report_id"] = "bad-id"
        result = report_validator.validate(report)
        assert result["valid"] is False

    def test_extra_field_rejected(self):
        report = _valid_report()
        report["unexpected_field"] = "oops"
        result = report_validator.validate(report)
        assert result["valid"] is False

    def test_optional_fields(self):
        report = _valid_report()
        report["unresolved_items"] = ["Item A"]
        report["assumptions"] = ["Assumed X"]
        report["escalation_recommendation"] = "none"
        result = report_validator.validate(report)
        assert result["valid"] is True
