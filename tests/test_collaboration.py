"""Tests for Phase 20 — Worker Collaboration Modes (Handoff + Subgraph).

Covers:
- CollaborationMode enum
- Handoff mode: prepare, execute, audit events
- Subgraph mode: create_context, execute, merge_result, audit events
- PDP delegation_resolver mode selection via RuleConfig.extra
- PEP executor mode dispatch (handoff / subgraph / default worker)
- Backward compatibility: existing worker mode unaffected
"""

from __future__ import annotations

import pytest

from src.collaboration.modes import CollaborationMode, ModeExecutor
from src.collaboration.handoff_mode import (
    HandoffRequest,
    prepare as handoff_prepare,
    execute as handoff_execute,
)
from src.collaboration.subgraph_mode import (
    SubgraphContext,
    create_context as sg_create_context,
    execute as sg_execute,
    merge_result as sg_merge,
)
from src.pdp.delegation_resolver import resolve as delegation_resolve
from src.pdp.decision_envelope import build_envelope
from src.pack.override_resolver import RuleConfig, default_rule_config
from src.pep.executor import Executor
from src.subagent import contract_factory, report_validator
from src.subagent.stub_worker import StubWorkerBackend


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mode_rule_config(mode: str) -> RuleConfig:
    """Build a RuleConfig with default platform values + mode override."""
    base = default_rule_config()
    base.extra = {"collaboration_mode": mode}
    return base

class _RecordingAuditLogger:
    """Minimal audit logger that records events for assertion."""

    def __init__(self):
        self.events: list[dict] = []

    def emit(self, event_type: str, source: str, trace_id: str, *, detail: dict | None = None):
        self.events.append({
            "event_type": event_type,
            "source": source,
            "trace_id": trace_id,
            "detail": detail or {},
        })


class _FailingWorker:
    """Worker that always raises."""

    def execute(self, contract: dict) -> dict:
        raise RuntimeError("worker exploded")


def _make_delegation(mode: str = "supervisor-worker", **extra) -> dict:
    """Build a minimal delegation decision dict."""
    return {
        "delegate": True,
        "mode": mode,
        "scope_summary": "test scope",
        "worker_only": mode == "supervisor-worker",
        "requires_review": mode in ("handoff", "subgraph"),
        "allow_handoff": mode == "handoff",
        "rationale": f"test delegation in {mode} mode",
        "contract_hints": {"suggested_task": "test task", "out_of_scope": []},
        **extra,
    }


def _make_contract(contract_id: str = "contract-test-001") -> dict:
    """Build a minimal contract dict."""
    return {
        "contract_id": contract_id,
        "scope": "test scope",
        "required_refs": ["AGENTS.md"],
        "out_of_scope": ["do not touch docs"],
    }


def _make_executor(**kwargs) -> Executor:
    return Executor(
        dry_run=True,
        worker=StubWorkerBackend(),
        contract_factory=contract_factory,
        report_validator=report_validator,
        **kwargs,
    )


# ===========================================================================
# 1. CollaborationMode enum
# ===========================================================================

class TestCollaborationMode:

    def test_enum_values(self):
        assert CollaborationMode.WORKER == "worker"
        assert CollaborationMode.HANDOFF == "handoff"
        assert CollaborationMode.SUBGRAPH == "subgraph"

    def test_enum_from_string(self):
        assert CollaborationMode("handoff") is CollaborationMode.HANDOFF

    def test_enum_invalid_raises(self):
        with pytest.raises(ValueError):
            CollaborationMode("swarm")


# ===========================================================================
# 2. Handoff mode
# ===========================================================================

class TestHandoffPrepare:

    def test_prepare_creates_request(self):
        delegation = _make_delegation("handoff")
        contract = _make_contract()
        req = handoff_prepare(delegation, contract)

        assert isinstance(req, HandoffRequest)
        assert req.request_id.startswith("hreq-")
        assert req.from_role == "main-ai"
        assert req.requires_review is True
        assert req.scope == "test scope"

    def test_prepare_uses_to_role_from_hints(self):
        delegation = _make_delegation("handoff")
        delegation["contract_hints"]["to_role"] = "doc-specialist"
        contract = _make_contract()
        req = handoff_prepare(delegation, contract)
        assert req.to_role == "doc-specialist"

    def test_prepare_defaults_to_role(self):
        delegation = _make_delegation("handoff")
        contract = _make_contract()
        req = handoff_prepare(delegation, contract)
        assert req.to_role == "specialist-ai"


class TestHandoffExecute:

    def test_execute_success(self):
        delegation = _make_delegation("handoff")
        contract = _make_contract()
        req = handoff_prepare(delegation, contract)
        worker = StubWorkerBackend()

        result = handoff_execute(req, contract, worker)
        assert result["mode"] == "handoff"
        assert result["status"] == "handoff_completed"
        assert result["report"] is not None
        assert result["handoff"] is not None
        assert result["handoff"]["from_role"] == "main-ai"

    def test_execute_emits_audit_events(self):
        delegation = _make_delegation("handoff")
        contract = _make_contract()
        req = handoff_prepare(delegation, contract)
        worker = StubWorkerBackend()
        logger = _RecordingAuditLogger()

        handoff_execute(req, contract, worker, audit_logger=logger, trace_id="t-001")

        event_types = [e["event_type"] for e in logger.events]
        assert "handoff_initiated" in event_types
        assert "handoff_completed" in event_types

    def test_execute_failure_emits_failed(self):
        delegation = _make_delegation("handoff")
        contract = _make_contract()
        req = handoff_prepare(delegation, contract)
        logger = _RecordingAuditLogger()

        result = handoff_execute(
            req, contract, _FailingWorker(),
            audit_logger=logger, trace_id="t-002",
        )

        assert result["status"] == "handoff_failed"
        assert result["report"] is None
        event_types = [e["event_type"] for e in logger.events]
        assert "handoff_failed" in event_types

    def test_handoff_object_has_required_fields(self):
        delegation = _make_delegation("handoff")
        contract = _make_contract()
        req = handoff_prepare(delegation, contract)
        worker = StubWorkerBackend()

        result = handoff_execute(req, contract, worker)
        handoff = result["handoff"]

        assert "handoff_id" in handoff
        assert "from_role" in handoff
        assert "to_role" in handoff
        assert "reason" in handoff
        assert "active_scope" in handoff
        assert "authoritative_refs" in handoff
        assert "intake_requirements" in handoff


# ===========================================================================
# 3. Subgraph mode
# ===========================================================================

class TestSubgraphCreateContext:

    def test_creates_context(self):
        delegation = _make_delegation("subgraph")
        contract = _make_contract()
        ctx = sg_create_context(delegation, contract, trace_id="t-100")

        assert isinstance(ctx, SubgraphContext)
        assert ctx.context_id.startswith("sg-")
        assert ctx.namespace == "contract-test-001"
        assert ctx.parent_trace_id == "t-100"
        assert ctx.isolation_level == "full"

    def test_shared_read_isolation(self):
        delegation = _make_delegation("subgraph")
        delegation["contract_hints"]["isolation_level"] = "shared-read"
        contract = _make_contract()
        ctx = sg_create_context(delegation, contract)
        assert ctx.isolation_level == "shared-read"


class TestSubgraphExecute:

    def test_execute_success(self):
        delegation = _make_delegation("subgraph")
        contract = _make_contract()
        ctx = sg_create_context(delegation, contract, trace_id="t-200")
        worker = StubWorkerBackend()

        result = sg_execute(ctx, contract, worker, trace_id="t-200")
        assert result["mode"] == "subgraph"
        assert result["status"] == "subgraph_completed"
        assert result["report"] is not None
        assert result["delta"] is not None
        assert result["delta"]["namespace"] == ctx.namespace

    def test_execute_emits_audit_events(self):
        delegation = _make_delegation("subgraph")
        contract = _make_contract()
        ctx = sg_create_context(delegation, contract, trace_id="t-201")
        worker = StubWorkerBackend()
        logger = _RecordingAuditLogger()

        sg_execute(ctx, contract, worker, audit_logger=logger, trace_id="t-201")

        event_types = [e["event_type"] for e in logger.events]
        assert "subgraph_created" in event_types
        assert "subgraph_completed" in event_types

    def test_execute_failure(self):
        delegation = _make_delegation("subgraph")
        contract = _make_contract()
        ctx = sg_create_context(delegation, contract, trace_id="t-202")
        logger = _RecordingAuditLogger()

        result = sg_execute(
            ctx, contract, _FailingWorker(),
            audit_logger=logger, trace_id="t-202",
        )

        assert result["status"] == "subgraph_failed"
        assert result["report"] is None
        event_types = [e["event_type"] for e in logger.events]
        assert "subgraph_failed" in event_types


class TestSubgraphMerge:

    def test_merge_applies_delta(self):
        parent = {"doc_count": 5, "status": "idle"}
        sg_result = {
            "delta": {
                "doc_count": 6,
                "new_key": "added",
            }
        }
        merged = sg_merge(sg_result, parent)
        assert merged["doc_count"] == 6
        assert merged["new_key"] == "added"
        assert merged["status"] == "idle"  # untouched

    def test_merge_empty_delta(self):
        parent = {"x": 1}
        merged = sg_merge({"delta": {}}, parent)
        assert merged == {"x": 1}

    def test_merge_none_delta(self):
        parent = {"x": 1}
        merged = sg_merge({"delta": None}, parent)
        assert merged == {"x": 1}


# ===========================================================================
# 4. PDP delegation_resolver mode selection
# ===========================================================================

class TestDelegationResolverModeSelection:

    def test_default_mode_is_supervisor_worker(self):
        intent = {"intent": "correction", "confidence": 0.9}
        gate = {"gate_level": "review"}
        result = delegation_resolve(intent, gate)
        assert result["mode"] == "supervisor-worker"

    def test_rule_config_overrides_mode_to_handoff(self):
        rc = default_rule_config()
        rc.extra = {"collaboration_mode": "handoff"}
        intent = {"intent": "correction", "confidence": 0.9}
        gate = {"gate_level": "review"}
        result = delegation_resolve(intent, gate, rule_config=rc)
        assert result["mode"] == "handoff"
        assert result["allow_handoff"] is True
        assert result["requires_review"] is True

    def test_rule_config_overrides_mode_to_subgraph(self):
        rc = default_rule_config()
        rc.extra = {"collaboration_mode": "subgraph"}
        intent = {"intent": "correction", "confidence": 0.9}
        gate = {"gate_level": "review"}
        result = delegation_resolve(intent, gate, rule_config=rc)
        assert result["mode"] == "subgraph"
        assert result["worker_only"] is False
        assert result["requires_review"] is True

    def test_invalid_mode_in_extra_falls_back(self):
        rc = default_rule_config()
        rc.extra = {"collaboration_mode": "swarm"}
        intent = {"intent": "correction", "confidence": 0.9}
        gate = {"gate_level": "review"}
        result = delegation_resolve(intent, gate, rule_config=rc)
        assert result["mode"] == "supervisor-worker"


# ===========================================================================
# 5. PEP executor mode dispatch
# ===========================================================================

class TestExecutorHandoffMode:

    def test_handoff_mode_dispatch(self):
        """Executor dispatches to handoff mode when delegation.mode == 'handoff'."""
        rc = _mode_rule_config("handoff")
        envelope = build_envelope("这里有个 bug 需要修复", rule_config=rc)
        executor = _make_executor()
        result = executor.execute(envelope)

        assert result["execution_status"] == "delegated"
        assert result.get("mode") == "handoff"
        assert result.get("handoff") is not None

    def test_handoff_mode_rsm_state(self):
        """Handoff mode transitions RSM to waiting_review."""
        rc = _mode_rule_config("handoff")
        envelope = build_envelope("这里有个 bug 需要修复", rule_config=rc)
        executor = _make_executor()
        result = executor.execute(envelope)

        # Handoff requires review — RSM should be in waiting_review
        assert result["execution_status"] == "delegated"


class TestExecutorSubgraphMode:

    def test_subgraph_mode_dispatch(self):
        """Executor dispatches to subgraph mode when delegation.mode == 'subgraph'."""
        rc = _mode_rule_config("subgraph")
        envelope = build_envelope("这里有个 bug 需要修复", rule_config=rc)
        executor = _make_executor()
        result = executor.execute(envelope)

        assert result["execution_status"] == "delegated"
        assert result.get("mode") == "subgraph"
        assert result.get("subgraph_context") is not None
        assert result.get("delta") is not None

    def test_subgraph_mode_rsm_state(self):
        """Subgraph mode transitions RSM to waiting_review."""
        rc = _mode_rule_config("subgraph")
        envelope = build_envelope("这里有个 bug 需要修复", rule_config=rc)
        executor = _make_executor()
        result = executor.execute(envelope)
        assert result["execution_status"] == "delegated"


class TestExecutorDefaultModeUnchanged:

    def test_default_mode_still_works(self):
        """Default supervisor-worker mode is unchanged."""
        envelope = build_envelope("这里有个 bug 需要修复")
        executor = _make_executor()
        result = executor.execute(envelope)

        assert result["execution_status"] == "delegated"
        assert "mode" not in result or result.get("mode") is None
        assert "contract" in result
        assert "report" in result
