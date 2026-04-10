"""Stub EscalationNotifier for testing.

Records notifications to an in-memory list instead of sending them
through a real channel.
"""

from __future__ import annotations


class StubNotifier:
    """Minimal EscalationNotifier that records to memory."""

    def __init__(self) -> None:
        self.notifications: list[dict] = []

    def notify(self, notification: dict) -> dict:
        self.notifications.append(notification)
        return {
            "delivered": True,
            "channel": "stub-memory",
        }
