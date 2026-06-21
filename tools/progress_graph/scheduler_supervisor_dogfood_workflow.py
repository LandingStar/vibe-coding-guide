"""Shared supervisor dogfood workflow surface.

This module composes scheduler fixture seeding, exact admission, lifecycle
control start, supervisor-step execution, and readback. It stays outside core
scheduler runtime because it is a host/operator workflow contract, not a daemon
or scheduler primitive.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Mapping

from src.runtime.orchestration import (
    DEFAULT_SCHEDULER_OPERATOR_DOGFOOD_ARTIFACT_ID,
    DEFAULT_SCHEDULER_OPERATOR_DOGFOOD_VERSION,
    DEFAULT_SCHEDULER_OPERATOR_MULTILANE_DOGFOOD_ARTIFACT_ID,
    DEFAULT_SCHEDULER_OPERATOR_MULTILANE_DOGFOOD_VERSION,
    SchedulerDaemonHarnessPolicy,
    SchedulerDaemonHarnessRequest,
    SchedulerDaemonLifecycleRequest,
    SchedulerDaemonLoopStopPolicy,
    SchedulerDaemonSupervisorRequest,
    admit_exchange_artifact_version_with_ledger,
    apply_scheduler_daemon_lifecycle_action,
    default_exchange_artifact_admission_ledger_path,
    default_exchange_artifact_store_path,
    inspect_scheduler_daemon_lifecycle_control,
    read_scheduler_state_snapshot,
    run_scheduler_daemon_supervisor_step,
    seed_scheduler_operator_dogfood_fixture,
    seed_scheduler_operator_multilane_dogfood_fixture,
    summarize_scheduler_queue,
)

from .scheduler_operator_workflow import (
    DEFAULT_SCHEDULER_OPERATOR_EVENT_LOG_RELATIVE_PATH,
    DEFAULT_SCHEDULER_OPERATOR_SNAPSHOT_RELATIVE_PATH,
)


SupervisorDogfoodWorkflowFixture = Literal["simple", "multilane"]
SupervisorDogfoodWorkflowStepStatus = Literal["completed", "skipped", "failed"]

DEFAULT_SUPERVISOR_DOGFOOD_CONTROL_RELATIVE_PATH = Path(
    ".codex/scheduler/scheduler-daemon-control.json"
)
DEFAULT_SUPERVISOR_DOGFOOD_SUPERVISOR_ID = "supervisor:dogfood"
DEFAULT_SUPERVISOR_DOGFOOD_DAEMON_ID = "daemon:supervisor-dogfood"
DEFAULT_SUPERVISOR_DOGFOOD_LIFECYCLE_RUN_ID = "lifecycle-run:supervisor-dogfood"
DEFAULT_SUPERVISOR_DOGFOOD_SUPERVISOR_RUN_ID = "supervisor-run:dogfood"


@dataclass(frozen=True, slots=True)
class SchedulerSupervisorDogfoodWorkflowRequest:
    """Request for deterministic fake-runtime supervisor dogfood."""

    project_root: str | Path
    fixture: SupervisorDogfoodWorkflowFixture = "simple"
    artifact_id: str = ""
    version: str = ""
    artifact_store_path: str | Path | None = None
    admission_ledger_path: str | Path | None = None
    snapshot_path: str | Path | None = None
    event_log_path: str | Path | None = None
    control_path: str | Path | None = None
    runtime_provider: str = "fake"
    max_cycles: int = 1
    max_loop_failures: int | None = 1
    max_ticks: int = 3
    max_runs_per_tick: int | None = 1
    max_runtime_failures: int | None = 1
    max_attempts: int = 1
    retry_stop_reasons: tuple[str, ...] = ()
    allow_duplicate_admission: bool = False
    replace_existing: bool = False
    actor: str = "supervisor-dogfood-workflow"
    timestamp: str = ""
    created_at: str = ""
    daemon_id: str = DEFAULT_SUPERVISOR_DOGFOOD_DAEMON_ID
    lifecycle_run_id: str = DEFAULT_SUPERVISOR_DOGFOOD_LIFECYCLE_RUN_ID
    supervisor_id: str = DEFAULT_SUPERVISOR_DOGFOOD_SUPERVISOR_ID
    session_id: str = ""
    run_id: str = DEFAULT_SUPERVISOR_DOGFOOD_SUPERVISOR_RUN_ID
    host_id: str = ""
    requested_by: str = ""
    status_readback_at: str = ""


@dataclass(frozen=True, slots=True)
class SchedulerSupervisorDogfoodWorkflowStep:
    """One ordered supervisor dogfood workflow step."""

    name: str
    status: SupervisorDogfoodWorkflowStepStatus
    mutated: bool = False
    error: str = ""
    result: Mapping[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "status": self.status,
            "mutated": self.mutated,
            "error": self.error,
            "result": dict(self.result),
        }


@dataclass(frozen=True, slots=True)
class SchedulerSupervisorDogfoodWorkflowResult:
    """Result of the deterministic supervisor dogfood workflow."""

    request: SchedulerSupervisorDogfoodWorkflowRequest
    project_root: Path
    artifact_store_path: Path
    admission_ledger_path: Path
    snapshot_path: Path
    event_log_path: Path
    control_path: Path
    artifact_id: str
    version: str
    steps: tuple[SchedulerSupervisorDogfoodWorkflowStep, ...]
    fixture_result: Mapping[str, object] = field(default_factory=dict)
    admission_result: Mapping[str, object] = field(default_factory=dict)
    lifecycle_start_result: Mapping[str, object] = field(default_factory=dict)
    supervisor_result: Mapping[str, object] = field(default_factory=dict)
    final_readback: Mapping[str, object] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not any(step.status == "failed" for step in self.steps)

    @property
    def authority_split(self) -> dict[str, object]:
        admission_authority = _mapping(self.admission_result.get("authority_split"))
        lifecycle_authority = _mapping(self.lifecycle_start_result.get("authority_split"))
        supervisor_authority = _mapping(self.supervisor_result.get("authority_split"))
        return {
            "workflow_surface": "scheduler-supervisor-dogfood-workflow",
            "fixture_seeded": _step_mutated(self.steps, "seedFixture"),
            "exchange_store_mutated": _step_mutated(self.steps, "seedFixture"),
            "admission_ledger_mutated": _step_mutated(self.steps, "admit"),
            "lifecycle_control_mutated": _step_mutated(self.steps, "startLifecycle")
            or bool(lifecycle_authority.get("lifecycle_mutated")),
            "scheduler_state_mutated": bool(admission_authority.get("scheduler_state_mutated"))
            or bool(supervisor_authority.get("scheduler_state_mutated")),
            "provider_executed": int(self.supervisor_result.get("total_run_count", 0) or 0) > 0,
            "supervisor_step_executed": _step_completed(self.steps, "supervisorStep"),
            "final_readback_performed": _step_completed(self.steps, "readFinalStatus"),
            "starts_os_service": False,
            "starts_background_process": False,
            "uses_timers_or_watchers": False,
            "scheduler_projection_refreshed": False,
            "cleanup_executed": False,
            "local_work_trajectory_mutated": False,
        }

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "workflow_surface": "scheduler-supervisor-dogfood-workflow",
            "project_root": str(self.project_root),
            "paths": {
                "artifact_store_path": str(self.artifact_store_path),
                "admission_ledger_path": str(self.admission_ledger_path),
                "snapshot_path": str(self.snapshot_path),
                "event_log_path": str(self.event_log_path),
                "control_path": str(self.control_path),
            },
            "request": {
                "fixture": self.request.fixture,
                "artifact_id": self.artifact_id,
                "version": self.version,
                "runtime_provider": self.request.runtime_provider,
                "max_cycles": self.request.max_cycles,
                "max_loop_failures": self.request.max_loop_failures,
                "max_ticks": self.request.max_ticks,
                "max_runs_per_tick": self.request.max_runs_per_tick,
                "max_runtime_failures": self.request.max_runtime_failures,
                "max_attempts": self.request.max_attempts,
                "retry_stop_reasons": list(self.request.retry_stop_reasons),
                "allow_duplicate_admission": self.request.allow_duplicate_admission,
                "replace_existing": self.request.replace_existing,
                "actor": self.request.actor,
                "daemon_id": self.request.daemon_id,
                "lifecycle_run_id": self.request.lifecycle_run_id,
                "supervisor_id": self.request.supervisor_id,
                "session_id": self.request.session_id,
                "run_id": self.request.run_id,
                "host_id": self.request.host_id,
                "requested_by": self.request.requested_by,
            },
            "steps": [step.to_json_dict() for step in self.steps],
            "fixture_result": dict(self.fixture_result),
            "admission_result": dict(self.admission_result),
            "lifecycle_start_result": dict(self.lifecycle_start_result),
            "supervisor_result": dict(self.supervisor_result),
            "final_readback": dict(self.final_readback),
            "authority_split": self.authority_split,
        }


def run_scheduler_supervisor_dogfood_workflow(
    request: SchedulerSupervisorDogfoodWorkflowRequest,
) -> SchedulerSupervisorDogfoodWorkflowResult:
    """Run seed -> admit -> lifecycle start -> supervisor step -> readback."""

    paths = _ResolvedSchedulerSupervisorDogfoodWorkflowPaths.from_request(request)
    artifact_id = request.artifact_id or _default_artifact_id(request.fixture)
    version = request.version or _default_version(request.fixture)
    steps: list[SchedulerSupervisorDogfoodWorkflowStep] = []
    fixture_result: Mapping[str, object] = {}
    admission_result: Mapping[str, object] = {}
    lifecycle_start_result: Mapping[str, object] = {}
    supervisor_result: Mapping[str, object] = {}
    final_readback: Mapping[str, object] = {}

    runtime_provider = (request.runtime_provider or "fake").strip().lower()
    if runtime_provider != "fake":
        steps.append(
            SchedulerSupervisorDogfoodWorkflowStep(
                name="preflightRuntime",
                status="failed",
                error=(
                    "scheduler supervisor dogfood workflow currently supports "
                    "runtimeProvider='fake' only; real providers require host-owned "
                    "adapter wiring."
                ),
            )
        )
        return SchedulerSupervisorDogfoodWorkflowResult(
            request=request,
            project_root=paths.project_root,
            artifact_store_path=paths.artifact_store_path,
            admission_ledger_path=paths.admission_ledger_path,
            snapshot_path=paths.snapshot_path,
            event_log_path=paths.event_log_path,
            control_path=paths.control_path,
            artifact_id=artifact_id,
            version=version,
            steps=tuple(steps),
        )

    fixture_failed = False
    try:
        fixture = _seed_fixture(request, paths, artifact_id, version)
        fixture_result = fixture.to_json_dict()
        steps.append(
            SchedulerSupervisorDogfoodWorkflowStep(
                name="seedFixture",
                status="completed",
                mutated=True,
                result=fixture_result,
            )
        )
    except Exception as exc:
        fixture_failed = True
        steps.append(
            SchedulerSupervisorDogfoodWorkflowStep(
                name="seedFixture",
                status="failed",
                error=str(exc),
            )
        )

    admission_failed = False
    if fixture_failed:
        admission_failed = True
        steps.append(_skipped("admit", "fixture seeding failed"))
    else:
        admission_result = admit_exchange_artifact_version_with_ledger(
            artifact_store_path=paths.artifact_store_path,
            artifact_id=artifact_id,
            version=version,
            snapshot_path=paths.snapshot_path,
            event_log_path=paths.event_log_path,
            admission_ledger_path=paths.admission_ledger_path,
            allow_duplicate_admission=request.allow_duplicate_admission,
            replace_existing=request.replace_existing,
            actor=request.actor or "supervisor-dogfood-workflow",
            surface="supervisor-dogfood-workflow:scheduler",
            timestamp=request.timestamp,
        )
        admission_ok = bool(admission_result.get("ok"))
        admission_failed = not admission_ok
        steps.append(
            SchedulerSupervisorDogfoodWorkflowStep(
                name="admit",
                status="completed" if admission_ok else "failed",
                mutated=_admission_result_mutated(admission_result),
                error="" if admission_ok else str(admission_result.get("error", "admission failed")),
                result=admission_result,
            )
        )

    lifecycle_failed = False
    if admission_failed:
        lifecycle_failed = True
        steps.append(_skipped("startLifecycle", "admission failed"))
    else:
        try:
            lifecycle = apply_scheduler_daemon_lifecycle_action(
                SchedulerDaemonLifecycleRequest(
                    control_path=paths.control_path,
                    action="start",
                    daemon_id=request.daemon_id or DEFAULT_SUPERVISOR_DOGFOOD_DAEMON_ID,
                    snapshot_path=paths.snapshot_path,
                    event_log_path=paths.event_log_path,
                    run_id=(
                        request.lifecycle_run_id
                        or DEFAULT_SUPERVISOR_DOGFOOD_LIFECYCLE_RUN_ID
                    ),
                    timestamp=request.timestamp,
                )
            )
            lifecycle_start_result = lifecycle.to_json_dict()
            steps.append(
                SchedulerSupervisorDogfoodWorkflowStep(
                    name="startLifecycle",
                    status="completed",
                    mutated=True,
                    result=lifecycle_start_result,
                )
            )
        except Exception as exc:
            lifecycle_failed = True
            steps.append(
                SchedulerSupervisorDogfoodWorkflowStep(
                    name="startLifecycle",
                    status="failed",
                    error=str(exc),
                )
            )

    supervisor_failed = False
    if lifecycle_failed:
        supervisor_failed = True
        steps.append(_skipped("supervisorStep", "lifecycle start failed"))
    else:
        try:
            supervisor = run_scheduler_daemon_supervisor_step(
                SchedulerDaemonSupervisorRequest(
                    supervisor_id=(
                        request.supervisor_id
                        or DEFAULT_SUPERVISOR_DOGFOOD_SUPERVISOR_ID
                    ),
                    session_id=request.session_id,
                    run_id=request.run_id or DEFAULT_SUPERVISOR_DOGFOOD_SUPERVISOR_RUN_ID,
                    host_id=request.host_id,
                    requested_by=request.requested_by,
                    status_readback_at=request.status_readback_at or request.timestamp,
                    harness_request=SchedulerDaemonHarnessRequest(
                        control_path=paths.control_path,
                        max_cycles=request.max_cycles,
                        stop_policy=SchedulerDaemonLoopStopPolicy(
                            max_ticks=request.max_ticks,
                            max_runs_per_tick=request.max_runs_per_tick,
                            max_runtime_failures=request.max_runtime_failures,
                        ),
                        runtime_provider="fake",
                        timestamp=request.timestamp,
                        workspace_root=str(paths.project_root),
                        max_loop_failures=request.max_loop_failures,
                    ),
                    policy=SchedulerDaemonHarnessPolicy(
                        max_attempts=request.max_attempts,
                        retry_stop_reasons=request.retry_stop_reasons,
                    ),
                    metadata={
                        "workflow_surface": "scheduler-supervisor-dogfood-workflow",
                        "fixture": request.fixture,
                        "artifact_id": artifact_id,
                        "version": version,
                    },
                )
            )
            supervisor_result = supervisor.to_json_dict()
            steps.append(
                SchedulerSupervisorDogfoodWorkflowStep(
                    name="supervisorStep",
                    status="completed",
                    mutated=supervisor.total_run_count > 0,
                    result=supervisor_result,
                )
            )
        except Exception as exc:
            supervisor_failed = True
            steps.append(
                SchedulerSupervisorDogfoodWorkflowStep(
                    name="supervisorStep",
                    status="failed",
                    error=str(exc),
                )
            )

    if supervisor_failed:
        steps.append(_skipped("readFinalStatus", "supervisor step failed"))
    else:
        try:
            lifecycle = inspect_scheduler_daemon_lifecycle_control(paths.control_path)
            scheduler_state = read_scheduler_state_snapshot(paths.snapshot_path)
            queue_summary = summarize_scheduler_queue(scheduler_state).to_json_dict()
            final_readback = {
                "ok": True,
                "lifecycle": lifecycle.to_json_dict(),
                "queue_summary": queue_summary,
                "completed_task_ids": queue_summary.get("completed_task_ids", []),
                "authority_split": {
                    "lifecycle_authority": "scheduler_daemon_lifecycle_control_file",
                    "scheduler_state_authority": "scheduler_snapshot",
                    "lifecycle_mutated": False,
                    "scheduler_state_mutated": False,
                    "provider_executed": False,
                    "scheduler_projection_refreshed": False,
                    "local_work_trajectory_mutated": False,
                },
            }
            steps.append(
                SchedulerSupervisorDogfoodWorkflowStep(
                    name="readFinalStatus",
                    status="completed",
                    result=final_readback,
                )
            )
        except Exception as exc:
            steps.append(
                SchedulerSupervisorDogfoodWorkflowStep(
                    name="readFinalStatus",
                    status="failed",
                    error=str(exc),
                )
            )

    return SchedulerSupervisorDogfoodWorkflowResult(
        request=request,
        project_root=paths.project_root,
        artifact_store_path=paths.artifact_store_path,
        admission_ledger_path=paths.admission_ledger_path,
        snapshot_path=paths.snapshot_path,
        event_log_path=paths.event_log_path,
        control_path=paths.control_path,
        artifact_id=artifact_id,
        version=version,
        steps=tuple(steps),
        fixture_result=fixture_result,
        admission_result=admission_result,
        lifecycle_start_result=lifecycle_start_result,
        supervisor_result=supervisor_result,
        final_readback=final_readback,
    )


@dataclass(frozen=True, slots=True)
class _ResolvedSchedulerSupervisorDogfoodWorkflowPaths:
    project_root: Path
    artifact_store_path: Path
    admission_ledger_path: Path
    snapshot_path: Path
    event_log_path: Path
    control_path: Path

    @classmethod
    def from_request(
        cls,
        request: SchedulerSupervisorDogfoodWorkflowRequest,
    ) -> "_ResolvedSchedulerSupervisorDogfoodWorkflowPaths":
        project_root = Path(request.project_root).resolve()
        artifact_store = (
            _resolve(project_root, request.artifact_store_path)
            if request.artifact_store_path is not None
            else default_exchange_artifact_store_path(project_root)
        )
        admission_ledger = (
            _resolve(project_root, request.admission_ledger_path)
            if request.admission_ledger_path is not None
            else default_exchange_artifact_admission_ledger_path(project_root)
        )
        snapshot = _resolve(
            project_root,
            request.snapshot_path or DEFAULT_SCHEDULER_OPERATOR_SNAPSHOT_RELATIVE_PATH,
        )
        event_log = _resolve(
            project_root,
            request.event_log_path or DEFAULT_SCHEDULER_OPERATOR_EVENT_LOG_RELATIVE_PATH,
        )
        control = _resolve(
            project_root,
            request.control_path or DEFAULT_SUPERVISOR_DOGFOOD_CONTROL_RELATIVE_PATH,
        )
        return cls(
            project_root=project_root,
            artifact_store_path=artifact_store,
            admission_ledger_path=admission_ledger,
            snapshot_path=snapshot,
            event_log_path=event_log,
            control_path=control,
        )


def _seed_fixture(
    request: SchedulerSupervisorDogfoodWorkflowRequest,
    paths: _ResolvedSchedulerSupervisorDogfoodWorkflowPaths,
    artifact_id: str,
    version: str,
):
    if request.fixture == "simple":
        return seed_scheduler_operator_dogfood_fixture(
            paths.project_root,
            artifact_store_path=paths.artifact_store_path,
            artifact_id=artifact_id,
            version=version,
            replace_existing=request.replace_existing,
            created_at=request.created_at or request.timestamp or "2026-06-21T00:00:00+00:00",
        )
    if request.fixture == "multilane":
        return seed_scheduler_operator_multilane_dogfood_fixture(
            paths.project_root,
            artifact_store_path=paths.artifact_store_path,
            artifact_id=artifact_id,
            version=version,
            replace_existing=request.replace_existing,
            created_at=request.created_at or request.timestamp or "2026-06-21T00:00:00+00:00",
        )
    raise ValueError("scheduler supervisor dogfood fixture must be simple or multilane")


def _default_artifact_id(fixture: str) -> str:
    if fixture == "multilane":
        return DEFAULT_SCHEDULER_OPERATOR_MULTILANE_DOGFOOD_ARTIFACT_ID
    return DEFAULT_SCHEDULER_OPERATOR_DOGFOOD_ARTIFACT_ID


def _default_version(fixture: str) -> str:
    if fixture == "multilane":
        return DEFAULT_SCHEDULER_OPERATOR_MULTILANE_DOGFOOD_VERSION
    return DEFAULT_SCHEDULER_OPERATOR_DOGFOOD_VERSION


def _resolve(project_root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return project_root / path


def _mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def _skipped(name: str, reason: str) -> SchedulerSupervisorDogfoodWorkflowStep:
    return SchedulerSupervisorDogfoodWorkflowStep(
        name=name,
        status="skipped",
        error=reason,
    )


def _admission_result_mutated(result: Mapping[str, object]) -> bool:
    if result.get("admission_ledger_record_id"):
        return True
    authority = _mapping(result.get("authority_split"))
    return bool(authority.get("scheduler_state_mutated"))


def _step_completed(
    steps: tuple[SchedulerSupervisorDogfoodWorkflowStep, ...],
    name: str,
) -> bool:
    return any(step.name == name and step.status == "completed" for step in steps)


def _step_mutated(
    steps: tuple[SchedulerSupervisorDogfoodWorkflowStep, ...],
    name: str,
) -> bool:
    return any(step.name == name and step.mutated for step in steps)
