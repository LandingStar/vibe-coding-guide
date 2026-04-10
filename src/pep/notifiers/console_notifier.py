"""Console notifier — prints notifications to stdout."""

from __future__ import annotations

import json
import sys


class ConsoleNotifier:
    """EscalationNotifier that prints to stdout (for dev/debug)."""

    def __init__(self, *, stream=None) -> None:
        self._stream = stream or sys.stdout

    def notify(self, notification: dict) -> dict:
        output = json.dumps(notification, indent=2, ensure_ascii=False)
        self._stream.write(f"[NOTIFICATION] {output}\n")
        return {
            "delivered": True,
            "channel": "console",
        }
