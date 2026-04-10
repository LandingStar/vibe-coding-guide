"""E2E governance flow tests and FeedbackAPI tests (Phase 14 Slice B).

Covers complete governance paths:
1. question → inform → applied (fast path)
2. correction → review → approve → applied → writeback
3. scope-change → approve → escalation → reject → terminal
4. correction → review → revision → resubmit → approve → applied
5. delegation → contract → worker → report → auto-apply
Plus FeedbackAPI external reviewer entry point tests.
"""

from __future__ import annotations

import pytest

from src.pdp.decision_envelope import build_envelope
from src.pep.executor import Executor
from src.pep.stub_notifier import StubNotifier
from src.pep.writeback_engine import WritebackEngine
from src.review.feedback_api import FeedbackAPI
from src.review.state_machine import (
    APPLIED,
    REJECTED,
    REVISED,
    WAITING_REVIEW,
)


# ── E2E Governance Paths ──────────────────────────────

class TestE2EInformFastPath:
    """question → inform → applied."""

    def test_question_fast_path(self):
        exe = Executor(dry_run=True)
        env = build_envelope("what is the current status?")
        result = exe.execute(env)

        assert env["intent_result"]["intent"] == "question"
        assert env["gate_decision"]["gate_level"] == "inform"
        assert result["review_state"] == APPLIED
        assert len(result["review_history"]) >= 1

    def test_question_no_delegation(self):
        env = build_envelope("what is the current status?")
        assert "delegation_decision" not in env


class TestE2EReviewApproveWriteback:
    """correction → review → waiting_review → approve → applied → writeback."""

    def test_full_review_to_writeback(self, tmp_path):
        engine = WritebackEngine(base_dir=tmp_path)
        exe = Executor(dry_run=False, writeback_engine=engine)
        env = build_envelope("fix this error in the code")

        # Step 1: Execute — should enter waiting_review
        result = exe.execute(env)
        assert env["intent_result"]["intent"] == "correction"
        assert env["gate_decision"]["gate_level"] == "review"
        assert result["review_state"] == WAITING_REVIEW
        assert "writeback_plans" not in result  # no writeback yet

        # Step 2: Approve — should transition to applied + trigger writeback
        result = exe.apply_review_feedback(env, result, "approve", reason="Looks good")
        assert result["review_state"] == APPLIED
        assert "writeback_plans" in result
        assert len(result["writeback_plans"]) > 0

        # Step 3: Verify file written
        wb_dir = tmp_path / ".codex" / "writebacks"
        assert wb_dir.exists()
        files = list(wb_dir.iterdir())
        assert len(files) == 1


class TestE2EApproveEscalationReject:
    """scope-change → approve gate → escalation → reject → terminal."""

    def test_scope_change_escalation_reject(self):
        stub = StubNotifier()
        exe = Executor(dry_run=True, escalation_notifier=stub)
        env = build_envelope("change scope to include new module")

        # Step 1: Execute — scope-change has high impact → approve gate
        result = exe.execute(env)
        assert env["intent_result"]["intent"] == "scope-change"
        assert env["gate_decision"]["gate_level"] == "approve"
        assert result["review_state"] == WAITING_REVIEW

        # Escalation should have been triggered (high_impact)
        assert "escalation_decision" in env
        assert env["escalation_decision"]["escalate"] is True

        # Step 2: Reject
        result = exe.apply_review_feedback(env, result, "reject", reason="Too risky")
        assert result["review_state"] == REJECTED

        # Should have rejection notification
        assert "feedback_notification" in result
        assert result["feedback_notification"]["type"] == "rejection"


class TestE2ERevisionCycle:
    """correction → review → request_revision → revise → resubmit → approve → applied."""

    def test_revision_then_approve(self):
        exe = Executor(dry_run=True)
        env = build_envelope("fix this error in the code")
        result = exe.execute(env)

        assert result["review_state"] == WAITING_REVIEW

        # Step 1: Reviewer requests revision
        result = exe.apply_review_feedback(
            env, result, "request_revision", reason="Add tests",
        )
        assert result["review_state"] == REVISED

        # Step 2: Author submits revision via orchestrator
        from src.pep.review_orchestrator import ReviewOrchestrator
        orch = ReviewOrchestrator()
        orch.submit_revision(result["_rsm"], reason="Tests added")
        assert result["_rsm"].current_state == WAITING_REVIEW

        # Step 3: Reviewer approves
        result = exe.apply_review_feedback(env, result, "approve", reason="OK now")
        assert result["review_state"] == APPLIED

    def test_revision_cycle_history_depth(self):
        """Verify audit trail captures all transitions."""
        exe = Executor(dry_run=True)
        env = build_envelope("fix this error in the code")
        result = exe.execute(env)

        # revision → revise → resubmit → approve → apply
        result = exe.apply_review_feedback(env, result, "request_revision")
        from src.pep.review_orchestrator import ReviewOrchestrator
        orch = ReviewOrchestrator()
        orch.submit_revision(result["_rsm"])
        result = exe.apply_review_feedback(env, result, "approve")

        # History: submit_for_review → request_revision → revise → submit_for_review → approve → apply
        assert len(result["review_history"]) >= 6


class TestE2EDelegation:
    """delegation → contract → worker → report → auto-apply."""

    def test_delegation_auto_apply(self):
        """With full subagent pipeline, delegation auto-applies."""
        from src.subagent import contract_factory, report_validator
        from src.subagent.stub_worker import StubWorkerBackend

        worker = StubWorkerBackend()
        exe = Executor(
            dry_run=True,
            worker=worker,
            contract_factory=contract_factory,
            report_validator=report_validator,
        )
        env = build_envelope("fix this error in the code")

        # correction → delegatable → delegate=True
        assert "delegation_decision" in env
        assert env["delegation_decision"]["delegate"] is True

        result = exe.execute(env)

        # Delegation with completed report → auto-apply
        assert result["review_state"] == APPLIED
        assert "contract" in result
        assert "report" in result

    def test_delegation_without_worker_falls_back(self):
        """Without worker, delegation falls back to review."""
        exe = Executor(dry_run=True)
        env = build_envelope("fix this error in the code")

        # delegation_decision exists but no worker configured
        assert "delegation_decision" in env
        result = exe.execute(env)
        assert result["review_state"] == WAITING_REVIEW


# ── FeedbackAPI Tests ──────────────────────────────────

class TestFeedbackAPI:
    def test_register_and_list_pending(self):
        exe = Executor(dry_run=True)
        api = FeedbackAPI(exe)

        env = build_envelope("fix this error in the code")
        result = exe.execute(env)
        api.register(env, result)

        pending = api.list_pending()
        assert len(pending) == 1
        assert pending[0]["review_state"] == "waiting_review"

    def test_submit_approve(self):
        exe = Executor(dry_run=True)
        api = FeedbackAPI(exe)

        env = build_envelope("fix this error in the code")
        result = exe.execute(env)
        api.register(env, result)

        eid = result["envelope_id"]
        updated = api.submit(eid, "approve", reason="LGTM")
        assert updated["review_state"] == APPLIED

        # Should no longer be pending
        assert len(api.list_pending()) == 0

    def test_submit_reject(self):
        exe = Executor(dry_run=True)
        api = FeedbackAPI(exe)

        env = build_envelope("fix this error in the code")
        result = exe.execute(env)
        api.register(env, result)

        eid = result["envelope_id"]
        updated = api.submit(eid, "reject", reason="No")
        assert updated["review_state"] == REJECTED

    def test_submit_unknown_envelope(self):
        exe = Executor(dry_run=True)
        api = FeedbackAPI(exe)
        result = api.submit("nonexistent-id", "approve")
        assert "error" in result

    def test_get_result(self):
        exe = Executor(dry_run=True)
        api = FeedbackAPI(exe)

        env = build_envelope("fix this error in the code")
        result = exe.execute(env)
        api.register(env, result)

        eid = result["envelope_id"]
        stored = api.get_result(eid)
        assert stored is not None
        assert stored["envelope_id"] == eid

    def test_get_result_not_found(self):
        exe = Executor(dry_run=True)
        api = FeedbackAPI(exe)
        assert api.get_result("nope") is None

    def test_feedback_with_writeback(self, tmp_path):
        engine = WritebackEngine(base_dir=tmp_path)
        exe = Executor(dry_run=False, writeback_engine=engine)
        api = FeedbackAPI(exe)

        env = build_envelope("fix this error in the code")
        result = exe.execute(env)
        api.register(env, result)

        eid = result["envelope_id"]
        updated = api.submit(eid, "approve")
        assert updated["review_state"] == APPLIED
        assert "writeback_plans" in updated

    def test_register_requires_envelope_id(self):
        exe = Executor(dry_run=True)
        api = FeedbackAPI(exe)
        with pytest.raises(ValueError):
            api.register({}, {})

    def test_multiple_envelopes(self):
        exe = Executor(dry_run=True)
        api = FeedbackAPI(exe)

        env1 = build_envelope("fix this error in the code")
        res1 = exe.execute(env1)
        api.register(env1, res1)

        env2 = build_envelope("fix this bug immediately")
        res2 = exe.execute(env2)
        api.register(env2, res2)

        pending = api.list_pending()
        assert len(pending) == 2

        # Approve first, second still pending
        api.submit(res1["envelope_id"], "approve")
        assert len(api.list_pending()) == 1
