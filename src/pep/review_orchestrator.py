"""Review orchestrator — drive reviewer feedback through the state machine.

Handles approve, reject, and request_revision feedback events,
including the revision → re-submit cycle.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.review.state_machine import (
    APPLY,
    APPROVE,
    REJECT,
    REQUEST_REVISION,
    REVISE,
    SUBMIT_FOR_REVIEW,
    ReviewStateMachine,
)

if TYPE_CHECKING:
    from src.interfaces import EscalationNotifier


class ReviewOrchestrator:
    """Accept reviewer feedback and drive the review state machine.

    Optionally sends notifications on rejection and revision requests.
    """

    def __init__(
        self,
        *,
        notifier: EscalationNotifier | None = None,
    ) -> None:
        self._notifier = notifier

    def submit_feedback(
        self,
        rsm: ReviewStateMachine,
        feedback: str,
        *,
        reason: str = "",
        auto_apply: bool = True,
    ) -> dict:
        """Apply reviewer *feedback* to the state machine.

        Parameters
        ----------
        rsm : ReviewStateMachine
            The review state machine (should be in ``waiting_review``).
        feedback : str
            One of ``"approve"``, ``"reject"``, ``"request_revision"``.
        reason : str
            Human-provided reason for the feedback.
        auto_apply : bool
            If True and feedback is "approve", automatically transition
            to ``applied`` after approval.

        Returns
        -------
        dict
            Result with ``review_state``, ``review_history``, and
            optional ``notification`` fields.
        """
        if feedback == "approve":
            return self._handle_approve(rsm, reason, auto_apply=auto_apply)
        elif feedback == "reject":
            return self._handle_reject(rsm, reason)
        elif feedback == "request_revision":
            return self._handle_revision(rsm, reason)
        else:
            return {
                "review_state": rsm.current_state,
                "review_history": rsm.history,
                "error": f"Unknown feedback: {feedback}",
            }

    def submit_revision(
        self,
        rsm: ReviewStateMachine,
        *,
        reason: str = "",
    ) -> dict:
        """Submit revised content back for review.

        Transitions: revised → proposed (via REVISE), then
        proposed → waiting_review (via SUBMIT_FOR_REVIEW).
        """
        rsm.transition(REVISE, reason=reason or "Revision submitted")
        rsm.transition(SUBMIT_FOR_REVIEW, reason="Re-submitted after revision")
        return {
            "review_state": rsm.current_state,
            "review_history": rsm.history,
        }

    # ── Internal handlers ──────────────────────────────

    def _handle_approve(
        self, rsm: ReviewStateMachine, reason: str, *, auto_apply: bool,
    ) -> dict:
        rsm.transition(APPROVE, reason=reason or "Approved by reviewer")
        if auto_apply:
            rsm.transition(APPLY, reason="Auto-apply after approval")
        return {
            "review_state": rsm.current_state,
            "review_history": rsm.history,
        }

    def _handle_reject(self, rsm: ReviewStateMachine, reason: str) -> dict:
        rsm.transition(REJECT, reason=reason or "Rejected by reviewer")
        result: dict = {
            "review_state": rsm.current_state,
            "review_history": rsm.history,
        }
        if self._notifier:
            notification = {
                "type": "rejection",
                "object_id": rsm.object_id,
                "reason": reason,
                "review_state": rsm.current_state,
            }
            delivery = self._notifier.notify(notification)
            result["notification"] = notification
            result["notification_delivery"] = delivery
        return result

    def _handle_revision(self, rsm: ReviewStateMachine, reason: str) -> dict:
        rsm.transition(REQUEST_REVISION, reason=reason or "Revision requested")
        result: dict = {
            "review_state": rsm.current_state,
            "review_history": rsm.history,
        }
        if self._notifier:
            notification = {
                "type": "revision_request",
                "object_id": rsm.object_id,
                "reason": reason,
                "review_state": rsm.current_state,
                "action_required": "Revise and re-submit",
            }
            delivery = self._notifier.notify(notification)
            result["notification"] = notification
            result["notification_delivery"] = delivery
        return result
