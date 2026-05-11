"""Graph-facing control snapshot helpers for progress graph consumers."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path

from src.runtime.orchestration import BridgeGroupItem, BridgeWorkItem
from src.workflow.checkpoint import read_checkpoint
from src.workflow.handoff_footprint import load_current_handoff_footprint

from .control_binding import normalize_control_bindings

_DEFAULT_CONTROL_SNAPSHOT_PATH = Path(".codex/progress-graph/control-snapshot.json")
_DEFAULT_CHECKPOINT_PATH = Path(".codex/checkpoints/latest.md")
_CURRENT_HANDOFF_PATH = Path(".codex/handoffs/CURRENT.md")
_CHECKPOINT_GRAPH_ID = "checkpoint-current"
_PLANNING_GATES_GRAPH_ID = "planning-gates-index"
_DOC_REF_RE = re.compile(
    r"((?:design_docs|docs|review|\.codex|src|tests|tools|vscode-extension)/[^\s`'\"，。；]+)"
)


def build_control_snapshot(
    *,
    work_items: Sequence[BridgeWorkItem],
    group_items: Sequence[BridgeGroupItem],
    bindings: Sequence[Mapping[str, object]] = (),
    generated_at: str,
) -> dict[str, object]:
    """Build a stable graph-facing control snapshot from bridge runtime primitives."""

    normalized_work_items = _export_work_items(work_items)
    normalized_group_items = _export_group_items(group_items)

    work_item_ids = {item["work_item_id"] for item in normalized_work_items}
    group_item_ids = {item["group_item_id"] for item in normalized_group_items}

    if len(work_item_ids) != len(normalized_work_items):
        raise ValueError("work_item_id must be unique")
    if len(group_item_ids) != len(normalized_group_items):
        raise ValueError("group_item_id must be unique")

    for group_item in normalized_group_items:
        if group_item["work_item_id"] not in work_item_ids:
            raise ValueError("group_item.work_item_id must reference an existing work item")

    normalized_bindings = _validate_bindings(bindings, work_item_ids=work_item_ids, group_item_ids=group_item_ids)

    return {
        "snapshot_version": "v1alpha1",
        "snapshot_kind": "orchestration-bridge-compact",
        "generated_at": generated_at,
        "work_items": normalized_work_items,
        "group_items": normalized_group_items,
        "bindings": normalized_bindings,
        "summary": _build_summary(
            work_items=normalized_work_items,
            group_items=normalized_group_items,
            bindings=normalized_bindings,
        ),
    }


def control_snapshot_path(project_root: str | Path) -> Path:
    return Path(project_root) / _DEFAULT_CONTROL_SNAPSHOT_PATH


def write_control_snapshot(
    project_root: str | Path,
    *,
    work_items: Sequence[BridgeWorkItem] = (),
    group_items: Sequence[BridgeGroupItem] = (),
    bindings: Sequence[Mapping[str, object]] = (),
    generated_at: str | None = None,
) -> Path:
    resolved_work_items = tuple(work_items)
    resolved_group_items = tuple(group_items)
    resolved_bindings = tuple(bindings)
    if not resolved_work_items and not resolved_group_items and not resolved_bindings:
        (
            resolved_work_items,
            resolved_group_items,
            resolved_bindings,
        ) = _build_doc_loop_snapshot_inputs(project_root)

    normalized_bindings = normalize_control_bindings(
        bindings=resolved_bindings,
        work_items=resolved_work_items,
        group_items=resolved_group_items,
    ) if resolved_bindings else ()
    snapshot = build_control_snapshot(
        work_items=resolved_work_items,
        group_items=resolved_group_items,
        bindings=normalized_bindings,
        generated_at=generated_at or datetime.now(timezone.utc).isoformat(),
    )
    path = control_snapshot_path(project_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def _build_doc_loop_snapshot_inputs(
    project_root: str | Path,
) -> tuple[
    tuple[BridgeWorkItem, ...],
    tuple[BridgeGroupItem, ...],
    tuple[dict[str, object], ...],
]:
    root = Path(project_root)
    checkpoint_inputs = _build_checkpoint_snapshot_inputs(root)
    handoff_inputs = _build_current_handoff_snapshot_inputs(root)
    return (
        (*checkpoint_inputs[0], *handoff_inputs[0]),
        (*checkpoint_inputs[1], *handoff_inputs[1]),
        (*checkpoint_inputs[2], *handoff_inputs[2]),
    )


def _build_checkpoint_snapshot_inputs(
    root: Path,
) -> tuple[
    tuple[BridgeWorkItem, ...],
    tuple[BridgeGroupItem, ...],
    tuple[dict[str, object], ...],
]:
    checkpoint_path = root / _DEFAULT_CHECKPOINT_PATH
    if not checkpoint_path.exists():
        return (), (), ()

    checkpoint = read_checkpoint(checkpoint_path)
    planning_gate = str(checkpoint.get("planning_gate") or "").strip()
    checkpoint_timestamp = str(checkpoint.get("timestamp") or "").strip()
    pending_decision = str(checkpoint.get("pending_decision") or "").strip()
    phase = str(checkpoint.get("phase") or "").strip()
    todo_rows = tuple(checkpoint.get("todos") or ())
    open_todos = tuple(
        (index, row)
        for index, row in enumerate(todo_rows, start=1)
        if str(row.get("status") or "not-started") != "done"
    )
    if not planning_gate and not open_todos and not pending_decision:
        return (), (), ()

    scope_key = _scope_key(planning_gate)
    work_item_id = f"doc-loop-work::{scope_key}"
    current_gate_state = "waiting_review" if pending_decision else "active"
    checkpoint_ref = _DEFAULT_CHECKPOINT_PATH.as_posix()

    todo_group_entries: list[tuple[int, dict[str, object], BridgeGroupItem]] = []
    for index, row in open_todos:
        group_item = BridgeGroupItem(
            group_item_id=f"doc-loop-group::{scope_key}::todo:{index:03d}",
            work_item_id=work_item_id,
            task_group_id=planning_gate or None,
            latest_trace_id=checkpoint_timestamp or None,
            lifecycle_state=_todo_group_lifecycle(str(row.get("status") or "not-started")),
            current_gate_state=current_gate_state,
            writeback_disposition="pending",
            authoritative_refs=tuple(
                _unique_strings(
                    [planning_gate, checkpoint_ref, *_extract_doc_refs(str(row.get("title") or ""))]
                )
            ),
            open_items=(str(row.get("title") or ""),),
        )
        todo_group_entries.append((index, row, group_item))

    open_item_titles = [str(row.get("title") or "") for _, row in open_todos]
    gate_group_item_id = f"doc-loop-group::{scope_key}::planning-gate" if planning_gate else None
    group_items: list[BridgeGroupItem] = []
    if gate_group_item_id is not None:
        gate_open_items = tuple(open_item_titles or ([pending_decision] if pending_decision else []))
        group_items.append(
            BridgeGroupItem(
                group_item_id=gate_group_item_id,
                work_item_id=work_item_id,
                task_group_id=planning_gate,
                child_task_ids=tuple(item.group_item_id for _, _, item in todo_group_entries),
                latest_trace_id=checkpoint_timestamp or None,
                lifecycle_state="dispatched" if pending_decision else "settled",
                governance_surface_kind="grouped_review" if pending_decision else "none",
                governance_surface_state="review_required" if pending_decision else "",
                current_gate_state=current_gate_state,
                writeback_disposition="pending" if open_todos or pending_decision else "eligible",
                authoritative_refs=tuple(_unique_strings([planning_gate, checkpoint_ref])),
                open_items=gate_open_items,
            )
        )
    group_items.extend(item for _, _, item in todo_group_entries)

    dominant_group_item_ids = tuple(
        item.group_item_id for _, _, item in todo_group_entries if item.lifecycle_state != "settled"
    )
    if pending_decision and gate_group_item_id is not None:
        dominant_group_item_ids = (gate_group_item_id, *dominant_group_item_ids)
    elif not dominant_group_item_ids and gate_group_item_id is not None:
        dominant_group_item_ids = (gate_group_item_id,)

    active_group_item_count = sum(1 for item in group_items if item.lifecycle_state != "settled")
    work_item = BridgeWorkItem(
        work_item_id=work_item_id,
        source_envelope_id=f"checkpoint::{scope_key}",
        scope_summary=planning_gate or phase or checkpoint_ref,
        source_trace_id=checkpoint_timestamp or None,
        group_item_ids=tuple(item.group_item_id for item in group_items),
        lifecycle_state=_work_item_lifecycle(open_todos=open_todos, pending_decision=pending_decision),
        rollup_surface_kind="grouped_review" if pending_decision else "none",
        rollup_surface_state="review_required" if pending_decision else "",
        rollup_writeback_disposition="pending" if open_todos or pending_decision else "eligible",
        dominant_group_item_ids=dominant_group_item_ids,
        open_group_item_count=active_group_item_count,
    )

    bindings: list[dict[str, object]] = []
    if planning_gate and gate_group_item_id is not None:
        planning_gate_path = root / planning_gate
        if planning_gate_path.exists():
            bindings.append(
                {
                    "binding_id": f"binding::{scope_key}::planning-gate",
                    "binding_kind": "node",
                    "graph_id": _PLANNING_GATES_GRAPH_ID,
                    "graph_target_id": planning_gate,
                    "graph_target_key": f"{_PLANNING_GATES_GRAPH_ID}::{planning_gate}",
                    "work_item_ids": [work_item_id],
                    "group_item_ids": [gate_group_item_id],
                    "binding_reason": "explicit-node-ref",
                }
            )
        else:
            bindings.append(
                {
                    "binding_id": f"binding::{scope_key}::planning-gate",
                    "binding_kind": "unbound-runtime-panel",
                    "work_item_ids": [work_item_id],
                    "group_item_ids": [gate_group_item_id],
                    "binding_reason": "unbound-no-stable-target",
                }
            )
    elif work_item_id:
        bindings.append(
            {
                "binding_id": f"binding::{scope_key}::work-item",
                "binding_kind": "unbound-runtime-panel",
                "work_item_ids": [work_item_id],
                "group_item_ids": [],
                "binding_reason": "unbound-no-stable-target",
            }
        )

    for index, _, group_item in todo_group_entries:
        target_id = f"todo:{index:03d}"
        bindings.append(
            {
                "binding_id": f"binding::{scope_key}::{target_id}",
                "binding_kind": "node",
                "graph_id": _CHECKPOINT_GRAPH_ID,
                "graph_target_id": target_id,
                "graph_target_key": f"{_CHECKPOINT_GRAPH_ID}::{target_id}",
                "work_item_ids": [],
                "group_item_ids": [group_item.group_item_id],
                "binding_reason": "explicit-node-ref",
            }
        )

    return (work_item,), tuple(group_items), tuple(bindings)


def _build_current_handoff_snapshot_inputs(
    root: Path,
) -> tuple[
    tuple[BridgeWorkItem, ...],
    tuple[BridgeGroupItem, ...],
    tuple[dict[str, object], ...],
]:
    handoff = load_current_handoff_footprint(root)
    if not handoff:
        return (), (), ()

    handoff_id = str(handoff.get("handoff_id") or "").strip()
    source_path = str(handoff.get("source_path") or "").strip()
    scope_key = str(handoff.get("scope_key") or "").strip()
    created_at = str(handoff.get("created_at") or "").strip()
    if not all((handoff_id, source_path, scope_key, created_at)):
        return (), (), ()

    current_handoff_path = _CURRENT_HANDOFF_PATH.as_posix()
    source_exists = (root / source_path).exists()
    blocked_reason = "" if source_exists else f"missing handoff source: {source_path}"
    work_item_id = f"doc-loop-work::handoff::{scope_key}"
    group_item_id = f"doc-loop-group::handoff::{scope_key}::current-mirror"

    group_item = BridgeGroupItem(
        group_item_id=group_item_id,
        work_item_id=work_item_id,
        task_group_id=current_handoff_path,
        latest_trace_id=created_at,
        lifecycle_state="settled",
        governance_surface_kind="group_terminal",
        governance_surface_state="handoff",
        blocked_reason=blocked_reason,
        authoritative_refs=tuple(_unique_strings([current_handoff_path, source_path])),
        open_items=(
            f"current handoff: {handoff_id}",
            f"source path: {source_path}",
        ),
        current_gate_state="active",
        writeback_disposition="none",
        delivery_surface_kind="handoff",
        delivery_state="delivered" if source_exists else "failed",
    )
    work_item = BridgeWorkItem(
        work_item_id=work_item_id,
        source_envelope_id=f"handoff::{handoff_id}",
        scope_summary=source_path,
        source_trace_id=created_at,
        group_item_ids=(group_item_id,),
        lifecycle_state="completed" if source_exists else "blocked",
        blocked_reason=blocked_reason,
        rollup_surface_kind="group_terminal",
        rollup_surface_state="handoff",
        rollup_blocked_reason=blocked_reason,
        rollup_writeback_disposition="none",
        dominant_group_item_ids=(group_item_id,),
        open_group_item_count=0,
    )
    binding = {
        "binding_id": f"binding::handoff::{scope_key}::current-mirror",
        "binding_kind": "unbound-runtime-panel",
        "work_item_ids": [work_item_id],
        "group_item_ids": [group_item_id],
        "binding_reason": "current-handoff-mirror",
    }
    return (work_item,), (group_item,), (binding,)


def _scope_key(planning_gate: str) -> str:
    if planning_gate:
        return Path(planning_gate).stem
    return _CHECKPOINT_GRAPH_ID


def _work_item_lifecycle(
    *,
    open_todos: Sequence[tuple[int, Mapping[str, object]]],
    pending_decision: str,
) -> str:
    if pending_decision:
        return "waiting_external_resolution"
    if open_todos:
        return "dispatching"
    return "completed"


def _todo_group_lifecycle(status: str) -> str:
    normalized = status.strip().lower()
    if normalized == "in-progress":
        return "dispatched"
    return "prepared"


def _extract_doc_refs(text: str) -> tuple[str, ...]:
    return tuple(_unique_strings(match.group(1) for match in _DOC_REF_RE.finditer(text)))


def _unique_strings(values: Sequence[str | None] | Sequence[object]) -> list[str]:
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        stripped = value.strip()
        if stripped and stripped not in normalized:
            normalized.append(stripped)
    return normalized


def _export_work_items(work_items: Sequence[BridgeWorkItem]) -> list[dict[str, object]]:
    exported: list[dict[str, object]] = []
    for item in sorted(work_items, key=lambda value: value.work_item_id):
        exported.append(
            {
                "work_item_id": item.work_item_id,
                "lifecycle_state": item.lifecycle_state,
                "rollup_surface_kind": item.rollup_surface_kind,
                "rollup_surface_state": item.rollup_surface_state,
                "rollup_blocked_reason": item.rollup_blocked_reason or None,
                "rollup_writeback_disposition": item.rollup_writeback_disposition,
                "dominant_group_item_ids": list(item.dominant_group_item_ids),
                "open_group_item_count": item.open_group_item_count,
                "source_trace_id": item.source_trace_id,
            }
        )
    return exported


def _export_group_items(group_items: Sequence[BridgeGroupItem]) -> list[dict[str, object]]:
    exported: list[dict[str, object]] = []
    for item in sorted(group_items, key=lambda value: value.group_item_id):
        exported.append(
            {
                "group_item_id": item.group_item_id,
                "work_item_id": item.work_item_id,
                "task_group_id": item.task_group_id,
                "child_task_ids": list(item.child_task_ids),
                "lifecycle_state": item.lifecycle_state,
                "governance_surface_kind": item.governance_surface_kind,
                "governance_surface_state": item.governance_surface_state,
                "current_gate_state": item.current_gate_state,
                "writeback_disposition": item.writeback_disposition,
                "delivery_surface_kind": item.delivery_surface_kind,
                "delivery_state": item.delivery_state,
                "blocked_reason": item.blocked_reason,
                "open_items": list(item.open_items),
                "authoritative_refs": list(item.authoritative_refs),
                "latest_trace_id": item.latest_trace_id,
                "latest_envelope_id": item.latest_envelope_id,
                "actor_label": None,
            }
        )
    return exported


def _validate_bindings(
    bindings: Sequence[Mapping[str, object]],
    *,
    work_item_ids: set[str],
    group_item_ids: set[str],
) -> list[dict[str, object]]:
    normalized: list[dict[str, object]] = []
    for row in bindings:
        work_ids = _read_id_list(row.get("work_item_ids"), field_name="work_item_ids")
        group_ids = _read_id_list(row.get("group_item_ids"), field_name="group_item_ids")

        for work_item_id in work_ids:
            if work_item_id not in work_item_ids:
                raise ValueError("binding references unknown work_item_id")
        for group_item_id in group_ids:
            if group_item_id not in group_item_ids:
                raise ValueError("binding references unknown group_item_id")

        normalized.append(dict(row))
    return sorted(normalized, key=lambda item: str(item["binding_id"]))


def _build_summary(
    *,
    work_items: Sequence[Mapping[str, object]],
    group_items: Sequence[Mapping[str, object]],
    bindings: Sequence[Mapping[str, object]],
) -> dict[str, int]:
    bound_group_item_ids: set[str] = set()
    for row in bindings:
        bound_group_item_ids.update(_read_id_list(row.get("group_item_ids"), field_name="group_item_ids"))

    return {
        "open_work_item_count": sum(
            1
            for item in work_items
            if item["lifecycle_state"] not in {"completed", "blocked"}
        ),
        "blocked_work_item_count": sum(
            1 for item in work_items if item["lifecycle_state"] == "blocked"
        ),
        "waiting_external_resolution_count": sum(
            1
            for item in work_items
            if item["lifecycle_state"] == "waiting_external_resolution"
        ),
        "active_group_item_count": sum(
            1 for item in group_items if item["lifecycle_state"] != "settled"
        ),
        "unbound_group_item_count": sum(
            1 for item in group_items if item["group_item_id"] not in bound_group_item_ids
        ),
    }


def _read_id_list(value: object, *, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"{field_name} must be a sequence of strings")

    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise ValueError(f"{field_name} must contain only strings")
        normalized.append(item)
    return normalized