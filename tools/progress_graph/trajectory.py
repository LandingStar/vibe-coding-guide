"""Local work trajectory model and checkpoint projection."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from src.workflow.checkpoint import read_checkpoint

TrajectoryLaneStatus = Literal["pending", "active", "waiting", "blocked", "done"]
TrajectoryEventKind = Literal[
    "start",
    "task",
    "decision",
    "review",
    "wait",
    "validation",
    "writeback",
    "handoff",
    "merge",
    "close",
]
TrajectoryEventStatus = Literal[
    "pending",
    "in_progress",
    "blocked",
    "waiting",
    "completed",
    "archived",
]
TrajectoryRelationKind = Literal[
    "sequence",
    "depends_on",
    "waits_for",
    "unblocks",
    "hands_off",
    "syncs_from",
    "merges_into",
    "proposes_new_line",
    "approves_new_line",
]

_LOCAL_WORK_RELATION_KINDS: set[str] = {
    "depends_on",
    "waits_for",
    "unblocks",
    "hands_off",
    "syncs_from",
    "merges_into",
    "proposes_new_line",
    "approves_new_line",
}

_DEFAULT_TRAJECTORY_PATH = Path(".codex/progress-graph/local-work-trajectory.json")


@dataclass(frozen=True)
class TrajectoryLane:
    """A single context-bearing work lane inside a local work trajectory."""

    id: str
    label: str
    status: TrajectoryLaneStatus = "pending"
    summary: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class TrajectoryEvent:
    """A timestamped or ordered event on a local work trajectory lane."""

    id: str
    lane_id: str
    title: str
    kind: TrajectoryEventKind = "task"
    status: TrajectoryEventStatus = "pending"
    order: int = 0
    summary: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class TrajectoryRelation:
    """A typed relation between two trajectory events."""

    source_event_id: str
    target_event_id: str
    kind: TrajectoryRelationKind = "sequence"
    summary: str = ""
    metadata: dict[str, str] = field(default_factory=dict)


class LocalWorkTrajectory:
    """A local work trajectory view with one or more work lanes.

    The first backend slice only projects one lane, but the model keeps relations
    explicit so later multi-lane and dynamic-line events do not need a format reset.
    """

    def __init__(
        self,
        *,
        trajectory_id: str,
        title: str,
        recorded_at: str = "",
        source_graph_id: str = "",
        source_node_id: str = "",
        guide_context: str = "",
        metadata: dict[str, str] | None = None,
    ) -> None:
        self.trajectory_id = trajectory_id
        self.title = title
        self.recorded_at = recorded_at
        self.source_graph_id = source_graph_id
        self.source_node_id = source_node_id
        self.guide_context = guide_context
        self.metadata = dict(metadata or {})
        self.lanes: dict[str, TrajectoryLane] = {}
        self.events: dict[str, TrajectoryEvent] = {}
        self.relations: list[TrajectoryRelation] = []

    def add_lane(self, lane: TrajectoryLane) -> None:
        self.lanes[lane.id] = lane

    def add_event(self, event: TrajectoryEvent) -> None:
        self.events[event.id] = event

    def add_relation(self, relation: TrajectoryRelation) -> None:
        self.relations.append(relation)

    def check_invariants(self) -> list[str]:
        errors: list[str] = []
        for event in self.events.values():
            if event.lane_id not in self.lanes:
                errors.append(f"event {event.id!r} references unknown lane {event.lane_id!r}")
        for relation in self.relations:
            if relation.source_event_id not in self.events:
                errors.append(
                    f"relation source {relation.source_event_id!r} does not exist"
                )
            if relation.target_event_id not in self.events:
                errors.append(
                    f"relation target {relation.target_event_id!r} does not exist"
                )
        return errors

    def validate(self) -> None:
        errors = self.check_invariants()
        if errors:
            raise ValueError("; ".join(errors))

    def summary(self) -> dict[str, object]:
        return {
            "trajectory_id": self.trajectory_id,
            "title": self.title,
            "lane_count": len(self.lanes),
            "event_count": len(self.events),
            "relation_count": len(self.relations),
            "source_graph_id": self.source_graph_id,
            "source_node_id": self.source_node_id,
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": "1.0",
            "trajectory_id": self.trajectory_id,
            "title": self.title,
            "recorded_at": self.recorded_at,
            "source_graph_id": self.source_graph_id,
            "source_node_id": self.source_node_id,
            "guide_context": self.guide_context,
            "metadata": dict(self.metadata),
            "summary": self.summary(),
            "lanes": {
                lane_id: asdict(lane)
                for lane_id, lane in sorted(self.lanes.items())
            },
            "events": {
                event_id: asdict(event)
                for event_id, event in sorted(
                    self.events.items(),
                    key=lambda item: (item[1].order, item[0]),
                )
            },
            "relations": [asdict(relation) for relation in self.relations],
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "LocalWorkTrajectory":
        trajectory = cls(
            trajectory_id=str(data["trajectory_id"]),
            title=str(data["title"]),
            recorded_at=str(data.get("recorded_at", "")),
            source_graph_id=str(data.get("source_graph_id", "")),
            source_node_id=str(data.get("source_node_id", "")),
            guide_context=str(data.get("guide_context", "")),
            metadata=dict(data.get("metadata", {})),
        )
        for lane_data in dict(data.get("lanes", {})).values():
            trajectory.add_lane(
                TrajectoryLane(
                    id=str(lane_data["id"]),
                    label=str(lane_data["label"]),
                    status=str(lane_data.get("status", "pending")),
                    summary=str(lane_data.get("summary", "")),
                    metadata=dict(lane_data.get("metadata", {})),
                )
            )
        for event_data in dict(data.get("events", {})).values():
            trajectory.add_event(
                TrajectoryEvent(
                    id=str(event_data["id"]),
                    lane_id=str(event_data["lane_id"]),
                    title=str(event_data["title"]),
                    kind=str(event_data.get("kind", "task")),
                    status=str(event_data.get("status", "pending")),
                    order=int(event_data.get("order", 0)),
                    summary=str(event_data.get("summary", "")),
                    metadata=dict(event_data.get("metadata", {})),
                )
            )
        for relation_data in list(data.get("relations", [])):
            trajectory.add_relation(
                TrajectoryRelation(
                    source_event_id=str(relation_data["source_event_id"]),
                    target_event_id=str(relation_data["target_event_id"]),
                    kind=str(relation_data.get("kind", "sequence")),
                    summary=str(relation_data.get("summary", "")),
                    metadata=dict(relation_data.get("metadata", {})),
                )
            )
        trajectory.validate()
        return trajectory

    def to_json(self, indent: int = 2) -> str:
        self.validate()
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_json(cls, data: str) -> "LocalWorkTrajectory":
        return cls.from_dict(json.loads(data))


def trajectory_json_path(project_root: str | Path) -> Path:
    return Path(project_root) / _DEFAULT_TRAJECTORY_PATH


def load_local_work_trajectory(project_root: str | Path) -> LocalWorkTrajectory:
    path = trajectory_json_path(project_root)
    return LocalWorkTrajectory.from_json(path.read_text(encoding="utf-8"))


def write_local_work_trajectory(
    project_root: str | Path,
    trajectory: LocalWorkTrajectory,
) -> Path:
    root = Path(project_root)
    trajectory.recorded_at = datetime.now(timezone.utc).isoformat()
    path = trajectory_json_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(trajectory.to_json(), encoding="utf-8")
    return path


def write_local_work_trajectory_artifact(project_root: str | Path) -> Path:
    """Write the UI trajectory artifact without clobbering explicit lifecycle state.

    Once the single-line lifecycle API owns the artifact, refresh keeps that
    explicit state. Missing or legacy checkpoint-projection artifacts are reset
    to an empty lifecycle-owned trajectory so local work does not silently grow
    from unrelated checkpoint todos.
    """

    root = Path(project_root)
    path = trajectory_json_path(root)
    if path.exists():
        try:
            trajectory = load_local_work_trajectory(root)
        except Exception:
            trajectory = None
        if trajectory is not None and _is_single_line_lifecycle(trajectory):
            return write_local_work_trajectory(root, trajectory)

    return clear_single_line_trajectory(root)


def clear_single_line_trajectory(
    project_root: str | Path,
    *,
    title: str = "Local Work Trajectory",
    guide_context: str = "vscode-progress-graph-preview",
    trajectory_id: str = "local-work:single-line-current",
) -> Path:
    """Write an empty lifecycle-owned local trajectory artifact.

    This is the durable empty state for the Local Work Trajectory view. It is
    intentionally different from deleting the JSON file, because refresh needs a
    marker that says "keep this local map empty" rather than falling back to a
    checkpoint todo projection.
    """

    trajectory = LocalWorkTrajectory(
        trajectory_id=trajectory_id,
        title=title,
        recorded_at=datetime.now(timezone.utc).isoformat(),
        source_graph_id="local-work",
        source_node_id="",
        guide_context=guide_context,
        metadata={
            "projection": "single-lane-lifecycle",
            "lane_mode": "single",
            "lifecycle_version": "1",
            "lifecycle_state": "empty",
        },
    )
    return write_local_work_trajectory(project_root, trajectory)


def write_checkpoint_work_trajectory(project_root: str | Path) -> Path:
    root = Path(project_root)
    trajectory = build_checkpoint_work_trajectory(root)
    path = trajectory_json_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(trajectory.to_json(), encoding="utf-8")
    return path


def start_single_line_trajectory(
    project_root: str | Path,
    *,
    title: str = "Local Work Trajectory",
    lane_label: str = "当前工作",
    first_event_title: str,
    first_event_kind: TrajectoryEventKind = "start",
    first_event_summary: str = "",
    guide_context: str = "",
    source_graph_id: str = "local-work",
    source_node_id: str = "",
    trajectory_id: str = "local-work:single-line-current",
    lane_id: str = "lane:main",
    metadata: dict[str, str] | None = None,
    event_metadata: dict[str, str] | None = None,
) -> Path:
    """Create the first single-line lane and its first active event."""

    now = datetime.now(timezone.utc).isoformat()
    trajectory = LocalWorkTrajectory(
        trajectory_id=trajectory_id,
        title=title,
        recorded_at=now,
        source_graph_id=source_graph_id,
        source_node_id=source_node_id,
        guide_context=guide_context,
        metadata={
            "projection": "single-lane-lifecycle",
            "lane_mode": "single",
            "lifecycle_version": "1",
            **dict(metadata or {}),
        },
    )
    trajectory.add_lane(
        TrajectoryLane(
            id=lane_id,
            label=lane_label,
            status="active",
            summary="Single-line local work lifecycle.",
            metadata={
                "line_kind": "single",
                "context": guide_context,
            },
        )
    )
    trajectory.add_event(
        TrajectoryEvent(
            id="event:001",
            lane_id=lane_id,
            title=first_event_title,
            kind=first_event_kind,
            status="in_progress",
            order=1,
            summary=first_event_summary,
            metadata={
                "created_at": now,
                "activated_at": now,
                "source": "single-line-lifecycle",
                **dict(event_metadata or {}),
            },
        )
    )
    trajectory.validate()
    return write_local_work_trajectory(project_root, trajectory)


def append_single_line_event(
    project_root: str | Path,
    *,
    title: str,
    kind: TrajectoryEventKind = "task",
    status: TrajectoryEventStatus = "pending",
    summary: str = "",
    lane_id: str = "",
    metadata: dict[str, str] | None = None,
) -> Path:
    """Append a subsequent event to the current single-line trajectory."""

    trajectory = _load_single_line_lifecycle(project_root)
    lane = _lane_by_id_or_primary(trajectory, lane_id)
    ordered_events = _ordered_lane_events(trajectory, lane.id)
    previous_event = ordered_events[-1] if ordered_events else None
    next_order = (previous_event.order if previous_event else 0) + 1
    event_id = _next_event_id(trajectory, next_order)
    now = datetime.now(timezone.utc).isoformat()

    trajectory.add_event(
        TrajectoryEvent(
            id=event_id,
            lane_id=lane.id,
            title=title,
            kind=kind,
            status=status,
            order=next_order,
            summary=summary,
            metadata={
                "created_at": now,
                "source": "single-line-lifecycle",
                **dict(metadata or {}),
            },
        )
    )
    if previous_event is not None:
        trajectory.add_relation(
            TrajectoryRelation(
                source_event_id=previous_event.id,
                target_event_id=event_id,
                kind="sequence",
                metadata={"source": "single-line-lifecycle"},
            )
        )
    _refresh_single_lane_status(trajectory, lane.id)
    trajectory.validate()
    return write_local_work_trajectory(project_root, trajectory)


def advance_single_line_event(
    project_root: str | Path,
    *,
    current_event_id: str | None = None,
    activate_next: bool = True,
) -> Path:
    """Complete the active event and activate the next pending event if present."""

    trajectory = _load_single_line_lifecycle(project_root)
    lane = _lane_for_current_or_primary(trajectory, current_event_id=current_event_id)
    ordered_events = _ordered_lane_events(trajectory, lane.id)
    if not ordered_events:
        raise ValueError("single-line trajectory has no events to advance")

    if current_event_id and current_event_id not in trajectory.events:
        raise ValueError(f"unknown trajectory event: {current_event_id}")
    current = (
        trajectory.events[current_event_id]
        if current_event_id
        else _first_event_with_status(ordered_events, "in_progress")
    )
    now = datetime.now(timezone.utc).isoformat()

    if current is None:
        pending = _first_event_with_status(ordered_events, "pending")
        if pending is None:
            _refresh_single_lane_status(trajectory, lane.id)
            return write_local_work_trajectory(project_root, trajectory)
        trajectory.events[pending.id] = replace(
            pending,
            status="in_progress",
            metadata={
                **dict(pending.metadata),
                "activated_at": now,
            },
        )
        _refresh_single_lane_status(trajectory, lane.id)
        return write_local_work_trajectory(project_root, trajectory)

    trajectory.events[current.id] = replace(
        current,
        status="completed",
        metadata={
            **dict(current.metadata),
            "completed_at": now,
        },
    )

    if activate_next:
        ordered_events = _ordered_lane_events(trajectory, lane.id)
        next_event = _next_pending_event_after(ordered_events, current.order)
        if next_event is not None:
            trajectory.events[next_event.id] = replace(
                next_event,
                status="in_progress",
                metadata={
                    **dict(next_event.metadata),
                    "activated_at": now,
                },
            )

    _refresh_single_lane_status(trajectory, lane.id)
    trajectory.validate()
    return write_local_work_trajectory(project_root, trajectory)


def update_single_line_event(
    project_root: str | Path,
    *,
    current_event_id: str | None = None,
    title: str = "",
    summary: str = "",
    metadata: dict[str, str] | None = None,
) -> Path:
    """Update title, summary, or metadata for the current single-line event."""

    trajectory = _load_single_line_lifecycle(project_root)
    lane = _lane_for_current_or_primary(trajectory, current_event_id=current_event_id)
    ordered_events = _ordered_lane_events(trajectory, lane.id)
    current = _select_current_event(
        trajectory,
        ordered_events,
        current_event_id=current_event_id,
        allowed_statuses={"in_progress", "blocked", "waiting", "pending"},
    )
    now = datetime.now(timezone.utc).isoformat()
    next_metadata = {
        **dict(current.metadata),
        "updated_at": now,
        **dict(metadata or {}),
    }
    trajectory.events[current.id] = replace(
        current,
        title=title or current.title,
        summary=summary if summary else current.summary,
        metadata=next_metadata,
    )
    _refresh_single_lane_status(trajectory, lane.id)
    trajectory.validate()
    return write_local_work_trajectory(project_root, trajectory)


def block_single_line_event(
    project_root: str | Path,
    *,
    current_event_id: str | None = None,
    reason: str = "",
    waiting: bool = False,
) -> Path:
    """Mark the current single-line event as blocked or waiting."""

    trajectory = _load_single_line_lifecycle(project_root)
    lane = _lane_for_current_or_primary(trajectory, current_event_id=current_event_id)
    ordered_events = _ordered_lane_events(trajectory, lane.id)
    current = _select_current_event(
        trajectory,
        ordered_events,
        current_event_id=current_event_id,
        allowed_statuses={"in_progress", "pending", "blocked", "waiting"},
    )
    now = datetime.now(timezone.utc).isoformat()
    status: TrajectoryEventStatus = "waiting" if waiting else "blocked"
    metadata_key = "waiting_reason" if waiting else "blocked_reason"
    trajectory.events[current.id] = replace(
        current,
        status=status,
        summary=reason or current.summary,
        metadata={
            **dict(current.metadata),
            f"{status}_at": now,
            metadata_key: reason,
        },
    )
    _refresh_single_lane_status(trajectory, lane.id)
    trajectory.validate()
    return write_local_work_trajectory(project_root, trajectory)


def resume_single_line_event(
    project_root: str | Path,
    *,
    current_event_id: str | None = None,
    summary: str = "",
) -> Path:
    """Resume a blocked, waiting, or pending single-line event as in progress."""

    trajectory = _load_single_line_lifecycle(project_root)
    lane = _lane_for_current_or_primary(trajectory, current_event_id=current_event_id)
    ordered_events = _ordered_lane_events(trajectory, lane.id)
    current = _select_current_event(
        trajectory,
        ordered_events,
        current_event_id=current_event_id,
        allowed_statuses={"blocked", "waiting", "pending", "in_progress"},
    )
    now = datetime.now(timezone.utc).isoformat()
    trajectory.events[current.id] = replace(
        current,
        status="in_progress",
        summary=summary or current.summary,
        metadata={
            **dict(current.metadata),
            "resumed_at": now,
            "activated_at": dict(current.metadata).get("activated_at", now),
        },
    )
    _refresh_single_lane_status(trajectory, lane.id)
    trajectory.validate()
    return write_local_work_trajectory(project_root, trajectory)


def close_single_line_trajectory(
    project_root: str | Path,
    *,
    current_event_id: str | None = None,
    summary: str = "",
) -> Path:
    """Complete the current event and mark the single-line lane as done."""

    trajectory = _load_single_line_lifecycle(project_root)
    lane = _lane_for_current_or_primary(trajectory, current_event_id=current_event_id)
    ordered_events = _ordered_lane_events(trajectory, lane.id)
    current = _select_current_event(
        trajectory,
        ordered_events,
        current_event_id=current_event_id,
        allowed_statuses={"in_progress", "pending", "blocked", "waiting"},
    )
    now = datetime.now(timezone.utc).isoformat()
    trajectory.events[current.id] = replace(
        current,
        status="completed",
        summary=summary or current.summary,
        metadata={
            **dict(current.metadata),
            "completed_at": now,
            "closed_at": now,
        },
    )
    for event in ordered_events:
        if event.id == current.id or event.status not in {"pending", "blocked", "waiting"}:
            continue
        trajectory.events[event.id] = replace(
            event,
            status="archived",
            metadata={
                **dict(event.metadata),
                "archived_at": now,
                "archive_reason": "single-line trajectory closed",
            },
        )
    _refresh_single_lane_status(trajectory, lane.id)
    trajectory.validate()
    return write_local_work_trajectory(project_root, trajectory)


def add_local_work_lane(
    project_root: str | Path,
    *,
    lane_label: str,
    first_event_title: str,
    first_event_kind: TrajectoryEventKind = "task",
    first_event_summary: str = "",
    source_event_id: str | None = None,
    lane_id: str = "",
) -> Path:
    """Add a new lane with its first active event to the lifecycle trajectory."""

    trajectory = _load_single_line_lifecycle(project_root)
    source_event = None
    if source_event_id:
        if source_event_id not in trajectory.events:
            raise ValueError(f"unknown trajectory event: {source_event_id}")
        source_event = trajectory.events[source_event_id]
    else:
        ordered_primary_events = _ordered_lane_events(trajectory, _primary_lane(trajectory).id)
        source_event = (
            _first_event_with_status(ordered_primary_events, "in_progress")
            or ordered_primary_events[-1]
            if ordered_primary_events
            else None
        )

    next_lane_id = lane_id or _next_lane_id(trajectory)
    if next_lane_id in trajectory.lanes:
        raise ValueError(f"trajectory lane already exists: {next_lane_id}")
    now = datetime.now(timezone.utc).isoformat()
    trajectory.add_lane(
        TrajectoryLane(
            id=next_lane_id,
            label=lane_label,
            status="active",
            summary="Additional local work lane.",
            metadata={
                "line_kind": "single",
                "created_at": now,
                "source": "single-line-lifecycle",
            },
        )
    )
    event_id = _next_event_id(trajectory, len(trajectory.events) + 1)
    trajectory.add_event(
        TrajectoryEvent(
            id=event_id,
            lane_id=next_lane_id,
            title=first_event_title,
            kind=first_event_kind,
            status="in_progress",
            order=1,
            summary=first_event_summary,
            metadata={
                "created_at": now,
                "activated_at": now,
                "source": "single-line-lifecycle",
            },
        )
    )
    if source_event is not None:
        trajectory.add_relation(
            TrajectoryRelation(
                source_event_id=source_event.id,
                target_event_id=event_id,
                kind="proposes_new_line",
                summary=f"Created lane {next_lane_id}",
                metadata={"source": "single-line-lifecycle"},
            )
        )
    trajectory.metadata["lane_mode"] = "multi"
    trajectory.validate()
    return write_local_work_trajectory(project_root, trajectory)


def merge_local_work_lane(
    project_root: str | Path,
    *,
    source_lane_id: str,
    target_lane_id: str = "lane:main",
    title: str = "merge",
    summary: str = "",
    source_event_id: str | None = None,
    target_event_id: str | None = None,
) -> Path:
    """Merge a source lane into a target lane with an explicit merge event."""

    trajectory = _load_single_line_lifecycle(project_root)
    if source_lane_id not in trajectory.lanes:
        raise ValueError(f"unknown source trajectory lane: {source_lane_id}")
    if target_lane_id not in trajectory.lanes:
        raise ValueError(f"unknown target trajectory lane: {target_lane_id}")
    if source_lane_id == target_lane_id:
        raise ValueError("merge requires distinct source and target lanes")

    source_events = _ordered_lane_events(trajectory, source_lane_id)
    target_events = _ordered_lane_events(trajectory, target_lane_id)
    if not source_events:
        raise ValueError(f"source trajectory lane has no events: {source_lane_id}")
    if not target_events:
        raise ValueError(f"target trajectory lane has no events: {target_lane_id}")

    source_event = _select_merge_source_event(
        trajectory,
        source_events,
        source_event_id=source_event_id,
    )
    target_event = (
        _select_current_event(
            trajectory,
            target_events,
            current_event_id=target_event_id,
            allowed_statuses={"in_progress", "pending", "blocked", "waiting", "completed"},
        )
        if target_event_id
        else (target_events[-1])
    )

    now = datetime.now(timezone.utc).isoformat()
    if source_event.status != "completed":
        trajectory.events[source_event.id] = replace(
            source_event,
            status="completed",
            metadata={
                **dict(source_event.metadata),
                "completed_at": now,
                "merged_at": now,
                "merged_into_lane": target_lane_id,
            },
        )
    if target_event.status != "completed":
        trajectory.events[target_event.id] = replace(
            target_event,
            status="completed",
            metadata={
                **dict(target_event.metadata),
                "completed_at": now,
                "completed_before_merge_at": now,
            },
        )

    merge_event_id = _next_event_id(trajectory, len(trajectory.events) + 1)
    next_order = (target_events[-1].order if target_events else 0) + 1
    trajectory.add_event(
        TrajectoryEvent(
            id=merge_event_id,
            lane_id=target_lane_id,
            title=title,
            kind="merge",
            status="in_progress",
            order=next_order,
            summary=summary,
            metadata={
                "created_at": now,
                "activated_at": now,
                "source": "single-line-lifecycle",
                "source_lane_id": source_lane_id,
                "target_lane_id": target_lane_id,
                "source_event_id": source_event.id,
                "target_event_id": target_event.id,
            },
        )
    )
    trajectory.add_relation(
        TrajectoryRelation(
            source_event_id=target_event.id,
            target_event_id=merge_event_id,
            kind="sequence",
            metadata={"source": "single-line-lifecycle"},
        )
    )
    trajectory.add_relation(
        TrajectoryRelation(
            source_event_id=source_event.id,
            target_event_id=merge_event_id,
            kind="merges_into",
            summary=summary,
            metadata={
                "source": "single-line-lifecycle",
                "source_lane_id": source_lane_id,
                "target_lane_id": target_lane_id,
            },
        )
    )
    _refresh_single_lane_status(trajectory, source_lane_id)
    _refresh_single_lane_status(trajectory, target_lane_id)
    trajectory.metadata["lane_mode"] = "multi"
    trajectory.validate()
    return write_local_work_trajectory(project_root, trajectory)


def add_local_work_relation(
    project_root: str | Path,
    *,
    source_event_id: str,
    target_event_id: str,
    relation_kind: str,
    summary: str = "",
    metadata: dict[str, str] | None = None,
) -> Path:
    """Add or update an explicit non-sequence relation between existing events."""

    normalized_kind = relation_kind.strip()
    if normalized_kind == "sequence":
        raise ValueError("local work relation cannot use sequence; append owns sequence edges")
    if normalized_kind not in _LOCAL_WORK_RELATION_KINDS:
        allowed = ", ".join(sorted(_LOCAL_WORK_RELATION_KINDS))
        raise ValueError(f"unknown local work relation kind: {relation_kind}; expected one of: {allowed}")
    if not source_event_id:
        raise ValueError("local work relation requires source_event_id")
    if not target_event_id:
        raise ValueError("local work relation requires target_event_id")
    if source_event_id == target_event_id:
        raise ValueError("local work relation requires distinct source and target events")

    trajectory = _load_single_line_lifecycle(project_root)
    if source_event_id not in trajectory.events:
        raise ValueError(f"unknown source trajectory event: {source_event_id}")
    if target_event_id not in trajectory.events:
        raise ValueError(f"unknown target trajectory event: {target_event_id}")

    source_event = trajectory.events[source_event_id]
    target_event = trajectory.events[target_event_id]
    now = datetime.now(timezone.utc).isoformat()
    relation_metadata = {
        "source": "single-line-lifecycle",
        "created_or_updated_at": now,
        "source_lane_id": source_event.lane_id,
        "target_lane_id": target_event.lane_id,
        **dict(metadata or {}),
    }
    next_relation = TrajectoryRelation(
        source_event_id=source_event_id,
        target_event_id=target_event_id,
        kind=normalized_kind,
        summary=summary,
        metadata=relation_metadata,
    )

    for index, relation in enumerate(trajectory.relations):
        if (
            relation.source_event_id == source_event_id
            and relation.target_event_id == target_event_id
            and relation.kind == normalized_kind
        ):
            trajectory.relations[index] = replace(
                relation,
                summary=summary or relation.summary,
                metadata={
                    **dict(relation.metadata),
                    **relation_metadata,
                },
            )
            break
    else:
        trajectory.add_relation(next_relation)

    if len(trajectory.lanes) > 1:
        trajectory.metadata["lane_mode"] = "multi"
    trajectory.validate()
    return write_local_work_trajectory(project_root, trajectory)


def build_checkpoint_work_trajectory(project_root: str | Path) -> LocalWorkTrajectory:
    root = Path(project_root)
    checkpoint_path = root / ".codex/checkpoints/latest.md"
    checkpoint = read_checkpoint(checkpoint_path)
    recorded_at = str(checkpoint.get("timestamp") or "").strip()
    if not recorded_at:
        recorded_at = datetime.now(timezone.utc).isoformat()

    planning_gate = str(checkpoint.get("planning_gate") or "").strip()
    phase = str(checkpoint.get("phase") or "").strip()
    current_handoff = checkpoint.get("current_handoff") or {}
    guide_context = planning_gate or phase or "checkpoint-current"
    scope_key = str(current_handoff.get("scope_key") or "").strip()

    trajectory = LocalWorkTrajectory(
        trajectory_id="local-work:checkpoint-current",
        title="Checkpoint Local Work Trajectory",
        recorded_at=recorded_at,
        source_graph_id="checkpoint-current",
        source_node_id="milestone:current-phase" if phase else "",
        guide_context=guide_context,
        metadata={
            "source_path": checkpoint_path.relative_to(root).as_posix(),
            "phase": phase,
            "planning_gate": planning_gate,
            "scope_key": scope_key,
            "projection": "single-lane-checkpoint-todos",
        },
    )
    lane = TrajectoryLane(
        id="lane:main",
        label=_lane_label(planning_gate=planning_gate, phase=phase),
        status=_lane_status(tuple(checkpoint.get("todos") or ())),
        summary="Single-lane projection of current checkpoint todos.",
        metadata={
            "source_section": "Current Todo",
            "context": guide_context,
        },
    )
    trajectory.add_lane(lane)

    previous_event_id: str | None = None
    for index, todo in enumerate(checkpoint.get("todos") or (), start=1):
        event_id = f"event:{index:03d}"
        status = _map_checkbox_status(str(todo.get("status", "not-started")))
        trajectory.add_event(
            TrajectoryEvent(
                id=event_id,
                lane_id=lane.id,
                title=str(todo.get("title", "")),
                kind="task",
                status=status,
                order=index,
                metadata={
                    "source_section": "Current Todo",
                    "checkpoint_todo_id": f"todo:{index:03d}",
                    "raw_status": str(todo.get("status", "")),
                },
            )
        )
        if previous_event_id:
            trajectory.add_relation(
                TrajectoryRelation(
                    source_event_id=previous_event_id,
                    target_event_id=event_id,
                    kind="sequence",
                    metadata={"source_section": "Current Todo"},
                )
            )
        previous_event_id = event_id

    trajectory.validate()
    return trajectory


def _lane_label(*, planning_gate: str, phase: str) -> str:
    source = planning_gate or phase or "当前工作"
    if "/" in source:
        source = source.rsplit("/", 1)[-1]
    if source.endswith(".md"):
        source = source[:-3]
    source = source.replace("-", " ").replace("_", " ").strip()
    if not source:
        return "当前工作"
    return source[:24]


def _lane_status(todos: tuple[object, ...]) -> TrajectoryLaneStatus:
    if not todos:
        return "pending"
    statuses = [str(getattr(todo, "get", lambda key, default=None: default)("status", "")) for todo in todos]
    if any(status in {"blocked"} for status in statuses):
        return "blocked"
    if any(status in {"in-progress", "in_progress"} for status in statuses):
        return "active"
    if all(status in {"done", "completed", "archived"} for status in statuses):
        return "done"
    return "pending"


def _map_checkbox_status(status: str) -> TrajectoryEventStatus:
    normalized = status.strip().lower().replace("_", "-")
    if normalized in {"done", "completed", "x"}:
        return "completed"
    if normalized in {"in-progress", "progress", "-"}:
        return "in_progress"
    if normalized == "blocked":
        return "blocked"
    if normalized == "archived":
        return "archived"
    return "pending"


def _is_single_line_lifecycle(trajectory: LocalWorkTrajectory) -> bool:
    return (
        trajectory.metadata.get("projection") == "single-lane-lifecycle"
        and trajectory.metadata.get("lane_mode") in {"single", "multi"}
    )


def _load_single_line_lifecycle(project_root: str | Path) -> LocalWorkTrajectory:
    trajectory = load_local_work_trajectory(project_root)
    if not _is_single_line_lifecycle(trajectory):
        raise ValueError(
            "local work trajectory is not owned by the single-line lifecycle; "
            "call start_single_line_trajectory first"
        )
    if not trajectory.lanes:
        raise ValueError("local work trajectory has no lanes")
    return trajectory


def _single_lane(trajectory: LocalWorkTrajectory) -> TrajectoryLane:
    if len(trajectory.lanes) != 1:
        raise ValueError("single-line lifecycle requires exactly one lane")
    return next(iter(trajectory.lanes.values()))


def _primary_lane(trajectory: LocalWorkTrajectory) -> TrajectoryLane:
    if "lane:main" in trajectory.lanes:
        return trajectory.lanes["lane:main"]
    return next(iter(sorted(trajectory.lanes.values(), key=lambda lane: lane.id)))


def _lane_for_current_or_primary(
    trajectory: LocalWorkTrajectory,
    *,
    current_event_id: str | None,
) -> TrajectoryLane:
    if current_event_id:
        if current_event_id not in trajectory.events:
            raise ValueError(f"unknown trajectory event: {current_event_id}")
        event = trajectory.events[current_event_id]
        return trajectory.lanes[event.lane_id]
    return _primary_lane(trajectory)


def _lane_by_id_or_primary(
    trajectory: LocalWorkTrajectory,
    lane_id: str,
) -> TrajectoryLane:
    if not lane_id:
        return _primary_lane(trajectory)
    if lane_id not in trajectory.lanes:
        raise ValueError(f"unknown trajectory lane: {lane_id}")
    return trajectory.lanes[lane_id]


def _ordered_lane_events(
    trajectory: LocalWorkTrajectory,
    lane_id: str,
) -> list[TrajectoryEvent]:
    return sorted(
        (event for event in trajectory.events.values() if event.lane_id == lane_id),
        key=lambda event: (event.order, event.id),
    )


def _first_event_with_status(
    events: list[TrajectoryEvent],
    status: TrajectoryEventStatus,
) -> TrajectoryEvent | None:
    return next((event for event in events if event.status == status), None)


def _select_current_event(
    trajectory: LocalWorkTrajectory,
    events: list[TrajectoryEvent],
    *,
    current_event_id: str | None,
    allowed_statuses: set[TrajectoryEventStatus],
) -> TrajectoryEvent:
    if current_event_id:
        if current_event_id not in trajectory.events:
            raise ValueError(f"unknown trajectory event: {current_event_id}")
        event = trajectory.events[current_event_id]
        if event.status not in allowed_statuses:
            allowed = ", ".join(sorted(allowed_statuses))
            raise ValueError(
                f"trajectory event {current_event_id} has status {event.status}; "
                f"expected one of: {allowed}"
            )
        return event

    for status in ("in_progress", "blocked", "waiting", "pending", "completed", "archived"):
        if status not in allowed_statuses:
            continue
        event = _first_event_with_status(events, status)
        if event is not None:
            return event
    raise ValueError("single-line trajectory has no current event to update")


def _select_merge_source_event(
    trajectory: LocalWorkTrajectory,
    events: list[TrajectoryEvent],
    *,
    source_event_id: str | None,
) -> TrajectoryEvent:
    if source_event_id:
        return _select_current_event(
            trajectory,
            events,
            current_event_id=source_event_id,
            allowed_statuses={"in_progress", "pending", "blocked", "waiting", "completed"},
        )

    for status in ("in_progress", "blocked", "waiting", "pending"):
        event = _first_event_with_status(events, status)
        if event is not None:
            return event

    completed_events = [event for event in events if event.status == "completed"]
    if completed_events:
        return completed_events[-1]
    raise ValueError("source trajectory lane has no mergeable event")


def _next_pending_event_after(
    events: list[TrajectoryEvent],
    order: int,
) -> TrajectoryEvent | None:
    return next(
        (event for event in events if event.order > order and event.status == "pending"),
        None,
    )


def _next_event_id(
    trajectory: LocalWorkTrajectory,
    preferred_order: int,
) -> str:
    order = preferred_order
    while True:
        candidate = f"event:{order:03d}"
        if candidate not in trajectory.events:
            return candidate
        order += 1


def _next_lane_id(trajectory: LocalWorkTrajectory) -> str:
    index = 2
    while True:
        candidate = f"lane:{index:03d}"
        if candidate not in trajectory.lanes:
            return candidate
        index += 1


def _refresh_single_lane_status(
    trajectory: LocalWorkTrajectory,
    lane_id: str,
) -> None:
    lane = trajectory.lanes[lane_id]
    events = _ordered_lane_events(trajectory, lane_id)
    if not events:
        status: TrajectoryLaneStatus = "pending"
    elif any(event.status == "blocked" for event in events):
        status = "blocked"
    elif any(event.status == "waiting" for event in events):
        status = "waiting"
    elif any(event.status == "in_progress" for event in events):
        status = "active"
    elif all(event.status in {"completed", "archived"} for event in events):
        status = "done"
    else:
        status = "pending"
    trajectory.lanes[lane_id] = replace(lane, status=status)
