"""Minimal scheduler skeleton for orchestration-owned task state."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from typing import Literal, Protocol

from .exchange import ExchangeReference, ExchangeScope
from .runtime_adapter import (
    AgentRuntimeAdapter,
    AgentRuntimeAdapterRegistry,
    AgentSpec,
    PermissionRequest,
    RuntimeRunResult,
    SessionHandle,
    TaskSpec,
)

RUNTIME_FAILURE_BLOCK_PREFIX = "runtime failure: "

ScheduledTaskState = Literal[
    "proposed",
    "ready",
    "running",
    "waiting",
    "review_required",
    "complete",
    "blocked",
    "cancelled",
]

TaskDependencyKind = Literal["depends_on", "waits_for"]

SchedulerMergeGateKind = Literal[
    "join_only",
    "review",
    "artifact_merge",
    "branch_choice",
    "compatibility_check",
    "conflict_resolution",
]

SchedulerMergeGateState = Literal[
    "proposed",
    "waiting",
    "ready",
    "review_required",
    "complete",
    "blocked",
    "cancelled",
]

EditLeaseMode = Literal["read", "write", "review-zone"]

SandboxProfileKind = Literal["none", "shared-process", "git-worktree", "docker", "remote-vm"]

AdmissionState = Literal["admissible", "waiting", "blocked"]

SchedulerDrainStopReason = Literal[
    "no_ready_tasks",
    "max_runs_reached",
    "blocked_tasks",
    "task_failed",
    "completed_with_failures",
]

SchedulerEventKind = Literal[
    "task_submitted",
    "task_ready",
    "task_waiting",
    "task_blocked",
    "task_running",
    "task_completed",
    "task_run_failed",
    "task_review_required",
    "task_permission_approved",
    "task_permission_rejected",
]

SchedulerMergeGateEventKind = Literal[
    "merge_gate_submitted",
    "merge_gate_waiting",
    "merge_gate_ready",
    "merge_gate_review_required",
    "merge_gate_completed",
    "merge_gate_blocked",
    "merge_gate_cancelled",
]


@dataclass(frozen=True, slots=True)
class ContextScope:
    """Task-visible context boundary."""

    context_id: str
    lane_id: str = ""
    required_refs: tuple[ExchangeReference, ...] = ()
    visible_artifacts: tuple[str, ...] = ()
    session_policy: str = "stateless"
    redaction_policy: str = ""


@dataclass(frozen=True, slots=True)
class EditScopeLease:
    """Project artifact edit authority for a scheduled task."""

    lease_id: str
    task_id: str
    allowed_artifacts: tuple[str, ...] = ()
    denied_artifacts: tuple[str, ...] = ()
    lease_mode: EditLeaseMode = "read"
    conflict_policy: str = "block-on-overlap"
    expires_at: str = ""


@dataclass(frozen=True, slots=True)
class SandboxProfile:
    """Execution isolation profile requested by a scheduled task."""

    profile_id: str
    profile_kind: SandboxProfileKind = "shared-process"
    network_policy: str = "disabled"
    secret_policy: str = "deny"
    mount_policy: str = "lease-scoped"


@dataclass(frozen=True, slots=True)
class TaskDependency:
    """Dependency edge between scheduled tasks."""

    dependency_id: str
    source_task_id: str
    target_task_id: str
    dependency_kind: TaskDependencyKind = "depends_on"
    required_state: ScheduledTaskState = "complete"


@dataclass(frozen=True, slots=True)
class SchedulerMergeGate:
    """Scheduler-owned fan-in gate for join points that require work."""

    gate_id: str
    title: str
    target_task_id: str
    source_task_ids: tuple[str, ...] = ()
    dependency_ids: tuple[str, ...] = ()
    gate_kind: SchedulerMergeGateKind = "join_only"
    state: SchedulerMergeGateState = "proposed"
    required_review: bool = False
    input_artifact_refs: tuple[ExchangeReference, ...] = ()
    output_artifact_id: str = ""
    decision_artifact_ref: ExchangeReference | None = None
    blocked_reason: str = ""
    created_at: str = ""
    resolved_at: str = ""


@dataclass(frozen=True, slots=True)
class ScheduledTask:
    """Scheduler-owned task state."""

    task_id: str
    title: str
    instruction: str
    agent: AgentSpec
    state: ScheduledTaskState = "proposed"
    context_scope: ContextScope = field(default_factory=lambda: ContextScope(context_id="default"))
    edit_lease: EditScopeLease | None = None
    sandbox_profile: SandboxProfile = field(default_factory=lambda: SandboxProfile(profile_id="shared"))
    input_artifact_refs: tuple[ExchangeReference, ...] = ()
    acceptance: tuple[str, ...] = ()
    output_artifact_id: str = ""
    blocked_reason: str = ""
    run_id: str = ""
    output_artifact_ref: ExchangeReference | None = None


@dataclass(frozen=True, slots=True)
class TaskRunRecord:
    """Scheduler record for one runtime invocation."""

    task_id: str
    run_id: str
    session_id: str
    output_artifact_id: str
    output_artifact_version: str
    state: ScheduledTaskState


@dataclass(frozen=True, slots=True)
class SchedulerState:
    """Immutable-ish scheduler snapshot for local tests."""

    tasks: dict[str, ScheduledTask] = field(default_factory=dict)
    dependencies: tuple[TaskDependency, ...] = ()
    run_records: tuple[TaskRunRecord, ...] = ()
    merge_gates: tuple[SchedulerMergeGate, ...] = ()


@dataclass(frozen=True, slots=True)
class SchedulerDrainResult:
    """Result of a bounded ready-queue drain."""

    state: SchedulerState
    run_results: tuple[RuntimeRunResult, ...] = ()
    stop_reason: SchedulerDrainStopReason = "no_ready_tasks"
    ready_task_ids: tuple[str, ...] = ()
    blocked_task_ids: tuple[str, ...] = ()
    failed_task_id: str = ""
    failed_task_ids: tuple[str, ...] = ()
    stop_detail: str = ""


@dataclass(frozen=True, slots=True)
class SchedulerRunPolicy:
    """Bounded scheduler drain policy.

    ``continue_on_failure`` only allows independent ready tasks to continue
    after a failed task is marked blocked. It does not retry the failed branch.
    """

    max_runs: int | None = None
    continue_on_failure: bool = False
    timeout_seconds: int | None = None
    max_retries: int = 0


@dataclass(frozen=True, slots=True)
class AdmissionDecision:
    """Readiness/admission decision for one task."""

    state: AdmissionState
    reason: str = ""


@dataclass(frozen=True, slots=True)
class SchedulerEvent:
    """Append-only scheduler history event."""

    event_id: str
    event_kind: SchedulerEventKind
    timestamp: str
    task_id: str
    from_state: str = ""
    to_state: str = ""
    reason: str = ""
    run_id: str = ""
    session_id: str = ""
    output_artifact_id: str = ""
    output_artifact_version: str = ""
    related_dependency_ids: tuple[str, ...] = ()
    related_artifact_ids: tuple[str, ...] = ()
    sequence: int | None = None


@dataclass(frozen=True, slots=True)
class SchedulerMergeGateEvent:
    """Append-only scheduler history event for merge gates."""

    event_id: str
    event_kind: SchedulerMergeGateEventKind
    timestamp: str
    gate_id: str
    target_task_id: str = ""
    from_state: str = ""
    to_state: str = ""
    reason: str = ""
    decision_artifact_id: str = ""
    decision_artifact_version: str = ""
    related_dependency_ids: tuple[str, ...] = ()
    related_task_ids: tuple[str, ...] = ()
    sequence: int | None = None


class SchedulerEventSink(Protocol):
    """Minimal sink accepted by scheduler helpers for event history."""

    def append(self, event: SchedulerEvent) -> SchedulerEvent:
        """Append one event and return it."""
        ...

    def read_all(self) -> tuple[SchedulerEvent, ...]:
        """Return currently persisted events in append order."""
        ...


class SchedulerMergeGateEventSink(Protocol):
    """Minimal sink accepted by merge-gate helpers for event history."""

    def append(self, event: SchedulerMergeGateEvent) -> SchedulerMergeGateEvent:
        """Append one merge-gate event and return it."""
        ...

    def read_all(self) -> tuple[SchedulerMergeGateEvent, ...]:
        """Return currently persisted merge-gate events in append order."""
        ...


def task_to_runtime_spec(task: ScheduledTask) -> TaskSpec:
    """Convert scheduler-owned task state into runtime adapter task spec."""

    return TaskSpec(
        task_id=task.task_id,
        title=task.title,
        instruction=task.instruction,
        input_artifact_refs=task.input_artifact_refs,
        scope=ExchangeScope(
            lane_id=task.context_scope.lane_id,
            task_id=task.task_id,
            context_id=task.context_scope.context_id,
            agent_id=task.agent.agent_id,
        ),
        acceptance=task.acceptance,
        output_artifact_id=task.output_artifact_id,
    )


def evaluate_task_admission(state: SchedulerState, task_id: str) -> AdmissionDecision:
    """Evaluate whether a task can run now."""

    task = state.tasks[task_id]
    waiting_dependency = _first_unsatisfied_dependency(state, task_id)
    if waiting_dependency is not None:
        return AdmissionDecision(
            state="waiting",
            reason=(
                f"waiting for {waiting_dependency.source_task_id} "
                f"to reach {waiting_dependency.required_state}"
            ),
        )

    waiting_merge_gate = _first_incomplete_merge_gate(state, task_id)
    if waiting_merge_gate is not None:
        return AdmissionDecision(
            state="waiting",
            reason=f"waiting for merge gate {waiting_merge_gate.gate_id} to reach complete",
        )

    conflict = _first_edit_lease_conflict(state, task)
    if conflict:
        return AdmissionDecision(state="blocked", reason=conflict)

    if task.sandbox_profile.profile_kind == "none" and task.edit_lease is not None:
        return AdmissionDecision(
            state="blocked",
            reason="sandbox profile 'none' cannot run a task with an edit lease",
        )

    return AdmissionDecision(state="admissible")


def mark_ready_tasks(
    state: SchedulerState,
    *,
    event_log: SchedulerEventSink | None = None,
    timestamp: str = "",
) -> SchedulerState:
    """Promote proposed tasks to ready or waiting/blocked based on admission."""

    updated = dict(state.tasks)
    for task in state.tasks.values():
        if task.state not in ("proposed", "waiting", "blocked"):
            continue
        decision = evaluate_task_admission(state, task.task_id)
        updated[task.task_id] = _task_from_admission_decision(
            state,
            task,
            decision,
            event_log=event_log,
            timestamp=timestamp,
        )
    return replace(state, tasks=updated)


def wake_dependent_tasks(
    state: SchedulerState,
    source_task_id: str,
    *,
    event_log: SchedulerEventSink | None = None,
    timestamp: str = "",
) -> SchedulerState:
    """Re-evaluate tasks that directly depend on a completed source task."""

    dependent_task_ids = tuple(
        sorted(
            {
                dependency.target_task_id
                for dependency in state.dependencies
                if dependency.source_task_id == source_task_id
                and dependency.target_task_id in state.tasks
            }
        )
    )
    if not dependent_task_ids:
        return state

    updated = dict(state.tasks)
    current = state
    for task_id in dependent_task_ids:
        task = current.tasks[task_id]
        if task.state not in ("proposed", "waiting", "blocked"):
            continue
        decision = evaluate_task_admission(current, task_id)
        updated_task = _task_from_admission_decision(
            current,
            task,
            decision,
            event_log=event_log,
            timestamp=timestamp,
        )
        updated[task_id] = updated_task
        current = replace(current, tasks=dict(updated))

    return replace(state, tasks=updated)


def run_ready_task(
    state: SchedulerState,
    task_id: str,
    *,
    runtime: AgentRuntimeAdapter,
    session: SessionHandle | None = None,
    event_log: SchedulerEventSink | None = None,
    timestamp: str = "",
) -> tuple[SchedulerState, RuntimeRunResult]:
    """Run a ready task through a runtime adapter and return updated state."""

    task = state.tasks[task_id]
    if task.state in ("proposed", "waiting", "blocked"):
        decision = evaluate_task_admission(state, task_id)
        task = _task_from_admission_decision(
            state,
            task,
            decision,
            event_log=event_log,
            timestamp=timestamp,
        )
    ready_tasks = dict(state.tasks)
    ready_tasks[task_id] = task
    ready_state = replace(state, tasks=ready_tasks)
    if task.state != "ready":
        raise ValueError(f"task {task_id!r} is not ready: {task.state} {task.blocked_reason}")

    session_handle = session or runtime.start_session(task.agent)
    running = replace(task, state="running")
    tasks_running = dict(ready_state.tasks)
    tasks_running[task_id] = running
    _record_scheduler_event(
        event_log,
        event_kind="task_running",
        task_id=task_id,
        from_state=task.state,
        to_state="running",
        session_id=session_handle.session_id,
        timestamp=timestamp,
    )

    try:
        result = runtime.run_task(session_handle, task_to_runtime_spec(running))
    except Exception as exc:
        failure_reason = _runtime_failure_reason(str(exc))
        _record_scheduler_event(
            event_log,
            event_kind="task_run_failed",
            task_id=task_id,
            from_state="running",
            to_state="blocked",
            reason=failure_reason,
            session_id=session_handle.session_id,
            timestamp=timestamp,
        )
        raise
    output_ref = ExchangeReference(
        ref_kind="exchange_artifact",
        ref_id=result.output_artifact.artifact_id,
        version=result.output_artifact.version,
    )
    next_state: ScheduledTaskState = (
        "review_required" if result.permission_requests else "complete"
    )
    blocked_reason = (
        _permission_review_reason(result.permission_requests)
        if result.permission_requests
        else ""
    )
    completed = replace(
        running,
        state=next_state,
        blocked_reason=blocked_reason,
        run_id=result.run_handle.run_id,
        output_artifact_ref=output_ref,
    )
    updated_tasks = dict(tasks_running)
    updated_tasks[task_id] = completed
    run_record = TaskRunRecord(
        task_id=task_id,
        run_id=result.run_handle.run_id,
        session_id=result.run_handle.session_id,
        output_artifact_id=result.output_artifact.artifact_id,
        output_artifact_version=result.output_artifact.version,
        state=next_state,
    )
    if result.permission_requests:
        _record_scheduler_event(
            event_log,
            event_kind="task_review_required",
            task_id=task_id,
            from_state="running",
            to_state="review_required",
            reason=blocked_reason,
            run_id=result.run_handle.run_id,
            session_id=result.run_handle.session_id,
            output_artifact_id=result.output_artifact.artifact_id,
            output_artifact_version=result.output_artifact.version,
            related_artifact_ids=(result.output_artifact.artifact_id,),
            timestamp=timestamp,
        )
        return replace(
            ready_state,
            tasks=updated_tasks,
            run_records=ready_state.run_records + (run_record,),
        ), result

    _record_scheduler_event(
        event_log,
        event_kind="task_completed",
        task_id=task_id,
        from_state="running",
        to_state="complete",
        run_id=result.run_handle.run_id,
        session_id=result.run_handle.session_id,
        output_artifact_id=result.output_artifact.artifact_id,
        output_artifact_version=result.output_artifact.version,
        related_artifact_ids=(result.output_artifact.artifact_id,),
        timestamp=timestamp,
    )
    completed_state = replace(
        ready_state,
        tasks=updated_tasks,
        run_records=ready_state.run_records + (run_record,),
    )
    return wake_dependent_tasks(
        completed_state,
        task_id,
        event_log=event_log,
        timestamp=timestamp,
    ), result


def run_scheduled_task_with_registry(
    state: SchedulerState,
    task_id: str,
    *,
    registry: AgentRuntimeAdapterRegistry,
    session: SessionHandle | None = None,
    event_log: SchedulerEventSink | None = None,
    timestamp: str = "",
) -> tuple[SchedulerState, RuntimeRunResult]:
    """Resolve a task runtime from a registry and run the scheduled task."""

    task = state.tasks[task_id]
    runtime = registry.get(task.agent.runtime_provider)
    return run_ready_task(
        state,
        task_id,
        runtime=runtime,
        session=session,
        event_log=event_log,
        timestamp=timestamp,
    )


def resolve_task_permission_review(
    state: SchedulerState,
    task_id: str,
    *,
    approved: bool,
    reason: str = "",
    event_log: SchedulerEventSink | None = None,
    timestamp: str = "",
) -> SchedulerState:
    """Resolve a permission review for a task paused in review_required."""

    task = state.tasks[task_id]
    if task.state != "review_required":
        raise ValueError(f"task {task_id!r} is not in review_required: {task.state}")

    if approved:
        completed = replace(task, state="complete", blocked_reason="")
        updated_tasks = dict(state.tasks)
        updated_tasks[task_id] = completed
        approved_state = replace(
            state,
            tasks=updated_tasks,
            run_records=_replace_task_run_record_state(
                state.run_records,
                task_id=task_id,
                run_id=task.run_id,
                next_state="complete",
            ),
        )
        _record_scheduler_event(
            event_log,
            event_kind="task_permission_approved",
            task_id=task_id,
            from_state="review_required",
            to_state="complete",
            reason=reason or "permission approved",
            run_id=task.run_id,
            output_artifact_id=task.output_artifact_ref.ref_id if task.output_artifact_ref else "",
            output_artifact_version=task.output_artifact_ref.version if task.output_artifact_ref else "",
            related_artifact_ids=(
                (task.output_artifact_ref.ref_id,) if task.output_artifact_ref else ()
            ),
            timestamp=timestamp,
        )
        return wake_dependent_tasks(
            approved_state,
            task_id,
            event_log=event_log,
            timestamp=timestamp,
        )

    blocked_reason = reason or "permission rejected"
    blocked = replace(task, state="blocked", blocked_reason=blocked_reason)
    updated_tasks = dict(state.tasks)
    updated_tasks[task_id] = blocked
    _record_scheduler_event(
        event_log,
        event_kind="task_permission_rejected",
        task_id=task_id,
        from_state="review_required",
        to_state="blocked",
        reason=blocked_reason,
        run_id=task.run_id,
        output_artifact_id=task.output_artifact_ref.ref_id if task.output_artifact_ref else "",
        output_artifact_version=task.output_artifact_ref.version if task.output_artifact_ref else "",
        related_artifact_ids=(
            (task.output_artifact_ref.ref_id,) if task.output_artifact_ref else ()
        ),
        timestamp=timestamp,
    )
    return replace(
        state,
        tasks=updated_tasks,
        run_records=_replace_task_run_record_state(
            state.run_records,
            task_id=task_id,
            run_id=task.run_id,
            next_state="blocked",
        ),
    )


def resolve_scheduler_merge_gate(
    state: SchedulerState,
    gate_id: str,
    *,
    approved: bool,
    reason: str = "",
    decision_artifact_ref: ExchangeReference | None = None,
    resolved_at: str = "",
    event_log: SchedulerMergeGateEventSink | None = None,
    timestamp: str = "",
) -> SchedulerState:
    """Resolve a scheduler-owned merge gate through an external decision."""

    gate = _merge_gate_by_id(state, gate_id)
    if gate.state in {"complete", "blocked", "cancelled"}:
        raise ValueError(f"merge gate {gate_id!r} is already terminal: {gate.state}")

    next_gate = replace(
        gate,
        state="complete" if approved else "blocked",
        blocked_reason="" if approved else (reason or "merge gate rejected"),
        decision_artifact_ref=decision_artifact_ref or gate.decision_artifact_ref,
        resolved_at=resolved_at,
    )
    updated_gates = tuple(
        next_gate if item.gate_id == gate_id else item
        for item in state.merge_gates
    )
    updated = replace(state, merge_gates=updated_gates)
    _record_merge_gate_event(
        event_log,
        event_kind="merge_gate_completed" if approved else "merge_gate_blocked",
        gate=gate,
        next_gate=next_gate,
        reason=reason or ("merge gate approved" if approved else "merge gate rejected"),
        decision_artifact_ref=decision_artifact_ref or gate.decision_artifact_ref,
        timestamp=timestamp or resolved_at,
    )
    if approved:
        return mark_ready_tasks(updated)
    return mark_ready_tasks(updated)


def drain_ready_tasks(
    state: SchedulerState,
    *,
    runtime: AgentRuntimeAdapter,
    max_runs: int | None = None,
    policy: SchedulerRunPolicy | None = None,
    event_log: SchedulerEventSink | None = None,
    timestamp: str = "",
) -> SchedulerDrainResult:
    """Run ready tasks in deterministic order until the queue is drained.

    This helper is intentionally bounded by ``max_runs`` when provided. It is a
    local scheduler primitive, not a long-running daemon.
    """

    active_policy = _normalize_run_policy(policy, max_runs)
    if active_policy.max_runs is not None and active_policy.max_runs < 0:
        raise ValueError("max_runs must be non-negative")
    if active_policy.max_retries < 0:
        raise ValueError("max_retries must be non-negative")
    if active_policy.timeout_seconds is not None and active_policy.timeout_seconds < 0:
        raise ValueError("timeout_seconds must be non-negative")

    current = mark_ready_tasks(state, event_log=event_log, timestamp=timestamp)
    results: list[RuntimeRunResult] = []
    failed_task_ids: list[str] = []

    while True:
        ready_task_ids = _ready_task_ids(current)
        if not ready_task_ids:
            blocked_task_ids = _blocked_task_ids(current)
            if failed_task_ids:
                return SchedulerDrainResult(
                    state=current,
                    run_results=tuple(results),
                    stop_reason="completed_with_failures",
                    blocked_task_ids=blocked_task_ids,
                    failed_task_id=failed_task_ids[0],
                    failed_task_ids=tuple(failed_task_ids),
                    stop_detail="ready queue drained after runtime failures",
                )
            if blocked_task_ids:
                return SchedulerDrainResult(
                    state=current,
                    run_results=tuple(results),
                    stop_reason="blocked_tasks",
                    blocked_task_ids=blocked_task_ids,
                    stop_detail="one or more tasks are blocked",
                )
            return SchedulerDrainResult(
                state=current,
                run_results=tuple(results),
                stop_reason="no_ready_tasks",
                ready_task_ids=(),
            )

        if active_policy.max_runs is not None and len(results) >= active_policy.max_runs:
            return SchedulerDrainResult(
                state=current,
                run_results=tuple(results),
                stop_reason="max_runs_reached",
                ready_task_ids=ready_task_ids,
                blocked_task_ids=_blocked_task_ids(current),
                failed_task_id=failed_task_ids[0] if failed_task_ids else "",
                failed_task_ids=tuple(failed_task_ids),
            )

        task_id = ready_task_ids[0]
        try:
            current, result = run_ready_task(
                current,
                task_id,
                runtime=runtime,
                event_log=event_log,
                timestamp=timestamp,
            )
        except Exception as exc:
            blocked_state = mark_task_blocked_after_runtime_failure(
                current,
                task_id,
                str(exc),
            )
            failed_task_ids.append(task_id)
            if active_policy.continue_on_failure:
                current = mark_ready_tasks(
                    blocked_state,
                    event_log=event_log,
                    timestamp=timestamp,
                )
                continue
            return SchedulerDrainResult(
                state=blocked_state,
                run_results=tuple(results),
                stop_reason="task_failed",
                ready_task_ids=tuple(
                    task for task in _ready_task_ids(blocked_state) if task != task_id
                ),
                blocked_task_ids=_blocked_task_ids(blocked_state),
                failed_task_id=task_id,
                failed_task_ids=tuple(failed_task_ids),
                stop_detail=str(exc),
            )
        results.append(result)
        current = mark_ready_tasks(current, event_log=event_log, timestamp=timestamp)


def _first_unsatisfied_dependency(state: SchedulerState, task_id: str) -> TaskDependency | None:
    for dependency in state.dependencies:
        if dependency.target_task_id != task_id:
            continue
        source = state.tasks.get(dependency.source_task_id)
        if source is None or source.state != dependency.required_state:
            return dependency
    return None


def _first_incomplete_merge_gate(state: SchedulerState, task_id: str) -> SchedulerMergeGate | None:
    for gate in sorted(state.merge_gates, key=lambda item: item.gate_id):
        if gate.target_task_id == task_id and gate.state != "complete":
            return gate
    return None


def _merge_gate_by_id(state: SchedulerState, gate_id: str) -> SchedulerMergeGate:
    for gate in state.merge_gates:
        if gate.gate_id == gate_id:
            return gate
    raise ValueError(f"unknown merge gate: {gate_id!r}")


def _blocking_dependency_ids(state: SchedulerState, task_id: str) -> tuple[str, ...]:
    return tuple(
        dependency.dependency_id
        for dependency in state.dependencies
        if dependency.target_task_id == task_id
        and (
            state.tasks.get(dependency.source_task_id) is None
            or state.tasks[dependency.source_task_id].state != dependency.required_state
        )
    )


def _permission_review_reason(permission_requests: tuple[PermissionRequest, ...]) -> str:
    request_count = len(permission_requests)
    if request_count == 1:
        request = permission_requests[0]
        return f"permission review required: {request.request_kind} {request.target}".rstrip()
    return f"permission review required: {request_count} requests"


def _ready_task_ids(state: SchedulerState) -> tuple[str, ...]:
    return tuple(
        sorted(
            task.task_id
            for task in state.tasks.values()
            if task.state == "ready"
        )
    )


def _normalize_run_policy(
    policy: SchedulerRunPolicy | None,
    max_runs: int | None,
) -> SchedulerRunPolicy:
    if policy is None:
        return SchedulerRunPolicy(max_runs=max_runs)
    if max_runs is None:
        return policy
    if policy.max_runs is not None and policy.max_runs != max_runs:
        raise ValueError("max_runs argument conflicts with policy.max_runs")
    return replace(policy, max_runs=max_runs)


def _blocked_task_ids(state: SchedulerState) -> tuple[str, ...]:
    return tuple(
        sorted(
            task.task_id
            for task in state.tasks.values()
            if task.state == "blocked"
        )
    )


def mark_task_blocked_after_runtime_failure(
    state: SchedulerState,
    task_id: str,
    reason: str,
) -> SchedulerState:
    """Return a state where a failed runtime task is blocked.

    The helper is public within the orchestration package so higher-level
    execution wrappers can preserve the same failure landing semantics as the
    scheduler's direct drain path.
    """

    task = state.tasks[task_id]
    updated = dict(state.tasks)
    updated[task_id] = replace(task, state="blocked", blocked_reason=_runtime_failure_reason(reason))
    return replace(state, tasks=updated)


def _runtime_failure_reason(reason: str) -> str:
    if reason.startswith(RUNTIME_FAILURE_BLOCK_PREFIX):
        return reason
    return f"{RUNTIME_FAILURE_BLOCK_PREFIX}{reason}"


def _replace_task_run_record_state(
    run_records: tuple[TaskRunRecord, ...],
    *,
    task_id: str,
    run_id: str,
    next_state: ScheduledTaskState,
) -> tuple[TaskRunRecord, ...]:
    if not run_id:
        return run_records
    return tuple(
        replace(record, state=next_state)
        if record.task_id == task_id and record.run_id == run_id
        else record
        for record in run_records
    )


def _is_runtime_failure_block(task: ScheduledTask) -> bool:
    return task.state == "blocked" and task.blocked_reason.startswith(RUNTIME_FAILURE_BLOCK_PREFIX)


def _task_from_admission_decision(
    state: SchedulerState,
    task: ScheduledTask,
    decision: AdmissionDecision,
    *,
    event_log: SchedulerEventSink | None,
    timestamp: str,
) -> ScheduledTask:
    if _is_runtime_failure_block(task):
        return task

    if decision.state == "admissible":
        updated = replace(task, state="ready", blocked_reason="")
        if task.state != "ready" or task.blocked_reason:
            _record_scheduler_event(
                event_log,
                event_kind="task_ready",
                task_id=task.task_id,
                from_state=task.state,
                to_state="ready",
                timestamp=timestamp,
            )
        return updated

    if decision.state == "waiting":
        updated = replace(task, state="waiting", blocked_reason=decision.reason)
        if task.state != "waiting" or task.blocked_reason != decision.reason:
            _record_scheduler_event(
                event_log,
                event_kind="task_waiting",
                task_id=task.task_id,
                from_state=task.state,
                to_state="waiting",
                reason=decision.reason,
                related_dependency_ids=_blocking_dependency_ids(state, task.task_id),
                timestamp=timestamp,
            )
        return updated

    updated = replace(task, state="blocked", blocked_reason=decision.reason)
    if task.state != "blocked" or task.blocked_reason != decision.reason:
        _record_scheduler_event(
            event_log,
            event_kind="task_blocked",
            task_id=task.task_id,
            from_state=task.state,
            to_state="blocked",
            reason=decision.reason,
            timestamp=timestamp,
        )
    return updated


def _first_edit_lease_conflict(state: SchedulerState, task: ScheduledTask) -> str:
    lease = task.edit_lease
    if lease is None or lease.lease_mode == "read":
        return ""

    requested = set(lease.allowed_artifacts)
    if not requested:
        return ""

    for other in state.tasks.values():
        if other.task_id == task.task_id or other.state not in ("ready", "running"):
            continue
        other_lease = other.edit_lease
        if other_lease is None or other_lease.lease_mode == "read":
            continue
        overlap = requested.intersection(other_lease.allowed_artifacts)
        if overlap:
            return (
                f"edit lease conflict with {other.task_id}: "
                f"{', '.join(sorted(overlap))}"
            )
    return ""


def _record_scheduler_event(
    event_log: SchedulerEventSink | None,
    *,
    event_kind: SchedulerEventKind,
    task_id: str,
    from_state: str,
    to_state: str,
    timestamp: str = "",
    reason: str = "",
    run_id: str = "",
    session_id: str = "",
    output_artifact_id: str = "",
    output_artifact_version: str = "",
    related_dependency_ids: tuple[str, ...] = (),
    related_artifact_ids: tuple[str, ...] = (),
) -> None:
    if event_log is None:
        return
    existing = event_log.read_all()
    sequence = len(existing) + 1
    event_log.append(
        SchedulerEvent(
            event_id=f"scheduler-event-{sequence}",
            event_kind=event_kind,
            timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
            task_id=task_id,
            from_state=from_state,
            to_state=to_state,
            reason=reason,
            run_id=run_id,
            session_id=session_id,
            output_artifact_id=output_artifact_id,
            output_artifact_version=output_artifact_version,
            related_dependency_ids=related_dependency_ids,
            related_artifact_ids=related_artifact_ids,
            sequence=sequence,
        )
    )


def _record_merge_gate_event(
    event_log: SchedulerMergeGateEventSink | None,
    *,
    event_kind: SchedulerMergeGateEventKind,
    gate: SchedulerMergeGate,
    next_gate: SchedulerMergeGate,
    reason: str = "",
    decision_artifact_ref: ExchangeReference | None = None,
    timestamp: str = "",
) -> None:
    if event_log is None:
        return
    existing = event_log.read_all()
    sequence = len(existing) + 1
    event_log.append(
        SchedulerMergeGateEvent(
            event_id=f"scheduler-merge-gate-event-{sequence}",
            event_kind=event_kind,
            timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
            gate_id=gate.gate_id,
            target_task_id=gate.target_task_id,
            from_state=gate.state,
            to_state=next_gate.state,
            reason=reason,
            decision_artifact_id=decision_artifact_ref.ref_id if decision_artifact_ref else "",
            decision_artifact_version=decision_artifact_ref.version if decision_artifact_ref else "",
            related_dependency_ids=gate.dependency_ids,
            related_task_ids=gate.source_task_ids + ((gate.target_task_id,) if gate.target_task_id else ()),
            sequence=sequence,
        )
    )
