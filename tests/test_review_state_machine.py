"""Tests for Review State Machine engine (Phase 11 Slice A)."""

from __future__ import annotations

import pytest

from src.review.state_machine import (
    ALL_EVENTS,
    ALL_STATES,
    APPLIED,
    APPROVE,
    APPROVED,
    APPLY,
    InvalidTransitionError,
    PROPOSED,
    PROPOSE,
    REJECT,
    REJECTED,
    REQUEST_REVISION,
    REVISED,
    REVISE,
    ReviewStateMachine,
    SUBMIT_FOR_REVIEW,
    WAITING_REVIEW,
)


class TestStateConstants:
    def test_six_states(self):
        assert len(ALL_STATES) == 6

    def test_seven_events(self):
        assert len(ALL_EVENTS) == 7


class TestCoreTransitions:
    """Test all 8 transition rules from review-state-machine.md."""

    def test_proposed_to_waiting_review(self):
        sm = ReviewStateMachine()
        assert sm.transition(SUBMIT_FOR_REVIEW) == WAITING_REVIEW

    def test_waiting_review_to_approved(self):
        sm = ReviewStateMachine()
        sm.transition(SUBMIT_FOR_REVIEW)
        assert sm.transition(APPROVE) == APPROVED

    def test_waiting_review_to_rejected(self):
        sm = ReviewStateMachine()
        sm.transition(SUBMIT_FOR_REVIEW)
        assert sm.transition(REJECT) == REJECTED

    def test_waiting_review_to_revised(self):
        sm = ReviewStateMachine()
        sm.transition(SUBMIT_FOR_REVIEW)
        assert sm.transition(REQUEST_REVISION) == REVISED

    def test_revised_to_proposed(self):
        sm = ReviewStateMachine()
        sm.transition(SUBMIT_FOR_REVIEW)
        sm.transition(REQUEST_REVISION)
        assert sm.transition(REVISE) == PROPOSED

    def test_approved_to_applied(self):
        sm = ReviewStateMachine()
        sm.transition(SUBMIT_FOR_REVIEW)
        sm.transition(APPROVE)
        assert sm.transition(APPLY) == APPLIED

    def test_inform_fast_path(self):
        """proposed → applied directly (inform gate)."""
        sm = ReviewStateMachine(gate_level="inform")
        assert sm.transition(APPLY) == APPLIED

    def test_full_happy_path(self):
        """proposed → waiting_review → approved → applied."""
        sm = ReviewStateMachine(object_id="test-obj")
        sm.transition(SUBMIT_FOR_REVIEW, reason="Ready for review")
        sm.transition(APPROVE, reason="Looks good")
        sm.transition(APPLY, reason="Applying changes")
        assert sm.current_state == APPLIED
        assert len(sm.history) == 3


class TestRevisionCycle:
    def test_revision_loop(self):
        """revised → proposed → waiting_review → approved → applied."""
        sm = ReviewStateMachine()
        sm.transition(SUBMIT_FOR_REVIEW)
        sm.transition(REQUEST_REVISION)
        sm.transition(REVISE)
        # Now back to proposed
        assert sm.current_state == PROPOSED
        sm.transition(SUBMIT_FOR_REVIEW)
        sm.transition(APPROVE)
        sm.transition(APPLY)
        assert sm.current_state == APPLIED
        assert len(sm.history) == 6


class TestInvalidTransitions:
    def test_cannot_approve_from_proposed(self):
        sm = ReviewStateMachine()
        with pytest.raises(InvalidTransitionError) as exc:
            sm.transition(APPROVE)
        assert exc.value.state == PROPOSED
        assert exc.value.event == APPROVE

    def test_cannot_reject_from_proposed(self):
        sm = ReviewStateMachine()
        with pytest.raises(InvalidTransitionError):
            sm.transition(REJECT)

    def test_cannot_apply_from_waiting_review(self):
        sm = ReviewStateMachine()
        sm.transition(SUBMIT_FOR_REVIEW)
        with pytest.raises(InvalidTransitionError):
            sm.transition(APPLY)

    def test_cannot_submit_from_approved(self):
        sm = ReviewStateMachine()
        sm.transition(SUBMIT_FOR_REVIEW)
        sm.transition(APPROVE)
        with pytest.raises(InvalidTransitionError):
            sm.transition(SUBMIT_FOR_REVIEW)

    def test_cannot_revise_from_proposed(self):
        sm = ReviewStateMachine()
        with pytest.raises(InvalidTransitionError):
            sm.transition(REVISE)

    def test_rejected_is_terminal(self):
        sm = ReviewStateMachine()
        sm.transition(SUBMIT_FOR_REVIEW)
        sm.transition(REJECT)
        with pytest.raises(InvalidTransitionError):
            sm.transition(SUBMIT_FOR_REVIEW)

    def test_applied_is_terminal(self):
        sm = ReviewStateMachine()
        sm.transition(APPLY)
        with pytest.raises(InvalidTransitionError):
            sm.transition(SUBMIT_FOR_REVIEW)


class TestAuditTrail:
    def test_history_structure(self):
        sm = ReviewStateMachine(object_id="obj-1", gate_level="review")
        sm.transition(SUBMIT_FOR_REVIEW, reason="Testing")
        assert len(sm.history) == 1
        entry = sm.history[0]
        assert entry["object_id"] == "obj-1"
        assert entry["from_state"] == PROPOSED
        assert entry["event"] == SUBMIT_FOR_REVIEW
        assert entry["to_state"] == WAITING_REVIEW
        assert entry["reason"] == "Testing"
        assert entry["gate_level"] == "review"
        assert "timestamp" in entry

    def test_history_is_copy(self):
        sm = ReviewStateMachine()
        sm.transition(SUBMIT_FOR_REVIEW)
        h = sm.history
        h.clear()
        assert len(sm.history) == 1  # original unchanged


class TestAllowedEvents:
    def test_proposed_allowed(self):
        sm = ReviewStateMachine()
        allowed = sm.allowed_events()
        assert SUBMIT_FOR_REVIEW in allowed
        assert APPLY in allowed  # inform fast path

    def test_waiting_review_allowed(self):
        sm = ReviewStateMachine()
        sm.transition(SUBMIT_FOR_REVIEW)
        allowed = sm.allowed_events()
        assert APPROVE in allowed
        assert REJECT in allowed
        assert REQUEST_REVISION in allowed

    def test_approved_allowed(self):
        sm = ReviewStateMachine()
        sm.transition(SUBMIT_FOR_REVIEW)
        sm.transition(APPROVE)
        allowed = sm.allowed_events()
        assert allowed == [APPLY]

    def test_rejected_no_events(self):
        sm = ReviewStateMachine()
        sm.transition(SUBMIT_FOR_REVIEW)
        sm.transition(REJECT)
        assert sm.allowed_events() == []


class TestInitialization:
    def test_default_state(self):
        sm = ReviewStateMachine()
        assert sm.current_state == PROPOSED

    def test_custom_initial_state(self):
        sm = ReviewStateMachine(initial_state=WAITING_REVIEW)
        assert sm.current_state == WAITING_REVIEW

    def test_invalid_initial_state(self):
        with pytest.raises(ValueError):
            ReviewStateMachine(initial_state="invalid")

    def test_auto_object_id(self):
        sm = ReviewStateMachine()
        assert sm.object_id.startswith("review-")
