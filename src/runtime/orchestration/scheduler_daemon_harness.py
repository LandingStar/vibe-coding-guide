"""Host-managed bounded scheduler daemon process harness.

The harness is a local host-owned loop around the existing scheduler daemon
lifecycle control file. It deliberately does not install or start an OS service.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from .artifact_paths import DEFAULT_DBC_SCRATCH_ROOT
from .exchange_store import InMemoryArtifactVersionStore
from .runtime_adapter import AgentRuntimeAdapterRegistry
from .sandbox import SandboxProviderRegistry
from .scheduler_daemon import SchedulerDaemonLoopStopPolicy
from .scheduler_daemon_lifecycle import (
    SchedulerDaemonLifecycleRunOnceRequest,
    SchedulerDaemonLifecycleRunOnceResult,
    inspect_scheduler_daemon_lifecycle_control,
    read_scheduler_daemon_lifecycle_control,
    run_scheduler_daemon_lifecycle_once,
)

SchedulerDaemonHarnessStopReason = Literal[
    "max_cycles_reached",
    "no_ready_tasks",
    "paused",
    "cancelling",
    "cancelled",
    "stopped",
    "stale",
    "loop_failure_limit_reached",
    "lifecycle_skipped",
]

SchedulerDaemonHarnessPolicyStopReason = Literal[
    "cancelled",
    "deadline_exceeded",
    "harness_completed",
    "max_attempts_reached",
]


@dataclass(frozen=True, slots=True)
class SchedulerDaemonHarnessRequest:
    """Request for a bounded host-managed scheduler daemon harness run."""

    control_path: str | Path
    max_cycles: int = 1
    stop_policy: SchedulerDaemonLoopStopPolicy = field(default_factory=SchedulerDaemonLoopStopPolicy)
    runtime_provider: str = "fake"
    timestamp: str = ""
    workspace_root: str = ""
    scratch_root: str = DEFAULT_DBC_SCRATCH_ROOT
    created_at: str = ""
    expires_at: str = ""
    strict_recovery: bool = True
    continue_on_failure: bool = True
    stale_now_epoch_seconds: int | None = None
    stale_after_seconds: int | None = None
    max_loop_failures: int | None = 1


@dataclass(frozen=True, slots=True)
class SchedulerDaemonHarnessCycle:
    """One bounded harness cycle summary."""

    cycle_index: int
    state_before: str
    state_after: str
    run_once: SchedulerDaemonLifecycleRunOnceResult | None = None
    skipped: bool = False
    skip_reason: str = ""
    stop_reason: SchedulerDaemonHarnessStopReason | str = ""

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-compatible cycle payload."""

        run_payload = None if self.run_once is None else self.run_once.to_json_dict()
        loop_payload = None if run_payload is None else run_payload.get("loop")
        return {
            "cycle_index": self.cycle_index,
            "state_before": self.state_before,
            "state_after": self.state_after,
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
            "stop_reason": self.stop_reason,
            "run_once": run_payload,
            "loop_stop_reason": "" if loop_payload is None else str(loop_payload.get("stop_reason", "")),
            "loop_total_run_count": 0 if loop_payload is None else int(loop_payload.get("total_run_count", 0)),
            "loop_tick_count": 0 if loop_payload is None else int(loop_payload.get("tick_count", 0)),
        }


@dataclass(frozen=True, slots=True)
class SchedulerDaemonHarnessResult:
    """Result of one bounded host-managed harness run."""

    request: SchedulerDaemonHarnessRequest
    control_path: Path
    cycles: tuple[SchedulerDaemonHarnessCycle, ...]
    stop_reason: SchedulerDaemonHarnessStopReason
    stop_detail: str = ""
    local_work_trajectory_mutated: bool = False
    scheduler_projection_refreshed: bool = False

    @property
    def cycle_count(self) -> int:
        """Return completed harness cycle count."""

        return len(self.cycles)

    @property
    def total_run_count(self) -> int:
        """Return task-run count across all cycles."""

        total = 0
        for cycle in self.cycles:
            if cycle.run_once is not None and cycle.run_once.loop is not None:
                total += cycle.run_once.loop.total_run_count
        return total

    def to_json_dict(self) -> dict[str, object]:
        """Return a compact JSON-compatible harness result."""

        return {
            "ok": True,
            "control_path": str(self.control_path),
            "max_cycles": self.request.max_cycles,
            "cycle_count": self.cycle_count,
            "total_run_count": self.total_run_count,
            "stop_reason": self.stop_reason,
            "stop_detail": self.stop_detail,
            "cycles": [cycle.to_json_dict() for cycle in self.cycles],
            "authority_split": {
                "harness_authority": "host-owned-bounded-process-harness",
                "lifecycle_authority": "scheduler_daemon_lifecycle_control_file",
                "scheduler_state_authority": "scheduler_snapshot_and_event_log",
                "starts_os_service": False,
                "runtime_provider": self.request.runtime_provider,
                "fake_runtime_only_by_default": self.request.runtime_provider == "fake",
                "scheduler_projection_refreshed": self.scheduler_projection_refreshed,
                "local_work_trajectory_mutated": self.local_work_trajectory_mutated,
                "exchange_artifact_store_mutated": False,
                "admission_ledger_mutated": False,
            },
        }


@dataclass(frozen=True, slots=True)
class SchedulerDaemonHarnessPolicy:
    """Deterministic retry/deadline/cancellation policy over harness runs."""

    cancelled: bool = False
    deadline_epoch_seconds: int | None = None
    now_epoch_seconds: int | None = None
    max_attempts: int = 1
    retry_stop_reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SchedulerDaemonHarnessPolicyAttempt:
    """One policy-controlled harness attempt."""

    attempt_index: int
    harness: SchedulerDaemonHarnessResult
    retryable: bool = False

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-compatible policy attempt payload."""

        return {
            "attempt_index": self.attempt_index,
            "retryable": self.retryable,
            "harness": self.harness.to_json_dict(),
        }


@dataclass(frozen=True, slots=True)
class SchedulerDaemonHarnessPolicyResult:
    """Result of applying policy to one or more bounded harness attempts."""

    request: SchedulerDaemonHarnessRequest
    policy: SchedulerDaemonHarnessPolicy
    attempts: tuple[SchedulerDaemonHarnessPolicyAttempt, ...] = ()
    stop_reason: SchedulerDaemonHarnessPolicyStopReason = "harness_completed"
    stop_detail: str = ""

    @property
    def attempt_count(self) -> int:
        """Return completed policy attempt count."""

        return len(self.attempts)

    @property
    def total_run_count(self) -> int:
        """Return task-run count across all policy attempts."""

        return sum(attempt.harness.total_run_count for attempt in self.attempts)

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-compatible policy result payload."""

        return {
            "ok": True,
            "control_path": str(Path(self.request.control_path)),
            "policy": {
                "cancelled": self.policy.cancelled,
                "deadline_epoch_seconds": self.policy.deadline_epoch_seconds,
                "now_epoch_seconds": self.policy.now_epoch_seconds,
                "max_attempts": self.policy.max_attempts,
                "retry_stop_reasons": list(self.policy.retry_stop_reasons),
            },
            "attempt_count": self.attempt_count,
            "total_run_count": self.total_run_count,
            "stop_reason": self.stop_reason,
            "stop_detail": self.stop_detail,
            "attempts": [attempt.to_json_dict() for attempt in self.attempts],
            "authority_split": {
                "policy_authority": "host-owned-harness-policy",
                "harness_authority": "host-owned-bounded-process-harness",
                "lifecycle_authority": "scheduler_daemon_lifecycle_control_file",
                "scheduler_state_authority": "scheduler_snapshot_and_event_log",
                "starts_os_service": False,
                "scheduler_projection_refreshed": False,
                "local_work_trajectory_mutated": False,
                "exchange_artifact_store_mutated": False,
                "admission_ledger_mutated": False,
            },
        }


def run_scheduler_daemon_harness(
    request: SchedulerDaemonHarnessRequest,
    *,
    runtime_registry: AgentRuntimeAdapterRegistry | None = None,
    sandbox_registry: SandboxProviderRegistry | None = None,
    artifact_store: InMemoryArtifactVersionStore | None = None,
) -> SchedulerDaemonHarnessResult:
    """Run a bounded host-managed harness around lifecycle run-once."""

    _validate_harness_request(request)
    control_path = Path(request.control_path)
    if request.max_cycles == 0:
        return SchedulerDaemonHarnessResult(
            request=request,
            control_path=control_path,
            cycles=(),
            stop_reason="max_cycles_reached",
            stop_detail="max_cycles is 0",
        )
    cycles: list[SchedulerDaemonHarnessCycle] = []
    stop_reason: SchedulerDaemonHarnessStopReason = "max_cycles_reached"
    stop_detail = "max_cycles reached"
    loop_failure_count = 0

    for cycle_index in range(1, request.max_cycles + 1):
        inspected = inspect_scheduler_daemon_lifecycle_control(
            control_path,
            now_epoch_seconds=request.stale_now_epoch_seconds,
            stale_after_seconds=request.stale_after_seconds,
        )
        state_before = inspected.control.state
        if state_before not in {"running", "cancelling"}:
            stop_reason = _stop_reason_for_lifecycle_state(state_before)
            stop_detail = f"lifecycle state {state_before!r} does not run scheduler loop"
            cycles.append(
                SchedulerDaemonHarnessCycle(
                    cycle_index=cycle_index,
                    state_before=state_before,
                    state_after=state_before,
                    skipped=True,
                    skip_reason=stop_detail,
                    stop_reason=stop_reason,
                )
            )
            break

        run_once = run_scheduler_daemon_lifecycle_once(
            SchedulerDaemonLifecycleRunOnceRequest(
                control_path=control_path,
                stop_policy=request.stop_policy,
                runtime_provider=request.runtime_provider,
                timestamp=request.timestamp,
                workspace_root=request.workspace_root,
                scratch_root=request.scratch_root,
                created_at=request.created_at,
                expires_at=request.expires_at,
                strict_recovery=request.strict_recovery,
                continue_on_failure=request.continue_on_failure,
            ),
            runtime_registry=runtime_registry,
            sandbox_registry=sandbox_registry,
            artifact_store=artifact_store,
        )
        state_after = run_once.control_after.state
        cycle_stop = _cycle_stop_reason(run_once)
        cycles.append(
            SchedulerDaemonHarnessCycle(
                cycle_index=cycle_index,
                state_before=state_before,
                state_after=state_after,
                run_once=run_once,
                skipped=run_once.skipped,
                skip_reason=run_once.skip_reason,
                stop_reason=cycle_stop,
            )
        )

        if run_once.skipped:
            stop_reason = cycle_stop
            stop_detail = run_once.skip_reason
            break
        if run_once.loop is None:
            stop_reason = "lifecycle_skipped"
            stop_detail = "lifecycle run-once returned without loop payload"
            break
        if run_once.loop.stop_reason == "no_ready_tasks":
            stop_reason = "no_ready_tasks"
            stop_detail = "no ready tasks remain"
            break
        if run_once.loop.stop_reason == "runtime_failure_limit_reached":
            loop_failure_count += 1
            if (
                request.max_loop_failures is not None
                and loop_failure_count >= request.max_loop_failures
            ):
                stop_reason = "loop_failure_limit_reached"
                stop_detail = run_once.loop.stop_detail or "loop failure limit reached"
                break

    if not cycles:
        control = read_scheduler_daemon_lifecycle_control(control_path)
        stop_reason = _stop_reason_for_lifecycle_state(control.state)
        stop_detail = f"lifecycle state {control.state!r} did not run scheduler loop"

    return SchedulerDaemonHarnessResult(
        request=request,
        control_path=control_path,
        cycles=tuple(cycles),
        stop_reason=stop_reason,
        stop_detail=stop_detail,
    )


def run_scheduler_daemon_harness_with_policy(
    request: SchedulerDaemonHarnessRequest,
    policy: SchedulerDaemonHarnessPolicy | None = None,
    *,
    runtime_registry: AgentRuntimeAdapterRegistry | None = None,
    sandbox_registry: SandboxProviderRegistry | None = None,
    artifact_store: InMemoryArtifactVersionStore | None = None,
) -> SchedulerDaemonHarnessPolicyResult:
    """Apply deterministic policy around bounded harness attempts."""

    active_policy = policy or SchedulerDaemonHarnessPolicy()
    _validate_harness_policy(active_policy)
    if active_policy.cancelled:
        return SchedulerDaemonHarnessPolicyResult(
            request=request,
            policy=active_policy,
            stop_reason="cancelled",
            stop_detail="policy cancelled before harness execution",
        )
    if _deadline_exceeded(active_policy):
        return SchedulerDaemonHarnessPolicyResult(
            request=request,
            policy=active_policy,
            stop_reason="deadline_exceeded",
            stop_detail=(
                "policy deadline exceeded before harness execution: "
                f"now={active_policy.now_epoch_seconds}, "
                f"deadline={active_policy.deadline_epoch_seconds}"
            ),
        )

    attempts: list[SchedulerDaemonHarnessPolicyAttempt] = []
    for attempt_index in range(1, active_policy.max_attempts + 1):
        harness = run_scheduler_daemon_harness(
            request,
            runtime_registry=runtime_registry,
            sandbox_registry=sandbox_registry,
            artifact_store=artifact_store,
        )
        retryable = harness.stop_reason in active_policy.retry_stop_reasons
        attempts.append(
            SchedulerDaemonHarnessPolicyAttempt(
                attempt_index=attempt_index,
                harness=harness,
                retryable=retryable,
            )
        )
        if not retryable:
            return SchedulerDaemonHarnessPolicyResult(
                request=request,
                policy=active_policy,
                attempts=tuple(attempts),
                stop_reason="harness_completed",
                stop_detail=f"harness stopped with {harness.stop_reason!r}",
            )

    return SchedulerDaemonHarnessPolicyResult(
        request=request,
        policy=active_policy,
        attempts=tuple(attempts),
        stop_reason="max_attempts_reached",
        stop_detail=f"retryable harness stop reason persisted for {active_policy.max_attempts} attempts",
    )


def _validate_harness_request(request: SchedulerDaemonHarnessRequest) -> None:
    if request.max_cycles < 0:
        raise ValueError("scheduler daemon harness max_cycles must be non-negative")
    if request.max_loop_failures is not None and request.max_loop_failures < 0:
        raise ValueError("scheduler daemon harness max_loop_failures must be non-negative")


def _validate_harness_policy(policy: SchedulerDaemonHarnessPolicy) -> None:
    if policy.max_attempts < 0:
        raise ValueError("scheduler daemon harness policy max_attempts must be non-negative")
    if policy.deadline_epoch_seconds is not None and policy.now_epoch_seconds is None:
        raise ValueError("scheduler daemon harness policy deadline requires now_epoch_seconds")
    if policy.max_attempts == 0 and not policy.cancelled and not _deadline_exceeded(policy):
        raise ValueError("scheduler daemon harness policy max_attempts must be positive")


def _deadline_exceeded(policy: SchedulerDaemonHarnessPolicy) -> bool:
    return (
        policy.deadline_epoch_seconds is not None
        and policy.now_epoch_seconds is not None
        and policy.now_epoch_seconds >= policy.deadline_epoch_seconds
    )


def _stop_reason_for_lifecycle_state(state: str) -> SchedulerDaemonHarnessStopReason:
    if state == "paused":
        return "paused"
    if state == "cancelling":
        return "cancelling"
    if state == "cancelled":
        return "cancelled"
    if state == "stopped":
        return "stopped"
    if state == "stale":
        return "stale"
    return "lifecycle_skipped"


def _cycle_stop_reason(
    run_once: SchedulerDaemonLifecycleRunOnceResult,
) -> SchedulerDaemonHarnessStopReason | str:
    if run_once.skipped:
        return _stop_reason_for_lifecycle_state(run_once.control_after.state)
    if run_once.loop is None:
        return "lifecycle_skipped"
    return run_once.loop.stop_reason
