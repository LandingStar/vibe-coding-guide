"""Structured action log for PEP execution records."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone


class ActionLog:
    """Append-only log of PEP execution actions."""

    def __init__(self) -> None:
        self._entries: list[dict] = []

    def record(self, action: str, detail: str, envelope_id: str) -> dict:
        entry = {
            "log_id": f"log-{uuid.uuid4().hex[:8]}",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "envelope_id": envelope_id,
            "action": action,
            "detail": detail,
        }
        self._entries.append(entry)
        return entry

    @property
    def entries(self) -> list[dict]:
        return list(self._entries)

    def to_json(self) -> list[dict]:
        return self.entries
