"""Reviewer feedback API — external entry point for review decisions.

Provides a programmatic interface for human reviewers or external
systems to submit approve/reject/revision feedback to envelopes
that are in ``waiting_review`` state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.pep.executor import Executor


class FeedbackAPI:
    """Submit reviewer feedback to previously executed envelopes.

    Maintains an in-memory store mapping ``envelope_id`` to
    ``(envelope, result)`` pairs.  Each ``execute()`` call on the
    associated :class:`Executor` should be followed by
    :meth:`register` so that feedback can be applied later.

    Example::

        api = FeedbackAPI(executor)
        result = executor.execute(envelope)
        api.register(envelope, result)
        # Later, reviewer submits feedback:
        fb = api.submit("pdp-abc123", "approve", reason="LGTM")
    """

    def __init__(self, executor: Executor) -> None:
        self._executor = executor
        self._store: dict[str, tuple[dict, dict]] = {}

    def register(self, envelope: dict, result: dict) -> None:
        """Store an executed envelope/result pair for later feedback."""
        envelope_id = result.get("envelope_id") or envelope.get("decision_id", "")
        if not envelope_id:
            raise ValueError("Cannot register: no envelope_id found.")
        self._store[envelope_id] = (envelope, result)

    def list_pending(self) -> list[dict]:
        """Return summaries of all envelopes in ``waiting_review``."""
        pending = []
        for eid, (env, res) in self._store.items():
            if res.get("review_state") == "waiting_review":
                pending.append({
                    "envelope_id": eid,
                    "intent": env.get("intent_result", {}).get("intent", "unknown"),
                    "gate_level": env.get("gate_decision", {}).get("gate_level", "unknown"),
                    "review_state": res.get("review_state"),
                })
        return pending

    def submit(
        self,
        envelope_id: str,
        feedback: str,
        *,
        reason: str = "",
    ) -> dict:
        """Submit feedback for the given envelope.

        Parameters
        ----------
        envelope_id:
            The decision_id of the envelope to review.
        feedback:
            One of ``"approve"``, ``"reject"``, ``"request_revision"``.
        reason:
            Human-provided rationale.

        Returns
        -------
        dict
            Updated execution result with new ``review_state``.
        """
        entry = self._store.get(envelope_id)
        if entry is None:
            return {"error": f"Envelope not found: {envelope_id}"}

        envelope, result = entry
        updated = self._executor.apply_review_feedback(
            envelope, result, feedback, reason=reason,
        )
        # Update stored result
        self._store[envelope_id] = (envelope, updated)
        return updated

    def get_result(self, envelope_id: str) -> dict | None:
        """Return the current result for an envelope, or None."""
        entry = self._store.get(envelope_id)
        return entry[1] if entry else None
