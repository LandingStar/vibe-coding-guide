"""Host-owned Codex execution over leader/worker delivery records."""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor
from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Literal

from .continuous_worker_binding import (
    DEFAULT_CONTINUOUS_WORKER_BINDING_EVENT_LOG_RELATIVE_PATH,
    DEFAULT_CONTINUOUS_WORKER_BINDING_LEDGER_RELATIVE_PATH,
    DEFAULT_CONTINUOUS_WORKER_DELIVERY_LEASE_EVENT_LOG_RELATIVE_PATH,
    DEFAULT_CONTINUOUS_WORKER_DELIVERY_LEASE_LEDGER_RELATIVE_PATH,
    DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_RELATIVE_PATH,
)
from .continuous_worker_context import (
    DEFAULT_CONTINUOUS_WORKER_COMPACT_CONTEXT_DIR_RELATIVE_PATH,
)
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
from .opencode_session_ledger import DEFAULT_OPENCODE_SESSION_LEDGER_RELATIVE_PATH
from .preflight import (
    OrchestrationPreflightBundle,
    PreflightedTaskRunResult,
    build_orchestration_preflight_bundle,
)
from .runtime_adapter import (
    CodexCliClient,
    CodexCliRequest,
    CodexCliResult,
    OpenCodeCliClient,
    OpenCodeCliRequest,
    OpenCodeCliResult,
    PermissionRequest,
    RuntimeProviderKind,
    RuntimeRunResult,
    TaskSpec,
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
    SchedulerEvent,
    SchedulerState,
    evaluate_task_admission,
    task_to_runtime_spec,
)
from .scheduler_store import JsonlSchedulerEventLog, recover_scheduler_state
from .worker_patch_review import build_worker_patch_review_artifact

CodexDeliverySupervisorRecordStatus = Literal[
    "acknowledged",
    "review_required",
    "failed",
    "skipped",
]


@dataclass(frozen=True, slots=True)
class _PreparedCodexDelivery:
    record: LeaderWorkerDeliveryRecord
    task: ScheduledTask
    retry_attempt: bool
    runtime_task: TaskSpec
    preflight: OrchestrationPreflightBundle | None = None
    batch_id: str = ""
    batch_size: int = 1
    continuous_worker_binding_id: str = ""
    continuous_worker_id: str = ""
    continuous_worker_delivery_lease_id: str = ""
    continuous_worker_delivery_lease_ledger_path: str | Path = ""
    continuous_worker_delivery_lease_event_log_path: str | Path = ""
    scheduler_event_log_path: str | Path = ""
    delivery_timestamp: str = ""


@dataclass(frozen=True, slots=True)
class _RuntimeDeliveryOutcome:
    prepared: _PreparedCodexDelivery
    session_id: str = ""
    run_id: str = ""
    invocation_id: str = ""
    run_result: RuntimeRunResult | None = None
    failure_kind: str = ""
    failure_detail: str = ""
    raw_error_type: str = ""
    retryable: bool = False


@dataclass(frozen=True, slots=True)
class CodexDeliverySupervisorRequest:
    """Request for one bounded host-owned Codex delivery supervisor pass."""

    delivery_state_path: str | Path
    delivery_event_log_path: str | Path
    scheduler_snapshot_path: str | Path
    scheduler_event_log_path: str | Path
    runtime_provider: RuntimeProviderKind = "codex"
    runtime_invocation_log_path: str | Path | None = DEFAULT_RUNTIME_INVOCATION_LOG_RELATIVE_PATH
    artifact_store_path: str | Path | None = DEFAULT_EXCHANGE_ARTIFACT_STORE_RELATIVE_PATH
    consume_success_results: bool = False
    replace_existing_result_artifact: bool = False
    max_deliveries: int = 1
    max_concurrent_deliveries: int = 1
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
    scratch_root: str | Path = ".dbc/scratch"
    git_worktree_sandbox_root: str | Path | None = None
    git_executable: str = "git"
    publish_worker_patch_artifacts: bool = False
    worker_patch_guide_agent_id: str = "agent:guide"
    worker_patch_target_task_id: str = ""
    opencode_session_ledger_path: str | Path = DEFAULT_OPENCODE_SESSION_LEDGER_RELATIVE_PATH
    opencode_enable_session_lookup: bool = False
    continuous_worker_binding_ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_LEDGER_RELATIVE_PATH
    continuous_worker_binding_event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_EVENT_LOG_RELATIVE_PATH
    continuous_worker_context_bundle_dir_path: str | Path = DEFAULT_CONTINUOUS_WORKER_COMPACT_CONTEXT_DIR_RELATIVE_PATH
    continuous_worker_delivery_lease_ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_DELIVERY_LEASE_LEDGER_RELATIVE_PATH
    continuous_worker_delivery_lease_event_log_path: str | Path = DEFAULT_CONTINUOUS_WORKER_DELIVERY_LEASE_EVENT_LOG_RELATIVE_PATH
    continuous_worker_lane_ownership_ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_LANE_OWNERSHIP_LEDGER_RELATIVE_PATH
    enable_continuous_worker_binding_lookup: bool = False
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
    concurrent_batch_id: str = ""
    concurrent_batch_size: int = 0
    process_parallel_execution: bool = False
    serialized_writeback: bool = True

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
            "concurrent_batch_id": self.concurrent_batch_id,
            "concurrent_batch_size": self.concurrent_batch_size,
            "process_parallel_execution": self.process_parallel_execution,
            "serialized_writeback": self.serialized_writeback,
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
            "runtime_provider": self.request.runtime_provider,
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
            "max_concurrent_deliveries": self.request.max_concurrent_deliveries,
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
            "concurrency": {
                "requested_max_concurrent_deliveries": self.request.max_concurrent_deliveries,
                "effective_max_concurrent_deliveries": max(1, self.request.max_concurrent_deliveries),
                "max_observed_concurrent_batch_size": max(
                    (record.concurrent_batch_size for record in self.records),
                    default=0,
                ),
                "process_parallel_execution": any(
                    record.process_parallel_execution for record in self.records
                ),
                "serialized_writeback": True,
                "lane_distinct_batches": True,
            },
            "authority_split": {
                "workflow_surface": _delivery_surface(self.request.runtime_provider),
                "runtime_registry_authority": "host_runtime_wiring",
                "provider_executed": self.attempted_count > 0,
                "process_parallel_execution": any(
                    record.process_parallel_execution for record in self.records
                ),
                "serialized_writeback": True,
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

    request = replace(request, runtime_provider="codex")
    return _run_delivery_supervisor_once(request, runtime_client=codex_cli_client)


def run_opencode_delivery_supervisor_once(
    request: CodexDeliverySupervisorRequest,
    *,
    opencode_cli_client: OpenCodeCliClient,
) -> CodexDeliverySupervisorResult:
    """Run one bounded OpenCode delivery supervisor pass.

    This uses the same leader-worker delivery state machine as Codex while
    selecting the OpenCode runtime adapter, audit provider, and host grant.
    """

    request = replace(request, runtime_provider="opencode")
    return _run_delivery_supervisor_once(request, runtime_client=opencode_cli_client)


def _run_delivery_supervisor_once(
    request: CodexDeliverySupervisorRequest,
    *,
    runtime_client: CodexCliClient | OpenCodeCliClient,
) -> CodexDeliverySupervisorResult:
    provider = request.runtime_provider
    if provider not in {"codex", "opencode"}:
        raise ValueError(
            "leader-worker delivery supervisor supports runtime_provider "
            f"'codex' or 'opencode'; got {provider!r}"
        )
    if request.max_deliveries < 0:
        raise ValueError(
            f"{provider} delivery supervisor max_deliveries must be non-negative"
        )
    if request.max_concurrent_deliveries < 1:
        raise ValueError(
            f"{provider} delivery supervisor max_concurrent_deliveries must be positive"
        )
    if request.max_delivery_attempts_per_record < 1:
        raise ValueError(
            f"{provider} delivery supervisor max_delivery_attempts_per_record must be positive"
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
    opencode_has_explicit_session_selector = (
        provider == "opencode"
        and _opencode_client_has_explicit_session_selector(runtime_client)
    )
    audited_client: CodexCliClient | OpenCodeCliClient = runtime_client
    if invocation_log_path is not None:
        audited_client = _audited_runtime_client(
            provider=provider,
            inner=audited_client,
            log=JsonlRuntimeInvocationLog(invocation_log_path),
            retry_policy=retry_policy,
            host_invocation_id=request.host_invocation_id,
        )
    host_invocation = RuntimeHostInvocation(
        surface="host-authorized-adapter",
        invocation_id=request.host_invocation_id,
        requested_providers=(provider,),
        requested_by=request.requested_by,
        reason=request.reason,
    )
    grant = RuntimeProviderPermissionGrant(
        grant_id=request.grant_id,
        provider=provider,
        approved_by=request.approved_by,
        approved_at=request.approved_at or request.timestamp,
        scope=request.grant_scope,
        allow_process_spawn=True,
        allow_network=request.allow_network,
    )
    config_kwargs: dict[str, object] = {
        "providers": (provider,),
        "timestamp": request.timestamp,
        "host_invocation": host_invocation,
    }
    client_kwargs: dict[str, object] = {}
    if provider == "codex":
        config_kwargs["codex_permission_grant"] = grant
        client_kwargs["codex_cli_client"] = audited_client
    else:
        config_kwargs["opencode_permission_grant"] = grant
        config_kwargs["opencode_session_ledger_path"] = request.opencode_session_ledger_path
        config_kwargs["opencode_enable_session_lookup"] = (
            request.opencode_enable_session_lookup
            and not opencode_has_explicit_session_selector
        )
        config_kwargs["continuous_worker_binding_ledger_path"] = (
            request.continuous_worker_binding_ledger_path
        )
        config_kwargs["continuous_worker_context_bundle_dir_path"] = (
            request.continuous_worker_context_bundle_dir_path
        )
        config_kwargs["enable_continuous_worker_binding_lookup"] = (
            request.enable_continuous_worker_binding_lookup
            and not opencode_has_explicit_session_selector
        )
        client_kwargs["opencode_cli_client"] = audited_client
    wiring = build_runtime_registry_from_config(
        RuntimeRegistryWiringConfig(**config_kwargs),  # type: ignore[arg-type]
        **client_kwargs,  # type: ignore[arg-type]
    )
    runtime = wiring.registry.get(provider)
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
    prepared: list[_PreparedCodexDelivery] = []
    selected_lane_ids: set[str] = set()
    selected_worker_binding_ids: set[str] = set()
    batch_limit = min(request.max_deliveries, request.max_concurrent_deliveries)
    batch_id = f"{request.host_invocation_id}:batch-0001"
    for record in candidate_records:
        if len(prepared) >= request.max_deliveries:
            break
        if len(prepared) >= batch_limit:
            break
        task = recovery.recovered_state.tasks.get(record.task_id)
        skip_reason = _skip_reason_for_record(
            record,
            scheduler_state=recovery.recovered_state,
            task=task,
            runtime_provider=provider,
        )
        if skip_reason:
            result_records.append(_skipped_record(record, skip_reason))
            continue

        precondition_failure = _precondition_failure_for_record(
            record,
            scheduler_state=recovery.recovered_state,
            task=task,
            runtime_provider=provider,
        )
        if precondition_failure:
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
        lane_id = record.lane_id or task.context_scope.lane_id
        if request.max_concurrent_deliveries > 1:
            if lane_id in selected_lane_ids:
                continue
        worker_binding = (
            None
            if opencode_has_explicit_session_selector
            else _resolve_continuous_worker_binding_for_task(request, task)
        )
        worker_binding_id = "" if worker_binding is None else worker_binding.binding_id
        if worker_binding_id and not _continuous_worker_lane_ownership_allows_delivery(
            request,
            worker_binding_id,
            lane_id,
        ):
            continue
        if worker_binding_id and _continuous_worker_binding_has_active_delivery_lease(
            request,
            worker_binding_id,
        ):
            continue
        if request.max_concurrent_deliveries > 1 and worker_binding_id:
            if worker_binding_id in selected_worker_binding_ids:
                continue
        try:
            prepared_item = _prepare_codex_delivery(
                request=request,
                record=record,
                task=task,
                scheduler_state=recovery.recovered_state,
                sandbox_registry=sandbox_registry,
                batch_id=batch_id,
                batch_size=1,
                continuous_worker_binding_id=worker_binding_id,
                continuous_worker_id="" if worker_binding is None else worker_binding.worker_id,
            )
            if worker_binding_id:
                lease = _reserve_continuous_worker_delivery_lease(
                    request=request,
                    record=record,
                    task=task,
                    binding_id=worker_binding_id,
                )
                if lease is None:
                    continue
                prepared_item = replace(
                    prepared_item,
                    continuous_worker_delivery_lease_id=lease.lease_id,
                )
            prepared.append(prepared_item)
            if request.max_concurrent_deliveries > 1:
                selected_lane_ids.add(lane_id)
                if worker_binding_id:
                    selected_worker_binding_ids.add(worker_binding_id)
        except Exception as exc:
            result_records.append(
                _fail_delivery_record(
                    request=request,
                    record=record,
                    state_path=state_path,
                    delivery_log_path=delivery_log_path,
                    failure_kind="delivery_preparation_failed",
                    failure_detail=str(getattr(exc, "summary", "") or exc),
                    runtime_session_id=str(getattr(exc, "session_id", "")),
                    runtime_run_id=str(getattr(exc, "run_id", "")),
                    invocation_id="",
                    attempted=False,
                    retry_attempt=record.delivery_state == "failed",
                )
            )
    if prepared:
        observed_batch_size = len(prepared)
        prepared = [
            replace(item, batch_size=observed_batch_size)
            for item in prepared
        ]
        outcomes = _run_codex_runtime_delivery_batch(
            prepared,
            runtime=runtime,
            provider=provider,
            concurrent=request.max_concurrent_deliveries > 1 and observed_batch_size > 1,
        )
        for outcome in outcomes:
            result_records.append(
                _consume_codex_runtime_delivery_outcome(
                    request=request,
                    outcome=outcome,
                    state_path=state_path,
                    delivery_log_path=delivery_log_path,
                    scheduler_log_path=scheduler_log_path,
                    artifact_store_path=artifact_store_path,
                    scheduler_state=recovery.recovered_state,
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


def _prepare_codex_delivery(
    *,
    request: CodexDeliverySupervisorRequest,
    record: LeaderWorkerDeliveryRecord,
    task: ScheduledTask,
    scheduler_state: SchedulerState,
    sandbox_registry: SandboxProviderRegistry | None,
    batch_id: str,
    batch_size: int,
    continuous_worker_binding_id: str = "",
    continuous_worker_id: str = "",
    continuous_worker_delivery_lease_id: str = "",
) -> _PreparedCodexDelivery:
    runtime_task = task_to_runtime_spec(task)
    preflight: OrchestrationPreflightBundle | None = None
    if sandbox_registry is not None:
        preflight = build_orchestration_preflight_bundle(
            _ready_task_for_preflight(task),
            sandbox_registry=sandbox_registry,
            scheduler_state=scheduler_state,
            workspace_root=str(request.workspace_root),
            scratch_root=str(request.scratch_root),
            created_at=request.timestamp,
        )
        runtime_task = preflight.runtime_task
    return _PreparedCodexDelivery(
        record=record,
        task=task,
        runtime_task=runtime_task,
        preflight=preflight,
        retry_attempt=record.delivery_state == "failed",
        batch_id=batch_id,
        batch_size=batch_size,
        continuous_worker_binding_id=continuous_worker_binding_id,
        continuous_worker_id=continuous_worker_id,
        continuous_worker_delivery_lease_id=continuous_worker_delivery_lease_id,
        continuous_worker_delivery_lease_ledger_path=(
            request.continuous_worker_delivery_lease_ledger_path
        ),
        continuous_worker_delivery_lease_event_log_path=(
            request.continuous_worker_delivery_lease_event_log_path
        ),
        scheduler_event_log_path=request.scheduler_event_log_path,
        delivery_timestamp=request.timestamp,
    )


def _run_codex_runtime_delivery_batch(
    prepared: list[_PreparedCodexDelivery],
    *,
    runtime,
    provider: RuntimeProviderKind = "codex",
    concurrent: bool,
) -> tuple[_RuntimeDeliveryOutcome, ...]:
    if not concurrent:
        return tuple(
            _run_codex_runtime_delivery(item, runtime=runtime, provider=provider)
            for item in prepared
        )
    with ThreadPoolExecutor(max_workers=len(prepared)) as executor:
        futures = [
            executor.submit(_run_codex_runtime_delivery, item, runtime=runtime, provider=provider)
            for item in prepared
        ]
        return tuple(future.result() for future in futures)


def _run_codex_runtime_delivery(
    prepared: _PreparedCodexDelivery,
    *,
    runtime,
    provider: RuntimeProviderKind = "codex",
) -> _RuntimeDeliveryOutcome:
    session = None
    invocation_id = ""
    try:
        session = runtime.start_session(prepared.task.agent)
        invocation_id = _runtime_invocation_id(
            prepared.batch_id.rsplit(":batch-", 1)[0],
            session.session_id,
            prepared.task.task_id,
            provider=provider,
        )
        _begin_continuous_worker_delivery_lease(
            prepared=prepared,
            invocation_id=invocation_id,
        )
        run_result = runtime.run_task(session, prepared.runtime_task)
    except Exception as exc:
        return _RuntimeDeliveryOutcome(
            prepared=prepared,
            session_id=str(
                getattr(exc, "session_id", "")
                or (session.session_id if session is not None else "")
            ),
            run_id=str(getattr(exc, "run_id", "")),
            invocation_id=invocation_id,
            failure_kind=str(getattr(exc, "error_kind", "") or type(exc).__name__),
            failure_detail=str(getattr(exc, "summary", "") or exc),
            raw_error_type=str(getattr(exc, "raw_error_type", "") or type(exc).__name__),
            retryable=bool(getattr(exc, "retryable", False)),
        )
    return _RuntimeDeliveryOutcome(
        prepared=prepared,
        session_id=run_result.run_handle.session_id,
        run_id=run_result.run_handle.run_id,
        invocation_id=invocation_id,
        run_result=run_result,
    )


def _consume_codex_runtime_delivery_outcome(
    *,
    request: CodexDeliverySupervisorRequest,
    outcome: _RuntimeDeliveryOutcome,
    state_path: Path,
    delivery_log_path: Path,
    scheduler_log_path: Path,
    artifact_store_path: Path | None,
    scheduler_state: SchedulerState,
) -> CodexDeliverySupervisorRecord:
    prepared = outcome.prepared
    record = prepared.record
    task = prepared.task
    retry_attempt = prepared.retry_attempt
    run_result = outcome.run_result
    process_parallel = prepared.batch_size > 1
    if run_result is None:
        _fail_continuous_worker_delivery_lease(
            prepared=prepared,
            outcome=outcome,
        )
        _mark_continuous_worker_binding_after_failure(
            request=request,
            prepared=prepared,
            outcome=outcome,
        )
        return replace(
            _fail_delivery_record(
                request=request,
                record=record,
                state_path=state_path,
                delivery_log_path=delivery_log_path,
                failure_kind=outcome.failure_kind,
                failure_detail=outcome.failure_detail,
                runtime_session_id=outcome.session_id,
                runtime_run_id=outcome.run_id,
                invocation_id=outcome.invocation_id,
                attempted=True,
                retry_attempt=retry_attempt,
            ),
            concurrent_batch_id=prepared.batch_id,
            concurrent_batch_size=prepared.batch_size,
            process_parallel_execution=process_parallel,
        )

    _complete_continuous_worker_delivery_lease(
        prepared=prepared,
        outcome=outcome,
    )
    _record_continuous_worker_binding_after_success(
        request=request,
        prepared=prepared,
        outcome=outcome,
    )

    result_consumption: CodexResultConsumerResult | None = None
    permission_review: CodexPermissionReviewConsumerResult | None = None
    if run_result.permission_requests:
        if artifact_store_path is None:
            return replace(
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
                    invocation_id=outcome.invocation_id,
                    attempted=True,
                    retry_attempt=retry_attempt,
                ),
                concurrent_batch_id=prepared.batch_id,
                concurrent_batch_size=prepared.batch_size,
                process_parallel_execution=process_parallel,
            )
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
            return replace(
                _fail_delivery_record(
                    request=request,
                    record=record,
                    state_path=state_path,
                    delivery_log_path=delivery_log_path,
                    failure_kind="permission_review_consumer_failed",
                    failure_detail=str(exc),
                    runtime_session_id=run_result.run_handle.session_id,
                    runtime_run_id=run_result.run_handle.run_id,
                    invocation_id=outcome.invocation_id,
                    attempted=True,
                    retry_attempt=retry_attempt,
                ),
                concurrent_batch_id=prepared.batch_id,
                concurrent_batch_size=prepared.batch_size,
                process_parallel_execution=process_parallel,
            )
        review_ack = acknowledge_leader_worker_delivery(
            LeaderWorkerDeliveryAckRequest(
                delivery_state_path=state_path,
                delivery_event_log_path=delivery_log_path,
                source_key=record.source_key,
                target_state="review_required",
                timestamp=request.timestamp,
                host_id=request.host_id,
                runtime_provider=request.runtime_provider,
                runtime_session_id=run_result.run_handle.session_id,
                runtime_run_id=run_result.run_handle.run_id,
                invocation_id=outcome.invocation_id,
                metadata=_ack_metadata(
                    request,
                    record,
                    run_result=run_result,
                    permission_review=permission_review,
                ),
            )
        )
        return CodexDeliverySupervisorRecord(
            source_key=record.source_key,
            delivery_record_id=record.delivery_id,
            task_id=record.task_id,
            agent_id=record.agent_id,
            status="review_required",
            attempted=True,
            runtime_session_id=run_result.run_handle.session_id,
            runtime_run_id=run_result.run_handle.run_id,
            invocation_id=outcome.invocation_id,
            output_artifact_id=run_result.output_artifact.artifact_id,
            output_artifact_version=run_result.output_artifact.version,
            permission_review=permission_review,
            permission_requests=tuple(run_result.permission_requests),
            delivery_acknowledgement=review_ack,
            retry_attempt=retry_attempt,
            concurrent_batch_id=prepared.batch_id,
            concurrent_batch_size=prepared.batch_size,
            process_parallel_execution=process_parallel,
        )

    worker_patch_review: CodexDeliveryWorkerPatchReviewPublication | None = None
    try:
        worker_patch_review = _publish_worker_patch_review_artifact(
            request=request,
            artifact_store_path=artifact_store_path,
            task=task,
            scheduler_state=scheduler_state,
            preflight=prepared.preflight,
            run_result=run_result,
        )
    except Exception as exc:
        return replace(
            _fail_delivery_record(
                request=request,
                record=record,
                state_path=state_path,
                delivery_log_path=delivery_log_path,
                failure_kind="worker_patch_review_publish_failed",
                failure_detail=str(exc),
                runtime_session_id=run_result.run_handle.session_id,
                runtime_run_id=run_result.run_handle.run_id,
                invocation_id=outcome.invocation_id,
                attempted=True,
                retry_attempt=retry_attempt,
            ),
            concurrent_batch_id=prepared.batch_id,
            concurrent_batch_size=prepared.batch_size,
            process_parallel_execution=process_parallel,
        )

    if request.consume_success_results:
        if artifact_store_path is None:
            return replace(
                _fail_delivery_record(
                    request=request,
                    record=record,
                    state_path=state_path,
                    delivery_log_path=delivery_log_path,
                    failure_kind="result_consumer_failed",
                    failure_detail=(
                        "consume_success_results requires artifact_store_path "
                        f"so the {request.runtime_provider} output artifact can be stored durably"
                    ),
                    runtime_session_id=run_result.run_handle.session_id,
                    runtime_run_id=run_result.run_handle.run_id,
                    invocation_id=outcome.invocation_id,
                    attempted=True,
                    retry_attempt=retry_attempt,
                ),
                concurrent_batch_id=prepared.batch_id,
                concurrent_batch_size=prepared.batch_size,
                process_parallel_execution=process_parallel,
            )
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
            return replace(
                _fail_delivery_record(
                    request=request,
                    record=record,
                    state_path=state_path,
                    delivery_log_path=delivery_log_path,
                    failure_kind="result_consumer_failed",
                    failure_detail=str(exc),
                    runtime_session_id=run_result.run_handle.session_id,
                    runtime_run_id=run_result.run_handle.run_id,
                    invocation_id=outcome.invocation_id,
                    attempted=True,
                    retry_attempt=retry_attempt,
                ),
                concurrent_batch_id=prepared.batch_id,
                concurrent_batch_size=prepared.batch_size,
                process_parallel_execution=process_parallel,
            )

    success_ack = acknowledge_leader_worker_delivery(
        LeaderWorkerDeliveryAckRequest(
            delivery_state_path=state_path,
            delivery_event_log_path=delivery_log_path,
            source_key=record.source_key,
            target_state="acknowledged",
            timestamp=request.timestamp,
            host_id=request.host_id,
            runtime_provider=request.runtime_provider,
            runtime_session_id=run_result.run_handle.session_id,
            runtime_run_id=run_result.run_handle.run_id,
            invocation_id=outcome.invocation_id,
            metadata=_ack_metadata(
                request,
                record,
                run_result=run_result,
                result_consumption=result_consumption,
                worker_patch_review=worker_patch_review,
            ),
        )
    )
    return CodexDeliverySupervisorRecord(
        source_key=record.source_key,
        delivery_record_id=record.delivery_id,
        task_id=record.task_id,
        agent_id=record.agent_id,
        status="acknowledged",
        attempted=True,
        runtime_session_id=run_result.run_handle.session_id,
        runtime_run_id=run_result.run_handle.run_id,
        invocation_id=outcome.invocation_id,
        output_artifact_id=run_result.output_artifact.artifact_id,
        output_artifact_version=run_result.output_artifact.version,
        result_consumption=result_consumption,
        worker_patch_review=worker_patch_review,
        permission_requests=tuple(run_result.permission_requests),
        delivery_acknowledgement=success_ack,
        retry_attempt=retry_attempt,
        concurrent_batch_id=prepared.batch_id,
        concurrent_batch_size=prepared.batch_size,
        process_parallel_execution=process_parallel,
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
            runtime_surface=_delivery_surface("codex"),
            metadata={
                "host_invocation_id": self.host_invocation_id,
                "lane_id": request.task.scope.lane_id,
                "context_id": request.task.scope.context_id,
                "run_id_available_at_client_seam": False,
            },
        )


class _AuditedOpenCodeCliClient:
    """Host-owned audit/retry wrapper around the OpenCode CLI client seam."""

    def __init__(
        self,
        *,
        inner: OpenCodeCliClient,
        log: JsonlRuntimeInvocationLog,
        retry_policy: RuntimeRetryPolicy,
        host_invocation_id: str,
    ) -> None:
        self.inner = inner
        self.log = log
        self.retry_policy = retry_policy
        self.host_invocation_id = host_invocation_id

    def exec(self, request: OpenCodeCliRequest) -> OpenCodeCliResult:
        host_session = request.host_session
        selector_source = _opencode_client_session_selector_source(self.inner, request)
        return run_with_runtime_invocation_audit(
            invocation_id=_runtime_invocation_id(
                self.host_invocation_id,
                request.session.session_id,
                request.task.task_id,
                provider="opencode",
            ),
            provider="opencode",
            operation=lambda: self.inner.exec(request),
            log=self.log,
            retry_policy=self.retry_policy,
            task_id=request.task.task_id,
            session_id=request.session.session_id,
            agent_id=request.agent.agent_id,
            runtime_surface=_delivery_surface("opencode"),
            metadata={
                "host_invocation_id": self.host_invocation_id,
                "lane_id": request.task.scope.lane_id,
                "context_id": request.task.scope.context_id,
                "session_selector_source": selector_source,
                "opencode_session_binding_id": (
                    "" if host_session is None else host_session.binding_id
                ),
                "opencode_session_scope_kind": (
                    "" if host_session is None else host_session.scope_kind
                ),
                "opencode_session_scope_id": (
                    "" if host_session is None else host_session.scope_id
                ),
                "continuous_worker_binding_id": (
                    "" if host_session is None else host_session.worker_binding_id
                ),
                "continuous_worker_id": (
                    "" if host_session is None else host_session.worker_id
                ),
                "continuous_worker_scope_kind": (
                    "" if host_session is None else host_session.worker_scope_kind
                ),
                "continuous_worker_scope_id": (
                    "" if host_session is None else host_session.worker_scope_id
                ),
                "continuous_worker_lane_ids": (
                    [] if host_session is None else list(host_session.worker_lane_ids)
                ),
                "continuous_worker_compact_context_ref": (
                    "" if host_session is None else host_session.compact_context_ref
                ),
                "continuous_worker_mailbox_cursor_ref": (
                    "" if host_session is None else host_session.mailbox_cursor_ref
                ),
                "continuous_worker_report_refs": (
                    [] if host_session is None else list(host_session.worker_report_refs)
                ),
                "continuous_worker_audit_refs": (
                    [] if host_session is None else list(host_session.audit_refs)
                ),
                "opencode_attached_to_server": (
                    False if host_session is None else bool(host_session.attach_url)
                ),
                "run_id_available_at_client_seam": False,
            },
        )


def _audited_runtime_client(
    *,
    provider: RuntimeProviderKind,
    inner: CodexCliClient | OpenCodeCliClient,
    log: JsonlRuntimeInvocationLog,
    retry_policy: RuntimeRetryPolicy,
    host_invocation_id: str,
) -> CodexCliClient | OpenCodeCliClient:
    if provider == "codex":
        return _AuditedCodexCliClient(
            inner=inner,  # type: ignore[arg-type]
            log=log,
            retry_policy=retry_policy,
            host_invocation_id=host_invocation_id,
        )
    if provider == "opencode":
        return _AuditedOpenCodeCliClient(
            inner=inner,  # type: ignore[arg-type]
            log=log,
            retry_policy=retry_policy,
            host_invocation_id=host_invocation_id,
        )
    raise ValueError(f"unsupported audited runtime provider: {provider!r}")


def _opencode_client_has_explicit_session_selector(
    client: CodexCliClient | OpenCodeCliClient,
) -> bool:
    config = getattr(client, "config", None)
    if config is None:
        inner = getattr(client, "inner", None)
        if inner is not None:
            return _opencode_client_has_explicit_session_selector(inner)
        return False
    return bool(
        getattr(config, "attach_url", "")
        or getattr(config, "session_id", "")
        or getattr(config, "continue_session", False)
        or getattr(config, "fork_session", False)
    )


def _opencode_client_session_selector_source(
    client: OpenCodeCliClient,
    request: OpenCodeCliRequest,
) -> str:
    if _opencode_client_has_explicit_session_selector(client):
        return "explicit_config"
    if request.host_session is not None:
        return request.host_session.selector_source or "session_ledger"
    return "none"


def _resolve_continuous_worker_binding_for_task(
    request: CodexDeliverySupervisorRequest,
    task: ScheduledTask,
):
    if (
        request.runtime_provider != "opencode"
        or not request.enable_continuous_worker_binding_lookup
    ):
        return None
    from .continuous_worker_binding import (
        ContinuousWorkerBindingResolveRequest,
        resolve_continuous_worker_binding,
    )

    result = resolve_continuous_worker_binding(
        ContinuousWorkerBindingResolveRequest(
            ledger_path=request.continuous_worker_binding_ledger_path,
            runtime_provider="opencode",
            task_id=task.task_id,
            agent_id=task.agent.agent_id,
            lane_id=task.context_scope.lane_id,
            timestamp=request.timestamp,
        )
    )
    return result.binding


def _continuous_worker_binding_has_active_delivery_lease(
    request: CodexDeliverySupervisorRequest,
    binding_id: str,
) -> bool:
    if (
        request.runtime_provider != "opencode"
        or not request.enable_continuous_worker_binding_lookup
        or not binding_id
    ):
        return False
    from .continuous_worker_binding import binding_has_active_delivery_lease

    return binding_has_active_delivery_lease(
        request.continuous_worker_delivery_lease_ledger_path,
        binding_id,
    )


def _continuous_worker_lane_ownership_allows_delivery(
    request: CodexDeliverySupervisorRequest,
    binding_id: str,
    lane_id: str,
) -> bool:
    if (
        request.runtime_provider != "opencode"
        or not request.enable_continuous_worker_binding_lookup
        or not binding_id
        or not lane_id
    ):
        return True
    from .continuous_worker_binding import lane_ownership_allows_delivery

    return lane_ownership_allows_delivery(
        request.continuous_worker_lane_ownership_ledger_path,
        binding_id=binding_id,
        lane_id=lane_id,
    )


def _reserve_continuous_worker_delivery_lease(
    *,
    request: CodexDeliverySupervisorRequest,
    record: LeaderWorkerDeliveryRecord,
    task: ScheduledTask,
    binding_id: str,
):
    if (
        request.runtime_provider != "opencode"
        or not request.enable_continuous_worker_binding_lookup
        or not binding_id
    ):
        return None
    from .continuous_worker_binding import (
        DeliveryLeaseReserveRequest,
        reserve_delivery_lease,
    )

    result = reserve_delivery_lease(
        DeliveryLeaseReserveRequest(
            ledger_path=request.continuous_worker_delivery_lease_ledger_path,
            event_log_path=request.continuous_worker_delivery_lease_event_log_path,
            binding_id=binding_id,
            task_id=task.task_id,
            delivery_id=record.delivery_id,
            reserved_at=request.timestamp,
            reason="continuous worker binding selected for delivery",
            audit_refs=(request.host_invocation_id,),
            metadata={
                "host_invocation_id": request.host_invocation_id,
                "source_key": record.source_key,
                "lane_id": task.context_scope.lane_id,
                "agent_id": task.agent.agent_id,
            },
        )
    )
    if result.ok and result.lease is not None:
        _append_continuous_worker_scheduler_audit_event(
            request.scheduler_event_log_path,
            event_kind="continuous_worker_delivery_lease_reserved",
            timestamp=request.timestamp,
            task_id=task.task_id,
            reason="continuous worker delivery lease reserved",
            binding_id=binding_id,
            worker_id="",
            lane_id=task.context_scope.lane_id,
            delivery_id=record.delivery_id,
            lease_id=result.lease.lease_id,
            invocation_id="",
            metadata={
                "host_invocation_id": request.host_invocation_id,
                "agent_id": task.agent.agent_id,
                "source_key": record.source_key,
            },
        )
    return result.lease if result.ok else None


def _begin_continuous_worker_delivery_lease(
    *,
    prepared: _PreparedCodexDelivery,
    invocation_id: str,
) -> None:
    if not prepared.continuous_worker_delivery_lease_id:
        return
    from .continuous_worker_binding import (
        DeliveryLeaseBeginRequest,
        begin_delivery_lease_run,
    )

    result = begin_delivery_lease_run(
        DeliveryLeaseBeginRequest(
            ledger_path=prepared.continuous_worker_delivery_lease_ledger_path,
            event_log_path=prepared.continuous_worker_delivery_lease_event_log_path,
            lease_id=prepared.continuous_worker_delivery_lease_id,
            binding_id=prepared.continuous_worker_binding_id,
            started_at=prepared.delivery_timestamp,
            audit_refs=(invocation_id,) if invocation_id else (),
            metadata={
                "invocation_id": invocation_id,
                "task_id": prepared.task.task_id,
                "delivery_record_id": prepared.record.delivery_id,
            },
        )
    )
    if not result.ok:
        raise RuntimeError(result.message)
    _append_continuous_worker_scheduler_audit_event(
        prepared.scheduler_event_log_path,
        event_kind="continuous_worker_delivery_lease_started",
        timestamp=prepared.delivery_timestamp,
        task_id=prepared.task.task_id,
        reason="continuous worker delivery lease run started",
        binding_id=prepared.continuous_worker_binding_id,
        worker_id=prepared.continuous_worker_id,
        lane_id=prepared.task.context_scope.lane_id,
        delivery_id=prepared.record.delivery_id,
        lease_id=prepared.continuous_worker_delivery_lease_id,
        invocation_id=invocation_id,
        metadata={
            "agent_id": prepared.task.agent.agent_id,
            "source_key": prepared.record.source_key,
        },
    )


def _complete_continuous_worker_delivery_lease(
    *,
    prepared: _PreparedCodexDelivery,
    outcome: _RuntimeDeliveryOutcome,
) -> None:
    if not prepared.continuous_worker_delivery_lease_id:
        return
    from .continuous_worker_binding import (
        DeliveryLeaseCompleteRequest,
        complete_delivery_lease,
    )

    complete_delivery_lease(
        DeliveryLeaseCompleteRequest(
            ledger_path=prepared.continuous_worker_delivery_lease_ledger_path,
            event_log_path=prepared.continuous_worker_delivery_lease_event_log_path,
            lease_id=prepared.continuous_worker_delivery_lease_id,
            binding_id=prepared.continuous_worker_binding_id,
            completed_at=prepared.delivery_timestamp,
            result_ref=outcome.invocation_id,
            audit_refs=(outcome.invocation_id,) if outcome.invocation_id else (),
            metadata={
                "runtime_session_id": outcome.session_id,
                "runtime_run_id": outcome.run_id,
                "delivery_record_id": prepared.record.delivery_id,
                "task_id": prepared.task.task_id,
            },
        )
    )
    _append_continuous_worker_scheduler_audit_event(
        prepared.scheduler_event_log_path,
        event_kind="continuous_worker_delivery_lease_completed",
        timestamp=prepared.delivery_timestamp,
        task_id=prepared.task.task_id,
        reason="continuous worker delivery lease completed",
        binding_id=prepared.continuous_worker_binding_id,
        worker_id=prepared.continuous_worker_id,
        lane_id=prepared.task.context_scope.lane_id,
        delivery_id=prepared.record.delivery_id,
        lease_id=prepared.continuous_worker_delivery_lease_id,
        invocation_id=outcome.invocation_id,
        metadata={
            "runtime_session_id": outcome.session_id,
            "runtime_run_id": outcome.run_id,
            "agent_id": prepared.task.agent.agent_id,
        },
    )


def _fail_continuous_worker_delivery_lease(
    *,
    prepared: _PreparedCodexDelivery,
    outcome: _RuntimeDeliveryOutcome,
) -> None:
    if not prepared.continuous_worker_delivery_lease_id:
        return
    from .continuous_worker_binding import (
        DeliveryLeaseFailRequest,
        fail_delivery_lease_retryable,
        fail_delivery_lease_terminal,
    )

    fail_request = DeliveryLeaseFailRequest(
        ledger_path=prepared.continuous_worker_delivery_lease_ledger_path,
        event_log_path=prepared.continuous_worker_delivery_lease_event_log_path,
        lease_id=prepared.continuous_worker_delivery_lease_id,
        binding_id=prepared.continuous_worker_binding_id,
        failed_at=prepared.delivery_timestamp,
        failure_kind=outcome.failure_kind or "unknown",
        result_ref=outcome.invocation_id,
        audit_refs=(outcome.invocation_id,) if outcome.invocation_id else (),
        metadata={
            "retryable": outcome.retryable,
            "raw_error_type": outcome.raw_error_type,
            "runtime_session_id": outcome.session_id,
            "runtime_run_id": outcome.run_id,
            "delivery_record_id": prepared.record.delivery_id,
            "task_id": prepared.task.task_id,
        },
    )
    if outcome.retryable:
        fail_delivery_lease_retryable(fail_request)
    else:
        fail_delivery_lease_terminal(fail_request)
    _append_continuous_worker_scheduler_audit_event(
        prepared.scheduler_event_log_path,
        event_kind="continuous_worker_delivery_lease_failed",
        timestamp=prepared.delivery_timestamp,
        task_id=prepared.task.task_id,
        reason=outcome.failure_kind or "continuous worker delivery lease failed",
        binding_id=prepared.continuous_worker_binding_id,
        worker_id=prepared.continuous_worker_id,
        lane_id=prepared.task.context_scope.lane_id,
        delivery_id=prepared.record.delivery_id,
        lease_id=prepared.continuous_worker_delivery_lease_id,
        invocation_id=outcome.invocation_id,
        metadata={
            "runtime_session_id": outcome.session_id,
            "runtime_run_id": outcome.run_id,
            "agent_id": prepared.task.agent.agent_id,
            "retryable": outcome.retryable,
        },
    )


def _record_continuous_worker_binding_after_success(
    *,
    request: CodexDeliverySupervisorRequest,
    prepared: _PreparedCodexDelivery,
    outcome: _RuntimeDeliveryOutcome,
) -> None:
    if request.runtime_provider != "opencode" or not prepared.continuous_worker_binding_id:
        return
    from .continuous_worker_binding import (
        ContinuousWorkerBindingReuseRequest,
        record_continuous_worker_binding_reuse,
    )

    record_continuous_worker_binding_reuse(
        ContinuousWorkerBindingReuseRequest(
            ledger_path=request.continuous_worker_binding_ledger_path,
            event_log_path=request.continuous_worker_binding_event_log_path,
            binding_id=prepared.continuous_worker_binding_id,
            task_id=prepared.task.task_id,
            agent_id=prepared.task.agent.agent_id,
            lane_id=prepared.task.context_scope.lane_id,
            timestamp=request.timestamp,
            audit_refs=(outcome.invocation_id,) if outcome.invocation_id else (),
            metadata={
                "runtime_session_id": outcome.session_id,
                "runtime_run_id": outcome.run_id,
                "delivery_record_id": prepared.record.delivery_id,
                "source_key": prepared.record.source_key,
            },
        )
    )
    _append_continuous_worker_scheduler_audit_event(
        request.scheduler_event_log_path,
        event_kind="continuous_worker_binding_reused",
        timestamp=request.timestamp,
        task_id=prepared.task.task_id,
        reason="continuous worker binding reused after successful delivery",
        binding_id=prepared.continuous_worker_binding_id,
        worker_id=prepared.continuous_worker_id,
        lane_id=prepared.task.context_scope.lane_id,
        delivery_id=prepared.record.delivery_id,
        lease_id=prepared.continuous_worker_delivery_lease_id,
        invocation_id=outcome.invocation_id,
        metadata={
            "runtime_session_id": outcome.session_id,
            "runtime_run_id": outcome.run_id,
            "agent_id": prepared.task.agent.agent_id,
            "source_key": prepared.record.source_key,
        },
    )


def _mark_continuous_worker_binding_after_failure(
    *,
    request: CodexDeliverySupervisorRequest,
    prepared: _PreparedCodexDelivery,
    outcome: _RuntimeDeliveryOutcome,
) -> None:
    if request.runtime_provider != "opencode" or not prepared.continuous_worker_binding_id:
        return
    if not _failure_may_invalidate_continuous_worker_binding(outcome):
        return
    from .continuous_worker_binding import (
        ContinuousWorkerBindingReleaseRequest,
        release_continuous_worker_binding,
    )

    release_continuous_worker_binding(
        ContinuousWorkerBindingReleaseRequest(
            ledger_path=request.continuous_worker_binding_ledger_path,
            event_log_path=request.continuous_worker_binding_event_log_path,
            binding_id=prepared.continuous_worker_binding_id,
            lifecycle_status="stale",
            timestamp=request.timestamp,
            reason=(
                "runtime delivery failed through continuous worker binding: "
                f"{outcome.failure_kind}"
            ),
        )
    )


def _failure_may_invalidate_continuous_worker_binding(
    outcome: _RuntimeDeliveryOutcome,
) -> bool:
    return outcome.retryable or outcome.failure_kind in {
        "timeout",
        "process_failed",
        "cli_unavailable",
        "authentication_failed",
        "unknown",
    }


def _append_continuous_worker_scheduler_audit_event(
    path: str | Path,
    *,
    event_kind: str,
    timestamp: str,
    task_id: str,
    reason: str,
    binding_id: str,
    worker_id: str,
    lane_id: str,
    delivery_id: str,
    lease_id: str,
    invocation_id: str,
    metadata: Mapping[str, object] | None = None,
) -> None:
    if not path:
        return
    JsonlSchedulerEventLog(path).append(
        SchedulerEvent(
            event_id=_scheduler_audit_event_id(
                event_kind,
                task_id,
                binding_id,
                lease_id,
                invocation_id,
            ),
            event_kind=event_kind,  # type: ignore[arg-type]
            timestamp=timestamp,
            task_id=task_id,
            reason=reason,
            run_id=invocation_id,
            related_artifact_ids=_unique_nonempty(
                (binding_id, lease_id, delivery_id, invocation_id)
            ),
            lease_id=lease_id,
            metadata={
                "audit_only": True,
                "audit_source": "continuous_worker_delivery",
                "binding_id": binding_id,
                "worker_id": worker_id,
                "lane_id": lane_id,
                "delivery_id": delivery_id,
                "lease_id": lease_id,
                "invocation_id": invocation_id,
                **dict(metadata or {}),
            },
        )
    )


def _scheduler_audit_event_id(
    event_kind: str,
    task_id: str,
    binding_id: str,
    lease_id: str,
    invocation_id: str,
) -> str:
    discriminator = invocation_id or lease_id or binding_id or task_id
    return "scheduler-audit:{kind}:{task}:{discriminator}".format(
        kind=_safe_id(event_kind),
        task=_safe_id(task_id),
        discriminator=_safe_id(discriminator),
    )


def _safe_id(value: str) -> str:
    return value.replace("\\", "/").strip("/").replace("/", "-").replace(":", "-")


def _unique_nonempty(values: tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in values:
        if value and value not in normalized:
            normalized.append(value)
    return tuple(normalized)


def _skip_reason_for_record(
    record: LeaderWorkerDeliveryRecord,
    *,
    scheduler_state: SchedulerState,
    task: ScheduledTask | None,
    runtime_provider: RuntimeProviderKind = "codex",
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
    if task.agent.runtime_provider != runtime_provider:
        return (
            f"task runtime provider is {task.agent.runtime_provider!r}, "
            f"not {runtime_provider!r}"
        )
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
    runtime_provider: RuntimeProviderKind = "codex",
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
    return f"task is not ready for {runtime_provider} delivery: {task.state}"


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
            runtime_provider=request.runtime_provider,
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
        "runner": _delivery_surface(request.runtime_provider),
        "runtime_provider": request.runtime_provider,
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
        "max_concurrent_deliveries": request.max_concurrent_deliveries,
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
    *,
    provider: RuntimeProviderKind = "codex",
) -> str:
    return ":".join(
        part
        for part in (
            f"{provider}-delivery",
            host_invocation_id,
            session_id,
            task_id,
        )
        if part
    )


def _delivery_surface(provider: RuntimeProviderKind) -> str:
    return f"host-owned-{provider}-delivery-supervisor-once"


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


ProviderDeliveryWorkerPatchReviewPublication = CodexDeliveryWorkerPatchReviewPublication
ProviderDeliverySupervisorRecord = CodexDeliverySupervisorRecord
ProviderDeliverySupervisorRecordStatus = CodexDeliverySupervisorRecordStatus
ProviderDeliverySupervisorRequest = CodexDeliverySupervisorRequest
ProviderDeliverySupervisorResult = CodexDeliverySupervisorResult
run_provider_delivery_supervisor_once_for_codex = run_codex_delivery_supervisor_once
run_provider_delivery_supervisor_once_for_opencode = run_opencode_delivery_supervisor_once


__all__ = [
    "CodexDeliveryWorkerPatchReviewPublication",
    "CodexDeliverySupervisorRecord",
    "CodexDeliverySupervisorRecordStatus",
    "CodexDeliverySupervisorRequest",
    "CodexDeliverySupervisorResult",
    "ProviderDeliveryWorkerPatchReviewPublication",
    "ProviderDeliverySupervisorRecord",
    "ProviderDeliverySupervisorRecordStatus",
    "ProviderDeliverySupervisorRequest",
    "ProviderDeliverySupervisorResult",
    "run_codex_delivery_supervisor_once",
    "run_opencode_delivery_supervisor_once",
    "run_provider_delivery_supervisor_once_for_codex",
    "run_provider_delivery_supervisor_once_for_opencode",
]
