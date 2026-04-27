"""Runtime models for orchestration bridge primitives."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

BridgeWorkLifecycle = Literal[
    "queued",
    "dispatching",
    "waiting_governance_result",
    "waiting_external_resolution",
    "completed",
    "blocked",
]

BridgeGroupLifecycle = Literal["prepared", "dispatched", "settled"]

GovernanceSurfaceKind = Literal["none", "grouped_review", "group_terminal", "blocked"]

GovernanceSurfaceState = Literal[
    "",
    "all_clear",
    "review_required",
    "escalation",
    "handoff",
    "blocked",
]

WritebackDisposition = Literal["pending", "eligible", "suppressed", "blocked", "none"]


@dataclass(frozen=True, slots=True)
class BridgeGroupItem:
    """Runtime model for a single executor-local group wrapper."""

    group_item_id: str
    work_item_id: str
    task_group_id: str | None = None
    child_task_ids: tuple[str, ...] = ()
    latest_envelope_id: str | None = None
    latest_trace_id: str | None = None
    lifecycle_state: BridgeGroupLifecycle = "prepared"
    governance_surface_kind: GovernanceSurfaceKind = "none"
    governance_surface_state: GovernanceSurfaceState = ""
    blocked_reason: str = ""
    authoritative_refs: tuple[str, ...] = ()
    open_items: tuple[str, ...] = ()
    current_gate_state: str = ""
    writeback_disposition: WritebackDisposition = "pending"


@dataclass(frozen=True, slots=True)
class BridgeWorkItem:
    """Runtime model for a bridge-owned orchestration work item."""

    work_item_id: str
    source_envelope_id: str
    scope_summary: str
    source_trace_id: str | None = None
    dependency_ids: tuple[str, ...] = ()
    group_item_ids: tuple[str, ...] = ()
    lifecycle_state: BridgeWorkLifecycle = "queued"
    blocked_reason: str = ""
    rollup_surface_kind: GovernanceSurfaceKind = "none"
    rollup_surface_state: GovernanceSurfaceState = ""
    rollup_blocked_reason: str = ""
    rollup_writeback_disposition: WritebackDisposition = "pending"
    dominant_group_item_ids: tuple[str, ...] = ()
    open_group_item_count: int = 0