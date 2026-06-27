"""Host-owned Codex execution over leader/worker delivery records."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Literal

from .leader_worker_delivery import (
    LeaderWorkerDeliveryAckRequest,
    LeaderWorkerDeliveryAckResult,
    LeaderWorkerDeliveryRecord,
    acknowledge_leader_worker_delivery,
    read_leader_worker_delivery_state,
)
from .codex_permission_review_consumer import (
    CodexPermissionReviewConsumerRequest,
    CodexPermissionReviewConsumerResult,
    consume_codex_permission_review_result,
)
from .codex_result_consumer import (
    CodexResultConsumerRequest,
    CodexResultConsumerResult,
    consume_successful_codex_result,
)
from .exchange_store import DEFAULT_EXCHANGE_ARTIFACT_STORE_RELATIVE_PATH
from .exchange_store import JsonArtifactVersionStore
from .preflight import (
    OrchestrationPreflightBundle,
    PreflightedTaskRunResult,
    build_orchestration_preflight_bundle,
)
from .runtime_adapter import (
    CodexCliClient,
    CodexCliRequest,
    CodexCliResult,
    PermissionRequest,
    RuntimeRunResult,
)
from .runtime_invocation_audit import (
    DEFAULT_RUNTIME_INVOCATION_LOG_RELATIVE_PATH,
    JsonlRuntimeInvocationLog,
    RuntimeRetryPolicy,
    run_with_runtime_invocation_audit,
)
from .sandbox import (
    GitWorktreeSandboxProvider,
    SandboxProviderRegistry,
    SharedProcessSandboxProvider,
)
from .runtime_wiring import (
    RuntimeHostInvocation,
    RuntimeProviderPermissionGrant,
    RuntimeRegistryWiringConfig,
    build_runtime_registry_from_config,
)
from .scheduler import (
    ScheduledTask,
    SchedulerState,
    evaluate_task_admission,
    task_to_runtime_spec,
)
from .scheduler_store import recover_scheduler_state
from .worker_patch_review import build_worker_patch_review_artifact

CodexDeliverySupervisorRecordStatus = Literal[
    "acknowledged",
    "review_required",
    "failed",
    "skipped",
]


@dataclass(frozen=True, slots=True)
class CodexDeliverySupervisorRequest:
    """Request for one bounded host-owned Codex delivery supervisor pass."""

    delivery_state_path: str | Path
    delivery_event_log_path: str | Path
    scheduler_snapshot_path: str | Path
    scheduler_event_log_path: str | Path
    runtime_invocation_log_path: str | Path | None = DEFAULT_RUNTIME_INVOCATION_LOG_RELATIVE_PATH
    artifact_store_path: str | Path | None = DEFAULT_EXCHANGE_ARTIFACT_STORE_RELATIVE_PATH
    consume_success_results: bool = False
    replace_existing_result_artifact: bool = False
    max_deliveries: int = 1
    retry_failed_delivery: bool = False
    retryable_failure_kinds: tuple[str, ...] = (
        "timeout",
        "process_failed",
        "unknown",
        "cli_unavailable",
    )
    max_delivery_attempts_per_record: int = 2
    timestamp: str = ""
    host_id: str = "host:codex-delivery-supervisor"
    host_invocation_id: str = "host-owned-codex-delivery-supervisor-once"
    requested_by: str = "host:codex-delivery-supervisor"
    reason: str = "host-owned Codex delivery supervisor pass"
    grant_id: str = "grant-host-owned-codex-delivery-supervisor"
    approved_by: str = "host:codex-delivery-supervisor"
    approved_at: str = ""
    grant_scope: str = "leader-worker-delivery"
    allow_network: bool = True
    strict_recovery: bool = True
    runtime_invocation_max_attempts: int = 2
    runtime_invocation_backoff_seconds: float = 0.0
    enable_sandbox_preflight: bool = False
    workspace_root: str | Path = ""
    scratch_root: str | Path = ".codex/scratch"
    git_worktree_sandbox_root: str | Path | None = None
    git_executable: str = "git"
    publish_worker_patch_artifacts: bool = False
    worker_patch_guide_agent_id: str = "agent:guide"
    worker_patch_target_task_id: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CodexDeliveryWorkerPatchReviewPublication:
    """Compact readback for a worker patch review proposal artifact."""

    artifact_id: str
    version: str
    patch_state: str
    changed_paths: tuple[str, ...] = ()
    sandbox_provider: str = ""
    sandbox_allocation_id: str = ""

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ref_kind": "exchange_artifact",
            "ref_id": self.artifact_id,
            "version": self.version,
            "patch_state": self.patch_state,
            "changed_paths": list(self.changed_paths),
            "sandbox_provider": self.sandbox_provider,
            "sandbox_allocation_id": self.sandbox_allocation_id,
        }


@dataclass(frozen=True, slots=True)
class CodexDeliverySupervisorRecord:
    """Compact result for one inspected delivery record."""

    source_key: str
    delivery_record_id: str
    task_id: str
    agent_id: str
    status: CodexDeliverySupervisorRecordStatus
    attempted: bool = False
    skip_reason: str = ""
    retry_attempt: bool = False
    failure_kind: str = ""
    failure_detail: str = ""
    runtime_session_id: str = ""
    runtime_run_id: str = ""
    invocation_id: str = ""
    output_artifact_id: str = ""
    output_artifact_version: str = ""
    permission_review: CodexPermissionReviewConsumerResult | None = None
    permission_requests: tuple[PermissionRequest, ...] = ()
    result_consumption: CodexResultConsumerResult | None = None
    worker_patch_review: CodexDeliveryWorkerPatchReviewPublication | None = None
    delivery_acknowledgement: LeaderWorkerDeliveryAckResult | None = None

    def to_json_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "source_key": self.source_key,
            "delivery_record_id": self.delivery_record_id,
            "task_id": self.task_id,
            "agent_id": self.agent_id,
            "status": self.status,
            "attempted": self.attempted,
            "skip_reason": self.skip_reason,
            "retry_attempt": self.retry_attempt,
            "failure_kind": self.failure_kind,
            "failure_detail": self.failure_detail,
            "runtime_session_id": self.runtime_session_id,
            "runtime_run_id": self.runtime_run_id,
            "invocation_id": self.invocation_id,
            "output_artifact_ref": {
                "ref_kind": "exchange_artifact" if self.output_artifact_id else "",
                "ref_id": self.output_artifact_id,
                "version": self.output_artifact_version,
            },
            "permission_request_count": len(self.permission_requests),
            "permission_requests": [
                _permission_request_to_json_dict(request)
                for request in self.permission_requests
            ],
        }
        if self.permission_review is not None:
            payload["permission_review"] = self.permission_review.to_json_dict()
        if self.result_consumption is not None:
            payload["result_consumption"] = self.result_consumption.to_json_dict()
        if self.worker_patch_review is not None:
            payload["worker_patch_review"] = self.worker_patch_review.to_json_dict()
        if self.delivery_acknowledgement is not None:
            payload["delivery_acknowledgement"] = (
                self.delivery_acknowledgement.to_json_dict()
            )
        return payload


@dataclass(frozen=True, slots=True)
class CodexDeliverySupervisorResult:
    """Result of one host-owned Codex delivery supervisor pass."""

    request: CodexDeliverySupervisorRequest
    records: tuple[CodexDeliverySupervisorRecord, ...]
    delivery_state_path: Path
    delivery_event_log_path: Path
    scheduler_snapshot_path: Path
    scheduler_event_log_path: Path
    artifact_store_path: Path | None = None
    runtime_invocation_log_path: Path | None = None
    recovered_scheduler_event_count: int = 0
    pending_delivery_count: int = 0
    inspected_delivery_count: int = 0

    @property
    def executed_count(self) -> int:
        return sum(1 for record in self.records if record.status == "acknowledged")

    @property
    def review_required_count(self) -> int:
        return sum(1 for record in self.records if record.status == "review_required")

    @property
    def failed_count(self) -> int:
        return sum(1 for record in self.records if record.status == "failed")

    @property
    def skipped_count(self) -> int:
        return sum(1 for record in self.records if record.status == "skipped")

    @property
    def attempted_count(self) -> int:
        return sum(1 for record in self.records if record.attempted)

    @property
    def ok(self) -> bool:
        return self.failed_count == 0

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "delivery_state_path": str(self.delivery_state_path),
            "delivery_event_log_path": str(self.delivery_event_log_path),
            "scheduler_snapshot_path": str(self.scheduler_snapshot_path),
            "scheduler_event_log_path": str(self.scheduler_event_log_path),
            "artifact_store_path": (
                "" if self.artifact_store_path is None else str(self.artifact_store_path)
            ),
            "runtime_invocation_log_path": (
                "" if self.runtime_invocation_log_path is None else str(self.runtime_invocation_log_path)
            ),
            "host_invocation_id": self.request.host_invocation_id,
            "host_id": self.request.host_id,
            "max_deliveries": self.request.max_deliveries,
            "retry_failed_delivery": self.request.retry_failed_delivery,
            "retryable_failure_kinds": list(self.request.retryable_failure_kinds),
            "max_delivery_attempts_per_record": self.request.max_delivery_attempts_per_record,
            "sandbox_preflight_enabled": self.request.enable_sandbox_preflight,
            "publish_worker_patch_artifacts": self.request.publish_worker_patch_artifacts,
            "pending_delivery_count": self.pending_delivery_count,
            "inspected_delivery_count": self.inspected_delivery_count,
            "attempted_count": self.attempted_count,
            "executed_count": self.executed_count,
            "review_required_count": self.review_required_count,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "recovered_scheduler_event_count": self.recovered_scheduler_event_count,
            "records": [record.to_json_dict() for record in self.records],
            "authority_split": {
                "workflow_surface": "host-owned-codex-delivery-supervisor-once",
                "runtime_registry_authority": "host_runtime_wiring",
                "provider_executed": self.attempted_count > 0,
                "delivery_state_mutated": self.attempted_count > 0,
                "delivery_log_mutated": self.attempted_count > 0,
                "runtime_invocation_log_mutated": (
                    self.runtime_invocation_log_path is not None and self.attempted_count > 0
                ),
                "scheduler_state_mutated": False,
                "scheduler_event_log_mutated": any(
                    record.result_consumption is not None
                    or record.permission_review is not None
                    for record in self.records
                ),
                "exchange_store_mutated": any(
                    record.result_consumption is not None
                    or record.permission_review is not None
                    or record.worker_patch_review is not None
                    for record in self.records
                ),
                "worker_patch_review_artifacts_published": any(
                    record.worker_patch_review is not None
                    for record in self.records
                ),
                "dispatcher_state_mutated": False,
                "mcp_live_provider_surface": False,
                "local_work_trajectory_mutated": False,
                "raw_transcript_persisted": False,
            },
        }


def run_codex_delivery_supervisor_once(
    request: CodexDeliverySupervisorRequest,
    *,
    codex_cli_client: CodexCliClient,
) -> CodexDeliverySupervisorResult:
    """Run one bounded Codex delivery supervisor pass.

    This function executes Codex over eligible pending delivery records and
    writes only delivery acknowledgement plus runtime invocation audit.
    Scheduler task lifecycle state is intentionally not mutated in this gate.
    """

    if request.max_deliveries < 0:
        raise ValueError("codex delivery supervisor max_deliveries must be non-negative")
    if request.max_delivery_attempts_per_record < 1:
        raise ValueError(
            "codex delivery supervisor max_delivery_attempts_per_record must be positive"
        )
    if request.publish_worker_patch_artifacts and not request.enable_sandbox_preflight:
        raise ValueError(
            "publish_worker_patch_artifacts requires enable_sandbox_preflight so "
            "sandbox allocation metadata is available"
        )
    retry_policy = RuntimeRetryPolicy(
        max_attempts=request.runtime_invocation_max_attempts,
        backoff_seconds=request.runtime_invocation_backoff_seconds,
    ).normalized()
    state_path = Path(request.delivery_state_path)
    delivery_log_path = Path(request.delivery_event_log_path)
    snapshot_path = Path(request.scheduler_snapshot_path)
    scheduler_log_path = Path(request.scheduler_event_log_path)
    artifact_store_path = (
        None if request.artifact_store_path is None else Path(request.artifact_store_path)
    )
    invocation_log_path = (
        None
        if request.runtime_invocation_log_path is None
        else Path(request.runtime_invocation_log_path)
    )
    delivery_state = read_leader_worker_delivery_state(state_path)
    if delivery_state is None:
        raise ValueError(f"leader-worker delivery state does not exist: {state_path}")
    recovery = recover_scheduler_state(
        snapshot_path,
        scheduler_log_path,
        strict=request.strict_recovery,
    )
    runtime_client: CodexCliClient = codex_cli_client
    if invocation_log_path is not None:
        runtime_client = _AuditedCodexCliClient(
            inner=runtime_client,
            log=JsonlRuntimeInvocationLog(invocation_log_path),
            retry_policy=retry_policy,
            host_invocation_id=request.host_invocation_id,
        )
    host_invocation = RuntimeHostInvocation(
        surface="host-authorized-adapter",
        invocation_id=request.host_invocation_id,
        requested_providers=("codex",),
        requested_by=request.requested_by,
        reason=request.reason,
    )
    wiring = build_runtime_registry_from_config(
        RuntimeRegistryWiringConfig(
            providers=("codex",),
            timestamp=request.timestamp,
            host_invocation=host_invocation,
            codex_permission_grant=RuntimeProviderPermissionGrant(
                grant_id=request.grant_id,
                provider="codex",
                approved_by=request.approved_by,
                approved_at=request.approved_at or request.timestamp,
                scope=request.grant_scope,
                allow_process_spawn=True,
                allow_network=request.allow_network,
            ),
        ),
        codex_cli_client=runtime_client,
    )
    runtime = wiring.registry.get("codex")
    sandbox_registry = (
        _sandbox_registry_for_request(request)
        if request.enable_sandbox_preflight
        else None
    )

    candidate_records = tuple(
        record
        for record in delivery_state.records.values()
        if _record_is_delivery_candidate(record, request)
    )
    result_records: list[CodexDeliverySupervisorRecord] = []
    attempted = 0
    for record in candidate_records:
        if attempted >= request.max_deliveries:
            break
        task = recovery.recovered_state.tasks.get(record.task_id)
        skip_reason = _skip_reason_for_record(
            record,
            scheduler_state=recovery.recovered_state,
            task=task,
        )
        if skip_reason:
            result_records.append(_skipped_record(record, skip_reason))
            continue

        precondition_failure = _precondition_failure_for_record(
            record,
            scheduler_state=recovery.recovered_state,
            task=task,
        )
        if precondition_failure:
            if attempted >= request.max_deliveries:
                break
            result_records.append(
                _fail_delivery_record(
                    request=request,
                    record=record,
                    state_path=state_path,
                    delivery_log_path=delivery_log_path,
                    failure_kind="delivery_precondition_failed",
                    failure_detail=precondition_failure,
                    runtime_session_id="",
                    runtime_run_id="",
                    invocation_id="",
                    attempted=False,
                )
            )
            continue

        assert task is not None
        attempted += 1
        retry_attempt = record.delivery_state == "failed"
        session = None
        invocation_id = ""
        preflight: OrchestrationPreflightBundle | None = None
        try:
            runtime_task = task_to_runtime_spec(task)
            if sandbox_registry is not None:
                preflight = build_orchestration_preflight_bundle(
                    _ready_task_for_preflight(task),
                    sandbox_registry=sandbox_registry,
                    scheduler_state=recovery.recovered_state,
                    workspace_root=str(request.workspace_root),
                    scratch_root=str(request.scratch_root),
                    created_at=request.timestamp,
                )
                runtime_task = preflight.runtime_task
            session = runtime.start_session(task.agent)
            invocation_id = _runtime_invocation_id(
                request.host_invocation_id,
                session.session_id,
                task.task_id,
            )
            run_result = runtime.run_task(session, runtime_task)
        except Exception as exc:
            result_records.append(
                _fail_delivery_record(
                    request=request,
                    record=record,
                    state_path=state_path,
                    delivery_log_path=delivery_log_path,
                    failure_kind=str(getattr(exc, "error_kind", "") or type(exc).__name__),
                    failure_detail=str(getattr(exc, "summary", "") or exc),
                    runtime_session_id=str(
                        getattr(exc, "session_id", "")
                        or (session.session_id if session is not None else "")
                    ),
                    runtime_run_id=str(getattr(exc, "run_id", "")),
                    invocation_id=invocation_id,
                    attempted=True,
                    retry_attempt=retry_attempt,
                )
            )
            continue

        result_consumption: CodexResultConsumerResult | None = None
        permission_review: CodexPermissionReviewConsumerResult | None = None
        if run_result.permission_requests:
            if artifact_store_path is None:
                result_records.append(
                    _fail_delivery_record(
                        request=request,
                        record=record,
                        state_path=state_path,
                        delivery_log_path=delivery_log_path,
                        failure_kind="permission_review_consumer_failed",
                        failure_detail=(
                            "Codex permission review requires artifact_store_path "
                            "so the review output artifact can be stored durably"
                        ),
                        runtime_session_id=run_result.run_handle.session_id,
                        runtime_run_id=run_result.run_handle.run_id,
                        invocation_id=invocation_id,
                        attempted=True,
                        retry_attempt=retry_attempt,
                    )
                )
                continue
            try:
                permission_review = consume_codex_permission_review_result(
                    CodexPermissionReviewConsumerRequest(
                        artifact_store_path=artifact_store_path,
                        scheduler_event_log_path=scheduler_log_path,
                        timestamp=request.timestamp,
                        event_id_prefix=request.host_invocation_id,
                        actor=request.host_id,
                        replace_existing_artifact=request.replace_existing_result_artifact,
                    ),
                    task=task,
                    run_result=run_result,
                )
            except Exception as exc:
                result_records.append(
                    _fail_delivery_record(
                        request=request,
                        record=record,
                        state_path=state_path,
                        delivery_log_path=delivery_log_path,
                        failure_kind="permission_review_consumer_failed",
                        failure_detail=str(exc),
                        runtime_session_id=run_result.run_handle.session_id,
                        runtime_run_id=run_result.run_handle.run_id,
                        invocation_id=invocation_id,
                        attempted=True,
                        retry_attempt=retry_attempt,
                    )
                )
                continue
            review_ack = acknowledge_leader_worker_delivery(
                LeaderWorkerDeliveryAckRequest(
                    delivery_state_path=state_path,
                    delivery_event_log_path=delivery_log_path,
                    source_key=record.source_key,
                    target_state="review_required",
                    timestamp=request.timestamp,
                    host_id=request.host_id,
                    runtime_provider="codex",
                    runtime_session_id=run_result.run_handle.session_id,
                    runtime_run_id=run_result.run_handle.run_id,
                    invocation_id=invocation_id,
                    metadata=_ack_metadata(
                        request,
                        record,
                        run_result=run_result,
                        permission_review=permission_review,
                    ),
                )
            )
            result_records.append(
                CodexDeliverySupervisorRecord(
                    source_key=record.source_key,
                    delivery_record_id=record.delivery_id,
                    task_id=record.task_id,
                    agent_id=record.agent_id,
                    status="review_required",
                    attempted=True,
                    runtime_session_id=run_result.run_handle.session_id,
                    runtime_run_id=run_result.run_handle.run_id,
                    invocation_id=invocation_id,
                    output_artifact_id=run_result.output_artifact.artifact_id,
                    output_artifact_version=run_result.output_artifact.version,
                    permission_review=permission_review,
                    permission_requests=tuple(run_result.permission_requests),
                    delivery_acknowledgement=review_ack,
                    retry_attempt=retry_attempt,
                )
            )
            continue

        worker_patch_review: CodexDeliveryWorkerPatchReviewPublication | None = None
        try:
            worker_patch_review = _publish_worker_patch_review_artifact(
                request=request,
                artifact_store_path=artifact_store_path,
                task=task,
                scheduler_state=recovery.recovered_state,
                preflight=preflight,
                run_result=run_result,
            )
        except Exception as exc:
            result_records.append(
                _fail_delivery_record(
                    request=request,
                    record=record,
                    state_path=state_path,
                    delivery_log_path=delivery_log_path,
                    failure_kind="worker_patch_review_publish_failed",
                    failure_detail=str(exc),
                    runtime_session_id=run_result.run_handle.session_id,
                    runtime_run_id=run_result.run_handle.run_id,
                    invocation_id=invocation_id,
                    attempted=True,
                    retry_attempt=retry_attempt,
                )
            )
            continue

        if request.consume_success_results:
            if artifact_store_path is None:
                result_records.append(
                    _fail_delivery_record(
                        request=request,
                        record=record,
                        state_path=state_path,
                        delivery_log_path=delivery_log_path,
                        failure_kind="result_consumer_failed",
                        failure_detail=(
                            "consume_success_results requires artifact_store_path "
                            "so the Codex output artifact can be stored durably"
                        ),
                        runtime_session_id=run_result.run_handle.session_id,
                        runtime_run_id=run_result.run_handle.run_id,
                        invocation_id=invocation_id,
                        attempted=True,
                        retry_attempt=retry_attempt,
                    )
                )
                continue
            try:
                result_consumption = consume_successful_codex_result(
                    CodexResultConsumerRequest(
                        artifact_store_path=artifact_store_path,
                        scheduler_event_log_path=scheduler_log_path,
                        timestamp=request.timestamp,
                        event_id_prefix=request.host_invocation_id,
                        actor=request.host_id,
                        replace_existing_artifact=request.replace_existing_result_artifact,
                    ),
                    task=task,
                    run_result=run_result,
                )
            except Exception as exc:
                result_records.append(
                    _fail_delivery_record(
                        request=request,
                        record=record,
                        state_path=state_path,
                        delivery_log_path=delivery_log_path,
                        failure_kind="result_consumer_failed",
                        failure_detail=str(exc),
                        runtime_session_id=run_result.run_handle.session_id,
                        runtime_run_id=run_result.run_handle.run_id,
                        invocation_id=invocation_id,
                        attempted=True,
                        retry_attempt=retry_attempt,
                    )
                )
                continue

        success_ack = acknowledge_leader_worker_delivery(
            LeaderWorkerDeliveryAckRequest(
                delivery_state_path=state_path,
                delivery_event_log_path=delivery_log_path,
                source_key=record.source_key,
                target_state="acknowledged",
                timestamp=request.timestamp,
                host_id=request.host_id,
                runtime_provider="codex",
                runtime_session_id=run_result.run_handle.session_id,
                runtime_run_id=run_result.run_handle.run_id,
                invocation_id=invocation_id,
                metadata=_ack_metadata(
                    request,
                    record,
                    run_result=run_result,
                    result_consumption=result_consumption,
                    worker_patch_review=worker_patch_review,
                ),
            )
        )
        result_records.append(
            CodexDeliverySupervisorRecord(
                source_key=record.source_key,
                delivery_record_id=record.delivery_id,
                task_id=record.task_id,
                agent_id=record.agent_id,
                status="acknowledged",
                attempted=True,
                runtime_session_id=run_result.run_handle.session_id,
                runtime_run_id=run_result.run_handle.run_id,
                invocation_id=invocation_id,
                output_artifact_id=run_result.output_artifact.artifact_id,
                output_artifact_version=run_result.output_artifact.version,
                result_consumption=result_consumption,
                worker_patch_review=worker_patch_review,
                permission_requests=tuple(run_result.permission_requests),
                delivery_acknowledgement=success_ack,
                retry_attempt=retry_attempt,
            )
        )

    return CodexDeliverySupervisorResult(
        request=request,
        records=tuple(result_records),
        delivery_state_path=state_path,
        delivery_event_log_path=delivery_log_path,
        scheduler_snapshot_path=snapshot_path,
        scheduler_event_log_path=scheduler_log_path,
        artifact_store_path=artifact_store_path,
        runtime_invocation_log_path=invocation_log_path,
        recovered_scheduler_event_count=recovery.event_count,
        pending_delivery_count=len(candidate_records),
        inspected_delivery_count=len(result_records),
    )


class _AuditedCodexCliClient:
    """Host-owned audit/retry wrapper around the Codex CLI client seam."""

    def __init__(
        self,
        *,
        inner: CodexCliClient,
        log: JsonlRuntimeInvocationLog,
        retry_policy: RuntimeRetryPolicy,
        host_invocation_id: str,
    ) -> None:
        self.inner = inner
        self.log = log
        self.retry_policy = retry_policy
        self.host_invocation_id = host_invocation_id

    def exec(self, request: CodexCliRequest) -> CodexCliResult:
        return run_with_runtime_invocation_audit(
            invocation_id=_runtime_invocation_id(
                self.host_invocation_id,
                request.session.session_id,
                request.task.task_id,
            ),
            provider="codex",
            operation=lambda: self.inner.exec(request),
            log=self.log,
            retry_policy=self.retry_policy,
            task_id=request.task.task_id,
            session_id=request.session.session_id,
            agent_id=request.agent.agent_id,
            runtime_surface="host-owned-codex-delivery-supervisor-once",
            metadata={
                "host_invocation_id": self.host_invocation_id,
                "lane_id": request.task.scope.lane_id,
                "context_id": request.task.scope.context_id,
                "run_id_available_at_client_seam": False,
            },
        )


def _skip_reason_for_record(
    record: LeaderWorkerDeliveryRecord,
    *,
    scheduler_state: SchedulerState,
    task: ScheduledTask | None,
) -> str:
    if record.event_kind != "task_ready" or record.next_action != "run_agent":
        return (
            "delivery record is not a task_ready/run_agent decision and must be "
            "handled by another delivery surface"
        )
    if task is None:
        return ""
    if task.agent.agent_id != record.agent_id:
        return ""
    if task.agent.runtime_provider != "codex":
        return f"task runtime provider is {task.agent.runtime_provider!r}, not 'codex'"
    if task.state == "complete":
        return "task already recovered as complete"
    return ""


def _record_is_delivery_candidate(
    record: LeaderWorkerDeliveryRecord,
    request: CodexDeliverySupervisorRequest,
) -> bool:
    if record.delivery_state == "pending":
        return True
    if record.delivery_state != "failed" or not request.retry_failed_delivery:
        return False
    if record.failure_kind not in set(request.retryable_failure_kinds):
        return False
    return record.delivery_attempt_count < request.max_delivery_attempts_per_record


def _precondition_failure_for_record(
    record: LeaderWorkerDeliveryRecord,
    *,
    scheduler_state: SchedulerState,
    task: ScheduledTask | None,
) -> str:
    if task is None:
        return f"scheduler task not found for delivery record task_id={record.task_id!r}"
    if task.agent.agent_id != record.agent_id:
        return (
            "delivery record agent does not match scheduler task agent: "
            f"delivery={record.agent_id!r}, scheduler={task.agent.agent_id!r}"
        )
    if task.state == "ready":
        return ""
    if task.state in {"proposed", "waiting", "blocked"}:
        decision = evaluate_task_admission(scheduler_state, task.task_id)
        if decision.state == "admissible":
            return ""
        return f"task is not currently admissible: {decision.state} {decision.reason}".strip()
    return f"task is not ready for Codex delivery: {task.state}"


def _sandbox_registry_for_request(
    request: CodexDeliverySupervisorRequest,
) -> SandboxProviderRegistry:
    registry = SandboxProviderRegistry()
    registry.register(SharedProcessSandboxProvider())
    if request.git_worktree_sandbox_root is not None and str(request.git_worktree_sandbox_root):
        registry.register(
            GitWorktreeSandboxProvider(
                request.git_worktree_sandbox_root,
                git_executable=request.git_executable,
            )
        )
    return registry


def _ready_task_for_preflight(task: ScheduledTask) -> ScheduledTask:
    if task.state == "ready":
        return task
    return replace(task, state="ready", blocked_reason="")


def _publish_worker_patch_review_artifact(
    *,
    request: CodexDeliverySupervisorRequest,
    artifact_store_path: Path | None,
    task: ScheduledTask,
    scheduler_state: SchedulerState,
    preflight: OrchestrationPreflightBundle | None,
    run_result: RuntimeRunResult,
) -> CodexDeliveryWorkerPatchReviewPublication | None:
    if not request.publish_worker_patch_artifacts:
        return None
    if preflight is None:
        return None
    if preflight.sandbox_allocation.provider != "git-worktree":
        return None
    if artifact_store_path is None:
        raise ValueError(
            "publish_worker_patch_artifacts requires artifact_store_path so "
            "the worker patch review proposal can be stored durably"
        )
    review = build_worker_patch_review_artifact(
        PreflightedTaskRunResult(
            preflight=preflight,
            state=scheduler_state,
            runtime_result=run_result,
        ),
        timestamp=request.timestamp,
        guide_agent_id=request.worker_patch_guide_agent_id,
        target_task_id=request.worker_patch_target_task_id or task.task_id,
        git_executable=request.git_executable,
    )
    JsonArtifactVersionStore(artifact_store_path).put(
        review.artifact,
        replace_existing=request.replace_existing_result_artifact,
    )
    return CodexDeliveryWorkerPatchReviewPublication(
        artifact_id=review.artifact.artifact_id,
        version=review.artifact.version,
        patch_state=review.patch_state,
        changed_paths=review.changed_paths,
        sandbox_provider=preflight.sandbox_allocation.provider,
        sandbox_allocation_id=preflight.sandbox_allocation.allocation_id,
    )


def _skipped_record(
    record: LeaderWorkerDeliveryRecord,
    skip_reason: str,
) -> CodexDeliverySupervisorRecord:
    return CodexDeliverySupervisorRecord(
        source_key=record.source_key,
        delivery_record_id=record.delivery_id,
        task_id=record.task_id,
        agent_id=record.agent_id,
        status="skipped",
        skip_reason=skip_reason,
    )


def _fail_delivery_record(
    *,
    request: CodexDeliverySupervisorRequest,
    record: LeaderWorkerDeliveryRecord,
    state_path: Path,
    delivery_log_path: Path,
    failure_kind: str,
    failure_detail: str,
    runtime_session_id: str,
    runtime_run_id: str,
    invocation_id: str,
    attempted: bool,
    retry_attempt: bool = False,
) -> CodexDeliverySupervisorRecord:
    failure_ack = acknowledge_leader_worker_delivery(
        LeaderWorkerDeliveryAckRequest(
            delivery_state_path=state_path,
            delivery_event_log_path=delivery_log_path,
            source_key=record.source_key,
            target_state="failed",
            timestamp=request.timestamp,
            host_id=request.host_id,
            runtime_provider="codex",
            runtime_session_id=runtime_session_id,
            runtime_run_id=runtime_run_id,
            invocation_id=invocation_id,
            failure_kind=failure_kind,
            failure_detail=_safe_failure_detail(failure_detail),
            metadata=_ack_metadata(request, record),
        )
    )
    return CodexDeliverySupervisorRecord(
        source_key=record.source_key,
        delivery_record_id=record.delivery_id,
        task_id=record.task_id,
        agent_id=record.agent_id,
        status="failed",
        attempted=attempted,
        failure_kind=failure_ack.record.failure_kind,
        failure_detail=failure_ack.record.failure_detail,
        runtime_session_id=failure_ack.record.runtime_session_id,
        runtime_run_id=failure_ack.record.runtime_run_id,
        invocation_id=failure_ack.record.invocation_id,
        retry_attempt=retry_attempt,
        delivery_acknowledgement=failure_ack,
    )


def _ack_metadata(
    request: CodexDeliverySupervisorRequest,
    record: LeaderWorkerDeliveryRecord,
    *,
    run_result: RuntimeRunResult | None = None,
    permission_review: CodexPermissionReviewConsumerResult | None = None,
    result_consumption: CodexResultConsumerResult | None = None,
    worker_patch_review: CodexDeliveryWorkerPatchReviewPublication | None = None,
) -> dict[str, object]:
    metadata: dict[str, object] = {
        "runner": "host-owned-codex-delivery-supervisor-once",
        "host_invocation_id": request.host_invocation_id,
        "delivery_record_id": record.delivery_id,
        "scheduler_snapshot_path": str(request.scheduler_snapshot_path),
        "scheduler_event_log_path": str(request.scheduler_event_log_path),
        "runtime_invocation_log_path": (
            "" if request.runtime_invocation_log_path is None else str(request.runtime_invocation_log_path)
        ),
        "artifact_store_path": (
            "" if request.artifact_store_path is None else str(request.artifact_store_path)
        ),
        "consume_success_results": request.consume_success_results,
        "retry_failed_delivery": request.retry_failed_delivery,
        "retryable_failure_kinds": list(request.retryable_failure_kinds),
        "max_delivery_attempts_per_record": request.max_delivery_attempts_per_record,
        "sandbox_preflight_enabled": request.enable_sandbox_preflight,
        "publish_worker_patch_artifacts": request.publish_worker_patch_artifacts,
        "retry_attempt": record.delivery_state == "failed",
        "scheduler_state_mutated": False,
        "scheduler_event_log_mutated": (
            result_consumption is not None or permission_review is not None
        ),
        "exchange_store_mutated": (
            result_consumption is not None
            or permission_review is not None
            or worker_patch_review is not None
        ),
    }
    if run_result is not None:
        metadata.update(
            {
                "output_artifact_id": run_result.output_artifact.artifact_id,
                "output_artifact_version": run_result.output_artifact.version,
                "permission_request_count": len(run_result.permission_requests),
                "permission_requests": [
                    _permission_request_to_json_dict(permission_request)
                    for permission_request in run_result.permission_requests
                ],
            }
        )
    if permission_review is not None:
        metadata["permission_review"] = permission_review.to_json_dict()
    if result_consumption is not None:
        metadata["result_consumption"] = result_consumption.to_json_dict()
    if worker_patch_review is not None:
        metadata["worker_patch_review"] = worker_patch_review.to_json_dict()
    metadata.update(dict(request.metadata))
    return metadata


def _runtime_invocation_id(
    host_invocation_id: str,
    session_id: str,
    task_id: str,
) -> str:
    return ":".join(
        part
        for part in (
            "codex-delivery",
            host_invocation_id,
            session_id,
            task_id,
        )
        if part
    )


def _safe_failure_detail(value: str, *, limit: int = 500) -> str:
    text = str(value or "").replace("\r\n", "\n").strip()
    redacted = text
    for marker in (
        "OPENAI_API_KEY",
        "CODEX_AUTH_TOKEN",
        "QODER_PERSONAL_ACCESS_TOKEN",
        "DASHSCOPE_API_KEY",
    ):
        redacted = re.sub(
            rf"{re.escape(marker)}\s*=\s*[^\s,;]+",
            f"{marker}=[redacted]",
            redacted,
        )
        redacted = re.sub(
            rf"\b{re.escape(marker)}\b(?!=\[redacted\])",
            f"{marker}[redacted]",
            redacted,
        )
    if len(redacted) <= limit:
        return redacted
    return redacted[: limit - 3].rstrip() + "..."


def _permission_request_to_json_dict(
    request: PermissionRequest,
) -> dict[str, object]:
    return {
        "request_id": request.request_id,
        "request_kind": request.request_kind,
        "run_id": request.run_id,
        "summary": request.summary,
        "target": request.target,
    }


__all__ = [
    "CodexDeliveryWorkerPatchReviewPublication",
    "CodexDeliverySupervisorRecord",
    "CodexDeliverySupervisorRecordStatus",
    "CodexDeliverySupervisorRequest",
    "CodexDeliverySupervisorResult",
    "run_codex_delivery_supervisor_once",
]
