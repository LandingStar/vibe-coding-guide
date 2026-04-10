"""Audit logger — centralized event recording with pluggable backends."""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass
class AuditEvent:
    """A single audit event in the governance trace."""

    event_id: str
    trace_id: str
    timestamp: str
    event_type: str  # e.g. intent_classified, gate_resolved, ...
    phase: str  # pdp, pep, writeback
    detail: dict = field(default_factory=dict)
    parent_trace_id: str | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        if d["parent_trace_id"] is None:
            del d["parent_trace_id"]
        return d


# ── Backends ──────────────────────────────────────────────────────────────


@runtime_checkable
class AuditBackend(Protocol):
    """Protocol for audit event storage."""

    def emit(self, event: AuditEvent) -> None: ...

    def query(self, trace_id: str) -> list[AuditEvent]: ...


class MemoryAuditBackend:
    """In-memory audit backend (default for tests and lightweight usage)."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def emit(self, event: AuditEvent) -> None:
        self._events.append(event)

    def query(self, trace_id: str) -> list[AuditEvent]:
        return [e for e in self._events if e.trace_id == trace_id]

    @property
    def all_events(self) -> list[AuditEvent]:
        return list(self._events)


class FileAuditBackend:
    """JSON-lines file audit backend. Each line is one event."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, event: AuditEvent) -> None:
        with self._path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event.to_dict(), ensure_ascii=False) + "\n")

    def query(self, trace_id: str) -> list[AuditEvent]:
        if not self._path.exists():
            return []
        results: list[AuditEvent] = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            data = json.loads(line)
            if data.get("trace_id") == trace_id:
                results.append(AuditEvent(**{
                    k: data.get(k, None) for k in AuditEvent.__dataclass_fields__
                }))
        return results


# ── Logger ────────────────────────────────────────────────────────────────


class AuditLogger:
    """Central audit logger that dispatches events to one or more backends."""

    def __init__(self, *backends: AuditBackend) -> None:
        self._backends: list[AuditBackend] = list(backends)
        if not self._backends:
            self._backends.append(MemoryAuditBackend())

    def emit(
        self,
        event_type: str,
        phase: str,
        trace_id: str,
        detail: dict | None = None,
        parent_trace_id: str | None = None,
    ) -> AuditEvent:
        """Create and dispatch an audit event."""
        event = AuditEvent(
            event_id=f"evt-{uuid.uuid4().hex[:8]}",
            trace_id=trace_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            event_type=event_type,
            phase=phase,
            detail=detail or {},
            parent_trace_id=parent_trace_id,
        )
        for backend in self._backends:
            backend.emit(event)
        return event

    def query(self, trace_id: str) -> list[AuditEvent]:
        """Query events by trace_id from the first backend."""
        if self._backends:
            return self._backends[0].query(trace_id)
        return []

    @property
    def backends(self) -> list[AuditBackend]:
        return list(self._backends)
