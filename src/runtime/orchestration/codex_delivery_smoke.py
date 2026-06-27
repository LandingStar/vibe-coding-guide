"""Host/operator Codex delivery smoke and bounded loop bindings."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from .codex_cli_client import CodexCliHostReadinessReport, CodexCliProcessClient
from .exchange import ExchangeReference
from .exchange_store import DEFAULT_EXCHANGE_ARTIFACT_STORE_RELATIVE_PATH
from .leader_worker_codex_delivery import (
    CodexDeliverySupervisorRequest,
    CodexDeliverySupervisorResult,
    run_codex_delivery_supervisor_once,
)
from .leader_worker_delivery import (
    DEFAULT_LEADER_WORKER_DELIVERY_EVENT_LOG_RELATIVE_PATH,
    DEFAULT_LEADER_WORKER_DELIVERY_STATE_RELATIVE_PATH,
    LeaderWorkerDeliverySyncRequest,
    LeaderWorkerDeliverySyncResult,
    read_leader_worker_delivery_state,
    sync_leader_worker_delivery_from_dispatch_log,
)
from .leader_worker_dispatcher import (
    DEFAULT_LEADER_WORKER_DISPATCHER_EVENT_LOG_RELATIVE_PATH,
    DEFAULT_LEADER_WORKER_DISPATCHER_STATE_RELATIVE_PATH,
    LeaderWorkerDispatcherTickRequest,
    LeaderWorkerDispatcherTickResult,
    run_leader_worker_dispatcher_tick,
)
from .runtime_adapter import AgentSpec, CodexCliClient
from .runtime_invocation_audit import (
    DEFAULT_RUNTIME_INVOCATION_LOG_RELATIVE_PATH,
    JsonlRuntimeInvocationLog,
)
from .scheduler import ContextScope, ScheduledTask, SchedulerState
from .scheduler import TaskDependency, mark_ready_tasks
from .scheduler_store import (
    JsonlSchedulerEventLog,
    SchedulerRecoveryResult,
    recover_scheduler_state,
    write_scheduler_state_snapshot,
)

DEFAULT_CODEX_DELIVERY_E2E_SMOKE_SNAPSHOT_RELATIVE_PATH = (
    ".codex/scheduler/codex-delivery-e2e-smoke-state.json"
)
DEFAULT_CODEX_DELIVERY_E2E_SMOKE_EVENT_LOG_RELATIVE_PATH = (
    ".codex/scheduler/codex-delivery-e2e-smoke-events.jsonl"
)


@dataclass(frozen=True, slots=True)
class CodexDeliveryE2ESmokeRequest:
    """Request for the C1 Codex delivery E2E smoke."""

    scheduler_snapshot_path: str | Path = DEFAULT_CODEX_DELIVERY_E2E_SMOKE_SNAPSHOT_RELATIVE_PATH
    scheduler_event_log_path: str | Path = DEFAULT_CODEX_DELIVERY_E2E_SMOKE_EVENT_LOG_RELATIVE_PATH
    artifact_store_path: str | Path = DEFAULT_EXCHANGE_ARTIFACT_STORE_RELATIVE_PATH
    dispatcher_state_path: str | Path = DEFAULT_LEADER_WORKER_DISPATCHER_STATE_RELATIVE_PATH
    dispatch_event_log_path: str | Path = DEFAULT_LEADER_WORKER_DISPATCHER_EVENT_LOG_RELATIVE_PATH
    delivery_state_path: str | Path = DEFAULT_LEADER_WORKER_DELIVERY_STATE_RELATIVE_PATH
    delivery_event_log_path: str | Path = DEFAULT_LEADER_WORKER_DELIVERY_EVENT_LOG_RELATIVE_PATH
    runtime_invocation_log_path: str | Path | None = DEFAULT_RUNTIME_INVOCATION_LOG_RELATIVE_PATH
    initialize_fixture: bool = False
    replace_existing_fixture: bool = False
    fixture: str = "simple"
    require_host_ready: bool = True
    strict_recovery: bool = True
    target_task_id: str = "codex-smoke:worker"
    parallel_task_id: str = "codex-smoke:parallel-worker"
    waiting_task_id: str = "codex-smoke:waiting-non-codex"
    followup_task_id: str = "codex-smoke:followup"
    codex_agent_id: str = "agent:codex-smoke-worker"
    parallel_agent_id: str = "agent:codex-smoke-parallel-worker"
    followup_agent_id: str = "agent:codex-smoke-followup"
    waiting_agent_id: str = "agent:codex-smoke-waiting"
    codex_lane_id: str = "lane:codex-smoke"
    parallel_lane_id: str = "lane:codex-smoke-parallel"
    followup_lane_id: str = "lane:codex-smoke"
    waiting_lane_id: str = "lane:waiting"
    leader_agent_id: str = "agent:guide"
    dispatcher_id: str = "leader-worker-dispatcher"
    trajectory_id: str = "codex-delivery-e2e-smoke"
    host_id: str = "host:codex-delivery-e2e-smoke"
    host_invocation_id: str = "host-owned-codex-delivery-e2e-smoke"
    timestamp: str = ""
    runtime_invocation_max_attempts: int = 2
    runtime_invocation_backoff_seconds: float = 0.0
    allow_network: bool = True
    enable_sandbox_preflight: bool = False
    workspace_root: str | Path = ""
    scratch_root: str | Path = ".codex/scratch"
    git_worktree_sandbox_root: str | Path | None = None
    git_executable: str = "git"
    publish_worker_patch_artifacts: bool = False
    worker_patch_guide_agent_id: str = "agent:guide"
    worker_patch_target_task_id: str = ""
    replace_existing_result_artifact: bool = False
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CodexDeliveryE2ESmokeFixtureResult:
    """Result of optional C1 fixture initialization."""

    initialized: bool
    snapshot_path: Path
    event_log_path: Path
    target_task_id: str
    fixture: str = "simple"
    parallel_task_id: str = ""
    followup_task_id: str = ""
    waiting_task_id: str = ""

    def to_json_dict(self) -> dict[str, object]:
        return {
            "initialized": self.initialized,
            "snapshot_path": str(self.snapshot_path),
            "event_log_path": str(self.event_log_path),
            "fixture": self.fixture,
            "target_task_id": self.target_task_id,
            "parallel_task_id": self.parallel_task_id,
            "followup_task_id": self.followup_task_id,
            "waiting_task_id": self.waiting_task_id,
        }


@dataclass(frozen=True, slots=True)
class CodexDeliveryE2ESmokeResult:
    """Compact readback for one C1 smoke run."""

    request: CodexDeliveryE2ESmokeRequest
    fixture: CodexDeliveryE2ESmokeFixtureResult
    readiness: CodexCliHostReadinessReport | None
    dispatcher_tick: LeaderWorkerDispatcherTickResult | None
    delivery_sync: LeaderWorkerDeliverySyncResult | None
    codex_delivery: CodexDeliverySupervisorResult | None
    recovery: SchedulerRecoveryResult | None
    target_task_state: str = ""
    target_output_artifact_id: str = ""
    target_output_artifact_version: str = ""
    ok: bool = False
    stop_reason: str = ""
    stop_detail: str = ""

    def to_json_dict(self) -> dict[str, object]:
        runtime_invocation_log_path = (
            ""
            if self.request.runtime_invocation_log_path is None
            else str(Path(self.request.runtime_invocation_log_path))
        )
        delivery_state = read_leader_worker_delivery_state(
            self.request.delivery_state_path
        )
        runtime_invocation_count = 0
        if self.request.runtime_invocation_log_path is not None:
            runtime_invocation_count = len(
                JsonlRuntimeInvocationLog(
                    self.request.runtime_invocation_log_path
                ).read_all()
            )
        return {
            "ok": self.ok,
            "stop_reason": self.stop_reason,
            "stop_detail": self.stop_detail,
            "target_task_id": self.request.target_task_id,
            "target_task_state": self.target_task_state,
            "target_output_artifact_ref": {
                "ref_kind": "exchange_artifact" if self.target_output_artifact_id else "",
                "ref_id": self.target_output_artifact_id,
                "version": self.target_output_artifact_version,
            },
            "fixture": self.fixture.to_json_dict(),
            "readiness": None if self.readiness is None else self.readiness.to_json_dict(),
            "paths": {
                "scheduler_snapshot_path": str(Path(self.request.scheduler_snapshot_path)),
                "scheduler_event_log_path": str(Path(self.request.scheduler_event_log_path)),
                "artifact_store_path": str(Path(self.request.artifact_store_path)),
                "dispatcher_state_path": str(Path(self.request.dispatcher_state_path)),
                "dispatch_event_log_path": str(Path(self.request.dispatch_event_log_path)),
                "delivery_state_path": str(Path(self.request.delivery_state_path)),
                "delivery_event_log_path": str(Path(self.request.delivery_event_log_path)),
                "runtime_invocation_log_path": runtime_invocation_log_path,
            },
            "counts": {
                "dispatcher_decisions": (
                    0 if self.dispatcher_tick is None else self.dispatcher_tick.tick_record.decision_count
                ),
                "delivery_synced": (
                    0 if self.delivery_sync is None else self.delivery_sync.synced_count
                ),
                "codex_attempted": (
                    0 if self.codex_delivery is None else self.codex_delivery.attempted_count
                ),
                "codex_acknowledged": (
                    0 if self.codex_delivery is None else self.codex_delivery.executed_count
                ),
                "codex_failed": (
                    0 if self.codex_delivery is None else self.codex_delivery.failed_count
                ),
                "codex_skipped": (
                    0 if self.codex_delivery is None else self.codex_delivery.skipped_count
                ),
                "recovered_scheduler_events": (
                    0 if self.recovery is None else self.recovery.event_count
                ),
                "runtime_invocations": runtime_invocation_count,
                "delivery_records": 0 if delivery_state is None else len(delivery_state.records),
            },
            "dispatcher_tick": (
                None if self.dispatcher_tick is None else self.dispatcher_tick.to_json_dict()
            ),
            "delivery_sync": (
                None if self.delivery_sync is None else self.delivery_sync.to_json_dict()
            ),
            "codex_delivery": (
                None if self.codex_delivery is None else self.codex_delivery.to_json_dict()
            ),
            "authority_split": {
                "workflow_surface": "host-owned-codex-delivery-e2e-smoke",
                "provider_executed": (
                    False if self.codex_delivery is None else self.codex_delivery.attempted_count > 0
                ),
                "scheduler_snapshot_mutated": self.fixture.initialized,
                "scheduler_event_log_mutated": (
                    False
                    if self.codex_delivery is None
                    else any(record.result_consumption is not None for record in self.codex_delivery.records)
                ),
                "dispatcher_state_mutated": self.dispatcher_tick is not None,
                "dispatcher_log_mutated": self.dispatcher_tick is not None,
                "delivery_state_mutated": self.delivery_sync is not None or self.codex_delivery is not None,
                "delivery_log_mutated": self.delivery_sync is not None or self.codex_delivery is not None,
                "exchange_store_mutated": (
                    False
                    if self.codex_delivery is None
                    else any(record.result_consumption is not None for record in self.codex_delivery.records)
                ),
                "runtime_invocation_log_mutated": runtime_invocation_count > 0,
                "mcp_live_provider_surface": False,
                "local_work_trajectory_mutated": False,
                "raw_transcript_persisted": False,
            },
        }


CodexDeliveryBoundedLoopStopReason = str


@dataclass(frozen=True, slots=True)
class CodexDeliveryBoundedLoopRequest:
    """Request for the C2 bounded Codex supervisor loop."""

    smoke_request: CodexDeliveryE2ESmokeRequest = field(
        default_factory=CodexDeliveryE2ESmokeRequest
    )
    max_ticks: int = 3
    max_deliveries: int = 3
    max_runtime_failures: int = 1
    max_delivery_attempts_per_record: int = 2
    target_task_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class CodexDeliveryBoundedLoopIteration:
    """One bounded C2 loop iteration."""

    iteration_index: int
    ready_marked_event_count_before: int
    ready_marked_event_count_after: int
    dispatcher_tick: LeaderWorkerDispatcherTickResult
    delivery_sync: LeaderWorkerDeliverySyncResult
    codex_delivery: CodexDeliverySupervisorResult
    recovery: SchedulerRecoveryResult

    def to_json_dict(self) -> dict[str, object]:
        return {
            "iteration_index": self.iteration_index,
            "ready_marked_event_count_before": self.ready_marked_event_count_before,
            "ready_marked_event_count_after": self.ready_marked_event_count_after,
            "dispatcher_decision_count": self.dispatcher_tick.tick_record.decision_count,
            "delivery_synced_count": self.delivery_sync.synced_count,
            "codex_attempted_count": self.codex_delivery.attempted_count,
            "codex_acknowledged_count": self.codex_delivery.executed_count,
            "codex_failed_count": self.codex_delivery.failed_count,
            "codex_skipped_count": self.codex_delivery.skipped_count,
            "recovered_scheduler_event_count": self.recovery.event_count,
            "dispatcher_tick": self.dispatcher_tick.to_json_dict(),
            "delivery_sync": self.delivery_sync.to_json_dict(),
            "codex_delivery": self.codex_delivery.to_json_dict(),
        }


@dataclass(frozen=True, slots=True)
class CodexDeliveryBoundedLoopResult:
    """Compact result for the C2 bounded Codex supervisor loop."""

    request: CodexDeliveryBoundedLoopRequest
    fixture: CodexDeliveryE2ESmokeFixtureResult
    readiness: CodexCliHostReadinessReport | None
    iterations: tuple[CodexDeliveryBoundedLoopIteration, ...]
    recovery: SchedulerRecoveryResult | None
    ok: bool
    stop_reason: CodexDeliveryBoundedLoopStopReason
    stop_detail: str = ""

    @property
    def tick_count(self) -> int:
        return len(self.iterations)

    @property
    def attempted_count(self) -> int:
        return sum(item.codex_delivery.attempted_count for item in self.iterations)

    @property
    def acknowledged_count(self) -> int:
        return sum(item.codex_delivery.executed_count for item in self.iterations)

    @property
    def failed_count(self) -> int:
        return sum(item.codex_delivery.failed_count for item in self.iterations)

    @property
    def skipped_count(self) -> int:
        return sum(item.codex_delivery.skipped_count for item in self.iterations)

    def to_json_dict(self) -> dict[str, object]:
        recovered_state = None if self.recovery is None else self.recovery.recovered_state
        task_states = (
            {}
            if recovered_state is None
            else _task_state_counts(recovered_state)
        )
        target_task_ids = _loop_target_task_ids(self.request)
        target_states = {
            task_id: (
                ""
                if recovered_state is None or task_id not in recovered_state.tasks
                else recovered_state.tasks[task_id].state
            )
            for task_id in target_task_ids
        }
        runtime_invocation_count = 0
        if self.request.smoke_request.runtime_invocation_log_path is not None:
            runtime_invocation_count = len(
                JsonlRuntimeInvocationLog(
                    self.request.smoke_request.runtime_invocation_log_path
                ).read_all()
            )
        delivery_state = read_leader_worker_delivery_state(
            self.request.smoke_request.delivery_state_path
        )
        return {
            "ok": self.ok,
            "stop_reason": self.stop_reason,
            "stop_detail": self.stop_detail,
            "max_ticks": self.request.max_ticks,
            "max_deliveries": self.request.max_deliveries,
            "max_runtime_failures": self.request.max_runtime_failures,
            "max_delivery_attempts_per_record": self.request.max_delivery_attempts_per_record,
            "tick_count": self.tick_count,
            "attempted_count": self.attempted_count,
            "acknowledged_count": self.acknowledged_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "runtime_invocation_count": runtime_invocation_count,
            "delivery_record_count": 0 if delivery_state is None else len(delivery_state.records),
            "task_state_counts": task_states,
            "target_task_states": target_states,
            "fixture": self.fixture.to_json_dict(),
            "readiness": None if self.readiness is None else self.readiness.to_json_dict(),
            "iterations": [item.to_json_dict() for item in self.iterations],
            "authority_split": {
                "workflow_surface": "host-owned-bounded-codex-supervisor-loop",
                "provider_executed": self.attempted_count > 0,
                "scheduler_snapshot_mutated": self.fixture.initialized,
                "scheduler_event_log_mutated": self.acknowledged_count > 0,
                "dispatcher_state_mutated": bool(self.iterations),
                "dispatcher_log_mutated": bool(self.iterations),
                "delivery_state_mutated": bool(self.iterations),
                "delivery_log_mutated": bool(self.iterations),
                "exchange_store_mutated": self.acknowledged_count > 0,
                "runtime_invocation_log_mutated": runtime_invocation_count > 0,
                "mcp_live_provider_surface": False,
                "local_work_trajectory_mutated": False,
                "raw_transcript_persisted": False,
            },
        }


def run_codex_delivery_e2e_smoke(
    request: CodexDeliveryE2ESmokeRequest,
    *,
    codex_cli_client: CodexCliClient,
) -> CodexDeliveryE2ESmokeResult:
    """Run the C1 Codex delivery E2E smoke over existing narrow surfaces."""

    _validate_fixture(request.fixture)
    if request.runtime_invocation_max_attempts < 1:
        raise ValueError("Codex delivery E2E smoke runtime attempts must be positive")
    if request.runtime_invocation_backoff_seconds < 0:
        raise ValueError("Codex delivery E2E smoke runtime backoff must be non-negative")
    fixture = CodexDeliveryE2ESmokeFixtureResult(
        initialized=False,
        snapshot_path=Path(request.scheduler_snapshot_path),
        event_log_path=Path(request.scheduler_event_log_path),
        target_task_id=request.target_task_id,
        fixture=request.fixture,
        parallel_task_id=request.parallel_task_id,
        followup_task_id=request.followup_task_id,
        waiting_task_id=request.waiting_task_id,
    )
    readiness: CodexCliHostReadinessReport | None = None
    if request.require_host_ready and hasattr(codex_cli_client, "host_readiness_report"):
        readiness = codex_cli_client.host_readiness_report()  # type: ignore[attr-defined]
        if not readiness.ready:
            return CodexDeliveryE2ESmokeResult(
                request=request,
                fixture=fixture,
                readiness=readiness,
                dispatcher_tick=None,
                delivery_sync=None,
                codex_delivery=None,
                recovery=None,
                ok=False,
                stop_reason="codex_not_ready",
                stop_detail=readiness.summary,
            )

    fixture = _initialize_fixture_if_requested(request)
    dispatcher_tick = run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=request.dispatcher_state_path,
            dispatch_event_log_path=request.dispatch_event_log_path,
            scheduler_snapshot_path=request.scheduler_snapshot_path,
            scheduler_event_log_path=request.scheduler_event_log_path,
            artifact_store_path=request.artifact_store_path,
            dispatcher_id=request.dispatcher_id,
            trajectory_id=request.trajectory_id,
            leader_agent_id=request.leader_agent_id,
            worker_agent_ids=_worker_agent_ids_for_fixture(request),
            timestamp=request.timestamp,
            strict_recovery=request.strict_recovery,
            metadata=request.metadata,
        )
    )
    delivery_sync = sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=request.delivery_state_path,
            delivery_event_log_path=request.delivery_event_log_path,
            dispatch_event_log_path=request.dispatch_event_log_path,
            delivery_id="leader-worker-delivery",
            dispatcher_id=request.dispatcher_id,
            timestamp=request.timestamp,
            host_id=request.host_id,
            metadata=request.metadata,
        )
    )
    codex_delivery = run_codex_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=request.delivery_state_path,
            delivery_event_log_path=request.delivery_event_log_path,
            scheduler_snapshot_path=request.scheduler_snapshot_path,
            scheduler_event_log_path=request.scheduler_event_log_path,
            runtime_invocation_log_path=request.runtime_invocation_log_path,
            artifact_store_path=request.artifact_store_path,
            consume_success_results=True,
            replace_existing_result_artifact=request.replace_existing_result_artifact,
            max_deliveries=1,
            timestamp=request.timestamp,
            host_id=request.host_id,
            host_invocation_id=request.host_invocation_id,
            requested_by="host:codex-delivery-e2e-smoke",
            reason="C1 host-owned Codex delivery E2E smoke",
            grant_id=f"grant-{request.host_invocation_id}",
            approved_by="host:codex-delivery-e2e-smoke",
            approved_at=request.timestamp,
            allow_network=request.allow_network,
                strict_recovery=request.strict_recovery,
                runtime_invocation_max_attempts=request.runtime_invocation_max_attempts,
                runtime_invocation_backoff_seconds=request.runtime_invocation_backoff_seconds,
                enable_sandbox_preflight=request.enable_sandbox_preflight,
                workspace_root=request.workspace_root,
                scratch_root=request.scratch_root,
                git_worktree_sandbox_root=request.git_worktree_sandbox_root,
                git_executable=request.git_executable,
                publish_worker_patch_artifacts=request.publish_worker_patch_artifacts,
                worker_patch_guide_agent_id=request.worker_patch_guide_agent_id,
                worker_patch_target_task_id=request.worker_patch_target_task_id,
                metadata=request.metadata,
            ),
            codex_cli_client=codex_cli_client,
        )
    recovery = recover_scheduler_state(
        request.scheduler_snapshot_path,
        request.scheduler_event_log_path,
        strict=request.strict_recovery,
    )
    task = recovery.recovered_state.tasks.get(request.target_task_id)
    output_ref = None if task is None else task.output_artifact_ref
    ok = bool(
        codex_delivery.ok
        and codex_delivery.executed_count == 1
        and task is not None
        and task.state == "complete"
        and output_ref is not None
        and output_ref.ref_id
    )
    return CodexDeliveryE2ESmokeResult(
        request=request,
        fixture=fixture,
        readiness=readiness,
        dispatcher_tick=dispatcher_tick,
        delivery_sync=delivery_sync,
        codex_delivery=codex_delivery,
        recovery=recovery,
        target_task_state="" if task is None else task.state,
        target_output_artifact_id="" if output_ref is None else output_ref.ref_id,
        target_output_artifact_version="" if output_ref is None else output_ref.version,
        ok=ok,
        stop_reason="complete" if ok else "target_not_complete",
        stop_detail=(
            "target Codex task recovered as complete"
            if ok
            else "target Codex task did not recover as complete"
        ),
    )


def run_bounded_codex_delivery_supervisor_loop(
    request: CodexDeliveryBoundedLoopRequest,
    *,
    codex_cli_client: CodexCliClient,
) -> CodexDeliveryBoundedLoopResult:
    """Run a bounded C2 loop that chains activation through Codex consumption."""

    _validate_fixture(request.smoke_request.fixture)
    if request.max_ticks < 0:
        raise ValueError("bounded Codex supervisor loop max_ticks must be non-negative")
    if request.max_deliveries < 0:
        raise ValueError("bounded Codex supervisor loop max_deliveries must be non-negative")
    if request.max_runtime_failures < 0:
        raise ValueError("bounded Codex supervisor loop max_runtime_failures must be non-negative")
    if request.max_delivery_attempts_per_record < 1:
        raise ValueError(
            "bounded Codex supervisor loop max_delivery_attempts_per_record must be positive"
        )

    smoke = request.smoke_request
    fixture = CodexDeliveryE2ESmokeFixtureResult(
        initialized=False,
        snapshot_path=Path(smoke.scheduler_snapshot_path),
        event_log_path=Path(smoke.scheduler_event_log_path),
        target_task_id=smoke.target_task_id,
        fixture=smoke.fixture,
        parallel_task_id=smoke.parallel_task_id,
        followup_task_id=smoke.followup_task_id,
        waiting_task_id=smoke.waiting_task_id,
    )
    readiness: CodexCliHostReadinessReport | None = None
    if smoke.require_host_ready and hasattr(codex_cli_client, "host_readiness_report"):
        readiness = codex_cli_client.host_readiness_report()  # type: ignore[attr-defined]
        if not readiness.ready:
            return CodexDeliveryBoundedLoopResult(
                request=request,
                fixture=fixture,
                readiness=readiness,
                iterations=(),
                recovery=None,
                ok=False,
                stop_reason="codex_not_ready",
                stop_detail=readiness.summary,
            )

    fixture = _initialize_fixture_if_requested(smoke)
    iterations: list[CodexDeliveryBoundedLoopIteration] = []
    total_deliveries = 0
    total_failures = 0
    recovery: SchedulerRecoveryResult | None = None
    stop_reason: CodexDeliveryBoundedLoopStopReason = "max_ticks_reached"
    stop_detail = "max_ticks reached"

    if request.max_ticks == 0:
        recovery = recover_scheduler_state(
            smoke.scheduler_snapshot_path,
            smoke.scheduler_event_log_path,
            strict=smoke.strict_recovery,
        )
        return CodexDeliveryBoundedLoopResult(
            request=request,
            fixture=fixture,
            readiness=readiness,
            iterations=(),
            recovery=recovery,
            ok=_all_targets_complete(recovery.recovered_state, _loop_target_task_ids(request)),
            stop_reason="max_ticks_reached",
            stop_detail="max_ticks is 0",
        )

    for iteration_index in range(1, request.max_ticks + 1):
        before_ready_count = _scheduler_event_count(smoke.scheduler_event_log_path)
        recovery = recover_scheduler_state(
            smoke.scheduler_snapshot_path,
            smoke.scheduler_event_log_path,
            strict=smoke.strict_recovery,
        )
        mark_ready_tasks(
            recovery.recovered_state,
            event_log=JsonlSchedulerEventLog(smoke.scheduler_event_log_path),
            timestamp=smoke.timestamp,
        )
        after_ready_count = _scheduler_event_count(smoke.scheduler_event_log_path)
        dispatcher_tick = run_leader_worker_dispatcher_tick(
            LeaderWorkerDispatcherTickRequest(
                dispatcher_state_path=smoke.dispatcher_state_path,
                dispatch_event_log_path=smoke.dispatch_event_log_path,
                scheduler_snapshot_path=smoke.scheduler_snapshot_path,
                scheduler_event_log_path=smoke.scheduler_event_log_path,
                artifact_store_path=smoke.artifact_store_path,
                dispatcher_id=smoke.dispatcher_id,
                trajectory_id=smoke.trajectory_id,
                leader_agent_id=smoke.leader_agent_id,
                worker_agent_ids=_worker_agent_ids_for_fixture(smoke),
                timestamp=smoke.timestamp,
                strict_recovery=smoke.strict_recovery,
                metadata=smoke.metadata,
            )
        )
        delivery_sync = sync_leader_worker_delivery_from_dispatch_log(
            LeaderWorkerDeliverySyncRequest(
                delivery_state_path=smoke.delivery_state_path,
                delivery_event_log_path=smoke.delivery_event_log_path,
                dispatch_event_log_path=smoke.dispatch_event_log_path,
                delivery_id="leader-worker-delivery",
                dispatcher_id=smoke.dispatcher_id,
                timestamp=smoke.timestamp,
                host_id=smoke.host_id,
                metadata=smoke.metadata,
            )
        )
        remaining_deliveries = request.max_deliveries - total_deliveries
        if remaining_deliveries <= 0:
            recovery = recover_scheduler_state(
                smoke.scheduler_snapshot_path,
                smoke.scheduler_event_log_path,
                strict=smoke.strict_recovery,
            )
            stop_reason = "max_deliveries_reached"
            stop_detail = "max_deliveries reached"
            break
        codex_delivery = run_codex_delivery_supervisor_once(
            CodexDeliverySupervisorRequest(
                delivery_state_path=smoke.delivery_state_path,
                delivery_event_log_path=smoke.delivery_event_log_path,
                scheduler_snapshot_path=smoke.scheduler_snapshot_path,
                scheduler_event_log_path=smoke.scheduler_event_log_path,
                runtime_invocation_log_path=smoke.runtime_invocation_log_path,
                artifact_store_path=smoke.artifact_store_path,
                consume_success_results=True,
                replace_existing_result_artifact=smoke.replace_existing_result_artifact,
                max_deliveries=remaining_deliveries,
                retry_failed_delivery=True,
                max_delivery_attempts_per_record=request.max_delivery_attempts_per_record,
                timestamp=smoke.timestamp,
                host_id=smoke.host_id,
                host_invocation_id=f"{smoke.host_invocation_id}:tick-{iteration_index:04d}",
                requested_by="host:bounded-codex-supervisor-loop",
                reason="C2 bounded host-owned Codex supervisor loop",
                grant_id=f"grant-{smoke.host_invocation_id}:tick-{iteration_index:04d}",
                approved_by="host:bounded-codex-supervisor-loop",
                approved_at=smoke.timestamp,
                allow_network=smoke.allow_network,
                strict_recovery=smoke.strict_recovery,
                runtime_invocation_max_attempts=smoke.runtime_invocation_max_attempts,
                runtime_invocation_backoff_seconds=smoke.runtime_invocation_backoff_seconds,
                enable_sandbox_preflight=smoke.enable_sandbox_preflight,
                workspace_root=smoke.workspace_root,
                scratch_root=smoke.scratch_root,
                git_worktree_sandbox_root=smoke.git_worktree_sandbox_root,
                git_executable=smoke.git_executable,
                publish_worker_patch_artifacts=smoke.publish_worker_patch_artifacts,
                worker_patch_guide_agent_id=smoke.worker_patch_guide_agent_id,
                worker_patch_target_task_id=smoke.worker_patch_target_task_id,
                metadata=smoke.metadata,
            ),
            codex_cli_client=codex_cli_client,
        )
        total_deliveries += codex_delivery.attempted_count
        total_failures += codex_delivery.failed_count
        recovery = recover_scheduler_state(
            smoke.scheduler_snapshot_path,
            smoke.scheduler_event_log_path,
            strict=smoke.strict_recovery,
        )
        iterations.append(
            CodexDeliveryBoundedLoopIteration(
                iteration_index=iteration_index,
                ready_marked_event_count_before=before_ready_count,
                ready_marked_event_count_after=after_ready_count,
                dispatcher_tick=dispatcher_tick,
                delivery_sync=delivery_sync,
                codex_delivery=codex_delivery,
                recovery=recovery,
            )
        )
        if total_failures >= request.max_runtime_failures and total_failures > 0:
            stop_reason = "max_runtime_failures_reached"
            stop_detail = "max_runtime_failures reached"
            break
        if total_deliveries >= request.max_deliveries:
            stop_reason = "max_deliveries_reached"
            stop_detail = "max_deliveries reached"
            break
        if _all_targets_complete(recovery.recovered_state, _loop_target_task_ids(request)):
            stop_reason = "all_targets_complete"
            stop_detail = "all target Codex tasks recovered as complete"
            break
        if (
            dispatcher_tick.tick_record.decision_count == 0
            and delivery_sync.synced_count == 0
            and codex_delivery.attempted_count == 0
            and after_ready_count == before_ready_count
        ):
            stop_reason = "no_progress"
            stop_detail = "no new readiness, dispatch, delivery, or Codex attempt"
            break

    if recovery is None:
        recovery = recover_scheduler_state(
            smoke.scheduler_snapshot_path,
            smoke.scheduler_event_log_path,
            strict=smoke.strict_recovery,
        )
    ok = _all_targets_complete(recovery.recovered_state, _loop_target_task_ids(request))
    return CodexDeliveryBoundedLoopResult(
        request=request,
        fixture=fixture,
        readiness=readiness,
        iterations=tuple(iterations),
        recovery=recovery,
        ok=ok,
        stop_reason=stop_reason,
        stop_detail=stop_detail,
    )


def run_bounded_codex_delivery_supervisor_loop_with_process_client(
    request: CodexDeliveryBoundedLoopRequest,
    *,
    codex_cli_client: CodexCliProcessClient,
) -> CodexDeliveryBoundedLoopResult:
    """Typed convenience wrapper for process-backed C2 loop callers."""

    return run_bounded_codex_delivery_supervisor_loop(
        request,
        codex_cli_client=codex_cli_client,
    )


def run_codex_delivery_e2e_smoke_with_process_client(
    request: CodexDeliveryE2ESmokeRequest,
    *,
    codex_cli_client: CodexCliProcessClient,
) -> CodexDeliveryE2ESmokeResult:
    """Typed convenience wrapper for process-backed host CLI callers."""

    return run_codex_delivery_e2e_smoke(
        request,
        codex_cli_client=codex_cli_client,
    )


def _initialize_fixture_if_requested(
    request: CodexDeliveryE2ESmokeRequest,
) -> CodexDeliveryE2ESmokeFixtureResult:
    _validate_fixture(request.fixture)
    snapshot_path = Path(request.scheduler_snapshot_path)
    event_log_path = Path(request.scheduler_event_log_path)
    if not request.initialize_fixture:
        return CodexDeliveryE2ESmokeFixtureResult(
            initialized=False,
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            target_task_id=request.target_task_id,
            fixture=request.fixture,
            parallel_task_id=request.parallel_task_id,
            followup_task_id=request.followup_task_id,
            waiting_task_id=request.waiting_task_id,
        )
    if snapshot_path.exists() and not request.replace_existing_fixture:
        raise ValueError(
            "Codex delivery E2E smoke fixture snapshot already exists; "
            "pass replace_existing_fixture=True or choose another path"
        )
    event_log_path.parent.mkdir(parents=True, exist_ok=True)
    JsonlSchedulerEventLog(event_log_path).clear()
    write_scheduler_state_snapshot(
        _fixture_scheduler_state(request),
        snapshot_path,
    )
    return CodexDeliveryE2ESmokeFixtureResult(
        initialized=True,
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        target_task_id=request.target_task_id,
        fixture=request.fixture,
        parallel_task_id=request.parallel_task_id,
        followup_task_id=request.followup_task_id,
        waiting_task_id=request.waiting_task_id,
    )


def _fixture_scheduler_state(request: CodexDeliveryE2ESmokeRequest) -> SchedulerState:
    if request.fixture == "multilane":
        return _multilane_fixture_scheduler_state(request)
    return _simple_fixture_scheduler_state(request)


def _simple_fixture_scheduler_state(request: CodexDeliveryE2ESmokeRequest) -> SchedulerState:
    return SchedulerState(
        tasks={
            request.target_task_id: ScheduledTask(
                task_id=request.target_task_id,
                title="Codex CLI C1 smoke worker",
                instruction=(
                    "Return one compact confirmation that this scheduler-owned "
                    "Codex worker task executed. Do not edit repository files."
                ),
                agent=AgentSpec(
                    agent_id=request.codex_agent_id,
                    runtime_provider="codex",
                ),
                state="ready",
                context_scope=ContextScope(
                    context_id="context:codex-delivery-e2e-smoke",
                    lane_id=request.codex_lane_id,
                ),
                acceptance=(
                    "Return a concise final message.",
                    "Do not include secrets or raw credential material.",
                    "Do not modify source workspace files.",
                ),
                output_artifact_id=f"{request.target_task_id}:codex-result",
            ),
            request.waiting_task_id: ScheduledTask(
                task_id=request.waiting_task_id,
                title="Waiting non-Codex control task",
                instruction="Remain waiting during the C1 Codex smoke.",
                agent=AgentSpec(
                    agent_id=request.waiting_agent_id,
                    runtime_provider="fake",
                ),
                state="waiting",
                context_scope=ContextScope(
                    context_id="context:codex-delivery-e2e-smoke-waiting",
                    lane_id=request.waiting_lane_id,
                ),
                input_artifact_refs=(
                    ExchangeReference(
                        ref_kind="exchange_artifact",
                        ref_id=f"{request.target_task_id}:codex-result",
                    ),
                ),
                blocked_reason=f"waiting for {request.target_task_id}",
            ),
            request.followup_task_id: ScheduledTask(
                task_id=request.followup_task_id,
                title="Codex CLI C2 follow-up worker",
                instruction=(
                    "Return one compact confirmation that the follow-up "
                    "scheduler-owned Codex worker task executed. Do not edit "
                    "repository files."
                ),
                agent=AgentSpec(
                    agent_id=request.followup_agent_id,
                    runtime_provider="codex",
                ),
                state="waiting",
                context_scope=ContextScope(
                    context_id="context:codex-delivery-e2e-smoke-followup",
                    lane_id=request.followup_lane_id,
                ),
                acceptance=(
                    "Return a concise final message.",
                    "Do not include secrets or raw credential material.",
                    "Do not modify source workspace files.",
                ),
                output_artifact_id=f"{request.followup_task_id}:codex-result",
                blocked_reason=f"waiting for {request.target_task_id}",
            ),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-codex-smoke-worker-followup",
                source_task_id=request.target_task_id,
                target_task_id=request.followup_task_id,
                required_state="complete",
            ),
        ),
    )


def _multilane_fixture_scheduler_state(request: CodexDeliveryE2ESmokeRequest) -> SchedulerState:
    state = _simple_fixture_scheduler_state(request)
    tasks = dict(state.tasks)
    tasks[request.parallel_task_id] = ScheduledTask(
        task_id=request.parallel_task_id,
        title="Codex CLI C6 parallel-lane worker",
        instruction=(
            "Return one compact confirmation that this independent lane "
            "scheduler-owned Codex worker task executed. Do not edit "
            "repository files."
        ),
        agent=AgentSpec(
            agent_id=request.parallel_agent_id,
            runtime_provider="codex",
        ),
        state="ready",
        context_scope=ContextScope(
            context_id="context:codex-delivery-multilane-parallel",
            lane_id=request.parallel_lane_id,
        ),
        acceptance=(
            "Return a concise final message.",
            "Do not include secrets or raw credential material.",
            "Do not modify source workspace files.",
        ),
        output_artifact_id=f"{request.parallel_task_id}:codex-result",
    )
    return SchedulerState(
        tasks=tasks,
        dependencies=state.dependencies,
        merge_gates=state.merge_gates,
        run_records=state.run_records,
        edit_lease_lifecycle=state.edit_lease_lifecycle,
    )


def _scheduler_event_count(path: str | Path) -> int:
    return len(JsonlSchedulerEventLog(path).read_all())


def _loop_target_task_ids(request: CodexDeliveryBoundedLoopRequest) -> tuple[str, ...]:
    if request.target_task_ids:
        return request.target_task_ids
    smoke = request.smoke_request
    if smoke.fixture == "multilane":
        return (smoke.target_task_id, smoke.parallel_task_id, smoke.followup_task_id)
    return (smoke.target_task_id, smoke.followup_task_id)


def _worker_agent_ids_for_fixture(
    request: CodexDeliveryE2ESmokeRequest,
) -> tuple[str, ...]:
    ids = [
        request.codex_agent_id,
        request.followup_agent_id,
        request.waiting_agent_id,
    ]
    if request.fixture == "multilane":
        ids.insert(1, request.parallel_agent_id)
    return tuple(dict.fromkeys(ids))


def _validate_fixture(fixture: str) -> None:
    if fixture not in {"simple", "multilane"}:
        raise ValueError(
            "Codex delivery fixture must be 'simple' or 'multilane'; "
            f"got {fixture!r}"
        )


def _all_targets_complete(state: SchedulerState, target_task_ids: tuple[str, ...]) -> bool:
    return bool(target_task_ids) and all(
        state.tasks.get(task_id) is not None
        and state.tasks[task_id].state == "complete"
        for task_id in target_task_ids
    )


def _task_state_counts(state: SchedulerState) -> dict[str, int]:
    counts: dict[str, int] = {}
    for task in state.tasks.values():
        counts[task.state] = counts.get(task.state, 0) + 1
    return dict(sorted(counts.items()))


__all__ = [
    "DEFAULT_CODEX_DELIVERY_E2E_SMOKE_EVENT_LOG_RELATIVE_PATH",
    "DEFAULT_CODEX_DELIVERY_E2E_SMOKE_SNAPSHOT_RELATIVE_PATH",
    "CodexDeliveryE2ESmokeFixtureResult",
    "CodexDeliveryE2ESmokeRequest",
    "CodexDeliveryE2ESmokeResult",
    "CodexDeliveryBoundedLoopIteration",
    "CodexDeliveryBoundedLoopRequest",
    "CodexDeliveryBoundedLoopResult",
    "CodexDeliveryBoundedLoopStopReason",
    "run_bounded_codex_delivery_supervisor_loop",
    "run_bounded_codex_delivery_supervisor_loop_with_process_client",
    "run_codex_delivery_e2e_smoke",
    "run_codex_delivery_e2e_smoke_with_process_client",
]
