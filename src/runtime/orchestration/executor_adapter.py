"""Adapters from executor execution results into orchestration runtime models."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from .models import BridgeGroupItem
from .projection import project_group_item_surface


def project_execution_result_to_group_item(
    group_item: BridgeGroupItem,
    execution_result: Mapping[str, object],
) -> BridgeGroupItem:
    """Normalize an executor execution result into a settled group-item surface."""

    updated_group_item = replace(
        group_item,
        task_group_id=_result_task_group_id(execution_result) or group_item.task_group_id,
        latest_envelope_id=_optional_str(execution_result.get("envelope_id"))
        or group_item.latest_envelope_id,
        latest_trace_id=_optional_str(execution_result.get("trace_id"))
        or group_item.latest_trace_id,
    )

    group_terminal = _mapping_or_none(execution_result.get("group_terminal_outcome"))
    if group_terminal:
        terminal_kind = _optional_str(group_terminal.get("terminal_kind")) or ""
        if terminal_kind not in ("escalation", "handoff"):
            terminal_kind = ""
        return project_group_item_surface(
            replace(
                updated_group_item,
                authoritative_refs=_string_tuple(group_terminal.get("authoritative_refs")),
                open_items=_string_tuple(group_terminal.get("open_items")),
                current_gate_state=_optional_str(group_terminal.get("current_gate_state"))
                or "",
            ),
            governance_surface_kind="group_terminal",
            governance_surface_state=terminal_kind,
            blocked_reason=_optional_str(group_terminal.get("blocked_reason")) or "",
            writeback_disposition="suppressed",
        )

    grouped_review = _mapping_or_none(execution_result.get("grouped_review_outcome"))
    if grouped_review:
        grouped_review_state = _optional_str(execution_result.get("grouped_review_state"))
        if grouped_review_state not in ("all_clear", "review_required"):
            grouped_review_state = _optional_str(grouped_review.get("outcome")) or ""
        if grouped_review_state not in ("all_clear", "review_required"):
            grouped_review_state = ""
        writeback_disposition = "eligible" if grouped_review_state == "all_clear" else "pending"
        return project_group_item_surface(
            replace(
                updated_group_item,
                authoritative_refs=(),
                open_items=_string_tuple(grouped_review.get("unresolved_items")),
                current_gate_state="",
            ),
            governance_surface_kind="grouped_review",
            governance_surface_state=grouped_review_state,
            blocked_reason=_optional_str(grouped_review.get("blocked_reason")) or "",
            writeback_disposition=writeback_disposition,
        )

    if _optional_str(execution_result.get("execution_status")) == "blocked":
        return project_group_item_surface(
            replace(
                updated_group_item,
                authoritative_refs=(),
                open_items=(),
                current_gate_state="",
            ),
            governance_surface_kind="blocked",
            governance_surface_state="blocked",
            blocked_reason=_optional_str(execution_result.get("detail")) or "",
            writeback_disposition="blocked",
        )

    return project_group_item_surface(
        replace(
            updated_group_item,
            authoritative_refs=(),
            open_items=(),
            current_gate_state="",
        ),
        governance_surface_kind="none",
        governance_surface_state="",
        blocked_reason="",
        writeback_disposition="pending",
    )


def _mapping_or_none(value: object) -> Mapping[str, object] | None:
    if isinstance(value, Mapping) and value:
        return value
    return None


def _optional_str(value: object) -> str | None:
    if isinstance(value, str) and value:
        return value
    return None


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, list):
        return ()
    return tuple(item for item in value if isinstance(item, str) and item)


def _result_task_group_id(execution_result: Mapping[str, object]) -> str | None:
    group_terminal = _mapping_or_none(execution_result.get("group_terminal_outcome"))
    if group_terminal:
        return _optional_str(group_terminal.get("task_group_id"))

    grouped_review = _mapping_or_none(execution_result.get("grouped_review_outcome"))
    if grouped_review:
        return _optional_str(grouped_review.get("task_group_id"))

    return None