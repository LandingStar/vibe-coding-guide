"""Tests for PEP ↔ Review State Machine integration (Phase 11 Slice B)."""

from __future__ import annotations

import pytest

from src.pep.executor import Executor
from src.pdp.decision_envelope import build_envelope
from src.review.state_machine import APPLIED, PROPOSED, WAITING_REVIEW


# ── Helpers ─────────────────────────────────────────────

def _make_executor(**kwargs) -> Executor:
    return Executor(dry_run=True, **kwargs)


def _envelope_for(text: str, **kw) -> dict:
    return build_envelope(text, **kw)


# ── Inform gate → fast-path (proposed → applied) ───────

class TestInformReviewState:
    def test_inform_review_state_is_applied(self):
        exe = _make_executor()
        env = _envelope_for("当前状态是什么")
        result = exe.execute(env)
        assert result["review_state"] == APPLIED

    def test_inform_review_history_single_entry(self):
        exe = _make_executor()
        env = _envelope_for("当前状态是什么")
        result = exe.execute(env)
        assert len(result["review_history"]) == 1
        entry = result["review_history"][0]
        assert entry["from_state"] == PROPOSED
        assert entry["to_state"] == APPLIED
        assert entry["gate_level"] == "inform"


# ── Review gate → waiting_review ───────────────────────

class TestReviewGateReviewState:
    def test_review_gate_state_is_waiting_review(self):
        exe = _make_executor()
        # "fix" triggers correction intent → medium impact → review gate
        env = _envelope_for("fix this error in the code")
        result = exe.execute(env)
        assert result["review_state"] == WAITING_REVIEW

    def test_review_gate_history_has_submit(self):
        exe = _make_executor()
        env = _envelope_for("fix this error in the code")
        result = exe.execute(env)
        assert any(
            h["event"] == "submit_for_review" for h in result["review_history"]
        )


# ── Approve gate → waiting_review ──────────────────────

class TestApproveGateReviewState:
    def test_approve_gate_state_is_waiting_review(self):
        exe = _make_executor()
        env = _envelope_for("scope change request")
        result = exe.execute(env)
        assert result["review_state"] == WAITING_REVIEW


# ── Delegation with completed report → applied ─────────

class TestDelegationReviewState:
    def test_completed_delegation_review_applied(self):
        from src.subagent import contract_factory, report_validator
        from src.subagent.stub_worker import StubWorkerBackend

        exe = Executor(
            dry_run=True,
            worker=StubWorkerBackend(),
            contract_factory=contract_factory,
            report_validator=report_validator,
        )
        # "fix this error" → correction → delegatable
        env = _envelope_for("fix this error in the code")
        result = exe.execute(env)
        assert result["review_state"] == APPLIED
        # History should have 3 transitions: submit → approve → apply
        review_events = [h["event"] for h in result["review_history"]]
        assert "submit_for_review" in review_events
        assert "approve" in review_events
        assert "apply" in review_events

    def test_delegation_without_worker_stays_waiting(self):
        exe = _make_executor()
        # correction is delegatable but no worker → falls back to queue-for-review
        env = _envelope_for("fix this error in the code")
        result = exe.execute(env)
        # No worker configured → falls back to waiting_review
        assert result["review_state"] == WAITING_REVIEW


# ── review_history gate_level matches envelope ─────────

class TestReviewHistoryGateLevel:
    def test_gate_level_propagated(self):
        exe = _make_executor()
        env = _envelope_for("当前状态是什么")
        result = exe.execute(env)
        for entry in result["review_history"]:
            assert entry["gate_level"] == "inform"
