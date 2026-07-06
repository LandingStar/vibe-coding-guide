"""Local scheduler daemon lifecycle control contract.

This module is deliberately not a background service. It stores scheduler
daemon lifecycle intent in a local JSON control file and provides one bounded
run-once wrapper over the existing scheduler daemon loop.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Mapping

from .artifact_paths import DEFAULT_DBC_SCRATCH_ROOT
from .exchange_store import InMemoryArtifactVersionStore
from .runtime_adapter import AgentRuntimeAdapterRegistry
from .sandbox import SandboxProviderRegistry
from .scheduler_daemon import (
    SchedulerDaemonLoopRequest,
    SchedulerDaemonLoopResult,
    SchedulerDaemonLoopStopPolicy,
    run_scheduler_daemon_loop,
    summarize_scheduler_queue,
)
from .scheduler_store import recover_scheduler_state

SCHEDULER_DAEMON_LIFECYCLE_SCHEMA_VERSION = "1"

SchedulerDaemonLifecycleState = Literal[
    "idle",
    "running",
    "paused",
    "cancelling",
    "cancelled",
    "stopped",
    "stale",
]

SchedulerDaemonLifecycleAction = Literal[
    "start",
    "heartbeat",
    "pause",
    "resume",
    "cancel",
    "shutdown",
    "mark_stale",
    "inspect",
]


@dataclass(frozen=True, slots=True)
class SchedulerDaemonLifecycleControl:
    """Durable local lifecycle intent for a scheduler daemon owner."""

    daemon_id: str
    snapshot_path: str
    event_log_path: str
    state: SchedulerDaemonLifecycleState = "idle"
    run_id: str = ""
    heartbeat_at: str = ""
    requested_action: str = ""
    updated_at: str = ""
    stale_after_seconds: int | None = None
    last_result_summary: Mapping[str, object] = field(default_factory=dict)
    metadata: Mapping[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-compatible lifecycle control payload."""

        return {
            "schema_version": SCHEDULER_DAEMON_LIFECYCLE_SCHEMA_VERSION,
            "daemon_id": self.daemon_id,
            "snapshot_path": self.snapshot_path,
            "event_log_path": self.event_log_path,
            "state": self.state,
            "run_id": self.run_id,
            "heartbeat_at": self.heartbeat_at,
            "requested_action": self.requested_action,
            "updated_at": self.updated_at,
            "stale_after_seconds": self.stale_after_seconds,
            "last_result_summary": dict(self.last_result_summary),
            "metadata": dict(self.metadata),
            "authority_split": {
                "lifecycle_authority": "scheduler_daemon_lifecycle_control_file",
                "scheduler_state_authority": "scheduler_snapshot_and_event_log",
                "starts_background_process": False,
                "provider_executed_by_lifecycle_transition": False,
                "local_work_trajectory_mutated": False,
            },
        }


@dataclass(frozen=True, slots=True)
class SchedulerDaemonLifecycleRequest:
    """Request for one deterministic lifecycle transition."""

    control_path: str | Path
    action: SchedulerDaemonLifecycleAction
    daemon_id: str = ""
    snapshot_path: str | Path | None = None
    event_log_path: str | Path | None = None
    run_id: str = ""
    timestamp: str = ""
    stale_after_seconds: int | None = None
    now_epoch_seconds: int | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SchedulerDaemonLifecycleResult:
    """Result of one lifecycle transition."""

    control_path: Path
    control: SchedulerDaemonLifecycleControl
    previous_state: SchedulerDaemonLifecycleState | None
    action: SchedulerDaemonLifecycleAction
    changed: bool
    reason: str = ""

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-compatible lifecycle transition result."""

        return {
            "ok": True,
            "control_path": str(self.control_path),
            "action": self.action,
            "changed": self.changed,
            "previous_state": self.previous_state or "",
            "state": self.control.state,
            "reason": self.reason,
            "control": self.control.to_json_dict(),
            "authority_split": {
                "lifecycle_authority": "scheduler_daemon_lifecycle_control_file",
                "lifecycle_mutated": self.changed,
                "scheduler_state_mutated": False,
                "provider_executed": False,
                "local_work_trajectory_mutated": False,
            },
        }


@dataclass(frozen=True, slots=True)
class SchedulerDaemonLifecycleRunOnceRequest:
    """Request to run one bounded loop under lifecycle control."""

    control_path: str | Path
    stop_policy: SchedulerDaemonLoopStopPolicy = field(default_factory=SchedulerDaemonLoopStopPolicy)
    runtime_provider: str = "fake"
    timestamp: str = ""
    workspace_root: str = ""
    scratch_root: str = DEFAULT_DBC_SCRATCH_ROOT
    created_at: str = ""
    expires_at: str = ""
    strict_recovery: bool = True
    continue_on_failure: bool = True


@dataclass(frozen=True, slots=True)
class SchedulerDaemonLifecycleRunOnceResult:
    """Result of a lifecycle-gated bounded scheduler loop attempt."""

    control_path: Path
    control_before: SchedulerDaemonLifecycleControl
    control_after: SchedulerDaemonLifecycleControl
    loop: SchedulerDaemonLoopResult | None = None
    skipped: bool = False
    skip_reason: str = ""

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-compatible lifecycle-gated run-once result."""

        loop_payload = None if self.loop is None else self.loop.to_json_dict()
        return {
            "ok": True,
            "control_path": str(self.control_path),
            "skipped": self.skipped,
            "skip_reason": self.skip_reason,
            "state_before": self.control_before.state,
            "state_after": self.control_after.state,
            "loop": loop_payload,
            "control": self.control_after.to_json_dict(),
            "authority_split": {
                "lifecycle_authority": "scheduler_daemon_lifecycle_control_file",
                "scheduler_state_authority": "scheduler_snapshot_and_event_log",
                "lifecycle_mutated": self.control_before != self.control_after,
                "scheduler_state_mutated": (
                    False
                    if self.loop is None
                    else bool(self.loop.iterations)
                ),
                "provider_executed": (
                    False
                    if self.loop is None
                    else self.loop.total_run_count > 0
                ),
                "starts_background_process": False,
                "scheduler_projection_refreshed": False,
                "local_work_trajectory_mutated": False,
                "exchange_artifact_store_mutated": False,
                "admission_ledger_mutated": False,
            },
        }


def read_scheduler_daemon_lifecycle_control(path: str | Path) -> SchedulerDaemonLifecycleControl:
    """Read one scheduler daemon lifecycle control file."""

    source = Path(path)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if str(payload.get("schema_version", "")) != SCHEDULER_DAEMON_LIFECYCLE_SCHEMA_VERSION:
        raise ValueError(
            "unsupported scheduler daemon lifecycle control version: "
            f"{payload.get('schema_version')!r}"
        )
    return SchedulerDaemonLifecycleControl(
        daemon_id=str(payload.get("daemon_id", "")),
        snapshot_path=str(payload.get("snapshot_path", "")),
        event_log_path=str(payload.get("event_log_path", "")),
        state=str(payload.get("state", "idle")),  # type: ignore[arg-type]
        run_id=str(payload.get("run_id", "")),
        heartbeat_at=str(payload.get("heartbeat_at", "")),
        requested_action=str(payload.get("requested_action", "")),
        updated_at=str(payload.get("updated_at", "")),
        stale_after_seconds=(
            payload.get("stale_after_seconds")
            if isinstance(payload.get("stale_after_seconds"), int)
            else None
        ),
        last_result_summary=(
            payload.get("last_result_summary")
            if isinstance(payload.get("last_result_summary"), dict)
            else {}
        ),
        metadata=payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {},
    )


def write_scheduler_daemon_lifecycle_control(
    control: SchedulerDaemonLifecycleControl,
    path: str | Path,
) -> Path:
    """Write one scheduler daemon lifecycle control file."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(control.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return target


def apply_scheduler_daemon_lifecycle_action(
    request: SchedulerDaemonLifecycleRequest,
) -> SchedulerDaemonLifecycleResult:
    """Apply one deterministic lifecycle transition to the control file."""

    control_path = Path(request.control_path)
    existing = _read_existing_control(control_path)
    previous_state = None if existing is None else existing.state
    control = _transition_control(existing, request)
    write_scheduler_daemon_lifecycle_control(control, control_path)
    return SchedulerDaemonLifecycleResult(
        control_path=control_path,
        control=control,
        previous_state=previous_state,
        action=request.action,
        changed=existing != control,
        reason=_transition_reason(request.action, previous_state, control.state),
    )


def run_scheduler_daemon_lifecycle_once(
    request: SchedulerDaemonLifecycleRunOnceRequest,
    *,
    runtime_registry: AgentRuntimeAdapterRegistry | None = None,
    sandbox_registry: SandboxProviderRegistry | None = None,
    artifact_store: InMemoryArtifactVersionStore | None = None,
) -> SchedulerDaemonLifecycleRunOnceResult:
    """Run one bounded daemon loop if lifecycle control allows it."""

    control_path = Path(request.control_path)
    control_before = read_scheduler_daemon_lifecycle_control(control_path)
    if control_before.state == "cancelling" or control_before.requested_action == "cancel":
        control_after = replace(
            control_before,
            state="cancelled",
            requested_action="",
            updated_at=request.timestamp or control_before.updated_at,
            last_result_summary={
                "stop_reason": "cancelled",
                "stop_detail": "lifecycle cancellation request consumed before scheduler loop",
                "tick_count": 0,
                "total_run_count": 0,
                "scheduler_event_count": 0,
                "ran_tasks": False,
            },
        )
        write_scheduler_daemon_lifecycle_control(control_after, control_path)
        return SchedulerDaemonLifecycleRunOnceResult(
            control_path=control_path,
            control_before=control_before,
            control_after=control_after,
            skipped=True,
            skip_reason="lifecycle cancellation request consumed before scheduler loop",
        )
    if control_before.state != "running":
        return SchedulerDaemonLifecycleRunOnceResult(
            control_path=control_path,
            control_before=control_before,
            control_after=control_before,
            skipped=True,
            skip_reason=f"lifecycle state {control_before.state!r} does not run scheduler loop",
        )

    loop = run_scheduler_daemon_loop(
        SchedulerDaemonLoopRequest(
            snapshot_path=control_before.snapshot_path,
            event_log_path=control_before.event_log_path,
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
    control_after = replace(
        control_before,
        state="running",
        requested_action="",
        updated_at=request.timestamp or control_before.updated_at,
        heartbeat_at=request.timestamp or control_before.heartbeat_at,
        last_result_summary={
            "stop_reason": loop.stop_reason,
            "stop_detail": loop.stop_detail,
            "tick_count": loop.tick_count,
            "total_run_count": loop.total_run_count,
            "scheduler_event_count": loop.scheduler_event_count,
            "ran_tasks": loop.total_run_count > 0,
        },
    )
    write_scheduler_daemon_lifecycle_control(control_after, control_path)
    return SchedulerDaemonLifecycleRunOnceResult(
        control_path=control_path,
        control_before=control_before,
        control_after=control_after,
        loop=loop,
        skipped=False,
    )


def inspect_scheduler_daemon_lifecycle_control(
    path: str | Path,
    *,
    now_epoch_seconds: int | None = None,
    stale_after_seconds: int | None = None,
) -> SchedulerDaemonLifecycleResult:
    """Read lifecycle control and optionally mark stale deterministically."""

    control_path = Path(path)
    control = read_scheduler_daemon_lifecycle_control(control_path)
    threshold = stale_after_seconds if stale_after_seconds is not None else control.stale_after_seconds
    if (
        now_epoch_seconds is not None
        and threshold is not None
        and _is_control_stale(control, now_epoch_seconds, threshold)
        and control.state in {"running", "paused"}
    ):
        stale_control = replace(
            control,
            state="stale",
            requested_action="mark_stale",
            updated_at=str(now_epoch_seconds),
        )
        write_scheduler_daemon_lifecycle_control(stale_control, control_path)
        return SchedulerDaemonLifecycleResult(
            control_path=control_path,
            control=stale_control,
            previous_state=control.state,
            action="mark_stale",
            changed=True,
            reason=f"heartbeat age exceeded {threshold} seconds",
        )
    return SchedulerDaemonLifecycleResult(
        control_path=control_path,
        control=control,
        previous_state=control.state,
        action="inspect",
        changed=False,
        reason="read-only lifecycle inspection",
    )


def _read_existing_control(path: Path) -> SchedulerDaemonLifecycleControl | None:
    if not path.exists():
        return None
    return read_scheduler_daemon_lifecycle_control(path)


def _transition_control(
    existing: SchedulerDaemonLifecycleControl | None,
    request: SchedulerDaemonLifecycleRequest,
) -> SchedulerDaemonLifecycleControl:
    if request.action == "start":
        if request.snapshot_path is None or request.event_log_path is None:
            raise ValueError("scheduler daemon lifecycle start requires snapshot_path and event_log_path")
        daemon_id = request.daemon_id or (existing.daemon_id if existing is not None else "")
        if not daemon_id:
            raise ValueError("scheduler daemon lifecycle start requires daemon_id")
        return SchedulerDaemonLifecycleControl(
            daemon_id=daemon_id,
            snapshot_path=str(request.snapshot_path),
            event_log_path=str(request.event_log_path),
            state="running",
            run_id=request.run_id,
            heartbeat_at=request.timestamp,
            requested_action="",
            updated_at=request.timestamp,
            stale_after_seconds=request.stale_after_seconds,
            metadata=dict(request.metadata),
        )
    if existing is None:
        raise ValueError(f"scheduler daemon lifecycle action {request.action!r} requires an existing control file")
    if request.action == "heartbeat":
        return replace(
            existing,
            heartbeat_at=request.timestamp,
            updated_at=request.timestamp,
            requested_action="",
            state="running" if existing.state in {"idle", "running"} else existing.state,
        )
    if request.action == "pause":
        return replace(existing, state="paused", requested_action="pause", updated_at=request.timestamp)
    if request.action == "resume":
        return replace(existing, state="running", requested_action="", updated_at=request.timestamp)
    if request.action == "cancel":
        return replace(existing, state="cancelling", requested_action="cancel", updated_at=request.timestamp)
    if request.action == "shutdown":
        return replace(existing, state="stopped", requested_action="shutdown", updated_at=request.timestamp)
    if request.action == "mark_stale":
        return replace(existing, state="stale", requested_action="mark_stale", updated_at=request.timestamp)
    if request.action == "inspect":
        return existing
    raise ValueError(f"unsupported scheduler daemon lifecycle action: {request.action!r}")


def _transition_reason(
    action: SchedulerDaemonLifecycleAction,
    previous_state: SchedulerDaemonLifecycleState | None,
    state: SchedulerDaemonLifecycleState,
) -> str:
    if previous_state is None:
        return f"created lifecycle control in state {state}"
    if previous_state == state:
        return f"lifecycle action {action} kept state {state}"
    return f"lifecycle action {action} moved state {previous_state} -> {state}"


def _is_control_stale(
    control: SchedulerDaemonLifecycleControl,
    now_epoch_seconds: int,
    stale_after_seconds: int,
) -> bool:
    if stale_after_seconds < 0:
        raise ValueError("stale_after_seconds must be non-negative")
    heartbeat = _parse_epoch_seconds(control.heartbeat_at)
    if heartbeat is None:
        return True
    return now_epoch_seconds - heartbeat > stale_after_seconds


def _parse_epoch_seconds(value: str) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp())


def lifecycle_queue_snapshot(control: SchedulerDaemonLifecycleControl) -> dict[str, object]:
    """Return a read-only queue summary for lifecycle diagnostics."""

    recovery = recover_scheduler_state(control.snapshot_path, control.event_log_path)
    return summarize_scheduler_queue(recovery.recovered_state).to_json_dict()
