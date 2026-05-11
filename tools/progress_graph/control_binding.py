"""Graph-facing binding normalization helpers for control snapshots."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from src.runtime.orchestration import BridgeGroupItem, BridgeWorkItem


def normalize_control_bindings(
    *,
    bindings: Sequence[Mapping[str, object]],
    work_items: Sequence[BridgeWorkItem],
    group_items: Sequence[BridgeGroupItem],
) -> tuple[dict[str, object], ...]:
    """Normalize graph binding rows into a stable graph-facing surface."""

    work_item_ids = {item.work_item_id for item in work_items}
    group_item_ids = {item.group_item_id for item in group_items}
    seen_binding_ids: set[str] = set()
    seen_bound_work_item_ids: set[str] = set()
    seen_bound_group_item_ids: set[str] = set()
    normalized_rows: list[dict[str, object]] = []

    for row in bindings:
        binding_id = _read_required_str(row, "binding_id")
        if binding_id in seen_binding_ids:
            raise ValueError("binding_id must be unique")
        seen_binding_ids.add(binding_id)

        binding_kind = _read_required_str(row, "binding_kind")
        work_item_id_list = _normalize_id_list(row.get("work_item_ids"), field_name="work_item_ids")
        group_item_id_list = _normalize_id_list(row.get("group_item_ids"), field_name="group_item_ids")

        if (
            binding_kind != "unbound-runtime-panel"
            and not work_item_id_list
            and not group_item_id_list
        ):
            raise ValueError("binding must reference at least one work item or group item")

        for work_item_id in work_item_id_list:
            if work_item_id not in work_item_ids:
                raise ValueError("binding references unknown work_item_id")
            if work_item_id in seen_bound_work_item_ids:
                raise ValueError("each work_item_id may appear in at most one binding row")
            seen_bound_work_item_ids.add(work_item_id)

        for group_item_id in group_item_id_list:
            if group_item_id not in group_item_ids:
                raise ValueError("binding references unknown group_item_id")
            if group_item_id in seen_bound_group_item_ids:
                raise ValueError("each group_item_id may appear in at most one binding row")
            seen_bound_group_item_ids.add(group_item_id)

        graph_id = _read_optional_str(row, "graph_id")
        graph_target_id = _read_optional_str(row, "graph_target_id")
        graph_target_key = _read_optional_str(row, "graph_target_key")

        if binding_kind == "unbound-runtime-panel":
            if graph_id or graph_target_id or graph_target_key:
                raise ValueError(
                    "unbound-runtime-panel bindings must not declare graph target fields"
                )
        else:
            if not graph_id or not graph_target_id or not graph_target_key:
                raise ValueError(
                    "bound bindings must declare graph_id, graph_target_id, and graph_target_key"
                )
            expected_key = f"{graph_id}::{graph_target_id}"
            if graph_target_key != expected_key:
                raise ValueError("graph_target_key must equal graph_id::graph_target_id")

        normalized_rows.append(
            {
                "binding_id": binding_id,
                "binding_kind": binding_kind,
                "graph_id": graph_id,
                "graph_target_id": graph_target_id,
                "graph_target_key": graph_target_key,
                "work_item_ids": work_item_id_list,
                "group_item_ids": group_item_id_list,
                "binding_reason": _read_required_str(row, "binding_reason"),
            }
        )

    return tuple(sorted(normalized_rows, key=lambda item: str(item["binding_id"])))


def _read_required_str(row: Mapping[str, object], field_name: str) -> str:
    value = _read_optional_str(row, field_name)
    if not value:
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _read_optional_str(row: Mapping[str, object], field_name: str) -> str | None:
    value = row.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string when provided")
    stripped = value.strip()
    return stripped or None


def _normalize_id_list(value: object, *, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a sequence of strings")

    normalized: set[str] = set()
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"{field_name} must contain only strings")
        stripped = item.strip()
        if not stripped:
            raise ValueError(f"{field_name} must not contain empty strings")
        normalized.add(stripped)
    return sorted(normalized)