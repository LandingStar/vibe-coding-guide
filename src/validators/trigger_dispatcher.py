"""Simple event-based trigger dispatcher."""

from __future__ import annotations

from .base import Trigger, TriggerResult


class TriggerDispatcher:
    """Route events to registered Trigger handlers by event type."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[Trigger]] = {}

    def register(self, event_type: str, trigger: Trigger) -> None:
        self._handlers.setdefault(event_type, []).append(trigger)

    def dispatch(self, event: dict) -> list[TriggerResult]:
        """Dispatch *event* to all handlers registered for its ``type``.

        Returns a list of TriggerResult, one per handler invoked.
        If no handlers match, returns an empty list.
        """
        event_type = event.get("type", "")
        handlers = self._handlers.get(event_type, [])
        return [h.handle(event) for h in handlers]

    def list_event_types(self) -> list[str]:
        return list(self._handlers)
