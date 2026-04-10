"""Trace context — correlation IDs for cross-phase audit trails."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class TraceContext:
    """Immutable trace identifier that flows through PDP → PEP → writeback."""

    trace_id: str
    parent_trace_id: str | None = None
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def new_trace() -> TraceContext:
    """Create a new root trace context."""
    return TraceContext(trace_id=f"trace-{uuid.uuid4().hex[:12]}")


def child_trace(parent: TraceContext) -> TraceContext:
    """Create a child trace linked to a parent."""
    return TraceContext(
        trace_id=f"trace-{uuid.uuid4().hex[:12]}",
        parent_trace_id=parent.trace_id,
    )
