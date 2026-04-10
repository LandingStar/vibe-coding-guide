"""End-to-end tests for PEP delegation pipeline (Slice C).

Full path: input → PDP → PEP → contract → stub worker → report → validate.
"""

from __future__ import annotations

import pytest

from src.pdp.decision_envelope import build_envelope
from src.pep.executor import Executor
from src.subagent import contract_factory, report_validator
from src.subagent.stub_worker import StubWorkerBackend


def _make_executor(**kwargs) -> Executor:
    return Executor(
        dry_run=True,
        worker=StubWorkerBackend(),
        contract_factory=contract_factory,
        report_validator=report_validator,
        **kwargs,
    )


class TestPepDelegation:
    """PEP executor routes delegation through contract → worker → report."""

    def test_delegation_full_pipeline(self):
        """A delegatable intent produces a full delegation result."""
        envelope = build_envelope("请修正这个拼写错误")  # correction intent
        executor = _make_executor()
        result = executor.execute(envelope)

        assert result["execution_status"] == "delegated"
        assert "contract" in result
        assert result["contract"]["contract_id"].startswith("contract-")
        assert "report" in result
        assert result["report"]["status"] == "completed"
        assert result["validation"]["valid"] is True

    def test_delegation_log_entries(self):
        """Delegation should produce 3 log entries: contract, worker, validate."""
        envelope = build_envelope("修正文档中的错误")
        executor = _make_executor()
        executor.execute(envelope)

        actions = [e["action"] for e in executor.log.entries]
        assert "contract-created" in actions
        assert "worker-executed" in actions
        assert "report-validated" in actions

    def test_non_delegatable_skips_pipeline(self):
        """A non-delegatable intent should not trigger delegation."""
        envelope = build_envelope("请介绍项目架构")  # description intent
        executor = _make_executor()
        result = executor.execute(envelope)

        assert result["execution_status"] != "delegated"
        assert "contract" not in result

    def test_inform_gate_skips_delegation(self):
        """Inform-gate intents never trigger delegation."""
        envelope = build_envelope("当前状态是什么")  # question → inform
        executor = _make_executor()
        result = executor.execute(envelope)

        # question → inform gate → fast path, no delegation
        assert result["execution_status"] in ("applied", "dry-run")

    def test_no_worker_falls_back(self):
        """Without worker configured, delegation falls back to queue."""
        envelope = build_envelope("修正拼写错误")
        executor = Executor(dry_run=True)  # no worker
        result = executor.execute(envelope)

        assert result["execution_status"] == "waiting_review"
        assert "not configured" in result["detail"]

    def test_contract_schema_valid(self):
        """Generated contract passes full schema validation."""
        import json
        from pathlib import Path
        import jsonschema

        schema_path = Path(__file__).resolve().parents[1] / "docs" / "specs" / "subagent-contract.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        envelope = build_envelope("请把这个bug修好")  # correction
        executor = _make_executor()
        result = executor.execute(envelope)

        jsonschema.validate(result["contract"], schema)

    def test_report_schema_valid(self):
        """Stub worker report passes schema validation."""
        import json
        from pathlib import Path
        import jsonschema

        schema_path = Path(__file__).resolve().parents[1] / "docs" / "specs" / "subagent-report.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))

        envelope = build_envelope("修正文档错误")
        executor = _make_executor()
        result = executor.execute(envelope)

        jsonschema.validate(result["report"], schema)


class TestPepDelegationWithoutValidator:
    """Delegation works even without a report validator."""

    def test_no_validator(self):
        executor = Executor(
            dry_run=True,
            worker=StubWorkerBackend(),
            contract_factory=contract_factory,
        )
        envelope = build_envelope("修正拼写")
        result = executor.execute(envelope)

        assert result["execution_status"] == "delegated"
        assert "validation" not in result


class TestExistingBehaviorPreserved:
    """Existing non-delegation behavior must not break."""

    def test_inform_still_works(self):
        executor = Executor(dry_run=True)
        envelope = build_envelope("当前状态是什么")
        result = executor.execute(envelope)
        assert result["execution_status"] in ("applied", "dry-run")

    def test_review_still_works(self):
        executor = Executor(dry_run=True)
        envelope = build_envelope("请增加一个新的约束条件")
        result = executor.execute(envelope)
        assert result["execution_status"] == "waiting_review"
