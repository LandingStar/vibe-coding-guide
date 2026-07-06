"""Minimal scheduler skeleton for orchestration-owned task state."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import PurePosixPath, PureWindowsPath
from collections.abc import Mapping
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

AdmissionState = Literal["admissible", "waiting", "review_required", "blocked"]

EditLeaseConflictState = Literal["compatible", "waiting", "review_required", "blocked"]

EditLeaseConflictClassification = Literal[
    "no_overlap",
    "exact_path_overlap",
    "directory_contains_file",
    "directory_overlap",
    "denied_artifact_hit",
    "unsupported_policy",
    "unsafe_path",
    "review_zone_overlap",
]

SUPPORTED_EDIT_LEASE_CONFLICT_POLICIES = ("block-on-overlap",)

EditLeaseLifecycleState = Literal[
    "requested",
    "acquired",
    "waiting",
    "review_required",
    "released",
    "expired",
    "revoked",
    "blocked",
]

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
    "lease_requested",
    "lease_acquired",
    "lease_waiting",
    "lease_review_required",
    "lease_released",
    "lease_expired",
    "lease_revoked",
    "lease_blocked",
    "trajectory_team_worker_assigned",
    "trajectory_team_worker_resolved",
    "trajectory_team_worker_activated",
    "trajectory_team_worker_suspended",
    "trajectory_team_worker_resumed",
    "trajectory_team_worker_transferred",
    "trajectory_team_worker_forked",
    "trajectory_team_worker_released",
    "trajectory_team_no_continuity",
    "continuous_worker_binding_reused",
    "continuous_worker_delivery_lease_reserved",
    "continuous_worker_delivery_lease_started",
    "continuous_worker_delivery_lease_completed",
    "continuous_worker_delivery_lease_failed",
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
class EditLeaseLifecycleRecord:
    """Scheduler-owned lifecycle evidence for one edit lease."""

    lease_id: str
    task_id: str
    state: EditLeaseLifecycleState = "requested"
    mode: EditLeaseMode = "read"
    allowed_artifacts: tuple[str, ...] = ()
    denied_artifacts: tuple[str, ...] = ()
    conflict_policy: str = "block-on-overlap"
    acquired_at: str = ""
    expires_at: str = ""
    released_at: str = ""
    reason: str = ""
    conflict_decision: EditLeaseConflictDecision | None = None


@dataclass(frozen=True, slots=True)
class SchedulerState:
    """Immutable-ish scheduler snapshot for local tests."""

    tasks: dict[str, ScheduledTask] = field(default_factory=dict)
    dependencies: tuple[TaskDependency, ...] = ()
    run_records: tuple[TaskRunRecord, ...] = ()
    merge_gates: tuple[SchedulerMergeGate, ...] = ()
    edit_lease_lifecycle: dict[str, EditLeaseLifecycleRecord] = field(default_factory=dict)


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
    edit_lease_conflict: EditLeaseConflictDecision | None = None


@dataclass(frozen=True, slots=True)
class EditLeaseConflictDecision:
    """Structured scheduler decision for edit lease compatibility."""

    state: EditLeaseConflictState = "compatible"
    classification: EditLeaseConflictClassification = "no_overlap"
    left_task_id: str = ""
    right_task_id: str = ""
    left_lease_id: str = ""
    right_lease_id: str = ""
    left_path: str = ""
    right_path: str = ""
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
    lease_id: str = ""
    edit_lease_lifecycle: EditLeaseLifecycleRecord | None = None
    sequence: int | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


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


def build_requested_edit_lease_lifecycle(
    task: ScheduledTask,
    *,
    timestamp: str = "",
    reason: str = "",
) -> EditLeaseLifecycleRecord | None:
    """Build the initial lifecycle record for a declared task edit lease."""

    lease = task.edit_lease
    if lease is None:
        return None
    return EditLeaseLifecycleRecord(
        lease_id=lease.lease_id,
        task_id=task.task_id,
        state="requested",
        mode=lease.lease_mode,
        allowed_artifacts=lease.allowed_artifacts,
        denied_artifacts=lease.denied_artifacts,
        conflict_policy=lease.conflict_policy,
        expires_at=lease.expires_at,
        reason=reason or "edit lease requested",
    )


def request_edit_lease_for_task(
    state: SchedulerState,
    task_id: str,
    *,
    timestamp: str = "",
    reason: str = "",
) -> SchedulerState:
    """Record that a task declared an edit lease request."""

    task = state.tasks[task_id]
    record = build_requested_edit_lease_lifecycle(
        task,
        timestamp=timestamp,
        reason=reason,
    )
    if record is None:
        return state
    return _replace_edit_lease_lifecycle_record(state, record)


def expire_edit_leases(
    state: SchedulerState,
    *,
    now: str = "",
    event_log: SchedulerEventSink | None = None,
    timestamp: str = "",
) -> SchedulerState:
    """Expire active edit leases using an explicit caller-provided timestamp.

    If ``now`` is empty, no expiry check is performed. This keeps replay paths
    deterministic and prevents hidden wall-clock reads.
    """

    if not now:
        return state
    now_dt = _parse_timestamp(now, field_name="now")
    current = state
    for record in sorted(state.edit_lease_lifecycle.values(), key=lambda item: item.lease_id):
        if record.state not in {"requested", "acquired", "waiting", "review_required"}:
            continue
        if not record.expires_at:
            continue
        expires_at = _parse_timestamp(record.expires_at, field_name="expires_at")
        if expires_at > now_dt:
            continue
        expired = replace(
            record,
            state="expired",
            released_at=now,
            reason=f"edit lease expired at {record.expires_at}",
        )
        current = _replace_edit_lease_lifecycle_record(current, expired)
        _record_scheduler_event(
            event_log,
            event_kind="lease_expired",
            task_id=record.task_id,
            from_state=record.state,
            to_state="expired",
            reason=expired.reason,
            timestamp=timestamp or now,
            lease_lifecycle=expired,
        )
    return current


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

    conflict = classify_edit_lease_conflict(state, task)
    if conflict.state in {"waiting", "review_required", "blocked"}:
        return AdmissionDecision(
            state=conflict.state,
            reason=conflict.reason,
            edit_lease_conflict=conflict,
        )

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
    lifecycle = dict(state.edit_lease_lifecycle)
    for task in state.tasks.values():
        if task.state not in ("proposed", "waiting", "blocked"):
            continue
        decision = evaluate_task_admission(state, task.task_id)
        lifecycle_record = _edit_lease_lifecycle_from_admission(
            state,
            task,
            decision,
            timestamp=timestamp,
        )
        if lifecycle_record is not None:
            lifecycle[lifecycle_record.lease_id] = lifecycle_record
        updated[task.task_id] = _task_from_admission_decision(
            state,
            task,
            decision,
            event_log=event_log,
            timestamp=timestamp,
            lease_lifecycle=lifecycle_record,
        )
    return replace(state, tasks=updated, edit_lease_lifecycle=lifecycle)


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
        lifecycle_record = _edit_lease_lifecycle_from_admission(
            current,
            task,
            decision,
            timestamp=timestamp,
        )
        updated_task = _task_from_admission_decision(
            current,
            task,
            decision,
            event_log=event_log,
            timestamp=timestamp,
            lease_lifecycle=lifecycle_record,
        )
        updated[task_id] = updated_task
        lifecycle = dict(current.edit_lease_lifecycle)
        if lifecycle_record is not None:
            lifecycle[lifecycle_record.lease_id] = lifecycle_record
        current = replace(current, tasks=dict(updated), edit_lease_lifecycle=lifecycle)

    return current


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
        lifecycle_record = _edit_lease_lifecycle_from_admission(
            state,
            task,
            decision,
            timestamp=timestamp,
        )
        task = _task_from_admission_decision(
            state,
            task,
            decision,
            event_log=event_log,
            timestamp=timestamp,
            lease_lifecycle=lifecycle_record,
        )
        if lifecycle_record is not None:
            state = _replace_edit_lease_lifecycle_record(state, lifecycle_record)
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
        revoked_lease = _terminal_edit_lease_lifecycle_record(
            ready_state,
            running,
            next_state="revoked",
            reason=failure_reason,
            timestamp=timestamp,
        )
        _record_scheduler_event(
            event_log,
            event_kind="task_run_failed",
            task_id=task_id,
            from_state="running",
            to_state="blocked",
            reason=failure_reason,
            session_id=session_handle.session_id,
            timestamp=timestamp,
            lease_lifecycle=revoked_lease,
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
            lease_lifecycle=ready_state.edit_lease_lifecycle.get(
                task.edit_lease.lease_id if task.edit_lease else ""
            ),
        )
        return replace(
            ready_state,
            tasks=updated_tasks,
            run_records=ready_state.run_records + (run_record,),
        ), result

    released_lease = _terminal_edit_lease_lifecycle_record(
        ready_state,
        running,
        next_state="released",
        reason="task completed",
        timestamp=timestamp,
    )
    if released_lease is not None:
        updated_lifecycle = dict(ready_state.edit_lease_lifecycle)
        updated_lifecycle[released_lease.lease_id] = released_lease
        ready_state = replace(ready_state, edit_lease_lifecycle=updated_lifecycle)
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
        lease_lifecycle=released_lease,
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
        released_lease = _terminal_edit_lease_lifecycle_record(
            state,
            task,
            next_state="released",
            reason=reason or "permission approved",
            timestamp=timestamp,
        )
        lifecycle = dict(state.edit_lease_lifecycle)
        if released_lease is not None:
            lifecycle[released_lease.lease_id] = released_lease
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
            edit_lease_lifecycle=lifecycle,
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
            lease_lifecycle=released_lease,
        )
        return wake_dependent_tasks(
            approved_state,
            task_id,
            event_log=event_log,
            timestamp=timestamp,
        )

    blocked_reason = reason or "permission rejected"
    revoked_lease = _terminal_edit_lease_lifecycle_record(
        state,
        task,
        next_state="revoked",
        reason=blocked_reason,
        timestamp=timestamp,
    )
    lifecycle = dict(state.edit_lease_lifecycle)
    if revoked_lease is not None:
        lifecycle[revoked_lease.lease_id] = revoked_lease
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
        lease_lifecycle=revoked_lease,
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
        edit_lease_lifecycle=lifecycle,
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


def classify_edit_lease_conflict(
    state: SchedulerState,
    task: ScheduledTask,
) -> EditLeaseConflictDecision:
    """Classify the first scheduler-visible edit lease conflict for *task*."""

    lease = task.edit_lease
    if lease is None:
        return _compatible_edit_lease_decision(task)

    unsupported = _unsupported_conflict_policy_decision(task, lease)
    if unsupported is not None:
        return unsupported

    allowed, unsafe_allowed = _normalize_lease_paths(lease.allowed_artifacts)
    if unsafe_allowed:
        return _unsafe_path_decision(task, lease, unsafe_allowed, side="left")

    denied, unsafe_denied = _normalize_lease_paths(lease.denied_artifacts)
    if unsafe_denied:
        return _unsafe_path_decision(task, lease, unsafe_denied, side="left")

    denied_hit = _first_denied_artifact_hit(
        task=task,
        lease=lease,
        allowed_paths=allowed,
        denied_paths=denied,
    )
    if denied_hit is not None:
        return denied_hit

    if lease.lease_mode == "read" or not allowed:
        return _compatible_edit_lease_decision(task)

    for other in sorted(state.tasks.values(), key=lambda item: item.task_id):
        if other.task_id == task.task_id or other.state not in ("ready", "running"):
            continue
        other_lease = other.edit_lease
        if other_lease is None:
            continue

        other_unsupported = _unsupported_conflict_policy_decision(other, other_lease)
        if other_unsupported is not None:
            return _with_left_context(other_unsupported, task, lease)

        other_allowed, other_unsafe_allowed = _normalize_lease_paths(
            other_lease.allowed_artifacts,
        )
        if other_unsafe_allowed:
            return _unsafe_path_decision(
                other,
                other_lease,
                other_unsafe_allowed,
                side="right",
                left=task,
                left_lease=lease,
            )

        other_denied, other_unsafe_denied = _normalize_lease_paths(
            other_lease.denied_artifacts,
        )
        if other_unsafe_denied:
            return _unsafe_path_decision(
                other,
                other_lease,
                other_unsafe_denied,
                side="right",
                left=task,
                left_lease=lease,
            )

        other_denied_hit = _first_denied_artifact_hit(
            task=other,
            lease=other_lease,
            allowed_paths=other_allowed,
            denied_paths=other_denied,
        )
        if other_denied_hit is not None:
            return _with_left_context(other_denied_hit, task, lease)

        if other_lease.lease_mode == "read" or not other_allowed:
            continue

        for left_path in allowed:
            for right_path in other_allowed:
                if not _paths_overlap(left_path, right_path):
                    continue
                denied_hit = _denied_artifact_hit_between_leases(
                    task=task,
                    lease=lease,
                    other=other,
                    other_lease=other_lease,
                    left_path=left_path,
                    right_path=right_path,
                    denied_paths=denied,
                    other_denied_paths=other_denied,
                )
                if denied_hit is not None:
                    return denied_hit
                return _overlap_edit_lease_decision(
                    task=task,
                    lease=lease,
                    other=other,
                    other_lease=other_lease,
                    left_path=left_path,
                    right_path=right_path,
                )

    return _compatible_edit_lease_decision(task)


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
    failure_reason = _runtime_failure_reason(reason)
    updated[task_id] = replace(task, state="blocked", blocked_reason=failure_reason)
    revoked_lease = _terminal_edit_lease_lifecycle_record(
        state,
        task,
        next_state="revoked",
        reason=failure_reason,
        timestamp="",
    )
    lifecycle = dict(state.edit_lease_lifecycle)
    if revoked_lease is not None:
        lifecycle[revoked_lease.lease_id] = revoked_lease
    return replace(state, tasks=updated, edit_lease_lifecycle=lifecycle)


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
    lease_lifecycle: EditLeaseLifecycleRecord | None = None,
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
                lease_lifecycle=lease_lifecycle,
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
                lease_lifecycle=lease_lifecycle,
            )
        return updated

    if decision.state == "review_required":
        updated = replace(task, state="review_required", blocked_reason=decision.reason)
        if task.state != "review_required" or task.blocked_reason != decision.reason:
            _record_scheduler_event(
                event_log,
                event_kind="task_review_required",
                task_id=task.task_id,
                from_state=task.state,
                to_state="review_required",
                reason=decision.reason,
                timestamp=timestamp,
                lease_lifecycle=lease_lifecycle,
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
            lease_lifecycle=lease_lifecycle,
        )
    return updated


def _replace_edit_lease_lifecycle_record(
    state: SchedulerState,
    record: EditLeaseLifecycleRecord,
) -> SchedulerState:
    lifecycle = dict(state.edit_lease_lifecycle)
    lifecycle[record.lease_id] = record
    return replace(state, edit_lease_lifecycle=lifecycle)


def _edit_lease_lifecycle_from_admission(
    state: SchedulerState,
    task: ScheduledTask,
    decision: AdmissionDecision,
    *,
    timestamp: str,
) -> EditLeaseLifecycleRecord | None:
    lease = task.edit_lease
    if lease is None:
        return None
    existing = state.edit_lease_lifecycle.get(lease.lease_id)
    if decision.state == "admissible":
        acquired_at = (
            existing.acquired_at
            if existing is not None and existing.state == "acquired" and existing.acquired_at
            else timestamp
        )
        return _lease_lifecycle_record_from_task(
            task,
            state="acquired",
            acquired_at=acquired_at,
            reason="edit lease acquired",
        )
    if decision.state == "waiting":
        return _lease_lifecycle_record_from_task(
            task,
            state="waiting",
            acquired_at=existing.acquired_at if existing else "",
            reason=decision.reason,
            conflict_decision=decision.edit_lease_conflict,
        )
    if decision.state == "review_required":
        return _lease_lifecycle_record_from_task(
            task,
            state="review_required",
            acquired_at=existing.acquired_at if existing else "",
            reason=decision.reason,
            conflict_decision=decision.edit_lease_conflict,
        )
    return _lease_lifecycle_record_from_task(
        task,
        state="blocked",
        acquired_at=existing.acquired_at if existing else "",
        reason=decision.reason,
        conflict_decision=decision.edit_lease_conflict,
    )


def _terminal_edit_lease_lifecycle_record(
    state: SchedulerState,
    task: ScheduledTask,
    *,
    next_state: Literal["released", "revoked"],
    reason: str,
    timestamp: str,
) -> EditLeaseLifecycleRecord | None:
    lease = task.edit_lease
    if lease is None:
        return None
    existing = state.edit_lease_lifecycle.get(lease.lease_id)
    return _lease_lifecycle_record_from_task(
        task,
        state=next_state,
        acquired_at=existing.acquired_at if existing else "",
        released_at=timestamp,
        reason=reason,
        conflict_decision=existing.conflict_decision if existing else None,
    )


def _lease_lifecycle_record_from_task(
    task: ScheduledTask,
    *,
    state: EditLeaseLifecycleState,
    acquired_at: str = "",
    released_at: str = "",
    reason: str = "",
    conflict_decision: EditLeaseConflictDecision | None = None,
) -> EditLeaseLifecycleRecord:
    lease = task.edit_lease
    if lease is None:
        raise ValueError(f"task {task.task_id!r} has no edit lease")
    return EditLeaseLifecycleRecord(
        lease_id=lease.lease_id,
        task_id=task.task_id,
        state=state,
        mode=lease.lease_mode,
        allowed_artifacts=lease.allowed_artifacts,
        denied_artifacts=lease.denied_artifacts,
        conflict_policy=lease.conflict_policy,
        acquired_at=acquired_at,
        expires_at=lease.expires_at,
        released_at=released_at,
        reason=reason,
        conflict_decision=conflict_decision,
    )


def _parse_timestamp(value: str, *, field_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid edit lease {field_name}: {value!r}") from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _compatible_edit_lease_decision(task: ScheduledTask) -> EditLeaseConflictDecision:
    lease = task.edit_lease
    return EditLeaseConflictDecision(
        state="compatible",
        classification="no_overlap",
        left_task_id=task.task_id,
        left_lease_id=lease.lease_id if lease else "",
        reason="",
    )


def _unsupported_conflict_policy_decision(
    task: ScheduledTask,
    lease: EditScopeLease,
) -> EditLeaseConflictDecision | None:
    if lease.conflict_policy in SUPPORTED_EDIT_LEASE_CONFLICT_POLICIES:
        return None
    return EditLeaseConflictDecision(
        state="blocked",
        classification="unsupported_policy",
        left_task_id=task.task_id,
        left_lease_id=lease.lease_id,
        reason=(
            f"unsupported edit lease conflict_policy for {task.task_id}: "
            f"{lease.conflict_policy}"
        ),
    )


def _normalize_lease_paths(raw_paths: tuple[str, ...]) -> tuple[tuple[str, ...], str]:
    normalized: list[str] = []
    for raw_path in raw_paths:
        normalized_path = _normalize_lease_path(raw_path)
        if normalized_path is None:
            return tuple(normalized), str(raw_path)
        if normalized_path not in normalized:
            normalized.append(normalized_path)
    return tuple(normalized), ""


def _normalize_lease_path(raw_path: object) -> str | None:
    """Normalize a lease path into a safe project-relative POSIX path."""

    if not isinstance(raw_path, str):
        return None
    stripped = raw_path.strip()
    if not stripped:
        return None
    windows_path = PureWindowsPath(stripped)
    if windows_path.drive or windows_path.root:
        return None
    if PurePosixPath(stripped).is_absolute():
        return None

    candidate = PurePosixPath(stripped.replace("\\", "/"))
    normalized_parts: list[str] = []
    for part in candidate.parts:
        if part in ("", "."):
            continue
        if part == "..":
            return None
        normalized_parts.append(part)

    if not normalized_parts:
        return None
    return PurePosixPath(*normalized_parts).as_posix()


def _unsafe_path_decision(
    task: ScheduledTask,
    lease: EditScopeLease,
    raw_path: str,
    *,
    side: Literal["left", "right"],
    left: ScheduledTask | None = None,
    left_lease: EditScopeLease | None = None,
) -> EditLeaseConflictDecision:
    left_task = left or task
    left_scope = left_lease or lease
    return EditLeaseConflictDecision(
        state="blocked",
        classification="unsafe_path",
        left_task_id=left_task.task_id,
        right_task_id=task.task_id if side == "right" else "",
        left_lease_id=left_scope.lease_id,
        right_lease_id=lease.lease_id if side == "right" else "",
        left_path=raw_path if side == "left" else "",
        right_path=raw_path if side == "right" else "",
        reason=f"unsafe edit lease path for {task.task_id}: {raw_path}",
    )


def _first_denied_artifact_hit(
    *,
    task: ScheduledTask,
    lease: EditScopeLease,
    allowed_paths: tuple[str, ...],
    denied_paths: tuple[str, ...],
) -> EditLeaseConflictDecision | None:
    for allowed_path in allowed_paths:
        for denied_path in denied_paths:
            if allowed_path == denied_path or _path_is_child_of(allowed_path, denied_path):
                return EditLeaseConflictDecision(
                    state="blocked",
                    classification="denied_artifact_hit",
                    left_task_id=task.task_id,
                    left_lease_id=lease.lease_id,
                    left_path=allowed_path,
                    right_path=denied_path,
                    reason=(
                        f"edit lease denied_artifacts conflicts with allowed_artifacts "
                        f"for {task.task_id}: {allowed_path}"
                    ),
                )
    return None


def _denied_artifact_hit_between_leases(
    *,
    task: ScheduledTask,
    lease: EditScopeLease,
    other: ScheduledTask,
    other_lease: EditScopeLease,
    left_path: str,
    right_path: str,
    denied_paths: tuple[str, ...],
    other_denied_paths: tuple[str, ...],
) -> EditLeaseConflictDecision | None:
    for other_denied_path in other_denied_paths:
        if left_path == other_denied_path or _path_is_child_of(left_path, other_denied_path):
            return EditLeaseConflictDecision(
                state="blocked",
                classification="denied_artifact_hit",
                left_task_id=task.task_id,
                right_task_id=other.task_id,
                left_lease_id=lease.lease_id,
                right_lease_id=other_lease.lease_id,
                left_path=left_path,
                right_path=other_denied_path,
                reason=(
                    f"edit lease denied_artifacts conflict with {other.task_id}: "
                    f"{left_path} is denied by {other_denied_path}"
                ),
            )

    for denied_path in denied_paths:
        if right_path == denied_path or _path_is_child_of(right_path, denied_path):
            return EditLeaseConflictDecision(
                state="blocked",
                classification="denied_artifact_hit",
                left_task_id=task.task_id,
                right_task_id=other.task_id,
                left_lease_id=lease.lease_id,
                right_lease_id=other_lease.lease_id,
                left_path=denied_path,
                right_path=right_path,
                reason=(
                    f"edit lease denied_artifacts conflict with {other.task_id}: "
                    f"{right_path} is denied by {denied_path}"
                ),
            )

    return None


def _with_left_context(
    decision: EditLeaseConflictDecision,
    task: ScheduledTask,
    lease: EditScopeLease,
) -> EditLeaseConflictDecision:
    return replace(
        decision,
        left_task_id=task.task_id,
        left_lease_id=lease.lease_id,
        right_task_id=decision.left_task_id,
        right_lease_id=decision.left_lease_id,
        left_path="",
        right_path=decision.left_path,
    )


def _overlap_edit_lease_decision(
    *,
    task: ScheduledTask,
    lease: EditScopeLease,
    other: ScheduledTask,
    other_lease: EditScopeLease,
    left_path: str,
    right_path: str,
) -> EditLeaseConflictDecision:
    classification = _classify_path_overlap(left_path, right_path)
    if lease.lease_mode == "review-zone" or other_lease.lease_mode == "review-zone":
        return EditLeaseConflictDecision(
            state="review_required",
            classification="review_zone_overlap",
            left_task_id=task.task_id,
            right_task_id=other.task_id,
            left_lease_id=lease.lease_id,
            right_lease_id=other_lease.lease_id,
            left_path=left_path,
            right_path=right_path,
            reason=(
                f"edit lease review required with {other.task_id}: "
                f"{left_path} overlaps {right_path}"
            ),
        )

    if left_path == right_path:
        reason = f"edit lease conflict with {other.task_id}: {left_path}"
    else:
        reason = (
            f"edit lease conflict with {other.task_id}: "
            f"{left_path} overlaps {right_path}"
        )
    return EditLeaseConflictDecision(
        state="blocked",
        classification=classification,
        left_task_id=task.task_id,
        right_task_id=other.task_id,
        left_lease_id=lease.lease_id,
        right_lease_id=other_lease.lease_id,
        left_path=left_path,
        right_path=right_path,
        reason=reason,
    )


def _classify_path_overlap(
    left_path: str,
    right_path: str,
) -> EditLeaseConflictClassification:
    if left_path == right_path:
        return "exact_path_overlap"
    if _looks_like_file_path(left_path) or _looks_like_file_path(right_path):
        return "directory_contains_file"
    if _path_is_child_of(left_path, right_path) or _path_is_child_of(right_path, left_path):
        return "directory_overlap"
    return "directory_contains_file"


def _path_is_denied(path: str, denied_paths: tuple[str, ...]) -> bool:
    return any(path == denied or _path_is_child_of(path, denied) for denied in denied_paths)


def _paths_overlap(left: str, right: str) -> bool:
    return left == right or _path_is_child_of(left, right) or _path_is_child_of(right, left)


def _path_is_child_of(path: str, parent: str) -> bool:
    return PurePosixPath(parent) in PurePosixPath(path).parents


def _looks_like_file_path(path: str) -> bool:
    return bool(PurePosixPath(path).suffix)


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
    lease_lifecycle: EditLeaseLifecycleRecord | None = None,
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
            lease_id=lease_lifecycle.lease_id if lease_lifecycle is not None else "",
            edit_lease_lifecycle=lease_lifecycle,
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
