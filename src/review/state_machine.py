"""Review State Machine — 6 states, 7 events, 8 transition rules.

Implements the minimal review state machine defined in
``docs/review-state-machine.md``.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone


# ── States ──────────────────────────────────────────────

PROPOSED = "proposed"
WAITING_REVIEW = "waiting_review"
APPROVED = "approved"
REJECTED = "rejected"
REVISED = "revised"
APPLIED = "applied"

ALL_STATES = frozenset({PROPOSED, WAITING_REVIEW, APPROVED, REJECTED, REVISED, APPLIED})

# ── Events ──────────────────────────────────────────────

PROPOSE = "propose"
SUBMIT_FOR_REVIEW = "submit_for_review"
APPROVE = "approve"
REJECT = "reject"
REQUEST_REVISION = "request_revision"
REVISE = "revise"
APPLY = "apply"

ALL_EVENTS = frozenset({PROPOSE, SUBMIT_FOR_REVIEW, APPROVE, REJECT, REQUEST_REVISION, REVISE, APPLY})

# ── Transition table ───────────────────────────────────
# Key: (current_state, event) → new_state

_TRANSITIONS: dict[tuple[str, str], str] = {
    # Core transitions
    (PROPOSED, SUBMIT_FOR_REVIEW): WAITING_REVIEW,
    (WAITING_REVIEW, APPROVE): APPROVED,
    (WAITING_REVIEW, REJECT): REJECTED,
    (WAITING_REVIEW, REQUEST_REVISION): REVISED,
    (REVISED, REVISE): PROPOSED,
    (APPROVED, APPLY): APPLIED,
    # Inform fast-path: proposed → applied directly
    (PROPOSED, APPLY): APPLIED,
}


class InvalidTransitionError(Exception):
    """Raised when an event is not valid for the current state."""

    def __init__(self, state: str, event: str) -> None:
        self.state = state
        self.event = event
        super().__init__(
            f"Cannot apply event '{event}' in state '{state}'."
        )


class ReviewStateMachine:
    """Minimal review state machine with audit trail."""

    def __init__(
        self,
        object_id: str = "",
        initial_state: str = PROPOSED,
        gate_level: str | None = None,
    ) -> None:
        if initial_state not in ALL_STATES:
            raise ValueError(f"Invalid state: {initial_state}")
        self._state = initial_state
        self._object_id = object_id or f"review-{uuid.uuid4().hex[:8]}"
        self._gate_level = gate_level
        self._history: list[dict] = []

    @property
    def current_state(self) -> str:
        return self._state

    @property
    def object_id(self) -> str:
        return self._object_id

    @property
    def history(self) -> list[dict]:
        return list(self._history)

    def transition(self, event: str, *, reason: str = "") -> str:
        """Apply *event* and return the new state.

        Raises :class:`InvalidTransitionError` if the event is not
        valid for the current state.
        """
        key = (self._state, event)
        new_state = _TRANSITIONS.get(key)
        if new_state is None:
            raise InvalidTransitionError(self._state, event)

        record = {
            "object_id": self._object_id,
            "from_state": self._state,
            "event": event,
            "to_state": new_state,
            "reason": reason,
            "gate_level": self._gate_level,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._history.append(record)
        self._state = new_state
        return new_state

    def allowed_events(self) -> list[str]:
        """Return events valid for the current state."""
        return [ev for (st, ev) in _TRANSITIONS if st == self._state]
