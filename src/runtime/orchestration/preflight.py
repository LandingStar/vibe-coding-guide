"""Preflight assembly for admitted scheduler tasks."""

from __future__ import annotations

from dataclasses import dataclass

from .agent_storage import AgentScratchSpace
from .runtime_adapter import AgentRuntimeAdapterRegistry, RuntimeRunResult, TaskSpec
from .sandbox import SandboxAllocation, SandboxProviderRegistry, SandboxRequest
from .scheduler import (
    EditLeaseLifecycleRecord,
    SchedulerDrainStopReason,
    SchedulerEventSink,
    SchedulerRunPolicy,
    SchedulerState,
    ScheduledTask,
    mark_task_blocked_after_runtime_failure,
    mark_ready_tasks,
    run_ready_task,
    task_to_runtime_spec,
)


@dataclass(frozen=True, slots=True)
class OrchestrationPreflightBundle:
    """Execution-preparation bundle assembled before runtime invocation."""

    task: ScheduledTask
    runtime_task: TaskSpec
    scratch: AgentScratchSpace
    sandbox_allocation: SandboxAllocation


@dataclass(frozen=True, slots=True)
class PreflightedTaskRunResult:
    """Result of running a task through an existing preflight bundle."""

    preflight: OrchestrationPreflightBundle
    state: SchedulerState
    runtime_result: RuntimeRunResult


@dataclass(frozen=True, slots=True)
class PreflightDrainResult:
    """Result of serially draining ready tasks through preflight bundles."""

    state: SchedulerState
    preflight_results: tuple[PreflightedTaskRunResult, ...] = ()
    stop_reason: SchedulerDrainStopReason = "no_ready_tasks"
    ready_task_ids: tuple[str, ...] = ()
    blocked_task_ids: tuple[str, ...] = ()
    failed_task_id: str = ""
    failed_task_ids: tuple[str, ...] = ()
    stop_detail: str = ""


def build_orchestration_preflight_bundle(
    task: ScheduledTask,
    *,
    sandbox_registry: SandboxProviderRegistry,
    scheduler_state: SchedulerState | None = None,
    workspace_root: str = "",
    scratch_root: str = ".codex/scratch",
    created_at: str = "",
    expires_at: str = "",
) -> OrchestrationPreflightBundle:
    """Assemble scheduler, sandbox, scratch, and runtime task inputs.

    This helper does not run the task, create directories, or mutate scheduler
    state. It only produces the project-owned preflight products that a later
    executor can consume.
    """

    if task.state != "ready":
        raise ValueError(f"cannot build preflight bundle for task {task.task_id!r}: state is {task.state!r}")

    scratch = _scratch_for_task(
        task,
        scratch_root=scratch_root,
        created_at=created_at,
        expires_at=expires_at,
    )
    provider = sandbox_registry.get(task.sandbox_profile.profile_kind)
    allocation = provider.allocate(
        SandboxRequest(
            task_id=task.task_id,
            profile=task.sandbox_profile,
            edit_lease=task.edit_lease,
            edit_lease_lifecycle=_edit_lease_lifecycle_for_task(
                task,
                scheduler_state,
            ),
            workspace_root=workspace_root,
            scratch_path=scratch.path,
            required_mounts=_required_mounts_for_task(task),
            metadata={
                "context_id": task.context_scope.context_id,
                "lane_id": task.context_scope.lane_id,
                "agent_id": task.agent.agent_id,
            },
        )
    )
    if allocation.state != "allocated":
        raise ValueError(
            f"sandbox allocation rejected for task {task.task_id!r}: "
            f"{allocation.reason or allocation.state}"
        )
    return OrchestrationPreflightBundle(
        task=task,
        runtime_task=task_to_runtime_spec(task),
        scratch=scratch,
        sandbox_allocation=allocation,
    )


def drain_preflighted_ready_tasks(
    state: SchedulerState,
    *,
    sandbox_registry: SandboxProviderRegistry,
    runtime_registry: AgentRuntimeAdapterRegistry,
    policy: SchedulerRunPolicy | None = None,
    max_runs: int | None = None,
    workspace_root: str = "",
    scratch_root: str = ".codex/scratch",
    created_at: str = "",
    expires_at: str = "",
    event_log: SchedulerEventSink | None = None,
    timestamp: str = "",
) -> PreflightDrainResult:
    """Serially drain ready tasks through preflight assembly and runtime execution."""

    active_policy = _normalize_run_policy(policy, max_runs)
    _validate_run_policy(active_policy)
    current = mark_ready_tasks(state, event_log=event_log, timestamp=timestamp)
    results: list[PreflightedTaskRunResult] = []
    failed_task_ids: list[str] = []

    while True:
        ready_task_ids = _ready_task_ids(current)
        if not ready_task_ids:
            blocked_task_ids = _blocked_task_ids(current)
            if failed_task_ids:
                return PreflightDrainResult(
                    state=current,
                    preflight_results=tuple(results),
                    stop_reason="completed_with_failures",
                    blocked_task_ids=blocked_task_ids,
                    failed_task_id=failed_task_ids[0],
                    failed_task_ids=tuple(failed_task_ids),
                    stop_detail="ready queue drained after preflight/runtime failures",
                )
            if blocked_task_ids:
                return PreflightDrainResult(
                    state=current,
                    preflight_results=tuple(results),
                    stop_reason="blocked_tasks",
                    blocked_task_ids=blocked_task_ids,
                    stop_detail="one or more tasks are blocked",
                )
            return PreflightDrainResult(
                state=current,
                preflight_results=tuple(results),
                stop_reason="no_ready_tasks",
            )

        if active_policy.max_runs is not None and len(results) >= active_policy.max_runs:
            return PreflightDrainResult(
                state=current,
                preflight_results=tuple(results),
                stop_reason="max_runs_reached",
                ready_task_ids=ready_task_ids,
                blocked_task_ids=_blocked_task_ids(current),
                failed_task_id=failed_task_ids[0] if failed_task_ids else "",
                failed_task_ids=tuple(failed_task_ids),
            )

        task_id = ready_task_ids[0]
        try:
            preflight = build_orchestration_preflight_bundle(
                current.tasks[task_id],
                sandbox_registry=sandbox_registry,
                scheduler_state=current,
                workspace_root=workspace_root,
                scratch_root=scratch_root,
                created_at=created_at,
                expires_at=expires_at,
            )
            run = run_preflighted_task(
                current,
                preflight,
                runtime_registry=runtime_registry,
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
                current = mark_ready_tasks(blocked_state, event_log=event_log, timestamp=timestamp)
                continue
            return PreflightDrainResult(
                state=blocked_state,
                preflight_results=tuple(results),
                stop_reason="task_failed",
                ready_task_ids=tuple(
                    task for task in _ready_task_ids(blocked_state) if task != task_id
                ),
                blocked_task_ids=_blocked_task_ids(blocked_state),
                failed_task_id=task_id,
                failed_task_ids=tuple(failed_task_ids),
                stop_detail=str(exc),
            )
        results.append(run)
        current = mark_ready_tasks(run.state, event_log=event_log, timestamp=timestamp)


def run_preflighted_task(
    state: SchedulerState,
    preflight: OrchestrationPreflightBundle,
    *,
    runtime_registry: AgentRuntimeAdapterRegistry,
    event_log: SchedulerEventSink | None = None,
    timestamp: str = "",
) -> PreflightedTaskRunResult:
    """Run a preflighted ready task through the scheduler-owned run path."""

    task_id = preflight.task.task_id
    current = state.tasks.get(task_id)
    if current is None:
        raise ValueError(f"preflight task {task_id!r} is missing from scheduler state")
    if current != preflight.task:
        raise ValueError(
            f"preflight bundle for task {task_id!r} does not match current scheduler state"
        )
    if preflight.sandbox_allocation.state != "allocated":
        raise ValueError(
            f"preflight sandbox allocation for task {task_id!r} is not allocated: "
            f"{preflight.sandbox_allocation.state}"
        )

    runtime = runtime_registry.get(current.agent.runtime_provider)
    updated, result = run_ready_task(
        state,
        task_id,
        runtime=runtime,
        event_log=event_log,
        timestamp=timestamp,
    )
    return PreflightedTaskRunResult(
        preflight=preflight,
        state=updated,
        runtime_result=result,
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
    return SchedulerRunPolicy(
        max_runs=max_runs,
        continue_on_failure=policy.continue_on_failure,
        timeout_seconds=policy.timeout_seconds,
        max_retries=policy.max_retries,
    )


def _validate_run_policy(policy: SchedulerRunPolicy) -> None:
    if policy.max_runs is not None and policy.max_runs < 0:
        raise ValueError("max_runs must be non-negative")
    if policy.max_retries < 0:
        raise ValueError("max_retries must be non-negative")
    if policy.timeout_seconds is not None and policy.timeout_seconds < 0:
        raise ValueError("timeout_seconds must be non-negative")


def _ready_task_ids(state: SchedulerState) -> tuple[str, ...]:
    return tuple(sorted(task.task_id for task in state.tasks.values() if task.state == "ready"))


def _blocked_task_ids(state: SchedulerState) -> tuple[str, ...]:
    return tuple(sorted(task.task_id for task in state.tasks.values() if task.state == "blocked"))


def _required_mounts_for_task(task: ScheduledTask) -> tuple[str, ...]:
    mounts = [
        ref.path
        for ref in (*task.context_scope.required_refs, *task.input_artifact_refs)
        if ref.path
    ]
    return tuple(dict.fromkeys(mounts))


def _edit_lease_lifecycle_for_task(
    task: ScheduledTask,
    scheduler_state: SchedulerState | None,
) -> EditLeaseLifecycleRecord | None:
    lease = task.edit_lease
    if lease is None or scheduler_state is None:
        return None
    return scheduler_state.edit_lease_lifecycle.get(lease.lease_id)


def _scratch_for_task(
    task: ScheduledTask,
    *,
    scratch_root: str,
    created_at: str,
    expires_at: str,
) -> AgentScratchSpace:
    normalized_root = scratch_root.rstrip("/\\")
    path = f"{normalized_root}/{task.task_id}" if normalized_root else task.task_id
    return AgentScratchSpace(
        scratch_id=f"scratch:{task.task_id}",
        agent_id=task.agent.agent_id,
        task_id=task.task_id,
        lane_id=task.context_scope.lane_id,
        context_id=task.context_scope.context_id,
        path=path,
        created_at=created_at,
        expires_at=expires_at,
        archive_policy="review-before-retention",
        cleanup_policy="archive-or-delete-on-task-close",
        manifest_path=f"{path}/manifest.json",
        audit_state="active",
    )
