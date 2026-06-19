"""Scheduler state -> Local Work Trajectory projection helpers.

This module deliberately builds a view object only. It must not mutate
scheduler state or the workspace-local trajectory artifact; orchestration state
remains the authority.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path

from src.runtime.orchestration.exchange_store import InMemoryArtifactVersionStore, JsonlCoordinationEventLog
from src.runtime.orchestration.runtime_adapter import AgentRuntimeAdapterRegistry, QoderQueryClient
from src.runtime.orchestration.sandbox import SandboxProviderRegistry
from src.runtime.orchestration.scheduler import (
    ScheduledTask,
    ScheduledTaskState,
    SchedulerEvent,
    SchedulerMergeGate,
    SchedulerMergeGateEvent,
    SchedulerRunPolicy,
    SchedulerState,
    TaskDependency,
    TaskRunRecord,
)
from src.runtime.orchestration.scheduler_runner import (
    PersistedSchedulerRunOnceResult,
    run_persisted_scheduler_once,
)
from src.runtime.orchestration.scheduler_host_runner import (
    HostSchedulerRunRequest,
    HostSchedulerRunResult,
    run_host_authorized_scheduler_once,
)
from src.runtime.orchestration.scheduler_host_daemon import (
    HostSchedulerDaemonLoopRequest,
    HostSchedulerDaemonLoopResult,
    run_host_authorized_scheduler_daemon_loop,
)
from src.runtime.orchestration.scheduler_store import (
    JsonlSchedulerEventLog,
    JsonlSchedulerMergeGateEventLog,
    read_scheduler_state_snapshot,
)

from .trajectory import (
    LocalWorkTrajectory,
    TrajectoryEvent,
    TrajectoryEventKind,
    TrajectoryEventStatus,
    TrajectoryLane,
    TrajectoryLaneStatus,
    TrajectoryRelation,
)


_DEFAULT_SCHEDULER_TRAJECTORY_PATH = Path(".codex/progress-graph/scheduler-work-trajectory.json")
_DEFAULT_HISTORY_TIMELINE_LIMIT = 40


@dataclass(frozen=True, slots=True)
class _SchedulerHistoryTimeline:
    """Compact projection-only scheduler history summary."""

    lines: tuple[str, ...]
    total_count: int
    limit: int

    @property
    def truncated(self) -> bool:
        return self.total_count > len(self.lines)


@dataclass(frozen=True, slots=True)
class SchedulerRunProjectionRefreshResult:
    """Result of one persisted scheduler run plus projection refresh."""

    run: PersistedSchedulerRunOnceResult
    projection_path: Path
    projection: LocalWorkTrajectory


@dataclass(frozen=True, slots=True)
class HostSchedulerRunProjectionRefreshResult:
    """Result of one host-authorized run plus scheduler projection refresh."""

    host_run: HostSchedulerRunResult
    projection_path: Path
    projection: LocalWorkTrajectory


@dataclass(frozen=True, slots=True)
class HostSchedulerDaemonLoopProjectionRefreshResult:
    """Result of one host-authorized daemon loop plus projection refresh."""

    host_loop: HostSchedulerDaemonLoopResult
    projection_path: Path
    projection: LocalWorkTrajectory

    def to_json_dict(self) -> dict[str, object]:
        """Return a compact JSON-compatible host workflow result."""

        payload = self.host_loop.to_json_dict()
        authority_payload = payload.get("authority_split", {})
        authority_split = dict(authority_payload) if isinstance(authority_payload, dict) else {}
        authority_split.update(
            {
                "scheduler_projection_refreshed": True,
                "scheduler_projection_role": "read-only-view",
                "scheduler_projection_path": str(self.projection_path),
                "local_work_trajectory_mutated": False,
            }
        )
        payload["scheduler_projection_path"] = str(self.projection_path)
        payload["projection_summary"] = self.projection.summary()
        payload["authority_split"] = authority_split
        return payload


def scheduler_work_trajectory_json_path(project_root: str | Path) -> Path:
    """Return the default artifact path for scheduler-derived trajectory views."""

    return Path(project_root) / _DEFAULT_SCHEDULER_TRAJECTORY_PATH


def build_scheduler_work_trajectory(
    state: SchedulerState,
    *,
    scheduler_events: tuple[SchedulerEvent, ...] = (),
    merge_gate_events: tuple[SchedulerMergeGateEvent, ...] = (),
    trajectory_id: str = "local-work:scheduler-projection",
    title: str = "Scheduler Local Work Trajectory",
    recorded_at: str = "",
    guide_context: str = "",
    source_graph_id: str = "",
    source_node_id: str = "",
) -> LocalWorkTrajectory:
    """Project scheduler-owned task state into a Local Work Trajectory view.

    The returned trajectory is suitable for UI consumption and tests. It is not
    a scheduler checkpoint, and callers must not treat trajectory edits as task
    lifecycle mutations.
    """

    timeline = _scheduler_history_timeline(
        scheduler_events,
        merge_gate_events,
        limit=_DEFAULT_HISTORY_TIMELINE_LIMIT,
    )
    trajectory = LocalWorkTrajectory(
        trajectory_id=trajectory_id,
        title=title,
        recorded_at=recorded_at or datetime.now(timezone.utc).isoformat(),
        source_graph_id=source_graph_id,
        source_node_id=source_node_id,
        guide_context=guide_context,
        metadata={
            "projection": "scheduler-state",
            "authority": "scheduler",
            "trajectory_role": "read-only-view",
            "task_count": str(len(state.tasks)),
            "dependency_count": str(len(state.dependencies)),
            "run_record_count": str(len(state.run_records)),
            "scheduler_history_timeline_count": str(timeline.total_count),
            "scheduler_history_timeline_limit": str(timeline.limit),
            "scheduler_history_timeline_truncated": "true" if timeline.truncated else "false",
        },
    )
    if timeline.lines:
        trajectory.metadata["scheduler_history_timeline"] = "\n".join(timeline.lines)

    event_ids = _event_ids_by_task(state)
    run_records = _run_records_by_task(state)
    scheduler_events_by_task = _scheduler_events_by_task(scheduler_events)
    fan_in_dependencies = _fan_in_dependencies_by_target(state)
    merge_gates_by_target = _merge_gates_by_target(state)
    merge_gate_events_by_gate = _merge_gate_events_by_gate(merge_gate_events)

    for lane_id, lane_tasks in _tasks_by_lane(state).items():
        trajectory.add_lane(
            TrajectoryLane(
                id=lane_id,
                label=_lane_label(lane_id),
                status=_lane_status(lane_tasks),
                summary="Scheduler context scope lane.",
                metadata={
                    "projection": "scheduler-state",
                    "authority": "scheduler",
                    "task_count": str(len(lane_tasks)),
                },
            )
        )

    for order, task in enumerate(_ordered_tasks(state), start=1):
        trajectory.add_event(
            TrajectoryEvent(
                id=event_ids[task.task_id],
                lane_id=_lane_id_for_task(task),
                title=task.title or task.task_id,
                kind=_event_kind(task),
                status=_event_status(task.state),
                order=order,
                summary=task.blocked_reason or task.instruction,
                metadata=_event_metadata(
                    task,
                    run_records.get(task.task_id, ()),
                    scheduler_events_by_task.get(task.task_id, ()),
                    fan_in_dependencies.get(task.task_id, ()),
                    merge_gates_by_target.get(task.task_id, ()),
                ),
            )
        )

    for gate in state.merge_gates:
        if gate.target_task_id not in state.tasks:
            continue
        target = state.tasks[gate.target_task_id]
        merge_event_id = _merge_gate_event_id(gate, event_ids)
        trajectory.add_event(
            TrajectoryEvent(
                id=merge_event_id,
                lane_id=_lane_id_for_task(target),
                title=gate.title or f"Merge gate {gate.gate_id}",
                kind="merge",
                status=_merge_gate_event_status(gate),
                order=_merge_event_order(target, state),
                summary=gate.blocked_reason or f"Scheduler-owned {gate.gate_kind} merge gate.",
                metadata=_merge_gate_metadata(
                    gate,
                    merge_gate_events_by_gate.get(gate.gate_id, ()),
                ),
            )
        )
        for source_task_id in gate.source_task_ids:
            if source_task_id not in state.tasks:
                continue
            trajectory.add_relation(
                TrajectoryRelation(
                    source_event_id=event_ids[source_task_id],
                    target_event_id=merge_event_id,
                    kind="depends_on",
                    summary=f"Scheduler merge gate source for {gate.target_task_id}.",
                    metadata={
                        "projection": "scheduler-state",
                        "authority": "scheduler",
                        "relation_role": "scheduler-merge-gate-source",
                        "scheduler_merge_gate_id": gate.gate_id,
                        "source_task_id": source_task_id,
                        "target_task_id": gate.target_task_id,
                    },
                )
            )
        trajectory.add_relation(
            TrajectoryRelation(
                source_event_id=merge_event_id,
                target_event_id=event_ids[gate.target_task_id],
                kind="merges_into",
                summary=f"Scheduler merge gate {gate.gate_id} merges into {gate.target_task_id}.",
                metadata={
                    "projection": "scheduler-state",
                    "authority": "scheduler",
                    "relation_role": "scheduler-merge-gate-target",
                    "scheduler_merge_gate_id": gate.gate_id,
                    "scheduler_target_task_id": gate.target_task_id,
                },
            )
        )

    for task_id, dependencies in fan_in_dependencies.items():
        if task_id in merge_gates_by_target:
            continue
        target = state.tasks.get(task_id)
        if target is None:
            continue
        merge_event_id = _merge_event_id(task_id, event_ids)
        dependency_ids = tuple(dependency.dependency_id for dependency in dependencies)
        source_task_ids = tuple(dependency.source_task_id for dependency in dependencies)
        trajectory.add_event(
            TrajectoryEvent(
                id=merge_event_id,
                lane_id=_lane_id_for_task(target),
                title=f"Merge dependencies for {target.title or target.task_id}",
                kind="merge",
                status=_event_status(target.state),
                order=_merge_event_order(target, state),
                summary=f"Fan-in from {len(dependencies)} scheduler dependencies.",
                metadata={
                    "projection": "scheduler-state",
                    "authority": "scheduler",
                    "scheduler_projection_role": "fan-in-merge",
                    "scheduler_target_task_id": task_id,
                    "scheduler_dependency_ids": "\n".join(dependency_ids),
                    "scheduler_source_task_ids": "\n".join(source_task_ids),
                },
            )
        )
        for dependency in dependencies:
            if dependency.source_task_id not in state.tasks:
                continue
            trajectory.add_relation(
                TrajectoryRelation(
                    source_event_id=event_ids[dependency.source_task_id],
                    target_event_id=merge_event_id,
                    kind=dependency.dependency_kind,
                    summary=f"Fan-in source for {task_id}.",
                    metadata={
                        **_dependency_metadata(dependency),
                        "relation_role": "fan-in-source",
                        "scheduler_merge_event_id": merge_event_id,
                    },
                )
            )
        trajectory.add_relation(
            TrajectoryRelation(
                source_event_id=merge_event_id,
                target_event_id=event_ids[task_id],
                kind="merges_into",
                summary=f"Scheduler fan-in gate merges into {task_id}.",
                metadata={
                    "projection": "scheduler-state",
                    "authority": "scheduler",
                    "relation_role": "fan-in-merge-target",
                    "scheduler_target_task_id": task_id,
                    "scheduler_dependency_ids": "\n".join(dependency_ids),
                },
            )
        )

    for dependency in state.dependencies:
        if dependency.source_task_id not in state.tasks or dependency.target_task_id not in state.tasks:
            continue
        trajectory.add_relation(
            TrajectoryRelation(
                source_event_id=event_ids[dependency.source_task_id],
                target_event_id=event_ids[dependency.target_task_id],
                kind=dependency.dependency_kind,
                summary=f"Requires {dependency.source_task_id} to reach {dependency.required_state}.",
                metadata=_dependency_metadata(dependency),
            )
        )

    for lane_id in trajectory.lanes:
        lane_events = sorted(
            (event for event in trajectory.events.values() if event.lane_id == lane_id),
            key=lambda event: (event.order, event.id),
        )
        for previous, current in zip(lane_events, lane_events[1:]):
            trajectory.add_relation(
                TrajectoryRelation(
                    source_event_id=previous.id,
                    target_event_id=current.id,
                    kind="sequence",
                    metadata={
                        "projection": "scheduler-state",
                        "authority": "scheduler",
                        "relation_role": "lane-order",
                    },
                )
            )

    trajectory.validate()
    return trajectory


def build_scheduler_work_trajectory_from_history(
    state: SchedulerState,
    *,
    scheduler_event_log_path: str | Path | None = None,
    merge_gate_event_log_path: str | Path | None = None,
    trajectory_id: str = "local-work:scheduler-projection",
    title: str = "Scheduler Local Work Trajectory",
    recorded_at: str = "",
    guide_context: str = "",
    source_graph_id: str = "",
    source_node_id: str = "",
) -> LocalWorkTrajectory:
    """Project scheduler state plus optional JSONL history into a read-only view."""

    scheduler_events: tuple[SchedulerEvent, ...] = ()
    if scheduler_event_log_path is not None:
        scheduler_events = JsonlSchedulerEventLog(scheduler_event_log_path).read_all()

    merge_gate_events: tuple[SchedulerMergeGateEvent, ...] = ()
    if merge_gate_event_log_path is not None:
        merge_gate_events = JsonlSchedulerMergeGateEventLog(merge_gate_event_log_path).read_all()

    trajectory = build_scheduler_work_trajectory(
        state,
        scheduler_events=scheduler_events,
        merge_gate_events=merge_gate_events,
        trajectory_id=trajectory_id,
        title=title,
        recorded_at=recorded_at,
        guide_context=guide_context,
        source_graph_id=source_graph_id,
        source_node_id=source_node_id,
    )
    trajectory.metadata["scheduler_event_log_path"] = (
        "" if scheduler_event_log_path is None else str(Path(scheduler_event_log_path))
    )
    trajectory.metadata["scheduler_event_log_count"] = str(len(scheduler_events))
    trajectory.metadata["scheduler_merge_gate_event_log_path"] = (
        "" if merge_gate_event_log_path is None else str(Path(merge_gate_event_log_path))
    )
    trajectory.metadata["scheduler_merge_gate_event_log_count"] = str(len(merge_gate_events))
    return trajectory


def write_scheduler_work_trajectory_artifact(
    project_root: str | Path,
    state: SchedulerState,
    *,
    scheduler_event_log_path: str | Path | None = None,
    merge_gate_event_log_path: str | Path | None = None,
    output_path: str | Path | None = None,
    trajectory_id: str = "local-work:scheduler-projection",
    title: str = "Scheduler Local Work Trajectory",
    recorded_at: str = "",
    guide_context: str = "",
    source_graph_id: str = "",
    source_node_id: str = "",
) -> Path:
    """Write a scheduler-derived trajectory artifact without mutating local work state."""

    target = Path(output_path) if output_path is not None else scheduler_work_trajectory_json_path(project_root)
    trajectory = build_scheduler_work_trajectory_from_history(
        state,
        scheduler_event_log_path=scheduler_event_log_path,
        merge_gate_event_log_path=merge_gate_event_log_path,
        trajectory_id=trajectory_id,
        title=title,
        recorded_at=recorded_at,
        guide_context=guide_context,
        source_graph_id=source_graph_id,
        source_node_id=source_node_id,
    )
    trajectory.metadata["projection_artifact_path"] = str(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(trajectory.to_json(), encoding="utf-8")
    return target


def run_persisted_scheduler_once_and_refresh_projection(
    project_root: str | Path,
    *,
    snapshot_path: str | Path,
    event_log_path: str | Path,
    sandbox_registry: SandboxProviderRegistry,
    runtime_registry: AgentRuntimeAdapterRegistry,
    merge_gate_event_log_path: str | Path | None = None,
    projection_output_path: str | Path | None = None,
    policy: SchedulerRunPolicy | None = None,
    max_runs: int | None = None,
    workspace_root: str = "",
    scratch_root: str = ".codex/scratch",
    created_at: str = "",
    expires_at: str = "",
    timestamp: str = "",
    strict_recovery: bool = True,
    trajectory_id: str = "local-work:scheduler-projection",
    title: str = "Scheduler Local Work Trajectory",
    recorded_at: str = "",
    guide_context: str = "",
    source_graph_id: str = "",
    source_node_id: str = "",
) -> SchedulerRunProjectionRefreshResult:
    """Run one persisted scheduler drain and refresh its trajectory projection.

    This host-facing helper composes the runtime-owned one-shot runner with the
    progress-graph projection writer. It intentionally lives in
    ``tools.progress_graph`` so the orchestration runtime does not depend on
    progress graph export code.
    """

    run = run_persisted_scheduler_once(
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        sandbox_registry=sandbox_registry,
        runtime_registry=runtime_registry,
        policy=policy,
        max_runs=max_runs,
        workspace_root=workspace_root,
        scratch_root=scratch_root,
        created_at=created_at,
        expires_at=expires_at,
        timestamp=timestamp,
        strict_recovery=strict_recovery,
    )
    state = read_scheduler_state_snapshot(snapshot_path)
    projection_path = write_scheduler_work_trajectory_artifact(
        project_root,
        state,
        scheduler_event_log_path=event_log_path,
        merge_gate_event_log_path=merge_gate_event_log_path,
        output_path=projection_output_path,
        trajectory_id=trajectory_id,
        title=title,
        recorded_at=recorded_at or timestamp,
        guide_context=guide_context,
        source_graph_id=source_graph_id,
        source_node_id=source_node_id,
    )
    return SchedulerRunProjectionRefreshResult(
        run=run,
        projection_path=projection_path,
        projection=LocalWorkTrajectory.from_json(projection_path.read_text(encoding="utf-8")),
    )


def run_host_authorized_scheduler_once_and_refresh_projection(
    project_root: str | Path,
    request: HostSchedulerRunRequest,
    *,
    artifact_store: InMemoryArtifactVersionStore | None = None,
    coordination_event_log: JsonlCoordinationEventLog | None = None,
    qoder_query_client: QoderQueryClient | None = None,
    sandbox_registry: SandboxProviderRegistry | None = None,
    trajectory_id: str = "local-work:scheduler-projection",
    title: str = "Scheduler Local Work Trajectory",
    recorded_at: str = "",
    guide_context: str = "",
    source_graph_id: str = "",
    source_node_id: str = "",
) -> HostSchedulerRunProjectionRefreshResult:
    """Run one host-authorized scheduler pass and refresh its read-only projection."""

    host_run = run_host_authorized_scheduler_once(
        request,
        artifact_store=artifact_store,
        coordination_event_log=coordination_event_log,
        qoder_query_client=qoder_query_client,
        sandbox_registry=sandbox_registry,
    )
    state = read_scheduler_state_snapshot(request.snapshot_path)
    projection_path = write_scheduler_work_trajectory_artifact(
        project_root,
        state,
        scheduler_event_log_path=request.event_log_path,
        merge_gate_event_log_path=request.merge_gate_event_log_path,
        output_path=request.projection_output_path,
        trajectory_id=trajectory_id,
        title=title,
        recorded_at=recorded_at or request.timestamp,
        guide_context=guide_context,
        source_graph_id=source_graph_id,
        source_node_id=source_node_id,
    )
    return HostSchedulerRunProjectionRefreshResult(
        host_run=replace(host_run, scheduler_projection_path=projection_path),
        projection_path=projection_path,
        projection=LocalWorkTrajectory.from_json(projection_path.read_text(encoding="utf-8")),
    )


def run_host_authorized_scheduler_daemon_loop_and_refresh_projection(
    project_root: str | Path,
    request: HostSchedulerDaemonLoopRequest,
    *,
    artifact_store: InMemoryArtifactVersionStore | None = None,
    coordination_event_log: JsonlCoordinationEventLog | None = None,
    qoder_query_client: QoderQueryClient | None = None,
    sandbox_registry: SandboxProviderRegistry | None = None,
    merge_gate_event_log_path: str | Path | None = None,
    projection_output_path: str | Path | None = None,
    trajectory_id: str = "local-work:scheduler-projection",
    title: str = "Scheduler Local Work Trajectory",
    recorded_at: str = "",
    guide_context: str = "",
    source_graph_id: str = "",
    source_node_id: str = "",
) -> HostSchedulerDaemonLoopProjectionRefreshResult:
    """Run a host-authorized daemon loop and refresh its read-only projection."""

    host_loop = run_host_authorized_scheduler_daemon_loop(
        request,
        artifact_store=artifact_store,
        coordination_event_log=coordination_event_log,
        qoder_query_client=qoder_query_client,
        sandbox_registry=sandbox_registry,
    )
    state = read_scheduler_state_snapshot(request.snapshot_path)
    projection_path = write_scheduler_work_trajectory_artifact(
        project_root,
        state,
        scheduler_event_log_path=request.event_log_path,
        merge_gate_event_log_path=merge_gate_event_log_path,
        output_path=projection_output_path,
        trajectory_id=trajectory_id,
        title=title,
        recorded_at=recorded_at or request.timestamp,
        guide_context=guide_context,
        source_graph_id=source_graph_id,
        source_node_id=source_node_id,
    )
    return HostSchedulerDaemonLoopProjectionRefreshResult(
        host_loop=replace(host_loop, scheduler_projection_refreshed=True),
        projection_path=projection_path,
        projection=LocalWorkTrajectory.from_json(projection_path.read_text(encoding="utf-8")),
    )


def _tasks_by_lane(state: SchedulerState) -> dict[str, tuple[ScheduledTask, ...]]:
    lanes: dict[str, list[ScheduledTask]] = {}
    for task in _ordered_tasks(state):
        lanes.setdefault(_lane_id_for_task(task), []).append(task)
    if not lanes:
        lanes["lane:scheduler"] = []
    return {
        lane_id: tuple(tasks)
        for lane_id, tasks in sorted(lanes.items(), key=lambda item: item[0])
    }


def _ordered_tasks(state: SchedulerState) -> tuple[ScheduledTask, ...]:
    return tuple(sorted(state.tasks.values(), key=lambda task: task.task_id))


def _event_ids_by_task(state: SchedulerState) -> dict[str, str]:
    used: set[str] = set()
    event_ids: dict[str, str] = {}
    for task in _ordered_tasks(state):
        base = _event_id_base(task.task_id)
        candidate = base
        index = 2
        while candidate in used:
            candidate = f"{base}:{index}"
            index += 1
        used.add(candidate)
        event_ids[task.task_id] = candidate
    return event_ids


def _run_records_by_task(state: SchedulerState) -> dict[str, tuple[TaskRunRecord, ...]]:
    records: dict[str, list[TaskRunRecord]] = {}
    for record in state.run_records:
        records.setdefault(record.task_id, []).append(record)
    return {task_id: tuple(items) for task_id, items in records.items()}


def _fan_in_dependencies_by_target(state: SchedulerState) -> dict[str, tuple[TaskDependency, ...]]:
    by_target: dict[str, list[TaskDependency]] = {}
    for dependency in state.dependencies:
        if dependency.source_task_id not in state.tasks or dependency.target_task_id not in state.tasks:
            continue
        by_target.setdefault(dependency.target_task_id, []).append(dependency)
    return {
        task_id: tuple(sorted(dependencies, key=lambda dependency: dependency.dependency_id))
        for task_id, dependencies in sorted(by_target.items())
        if len(dependencies) > 1
    }


def _scheduler_events_by_task(events: tuple[SchedulerEvent, ...]) -> dict[str, tuple[SchedulerEvent, ...]]:
    records: dict[str, list[SchedulerEvent]] = {}
    for event in sorted(events, key=_scheduler_event_order_key):
        records.setdefault(event.task_id, []).append(event)
    return {task_id: tuple(items) for task_id, items in records.items()}


def _merge_gates_by_target(state: SchedulerState) -> dict[str, tuple[SchedulerMergeGate, ...]]:
    records: dict[str, list[SchedulerMergeGate]] = {}
    for gate in sorted(state.merge_gates, key=lambda item: item.gate_id):
        records.setdefault(gate.target_task_id, []).append(gate)
    return {task_id: tuple(items) for task_id, items in records.items()}


def _merge_gate_events_by_gate(
    events: tuple[SchedulerMergeGateEvent, ...],
) -> dict[str, tuple[SchedulerMergeGateEvent, ...]]:
    records: dict[str, list[SchedulerMergeGateEvent]] = {}
    for event in sorted(events, key=_merge_gate_event_order_key):
        records.setdefault(event.gate_id, []).append(event)
    return {gate_id: tuple(items) for gate_id, items in records.items()}


def _lane_id_for_task(task: ScheduledTask) -> str:
    return task.context_scope.lane_id or "lane:scheduler"


def _lane_label(lane_id: str) -> str:
    if lane_id.startswith("lane:"):
        return lane_id.removeprefix("lane:").replace("-", " ").replace("_", " ")
    return lane_id


def _lane_status(tasks: tuple[ScheduledTask, ...]) -> TrajectoryLaneStatus:
    if not tasks:
        return "pending"
    states = {task.state for task in tasks}
    if "blocked" in states:
        return "blocked"
    if "waiting" in states:
        return "waiting"
    if states.intersection({"ready", "running", "review_required"}):
        return "active"
    if states and states.issubset({"complete", "cancelled"}):
        return "done"
    return "pending"


def _event_id_base(task_id: str) -> str:
    safe = "".join(character if character.isalnum() else "-" for character in task_id).strip("-")
    return f"scheduler-task:{safe or 'task'}"


def _merge_event_id(task_id: str, event_ids: dict[str, str]) -> str:
    return f"{event_ids[task_id]}:fan-in-merge"


def _merge_gate_event_id(gate: SchedulerMergeGate, event_ids: dict[str, str]) -> str:
    safe = "".join(character if character.isalnum() else "-" for character in gate.gate_id).strip("-")
    target = event_ids[gate.target_task_id]
    return f"{target}:merge-gate:{safe or 'gate'}"


def _merge_event_order(task: ScheduledTask, state: SchedulerState) -> int:
    ordered = _ordered_tasks(state)
    for index, item in enumerate(ordered, start=1):
        if item.task_id == task.task_id:
            return index * 100 - 1
    return len(ordered) * 100 + 99


def _merge_gate_event_status(gate: SchedulerMergeGate) -> TrajectoryEventStatus:
    if gate.state in {"ready", "review_required"}:
        return "in_progress"
    if gate.state == "waiting":
        return "waiting"
    if gate.state == "blocked":
        return "blocked"
    if gate.state == "complete":
        return "completed"
    if gate.state == "cancelled":
        return "archived"
    return "pending"


def _event_status(state: ScheduledTaskState) -> TrajectoryEventStatus:
    if state in {"ready", "running", "review_required"}:
        return "in_progress"
    if state == "waiting":
        return "waiting"
    if state == "blocked":
        return "blocked"
    if state == "complete":
        return "completed"
    if state == "cancelled":
        return "archived"
    return "pending"


def _event_kind(task: ScheduledTask) -> TrajectoryEventKind:
    if task.state == "review_required":
        return "review"
    if task.state == "waiting":
        return "wait"
    return "task"


def _event_metadata(
    task: ScheduledTask,
    run_records: tuple[TaskRunRecord, ...],
    scheduler_events: tuple[SchedulerEvent, ...],
    fan_in_dependencies: tuple[TaskDependency, ...],
    merge_gates: tuple[SchedulerMergeGate, ...],
) -> dict[str, str]:
    metadata = {
        "projection": "scheduler-state",
        "authority": "scheduler",
        "scheduler_task_id": task.task_id,
        "scheduler_state": task.state,
        "agent_id": task.agent.agent_id,
        "runtime_provider": task.agent.runtime_provider,
        "context_id": task.context_scope.context_id,
        "sandbox_profile_id": task.sandbox_profile.profile_id,
        "sandbox_profile_kind": task.sandbox_profile.profile_kind,
    }
    if task.edit_lease is not None:
        metadata.update(
            {
                "edit_lease_id": task.edit_lease.lease_id,
                "edit_lease_mode": task.edit_lease.lease_mode,
                "edit_lease_allowed_artifacts": "\n".join(task.edit_lease.allowed_artifacts),
            }
        )
    if task.run_id:
        metadata["run_id"] = task.run_id
    if run_records:
        metadata["run_record_run_ids"] = "\n".join(record.run_id for record in run_records)
        metadata["run_record_session_ids"] = "\n".join(record.session_id for record in run_records)
        metadata["run_record_states"] = "\n".join(record.state for record in run_records)
    if scheduler_events:
        metadata["scheduler_event_ids"] = "\n".join(event.event_id for event in scheduler_events)
        metadata["scheduler_event_kinds"] = "\n".join(event.event_kind for event in scheduler_events)
        metadata["scheduler_event_timestamps"] = "\n".join(event.timestamp for event in scheduler_events)
        metadata["scheduler_event_sequences"] = "\n".join(
            "" if event.sequence is None else str(event.sequence)
            for event in scheduler_events
        )
    if fan_in_dependencies:
        metadata["scheduler_fan_in_dependency_ids"] = "\n".join(
            dependency.dependency_id for dependency in fan_in_dependencies
        )
        metadata["scheduler_fan_in_source_task_ids"] = "\n".join(
            dependency.source_task_id for dependency in fan_in_dependencies
        )
    if merge_gates:
        metadata["scheduler_merge_gate_ids"] = "\n".join(gate.gate_id for gate in merge_gates)
        metadata["scheduler_merge_gate_states"] = "\n".join(gate.state for gate in merge_gates)
        metadata["scheduler_merge_gate_kinds"] = "\n".join(gate.gate_kind for gate in merge_gates)
    if task.output_artifact_ref is not None:
        metadata["output_artifact_id"] = task.output_artifact_ref.ref_id
        metadata["output_artifact_version"] = task.output_artifact_ref.version
    elif run_records:
        latest_record = run_records[-1]
        metadata["output_artifact_id"] = latest_record.output_artifact_id
        metadata["output_artifact_version"] = latest_record.output_artifact_version
    if task.blocked_reason:
        metadata["blocked_reason"] = task.blocked_reason
    return metadata


def _merge_gate_metadata(
    gate: SchedulerMergeGate,
    events: tuple[SchedulerMergeGateEvent, ...],
) -> dict[str, str]:
    metadata = {
        "projection": "scheduler-state",
        "authority": "scheduler",
        "scheduler_projection_role": "scheduler-owned-merge-gate",
        "scheduler_merge_gate_id": gate.gate_id,
        "scheduler_merge_gate_kind": gate.gate_kind,
        "scheduler_merge_gate_state": gate.state,
        "scheduler_target_task_id": gate.target_task_id,
        "scheduler_source_task_ids": "\n".join(gate.source_task_ids),
        "scheduler_dependency_ids": "\n".join(gate.dependency_ids),
        "required_review": "true" if gate.required_review else "false",
    }
    if gate.output_artifact_id:
        metadata["output_artifact_id"] = gate.output_artifact_id
    if gate.decision_artifact_ref is not None:
        metadata["decision_artifact_id"] = gate.decision_artifact_ref.ref_id
        metadata["decision_artifact_version"] = gate.decision_artifact_ref.version
    if gate.blocked_reason:
        metadata["blocked_reason"] = gate.blocked_reason
    if gate.created_at:
        metadata["created_at"] = gate.created_at
    if gate.resolved_at:
        metadata["resolved_at"] = gate.resolved_at
    if events:
        metadata["scheduler_merge_gate_event_ids"] = "\n".join(event.event_id for event in events)
        metadata["scheduler_merge_gate_event_kinds"] = "\n".join(event.event_kind for event in events)
        metadata["scheduler_merge_gate_event_timestamps"] = "\n".join(event.timestamp for event in events)
        metadata["scheduler_merge_gate_event_sequences"] = "\n".join(
            "" if event.sequence is None else str(event.sequence)
            for event in events
        )
        metadata["scheduler_merge_gate_event_log"] = "\n".join(
            _merge_gate_event_log_entry(event)
            for event in events
        )
        decision_artifact_ids = tuple(
            event.decision_artifact_id
            for event in events
            if event.decision_artifact_id
        )
        decision_artifact_versions = tuple(
            event.decision_artifact_version
            for event in events
            if event.decision_artifact_version
        )
        if decision_artifact_ids:
            metadata["scheduler_merge_gate_event_decision_artifact_ids"] = "\n".join(decision_artifact_ids)
        if decision_artifact_versions:
            metadata["scheduler_merge_gate_event_decision_artifact_versions"] = "\n".join(decision_artifact_versions)
    return metadata


def _scheduler_event_order_key(event: SchedulerEvent) -> tuple[int, str, str]:
    sequence = event.sequence if event.sequence is not None else 10**9
    return (sequence, event.timestamp, event.event_id)


def _merge_gate_event_order_key(event: SchedulerMergeGateEvent) -> tuple[int, str, str]:
    sequence = event.sequence if event.sequence is not None else 10**9
    return (sequence, event.timestamp, event.event_id)


def _scheduler_history_timeline(
    scheduler_events: tuple[SchedulerEvent, ...],
    merge_gate_events: tuple[SchedulerMergeGateEvent, ...],
    *,
    limit: int,
) -> _SchedulerHistoryTimeline:
    entries: list[tuple[int, str, str, str]] = []
    for event in scheduler_events:
        sequence = event.sequence if event.sequence is not None else 10**9
        entries.append((sequence, event.timestamp, event.event_id, _scheduler_event_timeline_entry(event)))
    for event in merge_gate_events:
        sequence = event.sequence if event.sequence is not None else 10**9
        entries.append((sequence, event.timestamp, event.event_id, _merge_gate_timeline_entry(event)))

    ordered = tuple(line for _, _, _, line in sorted(entries))
    if limit <= 0:
        return _SchedulerHistoryTimeline(lines=(), total_count=len(ordered), limit=limit)
    return _SchedulerHistoryTimeline(
        lines=ordered[:limit],
        total_count=len(ordered),
        limit=limit,
    )


def _scheduler_event_timeline_entry(event: SchedulerEvent) -> str:
    parts = [
        f"timestamp={event.timestamp}",
        f"kind={event.event_kind}",
        f"id={event.event_id}",
        f"task={event.task_id}",
    ]
    if event.sequence is not None:
        parts.append(f"sequence={event.sequence}")
    if event.from_state or event.to_state:
        parts.append(f"state={event.from_state or '?'}->{event.to_state or '?'}")
    if event.reason:
        parts.append(f"reason={event.reason}")
    if event.run_id:
        parts.append(f"run={event.run_id}")
    if event.session_id:
        parts.append(f"session={event.session_id}")
    if event.output_artifact_id:
        artifact = event.output_artifact_id
        if event.output_artifact_version:
            artifact = f"{artifact}@{event.output_artifact_version}"
        parts.append(f"output_artifact={artifact}")
    if event.related_dependency_ids:
        parts.append(f"dependencies={','.join(event.related_dependency_ids)}")
    if event.related_artifact_ids:
        parts.append(f"artifacts={','.join(event.related_artifact_ids)}")
    return " | ".join(parts)


def _merge_gate_timeline_entry(event: SchedulerMergeGateEvent) -> str:
    parts = [
        f"timestamp={event.timestamp}",
        f"kind={event.event_kind}",
        f"id={event.event_id}",
        f"gate={event.gate_id}",
    ]
    if event.target_task_id:
        parts.append(f"target={event.target_task_id}")
    if event.sequence is not None:
        parts.append(f"sequence={event.sequence}")
    if event.from_state or event.to_state:
        parts.append(f"state={event.from_state or '?'}->{event.to_state or '?'}")
    if event.reason:
        parts.append(f"reason={event.reason}")
    if event.decision_artifact_id:
        artifact = event.decision_artifact_id
        if event.decision_artifact_version:
            artifact = f"{artifact}@{event.decision_artifact_version}"
        parts.append(f"decision_artifact={artifact}")
    if event.related_dependency_ids:
        parts.append(f"dependencies={','.join(event.related_dependency_ids)}")
    if event.related_task_ids:
        parts.append(f"tasks={','.join(event.related_task_ids)}")
    return " | ".join(parts)


def _merge_gate_event_log_entry(event: SchedulerMergeGateEvent) -> str:
    parts = [
        f"timestamp={event.timestamp}",
        f"kind={event.event_kind}",
        f"id={event.event_id}",
    ]
    if event.sequence is not None:
        parts.append(f"sequence={event.sequence}")
    if event.from_state or event.to_state:
        parts.append(f"state={event.from_state or '?'}->{event.to_state or '?'}")
    if event.reason:
        parts.append(f"reason={event.reason}")
    if event.decision_artifact_id:
        artifact = event.decision_artifact_id
        if event.decision_artifact_version:
            artifact = f"{artifact}@{event.decision_artifact_version}"
        parts.append(f"decision_artifact={artifact}")
    return " | ".join(parts)


def _dependency_metadata(dependency: TaskDependency) -> dict[str, str]:
    return {
        "projection": "scheduler-state",
        "authority": "scheduler",
        "scheduler_dependency_id": dependency.dependency_id,
        "source_task_id": dependency.source_task_id,
        "target_task_id": dependency.target_task_id,
        "required_state": dependency.required_state,
    }
