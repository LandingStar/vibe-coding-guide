"""Host-managed scheduler daemon supervisor contract.

This module defines a deterministic supervisor layer over the policy-controlled
scheduler daemon harness. It is not a background service and deliberately does
not own timers, sleeps, watchers, or OS service registration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Mapping

from .exchange_store import InMemoryArtifactVersionStore
from .runtime_adapter import AgentRuntimeAdapterRegistry
from .sandbox import SandboxProviderRegistry
from .scheduler_daemon_harness import (
    SchedulerDaemonHarnessPolicy,
    SchedulerDaemonHarnessPolicyResult,
    SchedulerDaemonHarnessRequest,
    run_scheduler_daemon_harness_with_policy,
)
from .scheduler_daemon_lifecycle import (
    SchedulerDaemonLifecycleControl,
    lifecycle_queue_snapshot,
    read_scheduler_daemon_lifecycle_control,
)

SchedulerDaemonSupervisorStopReason = Literal[
    "cancelled",
    "deadline_exceeded",
    "harness_completed",
    "max_attempts_reached",
]


@dataclass(frozen=True, slots=True)
class SchedulerDaemonSupervisorRequest:
    """Request for one host-owned supervisor step over a bounded harness."""

    supervisor_id: str
    harness_request: SchedulerDaemonHarnessRequest
    policy: SchedulerDaemonHarnessPolicy = field(default_factory=SchedulerDaemonHarnessPolicy)
    session_id: str = ""
    run_id: str = ""
    host_id: str = ""
    requested_by: str = ""
    status_readback_at: str = ""
    cancellation_source: str = ""
    cancellation_reason: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SchedulerDaemonSupervisorStatus:
    """Readback facts visible to a host-owned daemon supervisor."""

    control_path: Path
    readback_at: str = ""
    control_exists: bool = False
    lifecycle_state: str = ""
    daemon_id: str = ""
    lifecycle_run_id: str = ""
    requested_action: str = ""
    heartbeat_at: str = ""
    updated_at: str = ""
    last_result_summary: Mapping[str, object] = field(default_factory=dict)
    queue_summary: Mapping[str, object] = field(default_factory=dict)
    readback_error: str = ""

    @classmethod
    def from_control(
        cls,
        control_path: str | Path,
        *,
        readback_at: str = "",
    ) -> "SchedulerDaemonSupervisorStatus":
        """Build supervisor status from lifecycle control when available."""

        path = Path(control_path)
        if not path.exists():
            return cls(
                control_path=path,
                readback_at=readback_at,
                control_exists=False,
                readback_error="lifecycle control file does not exist",
            )
        try:
            control = read_scheduler_daemon_lifecycle_control(path)
        except Exception as exc:  # pragma: no cover - message path covered by behavior tests
            return cls(
                control_path=path,
                readback_at=readback_at,
                control_exists=True,
                readback_error=f"failed to read lifecycle control: {exc}",
            )
        queue: Mapping[str, object]
        try:
            queue = lifecycle_queue_snapshot(control)
        except Exception as exc:
            queue = {}
            readback_error = f"failed to read scheduler queue: {exc}"
        else:
            readback_error = ""
        return cls.from_lifecycle_control(
            control,
            control_path=path,
            readback_at=readback_at,
            queue_summary=queue,
            readback_error=readback_error,
        )

    @classmethod
    def from_lifecycle_control(
        cls,
        control: SchedulerDaemonLifecycleControl,
        *,
        control_path: str | Path,
        readback_at: str = "",
        queue_summary: Mapping[str, object] | None = None,
        readback_error: str = "",
    ) -> "SchedulerDaemonSupervisorStatus":
        """Build supervisor status from an already-read lifecycle control."""

        return cls(
            control_path=Path(control_path),
            readback_at=readback_at,
            control_exists=True,
            lifecycle_state=control.state,
            daemon_id=control.daemon_id,
            lifecycle_run_id=control.run_id,
            requested_action=control.requested_action,
            heartbeat_at=control.heartbeat_at,
            updated_at=control.updated_at,
            last_result_summary=dict(control.last_result_summary),
            queue_summary=dict(queue_summary or {}),
            readback_error=readback_error,
        )

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-compatible status payload."""

        return {
            "control_path": str(self.control_path),
            "readback_at": self.readback_at,
            "control_exists": self.control_exists,
            "lifecycle_state": self.lifecycle_state,
            "daemon_id": self.daemon_id,
            "lifecycle_run_id": self.lifecycle_run_id,
            "requested_action": self.requested_action,
            "heartbeat_at": self.heartbeat_at,
            "updated_at": self.updated_at,
            "last_result_summary": dict(self.last_result_summary),
            "queue_summary": dict(self.queue_summary),
            "readback_error": self.readback_error,
        }


@dataclass(frozen=True, slots=True)
class SchedulerDaemonSupervisorResult:
    """Result of one deterministic host-managed supervisor step."""

    request: SchedulerDaemonSupervisorRequest
    status_before: SchedulerDaemonSupervisorStatus
    status_after: SchedulerDaemonSupervisorStatus
    harness_policy_result: SchedulerDaemonHarnessPolicyResult | None = None
    stop_reason: SchedulerDaemonSupervisorStopReason = "harness_completed"
    stop_detail: str = ""
    local_work_trajectory_mutated: bool = False
    scheduler_projection_refreshed: bool = False

    @property
    def attempted_harness(self) -> bool:
        """Return whether the supervisor invoked the bounded harness."""

        return self.harness_policy_result is not None

    @property
    def attempt_count(self) -> int:
        """Return harness policy attempt count."""

        if self.harness_policy_result is None:
            return 0
        return self.harness_policy_result.attempt_count

    @property
    def total_run_count(self) -> int:
        """Return task-run count across harness attempts."""

        if self.harness_policy_result is None:
            return 0
        return self.harness_policy_result.total_run_count

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-compatible supervisor result payload."""

        harness_payload = (
            None
            if self.harness_policy_result is None
            else self.harness_policy_result.to_json_dict()
        )
        return {
            "ok": True,
            "supervisor_id": self.request.supervisor_id,
            "session_id": self.request.session_id,
            "run_id": self.request.run_id,
            "host_id": self.request.host_id,
            "requested_by": self.request.requested_by,
            "control_path": str(Path(self.request.harness_request.control_path)),
            "attempted_harness": self.attempted_harness,
            "attempt_count": self.attempt_count,
            "total_run_count": self.total_run_count,
            "stop_reason": self.stop_reason,
            "stop_detail": self.stop_detail,
            "cancellation_source": self.request.cancellation_source,
            "cancellation_reason": self.request.cancellation_reason,
            "status_before": self.status_before.to_json_dict(),
            "status_after": self.status_after.to_json_dict(),
            "harness_policy_result": harness_payload,
            "metadata": dict(self.request.metadata),
            "authority_split": {
                "supervisor_authority": "host-owned-daemon-supervisor-contract",
                "policy_authority": "host-owned-harness-policy",
                "harness_authority": "host-owned-bounded-process-harness",
                "lifecycle_authority": "scheduler_daemon_lifecycle_control_file",
                "scheduler_state_authority": "scheduler_snapshot_and_event_log",
                "starts_os_service": False,
                "starts_background_process": False,
                "uses_timers_or_watchers": False,
                "scheduler_projection_refreshed": self.scheduler_projection_refreshed,
                "local_work_trajectory_mutated": self.local_work_trajectory_mutated,
                "exchange_artifact_store_mutated": False,
                "admission_ledger_mutated": False,
            },
        }


def run_scheduler_daemon_supervisor_step(
    request: SchedulerDaemonSupervisorRequest,
    *,
    runtime_registry: AgentRuntimeAdapterRegistry | None = None,
    sandbox_registry: SandboxProviderRegistry | None = None,
    artifact_store: InMemoryArtifactVersionStore | None = None,
) -> SchedulerDaemonSupervisorResult:
    """Run one deterministic host-managed supervisor step."""

    _validate_supervisor_request(request)
    control_path = Path(request.harness_request.control_path)
    if request.policy.cancelled:
        status = SchedulerDaemonSupervisorStatus(
            control_path=control_path,
            readback_at=request.status_readback_at,
            readback_error="status readback skipped because supervisor policy is cancelled",
        )
        return SchedulerDaemonSupervisorResult(
            request=request,
            status_before=status,
            status_after=status,
            stop_reason="cancelled",
            stop_detail=_cancelled_detail(request),
        )
    if _deadline_exceeded(request.policy):
        status = SchedulerDaemonSupervisorStatus(
            control_path=control_path,
            readback_at=request.status_readback_at,
            readback_error="status readback skipped because supervisor policy deadline is exceeded",
        )
        return SchedulerDaemonSupervisorResult(
            request=request,
            status_before=status,
            status_after=status,
            stop_reason="deadline_exceeded",
            stop_detail=(
                "supervisor policy deadline exceeded before harness execution: "
                f"now={request.policy.now_epoch_seconds}, "
                f"deadline={request.policy.deadline_epoch_seconds}"
            ),
        )

    status_before = SchedulerDaemonSupervisorStatus.from_control(
        control_path,
        readback_at=request.status_readback_at,
    )
    policy_result = run_scheduler_daemon_harness_with_policy(
        request.harness_request,
        request.policy,
        runtime_registry=runtime_registry,
        sandbox_registry=sandbox_registry,
        artifact_store=artifact_store,
    )
    status_after = SchedulerDaemonSupervisorStatus.from_control(
        control_path,
        readback_at=request.status_readback_at,
    )
    return SchedulerDaemonSupervisorResult(
        request=request,
        status_before=status_before,
        status_after=status_after,
        harness_policy_result=policy_result,
        stop_reason=policy_result.stop_reason,
        stop_detail=policy_result.stop_detail,
    )


def _validate_supervisor_request(request: SchedulerDaemonSupervisorRequest) -> None:
    if not request.supervisor_id:
        raise ValueError("scheduler daemon supervisor requires supervisor_id")
    if not str(request.harness_request.control_path):
        raise ValueError("scheduler daemon supervisor requires lifecycle control_path")
    _validate_supervisor_policy(request.policy)


def _validate_supervisor_policy(policy: SchedulerDaemonHarnessPolicy) -> None:
    if policy.max_attempts < 0:
        raise ValueError("scheduler daemon supervisor policy max_attempts must be non-negative")
    if policy.deadline_epoch_seconds is not None and policy.now_epoch_seconds is None:
        raise ValueError("scheduler daemon supervisor policy deadline requires now_epoch_seconds")
    if policy.max_attempts == 0 and not policy.cancelled and not _deadline_exceeded(policy):
        raise ValueError("scheduler daemon supervisor policy max_attempts must be positive")


def _deadline_exceeded(policy: SchedulerDaemonHarnessPolicy) -> bool:
    return (
        policy.deadline_epoch_seconds is not None
        and policy.now_epoch_seconds is not None
        and policy.now_epoch_seconds >= policy.deadline_epoch_seconds
    )


def _cancelled_detail(request: SchedulerDaemonSupervisorRequest) -> str:
    source = request.cancellation_source or "policy"
    reason = request.cancellation_reason or "supervisor policy cancelled before harness execution"
    return f"cancelled by {source}: {reason}"
