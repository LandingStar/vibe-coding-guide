"""Roll-up helpers for orchestration bridge work items."""

from __future__ import annotations

from dataclasses import replace

from .models import BridgeGroupItem, BridgeWorkItem, WritebackDisposition


def roll_up_work_item(
    work_item: BridgeWorkItem,
    group_items: tuple[BridgeGroupItem, ...],
) -> BridgeWorkItem:
    """Aggregate group-item surfaces into a work-item roll-up."""

    for group_item in group_items:
        if group_item.work_item_id != work_item.work_item_id:
            raise ValueError(
                "group_item.work_item_id must match work_item.work_item_id"
            )

    open_group_item_count = sum(
        1 for group_item in group_items if group_item.lifecycle_state != "settled"
    )
    settled_group_items = tuple(
        group_item for group_item in group_items if group_item.lifecycle_state == "settled"
    )

    dominant_group_items, rollup_surface_kind, rollup_surface_state = _resolve_dominant_surface(
        settled_group_items
    )
    dominant_group_item_ids = tuple(
        sorted(group_item.group_item_id for group_item in dominant_group_items)
    )
    rollup_blocked_reason = next(
        (
            group_item.blocked_reason
            for group_item in sorted(dominant_group_items, key=lambda item: item.group_item_id)
            if group_item.blocked_reason
        ),
        "",
    )
    rollup_writeback_disposition = _resolve_writeback_disposition(
        settled_group_items, open_group_item_count
    )

    return replace(
        work_item,
        rollup_surface_kind=rollup_surface_kind,
        rollup_surface_state=rollup_surface_state,
        rollup_blocked_reason=rollup_blocked_reason,
        rollup_writeback_disposition=rollup_writeback_disposition,
        dominant_group_item_ids=dominant_group_item_ids,
        open_group_item_count=open_group_item_count,
    )


def _resolve_dominant_surface(
    settled_group_items: tuple[BridgeGroupItem, ...],
) -> tuple[tuple[BridgeGroupItem, ...], str, str]:
    if not settled_group_items:
        return (), "none", ""

    blocked = tuple(
        group_item
        for group_item in settled_group_items
        if group_item.governance_surface_kind == "blocked"
    )
    if blocked:
        return blocked, "blocked", "blocked"

    escalation = tuple(
        group_item
        for group_item in settled_group_items
        if group_item.governance_surface_kind == "group_terminal"
        and group_item.governance_surface_state == "escalation"
    )
    if escalation:
        return escalation, "group_terminal", "escalation"

    handoff = tuple(
        group_item
        for group_item in settled_group_items
        if group_item.governance_surface_kind == "group_terminal"
        and group_item.governance_surface_state == "handoff"
    )
    if handoff:
        return handoff, "group_terminal", "handoff"

    review_required = tuple(
        group_item
        for group_item in settled_group_items
        if group_item.governance_surface_kind == "grouped_review"
        and group_item.governance_surface_state == "review_required"
    )
    if review_required:
        return review_required, "grouped_review", "review_required"

    all_clear = tuple(
        group_item
        for group_item in settled_group_items
        if group_item.governance_surface_kind == "grouped_review"
        and group_item.governance_surface_state == "all_clear"
    )
    if all_clear:
        return all_clear, "grouped_review", "all_clear"

    return (), "none", ""


def _resolve_writeback_disposition(
    settled_group_items: tuple[BridgeGroupItem, ...],
    open_group_item_count: int,
) -> WritebackDisposition:
    if any(item.writeback_disposition == "blocked" for item in settled_group_items):
        return "blocked"
    if any(item.writeback_disposition == "suppressed" for item in settled_group_items):
        return "suppressed"
    if open_group_item_count > 0:
        return "pending"
    if any(item.writeback_disposition == "pending" for item in settled_group_items):
        return "pending"
    if any(item.writeback_disposition == "eligible" for item in settled_group_items):
        return "eligible"
    return "none"