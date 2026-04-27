"""Landing artifact helpers for orchestration external-resolution boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from .coordinator import CoordinatorAdvanceResult

BridgeLandingKind = Literal["handoff", "escalation", "reviewer_takeover"]


@dataclass(frozen=True, slots=True)
class BridgeLandingArtifact:
    """Minimal landing artifact emitted for external-resolution surfaces."""

    landing_kind: BridgeLandingKind
    work_item_id: str
    active_scope: str
    task_group_id: str | None = None
    dominant_group_item_ids: tuple[str, ...] = ()
    reason: str = ""
    authoritative_refs: tuple[str, ...] = ()
    open_items: tuple[str, ...] = ()
    current_gate_state: str = "waiting_review"
    intake_requirements: tuple[str, ...] = ()


def build_landing_artifact(
    advance_result: CoordinatorAdvanceResult,
) -> BridgeLandingArtifact | None:
    """Build a landing artifact when coordinator reaches external resolution."""

    if advance_result.decision.boundary_kind != "wait_external_resolution":
        return None

    dominant_group_items = tuple(
        group_item
        for group_item in advance_result.group_items
        if group_item.group_item_id in advance_result.work_item.dominant_group_item_ids
    )

    if (
        advance_result.work_item.rollup_surface_kind == "group_terminal"
        and advance_result.work_item.rollup_surface_state in ("handoff", "escalation")
    ):
        current_gate_state = _first_non_empty(
            item.current_gate_state for item in dominant_group_items
        ) or "waiting_review"
        return BridgeLandingArtifact(
            landing_kind=advance_result.work_item.rollup_surface_state,
            work_item_id=advance_result.work_item.work_item_id,
            active_scope=advance_result.work_item.scope_summary,
            task_group_id=_first_non_empty(item.task_group_id for item in dominant_group_items),
            dominant_group_item_ids=advance_result.work_item.dominant_group_item_ids,
            reason=advance_result.decision.reason,
            authoritative_refs=_merge_string_tuples(
                item.authoritative_refs for item in dominant_group_items
            )
            or ("AGENTS.md",),
            open_items=_merge_string_tuples(item.open_items for item in dominant_group_items),
            current_gate_state=current_gate_state,
            intake_requirements=(
                "Review authoritative_refs before proceeding",
                "Inspect dominant group items before taking over",
            ),
        )

    if (
        advance_result.work_item.rollup_surface_kind == "grouped_review"
        and advance_result.work_item.rollup_surface_state == "review_required"
    ):
        open_items = _merge_string_tuples(item.open_items for item in dominant_group_items)
        if not open_items:
            open_items = ("review_required",)
        return BridgeLandingArtifact(
            landing_kind="reviewer_takeover",
            work_item_id=advance_result.work_item.work_item_id,
            active_scope=advance_result.work_item.scope_summary,
            task_group_id=_first_non_empty(item.task_group_id for item in dominant_group_items),
            dominant_group_item_ids=advance_result.work_item.dominant_group_item_ids,
            reason=advance_result.decision.reason or "review_required",
            authoritative_refs=("AGENTS.md",),
            open_items=open_items,
            current_gate_state="waiting_review",
            intake_requirements=(
                "Review authoritative_refs before proceeding",
                "Review grouped review evidence before deciding",
            ),
        )

    return None


def _first_non_empty(values: tuple[str | None, ...] | list[str | None] | object) -> str | None:
    for value in values:
        if isinstance(value, str) and value:
            return value
    return None


def _merge_string_tuples(values: object) -> tuple[str, ...]:
    merged: list[str] = []
    for value in values:
        if not isinstance(value, tuple):
            continue
        for item in value:
            if isinstance(item, str) and item and item not in merged:
                merged.append(item)
    return tuple(merged)