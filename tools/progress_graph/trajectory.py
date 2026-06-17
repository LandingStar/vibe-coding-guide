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
    "compound",
    "merge",
    "close",
]
TRAJECTORY_EVENT_KINDS: set[str] = {
    "start",
    "task",
    "decision",
    "review",
    "wait",
    "validation",
    "writeback",
    "handoff",
    "compound",
    "merge",
    "close",
}
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


@dataclass(frozen=True)
class TrajectoryEndpoint:
    """A precise relation endpoint inside a trajectory tree."""

    trajectory_id: str
    event_id: str
    parent_event_id: str = ""
    compound_path: str = ""

    def to_metadata(self, prefix: str) -> dict[str, str]:
        metadata = {
            f"{prefix}_endpoint_trajectory_id": self.trajectory_id,
            f"{prefix}_endpoint_event_id": self.event_id,
        }
        if self.parent_event_id:
            metadata[f"{prefix}_endpoint_parent_event_id"] = self.parent_event_id
        if self.compound_path:
            metadata[f"{prefix}_endpoint_compound_path"] = self.compound_path
        return metadata


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
        child_trajectories: dict[str, "LocalWorkTrajectory"] | None = None,
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
        self.child_trajectories: dict[str, LocalWorkTrajectory] = dict(
            child_trajectories or {}
        )

    def add_lane(self, lane: TrajectoryLane) -> None:
        self.lanes[lane.id] = lane

    def add_event(self, event: TrajectoryEvent) -> None:
        self.events[event.id] = event

    def add_relation(self, relation: TrajectoryRelation) -> None:
        self.relations.append(relation)

    def add_child_trajectory(self, trajectory: "LocalWorkTrajectory") -> None:
        self.child_trajectories[trajectory.trajectory_id] = trajectory

    def check_invariants(self) -> list[str]:
        errors: list[str] = []
        _check_local_work_trajectory_invariants(self, errors, set())
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
            "child_trajectories": {
                trajectory_id: child_trajectory.to_dict()
                for trajectory_id, child_trajectory in sorted(
                    self.child_trajectories.items()
                )
            },
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
        for child_data in dict(data.get("child_trajectories", {})).values():
            child_trajectory = cls.from_dict(dict(child_data))
            trajectory.add_child_trajectory(child_trajectory)
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


def set_local_work_trajectory_anchor(
    project_root: str | Path,
    *,
    source_graph_id: str = "",
    source_node_id: str = "",
    summary: str = "",
    reason: str = "",
) -> Path:
    """Set or clear the global progress-graph anchor for the current trajectory."""

    graph_id = source_graph_id.strip()
    node_id = source_node_id.strip()
    if bool(graph_id) != bool(node_id):
        raise ValueError(
            "trajectory anchor requires source_graph_id and source_node_id together, "
            "or neither when clearing the anchor"
        )

    trajectory = _load_single_line_lifecycle(project_root)
    previous_graph_id = trajectory.source_graph_id
    previous_node_id = trajectory.source_node_id
    trajectory.source_graph_id = graph_id
    trajectory.source_node_id = node_id
    now = datetime.now(timezone.utc).isoformat()
    trajectory.metadata["anchor_updated_at"] = now
    if graph_id and node_id:
        trajectory.metadata["anchor_state"] = "set"
        trajectory.metadata["anchor_graph_id"] = graph_id
        trajectory.metadata["anchor_node_id"] = node_id
    else:
        trajectory.metadata["anchor_state"] = "cleared"
        trajectory.metadata.pop("anchor_graph_id", None)
        trajectory.metadata.pop("anchor_node_id", None)
    if previous_graph_id or previous_node_id:
        trajectory.metadata["previous_anchor_graph_id"] = previous_graph_id
        trajectory.metadata["previous_anchor_node_id"] = previous_node_id
    else:
        trajectory.metadata.pop("previous_anchor_graph_id", None)
        trajectory.metadata.pop("previous_anchor_node_id", None)
    if summary:
        trajectory.metadata["anchor_summary"] = summary
    elif "anchor_summary" in trajectory.metadata:
        trajectory.metadata.pop("anchor_summary")
    if reason:
        trajectory.metadata["anchor_reason"] = reason
    elif "anchor_reason" in trajectory.metadata:
        trajectory.metadata.pop("anchor_reason")
    return write_local_work_trajectory(project_root, trajectory)


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
        source_graph_id="",
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
    source_graph_id: str = "",
    source_node_id: str = "",
    trajectory_id: str = "local-work:single-line-current",
    lane_id: str = "lane:main",
    metadata: dict[str, str] | None = None,
    event_metadata: dict[str, str] | None = None,
) -> Path:
    """Create the first single-line lane and its first active event."""

    graph_id = source_graph_id.strip()
    node_id = source_node_id.strip()
    if bool(graph_id) != bool(node_id):
        raise ValueError(
            "trajectory start anchor requires source_graph_id and source_node_id together, "
            "or neither when starting an unanchored trajectory"
        )

    now = datetime.now(timezone.utc).isoformat()
    trajectory_metadata = {
        "projection": "single-lane-lifecycle",
        "lane_mode": "single",
        "lifecycle_version": "1",
        **dict(metadata or {}),
    }
    if graph_id and node_id:
        trajectory_metadata.update(
            {
                "anchor_state": "set",
                "anchor_graph_id": graph_id,
                "anchor_node_id": node_id,
                "anchor_updated_at": now,
            }
        )
    trajectory = LocalWorkTrajectory(
        trajectory_id=trajectory_id,
        title=title,
        recorded_at=now,
        source_graph_id=graph_id,
        source_node_id=node_id,
        guide_context=guide_context,
        metadata=trajectory_metadata,
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


def add_local_work_compound(
    project_root: str | Path,
    *,
    title: str,
    summary: str = "",
    lane_id: str = "",
    first_child_event_title: str = "",
    first_child_event_kind: TrajectoryEventKind = "task",
    first_child_event_summary: str = "",
    child_lane_label: str = "compound work",
) -> Path:
    """Append a planned compound event and create its child trajectory.

    This is the forward-planning form of hierarchy: it creates a large event and
    an empty or seeded child trajectory. It intentionally does not move or pack
    existing events; retrospective interval packing is a separate operation.
    """

    if not title:
        raise ValueError("local work compound requires title")

    trajectory = _load_single_line_lifecycle(project_root)
    lane = _lane_by_id_or_primary(trajectory, lane_id)
    ordered_events = _ordered_lane_events(trajectory, lane.id)
    previous_event = ordered_events[-1] if ordered_events else None
    next_order = (previous_event.order if previous_event else 0) + 1
    event_id = _next_event_id(trajectory, next_order)
    now = datetime.now(timezone.utc).isoformat()
    child_trajectory_id = _child_trajectory_id(trajectory, event_id)
    child_trajectory = LocalWorkTrajectory(
        trajectory_id=child_trajectory_id,
        title=title,
        recorded_at=now,
        source_graph_id=trajectory.trajectory_id,
        source_node_id=event_id,
        guide_context=trajectory.guide_context,
        metadata={
            "projection": "local-work-compound-child",
            "parent_trajectory_id": trajectory.trajectory_id,
            "parent_event_id": event_id,
            "compound_mode": "planned",
            "lifecycle_version": trajectory.metadata.get("lifecycle_version", "1"),
        },
    )
    child_status: TrajectoryEventStatus = "pending"
    if first_child_event_title:
        child_trajectory.add_lane(
            TrajectoryLane(
                id="lane:main",
                label=child_lane_label or title,
                status="active",
                summary="Child trajectory for a planned compound event.",
                metadata={
                    "line_kind": "compound-child",
                    "created_at": now,
                    "source": "single-line-lifecycle",
                    "parent_event_id": event_id,
                },
            )
        )
        child_trajectory.add_event(
            TrajectoryEvent(
                id="event:001",
                lane_id="lane:main",
                title=first_child_event_title,
                kind=first_child_event_kind,
                status="in_progress",
                order=1,
                summary=first_child_event_summary,
                metadata={
                    "created_at": now,
                    "activated_at": now,
                    "source": "single-line-lifecycle",
                    "parent_event_id": event_id,
                },
            )
        )
        child_status = "in_progress"

    trajectory.add_child_trajectory(child_trajectory)
    trajectory.add_event(
        TrajectoryEvent(
            id=event_id,
            lane_id=lane.id,
            title=title,
            kind="compound",
            status=child_status,
            order=next_order,
            summary=summary,
            metadata={
                "created_at": now,
                "source": "single-line-lifecycle",
                "compound_mode": "planned",
                "child_trajectory_id": child_trajectory_id,
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


def pack_local_work_range(
    project_root: str | Path,
    *,
    title: str,
    range_start_event_id: str,
    range_end_event_id: str,
    summary: str = "",
    child_lane_label: str = "",
) -> Path:
    """Pack a continuous same-lane event range into a compound event.

    The parent lane keeps one compound event in place of the selected interval.
    The original events and interval-internal relations are preserved in the
    child trajectory. Cross-boundary non-sequence relations are rewired to the
    compound event so the parent graph does not retain dangling edges.
    """

    if not title:
        raise ValueError("local work packRange requires title")
    if not range_start_event_id:
        raise ValueError("local work packRange requires range_start_event_id")
    if not range_end_event_id:
        raise ValueError("local work packRange requires range_end_event_id")

    trajectory = _load_single_line_lifecycle(project_root)
    if range_start_event_id not in trajectory.events:
        raise ValueError(f"unknown range start trajectory event: {range_start_event_id}")
    if range_end_event_id not in trajectory.events:
        raise ValueError(f"unknown range end trajectory event: {range_end_event_id}")

    start_event = trajectory.events[range_start_event_id]
    end_event = trajectory.events[range_end_event_id]
    if start_event.lane_id != end_event.lane_id:
        raise ValueError("local work packRange requires events from the same lane")
    lane = trajectory.lanes[start_event.lane_id]
    ordered_events = _ordered_lane_events(trajectory, lane.id)
    start_index = _event_index(ordered_events, range_start_event_id)
    end_index = _event_index(ordered_events, range_end_event_id)
    if start_index > end_index:
        start_index, end_index = end_index, start_index
    packed_events = ordered_events[start_index : end_index + 1]
    if not packed_events:
        raise ValueError("local work packRange selected an empty range")

    packed_event_ids = {event.id for event in packed_events}
    previous_event = ordered_events[start_index - 1] if start_index > 0 else None
    next_event = ordered_events[end_index + 1] if end_index + 1 < len(ordered_events) else None
    compound_event_id = _next_event_id(trajectory, packed_events[0].order)
    now = datetime.now(timezone.utc).isoformat()
    child_trajectory_id = _child_trajectory_id(trajectory, compound_event_id)
    child_status = _status_for_packed_events(packed_events)
    child_trajectory = LocalWorkTrajectory(
        trajectory_id=child_trajectory_id,
        title=title,
        recorded_at=now,
        source_graph_id=trajectory.trajectory_id,
        source_node_id=compound_event_id,
        guide_context=trajectory.guide_context,
        metadata={
            "projection": "local-work-compound-child",
            "parent_trajectory_id": trajectory.trajectory_id,
            "parent_event_id": compound_event_id,
            "compound_mode": "packed-range",
            "packed_lane_id": lane.id,
            "packed_event_ids": ",".join(event.id for event in packed_events),
            "range_start_event_id": packed_events[0].id,
            "range_end_event_id": packed_events[-1].id,
            "lifecycle_version": trajectory.metadata.get("lifecycle_version", "1"),
        },
    )
    child_trajectory.add_lane(
        TrajectoryLane(
            id="lane:main",
            label=child_lane_label or title,
            status=_lane_status_for_events(packed_events),
            summary=f"Packed range from parent lane {lane.id}.",
            metadata={
                "line_kind": "compound-child",
                "created_at": now,
                "source": "single-line-lifecycle",
                "parent_event_id": compound_event_id,
                "source_lane_id": lane.id,
            },
        )
    )
    for index, event in enumerate(packed_events, start=1):
        nested_child_trajectory_id = event.metadata.get("child_trajectory_id", "")
        if nested_child_trajectory_id:
            nested_child = trajectory.child_trajectories.get(nested_child_trajectory_id)
            if nested_child is not None:
                child_trajectory.add_child_trajectory(nested_child)
        child_trajectory.add_event(
            replace(
                event,
                lane_id="lane:main",
                order=index,
                metadata={
                    **dict(event.metadata),
                    "packed_from_trajectory_id": trajectory.trajectory_id,
                    "packed_from_lane_id": lane.id,
                    "packed_from_event_id": event.id,
                    "packed_into_event_id": compound_event_id,
                    "packed_at": now,
                },
            )
        )

    parent_relations: list[TrajectoryRelation] = []
    child_relation_keys: set[tuple[str, str, str]] = set()
    for relation in trajectory.relations:
        source_inside = relation.source_event_id in packed_event_ids
        target_inside = relation.target_event_id in packed_event_ids
        if source_inside and target_inside:
            child_relation = replace(
                relation,
                metadata={
                    **dict(relation.metadata),
                    "packed_from_trajectory_id": trajectory.trajectory_id,
                    "packed_into_event_id": compound_event_id,
                },
            )
            child_key = (
                child_relation.source_event_id,
                child_relation.target_event_id,
                child_relation.kind,
            )
            if child_key not in child_relation_keys:
                child_trajectory.add_relation(child_relation)
                child_relation_keys.add(child_key)
            continue
        if relation.kind == "sequence" and (source_inside or target_inside):
            continue
        if source_inside or target_inside:
            rewired_relation = replace(
                relation,
                source_event_id=compound_event_id if source_inside else relation.source_event_id,
                target_event_id=compound_event_id if target_inside else relation.target_event_id,
                metadata={
                    **dict(relation.metadata),
                    "rewired_from_packed_range": "true",
                    "packed_child_trajectory_id": child_trajectory_id,
                },
            )
            if rewired_relation.source_event_id == rewired_relation.target_event_id:
                continue
            parent_relations.append(rewired_relation)
            continue
        parent_relations.append(relation)

    for event_id in packed_event_ids:
        del trajectory.events[event_id]
    for event in packed_events:
        nested_child_trajectory_id = event.metadata.get("child_trajectory_id", "")
        if nested_child_trajectory_id:
            trajectory.child_trajectories.pop(nested_child_trajectory_id, None)
    compound_event = TrajectoryEvent(
        id=compound_event_id,
        lane_id=lane.id,
        title=title,
        kind="compound",
        status=child_status,
        order=packed_events[0].order,
        summary=summary,
        metadata={
            "created_at": now,
            "source": "single-line-lifecycle",
            "compound_mode": "packed-range",
            "child_trajectory_id": child_trajectory_id,
            "packed_lane_id": lane.id,
            "packed_event_ids": ",".join(event.id for event in packed_events),
            "range_start_event_id": packed_events[0].id,
            "range_end_event_id": packed_events[-1].id,
        },
    )
    trajectory.add_child_trajectory(child_trajectory)
    trajectory.add_event(compound_event)

    remaining_lane_events = _ordered_lane_events(trajectory, lane.id)
    reordered_parent_relations = _drop_sequence_relations_for_lane(
        parent_relations,
        {event.id for event in remaining_lane_events},
    )
    trajectory.relations = reordered_parent_relations
    _renumber_lane_events(trajectory, lane.id)
    _rebuild_lane_sequence_relations(trajectory, lane.id)
    _refresh_single_lane_status(trajectory, lane.id)
    trajectory.validate()
    return write_local_work_trajectory(project_root, trajectory)


def pack_local_work_subgraph(
    project_root: str | Path,
    *,
    title: str,
    ranges: list[dict[str, str]] | str,
    anchor_lane_id: str = "",
    summary: str = "",
) -> Path:
    """Pack lane-local continuous ranges into one compound child trajectory."""

    if not title:
        raise ValueError("local work packSubgraph requires title")
    normalized_ranges = _normalize_pack_subgraph_ranges(ranges)
    if not normalized_ranges:
        raise ValueError("local work packSubgraph requires at least one range")

    trajectory = _load_single_line_lifecycle(project_root)
    selected_by_lane: dict[str, list[TrajectoryEvent]] = {}
    for range_spec in normalized_ranges:
        lane_id = range_spec["lane_id"]
        if lane_id not in trajectory.lanes:
            raise ValueError(f"unknown trajectory lane: {lane_id}")
        start_event_id = range_spec["range_start_event_id"]
        end_event_id = range_spec["range_end_event_id"]
        if start_event_id not in trajectory.events:
            raise ValueError(f"unknown range start trajectory event: {start_event_id}")
        if end_event_id not in trajectory.events:
            raise ValueError(f"unknown range end trajectory event: {end_event_id}")
        start_event = trajectory.events[start_event_id]
        end_event = trajectory.events[end_event_id]
        if start_event.lane_id != lane_id or end_event.lane_id != lane_id:
            raise ValueError("local work packSubgraph range events must belong to range lane")
        ordered_events = _ordered_lane_events(trajectory, lane_id)
        start_index = _event_index(ordered_events, start_event_id)
        end_index = _event_index(ordered_events, end_event_id)
        if start_index > end_index:
            start_index, end_index = end_index, start_index
        selected_by_lane[lane_id] = ordered_events[start_index : end_index + 1]

    packed_event_ids: set[str] = set()
    for lane_id, lane_events in selected_by_lane.items():
        if not lane_events:
            raise ValueError(f"local work packSubgraph selected an empty range for lane {lane_id}")
        for event in lane_events:
            if event.id in packed_event_ids:
                raise ValueError(f"local work packSubgraph selected event more than once: {event.id}")
            packed_event_ids.add(event.id)

    selected_lane_ids = list(selected_by_lane)
    resolved_anchor_lane_id = anchor_lane_id or selected_lane_ids[0]
    if resolved_anchor_lane_id not in selected_by_lane:
        raise ValueError("local work packSubgraph anchor_lane_id must be one of the selected lanes")

    now = datetime.now(timezone.utc).isoformat()
    reserved_event_ids: set[str] = set()
    anchor_first_event = selected_by_lane[resolved_anchor_lane_id][0]
    anchor_event_id = _next_event_id_excluding(
        trajectory,
        anchor_first_event.order,
        reserved_event_ids,
    )
    reserved_event_ids.add(anchor_event_id)
    proxy_event_ids: dict[str, str] = {}
    for lane_id in selected_lane_ids:
        if lane_id == resolved_anchor_lane_id:
            continue
        first_event = selected_by_lane[lane_id][0]
        proxy_event_id = _next_event_id_excluding(
            trajectory,
            first_event.order,
            reserved_event_ids,
        )
        reserved_event_ids.add(proxy_event_id)
        proxy_event_ids[lane_id] = proxy_event_id

    child_trajectory_id = _child_trajectory_id(trajectory, anchor_event_id)
    ordered_packed_events = [
        event
        for lane_id in selected_lane_ids
        for event in selected_by_lane[lane_id]
    ]
    packed_event_ids_text = ",".join(event.id for event in ordered_packed_events)
    child_trajectory = LocalWorkTrajectory(
        trajectory_id=child_trajectory_id,
        title=title,
        recorded_at=now,
        source_graph_id=trajectory.trajectory_id,
        source_node_id=anchor_event_id,
        guide_context=trajectory.guide_context,
        metadata={
            "projection": "local-work-compound-child",
            "parent_trajectory_id": trajectory.trajectory_id,
            "parent_event_id": anchor_event_id,
            "compound_mode": "packed-multi-line",
            "anchor_lane_id": resolved_anchor_lane_id,
            "packed_lane_ids": ",".join(selected_lane_ids),
            "packed_event_ids": packed_event_ids_text,
            "lifecycle_version": trajectory.metadata.get("lifecycle_version", "1"),
        },
    )

    for lane_id in selected_lane_ids:
        parent_lane = trajectory.lanes[lane_id]
        lane_events = selected_by_lane[lane_id]
        child_trajectory.add_lane(
            TrajectoryLane(
                id=lane_id,
                label=parent_lane.label,
                status=_lane_status_for_events(lane_events),
                summary=f"Packed range from parent lane {lane_id}.",
                metadata={
                    **dict(parent_lane.metadata),
                    "line_kind": "compound-child",
                    "created_at": now,
                    "source": "single-line-lifecycle",
                    "source_lane_id": lane_id,
                    "packed_from_trajectory_id": trajectory.trajectory_id,
                    "packed_into_event_id": anchor_event_id,
                },
            )
        )
        for index, event in enumerate(lane_events, start=1):
            nested_child_trajectory_id = event.metadata.get("child_trajectory_id", "")
            if nested_child_trajectory_id:
                nested_child = trajectory.child_trajectories.get(nested_child_trajectory_id)
                if nested_child is not None:
                    child_trajectory.add_child_trajectory(nested_child)
            child_trajectory.add_event(
                replace(
                    event,
                    order=index,
                    metadata={
                        **dict(event.metadata),
                        "packed_from_trajectory_id": trajectory.trajectory_id,
                        "packed_from_lane_id": lane_id,
                        "packed_from_event_id": event.id,
                        "packed_into_event_id": anchor_event_id,
                        "packed_at": now,
                    },
                )
            )

    projection_event_by_packed_event: dict[str, str] = {}
    for lane_id, lane_events in selected_by_lane.items():
        projection_event_id = (
            anchor_event_id
            if lane_id == resolved_anchor_lane_id
            else proxy_event_ids[lane_id]
        )
        for event in lane_events:
            projection_event_by_packed_event[event.id] = projection_event_id

    parent_relations: list[TrajectoryRelation] = []
    child_relation_keys: set[tuple[str, str, str]] = set()
    for relation in trajectory.relations:
        source_inside = relation.source_event_id in packed_event_ids
        target_inside = relation.target_event_id in packed_event_ids
        if source_inside and target_inside:
            child_relation = replace(
                relation,
                metadata={
                    **dict(relation.metadata),
                    "packed_from_trajectory_id": trajectory.trajectory_id,
                    "packed_into_event_id": anchor_event_id,
                },
            )
            child_key = (
                child_relation.source_event_id,
                child_relation.target_event_id,
                child_relation.kind,
            )
            if child_key not in child_relation_keys:
                child_trajectory.add_relation(child_relation)
                child_relation_keys.add(child_key)
            continue
        if relation.kind == "sequence" and (source_inside or target_inside):
            continue
        if source_inside or target_inside:
            projected_source_event_id = (
                projection_event_by_packed_event[relation.source_event_id]
                if source_inside
                else relation.source_event_id
            )
            projected_target_event_id = (
                projection_event_by_packed_event[relation.target_event_id]
                if target_inside
                else relation.target_event_id
            )
            if projected_source_event_id == projected_target_event_id:
                continue
            source_endpoint = (
                TrajectoryEndpoint(
                    trajectory_id=child_trajectory_id,
                    event_id=relation.source_event_id,
                    parent_event_id=anchor_event_id,
                    compound_path=anchor_event_id,
                )
                if source_inside
                else TrajectoryEndpoint(
                    trajectory_id=trajectory.trajectory_id,
                    event_id=relation.source_event_id,
                )
            )
            target_endpoint = (
                TrajectoryEndpoint(
                    trajectory_id=child_trajectory_id,
                    event_id=relation.target_event_id,
                    parent_event_id=anchor_event_id,
                    compound_path=anchor_event_id,
                )
                if target_inside
                else TrajectoryEndpoint(
                    trajectory_id=trajectory.trajectory_id,
                    event_id=relation.target_event_id,
                )
            )
            parent_relations.append(
                replace(
                    relation,
                    source_event_id=projected_source_event_id,
                    target_event_id=projected_target_event_id,
                    metadata={
                        **dict(relation.metadata),
                        "rewired_from_packed_subgraph": "true",
                        "packed_child_trajectory_id": child_trajectory_id,
                        "relation_projection": "cross-boundary",
                        **source_endpoint.to_metadata("source"),
                        **target_endpoint.to_metadata("target"),
                    },
                )
            )
            continue
        parent_relations.append(relation)

    for event_id in packed_event_ids:
        del trajectory.events[event_id]
    for event in ordered_packed_events:
        nested_child_trajectory_id = event.metadata.get("child_trajectory_id", "")
        if nested_child_trajectory_id:
            trajectory.child_trajectories.pop(nested_child_trajectory_id, None)

    anchor_event = TrajectoryEvent(
        id=anchor_event_id,
        lane_id=resolved_anchor_lane_id,
        title=title,
        kind="compound",
        status=_status_for_packed_events(ordered_packed_events),
        order=anchor_first_event.order,
        summary=summary,
        metadata={
            "created_at": now,
            "source": "single-line-lifecycle",
            "compound_mode": "packed-multi-line",
            "compound_role": "anchor",
            "child_trajectory_id": child_trajectory_id,
            "anchor_lane_id": resolved_anchor_lane_id,
            "packed_lane_ids": ",".join(selected_lane_ids),
            "packed_event_ids": packed_event_ids_text,
        },
    )
    trajectory.add_child_trajectory(child_trajectory)
    trajectory.add_event(anchor_event)
    for lane_id, proxy_event_id in proxy_event_ids.items():
        lane_events = selected_by_lane[lane_id]
        trajectory.add_event(
            TrajectoryEvent(
                id=proxy_event_id,
                lane_id=lane_id,
                title=title,
                kind="compound",
                status=_status_for_packed_events(lane_events),
                order=lane_events[0].order,
                summary=summary,
                metadata={
                    "created_at": now,
                    "source": "single-line-lifecycle",
                    "compound_mode": "packed-multi-line",
                    "compound_role": "proxy",
                    "anchor_compound_event_id": anchor_event_id,
                    "child_trajectory_id": child_trajectory_id,
                    "packed_lane_id": lane_id,
                    "packed_event_ids": ",".join(event.id for event in lane_events),
                },
            )
        )

    trajectory.relations = parent_relations
    for lane_id in selected_lane_ids:
        lane_event_ids = {event.id for event in _ordered_lane_events(trajectory, lane_id)}
        trajectory.relations = _drop_sequence_relations_for_lane(
            trajectory.relations,
            lane_event_ids,
        )
        _renumber_lane_events(trajectory, lane_id)
        _rebuild_lane_sequence_relations(trajectory, lane_id)
        _refresh_single_lane_status(trajectory, lane_id)
    trajectory.metadata["lane_mode"] = "multi" if len(trajectory.lanes) > 1 else "single"
    trajectory.validate()
    return write_local_work_trajectory(project_root, trajectory)


def append_local_work_child_event(
    project_root: str | Path,
    *,
    title: str,
    child_trajectory_id: str = "",
    parent_event_id: str = "",
    kind: TrajectoryEventKind = "task",
    status: TrajectoryEventStatus = "pending",
    summary: str = "",
    lane_id: str = "",
    child_lane_label: str = "compound work",
) -> Path:
    """Append an event inside an existing compound child trajectory."""

    if not title:
        raise ValueError("local work appendChild requires title")

    trajectory = _load_single_line_lifecycle(project_root)
    _, _, child_trajectory = _locate_child_context(
        trajectory,
        child_trajectory_id=child_trajectory_id,
        parent_event_id=parent_event_id,
    )
    lane = _child_lane_by_id_or_primary_or_create(
        child_trajectory,
        lane_id=lane_id,
        lane_label=child_lane_label,
    )
    ordered_events = _ordered_lane_events(child_trajectory, lane.id)
    previous_event = ordered_events[-1] if ordered_events else None
    next_order = (previous_event.order if previous_event else 0) + 1
    event_id = _next_event_id(child_trajectory, next_order)
    now = datetime.now(timezone.utc).isoformat()
    next_status = status
    if previous_event is None and status == "pending":
        next_status = "in_progress"

    child_trajectory.add_event(
        TrajectoryEvent(
            id=event_id,
            lane_id=lane.id,
            title=title,
            kind=kind,
            status=next_status,
            order=next_order,
            summary=summary,
            metadata={
                "created_at": now,
                "source": "compound-child-lifecycle",
            },
        )
    )
    if previous_event is not None:
        child_trajectory.add_relation(
            TrajectoryRelation(
                source_event_id=previous_event.id,
                target_event_id=event_id,
                kind="sequence",
                metadata={"source": "compound-child-lifecycle"},
            )
        )
    _refresh_single_lane_status(child_trajectory, lane.id)
    _refresh_all_compound_rollups(trajectory)
    trajectory.validate()
    return write_local_work_trajectory(project_root, trajectory)


def advance_local_work_child_event(
    project_root: str | Path,
    *,
    child_trajectory_id: str = "",
    parent_event_id: str = "",
    current_event_id: str | None = None,
    activate_next: bool = True,
) -> Path:
    """Complete the active event inside a compound child trajectory."""

    trajectory = _load_single_line_lifecycle(project_root)
    _, _, child_trajectory = _locate_child_context(
        trajectory,
        child_trajectory_id=child_trajectory_id,
        parent_event_id=parent_event_id,
    )
    lane = _lane_for_current_or_primary(
        child_trajectory,
        current_event_id=current_event_id,
    )
    ordered_events = _ordered_lane_events(child_trajectory, lane.id)
    if not ordered_events:
        raise ValueError("compound child trajectory has no events to advance")
    current = (
        child_trajectory.events[current_event_id]
        if current_event_id
        else _first_event_with_status(ordered_events, "in_progress")
    )
    now = datetime.now(timezone.utc).isoformat()

    if current is None:
        pending = _first_event_with_status(ordered_events, "pending")
        if pending is None:
            _refresh_single_lane_status(child_trajectory, lane.id)
            _refresh_all_compound_rollups(trajectory)
            return write_local_work_trajectory(project_root, trajectory)
        child_trajectory.events[pending.id] = replace(
            pending,
            status="in_progress",
            metadata={**dict(pending.metadata), "activated_at": now},
        )
        _refresh_single_lane_status(child_trajectory, lane.id)
        _refresh_all_compound_rollups(trajectory)
        return write_local_work_trajectory(project_root, trajectory)

    child_trajectory.events[current.id] = replace(
        current,
        status="completed",
        metadata={**dict(current.metadata), "completed_at": now},
    )
    if activate_next:
        ordered_events = _ordered_lane_events(child_trajectory, lane.id)
        next_event = _next_pending_event_after(ordered_events, current.order)
        if next_event is not None:
            child_trajectory.events[next_event.id] = replace(
                next_event,
                status="in_progress",
                metadata={**dict(next_event.metadata), "activated_at": now},
            )

    _refresh_single_lane_status(child_trajectory, lane.id)
    _refresh_all_compound_rollups(trajectory)
    trajectory.validate()
    return write_local_work_trajectory(project_root, trajectory)


def close_local_work_child_trajectory(
    project_root: str | Path,
    *,
    child_trajectory_id: str = "",
    parent_event_id: str = "",
    current_event_id: str | None = None,
    summary: str = "",
) -> Path:
    """Complete the current child event and close its primary lane."""

    trajectory = _load_single_line_lifecycle(project_root)
    _, _, child_trajectory = _locate_child_context(
        trajectory,
        child_trajectory_id=child_trajectory_id,
        parent_event_id=parent_event_id,
    )
    lane = _lane_for_current_or_primary(
        child_trajectory,
        current_event_id=current_event_id,
    )
    ordered_events = _ordered_lane_events(child_trajectory, lane.id)
    current = _select_current_event(
        child_trajectory,
        ordered_events,
        current_event_id=current_event_id,
        allowed_statuses={"in_progress", "pending", "blocked", "waiting"},
    )
    now = datetime.now(timezone.utc).isoformat()
    child_trajectory.events[current.id] = replace(
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
        child_trajectory.events[event.id] = replace(
            event,
            status="archived",
            metadata={
                **dict(event.metadata),
                "archived_at": now,
                "archive_reason": "compound child trajectory closed",
            },
        )
    _refresh_single_lane_status(child_trajectory, lane.id)
    _refresh_all_compound_rollups(trajectory)
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


def add_local_work_lanes(
    project_root: str | Path,
    *,
    lanes: list[dict[str, str]] | str,
    source_event_id: str | None = None,
) -> Path:
    """Add multiple lanes from one source event in a single trajectory write."""

    normalized_lanes = _normalize_add_lanes_specs(lanes)
    if not normalized_lanes:
        raise ValueError("local work addLanes requires at least one lane spec")

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

    now = datetime.now(timezone.utc).isoformat()
    used_lane_ids = set(trajectory.lanes)
    for index, lane_spec in enumerate(normalized_lanes, start=1):
        lane_id = lane_spec["lane_id"] or _next_lane_id_excluding(trajectory, used_lane_ids)
        if lane_id in used_lane_ids:
            raise ValueError(f"trajectory lane already exists or is duplicated: {lane_id}")
        used_lane_ids.add(lane_id)
        trajectory.add_lane(
            TrajectoryLane(
                id=lane_id,
                label=lane_spec["lane_label"],
                status="active",
                summary="Additional local work lane.",
                metadata={
                    "line_kind": "single",
                    "created_at": now,
                    "source": "single-line-lifecycle",
                    "batch_open_index": str(index),
                    "batch_open_count": str(len(normalized_lanes)),
                },
            )
        )
        event_id = _next_event_id(trajectory, len(trajectory.events) + 1)
        trajectory.add_event(
            TrajectoryEvent(
                id=event_id,
                lane_id=lane_id,
                title=lane_spec["first_event_title"],
                kind=lane_spec["event_kind"],
                status="in_progress",
                order=1,
                summary=lane_spec["summary"],
                metadata={
                    "created_at": now,
                    "activated_at": now,
                    "source": "single-line-lifecycle",
                    "batch_open_index": str(index),
                    "batch_open_count": str(len(normalized_lanes)),
                },
            )
        )
        if source_event is not None:
            trajectory.add_relation(
                TrajectoryRelation(
                    source_event_id=source_event.id,
                    target_event_id=event_id,
                    kind="proposes_new_line",
                    summary=f"Created lane {lane_id}",
                    metadata={
                        "source": "single-line-lifecycle",
                        "batch_open_index": str(index),
                        "batch_open_count": str(len(normalized_lanes)),
                    },
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
    source_endpoint: TrajectoryEndpoint | dict[str, str] | None = None,
    target_endpoint: TrajectoryEndpoint | dict[str, str] | None = None,
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
    if source_endpoint is None and target_endpoint is None and source_event_id == target_event_id:
        raise ValueError("local work relation requires distinct source and target events")

    trajectory = _load_single_line_lifecycle(project_root)
    if source_endpoint is None and source_event_id not in trajectory.events:
        raise ValueError(f"unknown source trajectory event: {source_event_id}")
    if target_endpoint is None and target_event_id not in trajectory.events:
        raise ValueError(f"unknown target trajectory event: {target_event_id}")
    resolved_source_endpoint = _coerce_relation_endpoint(
        source_endpoint,
        root_trajectory_id=trajectory.trajectory_id,
        projection_event_id=source_event_id,
    )
    resolved_target_endpoint = _coerce_relation_endpoint(
        target_endpoint,
        root_trajectory_id=trajectory.trajectory_id,
        projection_event_id=target_event_id,
    )
    relation_owner = _lowest_common_trajectory(
        trajectory,
        resolved_source_endpoint,
        resolved_target_endpoint,
    )
    projected_source_event_id = _projection_event_for_endpoint(
        relation_owner,
        resolved_source_endpoint,
    )
    projected_target_event_id = _projection_event_for_endpoint(
        relation_owner,
        resolved_target_endpoint,
    )
    if projected_source_event_id == projected_target_event_id:
        raise ValueError("local work relation projection requires distinct source and target events")

    source_event = relation_owner.events[projected_source_event_id]
    target_event = relation_owner.events[projected_target_event_id]
    projection_kind = _relation_projection_kind(
        relation_owner,
        resolved_source_endpoint,
        resolved_target_endpoint,
    )
    now = datetime.now(timezone.utc).isoformat()
    relation_metadata = {
        "source": "single-line-lifecycle",
        "created_or_updated_at": now,
        "source_lane_id": source_event.lane_id,
        "target_lane_id": target_event.lane_id,
        **dict(metadata or {}),
    }
    if projection_kind:
        relation_metadata.update(
            {
                "relation_projection": projection_kind,
                **resolved_source_endpoint.to_metadata("source"),
                **resolved_target_endpoint.to_metadata("target"),
            }
        )
    next_relation = TrajectoryRelation(
        source_event_id=projected_source_event_id,
        target_event_id=projected_target_event_id,
        kind=normalized_kind,
        summary=summary,
        metadata=relation_metadata,
    )

    for index, relation in enumerate(relation_owner.relations):
        if (
            relation.source_event_id == projected_source_event_id
            and relation.target_event_id == projected_target_event_id
            and relation.kind == normalized_kind
        ):
            relation_owner.relations[index] = replace(
                relation,
                summary=summary or relation.summary,
                metadata={
                    **dict(relation.metadata),
                    **relation_metadata,
                },
            )
            break
    else:
        relation_owner.add_relation(next_relation)

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


def _check_local_work_trajectory_invariants(
    trajectory: LocalWorkTrajectory,
    errors: list[str],
    seen_trajectory_ids: set[str],
) -> None:
    if trajectory.trajectory_id in seen_trajectory_ids:
        errors.append(f"duplicate child trajectory id {trajectory.trajectory_id!r}")
        return
    seen_trajectory_ids.add(trajectory.trajectory_id)

    for event in trajectory.events.values():
        if event.lane_id not in trajectory.lanes:
            errors.append(f"event {event.id!r} references unknown lane {event.lane_id!r}")
        child_trajectory_id = event.metadata.get("child_trajectory_id", "")
        if event.kind == "compound" and not child_trajectory_id:
            errors.append(f"compound event {event.id!r} does not reference a child trajectory")
        if child_trajectory_id and child_trajectory_id not in trajectory.child_trajectories:
            errors.append(
                f"event {event.id!r} references unknown child trajectory {child_trajectory_id!r}"
            )

    _check_compound_proxy_invariants(trajectory, errors)

    for relation in trajectory.relations:
        if relation.source_event_id not in trajectory.events:
            errors.append(
                f"relation source {relation.source_event_id!r} does not exist"
            )
        if relation.target_event_id not in trajectory.events:
            errors.append(
                f"relation target {relation.target_event_id!r} does not exist"
            )
        _check_relation_endpoint_metadata(trajectory, relation, errors)

    for child_trajectory_id, child_trajectory in trajectory.child_trajectories.items():
        if child_trajectory.trajectory_id != child_trajectory_id:
            errors.append(
                f"child trajectory key {child_trajectory_id!r} does not match "
                f"trajectory_id {child_trajectory.trajectory_id!r}"
            )
        before = len(errors)
        _check_local_work_trajectory_invariants(
            child_trajectory,
            errors,
            seen_trajectory_ids,
        )
        for index in range(before, len(errors)):
            errors[index] = f"{child_trajectory_id}: {errors[index]}"


def _check_compound_proxy_invariants(
    trajectory: LocalWorkTrajectory,
    errors: list[str],
) -> None:
    child_refs: dict[str, list[TrajectoryEvent]] = {}
    for event in trajectory.events.values():
        child_trajectory_id = event.metadata.get("child_trajectory_id", "")
        if event.kind == "compound" and child_trajectory_id:
            child_refs.setdefault(child_trajectory_id, []).append(event)
        if event.metadata.get("compound_role") != "proxy":
            continue
        anchor_event_id = event.metadata.get("anchor_compound_event_id", "")
        if not anchor_event_id:
            errors.append(f"compound proxy {event.id!r} does not reference an anchor compound event")
            continue
        anchor_event = trajectory.events.get(anchor_event_id)
        if anchor_event is None:
            errors.append(f"compound proxy {event.id!r} references missing anchor {anchor_event_id!r}")
            continue
        if anchor_event.kind != "compound":
            errors.append(f"compound proxy {event.id!r} references non-compound anchor {anchor_event_id!r}")
        if anchor_event.metadata.get("compound_role") != "anchor":
            errors.append(f"compound proxy {event.id!r} references non-anchor compound {anchor_event_id!r}")
        if anchor_event.metadata.get("child_trajectory_id", "") != event.metadata.get("child_trajectory_id", ""):
            errors.append(f"compound proxy {event.id!r} does not share its anchor child trajectory")

    for child_trajectory_id, events in child_refs.items():
        has_proxy = any(event.metadata.get("compound_role") == "proxy" for event in events)
        has_anchor = any(event.metadata.get("compound_role") == "anchor" for event in events)
        if has_proxy and not has_anchor:
            errors.append(f"child trajectory {child_trajectory_id!r} has proxy compounds but no anchor")


def _check_relation_endpoint_metadata(
    trajectory: LocalWorkTrajectory,
    relation: TrajectoryRelation,
    errors: list[str],
) -> None:
    source_endpoint = _endpoint_from_metadata(relation.metadata, "source", errors)
    target_endpoint = _endpoint_from_metadata(relation.metadata, "target", errors)
    projection = relation.metadata.get("relation_projection", "")
    if projection and (source_endpoint is None or target_endpoint is None):
        errors.append(
            f"projected relation {relation.source_event_id!r}->{relation.target_event_id!r} "
            "requires both source and target endpoint metadata"
        )
    for prefix, endpoint, projection_event_id in (
        ("source", source_endpoint, relation.source_event_id),
        ("target", target_endpoint, relation.target_event_id),
    ):
        if endpoint is None:
            continue
        if _find_trajectory_by_id(trajectory, endpoint.trajectory_id) is None:
            errors.append(
                f"{prefix} endpoint references unknown trajectory {endpoint.trajectory_id!r}"
            )
            continue
        endpoint_trajectory = _find_trajectory_by_id(trajectory, endpoint.trajectory_id)
        if endpoint_trajectory is None or endpoint.event_id not in endpoint_trajectory.events:
            errors.append(
                f"{prefix} endpoint event {endpoint.event_id!r} does not exist in "
                f"trajectory {endpoint.trajectory_id!r}"
            )
            continue
        if endpoint.parent_event_id and not _compound_event_contains_trajectory(
            trajectory,
            endpoint.parent_event_id,
            endpoint.trajectory_id,
        ):
            errors.append(
                f"{prefix} endpoint parent {endpoint.parent_event_id!r} does not contain "
                f"trajectory {endpoint.trajectory_id!r}"
            )
        if endpoint.compound_path and not _compound_path_resolves_to(
            trajectory,
            endpoint.compound_path,
            endpoint.trajectory_id,
        ):
            errors.append(
                f"{prefix} endpoint compound path {endpoint.compound_path!r} does not resolve "
                f"to trajectory {endpoint.trajectory_id!r}"
            )
        if not _projection_event_contains_endpoint(
            trajectory,
            projection_event_id,
            endpoint,
        ):
            errors.append(
                f"{prefix} projection event {projection_event_id!r} does not contain endpoint "
                f"{endpoint.trajectory_id!r}/{endpoint.event_id!r}"
            )


def _endpoint_from_metadata(
    metadata: dict[str, str],
    prefix: str,
    errors: list[str],
) -> TrajectoryEndpoint | None:
    fields = {
        "trajectory_id": metadata.get(f"{prefix}_endpoint_trajectory_id", ""),
        "event_id": metadata.get(f"{prefix}_endpoint_event_id", ""),
        "parent_event_id": metadata.get(f"{prefix}_endpoint_parent_event_id", ""),
        "compound_path": metadata.get(f"{prefix}_endpoint_compound_path", ""),
    }
    if not any(fields.values()):
        return None
    if not fields["trajectory_id"] or not fields["event_id"]:
        errors.append(f"{prefix} endpoint metadata requires trajectory_id and event_id")
        return None
    return TrajectoryEndpoint(**fields)


def _find_trajectory_by_id(
    trajectory: LocalWorkTrajectory,
    trajectory_id: str,
) -> LocalWorkTrajectory | None:
    if trajectory.trajectory_id == trajectory_id:
        return trajectory
    for child in trajectory.child_trajectories.values():
        found = _find_trajectory_by_id(child, trajectory_id)
        if found is not None:
            return found
    return None


def _path_to_trajectory(
    trajectory: LocalWorkTrajectory,
    trajectory_id: str,
) -> list[LocalWorkTrajectory] | None:
    if trajectory.trajectory_id == trajectory_id:
        return [trajectory]
    for child in trajectory.child_trajectories.values():
        child_path = _path_to_trajectory(child, trajectory_id)
        if child_path is not None:
            return [trajectory, *child_path]
    return None


def _trajectory_contains_id(
    trajectory: LocalWorkTrajectory,
    trajectory_id: str,
) -> bool:
    return _find_trajectory_by_id(trajectory, trajectory_id) is not None


def _compound_event_contains_trajectory(
    trajectory: LocalWorkTrajectory,
    event_id: str,
    trajectory_id: str,
) -> bool:
    for event in trajectory.events.values():
        child_trajectory_id = event.metadata.get("child_trajectory_id", "")
        if (
            event.id == event_id
            and event.kind == "compound"
            and child_trajectory_id
            and child_trajectory_id in trajectory.child_trajectories
            and _trajectory_contains_id(trajectory.child_trajectories[child_trajectory_id], trajectory_id)
        ):
            return True
    return any(
        _compound_event_contains_trajectory(child, event_id, trajectory_id)
        for child in trajectory.child_trajectories.values()
    )


def _compound_path_resolves_to(
    trajectory: LocalWorkTrajectory,
    compound_path: str,
    trajectory_id: str,
) -> bool:
    current = trajectory
    for event_id in [part for part in compound_path.split("/") if part]:
        event = current.events.get(event_id)
        if event is None or event.kind != "compound":
            return False
        child_trajectory_id = event.metadata.get("child_trajectory_id", "")
        if child_trajectory_id not in current.child_trajectories:
            return False
        current = current.child_trajectories[child_trajectory_id]
    return current.trajectory_id == trajectory_id


def _projection_event_contains_endpoint(
    trajectory: LocalWorkTrajectory,
    projection_event_id: str,
    endpoint: TrajectoryEndpoint,
) -> bool:
    if endpoint.trajectory_id == trajectory.trajectory_id:
        return projection_event_id == endpoint.event_id
    projection_event = trajectory.events.get(projection_event_id)
    if projection_event is None or projection_event.kind != "compound":
        return False
    child_trajectory_id = projection_event.metadata.get("child_trajectory_id", "")
    child_trajectory = trajectory.child_trajectories.get(child_trajectory_id)
    if child_trajectory is None:
        return False
    endpoint_trajectory = _find_trajectory_by_id(child_trajectory, endpoint.trajectory_id)
    return endpoint_trajectory is not None and endpoint.event_id in endpoint_trajectory.events


def _relation_endpoint_from_parts(
    *,
    root_trajectory_id: str,
    projection_event_id: str,
    trajectory_id: str = "",
    event_id: str = "",
    parent_event_id: str = "",
    compound_path: str = "",
) -> TrajectoryEndpoint:
    resolved_event_id = event_id or projection_event_id
    if not resolved_event_id:
        raise ValueError("local work relation endpoint requires event_id")
    return TrajectoryEndpoint(
        trajectory_id=trajectory_id or root_trajectory_id,
        event_id=resolved_event_id,
        parent_event_id=parent_event_id,
        compound_path=compound_path,
    )


def _coerce_relation_endpoint(
    endpoint: TrajectoryEndpoint | dict[str, str] | None,
    *,
    root_trajectory_id: str,
    projection_event_id: str,
) -> TrajectoryEndpoint:
    if endpoint is None:
        return _relation_endpoint_from_parts(
            root_trajectory_id=root_trajectory_id,
            projection_event_id=projection_event_id,
        )
    if isinstance(endpoint, TrajectoryEndpoint):
        return endpoint
    return _relation_endpoint_from_parts(
        root_trajectory_id=root_trajectory_id,
        projection_event_id=projection_event_id,
        trajectory_id=str(endpoint.get("trajectory_id", "")),
        event_id=str(endpoint.get("event_id", "")),
        parent_event_id=str(endpoint.get("parent_event_id", "")),
        compound_path=str(endpoint.get("compound_path", "")),
    )


def _lowest_common_trajectory(
    trajectory: LocalWorkTrajectory,
    left: TrajectoryEndpoint,
    right: TrajectoryEndpoint,
) -> LocalWorkTrajectory:
    left_path = _path_to_trajectory(trajectory, left.trajectory_id)
    right_path = _path_to_trajectory(trajectory, right.trajectory_id)
    if left_path is None:
        raise ValueError(f"unknown source endpoint trajectory: {left.trajectory_id}")
    if right_path is None:
        raise ValueError(f"unknown target endpoint trajectory: {right.trajectory_id}")
    owner = trajectory
    for left_item, right_item in zip(left_path, right_path):
        if left_item.trajectory_id != right_item.trajectory_id:
            break
        owner = left_item
    return owner


def _projection_event_for_endpoint(
    owner: LocalWorkTrajectory,
    endpoint: TrajectoryEndpoint,
) -> str:
    if endpoint.trajectory_id == owner.trajectory_id:
        if endpoint.event_id not in owner.events:
            raise ValueError(f"unknown endpoint event: {endpoint.event_id}")
        return endpoint.event_id

    path = _path_to_trajectory(owner, endpoint.trajectory_id)
    if path is None or len(path) < 2:
        raise ValueError(f"endpoint trajectory is not visible from relation owner: {endpoint.trajectory_id}")
    direct_child = path[1]
    candidates = [
        event for event in owner.events.values()
        if event.kind == "compound"
        and event.metadata.get("child_trajectory_id", "") == direct_child.trajectory_id
    ]
    if not candidates:
        raise ValueError(f"no projection event for endpoint trajectory: {endpoint.trajectory_id}")
    candidates.sort(
        key=lambda event: (
            0 if event.metadata.get("compound_role") == "anchor" else 1,
            event.order,
            event.id,
        )
    )
    return candidates[0].id


def _relation_projection_kind(
    owner: LocalWorkTrajectory,
    source_endpoint: TrajectoryEndpoint,
    target_endpoint: TrajectoryEndpoint,
) -> str:
    source_nested = source_endpoint.trajectory_id != owner.trajectory_id
    target_nested = target_endpoint.trajectory_id != owner.trajectory_id
    if source_nested and target_nested and source_endpoint.trajectory_id != target_endpoint.trajectory_id:
        return "cross-compound"
    if source_nested or target_nested:
        return "cross-boundary"
    return ""


def _normalize_pack_subgraph_ranges(
    ranges: list[dict[str, str]] | str,
) -> list[dict[str, str]]:
    if isinstance(ranges, str):
        raw = ranges.strip()
        if not raw:
            return []
        parsed = json.loads(raw)
    else:
        parsed = ranges
    if not isinstance(parsed, list):
        raise ValueError("local work packSubgraph ranges must be a list")
    normalized: list[dict[str, str]] = []
    for item in parsed:
        if not isinstance(item, dict):
            raise ValueError("local work packSubgraph range must be an object")
        lane_id = str(item.get("lane_id") or item.get("laneId") or "").strip()
        start_event_id = str(
            item.get("range_start_event_id")
            or item.get("rangeStartEventId")
            or item.get("sourceEventId")
            or ""
        ).strip()
        end_event_id = str(
            item.get("range_end_event_id")
            or item.get("rangeEndEventId")
            or item.get("targetEventId")
            or ""
        ).strip()
        if not lane_id:
            raise ValueError("local work packSubgraph range requires lane_id")
        if not start_event_id:
            raise ValueError("local work packSubgraph range requires range_start_event_id")
        if not end_event_id:
            raise ValueError("local work packSubgraph range requires range_end_event_id")
        normalized.append(
            {
                "lane_id": lane_id,
                "range_start_event_id": start_event_id,
                "range_end_event_id": end_event_id,
            }
        )
    return normalized


def _normalize_add_lanes_specs(lanes: list[dict[str, str]] | str) -> list[dict[str, str]]:
    if isinstance(lanes, str):
        raw = lanes.strip()
        if not raw:
            return []
        parsed = json.loads(raw)
    else:
        parsed = lanes
    if not isinstance(parsed, list):
        raise ValueError("local work addLanes lanes must be a list")
    normalized: list[dict[str, str]] = []
    for item in parsed:
        if not isinstance(item, dict):
            raise ValueError("local work addLanes lane spec must be an object")
        lane_label = str(item.get("lane_label") or item.get("laneLabel") or "").strip()
        first_event_title = str(
            item.get("first_event_title")
            or item.get("firstEventTitle")
            or item.get("title")
            or ""
        ).strip()
        event_kind = str(item.get("event_kind") or item.get("eventKind") or "task").strip()
        if not lane_label:
            raise ValueError("local work addLanes lane spec requires lane_label")
        if not first_event_title:
            raise ValueError("local work addLanes lane spec requires first_event_title")
        if event_kind not in TRAJECTORY_EVENT_KINDS:
            allowed = ", ".join(sorted(TRAJECTORY_EVENT_KINDS))
            raise ValueError(f"local work addLanes event_kind must be one of: {allowed}")
        normalized.append(
            {
                "lane_label": lane_label,
                "first_event_title": first_event_title,
                "event_kind": event_kind,
                "summary": str(
                    item.get("summary")
                    or item.get("first_event_summary")
                    or item.get("firstEventSummary")
                    or ""
                ),
                "lane_id": str(item.get("lane_id") or item.get("laneId") or "").strip(),
            }
        )
    return normalized


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


def _child_lane_by_id_or_primary_or_create(
    trajectory: LocalWorkTrajectory,
    *,
    lane_id: str,
    lane_label: str,
) -> TrajectoryLane:
    if trajectory.lanes:
        return _lane_by_id_or_primary(trajectory, lane_id)
    next_lane_id = lane_id or "lane:main"
    now = datetime.now(timezone.utc).isoformat()
    lane = TrajectoryLane(
        id=next_lane_id,
        label=lane_label,
        status="active",
        summary="Child trajectory lane.",
        metadata={
            "line_kind": "compound-child",
            "created_at": now,
            "source": "compound-child-lifecycle",
        },
    )
    trajectory.add_lane(lane)
    return lane


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
    return _next_event_id_excluding(trajectory, preferred_order, set())


def _next_event_id_excluding(
    trajectory: LocalWorkTrajectory,
    preferred_order: int,
    excluded_event_ids: set[str],
) -> str:
    order = preferred_order
    while True:
        candidate = f"event:{order:03d}"
        if candidate not in trajectory.events and candidate not in excluded_event_ids:
            return candidate
        order += 1


def _next_lane_id(trajectory: LocalWorkTrajectory) -> str:
    return _next_lane_id_excluding(trajectory, set())


def _next_lane_id_excluding(trajectory: LocalWorkTrajectory, excluded_lane_ids: set[str]) -> str:
    index = 2
    while True:
        candidate = f"lane:{index:03d}"
        if candidate not in trajectory.lanes and candidate not in excluded_lane_ids:
            return candidate
        index += 1


def _event_index(events: list[TrajectoryEvent], event_id: str) -> int:
    for index, event in enumerate(events):
        if event.id == event_id:
            return index
    raise ValueError(f"trajectory event {event_id} is not in the selected lane")


def _locate_child_context(
    trajectory: LocalWorkTrajectory,
    *,
    child_trajectory_id: str,
    parent_event_id: str,
) -> tuple[str, TrajectoryEvent, LocalWorkTrajectory]:
    resolved_parent_event_id = parent_event_id
    resolved_child_trajectory_id = child_trajectory_id
    if resolved_parent_event_id:
        if resolved_parent_event_id not in trajectory.events:
            raise ValueError(f"unknown parent trajectory event: {resolved_parent_event_id}")
        parent_event = trajectory.events[resolved_parent_event_id]
        resolved_child_trajectory_id = parent_event.metadata.get("child_trajectory_id", "")
        if parent_event.kind != "compound" or not resolved_child_trajectory_id:
            raise ValueError(f"trajectory event is not a compound parent: {resolved_parent_event_id}")
    elif resolved_child_trajectory_id:
        parent_event = next(
            (
                event for event in trajectory.events.values()
                if event.metadata.get("child_trajectory_id") == resolved_child_trajectory_id
            ),
            None,
        )
        if parent_event is None:
            raise ValueError(f"unknown child trajectory parent: {resolved_child_trajectory_id}")
        resolved_parent_event_id = parent_event.id
    else:
        raise ValueError("compound child action requires parent_event_id or child_trajectory_id")

    if resolved_child_trajectory_id not in trajectory.child_trajectories:
        raise ValueError(f"unknown child trajectory: {resolved_child_trajectory_id}")
    return (
        resolved_parent_event_id,
        parent_event,
        trajectory.child_trajectories[resolved_child_trajectory_id],
    )


def _child_trajectory_id(
    trajectory: LocalWorkTrajectory,
    event_id: str,
) -> str:
    base = f"{trajectory.trajectory_id}:{event_id}:child"
    if base not in trajectory.child_trajectories:
        return base
    index = 2
    while True:
        candidate = f"{base}:{index:03d}"
        if candidate not in trajectory.child_trajectories:
            return candidate
        index += 1


def _status_for_packed_events(events: list[TrajectoryEvent]) -> TrajectoryEventStatus:
    if any(event.status == "blocked" for event in events):
        return "blocked"
    if any(event.status == "waiting" for event in events):
        return "waiting"
    if any(event.status == "in_progress" for event in events):
        return "in_progress"
    if all(event.status in {"completed", "archived"} for event in events):
        return "completed"
    return "pending"


def _lane_status_for_events(events: list[TrajectoryEvent]) -> TrajectoryLaneStatus:
    if not events:
        return "pending"
    if any(event.status == "blocked" for event in events):
        return "blocked"
    if any(event.status == "waiting" for event in events):
        return "waiting"
    if any(event.status == "in_progress" for event in events):
        return "active"
    if all(event.status in {"completed", "archived"} for event in events):
        return "done"
    return "pending"


def _status_for_child_trajectory(
    trajectory: LocalWorkTrajectory,
) -> TrajectoryEventStatus:
    if not trajectory.events:
        return "pending"
    return _status_for_packed_events(list(trajectory.events.values()))


def _refresh_all_compound_rollups(trajectory: LocalWorkTrajectory) -> None:
    for child_trajectory in trajectory.child_trajectories.values():
        _refresh_all_compound_rollups(child_trajectory)
    for event in list(trajectory.events.values()):
        child_trajectory_id = event.metadata.get("child_trajectory_id", "")
        if event.kind != "compound" or not child_trajectory_id:
            continue
        child_trajectory = trajectory.child_trajectories.get(child_trajectory_id)
        if child_trajectory is None:
            continue
        next_status = _status_for_child_trajectory(child_trajectory)
        if event.status == next_status:
            continue
        trajectory.events[event.id] = replace(event, status=next_status)


def _drop_sequence_relations_for_lane(
    relations: list[TrajectoryRelation],
    lane_event_ids: set[str],
) -> list[TrajectoryRelation]:
    return [
        relation for relation in relations
        if not (
            relation.kind == "sequence"
            and relation.source_event_id in lane_event_ids
            and relation.target_event_id in lane_event_ids
        )
    ]


def _renumber_lane_events(
    trajectory: LocalWorkTrajectory,
    lane_id: str,
) -> None:
    for index, event in enumerate(_ordered_lane_events(trajectory, lane_id), start=1):
        if event.order == index:
            continue
        trajectory.events[event.id] = replace(event, order=index)


def _rebuild_lane_sequence_relations(
    trajectory: LocalWorkTrajectory,
    lane_id: str,
) -> None:
    lane_events = _ordered_lane_events(trajectory, lane_id)
    for previous, current in zip(lane_events, lane_events[1:]):
        trajectory.add_relation(
            TrajectoryRelation(
                source_event_id=previous.id,
                target_event_id=current.id,
                kind="sequence",
                metadata={"source": "single-line-lifecycle"},
            )
        )


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
