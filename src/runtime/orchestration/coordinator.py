"""Minimal orchestration coordinator glue over runtime helpers."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping

from .executor_adapter import project_execution_result_to_group_item
from .models import BridgeGroupItem, BridgeWorkItem
from .rollup import roll_up_work_item
from .stop_conditions import StopConditionDecision, evaluate_stop_condition


@dataclass(frozen=True, slots=True)
class CoordinatorAdvanceResult:
    """Result of a single coordinator step over one group item."""

    work_item: BridgeWorkItem
    group_items: tuple[BridgeGroupItem, ...]
    updated_group_item: BridgeGroupItem
    decision: StopConditionDecision


def advance_work_item_from_execution_result(
    work_item: BridgeWorkItem,
    group_items: tuple[BridgeGroupItem, ...],
    *,
    group_item_id: str,
    execution_result: Mapping[str, object],
) -> CoordinatorAdvanceResult:
    """Advance one work-item step from a single executor execution result."""

    matching_indexes = tuple(
        index for index, item in enumerate(group_items) if item.group_item_id == group_item_id
    )
    if len(matching_indexes) != 1:
        raise ValueError("group_item_id must match exactly one group item")

    target_index = matching_indexes[0]
    updated_group_item = project_execution_result_to_group_item(
        group_items[target_index],
        execution_result,
    )
    updated_group_items = (
        group_items[:target_index]
        + (updated_group_item,)
        + group_items[target_index + 1 :]
    )

    rolled_work_item = roll_up_work_item(work_item, updated_group_items)
    decision = evaluate_stop_condition(rolled_work_item)
    advanced_work_item = replace(
        rolled_work_item,
        lifecycle_state=decision.next_lifecycle_state,
        blocked_reason=decision.reason if decision.next_lifecycle_state == "blocked" else "",
    )
    return CoordinatorAdvanceResult(
        work_item=advanced_work_item,
        group_items=updated_group_items,
        updated_group_item=updated_group_item,
        decision=decision,
    )