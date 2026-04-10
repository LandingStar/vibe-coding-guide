"""Tests for ReviewOrchestrator and PEP feedback integration (Phase 13 Slice B)."""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from src.pep.executor import Executor
from src.pep.review_orchestrator import ReviewOrchestrator
from src.pep.notifiers.console_notifier import ConsoleNotifier
from src.pep.stub_notifier import StubNotifier
from src.pdp.decision_envelope import build_envelope
from src.review.state_machine import (
    APPLIED,
    APPROVED,
    PROPOSED,
    REJECTED,
    REVISED,
    WAITING_REVIEW,
    ReviewStateMachine,
    SUBMIT_FOR_REVIEW,
)


# ── ReviewOrchestrator unit tests ──────────────────────

class TestOrchestratorApprove:
    def test_approve_auto_apply(self):
        rsm = ReviewStateMachine()
        rsm.transition(SUBMIT_FOR_REVIEW)
        orch = ReviewOrchestrator()
        result = orch.submit_feedback(rsm, "approve", reason="LGTM")
        assert result["review_state"] == APPLIED

    def test_approve_no_auto_apply(self):
        rsm = ReviewStateMachine()
        rsm.transition(SUBMIT_FOR_REVIEW)
        orch = ReviewOrchestrator()
        result = orch.submit_feedback(rsm, "approve", auto_apply=False)
        assert result["review_state"] == APPROVED


class TestOrchestratorReject:
    def test_reject_terminal(self):
        rsm = ReviewStateMachine()
        rsm.transition(SUBMIT_FOR_REVIEW)
        orch = ReviewOrchestrator()
        result = orch.submit_feedback(rsm, "reject", reason="Not acceptable")
        assert result["review_state"] == REJECTED

    def test_reject_sends_notification(self):
        rsm = ReviewStateMachine()
        rsm.transition(SUBMIT_FOR_REVIEW)
        stub = StubNotifier()
        orch = ReviewOrchestrator(notifier=stub)
        result = orch.submit_feedback(rsm, "reject", reason="Bad quality")
        assert "notification" in result
        assert result["notification"]["type"] == "rejection"
        assert len(stub.notifications) == 1

    def test_reject_no_notifier_no_notification(self):
        rsm = ReviewStateMachine()
        rsm.transition(SUBMIT_FOR_REVIEW)
        orch = ReviewOrchestrator()
        result = orch.submit_feedback(rsm, "reject")
        assert "notification" not in result


class TestOrchestratorRevision:
    def test_revision_state(self):
        rsm = ReviewStateMachine()
        rsm.transition(SUBMIT_FOR_REVIEW)
        orch = ReviewOrchestrator()
        result = orch.submit_feedback(rsm, "request_revision", reason="Needs more detail")
        assert result["review_state"] == REVISED

    def test_revision_sends_notification(self):
        rsm = ReviewStateMachine()
        rsm.transition(SUBMIT_FOR_REVIEW)
        stub = StubNotifier()
        orch = ReviewOrchestrator(notifier=stub)
        result = orch.submit_feedback(rsm, "request_revision", reason="Clarify scope")
        assert result["notification"]["type"] == "revision_request"
        assert result["notification"]["action_required"] == "Revise and re-submit"

    def test_revision_then_resubmit(self):
        rsm = ReviewStateMachine()
        rsm.transition(SUBMIT_FOR_REVIEW)
        orch = ReviewOrchestrator()
        orch.submit_feedback(rsm, "request_revision")
        # Now submit revision
        result = orch.submit_revision(rsm, reason="Updated with fixes")
        assert result["review_state"] == WAITING_REVIEW
        # Can now approve
        result2 = orch.submit_feedback(rsm, "approve")
        assert result2["review_state"] == APPLIED


class TestOrchestratorEdgeCases:
    def test_unknown_feedback(self):
        rsm = ReviewStateMachine()
        rsm.transition(SUBMIT_FOR_REVIEW)
        orch = ReviewOrchestrator()
        result = orch.submit_feedback(rsm, "invalid_event")
        assert "error" in result

    def test_full_revision_cycle(self):
        """revision → revise → submit → approve → apply."""
        rsm = ReviewStateMachine()
        rsm.transition(SUBMIT_FOR_REVIEW)
        orch = ReviewOrchestrator()
        # First review: request revision
        orch.submit_feedback(rsm, "request_revision")
        assert rsm.current_state == REVISED
        # Author revises
        orch.submit_revision(rsm)
        assert rsm.current_state == WAITING_REVIEW
        # Second review: approve
        result = orch.submit_feedback(rsm, "approve")
        assert result["review_state"] == APPLIED
        # History should have transitions
        assert len(result["review_history"]) >= 5


# ── PEP integration with feedback ─────────────────────

class TestPepReviewFeedback:
    def test_review_then_approve(self):
        exe = Executor(dry_run=True)
        env = build_envelope("fix this error in the code")
        result = exe.execute(env)
        assert result["review_state"] == WAITING_REVIEW
        # Apply feedback
        result = exe.apply_review_feedback(env, result, "approve", reason="OK")
        assert result["review_state"] == APPLIED

    def test_review_then_reject(self):
        exe = Executor(dry_run=True)
        env = build_envelope("fix this error in the code")
        result = exe.execute(env)
        result = exe.apply_review_feedback(env, result, "reject", reason="No")
        assert result["review_state"] == REJECTED

    def test_review_then_revision_then_approve(self):
        exe = Executor(dry_run=True)
        env = build_envelope("fix this error in the code")
        result = exe.execute(env)
        # Request revision
        result = exe.apply_review_feedback(env, result, "request_revision")
        assert result["review_state"] == REVISED
        # Submit revision via orchestrator directly
        from src.pep.review_orchestrator import ReviewOrchestrator
        orch = ReviewOrchestrator()
        orch.submit_revision(result["_rsm"])
        # Now approve
        result = exe.apply_review_feedback(env, result, "approve")
        assert result["review_state"] == APPLIED

    def test_approve_triggers_writeback(self, tmp_path):
        from src.pep.writeback_engine import WritebackEngine
        engine = WritebackEngine(base_dir=tmp_path)
        exe = Executor(dry_run=False, writeback_engine=engine)
        env = build_envelope("fix this error in the code")
        result = exe.execute(env)
        assert result["review_state"] == WAITING_REVIEW
        assert "writeback_plans" not in result
        # Now approve → should trigger writeback
        result = exe.apply_review_feedback(env, result, "approve")
        assert result["review_state"] == APPLIED
        assert "writeback_plans" in result
        # Verify file written
        wb_dir = tmp_path / ".codex" / "writebacks"
        assert wb_dir.exists()

    def test_reject_no_writeback(self, tmp_path):
        from src.pep.writeback_engine import WritebackEngine
        engine = WritebackEngine(base_dir=tmp_path)
        exe = Executor(dry_run=False, writeback_engine=engine)
        env = build_envelope("fix this error in the code")
        result = exe.execute(env)
        result = exe.apply_review_feedback(env, result, "reject")
        assert "writeback_plans" not in result

    def test_no_rsm_returns_error(self):
        exe = Executor(dry_run=True)
        env = build_envelope("当前状态是什么")
        result = {"envelope_id": "test"}  # no _rsm
        fb = exe.apply_review_feedback(env, result, "approve")
        assert "error" in fb

    def test_rejection_notification_via_executor(self):
        stub = StubNotifier()
        exe = Executor(dry_run=True, escalation_notifier=stub)
        env = build_envelope("fix this error in the code")
        result = exe.execute(env)
        result = exe.apply_review_feedback(env, result, "reject", reason="Bad")
        assert "feedback_notification" in result
        assert result["feedback_notification"]["type"] == "rejection"
        assert len(stub.notifications) >= 1
