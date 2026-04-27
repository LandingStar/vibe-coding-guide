"""Stop-condition evaluator for orchestration bridge work items."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .models import BridgeWorkItem, BridgeWorkLifecycle

StopBoundaryKind = Literal[
    "continue_waiting",
    "wait_external_resolution",
    "completed",
    "blocked",
    "inconsistent",
]


@dataclass(frozen=True, slots=True)
class StopConditionDecision:
    """Pure stop-condition decision returned by the evaluator."""

    boundary_kind: StopBoundaryKind
    next_lifecycle_state: BridgeWorkLifecycle
    reason: str = ""


def evaluate_stop_condition(work_item: BridgeWorkItem) -> StopConditionDecision:
    """Evaluate bridge stop-condition from the work-item roll-up only."""

    if (
        work_item.rollup_surface_kind == "none"
        and work_item.dominant_group_item_ids
    ):
        return StopConditionDecision(
            boundary_kind="inconsistent",
            next_lifecycle_state=work_item.lifecycle_state,
            reason="inconsistent_rollup_state",
        )

    if work_item.rollup_surface_kind == "group_terminal" and work_item.rollup_surface_state not in (
        "escalation",
        "handoff",
    ):
        return StopConditionDecision(
            boundary_kind="inconsistent",
            next_lifecycle_state=work_item.lifecycle_state,
            reason="inconsistent_rollup_state",
        )

    if (
        work_item.open_group_item_count == 0
        and work_item.rollup_writeback_disposition == "pending"
        and work_item.rollup_surface_kind not in ("blocked", "group_terminal")
        and not (
            work_item.rollup_surface_kind == "grouped_review"
            and work_item.rollup_surface_state == "review_required"
        )
    ):
        return StopConditionDecision(
            boundary_kind="inconsistent",
            next_lifecycle_state=work_item.lifecycle_state,
            reason="inconsistent_rollup_state",
        )

    if work_item.rollup_surface_kind == "blocked":
        return StopConditionDecision(
            boundary_kind="blocked",
            next_lifecycle_state="blocked",
            reason=work_item.rollup_blocked_reason or "blocked",
        )

    if work_item.rollup_surface_kind == "group_terminal":
        return StopConditionDecision(
            boundary_kind="wait_external_resolution",
            next_lifecycle_state="waiting_external_resolution",
            reason=work_item.rollup_blocked_reason or work_item.rollup_surface_state,
        )

    if (
        work_item.rollup_surface_kind == "grouped_review"
        and work_item.rollup_surface_state == "review_required"
    ):
        return StopConditionDecision(
            boundary_kind="wait_external_resolution",
            next_lifecycle_state="waiting_external_resolution",
            reason="review_required",
        )

    if work_item.open_group_item_count > 0:
        return StopConditionDecision(
            boundary_kind="continue_waiting",
            next_lifecycle_state=_waiting_lifecycle_state(work_item),
            reason="",
        )

    if work_item.rollup_writeback_disposition in ("eligible", "none") and work_item.rollup_surface_kind not in (
        "blocked",
        "group_terminal",
    ):
        return StopConditionDecision(
            boundary_kind="completed",
            next_lifecycle_state="completed",
            reason="",
        )

    return StopConditionDecision(
        boundary_kind="inconsistent",
        next_lifecycle_state=work_item.lifecycle_state,
        reason="inconsistent_rollup_state",
    )


def _waiting_lifecycle_state(work_item: BridgeWorkItem) -> BridgeWorkLifecycle:
    if work_item.lifecycle_state in ("dispatching", "waiting_governance_result"):
        return work_item.lifecycle_state
    return "waiting_governance_result"