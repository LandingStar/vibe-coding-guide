"""Tests for audit & tracing system: AuditLogger, TraceContext, PDP/PEP integration."""

from __future__ import annotations

import json
import pytest
from pathlib import Path

from src.audit.trace_context import TraceContext, new_trace, child_trace
from src.audit.audit_logger import (
    AuditEvent,
    AuditLogger,
    MemoryAuditBackend,
    FileAuditBackend,
)
from src.pdp.decision_envelope import build_envelope
from src.pep.executor import Executor


# ===========================================================================
# TraceContext tests
# ===========================================================================


class TestTraceContext:
    def test_new_trace(self):
        tc = new_trace()
        assert tc.trace_id.startswith("trace-")
        assert tc.parent_trace_id is None
        assert tc.created_at  # non-empty

    def test_child_trace(self):
        parent = new_trace()
        child = child_trace(parent)
        assert child.trace_id.startswith("trace-")
        assert child.parent_trace_id == parent.trace_id
        assert child.trace_id != parent.trace_id

    def test_trace_immutable(self):
        tc = new_trace()
        with pytest.raises(AttributeError):
            tc.trace_id = "modified"


# ===========================================================================
# AuditEvent tests
# ===========================================================================


class TestAuditEvent:
    def test_to_dict(self):
        evt = AuditEvent(
            event_id="evt-1",
            trace_id="trace-abc",
            timestamp="2026-04-10T00:00:00Z",
            event_type="test",
            phase="pdp",
            detail={"key": "value"},
        )
        d = evt.to_dict()
        assert d["event_id"] == "evt-1"
        assert d["trace_id"] == "trace-abc"
        assert d["detail"] == {"key": "value"}
        assert "parent_trace_id" not in d  # None should be stripped

    def test_to_dict_with_parent(self):
        evt = AuditEvent(
            event_id="evt-2",
            trace_id="trace-abc",
            timestamp="2026-04-10T00:00:00Z",
            event_type="test",
            phase="pep",
            parent_trace_id="trace-parent",
        )
        d = evt.to_dict()
        assert d["parent_trace_id"] == "trace-parent"


# ===========================================================================
# MemoryAuditBackend tests
# ===========================================================================


class TestMemoryAuditBackend:
    def test_emit_and_query(self):
        backend = MemoryAuditBackend()
        evt = AuditEvent(
            event_id="evt-1", trace_id="t1", timestamp="now",
            event_type="test", phase="pdp",
        )
        backend.emit(evt)
        assert len(backend.all_events) == 1
        assert backend.query("t1") == [evt]
        assert backend.query("t2") == []

    def test_multiple_events(self):
        backend = MemoryAuditBackend()
        for i in range(5):
            backend.emit(AuditEvent(
                event_id=f"evt-{i}", trace_id="t1", timestamp="now",
                event_type="test", phase="pdp",
            ))
        backend.emit(AuditEvent(
            event_id="evt-other", trace_id="t2", timestamp="now",
            event_type="test", phase="pep",
        ))
        assert len(backend.query("t1")) == 5
        assert len(backend.query("t2")) == 1


# ===========================================================================
# FileAuditBackend tests
# ===========================================================================


class TestFileAuditBackend:
    def test_emit_and_query(self, tmp_path):
        path = tmp_path / "audit.jsonl"
        backend = FileAuditBackend(path)
        evt = AuditEvent(
            event_id="evt-1", trace_id="t1", timestamp="now",
            event_type="test", phase="pdp", detail={"a": 1},
        )
        backend.emit(evt)

        # File should exist
        assert path.exists()
        lines = path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 1
        parsed = json.loads(lines[0])
        assert parsed["event_id"] == "evt-1"

        # Query
        results = backend.query("t1")
        assert len(results) == 1
        assert results[0].event_id == "evt-1"

    def test_query_empty_file(self, tmp_path):
        path = tmp_path / "audit.jsonl"
        backend = FileAuditBackend(path)
        assert backend.query("t1") == []

    def test_creates_parent_dirs(self, tmp_path):
        path = tmp_path / "nested" / "dir" / "audit.jsonl"
        backend = FileAuditBackend(path)
        backend.emit(AuditEvent(
            event_id="evt-1", trace_id="t1", timestamp="now",
            event_type="test", phase="pdp",
        ))
        assert path.exists()


# ===========================================================================
# AuditLogger tests
# ===========================================================================


class TestAuditLogger:
    def test_emit_returns_event(self):
        logger = AuditLogger()
        evt = logger.emit("test_event", "pdp", "trace-1", detail={"x": 1})
        assert evt.event_type == "test_event"
        assert evt.trace_id == "trace-1"
        assert evt.detail == {"x": 1}

    def test_query(self):
        logger = AuditLogger()
        logger.emit("a", "pdp", "t1")
        logger.emit("b", "pep", "t1")
        logger.emit("c", "pdp", "t2")
        assert len(logger.query("t1")) == 2
        assert len(logger.query("t2")) == 1

    def test_multi_backend(self, tmp_path):
        mem = MemoryAuditBackend()
        file_backend = FileAuditBackend(tmp_path / "audit.jsonl")
        logger = AuditLogger(mem, file_backend)

        logger.emit("test", "pdp", "t1")
        assert len(mem.all_events) == 1
        assert len(file_backend.query("t1")) == 1

    def test_default_memory_backend(self):
        logger = AuditLogger()
        assert len(logger.backends) == 1
        assert isinstance(logger.backends[0], MemoryAuditBackend)

    def test_emit_parent_trace(self):
        logger = AuditLogger()
        evt = logger.emit("test", "pdp", "t1", parent_trace_id="parent-1")
        assert evt.parent_trace_id == "parent-1"


# ===========================================================================
# PDP audit integration tests
# ===========================================================================


class TestPDPAuditIntegration:
    def test_envelope_with_audit_logger(self):
        logger = AuditLogger()
        trace = new_trace()
        envelope = build_envelope(
            "fix this bug", audit_logger=logger, trace_ctx=trace,
        )
        assert envelope.get("trace_id") == trace.trace_id

        events = logger.query(trace.trace_id)
        event_types = [e.event_type for e in events]
        # At minimum: input_received, intent_classified, gate_resolved
        assert "input_received" in event_types
        assert "intent_classified" in event_types
        assert "gate_resolved" in event_types

    def test_envelope_with_delegation_audit(self):
        logger = AuditLogger()
        trace = new_trace()
        envelope = build_envelope(
            "fix this bug", audit_logger=logger, trace_ctx=trace,
        )
        events = logger.query(trace.trace_id)
        event_types = [e.event_type for e in events]
        # correction → review gate → delegation_decided
        assert "delegation_decided" in event_types

    def test_envelope_with_escalation_audit(self):
        logger = AuditLogger()
        trace = new_trace()
        # scope-change is high impact → escalation
        envelope = build_envelope(
            "change scope of project", audit_logger=logger, trace_ctx=trace,
        )
        events = logger.query(trace.trace_id)
        event_types = [e.event_type for e in events]
        assert "escalation_decided" in event_types

    def test_envelope_with_precedence_audit(self):
        logger = AuditLogger()
        trace = new_trace()
        rules = [
            {"rule_id": "r1", "layer": "platform"},
            {"rule_id": "r2", "layer": "project-local"},
        ]
        envelope = build_envelope(
            "what is this?", active_rules=rules,
            audit_logger=logger, trace_ctx=trace,
        )
        events = logger.query(trace.trace_id)
        event_types = [e.event_type for e in events]
        assert "precedence_resolved" in event_types

    def test_envelope_without_audit_logger(self):
        """Backward compat: no logger, no trace_id in envelope."""
        envelope = build_envelope("what is this?")
        assert "trace_id" not in envelope

    def test_envelope_auto_creates_trace(self):
        """If audit_logger given but no trace_ctx, a new trace is created."""
        logger = AuditLogger()
        envelope = build_envelope("what is this?", audit_logger=logger)
        assert "trace_id" in envelope
        events = logger.query(envelope["trace_id"])
        assert len(events) >= 3


# ===========================================================================
# PEP audit integration tests
# ===========================================================================


class TestPEPAuditIntegration:
    def test_execute_with_audit(self):
        logger = AuditLogger()
        trace = new_trace()
        envelope = build_envelope(
            "what is this?", audit_logger=logger, trace_ctx=trace,
        )
        executor = Executor(dry_run=True, audit_logger=logger)
        result = executor.execute(envelope)

        events = logger.query(trace.trace_id)
        event_types = [e.event_type for e in events]
        assert "execution_started" in event_types

    def test_execute_without_audit(self):
        """Backward compat: no audit logger works fine."""
        envelope = build_envelope("what is this?")
        executor = Executor(dry_run=True)
        result = executor.execute(envelope)
        assert result["execution_status"] in ("applied", "dry-run")

    def test_review_feedback_audit(self):
        logger = AuditLogger()
        trace = new_trace()
        envelope = build_envelope(
            "fix this bug", audit_logger=logger, trace_ctx=trace,
        )
        executor = Executor(dry_run=True, audit_logger=logger)
        result = executor.execute(envelope)

        if result["review_state"] == "waiting_review":
            executor.apply_review_feedback(
                envelope, result, "approve", reason="looks good",
            )
            events = logger.query(trace.trace_id)
            event_types = [e.event_type for e in events]
            assert "review_feedback" in event_types


# ===========================================================================
# Full chain audit trace test
# ===========================================================================


class TestFullChainAudit:
    def test_full_governance_trace(self):
        """Complete trace from input → PDP → PEP → review feedback.

        Should produce ≥7 events covering all governance phases.
        """
        logger = AuditLogger()
        trace = new_trace()

        # PDP phase
        envelope = build_envelope(
            "fix this bug please",
            active_rules=[
                {"rule_id": "r1", "layer": "platform"},
                {"rule_id": "r2", "layer": "project-local"},
            ],
            audit_logger=logger,
            trace_ctx=trace,
        )

        # PEP phase
        executor = Executor(dry_run=True, audit_logger=logger)
        result = executor.execute(envelope)

        # Review phase
        if result["review_state"] == "waiting_review":
            executor.apply_review_feedback(
                envelope, result, "approve", reason="lgtm",
            )

        events = logger.query(trace.trace_id)
        event_types = [e.event_type for e in events]

        # Verify ≥7 governance events
        assert len(events) >= 7, f"Expected ≥7 events, got {len(events)}: {event_types}"

        # All required event types should be present
        required = {
            "input_received",
            "intent_classified",
            "gate_resolved",
            "delegation_decided",
            "precedence_resolved",
            "execution_started",
            "review_feedback",
        }
        assert required.issubset(set(event_types)), (
            f"Missing events: {required - set(event_types)}"
        )

        # Verify all events share the same trace_id
        for event in events:
            assert event.trace_id == trace.trace_id

        # Verify chronological ordering (all phases covered)
        phases = [e.phase for e in events]
        assert "pdp" in phases
        assert "pep" in phases
