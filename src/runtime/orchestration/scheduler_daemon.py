"""Daemon-ready bounded scheduler tick contract."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .exchange_store import InMemoryArtifactVersionStore
from .runtime_adapter import AgentRuntimeAdapterRegistry, FakeAgentRuntimeAdapter
from .sandbox import SandboxProviderRegistry, SharedProcessSandboxProvider
from .scheduler import SchedulerRunPolicy, SchedulerState
from .scheduler_runner import PersistedSchedulerRunOnceResult, run_persisted_scheduler_once
from .scheduler_store import JsonlSchedulerEventLog


@dataclass(frozen=True, slots=True)
class SchedulerDaemonTickRequest:
    """Request for one bounded daemon-ready scheduler tick."""

    snapshot_path: str | Path
    event_log_path: str | Path
    max_runs: int | None = 1
    runtime_provider: str = "fake"
    timestamp: str = ""
    workspace_root: str = ""
    scratch_root: str = ".codex/scratch"
    created_at: str = ""
    expires_at: str = ""
    strict_recovery: bool = True
    continue_on_failure: bool = False


@dataclass(frozen=True, slots=True)
class SchedulerDaemonQueueSummary:
    """Compact scheduler queue readback for daemon and operator surfaces."""

    task_count: int
    dependency_count: int
    run_record_count: int
    merge_gate_count: int
    task_state_counts: dict[str, int] = field(default_factory=dict)
    task_ids_by_state: dict[str, tuple[str, ...]] = field(default_factory=dict)
    ready_task_ids: tuple[str, ...] = ()
    blocked_task_ids: tuple[str, ...] = ()
    running_task_ids: tuple[str, ...] = ()
    completed_task_ids: tuple[str, ...] = ()
    failed_task_ids: tuple[str, ...] = ()
    waiting_task_ids: tuple[str, ...] = ()
    review_required_task_ids: tuple[str, ...] = ()
    cancelled_task_ids: tuple[str, ...] = ()
    dependency_ids: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-compatible queue summary."""

        return {
            "task_count": self.task_count,
            "dependency_count": self.dependency_count,
            "run_record_count": self.run_record_count,
            "merge_gate_count": self.merge_gate_count,
            "task_state_counts": dict(self.task_state_counts),
            "task_ids_by_state": {
                state: list(task_ids)
                for state, task_ids in self.task_ids_by_state.items()
            },
            "ready_task_ids": list(self.ready_task_ids),
            "blocked_task_ids": list(self.blocked_task_ids),
            "running_task_ids": list(self.running_task_ids),
            "completed_task_ids": list(self.completed_task_ids),
            "failed_task_ids": list(self.failed_task_ids),
            "waiting_task_ids": list(self.waiting_task_ids),
            "review_required_task_ids": list(self.review_required_task_ids),
            "cancelled_task_ids": list(self.cancelled_task_ids),
            "dependency_ids": list(self.dependency_ids),
        }


@dataclass(frozen=True, slots=True)
class SchedulerDaemonTickResult:
    """Result of one bounded scheduler daemon-ready tick."""

    request: SchedulerDaemonTickRequest
    run: PersistedSchedulerRunOnceResult
    queue_summary: SchedulerDaemonQueueSummary
    scheduler_event_count: int = 0
    local_work_trajectory_mutated: bool = False
    scheduler_projection_refreshed: bool = False

    def to_json_dict(self) -> dict[str, object]:
        """Return a compact JSON-compatible tick result."""

        return {
            "ok": True,
            "snapshot_path": str(self.run.snapshot_path),
            "event_log_path": str(self.run.event_log_path),
            "runtime_provider": self.request.runtime_provider,
            "runtime_registry_providers": list(self.run.runtime_registry_providers),
            "runtime_host_surface": self.run.runtime_host_surface,
            "max_runs": self.request.max_runs,
            "run_count": len(self.run.drain.preflight_results),
            "stop_reason": self.run.drain.stop_reason,
            "stop_detail": self.run.drain.stop_detail,
            "state_written": self.run.state_written,
            "scheduler_event_count": self.scheduler_event_count,
            "recovered_event_count": self.run.recovery.event_count,
            "ran_tasks": bool(self.run.drain.preflight_results),
            "refreshed_projection": self.scheduler_projection_refreshed,
            "queue_summary": self.queue_summary.to_json_dict(),
            "authority_split": {
                "scheduler_state_authority": "scheduler_snapshot_and_event_log",
                "scheduler_state_mutated": self.run.state_written,
                "provider_executed": bool(self.run.drain.preflight_results),
                "scheduler_projection_refreshed": self.scheduler_projection_refreshed,
                "local_work_trajectory_mutated": self.local_work_trajectory_mutated,
                "exchange_artifact_store_mutated": False,
                "admission_ledger_mutated": False,
            },
        }


def summarize_scheduler_queue(state: SchedulerState) -> SchedulerDaemonQueueSummary:
    """Build a stable queue summary from scheduler state."""

    task_state_counts: dict[str, int] = {}
    task_ids_by_state_lists: dict[str, list[str]] = {}
    for task_id, task in sorted(state.tasks.items()):
        task_state_counts[task.state] = task_state_counts.get(task.state, 0) + 1
        task_ids_by_state_lists.setdefault(task.state, []).append(task_id)
    task_ids_by_state = {
        state: tuple(task_ids)
        for state, task_ids in sorted(task_ids_by_state_lists.items())
    }

    return SchedulerDaemonQueueSummary(
        task_count=len(state.tasks),
        dependency_count=len(state.dependencies),
        run_record_count=len(state.run_records),
        merge_gate_count=len(state.merge_gates),
        task_state_counts=task_state_counts,
        task_ids_by_state=task_ids_by_state,
        ready_task_ids=task_ids_by_state.get("ready", ()),
        blocked_task_ids=task_ids_by_state.get("blocked", ()),
        running_task_ids=task_ids_by_state.get("running", ()),
        completed_task_ids=task_ids_by_state.get("complete", ()),
        failed_task_ids=tuple(
            task_id
            for task_id, task in sorted(state.tasks.items())
            if task.state == "blocked" and task.blocked_reason.startswith("runtime failure: ")
        ),
        waiting_task_ids=task_ids_by_state.get("waiting", ()),
        review_required_task_ids=task_ids_by_state.get("review_required", ()),
        cancelled_task_ids=task_ids_by_state.get("cancelled", ()),
        dependency_ids=tuple(dependency.dependency_id for dependency in state.dependencies),
    )


def run_scheduler_daemon_tick(
    request: SchedulerDaemonTickRequest,
    *,
    runtime_registry: AgentRuntimeAdapterRegistry | None = None,
    sandbox_registry: SandboxProviderRegistry | None = None,
    artifact_store: InMemoryArtifactVersionStore | None = None,
) -> SchedulerDaemonTickResult:
    """Run one bounded scheduler tick over durable scheduler state.

    This is daemon-ready but not a long-running daemon. The default path is
    fake-runtime only; non-fake execution must come from an explicitly injected
    host-owned runtime registry.
    """

    if request.max_runs is not None and request.max_runs < 0:
        raise ValueError("scheduler daemon tick max_runs must be non-negative")
    if runtime_registry is None and request.runtime_provider != "fake":
        raise ValueError(
            "scheduler daemon tick only supports runtime_provider='fake' unless "
            "a host-owned runtime registry is explicitly injected"
        )

    active_runtime_registry = runtime_registry or _default_fake_runtime_registry(
        artifact_store=artifact_store,
        timestamp=request.timestamp,
    )
    if not active_runtime_registry.has(request.runtime_provider):  # type: ignore[arg-type]
        available = ", ".join(active_runtime_registry.providers()) or "(none)"
        raise ValueError(
            "scheduler daemon tick runtime provider "
            f"{request.runtime_provider!r} is not registered; available providers: {available}"
        )
    active_sandbox_registry = sandbox_registry or _default_sandbox_registry()
    policy = SchedulerRunPolicy(
        max_runs=request.max_runs,
        continue_on_failure=request.continue_on_failure,
    )
    run = run_persisted_scheduler_once(
        snapshot_path=request.snapshot_path,
        event_log_path=request.event_log_path,
        sandbox_registry=active_sandbox_registry,
        runtime_registry=active_runtime_registry,
        policy=policy,
        workspace_root=request.workspace_root,
        scratch_root=request.scratch_root,
        created_at=request.created_at,
        expires_at=request.expires_at,
        timestamp=request.timestamp,
        strict_recovery=request.strict_recovery,
    )
    queue_summary = summarize_scheduler_queue(run.drain.state)
    scheduler_event_count = len(JsonlSchedulerEventLog(request.event_log_path).read_all())
    return SchedulerDaemonTickResult(
        request=request,
        run=run,
        queue_summary=queue_summary,
        scheduler_event_count=scheduler_event_count,
    )


def _default_fake_runtime_registry(
    *,
    artifact_store: InMemoryArtifactVersionStore | None = None,
    timestamp: str = "",
) -> AgentRuntimeAdapterRegistry:
    registry = AgentRuntimeAdapterRegistry()
    registry.register(
        FakeAgentRuntimeAdapter(
            artifact_store=artifact_store or InMemoryArtifactVersionStore(),
            timestamp=timestamp or "1970-01-01T00:00:00+00:00",
        )
    )
    return registry


def _default_sandbox_registry() -> SandboxProviderRegistry:
    registry = SandboxProviderRegistry()
    registry.register(SharedProcessSandboxProvider())
    return registry
