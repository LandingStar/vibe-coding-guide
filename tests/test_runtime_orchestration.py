"""Targeted tests for orchestration runtime models."""

from __future__ import annotations

import asyncio
import json
import shutil
import subprocess
import threading
import time
import urllib.error
from dataclasses import replace
from pathlib import Path

import pytest

from src.runtime.orchestration import (
    BridgeGroupItem,
    BridgeWorkItem,
    CoordinationEvent,
    AgentSpec,
    AgentHomeRegistration,
    AgentMailboxCursor,
    AgentScratchSpace,
    ArtifactDelta,
    ArtifactVersionRecord,
    CodexCliAgentRuntimeAdapter,
    CodexCliClientConfig,
    CodexCliProcessClient,
    CodexCliRequest,
    CodexCliResult,
    CodexCliRuntimeError,
    CleanupReceipt,
    ContextScope,
    CodexResultConsumerRequest,
    EditLeaseLifecycleRecord,
    EditScopeLease,
    ExchangeArtifact,
    ExchangeCausality,
    ExchangeContract,
    ExchangeLog,
    ExchangePayloadPart,
    ExchangeReference,
    ExchangeRelation,
    ExchangeScope,
    ExchangeArtifactAdmissionRecord,
    GitWorktreeCommandReceipt,
    GitWorktreeSandboxProvider,
    GitWorktreeSandboxReceipt,
    HostSchedulerRunRequest,
    AgentRuntimeAdapterRegistry,
    FakeAgentRuntimeAdapter,
    HostSchedulerRunEvidence,
    HostSchedulerRunEvidenceSummary,
    HostSchedulerRunResult,
    InMemoryArtifactVersionStore,
    JsonArtifactVersionStore,
    JsonExchangeArtifactAdmissionLedger,
    JsonlCoordinationEventLog,
    JsonlLeaderWorkerDeliveryEventLog,
    JsonlLeaderWorkerDispatcherEventLog,
    JsonlRuntimeInvocationLog,
    JsonlSchedulerEventLog,
    JsonlSchedulerMergeGateEventLog,
    LeaderWorkerActivationState,
    LeaderWorkerDeliveryAckRequest,
    LeaderWorkerDeliverySyncRequest,
    CodexDeliverySupervisorRequest,
    CodexDeliveryBoundedLoopRequest,
    CodexDeliveryE2ESmokeRequest,
    ProviderDeliverySupervisorRecord,
    ProviderDeliverySupervisorRequest,
    ProviderDeliverySupervisorResult,
    ProviderDeliveryBoundedLoopRequest,
    ProviderDeliveryE2ESmokeRequest,
    LiveCodexConcurrentWorkerSmokeRequest,
    LiveOpenCodeConcurrentWorkerSmokeRequest,
    MonitoringSnapshotRequest,
    CodexRuntimeStatusRequest,
    OpenCodeRuntimeStatusRequest,
    CodexCliHostReadinessReport,
    OpenCodeCliAgentRuntimeAdapter,
    OpenCodeCliClientConfig,
    OpenCodeHostSessionSelector,
    OpenCodeCliProcessClient,
    OpenCodeCliRequest,
    OpenCodeCliResult,
    OpenCodeCliRuntimeError,
    OpenCodeCliHostReadinessReport,
    OpenCodeServerApiClient,
    OpenCodeServerApiClientConfig,
    OpenCodeServeLifecycleInspectRequest,
    OpenCodeServeLifecycleRecordRequest,
    OpenCodeServeReadinessRequest,
    OpenCodeSessionClaimRequest,
    OpenCodeSessionInspectRequest,
    OpenCodeSessionRecoverStaleRequest,
    OpenCodeSessionReleaseRequest,
    ContinuousWorkerBindingClaimRequest,
    ContinuousWorkerBindingCompactRequest,
    ContinuousWorkerBindingForkRequest,
    ContinuousWorkerBindingInspectRequest,
    ContinuousWorkerBindingRecoverStaleRequest,
    ContinuousWorkerBindingReleaseRequest,
    ContinuousWorkerBindingResolveRequest,
    ContinuousWorkerBindingReuseRequest,
    ContinuousWorkerBinding,
    ContinuousWorkerCompactContextBuildRequest,
    ContinuousWorkerSessionSelector,
    ServerApiCreatedSessionPromotionRequest,
    WorkerBindingPromotionCandidateReadbackRequest,
    DeliveryLease,
    DeliveryLeaseBeginRequest,
    DeliveryLeaseCompleteRequest,
    DeliveryLeaseFailRequest,
    DeliveryLeaseInspectRequest,
    DeliveryLeaseReleaseRequest,
    DeliveryLeaseReserveRequest,
    JsonlDeliveryLeaseEventLog,
    JsonlContinuousWorkerBindingEventLog,
    JsonlLaneOwnershipEventLog,
    LaneOwnership,
    LaneOwnershipActivateRequest,
    LaneOwnershipClaimRequest,
    LaneOwnershipInspectRequest,
    LaneOwnershipReleaseRequest,
    LaneOwnershipResumeRequest,
    LaneOwnershipSuspendRequest,
    LaneOwnershipTransferRequest,
    active_delivery_lease_conflicts,
    activate_lane_ownership,
    begin_delivery_lease_run,
    build_continuous_worker_compact_context_bundle,
    claim_continuous_worker_binding,
    claim_lane_ownership,
    compact_continuous_worker_binding,
    complete_delivery_lease,
    continuous_worker_binding_from_json_dict,
    delivery_lease_from_json_dict,
    fail_delivery_lease_retryable,
    fork_continuous_worker_binding,
    inspect_delivery_leases,
    inspect_lane_ownerships,
    inspect_continuous_worker_bindings,
    lane_ownership_allows_delivery,
    lane_ownership_from_json_dict,
    record_continuous_worker_binding_reuse,
    promote_server_api_created_session_to_continuous_worker_binding,
    inspect_worker_binding_promotion_candidates,
    read_delivery_lease_ledger,
    read_lane_ownership_ledger,
    recover_stale_continuous_worker_bindings,
    release_delivery_lease,
    release_lane_ownership,
    release_continuous_worker_binding,
    resume_lane_ownership,
    reserve_delivery_lease,
    resolve_continuous_worker_binding,
    selectable_lane_ownership_conflicts,
    suspend_lane_ownership,
    transfer_lane_ownership,
    validate_no_active_delivery_lease_conflicts,
    validate_no_selectable_lane_ownership_conflicts,
    inspect_opencode_serve_lifecycle_receipts,
    record_opencode_serve_lifecycle_receipt,
    LeaderWorkerDispatcherLoopRequest,
    LeaderWorkerDispatcherTickRequest,
    SandboxAllocation,
    SandboxLeaseMountAuthorization,
    SandboxProviderRegistry,
    SandboxProfile,
    SandboxRequest,
    ScheduledTask,
    ScheduledTaskState,
    SchedulerEvent,
    SchedulerMergeGateEvent,
    SchedulerRunPolicy,
    SchedulerMergeGate,
    SchedulerState,
    TaskDependency,
    TaskSpec,
    QoderAgentRuntimeAdapter,
    QoderQueryRequest,
    QoderQueryResult,
    QoderRuntimeError,
    QoderSDKHostReadinessReport,
    PermissionRequest,
    RuntimeCapabilities,
    RuntimeProviderKind,
    RuntimeHostInvocation,
    RuntimeInvocationRecord,
    RuntimeProviderPermissionGrant,
    RuntimeRegistryWiringConfig,
    RuntimeRegistryWiringResult,
    RuntimeRetryPolicy,
    RuntimeRunResult,
    RuntimeAttemptRecord,
    PreflightedTaskRunResult,
    RunHandle,
    SessionHandle,
    SharedProcessSandboxProvider,
    VisibilityPolicy,
    QoderSDKQueryClient,
    QoderSDKQueryClientConfig,
    ScratchManifest,
    ScratchManifestEntry,
    SchedulerTaskBatchSubmission,
    SchedulerTaskSubmission,
    SchedulerDaemonLoopRequest,
    SchedulerDaemonLoopStopPolicy,
    SchedulerDaemonTickRequest,
    HostSchedulerDaemonLoopRequest,
    HostSchedulerDaemonLoopResult,
    SchedulerDaemonLifecycleRequest,
    SchedulerDaemonLifecycleRunOnceRequest,
    SchedulerDaemonHarnessPolicy,
    SchedulerDaemonHarnessRequest,
    SchedulerDaemonSupervisorRequest,
    SchedulerLoopEvidence,
    SchedulerLoopEvidenceSummary,
    SchedulerOperatorDogfoodFixtureResult,
    GuideWorkerInstruction,
    GuideWorkerLocalOrchestrationRequest,
    GuideWorkerParallelWave,
    GuideWorkerPlannerLaneSpec,
    GuideWorkerPlanningRequest,
    execute_guide_worker_parallel_wave,
    guide_worker_instructions_from_sequence,
    SUPERVISOR_STORAGE_BINDING_ARTIFACT_PRODUCT_TYPE,
    SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
    SUPERVISOR_STORAGE_BINDING_ARTIFACT_SCHEMA_VERSION,
    SupervisorAgentStorageBindingRequest,
    SupervisorStorageBindingEvidenceSummary,
    WorkerTrajectoryReportConsumerRequest,
    WorkerTrajectoryReportConsumerResult,
    acknowledge_leader_worker_delivery,
    admit_exchange_artifact_version_to_scheduler,
    admit_exchange_artifact_version_with_ledger,
    agent_home_registration_to_artifact,
    apply_scheduler_daemon_lifecycle_action,
    build_supervisor_agent_storage_binding,
    cleanup_receipt_to_artifact,
    classify_edit_lease_conflict,
    build_orchestration_preflight_bundle,
    build_host_scheduler_run_evidence,
    build_runtime_registry_from_config,
    build_sandbox_allocation_receipt_evidence,
    build_scheduler_loop_evidence,
    build_supervisor_storage_binding_evidence,
    build_worker_patch_review_artifact,
    compact_runtime_invocation_log,
    consume_successful_codex_result,
    consume_worker_patch_review_decision,
    consume_worker_trajectory_report,
    decide_agent_exchange_action_candidate,
    default_supervisor_storage_binding_evidence_path,
    default_sandbox_allocation_receipt_evidence_path,
    seed_scheduler_operator_binding_consumer_dogfood_fixture,
    seed_scheduler_operator_dogfood_fixture,
    seed_scheduler_operator_multilane_dogfood_fixture,
    drain_preflighted_ready_tasks,
    drain_ready_tasks,
    evaluate_stop_condition,
    evaluate_leader_worker_policy,
    evaluate_task_admission,
    expire_edit_leases,
    exchange_artifact_from_json_dict,
    exchange_artifact_to_json_dict,
    inspect_exchange_artifact_admission_ledger,
    inspect_exchange_artifact_store,
    inspect_supervisor_storage_binding_artifact_refs_for_submission,
    inspect_scheduler_daemon_lifecycle_control,
    inspect_scheduler_authorization,
    inspect_scheduler_authorization_snapshot,
    inspect_leader_worker_delivery_state,
    inspect_runtime_invocation_log,
    has_scheduler_readable_relation,
    mark_ready_tasks,
    mark_exchange_artifact_version_consumed,
    part_types,
    publish_supervisor_storage_binding_artifact_from_evidence,
    qoder_runtime_capabilities,
    codex_cli_runtime_capabilities,
    opencode_cli_runtime_capabilities,
    qoder_query_result_from_response,
    project_group_item_delivery_signal,
    project_group_item_surface,
    recover_scheduler_state,
    read_leader_worker_dispatcher_state,
    read_leader_worker_delivery_state,
    read_continuous_worker_compact_context_bundle,
    replay_scheduler_events,
    resolve_scheduler_merge_gate,
    resolve_task_permission_review,
    run_preflighted_task,
    run_persisted_scheduler_once,
    run_persisted_scheduler_once_with_wiring,
    run_host_authorized_scheduler_once,
    run_host_authorized_scheduler_daemon_loop,
    run_ready_task,
    run_scheduled_task_with_registry,
    run_scheduler_daemon_loop,
    run_scheduler_daemon_harness,
    run_scheduler_daemon_harness_with_policy,
    run_scheduler_daemon_supervisor_step,
    run_scheduler_daemon_lifecycle_once,
    run_scheduler_daemon_tick,
    run_guide_worker_local_trajectory_orchestration,
    run_leader_worker_activation_pass,
    run_bounded_codex_delivery_supervisor_loop,
    run_bounded_opencode_delivery_supervisor_loop,
    run_bounded_provider_delivery_supervisor_loop_for_codex,
    run_bounded_provider_delivery_supervisor_loop_for_opencode,
    run_provider_delivery_supervisor_once_for_codex,
    run_provider_delivery_supervisor_once_for_opencode,
    run_provider_delivery_e2e_smoke_for_codex,
    run_provider_delivery_e2e_smoke_for_opencode,
    run_live_codex_concurrent_worker_smoke,
    run_live_opencode_concurrent_worker_smoke,
    inspect_monitoring_snapshot,
    run_codex_delivery_e2e_smoke,
    run_opencode_delivery_e2e_smoke,
    run_codex_delivery_supervisor_once,
    run_opencode_delivery_supervisor_once,
    inspect_codex_runtime_status,
    inspect_opencode_runtime_status,
    inspect_opencode_server_api_readiness,
    inspect_opencode_serve_readiness,
    claim_opencode_session_binding,
    inspect_opencode_session_bindings,
    recover_stale_opencode_session_bindings,
    release_opencode_session_binding,
    run_leader_worker_dispatcher_loop,
    run_leader_worker_dispatcher_tick,
    run_with_runtime_invocation_audit,
    roll_up_work_item,
    sandbox_capability_placeholder,
    scheduler_task_batch_submission_from_artifact,
    scheduler_task_batch_submission_to_artifact,
    scheduler_task_submission_from_artifact,
    scheduler_task_submission_to_artifact,
    scratch_manifest_to_artifact,
    submit_scheduler_task_batch,
    submit_scheduler_task_batch_with_persistence,
    submit_scheduler_task,
    sync_leader_worker_delivery_from_dispatch_log,
    supervisor_storage_binding_evidence_summary_to_artifact,
    validate_supervisor_storage_binding_artifact_refs,
    validate_exchange_artifact,
    summarize_scheduler_queue,
    select_ready_worker_parallel_wave,
    wake_dependent_tasks,
    write_compacted_scheduler_snapshot,
    read_scheduler_daemon_lifecycle_control,
    write_host_scheduler_run_evidence,
    read_sandbox_allocation_receipt_evidence_summary,
    read_scheduler_state_snapshot,
    read_host_scheduler_run_evidence_summaries,
    read_host_scheduler_run_evidence_summary,
    read_scheduler_loop_evidence_summary,
    read_supervisor_storage_binding_evidence_summary,
    run_sandbox_allocation_cleanup_over_receipts,
    preflight_worker_patch_composition,
    review_worker_patch_action_candidate,
    worker_patch_composition_refs_from_tokens,
    write_scheduler_state_snapshot,
    write_sandbox_allocation_receipt_evidence,
    write_scheduler_loop_evidence,
    write_supervisor_storage_binding_evidence,
)
from tools.progress_graph import (
    EvidencePublishToConsumerClosureRequest,
    HostOwnedGuideWorkerProviderExecutionConfig,
    HostSandboxReceiptWorkflowRequest,
    SchedulerOperatorDogfoodClosureRequest,
    SchedulerOperatorWorkflowRequest,
    SchedulerSupervisorDogfoodWorkflowRequest,
    build_supervisor_dogfood_storage_binding,
    build_host_evidence_presentation,
    read_host_evidence_bundle,
    run_evidence_publish_to_consumer_closure,
    run_host_owned_guide_worker_provider_execution,
    run_host_sandbox_receipt_workflow,
    run_scheduler_operator_dogfood_closure,
    run_scheduler_operator_workflow,
    run_scheduler_supervisor_dogfood_workflow,
)


def test_bridge_group_item_defaults_allow_pre_dispatch_missing_lineage() -> None:
    item = BridgeGroupItem(group_item_id="group-1", work_item_id="work-1")

    assert item.task_group_id is None
    assert item.latest_envelope_id is None
    assert item.latest_trace_id is None
    assert item.child_task_ids == ()
    assert item.lifecycle_state == "prepared"
    assert item.governance_surface_kind == "none"
    assert item.writeback_disposition == "pending"
    assert item.delivery_surface_kind == "none"
    assert item.delivery_state == ""
    assert item.delivery_record_id == ""
    assert item.delivery_failure_detail == ""


def test_bridge_work_item_defaults_start_queued_with_empty_rollup() -> None:
    item = BridgeWorkItem(
        work_item_id="work-1",
        source_envelope_id="env-1",
        scope_summary="narrow slice",
    )

    assert item.source_trace_id is None
    assert item.dependency_ids == ()
    assert item.group_item_ids == ()
    assert item.lifecycle_state == "queued"
    assert item.rollup_surface_kind == "none"
    assert item.rollup_writeback_disposition == "pending"
    assert item.open_group_item_count == 0


def test_models_use_tuple_based_stable_collections() -> None:
    group_item = BridgeGroupItem(
        group_item_id="group-1",
        work_item_id="work-1",
        child_task_ids=("child-1", "child-2"),
    )
    work_item = BridgeWorkItem(
        work_item_id="work-1",
        source_envelope_id="env-1",
        scope_summary="narrow slice",
        dependency_ids=("dep-1",),
        group_item_ids=("group-1",),
        dominant_group_item_ids=("group-1",),
    )

    assert group_item.child_task_ids == ("child-1", "child-2")
    assert work_item.dependency_ids == ("dep-1",)
    assert work_item.group_item_ids == ("group-1",)
    assert work_item.dominant_group_item_ids == ("group-1",)


def test_project_group_item_surface_returns_new_settled_item() -> None:
    original = BridgeGroupItem(group_item_id="group-1", work_item_id="work-1")

    projected = project_group_item_surface(
        original,
        governance_surface_kind="grouped_review",
        governance_surface_state="all_clear",
        writeback_disposition="eligible",
    )

    assert original.lifecycle_state == "prepared"
    assert projected is not original
    assert projected.lifecycle_state == "settled"
    assert projected.governance_surface_kind == "grouped_review"
    assert projected.governance_surface_state == "all_clear"
    assert projected.writeback_disposition == "eligible"


def test_project_group_item_delivery_signal_overlays_existing_group_item() -> None:
    original = project_group_item_surface(
        BridgeGroupItem(group_item_id="group-1", work_item_id="work-1"),
        governance_surface_kind="group_terminal",
        governance_surface_state="handoff",
        writeback_disposition="suppressed",
    )

    projected = project_group_item_delivery_signal(
        original,
        delivery_surface_kind="handoff",
        delivery_state="delivered",
        delivery_record_id="handoff-123",
    )

    assert projected is not original
    assert projected.lifecycle_state == "settled"
    assert projected.governance_surface_kind == "group_terminal"
    assert projected.governance_surface_state == "handoff"
    assert projected.writeback_disposition == "suppressed"
    assert projected.delivery_surface_kind == "handoff"
    assert projected.delivery_state == "delivered"
    assert projected.delivery_record_id == "handoff-123"
    assert projected.delivery_failure_detail == ""


def test_project_group_item_delivery_signal_can_record_failure_without_mutating_source() -> None:
    original = project_group_item_surface(
        BridgeGroupItem(group_item_id="group-1", work_item_id="work-1"),
        governance_surface_kind="group_terminal",
        governance_surface_state="escalation",
        writeback_disposition="suppressed",
    )

    projected = project_group_item_delivery_signal(
        original,
        delivery_surface_kind="review_intake",
        delivery_state="failed",
        delivery_failure_detail="review intake consumer is not configured",
    )

    assert original.delivery_surface_kind == "none"
    assert original.delivery_state == ""
    assert original.delivery_failure_detail == ""
    assert projected.delivery_surface_kind == "review_intake"
    assert projected.delivery_state == "failed"
    assert projected.delivery_record_id == ""
    assert projected.delivery_failure_detail == "review intake consumer is not configured"


def test_guide_worker_local_orchestration_runs_cross_lane_wave(tmp_path) -> None:
    result = run_guide_worker_local_trajectory_orchestration(
        GuideWorkerLocalOrchestrationRequest(
            artifact_store_path=tmp_path / ".codex/orchestration/exchange-artifacts.json",
            admission_ledger_path=tmp_path / ".codex/orchestration/admissions.json",
            snapshot_path=tmp_path / ".codex/scheduler/state.json",
            event_log_path=tmp_path / ".codex/scheduler/events.jsonl",
            trajectory_id="local-work:test",
            artifact_id_prefix="gw-local-test",
            timestamp="2026-06-23T00:00:00Z",
            workspace_root=str(tmp_path),
        )
    )

    payload = result.to_json_dict()

    assert payload["ok"] is True
    assert payload["scenario"]["parallelism_contract"] == "one_ready_worker_task_per_lane_per_wave"
    assert payload["scenario"]["execution_model"] == "scheduled_parallel_wave_sequential_fake_runtime"
    assert payload["submitted_task_ids"] == [
        "task/gw-local-test/client",
        "task/gw-local-test/server",
    ]
    assert payload["lane_ids"] == ["lane:client", "lane:server"]
    assert payload["parallel_waves"] == [
        {
            "wave_id": "parallel-wave:001",
            "task_ids": [
                "task/gw-local-test/client",
                "task/gw-local-test/server",
            ],
            "lane_ids": ["lane:client", "lane:server"],
            "execution_model": "scheduled_parallel_wave_sequential_fake_runtime",
            "sequential_runtime": True,
        }
    ]
    assert payload["task_states"]["task/gw-local-test/client"] == "complete"
    assert payload["task_states"]["task/gw-local-test/server"] == "complete"
    assert payload["authority_split"]["scheduler_state_mutated"] is True
    assert payload["authority_split"]["provider_executed"] is True
    assert payload["authority_split"]["true_process_parallelism"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False

    state = read_scheduler_state_snapshot(tmp_path / ".codex/scheduler/state.json")
    assert state.tasks["task/gw-local-test/client"].context_scope.lane_id == "lane:client"
    assert state.tasks["task/gw-local-test/server"].context_scope.lane_id == "lane:server"
    assert len(state.run_records) == 2
    assert not (tmp_path / ".codex/progress-graph/local-work-trajectory.json").exists()


def test_guide_worker_local_orchestration_plans_instructions_from_task(
    tmp_path,
) -> None:
    result = run_guide_worker_local_trajectory_orchestration(
        GuideWorkerLocalOrchestrationRequest(
            artifact_store_path=tmp_path / ".codex/orchestration/exchange-artifacts.json",
            admission_ledger_path=tmp_path / ".codex/orchestration/admissions.json",
            snapshot_path=tmp_path / ".codex/scheduler/state.json",
            event_log_path=tmp_path / ".codex/scheduler/events.jsonl",
            trajectory_id="local-work:planned",
            artifact_id_prefix="gw-planned",
            timestamp="2026-06-24T10:00:00Z",
            planning_request=GuideWorkerPlanningRequest(
                task_title="Build a maze game with separated client and server",
                task_summary=(
                    "Create a web maze game where browser interaction and server "
                    "state are isolated by a network boundary."
                ),
                lane_specs=(
                    GuideWorkerPlannerLaneSpec(
                        lane_id="lane:client",
                        label="Client UI",
                        focus="browser maze controls and CLI-like test hooks",
                        allowed_artifacts=("client", "web"),
                        acceptance=(
                            "Client worker reports browser controls.",
                            "Client worker reports CLI-like hooks for tests.",
                        ),
                    ),
                    GuideWorkerPlannerLaneSpec(
                        lane_id="lane:server",
                        label="Server API",
                        focus="server state API and port boundary",
                        allowed_artifacts=("server", "api"),
                        acceptance=(
                            "Server worker reports state API.",
                            "Server worker reports port isolation.",
                        ),
                    ),
                ),
            ),
            max_parallel_lanes=2,
            max_waves=1,
            workspace_root=str(tmp_path),
        )
    )

    payload = result.to_json_dict()

    assert payload["ok"] is True
    assert payload["planning"]["planner"] == "deterministic-lane-spec-v1"
    assert payload["planning"]["source"] == "planning_request"
    assert payload["planning"]["leader_agent_id"] == "agent:guide"
    assert payload["planning"]["worker_count"] == 2
    assert payload["planning"]["task_title"] == (
        "Build a maze game with separated client and server"
    )
    assert payload["submitted_task_ids"] == [
        "task/gw-planned/client",
        "task/gw-planned/server",
    ]
    assert payload["lane_ids"] == ["lane:client", "lane:server"]
    assert payload["parallel_waves"][0]["task_ids"] == [
        "task/gw-planned/client",
        "task/gw-planned/server",
    ]
    assert payload["planned_worker_instructions"][0]["title"] == "Client UI"
    assert "browser maze controls" in payload["planned_worker_instructions"][0]["instruction"]
    assert payload["planned_worker_instructions"][1]["allowed_artifacts"] == [
        "server",
        "api",
    ]


def test_guide_worker_local_orchestration_explicit_instructions_override_planner(
    tmp_path,
) -> None:
    result = run_guide_worker_local_trajectory_orchestration(
        GuideWorkerLocalOrchestrationRequest(
            artifact_store_path=tmp_path / ".codex/orchestration/exchange-artifacts.json",
            admission_ledger_path=tmp_path / ".codex/orchestration/admissions.json",
            snapshot_path=tmp_path / ".codex/scheduler/state.json",
            event_log_path=tmp_path / ".codex/scheduler/events.jsonl",
            trajectory_id="local-work:planned",
            artifact_id_prefix="gw-explicit-wins",
            timestamp="2026-06-24T10:10:00Z",
            planning_request=GuideWorkerPlanningRequest(
                task_title="This planner should not be used",
                task_summary="Explicit worker instructions take precedence.",
            ),
            worker_instructions=(
                GuideWorkerInstruction(
                    task_id="task/explicit/only",
                    title="Explicit worker",
                    instruction="Run only this explicit worker instruction.",
                    lane_id="lane:explicit",
                ),
            ),
            max_parallel_lanes=2,
            max_waves=1,
            workspace_root=str(tmp_path),
        )
    )

    payload = result.to_json_dict()

    assert payload["ok"] is True
    assert payload["planning"]["source"] == "explicit_worker_instructions"
    assert payload["submitted_task_ids"] == ["task/explicit/only"]
    assert payload["lane_ids"] == ["lane:explicit"]


def test_guide_worker_local_orchestration_preserves_instruction_sandbox_profile(
    tmp_path,
) -> None:
    repo = _git_repo(tmp_path)
    sandbox_registry = SandboxProviderRegistry()
    sandbox_registry.register(SharedProcessSandboxProvider())
    sandbox_registry.register(GitWorktreeSandboxProvider(tmp_path / "sandboxes"))
    result = run_guide_worker_local_trajectory_orchestration(
        GuideWorkerLocalOrchestrationRequest(
            artifact_store_path=tmp_path / ".codex/orchestration/exchange-artifacts.json",
            admission_ledger_path=tmp_path / ".codex/orchestration/admissions.json",
            snapshot_path=tmp_path / ".codex/scheduler/state.json",
            event_log_path=tmp_path / ".codex/scheduler/events.jsonl",
            trajectory_id="local-work:sandbox-profile",
            artifact_id_prefix="gw-sandbox-profile",
            timestamp="2026-06-24T23:20:00Z",
            worker_instructions=(
                GuideWorkerInstruction(
                    task_id="task/sandbox/client",
                    title="Client sandbox worker",
                    instruction="Run in a git worktree sandbox.",
                    lane_id="lane:client",
                    allowed_artifacts=("client/app.js",),
                    sandbox_profile=SandboxProfile(
                        profile_id="worktree-client",
                        profile_kind="git-worktree",
                    ),
                ),
            ),
            max_parallel_lanes=1,
            max_waves=1,
            workspace_root=str(repo),
        ),
        sandbox_registry=sandbox_registry,
    )

    payload = result.to_json_dict()
    state = read_scheduler_state_snapshot(tmp_path / ".codex/scheduler/state.json")
    task = state.tasks["task/sandbox/client"]

    assert payload["planned_worker_instructions"][0]["sandbox_profile"] == {
        "profile_id": "worktree-client",
        "profile_kind": "git-worktree",
        "network_policy": "disabled",
        "secret_policy": "deny",
        "mount_policy": "lease-scoped",
    }
    assert task.sandbox_profile.profile_kind == "git-worktree"
    assert task.sandbox_profile.profile_id == "worktree-client"
    allocation = result.run_results[0].preflight.sandbox_allocation
    assert allocation.provider == "git-worktree"
    GitWorktreeSandboxProvider(tmp_path / "sandboxes").cleanup(allocation)


def test_guide_worker_parallel_wave_selects_one_ready_task_per_lane(tmp_path) -> None:
    result = run_guide_worker_local_trajectory_orchestration(
        GuideWorkerLocalOrchestrationRequest(
            artifact_store_path=tmp_path / ".codex/orchestration/exchange-artifacts.json",
            admission_ledger_path=tmp_path / ".codex/orchestration/admissions.json",
            snapshot_path=tmp_path / ".codex/scheduler/state.json",
            event_log_path=tmp_path / ".codex/scheduler/events.jsonl",
            trajectory_id="local-work:test",
            artifact_id_prefix="gw-local-same-lane",
            timestamp="2026-06-23T00:00:00Z",
            worker_instructions=(
                GuideWorkerInstruction(
                    task_id="task/same-lane/a",
                    title="Same lane task A",
                    instruction="Produce first same-lane fake result.",
                    lane_id="lane:shared",
                ),
                GuideWorkerInstruction(
                    task_id="task/same-lane/b",
                    title="Same lane task B",
                    instruction="Produce second same-lane fake result.",
                    lane_id="lane:shared",
                ),
            ),
            max_parallel_lanes=2,
            max_waves=2,
            workspace_root=str(tmp_path),
        )
    )

    payload = result.to_json_dict()

    assert payload["ok"] is True
    assert payload["parallel_waves"][0]["task_ids"] == ["task/same-lane/a"]
    assert payload["parallel_waves"][0]["lane_ids"] == ["lane:shared"]
    assert payload["parallel_waves"][1]["task_ids"] == ["task/same-lane/b"]
    assert payload["parallel_waves"][1]["lane_ids"] == ["lane:shared"]
    assert payload["run_task_ids"] == ["task/same-lane/a", "task/same-lane/b"]

    completed_state = read_scheduler_state_snapshot(tmp_path / ".codex/scheduler/state.json")
    ready_state = mark_ready_tasks(completed_state)
    empty_wave = select_ready_worker_parallel_wave(
        ready_state,
        submitted_task_ids=("task/same-lane/a", "task/same-lane/b"),
        max_parallel_lanes=2,
        wave_index=3,
    )
    assert empty_wave.task_ids == ()


def test_guide_worker_local_orchestration_threaded_wave_reports_deterministic_merge(
    tmp_path,
) -> None:
    result = run_guide_worker_local_trajectory_orchestration(
        GuideWorkerLocalOrchestrationRequest(
            artifact_store_path=tmp_path / ".codex/orchestration/exchange-artifacts.json",
            admission_ledger_path=tmp_path / ".codex/orchestration/admissions.json",
            snapshot_path=tmp_path / ".codex/scheduler/state.json",
            event_log_path=tmp_path / ".codex/scheduler/events.jsonl",
            trajectory_id="local-work:test",
            artifact_id_prefix="gw-local-threaded",
            timestamp="2026-06-24T00:00:00Z",
            worker_instructions=(
                GuideWorkerInstruction(
                    task_id="task/threaded/b",
                    title="Threaded server",
                    instruction="Produce server fake result.",
                    lane_id="lane:server",
                ),
                GuideWorkerInstruction(
                    task_id="task/threaded/a",
                    title="Threaded client",
                    instruction="Produce client fake result.",
                    lane_id="lane:client",
                ),
            ),
            max_parallel_lanes=2,
            max_waves=1,
            wave_execution_mode="threaded",
            workspace_root=str(tmp_path),
        )
    )

    payload = result.to_json_dict()

    assert payload["ok"] is True
    assert payload["parallel_waves"][0]["task_ids"] == [
        "task/threaded/a",
        "task/threaded/b",
    ]
    assert payload["wave_execution_results"] == [
        {
            "wave_id": "parallel-wave:001",
            "mode": "threaded",
            "attempted_task_ids": ["task/threaded/a", "task/threaded/b"],
            "completed_task_ids": ["task/threaded/a", "task/threaded/b"],
            "failed_task_ids": [],
            "deterministic_merge_order": ["task/threaded/a", "task/threaded/b"],
            "invoked_as_wave": True,
            "true_process_parallelism": True,
        }
    ]
    assert payload["authority_split"]["wave_executor_mode"] == "threaded"
    assert payload["authority_split"]["true_process_parallelism"] is True
    state = read_scheduler_state_snapshot(tmp_path / ".codex/scheduler/state.json")
    assert state.tasks["task/threaded/a"].state == "complete"
    assert state.tasks["task/threaded/b"].state == "complete"
    assert [record.task_id for record in state.run_records] == [
        "task/threaded/a",
        "task/threaded/b",
    ]


def test_guide_worker_local_orchestration_can_use_injected_qoder_worker_runtime(
    tmp_path,
) -> None:
    client = _RecordingQoderClient(
        QoderQueryResult(
            summary="qoder worker completed guide-assigned task",
            output_text="qoder worker result",
        )
    )
    registry = AgentRuntimeAdapterRegistry()
    registry.register(
        FakeAgentRuntimeAdapter(
            artifact_store=InMemoryArtifactVersionStore(),
            timestamp="2026-06-24T00:00:00Z",
        )
    )
    registry.register(
        QoderAgentRuntimeAdapter(
            query_client=client,
            timestamp="2026-06-24T00:00:00Z",
        )
    )

    result = run_guide_worker_local_trajectory_orchestration(
        GuideWorkerLocalOrchestrationRequest(
            artifact_store_path=tmp_path / ".codex/orchestration/exchange-artifacts.json",
            admission_ledger_path=tmp_path / ".codex/orchestration/admissions.json",
            snapshot_path=tmp_path / ".codex/scheduler/state.json",
            event_log_path=tmp_path / ".codex/scheduler/events.jsonl",
            trajectory_id="local-work:test",
            artifact_id_prefix="gw-local-qoder",
            timestamp="2026-06-24T00:00:00Z",
            worker_instructions=(
                GuideWorkerInstruction(
                    task_id="task/qoder/worker",
                    title="Qoder worker",
                    instruction="Run this guide-assigned task through injected Qoder.",
                    lane_id="lane:qoder",
                    worker_agent_id="agent:qoder-worker",
                    worker_runtime_provider="qoder",
                    output_artifact_id="task/qoder/worker:result",
                ),
            ),
            max_parallel_lanes=1,
            max_waves=1,
            wave_execution_mode="threaded",
            workspace_root=str(tmp_path),
        ),
        runtime_registry=registry,
    )

    payload = result.to_json_dict()
    state = read_scheduler_state_snapshot(tmp_path / ".codex/scheduler/state.json")

    assert payload["ok"] is True
    assert payload["scenario"]["runtime_provider"] == "qoder"
    assert payload["scenario"]["worker_runtime_providers"] == ["qoder"]
    assert payload["authority_split"]["runtime_provider"] == "qoder"
    assert payload["submitted_task_ids"] == ["task/qoder/worker"]
    assert payload["wave_execution_results"][0]["completed_task_ids"] == [
        "task/qoder/worker",
    ]
    assert state.tasks["task/qoder/worker"].agent.runtime_provider == "qoder"
    assert state.tasks["task/qoder/worker"].state == "complete"
    assert client.requests[0].agent.agent_id == "agent:qoder-worker"
    assert client.requests[0].agent.runtime_provider == "qoder"
    assert client.requests[0].task.task_id == "task/qoder/worker"


def test_guide_worker_instruction_parser_accepts_mcp_camel_case_payload() -> None:
    instructions = guide_worker_instructions_from_sequence(
        [
            {
                "taskId": "task/parser/client",
                "title": "Parser client",
                "instruction": "Parse this MCP worker instruction.",
                "laneId": "lane:client",
                "contextId": "context/parser/client",
                "workerAgentId": "agent:client-worker",
                "workerRuntimeProvider": "qoder",
                "allowedArtifacts": ["client"],
                "acceptance": ["Client parser instruction is valid."],
                "dependsOnTaskIds": ["task/parser/setup"],
                "outputArtifactId": "task/parser/client:result",
            }
        ]
    )

    assert len(instructions) == 1
    assert instructions[0].task_id == "task/parser/client"
    assert instructions[0].lane_id == "lane:client"
    assert instructions[0].context_id == "context/parser/client"
    assert instructions[0].worker_agent_id == "agent:client-worker"
    assert instructions[0].worker_runtime_provider == "qoder"
    assert instructions[0].allowed_artifacts == ("client",)
    assert instructions[0].acceptance == ("Client parser instruction is valid.",)
    assert instructions[0].depends_on_task_ids == ("task/parser/setup",)
    assert instructions[0].output_artifact_id == "task/parser/client:result"

    with pytest.raises(ValueError, match=r"workerInstructions\[0\]\.instruction"):
        guide_worker_instructions_from_sequence(
            [
                {
                    "taskId": "task/parser/bad",
                    "title": "Bad parser",
                    "laneId": "lane:bad",
                }
            ]
        )


def test_roll_up_work_item_prefers_blocked_over_all_clear() -> None:
    work_item = BridgeWorkItem(
        work_item_id="work-1",
        source_envelope_id="env-1",
        scope_summary="narrow slice",
    )
    blocked = project_group_item_surface(
        BridgeGroupItem(group_item_id="group-b", work_item_id="work-1"),
        governance_surface_kind="blocked",
        governance_surface_state="blocked",
        blocked_reason="child_failed",
        writeback_disposition="blocked",
    )
    all_clear = project_group_item_surface(
        BridgeGroupItem(group_item_id="group-a", work_item_id="work-1"),
        governance_surface_kind="grouped_review",
        governance_surface_state="all_clear",
        writeback_disposition="eligible",
    )

    rolled = roll_up_work_item(work_item, (all_clear, blocked))

    assert rolled.rollup_surface_kind == "blocked"
    assert rolled.rollup_surface_state == "blocked"
    assert rolled.rollup_blocked_reason == "child_failed"
    assert rolled.rollup_writeback_disposition == "blocked"
    assert rolled.dominant_group_item_ids == ("group-b",)


def test_roll_up_work_item_keeps_pending_when_open_group_exists() -> None:
    work_item = BridgeWorkItem(
        work_item_id="work-1",
        source_envelope_id="env-1",
        scope_summary="narrow slice",
    )
    settled = project_group_item_surface(
        BridgeGroupItem(group_item_id="group-1", work_item_id="work-1"),
        governance_surface_kind="grouped_review",
        governance_surface_state="all_clear",
        writeback_disposition="eligible",
    )
    open_group = BridgeGroupItem(group_item_id="group-2", work_item_id="work-1")

    rolled = roll_up_work_item(work_item, (settled, open_group))

    assert rolled.open_group_item_count == 1
    assert rolled.rollup_writeback_disposition == "pending"


def test_evaluate_stop_condition_maps_group_terminal_to_external_resolution() -> None:
    work_item = BridgeWorkItem(
        work_item_id="work-1",
        source_envelope_id="env-1",
        scope_summary="narrow slice",
        rollup_surface_kind="group_terminal",
        rollup_surface_state="handoff",
    )

    decision = evaluate_stop_condition(work_item)

    assert decision.boundary_kind == "wait_external_resolution"
    assert decision.next_lifecycle_state == "waiting_external_resolution"
    assert decision.reason == "handoff"


def test_evaluate_stop_condition_flags_inconsistent_pending_without_open_groups() -> None:
    work_item = BridgeWorkItem(
        work_item_id="work-1",
        source_envelope_id="env-1",
        scope_summary="narrow slice",
        lifecycle_state="waiting_governance_result",
        rollup_writeback_disposition="pending",
        open_group_item_count=0,
    )

    decision = evaluate_stop_condition(work_item)

    assert decision.boundary_kind == "inconsistent"
    assert decision.next_lifecycle_state == "waiting_governance_result"
    assert decision.reason == "inconsistent_rollup_state"


def test_exchange_blocker_with_relation_part_is_scheduler_readable() -> None:
    relation = ExchangeRelation(
        relation_id="rel-1",
        relation_kind="waits_for",
        source=ExchangeReference(ref_kind="task", ref_id="task-client"),
        target=ExchangeReference(ref_kind="contract", ref_id="server-api", version="v2"),
        reason="client needs stable move response shape",
    )
    artifact = ExchangeArtifact(
        artifact_id="ex-1",
        kind="blocker",
        intent="declare_blocked",
        producer="agent:client",
        scope=ExchangeScope(task_id="task-client", lane_id="lane-client"),
        parts=(
            ExchangePayloadPart(part_type="text", text="Client is waiting for server API v2."),
            ExchangePayloadPart(part_type="relation", relation=relation),
        ),
    )

    assert validate_exchange_artifact(artifact) == ()
    assert part_types(artifact) == ("text", "relation")
    assert has_scheduler_readable_relation(artifact, "waits_for") is True
    assert has_scheduler_readable_relation(artifact, "blocks") is False


def test_exchange_blocker_text_without_relation_is_invalid() -> None:
    artifact = ExchangeArtifact(
        artifact_id="ex-2",
        kind="blocker",
        intent="declare_blocked",
        producer="agent:client",
        parts=(ExchangePayloadPart(part_type="text", text="I am blocked by the server API."),),
    )

    errors = validate_exchange_artifact(artifact)

    assert len(errors) == 1
    assert "requires payload part 'relation'" in errors[0]
    assert "must not exist only in text" in errors[0]


def test_exchange_contract_artifact_preserves_versioned_contract_payload() -> None:
    contract = ExchangeContract(
        contract_id="server-api",
        contract_kind="api",
        version="v2",
        title="Maze server API",
        producer="agent:server",
        consumers=("agent:client", "agent:test"),
        status="accepted",
        content={
            "endpoints": [
                {"method": "GET", "path": "/state"},
                {"method": "POST", "path": "/move"},
            ]
        },
        supersedes=("server-api@v1",),
    )
    artifact = ExchangeArtifact(
        artifact_id="ex-3",
        kind="contract",
        intent="inform",
        producer="agent:server",
        parts=(
            ExchangePayloadPart(part_type="contract", contract=contract),
            ExchangePayloadPart(
                part_type="relation",
                relation=ExchangeRelation(
                    relation_id="rel-2",
                    relation_kind="produces_contract",
                    source=ExchangeReference(ref_kind="task", ref_id="task-server"),
                    target=ExchangeReference(ref_kind="contract", ref_id="server-api", version="v2"),
                ),
            ),
        ),
    )

    assert validate_exchange_artifact(artifact) == ()
    assert artifact.parts[0].contract is not None
    assert artifact.parts[0].contract.contract_id == "server-api"
    assert artifact.parts[0].contract.version == "v2"
    assert artifact.parts[0].contract.supersedes == ("server-api@v1",)


def test_exchange_log_part_is_compact_history_not_raw_transcript() -> None:
    log = ExchangeLog(
        timestamp="2026-06-16T16:00:00+08:00",
        actor="scheduler",
        action="accepted_contract",
        channel="coordination-event-log",
        summary="Accepted server-api v2 for client consumption.",
        related_artifact_ids=("ex-3",),
        related_event_ids=("event:server-contract",),
        related_run_ids=("run:scheduler-1",),
        sequence=42,
        clock="wall",
    )
    artifact = ExchangeArtifact(
        artifact_id="ex-4",
        kind="message",
        intent="inform",
        producer="scheduler",
        parts=(ExchangePayloadPart(part_type="log", log=log),),
    )

    assert validate_exchange_artifact(artifact) == ()
    assert artifact.parts[0].log is not None
    assert artifact.parts[0].log.timestamp == "2026-06-16T16:00:00+08:00"
    assert artifact.parts[0].log.related_artifact_ids == ("ex-3",)


def test_exchange_log_part_requires_history_identity_fields() -> None:
    artifact = ExchangeArtifact(
        artifact_id="ex-log-invalid",
        kind="message",
        intent="inform",
        producer="scheduler",
        parts=(
            ExchangePayloadPart(
                part_type="log",
                log=ExchangeLog(
                    timestamp="",
                    actor="",
                    action="",
                    summary="This entry cannot be ordered or attributed.",
                ),
            ),
        ),
    )

    errors = validate_exchange_artifact(artifact)

    assert errors == (
        "payload part 0 is 'log' but log.timestamp is empty",
        "payload part 0 is 'log' but log.actor is empty",
        "payload part 0 is 'log' but log.action is empty",
    )


def test_exchange_part_specific_validation_reports_missing_payloads() -> None:
    artifact = ExchangeArtifact(
        artifact_id="ex-5",
        kind="message",
        intent="inform",
        producer="agent:server",
        parts=(
            ExchangePayloadPart(part_type="text"),
            ExchangePayloadPart(part_type="relation"),
            ExchangePayloadPart(part_type="contract"),
            ExchangePayloadPart(part_type="log"),
        ),
    )

    errors = validate_exchange_artifact(artifact)

    assert errors == (
        "payload part 0 is 'text' but text is empty",
        "payload part 1 is 'relation' but relation payload is missing",
        "payload part 2 is 'contract' but contract payload is missing",
        "payload part 3 is 'log' but log payload is missing",
    )


def test_agent_home_registration_maps_to_retention_exchange_artifact() -> None:
    registration = AgentHomeRegistration(
        registration_id="home-reg-1",
        agent_id="agent:maze-server",
        requested_by="agent:guide",
        purpose="Persist safe server-side maze testing notes.",
        capability_domain="maze-server",
        requested_path_hint=".codex/agents/maze-server",
        allowed_content_types=("notes", "checklist"),
        allowed_sources=("reviewed-scratch",),
        created_at="2026-06-16T23:50:00+08:00",
        updated_at="2026-06-16T23:50:00+08:00",
    )

    artifact = agent_home_registration_to_artifact(registration)

    assert artifact.artifact_id == "agent-home-registration:home-reg-1"
    assert artifact.kind == "retention"
    assert artifact.intent == "request_registration"
    assert artifact.scope.agent_id == "agent:maze-server"
    assert artifact.visibility_policy.audience == ("workspace-registration", "agent:maze-server")
    assert validate_exchange_artifact(artifact) == ()
    assert part_types(artifact) == ("structured", "storage_manifest", "log")
    assert artifact.parts[1].data["product_type"] == "agent_home_registration"
    assert artifact.parts[1].data["secret_policy"] == "deny"
    assert artifact.parts[2].log is not None
    assert artifact.parts[2].log.action == "agent_home_requested"


def test_scratch_manifest_maps_to_retention_review_artifact_with_redaction_flag() -> None:
    scratch = AgentScratchSpace(
        scratch_id="scratch-1",
        agent_id="agent:maze-client",
        run_id="run-1",
        task_id="task-client",
        lane_id="lane-client",
        context_id="context-client",
        path=".codex/scratch/task-client",
        created_at="2026-06-16T23:55:00+08:00",
        manifest_path=".codex/scratch/task-client/manifest.json",
        audit_state="pending_review",
    )
    manifest = ScratchManifest(
        manifest_id="manifest-1",
        scratch_id="scratch-1",
        agent_id="agent:maze-client",
        produced_at="2026-06-16T23:56:00+08:00",
        notes="Review generated CLI fixtures before retention.",
        entries=(
            ScratchManifestEntry(
                path="fixtures/maze-state.json",
                content_type="test-fixture",
                source="generated",
                disposition="archive",
                summary="Deterministic maze fixture.",
            ),
            ScratchManifestEntry(
                path="notes/private-debug.md",
                content_type="runtime-note",
                source="runtime-transcript-excerpt",
                disposition="delete",
                summary="Contains private runtime note.",
                contains_sensitive_content=True,
            ),
        ),
    )

    artifact = scratch_manifest_to_artifact(manifest, scratch)

    assert artifact.kind == "retention"
    assert artifact.intent == "request_retention"
    assert artifact.scope.task_id == "task-client"
    assert artifact.scope.runtime_session_id == "run-1"
    assert artifact.visibility_policy.contains_sensitive_content is True
    assert artifact.visibility_policy.redaction_required is True
    assert validate_exchange_artifact(artifact) == ()
    assert artifact.parts[1].data["product_type"] == "scratch_manifest"
    entries = artifact.parts[1].data["entries"]
    assert isinstance(entries, list)
    assert entries[1]["contains_sensitive_content"] is True
    assert artifact.parts[2].log is not None
    assert artifact.parts[2].log.action == "scratch_manifest_submitted"


def test_cleanup_receipt_maps_to_cleanup_exchange_artifact() -> None:
    scratch = AgentScratchSpace(
        scratch_id="scratch-1",
        agent_id="agent:maze-client",
        run_id="run-1",
        task_id="task-client",
        lane_id="lane-client",
        context_id="context-client",
        path=".codex/scratch/task-client",
        audit_state="cleaned",
    )
    receipt = CleanupReceipt(
        receipt_id="cleanup-1",
        scratch_id="scratch-1",
        agent_id="agent:maze-client",
        cleaned_at="2026-06-17T00:00:00+08:00",
        archived_paths=("fixtures/maze-state.json",),
        deleted_paths=("notes/private-debug.md",),
        reviewed_by="agent:guide",
        summary="Archived safe fixture and deleted private debug note.",
    )

    artifact = cleanup_receipt_to_artifact(receipt, scratch)

    assert artifact.artifact_id == "cleanup-receipt:cleanup-1"
    assert artifact.kind == "cleanup"
    assert artifact.intent == "inform"
    assert artifact.producer == "agent:guide"
    assert validate_exchange_artifact(artifact) == ()
    assert part_types(artifact) == ("storage_manifest", "log")
    assert artifact.parts[0].data["product_type"] == "cleanup_receipt"
    assert artifact.parts[0].data["receipt"]["deleted_paths"] == ["notes/private-debug.md"]
    assert artifact.parts[1].log is not None
    assert artifact.parts[1].log.action == "scratch_cleanup_recorded"


def test_exchange_artifact_version_store_keeps_versions_append_only() -> None:
    store = InMemoryArtifactVersionStore()
    first = _accepted_contract_artifact(version="v1")
    second = _accepted_contract_artifact(version="v2")

    first_record = store.put(first)
    second_record = store.put(second)

    assert first_record.artifact is first
    assert second_record.artifact is second
    assert store.get("server-api", "v1").artifact.version == "v1"
    assert store.latest("server-api").artifact.version == "v2"
    assert store.list_versions("server-api") == ("v1", "v2")

    with pytest.raises(ValueError, match="already exists"):
        store.put(first)


def test_exchange_artifact_version_store_rejects_invalid_scheduler_relevant_artifact() -> None:
    store = InMemoryArtifactVersionStore()
    invalid = ExchangeArtifact(
        artifact_id="blocked-client",
        kind="blocker",
        intent="declare_blocked",
        producer="agent:client",
        version="v1",
        parts=(ExchangePayloadPart(part_type="text", text="blocked by server api"),),
    )

    with pytest.raises(ValueError, match="must not exist only in text"):
        store.put(invalid)


def test_exchange_artifact_json_round_trip_covers_current_payload_parts() -> None:
    artifact = _all_parts_exchange_artifact()

    restored = exchange_artifact_from_json_dict(exchange_artifact_to_json_dict(artifact))

    assert restored == artifact
    assert part_types(restored) == (
        "text",
        "structured",
        "ref",
        "artifact_delta",
        "contract",
        "evidence",
        "relation",
        "storage_manifest",
        "log",
    )
    assert validate_exchange_artifact(restored) == ()


def test_json_artifact_version_store_persists_versions_and_reads_latest(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    store = JsonArtifactVersionStore(store_path)
    first = _accepted_contract_artifact(version="v1")
    second = _accepted_contract_artifact(version="v2")

    first_record = store.put(first)
    second_record = store.put(second)
    restored = JsonArtifactVersionStore(store_path)

    assert first_record.artifact == first
    assert second_record.artifact == second
    assert restored.get("server-api", "v1").artifact == first
    assert restored.latest("server-api").artifact == second
    assert restored.list_versions("server-api") == ("v1", "v2")

    with pytest.raises(ValueError, match="already exists"):
        restored.put(first)


def test_json_artifact_version_store_replaces_exact_version_only_when_explicit(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    store = JsonArtifactVersionStore(store_path)
    first_v1 = replace(
        _accepted_contract_artifact(version="v1"),
        created_at="2026-06-18T01:00:00+08:00",
    )
    second_v1 = replace(
        _accepted_contract_artifact(version="v1"),
        created_at="2026-06-18T02:00:00+08:00",
    )
    v2 = replace(
        _accepted_contract_artifact(version="v2"),
        created_at="2026-06-18T03:00:00+08:00",
    )

    store.put(first_v1)
    store.put(v2)
    replaced = store.put(second_v1, replace_existing=True)
    restored = JsonArtifactVersionStore(store_path)

    assert replaced.artifact == second_v1
    assert restored.get("server-api", "v1").artifact.created_at == "2026-06-18T02:00:00+08:00"
    assert restored.get("server-api", "v2").artifact.created_at == "2026-06-18T03:00:00+08:00"
    assert restored.list_versions("server-api") == ("v2", "v1")
    assert [record.version for record in restored.list_records()] == ["v2", "v1"]


def test_json_artifact_version_store_rejects_invalid_artifact_before_write(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    store = JsonArtifactVersionStore(store_path)
    invalid = ExchangeArtifact(
        artifact_id="blocked-client",
        kind="blocker",
        intent="declare_blocked",
        producer="agent:client",
        version="v1",
        parts=(ExchangePayloadPart(part_type="text", text="blocked by server api"),),
    )

    with pytest.raises(ValueError, match="must not exist only in text"):
        store.put(invalid)

    assert not store_path.exists()


def test_json_artifact_version_store_reports_unsupported_schema_version(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    store_path.write_text(
        json.dumps({"schema_version": "exchange-artifact-store.v0", "records": []}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsupported exchange artifact store version"):
        JsonArtifactVersionStore(store_path).list_versions("server-api")


def test_exchange_artifact_store_inspection_reports_missing_store_as_empty(tmp_path) -> None:
    store_path = tmp_path / "missing-exchange-artifacts.json"

    bundle = inspect_exchange_artifact_store(store_path)

    assert bundle.exists is False
    assert bundle.artifact_count == 0
    assert bundle.version_count == 0
    assert bundle.error_count == 0
    payload = bundle.to_json_dict()
    assert payload["store_path"] == str(store_path)
    assert payload["summaries"] == []
    assert payload["authority_split"]["scheduler_mutated"] is False
    assert payload["authority_split"]["admission_preparation_only"] is True


def test_exchange_artifact_store_inspection_summarizes_versions_and_candidates(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    store = JsonArtifactVersionStore(store_path)
    store.put(_accepted_contract_artifact(version="v1"))
    submission = SchedulerTaskSubmission(
        task_id="task-server",
        title="Implement server",
        instruction="Implement the server side.",
        agent=AgentSpec(agent_id="agent:server", runtime_provider="fake"),
        context_scope=ContextScope(context_id="context:server", lane_id="lane:server"),
        output_artifact_id="task-server:result",
    )
    store.put(
        scheduler_task_submission_to_artifact(
            submission,
            artifact_id="submission:server",
            created_at="2026-06-19T00:10:00+08:00",
            version="v1",
        )
    )
    batch = SchedulerTaskBatchSubmission(
        batch_id="batch-maze",
        tasks=(
            submission,
            SchedulerTaskSubmission(
                task_id="task-client",
                title="Implement client",
                instruction="Implement the client side.",
                agent=AgentSpec(agent_id="agent:client", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:client", lane_id="lane:client"),
                output_artifact_id="task-client:result",
            ),
        ),
    )
    store.put(
        scheduler_task_batch_submission_to_artifact(
            batch,
            artifact_id="submission:batch",
            created_at="2026-06-19T00:11:00+08:00",
            version="v1",
        )
    )

    bundle = inspect_exchange_artifact_store(store_path)
    payload = bundle.to_json_dict()

    assert bundle.exists is True
    assert bundle.artifact_count == 3
    assert bundle.version_count == 3
    assert bundle.admission_candidate_count == 2
    assert payload["summaries"][0]["artifact_id"] == "server-api"
    single = next(
        summary for summary in payload["summaries"]
        if summary["artifact_id"] == "submission:server"
    )
    assert single["kind"] == "request"
    assert single["intent"] == "propose"
    assert single["latest"] is True
    assert single["scope"]["task_id"] == "task-server"
    assert single["admission_candidates"][0]["product_type"] == "scheduler_task_submission"
    assert single["admission_candidates"][0]["task_ids"] == ["task-server"]
    batch_summary = next(
        summary for summary in payload["summaries"]
        if summary["artifact_id"] == "submission:batch"
    )
    assert batch_summary["admission_candidates"][0]["product_type"] == "scheduler_task_batch_submission"
    assert batch_summary["admission_candidates"][0]["batch_id"] == "batch-maze"
    assert batch_summary["admission_candidates"][0]["task_count"] == 2
    assert batch_summary["admission_candidates"][0]["task_ids"] == [
        "task-server",
        "task-client",
    ]
    assert single["admission_state"]["status"] == "not_admitted"
    assert single["admission_state"]["record_count"] == 0


def test_exchange_artifact_store_inspection_projects_admission_state_from_ledger(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    ledger_path = tmp_path / "exchange-artifact-admissions.json"
    store = JsonArtifactVersionStore(store_path)
    store.put(
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task-server",
                title="Implement server",
                instruction="Implement the server side.",
                agent=AgentSpec(agent_id="agent:server", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:server"),
            ),
            artifact_id="submission:server",
            created_at="2026-06-19T06:05:00+08:00",
            version="v1",
        )
    )
    ledger = JsonExchangeArtifactAdmissionLedger(ledger_path)
    admitted = ledger.append(
        ExchangeArtifactAdmissionRecord(
            ledger_id="",
            artifact_store_path=store_path,
            artifact_id="submission:server",
            artifact_version="v1",
            product_type="scheduler_task_submission",
            surface="mcp:admitExchangeArtifact",
            actor="agent:guide",
            timestamp="2026-06-19T06:06:00+08:00",
            snapshot_path=tmp_path / "scheduler-state.json",
            event_log_path=tmp_path / "scheduler-events.jsonl",
            status="admitted",
            submitted_task_ids=("task-server",),
            submission_event_ids=("scheduler-event-1",),
        )
    )
    rejected = ledger.append(
        ExchangeArtifactAdmissionRecord(
            ledger_id="",
            artifact_store_path=store_path,
            artifact_id="submission:server",
            artifact_version="v1",
            product_type="scheduler_task_submission",
            surface="mcp:admitExchangeArtifact",
            actor="agent:guide",
            timestamp="2026-06-19T06:07:00+08:00",
            snapshot_path=tmp_path / "scheduler-state.json",
            event_log_path=tmp_path / "scheduler-events.jsonl",
            status="rejected_duplicate",
            error_summary="duplicate rejected",
            duplicate_of=admitted.ledger_id,
        )
    )

    bundle = inspect_exchange_artifact_store(
        store_path,
        admission_ledger_path=ledger_path,
    )
    payload = bundle.to_json_dict()
    summary = payload["summaries"][0]
    admission_state = summary["admission_state"]

    assert payload["admission_ledger_path"] == str(ledger_path)
    assert payload["admission_ledger_exists"] is True
    assert admission_state["status"] == "admitted"
    assert admission_state["record_count"] == 2
    assert admission_state["status_counts"] == {
        "admitted": 1,
        "rejected_duplicate": 1,
    }
    assert admission_state["latest_record_id"] == rejected.ledger_id
    assert admission_state["latest_status"] == "rejected_duplicate"
    assert admission_state["latest_error_summary"] == "duplicate rejected"
    assert admission_state["admitted_record_ids"] == [admitted.ledger_id]
    assert admission_state["rejected_duplicate_record_ids"] == [rejected.ledger_id]
    assert payload["authority_split"]["exchange_store_mutated"] is False


def test_exchange_artifact_store_projects_binding_readiness_before_admission(
    tmp_path,
) -> None:
    store_path = tmp_path / ".codex" / "orchestration" / "exchange-artifacts.json"
    ledger_path = tmp_path / ".codex" / "orchestration" / "exchange-artifact-admissions.json"
    seed_scheduler_operator_binding_consumer_dogfood_fixture(
        tmp_path,
        artifact_store_path=store_path,
    )

    bundle = inspect_exchange_artifact_store(
        store_path,
        admission_ledger_path=ledger_path,
    )
    payload = bundle.to_json_dict()
    summary = next(
        item for item in payload["summaries"]
        if item["artifact_id"] == "fixture:scheduler-operator-binding-consumer-dogfood"
    )
    candidate = summary["admission_candidates"][0]
    readiness = candidate["binding_reference_readiness"]

    assert summary["admission_state"]["status"] == "not_admitted"
    assert "latest_binding_reference_summary" not in candidate
    assert readiness["enabled"] is True
    assert readiness["ok"] is True
    assert readiness["source_artifact_id"] == "fixture:scheduler-operator-binding-consumer-dogfood"
    assert readiness["submission_product_type"] == "scheduler_task_batch_submission"
    assert readiness["task_count"] == 1
    assert readiness["binding_ref_count"] == 1
    assert readiness["checked_ref_count"] == 1
    assert readiness["tasks"][0]["task_id"] == "dogfood:binding-consumer"
    assert readiness["tasks"][0]["binding_refs"][0]["ref_id"] == (
        "fixture:supervisor-storage-binding-dogfood"
    )
    assert readiness["raw_evidence_json_read"] is False
    assert "binding" not in readiness
    assert "records" not in candidate


def test_exchange_artifact_store_projects_latest_binding_summary_after_admission(
    tmp_path,
) -> None:
    store_path = tmp_path / ".codex" / "orchestration" / "exchange-artifacts.json"
    ledger_path = tmp_path / ".codex" / "orchestration" / "exchange-artifact-admissions.json"
    snapshot_path = tmp_path / ".codex" / "scheduler" / "scheduler-state.json"
    event_log_path = tmp_path / ".codex" / "scheduler" / "scheduler-events.jsonl"
    seed_scheduler_operator_binding_consumer_dogfood_fixture(
        tmp_path,
        artifact_store_path=store_path,
    )
    admitted = admit_exchange_artifact_version_with_ledger(
        artifact_store_path=store_path,
        artifact_id="fixture:scheduler-operator-binding-consumer-dogfood",
        version="v1",
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        admission_ledger_path=ledger_path,
        validate_binding_artifact_refs=True,
        actor="agent:test",
        surface="test:binding-summary-projection",
    )

    bundle = inspect_exchange_artifact_store(
        store_path,
        admission_ledger_path=ledger_path,
    )
    payload = bundle.to_json_dict()
    summary = next(
        item for item in payload["summaries"]
        if item["artifact_id"] == "fixture:scheduler-operator-binding-consumer-dogfood"
    )
    candidate = summary["admission_candidates"][0]
    latest = candidate["latest_binding_reference_summary"]

    assert admitted["ok"] is True
    assert summary["admission_state"]["status"] == "admitted"
    assert latest["ledger_id"] == admitted["admission_ledger_record_id"]
    assert latest["status"] == "admitted"
    assert latest["actor"] == "agent:test"
    assert latest["surface"] == "test:binding-summary-projection"
    assert latest["enabled"] is True
    assert latest["ok"] is True
    assert latest["binding_ref_count"] == 1
    assert latest["checked_ref_count"] == 1
    assert latest["tasks"][0]["task_id"] == "dogfood:binding-consumer"
    assert latest["raw_evidence_json_read"] is False
    assert "binding" not in latest
    assert "records" not in candidate


def test_exchange_artifact_store_inspection_isolates_malformed_admission_ledger(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    ledger_path = tmp_path / "exchange-artifact-admissions.json"
    JsonArtifactVersionStore(store_path).put(_accepted_contract_artifact(version="v1"))
    ledger_path.write_text("{bad json", encoding="utf-8")

    bundle = inspect_exchange_artifact_store(
        store_path,
        admission_ledger_path=ledger_path,
    )
    payload = bundle.to_json_dict()

    assert bundle.exists is True
    assert bundle.version_count == 1
    assert bundle.error_count == 1
    assert "invalid exchange artifact admission ledger JSON" in bundle.errors[0]
    assert payload["summaries"][0]["admission_state"]["status"] == "not_admitted"
    assert payload["admission_ledger_exists"] is True


def test_exchange_artifact_store_inspection_isolates_malformed_store(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    store_path.write_text("{bad json", encoding="utf-8")

    bundle = inspect_exchange_artifact_store(store_path)

    assert bundle.exists is True
    assert bundle.version_count == 0
    assert bundle.error_count == 1
    assert "invalid exchange artifact store JSON" in bundle.errors[0]


def test_exchange_artifact_admission_ledger_round_trips_and_finds_duplicates(tmp_path) -> None:
    ledger_path = tmp_path / "exchange-artifact-admissions.json"
    ledger = JsonExchangeArtifactAdmissionLedger(ledger_path)
    admitted = ledger.append(
        ExchangeArtifactAdmissionRecord(
            ledger_id="",
            artifact_store_path=tmp_path / "exchange-artifacts.json",
            artifact_id="submission:server",
            artifact_version="v1",
            product_type="scheduler_task_submission",
            surface="cli:scheduler admit-exchange-artifact",
            actor="agent:guide",
            timestamp="2026-06-19T04:00:00+00:00",
            snapshot_path=tmp_path / "scheduler-state.json",
            event_log_path=tmp_path / "scheduler-events.jsonl",
            status="admitted",
            submitted_task_ids=("task-server",),
            dependency_ids=("dep-api-server",),
            submission_event_ids=("scheduler-event-1",),
        )
    )
    rejected = ledger.append(
        ExchangeArtifactAdmissionRecord(
            ledger_id="",
            artifact_store_path=tmp_path / "exchange-artifacts.json",
            artifact_id="submission:server",
            artifact_version="v1",
            product_type="scheduler_task_submission",
            surface="cli:scheduler admit-exchange-artifact",
            actor="agent:guide",
            timestamp="2026-06-19T04:01:00+00:00",
            snapshot_path=tmp_path / "scheduler-state.json",
            event_log_path=tmp_path / "scheduler-events.jsonl",
            status="rejected_duplicate",
            error_summary="duplicate rejected",
            duplicate_of=admitted.ledger_id,
        )
    )

    restored = JsonExchangeArtifactAdmissionLedger(ledger_path)
    records = restored.read_all()
    duplicates = restored.find_successful_admissions("submission:server", "v1")
    inspection = inspect_exchange_artifact_admission_ledger(
        ledger_path,
        artifact_id="submission:server",
        artifact_version="v1",
    )
    payload = inspection.to_json_dict()

    assert admitted.ledger_id == "exchange-artifact-admission-1"
    assert rejected.ledger_id == "exchange-artifact-admission-2"
    assert records[0].submitted_task_ids == ("task-server",)
    assert records[0].dependency_ids == ("dep-api-server",)
    assert duplicates == (records[0],)
    assert inspection.record_count == 2
    assert inspection.status_counts == {"admitted": 1, "rejected_duplicate": 1}
    assert payload["authority_split"]["scheduler_state_mutated"] is False
    assert payload["records"][1]["duplicate_of"] == admitted.ledger_id


def test_exchange_artifact_admission_ledger_round_trips_empty_binding_summary(
    tmp_path,
) -> None:
    ledger_path = tmp_path / "exchange-artifact-admissions.json"
    ledger = JsonExchangeArtifactAdmissionLedger(ledger_path)
    ledger.append(
        ExchangeArtifactAdmissionRecord(
            ledger_id="",
            artifact_store_path=tmp_path / "exchange-artifacts.json",
            artifact_id="submission:server",
            artifact_version="v1",
            product_type="scheduler_task_submission",
            surface="legacy",
            actor="agent:guide",
            timestamp="2026-06-19T04:00:00+00:00",
            snapshot_path=tmp_path / "scheduler-state.json",
            event_log_path=tmp_path / "scheduler-events.jsonl",
            status="admitted",
            submitted_task_ids=("task-server",),
        )
    )

    record = JsonExchangeArtifactAdmissionLedger(ledger_path).read_all()[0]
    payload = inspect_exchange_artifact_admission_ledger(ledger_path).to_json_dict()

    assert record.binding_reference_summary == {}
    assert "binding_reference_summary" not in payload["records"][0]


def test_exchange_artifact_admission_ledger_inspection_isolates_malformed_store(tmp_path) -> None:
    ledger_path = tmp_path / "exchange-artifact-admissions.json"
    ledger_path.write_text("{bad json", encoding="utf-8")

    inspection = inspect_exchange_artifact_admission_ledger(ledger_path)

    assert inspection.exists is True
    assert inspection.record_count == 0
    assert inspection.error_count == 1
    assert "invalid exchange artifact admission ledger JSON" in inspection.errors[0]


def test_coordination_event_log_appends_reads_and_projects_log_part(tmp_path) -> None:
    log_path = tmp_path / "coordination-events.jsonl"
    event_log = JsonlCoordinationEventLog(log_path)
    event = CoordinationEvent(
        event_id="event-1",
        event_kind="artifact_recorded",
        timestamp="2026-06-16T16:30:00+08:00",
        actor="scheduler",
        artifact_id="server-api",
        artifact_version="v1",
        summary="Recorded accepted server api contract.",
        related_run_ids=("run-1",),
        sequence=1,
    )

    event_log.append(event)
    loaded = event_log.read_all()
    projected = loaded[0].to_exchange_log()

    assert loaded == (event,)
    assert projected.timestamp == event.timestamp
    assert projected.action == "artifact_recorded"
    assert projected.channel == "coordination-event-log"
    assert projected.related_artifact_ids == ("server-api",)
    assert projected.related_event_ids == ("event-1",)
    assert projected.related_run_ids == ("run-1",)
    assert projected.sequence == 1


def test_coordination_event_log_projection_can_be_used_as_exchange_log_part(tmp_path) -> None:
    event_log = JsonlCoordinationEventLog(tmp_path / "coordination-events.jsonl")
    event_log.append(
        CoordinationEvent(
            event_id="event-1",
            event_kind="artifact_consumed",
            timestamp="2026-06-16T16:45:00+08:00",
            actor="agent:client",
            artifact_id="server-api",
            artifact_version="v2",
            summary="Client consumed server-api v2 before implementation.",
            related_event_ids=("event:contract-accepted",),
            related_run_ids=("run:client-1",),
            sequence=7,
        )
    )
    projected = event_log.read_all()[0].to_exchange_log()
    artifact = ExchangeArtifact(
        artifact_id="history:client-consumed-contract",
        kind="message",
        intent="inform",
        producer="coordination-event-log",
        version="v1",
        parts=(ExchangePayloadPart(part_type="log", log=projected),),
    )

    assert validate_exchange_artifact(artifact) == ()
    assert artifact.parts[0].log is not None
    assert artifact.parts[0].log.timestamp == "2026-06-16T16:45:00+08:00"
    assert artifact.parts[0].log.actor == "agent:client"
    assert artifact.parts[0].log.action == "artifact_consumed"
    assert artifact.parts[0].log.sequence == 7


def test_coordination_event_log_empty_missing_file_reads_as_empty(tmp_path) -> None:
    event_log = JsonlCoordinationEventLog(tmp_path / "missing.jsonl")

    assert event_log.read_all() == ()


def test_fake_runtime_consumes_input_artifact_and_produces_result_artifact(tmp_path) -> None:
    store = InMemoryArtifactVersionStore()
    event_log = JsonlCoordinationEventLog(tmp_path / "runtime-events.jsonl")
    store.put(_accepted_contract_artifact(version="v1"))
    runtime = FakeAgentRuntimeAdapter(
        artifact_store=store,
        event_log=event_log,
        timestamp="2026-06-16T17:00:00+08:00",
    )
    session = runtime.start_session(AgentSpec(agent_id="agent:test", runtime_provider="fake"))
    task = TaskSpec(
        task_id="task-1",
        title="Use server API contract",
        instruction="Produce a deterministic result from the input contract.",
        input_artifact_refs=(
            ExchangeReference(ref_kind="exchange_artifact", ref_id="server-api", version="v1"),
        ),
        scope=ExchangeScope(task_id="task-1", lane_id="lane-test"),
        acceptance=("result artifact is recorded",),
        output_artifact_id="task-1:result",
    )

    result = runtime.run_task(session, task)
    output_record = store.get("task-1:result", "v1")
    events = event_log.read_all()

    assert result.run_handle.run_id == "fake-run-1"
    assert result.output_artifact is output_record.artifact
    assert result.artifact_delta.artifact_id == "task-1:result"
    assert result.artifact_delta.version == "v1"
    assert [event.event_kind for event in result.events] == [
        "task_started",
        "artifact_consumed",
        "artifact_produced",
        "task_completed",
    ]
    assert part_types(result.output_artifact) == (
        "text",
        "structured",
        "ref",
        "artifact_delta",
    )
    assert result.output_artifact.parts[2].ref is not None
    assert result.output_artifact.parts[2].ref.ref_id == "server-api"
    assert result.output_artifact.parts[2].ref.version == "v1"
    assert len(events) == 5
    assert events[-1].related_run_ids == ("fake-run-1",)


def test_fake_runtime_requires_versioned_input_artifact_ref() -> None:
    runtime = FakeAgentRuntimeAdapter(
        artifact_store=InMemoryArtifactVersionStore(),
        timestamp="2026-06-16T17:00:00+08:00",
    )
    session = runtime.start_session(AgentSpec(agent_id="agent:test", runtime_provider="fake"))
    task = TaskSpec(
        task_id="task-1",
        title="Bad input ref",
        instruction="This should fail before reading latest implicitly.",
        input_artifact_refs=(ExchangeReference(ref_kind="exchange_artifact", ref_id="server-api"),),
    )

    with pytest.raises(ValueError, match="requires a version"):
        runtime.run_task(session, task)


def test_qoder_capability_mapping_is_runtime_not_scheduler() -> None:
    capabilities = qoder_runtime_capabilities()

    assert capabilities.provider == "qoder"
    assert capabilities.supports_sessions is True
    assert capabilities.supports_streaming_events is True
    assert capabilities.supports_subagents is True
    assert capabilities.supports_mcp is True
    assert capabilities.supports_permission_callback is True
    assert capabilities.supports_transcript_inspection is True


def test_codex_cli_capability_mapping_is_runtime_not_scheduler() -> None:
    capabilities = codex_cli_runtime_capabilities()

    assert capabilities.provider == "codex"
    assert capabilities.supports_sessions is True
    assert capabilities.supports_streaming_events is True
    assert capabilities.supports_subagents is False
    assert capabilities.supports_mcp is True
    assert capabilities.supports_permission_callback is True
    assert capabilities.supports_transcript_inspection is False


def test_opencode_cli_capability_mapping_is_runtime_not_scheduler() -> None:
    capabilities = opencode_cli_runtime_capabilities()

    assert capabilities.provider == "opencode"
    assert capabilities.supports_sessions is True
    assert capabilities.supports_streaming_events is False
    assert capabilities.supports_subagents is True
    assert capabilities.supports_mcp is False
    assert capabilities.supports_permission_callback is True
    assert capabilities.supports_transcript_inspection is False


def test_runtime_adapter_registry_registers_and_resolves_by_provider() -> None:
    runtime = FakeAgentRuntimeAdapter(artifact_store=InMemoryArtifactVersionStore())
    registry = AgentRuntimeAdapterRegistry()

    registered = registry.register(runtime)

    assert registered is runtime
    assert registry.get("fake") is runtime
    assert registry.has("fake") is True
    assert registry.has("qoder") is False
    assert registry.providers() == ("fake",)


def test_runtime_adapter_registry_rejects_duplicate_without_replace() -> None:
    first = FakeAgentRuntimeAdapter(artifact_store=InMemoryArtifactVersionStore())
    second = FakeAgentRuntimeAdapter(artifact_store=InMemoryArtifactVersionStore())
    registry = AgentRuntimeAdapterRegistry()
    registry.register(first)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(second)

    replaced = registry.register(second, replace_existing=True)

    assert replaced is second
    assert registry.get("fake") is second


def test_runtime_adapter_registry_rejects_provider_mismatch() -> None:
    runtime = FakeAgentRuntimeAdapter(artifact_store=InMemoryArtifactVersionStore())
    registry = AgentRuntimeAdapterRegistry()

    with pytest.raises(ValueError, match="provider mismatch"):
        registry.register(runtime, provider="qoder")


def test_runtime_adapter_registry_reports_missing_provider_with_available_keys() -> None:
    runtime = FakeAgentRuntimeAdapter(artifact_store=InMemoryArtifactVersionStore())
    registry = AgentRuntimeAdapterRegistry()
    registry.register(runtime)

    with pytest.raises(KeyError, match="available providers: fake"):
        registry.get("qoder")


def test_runtime_registry_wiring_default_registers_fake_only() -> None:
    result = build_runtime_registry_from_config(
        RuntimeRegistryWiringConfig(timestamp="2026-06-17T15:20:00+08:00")
    )

    assert result.registered_providers == ("fake",)
    assert result.registry.has("fake") is True
    assert result.registry.has("qoder") is False


def test_runtime_registry_wiring_accepts_mcp_fake_only_host_invocation() -> None:
    result = build_runtime_registry_from_config(
        RuntimeRegistryWiringConfig(
            providers=("fake",),
            host_invocation=RuntimeHostInvocation(
                surface="mcp-scheduler-run-once",
                invocation_id="mcp-run-1",
                requested_providers=("fake",),
                requested_by="mcp",
            ),
        )
    )

    assert result.registered_providers == ("fake",)
    assert result.config.host_invocation is not None
    assert result.config.host_invocation.surface == "mcp-scheduler-run-once"


def test_runtime_registry_wiring_rejects_qoder_from_fake_only_host_surface() -> None:
    with pytest.raises(ValueError, match="fake-only"):
        build_runtime_registry_from_config(
            RuntimeRegistryWiringConfig(
                providers=("qoder",),
                host_invocation=RuntimeHostInvocation(
                    surface="mcp-scheduler-run-once",
                    invocation_id="mcp-run-qoder",
                    requested_providers=("qoder",),
                    requested_by="mcp",
                ),
            )
        )


def test_runtime_registry_wiring_rejects_host_invocation_provider_mismatch() -> None:
    with pytest.raises(ValueError, match="requested_providers must match"):
        build_runtime_registry_from_config(
            RuntimeRegistryWiringConfig(
                providers=("fake",),
                host_invocation=RuntimeHostInvocation(
                    surface="host-authorized-adapter",
                    invocation_id="host-run-qoder",
                    requested_providers=("qoder",),
                ),
            )
        )


def test_runtime_registry_wiring_requires_explicit_qoder_permission() -> None:
    with pytest.raises(ValueError, match="RuntimeProviderPermissionGrant"):
        build_runtime_registry_from_config(
            RuntimeRegistryWiringConfig(providers=("qoder",))
        )


def test_runtime_registry_wiring_validates_qoder_permission_grant() -> None:
    with pytest.raises(ValueError, match="allow_sdk_client=True"):
        build_runtime_registry_from_config(
            RuntimeRegistryWiringConfig(
                providers=("qoder",),
                qoder_permission_grant=RuntimeProviderPermissionGrant(
                    grant_id="grant-qoder",
                    provider="qoder",
                    approved_by="host:test",
                    approved_at="2026-06-17T15:24:00+08:00",
                ),
            )
        )


def test_runtime_registry_wiring_requires_injected_qoder_client() -> None:
    with pytest.raises(ValueError, match="injected QoderQueryClient"):
        build_runtime_registry_from_config(
            RuntimeRegistryWiringConfig(
                providers=("qoder",),
                qoder_permission_grant=RuntimeProviderPermissionGrant(
                    grant_id="grant-qoder",
                    provider="qoder",
                    approved_by="host:test",
                    approved_at="2026-06-17T15:24:00+08:00",
                    allow_sdk_client=True,
                ),
            )
        )


def test_runtime_registry_wiring_can_register_authorized_mock_qoder_client() -> None:
    client = _RecordingQoderClient(QoderQueryResult(summary="configured qoder"))
    result = build_runtime_registry_from_config(
        RuntimeRegistryWiringConfig(
            providers=("fake", "qoder", "fake"),
            timestamp="2026-06-17T15:25:00+08:00",
            host_invocation=RuntimeHostInvocation(
                surface="host-authorized-adapter",
                invocation_id="host-run-qoder",
                requested_providers=("fake", "qoder"),
                requested_by="host:test",
                reason="mock qoder registry wiring test",
            ),
            qoder_permission_grant=RuntimeProviderPermissionGrant(
                grant_id="grant-qoder",
                provider="qoder",
                approved_by="host:test",
                approved_at="2026-06-17T15:24:00+08:00",
                scope="scheduler-smoke",
                allow_sdk_client=True,
                allow_process_spawn=False,
                allow_network=False,
            ),
        ),
        qoder_query_client=client,
    )

    assert result.registered_providers == ("fake", "qoder")
    assert result.registry.has("fake") is True
    assert result.registry.has("qoder") is True
    assert result.config.qoder_permission_grant is not None
    assert result.config.qoder_permission_grant.grant_id == "grant-qoder"


def test_runtime_registry_wiring_requires_explicit_codex_permission() -> None:
    with pytest.raises(ValueError, match="RuntimeProviderPermissionGrant"):
        build_runtime_registry_from_config(
            RuntimeRegistryWiringConfig(providers=("codex",))
        )


def test_runtime_registry_wiring_validates_codex_permission_grant() -> None:
    with pytest.raises(ValueError, match="allow_process_spawn=True"):
        build_runtime_registry_from_config(
            RuntimeRegistryWiringConfig(
                providers=("codex",),
                codex_permission_grant=RuntimeProviderPermissionGrant(
                    grant_id="grant-codex",
                    provider="codex",
                    approved_by="host:test",
                    approved_at="2026-06-24T22:10:00+08:00",
                ),
            )
        )


def test_runtime_registry_wiring_requires_injected_codex_client() -> None:
    with pytest.raises(ValueError, match="injected CodexCliClient"):
        build_runtime_registry_from_config(
            RuntimeRegistryWiringConfig(
                providers=("codex",),
                codex_permission_grant=RuntimeProviderPermissionGrant(
                    grant_id="grant-codex",
                    provider="codex",
                    approved_by="host:test",
                    approved_at="2026-06-24T22:10:00+08:00",
                    allow_process_spawn=True,
                ),
            )
        )


def test_runtime_registry_wiring_can_register_authorized_mock_codex_client() -> None:
    client = _RecordingCodexCliClient(CodexCliResult(summary="configured codex"))
    result = build_runtime_registry_from_config(
        RuntimeRegistryWiringConfig(
            providers=("fake", "codex", "fake"),
            timestamp="2026-06-24T22:12:00+08:00",
            host_invocation=RuntimeHostInvocation(
                surface="host-authorized-adapter",
                invocation_id="host-run-codex",
                requested_providers=("fake", "codex"),
                requested_by="host:test",
                reason="mock codex registry wiring test",
            ),
            codex_permission_grant=RuntimeProviderPermissionGrant(
                grant_id="grant-codex",
                provider="codex",
                approved_by="host:test",
                approved_at="2026-06-24T22:10:00+08:00",
                scope="scheduler-smoke",
                allow_process_spawn=True,
                allow_network=False,
            ),
        ),
        codex_cli_client=client,
    )

    assert result.registered_providers == ("codex", "fake")
    assert result.registry.has("fake") is True
    assert result.registry.has("codex") is True
    assert result.config.codex_permission_grant is not None
    assert result.config.codex_permission_grant.grant_id == "grant-codex"


def test_runtime_registry_wiring_requires_explicit_opencode_permission() -> None:
    with pytest.raises(ValueError, match="RuntimeProviderPermissionGrant"):
        build_runtime_registry_from_config(
            RuntimeRegistryWiringConfig(providers=("opencode",))
        )


def test_runtime_registry_wiring_validates_opencode_permission_grant() -> None:
    with pytest.raises(ValueError, match="allow_process_spawn=True"):
        build_runtime_registry_from_config(
            RuntimeRegistryWiringConfig(
                providers=("opencode",),
                opencode_permission_grant=RuntimeProviderPermissionGrant(
                    grant_id="grant-opencode",
                    provider="opencode",
                    approved_by="host:test",
                    approved_at="2026-06-28T21:10:00+08:00",
                ),
            )
        )


def test_runtime_registry_wiring_requires_injected_opencode_client() -> None:
    with pytest.raises(ValueError, match="injected OpenCodeCliClient"):
        build_runtime_registry_from_config(
            RuntimeRegistryWiringConfig(
                providers=("opencode",),
                opencode_permission_grant=RuntimeProviderPermissionGrant(
                    grant_id="grant-opencode",
                    provider="opencode",
                    approved_by="host:test",
                    approved_at="2026-06-28T21:10:00+08:00",
                    allow_process_spawn=True,
                ),
            )
        )


def test_runtime_registry_wiring_can_register_authorized_mock_opencode_client() -> None:
    client = _RecordingOpenCodeCliClient(OpenCodeCliResult(summary="configured opencode"))
    result = build_runtime_registry_from_config(
        RuntimeRegistryWiringConfig(
            providers=("fake", "opencode", "fake"),
            timestamp="2026-06-28T21:12:00+08:00",
            host_invocation=RuntimeHostInvocation(
                surface="host-authorized-adapter",
                invocation_id="host-run-opencode",
                requested_providers=("fake", "opencode"),
                requested_by="host:test",
                reason="mock opencode registry wiring test",
            ),
            opencode_permission_grant=RuntimeProviderPermissionGrant(
                grant_id="grant-opencode",
                provider="opencode",
                approved_by="host:test",
                approved_at="2026-06-28T21:10:00+08:00",
                scope="scheduler-smoke",
                allow_process_spawn=True,
                allow_network=False,
            ),
        ),
        opencode_cli_client=client,
    )

    assert result.registered_providers == ("fake", "opencode")
    assert result.registry.has("fake") is True
    assert result.registry.has("opencode") is True
    assert result.config.opencode_permission_grant is not None
    assert result.config.opencode_permission_grant.grant_id == "grant-opencode"


def test_mixed_provider_planner_accepts_codex_and_opencode_workers(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    ledger_path = tmp_path / "admissions.json"
    snapshot_path = tmp_path / "state.json"
    event_log_path = tmp_path / "events.jsonl"
    registry = AgentRuntimeAdapterRegistry()
    registry.register(
        CodexCliAgentRuntimeAdapter(
            cli_client=_RecordingCodexCliClient(
                CodexCliResult(summary="codex lane complete", output_text="codex done")
            )
        )
    )
    registry.register(
        OpenCodeCliAgentRuntimeAdapter(
            cli_client=_RecordingOpenCodeCliClient(
                OpenCodeCliResult(
                    summary="opencode lane complete",
                    output_text="opencode done",
                )
            )
        )
    )

    result = run_guide_worker_local_trajectory_orchestration(
        GuideWorkerLocalOrchestrationRequest(
            artifact_store_path=store_path,
            admission_ledger_path=ledger_path,
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            planning_request=GuideWorkerPlanningRequest(
                task_title="Mixed provider fixture",
                task_summary="Split work across Codex and OpenCode.",
                lane_specs=(
                    GuideWorkerPlannerLaneSpec(
                        lane_id="lane:codex",
                        label="Codex",
                        focus="Codex lane work",
                        worker_runtime_provider="codex",
                    ),
                    GuideWorkerPlannerLaneSpec(
                        lane_id="lane:opencode",
                        label="OpenCode",
                        focus="OpenCode lane work",
                        worker_runtime_provider="opencode",
                    ),
                ),
            ),
            max_parallel_lanes=2,
            max_waves=1,
            replace_existing=True,
            allow_duplicate_admission=True,
        ),
        runtime_registry=registry,
    )

    payload = result.to_json_dict()
    assert result.ok is True
    assert payload["scenario"]["worker_runtime_providers"] == ["codex", "opencode"]
    assert sorted(payload["run_task_ids"]) == [
        "task/guide-worker-local-orchestration/codex",
        "task/guide-worker-local-orchestration/opencode",
    ]


def test_mixed_provider_host_wrapper_fails_before_state_when_opencode_missing(
    tmp_path: Path,
) -> None:
    snapshot_path = tmp_path / ".codex/scheduler/mixed-state.json"
    event_log_path = tmp_path / ".codex/scheduler/mixed-events.jsonl"
    evidence_path = tmp_path / ".codex/scheduler/evidence/mixed.json"
    runtime_log_path = tmp_path / ".codex/runtime/invocations.jsonl"
    opencode_client = OpenCodeCliProcessClient(
        OpenCodeCliClientConfig(executable="definitely-missing-dbc-opencode"),
        which=lambda _executable: None,
    )

    with pytest.raises(OpenCodeCliRuntimeError, match="cli_unavailable"):
        run_host_owned_guide_worker_provider_execution(
            tmp_path,
            config=HostOwnedGuideWorkerProviderExecutionConfig(
                evidence_id="mixed-provider-negative",
                timestamp="2026-06-28T23:20:00+08:00",
                snapshot_path=snapshot_path,
                event_log_path=event_log_path,
                evidence_output_path=evidence_path,
                runtime_invocation_log_path=runtime_log_path,
                providers=("codex", "opencode"),
                planning_request=GuideWorkerPlanningRequest(
                    task_title="Mixed provider negative readiness",
                    task_summary="Codex is injected but OpenCode is missing.",
                    lane_specs=(
                        GuideWorkerPlannerLaneSpec(
                            lane_id="lane:codex",
                            label="Codex",
                            focus="Codex lane",
                            worker_runtime_provider="codex",
                        ),
                        GuideWorkerPlannerLaneSpec(
                            lane_id="lane:opencode",
                            label="OpenCode",
                            focus="OpenCode lane",
                            worker_runtime_provider="opencode",
                        ),
                    ),
                ),
            ),
            codex_cli_client=_RecordingCodexCliClient(
                CodexCliResult(summary="codex would be ready")
            ),
            opencode_cli_client=opencode_client,
        )

    assert snapshot_path.exists() is False
    assert event_log_path.exists() is False
    assert evidence_path.exists() is False
    assert runtime_log_path.exists() is False


def test_runtime_registry_wiring_rejects_empty_provider_set() -> None:
    with pytest.raises(ValueError, match="requires at least one provider"):
        build_runtime_registry_from_config(RuntimeRegistryWiringConfig(providers=()))


def test_qoder_adapter_uses_mock_query_client_and_returns_runtime_result() -> None:
    client = _RecordingQoderClient(
        QoderQueryResult(
            summary="Qoder completed bounded task.",
            output_text="Qoder result body.",
            artifact_delta=ArtifactDelta(
                artifact_id="task-q:artifact",
                version="v2",
                summary="changed generated files",
                changed_refs=(
                    ExchangeReference(ref_kind="file", ref_id="src/app.py", path="src/app.py"),
                ),
            ),
            permission_requests=(
                PermissionRequest(
                    request_id="perm-1",
                    request_kind="artifact_write",
                    run_id="pending",
                    summary="Qoder wants to write src/app.py",
                    target="src/app.py",
                ),
            ),
            metadata={"turns": 3},
        )
    )
    adapter = QoderAgentRuntimeAdapter(
        query_client=client,
        timestamp="2026-06-16T22:30:00+08:00",
    )
    agent = AgentSpec(
        agent_id="agent:qoder",
        runtime_provider="qoder",
        model="qoder-model",
        tools=("read", "edit"),
    )
    session = adapter.start_session(agent)
    task = TaskSpec(
        task_id="task-q",
        title="Qoder task",
        instruction="Run through mock qoder client.",
        output_artifact_id="task-q:result",
    )

    result = adapter.run_task(session, task)

    assert adapter.capabilities().provider == "qoder"
    assert client.requests[0].agent == agent
    assert client.requests[0].task == task
    assert client.requests[0].session == session
    assert client.requests[0].instruction == "Run through mock qoder client."
    assert client.requests[0].output_artifact_id == "task-q:result"
    assert result.run_handle.run_id == "qoder-run-1"
    assert result.output_artifact.artifact_id == "task-q:artifact"
    assert result.output_artifact.version == "v2"
    assert result.artifact_delta.summary == "changed generated files"
    assert part_types(result.output_artifact) == ("text", "structured", "artifact_delta")
    assert result.output_artifact.parts[1].data["metadata"] == {"turns": 3}
    assert [event.event_kind for event in result.events] == ["task_started", "task_completed"]
    assert result.permission_requests[0].request_kind == "artifact_write"
    assert result.permission_requests[0].target == "src/app.py"


def test_codex_cli_adapter_uses_mock_client_and_returns_runtime_result() -> None:
    client = _RecordingCodexCliClient(
        CodexCliResult(
            summary="Codex completed bounded task.",
            output_text="Codex result body.",
            artifact_delta=ArtifactDelta(
                artifact_id="task-c:artifact",
                version="v2",
                summary="changed generated files",
                changed_refs=(
                    ExchangeReference(ref_kind="file", ref_id="src/app.py", path="src/app.py"),
                ),
            ),
            permission_requests=(
                PermissionRequest(
                    request_id="perm-1",
                    request_kind="shell",
                    run_id="pending",
                    summary="Codex wants to run npm test",
                    target="npm test",
                ),
            ),
            metadata={"turns": 2},
        )
    )
    adapter = CodexCliAgentRuntimeAdapter(
        cli_client=client,
        timestamp="2026-06-24T22:20:00+08:00",
    )
    agent = AgentSpec(
        agent_id="agent:codex",
        runtime_provider="codex",
        model="gpt-5-codex",
        tools=("read", "edit"),
    )
    session = adapter.start_session(agent)
    task = TaskSpec(
        task_id="task-c",
        title="Codex task",
        instruction="Run through mock codex client.",
        output_artifact_id="task-c:result",
    )

    result = adapter.run_task(session, task)

    assert adapter.capabilities().provider == "codex"
    assert client.requests[0].agent == agent
    assert client.requests[0].task == task
    assert client.requests[0].session == session
    assert client.requests[0].instruction == "Run through mock codex client."
    assert client.requests[0].output_artifact_id == "task-c:result"
    assert result.run_handle.run_id == "codex-run-1"
    assert result.output_artifact.artifact_id == "task-c:artifact"
    assert result.output_artifact.version == "v2"
    assert result.artifact_delta.summary == "changed generated files"
    assert part_types(result.output_artifact) == ("text", "structured", "artifact_delta")
    assert result.output_artifact.parts[1].data["metadata"] == {"turns": 2}
    assert [event.event_kind for event in result.events] == ["task_started", "task_completed"]
    assert result.permission_requests[0].request_kind == "shell"
    assert result.permission_requests[0].target == "npm test"


def test_opencode_cli_adapter_uses_mock_client_and_returns_runtime_result() -> None:
    client = _RecordingOpenCodeCliClient(
        OpenCodeCliResult(
            summary="OpenCode completed bounded task.",
            output_text="OpenCode result body.",
            artifact_delta=ArtifactDelta(
                artifact_id="task-o:artifact",
                version="v2",
                summary="changed generated files",
                changed_refs=(
                    ExchangeReference(ref_kind="file", ref_id="src/app.py", path="src/app.py"),
                ),
            ),
            permission_requests=(
                PermissionRequest(
                    request_id="perm-1",
                    request_kind="shell",
                    run_id="pending",
                    summary="OpenCode wants to run npm test",
                    target="npm test",
                ),
            ),
            metadata={"events": 2},
        )
    )
    adapter = OpenCodeCliAgentRuntimeAdapter(
        cli_client=client,
        timestamp="2026-06-28T21:20:00+08:00",
    )
    agent = AgentSpec(
        agent_id="agent:opencode",
        runtime_provider="opencode",
        model="anthropic/claude-sonnet-4",
        tools=("read", "edit"),
    )
    session = adapter.start_session(agent)
    task = TaskSpec(
        task_id="task-o",
        title="OpenCode task",
        instruction="Run through mock opencode client.",
        output_artifact_id="task-o:result",
    )

    result = adapter.run_task(session, task)

    assert adapter.capabilities().provider == "opencode"
    assert client.requests[0].agent == agent
    assert client.requests[0].task == task
    assert client.requests[0].session == session
    assert client.requests[0].instruction == "Run through mock opencode client."
    assert client.requests[0].output_artifact_id == "task-o:result"
    assert result.run_handle.run_id == "opencode-run-1"
    assert result.output_artifact.artifact_id == "task-o:artifact"
    assert result.output_artifact.version == "v2"
    assert result.artifact_delta.summary == "changed generated files"
    assert part_types(result.output_artifact) == ("text", "structured", "artifact_delta")
    assert result.output_artifact.parts[1].data["metadata"] == {"events": 2}
    assert [event.event_kind for event in result.events] == ["task_started", "task_completed"]
    assert result.permission_requests[0].request_kind == "shell"
    assert result.permission_requests[0].target == "npm test"


def test_codex_cli_process_client_prefers_task_runtime_workspace(tmp_path) -> None:
    captured: dict[str, object] = {}
    workspace = tmp_path / "worker-worktree"
    workspace.mkdir()

    def runner(command, **kwargs):
        captured["command"] = command
        captured["cwd"] = kwargs.get("cwd")
        output_path = Path(command[command.index("--output-last-message") + 1])
        output_path.write_text("done from worker workspace\n", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    client = CodexCliProcessClient(
        CodexCliClientConfig(executable="codex", cwd=tmp_path / "source-root"),
        runner=runner,
        which=lambda executable: f"/bin/{executable}",
    )
    result = client.exec(
        CodexCliRequest(
            agent=AgentSpec(agent_id="agent:codex", runtime_provider="codex"),
            session=SessionHandle(
                session_id="codex-session-1",
                provider="codex",
                agent_id="agent:codex",
            ),
            task=TaskSpec(
                task_id="task-c",
                title="Codex sandbox task",
                instruction="Run in the worker sandbox.",
                runtime_workspace_root=str(workspace),
                sandbox_provider="git-worktree",
                sandbox_allocation_id="git-worktree:task-c:worktree",
                visible_mounts=("src/app.py",),
                scratch_path=".codex/scratch/task-c",
            ),
            instruction="Run in the worker sandbox.",
        )
    )

    assert result.summary == "done from worker workspace"
    assert captured["cwd"] == str(workspace)
    command = captured["command"]
    assert isinstance(command, list)
    assert command[0] == "/bin/codex"
    assert command[command.index("--cd") + 1] == str(workspace)
    assert result.metadata["cwd"] == str(workspace)


def test_opencode_cli_process_client_prefers_task_runtime_workspace(tmp_path) -> None:
    captured: dict[str, object] = {}
    workspace = tmp_path / "worker-worktree"
    workspace.mkdir()

    def runner(command, **kwargs):
        captured["command"] = command
        captured["cwd"] = kwargs.get("cwd")
        captured["input"] = kwargs.get("input")
        return subprocess.CompletedProcess(
            command,
            0,
            stdout='{"type":"message","text":"done from opencode workspace"}\n',
            stderr="",
        )

    client = OpenCodeCliProcessClient(
        OpenCodeCliClientConfig(executable="opencode", cwd=tmp_path / "source-root"),
        runner=runner,
        which=lambda executable: f"/bin/{executable}",
    )
    result = client.exec(
        OpenCodeCliRequest(
            agent=AgentSpec(agent_id="agent:opencode", runtime_provider="opencode"),
            session=SessionHandle(
                session_id="opencode-session-1",
                provider="opencode",
                agent_id="agent:opencode",
            ),
            task=TaskSpec(
                task_id="task-o",
                title="OpenCode sandbox task",
                instruction="Run in the worker sandbox.",
                runtime_workspace_root=str(workspace),
                sandbox_provider="git-worktree",
                sandbox_allocation_id="git-worktree:task-o:worktree",
                visible_mounts=("src/app.py",),
                scratch_path=".codex/scratch/task-o",
            ),
            instruction="Run in the worker sandbox.",
        )
    )

    assert result.summary == "done from opencode workspace"
    assert result.output_text == "done from opencode workspace"
    assert captured["cwd"] == str(workspace)
    assert captured["input"] is None
    command = captured["command"]
    assert isinstance(command, list)
    assert command[:2] == ["/bin/opencode", "run"]
    assert command[command.index("--dir") + 1] == str(workspace)
    assert command[command.index("--format") + 1] == "json"
    assert "Runtime workspace root:" in command[-1]
    assert result.metadata["cwd"] == str(workspace)


def test_opencode_cli_process_client_can_attach_to_server_session(tmp_path) -> None:
    captured: dict[str, object] = {}

    def runner(command, **kwargs):
        captured["command"] = command
        captured["cwd"] = kwargs.get("cwd")
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="done from attached opencode session\n",
            stderr="",
        )

    client = OpenCodeCliProcessClient(
        OpenCodeCliClientConfig(
            executable="opencode",
            cwd=tmp_path,
            output_format="text",
            attach_url="http://127.0.0.1:4096",
            session_id="session-opencode-1",
            fork_session=True,
        ),
        runner=runner,
        which=lambda executable: f"/bin/{executable}",
    )

    result = client.exec(
        OpenCodeCliRequest(
            agent=AgentSpec(agent_id="agent:opencode", runtime_provider="opencode"),
            session=SessionHandle(
                session_id="dbc-opencode-session",
                provider="opencode",
                agent_id="agent:opencode",
            ),
            task=TaskSpec(
                task_id="task-o-attach",
                title="OpenCode attached task",
                instruction="Run through an attached OpenCode server session.",
            ),
            instruction="Run through an attached OpenCode server session.",
        )
    )

    command = captured["command"]
    assert isinstance(command, list)
    assert command[:2] == ["/bin/opencode", "run"]
    assert command[command.index("--attach") + 1] == "http://127.0.0.1:4096"
    assert command[command.index("--session") + 1] == "session-opencode-1"
    assert "--fork" in command
    assert command[command.index("--format") + 1] == "default"
    assert result.output_text == "done from attached opencode session"
    assert result.metadata["attached_to_server"] is True
    assert result.metadata["attach_url"] == "http://127.0.0.1:4096"
    assert result.metadata["session_id"] == "session-opencode-1"
    assert result.metadata["fork_session"] is True


def test_opencode_cli_process_client_uses_host_session_selector(tmp_path) -> None:
    captured: dict[str, object] = {}

    def runner(command, **kwargs):
        captured["command"] = command
        return subprocess.CompletedProcess(
            command,
            0,
            stdout="done from ledger session\n",
            stderr="",
        )

    client = OpenCodeCliProcessClient(
        OpenCodeCliClientConfig(
            executable="opencode",
            cwd=tmp_path,
            output_format="text",
        ),
        runner=runner,
        which=lambda executable: f"/bin/{executable}",
    )
    result = client.exec(
        OpenCodeCliRequest(
            agent=AgentSpec(agent_id="agent:opencode", runtime_provider="opencode"),
            session=SessionHandle(
                session_id="dbc-opencode-session",
                provider="opencode",
                agent_id="agent:opencode",
            ),
            task=TaskSpec(
                task_id="task-o-ledger",
                title="OpenCode ledger task",
                instruction="Run through a ledger-selected OpenCode session.",
            ),
            instruction="Run through a ledger-selected OpenCode session.",
            host_session=OpenCodeHostSessionSelector(
                attach_url="http://127.0.0.1:4096",
                session_id="session-ledger-1",
                fork_session=True,
                binding_id="opencode-session:lane:lane-server",
                scope_kind="lane",
                scope_id="lane:server",
                ledger_path=".codex/runtime/opencode-session-ledger.json",
            ),
        )
    )

    command = captured["command"]
    assert isinstance(command, list)
    assert command[command.index("--attach") + 1] == "http://127.0.0.1:4096"
    assert command[command.index("--session") + 1] == "session-ledger-1"
    assert "--fork" in command
    assert result.metadata["session_selector_source"] == "session_ledger"
    assert result.metadata["fork_session"] is True
    assert result.metadata["host_session_selector"]["binding_id"] == (
        "opencode-session:lane:lane-server"
    )


def test_opencode_cli_process_client_explicit_session_overrides_host_selector(
    tmp_path,
) -> None:
    captured: dict[str, object] = {}

    def runner(command, **kwargs):
        captured["command"] = command
        return subprocess.CompletedProcess(command, 0, stdout="done\n", stderr="")

    client = OpenCodeCliProcessClient(
        OpenCodeCliClientConfig(
            executable="opencode",
            cwd=tmp_path,
            output_format="text",
            attach_url="http://127.0.0.1:5099",
            session_id="session-explicit",
        ),
        runner=runner,
        which=lambda executable: f"/bin/{executable}",
    )
    result = client.exec(
        OpenCodeCliRequest(
            agent=AgentSpec(agent_id="agent:opencode", runtime_provider="opencode"),
            session=SessionHandle(
                session_id="dbc-opencode-session",
                provider="opencode",
                agent_id="agent:opencode",
            ),
            task=TaskSpec(
                task_id="task-o-explicit",
                title="OpenCode explicit task",
                instruction="Run through explicit OpenCode session flags.",
            ),
            instruction="Run through explicit OpenCode session flags.",
            host_session=OpenCodeHostSessionSelector(
                attach_url="http://127.0.0.1:4096",
                session_id="session-ledger-1",
            ),
        )
    )

    command = captured["command"]
    assert isinstance(command, list)
    assert command[command.index("--attach") + 1] == "http://127.0.0.1:5099"
    assert command[command.index("--session") + 1] == "session-explicit"
    assert result.metadata["session_selector_source"] == "explicit_config"


def test_opencode_cli_process_client_validates_session_config() -> None:
    with pytest.raises(ValueError, match="cannot set both session_id and continue_session"):
        OpenCodeCliClientConfig(session_id="session-1", continue_session=True)

    with pytest.raises(ValueError, match="fork_session requires session_id or continue_session"):
        OpenCodeCliClientConfig(fork_session=True)


def test_opencode_serve_readiness_reports_healthy_attach_target_without_secrets() -> None:
    captured: dict[str, object] = {}

    class Response:
        status = 200

    def opener(request, **kwargs):
        captured["url"] = request.full_url
        captured["authorization"] = request.headers.get("Authorization", "")
        captured["timeout"] = kwargs.get("timeout")
        return Response()

    report = inspect_opencode_serve_readiness(
        OpenCodeServeReadinessRequest(
            executable="opencode",
            attach_url="http://127.0.0.1:4096",
            health_timeout_seconds=1.5,
            require_healthy=True,
            metadata={"surface": "test"},
        ),
        which=lambda executable: f"/bin/{executable}",
        opener=opener,
        environ={
            "OPENCODE_SERVER_USERNAME": "operator",
            "OPENCODE_SERVER_PASSWORD": "super-secret",
        },
    )
    payload = report.to_json_dict()

    assert report.ready is True
    assert report.healthy is True
    assert report.attach_url == "http://127.0.0.1:4096"
    assert report.health_url == "http://127.0.0.1:4096/global/health"
    assert captured["url"] == "http://127.0.0.1:4096/global/health"
    assert captured["timeout"] == 1.5
    assert str(captured["authorization"]).startswith("Basic ")
    assert "super-secret" not in json.dumps(payload, sort_keys=True)
    assert payload["auth_configured"] is True
    assert payload["authority_split"]["server_started"] is False
    assert payload["authority_split"]["secret_value_persisted"] is False


def test_opencode_serve_readiness_fails_closed_when_cli_missing() -> None:
    def opener(*args, **kwargs):
        raise AssertionError("health check should not run without CLI")

    report = inspect_opencode_serve_readiness(
        OpenCodeServeReadinessRequest(executable="missing-opencode", require_healthy=True),
        which=lambda executable: None,
        opener=opener,
    )
    payload = report.to_json_dict()

    assert report.ready is False
    assert report.cli_available is False
    assert report.health_checked is False
    assert report.error_kind == "cli_unavailable"
    assert payload["authority_split"]["provider_executed"] is False


def test_opencode_serve_readiness_can_require_healthy_server() -> None:
    def opener(*args, **kwargs):
        raise TimeoutError("server did not answer")

    soft = inspect_opencode_serve_readiness(
        OpenCodeServeReadinessRequest(require_healthy=False),
        which=lambda executable: f"/bin/{executable}",
        opener=opener,
    )
    strict = inspect_opencode_serve_readiness(
        OpenCodeServeReadinessRequest(require_healthy=True),
        which=lambda executable: f"/bin/{executable}",
        opener=opener,
    )

    assert soft.ready is True
    assert soft.healthy is False
    assert soft.error_kind == "server_unreachable"
    assert strict.ready is False
    assert strict.healthy is False
    assert strict.error_kind == "server_unreachable"


def test_opencode_server_api_readiness_reports_health_and_doc_without_secrets() -> None:
    captured: list[str] = []

    def opener(request, **kwargs):
        captured.append(request.full_url)
        if request.full_url.endswith("/global/health"):
            return _JsonHttpResponse({"status": "ok", "version": "test"}, status=200)
        if request.full_url.endswith("/doc"):
            return _JsonHttpResponse(
                {
                    "openapi": "3.1.0",
                    "info": {"title": "OpenCode API", "version": "1.2.3"},
                },
                status=200,
            )
        raise AssertionError(f"unexpected URL: {request.full_url}")

    report = inspect_opencode_server_api_readiness(
        OpenCodeServerApiClientConfig(base_url="http://127.0.0.1:4096"),
        check_doc=True,
        opener=opener,
        environ={"OPENCODE_SERVER_PASSWORD": "secret-value"},
    )
    payload = report.to_json_dict()

    assert report.ready is True
    assert payload["healthy"] is True
    assert payload["doc_available"] is True
    assert payload["openapi_version"] == "3.1.0"
    assert payload["api_title"] == "OpenCode API"
    assert payload["auth_configured"] is True
    assert payload["authority_split"]["server_api_called"] is True
    assert payload["authority_split"]["provider_executed"] is False
    assert "secret-value" not in json.dumps(payload)
    assert captured == [
        "http://127.0.0.1:4096/global/health",
        "http://127.0.0.1:4096/doc",
    ]


def test_opencode_server_api_readiness_reports_unreachable() -> None:
    def opener(*args, **kwargs):
        raise TimeoutError("server did not answer")

    report = inspect_opencode_server_api_readiness(
        OpenCodeServerApiClientConfig(base_url="http://127.0.0.1:4096"),
        opener=opener,
    )

    assert report.ready is False
    assert report.error_kind == "server_unreachable"
    assert report.to_json_dict()["authority_split"]["provider_executed"] is False


def test_opencode_server_api_client_creates_session_and_sends_prompt() -> None:
    calls: list[tuple[str, str, dict[str, object]]] = []

    def opener(request, **kwargs):
        payload = _request_json_payload(request)
        calls.append((request.get_method(), request.full_url, payload))
        if request.full_url.endswith("/session"):
            return _JsonHttpResponse({"id": "session-created"})
        if request.full_url.endswith("/session/session-created/message"):
            return _JsonHttpResponse({"message": {"content": "server api done"}})
        raise AssertionError(f"unexpected URL: {request.full_url}")

    client = OpenCodeServerApiClient(
        OpenCodeServerApiClientConfig(base_url="http://127.0.0.1:4096"),
        opener=opener,
    )

    result = client.exec(_opencode_server_api_request())

    assert result.summary == "server api done"
    assert result.output_text == "server api done"
    assert result.metadata["transport"] == "server-api"
    assert result.metadata["created_session"] is True
    assert result.metadata["session_id"] == "session-created"
    assert result.metadata["session_selector_source"] == "server_api_created"
    assert result.metadata["session_persistence"] == "not_persisted_by_delivery"
    assert result.metadata["server_api_created_session_persisted"] is False
    assert result.metadata["server_api_created_session_persistence_authority"] == (
        "explicit_host_owned_claim_required"
    )
    assert calls[0][0] == "POST"
    assert calls[0][1] == "http://127.0.0.1:4096/session"
    assert calls[1][1] == "http://127.0.0.1:4096/session/session-created/message"
    assert "Task ID: task-opencode-api" in str(calls[1][2])


def test_opencode_server_api_client_uses_explicit_session_without_creation() -> None:
    calls: list[str] = []

    def opener(request, **kwargs):
        calls.append(request.full_url)
        if request.full_url.endswith("/session/session-explicit/message"):
            return _JsonHttpResponse({"content": "explicit session done"})
        raise AssertionError(f"unexpected URL: {request.full_url}")

    client = OpenCodeServerApiClient(
        OpenCodeServerApiClientConfig(
            base_url="http://127.0.0.1:4096",
            session_id="session-explicit",
        ),
        opener=opener,
    )

    result = client.exec(_opencode_server_api_request())

    assert result.summary == "explicit session done"
    assert result.metadata["created_session"] is False
    assert result.metadata["session_selector_source"] == "explicit_config"
    assert result.metadata["session_persistence"] == "preexisting_selector"
    assert result.metadata["server_api_created_session_persisted"] is False
    assert calls == ["http://127.0.0.1:4096/session/session-explicit/message"]


def test_opencode_server_api_client_maps_http_failure_to_runtime_error() -> None:
    def opener(request, **kwargs):
        if request.full_url.endswith("/session"):
            return _JsonHttpResponse({"id": "session-created"})
        raise urllib.error.HTTPError(
            request.full_url,
            401,
            "unauthorized",
            hdrs=None,
            fp=None,
        )

    client = OpenCodeServerApiClient(
        OpenCodeServerApiClientConfig(base_url="http://127.0.0.1:4096"),
        opener=opener,
    )

    with pytest.raises(OpenCodeCliRuntimeError) as excinfo:
        client.exec(_opencode_server_api_request())

    assert excinfo.value.error_kind == "authentication_failed"
    assert excinfo.value.raw_error_type == "HTTP401"


def test_opencode_serve_lifecycle_receipts_record_and_inspect(tmp_path: Path) -> None:
    ledger_path = tmp_path / ".codex/runtime/opencode-serve-lifecycle-ledger.json"

    recorded = record_opencode_serve_lifecycle_receipt(
        OpenCodeServeLifecycleRecordRequest(
            ledger_path=ledger_path,
            action="start",
            status="observed",
            executable="opencode",
            hostname="127.0.0.1",
            port=4096,
            timestamp="2026-06-29T12:00:00+00:00",
            pid="4242",
            actor="host:test",
            reason="operator started OpenCode serve for worker session reuse",
        )
    )
    inspected = inspect_opencode_serve_lifecycle_receipts(
        OpenCodeServeLifecycleInspectRequest(
            ledger_path=ledger_path,
            action="start",
            latest_limit=1,
        )
    )

    assert recorded.ok is True
    assert recorded.receipt is not None
    assert recorded.receipt.action == "start"
    assert recorded.receipt.status == "observed"
    assert recorded.receipt.attach_url == "http://127.0.0.1:4096"
    assert recorded.receipt.command_preview == (
        "opencode",
        "serve",
        "--hostname",
        "127.0.0.1",
        "--port",
        "4096",
    )
    assert recorded.to_json_dict()["authority_split"]["serve_lifecycle_ledger_mutated"] is True
    assert recorded.to_json_dict()["authority_split"]["server_started"] is False
    assert recorded.to_json_dict()["authority_split"]["provider_executed"] is False
    assert inspected.ok is True
    assert inspected.ledger_mutated is False
    assert len(inspected.receipts) == 1
    assert inspected.receipts[0].pid == "4242"
    payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "opencode-serve-lifecycle-ledger.v1"
    assert "transcript" not in json.dumps(payload).lower()
    assert "secret" not in json.dumps(payload).lower()


def test_opencode_serve_lifecycle_receipts_validate_action_and_status(tmp_path: Path) -> None:
    ledger_path = tmp_path / ".codex/runtime/opencode-serve-lifecycle-ledger.json"

    with pytest.raises(ValueError, match="action must be start"):
        record_opencode_serve_lifecycle_receipt(
            OpenCodeServeLifecycleRecordRequest(
                ledger_path=ledger_path,
                action="launch",  # type: ignore[arg-type]
            )
        )

    with pytest.raises(ValueError, match="status must be planned"):
        inspect_opencode_serve_lifecycle_receipts(
            OpenCodeServeLifecycleInspectRequest(
                ledger_path=ledger_path,
                status="running",
            )
        )


def test_opencode_session_ledger_claim_inspect_release_roundtrip(tmp_path: Path) -> None:
    ledger_path = tmp_path / ".codex/runtime/opencode-session-ledger.json"

    claimed = claim_opencode_session_binding(
        OpenCodeSessionClaimRequest(
            ledger_path=ledger_path,
            scope_kind="lane",
            scope_id="lane:server",
            attach_url="http://127.0.0.1:4096",
            session_id="ses_123",
            owner_agent_id="agent:guide",
            lane_id="lane:server",
            worker_agent_id="agent:server",
            reason="reuse server lane context",
            timestamp="2026-06-29T10:00:00+00:00",
        )
    )
    inspected = inspect_opencode_session_bindings(
        OpenCodeSessionInspectRequest(
            ledger_path=ledger_path,
            scope_kind="lane",
            scope_id="lane:server",
        )
    )
    released = release_opencode_session_binding(
        OpenCodeSessionReleaseRequest(
            ledger_path=ledger_path,
            scope_kind="lane",
            scope_id="lane:server",
            timestamp="2026-06-29T11:00:00+00:00",
        )
    )
    active_after_release = inspect_opencode_session_bindings(
        OpenCodeSessionInspectRequest(ledger_path=ledger_path)
    )
    all_after_release = inspect_opencode_session_bindings(
        OpenCodeSessionInspectRequest(ledger_path=ledger_path, include_released=True)
    )

    assert claimed.ok is True
    assert claimed.binding is not None
    assert claimed.binding.binding_id == "opencode-session:lane:lane-server"
    assert claimed.binding.status == "active"
    assert claimed.to_json_dict()["authority_split"]["provider_executed"] is False
    assert inspected.ok is True
    assert len(inspected.bindings) == 1
    assert inspected.bindings[0].session_id == "ses_123"
    assert released.ok is True
    assert released.binding is not None
    assert released.binding.status == "released"
    assert active_after_release.bindings == ()
    assert len(all_after_release.bindings) == 1
    assert all_after_release.bindings[0].status == "released"
    payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "opencode-session-ledger.v1"
    assert "transcript" not in json.dumps(payload).lower()


def test_opencode_session_ledger_claim_conflict_without_replace(tmp_path: Path) -> None:
    ledger_path = tmp_path / ".codex/runtime/opencode-session-ledger.json"
    first = claim_opencode_session_binding(
        OpenCodeSessionClaimRequest(
            ledger_path=ledger_path,
            scope_kind="agent",
            scope_id="agent:worker",
            attach_url="http://127.0.0.1:4096",
            session_id="session-a",
        )
    )
    second = claim_opencode_session_binding(
        OpenCodeSessionClaimRequest(
            ledger_path=ledger_path,
            scope_kind="agent",
            scope_id="agent:worker",
            attach_url="http://127.0.0.1:4096",
            session_id="session-b",
            replace_existing=False,
        )
    )

    assert first.ok is True
    assert second.ok is False
    assert second.status == "conflict"
    assert second.binding is not None
    assert second.binding.session_id == "session-a"


def test_opencode_session_recover_stale_expires_elapsed_binding(tmp_path: Path) -> None:
    ledger_path = tmp_path / ".codex/runtime/opencode-session-ledger.json"
    claim_opencode_session_binding(
        OpenCodeSessionClaimRequest(
            ledger_path=ledger_path,
            scope_kind="lane",
            scope_id="lane:expired",
            attach_url="http://127.0.0.1:4096",
            session_id="session-expired",
            expires_at="2026-06-29T09:00:00+00:00",
        )
    )
    claim_opencode_session_binding(
        OpenCodeSessionClaimRequest(
            ledger_path=ledger_path,
            scope_kind="lane",
            scope_id="lane:active",
            attach_url="http://127.0.0.1:4096",
            session_id="session-active",
            expires_at="2026-06-29T11:00:00+00:00",
        )
    )

    recovered = recover_stale_opencode_session_bindings(
        OpenCodeSessionRecoverStaleRequest(
            ledger_path=ledger_path,
            now="2026-06-29T10:00:00+00:00",
            timestamp="2026-06-29T10:00:01+00:00",
        )
    )
    active = inspect_opencode_session_bindings(
        OpenCodeSessionInspectRequest(ledger_path=ledger_path)
    )
    all_bindings = inspect_opencode_session_bindings(
        OpenCodeSessionInspectRequest(ledger_path=ledger_path, include_released=True)
    )

    assert recovered.ok is True
    assert recovered.status == "expired_stale_bindings"
    assert recovered.checked_count == 2
    assert recovered.expired_count == 1
    assert recovered.bindings[0].scope_id == "lane:expired"
    assert recovered.stale_reasons[recovered.bindings[0].binding_id] == "expires_at elapsed"
    assert [binding.scope_id for binding in active.bindings] == ["lane:active"]
    expired = next(binding for binding in all_bindings.bindings if binding.scope_id == "lane:expired")
    assert expired.status == "expired"
    assert expired.metadata["stale_recovery_reason"] == "expires_at elapsed"


def test_opencode_session_recover_stale_can_expire_unhealthy_binding(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / ".codex/runtime/opencode-session-ledger.json"
    claim_opencode_session_binding(
        OpenCodeSessionClaimRequest(
            ledger_path=ledger_path,
            scope_kind="lane",
            scope_id="lane:server",
            attach_url="http://127.0.0.1:4096",
            session_id="session-server",
        )
    )

    recovered = recover_stale_opencode_session_bindings(
        OpenCodeSessionRecoverStaleRequest(
            ledger_path=ledger_path,
            now="2026-06-29T10:00:00+00:00",
            expire_unhealthy=True,
        ),
        health_inspector=lambda binding, request: "attach target unhealthy: server_unreachable",
    )

    assert recovered.ok is True
    assert recovered.expired_count == 1
    assert recovered.bindings[0].status == "expired"
    assert recovered.stale_reasons[recovered.bindings[0].binding_id] == (
        "attach target unhealthy: server_unreachable"
    )


def test_opencode_session_recover_stale_noops_without_matching_policy(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / ".codex/runtime/opencode-session-ledger.json"
    claim_opencode_session_binding(
        OpenCodeSessionClaimRequest(
            ledger_path=ledger_path,
            scope_kind="lane",
            scope_id="lane:server",
            attach_url="http://127.0.0.1:4096",
            session_id="session-server",
            expires_at="2026-06-29T11:00:00+00:00",
        )
    )

    recovered = recover_stale_opencode_session_bindings(
        OpenCodeSessionRecoverStaleRequest(
            ledger_path=ledger_path,
            now="2026-06-29T10:00:00+00:00",
        )
    )

    assert recovered.ok is True
    assert recovered.status == "no_stale_bindings"
    assert recovered.ledger_mutated is False
    assert recovered.expired_count == 0


def test_continuous_worker_binding_claim_inspect_release_roundtrip(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / ".codex/runtime/continuous-worker-bindings.json"
    event_log_path = tmp_path / ".codex/runtime/continuous-worker-binding-events.jsonl"

    claimed = claim_continuous_worker_binding(
        ContinuousWorkerBindingClaimRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            worker_id="worker:server",
            runtime_provider="opencode",
            scope_kind="lane",
            scope_id="lane:server",
            lane_ids=("lane:server",),
            active_session_selector=ContinuousWorkerSessionSelector(
                provider="opencode",
                attach_url="http://127.0.0.1:4096",
                session_id="session-server-lane",
            ),
            compact_context_ref="dbc://context/worker-server-compact",
            audit_refs=("audit:claim-server",),
            timestamp="2026-06-29T09:00:00+00:00",
            expires_at="2026-06-29T10:00:00+00:00",
            reason="reuse server lane context",
        )
    )
    inspected = inspect_continuous_worker_bindings(
        ContinuousWorkerBindingInspectRequest(
            ledger_path=ledger_path,
            scope_kind="lane",
            scope_id="lane:server",
        )
    )
    released = release_continuous_worker_binding(
        ContinuousWorkerBindingReleaseRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            scope_kind="lane",
            scope_id="lane:server",
            timestamp="2026-06-29T09:05:00+00:00",
            reason="lane completed",
        )
    )
    active_after_release = inspect_continuous_worker_bindings(
        ContinuousWorkerBindingInspectRequest(ledger_path=ledger_path)
    )
    all_after_release = inspect_continuous_worker_bindings(
        ContinuousWorkerBindingInspectRequest(
            ledger_path=ledger_path,
            include_inactive=True,
        )
    )
    events = JsonlContinuousWorkerBindingEventLog(event_log_path).read_all()

    assert claimed.ok is True
    assert claimed.binding is not None
    assert claimed.binding.worker_id == "worker:server"
    assert claimed.binding.active_session_selector is not None
    assert claimed.binding.active_session_selector.session_id == "session-server-lane"
    assert claimed.to_json_dict()["authority_split"]["provider_executed"] is False
    assert inspected.bindings == (claimed.binding,)
    assert released.ok is True
    assert released.binding is not None
    assert released.binding.lifecycle_status == "released"
    assert active_after_release.bindings == ()
    assert len(all_after_release.bindings) == 1
    assert [event.event_kind for event in events] == [
        "binding_claimed",
        "binding_released",
    ]
    assert events[0].binding_id == claimed.binding.binding_id


def test_server_api_created_session_promotion_claims_continuous_worker_binding(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / ".codex/runtime/continuous-worker-bindings.json"
    event_log_path = tmp_path / ".codex/runtime/continuous-worker-binding-events.jsonl"
    opencode_session_ledger_path = tmp_path / ".codex/runtime/opencode-session-ledger.json"

    promoted = promote_server_api_created_session_to_continuous_worker_binding(
        ServerApiCreatedSessionPromotionRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            attach_url="http://127.0.0.1:4096/",
            session_id="session-created-api",
            worker_id="worker:server",
            scope_kind="lane",
            scope_id="lane:server",
            audit_refs=("audit:server-api-created",),
            timestamp="2026-06-30T15:10:00+00:00",
            expires_at="2026-06-30T16:10:00+00:00",
            metadata={"source_delivery_id": "delivery:server-api"},
        )
    )
    inspected = inspect_continuous_worker_bindings(
        ContinuousWorkerBindingInspectRequest(
            ledger_path=ledger_path,
            scope_kind="lane",
            scope_id="lane:server",
        )
    )
    events = JsonlContinuousWorkerBindingEventLog(event_log_path).read_all()

    assert promoted.ok is True
    assert promoted.status == "promoted"
    assert promoted.binding_claimed is True
    assert promoted.binding is not None
    assert promoted.binding == inspected.bindings[0]
    assert promoted.binding.runtime_provider == "opencode"
    assert promoted.binding.lane_ids == ("lane:server",)
    assert promoted.binding.metadata["promotion_source"] == "server_api_created"
    assert promoted.binding.metadata["promotion_authority"] == "explicit_host_owned_claim"
    assert promoted.binding.active_session_selector is not None
    assert promoted.binding.active_session_selector.attach_url == "http://127.0.0.1:4096"
    assert promoted.binding.active_session_selector.session_id == "session-created-api"
    assert promoted.to_json_dict()["authority_split"]["provider_executed"] is False
    assert promoted.to_json_dict()["authority_split"]["delivery_state_mutated"] is False
    assert promoted.to_json_dict()["authority_split"]["local_work_trajectory_mutated"] is False
    assert [event.event_kind for event in events] == ["binding_claimed"]
    assert events[0].metadata["promotion_source"] == "server_api_created"
    assert events[0].metadata["session_selector_source"] == "server_api_created"
    assert not opencode_session_ledger_path.exists()


def test_server_api_created_session_promotion_supports_lane_group(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / ".codex/runtime/continuous-worker-bindings.json"
    promoted = promote_server_api_created_session_to_continuous_worker_binding(
        ServerApiCreatedSessionPromotionRequest(
            ledger_path=ledger_path,
            event_log_path=tmp_path / ".codex/runtime/continuous-worker-binding-events.jsonl",
            attach_url="http://127.0.0.1:4096",
            session_id="session-web",
            worker_id="worker:web",
            scope_kind="lane_group",
            scope_id="lane-group:web",
            lane_ids=("lane:client", "lane:server"),
            timestamp="2026-06-30T15:11:00+00:00",
        )
    )

    assert promoted.ok is True
    assert promoted.binding is not None
    assert promoted.binding.scope_kind == "lane_group"
    assert promoted.binding.lane_ids == ("lane:client", "lane:server")
    assert promoted.binding.owned_lane_ids == ("lane:client", "lane:server")


@pytest.mark.parametrize(
    "selector_source",
    ["explicit_config", "session_ledger", "continuous_worker_binding", "none"],
)
def test_server_api_created_session_promotion_rejects_non_created_sources(
    tmp_path: Path,
    selector_source: str,
) -> None:
    with pytest.raises(ValueError, match="session_selector_source=server_api_created"):
        promote_server_api_created_session_to_continuous_worker_binding(
            ServerApiCreatedSessionPromotionRequest(
                ledger_path=tmp_path / ".codex/runtime/continuous-worker-bindings.json",
                event_log_path=tmp_path / ".codex/runtime/continuous-worker-binding-events.jsonl",
                session_selector_source=selector_source,
                attach_url="http://127.0.0.1:4096",
                session_id="session-created-api",
                worker_id="worker:server",
                scope_kind="lane",
                scope_id="lane:server",
            )
        )


@pytest.mark.parametrize(
    ("field_name", "override"),
    [
        ("attach_url", {"attach_url": ""}),
        ("session_id", {"session_id": ""}),
        ("scope_id", {"scope_id": ""}),
        ("worker_id", {"worker_id": ""}),
    ],
)
def test_server_api_created_session_promotion_rejects_missing_required_fields(
    tmp_path: Path,
    field_name: str,
    override: dict[str, object],
) -> None:
    payload = {
        "ledger_path": tmp_path / ".codex/runtime/continuous-worker-bindings.json",
        "event_log_path": tmp_path / ".codex/runtime/continuous-worker-binding-events.jsonl",
        "attach_url": "http://127.0.0.1:4096",
        "session_id": "session-created-api",
        "worker_id": "worker:server",
        "scope_kind": "lane",
        "scope_id": "lane:server",
    }
    payload.update(override)

    with pytest.raises(ValueError, match=field_name):
        promote_server_api_created_session_to_continuous_worker_binding(
            ServerApiCreatedSessionPromotionRequest(**payload)  # type: ignore[arg-type]
        )


def test_server_api_created_session_promotion_rejects_lane_group_without_lanes(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="lane_ids"):
        promote_server_api_created_session_to_continuous_worker_binding(
            ServerApiCreatedSessionPromotionRequest(
                ledger_path=tmp_path / ".codex/runtime/continuous-worker-bindings.json",
                event_log_path=tmp_path / ".codex/runtime/continuous-worker-binding-events.jsonl",
                attach_url="http://127.0.0.1:4096",
                session_id="session-web",
                worker_id="worker:web",
                scope_kind="lane_group",
                scope_id="lane-group:web",
            )
        )


def test_server_api_created_session_promotion_rejects_secret_metadata(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="raw transcript or secret value"):
        promote_server_api_created_session_to_continuous_worker_binding(
            ServerApiCreatedSessionPromotionRequest(
                ledger_path=tmp_path / ".codex/runtime/continuous-worker-bindings.json",
                event_log_path=tmp_path / ".codex/runtime/continuous-worker-binding-events.jsonl",
                attach_url="http://127.0.0.1:4096",
                session_id="session-created-api",
                worker_id="worker:server",
                scope_kind="lane",
                scope_id="lane:server",
                metadata={"api_key": "should-not-persist"},
            )
        )


def test_continuous_worker_binding_recover_stale_and_lane_group_resolution(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / ".codex/runtime/continuous-worker-bindings.json"
    event_log_path = tmp_path / ".codex/runtime/continuous-worker-binding-events.jsonl"
    claim_continuous_worker_binding(
        ContinuousWorkerBindingClaimRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            worker_id="worker:ui-and-api",
            runtime_provider="opencode",
            scope_kind="lane_group",
            scope_id="lane-group:web",
            lane_ids=("lane:client", "lane:server"),
            active_session_selector=ContinuousWorkerSessionSelector(
                provider="opencode",
                attach_url="http://127.0.0.1:4096",
                session_id="session-web-group",
            ),
            timestamp="2026-06-29T09:10:00+00:00",
            expires_at="2026-06-29T09:30:00+00:00",
        )
    )
    before = inspect_continuous_worker_bindings(
        ContinuousWorkerBindingInspectRequest(
            ledger_path=ledger_path,
            lane_id="lane:server",
        )
    )
    stale = recover_stale_continuous_worker_bindings(
        ContinuousWorkerBindingRecoverStaleRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            now="2026-06-29T09:31:00+00:00",
            timestamp="2026-06-29T09:31:01+00:00",
        )
    )
    after = inspect_continuous_worker_bindings(
        ContinuousWorkerBindingInspectRequest(
            ledger_path=ledger_path,
            lane_id="lane:server",
        )
    )
    all_bindings = inspect_continuous_worker_bindings(
        ContinuousWorkerBindingInspectRequest(
            ledger_path=ledger_path,
            lane_id="lane:server",
            include_inactive=True,
        )
    )

    assert len(before.bindings) == 1
    assert before.bindings[0].scope_kind == "lane_group"
    assert stale.ok is True
    assert stale.stale_count == 1
    assert stale.bindings[0].lifecycle_status == "stale"
    assert after.bindings == ()
    assert all_bindings.bindings[0].lifecycle_status == "stale"


def test_continuous_worker_binding_reuse_fork_compact_and_expiry_resolution(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / ".codex/runtime/continuous-worker-bindings.json"
    event_log_path = tmp_path / ".codex/runtime/continuous-worker-binding-events.jsonl"
    claimed = claim_continuous_worker_binding(
        ContinuousWorkerBindingClaimRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            worker_id="worker:server",
            runtime_provider="opencode",
            scope_kind="lane",
            scope_id="lane:server",
            active_session_selector=ContinuousWorkerSessionSelector(
                provider="opencode",
                attach_url="http://127.0.0.1:4096",
                session_id="session-server",
            ),
            compact_context_ref="dbc://context/server-v1",
            timestamp="2026-06-29T09:00:00+00:00",
            expires_at="2026-06-29T10:00:00+00:00",
        )
    )

    reused = record_continuous_worker_binding_reuse(
        ContinuousWorkerBindingReuseRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            binding_id=claimed.binding.binding_id,  # type: ignore[union-attr]
            task_id="task-server-1",
            agent_id="agent:server",
            lane_id="lane:server",
            timestamp="2026-06-29T09:05:00+00:00",
            audit_refs=("audit:delivery-1",),
        )
    )
    compacted = compact_continuous_worker_binding(
        ContinuousWorkerBindingCompactRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            binding_id=claimed.binding.binding_id,  # type: ignore[union-attr]
            compact_context_ref="dbc://context/server-v2",
            mailbox_cursor_ref="dbc://mailbox/server@42",
            worker_report_refs=("report:server-1",),
            audit_refs=("audit:compact-1",),
            timestamp="2026-06-29T09:10:00+00:00",
        )
    )
    forked = fork_continuous_worker_binding(
        ContinuousWorkerBindingForkRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            source_binding_id=claimed.binding.binding_id,  # type: ignore[union-attr]
            worker_id="worker:server-experiment",
            scope_kind="lane",
            scope_id="lane:server-experiment",
            timestamp="2026-06-29T09:15:00+00:00",
            audit_refs=("audit:fork-1",),
        )
    )
    before_expiry = resolve_continuous_worker_binding(
        ContinuousWorkerBindingResolveRequest(
            ledger_path=ledger_path,
            runtime_provider="opencode",
            lane_id="lane:server",
            timestamp="2026-06-29T09:59:00+00:00",
        )
    )
    after_expiry = resolve_continuous_worker_binding(
        ContinuousWorkerBindingResolveRequest(
            ledger_path=ledger_path,
            runtime_provider="opencode",
            lane_id="lane:server",
            timestamp="2026-06-29T10:01:00+00:00",
        )
    )
    events = JsonlContinuousWorkerBindingEventLog(event_log_path).read_all()

    assert reused.ok is True
    assert reused.binding is not None
    assert reused.binding.last_used_at == "2026-06-29T09:05:00+00:00"
    assert "audit:delivery-1" in reused.binding.audit_refs
    assert compacted.ok is True
    assert compacted.binding is not None
    assert compacted.binding.compact_context_ref == "dbc://context/server-v2"
    assert compacted.binding.mailbox_cursor_ref == "dbc://mailbox/server@42"
    assert compacted.binding.worker_report_refs == ("report:server-1",)
    assert forked.ok is True
    assert forked.binding is not None
    assert forked.binding.scope_id == "lane:server-experiment"
    assert forked.binding.active_session_selector is not None
    assert forked.binding.active_session_selector.fork_session is True
    assert forked.binding.metadata["forked_from_binding_id"] == claimed.binding.binding_id  # type: ignore[union-attr]
    assert before_expiry.ok is True
    assert before_expiry.binding is not None
    assert before_expiry.binding.binding_id == claimed.binding.binding_id  # type: ignore[union-attr]
    assert after_expiry.ok is False
    assert after_expiry.status == "not_found"
    assert [event.event_kind for event in events] == [
        "binding_claimed",
        "binding_reused",
        "binding_compacted",
        "binding_forked",
    ]


def test_continuous_worker_binding_archive_has_distinct_event(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / ".codex/runtime/continuous-worker-bindings.json"
    event_log_path = tmp_path / ".codex/runtime/continuous-worker-binding-events.jsonl"
    claim_continuous_worker_binding(
        ContinuousWorkerBindingClaimRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            worker_id="worker:archive",
            runtime_provider="opencode",
            scope_kind="lane",
            scope_id="lane:archive",
            active_session_selector=ContinuousWorkerSessionSelector(
                provider="opencode",
                session_id="session-archive",
            ),
        )
    )

    archived = release_continuous_worker_binding(
        ContinuousWorkerBindingReleaseRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            scope_kind="lane",
            scope_id="lane:archive",
            lifecycle_status="archived",
            timestamp="2026-06-29T13:20:00+00:00",
            reason="lane archived after merge",
        )
    )
    events = JsonlContinuousWorkerBindingEventLog(event_log_path).read_all()

    assert archived.ok is True
    assert archived.binding is not None
    assert archived.binding.lifecycle_status == "archived"
    assert events[-1].event_kind == "binding_archived"
    assert events[-1].next_status == "archived"


def test_continuous_worker_ownership_schema_lane_ownership_round_trips() -> None:
    ownership = LaneOwnership(
        ownership_id="lane-ownership:server",
        scope_kind="lane",
        scope_id="lane:server",
        lane_ids=("lane:server",),
        binding_id="continuous-worker:lane:server",
        worker_id="worker:server",
        status="active",
        created_at="2026-06-30T09:00:00+00:00",
        activated_at="2026-06-30T09:05:00+00:00",
        updated_at="2026-06-30T09:06:00+00:00",
        reason="server lane first delivery succeeded",
        audit_refs=("audit:ownership-activated",),
    )

    restored = lane_ownership_from_json_dict(ownership.to_json_dict())

    assert restored == ownership
    assert restored.to_json_dict()["authority_split"]["provider_executed"] is False


def test_continuous_worker_lane_ownership_claim_inspect_roundtrip(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / ".codex/runtime/continuous-worker-lane-ownerships.json"
    event_log_path = tmp_path / ".codex/runtime/continuous-worker-lane-ownership-events.jsonl"

    claimed = claim_lane_ownership(
        LaneOwnershipClaimRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            scope_kind="lane",
            scope_id="lane:server",
            binding_id="continuous-worker:lane:server",
            worker_id="worker:server",
            timestamp="2026-06-30T10:00:00+00:00",
            requested_by="host:test",
            audit_refs=("audit:claim",),
            metadata={"source": "unit-test"},
        )
    )
    inspected = inspect_lane_ownerships(
        LaneOwnershipInspectRequest(ledger_path=ledger_path, lane_id="lane:server")
    )
    allows_delivery = lane_ownership_allows_delivery(
        ledger_path,
        binding_id="continuous-worker:lane:server",
        lane_id="lane:server",
    )
    ledger = read_lane_ownership_ledger(ledger_path)
    events = JsonlLaneOwnershipEventLog(event_log_path).read_all()

    assert claimed.ok is True
    assert claimed.ownership is not None
    assert claimed.ownership.status == "claimed"
    assert claimed.ownership.lane_ids == ("lane:server",)
    assert inspected.ownerships == (claimed.ownership,)
    assert inspected.selectable is True
    assert allows_delivery is True
    assert ledger.ownerships == (claimed.ownership,)
    assert [event.event_kind for event in events] == ["lane_ownership_claimed"]
    assert events[0].metadata["requested_by"] == "host:test"


def test_continuous_worker_lane_ownership_lane_group_conflict_and_release(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / ".codex/runtime/continuous-worker-lane-ownerships.json"
    event_log_path = tmp_path / ".codex/runtime/continuous-worker-lane-ownership-events.jsonl"

    group_claim = claim_lane_ownership(
        LaneOwnershipClaimRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            scope_kind="lane_group",
            scope_id="lane-group:web",
            lane_ids=("lane:server", "lane:client"),
            binding_id="continuous-worker:lane-group:web",
            worker_id="worker:web",
            timestamp="2026-06-30T10:01:00+00:00",
        )
    )
    conflict = claim_lane_ownership(
        LaneOwnershipClaimRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            scope_kind="lane",
            scope_id="lane:server",
            binding_id="continuous-worker:lane:server",
            worker_id="worker:server",
            timestamp="2026-06-30T10:01:01+00:00",
        )
    )
    release = release_lane_ownership(
        LaneOwnershipReleaseRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            binding_id="continuous-worker:lane-group:web",
            timestamp="2026-06-30T10:01:02+00:00",
        )
    )
    lane_claim = claim_lane_ownership(
        LaneOwnershipClaimRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            scope_kind="lane",
            scope_id="lane:server",
            binding_id="continuous-worker:lane:server",
            worker_id="worker:server",
            timestamp="2026-06-30T10:01:03+00:00",
        )
    )
    active = inspect_lane_ownerships(
        LaneOwnershipInspectRequest(ledger_path=ledger_path, include_inactive=False)
    )
    all_records = inspect_lane_ownerships(
        LaneOwnershipInspectRequest(ledger_path=ledger_path, include_inactive=True)
    )

    assert group_claim.ok is True
    assert group_claim.ownership is not None
    assert group_claim.ownership.lane_ids == ("lane:server", "lane:client")
    assert conflict.ok is False
    assert conflict.status == "conflict"
    assert "lane ownership conflict: lane already has active owner" in conflict.message
    assert "allowed=transferOwnership|releaseOwnership|suspendOwnership" in conflict.message
    assert release.ok is True
    assert release.ownership is not None
    assert release.ownership.status == "released"
    assert lane_claim.ok is True
    assert tuple(item.binding_id for item in active.ownerships) == (
        "continuous-worker:lane:server",
    )
    assert len(all_records.ownerships) == 2


def test_continuous_worker_lane_ownership_lifecycle_transitions(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / ".codex/runtime/continuous-worker-lane-ownerships.json"
    event_log_path = tmp_path / ".codex/runtime/continuous-worker-lane-ownership-events.jsonl"

    claim_lane_ownership(
        LaneOwnershipClaimRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            scope_kind="lane",
            scope_id="lane:server",
            binding_id="continuous-worker:lane:server",
            worker_id="worker:server",
            timestamp="2026-06-30T10:02:00+00:00",
        )
    )
    activated = activate_lane_ownership(
        LaneOwnershipActivateRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            binding_id="continuous-worker:lane:server",
            activated_at="2026-06-30T10:02:01+00:00",
            delivery_id="delivery:server",
            task_id="task:server",
        )
    )
    suspended = suspend_lane_ownership(
        LaneOwnershipSuspendRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            binding_id="continuous-worker:lane:server",
            timestamp="2026-06-30T10:02:02+00:00",
            reason="waiting for dependency",
        )
    )
    disallowed_while_suspended = lane_ownership_allows_delivery(
        ledger_path,
        binding_id="continuous-worker:lane:server",
        lane_id="lane:server",
    )
    resumed = resume_lane_ownership(
        LaneOwnershipResumeRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            binding_id="continuous-worker:lane:server",
            timestamp="2026-06-30T10:02:03+00:00",
        )
    )
    transferred = transfer_lane_ownership(
        LaneOwnershipTransferRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            binding_id="continuous-worker:lane:server",
            replacement_binding_id="continuous-worker:lane:server-v2",
            timestamp="2026-06-30T10:02:04+00:00",
        )
    )
    active = inspect_lane_ownerships(
        LaneOwnershipInspectRequest(ledger_path=ledger_path, include_inactive=False)
    )
    events = JsonlLaneOwnershipEventLog(event_log_path).read_all()

    assert activated.ok is True
    assert activated.ownership is not None
    assert activated.ownership.status == "active"
    assert suspended.ok is True
    assert suspended.ownership is not None
    assert suspended.ownership.status == "suspended"
    assert suspended.selectable is False
    assert disallowed_while_suspended is False
    assert resumed.ok is True
    assert resumed.ownership is not None
    assert resumed.ownership.status == "active"
    assert transferred.ok is True
    assert transferred.ownership is not None
    assert transferred.ownership.status == "transferred"
    assert transferred.ownership.replacement_binding_id == (
        "continuous-worker:lane:server-v2"
    )
    assert transferred.selectable is False
    assert active.ownerships == ()
    assert [event.event_kind for event in events] == [
        "lane_ownership_claimed",
        "lane_ownership_activated",
        "lane_ownership_suspended",
        "lane_ownership_resumed",
        "lane_ownership_transferred",
    ]


def test_continuous_worker_lane_ownership_conflict_helpers_and_delivery_allowance() -> None:
    active = LaneOwnership(
        ownership_id="lane-ownership:server",
        scope_kind="lane",
        scope_id="lane:server",
        lane_ids=("lane:server",),
        binding_id="continuous-worker:lane:server",
        worker_id="worker:server",
        status="active",
    )
    claimed_group = LaneOwnership(
        ownership_id="lane-ownership:web",
        scope_kind="lane_group",
        scope_id="lane-group:web",
        lane_ids=("lane:server", "lane:client"),
        binding_id="continuous-worker:lane-group:web",
        worker_id="worker:web",
        status="claimed",
    )
    suspended = LaneOwnership(
        ownership_id="lane-ownership:suspended",
        scope_kind="lane",
        scope_id="lane:suspended",
        lane_ids=("lane:suspended",),
        binding_id="continuous-worker:lane:suspended",
        worker_id="worker:suspended",
        status="suspended",
    )

    conflicts = selectable_lane_ownership_conflicts((active, claimed_group, suspended))

    assert conflicts == ((active, claimed_group),)
    with pytest.raises(
        ValueError,
        match="lane ownership conflict: lane already has active owner",
    ):
        validate_no_selectable_lane_ownership_conflicts((active, claimed_group))
    validate_no_selectable_lane_ownership_conflicts((active, suspended))


def test_continuous_worker_lane_ownership_rejects_secret_metadata(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="lane ownership rejected: raw transcript or secret value is not allowed",
    ):
        claim_lane_ownership(
            LaneOwnershipClaimRequest(
                ledger_path=tmp_path / "lane-ownerships.json",
                event_log_path=tmp_path / "lane-ownership-events.jsonl",
                scope_kind="lane",
                scope_id="lane:server",
                binding_id="continuous-worker:lane:server",
                worker_id="worker:server",
                metadata={"raw_transcript": "full provider transcript"},
            )
        )


def test_continuous_worker_ownership_schema_delivery_lease_round_trips() -> None:
    lease = DeliveryLease(
        lease_id="lease:server-1",
        binding_id="continuous-worker:lane:server",
        task_id="task:server-1",
        delivery_id="delivery:server-1",
        status="running",
        reserved_at="2026-06-30T09:00:00+00:00",
        started_at="2026-06-30T09:00:03+00:00",
        expires_at="2026-06-30T09:10:00+00:00",
        result_ref="",
        audit_refs=("audit:lease-started",),
    )

    restored = delivery_lease_from_json_dict(lease.to_json_dict())

    assert restored == lease
    assert restored.to_json_dict()["authority_split"]["scheduler_state_mutated"] is False


def test_continuous_worker_ownership_schema_binding_fields_round_trip(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / ".codex/runtime/continuous-worker-bindings.json"
    event_log_path = tmp_path / ".codex/runtime/continuous-worker-binding-events.jsonl"

    claimed = claim_continuous_worker_binding(
        ContinuousWorkerBindingClaimRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            binding_id="continuous-worker:lane:server",
            worker_id="worker:server",
            runtime_provider="opencode",
            scope_kind="lane",
            scope_id="lane:server",
            lane_ids=("lane:server",),
            active_session_selector=ContinuousWorkerSessionSelector(
                provider="opencode",
                session_id="session-server",
            ),
            generation=2,
            parent_binding_id="continuous-worker:lane:server-parent",
            owned_lane_ids=("lane:server",),
            private_storage_ref="dbc://agent-home/continuous-worker/custom-server",
            private_storage_policy_ref="dbc://agent-home-policy/custom-retain",
            compact_policy_ref="dbc://compact-policy/server",
            compact_policy_default="manual",
            last_compact_at="2026-06-30T08:30:00+00:00",
            compact_needed=True,
            timestamp="2026-06-30T09:00:00+00:00",
        )
    )

    assert claimed.binding is not None
    payload = claimed.binding.to_json_dict()
    restored = continuous_worker_binding_from_json_dict(payload)
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    restored_from_ledger = continuous_worker_binding_from_json_dict(
        ledger["bindings"][0]
    )

    assert restored == claimed.binding
    assert restored_from_ledger == claimed.binding
    assert restored.generation == 2
    assert restored.parent_binding_id == "continuous-worker:lane:server-parent"
    assert restored.owned_lane_ids == ("lane:server",)
    assert restored.private_storage_ref == "dbc://agent-home/continuous-worker/custom-server"
    assert restored.private_storage_policy_ref == "dbc://agent-home-policy/custom-retain"
    assert restored.compact_policy_ref == "dbc://compact-policy/server"
    assert restored.compact_policy_default == "manual"
    assert restored.last_compact_at == "2026-06-30T08:30:00+00:00"
    assert restored.compact_needed is True


def test_continuous_worker_ownership_schema_defaults_private_storage_and_auto_compact() -> None:
    binding = ContinuousWorkerBinding(
        binding_id="continuous-worker:lane:server",
        worker_id="worker:server",
        runtime_provider="opencode",
        scope_kind="lane",
        scope_id="lane:server",
        lane_ids=("lane:server",),
        active_session_selector=ContinuousWorkerSessionSelector(
            provider="opencode",
            session_id="session-server",
        ),
    )

    assert binding.private_storage_ref == (
        "dbc://agent-home/continuous-worker/continuous-worker:lane:server"
    )
    assert binding.private_storage_policy_ref.endswith(
        "default-retain-after-owned-lanes-merge"
    )
    assert binding.compact_policy_default == "auto"
    assert binding.owned_lane_ids == ("lane:server",)
    assert "has_private_storage" not in binding.to_json_dict()


def test_continuous_worker_ownership_schema_rejects_has_private_storage() -> None:
    payload = {
        "binding_id": "continuous-worker:lane:server",
        "worker_id": "worker:server",
        "runtime_provider": "opencode",
        "scope_kind": "lane",
        "scope_id": "lane:server",
        "has_private_storage": True,
    }

    with pytest.raises(
        ValueError,
        match="worker binding schema rejected: private storage is a derived invariant",
    ):
        continuous_worker_binding_from_json_dict(payload)


def test_continuous_worker_ownership_schema_manual_compact_keeps_auto_fallback() -> None:
    accepted = continuous_worker_binding_from_json_dict(
        {
            "binding_id": "continuous-worker:lane:server",
            "worker_id": "worker:server",
            "runtime_provider": "opencode",
            "scope_kind": "lane",
            "scope_id": "lane:server",
            "compact_policy_default": "manual",
            "metadata": {"manual_compact": "operator-triggered"},
        }
    )

    assert accepted.compact_policy_default == "manual"
    with pytest.raises(
        ValueError,
        match="compact policy rejected: manual compact cannot disable auto fallback",
    ):
        continuous_worker_binding_from_json_dict(
            {
                "binding_id": "continuous-worker:lane:server",
                "worker_id": "worker:server",
                "runtime_provider": "opencode",
                "scope_kind": "lane",
                "scope_id": "lane:server",
                "compact_policy_default": "manual",
                "metadata": {"auto_fallback_disabled": True},
            }
        )


def test_continuous_worker_ownership_schema_accepts_llm_auto_as_future_policy_value() -> None:
    binding = continuous_worker_binding_from_json_dict(
        {
            "binding_id": "continuous-worker:lane:research",
            "worker_id": "worker:research",
            "runtime_provider": "opencode",
            "scope_kind": "lane",
            "scope_id": "lane:research",
            "compact_policy_default": "llm-auto",
            "metadata": {"future_policy_slot": "no model invocation in schema slice"},
        }
    )

    assert binding.compact_policy_default == "llm-auto"
    assert binding.metadata["future_policy_slot"] == "no model invocation in schema slice"


def test_continuous_worker_ownership_schema_rejects_raw_transcript_or_secret_like_fields() -> None:
    with pytest.raises(
        ValueError,
        match="worker binding rejected: raw transcript or secret value is not allowed",
    ):
        continuous_worker_binding_from_json_dict(
            {
                "binding_id": "continuous-worker:lane:server",
                "worker_id": "worker:server",
                "runtime_provider": "opencode",
                "scope_kind": "lane",
                "scope_id": "lane:server",
                "metadata": {"raw_transcript": "full provider output"},
            }
        )

    with pytest.raises(
        ValueError,
        match="delivery lease rejected: raw transcript or secret value is not allowed",
    ):
        delivery_lease_from_json_dict(
            {
                "lease_id": "lease:server",
                "binding_id": "continuous-worker:lane:server",
                "task_id": "task:server",
                "delivery_id": "delivery:server",
                "audit_refs": ("audit:lease",),
                "metadata": {"failure_detail": "api_key=abc123"},
            }
        )


def test_continuous_worker_ownership_schema_detects_active_delivery_lease_conflicts() -> None:
    running = DeliveryLease(
        lease_id="lease:server-running",
        binding_id="continuous-worker:lane:server",
        task_id="task:server-1",
        delivery_id="delivery:server-1",
        status="running",
    )
    reserved = DeliveryLease(
        lease_id="lease:server-reserved",
        binding_id="continuous-worker:lane:server",
        task_id="task:server-2",
        delivery_id="delivery:server-2",
        status="reserved",
    )
    completed = DeliveryLease(
        lease_id="lease:server-completed",
        binding_id="continuous-worker:lane:server",
        task_id="task:server-0",
        delivery_id="delivery:server-0",
        status="completed",
    )

    conflicts = active_delivery_lease_conflicts((running, completed, reserved))

    assert conflicts == ((running, reserved),)
    with pytest.raises(
        ValueError,
        match="delivery lease conflict: binding already has active lease",
    ):
        validate_no_active_delivery_lease_conflicts((running, reserved))
    validate_no_active_delivery_lease_conflicts((running, completed))


def test_continuous_worker_delivery_lease_ledger_round_trip_and_conflict(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / ".codex/runtime/continuous-worker-delivery-leases.json"
    event_log_path = tmp_path / ".codex/runtime/continuous-worker-delivery-lease-events.jsonl"

    reserved = reserve_delivery_lease(
        DeliveryLeaseReserveRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            binding_id="continuous-worker:lane:server",
            task_id="task:server-1",
            delivery_id="delivery:server-1",
            reserved_at="2026-06-30T09:00:00+00:00",
            audit_refs=("audit:reserve",),
            metadata={"lane_id": "lane:server"},
        )
    )
    conflict = reserve_delivery_lease(
        DeliveryLeaseReserveRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            binding_id="continuous-worker:lane:server",
            task_id="task:server-2",
            delivery_id="delivery:server-2",
            reserved_at="2026-06-30T09:00:01+00:00",
        )
    )
    ledger = read_delivery_lease_ledger(ledger_path)
    events = JsonlDeliveryLeaseEventLog(event_log_path).read_all()

    assert reserved.ok is True
    assert reserved.lease is not None
    assert reserved.lease.status == "reserved"
    assert conflict.ok is False
    assert conflict.status == "active_conflict"
    assert len(ledger.leases) == 1
    assert ledger.leases[0] == reserved.lease
    assert [event.event_kind for event in events] == ["delivery_lease_reserved"]
    assert events[0].metadata["lane_id"] == "lane:server"
    assert ledger.to_json_dict()["authority_split"]["provider_executed"] is False


def test_continuous_worker_delivery_lease_transitions_release_then_rereserve(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / ".codex/runtime/continuous-worker-delivery-leases.json"
    event_log_path = tmp_path / ".codex/runtime/continuous-worker-delivery-lease-events.jsonl"

    reserve = reserve_delivery_lease(
        DeliveryLeaseReserveRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            lease_id="lease:server-1",
            binding_id="continuous-worker:lane:server",
            task_id="task:server-1",
            delivery_id="delivery:server-1",
            reserved_at="2026-06-30T09:00:00+00:00",
        )
    )
    begin = begin_delivery_lease_run(
        DeliveryLeaseBeginRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            lease_id="lease:server-1",
            started_at="2026-06-30T09:00:01+00:00",
            audit_refs=("opencode-delivery:run-1",),
        )
    )
    complete = complete_delivery_lease(
        DeliveryLeaseCompleteRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            lease_id="lease:server-1",
            completed_at="2026-06-30T09:00:05+00:00",
            result_ref="opencode-delivery:run-1",
        )
    )
    release = release_delivery_lease(
        DeliveryLeaseReleaseRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            lease_id="lease:server-1",
            released_at="2026-06-30T09:00:06+00:00",
        )
    )
    second = reserve_delivery_lease(
        DeliveryLeaseReserveRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            lease_id="lease:server-2",
            binding_id="continuous-worker:lane:server",
            task_id="task:server-2",
            delivery_id="delivery:server-2",
            reserved_at="2026-06-30T09:00:07+00:00",
        )
    )
    active = inspect_delivery_leases(
        DeliveryLeaseInspectRequest(
            ledger_path=ledger_path,
            include_inactive=False,
        )
    )
    events = JsonlDeliveryLeaseEventLog(event_log_path).read_all()

    assert reserve.ok is True
    assert begin.ok is True
    assert complete.ok is True
    assert release.ok is True
    assert second.ok is True
    assert release.lease is not None
    assert release.lease.status == "released"
    assert active.leases == (second.lease,)
    assert [event.event_kind for event in events] == [
        "delivery_lease_reserved",
        "delivery_lease_started",
        "delivery_lease_completed",
        "delivery_lease_released",
        "delivery_lease_reserved",
    ]


def test_continuous_worker_delivery_lease_failed_retryable_does_not_block_rereserve(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / ".codex/runtime/continuous-worker-delivery-leases.json"
    event_log_path = tmp_path / ".codex/runtime/continuous-worker-delivery-lease-events.jsonl"

    reserve_delivery_lease(
        DeliveryLeaseReserveRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            lease_id="lease:server-failure",
            binding_id="continuous-worker:lane:server",
            task_id="task:server-1",
            delivery_id="delivery:server-1",
            reserved_at="2026-06-30T09:00:00+00:00",
        )
    )
    failed = fail_delivery_lease_retryable(
        DeliveryLeaseFailRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            lease_id="lease:server-failure",
            failed_at="2026-06-30T09:00:05+00:00",
            failure_kind="timeout",
            result_ref="opencode-delivery:run-failure",
        )
    )
    next_reserve = reserve_delivery_lease(
        DeliveryLeaseReserveRequest(
            ledger_path=ledger_path,
            event_log_path=event_log_path,
            lease_id="lease:server-retry",
            binding_id="continuous-worker:lane:server",
            task_id="task:server-2",
            delivery_id="delivery:server-2",
            reserved_at="2026-06-30T09:00:06+00:00",
        )
    )

    assert failed.ok is True
    assert failed.lease is not None
    assert failed.lease.status == "failed_retryable"
    assert next_reserve.ok is True
    assert next_reserve.lease is not None
    assert next_reserve.lease.status == "reserved"


def test_continuous_worker_delivery_lease_rejects_secret_metadata(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        ValueError,
        match="delivery lease rejected: raw transcript or secret value is not allowed",
    ):
        reserve_delivery_lease(
            DeliveryLeaseReserveRequest(
                ledger_path=tmp_path / "leases.json",
                event_log_path=tmp_path / "lease-events.jsonl",
                binding_id="continuous-worker:lane:server",
                task_id="task:server",
                delivery_id="delivery:server",
                metadata={"raw_transcript": "full provider transcript"},
            )
        )


def test_continuous_worker_compact_context_bundle_is_project_owned(
    tmp_path: Path,
) -> None:
    ledger_path = tmp_path / ".codex/runtime/continuous-worker-bindings.json"
    bundle_dir = tmp_path / ".codex/runtime/continuous-worker-contexts"
    claim_continuous_worker_binding(
        ContinuousWorkerBindingClaimRequest(
            ledger_path=ledger_path,
            worker_id="worker:server",
            runtime_provider="opencode",
            scope_kind="lane",
            scope_id="lane:server",
            active_session_selector=ContinuousWorkerSessionSelector(
                provider="opencode",
                session_id="session-server",
            ),
            mailbox_cursor_ref="dbc://mailbox/server@10",
            worker_report_refs=("report:previous",),
            audit_refs=("audit:claim",),
            timestamp="2026-06-29T13:00:00+00:00",
        )
    )

    built = build_continuous_worker_compact_context_bundle(
        ContinuousWorkerCompactContextBuildRequest(
            ledger_path=ledger_path,
            bundle_dir_path=bundle_dir,
            binding_id="continuous-worker:lane:lane-server",
            timestamp="2026-06-29T13:10:00+00:00",
            summary="Server worker finished the API skeleton and is ready for routing.",
            key_decisions=("Keep server/client ports isolated.",),
            current_state="waiting for route validation",
            artifact_refs=("server.js", "TEST_REPORT.md"),
            worker_report_refs=("report:latest",),
            audit_refs=("audit:compact",),
        )
    )
    loaded = read_continuous_worker_compact_context_bundle(built.bundle_path)

    assert built.ok is True
    assert built.compact_context_ref.startswith("dbc://continuous-worker-context/")
    assert built.to_json_dict()["authority_split"]["raw_transcript_persisted"] is False
    assert loaded.binding_id == "continuous-worker:lane:lane-server"
    assert loaded.summary.startswith("Server worker finished")
    assert loaded.mailbox_cursor_ref == "dbc://mailbox/server@10"
    assert loaded.worker_report_refs == ("report:previous", "report:latest")
    assert loaded.audit_refs == ("audit:claim", "audit:compact")


def test_provider_generic_delivery_naming_aliases_remain_compatible() -> None:
    assert ProviderDeliverySupervisorRequest is CodexDeliverySupervisorRequest
    assert ProviderDeliverySupervisorRecord is not None
    assert ProviderDeliverySupervisorResult is not None
    assert ProviderDeliveryBoundedLoopRequest is CodexDeliveryBoundedLoopRequest
    assert ProviderDeliveryE2ESmokeRequest is CodexDeliveryE2ESmokeRequest
    assert (
        run_bounded_provider_delivery_supervisor_loop_for_codex
        is run_bounded_codex_delivery_supervisor_loop
    )
    assert (
        run_bounded_provider_delivery_supervisor_loop_for_opencode
        is run_bounded_opencode_delivery_supervisor_loop
    )
    assert run_provider_delivery_supervisor_once_for_codex is run_codex_delivery_supervisor_once
    assert run_provider_delivery_supervisor_once_for_opencode is run_opencode_delivery_supervisor_once
    assert run_provider_delivery_e2e_smoke_for_codex is run_codex_delivery_e2e_smoke
    assert run_provider_delivery_e2e_smoke_for_opencode is run_opencode_delivery_e2e_smoke

    request = ProviderDeliveryE2ESmokeRequest(runtime_provider="opencode")
    supervisor_request = ProviderDeliverySupervisorRequest(
        delivery_state_path=".codex/scheduler/delivery-state.json",
        delivery_event_log_path=".codex/scheduler/delivery-events.jsonl",
        scheduler_snapshot_path=".codex/scheduler/state.json",
        scheduler_event_log_path=".codex/scheduler/events.jsonl",
        runtime_provider="opencode",
    )

    assert request.runtime_provider == "opencode"
    assert supervisor_request.runtime_provider == "opencode"


def test_scheduler_runs_qoder_adapter_through_registry_with_mock_client(tmp_path) -> None:
    client = _RecordingQoderClient(
        QoderQueryResult(summary="Qoder registry run complete.", output_text="done")
    )
    adapter = QoderAgentRuntimeAdapter(
        query_client=client,
        timestamp="2026-06-16T22:40:00+08:00",
    )
    registry = AgentRuntimeAdapterRegistry()
    registry.register(adapter)
    scheduler_log = JsonlSchedulerEventLog(tmp_path / "qoder-registry-run-events.jsonl")
    task = _scheduled_task(
        "task-q",
        agent=AgentSpec(agent_id="agent:qoder", runtime_provider="qoder"),
        output_artifact_id="task-q:result",
    )

    updated, result = run_scheduled_task_with_registry(
        SchedulerState(tasks={"task-q": task}),
        "task-q",
        registry=registry,
        event_log=scheduler_log,
        timestamp="2026-06-16T22:40:00+08:00",
    )

    assert updated.tasks["task-q"].state == "complete"
    assert result.output_artifact.artifact_id == "task-q:result"
    assert result.output_artifact.parts[0].text == "done"
    assert client.requests[0].agent.runtime_provider == "qoder"
    assert client.requests[0].acceptance == ("complete fake task",)
    assert [event.event_kind for event in scheduler_log.read_all()] == [
        "task_ready",
        "task_running",
        "task_completed",
    ]


def test_qoder_adapter_normalizes_known_runtime_error_with_context() -> None:
    class FailingClient:
        def query(self, request: QoderQueryRequest) -> QoderQueryResult:
            raise QoderRuntimeError(
                error_kind="sdk_unavailable",
                summary="Qoder CLI executable was not found.",
                retryable=False,
                raw_error_type="FileNotFoundError",
            )

    adapter = QoderAgentRuntimeAdapter(
        query_client=FailingClient(),
        timestamp="2026-06-17T16:10:00+08:00",
    )
    session = adapter.start_session(AgentSpec(agent_id="agent:qoder", runtime_provider="qoder"))

    with pytest.raises(QoderRuntimeError) as raised:
        adapter.run_task(
            session,
            TaskSpec(task_id="task-q", title="Qoder unavailable", instruction="Run qoder."),
        )

    error = raised.value
    assert error.error_kind == "sdk_unavailable"
    assert error.task_id == "task-q"
    assert error.session_id == "qoder-session-1"
    assert error.run_id == "qoder-run-1"
    assert "qoder runtime error [sdk_unavailable]" in str(error)
    assert "raw_error_type=FileNotFoundError" in str(error)


def test_qoder_adapter_wraps_unknown_query_client_exception() -> None:
    class BrokenClient:
        def query(self, request: QoderQueryRequest) -> QoderQueryResult:
            raise RuntimeError("unexpected response envelope")

    adapter = QoderAgentRuntimeAdapter(query_client=BrokenClient())
    session = adapter.start_session(AgentSpec(agent_id="agent:qoder", runtime_provider="qoder"))

    with pytest.raises(QoderRuntimeError) as raised:
        adapter.run_task(
            session,
            TaskSpec(task_id="task-q", title="Broken qoder", instruction="Run qoder."),
        )

    error = raised.value
    assert error.error_kind == "unknown"
    assert error.summary == "unexpected response envelope"
    assert error.raw_error_type == "RuntimeError"
    assert error.task_id == "task-q"


def test_qoder_query_result_from_response_converts_full_response_shape() -> None:
    result = qoder_query_result_from_response(
        {
            "summary": "Qoder completed task.",
            "output_text": "Done.",
            "artifact_delta": {
                "artifact_id": "task-q:result",
                "version": "v3",
                "summary": "updated files",
                "changed_refs": [
                    {
                        "ref_kind": "file",
                        "ref_id": "src/app.py",
                        "path": "src/app.py",
                        "label": "app",
                    }
                ],
            },
            "permission_requests": [
                {
                    "request_id": "perm-network",
                    "request_kind": "network",
                    "run_id": "run-q",
                    "summary": "Qoder wants network access",
                    "target": "https://example.test",
                }
            ],
            "metadata": {"turns": 2, "provider_run_id": "qoder-run-remote"},
        }
    )

    assert result.summary == "Qoder completed task."
    assert result.output_text == "Done."
    assert result.artifact_delta is not None
    assert result.artifact_delta.artifact_id == "task-q:result"
    assert result.artifact_delta.changed_refs[0].path == "src/app.py"
    assert result.permission_requests[0].request_kind == "network"
    assert result.permission_requests[0].target == "https://example.test"
    assert result.metadata == {"turns": 2, "provider_run_id": "qoder-run-remote"}


def test_qoder_query_result_from_response_rejects_missing_summary() -> None:
    with pytest.raises(QoderRuntimeError) as raised:
        qoder_query_result_from_response({"output_text": "missing summary"})

    assert raised.value.error_kind == "invalid_response"
    assert "summary must be a non-empty string" in str(raised.value)


def test_qoder_query_result_from_response_rejects_bad_artifact_delta_shape() -> None:
    with pytest.raises(QoderRuntimeError) as raised:
        qoder_query_result_from_response(
            {
                "summary": "bad delta",
                "artifact_delta": {"artifact_id": "task-q:result"},
            }
        )

    assert raised.value.error_kind == "invalid_response"
    assert "artifact_delta.version must be a non-empty string" in str(raised.value)


def test_qoder_query_result_from_response_rejects_unsupported_permission_kind() -> None:
    with pytest.raises(QoderRuntimeError) as raised:
        qoder_query_result_from_response(
            {
                "summary": "bad permission",
                "permission_requests": [
                    {
                        "request_id": "perm-bad",
                        "request_kind": "telepathy",
                        "summary": "Unsupported permission",
                    }
                ],
            }
        )

    assert raised.value.error_kind == "invalid_response"
    assert "unsupported value 'telepathy'" in str(raised.value)


def test_qoder_sdk_query_client_fails_closed_when_sdk_missing() -> None:
    def missing_importer(name: str):
        raise ModuleNotFoundError(name)

    client = QoderSDKQueryClient(
        sdk_importer=missing_importer,
        environment={"QODER_PERSONAL_ACCESS_TOKEN": "redaction-fixture-value"},
    )

    with pytest.raises(QoderRuntimeError) as raised:
        client.query(_qoder_sdk_request())

    assert raised.value.error_kind == "sdk_unavailable"
    assert "qoder-agent-sdk" in raised.value.summary
    assert "redaction-fixture-value" not in str(raised.value)


def test_qoder_sdk_host_readiness_report_is_credential_safe_when_missing() -> None:
    def missing_importer(name: str):
        raise ModuleNotFoundError(name)

    client = QoderSDKQueryClient(
        sdk_importer=missing_importer,
        environment={"QODER_PERSONAL_ACCESS_TOKEN": "redaction-fixture-value"},
    )

    report = client.host_readiness_report()
    payload = report.to_json_dict()

    assert isinstance(report, QoderSDKHostReadinessReport)
    assert payload["sdk_module_name"] == "qoder_agent_sdk"
    assert payload["sdk_importable"] is False
    assert payload["auth_mode"] == "env"
    assert payload["auth_env_var"] == "QODER_PERSONAL_ACCESS_TOKEN"
    assert payload["token_present"] is True
    assert payload["ready"] is False
    assert payload["error_kind"] == "sdk_unavailable"
    assert "redaction-fixture-value" not in json.dumps(payload)


def test_codex_mcp_exposure_skips_when_cli_missing(tmp_path: Path) -> None:
    from src.runtime.orchestration import inspect_codex_mcp_exposure

    project = tmp_path / "project"
    (project / ".codex").mkdir(parents=True)
    (project / ".codex" / "config.toml").write_text(
        "[mcp_servers.doc_based_coding_governance]\n"
        "command = \".venv\\\\Scripts\\\\doc-based-coding-mcp.exe\"\n",
        encoding="utf-8",
    )
    user_config = tmp_path / "config.toml"

    diagnostic = inspect_codex_mcp_exposure(
        project,
        executable="missing-codex",
        user_config_path=user_config,
        which=lambda executable: None,
    )
    payload = diagnostic.to_json_dict()

    assert payload["diagnostic_status"] == "skipped"
    assert payload["suspected_problem"] == "codex_cli_unavailable"
    assert payload["project_config_exists"] is True
    assert payload["project_trusted"] is None
    assert payload["mcp_list_ran"] is False
    assert payload["authority_split"]["secret_material_read"] is False


def test_codex_mcp_exposure_reports_untrusted_project(tmp_path: Path) -> None:
    from src.runtime.orchestration import inspect_codex_mcp_exposure

    project = tmp_path / "project"
    (project / ".codex").mkdir(parents=True)
    (project / ".codex" / "config.toml").write_text(
        "[mcp_servers.doc_based_coding_governance]\n"
        "command = \".venv\\\\Scripts\\\\doc-based-coding-mcp.exe\"\n",
        encoding="utf-8",
    )
    user_config = tmp_path / "config.toml"
    user_config.write_text(
        "[projects.'c:\\\\other']\ntrust_level = \"trusted\"\n",
        encoding="utf-8",
    )

    def runner(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout="No MCP servers configured yet. Try `codex mcp add my-tool -- my-command`.\n",
            stderr="",
        )

    diagnostic = inspect_codex_mcp_exposure(
        project,
        user_config_path=user_config,
        runner=runner,
        which=lambda executable: "C:/tools/codex.exe",
    )
    payload = diagnostic.to_json_dict()

    assert payload["diagnostic_status"] == "warning"
    assert payload["suspected_problem"] == "project_not_trusted"
    assert payload["project_config_exists"] is True
    assert payload["project_trusted"] is False
    assert payload["mcp_servers_zero_hint"] is True
    assert any("trusted" in item for item in payload["remediation"])
    assert payload["doc_based_coding_server_visible"] is False


def test_codex_mcp_exposure_reports_visible_enabled_server(tmp_path: Path) -> None:
    from src.runtime.orchestration import inspect_codex_mcp_exposure

    project = tmp_path / "project"
    (project / ".codex").mkdir(parents=True)
    (project / ".codex" / "config.toml").write_text(
        "[mcp_servers.doc-based-coding]\n"
        "command = \".venv\\\\Scripts\\\\doc-based-coding-mcp.exe\"\n",
        encoding="utf-8",
    )
    user_config = tmp_path / "config.toml"
    user_config.write_text(
        f"[projects.'{str(project).lower()}']\ntrust_level = \"trusted\"\n",
        encoding="utf-8",
    )

    def runner(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=(
                "Name              Command                         Args  Env  Cwd  Status   Auth\n"
                "doc-based-coding  .venv\\\\Scripts\\\\doc-based-coding-mcp.exe  -  -  .    enabled  Unsupported\n"
            ),
            stderr="",
        )

    diagnostic = inspect_codex_mcp_exposure(
        project,
        user_config_path=user_config,
        runner=runner,
        which=lambda executable: "C:/tools/codex.exe",
    )
    payload = diagnostic.to_json_dict()

    assert payload["diagnostic_status"] == "ok"
    assert payload["suspected_problem"] == ""
    assert payload["project_trusted"] is True
    assert payload["doc_based_coding_server_visible"] is True
    assert payload["doc_based_coding_server_enabled"] is True
    assert payload["authority_split"]["mcp_tool_called"] is False


def test_self_check_registry_filters_profile_and_aggregates_status(tmp_path: Path) -> None:
    from src.runtime.orchestration import (
        SelfCheckContext,
        SelfCheckDefinition,
        SelfCheckRegistry,
        SelfCheckResult,
    )

    registry = SelfCheckRegistry(
        (
            SelfCheckDefinition(
                check_id="codex.ok",
                profiles=("codex",),
                title="Codex OK",
                description="ok",
                run=lambda context: SelfCheckResult(
                    check_id="codex.ok",
                    profiles=("codex",),
                    title="Codex OK",
                    status="ok",
                    summary="ok",
                ),
            ),
            SelfCheckDefinition(
                check_id="runtime.warn",
                profiles=("runtime",),
                title="Runtime Warning",
                description="warning",
                run=lambda context: SelfCheckResult(
                    check_id="runtime.warn",
                    profiles=("runtime",),
                    title="Runtime Warning",
                    status="warning",
                    summary="warning",
                    remediation=("Fix runtime warning.",),
                ),
            ),
        )
    )
    context = SelfCheckContext(project_root=tmp_path)

    codex_report = registry.run("codex", context)
    all_report = registry.run("all", context)
    vscode_report = registry.run("vscode", context)

    assert [check.check_id for check in codex_report.checks] == ["codex.ok"]
    assert codex_report.overall_status == "ok"
    assert all_report.overall_status == "warning"
    assert all_report.counts == {"ok": 1, "warning": 1, "failed": 0, "skipped": 0}
    assert all_report.next_actions == ("Fix runtime warning.",)
    assert vscode_report.overall_status == "skipped"
    assert vscode_report.counts == {"ok": 0, "warning": 0, "failed": 0, "skipped": 0}


def test_self_check_registry_rejects_duplicate_and_unknown_profiles() -> None:
    from src.runtime.orchestration import SelfCheckDefinition, SelfCheckRegistry, SelfCheckResult

    definition = SelfCheckDefinition(
        check_id="dup",
        profiles=("codex",),
        title="Duplicate",
        description="duplicate",
        run=lambda context: SelfCheckResult(
            check_id="dup",
            profiles=("codex",),
            title="Duplicate",
            status="ok",
            summary="ok",
        ),
    )
    registry = SelfCheckRegistry((definition,))

    with pytest.raises(ValueError, match="Duplicate self-check id"):
        registry.register(definition)
    with pytest.raises(ValueError, match="unknown profile"):
        SelfCheckRegistry(
            (
                SelfCheckDefinition(
                    check_id="bad",
                    profiles=("moon",),  # type: ignore[arg-type]
                    title="Bad",
                    description="bad",
                    run=definition.run,
                ),
            )
        )


def test_doctor_exit_code_maps_failed_report_to_two(tmp_path: Path) -> None:
    from src.runtime.orchestration import (
        SelfCheckContext,
        SelfCheckDefinition,
        SelfCheckRegistry,
        SelfCheckResult,
        doctor_exit_code,
    )

    registry = SelfCheckRegistry(
        (
            SelfCheckDefinition(
                check_id="codex.failed",
                profiles=("codex",),
                title="Codex Failed",
                description="failed",
                run=lambda context: SelfCheckResult(
                    check_id="codex.failed",
                    profiles=("codex",),
                    title="Codex Failed",
                    status="failed",
                    summary="failed",
                ),
            ),
        )
    )

    failed_report = registry.run("codex", SelfCheckContext(project_root=tmp_path))
    assert failed_report.overall_status == "failed"
    assert doctor_exit_code(failed_report) == 2


def test_run_self_check_doctor_codex_profile_uses_injected_codex_mcp_check(
    tmp_path: Path,
) -> None:
    from src.runtime.orchestration import run_self_check_doctor

    project = tmp_path / "project"
    (project / ".codex").mkdir(parents=True)
    (project / ".codex" / "config.toml").write_text(
        "[mcp_servers.doc-based-coding]\n"
        "command = \".venv\\\\Scripts\\\\doc-based-coding-mcp.exe\"\n",
        encoding="utf-8",
    )
    user_config = tmp_path / "config.toml"
    user_config.write_text(
        f"[projects.'{str(project).lower()}']\ntrust_level = \"trusted\"\n",
        encoding="utf-8",
    )

    def runner(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=(
                "Name              Command                         Args  Env  Cwd  Status   Auth\n"
                "doc-based-coding  .venv\\\\Scripts\\\\doc-based-coding-mcp.exe  -  -  .    enabled  Unsupported\n"
            ),
            stderr="",
        )

    report = run_self_check_doctor(
        project,
        profile="codex",
        user_config_path=user_config,
        runner=runner,
        which=lambda executable: "C:/tools/codex.exe",
    )
    payload = report.to_json_dict()

    assert payload["schema_version"] == "self-check-report/v1"
    assert payload["overall_status"] == "ok"
    assert payload["counts"] == {"ok": 1, "warning": 0, "failed": 0, "skipped": 0}
    assert payload["checks"][0]["check_id"] == "codex.mcp_exposure"
    assert payload["checks"][0]["secret_safe"] is True
    assert payload["checks"][0]["authority_split"]["mcp_tool_called"] is False
    assert "token" not in json.dumps(payload).lower()


def test_opencode_cli_readiness_self_check_uses_injected_which(tmp_path: Path) -> None:
    from src.runtime.orchestration import run_self_check_doctor

    missing = run_self_check_doctor(
        tmp_path,
        profile="opencode",
        which=lambda executable: None,
    )
    missing_payload = missing.to_json_dict()
    assert missing_payload["overall_status"] == "skipped"
    assert missing_payload["checks"][0]["check_id"] == "opencode.cli_readiness"
    assert missing_payload["checks"][0]["suspected_problem"] == "cli_unavailable"

    available = run_self_check_doctor(
        tmp_path,
        profile="opencode",
        which=lambda executable: "C:/tools/opencode.exe",
    )
    available_payload = available.to_json_dict()
    assert available_payload["overall_status"] == "ok"
    assert available_payload["checks"][0]["status"] == "ok"
    assert available_payload["checks"][0]["authority_split"]["provider_executed"] is False
    assert "token" not in json.dumps(available_payload).lower()


def test_opencode_server_api_readiness_self_check_uses_injected_opener(
    tmp_path: Path,
) -> None:
    from src.runtime.orchestration import run_self_check_doctor

    calls: list[str] = []

    def opener(request, **kwargs):
        calls.append(request.full_url)
        if request.full_url.endswith("/global/health"):
            return _JsonHttpResponse({"status": "ok", "version": "test"}, status=200)
        if request.full_url.endswith("/doc"):
            return _JsonHttpResponse(
                {
                    "openapi": "3.1.0",
                    "info": {"title": "OpenCode API", "version": "1.2.3"},
                },
                status=200,
            )
        raise AssertionError(f"unexpected URL: {request.full_url}")

    report = run_self_check_doctor(
        tmp_path,
        profile="opencode",
        which=lambda executable: "C:/tools/opencode.exe",
        environment={"OPENCODE_SERVER_PASSWORD": "secret-value"},
        metadata={
            "opencode_server_api_base_url": "http://127.0.0.1:4096",
            "opencode_server_api_check_doc": True,
            "opencode_server_api_opener": opener,
        },
    )
    payload = report.to_json_dict()
    checks = {check["check_id"]: check for check in payload["checks"]}

    assert payload["overall_status"] == "ok"
    assert set(checks) == {"opencode.cli_readiness", "opencode.server_api_readiness"}
    server_check = checks["opencode.server_api_readiness"]
    assert server_check["status"] == "ok"
    assert server_check["evidence"]["doc_available"] is True
    assert server_check["evidence"]["api_title"] == "OpenCode API"
    assert server_check["authority_split"]["provider_executed"] is False
    assert server_check["authority_split"]["secret_material_read"] is False
    assert calls == [
        "http://127.0.0.1:4096/global/health",
        "http://127.0.0.1:4096/doc",
    ]
    assert "secret-value" not in json.dumps(payload)


def test_opencode_server_api_readiness_self_check_skips_unreachable(
    tmp_path: Path,
) -> None:
    from src.runtime.orchestration import run_self_check_doctor

    def opener(*args, **kwargs):
        raise TimeoutError("server did not answer")

    report = run_self_check_doctor(
        tmp_path,
        profile="runtime",
        which=lambda executable: None,
        metadata={"opencode_server_api_opener": opener},
    )
    payload = report.to_json_dict()
    checks = {check["check_id"]: check for check in payload["checks"]}

    assert checks["opencode.server_api_readiness"]["status"] == "skipped"
    assert checks["opencode.server_api_readiness"]["suspected_problem"] == (
        "server_unreachable"
    )
    assert checks["opencode.server_api_readiness"]["authority_split"][
        "provider_executed"
    ] is False


def test_scheduler_storage_visibility_reports_missing_storage(tmp_path: Path) -> None:
    from src.runtime.orchestration import run_self_check_doctor

    report = run_self_check_doctor(tmp_path, profile="scheduler")
    payload = report.to_json_dict()

    assert payload["overall_status"] == "warning"
    assert payload["checks"][0]["check_id"] == "scheduler.storage_visibility"
    assert payload["checks"][0]["suspected_problem"] == "scheduler_storage_missing"
    assert payload["checks"][0]["authority_split"]["provider_executed"] is False


def test_scheduler_storage_visibility_reads_default_snapshot_and_event_log(
    tmp_path: Path,
) -> None:
    from src.runtime.orchestration import (
        SchedulerState,
        ScheduledTask,
        AgentSpec,
        ContextScope,
        run_self_check_doctor,
        write_scheduler_state_snapshot,
    )

    scheduler_dir = tmp_path / ".codex" / "scheduler"
    snapshot = scheduler_dir / "state.json"
    event_log = scheduler_dir / "events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-1": ScheduledTask(
                    task_id="task-1",
                    title="Task",
                    instruction="Do work",
                    agent=AgentSpec(agent_id="agent:one", runtime_provider="fake"),
                    context_scope=ContextScope(context_id="ctx", lane_id="lane:main"),
                )
            }
        ),
        snapshot,
    )
    event_log.write_text('{"event_id":"event-1"}\n\n', encoding="utf-8")

    report = run_self_check_doctor(tmp_path, profile="scheduler")
    payload = report.to_json_dict()

    assert payload["overall_status"] == "ok"
    evidence = payload["checks"][0]["evidence"]
    assert evidence["task_count"] == 1
    assert evidence["event_log_line_count"] == 1
    assert payload["checks"][0]["authority_split"]["read_only"] is True


def test_qoder_sdk_query_client_fails_closed_when_auth_token_missing() -> None:
    client = QoderSDKQueryClient(
        sdk_importer=lambda name: _FakeQoderSDK(messages=()),
        environment={},
    )

    with pytest.raises(QoderRuntimeError) as raised:
        client.query(_qoder_sdk_request())

    assert raised.value.error_kind == "authentication_failed"
    assert "QODER_PERSONAL_ACCESS_TOKEN" in raised.value.summary


def test_qoder_sdk_host_readiness_report_supports_ready_qodercli_auth() -> None:
    sdk = _FakeQoderSDK(messages=())
    client = QoderSDKQueryClient(
        QoderSDKQueryClientConfig(auth_mode="qodercli"),
        sdk_importer=lambda name: sdk,
        environment={},
    )

    report = client.host_readiness_report()

    assert report.sdk_importable is False
    assert report.auth_mode == "qodercli"
    assert report.token_present is False
    assert report.ready is True
    assert report.error_kind == ""


def test_qoder_sdk_query_client_streams_text_into_query_result() -> None:
    sdk = _FakeQoderSDK(messages=({"content": "implemented\n"}, {"content": "validated"}))
    client = QoderSDKQueryClient(
        QoderSDKQueryClientConfig(
            cwd=".",
            model="configured-model",
            max_turns=2,
            allowed_tools=("read",),
            permission_mode="ask",
            metadata={"host_surface": "test"},
        ),
        sdk_importer=lambda name: sdk,
        environment={"QODER_PERSONAL_ACCESS_TOKEN": "redaction-fixture-value"},
    )

    result = client.query(_qoder_sdk_request())

    assert result.summary == "implemented"
    assert result.output_text == "implemented\nvalidated"
    assert result.permission_requests == ()
    assert result.metadata["sdk"] == "qoder-agent-sdk"
    assert result.metadata["message_count"] == 2
    assert result.metadata["model"] == "configured-model"
    assert result.metadata["max_turns"] == 2
    assert result.metadata["allowed_tool_count"] == 1
    assert result.metadata["host_surface"] == "test"
    assert sdk.auth_calls == ["from_env"]
    assert sdk.option_kwargs["auth"] == "auth:env"
    assert sdk.option_kwargs["cwd"] == "."
    assert sdk.option_kwargs["model"] == "configured-model"
    assert sdk.option_kwargs["max_turns"] == 2
    assert sdk.option_kwargs["allowed_tools"] == ["read"]
    assert sdk.query_prompt.startswith("Task ID: task-qoder-sdk")
    assert "Acceptance criteria:" in sdk.query_prompt
    assert sdk.query_options is sdk.options_instance


def test_qoder_sdk_query_client_accepts_structured_final_response_message() -> None:
    sdk = _FakeQoderSDK(
        messages=(
            {
                "result": {
                    "summary": "structured qoder result",
                    "output_text": "final output",
                    "metadata": {"provider_run_id": "run-remote"},
                }
            },
        )
    )
    client = QoderSDKQueryClient(
        sdk_importer=lambda name: sdk,
        environment={"QODER_PERSONAL_ACCESS_TOKEN": "redaction-fixture-value"},
    )

    result = client.query(_qoder_sdk_request())

    assert result.summary == "structured qoder result"
    assert result.output_text == "final output"
    assert result.metadata["provider_run_id"] == "run-remote"
    assert result.metadata["message_count"] == 1


def test_qoder_sdk_query_client_rejects_invalid_stream_shape() -> None:
    sdk = _FakeQoderSDK(messages=(), stream_override={"not": "an async stream"})
    client = QoderSDKQueryClient(
        sdk_importer=lambda name: sdk,
        environment={"QODER_PERSONAL_ACCESS_TOKEN": "redaction-fixture-value"},
    )

    with pytest.raises(QoderRuntimeError) as raised:
        client.query(_qoder_sdk_request())

    assert raised.value.error_kind == "invalid_response"
    assert "async message stream" in raised.value.summary


def test_qoder_sdk_query_client_denies_permission_callback_by_default() -> None:
    sdk = _FakeQoderSDK(messages=({"content": "unreachable"},), trigger_permission=True)
    client = QoderSDKQueryClient(
        sdk_importer=lambda name: sdk,
        environment={"QODER_PERSONAL_ACCESS_TOKEN": "redaction-fixture-value"},
    )

    with pytest.raises(QoderRuntimeError) as raised:
        client.query(_qoder_sdk_request())

    assert raised.value.error_kind == "permission_denied"
    assert "write src/app.py" in raised.value.summary


def test_qoder_sdk_query_client_can_surface_permission_request_without_approving() -> None:
    sdk = _FakeQoderSDK(messages=(), trigger_permission=True)
    client = QoderSDKQueryClient(
        QoderSDKQueryClientConfig(permission_request_policy="surface"),
        sdk_importer=lambda name: sdk,
        environment={"QODER_PERSONAL_ACCESS_TOKEN": "redaction-fixture-value"},
    )

    result = client.query(_qoder_sdk_request())

    assert result.summary == "Qoder SDK requested permission review."
    assert len(result.permission_requests) == 1
    request = result.permission_requests[0]
    assert request.request_kind == "artifact_write"
    assert request.target == "src/app.py"
    assert "write src/app.py" in request.summary


def test_qoder_sdk_query_client_redacts_token_from_sdk_errors() -> None:
    token = "redaction-fixture-value"
    sdk = _FakeQoderSDK(
        messages=(),
        query_exception=RuntimeError(f"auth failed for {token}"),
    )
    client = QoderSDKQueryClient(
        sdk_importer=lambda name: sdk,
        environment={"QODER_PERSONAL_ACCESS_TOKEN": token},
    )

    with pytest.raises(QoderRuntimeError) as raised:
        client.query(_qoder_sdk_request())

    assert raised.value.error_kind == "authentication_failed"
    assert token not in str(raised.value)
    assert "[redacted]" in raised.value.summary


def test_scheduler_records_qoder_runtime_error_as_runtime_failure(tmp_path) -> None:
    class AuthFailingClient:
        def query(self, request: QoderQueryRequest) -> QoderQueryResult:
            raise QoderRuntimeError(
                error_kind="authentication_failed",
                summary="Qoder login is required.",
                raw_error_type="AuthError",
            )

    registry = AgentRuntimeAdapterRegistry()
    registry.register(QoderAgentRuntimeAdapter(query_client=AuthFailingClient()))
    scheduler_log = JsonlSchedulerEventLog(tmp_path / "qoder-auth-failed-events.jsonl")
    state = SchedulerState(
        tasks={
            "task-q": _scheduled_task(
                "task-q",
                agent=AgentSpec(agent_id="agent:qoder", runtime_provider="qoder"),
            ),
        },
    )
    sandbox_registry = SandboxProviderRegistry()
    sandbox_registry.register(SharedProcessSandboxProvider())

    result = drain_preflighted_ready_tasks(
        state,
        sandbox_registry=sandbox_registry,
        runtime_registry=registry,
        event_log=scheduler_log,
        timestamp="2026-06-17T16:15:00+08:00",
    )

    task = result.state.tasks["task-q"]
    events = scheduler_log.read_all()
    assert result.stop_reason == "task_failed"
    assert task.state == "blocked"
    assert "qoder runtime error [authentication_failed]" in task.blocked_reason
    assert "Qoder login is required." in task.blocked_reason
    assert events[-1].event_kind == "task_run_failed"
    assert events[-1].reason == task.blocked_reason


def test_scheduler_registry_qoder_path_preserves_permission_requests(tmp_path) -> None:
    permission = PermissionRequest(
        request_id="perm-shell",
        request_kind="shell",
        run_id="pending",
        summary="Qoder wants shell access",
        target="npm test",
    )
    client = _RecordingQoderClient(
        QoderQueryResult(
            summary="Qoder surfaced permission request.",
            permission_requests=(permission,),
        )
    )
    adapter = QoderAgentRuntimeAdapter(query_client=client)
    registry = AgentRuntimeAdapterRegistry()
    registry.register(adapter)
    task = _scheduled_task(
        "task-q",
        agent=AgentSpec(agent_id="agent:qoder", runtime_provider="qoder"),
    )

    updated, result = run_scheduled_task_with_registry(
        SchedulerState(tasks={"task-q": task}),
        "task-q",
        registry=registry,
        event_log=JsonlSchedulerEventLog(tmp_path / "qoder-permission-events.jsonl"),
    )

    assert updated.tasks["task-q"].state == "review_required"
    assert updated.tasks["task-q"].blocked_reason == "permission review required: shell npm test"
    assert result.permission_requests == (permission,)
    assert result.permission_requests[0].request_kind == "shell"
    assert result.permission_requests[0].target == "npm test"


def test_permission_request_keeps_dependent_waiting_after_runtime_run(tmp_path) -> None:
    permission = PermissionRequest(
        request_id="perm-write",
        request_kind="artifact_write",
        run_id="pending",
        summary="Qoder wants write access",
        target="src/app.py",
    )
    client = _RecordingQoderClient(
        QoderQueryResult(
            summary="Qoder produced output but needs permission.",
            permission_requests=(permission,),
        )
    )
    adapter = QoderAgentRuntimeAdapter(query_client=client)
    registry = AgentRuntimeAdapterRegistry()
    registry.register(adapter)
    scheduler_log = JsonlSchedulerEventLog(tmp_path / "permission-gate-events.jsonl")
    state = SchedulerState(
        tasks={
            "task-a": _scheduled_task(
                "task-a",
                agent=AgentSpec(agent_id="agent:qoder", runtime_provider="qoder"),
            ),
            "task-b": _scheduled_task("task-b", state="waiting"),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-a-b",
                source_task_id="task-a",
                target_task_id="task-b",
                required_state="complete",
            ),
        ),
    )

    updated, result = run_scheduled_task_with_registry(
        state,
        "task-a",
        registry=registry,
        event_log=scheduler_log,
        timestamp="2026-06-16T22:50:00+08:00",
    )
    events = scheduler_log.read_all()

    assert result.permission_requests == (permission,)
    assert updated.tasks["task-a"].state == "review_required"
    assert updated.tasks["task-a"].blocked_reason == (
        "permission review required: artifact_write src/app.py"
    )
    assert updated.tasks["task-b"].state == "waiting"
    assert [event.event_kind for event in events] == [
        "task_ready",
        "task_running",
        "task_review_required",
    ]
    assert events[-1].reason == "permission review required: artifact_write src/app.py"


def test_resolve_permission_review_approval_completes_task_and_wakes_dependents(tmp_path) -> None:
    permission = PermissionRequest(
        request_id="perm-write",
        request_kind="artifact_write",
        run_id="pending",
        summary="Qoder wants write access",
        target="src/app.py",
    )
    client = _RecordingQoderClient(
        QoderQueryResult(
            summary="Qoder produced output but needs permission.",
            permission_requests=(permission,),
        )
    )
    registry = AgentRuntimeAdapterRegistry()
    registry.register(QoderAgentRuntimeAdapter(query_client=client))
    scheduler_log = JsonlSchedulerEventLog(tmp_path / "permission-approved-events.jsonl")
    state = SchedulerState(
        tasks={
            "task-a": _scheduled_task(
                "task-a",
                agent=AgentSpec(agent_id="agent:qoder", runtime_provider="qoder"),
            ),
            "task-b": _scheduled_task("task-b", state="waiting"),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-a-b",
                source_task_id="task-a",
                target_task_id="task-b",
                required_state="complete",
            ),
        ),
    )
    review_state, _ = run_scheduled_task_with_registry(
        state,
        "task-a",
        registry=registry,
        event_log=scheduler_log,
        timestamp="2026-06-16T23:00:00+08:00",
    )

    approved = resolve_task_permission_review(
        review_state,
        "task-a",
        approved=True,
        reason="review approved shell-free patch",
        event_log=scheduler_log,
        timestamp="2026-06-16T23:01:00+08:00",
    )
    events = scheduler_log.read_all()

    assert approved.tasks["task-a"].state == "complete"
    assert approved.tasks["task-a"].blocked_reason == ""
    assert approved.tasks["task-b"].state == "ready"
    assert approved.run_records[0].state == "complete"
    assert [event.event_kind for event in events] == [
        "task_ready",
        "task_running",
        "task_review_required",
        "task_permission_approved",
        "task_ready",
    ]
    assert events[-2].run_id == "qoder-run-1"
    assert events[-2].reason == "review approved shell-free patch"


def test_resolve_permission_review_rejection_blocks_task_without_waking_dependents(tmp_path) -> None:
    permission = PermissionRequest(
        request_id="perm-shell",
        request_kind="shell",
        run_id="pending",
        summary="Qoder wants shell access",
        target="npm test",
    )
    client = _RecordingQoderClient(
        QoderQueryResult(
            summary="Qoder produced output but needs shell permission.",
            permission_requests=(permission,),
        )
    )
    registry = AgentRuntimeAdapterRegistry()
    registry.register(QoderAgentRuntimeAdapter(query_client=client))
    scheduler_log = JsonlSchedulerEventLog(tmp_path / "permission-rejected-events.jsonl")
    state = SchedulerState(
        tasks={
            "task-a": _scheduled_task(
                "task-a",
                agent=AgentSpec(agent_id="agent:qoder", runtime_provider="qoder"),
            ),
            "task-b": _scheduled_task("task-b", state="waiting"),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-a-b",
                source_task_id="task-a",
                target_task_id="task-b",
                required_state="complete",
            ),
        ),
    )
    review_state, _ = run_scheduled_task_with_registry(
        state,
        "task-a",
        registry=registry,
        event_log=scheduler_log,
        timestamp="2026-06-16T23:05:00+08:00",
    )

    rejected = resolve_task_permission_review(
        review_state,
        "task-a",
        approved=False,
        reason="shell command outside admitted scope",
        event_log=scheduler_log,
        timestamp="2026-06-16T23:06:00+08:00",
    )
    events = scheduler_log.read_all()

    assert rejected.tasks["task-a"].state == "blocked"
    assert rejected.tasks["task-a"].blocked_reason == "shell command outside admitted scope"
    assert rejected.tasks["task-b"].state == "waiting"
    assert rejected.run_records[0].state == "blocked"
    assert [event.event_kind for event in events] == [
        "task_ready",
        "task_running",
        "task_review_required",
        "task_permission_rejected",
    ]
    assert events[-1].run_id == "qoder-run-1"
    assert events[-1].reason == "shell command outside admitted scope"


def test_resolve_permission_review_rejects_tasks_not_waiting_for_review() -> None:
    state = SchedulerState(tasks={"task-a": _scheduled_task("task-a", state="ready")})

    with pytest.raises(ValueError, match="is not in review_required"):
        resolve_task_permission_review(state, "task-a", approved=True)


def test_qoder_adapter_rejects_non_qoder_agent_or_unknown_session() -> None:
    adapter = QoderAgentRuntimeAdapter(query_client=_RecordingQoderClient(QoderQueryResult(summary="ok")))

    with pytest.raises(ValueError, match="requires agent.runtime_provider='qoder'"):
        adapter.start_session(AgentSpec(agent_id="agent:fake", runtime_provider="fake"))

    with pytest.raises(ValueError, match="unknown Qoder runtime session"):
        adapter.run_task(
            SessionHandle(session_id="missing", provider="qoder", agent_id="agent:qoder"),
            TaskSpec(task_id="task-q", title="Qoder task", instruction=""),
        )


def test_scheduler_marks_dependency_free_task_ready() -> None:
    state = SchedulerState(tasks={"task-1": _scheduled_task("task-1")})

    updated = mark_ready_tasks(state)

    assert updated.tasks["task-1"].state == "ready"
    assert updated.tasks["task-1"].blocked_reason == ""


def test_scheduler_keeps_dependency_blocked_task_waiting() -> None:
    state = SchedulerState(
        tasks={
            "task-a": _scheduled_task("task-a", state="proposed"),
            "task-b": _scheduled_task("task-b", state="proposed"),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-1",
                source_task_id="task-a",
                target_task_id="task-b",
                required_state="complete",
            ),
        ),
    )

    updated = mark_ready_tasks(state)

    assert updated.tasks["task-a"].state == "ready"
    assert updated.tasks["task-b"].state == "waiting"
    assert updated.tasks["task-b"].blocked_reason == "waiting for task-a to reach complete"


def test_scheduler_waits_for_incomplete_merge_gate_before_target_ready() -> None:
    state = SchedulerState(
        tasks={
            "task-a": _scheduled_task("task-a", state="complete"),
            "task-b": _scheduled_task("task-b", state="complete"),
            "task-c": _scheduled_task("task-c", state="proposed"),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-a-c",
                source_task_id="task-a",
                target_task_id="task-c",
            ),
            TaskDependency(
                dependency_id="dep-b-c",
                source_task_id="task-b",
                target_task_id="task-c",
            ),
        ),
        merge_gates=(
            SchedulerMergeGate(
                gate_id="merge-c",
                title="Review merged inputs",
                target_task_id="task-c",
                source_task_ids=("task-a", "task-b"),
                dependency_ids=("dep-a-c", "dep-b-c"),
                gate_kind="review",
                state="review_required",
                required_review=True,
            ),
        ),
    )

    decision = evaluate_task_admission(state, "task-c")
    updated = mark_ready_tasks(state)

    assert decision.state == "waiting"
    assert decision.reason == "waiting for merge gate merge-c to reach complete"
    assert updated.tasks["task-c"].state == "waiting"
    assert updated.tasks["task-c"].blocked_reason == "waiting for merge gate merge-c to reach complete"


def test_scheduler_allows_target_ready_after_merge_gate_complete() -> None:
    state = SchedulerState(
        tasks={
            "task-a": _scheduled_task("task-a", state="complete"),
            "task-b": _scheduled_task("task-b", state="complete"),
            "task-c": _scheduled_task("task-c", state="proposed"),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-a-c",
                source_task_id="task-a",
                target_task_id="task-c",
            ),
            TaskDependency(
                dependency_id="dep-b-c",
                source_task_id="task-b",
                target_task_id="task-c",
            ),
        ),
        merge_gates=(
            SchedulerMergeGate(
                gate_id="merge-c",
                title="Review merged inputs",
                target_task_id="task-c",
                source_task_ids=("task-a", "task-b"),
                dependency_ids=("dep-a-c", "dep-b-c"),
                gate_kind="review",
                state="complete",
                required_review=True,
            ),
        ),
    )

    decision = evaluate_task_admission(state, "task-c")
    updated = mark_ready_tasks(state)

    assert decision.state == "admissible"
    assert updated.tasks["task-c"].state == "ready"
    assert updated.tasks["task-c"].blocked_reason == ""


def test_resolve_scheduler_merge_gate_approval_completes_gate_and_wakes_target() -> None:
    state = SchedulerState(
        tasks={
            "task-a": _scheduled_task("task-a", state="complete"),
            "task-b": _scheduled_task("task-b", state="complete"),
            "task-c": _scheduled_task("task-c", state="waiting"),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-a-c",
                source_task_id="task-a",
                target_task_id="task-c",
            ),
            TaskDependency(
                dependency_id="dep-b-c",
                source_task_id="task-b",
                target_task_id="task-c",
            ),
        ),
        merge_gates=(
            SchedulerMergeGate(
                gate_id="merge-c",
                title="Review merged inputs",
                target_task_id="task-c",
                source_task_ids=("task-a", "task-b"),
                dependency_ids=("dep-a-c", "dep-b-c"),
                gate_kind="review",
                state="review_required",
                required_review=True,
            ),
        ),
    )

    updated = resolve_scheduler_merge_gate(
        state,
        "merge-c",
        approved=True,
        reason="guide approved merged inputs",
        decision_artifact_ref=ExchangeReference(
            ref_kind="exchange_artifact",
            ref_id="merge-c:decision",
            version="v1",
        ),
        resolved_at="2026-06-17T02:20:00+08:00",
    )

    assert updated.merge_gates[0].state == "complete"
    assert updated.merge_gates[0].blocked_reason == ""
    assert updated.merge_gates[0].decision_artifact_ref is not None
    assert updated.merge_gates[0].decision_artifact_ref.ref_id == "merge-c:decision"
    assert updated.merge_gates[0].resolved_at == "2026-06-17T02:20:00+08:00"
    assert updated.tasks["task-c"].state == "ready"
    assert updated.tasks["task-c"].blocked_reason == ""


def test_resolve_scheduler_merge_gate_rejection_blocks_gate_and_keeps_target_waiting() -> None:
    state = SchedulerState(
        tasks={
            "task-a": _scheduled_task("task-a", state="complete"),
            "task-c": _scheduled_task("task-c", state="waiting"),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-a-c",
                source_task_id="task-a",
                target_task_id="task-c",
            ),
        ),
        merge_gates=(
            SchedulerMergeGate(
                gate_id="merge-c",
                title="Review merged inputs",
                target_task_id="task-c",
                source_task_ids=("task-a",),
                dependency_ids=("dep-a-c",),
                gate_kind="review",
                state="review_required",
                required_review=True,
            ),
        ),
    )

    updated = resolve_scheduler_merge_gate(
        state,
        "merge-c",
        approved=False,
        reason="guide rejected incompatible inputs",
        resolved_at="2026-06-17T02:21:00+08:00",
    )

    assert updated.merge_gates[0].state == "blocked"
    assert updated.merge_gates[0].blocked_reason == "guide rejected incompatible inputs"
    assert updated.merge_gates[0].resolved_at == "2026-06-17T02:21:00+08:00"
    assert updated.tasks["task-c"].state == "waiting"
    assert updated.tasks["task-c"].blocked_reason == "waiting for merge gate merge-c to reach complete"


def test_resolve_scheduler_merge_gate_rejects_unknown_or_terminal_gate() -> None:
    state = SchedulerState(
        tasks={"task-c": _scheduled_task("task-c", state="waiting")},
        merge_gates=(
            SchedulerMergeGate(
                gate_id="merge-c",
                title="Review merged inputs",
                target_task_id="task-c",
                state="complete",
            ),
        ),
    )

    with pytest.raises(ValueError, match="already terminal"):
        resolve_scheduler_merge_gate(state, "merge-c", approved=True)

    with pytest.raises(ValueError, match="unknown merge gate"):
        resolve_scheduler_merge_gate(state, "missing", approved=True)


def test_scheduler_merge_gate_event_log_round_trips_jsonl(tmp_path) -> None:
    event_log = JsonlSchedulerMergeGateEventLog(tmp_path / "merge-gate-events.jsonl")
    event = SchedulerMergeGateEvent(
        event_id="merge-gate-event-1",
        event_kind="merge_gate_completed",
        timestamp="2026-06-17T02:30:00+08:00",
        gate_id="merge-c",
        target_task_id="task-c",
        from_state="review_required",
        to_state="complete",
        reason="guide approved merged inputs",
        decision_artifact_id="merge-c:decision",
        decision_artifact_version="v1",
        related_dependency_ids=("dep-a-c", "dep-b-c"),
        related_task_ids=("task-a", "task-b", "task-c"),
        sequence=1,
    )

    event_log.append(event)
    loaded = event_log.read_all()

    assert loaded == (event,)
    assert loaded[0].decision_artifact_id == "merge-c:decision"
    assert loaded[0].related_task_ids == ("task-a", "task-b", "task-c")


def test_resolve_scheduler_merge_gate_records_completed_event(tmp_path) -> None:
    event_log = JsonlSchedulerMergeGateEventLog(tmp_path / "merge-gate-events.jsonl")
    state = SchedulerState(
        tasks={
            "task-a": _scheduled_task("task-a", state="complete"),
            "task-c": _scheduled_task("task-c", state="waiting"),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-a-c",
                source_task_id="task-a",
                target_task_id="task-c",
            ),
        ),
        merge_gates=(
            SchedulerMergeGate(
                gate_id="merge-c",
                title="Review merged inputs",
                target_task_id="task-c",
                source_task_ids=("task-a",),
                dependency_ids=("dep-a-c",),
                gate_kind="review",
                state="review_required",
                required_review=True,
            ),
        ),
    )

    resolve_scheduler_merge_gate(
        state,
        "merge-c",
        approved=True,
        reason="guide approved merged inputs",
        decision_artifact_ref=ExchangeReference(
            ref_kind="exchange_artifact",
            ref_id="merge-c:decision",
            version="v1",
        ),
        event_log=event_log,
        timestamp="2026-06-17T02:31:00+08:00",
    )
    events = event_log.read_all()

    assert [event.event_kind for event in events] == ["merge_gate_completed"]
    assert events[0].gate_id == "merge-c"
    assert events[0].from_state == "review_required"
    assert events[0].to_state == "complete"
    assert events[0].reason == "guide approved merged inputs"
    assert events[0].decision_artifact_id == "merge-c:decision"
    assert events[0].related_dependency_ids == ("dep-a-c",)
    assert events[0].related_task_ids == ("task-a", "task-c")


def test_resolve_scheduler_merge_gate_records_blocked_event(tmp_path) -> None:
    event_log = JsonlSchedulerMergeGateEventLog(tmp_path / "merge-gate-events.jsonl")
    state = SchedulerState(
        tasks={"task-c": _scheduled_task("task-c", state="waiting")},
        merge_gates=(
            SchedulerMergeGate(
                gate_id="merge-c",
                title="Review merged inputs",
                target_task_id="task-c",
                gate_kind="review",
                state="review_required",
                required_review=True,
            ),
        ),
    )

    resolve_scheduler_merge_gate(
        state,
        "merge-c",
        approved=False,
        reason="guide rejected incompatible inputs",
        event_log=event_log,
        timestamp="2026-06-17T02:32:00+08:00",
    )
    events = event_log.read_all()

    assert [event.event_kind for event in events] == ["merge_gate_blocked"]
    assert events[0].gate_id == "merge-c"
    assert events[0].to_state == "blocked"
    assert events[0].reason == "guide rejected incompatible inputs"
    assert events[0].related_task_ids == ("task-c",)


def test_scheduler_merge_gate_event_log_rejects_invalid_jsonl(tmp_path) -> None:
    path = tmp_path / "broken-merge-gate-events.jsonl"
    path.write_text("{not-json}\n", encoding="utf-8")
    event_log = JsonlSchedulerMergeGateEventLog(path)

    with pytest.raises(ValueError, match="invalid scheduler merge-gate event JSONL"):
        event_log.read_all()


def test_scheduler_wakes_direct_dependents_after_source_completion(tmp_path) -> None:
    event_log = JsonlSchedulerEventLog(tmp_path / "wake-events.jsonl")
    state = SchedulerState(
        tasks={
            "task-a": _scheduled_task("task-a", state="complete"),
            "task-b": _scheduled_task("task-b", state="waiting"),
            "task-c": _scheduled_task("task-c", state="proposed"),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-a-b",
                source_task_id="task-a",
                target_task_id="task-b",
                required_state="complete",
            ),
            TaskDependency(
                dependency_id="dep-b-c",
                source_task_id="task-b",
                target_task_id="task-c",
                required_state="complete",
            ),
        ),
    )

    updated = wake_dependent_tasks(
        state,
        "task-a",
        event_log=event_log,
        timestamp="2026-06-16T21:00:00+08:00",
    )
    events = event_log.read_all()

    assert updated.tasks["task-b"].state == "ready"
    assert updated.tasks["task-b"].blocked_reason == ""
    assert updated.tasks["task-c"].state == "proposed"
    assert [event.event_kind for event in events] == ["task_ready"]
    assert events[0].task_id == "task-b"
    assert events[0].from_state == "waiting"


def test_scheduler_wake_keeps_dependent_waiting_when_another_dependency_is_unsatisfied(tmp_path) -> None:
    event_log = JsonlSchedulerEventLog(tmp_path / "wake-waiting-events.jsonl")
    state = SchedulerState(
        tasks={
            "task-a": _scheduled_task("task-a", state="complete"),
            "task-b": _scheduled_task("task-b", state="proposed"),
            "task-c": _scheduled_task("task-c", state="waiting"),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-a-c",
                source_task_id="task-a",
                target_task_id="task-c",
                required_state="complete",
            ),
            TaskDependency(
                dependency_id="dep-b-c",
                source_task_id="task-b",
                target_task_id="task-c",
                required_state="complete",
            ),
        ),
    )

    updated = wake_dependent_tasks(
        state,
        "task-a",
        event_log=event_log,
        timestamp="2026-06-16T21:05:00+08:00",
    )
    events = event_log.read_all()

    assert updated.tasks["task-c"].state == "waiting"
    assert updated.tasks["task-c"].blocked_reason == "waiting for task-b to reach complete"
    assert events[0].event_kind == "task_waiting"
    assert events[0].related_dependency_ids == ("dep-b-c",)


def test_scheduler_blocks_conflicting_write_leases_against_ready_or_running_tasks() -> None:
    running = _scheduled_task(
        "task-a",
        state="running",
        edit_lease=EditScopeLease(
            lease_id="lease-a",
            task_id="task-a",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
    )
    proposed = _scheduled_task(
        "task-b",
        edit_lease=EditScopeLease(
            lease_id="lease-b",
            task_id="task-b",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
    )
    state = SchedulerState(tasks={"task-a": running, "task-b": proposed})

    decision = evaluate_task_admission(state, "task-b")
    updated = mark_ready_tasks(state)

    assert decision.state == "blocked"
    assert decision.reason == "edit lease conflict with task-a: src/app.py"
    assert decision.edit_lease_conflict is not None
    assert decision.edit_lease_conflict.classification == "exact_path_overlap"
    assert decision.edit_lease_conflict.left_path == "src/app.py"
    assert decision.edit_lease_conflict.right_path == "src/app.py"
    assert updated.tasks["task-b"].state == "blocked"


def test_edit_lease_classifier_blocks_directory_containment_overlap() -> None:
    running = _scheduled_task(
        "task-a",
        state="running",
        edit_lease=EditScopeLease(
            lease_id="lease-a",
            task_id="task-a",
            allowed_artifacts=("src",),
            lease_mode="write",
        ),
    )
    proposed = _scheduled_task(
        "task-b",
        edit_lease=EditScopeLease(
            lease_id="lease-b",
            task_id="task-b",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
    )
    state = SchedulerState(tasks={"task-a": running, "task-b": proposed})

    decision = evaluate_task_admission(state, "task-b")

    assert decision.state == "blocked"
    assert decision.edit_lease_conflict is not None
    assert decision.edit_lease_conflict.classification == "directory_contains_file"
    assert decision.edit_lease_conflict.left_path == "src/app.py"
    assert decision.edit_lease_conflict.right_path == "src"
    assert decision.reason == "edit lease conflict with task-a: src/app.py overlaps src"


def test_edit_lease_classifier_classifies_directory_overlap() -> None:
    running = _scheduled_task(
        "task-a",
        state="running",
        edit_lease=EditScopeLease(
            lease_id="lease-a",
            task_id="task-a",
            allowed_artifacts=("src",),
            lease_mode="write",
        ),
    )
    proposed = _scheduled_task(
        "task-b",
        edit_lease=EditScopeLease(
            lease_id="lease-b",
            task_id="task-b",
            allowed_artifacts=("src/components",),
            lease_mode="write",
        ),
    )
    state = SchedulerState(tasks={"task-a": running, "task-b": proposed})

    decision = evaluate_task_admission(state, "task-b")

    assert decision.state == "blocked"
    assert decision.edit_lease_conflict is not None
    assert decision.edit_lease_conflict.classification == "directory_overlap"
    assert decision.reason == "edit lease conflict with task-a: src/components overlaps src"


def test_edit_lease_classifier_blocks_denied_artifact_hit() -> None:
    running = _scheduled_task(
        "task-a",
        state="running",
        edit_lease=EditScopeLease(
            lease_id="lease-a",
            task_id="task-a",
            allowed_artifacts=("src",),
            denied_artifacts=("src/generated",),
            lease_mode="write",
        ),
    )
    proposed = _scheduled_task(
        "task-b",
        edit_lease=EditScopeLease(
            lease_id="lease-b",
            task_id="task-b",
            allowed_artifacts=("src/generated/model.py",),
            lease_mode="write",
        ),
    )
    state = SchedulerState(tasks={"task-a": running, "task-b": proposed})

    decision = classify_edit_lease_conflict(state, proposed)

    assert decision.state == "blocked"
    assert decision.classification == "denied_artifact_hit"
    assert decision.left_path == "src/generated/model.py"
    assert decision.right_path == "src/generated"
    assert "is denied by src/generated" in decision.reason


def test_edit_lease_classifier_routes_review_zone_overlap_to_review_required(
    tmp_path,
) -> None:
    event_log = JsonlSchedulerEventLog(tmp_path / "review-zone-events.jsonl")
    running = _scheduled_task(
        "task-a",
        state="running",
        edit_lease=EditScopeLease(
            lease_id="lease-a",
            task_id="task-a",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
    )
    proposed = _scheduled_task(
        "task-b",
        edit_lease=EditScopeLease(
            lease_id="lease-b",
            task_id="task-b",
            allowed_artifacts=("src/app.py",),
            lease_mode="review-zone",
        ),
    )
    state = SchedulerState(tasks={"task-a": running, "task-b": proposed})

    decision = evaluate_task_admission(state, "task-b")
    updated = mark_ready_tasks(
        state,
        event_log=event_log,
        timestamp="2026-06-20T12:10:00+08:00",
    )

    assert decision.state == "review_required"
    assert decision.edit_lease_conflict is not None
    assert decision.edit_lease_conflict.classification == "review_zone_overlap"
    assert updated.tasks["task-b"].state == "review_required"
    assert updated.tasks["task-b"].blocked_reason == (
        "edit lease review required with task-a: src/app.py overlaps src/app.py"
    )
    events = event_log.read_all()
    assert [event.event_kind for event in events] == ["task_review_required"]
    assert events[0].reason == updated.tasks["task-b"].blocked_reason


def test_edit_lease_classifier_blocks_unsupported_conflict_policy() -> None:
    proposed = _scheduled_task(
        "task-b",
        edit_lease=EditScopeLease(
            lease_id="lease-b",
            task_id="task-b",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
            conflict_policy="merge-later",
        ),
    )
    state = SchedulerState(tasks={"task-b": proposed})

    decision = evaluate_task_admission(state, "task-b")

    assert decision.state == "blocked"
    assert decision.edit_lease_conflict is not None
    assert decision.edit_lease_conflict.classification == "unsupported_policy"
    assert "unsupported edit lease conflict_policy" in decision.reason


def test_edit_lease_classifier_blocks_unsafe_project_relative_paths() -> None:
    proposed = _scheduled_task(
        "task-b",
        edit_lease=EditScopeLease(
            lease_id="lease-b",
            task_id="task-b",
            allowed_artifacts=("../outside.py",),
            lease_mode="write",
        ),
    )
    state = SchedulerState(tasks={"task-b": proposed})

    decision = evaluate_task_admission(state, "task-b")

    assert decision.state == "blocked"
    assert decision.edit_lease_conflict is not None
    assert decision.edit_lease_conflict.classification == "unsafe_path"
    assert decision.edit_lease_conflict.left_path == "../outside.py"
    assert "unsafe edit lease path" in decision.reason


def test_edit_lease_classifier_keeps_read_write_compatible() -> None:
    running = _scheduled_task(
        "task-a",
        state="running",
        edit_lease=EditScopeLease(
            lease_id="lease-a",
            task_id="task-a",
            allowed_artifacts=("src/app.py",),
            lease_mode="read",
        ),
    )
    proposed = _scheduled_task(
        "task-b",
        edit_lease=EditScopeLease(
            lease_id="lease-b",
            task_id="task-b",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
    )
    state = SchedulerState(tasks={"task-a": running, "task-b": proposed})

    decision = evaluate_task_admission(state, "task-b")

    assert decision.state == "admissible"
    assert decision.edit_lease_conflict is None


def test_edit_lease_lifecycle_acquires_when_task_becomes_ready(tmp_path) -> None:
    event_log = JsonlSchedulerEventLog(tmp_path / "lease-acquire-events.jsonl")
    proposed = _scheduled_task(
        "task-b",
        edit_lease=EditScopeLease(
            lease_id="lease-b",
            task_id="task-b",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
            expires_at="2026-06-20T12:30:00+08:00",
        ),
    )
    state = SchedulerState(tasks={"task-b": proposed})

    updated = mark_ready_tasks(
        state,
        event_log=event_log,
        timestamp="2026-06-20T12:00:00+08:00",
    )

    record = updated.edit_lease_lifecycle["lease-b"]
    assert updated.tasks["task-b"].state == "ready"
    assert record.state == "acquired"
    assert record.mode == "write"
    assert record.allowed_artifacts == ("src/app.py",)
    assert record.acquired_at == "2026-06-20T12:00:00+08:00"
    assert record.expires_at == "2026-06-20T12:30:00+08:00"
    events = event_log.read_all()
    assert events[0].event_kind == "task_ready"
    assert events[0].lease_id == "lease-b"
    assert events[0].edit_lease_lifecycle is not None
    assert events[0].edit_lease_lifecycle.state == "acquired"


def test_edit_lease_lifecycle_blocks_with_conflict_evidence() -> None:
    running = _scheduled_task(
        "task-a",
        state="running",
        edit_lease=EditScopeLease(
            lease_id="lease-a",
            task_id="task-a",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
    )
    proposed = _scheduled_task(
        "task-b",
        edit_lease=EditScopeLease(
            lease_id="lease-b",
            task_id="task-b",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
    )
    state = SchedulerState(tasks={"task-a": running, "task-b": proposed})

    updated = mark_ready_tasks(state, timestamp="2026-06-20T12:05:00+08:00")

    record = updated.edit_lease_lifecycle["lease-b"]
    assert updated.tasks["task-b"].state == "blocked"
    assert record.state == "blocked"
    assert record.conflict_decision is not None
    assert record.conflict_decision.classification == "exact_path_overlap"
    assert record.reason == "edit lease conflict with task-a: src/app.py"


def test_edit_lease_lifecycle_review_required_preserves_review_zone_evidence() -> None:
    running = _scheduled_task(
        "task-a",
        state="running",
        edit_lease=EditScopeLease(
            lease_id="lease-a",
            task_id="task-a",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
    )
    proposed = _scheduled_task(
        "task-b",
        edit_lease=EditScopeLease(
            lease_id="lease-b",
            task_id="task-b",
            allowed_artifacts=("src/app.py",),
            lease_mode="review-zone",
        ),
    )
    state = SchedulerState(tasks={"task-a": running, "task-b": proposed})

    updated = mark_ready_tasks(state, timestamp="2026-06-20T12:10:00+08:00")

    record = updated.edit_lease_lifecycle["lease-b"]
    assert updated.tasks["task-b"].state == "review_required"
    assert record.state == "review_required"
    assert record.conflict_decision is not None
    assert record.conflict_decision.classification == "review_zone_overlap"


def test_edit_lease_lifecycle_releases_on_completed_task(tmp_path) -> None:
    store = InMemoryArtifactVersionStore()
    runtime = FakeAgentRuntimeAdapter(
        artifact_store=store,
        timestamp="2026-06-20T12:20:00+08:00",
    )
    event_log = JsonlSchedulerEventLog(tmp_path / "lease-release-events.jsonl")
    task = _scheduled_task(
        "task-b",
        state="ready",
        edit_lease=EditScopeLease(
            lease_id="lease-b",
            task_id="task-b",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
        output_artifact_id="task-b:result",
    )
    state = SchedulerState(
        tasks={"task-b": task},
        edit_lease_lifecycle={
            "lease-b": EditLeaseLifecycleRecord(
                lease_id="lease-b",
                task_id="task-b",
                state="acquired",
                mode="write",
                allowed_artifacts=("src/app.py",),
                acquired_at="2026-06-20T12:00:00+08:00",
            )
        },
    )

    updated, _ = run_ready_task(
        state,
        "task-b",
        runtime=runtime,
        event_log=event_log,
        timestamp="2026-06-20T12:20:00+08:00",
    )

    record = updated.edit_lease_lifecycle["lease-b"]
    assert updated.tasks["task-b"].state == "complete"
    assert record.state == "released"
    assert record.acquired_at == "2026-06-20T12:00:00+08:00"
    assert record.released_at == "2026-06-20T12:20:00+08:00"
    events = event_log.read_all()
    assert events[-1].event_kind == "task_completed"
    assert events[-1].edit_lease_lifecycle is not None
    assert events[-1].edit_lease_lifecycle.state == "released"


def test_edit_lease_lifecycle_revokes_on_permission_rejection(tmp_path) -> None:
    event_log = JsonlSchedulerEventLog(tmp_path / "lease-revoke-events.jsonl")
    task = _scheduled_task(
        "task-b",
        state="review_required",
        edit_lease=EditScopeLease(
            lease_id="lease-b",
            task_id="task-b",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
    )
    task = replace(
        task,
        run_id="run-b",
        output_artifact_ref=ExchangeReference(
            ref_kind="exchange_artifact",
            ref_id="task-b:result",
            version="v1",
        ),
    )
    state = SchedulerState(
        tasks={"task-b": task},
        edit_lease_lifecycle={
            "lease-b": EditLeaseLifecycleRecord(
                lease_id="lease-b",
                task_id="task-b",
                state="acquired",
                mode="write",
                allowed_artifacts=("src/app.py",),
                acquired_at="2026-06-20T12:00:00+08:00",
            )
        },
    )

    updated = resolve_task_permission_review(
        state,
        "task-b",
        approved=False,
        reason="write permission denied",
        event_log=event_log,
        timestamp="2026-06-20T12:25:00+08:00",
    )

    record = updated.edit_lease_lifecycle["lease-b"]
    assert updated.tasks["task-b"].state == "blocked"
    assert record.state == "revoked"
    assert record.reason == "write permission denied"
    assert record.released_at == "2026-06-20T12:25:00+08:00"
    assert event_log.read_all()[-1].edit_lease_lifecycle is not None


def test_edit_lease_lifecycle_revokes_on_runtime_failure(tmp_path) -> None:
    event_log = JsonlSchedulerEventLog(tmp_path / "lease-runtime-failure-events.jsonl")
    task = _scheduled_task(
        "task-b",
        state="ready",
        edit_lease=EditScopeLease(
            lease_id="lease-b",
            task_id="task-b",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
    )
    state = SchedulerState(
        tasks={"task-b": task},
        edit_lease_lifecycle={
            "lease-b": EditLeaseLifecycleRecord(
                lease_id="lease-b",
                task_id="task-b",
                state="acquired",
                mode="write",
                allowed_artifacts=("src/app.py",),
                acquired_at="2026-06-20T12:00:00+08:00",
            )
        },
    )

    result = drain_ready_tasks(
        state,
        runtime=_FailingRuntime("boom"),
        event_log=event_log,
        timestamp="2026-06-20T12:26:00+08:00",
    )

    record = result.state.edit_lease_lifecycle["lease-b"]
    assert result.state.tasks["task-b"].state == "blocked"
    assert record.state == "revoked"
    assert record.reason == "runtime failure: boom"
    assert event_log.read_all()[-1].edit_lease_lifecycle is not None


def test_edit_lease_lifecycle_expiry_requires_explicit_now(tmp_path) -> None:
    event_log = JsonlSchedulerEventLog(tmp_path / "lease-expire-events.jsonl")
    state = SchedulerState(
        tasks={
            "task-b": _scheduled_task(
                "task-b",
                edit_lease=EditScopeLease(
                    lease_id="lease-b",
                    task_id="task-b",
                    allowed_artifacts=("src/app.py",),
                    lease_mode="write",
                    expires_at="2026-06-20T12:30:00+08:00",
                ),
            )
        },
        edit_lease_lifecycle={
            "lease-b": EditLeaseLifecycleRecord(
                lease_id="lease-b",
                task_id="task-b",
                state="acquired",
                mode="write",
                allowed_artifacts=("src/app.py",),
                acquired_at="2026-06-20T12:00:00+08:00",
                expires_at="2026-06-20T12:30:00+08:00",
            )
        },
    )

    unchanged = expire_edit_leases(state, event_log=event_log)
    expired = expire_edit_leases(
        state,
        now="2026-06-20T12:31:00+08:00",
        event_log=event_log,
    )

    assert unchanged.edit_lease_lifecycle["lease-b"].state == "acquired"
    assert event_log.read_all()[0].event_kind == "lease_expired"
    record = expired.edit_lease_lifecycle["lease-b"]
    assert record.state == "expired"
    assert record.released_at == "2026-06-20T12:31:00+08:00"


def test_shared_process_sandbox_provider_allocates_metadata_only() -> None:
    provider = SharedProcessSandboxProvider()
    capability = provider.capability()
    request = SandboxRequest(
        task_id="task-1",
        profile=SandboxProfile(
            profile_id="shared",
            profile_kind="shared-process",
            network_policy="disabled",
            secret_policy="deny",
            mount_policy="lease-scoped",
        ),
        edit_lease=EditScopeLease(
            lease_id="lease-1",
            task_id="task-1",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
        edit_lease_lifecycle=EditLeaseLifecycleRecord(
            lease_id="lease-1",
            task_id="task-1",
            state="acquired",
            mode="write",
            allowed_artifacts=("src/app.py",),
            acquired_at="2026-06-21T00:00:00+08:00",
        ),
        workspace_root="E:/workspace/project",
        scratch_path=".codex/scratch/task-1",
        required_mounts=("README.md",),
    )

    allocation = provider.allocate(request)

    assert capability.provider == "shared-process"
    assert capability.supports_process_isolation is False
    assert capability.supports_filesystem_isolation is False
    assert capability.supports_secret_policy is True
    assert allocation.state == "allocated"
    assert allocation.allocation_id == "shared-process:task-1:shared"
    assert allocation.workspace_root == "E:/workspace/project"
    assert allocation.scratch_path == ".codex/scratch/task-1"
    assert allocation.visible_mounts == ("README.md", "src/app.py")
    assert allocation.network_policy == "disabled"
    assert allocation.secret_policy == "deny"
    assert allocation.cleanup_required is False
    assert allocation.lease_authorization_state == "authorized"
    assert allocation.lease_authorized_mounts[0].lease_id == "lease-1"
    assert allocation.lease_authorized_mounts[0].authorized_mounts == ("src/app.py",)


def test_shared_process_sandbox_provider_rejects_static_lease_without_acquired_lifecycle() -> None:
    provider = SharedProcessSandboxProvider()

    allocation = provider.allocate(
        SandboxRequest(
            task_id="task-1",
            profile=SandboxProfile(
                profile_id="shared",
                profile_kind="shared-process",
                mount_policy="lease-scoped",
            ),
            edit_lease=EditScopeLease(
                lease_id="lease-1",
                task_id="task-1",
                allowed_artifacts=("src/app.py",),
                lease_mode="write",
            ),
            required_mounts=("README.md",),
        )
    )

    assert allocation.state == "rejected"
    assert allocation.visible_mounts == ("README.md",)
    assert allocation.lease_authorization_state == "rejected"
    assert allocation.lease_authorized_mounts[0].denied_mounts == ("src/app.py",)
    assert "require acquired edit lease lifecycle record" in allocation.reason


def test_shared_process_sandbox_provider_rejects_other_profile_kind() -> None:
    provider = SharedProcessSandboxProvider()

    allocation = provider.allocate(
        SandboxRequest(
            task_id="task-1",
            profile=SandboxProfile(profile_id="docker", profile_kind="docker"),
        )
    )

    assert allocation.state == "rejected"
    assert allocation.provider == "shared-process"
    assert "profile_kind='shared-process'" in allocation.reason


def test_git_worktree_sandbox_provider_advertises_filesystem_isolation(tmp_path) -> None:
    provider = GitWorktreeSandboxProvider(tmp_path / "sandboxes")

    capability = provider.capability()

    assert capability.provider == "git-worktree"
    assert capability.supports_process_isolation is False
    assert capability.supports_filesystem_isolation is True
    assert capability.supports_mount_policy is True
    assert capability.supports_cleanup is True


def test_git_worktree_sandbox_provider_allocates_and_cleans_up_worktree(tmp_path) -> None:
    repo = _git_repo(tmp_path)
    provider = GitWorktreeSandboxProvider(tmp_path / "sandboxes")
    request = SandboxRequest(
        task_id="task-1",
        profile=SandboxProfile(
            profile_id="worktree",
            profile_kind="git-worktree",
            network_policy="disabled",
            secret_policy="deny",
            mount_policy="lease-scoped",
        ),
        edit_lease=EditScopeLease(
            lease_id="lease-1",
            task_id="task-1",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
        edit_lease_lifecycle=EditLeaseLifecycleRecord(
            lease_id="lease-1",
            task_id="task-1",
            state="acquired",
            mode="write",
            allowed_artifacts=("src/app.py",),
            acquired_at="2026-06-21T00:00:00+08:00",
        ),
        workspace_root=str(repo),
        scratch_path=".codex/scratch/task-1",
        required_mounts=("README.md",),
    )

    allocation = provider.allocate(request)

    assert allocation.state == "allocated"
    assert allocation.provider == "git-worktree"
    assert allocation.allocation_id == "git-worktree:task-1:worktree"
    assert allocation.visible_mounts == ("README.md", "src/app.py")
    assert allocation.cleanup_required is True
    assert allocation.lease_authorization_state == "authorized"
    assert allocation.lease_authorized_mounts[0].authorized_mounts == ("src/app.py",)
    receipt = allocation.git_worktree_receipt
    assert receipt is not None
    assert receipt.source_repository_root == str(repo)
    assert receipt.sandbox_root == str(tmp_path / "sandboxes")
    assert receipt.branch_name.startswith("dbc-sandbox/task-1-worktree-")
    assert receipt.authorized_writable_paths == ("src/app.py",)
    assert receipt.denied_writable_paths == ()
    assert receipt.cleanup_state == "required"
    assert receipt.allocation.returncode == 0
    assert Path(receipt.worktree_path).exists()

    cleaned = provider.cleanup(allocation)

    cleaned_receipt = cleaned.git_worktree_receipt
    assert cleaned.cleanup_required is False
    assert cleaned_receipt is not None
    assert cleaned_receipt.cleanup_state == "completed"
    assert cleaned_receipt.cleanup.returncode == 0
    assert cleaned_receipt.branch_cleanup.returncode == 0
    assert not Path(receipt.worktree_path).exists()


def test_git_worktree_sandbox_provider_rejects_missing_lifecycle_without_worktree(
    tmp_path,
) -> None:
    repo = _git_repo(tmp_path)
    sandbox_root = tmp_path / "sandboxes"
    provider = GitWorktreeSandboxProvider(sandbox_root)

    allocation = provider.allocate(
        SandboxRequest(
            task_id="task-1",
            profile=SandboxProfile(profile_id="worktree", profile_kind="git-worktree"),
            edit_lease=EditScopeLease(
                lease_id="lease-1",
                task_id="task-1",
                allowed_artifacts=("src/app.py",),
                lease_mode="write",
            ),
            workspace_root=str(repo),
            required_mounts=("README.md",),
        )
    )

    assert allocation.state == "rejected"
    assert allocation.cleanup_required is False
    assert allocation.lease_authorization_state == "rejected"
    assert allocation.lease_authorized_mounts[0].denied_mounts == ("src/app.py",)
    assert "require acquired edit lease lifecycle record" in allocation.reason
    receipt = allocation.git_worktree_receipt
    assert receipt is not None
    assert receipt.denied_writable_paths == ("src/app.py",)
    assert receipt.allocation.command == ()
    assert not sandbox_root.exists()


def test_git_worktree_sandbox_provider_rejects_non_acquired_lifecycle(tmp_path) -> None:
    repo = _git_repo(tmp_path)
    sandbox_root = tmp_path / "sandboxes"
    provider = GitWorktreeSandboxProvider(sandbox_root)

    allocation = provider.allocate(
        SandboxRequest(
            task_id="task-1",
            profile=SandboxProfile(profile_id="worktree", profile_kind="git-worktree"),
            edit_lease=EditScopeLease(
                lease_id="lease-1",
                task_id="task-1",
                allowed_artifacts=("src/app.py",),
                lease_mode="write",
            ),
            edit_lease_lifecycle=EditLeaseLifecycleRecord(
                lease_id="lease-1",
                task_id="task-1",
                state="released",
                mode="write",
                allowed_artifacts=("src/app.py",),
                released_at="2026-06-21T00:05:00+08:00",
            ),
            workspace_root=str(repo),
        )
    )

    assert allocation.state == "rejected"
    assert allocation.cleanup_required is False
    assert allocation.lease_authorization_state == "rejected"
    assert allocation.lease_authorized_mounts[0].lifecycle_state == "released"
    assert "current lifecycle state is 'released'" in allocation.reason
    receipt = allocation.git_worktree_receipt
    assert receipt is not None
    assert receipt.denied_writable_paths == ("src/app.py",)
    assert not sandbox_root.exists()


def test_orchestration_preflight_bundle_can_use_git_worktree_provider(tmp_path) -> None:
    repo = _git_repo(tmp_path)
    registry = SandboxProviderRegistry()
    provider = GitWorktreeSandboxProvider(tmp_path / "sandboxes")
    registry.register(provider)
    task = _scheduled_task(
        "task-1",
        state="ready",
        edit_lease=EditScopeLease(
            lease_id="lease-1",
            task_id="task-1",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
        sandbox_profile=SandboxProfile(
            profile_id="worktree",
            profile_kind="git-worktree",
            mount_policy="lease-scoped",
        ),
        input_artifact_refs=(ExchangeReference(ref_kind="file", ref_id="readme", path="README.md"),),
        output_artifact_id="task-1:result",
    )
    state = SchedulerState(
        tasks={"task-1": task},
        edit_lease_lifecycle={
            "lease-1": EditLeaseLifecycleRecord(
                lease_id="lease-1",
                task_id="task-1",
                state="acquired",
                mode="write",
                allowed_artifacts=("src/app.py",),
                acquired_at="2026-06-21T00:00:00+08:00",
            )
        },
    )

    bundle = build_orchestration_preflight_bundle(
        task,
        sandbox_registry=registry,
        scheduler_state=state,
        workspace_root=str(repo),
    )

    assert bundle.sandbox_allocation.provider == "git-worktree"
    assert bundle.sandbox_allocation.state == "allocated"
    assert bundle.sandbox_allocation.visible_mounts == ("README.md", "src/app.py")
    assert bundle.sandbox_allocation.git_worktree_receipt is not None

    provider.cleanup(bundle.sandbox_allocation)


def test_worker_patch_review_artifact_collects_git_worktree_diff(tmp_path) -> None:
    repo = _git_repo(tmp_path)
    registry = SandboxProviderRegistry()
    provider = GitWorktreeSandboxProvider(tmp_path / "sandboxes")
    registry.register(provider)
    task = _scheduled_task(
        "task-1",
        state="ready",
        agent=AgentSpec(agent_id="agent:codex-worker", runtime_provider="codex"),
        edit_lease=EditScopeLease(
            lease_id="lease-1",
            task_id="task-1",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
        sandbox_profile=SandboxProfile(
            profile_id="worktree",
            profile_kind="git-worktree",
            mount_policy="lease-scoped",
        ),
        output_artifact_id="task-1:result",
    )
    state = SchedulerState(
        tasks={"task-1": task},
        edit_lease_lifecycle={
            "lease-1": EditLeaseLifecycleRecord(
                lease_id="lease-1",
                task_id="task-1",
                state="acquired",
                mode="write",
                allowed_artifacts=("src/app.py",),
            )
        },
    )
    bundle = build_orchestration_preflight_bundle(
        task,
        sandbox_registry=registry,
        scheduler_state=state,
        workspace_root=str(repo),
    )
    receipt = bundle.sandbox_allocation.git_worktree_receipt
    assert receipt is not None
    app = Path(receipt.worktree_path) / "src" / "app.py"
    app.parent.mkdir(parents=True, exist_ok=True)
    app.write_text("print('worker patch')\n", encoding="utf-8")
    output = ExchangeArtifact(
        artifact_id="task-1:result",
        kind="result",
        intent="inform",
        producer="agent:codex-worker",
        version="v1",
    )
    run = PreflightedTaskRunResult(
        preflight=bundle,
        state=state,
        runtime_result=RuntimeRunResult(
            run_handle=RunHandle(
                run_id="codex-run-1",
                session_id="codex-session-1",
                task_id="task-1",
            ),
            output_artifact=output,
            artifact_delta=ArtifactDelta(
                artifact_id="task-1:result",
                version="v1",
                summary="worker changed src/app.py",
                changed_refs=(
                    ExchangeReference(
                        ref_kind="file",
                        ref_id="src/app.py",
                        path="src/app.py",
                    ),
                ),
            ),
        ),
    )

    review = build_worker_patch_review_artifact(
        run,
        timestamp="2026-06-24T23:58:00+08:00",
        guide_agent_id="agent:guide",
        target_task_id="task:merge-target",
    )

    assert review.patch_state == "has_patch"
    assert review.changed_paths == ("src/app.py",)
    assert "worker patch" in review.patch_text
    assert review.artifact.intent == "request_merge"
    assert has_scheduler_readable_relation(review.artifact, "merges_into")
    assert review.artifact.parts[1].data["sandbox_workspace_root"] == receipt.worktree_path

    provider.cleanup(bundle.sandbox_allocation)


def test_worker_patch_review_consumer_checks_without_mutating_workspace(tmp_path) -> None:
    source_repo = _git_repo(tmp_path / "source")
    target_repo = _git_repo(tmp_path / "target")
    store_path, disposition_id = _worker_patch_review_store(
        tmp_path,
        source_repo=source_repo,
        target_surface="workerPatchReview",
    )

    result = consume_worker_patch_review_decision(
        artifact_store_path=store_path,
        disposition_artifact_id=disposition_id,
        disposition_version="v1",
        action="check",
        source_workspace_root=target_repo,
        actor="agent:guide",
        timestamp="2026-06-24T23:59:00+08:00",
    )
    stored = JsonArtifactVersionStore(store_path).get("task-1:patch-review", "v1").artifact

    assert result.ok is True
    assert result.git_check_returncode == 0
    assert result.git_apply_returncode is None
    assert result.changed_paths == ("src/app.py",)
    assert result.to_json_dict()["authority_split"]["source_workspace_mutated"] is False
    assert (target_repo / "src" / "app.py").read_text(encoding="utf-8") == "print('ok')\n"
    assert stored.lifecycle_state == "accepted"


def test_worker_patch_review_consumer_applies_patch_and_marks_consumed(tmp_path) -> None:
    source_repo = _git_repo(tmp_path / "source")
    target_repo = _git_repo(tmp_path / "target")
    store_path, disposition_id = _worker_patch_review_store(
        tmp_path,
        source_repo=source_repo,
        target_surface="cli:scheduler consume-worker-patch-review",
    )

    result = consume_worker_patch_review_decision(
        artifact_store_path=store_path,
        disposition_artifact_id=disposition_id,
        disposition_version="v1",
        action="apply",
        source_workspace_root=target_repo,
        actor="agent:guide",
        timestamp="2026-06-25T00:00:00+08:00",
    )
    stored = JsonArtifactVersionStore(store_path).get("task-1:patch-review", "v1").artifact

    assert result.ok is True
    assert result.git_check_returncode == 0
    assert result.git_apply_returncode == 0
    assert result.cleanup_recommended is True
    assert result.to_json_dict()["authority_split"]["patch_apply_executed"] is True
    assert result.to_json_dict()["authority_split"]["source_workspace_mutated"] is True
    assert (target_repo / "src" / "app.py").read_text(encoding="utf-8") == (
        "print('worker patch')\n"
    )
    assert stored.lifecycle_state == "consumed"


def test_worker_patch_review_consumer_rejects_without_git_apply(tmp_path) -> None:
    source_repo = _git_repo(tmp_path / "source")
    store_path, disposition_id = _worker_patch_review_store(
        tmp_path,
        source_repo=source_repo,
        target_surface="workerPatchReview",
    )

    result = consume_worker_patch_review_decision(
        artifact_store_path=store_path,
        disposition_artifact_id=disposition_id,
        disposition_version="v1",
        action="reject",
        actor="agent:guide",
        reason="not needed",
    )
    stored = JsonArtifactVersionStore(store_path).get("task-1:patch-review", "v1").artifact

    assert result.ok is True
    assert result.git_check_returncode is None
    assert result.git_apply_returncode is None
    assert result.cleanup_recommended is True
    assert result.to_json_dict()["authority_split"]["patch_apply_executed"] is False
    assert stored.lifecycle_state == "rejected"


def test_worker_patch_review_operator_checks_candidate_without_apply(tmp_path) -> None:
    source_repo = _git_repo(tmp_path / "source")
    target_repo = _git_repo(tmp_path / "target")
    store_path, _disposition_id = _worker_patch_review_store(
        tmp_path,
        source_repo=source_repo,
        target_surface="workerPatchReview",
    )

    result = review_worker_patch_action_candidate(
        artifact_store_path=store_path,
        candidate_id="task-1:patch-review@v1:merge",
        action="check",
        source_workspace_root=target_repo,
        actor="agent:guide",
        disposition_artifact_id="task-1:operator-check-decision",
        timestamp="2026-06-25T00:05:00+08:00",
    )
    stored = JsonArtifactVersionStore(store_path).get("task-1:patch-review", "v1").artifact

    assert result.ok is True
    assert result.disposition.disposition == "accept"
    assert result.consumer.git_check_returncode == 0
    assert result.consumer.git_apply_returncode is None
    assert result.to_json_dict()["authority_split"]["source_workspace_mutated"] is False
    assert (target_repo / "src" / "app.py").read_text(encoding="utf-8") == "print('ok')\n"
    assert stored.lifecycle_state == "accepted"


def test_worker_patch_review_operator_rejects_candidate_without_git(tmp_path) -> None:
    source_repo = _git_repo(tmp_path / "source")
    store_path, _disposition_id = _worker_patch_review_store(
        tmp_path,
        source_repo=source_repo,
        target_surface="workerPatchReview",
    )

    result = review_worker_patch_action_candidate(
        artifact_store_path=store_path,
        candidate_id="task-1:patch-review@v1:merge",
        action="reject",
        actor="agent:guide",
        disposition_artifact_id="task-1:operator-reject-decision",
        reason="defer patch",
    )
    stored = JsonArtifactVersionStore(store_path).get("task-1:patch-review", "v1").artifact

    assert result.ok is True
    assert result.consumer.git_check_returncode is None
    assert result.consumer.git_apply_returncode is None
    assert result.consumer.cleanup_recommended is True
    assert result.to_json_dict()["authority_split"]["patch_apply_executed"] is False
    assert stored.lifecycle_state == "rejected"


def test_worker_patch_review_operator_rejects_apply_boundary(tmp_path) -> None:
    source_repo = _git_repo(tmp_path / "source")
    target_repo = _git_repo(tmp_path / "target")
    store_path, _disposition_id = _worker_patch_review_store(
        tmp_path,
        source_repo=source_repo,
        target_surface="workerPatchReview",
    )

    with pytest.raises(ValueError, match="check, reject"):
        review_worker_patch_action_candidate(
            artifact_store_path=store_path,
            candidate_id="task-1:patch-review@v1:merge",
            action="apply",  # type: ignore[arg-type]
            source_workspace_root=target_repo,
            actor="agent:guide",
        )


def test_worker_patch_composition_preflight_passes_without_mutating_source(tmp_path) -> None:
    source_repo = _git_repo(tmp_path / "source")
    (source_repo / "src" / "extra.py").write_text("print('extra')\n", encoding="utf-8")
    _run_git(source_repo, "add", ".")
    _run_git(source_repo, "commit", "-m", "add extra")
    store_path = tmp_path / "exchange-artifacts.json"
    _store_worker_patch_artifact(
        store_path,
        artifact_id="task-client:patch-review",
        task_id="task-client",
        lane_id="lane:client",
        worker_agent_id="agent:client-worker",
        changed_path="src/app.py",
        patch_text=_patch_for_file_change(
            tmp_path / "patch-client",
            relative_path="src/app.py",
            original="print('ok')\n",
            changed="print('client patch')\n",
        ),
    )
    _store_worker_patch_artifact(
        store_path,
        artifact_id="task-server:patch-review",
        task_id="task-server",
        lane_id="lane:server",
        worker_agent_id="agent:server-worker",
        changed_path="src/extra.py",
        patch_text=_patch_for_file_change(
            tmp_path / "patch-server",
            relative_path="src/extra.py",
            original="print('extra')\n",
            changed="print('server patch')\n",
        ),
    )

    result = preflight_worker_patch_composition(
        artifact_store_path=store_path,
        patch_refs=worker_patch_composition_refs_from_tokens(
            ("task-client:patch-review@v1", "task-server:patch-review@v1")
        ),
        source_workspace_root=source_repo,
        scratch_root=tmp_path / "scratch",
    )

    assert result.ok is True
    assert [step.ref.artifact_id for step in result.steps] == [
        "task-client:patch-review",
        "task-server:patch-review",
    ]
    assert result.touched_path_collisions == {}
    assert result.to_json_dict()["authority_split"]["source_workspace_mutated"] is False
    assert (source_repo / "src" / "app.py").read_text(encoding="utf-8") == "print('ok')\n"
    assert (source_repo / "src" / "extra.py").read_text(encoding="utf-8") == "print('extra')\n"


def test_worker_patch_composition_preflight_reports_first_conflict(tmp_path) -> None:
    source_repo = _git_repo(tmp_path / "source")
    store_path = tmp_path / "exchange-artifacts.json"
    _store_worker_patch_artifact(
        store_path,
        artifact_id="task-a:patch-review",
        task_id="task-a",
        lane_id="lane:a",
        worker_agent_id="agent:a",
        changed_path="src/app.py",
        patch_text=_patch_for_file_change(
            tmp_path / "patch-a",
            relative_path="src/app.py",
            original="print('ok')\n",
            changed="print('a patch')\n",
        ),
    )
    _store_worker_patch_artifact(
        store_path,
        artifact_id="task-b:patch-review",
        task_id="task-b",
        lane_id="lane:b",
        worker_agent_id="agent:b",
        changed_path="src/app.py",
        patch_text=_patch_for_file_change(
            tmp_path / "patch-b",
            relative_path="src/app.py",
            original="print('ok')\n",
            changed="print('b patch')\n",
        ),
    )

    result = preflight_worker_patch_composition(
        artifact_store_path=store_path,
        patch_refs=worker_patch_composition_refs_from_tokens(
            ("task-a:patch-review@v1", "task-b:patch-review@v1")
        ),
        source_workspace_root=source_repo,
    )

    assert result.ok is False
    assert result.failed_ref is not None
    assert result.failed_ref.artifact_id == "task-b:patch-review"
    assert len(result.steps) == 2
    assert result.steps[0].ok is True
    assert result.steps[1].check_returncode != 0
    assert result.touched_path_collisions == {
        "src/app.py": ("task-a:patch-review@v1", "task-b:patch-review@v1")
    }
    assert (source_repo / "src" / "app.py").read_text(encoding="utf-8") == "print('ok')\n"


def test_sandbox_provider_registry_resolves_provider_by_capability() -> None:
    registry = SandboxProviderRegistry()
    provider = SharedProcessSandboxProvider()

    registered = registry.register(provider)

    assert registered is provider
    assert registry.providers() == ("shared-process",)
    assert registry.get("shared-process") is provider

    with pytest.raises(ValueError, match="already registered"):
        registry.register(provider)
    with pytest.raises(KeyError, match="available providers: shared-process"):
        registry.get("docker")


def test_sandbox_capability_placeholders_do_not_claim_available_provider() -> None:
    docker = sandbox_capability_placeholder("docker")
    remote = sandbox_capability_placeholder("remote-vm")
    none = sandbox_capability_placeholder("none")

    assert docker.provider == "docker"
    assert docker.supports_process_isolation is True
    assert "placeholder only" in docker.notes
    assert remote.supports_network_policy is True
    assert "placeholder only" in remote.notes
    assert none.provider == "none"
    assert "incompatible with edit-lease tasks" in none.notes


def test_orchestration_preflight_bundle_assembles_runtime_sandbox_and_scratch() -> None:
    registry = SandboxProviderRegistry()
    registry.register(SharedProcessSandboxProvider())
    task = _scheduled_task(
        "task-1",
        state="ready",
        edit_lease=EditScopeLease(
            lease_id="lease-1",
            task_id="task-1",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
        input_artifact_refs=(
            ExchangeReference(
                ref_kind="file",
                ref_id="README",
                path="README.md",
            ),
        ),
        output_artifact_id="task-1:result",
    )
    state = SchedulerState(
        tasks={"task-1": task},
        edit_lease_lifecycle={
            "lease-1": EditLeaseLifecycleRecord(
                lease_id="lease-1",
                task_id="task-1",
                state="acquired",
                mode="write",
                allowed_artifacts=("src/app.py",),
                acquired_at="2026-06-21T00:00:00+08:00",
            )
        },
    )

    bundle = build_orchestration_preflight_bundle(
        task,
        sandbox_registry=registry,
        scheduler_state=state,
        workspace_root="E:/workspace/project",
        scratch_root=".codex/scratch",
        created_at="2026-06-17T00:10:00+08:00",
        expires_at="2026-06-17T01:10:00+08:00",
    )

    assert bundle.task is task
    assert bundle.runtime_task.task_id == "task-1"
    assert bundle.runtime_task.output_artifact_id == "task-1:result"
    assert bundle.runtime_task.scope.task_id == "task-1"
    assert bundle.scratch.scratch_id == "scratch:task-1"
    assert bundle.scratch.path == ".codex/scratch/task-1"
    assert bundle.scratch.manifest_path == ".codex/scratch/task-1/manifest.json"
    assert bundle.sandbox_allocation.state == "allocated"
    assert bundle.sandbox_allocation.workspace_root == "E:/workspace/project"
    assert bundle.sandbox_allocation.scratch_path == ".codex/scratch/task-1"
    assert bundle.sandbox_allocation.visible_mounts == ("README.md", "src/app.py")
    assert bundle.sandbox_allocation.lease_authorization_state == "authorized"


def test_orchestration_preflight_bundle_rejects_missing_acquired_lease_lifecycle() -> None:
    registry = SandboxProviderRegistry()
    registry.register(SharedProcessSandboxProvider())
    task = _scheduled_task(
        "task-1",
        state="ready",
        edit_lease=EditScopeLease(
            lease_id="lease-1",
            task_id="task-1",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
    )

    with pytest.raises(ValueError, match="require acquired edit lease lifecycle record"):
        build_orchestration_preflight_bundle(
            task,
            sandbox_registry=registry,
            scheduler_state=SchedulerState(tasks={"task-1": task}),
        )


def test_orchestration_preflight_bundle_rejects_non_acquired_lease_lifecycle() -> None:
    registry = SandboxProviderRegistry()
    registry.register(SharedProcessSandboxProvider())
    task = _scheduled_task(
        "task-1",
        state="ready",
        edit_lease=EditScopeLease(
            lease_id="lease-1",
            task_id="task-1",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
    )
    state = SchedulerState(
        tasks={"task-1": task},
        edit_lease_lifecycle={
            "lease-1": EditLeaseLifecycleRecord(
                lease_id="lease-1",
                task_id="task-1",
                state="released",
                mode="write",
                allowed_artifacts=("src/app.py",),
                released_at="2026-06-21T00:05:00+08:00",
            )
        },
    )

    with pytest.raises(ValueError, match="current lifecycle state is 'released'"):
        build_orchestration_preflight_bundle(
            task,
            sandbox_registry=registry,
            scheduler_state=state,
        )


def test_orchestration_preflight_bundle_requires_ready_task() -> None:
    registry = SandboxProviderRegistry()
    registry.register(SharedProcessSandboxProvider())

    with pytest.raises(ValueError, match="state is 'proposed'"):
        build_orchestration_preflight_bundle(
            _scheduled_task("task-1", state="proposed"),
            sandbox_registry=registry,
        )


def test_orchestration_preflight_bundle_surfaces_sandbox_rejection() -> None:
    registry = SandboxProviderRegistry()
    registry.register(SharedProcessSandboxProvider())
    task = _scheduled_task(
        "task-1",
        state="ready",
        sandbox_profile=SandboxProfile(profile_id="docker", profile_kind="docker"),
    )

    with pytest.raises(KeyError, match="no sandbox provider registered for 'docker'"):
        build_orchestration_preflight_bundle(task, sandbox_registry=registry)


def test_scheduler_authorization_readback_reports_acquired_mount_authorization() -> None:
    task = _scheduled_task(
        "task-1",
        state="ready",
        edit_lease=EditScopeLease(
            lease_id="lease-1",
            task_id="task-1",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
        input_artifact_refs=(
            ExchangeReference(ref_kind="file", ref_id="readme", path="README.md"),
        ),
    )
    state = SchedulerState(
        tasks={"task-1": task},
        edit_lease_lifecycle={
            "lease-1": EditLeaseLifecycleRecord(
                lease_id="lease-1",
                task_id="task-1",
                state="acquired",
                mode="write",
                allowed_artifacts=("src/app.py",),
                acquired_at="2026-06-21T01:20:00+08:00",
            )
        },
    )

    readback = inspect_scheduler_authorization(
        state,
        workspace_root="E:/workspace/project",
        snapshot_path="scheduler-state.json",
    )
    payload = readback.to_json_dict()
    task_payload = payload["tasks"][0]
    sandbox = task_payload["sandbox_authorization"]

    assert payload["product_type"] == "scheduler_authorization_readback"
    assert payload["task_count"] == 1
    assert payload["edit_lease_task_count"] == 1
    assert payload["lifecycle_state_counts"] == {"acquired": 1}
    assert task_payload["lifecycle_missing"] is False
    assert task_payload["lifecycle"]["state"] == "acquired"
    assert sandbox["allocation_state"] == "allocated"
    assert sandbox["lease_authorization_state"] == "authorized"
    assert sandbox["visible_mounts"] == ["README.md", "src/app.py"]
    assert sandbox["lease_authorizations"][0]["authorized_mounts"] == ["src/app.py"]
    assert payload["authority_split"]["scheduler_state_mutated"] is False
    assert payload["authority_split"]["runtime_provider_executed"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False


def test_scheduler_authorization_readback_reports_missing_lifecycle_rejection() -> None:
    task = _scheduled_task(
        "task-1",
        state="ready",
        edit_lease=EditScopeLease(
            lease_id="lease-1",
            task_id="task-1",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
    )

    readback = inspect_scheduler_authorization(SchedulerState(tasks={"task-1": task}))
    task_payload = readback.to_json_dict()["tasks"][0]
    sandbox = task_payload["sandbox_authorization"]

    assert task_payload["has_edit_lease"] is True
    assert task_payload["lifecycle_missing"] is True
    assert task_payload["lifecycle"] is None
    assert sandbox["allocation_state"] == "rejected"
    assert sandbox["lease_authorization_state"] == "rejected"
    assert sandbox["lease_authorizations"][0]["denied_mounts"] == ["src/app.py"]
    assert "require acquired edit lease lifecycle record" in sandbox["allocation_reason"]


def test_scheduler_authorization_readback_reports_non_acquired_lifecycle_rejection() -> None:
    task = _scheduled_task(
        "task-1",
        state="ready",
        edit_lease=EditScopeLease(
            lease_id="lease-1",
            task_id="task-1",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
    )
    state = SchedulerState(
        tasks={"task-1": task},
        edit_lease_lifecycle={
            "lease-1": EditLeaseLifecycleRecord(
                lease_id="lease-1",
                task_id="task-1",
                state="released",
                mode="write",
                allowed_artifacts=("src/app.py",),
                released_at="2026-06-21T01:25:00+08:00",
            )
        },
    )

    task_payload = inspect_scheduler_authorization(state).to_json_dict()["tasks"][0]
    sandbox = task_payload["sandbox_authorization"]

    assert task_payload["lifecycle"]["state"] == "released"
    assert sandbox["allocation_state"] == "rejected"
    assert sandbox["lease_authorization_state"] == "rejected"
    assert sandbox["lease_authorizations"][0]["lifecycle_state"] == "released"
    assert "current lifecycle state is 'released'" in sandbox["allocation_reason"]


def test_scheduler_authorization_readback_summarizes_git_worktree_allocation_receipt() -> None:
    task = _git_worktree_task()
    state = _state_with_acquired_git_worktree_lease(task)
    allocation = _git_worktree_allocation(
        task,
        cleanup_required=True,
        cleanup_state="required",
    )

    payload = inspect_scheduler_authorization(
        state,
        sandbox_allocations={"task-1": allocation},
    ).to_json_dict()
    sandbox = payload["tasks"][0]["sandbox_authorization"]
    receipt = sandbox["git_worktree_receipt"]

    assert sandbox["profile_kind"] == "git-worktree"
    assert sandbox["allocation_state"] == "allocated"
    assert sandbox["lease_authorization_state"] == "authorized"
    assert receipt["source_repository_root"] == "E:/workspace/project"
    assert receipt["sandbox_root"] == "E:/workspace/sandboxes"
    assert receipt["worktree_path"].endswith("task-1-worktree")
    assert receipt["branch_name"] == "dbc-sandbox/task-1-worktree"
    assert receipt["authorized_writable_paths"] == ["src/app.py"]
    assert receipt["denied_writable_paths"] == []
    assert receipt["cleanup_state"] == "required"
    assert receipt["cleanup_required"] is True
    assert receipt["cleanup_owner"] == "host-or-daemon"
    assert receipt["cleanup_policy"] == "explicit-cleanup-required"
    assert receipt["allocation"]["command"] == [
        "git",
        "-C",
        "E:/workspace/project",
        "worktree",
        "add",
    ]
    assert receipt["allocation"]["returncode"] == 0
    assert payload["authority_split"]["real_sandbox_provider_executed"] is False


def test_scheduler_authorization_readback_summarizes_git_worktree_rejection_receipt() -> None:
    task = _git_worktree_task()
    state = SchedulerState(tasks={"task-1": task})
    allocation = _git_worktree_allocation(
        task,
        state="rejected",
        cleanup_required=False,
        cleanup_state="not_required",
        lifecycle_state="missing",
        authorized_mounts=(),
        denied_mounts=("src/app.py",),
        reason="require acquired edit lease lifecycle record",
    )

    sandbox = inspect_scheduler_authorization(
        state,
        sandbox_allocations={"task-1": allocation},
    ).to_json_dict()["tasks"][0]["sandbox_authorization"]
    receipt = sandbox["git_worktree_receipt"]

    assert sandbox["allocation_state"] == "rejected"
    assert sandbox["allocation_reason"] == "require acquired edit lease lifecycle record"
    assert sandbox["lease_authorization_state"] == "rejected"
    assert sandbox["lease_authorizations"][0]["denied_mounts"] == ["src/app.py"]
    assert receipt["cleanup_required"] is False
    assert receipt["cleanup_owner"] == "none"
    assert receipt["cleanup_policy"] == "no-cleanup-required"
    assert receipt["denied_writable_paths"] == ["src/app.py"]


def test_scheduler_authorization_readback_summarizes_git_worktree_cleanup_completed_receipt() -> None:
    task = _git_worktree_task()
    state = _state_with_acquired_git_worktree_lease(task)
    allocation = _git_worktree_allocation(
        task,
        cleanup_required=False,
        cleanup_state="completed",
        cleanup_returncode=0,
        branch_cleanup_returncode=0,
    )

    sandbox = inspect_scheduler_authorization(
        state,
        sandbox_allocations={"task-1": allocation},
    ).to_json_dict()["tasks"][0]["sandbox_authorization"]
    receipt = sandbox["git_worktree_receipt"]

    assert sandbox["allocation_state"] == "allocated"
    assert receipt["cleanup_state"] == "completed"
    assert receipt["cleanup_required"] is False
    assert receipt["cleanup_owner"] == "none"
    assert receipt["cleanup"]["command"] == ["git", "worktree", "remove", "--force"]
    assert receipt["cleanup"]["returncode"] == 0
    assert receipt["branch_cleanup"]["command"] == ["git", "branch", "-D"]
    assert receipt["branch_cleanup"]["returncode"] == 0


def test_scheduler_authorization_readback_reports_null_git_worktree_receipt_when_missing() -> None:
    task = _git_worktree_task()
    state = _state_with_acquired_git_worktree_lease(task)

    sandbox = inspect_scheduler_authorization(state).to_json_dict()["tasks"][0][
        "sandbox_authorization"
    ]

    assert sandbox["profile_kind"] == "git-worktree"
    assert sandbox["git_worktree_receipt"] is None
    assert sandbox["allocation_state"] == "rejected"
    assert "profile_kind='shared-process'" in sandbox["allocation_reason"]


def test_sandbox_allocation_receipt_evidence_round_trips_git_worktree_receipt(
    tmp_path,
) -> None:
    task = _git_worktree_task()
    allocation = _git_worktree_allocation(
        task,
        cleanup_required=True,
        cleanup_state="required",
    )
    evidence = build_sandbox_allocation_receipt_evidence(
        (allocation,),
        evidence_id="receipt:task-1",
        timestamp="2026-06-21T05:10:00+08:00",
        metadata={"source": "unit-test"},
    )
    evidence_path = default_sandbox_allocation_receipt_evidence_path(
        tmp_path,
        "receipt:task-1",
    )

    result = write_sandbox_allocation_receipt_evidence(evidence, evidence_path)
    summary = read_sandbox_allocation_receipt_evidence_summary(result.evidence_path)
    payload = summary.to_json_dict()
    restored = summary.allocations_by_task_id["task-1"]
    restored_receipt = restored.git_worktree_receipt

    assert result.evidence_path == tmp_path / ".codex/scheduler/evidence/receipt-task-1.json"
    assert payload["product_type"] == "sandbox_allocation_receipt_evidence"
    assert payload["schema_version"] == "1"
    assert payload["allocation_count"] == 1
    assert payload["authority_split"]["sandbox_provider_executed"] is False
    assert payload["authority_split"]["cleanup_executed"] is False
    assert payload["authority_split"]["evidence_written"] is True
    assert summary.metadata == {"source": "unit-test"}
    assert restored == allocation
    assert restored_receipt is not None
    assert restored_receipt.allocation.stdout == "allocated"
    assert restored_receipt.cleanup_state == "required"


def test_sandbox_allocation_receipt_evidence_rejects_wrong_contract(
    tmp_path,
) -> None:
    wrong_product = tmp_path / "wrong-product.json"
    wrong_product.write_text(
        json.dumps(
            {
                "product_type": "other_product",
                "schema_version": "1",
                "evidence_id": "bad",
                "timestamp": "2026-06-21T05:15:00+08:00",
                "allocations": [],
                "authority_split": {},
                "metadata": {},
            }
        ),
        encoding="utf-8",
    )
    wrong_schema = tmp_path / "wrong-schema.json"
    wrong_schema.write_text(
        json.dumps(
            {
                "product_type": "sandbox_allocation_receipt_evidence",
                "schema_version": "999",
                "evidence_id": "bad",
                "timestamp": "2026-06-21T05:15:00+08:00",
                "allocations": [],
                "authority_split": {},
                "metadata": {},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="product_type"):
        read_sandbox_allocation_receipt_evidence_summary(wrong_product)
    with pytest.raises(ValueError, match="schema_version"):
        read_sandbox_allocation_receipt_evidence_summary(wrong_schema)


def test_scheduler_authorization_snapshot_readback_uses_existing_recovery(tmp_path) -> None:
    task = _scheduled_task(
        "task-1",
        state="ready",
        edit_lease=EditScopeLease(
            lease_id="lease-1",
            task_id="task-1",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
    )
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(SchedulerState(tasks={"task-1": task}), snapshot_path)
    JsonlSchedulerEventLog(event_log_path).append(
        SchedulerEvent(
            event_id="scheduler-event-1",
            event_kind="lease_acquired",
            timestamp="2026-06-21T01:30:00+08:00",
            task_id="task-1",
            from_state="requested",
            to_state="acquired",
            lease_id="lease-1",
            edit_lease_lifecycle=EditLeaseLifecycleRecord(
                lease_id="lease-1",
                task_id="task-1",
                state="acquired",
                mode="write",
                allowed_artifacts=("src/app.py",),
                acquired_at="2026-06-21T01:30:00+08:00",
            ),
            sequence=1,
        )
    )

    readback = inspect_scheduler_authorization_snapshot(
        snapshot_path,
        scheduler_event_log_path=event_log_path,
        workspace_root=str(tmp_path),
    )
    payload = readback.to_json_dict()

    assert payload["snapshot_path"] == str(snapshot_path)
    assert payload["scheduler_event_log_path"] == str(event_log_path)
    assert payload["recovered_from_event_log"] is True
    assert payload["authority_split"]["scheduler_event_log_read"] is True
    assert payload["lifecycle_state_counts"] == {"acquired": 1}
    assert payload["tasks"][0]["sandbox_authorization"]["lease_authorization_state"] == "authorized"
    assert read_scheduler_state_snapshot(snapshot_path).edit_lease_lifecycle == {}


def test_scheduler_authorization_snapshot_readback_merges_allocation_evidence(
    tmp_path,
) -> None:
    task = _git_worktree_task()
    snapshot_path = tmp_path / "scheduler-state.json"
    state = _state_with_acquired_git_worktree_lease(task)
    write_scheduler_state_snapshot(state, snapshot_path)
    allocation = _git_worktree_allocation(
        task,
        cleanup_required=True,
        cleanup_state="required",
    )
    evidence_path = tmp_path / ".codex/scheduler/evidence/git-worktree-receipts.json"
    write_sandbox_allocation_receipt_evidence(
        build_sandbox_allocation_receipt_evidence(
            (allocation,),
            evidence_id="git-worktree-receipts",
            timestamp="2026-06-21T05:20:00+08:00",
        ),
        evidence_path,
    )

    readback = inspect_scheduler_authorization_snapshot(
        snapshot_path,
        sandbox_allocation_evidence_path=evidence_path,
    )
    payload = readback.to_json_dict()
    sandbox = payload["tasks"][0]["sandbox_authorization"]
    receipt = sandbox["git_worktree_receipt"]

    assert payload["metadata"]["sandbox_allocation_evidence_path"] == str(evidence_path)
    assert payload["metadata"]["sandbox_allocation_evidence_id"] == "git-worktree-receipts"
    assert payload["metadata"]["sandbox_allocation_evidence_allocation_count"] == 1
    assert payload["authority_split"]["real_sandbox_provider_executed"] is False
    assert sandbox["allocation_state"] == "allocated"
    assert sandbox["visible_mounts"] == ["README.md", "src/app.py"]
    assert sandbox["lease_authorization_state"] == "authorized"
    assert receipt["cleanup_state"] == "required"
    assert receipt["cleanup_required"] is True
    assert receipt["allocation"]["stdout"] == "allocated"


def test_sandbox_allocation_cleanup_runner_cleans_git_worktree_receipts(
    tmp_path,
) -> None:
    repo = _git_repo(tmp_path)
    allocation = _allocated_git_worktree_for_cleanup(tmp_path, repo)
    receipt = allocation.git_worktree_receipt
    assert receipt is not None
    input_path = tmp_path / "evidence" / "allocation-receipts.json"
    output_path = tmp_path / "evidence" / "allocation-receipts-cleaned.json"
    write_sandbox_allocation_receipt_evidence(
        build_sandbox_allocation_receipt_evidence(
            (allocation,),
            evidence_id="allocation-receipts",
            timestamp="2026-06-21T06:10:00+08:00",
            metadata={"surface": "unit-test"},
        ),
        input_path,
    )

    result = run_sandbox_allocation_cleanup_over_receipts(
        input_path,
        output_evidence_path=output_path,
        output_evidence_id="allocation-receipts-cleaned",
        timestamp="2026-06-21T06:15:00+08:00",
    )
    payload = result.to_json_dict()
    summary = read_sandbox_allocation_receipt_evidence_summary(output_path)
    cleaned = summary.allocations_by_task_id["task-1"]
    cleaned_receipt = cleaned.git_worktree_receipt

    assert payload["ok"] is True
    assert payload["selected_allocation_ids"] == ["git-worktree:task-1:worktree"]
    assert payload["cleaned_allocation_ids"] == ["git-worktree:task-1:worktree"]
    assert payload["failed_allocation_ids"] == []
    assert payload["authority_split"]["cleanup_executed"] is True
    assert result.evidence_write.evidence_path == output_path
    assert summary.evidence_id == "allocation-receipts-cleaned"
    assert summary.timestamp == "2026-06-21T06:15:00+08:00"
    assert summary.metadata["surface"] == "explicit-sandbox-allocation-cleanup-runner"
    assert summary.metadata["source_evidence_id"] == "allocation-receipts"
    assert summary.authority_split["cleanup_executed"] is True
    assert cleaned.cleanup_required is False
    assert cleaned_receipt is not None
    assert cleaned_receipt.cleanup_state == "completed"
    assert cleaned_receipt.cleanup.returncode == 0
    assert cleaned_receipt.branch_cleanup.returncode == 0
    assert not Path(receipt.worktree_path).exists()


def test_sandbox_allocation_cleanup_runner_noops_without_required_cleanup(
    tmp_path,
) -> None:
    task = _git_worktree_task()
    allocation = _git_worktree_allocation(
        task,
        cleanup_required=False,
        cleanup_state="completed",
        cleanup_returncode=0,
        branch_cleanup_returncode=0,
    )
    input_path = default_sandbox_allocation_receipt_evidence_path(
        tmp_path,
        "already-clean",
    )
    write_sandbox_allocation_receipt_evidence(
        build_sandbox_allocation_receipt_evidence(
            (allocation,),
            evidence_id="already-clean",
            timestamp="2026-06-21T06:20:00+08:00",
        ),
        input_path,
    )

    result = run_sandbox_allocation_cleanup_over_receipts(input_path)
    payload = result.to_json_dict()
    summary = read_sandbox_allocation_receipt_evidence_summary(result.output_evidence_path)
    restored = summary.allocations_by_task_id["task-1"]

    assert result.output_evidence_path == tmp_path / ".codex/scheduler/evidence/already-clean-cleanup.json"
    assert payload["ok"] is True
    assert payload["selected_allocation_ids"] == []
    assert payload["skipped_allocation_ids"] == ["git-worktree:task-1:worktree"]
    assert payload["authority_split"]["cleanup_executed"] is False
    assert summary.evidence_id == "already-clean:cleanup"
    assert summary.authority_split["cleanup_executed"] is False
    assert restored == allocation


def test_sandbox_allocation_cleanup_runner_default_output_path_for_relative_codex_path(
    tmp_path,
    monkeypatch,
) -> None:
    task = _git_worktree_task()
    allocation = _git_worktree_allocation(
        task,
        cleanup_required=False,
        cleanup_state="completed",
        cleanup_returncode=0,
        branch_cleanup_returncode=0,
    )
    monkeypatch.chdir(tmp_path)
    input_path = Path(".codex/scheduler/evidence/relative-receipts.json")
    write_sandbox_allocation_receipt_evidence(
        build_sandbox_allocation_receipt_evidence(
            (allocation,),
            evidence_id="relative-receipts",
            timestamp="2026-06-21T06:25:00+08:00",
        ),
        input_path,
    )

    result = run_sandbox_allocation_cleanup_over_receipts(input_path)

    assert result.output_evidence_path == Path(".codex/scheduler/evidence/relative-receipts-cleanup.json")
    assert result.output_evidence_path.exists()


def test_run_preflighted_task_uses_scheduler_run_path_and_runtime_registry(tmp_path) -> None:
    sandbox_registry = SandboxProviderRegistry()
    sandbox_registry.register(SharedProcessSandboxProvider())
    runtime_registry = AgentRuntimeAdapterRegistry()
    store = InMemoryArtifactVersionStore()
    runtime_registry.register(
        FakeAgentRuntimeAdapter(
            artifact_store=store,
            timestamp="2026-06-17T00:20:00+08:00",
        )
    )
    scheduler_log = JsonlSchedulerEventLog(tmp_path / "preflight-run-events.jsonl")
    task = _scheduled_task("task-1", state="ready", output_artifact_id="task-1:result")
    state = SchedulerState(tasks={"task-1": task})
    preflight = build_orchestration_preflight_bundle(
        task,
        sandbox_registry=sandbox_registry,
        workspace_root="E:/workspace/project",
    )

    result = run_preflighted_task(
        state,
        preflight,
        runtime_registry=runtime_registry,
        event_log=scheduler_log,
        timestamp="2026-06-17T00:20:00+08:00",
    )

    assert result.preflight is preflight
    assert result.runtime_result.run_handle.task_id == "task-1"
    assert result.state.tasks["task-1"].state == "complete"
    assert result.state.run_records[0].output_artifact_id == "task-1:result"
    assert [event.event_kind for event in scheduler_log.read_all()] == [
        "task_running",
        "task_completed",
    ]


def test_run_preflighted_task_rejects_stale_preflight_bundle() -> None:
    sandbox_registry = SandboxProviderRegistry()
    sandbox_registry.register(SharedProcessSandboxProvider())
    runtime_registry = AgentRuntimeAdapterRegistry()
    runtime_registry.register(FakeAgentRuntimeAdapter(artifact_store=InMemoryArtifactVersionStore()))
    task = _scheduled_task("task-1", state="ready")
    preflight = build_orchestration_preflight_bundle(task, sandbox_registry=sandbox_registry)
    changed = _scheduled_task("task-1", state="ready", output_artifact_id="changed:result")

    with pytest.raises(ValueError, match="does not match current scheduler state"):
        run_preflighted_task(
            SchedulerState(tasks={"task-1": changed}),
            preflight,
            runtime_registry=runtime_registry,
        )


def test_run_preflighted_task_surfaces_missing_runtime_adapter() -> None:
    sandbox_registry = SandboxProviderRegistry()
    sandbox_registry.register(SharedProcessSandboxProvider())
    task = _scheduled_task("task-1", state="ready")
    preflight = build_orchestration_preflight_bundle(task, sandbox_registry=sandbox_registry)

    with pytest.raises(KeyError, match="no runtime adapter registered for provider 'fake'"):
        run_preflighted_task(
            SchedulerState(tasks={"task-1": task}),
            preflight,
            runtime_registry=AgentRuntimeAdapterRegistry(),
        )


def test_scheduler_task_submission_artifact_round_trips_to_structured_request() -> None:
    submission = SchedulerTaskSubmission(
        task_id="task-submit",
        title="Submitted task",
        instruction="Implement the submitted task.",
        agent=AgentSpec(
            agent_id="agent:submit",
            runtime_provider="fake",
            display_name="Submit Agent",
            tools=("read", "write"),
            max_turns=8,
        ),
        context_scope=ContextScope(
            context_id="context:submit",
            lane_id="lane:submit",
            required_refs=(ExchangeReference(ref_kind="file", ref_id="README", path="README.md"),),
            visible_artifacts=("contract:api",),
        ),
        edit_lease=EditScopeLease(
            lease_id="lease-submit",
            task_id="task-submit",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
        sandbox_profile=SandboxProfile(
            profile_id="shared-submit",
            profile_kind="shared-process",
            network_policy="disabled",
            secret_policy="deny",
        ),
        input_artifact_refs=(ExchangeReference(ref_kind="exchange_artifact", ref_id="server-api", version="v1"),),
        acceptance=("tests pass", "artifact recorded"),
        output_artifact_id="task-submit:result",
        dependencies=(
            TaskDependency(
                dependency_id="dep-base-submit",
                source_task_id="task-base",
                target_task_id="task-submit",
                required_state="complete",
            ),
        ),
    )

    artifact = scheduler_task_submission_to_artifact(
        submission,
        artifact_id="submission:task-submit",
        producer="agent:guide",
        created_at="2026-06-17T00:55:00+08:00",
    )
    parsed = scheduler_task_submission_from_artifact(artifact)

    assert artifact.kind == "request"
    assert artifact.intent == "propose"
    assert artifact.scope.task_id == "task-submit"
    assert part_types(artifact) == ("structured", "log")
    assert artifact.parts[1].log is not None
    assert artifact.parts[1].log.timestamp == "2026-06-17T00:55:00+08:00"
    assert artifact.parts[1].log.actor == "agent:guide"
    assert artifact.parts[1].log.action == "scheduler_task_submitted"
    assert artifact.parts[1].log.related_artifact_ids == ("submission:task-submit",)
    assert parsed.task_id == "task-submit"
    assert parsed.agent.agent_id == "agent:submit"
    assert parsed.agent.tools == ("read", "write")
    assert parsed.context_scope.required_refs[0].path == "README.md"
    assert parsed.edit_lease is not None
    assert parsed.edit_lease.allowed_artifacts == ("src/app.py",)
    assert parsed.input_artifact_refs[0].ref_id == "server-api"
    assert parsed.acceptance == ("tests pass", "artifact recorded")
    assert parsed.dependencies[0].source_task_id == "task-base"


def test_submit_scheduler_task_adds_task_and_dependencies_to_state() -> None:
    submission = SchedulerTaskSubmission(
        task_id="task-child",
        title="Child task",
        instruction="Run after base task.",
        agent=AgentSpec(agent_id="agent:child", runtime_provider="fake"),
        context_scope=ContextScope(context_id="context:child", lane_id="lane:child"),
        output_artifact_id="task-child:result",
        dependencies=(
            TaskDependency(
                dependency_id="dep-base-child",
                source_task_id="task-base",
                target_task_id="task-child",
                required_state="complete",
            ),
        ),
    )
    artifact = scheduler_task_submission_to_artifact(submission)
    base = _scheduled_task("task-base")

    result = submit_scheduler_task(SchedulerState(tasks={"task-base": base}), artifact)
    marked = mark_ready_tasks(result.state)

    assert result.source_artifact_id == "scheduler-task-submission:task-child"
    assert result.task.task_id == "task-child"
    assert result.state.tasks["task-child"].state == "proposed"
    assert result.state.dependencies[0].dependency_id == "dep-base-child"
    assert marked.tasks["task-child"].state == "waiting"
    assert marked.tasks["task-child"].blocked_reason == "waiting for task-base to reach complete"


def test_submit_scheduler_task_rejects_existing_task_without_replace() -> None:
    submission = SchedulerTaskSubmission(
        task_id="task-a",
        title="Replacement",
        instruction="Replace task-a.",
        agent=AgentSpec(agent_id="agent:a", runtime_provider="fake"),
        context_scope=ContextScope(context_id="context:a"),
    )
    artifact = scheduler_task_submission_to_artifact(submission)
    state = SchedulerState(tasks={"task-a": _scheduled_task("task-a")})

    with pytest.raises(ValueError, match="references existing task 'task-a'"):
        submit_scheduler_task(state, artifact)

    replaced = submit_scheduler_task(state, artifact, replace_existing=True)
    assert replaced.state.tasks["task-a"].title == "Replacement"


def test_scheduler_task_submission_reports_missing_or_bad_payload() -> None:
    missing = ExchangeArtifact(
        artifact_id="submission:missing",
        kind="request",
        intent="propose",
        producer="agent:guide",
        parts=(ExchangePayloadPart(part_type="structured", data={"product_type": "other"}),),
    )
    bad_provider = ExchangeArtifact(
        artifact_id="submission:bad-provider",
        kind="request",
        intent="propose",
        producer="agent:guide",
        parts=(
            ExchangePayloadPart(
                part_type="structured",
                data={
                    "product_type": "scheduler_task_submission",
                    "task_id": "task-bad",
                    "title": "Bad provider",
                    "instruction": "Should fail.",
                    "agent": {"agent_id": "agent:bad", "runtime_provider": "unknown"},
                    "context_scope": {"context_id": "context:bad"},
                },
            ),
        ),
    )

    with pytest.raises(ValueError, match="product_type='scheduler_task_submission'"):
        scheduler_task_submission_from_artifact(missing)
    with pytest.raises(ValueError, match="unsupported agent.runtime_provider 'unknown'"):
        scheduler_task_submission_from_artifact(bad_provider)


def test_scheduler_task_batch_submission_adds_multiple_tasks_and_dependencies() -> None:
    batch = SchedulerTaskBatchSubmission(
        batch_id="batch-maze",
        title="Maze split",
        summary="Split maze work into server and client tasks.",
        tasks=(
            SchedulerTaskSubmission(
                task_id="task-server",
                title="Server task",
                instruction="Build the maze server.",
                agent=AgentSpec(agent_id="agent:server", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:server", lane_id="lane:server"),
                output_artifact_id="task-server:result",
            ),
            SchedulerTaskSubmission(
                task_id="task-client",
                title="Client task",
                instruction="Build the maze client.",
                agent=AgentSpec(agent_id="agent:client", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:client", lane_id="lane:client"),
                output_artifact_id="task-client:result",
                dependencies=(
                    TaskDependency(
                        dependency_id="dep-server-client",
                        source_task_id="task-server",
                        target_task_id="task-client",
                        required_state="complete",
                    ),
                ),
            ),
        ),
    )
    artifact = scheduler_task_batch_submission_to_artifact(
        batch,
        artifact_id="submission:maze-batch",
        producer="agent:guide",
    )

    parsed = scheduler_task_batch_submission_from_artifact(artifact)
    result = submit_scheduler_task_batch(SchedulerState(), artifact)
    marked = mark_ready_tasks(result.state)

    assert artifact.kind == "request"
    assert artifact.intent == "propose"
    assert artifact.scope.lane_id == "lane:server"
    assert part_types(artifact) == ("structured", "log")
    assert artifact.parts[1].log is not None
    assert artifact.parts[1].log.timestamp
    assert artifact.parts[1].log.action == "scheduler_task_batch_submitted"
    assert artifact.parts[1].log.related_artifact_ids == ("submission:maze-batch",)
    assert parsed.batch_id == "batch-maze"
    assert tuple(task.task_id for task in parsed.tasks) == ("task-server", "task-client")
    assert tuple(task.task_id for task in result.tasks) == ("task-server", "task-client")
    assert result.dependencies_added[0].dependency_id == "dep-server-client"
    assert marked.tasks["task-server"].state == "ready"
    assert marked.tasks["task-client"].state == "waiting"


def test_scheduler_task_batch_submission_graph_can_drain_after_submission(tmp_path) -> None:
    store = InMemoryArtifactVersionStore()
    runtime = FakeAgentRuntimeAdapter(
        artifact_store=store,
        timestamp="2026-06-17T01:05:00+08:00",
    )
    batch = SchedulerTaskBatchSubmission(
        batch_id="batch-drain",
        tasks=(
            SchedulerTaskSubmission(
                task_id="task-a",
                title="Task A",
                instruction="Complete A.",
                agent=AgentSpec(agent_id="agent:a", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:a", lane_id="lane:a"),
                output_artifact_id="task-a:result",
            ),
            SchedulerTaskSubmission(
                task_id="task-b",
                title="Task B",
                instruction="Complete B after A.",
                agent=AgentSpec(agent_id="agent:b", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:b", lane_id="lane:b"),
                output_artifact_id="task-b:result",
                dependencies=(
                    TaskDependency(
                        dependency_id="dep-a-b",
                        source_task_id="task-a",
                        target_task_id="task-b",
                        required_state="complete",
                    ),
                ),
            ),
        ),
    )
    submitted = submit_scheduler_task_batch(
        SchedulerState(),
        scheduler_task_batch_submission_to_artifact(batch),
    )

    drained = drain_ready_tasks(
        submitted.state,
        runtime=runtime,
        event_log=JsonlSchedulerEventLog(tmp_path / "batch-drain-events.jsonl"),
        timestamp="2026-06-17T01:05:00+08:00",
    )

    assert drained.stop_reason == "no_ready_tasks"
    assert tuple(run.run_handle.task_id for run in drained.run_results) == ("task-a", "task-b")
    assert drained.state.tasks["task-a"].state == "complete"
    assert drained.state.tasks["task-b"].state == "complete"


def test_scheduler_task_batch_submission_rejects_duplicate_or_empty_tasks() -> None:
    duplicate = SchedulerTaskBatchSubmission(
        batch_id="batch-duplicate",
        tasks=(
            SchedulerTaskSubmission(
                task_id="task-a",
                title="Task A",
                instruction="First task.",
                agent=AgentSpec(agent_id="agent:a", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:a"),
            ),
            SchedulerTaskSubmission(
                task_id="task-a",
                title="Task A duplicate",
                instruction="Duplicate task.",
                agent=AgentSpec(agent_id="agent:a2", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:a2"),
            ),
        ),
    )
    empty = ExchangeArtifact(
        artifact_id="submission:empty-batch",
        kind="request",
        intent="propose",
        producer="agent:guide",
        parts=(
            ExchangePayloadPart(
                part_type="structured",
                data={
                    "product_type": "scheduler_task_batch_submission",
                    "batch_id": "batch-empty",
                    "tasks": [],
                },
            ),
        ),
    )

    with pytest.raises(ValueError, match="duplicate task_id 'task-a'"):
        scheduler_task_batch_submission_from_artifact(
            scheduler_task_batch_submission_to_artifact(duplicate)
        )
    with pytest.raises(ValueError, match="requires at least one task"):
        scheduler_task_batch_submission_from_artifact(empty)


def test_submit_scheduler_task_batch_with_persistence_recovers_and_drains(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    drain_log_path = tmp_path / "scheduler-drain-events.jsonl"
    batch = SchedulerTaskBatchSubmission(
        batch_id="batch-persist",
        tasks=(
            SchedulerTaskSubmission(
                task_id="task-a",
                title="Task A",
                instruction="Complete A.",
                agent=AgentSpec(agent_id="agent:a", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:a", lane_id="lane:a"),
                output_artifact_id="task-a:result",
            ),
            SchedulerTaskSubmission(
                task_id="task-b",
                title="Task B",
                instruction="Complete B after A.",
                agent=AgentSpec(agent_id="agent:b", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:b", lane_id="lane:b"),
                output_artifact_id="task-b:result",
                dependencies=(
                    TaskDependency(
                        dependency_id="dep-a-b",
                        source_task_id="task-a",
                        target_task_id="task-b",
                        required_state="complete",
                    ),
                ),
            ),
        ),
    )
    artifact = scheduler_task_batch_submission_to_artifact(
        batch,
        artifact_id="submission:persist-batch",
    )

    persisted = submit_scheduler_task_batch_with_persistence(
        SchedulerState(),
        artifact,
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        timestamp="2026-06-17T01:10:00+08:00",
    )
    restored = read_scheduler_state_snapshot(snapshot_path)
    recovery = recover_scheduler_state(snapshot_path, event_log_path)
    drain = drain_ready_tasks(
        recovery.recovered_state,
        runtime=FakeAgentRuntimeAdapter(
            artifact_store=InMemoryArtifactVersionStore(),
            timestamp="2026-06-17T01:11:00+08:00",
        ),
        event_log=JsonlSchedulerEventLog(drain_log_path),
        timestamp="2026-06-17T01:11:00+08:00",
    )
    submission_events = JsonlSchedulerEventLog(event_log_path).read_all()

    assert persisted.snapshot_path == snapshot_path
    assert persisted.event_log_path == event_log_path
    assert persisted.submission_event_ids == ("scheduler-event-1", "scheduler-event-2")
    assert tuple(task.task_id for task in persisted.submission.tasks) == ("task-a", "task-b")
    assert tuple(sorted(restored.tasks)) == ("task-a", "task-b")
    assert restored.dependencies[0].dependency_id == "dep-a-b"
    assert [event.event_kind for event in submission_events] == ["task_submitted", "task_submitted"]
    assert submission_events[1].related_dependency_ids == ("dep-a-b",)
    assert submission_events[0].related_artifact_ids == ("submission:persist-batch",)
    assert recovery.event_count == 2
    assert recovery.recovered_state.tasks["task-a"].state == "proposed"
    assert drain.stop_reason == "no_ready_tasks"
    assert tuple(run.run_handle.task_id for run in drain.run_results) == ("task-a", "task-b")
    assert drain.state.tasks["task-b"].state == "complete"


def test_seed_scheduler_operator_dogfood_fixture_creates_candidate_only(tmp_path) -> None:
    store_path = tmp_path / ".codex" / "orchestration" / "exchange-artifacts.json"
    snapshot_path = tmp_path / ".codex" / "scheduler" / "scheduler-state.json"
    ledger_path = tmp_path / ".codex" / "orchestration" / "exchange-artifact-admissions.json"

    result = seed_scheduler_operator_dogfood_fixture(
        tmp_path,
        artifact_store_path=store_path,
    )
    bundle = inspect_exchange_artifact_store(store_path)
    payload = result.to_json_dict()

    assert isinstance(result, SchedulerOperatorDogfoodFixtureResult)
    assert payload["artifact_id"] == "fixture:scheduler-operator-dogfood"
    assert payload["version"] == "v1"
    assert payload["product_type"] == "scheduler_task_batch_submission"
    assert payload["task_ids"] == ["dogfood:prepare", "dogfood:verify"]
    assert payload["dependency_ids"] == ["dep:dogfood-prepare->dogfood-verify"]
    assert payload["replaced_existing"] is False
    assert payload["authority_split"]["exchange_store_mutated"] is True
    assert payload["authority_split"]["scheduler_state_mutated"] is False
    assert payload["authority_split"]["provider_executed"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert store_path.exists()
    assert not snapshot_path.exists()
    assert not ledger_path.exists()
    assert bundle.admission_candidate_count == 1
    assert bundle.summaries[0].admission_candidates[0].task_ids == (
        "dogfood:prepare",
        "dogfood:verify",
    )


def test_seed_scheduler_operator_multilane_dogfood_fixture_creates_candidate_only(tmp_path) -> None:
    store_path = tmp_path / ".codex" / "orchestration" / "exchange-artifacts.json"
    snapshot_path = tmp_path / ".codex" / "scheduler" / "scheduler-state.json"
    ledger_path = tmp_path / ".codex" / "orchestration" / "exchange-artifact-admissions.json"

    result = seed_scheduler_operator_multilane_dogfood_fixture(
        tmp_path,
        artifact_store_path=store_path,
    )
    bundle = inspect_exchange_artifact_store(store_path)
    payload = result.to_json_dict()

    assert isinstance(result, SchedulerOperatorDogfoodFixtureResult)
    assert payload["artifact_id"] == "fixture:scheduler-operator-multilane-dogfood"
    assert payload["version"] == "v1"
    assert payload["product_type"] == "scheduler_task_batch_submission"
    assert payload["batch_id"] == "batch:scheduler-operator-multilane-dogfood"
    assert payload["task_ids"] == [
        "dogfood:api-design",
        "dogfood:data-schema",
        "dogfood:client-integration",
        "dogfood:integration-verify",
    ]
    assert payload["lane_ids"] == ["lane:api", "lane:data", "lane:client", "lane:qa"]
    assert payload["dependency_ids"] == [
        "dep:dogfood-api->dogfood-client",
        "dep:dogfood-data->dogfood-client",
        "dep:dogfood-client->dogfood-integration",
        "dep:dogfood-data->dogfood-integration",
    ]
    assert payload["authority_split"]["exchange_store_mutated"] is True
    assert payload["authority_split"]["scheduler_state_mutated"] is False
    assert payload["authority_split"]["provider_executed"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert store_path.exists()
    assert not snapshot_path.exists()
    assert not ledger_path.exists()
    assert bundle.admission_candidate_count == 1
    candidate = bundle.summaries[0].admission_candidates[0]
    assert candidate.artifact_id == "fixture:scheduler-operator-multilane-dogfood"
    assert candidate.batch_id == "batch:scheduler-operator-multilane-dogfood"
    assert candidate.task_count == 4
    assert candidate.task_ids == (
        "dogfood:api-design",
        "dogfood:data-schema",
        "dogfood:client-integration",
        "dogfood:integration-verify",
    )


def test_seed_scheduler_operator_binding_consumer_fixture_creates_compact_ref_pair(
    tmp_path,
) -> None:
    store_path = tmp_path / ".codex" / "orchestration" / "exchange-artifacts.json"
    snapshot_path = tmp_path / ".codex" / "scheduler" / "scheduler-state.json"
    ledger_path = tmp_path / ".codex" / "orchestration" / "exchange-artifact-admissions.json"
    evidence_path = (
        tmp_path
        / ".codex"
        / "scheduler"
        / "evidence"
        / "fixture-supervisor-storage-binding-dogfood.json"
    )

    result = seed_scheduler_operator_binding_consumer_dogfood_fixture(
        tmp_path,
        artifact_store_path=store_path,
        created_at="2026-06-22T01:00:00+08:00",
    )
    payload = result.to_json_dict()
    records = JsonArtifactVersionStore(store_path).list_records()
    bundle = inspect_exchange_artifact_store(store_path)
    binding_record = JsonArtifactVersionStore(store_path).get(
        "fixture:supervisor-storage-binding-dogfood",
        "v1",
    )
    submission_record = JsonArtifactVersionStore(store_path).get(
        "fixture:scheduler-operator-binding-consumer-dogfood",
        "v1",
    )
    batch = scheduler_task_batch_submission_from_artifact(submission_record.artifact)

    assert payload["artifact_id"] == "fixture:scheduler-operator-binding-consumer-dogfood"
    assert payload["batch_id"] == "batch:scheduler-operator-binding-consumer-dogfood"
    assert payload["task_ids"] == ["dogfood:binding-consumer"]
    assert payload["lane_ids"] == ["lane:binding-consumer"]
    assert payload["dependency_ids"] == []
    assert payload["binding_artifact_ids"] == ["fixture:supervisor-storage-binding-dogfood"]
    assert payload["binding_artifact_versions"] == ["v1"]
    assert payload["recommended_operator_workflow_options"] == [
        "--inspect-binding-refs",
        "--admit",
    ]
    assert payload["authority_split"]["exchange_store_mutated"] is True
    assert payload["authority_split"]["scheduler_state_mutated"] is False
    assert payload["authority_split"]["provider_executed"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert len(records) == 2
    assert not snapshot_path.exists()
    assert not ledger_path.exists()
    assert not evidence_path.exists()
    assert bundle.admission_candidate_count == 1

    structured_parts = [
        part.data
        for part in binding_record.artifact.parts
        if part.part_type == "structured"
    ]
    assert structured_parts[0]["product_type"] == "supervisor_storage_binding_artifact"
    assert structured_parts[0]["binding_id"] == (
        "supervisor-storage-binding:context-session-dogfood-binding-consumer"
    )
    assert structured_parts[0]["authority_split"]["evidence_written"] is False
    assert structured_parts[0]["metadata"]["raw_evidence_json_written"] is False

    assert len(batch.tasks) == 1
    ref = batch.tasks[0].input_artifact_refs[0]
    assert ref.ref_kind == SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND
    assert ref.ref_id == "fixture:supervisor-storage-binding-dogfood"
    assert ref.version == "v1"


def test_seed_scheduler_operator_binding_consumer_fixture_rejects_duplicate_keys(
    tmp_path,
) -> None:
    store_path = tmp_path / ".codex" / "orchestration" / "exchange-artifacts.json"

    with pytest.raises(ValueError, match="requires distinct artifact version keys"):
        seed_scheduler_operator_binding_consumer_dogfood_fixture(
            tmp_path,
            artifact_store_path=store_path,
            artifact_id="fixture:duplicate",
            binding_artifact_id="fixture:duplicate",
        )

    assert not store_path.exists()


def test_seed_scheduler_operator_dogfood_fixture_requires_explicit_replace(tmp_path) -> None:
    store_path = tmp_path / ".codex" / "orchestration" / "exchange-artifacts.json"
    seed_scheduler_operator_dogfood_fixture(tmp_path, artifact_store_path=store_path)

    with pytest.raises(ValueError, match="exchange artifact version already exists"):
        seed_scheduler_operator_dogfood_fixture(tmp_path, artifact_store_path=store_path)

    replaced = seed_scheduler_operator_dogfood_fixture(
        tmp_path,
        artifact_store_path=store_path,
        replace_existing=True,
        created_at="2026-06-19T12:00:00+08:00",
    )
    records = JsonArtifactVersionStore(store_path).list_records()

    assert replaced.replaced_existing is True
    assert len(records) == 1
    assert records[0].artifact.created_at == "2026-06-19T12:00:00+08:00"


def test_scheduler_operator_workflow_read_only_inspects_without_mutation(tmp_path) -> None:
    store_path = tmp_path / ".codex" / "orchestration" / "exchange-artifacts.json"
    snapshot_path = tmp_path / ".codex" / "scheduler" / "scheduler-state.json"
    ledger_path = tmp_path / ".codex" / "orchestration" / "exchange-artifact-admissions.json"
    projection_path = tmp_path / ".codex" / "progress-graph" / "scheduler-work-trajectory.json"
    seed_scheduler_operator_dogfood_fixture(tmp_path, artifact_store_path=store_path)

    result = run_scheduler_operator_workflow(
        SchedulerOperatorWorkflowRequest(project_root=tmp_path)
    )
    payload = result.to_json_dict()

    assert payload["ok"] is True
    assert [step["name"] for step in payload["steps"]] == [
        "inspectCandidates",
        "admit",
        "runLoop",
        "refreshProjection",
        "readHostEvidencePresentation",
    ]
    assert payload["steps"][0]["status"] == "completed"
    assert payload["steps"][1]["status"] == "skipped"
    assert payload["steps"][2]["status"] == "skipped"
    assert payload["steps"][3]["status"] == "skipped"
    assert payload["candidate_bundle"]["admission_candidate_count"] == 1
    assert payload["host_evidence_presentation"]["status"] == "empty"
    assert payload["authority_split"]["scheduler_state_mutated"] is False
    assert payload["authority_split"]["provider_executed"] is False
    assert payload["authority_split"]["scheduler_projection_refreshed"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert not snapshot_path.exists()
    assert not ledger_path.exists()
    assert not projection_path.exists()
    assert not (tmp_path / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_operator_workflow_inspects_binding_refs_without_mutation(tmp_path) -> None:
    store_path = tmp_path / ".codex" / "orchestration" / "exchange-artifacts.json"
    snapshot_path = tmp_path / ".codex" / "scheduler" / "scheduler-state.json"
    ledger_path = tmp_path / ".codex" / "orchestration" / "exchange-artifact-admissions.json"
    store = JsonArtifactVersionStore(store_path)
    store.put(
        ExchangeArtifact(
            artifact_id="binding:workflow",
            kind="retention",
            intent="inform",
            producer="agent:projection",
            version="v1",
            parts=(
                ExchangePayloadPart(
                    part_type="structured",
                    data={
                        "product_type": SUPERVISOR_STORAGE_BINDING_ARTIFACT_PRODUCT_TYPE,
                        "binding_id": "binding:workflow",
                    },
                ),
                ExchangePayloadPart(
                    part_type="storage_manifest",
                    data={
                        "product_type": SUPERVISOR_STORAGE_BINDING_ARTIFACT_PRODUCT_TYPE,
                        "binding_id": "binding:workflow",
                    },
                ),
            ),
        )
    )
    store.put(
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task-workflow-binding",
                title="Workflow binding task",
                instruction="Use the inspected binding artifact.",
                agent=AgentSpec(agent_id="agent:workflow-binding", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:workflow-binding"),
                input_artifact_refs=(
                    ExchangeReference(
                        ref_kind=SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
                        ref_id="binding:workflow",
                        version="v1",
                    ),
                ),
            ),
            artifact_id="submission:workflow-binding",
            version="v1",
        )
    )

    result = run_scheduler_operator_workflow(
        SchedulerOperatorWorkflowRequest(
            project_root=tmp_path,
            artifact_id="submission:workflow-binding",
            version="v1",
            inspect_binding_refs=True,
        )
    )
    payload = result.to_json_dict()

    assert payload["ok"] is True
    assert [step["name"] for step in payload["steps"]] == [
        "inspectCandidates",
        "inspectBindingRefs",
        "admit",
        "runLoop",
        "refreshProjection",
        "readHostEvidencePresentation",
    ]
    assert payload["steps"][1]["status"] == "completed"
    assert payload["steps"][1]["mutated"] is False
    assert payload["binding_reference_inspection"]["ok"] is True
    assert payload["binding_reference_inspection"]["binding_ref_count"] == 1
    assert payload["binding_reference_inspection"]["tasks"][0]["task_id"] == (
        "task-workflow-binding"
    )
    assert payload["request"]["inspect_binding_refs"] is True
    assert payload["authority_split"]["scheduler_state_mutated"] is False
    assert payload["authority_split"]["provider_executed"] is False
    assert not snapshot_path.exists()
    assert not ledger_path.exists()
    assert not (tmp_path / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_operator_workflow_full_dogfood_flow(tmp_path) -> None:
    seed_scheduler_operator_dogfood_fixture(tmp_path)

    result = run_scheduler_operator_workflow(
        SchedulerOperatorWorkflowRequest(
            project_root=tmp_path,
            artifact_id="fixture:scheduler-operator-dogfood",
            version="v1",
            admit=True,
            run_loop=True,
            refresh_projection=True,
            evidence_id="workflow-helper-loop",
            timestamp="2026-06-19T11:30:00+08:00",
            guide_context="workflow-helper-test",
        )
    )
    payload = result.to_json_dict()

    assert payload["ok"] is True
    assert [step["status"] for step in payload["steps"]] == [
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
    ]
    assert payload["admission_result"]["submitted_task_ids"] == [
        "dogfood:prepare",
        "dogfood:verify",
    ]
    assert payload["loop_result"]["tick_count"] == 2
    assert payload["loop_result"]["total_run_count"] == 2
    assert payload["loop_result"]["stop_reason"] == "no_ready_tasks"
    assert payload["loop_result"]["evidence_written"] is True
    assert payload["projection_result"]["event_count"] == 2
    assert payload["projection_result"]["guide_context"] == "workflow-helper-test"
    assert payload["host_evidence_presentation"]["card_count"] == 1
    assert payload["host_evidence_presentation"]["cards"][0]["id"] == "workflow-helper-loop"
    assert payload["host_evidence_presentation"]["cards"][0]["metadata"][
        "scheduler_projection_refreshed"
    ] == "true"
    assert payload["authority_split"]["admission_ledger_mutated"] is True
    assert payload["authority_split"]["scheduler_state_mutated"] is True
    assert payload["authority_split"]["provider_executed"] is True
    assert payload["authority_split"]["scheduler_projection_refreshed"] is True
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert (tmp_path / ".codex" / "scheduler" / "scheduler-state.json").exists()
    assert (tmp_path / ".codex" / "scheduler" / "evidence" / "workflow-helper-loop.json").exists()
    assert (tmp_path / ".codex" / "progress-graph" / "scheduler-work-trajectory.json").exists()
    assert not (tmp_path / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_operator_workflow_inspect_binding_refs_then_admit(tmp_path) -> None:
    store_path = tmp_path / ".codex" / "orchestration" / "exchange-artifacts.json"
    store = JsonArtifactVersionStore(store_path)
    store.put(
        ExchangeArtifact(
            artifact_id="binding:workflow-admit",
            kind="retention",
            intent="inform",
            producer="agent:projection",
            version="v1",
            parts=(
                ExchangePayloadPart(
                    part_type="structured",
                    data={
                        "product_type": SUPERVISOR_STORAGE_BINDING_ARTIFACT_PRODUCT_TYPE,
                        "binding_id": "binding:workflow-admit",
                    },
                ),
                ExchangePayloadPart(
                    part_type="storage_manifest",
                    data={
                        "product_type": SUPERVISOR_STORAGE_BINDING_ARTIFACT_PRODUCT_TYPE,
                        "binding_id": "binding:workflow-admit",
                    },
                ),
            ),
        )
    )
    store.put(
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task-workflow-binding-admit",
                title="Workflow binding admit task",
                instruction="Admit only after binding refs are inspected.",
                agent=AgentSpec(agent_id="agent:workflow-binding", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:workflow-binding"),
                input_artifact_refs=(
                    ExchangeReference(
                        ref_kind=SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
                        ref_id="binding:workflow-admit",
                        version="v1",
                    ),
                ),
            ),
            artifact_id="submission:workflow-binding-admit",
            version="v1",
        )
    )

    result = run_scheduler_operator_workflow(
        SchedulerOperatorWorkflowRequest(
            project_root=tmp_path,
            artifact_id="submission:workflow-binding-admit",
            version="v1",
            inspect_binding_refs=True,
            admit=True,
        )
    )
    payload = result.to_json_dict()

    assert payload["ok"] is True
    assert payload["steps"][1]["name"] == "inspectBindingRefs"
    assert payload["steps"][1]["status"] == "completed"
    assert payload["steps"][2]["name"] == "admit"
    assert payload["steps"][2]["status"] == "completed"
    assert payload["binding_reference_inspection"]["ok"] is True
    assert payload["admission_result"]["submitted_task_ids"] == [
        "task-workflow-binding-admit",
    ]
    assert payload["authority_split"]["admission_ledger_mutated"] is True
    assert payload["authority_split"]["scheduler_state_mutated"] is True


def test_scheduler_operator_workflow_can_mark_consumed_on_success(tmp_path) -> None:
    store_path = tmp_path / ".codex" / "orchestration" / "exchange-artifacts.json"
    seed_scheduler_operator_dogfood_fixture(tmp_path, artifact_store_path=store_path)

    result = run_scheduler_operator_workflow(
        SchedulerOperatorWorkflowRequest(
            project_root=tmp_path,
            artifact_id="fixture:scheduler-operator-dogfood",
            version="v1",
            admit=True,
            mark_consumed_on_success=True,
            actor="agent:operator",
            timestamp="2026-06-22T11:00:00+08:00",
        )
    )
    payload = result.to_json_dict()
    bundle = inspect_exchange_artifact_store(store_path).to_json_dict()
    summary = next(
        item
        for item in bundle["summaries"]
        if item["artifact_id"] == "fixture:scheduler-operator-dogfood"
    )

    assert payload["ok"] is True
    assert payload["request"]["mark_consumed_on_success"] is True
    assert payload["admission_result"]["consumption_state"]["consumed"] is True
    assert payload["admission_result"]["consumption_state"]["actor"] == "agent:operator"
    assert payload["authority_split"]["exchange_store_mutated"] is True
    assert payload["authority_split"]["admission_ledger_mutated"] is True
    assert payload["authority_split"]["scheduler_state_mutated"] is True
    assert summary["lifecycle_state"] == "consumed"


def test_scheduler_operator_workflow_full_multilane_dogfood_flow(tmp_path) -> None:
    seed_scheduler_operator_multilane_dogfood_fixture(tmp_path)

    result = run_scheduler_operator_workflow(
        SchedulerOperatorWorkflowRequest(
            project_root=tmp_path,
            artifact_id="fixture:scheduler-operator-multilane-dogfood",
            version="v1",
            admit=True,
            run_loop=True,
            refresh_projection=True,
            max_ticks=4,
            max_runs_per_tick=2,
            evidence_id="workflow-helper-multilane-loop",
            timestamp="2026-06-19T12:30:00+08:00",
            guide_context="workflow-helper-multilane-test",
        )
    )
    payload = result.to_json_dict()

    assert payload["ok"] is True
    assert [step["status"] for step in payload["steps"]] == [
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
    ]
    assert payload["admission_result"]["submitted_task_ids"] == [
        "dogfood:api-design",
        "dogfood:data-schema",
        "dogfood:client-integration",
        "dogfood:integration-verify",
    ]
    assert payload["admission_result"]["dependency_count"] == 4
    assert payload["loop_result"]["tick_count"] == 2
    assert payload["loop_result"]["total_run_count"] == 4
    assert payload["loop_result"]["stop_reason"] == "no_ready_tasks"
    assert payload["loop_result"]["final_queue_summary"]["completed_task_ids"] == [
        "dogfood:api-design",
        "dogfood:client-integration",
        "dogfood:data-schema",
        "dogfood:integration-verify",
    ]
    assert payload["projection_result"]["event_count"] == 6
    assert payload["projection_result"]["lane_count"] == 4
    assert payload["projection_result"]["relation_count"] >= 8
    assert payload["projection_result"]["guide_context"] == "workflow-helper-multilane-test"
    assert payload["host_evidence_presentation"]["card_count"] == 1
    assert payload["host_evidence_presentation"]["cards"][0]["id"] == "workflow-helper-multilane-loop"
    assert payload["host_evidence_presentation"]["cards"][0]["run_count"] == 4
    assert payload["authority_split"]["admission_ledger_mutated"] is True
    assert payload["authority_split"]["scheduler_state_mutated"] is True
    assert payload["authority_split"]["provider_executed"] is True
    assert payload["authority_split"]["scheduler_projection_refreshed"] is True
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert (tmp_path / ".codex" / "scheduler" / "scheduler-state.json").exists()
    assert (
        tmp_path / ".codex" / "scheduler" / "evidence" / "workflow-helper-multilane-loop.json"
    ).exists()
    assert (tmp_path / ".codex" / "progress-graph" / "scheduler-work-trajectory.json").exists()
    assert not (tmp_path / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_operator_workflow_duplicate_admission_stops_dependent_steps(tmp_path) -> None:
    seed_scheduler_operator_dogfood_fixture(tmp_path)
    first = run_scheduler_operator_workflow(
        SchedulerOperatorWorkflowRequest(
            project_root=tmp_path,
            artifact_id="fixture:scheduler-operator-dogfood",
            version="v1",
            admit=True,
            run_loop=False,
            refresh_projection=False,
        )
    )
    duplicate = run_scheduler_operator_workflow(
        SchedulerOperatorWorkflowRequest(
            project_root=tmp_path,
            artifact_id="fixture:scheduler-operator-dogfood",
            version="v1",
            admit=True,
            run_loop=True,
            refresh_projection=True,
            evidence_id="duplicate-should-not-run",
        )
    )
    payload = duplicate.to_json_dict()

    assert first.ok is True
    assert payload["ok"] is False
    assert payload["steps"][1]["name"] == "admit"
    assert payload["steps"][1]["status"] == "failed"
    assert payload["steps"][1]["result"]["status"] == "rejected_duplicate"
    assert payload["steps"][2]["name"] == "runLoop"
    assert payload["steps"][2]["status"] == "skipped"
    assert payload["steps"][3]["name"] == "refreshProjection"
    assert payload["steps"][3]["status"] == "skipped"
    assert payload["authority_split"]["provider_executed"] is False
    assert payload["authority_split"]["scheduler_projection_refreshed"] is False
    assert not (tmp_path / ".codex" / "scheduler" / "evidence" / "duplicate-should-not-run.json").exists()


def test_scheduler_operator_workflow_binding_ref_failure_stops_dependents(tmp_path) -> None:
    store_path = tmp_path / ".codex" / "orchestration" / "exchange-artifacts.json"
    JsonArtifactVersionStore(store_path).put(
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task-workflow-missing-binding",
                title="Workflow missing binding task",
                instruction="This ref is missing and must stop admission.",
                agent=AgentSpec(agent_id="agent:workflow-binding", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:workflow-binding"),
                input_artifact_refs=(
                    ExchangeReference(
                        ref_kind=SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
                        ref_id="binding:missing",
                        version="v1",
                    ),
                ),
            ),
            artifact_id="submission:workflow-missing-binding",
            version="v1",
        )
    )

    result = run_scheduler_operator_workflow(
        SchedulerOperatorWorkflowRequest(
            project_root=tmp_path,
            artifact_id="submission:workflow-missing-binding",
            version="v1",
            inspect_binding_refs=True,
            admit=True,
            run_loop=True,
            refresh_projection=True,
            evidence_id="binding-failure-should-not-run",
        )
    )
    payload = result.to_json_dict()

    assert payload["ok"] is False
    assert payload["steps"][1]["name"] == "inspectBindingRefs"
    assert payload["steps"][1]["status"] == "failed"
    assert payload["steps"][2]["name"] == "admit"
    assert payload["steps"][2]["status"] == "skipped"
    assert payload["steps"][2]["error"] == "binding reference inspection failed"
    assert payload["steps"][3]["name"] == "runLoop"
    assert payload["steps"][3]["status"] == "skipped"
    assert payload["steps"][4]["name"] == "refreshProjection"
    assert payload["steps"][4]["status"] == "skipped"
    assert payload["binding_reference_inspection"]["ok"] is False
    assert "binding:missing" in payload["binding_reference_inspection"]["errors"][0]
    assert payload["authority_split"]["admission_ledger_mutated"] is False
    assert payload["authority_split"]["scheduler_state_mutated"] is False
    assert payload["authority_split"]["provider_executed"] is False
    assert not (tmp_path / ".codex" / "scheduler" / "scheduler-state.json").exists()
    assert not (
        tmp_path / ".codex" / "scheduler" / "evidence" / "binding-failure-should-not-run.json"
    ).exists()


def test_scheduler_operator_dogfood_closure_runs_binding_consumer_full_flow(
    tmp_path,
) -> None:
    result = run_scheduler_operator_dogfood_closure(
        SchedulerOperatorDogfoodClosureRequest(
            project_root=tmp_path,
            fixture="binding-consumer",
            evidence_id="operator-closure-test",
            timestamp="2026-06-22T15:00:00+08:00",
            guide_context="operator-closure-test",
        )
    )
    payload = result.to_json_dict()

    assert payload["ok"] is True
    assert [step["name"] for step in payload["steps"]] == [
        "seedFixture",
        "operatorWorkflow",
        "readClosureSummary",
    ]
    assert payload["fixture_result"]["artifact_id"] == (
        "fixture:scheduler-operator-binding-consumer-dogfood"
    )
    assert payload["workflow_result"]["binding_reference_inspection"]["ok"] is True
    assert payload["workflow_result"]["admission_result"]["submitted_task_ids"] == [
        "dogfood:binding-consumer",
    ]
    assert payload["workflow_result"]["admission_result"]["binding_reference_summary"][
        "ok"
    ] is True
    assert payload["workflow_result"]["admission_result"]["consumption_state"][
        "consumed"
    ] is True
    assert payload["closure_summary"]["fixture"] == "binding-consumer"
    assert payload["closure_summary"]["lifecycle_state"] == "consumed"
    assert payload["closure_summary"]["admission_status"] == "admitted"
    assert payload["closure_summary"]["binding_summary_ok"] is True
    assert payload["closure_summary"]["consumed"] is True
    assert payload["closure_summary"]["loop_evidence_id"] == "operator-closure-test"
    assert payload["closure_summary"]["loop_stop_reason"] == "no_ready_tasks"
    assert payload["closure_summary"]["scheduler_projection_event_count"] == 1
    assert payload["closure_summary"]["host_evidence_status"] == "ok"
    assert payload["closure_summary"]["host_evidence_card_count"] == 1
    assert payload["authority_split"]["fixture_seeded"] is True
    assert payload["authority_split"]["exchange_store_mutated"] is True
    assert payload["authority_split"]["admission_ledger_mutated"] is True
    assert payload["authority_split"]["scheduler_state_mutated"] is True
    assert payload["authority_split"]["provider_executed"] is True
    assert payload["authority_split"]["evidence_written"] is True
    assert payload["authority_split"]["scheduler_projection_refreshed"] is True
    assert payload["authority_split"]["host_evidence_read"] is True
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert (
        tmp_path / ".codex" / "scheduler" / "evidence" / "operator-closure-test.json"
    ).exists()
    assert (
        tmp_path / ".codex" / "progress-graph" / "scheduler-work-trajectory.json"
    ).exists()
    assert not (tmp_path / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_operator_dogfood_closure_rejects_live_provider(
    tmp_path,
) -> None:
    result = run_scheduler_operator_dogfood_closure(
        SchedulerOperatorDogfoodClosureRequest(
            project_root=tmp_path,
            runtime_provider="qoder",
        )
    )
    payload = result.to_json_dict()

    assert payload["ok"] is False
    assert payload["steps"][0]["name"] == "preflightRuntime"
    assert payload["steps"][0]["status"] == "failed"
    assert "fake" in payload["steps"][0]["error"]
    assert payload["authority_split"]["provider_executed"] is False
    assert not (tmp_path / ".codex").exists()


def test_evidence_publish_to_consumer_closure_runs_published_artifact_flow(
    tmp_path,
) -> None:
    result = run_evidence_publish_to_consumer_closure(
        EvidencePublishToConsumerClosureRequest(
            project_root=tmp_path,
            binding_evidence_id="publish-closure-binding",
            binding_artifact_id="artifact:published-binding",
            binding_artifact_version="v7",
            consumer_artifact_id="artifact:published-binding-consumer",
            consumer_version="v2",
            loop_evidence_id="publish-closure-loop",
            timestamp="2026-06-22T18:00:00+08:00",
            guide_context="publish-closure-test",
        )
    )
    payload = result.to_json_dict()

    assert payload["ok"] is True
    assert [step["name"] for step in payload["steps"]] == [
        "writeBindingEvidence",
        "publishBindingArtifact",
        "seedConsumerSubmission",
        "operatorWorkflow",
        "readClosureSummary",
    ]
    assert payload["evidence_write"]["evidence_id"] == "publish-closure-binding"
    assert "binding" not in payload["evidence_write"]
    assert payload["publish_result"]["artifact_id"] == "artifact:published-binding"
    assert payload["publish_result"]["version"] == "v7"
    assert payload["publish_result"]["authority_split"][
        "raw_binding_payload_embedded_in_exchange"
    ] is False
    assert payload["consumer_seed_result"]["binding_artifact_ids"] == [
        "artifact:published-binding",
    ]
    assert payload["consumer_seed_result"]["binding_artifact_versions"] == ["v7"]
    assert payload["workflow_result"]["binding_reference_inspection"]["ok"] is True
    assert payload["workflow_result"]["admission_result"]["submitted_task_ids"] == [
        "dogfood:evidence-publish-binding-consumer",
    ]
    assert payload["workflow_result"]["admission_result"]["binding_reference_summary"][
        "ok"
    ] is True
    assert payload["workflow_result"]["admission_result"]["consumption_state"][
        "consumed"
    ] is True
    assert payload["closure_summary"]["consumer_references_published_artifact"] is True
    assert payload["closure_summary"]["binding_artifact_id"] == "artifact:published-binding"
    assert payload["closure_summary"]["binding_artifact_version"] == "v7"
    assert payload["closure_summary"]["consumer_artifact_id"] == (
        "artifact:published-binding-consumer"
    )
    assert payload["closure_summary"]["lifecycle_state"] == "consumed"
    assert payload["closure_summary"]["binding_summary_ok"] is True
    assert payload["closure_summary"]["consumed"] is True
    assert payload["closure_summary"]["loop_evidence_id"] == "publish-closure-loop"
    assert payload["closure_summary"]["loop_stop_reason"] == "no_ready_tasks"
    assert payload["closure_summary"]["scheduler_projection_event_count"] == 1
    assert payload["closure_summary"]["host_evidence_card_count"] == 2
    assert payload["authority_split"]["binding_evidence_written"] is True
    assert payload["authority_split"]["binding_artifact_published"] is True
    assert payload["authority_split"]["consumer_submission_seeded"] is True
    assert payload["authority_split"]["exchange_store_mutated"] is True
    assert payload["authority_split"]["admission_ledger_mutated"] is True
    assert payload["authority_split"]["scheduler_state_mutated"] is True
    assert payload["authority_split"]["provider_executed"] is True
    assert payload["authority_split"]["loop_evidence_written"] is True
    assert payload["authority_split"]["scheduler_projection_refreshed"] is True
    assert payload["authority_split"]["host_evidence_read"] is True
    assert payload["authority_split"]["agent_home_directory_created"] is False
    assert payload["authority_split"]["scratch_directories_created"] is False
    assert payload["authority_split"]["scratch_manifest_written"] is False
    assert payload["authority_split"]["cleanup_executed"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert (
        tmp_path / ".codex" / "scheduler" / "evidence" / "publish-closure-binding.json"
    ).exists()
    assert (
        tmp_path / ".codex" / "scheduler" / "evidence" / "publish-closure-loop.json"
    ).exists()
    assert (
        tmp_path / ".codex" / "progress-graph" / "scheduler-work-trajectory.json"
    ).exists()
    assert not (tmp_path / ".codex" / "scratch").exists()
    assert not (tmp_path / ".codex" / "agents").exists()
    assert not (tmp_path / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()
    store_payload = json.loads(
        (tmp_path / ".codex" / "orchestration" / "exchange-artifacts.json").read_text(
            encoding="utf-8"
        )
    )
    records = {
        (record["artifact_id"], record["version"]): record["artifact"]
        for record in store_payload["records"]
    }
    binding_artifact = records[("artifact:published-binding", "v7")]
    consumer_artifact = records[("artifact:published-binding-consumer", "v2")]
    assert '"binding"' not in json.dumps(binding_artifact, sort_keys=True)
    consumer_json = json.dumps(consumer_artifact, sort_keys=True)
    assert "artifact:published-binding" in consumer_json
    assert "fixture:supervisor-storage-binding-dogfood" not in consumer_json


def test_evidence_publish_to_consumer_closure_rejects_live_provider(tmp_path) -> None:
    result = run_evidence_publish_to_consumer_closure(
        EvidencePublishToConsumerClosureRequest(
            project_root=tmp_path,
            runtime_provider="qoder",
        )
    )
    payload = result.to_json_dict()

    assert payload["ok"] is False
    assert payload["steps"][0]["name"] == "preflightRuntime"
    assert payload["steps"][0]["status"] == "failed"
    assert "fake" in payload["steps"][0]["error"]
    assert payload["authority_split"]["provider_executed"] is False
    assert not (tmp_path / ".codex").exists()


def test_scheduler_supervisor_dogfood_workflow_full_simple_flow(tmp_path) -> None:
    result = run_scheduler_supervisor_dogfood_workflow(
        SchedulerSupervisorDogfoodWorkflowRequest(
            project_root=tmp_path,
            fixture="simple",
            timestamp="2026-06-21T10:00:00+00:00",
            supervisor_id="supervisor:test",
            session_id="session:test",
            run_id="run:test",
            host_id="host:test",
            requested_by="agent:test",
            status_readback_at="2026-06-21T10:00:01+00:00",
        )
    )
    payload = result.to_json_dict()

    assert payload["ok"] is True
    assert [step["name"] for step in payload["steps"]] == [
        "seedFixture",
        "admit",
        "startLifecycle",
        "supervisorStep",
        "readFinalStatus",
    ]
    assert [step["status"] for step in payload["steps"]] == [
        "completed",
        "completed",
        "completed",
        "completed",
        "completed",
    ]
    assert payload["fixture_result"]["task_ids"] == ["dogfood:prepare", "dogfood:verify"]
    assert payload["admission_result"]["submitted_task_ids"] == [
        "dogfood:prepare",
        "dogfood:verify",
    ]
    assert payload["lifecycle_start_result"]["control"]["state"] == "running"
    assert payload["supervisor_result"]["supervisor_id"] == "supervisor:test"
    assert payload["supervisor_result"]["session_id"] == "session:test"
    assert payload["supervisor_result"]["total_run_count"] == 2
    assert payload["supervisor_result"]["status_before"]["queue_summary"]["task_state_counts"] == {
        "proposed": 2
    }
    assert payload["supervisor_result"]["status_after"]["queue_summary"]["task_state_counts"] == {
        "complete": 2
    }
    assert payload["final_readback"]["completed_task_ids"] == [
        "dogfood:prepare",
        "dogfood:verify",
    ]
    assert payload["authority_split"]["exchange_store_mutated"] is True
    assert payload["authority_split"]["admission_ledger_mutated"] is True
    assert payload["authority_split"]["lifecycle_control_mutated"] is True
    assert payload["authority_split"]["scheduler_state_mutated"] is True
    assert payload["authority_split"]["provider_executed"] is True
    assert payload["authority_split"]["scheduler_projection_refreshed"] is False
    assert payload["authority_split"]["cleanup_executed"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert (tmp_path / ".codex" / "scheduler" / "scheduler-daemon-control.json").exists()
    assert not (tmp_path / ".codex" / "progress-graph" / "scheduler-work-trajectory.json").exists()
    assert not (tmp_path / ".codex" / "progress-graph" / "local-work-trajectory.json").exists()


def test_scheduler_supervisor_dogfood_workflow_multilane_flow(tmp_path) -> None:
    result = run_scheduler_supervisor_dogfood_workflow(
        SchedulerSupervisorDogfoodWorkflowRequest(
            project_root=tmp_path,
            fixture="multilane",
            max_ticks=4,
            max_runs_per_tick=2,
            timestamp="2026-06-21T10:10:00+00:00",
        )
    )
    payload = result.to_json_dict()

    assert payload["ok"] is True
    assert payload["fixture_result"]["lane_ids"] == [
        "lane:api",
        "lane:data",
        "lane:client",
        "lane:qa",
    ]
    assert payload["admission_result"]["dependency_count"] == 4
    assert payload["supervisor_result"]["total_run_count"] == 4
    assert payload["final_readback"]["queue_summary"]["task_state_counts"] == {"complete": 4}
    assert payload["authority_split"]["scheduler_projection_refreshed"] is False


def test_supervisor_dogfood_storage_binding_maps_run_identity_and_scheduler_facts(tmp_path) -> None:
    result = run_scheduler_supervisor_dogfood_workflow(
        SchedulerSupervisorDogfoodWorkflowRequest(
            project_root=tmp_path,
            fixture="simple",
            timestamp="2026-06-21T11:00:00+00:00",
            supervisor_id="supervisor:binding",
            session_id="session:binding",
            run_id="run:binding",
            host_id="host:binding",
            requested_by="agent:guide",
        )
    )

    binding = build_supervisor_dogfood_storage_binding(
        result,
        agent_id="agent:supervisor-binding",
        context_session_id="context-session:binding",
        scratch_root=".codex/scratch/supervisor-binding",
        home_root=".codex/agents",
        expires_at="2026-06-22T11:00:00+00:00",
    )
    payload = binding.to_json_dict()

    assert payload["binding_id"] == "supervisor-storage-binding:context-session-binding"
    assert payload["supervisor_id"] == "supervisor:binding"
    assert payload["session_id"] == "session:binding"
    assert payload["run_id"] == "run:binding"
    assert payload["host_id"] == "host:binding"
    assert payload["requested_by"] == "agent:guide"
    assert payload["agent_id"] == "agent:supervisor-binding"
    assert payload["context_session_id"] == "context-session:binding"
    assert payload["scheduler_task_ids"] == ["dogfood:prepare", "dogfood:verify"]
    assert payload["scheduler_context_ids"] == [
        "context:dogfood-prepare",
        "context:dogfood-verify",
    ]
    assert payload["scheduler_lane_ids"] == ["lane:dogfood"]
    assert payload["runtime_session_ids"] == ["fake-session-1"]
    assert payload["home_registration"]["registration_id"] == (
        "home-reg:context-session-binding"
    )
    assert payload["home_registration"]["audit_state"] == "requested"
    assert payload["home_registration"]["requested_path_hint"] == (
        ".codex/agents/agent-supervisor-binding"
    )
    assert [scratch["task_id"] for scratch in payload["scratch_spaces"]] == [
        "dogfood:prepare",
        "dogfood:verify",
    ]
    assert payload["scratch_spaces"][0]["agent_id"] == "agent:dogfood-prepare"
    assert payload["scratch_spaces"][0]["path"] == (
        ".codex/scratch/supervisor-binding/dogfood:prepare"
    )
    assert payload["scratch_spaces"][0]["run_id"] == "fake-run-1"
    assert payload["scratch_spaces"][1]["run_id"] == "fake-run-1"
    assert payload["source_snapshot_path"] == str(result.snapshot_path)
    assert payload["authority_split"]["agent_home_registration_persisted"] is False
    assert payload["authority_split"]["agent_home_directory_created"] is False
    assert payload["authority_split"]["scratch_directories_created"] is False
    assert payload["authority_split"]["scratch_manifest_written"] is False
    assert payload["authority_split"]["cleanup_executed"] is False
    assert payload["authority_split"]["scheduler_projection_refreshed"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False


def test_supervisor_agent_storage_binding_requires_supervisor_session_and_run() -> None:
    state = SchedulerState()

    with pytest.raises(ValueError, match="requires session_id"):
        build_supervisor_agent_storage_binding(
            SupervisorAgentStorageBindingRequest(
                supervisor_id="supervisor:missing-session",
                session_id="",
                run_id="run:1",
            ),
            state,
        )

    with pytest.raises(ValueError, match="requires run_id"):
        build_supervisor_agent_storage_binding(
            SupervisorAgentStorageBindingRequest(
                supervisor_id="supervisor:missing-run",
                session_id="session:1",
                run_id="",
            ),
            state,
        )


def test_supervisor_storage_binding_evidence_round_trips_summary(tmp_path) -> None:
    summary, evidence_path, workflow = _supervisor_storage_binding_evidence_summary(
        tmp_path,
    )
    payload = summary.to_json_dict()

    assert isinstance(summary, SupervisorStorageBindingEvidenceSummary)
    assert payload["product_type"] == "supervisor_storage_binding_evidence"
    assert payload["schema_version"] == "1"
    assert payload["evidence_id"] == "supervisor-binding:evidence"
    assert payload["evidence_path"] == str(evidence_path)
    assert payload["binding_id"] == "supervisor-storage-binding:context-session-evidence"
    assert payload["supervisor_id"] == "supervisor:evidence"
    assert payload["session_id"] == "session:evidence"
    assert payload["run_id"] == "run:evidence"
    assert payload["host_id"] == "host:evidence"
    assert payload["requested_by"] == "agent:guide"
    assert payload["agent_id"] == "agent:supervisor-evidence"
    assert payload["context_session_id"] == "context-session:evidence"
    assert payload["scheduler_task_ids"] == ["dogfood:prepare", "dogfood:verify"]
    assert payload["scheduler_context_ids"] == [
        "context:dogfood-prepare",
        "context:dogfood-verify",
    ]
    assert payload["scheduler_lane_ids"] == ["lane:dogfood"]
    assert payload["runtime_session_ids"] == ["fake-session-1"]
    assert payload["home_registration_id"] == "home-reg:context-session-evidence"
    assert payload["home_registration_audit_state"] == "requested"
    assert payload["scratch_count"] == 2
    assert payload["scratch_ids"] == ["scratch:dogfood:prepare", "scratch:dogfood:verify"]
    assert payload["source_snapshot_path"] == str(workflow.snapshot_path)
    assert payload["metadata"] == {"workflow_surface": "supervisor-dogfood-workflow"}
    assert payload["authority_split"]["evidence_written"] is True
    assert payload["authority_split"]["scheduler_state_mutated"] is False
    assert payload["authority_split"]["agent_home_directory_created"] is False
    assert payload["authority_split"]["scratch_directories_created"] is False
    assert payload["authority_split"]["scratch_manifest_written"] is False
    assert payload["authority_split"]["cleanup_executed"] is False
    assert payload["authority_split"]["scheduler_projection_refreshed"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False

    raw_payload = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert "binding" in raw_payload
    assert raw_payload["binding"]["home_registration"]["audit_state"] == "requested"


def test_supervisor_storage_binding_evidence_summary_maps_to_exchange_artifact(tmp_path) -> None:
    summary, evidence_path, _workflow = _supervisor_storage_binding_evidence_summary(
        tmp_path,
    )

    artifact = supervisor_storage_binding_evidence_summary_to_artifact(summary)
    restored = exchange_artifact_from_json_dict(exchange_artifact_to_json_dict(artifact))

    assert artifact.artifact_id == (
        "supervisor-storage-binding-evidence:supervisor-binding:evidence"
    )
    assert artifact.kind == "retention"
    assert artifact.intent == "inform"
    assert artifact.producer == "supervisor:evidence"
    assert artifact.audience == ("scheduler", "workspace-registration")
    assert artifact.lifecycle_state == "accepted"
    assert artifact.created_at == "2026-06-21T11:20:01+00:00"
    assert artifact.version == "v1"
    assert artifact.scope.agent_id == "agent:supervisor-evidence"
    assert artifact.scope.lane_id == "lane:dogfood"
    assert artifact.scope.runtime_session_id == "fake-session-1"
    assert artifact.scope.task_id == ""
    assert artifact.scope.context_id == ""
    assert artifact.visibility_policy.audience == (
        "scheduler",
        "workspace-registration",
        "agent:supervisor-evidence",
    )
    assert validate_exchange_artifact(artifact) == ()
    assert part_types(artifact) == (
        "structured",
        "storage_manifest",
        "evidence",
        "ref",
        "log",
    )
    assert restored == artifact
    store = JsonArtifactVersionStore(tmp_path / "binding-exchange-artifacts.json")
    stored = store.put(artifact)
    assert stored.artifact == artifact
    assert store.get(artifact.artifact_id, "v1").artifact == artifact

    structured = artifact.parts[0].data
    assert structured["product_type"] == SUPERVISOR_STORAGE_BINDING_ARTIFACT_PRODUCT_TYPE
    assert structured["schema_version"] == SUPERVISOR_STORAGE_BINDING_ARTIFACT_SCHEMA_VERSION
    assert structured["evidence_product_type"] == "supervisor_storage_binding_evidence"
    assert structured["evidence_schema_version"] == "1"
    assert structured["evidence_id"] == "supervisor-binding:evidence"
    assert structured["evidence_path"] == str(evidence_path)
    assert structured["binding_id"] == "supervisor-storage-binding:context-session-evidence"
    assert structured["scheduler_task_ids"] == ["dogfood:prepare", "dogfood:verify"]
    assert structured["scheduler_context_ids"] == [
        "context:dogfood-prepare",
        "context:dogfood-verify",
    ]
    assert structured["scheduler_lane_ids"] == ["lane:dogfood"]
    assert structured["runtime_session_ids"] == ["fake-session-1"]
    assert structured["home_registration_id"] == "home-reg:context-session-evidence"
    assert structured["scratch_ids"] == [
        "scratch:dogfood:prepare",
        "scratch:dogfood:verify",
    ]
    assert structured["metadata"] == {"workflow_surface": "supervisor-dogfood-workflow"}
    assert structured["authority_split"]["evidence_written"] is True
    assert structured["authority_split"]["scheduler_state_mutated"] is False
    assert structured["authority_split"]["agent_home_directory_created"] is False
    assert structured["authority_split"]["scratch_directories_created"] is False
    assert structured["authority_split"]["scratch_manifest_written"] is False
    assert structured["authority_split"]["cleanup_executed"] is False
    assert structured["authority_split"]["scheduler_projection_refreshed"] is False
    assert structured["authority_split"]["local_work_trajectory_mutated"] is False

    storage_manifest = artifact.parts[1].data
    assert storage_manifest["product_type"] == SUPERVISOR_STORAGE_BINDING_ARTIFACT_PRODUCT_TYPE
    assert storage_manifest["binding_id"] == structured["binding_id"]
    assert storage_manifest["scratch_count"] == 2
    evidence = artifact.parts[2].data
    assert evidence == {
        "product_type": "supervisor_storage_binding_evidence",
        "schema_version": "1",
        "evidence_id": "supervisor-binding:evidence",
        "evidence_path": str(evidence_path),
        "binding_id": "supervisor-storage-binding:context-session-evidence",
        "timestamp": "2026-06-21T11:20:01+00:00",
    }
    assert artifact.parts[3].ref is not None
    assert artifact.parts[3].ref.ref_kind == "file"
    assert artifact.parts[3].ref.ref_id == "supervisor-binding:evidence"
    assert artifact.parts[3].ref.path == str(evidence_path)
    assert artifact.parts[4].log is not None
    assert artifact.parts[4].log.action == (
        "supervisor_storage_binding_evidence_projected"
    )

    serialized = json.dumps(exchange_artifact_to_json_dict(artifact), sort_keys=True)
    assert '"binding"' not in serialized


def test_supervisor_storage_binding_evidence_artifact_accepts_explicit_identity(
    tmp_path,
) -> None:
    summary, _evidence_path, _workflow = _supervisor_storage_binding_evidence_summary(
        tmp_path,
    )

    artifact = supervisor_storage_binding_evidence_summary_to_artifact(
        summary,
        artifact_id="artifact:binding-evidence",
        version="v2",
        producer="agent:projection",
        audience=("agent:consumer",),
        created_at="2026-06-21T12:00:00+00:00",
    )

    assert artifact.artifact_id == "artifact:binding-evidence"
    assert artifact.version == "v2"
    assert artifact.producer == "agent:projection"
    assert artifact.audience == ("agent:consumer",)
    assert artifact.created_at == "2026-06-21T12:00:00+00:00"
    assert artifact.visibility_policy.audience == (
        "agent:consumer",
        "agent:supervisor-evidence",
    )
    assert validate_exchange_artifact(artifact) == ()


def test_publish_supervisor_storage_binding_artifact_from_evidence(
    tmp_path,
) -> None:
    summary, evidence_path, _workflow = _supervisor_storage_binding_evidence_summary(
        tmp_path,
    )
    store_path = tmp_path / "exchange-artifacts.json"

    result = publish_supervisor_storage_binding_artifact_from_evidence(
        evidence_path=evidence_path,
        artifact_store_path=store_path,
        artifact_id="artifact:binding-published",
        version="v3",
        producer="operator:publish",
        audience=("scheduler", "workspace-registration", "agent:consumer"),
        created_at="2026-06-22T08:00:00+00:00",
    )

    assert result.artifact_store_path == store_path
    assert result.evidence_path == evidence_path
    assert result.evidence_id == summary.evidence_id
    assert result.artifact_id == "artifact:binding-published"
    assert result.version == "v3"
    assert result.producer == "operator:publish"
    assert result.audience == (
        "scheduler",
        "workspace-registration",
        "agent:consumer",
    )
    assert result.created_at == "2026-06-22T08:00:00+00:00"
    assert result.replaced_existing is False
    payload = result.to_json_dict()
    assert payload["authority_split"]["exchange_store_mutated"] is True
    assert payload["authority_split"]["scheduler_state_mutated"] is False
    assert payload["authority_split"]["agent_home_directory_created"] is False
    assert payload["authority_split"]["scratch_directories_created"] is False
    assert payload["authority_split"]["scratch_manifest_written"] is False
    assert payload["authority_split"]["raw_binding_payload_embedded_in_exchange"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False

    stored = JsonArtifactVersionStore(store_path).get(
        "artifact:binding-published",
        "v3",
    )
    structured = stored.artifact.parts[0].data
    assert structured["product_type"] == SUPERVISOR_STORAGE_BINDING_ARTIFACT_PRODUCT_TYPE
    assert structured["evidence_id"] == summary.evidence_id
    serialized = json.dumps(
        exchange_artifact_to_json_dict(stored.artifact),
        sort_keys=True,
    )
    assert '"binding"' not in serialized

    with pytest.raises(ValueError, match="already exists"):
        publish_supervisor_storage_binding_artifact_from_evidence(
            evidence_path=evidence_path,
            artifact_store_path=store_path,
            artifact_id="artifact:binding-published",
            version="v3",
        )

    replaced = publish_supervisor_storage_binding_artifact_from_evidence(
        evidence_path=evidence_path,
        artifact_store_path=store_path,
        artifact_id="artifact:binding-published",
        version="v3",
        producer="operator:replace",
        replace_existing=True,
    )

    assert replaced.replaced_existing is True
    assert JsonArtifactVersionStore(store_path).get(
        "artifact:binding-published",
        "v3",
    ).artifact.producer == "operator:replace"


def test_supervisor_storage_binding_artifact_refs_validate_exact_version(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    summary, _evidence_path, _workflow = _supervisor_storage_binding_evidence_summary(
        tmp_path,
    )
    binding_artifact = supervisor_storage_binding_evidence_summary_to_artifact(
        summary,
        artifact_id="binding:context-session-evidence",
        version="v7",
    )
    JsonArtifactVersionStore(store_path).put(binding_artifact)
    submission = SchedulerTaskSubmission(
        task_id="task-consume-binding",
        title="Consume binding",
        instruction="Use the exact supervisor binding artifact.",
        agent=AgentSpec(agent_id="agent:consumer", runtime_provider="fake"),
        context_scope=ContextScope(context_id="context:consumer"),
        input_artifact_refs=(
            ExchangeReference(
                ref_kind=SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
                ref_id="binding:context-session-evidence",
                version="v7",
            ),
        ),
    )

    validation = validate_supervisor_storage_binding_artifact_refs(
        submission,
        store_path,
    )

    assert validation.ok is True
    assert validation.checked_count == 1
    assert validation.checked_refs[0].ref_id == "binding:context-session-evidence"
    validation.raise_for_errors()


def test_supervisor_storage_binding_reference_inspection_reports_single_submission(
    tmp_path,
) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    summary, _evidence_path, _workflow = _supervisor_storage_binding_evidence_summary(
        tmp_path,
    )
    binding_artifact = supervisor_storage_binding_evidence_summary_to_artifact(
        summary,
        artifact_id="binding:context-session-evidence",
        version="v7",
    )
    submission_artifact = scheduler_task_submission_to_artifact(
        SchedulerTaskSubmission(
            task_id="task-consume-binding",
            title="Consume binding",
            instruction="Use the exact supervisor binding artifact.",
            agent=AgentSpec(agent_id="agent:consumer", runtime_provider="fake"),
            context_scope=ContextScope(context_id="context:consumer"),
            input_artifact_refs=(
                ExchangeReference(
                    ref_kind=SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
                    ref_id="binding:context-session-evidence",
                    version="v7",
                    label="context session binding",
                ),
            ),
        ),
        artifact_id="submission:consume-binding",
        version="v1",
    )
    store = JsonArtifactVersionStore(store_path)
    store.put(binding_artifact)
    store.put(submission_artifact)

    inspection = inspect_supervisor_storage_binding_artifact_refs_for_submission(
        artifact_store_path=store_path,
        artifact_id="submission:consume-binding",
        version="v1",
    )
    payload = inspection.to_json_dict()

    assert inspection.ok is True
    assert payload["product_type"] == "supervisor_storage_binding_reference_inspection"
    assert payload["submission_product_type"] == "scheduler_task_submission"
    assert payload["task_count"] == 1
    assert payload["binding_ref_count"] == 1
    assert payload["checked_ref_count"] == 1
    assert payload["error_count"] == 0
    assert payload["tasks"][0]["task_id"] == "task-consume-binding"
    assert payload["tasks"][0]["binding_refs"][0]["ref_id"] == (
        "binding:context-session-evidence"
    )
    assert payload["authority_split"]["scheduler_state_mutated"] is False
    assert payload["authority_split"]["exchange_store_mutated"] is False
    assert payload["authority_split"]["admission_ledger_mutated"] is False
    assert payload["authority_split"]["raw_evidence_json_read"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False


def test_supervisor_storage_binding_reference_inspection_reports_batch_errors(
    tmp_path,
) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    summary, _evidence_path, _workflow = _supervisor_storage_binding_evidence_summary(
        tmp_path,
    )
    binding_artifact = supervisor_storage_binding_evidence_summary_to_artifact(
        summary,
        artifact_id="binding:valid",
        version="v1",
    )
    batch_artifact = scheduler_task_batch_submission_to_artifact(
        SchedulerTaskBatchSubmission(
            batch_id="batch-binding-inspect",
            tasks=(
                SchedulerTaskSubmission(
                    task_id="task-valid-binding",
                    title="Valid binding",
                    instruction="Use a valid binding ref.",
                    agent=AgentSpec(agent_id="agent:valid", runtime_provider="fake"),
                    context_scope=ContextScope(context_id="context:valid"),
                    input_artifact_refs=(
                        ExchangeReference(
                            ref_kind=SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
                            ref_id="binding:valid",
                            version="v1",
                        ),
                    ),
                ),
                SchedulerTaskSubmission(
                    task_id="task-missing-binding",
                    title="Missing binding",
                    instruction="Use a missing binding ref.",
                    agent=AgentSpec(agent_id="agent:missing", runtime_provider="fake"),
                    context_scope=ContextScope(context_id="context:missing"),
                    input_artifact_refs=(
                        ExchangeReference(
                            ref_kind=SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
                            ref_id="binding:missing",
                            version="v1",
                        ),
                    ),
                ),
            ),
        ),
        artifact_id="submission:batch-binding-inspect",
        version="v2",
    )
    store = JsonArtifactVersionStore(store_path)
    store.put(binding_artifact)
    store.put(batch_artifact)

    inspection = inspect_supervisor_storage_binding_artifact_refs_for_submission(
        artifact_store_path=store_path,
        artifact_id="submission:batch-binding-inspect",
        version="v2",
    )
    payload = inspection.to_json_dict()

    assert inspection.ok is False
    assert payload["submission_product_type"] == "scheduler_task_batch_submission"
    assert payload["task_count"] == 2
    assert payload["binding_ref_count"] == 2
    assert payload["checked_ref_count"] == 1
    assert payload["error_count"] == 1
    assert payload["tasks"][0]["ok"] is True
    assert payload["tasks"][1]["ok"] is False
    assert "binding:missing" in payload["tasks"][1]["errors"][0]


def test_supervisor_storage_binding_reference_inspection_reports_source_errors(
    tmp_path,
) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    JsonArtifactVersionStore(store_path).put(_accepted_contract_artifact(version="v1"))

    missing = inspect_supervisor_storage_binding_artifact_refs_for_submission(
        artifact_store_path=store_path,
        artifact_id="submission:missing",
        version="v1",
    )
    wrong_product = inspect_supervisor_storage_binding_artifact_refs_for_submission(
        artifact_store_path=store_path,
        artifact_id="server-api",
        version="v1",
    )

    assert missing.ok is False
    assert "not found" in missing.errors[0]
    assert missing.task_count == 0
    assert wrong_product.ok is False
    assert "is not a scheduler submission artifact" in wrong_product.errors[0]
    payload = wrong_product.to_json_dict()
    assert payload["authority_split"]["scheduler_state_mutated"] is False
    assert payload["authority_split"]["provider_executed"] is False


def test_supervisor_storage_binding_artifact_refs_report_invalid_refs(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    store = JsonArtifactVersionStore(store_path)
    store.put(_accepted_contract_artifact(version="v1"))
    store.put(
        ExchangeArtifact(
            artifact_id="binding:ambiguous",
            kind="retention",
            intent="inform",
            producer="agent:projection",
            version="v1",
            parts=(
                ExchangePayloadPart(
                    part_type="structured",
                    data={
                        "product_type": SUPERVISOR_STORAGE_BINDING_ARTIFACT_PRODUCT_TYPE,
                        "binding_id": "binding:one",
                    },
                ),
                ExchangePayloadPart(
                    part_type="structured",
                    data={
                        "product_type": SUPERVISOR_STORAGE_BINDING_ARTIFACT_PRODUCT_TYPE,
                        "binding_id": "binding:two",
                    },
                ),
                ExchangePayloadPart(
                    part_type="storage_manifest",
                    data={
                        "product_type": SUPERVISOR_STORAGE_BINDING_ARTIFACT_PRODUCT_TYPE,
                        "binding_id": "binding:ambiguous",
                    },
                ),
            ),
        )
    )
    missing_version = SchedulerTaskSubmission(
        task_id="task-missing-version",
        title="Missing version",
        instruction="Should fail before store lookup.",
        agent=AgentSpec(agent_id="agent:consumer", runtime_provider="fake"),
        context_scope=ContextScope(context_id="context:consumer"),
        input_artifact_refs=(
            ExchangeReference(
                ref_kind=SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
                ref_id="binding:missing-version",
            ),
        ),
    )
    missing_artifact = SchedulerTaskSubmission(
        task_id="task-missing-artifact",
        title="Missing artifact",
        instruction="Should fail closed.",
        agent=AgentSpec(agent_id="agent:consumer", runtime_provider="fake"),
        context_scope=ContextScope(context_id="context:consumer"),
        input_artifact_refs=(
            ExchangeReference(
                ref_kind=SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
                ref_id="binding:not-found",
                version="v1",
            ),
        ),
    )
    wrong_product = SchedulerTaskSubmission(
        task_id="task-wrong-product",
        title="Wrong product",
        instruction="Should reject non-binding artifact.",
        agent=AgentSpec(agent_id="agent:consumer", runtime_provider="fake"),
        context_scope=ContextScope(context_id="context:consumer"),
        input_artifact_refs=(
            ExchangeReference(
                ref_kind=SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
                ref_id="server-api",
                version="v1",
            ),
        ),
    )
    ambiguous_product = SchedulerTaskSubmission(
        task_id="task-ambiguous-product",
        title="Ambiguous product",
        instruction="Should reject ambiguous binding artifact payloads.",
        agent=AgentSpec(agent_id="agent:consumer", runtime_provider="fake"),
        context_scope=ContextScope(context_id="context:consumer"),
        input_artifact_refs=(
            ExchangeReference(
                ref_kind=SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
                ref_id="binding:ambiguous",
                version="v1",
            ),
        ),
    )

    assert validate_supervisor_storage_binding_artifact_refs(
        missing_version,
        store_path,
    ).errors == (
        "task 'task-missing-version' supervisor storage binding artifact ref "
        "'binding:missing-version' requires non-empty version",
    )
    assert "not found" in validate_supervisor_storage_binding_artifact_refs(
        missing_artifact,
        store_path,
    ).errors[0]
    wrong = validate_supervisor_storage_binding_artifact_refs(
        wrong_product,
        store_path,
    )
    assert wrong.ok is False
    assert "does not contain structured product_type" in wrong.errors[0]
    ambiguous = validate_supervisor_storage_binding_artifact_refs(
        ambiguous_product,
        store_path,
    )
    assert ambiguous.ok is False
    assert "contains multiple" in ambiguous.errors[0]
    with pytest.raises(ValueError, match="supervisor storage binding artifact ref"):
        wrong.raise_for_errors()


def test_supervisor_storage_binding_evidence_rejects_wrong_product_and_schema(tmp_path) -> None:
    wrong_product = tmp_path / "wrong-product.json"
    wrong_product.write_text(
        json.dumps(
            {
                "product_type": "other",
                "schema_version": "1",
            }
        ),
        encoding="utf-8",
    )
    wrong_schema = tmp_path / "wrong-schema.json"
    wrong_schema.write_text(
        json.dumps(
            {
                "product_type": "supervisor_storage_binding_evidence",
                "schema_version": "999",
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="has product_type"):
        read_supervisor_storage_binding_evidence_summary(wrong_product)
    with pytest.raises(ValueError, match="has schema_version"):
        read_supervisor_storage_binding_evidence_summary(wrong_schema)


def test_admit_exchange_artifact_version_submits_exact_single_task(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    projection_path = tmp_path / "scheduler-work-trajectory.json"
    local_trajectory_path = tmp_path / "local-work-trajectory.json"
    store = JsonArtifactVersionStore(store_path)
    artifact = scheduler_task_submission_to_artifact(
        SchedulerTaskSubmission(
            task_id="task-single",
            title="Single stored task",
            instruction="Admit this exact stored task.",
            agent=AgentSpec(agent_id="agent:single", runtime_provider="fake"),
            context_scope=ContextScope(context_id="context:single", lane_id="lane:single"),
            output_artifact_id="task-single:result",
        ),
        artifact_id="submission:single",
        created_at="2026-06-19T01:40:00+08:00",
        version="v1",
    )
    store.put(artifact)

    result = admit_exchange_artifact_version_to_scheduler(
        artifact_store_path=store_path,
        artifact_id="submission:single",
        version="v1",
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
    )
    restored = read_scheduler_state_snapshot(snapshot_path)
    events = JsonlSchedulerEventLog(event_log_path).read_all()
    payload = result.to_json_dict()

    assert result.product_type == "scheduler_task_submission"
    assert result.source_artifact_id == "submission:single"
    assert result.source_artifact_version == "v1"
    assert result.submission_event_ids == ("scheduler-event-1",)
    assert tuple(task.task_id for task in result.submitted_tasks) == ("task-single",)
    assert restored.tasks["task-single"].title == "Single stored task"
    assert [event.event_kind for event in events] == ["task_submitted"]
    assert events[0].timestamp == "2026-06-19T01:40:00+08:00"
    assert events[0].reason == "scheduler task submitted"
    assert events[0].related_artifact_ids == ("submission:single",)
    assert payload["state_written"] is True
    assert payload["ran_tasks"] is False
    assert payload["refreshed_projection"] is False
    assert payload["authority_split"]["scheduler_state_authority"] == "scheduler_snapshot"
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert not projection_path.exists()
    assert not local_trajectory_path.exists()


def test_mark_exchange_artifact_version_consumed_updates_exact_store_version(
    tmp_path,
) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    store = JsonArtifactVersionStore(store_path)
    first = scheduler_task_submission_to_artifact(
        SchedulerTaskSubmission(
            task_id="task-consume-marker",
            title="Consume marker",
            instruction="Mark this exact artifact consumed.",
            agent=AgentSpec(agent_id="agent:consumer", runtime_provider="fake"),
            context_scope=ContextScope(context_id="context:consume-marker"),
        ),
        artifact_id="submission:consume-marker",
        created_at="2026-06-22T10:00:00+08:00",
        version="v1",
    )
    second = scheduler_task_submission_to_artifact(
        SchedulerTaskSubmission(
            task_id="task-consume-marker-v2",
            title="Consume marker v2",
            instruction="Keep latest ordering stable.",
            agent=AgentSpec(agent_id="agent:consumer", runtime_provider="fake"),
            context_scope=ContextScope(context_id="context:consume-marker"),
        ),
        artifact_id="submission:consume-marker",
        created_at="2026-06-22T10:05:00+08:00",
        version="v2",
    )
    store.put(first)
    store.put(second)

    result = mark_exchange_artifact_version_consumed(
        store_path=store_path,
        artifact_id="submission:consume-marker",
        version="v1",
        actor="agent:guide",
        reason="accepted work package admitted into scheduler",
        timestamp="2026-06-22T10:10:00+08:00",
    )
    bundle = inspect_exchange_artifact_store(store_path).to_json_dict()
    summaries = {
        (item["artifact_id"], item["version"]): item
        for item in bundle["summaries"]
    }
    consumed_record = JsonArtifactVersionStore(store_path).get(
        "submission:consume-marker",
        "v1",
    )
    idempotent = mark_exchange_artifact_version_consumed(
        store_path=store_path,
        artifact_id="submission:consume-marker",
        version="v1",
        actor="agent:guide",
    )

    assert result.consumed is True
    assert result.previous_lifecycle_state == "draft"
    assert result.current_lifecycle_state == "consumed"
    assert result.to_json_dict()["exchange_store_mutated"] is True
    assert summaries[("submission:consume-marker", "v1")]["lifecycle_state"] == "consumed"
    assert summaries[("submission:consume-marker", "v1")]["latest"] is False
    assert summaries[("submission:consume-marker", "v2")]["latest"] is True
    assert consumed_record.artifact.parts[-1].part_type == "log"
    assert consumed_record.artifact.parts[-1].log is not None
    assert consumed_record.artifact.parts[-1].log.action == "artifact_consumed"
    assert consumed_record.artifact.parts[-1].log.actor == "agent:guide"
    assert idempotent.already_consumed is True
    assert idempotent.to_json_dict()["exchange_store_mutated"] is False


def test_admit_exchange_artifact_version_validates_binding_refs_when_enabled(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    store = JsonArtifactVersionStore(store_path)
    summary, _evidence_path, _workflow = _supervisor_storage_binding_evidence_summary(
        tmp_path,
    )
    binding_artifact = supervisor_storage_binding_evidence_summary_to_artifact(
        summary,
        artifact_id="binding:context-session-evidence",
        version="v7",
    )
    submission_artifact = scheduler_task_submission_to_artifact(
        SchedulerTaskSubmission(
            task_id="task-consume-binding",
            title="Consume binding",
            instruction="Use the exact supervisor binding artifact.",
            agent=AgentSpec(agent_id="agent:consumer", runtime_provider="fake"),
            context_scope=ContextScope(context_id="context:consumer"),
            input_artifact_refs=(
                ExchangeReference(
                    ref_kind=SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
                    ref_id="binding:context-session-evidence",
                    version="v7",
                ),
            ),
        ),
        artifact_id="submission:consume-binding",
        version="v1",
    )
    store.put(binding_artifact)
    store.put(submission_artifact)

    result = admit_exchange_artifact_version_to_scheduler(
        artifact_store_path=store_path,
        artifact_id="submission:consume-binding",
        version="v1",
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        validate_binding_artifact_refs=True,
    )

    assert tuple(task.task_id for task in result.submitted_tasks) == (
        "task-consume-binding",
    )
    restored = read_scheduler_state_snapshot(snapshot_path)
    assert restored.tasks["task-consume-binding"].input_artifact_refs[0].ref_kind == (
        SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND
    )


def test_admit_exchange_artifact_version_rejects_missing_binding_ref_before_mutation(
    tmp_path,
) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    store = JsonArtifactVersionStore(store_path)
    submission_artifact = scheduler_task_submission_to_artifact(
        SchedulerTaskSubmission(
            task_id="task-bad-binding-ref",
            title="Bad binding ref",
            instruction="Should not be admitted.",
            agent=AgentSpec(agent_id="agent:consumer", runtime_provider="fake"),
            context_scope=ContextScope(context_id="context:consumer"),
            input_artifact_refs=(
                ExchangeReference(
                    ref_kind=SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
                    ref_id="binding:not-found",
                    version="v1",
                ),
            ),
        ),
        artifact_id="submission:bad-binding-ref",
        version="v1",
    )
    store.put(submission_artifact)

    with pytest.raises(ValueError, match="binding:not-found"):
        admit_exchange_artifact_version_to_scheduler(
            artifact_store_path=store_path,
            artifact_id="submission:bad-binding-ref",
            version="v1",
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            validate_binding_artifact_refs=True,
        )

    assert not snapshot_path.exists()
    assert not event_log_path.exists()


def test_admit_exchange_artifact_with_ledger_records_binding_summary_on_success(
    tmp_path,
) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    ledger_path = tmp_path / "exchange-artifact-admissions.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    store = JsonArtifactVersionStore(store_path)
    summary, _evidence_path, _workflow = _supervisor_storage_binding_evidence_summary(
        tmp_path,
    )
    store.put(
        supervisor_storage_binding_evidence_summary_to_artifact(
            summary,
            artifact_id="binding:ledger-success",
            version="v1",
        )
    )
    store.put(
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task-ledger-binding-success",
                title="Ledger binding success",
                instruction="Admit with binding summary.",
                agent=AgentSpec(agent_id="agent:consumer", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:consumer"),
                input_artifact_refs=(
                    ExchangeReference(
                        ref_kind=SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
                        ref_id="binding:ledger-success",
                        version="v1",
                    ),
                ),
            ),
            artifact_id="submission:ledger-binding-success",
            version="v1",
        )
    )

    result = admit_exchange_artifact_version_with_ledger(
        artifact_store_path=store_path,
        artifact_id="submission:ledger-binding-success",
        version="v1",
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        admission_ledger_path=ledger_path,
        validate_binding_artifact_refs=True,
    )
    records = JsonExchangeArtifactAdmissionLedger(ledger_path).read_all()
    readback = inspect_exchange_artifact_admission_ledger(ledger_path).to_json_dict()

    assert result["ok"] is True
    assert result["binding_reference_summary"]["enabled"] is True
    assert result["binding_reference_summary"]["ok"] is True
    assert result["binding_reference_summary"]["binding_ref_count"] == 1
    assert records[0].binding_reference_summary["checked_ref_count"] == 1
    assert readback["records"][0]["binding_reference_summary"]["tasks"][0][
        "task_id"
    ] == "task-ledger-binding-success"
    assert readback["records"][0]["binding_reference_summary"]["tasks"][0][
        "binding_refs"
    ][0]["ref_id"] == "binding:ledger-success"
    assert readback["records"][0]["binding_reference_summary"][
        "raw_evidence_json_read"
    ] is False


def test_admit_exchange_artifact_with_ledger_can_mark_consumed_on_success(
    tmp_path,
) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    ledger_path = tmp_path / "exchange-artifact-admissions.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    JsonArtifactVersionStore(store_path).put(
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task-consume-on-admit",
                title="Consume on admit",
                instruction="Mark consumed after successful admission.",
                agent=AgentSpec(agent_id="agent:consumer", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:consumer"),
            ),
            artifact_id="submission:consume-on-admit",
            version="v1",
        )
    )

    result = admit_exchange_artifact_version_with_ledger(
        artifact_store_path=store_path,
        artifact_id="submission:consume-on-admit",
        version="v1",
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        admission_ledger_path=ledger_path,
        mark_consumed_on_success=True,
        actor="agent:guide",
        timestamp="2026-06-22T10:20:00+08:00",
    )
    bundle = inspect_exchange_artifact_store(
        store_path,
        admission_ledger_path=ledger_path,
    ).to_json_dict()
    summary = bundle["summaries"][0]

    assert result["ok"] is True
    assert result["consumption_state"]["requested"] is True
    assert result["consumption_state"]["consumed"] is True
    assert result["consumption_state"]["previous_lifecycle_state"] == "draft"
    assert result["consumption_state"]["current_lifecycle_state"] == "consumed"
    assert result["consumption_state"]["actor"] == "agent:guide"
    assert result["authority_split"]["exchange_store_mutated"] is True
    assert summary["lifecycle_state"] == "consumed"
    assert summary["admission_state"]["status"] == "admitted"


def test_admit_exchange_artifact_with_ledger_records_binding_summary_on_failure(
    tmp_path,
) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    ledger_path = tmp_path / "exchange-artifact-admissions.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    JsonArtifactVersionStore(store_path).put(
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task-ledger-binding-failure",
                title="Ledger binding failure",
                instruction="Should fail before scheduler mutation.",
                agent=AgentSpec(agent_id="agent:consumer", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:consumer"),
                input_artifact_refs=(
                    ExchangeReference(
                        ref_kind=SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
                        ref_id="binding:missing-ledger",
                        version="v1",
                    ),
                ),
            ),
            artifact_id="submission:ledger-binding-failure",
            version="v1",
        )
    )

    result = admit_exchange_artifact_version_with_ledger(
        artifact_store_path=store_path,
        artifact_id="submission:ledger-binding-failure",
        version="v1",
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        admission_ledger_path=ledger_path,
        validate_binding_artifact_refs=True,
    )
    readback = inspect_exchange_artifact_admission_ledger(ledger_path).to_json_dict()

    assert result["ok"] is False
    assert "binding:missing-ledger" in result["error"]
    assert result["binding_reference_summary"]["ok"] is False
    assert result["binding_reference_summary"]["error_count"] == 1
    assert readback["records"][0]["status"] == "failed"
    assert readback["records"][0]["binding_reference_summary"]["ok"] is False
    assert "binding:missing-ledger" in readback["records"][0][
        "binding_reference_summary"
    ]["errors"][0]
    assert not snapshot_path.exists()
    assert not event_log_path.exists()


def test_admit_exchange_artifact_with_ledger_does_not_consume_on_failure(
    tmp_path,
) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    ledger_path = tmp_path / "exchange-artifact-admissions.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    JsonArtifactVersionStore(store_path).put(
        ExchangeArtifact(
            artifact_id="message:not-submission",
            kind="message",
            intent="inform",
            producer="agent:guide",
            version="v1",
            lifecycle_state="accepted",
            parts=(ExchangePayloadPart(part_type="text", text="Not admissible."),),
        )
    )

    result = admit_exchange_artifact_version_with_ledger(
        artifact_store_path=store_path,
        artifact_id="message:not-submission",
        version="v1",
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        admission_ledger_path=ledger_path,
        mark_consumed_on_success=True,
    )
    bundle = inspect_exchange_artifact_store(
        store_path,
        admission_ledger_path=ledger_path,
    ).to_json_dict()

    assert result["ok"] is False
    assert result["consumption_state"]["requested"] is True
    assert result["consumption_state"]["consumed"] is False
    assert result["authority_split"]["exchange_store_mutated"] is False
    assert bundle["summaries"][0]["lifecycle_state"] == "accepted"
    assert bundle["summaries"][0]["admission_state"]["status"] == "failed"
    assert not snapshot_path.exists()
    assert not event_log_path.exists()


def test_admit_exchange_artifact_version_submits_exact_batch(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    base = _scheduled_task("task-base", state="complete")
    write_scheduler_state_snapshot(SchedulerState(tasks={"task-base": base}), snapshot_path)
    store = JsonArtifactVersionStore(store_path)
    batch_artifact = scheduler_task_batch_submission_to_artifact(
        SchedulerTaskBatchSubmission(
            batch_id="batch-exact",
            tasks=(
                SchedulerTaskSubmission(
                    task_id="task-a",
                    title="Task A",
                    instruction="Complete A.",
                    agent=AgentSpec(agent_id="agent:a", runtime_provider="fake"),
                    context_scope=ContextScope(context_id="context:a", lane_id="lane:a"),
                    output_artifact_id="task-a:result",
                    dependencies=(
                        TaskDependency(
                            dependency_id="dep-base-a",
                            source_task_id="task-base",
                            target_task_id="task-a",
                            required_state="complete",
                        ),
                    ),
                ),
                SchedulerTaskSubmission(
                    task_id="task-b",
                    title="Task B",
                    instruction="Complete B after A.",
                    agent=AgentSpec(agent_id="agent:b", runtime_provider="fake"),
                    context_scope=ContextScope(context_id="context:b", lane_id="lane:b"),
                    output_artifact_id="task-b:result",
                    dependencies=(
                        TaskDependency(
                            dependency_id="dep-a-b",
                            source_task_id="task-a",
                            target_task_id="task-b",
                            required_state="complete",
                        ),
                    ),
                ),
            ),
        ),
        artifact_id="submission:batch-exact",
        created_at="2026-06-19T01:41:00+08:00",
        version="v2",
    )
    store.put(batch_artifact)

    result = admit_exchange_artifact_version_to_scheduler(
        artifact_store_path=store_path,
        artifact_id="submission:batch-exact",
        version="v2",
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        timestamp="2026-06-19T01:42:00+08:00",
    )
    restored = read_scheduler_state_snapshot(snapshot_path)
    events = JsonlSchedulerEventLog(event_log_path).read_all()

    assert result.product_type == "scheduler_task_batch_submission"
    assert result.snapshot_existed is True
    assert result.submission_event_ids == ("scheduler-event-1", "scheduler-event-2")
    assert tuple(task.task_id for task in result.submitted_tasks) == ("task-a", "task-b")
    assert tuple(sorted(restored.tasks)) == ("task-a", "task-b", "task-base")
    assert tuple(dependency.dependency_id for dependency in result.dependencies_added) == (
        "dep-base-a",
        "dep-a-b",
    )
    assert [event.timestamp for event in events] == [
        "2026-06-19T01:42:00+08:00",
        "2026-06-19T01:42:00+08:00",
    ]
    assert events[0].related_dependency_ids == ("dep-base-a",)
    assert events[1].related_dependency_ids == ("dep-a-b",)


def test_admit_exchange_artifact_version_reports_missing_exact_version(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    JsonArtifactVersionStore(store_path).put(_accepted_contract_artifact(version="v1"))

    with pytest.raises(ValueError, match="exchange artifact version not found"):
        admit_exchange_artifact_version_to_scheduler(
            artifact_store_path=store_path,
            artifact_id="server-api",
            version="v2",
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
        )

    assert not snapshot_path.exists()
    assert not event_log_path.exists()


def test_admit_exchange_artifact_version_rejects_non_submission_without_mutation(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    JsonArtifactVersionStore(store_path).put(_accepted_contract_artifact(version="v1"))

    with pytest.raises(ValueError, match="is not a scheduler submission artifact"):
        admit_exchange_artifact_version_to_scheduler(
            artifact_store_path=store_path,
            artifact_id="server-api",
            version="v1",
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
        )

    assert not snapshot_path.exists()
    assert not event_log_path.exists()


def test_admit_exchange_artifact_version_rejects_ambiguous_submission_payloads(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    first = SchedulerTaskSubmission(
        task_id="task-a",
        title="Task A",
        instruction="Complete A.",
        agent=AgentSpec(agent_id="agent:a", runtime_provider="fake"),
        context_scope=ContextScope(context_id="context:a"),
    )
    second = SchedulerTaskSubmission(
        task_id="task-b",
        title="Task B",
        instruction="Complete B.",
        agent=AgentSpec(agent_id="agent:b", runtime_provider="fake"),
        context_scope=ContextScope(context_id="context:b"),
    )
    ambiguous = ExchangeArtifact(
        artifact_id="submission:ambiguous",
        kind="request",
        intent="propose",
        producer="agent:guide",
        version="v1",
        parts=(
            ExchangePayloadPart(part_type="structured", data={
                "product_type": "scheduler_task_submission",
                "task_id": first.task_id,
                "title": first.title,
                "instruction": first.instruction,
                "agent": {"agent_id": first.agent.agent_id, "runtime_provider": "fake"},
                "context_scope": {"context_id": first.context_scope.context_id},
            }),
            ExchangePayloadPart(part_type="structured", data={
                "product_type": "scheduler_task_submission",
                "task_id": second.task_id,
                "title": second.title,
                "instruction": second.instruction,
                "agent": {"agent_id": second.agent.agent_id, "runtime_provider": "fake"},
                "context_scope": {"context_id": second.context_scope.context_id},
            }),
        ),
    )
    JsonArtifactVersionStore(store_path).put(ambiguous)

    with pytest.raises(ValueError, match="multiple scheduler submission payloads"):
        admit_exchange_artifact_version_to_scheduler(
            artifact_store_path=store_path,
            artifact_id="submission:ambiguous",
            version="v1",
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
        )

    assert not snapshot_path.exists()
    assert not event_log_path.exists()


def test_admit_exchange_artifact_version_surfaces_malformed_store_error(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    store_path.write_text("{bad json", encoding="utf-8")

    with pytest.raises(ValueError, match="invalid exchange artifact store JSON"):
        admit_exchange_artifact_version_to_scheduler(
            artifact_store_path=store_path,
            artifact_id="submission:any",
            version="v1",
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
        )

    assert not snapshot_path.exists()
    assert not event_log_path.exists()


def test_admit_exchange_artifact_version_with_ledger_rejects_duplicate_before_scheduler_mutation(tmp_path) -> None:
    store_path = tmp_path / "exchange-artifacts.json"
    ledger_path = tmp_path / "exchange-artifact-admissions.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    JsonArtifactVersionStore(store_path).put(
        scheduler_task_submission_to_artifact(
            SchedulerTaskSubmission(
                task_id="task-ledger-dup",
                title="Ledger duplicate task",
                instruction="Admit once, reject replay by default.",
                agent=AgentSpec(agent_id="agent:ledger-dup", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:ledger-dup"),
                output_artifact_id="task-ledger-dup:result",
            ),
            artifact_id="submission:ledger-dup",
            created_at="2026-06-19T05:20:00+08:00",
            version="v1",
        )
    )

    first = admit_exchange_artifact_version_with_ledger(
        artifact_store_path=store_path,
        artifact_id="submission:ledger-dup",
        version="v1",
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        admission_ledger_path=ledger_path,
    )
    duplicate = admit_exchange_artifact_version_with_ledger(
        artifact_store_path=store_path,
        artifact_id="submission:ledger-dup",
        version="v1",
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        admission_ledger_path=ledger_path,
        replace_existing=True,
    )

    assert first["ok"] is True
    assert duplicate["ok"] is False
    assert duplicate["status"] == "rejected_duplicate"
    assert duplicate["duplicate_of"] == "exchange-artifact-admission-1"
    assert duplicate["scheduler_state_mutated"] is False
    assert duplicate["event_log_mutated"] is False
    assert duplicate["authority_split"]["scheduler_state_mutated"] is False
    assert len(read_scheduler_state_snapshot(snapshot_path).tasks) == 1
    assert len(JsonlSchedulerEventLog(event_log_path).read_all()) == 1
    records = JsonExchangeArtifactAdmissionLedger(ledger_path).read_all()
    assert [record.status for record in records] == ["admitted", "rejected_duplicate"]


def test_run_persisted_scheduler_once_recovers_drains_and_writes_snapshot(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    batch = SchedulerTaskBatchSubmission(
        batch_id="batch-run-once",
        tasks=(
            SchedulerTaskSubmission(
                task_id="task-a",
                title="Task A",
                instruction="Complete A.",
                agent=AgentSpec(agent_id="agent:a", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:a", lane_id="lane:a"),
                output_artifact_id="task-a:result",
            ),
            SchedulerTaskSubmission(
                task_id="task-b",
                title="Task B",
                instruction="Complete B after A.",
                agent=AgentSpec(agent_id="agent:b", runtime_provider="fake"),
                context_scope=ContextScope(context_id="context:b", lane_id="lane:b"),
                output_artifact_id="task-b:result",
                dependencies=(
                    TaskDependency(
                        dependency_id="dep-a-b",
                        source_task_id="task-a",
                        target_task_id="task-b",
                        required_state="complete",
                    ),
                ),
            ),
        ),
    )
    submit_scheduler_task_batch_with_persistence(
        SchedulerState(),
        scheduler_task_batch_submission_to_artifact(
            batch,
            artifact_id="submission:run-once-batch",
        ),
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        timestamp="2026-06-17T01:20:00+08:00",
    )
    sandbox_registry = SandboxProviderRegistry()
    sandbox_registry.register(SharedProcessSandboxProvider())
    runtime_registry = AgentRuntimeAdapterRegistry()
    runtime_registry.register(
        FakeAgentRuntimeAdapter(
            artifact_store=InMemoryArtifactVersionStore(),
            timestamp="2026-06-17T01:21:00+08:00",
        )
    )

    result = run_persisted_scheduler_once(
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        sandbox_registry=sandbox_registry,
        runtime_registry=runtime_registry,
        workspace_root="E:/workspace/project",
        scratch_root=".codex/scratch",
        timestamp="2026-06-17T01:21:00+08:00",
    )
    written = read_scheduler_state_snapshot(snapshot_path)
    events = JsonlSchedulerEventLog(event_log_path).read_all()
    second = run_persisted_scheduler_once(
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        sandbox_registry=sandbox_registry,
        runtime_registry=runtime_registry,
        timestamp="2026-06-17T01:22:00+08:00",
    )

    assert result.state_written is True
    assert result.snapshot_path == snapshot_path
    assert result.recovery.event_count == 2
    assert result.drain.stop_reason == "no_ready_tasks"
    assert tuple(run.runtime_result.run_handle.task_id for run in result.drain.preflight_results) == (
        "task-a",
        "task-b",
    )
    assert result.drain.preflight_results[0].preflight.scratch.path == ".codex/scratch/task-a"
    assert written.tasks["task-a"].state == "complete"
    assert written.tasks["task-b"].state == "complete"
    assert tuple(record.task_id for record in written.run_records) == ("task-a", "task-b")
    assert [event.event_kind for event in events] == [
        "task_submitted",
        "task_submitted",
        "task_ready",
        "task_waiting",
        "task_running",
        "task_completed",
        "task_ready",
        "task_running",
        "task_completed",
    ]
    assert second.drain.stop_reason == "no_ready_tasks"
    assert second.drain.preflight_results == ()


def test_run_persisted_scheduler_once_with_fake_wiring_records_provider_metadata(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-a": _scheduled_task(
                    "task-a",
                    output_artifact_id="task-a:result",
                ),
            },
        ),
        snapshot_path,
    )
    sandbox_registry = SandboxProviderRegistry()
    sandbox_registry.register(SharedProcessSandboxProvider())
    runtime_wiring = build_runtime_registry_from_config(
        RuntimeRegistryWiringConfig(
            providers=("fake",),
            host_invocation=RuntimeHostInvocation(
                surface="mcp-scheduler-run-once",
                invocation_id="mcp-fake-run",
                requested_providers=("fake",),
            ),
        )
    )

    result = run_persisted_scheduler_once_with_wiring(
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        sandbox_registry=sandbox_registry,
        runtime_wiring=runtime_wiring,
        timestamp="2026-06-17T17:00:00+08:00",
    )

    assert result.drain.stop_reason == "no_ready_tasks"
    assert result.runtime_registry_providers == ("fake",)
    assert result.runtime_host_surface == "mcp-scheduler-run-once"
    assert read_scheduler_state_snapshot(snapshot_path).tasks["task-a"].state == "complete"


def test_run_persisted_scheduler_once_with_host_authorized_qoder_wiring(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-q": _scheduled_task(
                    "task-q",
                    agent=AgentSpec(agent_id="agent:qoder", runtime_provider="qoder"),
                    output_artifact_id="task-q:result",
                ),
            },
        ),
        snapshot_path,
    )
    sandbox_registry = SandboxProviderRegistry()
    sandbox_registry.register(SharedProcessSandboxProvider())
    runtime_wiring = build_runtime_registry_from_config(
        RuntimeRegistryWiringConfig(
            providers=("qoder",),
            host_invocation=RuntimeHostInvocation(
                surface="host-authorized-adapter",
                invocation_id="host-qoder-run",
                requested_providers=("qoder",),
                requested_by="host:test",
            ),
            qoder_permission_grant=RuntimeProviderPermissionGrant(
                grant_id="grant-qoder",
                provider="qoder",
                approved_by="host:test",
                approved_at="2026-06-17T16:59:00+08:00",
                allow_sdk_client=True,
            ),
        ),
        qoder_query_client=_RecordingQoderClient(
            QoderQueryResult(summary="Qoder host run complete.", output_text="done")
        ),
    )

    result = run_persisted_scheduler_once_with_wiring(
        snapshot_path=snapshot_path,
        event_log_path=event_log_path,
        sandbox_registry=sandbox_registry,
        runtime_wiring=runtime_wiring,
        timestamp="2026-06-17T17:01:00+08:00",
    )

    assert result.drain.stop_reason == "no_ready_tasks"
    assert result.runtime_registry_providers == ("qoder",)
    assert result.runtime_host_surface == "host-authorized-adapter"
    assert read_scheduler_state_snapshot(snapshot_path).tasks["task-q"].state == "complete"


def test_run_persisted_scheduler_once_with_wiring_rejects_non_fake_without_host_invocation(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(SchedulerState(), snapshot_path)
    sandbox_registry = SandboxProviderRegistry()
    sandbox_registry.register(SharedProcessSandboxProvider())
    registry = AgentRuntimeAdapterRegistry()
    registry.register(
        QoderAgentRuntimeAdapter(
            query_client=_RecordingQoderClient(QoderQueryResult(summary="unused"))
        )
    )
    runtime_wiring = RuntimeRegistryWiringResult(
        registry=registry,
        config=RuntimeRegistryWiringConfig(providers=("qoder",)),
        registered_providers=("qoder",),
    )

    with pytest.raises(ValueError, match="requires RuntimeHostInvocation"):
        run_persisted_scheduler_once_with_wiring(
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            sandbox_registry=sandbox_registry,
            runtime_wiring=runtime_wiring,
        )


def test_scheduler_daemon_tick_advances_one_bounded_fake_task(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-a": _scheduled_task("task-a", output_artifact_id="task-a:result"),
                "task-b": _scheduled_task("task-b", output_artifact_id="task-b:result"),
            },
            dependencies=(
                TaskDependency(
                    dependency_id="dep-a-b",
                    source_task_id="task-a",
                    target_task_id="task-b",
                    required_state="complete",
                ),
            ),
        ),
        snapshot_path,
    )

    result = run_scheduler_daemon_tick(
        SchedulerDaemonTickRequest(
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            max_runs=1,
            timestamp="2026-06-19T10:40:00+08:00",
        )
    )
    payload = result.to_json_dict()
    written = read_scheduler_state_snapshot(snapshot_path)

    assert payload["ok"] is True
    assert payload["run_count"] == 1
    assert payload["stop_reason"] == "max_runs_reached"
    assert payload["ran_tasks"] is True
    assert payload["refreshed_projection"] is False
    assert payload["scheduler_event_count"] == 5
    assert payload["queue_summary"]["completed_task_ids"] == ["task-a"]
    assert payload["queue_summary"]["ready_task_ids"] == ["task-b"]
    assert payload["queue_summary"]["dependency_ids"] == ["dep-a-b"]
    assert payload["authority_split"]["scheduler_state_mutated"] is True
    assert payload["authority_split"]["scheduler_projection_refreshed"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert written.tasks["task-a"].state == "complete"
    assert written.tasks["task-b"].state == "ready"


def test_scheduler_daemon_tick_reports_blocked_queue_without_running(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-blocked": _scheduled_task(
                    "task-blocked",
                    edit_lease=EditScopeLease(
                        lease_id="lease-blocked",
                        task_id="task-blocked",
                        allowed_artifacts=("src/app.py",),
                    ),
                    sandbox_profile=SandboxProfile(
                        profile_id="none",
                        profile_kind="none",
                    ),
                ),
            },
        ),
        snapshot_path,
    )

    result = run_scheduler_daemon_tick(
        SchedulerDaemonTickRequest(
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            max_runs=1,
        )
    )
    payload = result.to_json_dict()

    assert payload["run_count"] == 0
    assert payload["stop_reason"] == "blocked_tasks"
    assert payload["ran_tasks"] is False
    assert payload["queue_summary"]["blocked_task_ids"] == ["task-blocked"]
    assert payload["queue_summary"]["task_state_counts"] == {"blocked": 1}
    assert payload["authority_split"]["provider_executed"] is False


def test_scheduler_daemon_tick_rejects_non_fake_without_injected_runtime(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(SchedulerState(), snapshot_path)

    with pytest.raises(ValueError, match="only supports runtime_provider='fake'"):
        run_scheduler_daemon_tick(
            SchedulerDaemonTickRequest(
                snapshot_path=snapshot_path,
                event_log_path=event_log_path,
                runtime_provider="qoder",
            )
        )


def test_summarize_scheduler_queue_groups_task_states() -> None:
    summary = summarize_scheduler_queue(
        SchedulerState(
            tasks={
                "task-a": _scheduled_task("task-a", state="complete"),
                "task-b": _scheduled_task("task-b", state="ready"),
                "task-c": _scheduled_task("task-c", state="waiting"),
            },
            dependencies=(
                TaskDependency(
                    dependency_id="dep-a-c",
                    source_task_id="task-a",
                    target_task_id="task-c",
                    required_state="complete",
                ),
            ),
        )
    )
    payload = summary.to_json_dict()

    assert payload["task_state_counts"] == {
        "complete": 1,
        "ready": 1,
        "waiting": 1,
    }
    assert payload["completed_task_ids"] == ["task-a"]
    assert payload["ready_task_ids"] == ["task-b"]
    assert payload["waiting_task_ids"] == ["task-c"]
    assert payload["dependency_ids"] == ["dep-a-c"]


def test_scheduler_daemon_loop_runs_dependent_tasks_until_no_ready(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-a": _scheduled_task("task-a", output_artifact_id="task-a:result"),
                "task-b": _scheduled_task("task-b", output_artifact_id="task-b:result"),
            },
            dependencies=(
                TaskDependency(
                    dependency_id="dep-a-b",
                    source_task_id="task-a",
                    target_task_id="task-b",
                    required_state="complete",
                ),
            ),
        ),
        snapshot_path,
    )

    result = run_scheduler_daemon_loop(
        SchedulerDaemonLoopRequest(
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            stop_policy=SchedulerDaemonLoopStopPolicy(
                max_ticks=3,
                max_runs_per_tick=1,
            ),
            timestamp="2026-06-19T11:10:00+08:00",
        )
    )
    payload = result.to_json_dict()
    written = read_scheduler_state_snapshot(snapshot_path)

    assert payload["ok"] is True
    assert payload["tick_count"] == 2
    assert payload["total_run_count"] == 2
    assert payload["stop_reason"] == "no_ready_tasks"
    assert payload["ran_tasks"] is True
    assert payload["refreshed_projection"] is False
    assert [item["run_count"] for item in payload["iterations"]] == [1, 1]
    assert payload["final_queue_summary"]["completed_task_ids"] == ["task-a", "task-b"]
    assert payload["final_queue_summary"]["ready_task_ids"] == []
    assert payload["authority_split"]["scheduler_state_mutated"] is True
    assert payload["authority_split"]["provider_executed"] is True
    assert payload["authority_split"]["scheduler_projection_refreshed"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert written.tasks["task-a"].state == "complete"
    assert written.tasks["task-b"].state == "complete"


def test_scheduler_daemon_loop_stops_at_max_ticks_with_ready_work(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-a": _scheduled_task("task-a", output_artifact_id="task-a:result"),
                "task-b": _scheduled_task("task-b", output_artifact_id="task-b:result"),
            },
            dependencies=(
                TaskDependency(
                    dependency_id="dep-a-b",
                    source_task_id="task-a",
                    target_task_id="task-b",
                    required_state="complete",
                ),
            ),
        ),
        snapshot_path,
    )

    result = run_scheduler_daemon_loop(
        SchedulerDaemonLoopRequest(
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            stop_policy=SchedulerDaemonLoopStopPolicy(
                max_ticks=1,
                max_runs_per_tick=1,
            ),
        )
    )
    payload = result.to_json_dict()

    assert payload["tick_count"] == 1
    assert payload["total_run_count"] == 1
    assert payload["stop_reason"] == "max_ticks_reached"
    assert payload["final_queue_summary"]["completed_task_ids"] == ["task-a"]
    assert payload["final_queue_summary"]["ready_task_ids"] == ["task-b"]


def test_scheduler_daemon_loop_reports_blocked_tasks_without_running(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-blocked": _scheduled_task(
                    "task-blocked",
                    edit_lease=EditScopeLease(
                        lease_id="lease-blocked",
                        task_id="task-blocked",
                        allowed_artifacts=("src/app.py",),
                    ),
                    sandbox_profile=SandboxProfile(
                        profile_id="none",
                        profile_kind="none",
                    ),
                ),
            },
        ),
        snapshot_path,
    )

    result = run_scheduler_daemon_loop(
        SchedulerDaemonLoopRequest(
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            stop_policy=SchedulerDaemonLoopStopPolicy(max_ticks=3),
        )
    )
    payload = result.to_json_dict()

    assert payload["tick_count"] == 1
    assert payload["total_run_count"] == 0
    assert payload["stop_reason"] == "blocked_tasks"
    assert payload["final_queue_summary"]["blocked_task_ids"] == ["task-blocked"]
    assert payload["authority_split"]["provider_executed"] is False


def test_scheduler_daemon_loop_stops_at_runtime_failure_limit(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-a": _scheduled_task("task-a", output_artifact_id="task-a:result"),
                "task-b": _scheduled_task("task-b", output_artifact_id="task-b:result"),
            },
        ),
        snapshot_path,
    )
    runtime_registry = AgentRuntimeAdapterRegistry()
    runtime_registry.register(
        _SelectiveFailingRuntime(
            failing_task_ids=("task-a",),
            artifact_store=InMemoryArtifactVersionStore(),
            timestamp="2026-06-19T11:20:00+08:00",
        )
    )
    sandbox_registry = SandboxProviderRegistry()
    sandbox_registry.register(SharedProcessSandboxProvider())

    result = run_scheduler_daemon_loop(
        SchedulerDaemonLoopRequest(
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            stop_policy=SchedulerDaemonLoopStopPolicy(
                max_ticks=3,
                max_runs_per_tick=2,
                max_runtime_failures=1,
            ),
            continue_on_failure=True,
        ),
        runtime_registry=runtime_registry,
        sandbox_registry=sandbox_registry,
    )
    payload = result.to_json_dict()

    assert payload["stop_reason"] == "runtime_failure_limit_reached"
    assert payload["total_run_count"] == 1
    assert payload["final_queue_summary"]["failed_task_ids"] == ["task-a"]
    assert payload["final_queue_summary"]["completed_task_ids"] == ["task-b"]
    assert "runtime failure count 1 reached limit 1" in payload["stop_detail"]


def test_scheduler_daemon_loop_zero_max_ticks_is_read_only(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-a": _scheduled_task("task-a", output_artifact_id="task-a:result"),
            },
        ),
        snapshot_path,
    )

    result = run_scheduler_daemon_loop(
        SchedulerDaemonLoopRequest(
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            stop_policy=SchedulerDaemonLoopStopPolicy(max_ticks=0),
        )
    )
    payload = result.to_json_dict()
    written = read_scheduler_state_snapshot(snapshot_path)

    assert payload["tick_count"] == 0
    assert payload["total_run_count"] == 0
    assert payload["stop_reason"] == "max_ticks_reached"
    assert payload["authority_split"]["scheduler_state_mutated"] is False
    assert payload["final_queue_summary"]["task_state_counts"] == {"proposed": 1}
    assert written.tasks["task-a"].state == "proposed"
    assert not event_log_path.exists()


def test_scheduler_daemon_lifecycle_transitions_round_trip(tmp_path) -> None:
    control_path = tmp_path / "scheduler-daemon-control.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"

    started = apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="start",
            daemon_id="daemon-1",
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            run_id="run-1",
            timestamp="100",
            stale_after_seconds=30,
            metadata={"owner": "test"},
        )
    )
    paused = apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="pause",
            timestamp="110",
        )
    )
    resumed = apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="resume",
            timestamp="120",
        )
    )
    heartbeat = apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="heartbeat",
            timestamp="130",
        )
    )
    cancelling = apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="cancel",
            timestamp="140",
        )
    )
    stopped = apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="shutdown",
            timestamp="150",
        )
    )
    control = read_scheduler_daemon_lifecycle_control(control_path)

    assert started.control.state == "running"
    assert started.control.snapshot_path == str(snapshot_path)
    assert started.control.metadata == {"owner": "test"}
    assert paused.control.state == "paused"
    assert resumed.control.state == "running"
    assert heartbeat.control.heartbeat_at == "130"
    assert cancelling.control.state == "cancelling"
    assert cancelling.control.requested_action == "cancel"
    assert stopped.control.state == "stopped"
    assert control.state == "stopped"
    assert control.run_id == "run-1"
    assert control.stale_after_seconds == 30
    assert control.to_json_dict()["authority_split"]["starts_background_process"] is False


def test_scheduler_daemon_lifecycle_marks_stale_from_heartbeat_threshold(tmp_path) -> None:
    control_path = tmp_path / "scheduler-daemon-control.json"
    apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="start",
            daemon_id="daemon-1",
            snapshot_path=tmp_path / "scheduler-state.json",
            event_log_path=tmp_path / "scheduler-events.jsonl",
            timestamp="100",
            stale_after_seconds=10,
        )
    )

    fresh = inspect_scheduler_daemon_lifecycle_control(
        control_path,
        now_epoch_seconds=105,
    )
    stale = inspect_scheduler_daemon_lifecycle_control(
        control_path,
        now_epoch_seconds=111,
    )

    assert fresh.changed is False
    assert fresh.control.state == "running"
    assert stale.changed is True
    assert stale.previous_state == "running"
    assert stale.control.state == "stale"
    assert "heartbeat age exceeded 10 seconds" in stale.reason


def test_scheduler_daemon_lifecycle_stale_detection_accepts_iso_heartbeat(tmp_path) -> None:
    control_path = tmp_path / "scheduler-daemon-control.json"
    apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="start",
            daemon_id="daemon-1",
            snapshot_path=tmp_path / "scheduler-state.json",
            event_log_path=tmp_path / "scheduler-events.jsonl",
            timestamp="2026-06-20T00:00:00+00:00",
            stale_after_seconds=60,
        )
    )

    fresh = inspect_scheduler_daemon_lifecycle_control(
        control_path,
        now_epoch_seconds=1781913630,
    )
    stale = inspect_scheduler_daemon_lifecycle_control(
        control_path,
        now_epoch_seconds=1781913661,
    )

    assert fresh.changed is False
    assert fresh.control.state == "running"
    assert stale.changed is True
    assert stale.control.state == "stale"


def test_scheduler_daemon_lifecycle_run_once_skips_paused_without_scheduler_mutation(
    tmp_path,
) -> None:
    control_path = tmp_path / "scheduler-daemon-control.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(tasks={"task-a": _scheduled_task("task-a", output_artifact_id="task-a:result")}),
        snapshot_path,
    )
    apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="start",
            daemon_id="daemon-1",
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            timestamp="100",
        )
    )
    apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="pause",
            timestamp="101",
        )
    )

    result = run_scheduler_daemon_lifecycle_once(
        SchedulerDaemonLifecycleRunOnceRequest(
            control_path=control_path,
            stop_policy=SchedulerDaemonLoopStopPolicy(max_ticks=2, max_runs_per_tick=1),
            timestamp="102",
        )
    )
    payload = result.to_json_dict()

    assert payload["skipped"] is True
    assert "paused" in payload["skip_reason"]
    assert payload["authority_split"]["scheduler_state_mutated"] is False
    assert read_scheduler_state_snapshot(snapshot_path).tasks["task-a"].state == "proposed"
    assert not event_log_path.exists()


def test_scheduler_daemon_lifecycle_run_once_runs_bounded_loop_and_records_summary(
    tmp_path,
) -> None:
    control_path = tmp_path / "scheduler-daemon-control.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(tasks={"task-a": _scheduled_task("task-a", output_artifact_id="task-a:result")}),
        snapshot_path,
    )
    apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="start",
            daemon_id="daemon-1",
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            timestamp="100",
        )
    )

    result = run_scheduler_daemon_lifecycle_once(
        SchedulerDaemonLifecycleRunOnceRequest(
            control_path=control_path,
            stop_policy=SchedulerDaemonLoopStopPolicy(max_ticks=2, max_runs_per_tick=1),
            timestamp="110",
        )
    )
    control = read_scheduler_daemon_lifecycle_control(control_path)
    payload = result.to_json_dict()

    assert result.skipped is False
    assert result.loop is not None
    assert result.loop.total_run_count == 1
    assert control.state == "running"
    assert control.heartbeat_at == "110"
    assert control.last_result_summary["stop_reason"] == "no_ready_tasks"
    assert control.last_result_summary["total_run_count"] == 1
    assert payload["authority_split"]["scheduler_state_mutated"] is True
    assert payload["authority_split"]["provider_executed"] is True
    assert payload["authority_split"]["starts_background_process"] is False
    assert read_scheduler_state_snapshot(snapshot_path).tasks["task-a"].state == "complete"


def test_scheduler_daemon_lifecycle_run_once_consumes_cancel_without_running_loop(
    tmp_path,
) -> None:
    control_path = tmp_path / "scheduler-daemon-control.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(tasks={"task-a": _scheduled_task("task-a", output_artifact_id="task-a:result")}),
        snapshot_path,
    )
    apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="start",
            daemon_id="daemon-1",
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            timestamp="100",
        )
    )
    apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="cancel",
            timestamp="101",
        )
    )

    result = run_scheduler_daemon_lifecycle_once(
        SchedulerDaemonLifecycleRunOnceRequest(
            control_path=control_path,
            stop_policy=SchedulerDaemonLoopStopPolicy(max_ticks=2, max_runs_per_tick=1),
            timestamp="102",
        )
    )
    control = read_scheduler_daemon_lifecycle_control(control_path)
    payload = result.to_json_dict()

    assert result.skipped is True
    assert control.state == "cancelled"
    assert control.last_result_summary["stop_reason"] == "cancelled"
    assert payload["authority_split"]["scheduler_state_mutated"] is False
    assert read_scheduler_state_snapshot(snapshot_path).tasks["task-a"].state == "proposed"
    assert not event_log_path.exists()


def test_scheduler_daemon_harness_drains_fake_runtime_until_no_ready_tasks(tmp_path) -> None:
    control_path = tmp_path / "scheduler-daemon-control.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(tasks={"task-a": _scheduled_task("task-a", output_artifact_id="task-a:result")}),
        snapshot_path,
    )
    apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="start",
            daemon_id="daemon-1",
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            timestamp="100",
        )
    )

    result = run_scheduler_daemon_harness(
        SchedulerDaemonHarnessRequest(
            control_path=control_path,
            max_cycles=3,
            stop_policy=SchedulerDaemonLoopStopPolicy(max_ticks=2, max_runs_per_tick=1),
            timestamp="110",
        )
    )
    payload = result.to_json_dict()

    assert result.stop_reason == "no_ready_tasks"
    assert result.cycle_count == 1
    assert result.total_run_count == 1
    assert payload["authority_split"]["starts_os_service"] is False
    assert payload["authority_split"]["scheduler_projection_refreshed"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert payload["cycles"][0]["loop_stop_reason"] == "no_ready_tasks"
    assert read_scheduler_state_snapshot(snapshot_path).tasks["task-a"].state == "complete"


def test_scheduler_daemon_harness_stops_paused_without_scheduler_mutation(tmp_path) -> None:
    control_path = tmp_path / "scheduler-daemon-control.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(tasks={"task-a": _scheduled_task("task-a", output_artifact_id="task-a:result")}),
        snapshot_path,
    )
    apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="start",
            daemon_id="daemon-1",
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            timestamp="100",
        )
    )
    apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="pause",
            timestamp="101",
        )
    )

    result = run_scheduler_daemon_harness(
        SchedulerDaemonHarnessRequest(
            control_path=control_path,
            max_cycles=2,
            stop_policy=SchedulerDaemonLoopStopPolicy(max_ticks=2, max_runs_per_tick=1),
            timestamp="110",
        )
    )

    assert result.stop_reason == "paused"
    assert result.cycles[0].skipped is True
    assert read_scheduler_state_snapshot(snapshot_path).tasks["task-a"].state == "proposed"
    assert not event_log_path.exists()


def test_scheduler_daemon_harness_stops_shutdown_without_scheduler_mutation(tmp_path) -> None:
    control_path = tmp_path / "scheduler-daemon-control.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(tasks={"task-a": _scheduled_task("task-a", output_artifact_id="task-a:result")}),
        snapshot_path,
    )
    apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="start",
            daemon_id="daemon-1",
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            timestamp="100",
        )
    )
    apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="shutdown",
            timestamp="101",
        )
    )

    result = run_scheduler_daemon_harness(
        SchedulerDaemonHarnessRequest(
            control_path=control_path,
            max_cycles=2,
            stop_policy=SchedulerDaemonLoopStopPolicy(max_ticks=2, max_runs_per_tick=1),
            timestamp="110",
        )
    )

    assert result.stop_reason == "stopped"
    assert result.cycles[0].skipped is True
    assert read_scheduler_state_snapshot(snapshot_path).tasks["task-a"].state == "proposed"
    assert not event_log_path.exists()


def test_scheduler_daemon_harness_consumes_cancelling_lifecycle(tmp_path) -> None:
    control_path = tmp_path / "scheduler-daemon-control.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(tasks={"task-a": _scheduled_task("task-a", output_artifact_id="task-a:result")}),
        snapshot_path,
    )
    apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="start",
            daemon_id="daemon-1",
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            timestamp="100",
        )
    )
    apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="cancel",
            timestamp="101",
        )
    )

    result = run_scheduler_daemon_harness(
        SchedulerDaemonHarnessRequest(
            control_path=control_path,
            max_cycles=2,
            stop_policy=SchedulerDaemonLoopStopPolicy(max_ticks=2, max_runs_per_tick=1),
            timestamp="110",
        )
    )
    control = read_scheduler_daemon_lifecycle_control(control_path)

    assert result.stop_reason == "cancelled"
    assert result.cycles[0].skipped is True
    assert control.state == "cancelled"
    assert read_scheduler_state_snapshot(snapshot_path).tasks["task-a"].state == "proposed"


def test_scheduler_daemon_harness_zero_cycles_does_not_inspect_or_mutate(tmp_path) -> None:
    control_path = tmp_path / "missing-control.json"

    result = run_scheduler_daemon_harness(
        SchedulerDaemonHarnessRequest(
            control_path=control_path,
            max_cycles=0,
            stop_policy=SchedulerDaemonLoopStopPolicy(max_ticks=2, max_runs_per_tick=1),
            timestamp="110",
        )
    )

    assert result.stop_reason == "max_cycles_reached"
    assert result.stop_detail == "max_cycles is 0"
    assert result.cycles == ()
    assert not control_path.exists()


def test_scheduler_daemon_harness_policy_cancelled_preflight_does_not_read_control(tmp_path) -> None:
    control_path = tmp_path / "missing-control.json"

    result = run_scheduler_daemon_harness_with_policy(
        SchedulerDaemonHarnessRequest(
            control_path=control_path,
            max_cycles=2,
            timestamp="110",
        ),
        SchedulerDaemonHarnessPolicy(cancelled=True, max_attempts=2),
    )
    payload = result.to_json_dict()

    assert result.stop_reason == "cancelled"
    assert result.attempt_count == 0
    assert payload["authority_split"]["starts_os_service"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert not control_path.exists()


def test_scheduler_daemon_harness_policy_deadline_preflight_does_not_mutate_scheduler(tmp_path) -> None:
    control_path = tmp_path / "scheduler-daemon-control.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(tasks={"task-a": _scheduled_task("task-a", output_artifact_id="task-a:result")}),
        snapshot_path,
    )
    apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="start",
            daemon_id="daemon-1",
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            timestamp="100",
        )
    )

    result = run_scheduler_daemon_harness_with_policy(
        SchedulerDaemonHarnessRequest(
            control_path=control_path,
            max_cycles=2,
            timestamp="110",
        ),
        SchedulerDaemonHarnessPolicy(
            deadline_epoch_seconds=200,
            now_epoch_seconds=200,
            max_attempts=2,
        ),
    )

    assert result.stop_reason == "deadline_exceeded"
    assert result.attempt_count == 0
    assert read_scheduler_state_snapshot(snapshot_path).tasks["task-a"].state == "proposed"
    assert not event_log_path.exists()


def test_scheduler_daemon_harness_policy_retries_explicit_retryable_stop_reason(tmp_path) -> None:
    control_path = tmp_path / "scheduler-daemon-control.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(tasks={"task-a": _scheduled_task("task-a", output_artifact_id="task-a:result")}),
        snapshot_path,
    )
    apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="start",
            daemon_id="daemon-1",
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            timestamp="100",
        )
    )
    apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="pause",
            timestamp="101",
        )
    )

    result = run_scheduler_daemon_harness_with_policy(
        SchedulerDaemonHarnessRequest(
            control_path=control_path,
            max_cycles=1,
            timestamp="110",
        ),
        SchedulerDaemonHarnessPolicy(
            max_attempts=2,
            retry_stop_reasons=("paused",),
        ),
    )

    assert result.stop_reason == "max_attempts_reached"
    assert result.attempt_count == 2
    assert all(attempt.retryable for attempt in result.attempts)
    assert [attempt.harness.stop_reason for attempt in result.attempts] == ["paused", "paused"]
    assert read_scheduler_state_snapshot(snapshot_path).tasks["task-a"].state == "proposed"
    assert not event_log_path.exists()


def test_scheduler_daemon_harness_policy_does_not_retry_non_retryable_stop_reason(tmp_path) -> None:
    control_path = tmp_path / "scheduler-daemon-control.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(tasks={"task-a": _scheduled_task("task-a", output_artifact_id="task-a:result")}),
        snapshot_path,
    )
    apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="start",
            daemon_id="daemon-1",
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            timestamp="100",
        )
    )

    result = run_scheduler_daemon_harness_with_policy(
        SchedulerDaemonHarnessRequest(
            control_path=control_path,
            max_cycles=2,
            stop_policy=SchedulerDaemonLoopStopPolicy(max_ticks=2, max_runs_per_tick=1),
            timestamp="110",
        ),
        SchedulerDaemonHarnessPolicy(
            max_attempts=3,
            retry_stop_reasons=("paused",),
        ),
    )

    assert result.stop_reason == "harness_completed"
    assert result.attempt_count == 1
    assert result.attempts[0].retryable is False
    assert result.attempts[0].harness.stop_reason == "no_ready_tasks"
    assert read_scheduler_state_snapshot(snapshot_path).tasks["task-a"].state == "complete"


def test_scheduler_daemon_supervisor_cancelled_preflight_skips_control_read(tmp_path) -> None:
    control_path = tmp_path / "missing-control.json"

    result = run_scheduler_daemon_supervisor_step(
        SchedulerDaemonSupervisorRequest(
            supervisor_id="supervisor-1",
            session_id="session-1",
            run_id="run-1",
            host_id="host-1",
            requested_by="agent:test",
            cancellation_source="operator",
            cancellation_reason="manual stop",
            harness_request=SchedulerDaemonHarnessRequest(
                control_path=control_path,
                max_cycles=2,
                timestamp="110",
            ),
            policy=SchedulerDaemonHarnessPolicy(cancelled=True, max_attempts=2),
            status_readback_at="111",
        )
    )
    payload = result.to_json_dict()

    assert result.stop_reason == "cancelled"
    assert result.attempted_harness is False
    assert result.attempt_count == 0
    assert "cancelled by operator" in result.stop_detail
    assert payload["authority_split"]["starts_os_service"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert payload["status_before"]["control_exists"] is False
    assert "readback skipped" in payload["status_before"]["readback_error"]
    assert not control_path.exists()


def test_scheduler_daemon_supervisor_deadline_preflight_skips_scheduler_mutation(tmp_path) -> None:
    control_path = tmp_path / "scheduler-daemon-control.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(tasks={"task-a": _scheduled_task("task-a", output_artifact_id="task-a:result")}),
        snapshot_path,
    )
    apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="start",
            daemon_id="daemon-1",
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            timestamp="100",
        )
    )

    result = run_scheduler_daemon_supervisor_step(
        SchedulerDaemonSupervisorRequest(
            supervisor_id="supervisor-1",
            harness_request=SchedulerDaemonHarnessRequest(
                control_path=control_path,
                max_cycles=2,
                timestamp="110",
            ),
            policy=SchedulerDaemonHarnessPolicy(
                deadline_epoch_seconds=200,
                now_epoch_seconds=200,
                max_attempts=2,
            ),
            status_readback_at="201",
        )
    )
    payload = result.to_json_dict()

    assert result.stop_reason == "deadline_exceeded"
    assert result.attempted_harness is False
    assert result.status_before.control_exists is False
    assert "deadline exceeded" in result.stop_detail
    assert "readback skipped" in payload["status_after"]["readback_error"]
    assert read_scheduler_state_snapshot(snapshot_path).tasks["task-a"].state == "proposed"
    assert not event_log_path.exists()


def test_scheduler_daemon_supervisor_runs_policy_harness_and_reads_status(tmp_path) -> None:
    control_path = tmp_path / "scheduler-daemon-control.json"
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(tasks={"task-a": _scheduled_task("task-a", output_artifact_id="task-a:result")}),
        snapshot_path,
    )
    apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="start",
            daemon_id="daemon-1",
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            run_id="lifecycle-run-1",
            timestamp="100",
        )
    )

    result = run_scheduler_daemon_supervisor_step(
        SchedulerDaemonSupervisorRequest(
            supervisor_id="supervisor-1",
            session_id="session-1",
            run_id="supervisor-run-1",
            host_id="host-1",
            requested_by="agent:test",
            harness_request=SchedulerDaemonHarnessRequest(
                control_path=control_path,
                max_cycles=2,
                stop_policy=SchedulerDaemonLoopStopPolicy(max_ticks=2, max_runs_per_tick=1),
                timestamp="110",
            ),
            policy=SchedulerDaemonHarnessPolicy(max_attempts=2, retry_stop_reasons=("paused",)),
            status_readback_at="111",
            metadata={"purpose": "test"},
        )
    )
    payload = result.to_json_dict()

    assert result.stop_reason == "harness_completed"
    assert result.attempted_harness is True
    assert result.attempt_count == 1
    assert result.total_run_count == 1
    assert result.status_before.lifecycle_state == "running"
    assert result.status_before.queue_summary["task_state_counts"] == {"proposed": 1}
    assert result.status_after.lifecycle_state == "running"
    assert result.status_after.queue_summary["task_state_counts"] == {"complete": 1}
    assert payload["harness_policy_result"]["attempts"][0]["harness"]["stop_reason"] == "no_ready_tasks"
    assert payload["metadata"] == {"purpose": "test"}
    assert payload["authority_split"]["starts_background_process"] is False
    assert payload["authority_split"]["scheduler_projection_refreshed"] is False


def test_scheduler_daemon_supervisor_status_readback_reports_queue_error(tmp_path) -> None:
    control_path = tmp_path / "scheduler-daemon-control.json"
    snapshot_path = tmp_path / "missing-scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    apply_scheduler_daemon_lifecycle_action(
        SchedulerDaemonLifecycleRequest(
            control_path=control_path,
            action="start",
            daemon_id="daemon-1",
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            timestamp="100",
        )
    )

    result = run_scheduler_daemon_supervisor_step(
        SchedulerDaemonSupervisorRequest(
            supervisor_id="supervisor-1",
            harness_request=SchedulerDaemonHarnessRequest(
                control_path=control_path,
                max_cycles=0,
                timestamp="110",
            ),
            policy=SchedulerDaemonHarnessPolicy(max_attempts=1),
            status_readback_at="111",
        )
    )
    payload = result.to_json_dict()

    assert result.stop_reason == "harness_completed"
    assert result.status_before.control_exists is True
    assert result.status_before.lifecycle_state == "running"
    assert result.status_before.queue_summary == {}
    assert "failed to read scheduler queue" in result.status_before.readback_error
    assert payload["status_before"]["readback_error"].startswith("failed to read scheduler queue")
    assert payload["harness_policy_result"]["attempts"][0]["harness"]["stop_reason"] == "max_cycles_reached"


def test_scheduler_loop_evidence_writes_and_reads_summary(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    evidence_path = tmp_path / "evidence" / "scheduler-loop.json"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-a": _scheduled_task("task-a", output_artifact_id="task-a:result"),
            },
        ),
        snapshot_path,
    )
    loop_result = run_scheduler_daemon_loop(
        SchedulerDaemonLoopRequest(
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            stop_policy=SchedulerDaemonLoopStopPolicy(max_ticks=2, max_runs_per_tick=1),
            timestamp="2026-06-19T11:40:00+08:00",
        )
    )

    evidence = build_scheduler_loop_evidence(
        loop_result,
        evidence_id="loop-evidence",
        timestamp="2026-06-19T11:40:00+08:00",
        metadata={"surface": "test"},
    )
    written = write_scheduler_loop_evidence(evidence, evidence_path)
    summary = read_scheduler_loop_evidence_summary(evidence_path)
    payload = summary.to_json_dict()

    assert isinstance(evidence, SchedulerLoopEvidence)
    assert isinstance(summary, SchedulerLoopEvidenceSummary)
    assert written.evidence_path == evidence_path
    assert payload["product_type"] == "scheduler_loop_evidence"
    assert payload["schema_version"] == "1"
    assert payload["evidence_id"] == "loop-evidence"
    assert payload["runtime_provider"] == "fake"
    assert payload["tick_count"] == 1
    assert payload["total_run_count"] == 1
    assert payload["stop_reason"] == "no_ready_tasks"
    assert payload["scheduler_event_count"] == 3
    assert payload["final_queue_summary"]["completed_task_ids"] == ["task-a"]
    assert payload["authority_split"]["scheduler_projection_refreshed"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert "loop_result" not in payload

    loaded = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert loaded["loop_result"]["iterations"][0]["run_count"] == 1
    assert loaded["metadata"] == {"surface": "test"}


def test_scheduler_loop_evidence_summary_rejects_wrong_product_type(tmp_path) -> None:
    evidence_path = tmp_path / "loop-evidence.json"
    evidence_path.write_text(
        '{"product_type": "host_scheduler_run_evidence", "schema_version": "1"}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="product_type"):
        read_scheduler_loop_evidence_summary(evidence_path)


def test_host_scheduler_runner_fake_result_is_json_serializable(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-a": _scheduled_task(
                    "task-a",
                    output_artifact_id="task-a:result",
                ),
            },
        ),
        snapshot_path,
    )

    result = run_host_authorized_scheduler_once(
        HostSchedulerRunRequest(
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            runtime_config=RuntimeRegistryWiringConfig(
                providers=("fake",),
                timestamp="2026-06-17T19:00:00+08:00",
                host_invocation=RuntimeHostInvocation(
                    surface="host-authorized-adapter",
                    invocation_id="host-fake-run",
                    requested_providers=("fake",),
                    requested_by="host:test",
                ),
            ),
            timestamp="2026-06-17T19:00:00+08:00",
            history_summary={
                "source_log": {
                    "timestamp": "2026-06-17T18:59:00+08:00",
                    "action": "scheduler_task_batch_submitted",
                },
            },
        ),
        artifact_store=InMemoryArtifactVersionStore(),
    )
    payload = result.to_json_dict()

    assert isinstance(result, HostSchedulerRunResult)
    assert payload["ok"] is True
    assert payload["runtime_registry_providers"] == ["fake"]
    assert payload["runtime_host_surface"] == "host-authorized-adapter"
    assert payload["stop_reason"] == "no_ready_tasks"
    assert payload["run_count"] == 1
    assert payload["state_written"] is True
    assert payload["git_worktree_sandbox_opt_in"] is False
    assert payload["sandbox_allocation_evidence_written"] is False
    assert payload["sandbox_allocation_evidence_path"] == ""
    assert payload["local_trajectory_mutated"] is False
    assert payload["output_artifact_refs"] == [
        {
            "task_id": "task-a",
            "artifact_id": "task-a:result",
            "version": "v1",
        }
    ]
    assert payload["history_summary"]["source_log"]["action"] == "scheduler_task_batch_submitted"

    import json

    json.dumps(payload, ensure_ascii=False)
    assert read_scheduler_state_snapshot(snapshot_path).tasks["task-a"].state == "complete"


def test_host_scheduler_runner_git_worktree_opt_in_requires_paths(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(tasks={"task-1": _git_worktree_task()}),
        snapshot_path,
    )

    with pytest.raises(ValueError, match="workspace_root source repository"):
        run_host_authorized_scheduler_once(
            HostSchedulerRunRequest(
                snapshot_path=snapshot_path,
                event_log_path=event_log_path,
                runtime_config=RuntimeRegistryWiringConfig(
                    providers=("fake",),
                    host_invocation=RuntimeHostInvocation(
                        surface="host-authorized-adapter",
                        invocation_id="missing-workspace-root",
                        requested_providers=("fake",),
                    ),
                ),
                git_worktree_sandbox_root=tmp_path / "sandboxes",
                sandbox_allocation_evidence_id="missing-workspace-root",
            ),
            artifact_store=InMemoryArtifactVersionStore(),
        )

    with pytest.raises(ValueError, match="sandbox_allocation_evidence_id"):
        run_host_authorized_scheduler_once(
            HostSchedulerRunRequest(
                snapshot_path=snapshot_path,
                event_log_path=event_log_path,
                runtime_config=RuntimeRegistryWiringConfig(
                    providers=("fake",),
                    host_invocation=RuntimeHostInvocation(
                        surface="host-authorized-adapter",
                        invocation_id="missing-evidence-id",
                        requested_providers=("fake",),
                    ),
                ),
                workspace_root=str(tmp_path),
                git_worktree_sandbox_root=tmp_path / "sandboxes",
            ),
            artifact_store=InMemoryArtifactVersionStore(),
        )


def test_host_scheduler_runner_git_worktree_opt_in_writes_allocation_evidence(
    tmp_path,
) -> None:
    repo = _git_repo(tmp_path)
    task = _scheduled_task(
        "task-1",
        state="ready",
        edit_lease=EditScopeLease(
            lease_id="lease-1",
            task_id="task-1",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
        sandbox_profile=SandboxProfile(
            profile_id="worktree",
            profile_kind="git-worktree",
            mount_policy="lease-scoped",
        ),
        output_artifact_id="task-1:result",
    )
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    evidence_path = tmp_path / "evidence" / "allocation-receipts.json"
    write_scheduler_state_snapshot(
        _state_with_acquired_git_worktree_lease(task),
        snapshot_path,
    )

    result = run_host_authorized_scheduler_once(
        HostSchedulerRunRequest(
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            runtime_config=RuntimeRegistryWiringConfig(
                providers=("fake",),
                timestamp="2026-06-21T05:50:00+08:00",
                host_invocation=RuntimeHostInvocation(
                    surface="host-authorized-adapter",
                    invocation_id="host-git-worktree-run",
                    requested_providers=("fake",),
                    requested_by="host:test",
                ),
            ),
            workspace_root=str(repo),
            git_worktree_sandbox_root=tmp_path / "sandboxes",
            sandbox_allocation_evidence_id="allocation-receipts",
            sandbox_allocation_evidence_path=evidence_path,
            timestamp="2026-06-21T05:50:00+08:00",
        ),
        artifact_store=InMemoryArtifactVersionStore(),
    )
    payload = result.to_json_dict()
    summary = read_sandbox_allocation_receipt_evidence_summary(evidence_path)
    allocation = summary.allocations_by_task_id["task-1"]
    receipt = allocation.git_worktree_receipt

    assert payload["git_worktree_sandbox_opt_in"] is True
    assert payload["git_worktree_sandbox_root"] == str(tmp_path / "sandboxes")
    assert payload["sandbox_allocation_evidence_written"] is True
    assert payload["sandbox_allocation_evidence_path"] == str(evidence_path)
    assert payload["authority_split"]["sandbox_provider_authority"] == "host-explicit-opt-in"
    assert result.sandbox_allocation_evidence_write is not None
    assert summary.evidence_id == "allocation-receipts"
    assert summary.allocation_count == 1
    assert summary.metadata["git_worktree_sandbox_opt_in"] is True
    assert allocation.provider == "git-worktree"
    assert allocation.state == "allocated"
    assert allocation.workspace_root == str(repo)
    assert allocation.visible_mounts == ("src/app.py",)
    assert allocation.cleanup_required is True
    assert receipt is not None
    assert receipt.source_repository_root == str(repo)
    assert receipt.sandbox_root == str(tmp_path / "sandboxes")
    assert receipt.cleanup_state == "required"
    assert receipt.allocation.returncode == 0
    assert Path(receipt.worktree_path).exists()
    assert read_scheduler_state_snapshot(snapshot_path).tasks["task-1"].state == "complete"

    GitWorktreeSandboxProvider(tmp_path / "sandboxes").cleanup(allocation)


def test_host_scheduler_run_evidence_writes_contract_shape(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    evidence_path = tmp_path / "evidence" / "host-run.json"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-a": _scheduled_task(
                    "task-a",
                    output_artifact_id="task-a:result",
                ),
            },
        ),
        snapshot_path,
    )
    host_result = run_host_authorized_scheduler_once(
        HostSchedulerRunRequest(
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            runtime_config=RuntimeRegistryWiringConfig(
                providers=("fake",),
                timestamp="2026-06-17T20:00:00+08:00",
                host_invocation=RuntimeHostInvocation(
                    surface="host-authorized-adapter",
                    invocation_id="host-fake-evidence",
                    requested_providers=("fake",),
                    requested_by="host:test",
                    reason="write evidence contract",
                ),
            ),
            timestamp="2026-06-17T20:00:00+08:00",
        ),
        artifact_store=InMemoryArtifactVersionStore(),
    )

    evidence = build_host_scheduler_run_evidence(
        host_result,
        evidence_id="evidence-fake",
        timestamp="2026-06-17T20:00:00+08:00",
    )
    written = write_host_scheduler_run_evidence(evidence, evidence_path)
    payload = written.to_json_dict()

    assert isinstance(evidence, HostSchedulerRunEvidence)
    assert written.evidence_path == evidence_path
    assert payload["product_type"] == "host_scheduler_run_evidence"
    assert payload["schema_version"] == "1"
    assert payload["evidence_id"] == "evidence-fake"
    assert payload["runtime_providers"] == ["fake"]
    assert payload["host_invocation"] == {
        "surface": "host-authorized-adapter",
        "invocation_id": "host-fake-evidence",
        "requested_by": "host:test",
        "reason": "write evidence contract",
    }
    assert payload["run_count"] == 1
    assert payload["stop_reason"] == "no_ready_tasks"
    assert payload["output_artifact_refs"] == [
        {
            "task_id": "task-a",
            "artifact_id": "task-a:result",
            "version": "v1",
        }
    ]
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert payload["history_summary"]["scheduler_event_log_path"] == str(event_log_path)

    import json

    loaded = json.loads(evidence_path.read_text(encoding="utf-8"))
    assert loaded["host_result"]["authority_split"]["scheduler_projection_role"] == "read-only-view"


def test_host_scheduler_run_evidence_summary_reads_ui_safe_contract(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    evidence_path = tmp_path / "evidence" / "host-run.json"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-a": _scheduled_task(
                    "task-a",
                    output_artifact_id="task-a:result",
                ),
            },
        ),
        snapshot_path,
    )
    host_result = run_host_authorized_scheduler_once(
        HostSchedulerRunRequest(
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            runtime_config=RuntimeRegistryWiringConfig(
                providers=("fake",),
                timestamp="2026-06-17T20:05:00+08:00",
                host_invocation=RuntimeHostInvocation(
                    surface="host-authorized-adapter",
                    invocation_id="host-fake-summary",
                    requested_providers=("fake",),
                    requested_by="host:test",
                    reason="read evidence summary",
                ),
            ),
            timestamp="2026-06-17T20:05:00+08:00",
        ),
        artifact_store=InMemoryArtifactVersionStore(),
    )
    write_host_scheduler_run_evidence(
        build_host_scheduler_run_evidence(
            host_result,
            evidence_id="evidence-summary",
            timestamp="2026-06-17T20:05:00+08:00",
        ),
        evidence_path,
    )

    summary = read_host_scheduler_run_evidence_summary(evidence_path)
    payload = summary.to_json_dict()

    assert isinstance(summary, HostSchedulerRunEvidenceSummary)
    assert payload["evidence_id"] == "evidence-summary"
    assert payload["runtime_providers"] == ["fake"]
    assert payload["host_invocation"] == {
        "surface": "host-authorized-adapter",
        "invocation_id": "host-fake-summary",
        "requested_by": "host:test",
        "reason": "read evidence summary",
    }
    assert payload["run_count"] == 1
    assert payload["output_artifact_refs"] == [
        {
            "task_id": "task-a",
            "artifact_id": "task-a:result",
            "version": "v1",
        }
    ]
    assert "host_result" not in payload


def test_host_scheduler_run_evidence_summary_rejects_wrong_product_type(tmp_path) -> None:
    evidence_path = tmp_path / "evidence.json"
    evidence_path.write_text(
        '{"product_type": "wrong", "schema_version": "1"}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="product_type"):
        read_host_scheduler_run_evidence_summary(evidence_path)


def test_host_scheduler_run_evidence_summaries_missing_directory_is_empty(tmp_path) -> None:
    assert read_host_scheduler_run_evidence_summaries(tmp_path / "missing") == ()


def test_host_scheduler_runner_mock_qoder_requires_host_authorization(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-q": _scheduled_task(
                    "task-q",
                    agent=AgentSpec(agent_id="agent:qoder", runtime_provider="qoder"),
                    output_artifact_id="task-q:result",
                ),
            },
        ),
        snapshot_path,
    )

    with pytest.raises(ValueError, match="fake-only"):
        run_host_authorized_scheduler_once(
            HostSchedulerRunRequest(
                snapshot_path=snapshot_path,
                event_log_path=event_log_path,
                runtime_config=RuntimeRegistryWiringConfig(
                    providers=("qoder",),
                    host_invocation=RuntimeHostInvocation(
                        surface="cli-scheduler-run-once",
                        invocation_id="bad-qoder-host",
                        requested_providers=("qoder",),
                    ),
                    qoder_permission_grant=RuntimeProviderPermissionGrant(
                        grant_id="grant-qoder",
                        provider="qoder",
                        approved_by="host:test",
                        approved_at="2026-06-17T19:01:00+08:00",
                        allow_sdk_client=True,
                    ),
                ),
            ),
            qoder_query_client=_RecordingQoderClient(QoderQueryResult(summary="unused")),
        )

    with pytest.raises(ValueError, match="RuntimeProviderPermissionGrant"):
        run_host_authorized_scheduler_once(
            HostSchedulerRunRequest(
                snapshot_path=snapshot_path,
                event_log_path=event_log_path,
                runtime_config=RuntimeRegistryWiringConfig(
                    providers=("qoder",),
                    host_invocation=RuntimeHostInvocation(
                        surface="host-authorized-adapter",
                        invocation_id="missing-grant",
                        requested_providers=("qoder",),
                    ),
                ),
            ),
            qoder_query_client=_RecordingQoderClient(QoderQueryResult(summary="unused")),
        )

    result = run_host_authorized_scheduler_once(
        HostSchedulerRunRequest(
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            runtime_config=RuntimeRegistryWiringConfig(
                providers=("qoder",),
                timestamp="2026-06-17T19:02:00+08:00",
                host_invocation=RuntimeHostInvocation(
                    surface="host-authorized-adapter",
                    invocation_id="host-qoder-run",
                    requested_providers=("qoder",),
                    requested_by="host:test",
                ),
                qoder_permission_grant=RuntimeProviderPermissionGrant(
                    grant_id="grant-qoder",
                    provider="qoder",
                    approved_by="host:test",
                    approved_at="2026-06-17T19:01:00+08:00",
                    allow_sdk_client=True,
                ),
            ),
            timestamp="2026-06-17T19:02:00+08:00",
        ),
        qoder_query_client=_RecordingQoderClient(
            QoderQueryResult(summary="Qoder host adapter complete.", output_text="done")
        ),
    )
    payload = result.to_json_dict()

    assert result.run.runtime_registry_providers == ("qoder",)
    assert result.run.runtime_host_surface == "host-authorized-adapter"
    assert payload["runtime_registry_providers"] == ["qoder"]
    assert payload["host_invocation_id"] == "host-qoder-run"
    assert payload["run_count"] == 1
    assert payload["output_artifact_refs"] == [
        {
            "task_id": "task-q",
            "artifact_id": "task-q:result",
            "version": "v1",
        }
    ]
    assert read_scheduler_state_snapshot(snapshot_path).tasks["task-q"].state == "complete"


def test_host_scheduler_daemon_loop_fake_result_is_json_serializable(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-a": _scheduled_task("task-a", output_artifact_id="task-a:result"),
                "task-b": _scheduled_task("task-b", output_artifact_id="task-b:result"),
            },
            dependencies=(
                TaskDependency(
                    dependency_id="dep-a-b",
                    source_task_id="task-a",
                    target_task_id="task-b",
                    required_state="complete",
                ),
            ),
        ),
        snapshot_path,
    )

    result = run_host_authorized_scheduler_daemon_loop(
        HostSchedulerDaemonLoopRequest(
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            stop_policy=SchedulerDaemonLoopStopPolicy(
                max_ticks=3,
                max_runs_per_tick=1,
            ),
            runtime_config=RuntimeRegistryWiringConfig(
                providers=("fake",),
                timestamp="2026-06-19T15:20:00+08:00",
                host_invocation=RuntimeHostInvocation(
                    surface="host-authorized-adapter",
                    invocation_id="host-loop-fake",
                    requested_providers=("fake",),
                    requested_by="host:test",
                ),
            ),
            timestamp="2026-06-19T15:20:00+08:00",
            metadata={"scenario": "fake-host-loop"},
        ),
        artifact_store=InMemoryArtifactVersionStore(),
    )
    payload = result.to_json_dict()

    assert isinstance(result, HostSchedulerDaemonLoopResult)
    assert payload["ok"] is True
    assert payload["runtime_registry_providers"] == ["fake"]
    assert payload["runtime_host_surface"] == "host-authorized-adapter"
    assert payload["host_invocation_id"] == "host-loop-fake"
    assert payload["tick_count"] == 2
    assert payload["total_run_count"] == 2
    assert payload["stop_reason"] == "no_ready_tasks"
    assert payload["final_queue_summary"]["completed_task_ids"] == ["task-a", "task-b"]
    assert payload["evidence_written"] is False
    assert payload["authority_split"]["runtime_registry_authority"] == "host_runtime_wiring"
    assert payload["authority_split"]["scheduler_projection_refreshed"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False

    import json

    json.dumps(payload, ensure_ascii=False)
    written = read_scheduler_state_snapshot(snapshot_path)
    assert written.tasks["task-a"].state == "complete"
    assert written.tasks["task-b"].state == "complete"


def test_host_scheduler_daemon_loop_git_worktree_opt_in_requires_paths(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(tasks={"task-1": _git_worktree_task()}),
        snapshot_path,
    )

    with pytest.raises(ValueError, match="workspace_root source repository"):
        run_host_authorized_scheduler_daemon_loop(
            HostSchedulerDaemonLoopRequest(
                snapshot_path=snapshot_path,
                event_log_path=event_log_path,
                runtime_config=RuntimeRegistryWiringConfig(
                    providers=("fake",),
                    host_invocation=RuntimeHostInvocation(
                        surface="host-authorized-adapter",
                        invocation_id="missing-loop-workspace-root",
                        requested_providers=("fake",),
                    ),
                ),
                git_worktree_sandbox_root=tmp_path / "sandboxes",
                sandbox_allocation_evidence_id="missing-loop-workspace-root",
            ),
            artifact_store=InMemoryArtifactVersionStore(),
        )

    with pytest.raises(ValueError, match="sandbox_allocation_evidence_id"):
        run_host_authorized_scheduler_daemon_loop(
            HostSchedulerDaemonLoopRequest(
                snapshot_path=snapshot_path,
                event_log_path=event_log_path,
                runtime_config=RuntimeRegistryWiringConfig(
                    providers=("fake",),
                    host_invocation=RuntimeHostInvocation(
                        surface="host-authorized-adapter",
                        invocation_id="missing-loop-evidence-id",
                        requested_providers=("fake",),
                    ),
                ),
                workspace_root=str(tmp_path),
                git_worktree_sandbox_root=tmp_path / "sandboxes",
            ),
            artifact_store=InMemoryArtifactVersionStore(),
        )


def test_host_scheduler_daemon_loop_git_worktree_opt_in_writes_allocation_evidence(
    tmp_path,
) -> None:
    repo = _git_repo(tmp_path)
    task = _workflow_git_worktree_task()
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    evidence_path = tmp_path / ".codex" / "scheduler" / "evidence" / "daemon-allocation-receipts.json"
    write_scheduler_state_snapshot(
        _state_with_acquired_git_worktree_lease(task),
        snapshot_path,
    )

    result = run_host_authorized_scheduler_daemon_loop(
        HostSchedulerDaemonLoopRequest(
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            stop_policy=SchedulerDaemonLoopStopPolicy(max_ticks=2, max_runs_per_tick=1),
            runtime_config=RuntimeRegistryWiringConfig(
                providers=("fake",),
                timestamp="2026-06-21T08:10:00+08:00",
                host_invocation=RuntimeHostInvocation(
                    surface="host-authorized-adapter",
                    invocation_id="host-loop-git-worktree",
                    requested_providers=("fake",),
                    requested_by="host:test",
                ),
            ),
            workspace_root=str(repo),
            git_worktree_sandbox_root=tmp_path / "sandboxes",
            sandbox_allocation_evidence_id="daemon-allocation-receipts",
            sandbox_allocation_evidence_path=evidence_path,
            timestamp="2026-06-21T08:10:00+08:00",
            metadata={"scenario": "daemon-git-worktree-opt-in"},
        ),
        artifact_store=InMemoryArtifactVersionStore(),
    )
    payload = result.to_json_dict()
    summary = read_sandbox_allocation_receipt_evidence_summary(evidence_path)
    allocation = summary.allocations_by_task_id["task-1"]
    receipt = allocation.git_worktree_receipt
    host_evidence = build_host_evidence_presentation(
        read_host_evidence_bundle(tmp_path)
    ).to_json_dict()
    host_card = host_evidence["cards"][0]

    assert payload["git_worktree_sandbox_opt_in"] is True
    assert payload["git_worktree_sandbox_root"] == str(tmp_path / "sandboxes")
    assert payload["sandbox_allocation_evidence_written"] is True
    assert payload["sandbox_allocation_evidence_path"] == str(evidence_path)
    assert payload["authority_split"]["sandbox_provider_authority"] == "host-explicit-opt-in"
    assert payload["authority_split"]["sandbox_allocation_evidence_written"] is True
    assert result.sandbox_allocation_evidence_write is not None
    assert summary.evidence_id == "daemon-allocation-receipts"
    assert summary.allocation_count == 1
    assert summary.metadata["surface"] == "host-authorized-scheduler-daemon-loop"
    assert summary.metadata["host_invocation_id"] == "host-loop-git-worktree"
    assert summary.metadata["git_worktree_sandbox_opt_in"] is True
    assert summary.metadata["scenario"] == "daemon-git-worktree-opt-in"
    assert summary.authority_split["scheduler_state_read"] is True
    assert summary.authority_split["scheduler_state_mutated"] is True
    assert summary.authority_split["runtime_provider_executed"] is True
    assert summary.authority_split["sandbox_provider_executed"] is True
    assert summary.authority_split["cleanup_executed"] is False
    assert allocation.provider == "git-worktree"
    assert allocation.state == "allocated"
    assert allocation.workspace_root == str(repo)
    assert allocation.visible_mounts == ("README.md", "src/app.py")
    assert allocation.cleanup_required is True
    assert receipt is not None
    assert receipt.source_repository_root == str(repo)
    assert receipt.sandbox_root == str(tmp_path / "sandboxes")
    assert receipt.cleanup_state == "required"
    assert receipt.allocation.returncode == 0
    assert Path(receipt.worktree_path).exists()
    assert read_scheduler_state_snapshot(snapshot_path).tasks["task-1"].state == "complete"
    assert host_evidence["status"] == "degraded"
    assert host_card["id"] == "daemon-allocation-receipts"
    assert host_card["title"] == "Sandbox cleanup evidence daemon-allocation-receipts"
    assert host_card["status"] == "partial"
    assert host_card["host_surface"] == "host-authorized-scheduler-daemon-loop"
    assert host_card["runtime_providers"] == ["git-worktree"]
    assert {"label": "Cleanup required", "value": "1"} in host_card["key_facts"]
    assert {"label": "Sandbox provider executed", "value": "true"} in host_card["authority_clues"]
    assert {"label": "Evidence written", "value": "true"} in host_card["authority_clues"]

    GitWorktreeSandboxProvider(tmp_path / "sandboxes").cleanup(allocation)


def test_host_sandbox_receipt_workflow_run_once_cleans_and_reads_back(
    tmp_path,
) -> None:
    repo = _git_repo(tmp_path)
    task = _workflow_git_worktree_task()
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    allocation_path = tmp_path / ".codex" / "scheduler" / "evidence" / "workflow-run-allocation.json"
    cleanup_path = tmp_path / ".codex" / "scheduler" / "evidence" / "workflow-run-cleanup.json"
    write_scheduler_state_snapshot(
        _state_with_acquired_git_worktree_lease(task),
        snapshot_path,
    )

    result = run_host_sandbox_receipt_workflow(
        HostSandboxReceiptWorkflowRequest(
            project_root=tmp_path,
            mode="run_once",
            run_once_request=HostSchedulerRunRequest(
                snapshot_path=snapshot_path,
                event_log_path=event_log_path,
                runtime_config=RuntimeRegistryWiringConfig(
                    providers=("fake",),
                    timestamp="2026-06-21T08:45:00+08:00",
                    host_invocation=RuntimeHostInvocation(
                        surface="host-authorized-adapter",
                        invocation_id="workflow-run-once",
                        requested_providers=("fake",),
                        requested_by="host:test",
                    ),
                ),
                workspace_root=str(repo),
                git_worktree_sandbox_root=tmp_path / "sandboxes",
                sandbox_allocation_evidence_id="workflow-run-allocation",
                sandbox_allocation_evidence_path=allocation_path,
                timestamp="2026-06-21T08:45:00+08:00",
            ),
            cleanup=True,
            cleanup_evidence_id="workflow-run-cleanup",
            cleanup_evidence_path=cleanup_path,
            timestamp="2026-06-21T08:45:00+08:00",
        ),
        artifact_store=InMemoryArtifactVersionStore(),
    )
    payload = result.to_json_dict()
    allocation_summary = read_sandbox_allocation_receipt_evidence_summary(allocation_path)
    cleanup_summary = read_sandbox_allocation_receipt_evidence_summary(cleanup_path)
    allocation = allocation_summary.allocations_by_task_id["task-1"]
    cleaned = cleanup_summary.allocations_by_task_id["task-1"]
    allocation_card = payload["allocation_readback_presentation"]["cards"][0]
    cleanup_card = payload["cleanup_readback_presentation"]["cards"][0]

    assert payload["ok"] is True
    assert payload["workflow_surface"] == "host-sandbox-receipt-workflow"
    assert payload["workflow_mode"] == "run_once"
    assert payload["paths"]["allocation_evidence_path"] == str(allocation_path)
    assert payload["paths"]["cleanup_evidence_path"] == str(cleanup_path)
    assert [step["name"] for step in payload["steps"]] == [
        "runHostSchedulerOnce",
        "readAllocationEvidence",
        "cleanupReceipts",
        "readCleanupEvidence",
    ]
    assert payload["authority_split"]["cleanup_requested"] is True
    assert payload["authority_split"]["cleanup_executed"] is True
    assert payload["authority_split"]["cleanup_evidence_written"] is True
    assert payload["run_result"]["sandbox_allocation_evidence_written"] is True
    assert payload["cleanup_result"]["cleaned_allocation_ids"] == [allocation.allocation_id]
    assert allocation.cleanup_required is True
    assert cleaned.cleanup_required is False
    assert cleaned.git_worktree_receipt is not None
    assert cleaned.git_worktree_receipt.cleanup_state == "completed"
    assert not Path(cleaned.git_worktree_receipt.worktree_path).exists()
    assert allocation_card["status"] == "partial"
    assert cleanup_card["status"] == "completed"
    assert cleanup_card["stop_reason"] == "cleanup_settled"
    assert read_scheduler_state_snapshot(snapshot_path).tasks["task-1"].state == "complete"

    json.dumps(payload, ensure_ascii=False)


def test_host_sandbox_receipt_workflow_daemon_loop_cleans_and_reads_back(
    tmp_path,
) -> None:
    repo = _git_repo(tmp_path)
    task = _workflow_git_worktree_task()
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    allocation_path = tmp_path / ".codex" / "scheduler" / "evidence" / "workflow-loop-allocation.json"
    cleanup_path = tmp_path / ".codex" / "scheduler" / "evidence" / "workflow-loop-cleanup.json"
    write_scheduler_state_snapshot(
        _state_with_acquired_git_worktree_lease(task),
        snapshot_path,
    )

    result = run_host_sandbox_receipt_workflow(
        HostSandboxReceiptWorkflowRequest(
            project_root=tmp_path,
            mode="daemon_loop",
            daemon_loop_request=HostSchedulerDaemonLoopRequest(
                snapshot_path=snapshot_path,
                event_log_path=event_log_path,
                stop_policy=SchedulerDaemonLoopStopPolicy(max_ticks=2, max_runs_per_tick=1),
                runtime_config=RuntimeRegistryWiringConfig(
                    providers=("fake",),
                    timestamp="2026-06-21T08:50:00+08:00",
                    host_invocation=RuntimeHostInvocation(
                        surface="host-authorized-adapter",
                        invocation_id="workflow-daemon-loop",
                        requested_providers=("fake",),
                        requested_by="host:test",
                    ),
                ),
                workspace_root=str(repo),
                git_worktree_sandbox_root=tmp_path / "sandboxes",
                sandbox_allocation_evidence_id="workflow-loop-allocation",
                sandbox_allocation_evidence_path=allocation_path,
                timestamp="2026-06-21T08:50:00+08:00",
            ),
            cleanup=True,
            cleanup_evidence_id="workflow-loop-cleanup",
            cleanup_evidence_path=cleanup_path,
            timestamp="2026-06-21T08:50:00+08:00",
        ),
        artifact_store=InMemoryArtifactVersionStore(),
    )
    payload = result.to_json_dict()
    cleanup_summary = read_sandbox_allocation_receipt_evidence_summary(cleanup_path)
    cleaned = cleanup_summary.allocations_by_task_id["task-1"]

    assert payload["ok"] is True
    assert payload["workflow_mode"] == "daemon_loop"
    assert [step["name"] for step in payload["steps"]] == [
        "runHostSchedulerDaemonLoop",
        "readAllocationEvidence",
        "cleanupReceipts",
        "readCleanupEvidence",
    ]
    assert payload["run_result"]["sandbox_allocation_evidence_written"] is True
    assert payload["run_result"]["total_run_count"] == 1
    assert payload["allocation_readback_presentation"]["cards"][0]["status"] == "partial"
    assert payload["cleanup_readback_presentation"]["cards"][0]["status"] == "completed"
    assert payload["authority_split"]["host_daemon_loop_executed"] is True
    assert payload["authority_split"]["cleanup_executed"] is True
    assert cleaned.cleanup_required is False
    assert cleaned.git_worktree_receipt is not None
    assert cleaned.git_worktree_receipt.cleanup_state == "completed"
    assert read_scheduler_state_snapshot(snapshot_path).tasks["task-1"].state == "complete"


def test_host_sandbox_receipt_workflow_cleanup_outputs_require_cleanup_opt_in(
    tmp_path,
) -> None:
    with pytest.raises(ValueError, match="cleanup evidence output requires cleanup=True"):
        run_host_sandbox_receipt_workflow(
            HostSandboxReceiptWorkflowRequest(
                project_root=tmp_path,
                mode="run_once",
                run_once_request=HostSchedulerRunRequest(
                    snapshot_path=tmp_path / "scheduler-state.json",
                    event_log_path=tmp_path / "scheduler-events.jsonl",
                    workspace_root=str(tmp_path),
                    git_worktree_sandbox_root=tmp_path / "sandboxes",
                    sandbox_allocation_evidence_id="allocation",
                ),
                cleanup_evidence_path=tmp_path / "cleanup.json",
            )
        )


def test_host_scheduler_daemon_loop_mock_qoder_writes_scheduler_loop_evidence(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    evidence_path = tmp_path / "evidence" / "host-loop-qoder.json"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-q": _scheduled_task(
                    "task-q",
                    agent=AgentSpec(agent_id="agent:qoder", runtime_provider="qoder"),
                    output_artifact_id="task-q:result",
                ),
            },
        ),
        snapshot_path,
    )

    result = run_host_authorized_scheduler_daemon_loop(
        HostSchedulerDaemonLoopRequest(
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            stop_policy=SchedulerDaemonLoopStopPolicy(max_ticks=2, max_runs_per_tick=1),
            runtime_config=RuntimeRegistryWiringConfig(
                providers=("qoder",),
                timestamp="2026-06-19T15:30:00+08:00",
                host_invocation=RuntimeHostInvocation(
                    surface="host-authorized-adapter",
                    invocation_id="host-loop-qoder",
                    requested_providers=("qoder",),
                    requested_by="host:test",
                    reason="mock qoder daemon loop",
                ),
                qoder_permission_grant=RuntimeProviderPermissionGrant(
                    grant_id="grant-qoder",
                    provider="qoder",
                    approved_by="host:test",
                    approved_at="2026-06-19T15:29:00+08:00",
                    allow_sdk_client=True,
                ),
            ),
            evidence_id="host-loop:qoder",
            evidence_path=evidence_path,
            timestamp="2026-06-19T15:30:00+08:00",
            metadata={"scenario": "mock-qoder-host-loop"},
        ),
        qoder_query_client=_RecordingQoderClient(
            QoderQueryResult(summary="Qoder daemon loop completed.", output_text="done")
        ),
    )
    payload = result.to_json_dict()
    summary = read_scheduler_loop_evidence_summary(evidence_path)

    assert payload["runtime_registry_providers"] == ["qoder"]
    assert payload["runtime_provider"] == "qoder"
    assert payload["runtime_host_surface"] == "host-authorized-adapter"
    assert payload["host_invocation_id"] == "host-loop-qoder"
    assert payload["tick_count"] == 1
    assert payload["total_run_count"] == 1
    assert payload["stop_reason"] == "no_ready_tasks"
    assert payload["evidence_written"] is True
    assert payload["evidence_path"] == str(evidence_path)
    assert payload["authority_split"]["evidence_written"] is True
    assert evidence_path.exists()
    assert summary.evidence_id == "host-loop:qoder"
    assert summary.runtime_provider == "qoder"
    assert summary.metadata["surface"] == "host-authorized-scheduler-daemon-loop"
    assert summary.metadata["runtime_host_surface"] == "host-authorized-adapter"
    assert summary.metadata["host_invocation_id"] == "host-loop-qoder"
    assert summary.metadata["scenario"] == "mock-qoder-host-loop"
    assert read_scheduler_state_snapshot(snapshot_path).tasks["task-q"].state == "complete"


def test_host_scheduler_daemon_loop_default_evidence_path_uses_workspace_root(tmp_path) -> None:
    project = tmp_path / "project"
    snapshot_path = project / ".codex" / "scheduler" / "scheduler-state.json"
    event_log_path = project / ".codex" / "scheduler" / "scheduler-events.jsonl"
    evidence_path = project / ".codex" / "scheduler" / "evidence" / "host-loop-default.json"
    write_scheduler_state_snapshot(SchedulerState(), snapshot_path)

    result = run_host_authorized_scheduler_daemon_loop(
        HostSchedulerDaemonLoopRequest(
            snapshot_path=snapshot_path,
            event_log_path=event_log_path,
            stop_policy=SchedulerDaemonLoopStopPolicy(max_ticks=0),
            runtime_config=RuntimeRegistryWiringConfig(
                providers=("fake",),
                host_invocation=RuntimeHostInvocation(
                    surface="host-authorized-adapter",
                    invocation_id="host-loop-default-path",
                    requested_providers=("fake",),
                ),
            ),
            evidence_id="host-loop:default",
        )
    )
    payload = result.to_json_dict()

    assert payload["evidence_written"] is True
    assert payload["evidence_path"] == str(evidence_path)
    assert evidence_path.exists()


def test_host_scheduler_daemon_loop_rejects_qoder_without_host_authorization(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-q": _scheduled_task(
                    "task-q",
                    agent=AgentSpec(agent_id="agent:qoder", runtime_provider="qoder"),
                ),
            },
        ),
        snapshot_path,
    )

    with pytest.raises(ValueError, match="fake-only"):
        run_host_authorized_scheduler_daemon_loop(
            HostSchedulerDaemonLoopRequest(
                snapshot_path=snapshot_path,
                event_log_path=event_log_path,
                runtime_config=RuntimeRegistryWiringConfig(
                    providers=("qoder",),
                    host_invocation=RuntimeHostInvocation(
                        surface="cli-scheduler-run-once",
                        invocation_id="bad-loop-qoder",
                        requested_providers=("qoder",),
                    ),
                    qoder_permission_grant=RuntimeProviderPermissionGrant(
                        grant_id="grant-qoder",
                        provider="qoder",
                        approved_by="host:test",
                        approved_at="2026-06-19T15:40:00+08:00",
                        allow_sdk_client=True,
                    ),
                ),
            ),
            qoder_query_client=_RecordingQoderClient(QoderQueryResult(summary="unused")),
        )

    with pytest.raises(ValueError, match="RuntimeProviderPermissionGrant"):
        run_host_authorized_scheduler_daemon_loop(
            HostSchedulerDaemonLoopRequest(
                snapshot_path=snapshot_path,
                event_log_path=event_log_path,
                runtime_config=RuntimeRegistryWiringConfig(
                    providers=("qoder",),
                    host_invocation=RuntimeHostInvocation(
                        surface="host-authorized-adapter",
                        invocation_id="missing-loop-grant",
                        requested_providers=("qoder",),
                    ),
                ),
            ),
            qoder_query_client=_RecordingQoderClient(QoderQueryResult(summary="unused")),
        )

    with pytest.raises(ValueError, match="injected QoderQueryClient"):
        run_host_authorized_scheduler_daemon_loop(
            HostSchedulerDaemonLoopRequest(
                snapshot_path=snapshot_path,
                event_log_path=event_log_path,
                runtime_config=RuntimeRegistryWiringConfig(
                    providers=("qoder",),
                    host_invocation=RuntimeHostInvocation(
                        surface="host-authorized-adapter",
                        invocation_id="missing-loop-client",
                        requested_providers=("qoder",),
                    ),
                    qoder_permission_grant=RuntimeProviderPermissionGrant(
                        grant_id="grant-qoder",
                        provider="qoder",
                        approved_by="host:test",
                        approved_at="2026-06-19T15:41:00+08:00",
                        allow_sdk_client=True,
                    ),
                ),
            )
        )

    assert read_scheduler_state_snapshot(snapshot_path).tasks["task-q"].state == "proposed"
    assert not event_log_path.exists()


def test_host_scheduler_daemon_loop_rejects_mixed_runtime_registry(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(SchedulerState(), snapshot_path)

    with pytest.raises(ValueError, match="requires exactly one runtime provider"):
        run_host_authorized_scheduler_daemon_loop(
            HostSchedulerDaemonLoopRequest(
                snapshot_path=snapshot_path,
                event_log_path=event_log_path,
                runtime_config=RuntimeRegistryWiringConfig(
                    providers=("fake", "qoder"),
                    host_invocation=RuntimeHostInvocation(
                        surface="host-authorized-adapter",
                        invocation_id="mixed-loop",
                        requested_providers=("fake", "qoder"),
                    ),
                    qoder_permission_grant=RuntimeProviderPermissionGrant(
                        grant_id="grant-qoder",
                        provider="qoder",
                        approved_by="host:test",
                        approved_at="2026-06-19T15:45:00+08:00",
                        allow_sdk_client=True,
                    ),
                ),
            ),
            qoder_query_client=_RecordingQoderClient(QoderQueryResult(summary="unused")),
        )


def test_drain_preflighted_ready_tasks_runs_dependency_chain_to_completion(tmp_path) -> None:
    sandbox_registry = SandboxProviderRegistry()
    sandbox_registry.register(SharedProcessSandboxProvider())
    runtime_registry = AgentRuntimeAdapterRegistry()
    store = InMemoryArtifactVersionStore()
    store.put(_accepted_contract_artifact(version="v1"))
    runtime_registry.register(
        FakeAgentRuntimeAdapter(
            artifact_store=store,
            timestamp="2026-06-17T00:30:00+08:00",
        )
    )
    scheduler_log = JsonlSchedulerEventLog(tmp_path / "preflight-drain-events.jsonl")
    state = SchedulerState(
        tasks={
            "task-a": _scheduled_task(
                "task-a",
                input_artifact_refs=(
                    ExchangeReference(ref_kind="exchange_artifact", ref_id="server-api", version="v1"),
                ),
                output_artifact_id="task-a:result",
            ),
            "task-b": _scheduled_task("task-b", output_artifact_id="task-b:result"),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-a-b",
                source_task_id="task-a",
                target_task_id="task-b",
                required_state="complete",
            ),
        ),
    )

    result = drain_preflighted_ready_tasks(
        state,
        sandbox_registry=sandbox_registry,
        runtime_registry=runtime_registry,
        workspace_root="E:/workspace/project",
        scratch_root=".codex/scratch",
        event_log=scheduler_log,
        timestamp="2026-06-17T00:30:00+08:00",
    )

    assert result.stop_reason == "no_ready_tasks"
    assert tuple(run.runtime_result.run_handle.task_id for run in result.preflight_results) == (
        "task-a",
        "task-b",
    )
    assert tuple(run.preflight.scratch.path for run in result.preflight_results) == (
        ".codex/scratch/task-a",
        ".codex/scratch/task-b",
    )
    assert all(task.state == "complete" for task in result.state.tasks.values())
    assert [event.event_kind for event in scheduler_log.read_all()] == [
        "task_ready",
        "task_waiting",
        "task_running",
        "task_completed",
        "task_ready",
        "task_running",
        "task_completed",
    ]


def test_drain_preflighted_ready_tasks_respects_max_runs() -> None:
    sandbox_registry = SandboxProviderRegistry()
    sandbox_registry.register(SharedProcessSandboxProvider())
    runtime_registry = AgentRuntimeAdapterRegistry()
    runtime_registry.register(FakeAgentRuntimeAdapter(artifact_store=InMemoryArtifactVersionStore()))
    state = SchedulerState(
        tasks={
            "task-a": _scheduled_task("task-a", output_artifact_id="task-a:result"),
            "task-b": _scheduled_task("task-b", output_artifact_id="task-b:result"),
        },
    )

    result = drain_preflighted_ready_tasks(
        state,
        sandbox_registry=sandbox_registry,
        runtime_registry=runtime_registry,
        max_runs=1,
    )

    assert result.stop_reason == "max_runs_reached"
    assert tuple(run.runtime_result.run_handle.task_id for run in result.preflight_results) == ("task-a",)
    assert result.state.tasks["task-a"].state == "complete"
    assert result.state.tasks["task-b"].state == "ready"
    assert result.ready_task_ids == ("task-b",)


def test_drain_preflighted_ready_tasks_blocks_failed_task_and_stops(tmp_path) -> None:
    sandbox_registry = SandboxProviderRegistry()
    sandbox_registry.register(SharedProcessSandboxProvider())
    runtime_registry = AgentRuntimeAdapterRegistry()
    runtime_registry.register(_FailingRuntime("runtime crashed"))
    scheduler_log = JsonlSchedulerEventLog(tmp_path / "preflight-drain-failed-events.jsonl")
    state = SchedulerState(
        tasks={
            "task-a": _scheduled_task("task-a", output_artifact_id="task-a:result"),
            "task-b": _scheduled_task("task-b", output_artifact_id="task-b:result"),
        },
    )

    result = drain_preflighted_ready_tasks(
        state,
        sandbox_registry=sandbox_registry,
        runtime_registry=runtime_registry,
        event_log=scheduler_log,
        timestamp="2026-06-17T00:40:00+08:00",
    )

    assert result.stop_reason == "task_failed"
    assert result.failed_task_id == "task-a"
    assert result.blocked_task_ids == ("task-a",)
    assert result.ready_task_ids == ("task-b",)
    assert result.state.tasks["task-a"].state == "blocked"
    assert result.state.tasks["task-a"].blocked_reason == "runtime failure: runtime crashed"
    assert result.state.tasks["task-b"].state == "ready"
    assert [event.event_kind for event in scheduler_log.read_all()] == [
        "task_ready",
        "task_ready",
        "task_running",
        "task_run_failed",
    ]


def test_drain_preflighted_ready_tasks_can_continue_independent_branch_after_failure() -> None:
    sandbox_registry = SandboxProviderRegistry()
    sandbox_registry.register(SharedProcessSandboxProvider())
    runtime_registry = AgentRuntimeAdapterRegistry()
    store = InMemoryArtifactVersionStore()
    store.put(_accepted_contract_artifact(version="v1"))
    runtime_registry.register(
        _SelectiveFailingRuntime(
            failing_task_ids=("task-a",),
            artifact_store=store,
            timestamp="2026-06-17T00:50:00+08:00",
        )
    )
    state = SchedulerState(
        tasks={
            "task-a": _scheduled_task(
                "task-a",
                input_artifact_refs=(
                    ExchangeReference(ref_kind="exchange_artifact", ref_id="server-api", version="v1"),
                ),
                output_artifact_id="task-a:result",
            ),
            "task-b": _scheduled_task("task-b", output_artifact_id="task-b:result"),
            "task-c": _scheduled_task(
                "task-c",
                input_artifact_refs=(
                    ExchangeReference(ref_kind="exchange_artifact", ref_id="server-api", version="v1"),
                ),
                output_artifact_id="task-c:result",
            ),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-a-b",
                source_task_id="task-a",
                target_task_id="task-b",
                required_state="complete",
            ),
        ),
    )

    result = drain_preflighted_ready_tasks(
        state,
        sandbox_registry=sandbox_registry,
        runtime_registry=runtime_registry,
        policy=SchedulerRunPolicy(continue_on_failure=True),
    )

    assert result.stop_reason == "completed_with_failures"
    assert result.failed_task_ids == ("task-a",)
    assert result.blocked_task_ids == ("task-a",)
    assert tuple(run.runtime_result.run_handle.task_id for run in result.preflight_results) == ("task-c",)
    assert result.state.tasks["task-a"].state == "blocked"
    assert result.state.tasks["task-b"].state == "waiting"
    assert result.state.tasks["task-c"].state == "complete"


def test_scheduler_event_log_records_readiness_decisions(tmp_path) -> None:
    event_log = JsonlSchedulerEventLog(tmp_path / "scheduler-events.jsonl")
    state = SchedulerState(
        tasks={
            "task-a": _scheduled_task("task-a", state="complete"),
            "task-b": _scheduled_task("task-b", state="proposed"),
            "task-c": _scheduled_task(
                "task-c",
                edit_lease=EditScopeLease(
                    lease_id="lease-c",
                    task_id="task-c",
                    allowed_artifacts=("src/app.py",),
                    lease_mode="write",
                ),
            ),
            "task-d": _scheduled_task(
                "task-d",
                state="running",
                edit_lease=EditScopeLease(
                    lease_id="lease-d",
                    task_id="task-d",
                    allowed_artifacts=("src/app.py",),
                    lease_mode="write",
                ),
            ),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-a-b",
                source_task_id="task-a",
                target_task_id="task-b",
                required_state="complete",
            ),
            TaskDependency(
                dependency_id="dep-missing-c",
                source_task_id="task-missing",
                target_task_id="task-c",
                required_state="complete",
            ),
        ),
    )

    updated = mark_ready_tasks(
        state,
        event_log=event_log,
        timestamp="2026-06-16T20:00:00+08:00",
    )
    events = event_log.read_all()

    assert updated.tasks["task-b"].state == "ready"
    assert updated.tasks["task-c"].state == "waiting"
    assert [event.event_kind for event in events] == ["task_ready", "task_waiting"]
    assert events[0].event_id == "scheduler-event-1"
    assert events[0].from_state == "proposed"
    assert events[0].to_state == "ready"
    assert events[1].related_dependency_ids == ("dep-missing-c",)
    assert events[1].reason == "waiting for task-missing to reach complete"


def test_scheduler_event_log_records_ready_task_run(tmp_path) -> None:
    store = InMemoryArtifactVersionStore()
    store.put(_accepted_contract_artifact(version="v1"))
    runtime = FakeAgentRuntimeAdapter(
        artifact_store=store,
        timestamp="2026-06-16T20:10:00+08:00",
    )
    scheduler_log = JsonlSchedulerEventLog(tmp_path / "scheduler-run-events.jsonl")
    task = _scheduled_task(
        "task-1",
        input_artifact_refs=(
            ExchangeReference(ref_kind="exchange_artifact", ref_id="server-api", version="v1"),
        ),
        output_artifact_id="task-1:result",
    )

    updated, result = run_ready_task(
        SchedulerState(tasks={"task-1": task}),
        "task-1",
        runtime=runtime,
        event_log=scheduler_log,
        timestamp="2026-06-16T20:10:00+08:00",
    )
    events = scheduler_log.read_all()

    assert updated.tasks["task-1"].state == "complete"
    assert result.output_artifact.artifact_id == "task-1:result"
    assert [event.event_kind for event in events] == [
        "task_ready",
        "task_running",
        "task_completed",
    ]
    assert events[-1].run_id == "fake-run-1"
    assert events[-1].session_id == "fake-session-1"
    assert events[-1].output_artifact_id == "task-1:result"
    assert events[-1].related_artifact_ids == ("task-1:result",)


def test_scheduler_runs_ready_task_through_registry_runtime(tmp_path) -> None:
    store = InMemoryArtifactVersionStore()
    store.put(_accepted_contract_artifact(version="v1"))
    runtime = FakeAgentRuntimeAdapter(
        artifact_store=store,
        timestamp="2026-06-16T22:20:00+08:00",
    )
    registry = AgentRuntimeAdapterRegistry()
    registry.register(runtime)
    scheduler_log = JsonlSchedulerEventLog(tmp_path / "registry-run-events.jsonl")
    task = _scheduled_task(
        "task-1",
        input_artifact_refs=(
            ExchangeReference(ref_kind="exchange_artifact", ref_id="server-api", version="v1"),
        ),
        output_artifact_id="task-1:result",
    )

    updated, result = run_scheduled_task_with_registry(
        SchedulerState(tasks={"task-1": task}),
        "task-1",
        registry=registry,
        event_log=scheduler_log,
        timestamp="2026-06-16T22:20:00+08:00",
    )

    assert updated.tasks["task-1"].state == "complete"
    assert result.output_artifact.artifact_id == "task-1:result"
    assert [event.event_kind for event in scheduler_log.read_all()] == [
        "task_ready",
        "task_running",
        "task_completed",
    ]


def test_scheduler_registry_runtime_helper_reports_missing_provider() -> None:
    registry = AgentRuntimeAdapterRegistry()
    state = SchedulerState(tasks={"task-1": _scheduled_task("task-1")})

    with pytest.raises(KeyError, match="no runtime adapter registered for provider 'fake'"):
        run_scheduled_task_with_registry(state, "task-1", registry=registry)


def test_run_ready_task_wakes_dependents_after_completion(tmp_path) -> None:
    store = InMemoryArtifactVersionStore()
    store.put(_accepted_contract_artifact(version="v1"))
    runtime = FakeAgentRuntimeAdapter(
        artifact_store=store,
        timestamp="2026-06-16T21:10:00+08:00",
    )
    scheduler_log = JsonlSchedulerEventLog(tmp_path / "run-wake-events.jsonl")
    state = SchedulerState(
        tasks={
            "task-a": _scheduled_task(
                "task-a",
                input_artifact_refs=(
                    ExchangeReference(ref_kind="exchange_artifact", ref_id="server-api", version="v1"),
                ),
                output_artifact_id="task-a:result",
            ),
            "task-b": _scheduled_task("task-b", state="waiting"),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-a-b",
                source_task_id="task-a",
                target_task_id="task-b",
                required_state="complete",
            ),
        ),
    )

    updated, result = run_ready_task(
        state,
        "task-a",
        runtime=runtime,
        event_log=scheduler_log,
        timestamp="2026-06-16T21:10:00+08:00",
    )
    events = scheduler_log.read_all()

    assert result.output_artifact.artifact_id == "task-a:result"
    assert updated.tasks["task-a"].state == "complete"
    assert updated.tasks["task-b"].state == "ready"
    assert [event.event_kind for event in events] == [
        "task_ready",
        "task_running",
        "task_completed",
        "task_ready",
    ]
    assert events[-1].task_id == "task-b"


def test_drain_ready_tasks_runs_dependency_chain_to_completion(tmp_path) -> None:
    store = InMemoryArtifactVersionStore()
    store.put(_accepted_contract_artifact(version="v1"))
    runtime = FakeAgentRuntimeAdapter(
        artifact_store=store,
        timestamp="2026-06-16T21:20:00+08:00",
    )
    scheduler_log = JsonlSchedulerEventLog(tmp_path / "drain-chain-events.jsonl")
    state = SchedulerState(
        tasks={
            "task-a": _scheduled_task(
                "task-a",
                input_artifact_refs=(
                    ExchangeReference(ref_kind="exchange_artifact", ref_id="server-api", version="v1"),
                ),
                output_artifact_id="task-a:result",
            ),
            "task-b": _scheduled_task("task-b", output_artifact_id="task-b:result"),
            "task-c": _scheduled_task("task-c", output_artifact_id="task-c:result"),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-a-b",
                source_task_id="task-a",
                target_task_id="task-b",
                required_state="complete",
            ),
            TaskDependency(
                dependency_id="dep-b-c",
                source_task_id="task-b",
                target_task_id="task-c",
                required_state="complete",
            ),
        ),
    )

    result = drain_ready_tasks(
        state,
        runtime=runtime,
        event_log=scheduler_log,
        timestamp="2026-06-16T21:20:00+08:00",
    )
    events = scheduler_log.read_all()

    assert result.stop_reason == "no_ready_tasks"
    assert result.ready_task_ids == ()
    assert tuple(run.run_handle.task_id for run in result.run_results) == (
        "task-a",
        "task-b",
        "task-c",
    )
    assert all(task.state == "complete" for task in result.state.tasks.values())
    assert tuple(record.task_id for record in result.state.run_records) == (
        "task-a",
        "task-b",
        "task-c",
    )
    assert [event.event_kind for event in events] == [
        "task_ready",
        "task_waiting",
        "task_waiting",
        "task_running",
        "task_completed",
        "task_ready",
        "task_running",
        "task_completed",
        "task_ready",
        "task_running",
        "task_completed",
    ]


def test_drain_ready_tasks_respects_max_runs_and_reports_remaining_ready(tmp_path) -> None:
    store = InMemoryArtifactVersionStore()
    store.put(_accepted_contract_artifact(version="v1"))
    runtime = FakeAgentRuntimeAdapter(
        artifact_store=store,
        timestamp="2026-06-16T21:30:00+08:00",
    )
    state = SchedulerState(
        tasks={
            "task-a": _scheduled_task(
                "task-a",
                input_artifact_refs=(
                    ExchangeReference(ref_kind="exchange_artifact", ref_id="server-api", version="v1"),
                ),
                output_artifact_id="task-a:result",
            ),
            "task-b": _scheduled_task("task-b", output_artifact_id="task-b:result"),
            "task-c": _scheduled_task("task-c", output_artifact_id="task-c:result"),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-a-b",
                source_task_id="task-a",
                target_task_id="task-b",
                required_state="complete",
            ),
        ),
    )

    result = drain_ready_tasks(state, runtime=runtime, max_runs=1)

    assert result.stop_reason == "max_runs_reached"
    assert tuple(run.run_handle.task_id for run in result.run_results) == ("task-a",)
    assert result.state.tasks["task-a"].state == "complete"
    assert result.state.tasks["task-b"].state == "ready"
    assert result.state.tasks["task-c"].state == "ready"
    assert result.ready_task_ids == ("task-b", "task-c")


def test_drain_ready_tasks_can_only_mark_waiting_without_running(tmp_path) -> None:
    runtime = FakeAgentRuntimeAdapter(
        artifact_store=InMemoryArtifactVersionStore(),
        timestamp="2026-06-16T21:40:00+08:00",
    )
    scheduler_log = JsonlSchedulerEventLog(tmp_path / "drain-no-ready-events.jsonl")
    state = SchedulerState(
        tasks={
            "task-a": _scheduled_task("task-a"),
            "task-b": _scheduled_task("task-b"),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-missing-a",
                source_task_id="task-missing",
                target_task_id="task-a",
                required_state="complete",
            ),
            TaskDependency(
                dependency_id="dep-missing-b",
                source_task_id="task-missing",
                target_task_id="task-b",
                required_state="complete",
            ),
        ),
    )

    result = drain_ready_tasks(
        state,
        runtime=runtime,
        event_log=scheduler_log,
        timestamp="2026-06-16T21:40:00+08:00",
    )

    assert result.stop_reason == "no_ready_tasks"
    assert result.run_results == ()
    assert result.ready_task_ids == ()
    assert result.state.tasks["task-a"].state == "waiting"
    assert result.state.tasks["task-b"].state == "waiting"
    assert [event.event_kind for event in scheduler_log.read_all()] == [
        "task_waiting",
        "task_waiting",
    ]


def test_drain_ready_tasks_stops_and_blocks_failed_runtime_task(tmp_path) -> None:
    runtime = _FailingRuntime("runtime crashed")
    scheduler_log = JsonlSchedulerEventLog(tmp_path / "drain-failed-events.jsonl")
    state = SchedulerState(
        tasks={
            "task-a": _scheduled_task("task-a", output_artifact_id="task-a:result"),
            "task-b": _scheduled_task("task-b", output_artifact_id="task-b:result"),
            "task-c": _scheduled_task("task-c", output_artifact_id="task-c:result"),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-a-b",
                source_task_id="task-a",
                target_task_id="task-b",
                required_state="complete",
            ),
        ),
    )

    result = drain_ready_tasks(
        state,
        runtime=runtime,
        event_log=scheduler_log,
        timestamp="2026-06-16T21:50:00+08:00",
    )
    events = scheduler_log.read_all()

    assert result.stop_reason == "task_failed"
    assert result.failed_task_id == "task-a"
    assert result.stop_detail == "runtime crashed"
    assert result.run_results == ()
    assert result.ready_task_ids == ("task-c",)
    assert result.blocked_task_ids == ("task-a",)
    assert result.state.tasks["task-a"].state == "blocked"
    assert result.state.tasks["task-a"].blocked_reason == "runtime failure: runtime crashed"
    assert result.state.tasks["task-b"].state == "waiting"
    assert result.state.tasks["task-c"].state == "ready"
    assert [event.event_kind for event in events] == [
        "task_ready",
        "task_waiting",
        "task_ready",
        "task_running",
        "task_run_failed",
    ]
    assert events[-1].task_id == "task-a"
    assert events[-1].reason == "runtime failure: runtime crashed"


def test_drain_ready_tasks_reports_blocked_admission_without_running(tmp_path) -> None:
    runtime = FakeAgentRuntimeAdapter(
        artifact_store=InMemoryArtifactVersionStore(),
        timestamp="2026-06-16T22:00:00+08:00",
    )
    scheduler_log = JsonlSchedulerEventLog(tmp_path / "drain-blocked-events.jsonl")
    state = SchedulerState(
        tasks={
            "task-running": _scheduled_task(
                "task-running",
                state="running",
                edit_lease=EditScopeLease(
                    lease_id="lease-running",
                    task_id="task-running",
                    allowed_artifacts=("src/app.py",),
                    lease_mode="write",
                ),
            ),
            "task-blocked": _scheduled_task(
                "task-blocked",
                edit_lease=EditScopeLease(
                    lease_id="lease-blocked",
                    task_id="task-blocked",
                    allowed_artifacts=("src/app.py",),
                    lease_mode="write",
                ),
            ),
        },
    )

    result = drain_ready_tasks(
        state,
        runtime=runtime,
        event_log=scheduler_log,
        timestamp="2026-06-16T22:00:00+08:00",
    )

    assert result.stop_reason == "blocked_tasks"
    assert result.blocked_task_ids == ("task-blocked",)
    assert result.stop_detail == "one or more tasks are blocked"
    assert result.run_results == ()
    assert result.ready_task_ids == ()
    assert result.state.tasks["task-blocked"].blocked_reason == (
        "edit lease conflict with task-running: src/app.py"
    )
    assert [event.event_kind for event in scheduler_log.read_all()] == ["task_blocked"]


def test_drain_ready_tasks_policy_can_continue_independent_branch_after_failure(tmp_path) -> None:
    store = InMemoryArtifactVersionStore()
    store.put(_accepted_contract_artifact(version="v1"))
    runtime = _SelectiveFailingRuntime(
        failing_task_ids=("task-a",),
        artifact_store=store,
        timestamp="2026-06-16T22:10:00+08:00",
    )
    scheduler_log = JsonlSchedulerEventLog(tmp_path / "drain-continue-failure-events.jsonl")
    state = SchedulerState(
        tasks={
            "task-a": _scheduled_task(
                "task-a",
                input_artifact_refs=(
                    ExchangeReference(ref_kind="exchange_artifact", ref_id="server-api", version="v1"),
                ),
                output_artifact_id="task-a:result",
            ),
            "task-b": _scheduled_task("task-b", output_artifact_id="task-b:result"),
            "task-c": _scheduled_task(
                "task-c",
                input_artifact_refs=(
                    ExchangeReference(ref_kind="exchange_artifact", ref_id="server-api", version="v1"),
                ),
                output_artifact_id="task-c:result",
            ),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-a-b",
                source_task_id="task-a",
                target_task_id="task-b",
                required_state="complete",
            ),
        ),
    )

    result = drain_ready_tasks(
        state,
        runtime=runtime,
        policy=SchedulerRunPolicy(continue_on_failure=True),
        event_log=scheduler_log,
        timestamp="2026-06-16T22:10:00+08:00",
    )
    events = scheduler_log.read_all()

    assert result.stop_reason == "completed_with_failures"
    assert result.failed_task_id == "task-a"
    assert result.failed_task_ids == ("task-a",)
    assert result.blocked_task_ids == ("task-a",)
    assert result.ready_task_ids == ()
    assert tuple(run.run_handle.task_id for run in result.run_results) == ("task-c",)
    assert result.state.tasks["task-a"].state == "blocked"
    assert result.state.tasks["task-b"].state == "waiting"
    assert result.state.tasks["task-b"].blocked_reason == "waiting for task-a to reach complete"
    assert result.state.tasks["task-c"].state == "complete"
    assert [event.event_kind for event in events] == [
        "task_ready",
        "task_waiting",
        "task_ready",
        "task_running",
        "task_run_failed",
        "task_running",
        "task_completed",
    ]


def test_drain_ready_tasks_rejects_conflicting_or_invalid_policy() -> None:
    runtime = FakeAgentRuntimeAdapter(artifact_store=InMemoryArtifactVersionStore())
    state = SchedulerState(tasks={"task-a": _scheduled_task("task-a")})

    with pytest.raises(ValueError, match="conflicts with policy.max_runs"):
        drain_ready_tasks(
            state,
            runtime=runtime,
            max_runs=1,
            policy=SchedulerRunPolicy(max_runs=2),
        )

    with pytest.raises(ValueError, match="max_retries must be non-negative"):
        drain_ready_tasks(
            state,
            runtime=runtime,
            policy=SchedulerRunPolicy(max_retries=-1),
        )

    with pytest.raises(ValueError, match="timeout_seconds must be non-negative"):
        drain_ready_tasks(
            state,
            runtime=runtime,
            policy=SchedulerRunPolicy(timeout_seconds=-1),
        )


def test_scheduler_event_log_rejects_invalid_jsonl(tmp_path) -> None:
    path = tmp_path / "broken-scheduler-events.jsonl"
    path.write_text("{not-json}\n", encoding="utf-8")
    event_log = JsonlSchedulerEventLog(path)

    with pytest.raises(ValueError, match="invalid scheduler event JSONL"):
        event_log.read_all()


def test_replay_scheduler_events_recovers_task_state_and_run_records(tmp_path) -> None:
    scheduler_log = JsonlSchedulerEventLog(tmp_path / "scheduler-replay-events.jsonl")
    scheduler_log.append(
        SchedulerEvent(
            event_id="scheduler-event-1",
            event_kind="task_ready",
            timestamp="2026-06-16T20:20:00+08:00",
            task_id="task-1",
            from_state="proposed",
            to_state="ready",
            sequence=1,
        )
    )
    scheduler_log.append(
        SchedulerEvent(
            event_id="scheduler-event-2",
            event_kind="task_running",
            timestamp="2026-06-16T20:21:00+08:00",
            task_id="task-1",
            from_state="ready",
            to_state="running",
            session_id="session-1",
            sequence=2,
        )
    )
    scheduler_log.append(
        SchedulerEvent(
            event_id="scheduler-event-3",
            event_kind="task_completed",
            timestamp="2026-06-16T20:22:00+08:00",
            task_id="task-1",
            from_state="running",
            to_state="complete",
            run_id="run-1",
            session_id="session-1",
            output_artifact_id="task-1:result",
            output_artifact_version="v1",
            related_artifact_ids=("task-1:result",),
            sequence=3,
        )
    )
    baseline = SchedulerState(tasks={"task-1": _scheduled_task("task-1")})

    recovered = replay_scheduler_events(baseline, scheduler_log.read_all())
    task = recovered.tasks["task-1"]

    assert task.state == "complete"
    assert task.run_id == "run-1"
    assert task.output_artifact_ref is not None
    assert task.output_artifact_ref.ref_id == "task-1:result"
    assert task.output_artifact_ref.version == "v1"
    assert len(recovered.run_records) == 1
    assert recovered.run_records[0].run_id == "run-1"
    assert recovered.run_records[0].session_id == "session-1"


def test_replay_scheduler_events_recovers_edit_lease_lifecycle_record(tmp_path) -> None:
    scheduler_log = JsonlSchedulerEventLog(tmp_path / "lease-replay-events.jsonl")
    scheduler_log.append(
        SchedulerEvent(
            event_id="scheduler-event-1",
            event_kind="task_ready",
            timestamp="2026-06-20T12:00:00+08:00",
            task_id="task-1",
            from_state="proposed",
            to_state="ready",
            lease_id="lease-1",
            edit_lease_lifecycle=EditLeaseLifecycleRecord(
                lease_id="lease-1",
                task_id="task-1",
                state="acquired",
                mode="write",
                allowed_artifacts=("src/app.py",),
                acquired_at="2026-06-20T12:00:00+08:00",
            ),
            sequence=1,
        )
    )
    scheduler_log.append(
        SchedulerEvent(
            event_id="scheduler-event-2",
            event_kind="lease_expired",
            timestamp="2026-06-20T12:31:00+08:00",
            task_id="task-1",
            from_state="acquired",
            to_state="expired",
            lease_id="lease-1",
            edit_lease_lifecycle=EditLeaseLifecycleRecord(
                lease_id="lease-1",
                task_id="task-1",
                state="expired",
                mode="write",
                allowed_artifacts=("src/app.py",),
                acquired_at="2026-06-20T12:00:00+08:00",
                expires_at="2026-06-20T12:30:00+08:00",
                released_at="2026-06-20T12:31:00+08:00",
                reason="edit lease expired at 2026-06-20T12:30:00+08:00",
            ),
            sequence=2,
        )
    )
    baseline = SchedulerState(tasks={"task-1": _scheduled_task("task-1")})

    recovered = replay_scheduler_events(baseline, scheduler_log.read_all())

    assert recovered.tasks["task-1"].state == "ready"
    record = recovered.edit_lease_lifecycle["lease-1"]
    assert record.state == "expired"
    assert record.released_at == "2026-06-20T12:31:00+08:00"
    assert record.reason == "edit lease expired at 2026-06-20T12:30:00+08:00"


def test_recover_scheduler_state_reads_snapshot_and_jsonl_event_log(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    baseline = SchedulerState(
        tasks={
            "task-1": _scheduled_task("task-1"),
            "task-2": _scheduled_task("task-2", state="waiting"),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-1-2",
                source_task_id="task-1",
                target_task_id="task-2",
                required_state="complete",
            ),
        ),
    )
    write_scheduler_state_snapshot(baseline, snapshot_path)
    scheduler_log = JsonlSchedulerEventLog(event_log_path)
    scheduler_log.append(
        SchedulerEvent(
            event_id="scheduler-event-1",
            event_kind="task_ready",
            timestamp="2026-06-16T23:30:00+08:00",
            task_id="task-1",
            from_state="proposed",
            to_state="ready",
            sequence=1,
        )
    )
    scheduler_log.append(
        SchedulerEvent(
            event_id="scheduler-event-2",
            event_kind="task_completed",
            timestamp="2026-06-16T23:31:00+08:00",
            task_id="task-1",
            from_state="running",
            to_state="complete",
            run_id="run-1",
            session_id="session-1",
            output_artifact_id="task-1:result",
            output_artifact_version="v1",
            sequence=2,
        )
    )

    recovery = recover_scheduler_state(snapshot_path, event_log_path)

    assert recovery.snapshot_path == snapshot_path
    assert recovery.event_log_path == event_log_path
    assert recovery.strict is True
    assert recovery.event_count == 2
    assert recovery.baseline_state.tasks["task-1"].state == "proposed"
    assert recovery.recovered_state.tasks["task-1"].state == "complete"
    assert recovery.recovered_state.tasks["task-1"].output_artifact_ref is not None
    assert recovery.recovered_state.tasks["task-1"].output_artifact_ref.ref_id == "task-1:result"
    assert recovery.recovered_state.dependencies[0].dependency_id == "dep-1-2"
    assert recovery.recovered_state.run_records[0].state == "complete"


def test_recover_scheduler_state_can_ignore_unknown_events_when_not_strict(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(tasks={"task-1": _scheduled_task("task-1")}),
        snapshot_path,
    )
    scheduler_log = JsonlSchedulerEventLog(event_log_path)
    scheduler_log.append(
        SchedulerEvent(
            event_id="scheduler-event-unknown",
            event_kind="task_completed",
            timestamp="2026-06-16T23:35:00+08:00",
            task_id="task-missing",
            from_state="running",
            to_state="complete",
            run_id="run-missing",
            output_artifact_id="task-missing:result",
            output_artifact_version="v1",
            sequence=1,
        )
    )

    recovery = recover_scheduler_state(snapshot_path, event_log_path, strict=False)

    assert recovery.strict is False
    assert recovery.event_count == 1
    assert recovery.recovered_state.tasks["task-1"].state == "proposed"
    assert recovery.recovered_state.run_records == ()


def test_write_compacted_scheduler_snapshot_persists_recovered_state_without_truncating_log(
    tmp_path,
) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    compacted_path = tmp_path / "scheduler-state.compacted.json"
    write_scheduler_state_snapshot(
        SchedulerState(tasks={"task-1": _scheduled_task("task-1")}),
        snapshot_path,
    )
    scheduler_log = JsonlSchedulerEventLog(event_log_path)
    scheduler_log.append(
        SchedulerEvent(
            event_id="scheduler-event-1",
            event_kind="task_completed",
            timestamp="2026-06-16T23:40:00+08:00",
            task_id="task-1",
            from_state="running",
            to_state="complete",
            run_id="run-1",
            session_id="session-1",
            output_artifact_id="task-1:result",
            output_artifact_version="v1",
            sequence=1,
        )
    )

    result = write_compacted_scheduler_snapshot(
        snapshot_path,
        event_log_path,
        compacted_path,
    )
    compacted_state = read_scheduler_state_snapshot(compacted_path)

    assert result.compacted_snapshot_path == compacted_path
    assert result.event_log_truncated is False
    assert result.event_count == 1
    assert result.compacted_state.tasks["task-1"].state == "complete"
    assert compacted_state.tasks["task-1"].state == "complete"
    assert compacted_state.run_records[0].run_id == "run-1"
    assert len(JsonlSchedulerEventLog(event_log_path).read_all()) == 1
    assert result.archived_event_log_path is None
    assert result.archive_requested is False
    assert result.reset_event_log_requested is False
    assert result.archived_event_count == 0
    assert result.active_event_count_after_compaction == 1
    assert result.replay_boundary_summary["event_log_truncated"] is False


def test_write_compacted_scheduler_snapshot_can_archive_and_reset_event_log(
    tmp_path,
) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    compacted_path = tmp_path / "scheduler-state.compacted.json"
    archive_path = tmp_path / "archive" / "scheduler-events.pre-compaction.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(tasks={"task-1": _scheduled_task("task-1")}),
        snapshot_path,
    )
    scheduler_log = JsonlSchedulerEventLog(event_log_path)
    scheduler_log.append(
        SchedulerEvent(
            event_id="scheduler-event-1",
            event_kind="task_ready",
            timestamp="2026-06-20T00:00:00+08:00",
            task_id="task-1",
            from_state="proposed",
            to_state="ready",
            sequence=1,
        )
    )
    scheduler_log.append(
        SchedulerEvent(
            event_id="scheduler-event-2",
            event_kind="task_completed",
            timestamp="2026-06-20T00:01:00+08:00",
            task_id="task-1",
            from_state="running",
            to_state="complete",
            run_id="run-1",
            session_id="session-1",
            output_artifact_id="task-1:result",
            output_artifact_version="v1",
            sequence=2,
        )
    )

    result = write_compacted_scheduler_snapshot(
        snapshot_path,
        event_log_path,
        compacted_path,
        archive_event_log_path=archive_path,
        reset_event_log=True,
    )

    assert result.compacted_snapshot_path == compacted_path
    assert result.archived_event_log_path == archive_path
    assert result.archive_requested is True
    assert result.reset_event_log_requested is True
    assert result.event_log_truncated is True
    assert result.event_count == 2
    assert result.archived_event_count == 2
    assert result.active_event_count_after_compaction == 0
    assert JsonlSchedulerEventLog(archive_path).read_all()[1].event_id == "scheduler-event-2"
    assert JsonlSchedulerEventLog(event_log_path).read_all() == ()
    compacted_state = read_scheduler_state_snapshot(compacted_path)
    assert compacted_state.tasks["task-1"].state == "complete"
    assert compacted_state.run_records[0].run_id == "run-1"
    assert result.replay_boundary_summary["archived_event_count"] == 2
    assert result.replay_boundary_summary["active_event_count_after_compaction"] == 0


def test_recover_scheduler_state_replays_only_post_compaction_events_after_reset(
    tmp_path,
) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    compacted_path = tmp_path / "scheduler-state.compacted.json"
    archive_path = tmp_path / "scheduler-events.archive.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-1": _scheduled_task("task-1"),
                "task-2": _scheduled_task("task-2", state="waiting"),
            },
            dependencies=(
                TaskDependency(
                    dependency_id="dep-1-2",
                    source_task_id="task-1",
                    target_task_id="task-2",
                    required_state="complete",
                ),
            ),
        ),
        snapshot_path,
    )
    JsonlSchedulerEventLog(event_log_path).append(
        SchedulerEvent(
            event_id="scheduler-event-1",
            event_kind="task_completed",
            timestamp="2026-06-20T00:10:00+08:00",
            task_id="task-1",
            from_state="running",
            to_state="complete",
            run_id="run-1",
            output_artifact_id="task-1:result",
            output_artifact_version="v1",
            sequence=1,
        )
    )
    write_compacted_scheduler_snapshot(
        snapshot_path,
        event_log_path,
        compacted_path,
        archive_event_log_path=archive_path,
        reset_event_log=True,
    )
    JsonlSchedulerEventLog(event_log_path).append(
        SchedulerEvent(
            event_id="scheduler-event-2",
            event_kind="task_ready",
            timestamp="2026-06-20T00:11:00+08:00",
            task_id="task-2",
            from_state="waiting",
            to_state="ready",
            sequence=2,
        )
    )

    recovery = recover_scheduler_state(compacted_path, event_log_path)

    assert recovery.event_count == 1
    assert recovery.baseline_state.tasks["task-1"].state == "complete"
    assert recovery.recovered_state.tasks["task-1"].state == "complete"
    assert recovery.recovered_state.tasks["task-2"].state == "ready"
    assert recovery.recovered_state.run_records[0].run_id == "run-1"


def test_write_compacted_scheduler_snapshot_archive_reset_handles_missing_log(
    tmp_path,
) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "missing-scheduler-events.jsonl"
    compacted_path = tmp_path / "scheduler-state.compacted.json"
    archive_path = tmp_path / "scheduler-events.archive.jsonl"
    write_scheduler_state_snapshot(
        SchedulerState(tasks={"task-1": _scheduled_task("task-1")}),
        snapshot_path,
    )

    result = write_compacted_scheduler_snapshot(
        snapshot_path,
        event_log_path,
        compacted_path,
        archive_event_log_path=archive_path,
        reset_event_log=True,
    )

    assert result.event_count == 0
    assert result.archived_event_count == 0
    assert result.active_event_count_after_compaction == 0
    assert archive_path.exists()
    assert event_log_path.exists()
    assert archive_path.read_text(encoding="utf-8") == ""
    assert event_log_path.read_text(encoding="utf-8") == ""
    assert read_scheduler_state_snapshot(compacted_path).tasks["task-1"].state == "proposed"


def test_write_compacted_scheduler_snapshot_requires_archive_before_reset(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    compacted_path = tmp_path / "scheduler-state.compacted.json"
    write_scheduler_state_snapshot(
        SchedulerState(tasks={"task-1": _scheduled_task("task-1")}),
        snapshot_path,
    )

    with pytest.raises(ValueError, match="reset_event_log requires archive_event_log_path"):
        write_compacted_scheduler_snapshot(
            snapshot_path,
            event_log_path,
            compacted_path,
            reset_event_log=True,
        )

    assert not compacted_path.exists()


def test_write_compacted_scheduler_snapshot_honors_non_strict_recovery(tmp_path) -> None:
    snapshot_path = tmp_path / "scheduler-state.json"
    event_log_path = tmp_path / "scheduler-events.jsonl"
    compacted_path = tmp_path / "scheduler-state.compacted.json"
    write_scheduler_state_snapshot(
        SchedulerState(tasks={"task-1": _scheduled_task("task-1")}),
        snapshot_path,
    )
    JsonlSchedulerEventLog(event_log_path).append(
        SchedulerEvent(
            event_id="scheduler-event-unknown",
            event_kind="task_completed",
            timestamp="2026-06-16T23:45:00+08:00",
            task_id="task-missing",
            from_state="running",
            to_state="complete",
            run_id="run-missing",
            output_artifact_id="task-missing:result",
            output_artifact_version="v1",
            sequence=1,
        )
    )

    result = write_compacted_scheduler_snapshot(
        snapshot_path,
        event_log_path,
        compacted_path,
        strict=False,
    )
    compacted_state = read_scheduler_state_snapshot(compacted_path)

    assert result.recovery.strict is False
    assert result.event_count == 1
    assert compacted_state.tasks["task-1"].state == "proposed"
    assert compacted_state.run_records == ()


def test_replay_scheduler_events_recovers_failed_run_as_blocked() -> None:
    baseline = SchedulerState(tasks={"task-1": _scheduled_task("task-1")})

    recovered = replay_scheduler_events(
        baseline,
        (
            SchedulerEvent(
                event_id="scheduler-event-1",
                event_kind="task_run_failed",
                timestamp="2026-06-16T20:25:00+08:00",
                task_id="task-1",
                from_state="running",
                to_state="blocked",
                reason="runtime crashed",
                session_id="session-1",
                sequence=1,
            ),
        ),
    )

    assert recovered.tasks["task-1"].state == "blocked"
    assert recovered.tasks["task-1"].blocked_reason == "runtime crashed"
    assert recovered.run_records == ()


def test_replay_scheduler_events_recovers_permission_review_required() -> None:
    baseline = SchedulerState(tasks={"task-1": _scheduled_task("task-1")})

    recovered = replay_scheduler_events(
        baseline,
        (
            SchedulerEvent(
                event_id="scheduler-event-1",
                event_kind="task_review_required",
                timestamp="2026-06-16T22:55:00+08:00",
                task_id="task-1",
                from_state="running",
                to_state="review_required",
                reason="permission review required: shell npm test",
                run_id="run-1",
                session_id="session-1",
                output_artifact_id="task-1:result",
                output_artifact_version="v1",
                sequence=1,
            ),
        ),
    )

    assert recovered.tasks["task-1"].state == "review_required"
    assert recovered.tasks["task-1"].blocked_reason == "permission review required: shell npm test"
    assert recovered.tasks["task-1"].output_artifact_ref is not None
    assert recovered.tasks["task-1"].output_artifact_ref.ref_id == "task-1:result"
    assert len(recovered.run_records) == 1
    assert recovered.run_records[0].state == "review_required"


def test_replay_scheduler_events_recovers_permission_approval_as_complete() -> None:
    baseline = SchedulerState(tasks={"task-1": _scheduled_task("task-1")})

    recovered = replay_scheduler_events(
        baseline,
        (
            SchedulerEvent(
                event_id="scheduler-event-1",
                event_kind="task_review_required",
                timestamp="2026-06-16T23:10:00+08:00",
                task_id="task-1",
                from_state="running",
                to_state="review_required",
                reason="permission review required: shell npm test",
                run_id="run-1",
                session_id="session-1",
                output_artifact_id="task-1:result",
                output_artifact_version="v1",
                sequence=1,
            ),
            SchedulerEvent(
                event_id="scheduler-event-2",
                event_kind="task_permission_approved",
                timestamp="2026-06-16T23:11:00+08:00",
                task_id="task-1",
                from_state="review_required",
                to_state="complete",
                reason="permission approved",
                run_id="run-1",
                session_id="session-1",
                output_artifact_id="task-1:result",
                output_artifact_version="v1",
                sequence=2,
            ),
        ),
    )

    assert recovered.tasks["task-1"].state == "complete"
    assert recovered.tasks["task-1"].blocked_reason == ""
    assert recovered.tasks["task-1"].run_id == "run-1"
    assert recovered.tasks["task-1"].output_artifact_ref is not None
    assert recovered.tasks["task-1"].output_artifact_ref.ref_id == "task-1:result"
    assert len(recovered.run_records) == 1
    assert recovered.run_records[0].state == "complete"


def test_replay_scheduler_events_recovers_permission_rejection_as_blocked() -> None:
    baseline = SchedulerState(tasks={"task-1": _scheduled_task("task-1")})

    recovered = replay_scheduler_events(
        baseline,
        (
            SchedulerEvent(
                event_id="scheduler-event-1",
                event_kind="task_review_required",
                timestamp="2026-06-16T23:20:00+08:00",
                task_id="task-1",
                from_state="running",
                to_state="review_required",
                reason="permission review required: artifact_write src/app.py",
                run_id="run-1",
                session_id="session-1",
                output_artifact_id="task-1:result",
                output_artifact_version="v1",
                sequence=1,
            ),
            SchedulerEvent(
                event_id="scheduler-event-2",
                event_kind="task_permission_rejected",
                timestamp="2026-06-16T23:21:00+08:00",
                task_id="task-1",
                from_state="review_required",
                to_state="blocked",
                reason="write permission denied",
                run_id="run-1",
                session_id="session-1",
                output_artifact_id="task-1:result",
                output_artifact_version="v1",
                sequence=2,
            ),
        ),
    )

    assert recovered.tasks["task-1"].state == "blocked"
    assert recovered.tasks["task-1"].blocked_reason == "write permission denied"
    assert recovered.tasks["task-1"].run_id == "run-1"
    assert recovered.tasks["task-1"].output_artifact_ref is not None
    assert recovered.tasks["task-1"].output_artifact_ref.ref_id == "task-1:result"
    assert len(recovered.run_records) == 1
    assert recovered.run_records[0].state == "blocked"


def test_replay_scheduler_events_rejects_unknown_task_in_strict_mode() -> None:
    event = SchedulerEvent(
        event_id="scheduler-event-1",
        event_kind="task_ready",
        timestamp="2026-06-16T20:30:00+08:00",
        task_id="task-missing",
        from_state="proposed",
        to_state="ready",
        sequence=1,
    )

    with pytest.raises(ValueError, match="snapshot task contract"):
        replay_scheduler_events(SchedulerState(), (event,))

    recovered = replay_scheduler_events(SchedulerState(), (event,), strict=False)
    assert recovered.tasks == {}
    assert recovered.run_records == ()

def test_scheduler_runs_ready_task_through_fake_runtime(tmp_path) -> None:
    store = InMemoryArtifactVersionStore()
    event_log = JsonlCoordinationEventLog(tmp_path / "scheduler-events.jsonl")
    store.put(_accepted_contract_artifact(version="v1"))
    runtime = FakeAgentRuntimeAdapter(
        artifact_store=store,
        event_log=event_log,
        timestamp="2026-06-16T18:00:00+08:00",
    )
    task = _scheduled_task(
        "task-1",
        input_artifact_refs=(
            ExchangeReference(ref_kind="exchange_artifact", ref_id="server-api", version="v1"),
        ),
        output_artifact_id="task-1:result",
    )
    state = SchedulerState(tasks={"task-1": task})

    updated, result = run_ready_task(state, "task-1", runtime=runtime)

    completed = updated.tasks["task-1"]
    assert completed.state == "complete"
    assert completed.run_id == "fake-run-1"
    assert completed.output_artifact_ref is not None
    assert completed.output_artifact_ref.ref_id == "task-1:result"
    assert completed.output_artifact_ref.version == "v1"
    assert updated.run_records[0].run_id == "fake-run-1"
    assert result.output_artifact.artifact_id == "task-1:result"
    assert store.get("task-1:result", "v1").artifact is result.output_artifact
    assert event_log.read_all()[-1].related_run_ids == ("fake-run-1",)


def test_scheduler_state_snapshot_round_trips_task_graph(tmp_path) -> None:
    state = SchedulerState(
        tasks={
            "task-a": _scheduled_task(
                "task-a",
                state="complete",
                edit_lease=EditScopeLease(
                    lease_id="lease-a",
                    task_id="task-a",
                    allowed_artifacts=("src/server.py",),
                    lease_mode="write",
                    expires_at="2026-06-16T19:00:00+08:00",
                ),
                output_artifact_id="task-a:result",
            ),
            "task-b": _scheduled_task(
                "task-b",
                input_artifact_refs=(
                    ExchangeReference(ref_kind="exchange_artifact", ref_id="server-api", version="v1"),
                ),
            ),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-1",
                source_task_id="task-a",
                target_task_id="task-b",
                required_state="complete",
            ),
        ),
    )
    path = tmp_path / "scheduler-state.json"

    written = write_scheduler_state_snapshot(state, path)
    restored = read_scheduler_state_snapshot(path)

    assert written == path
    assert restored.tasks["task-a"].edit_lease is not None
    assert restored.tasks["task-a"].edit_lease.allowed_artifacts == ("src/server.py",)
    assert restored.tasks["task-a"].sandbox_profile.profile_kind == "shared-process"
    assert restored.tasks["task-b"].input_artifact_refs[0].ref_id == "server-api"
    assert restored.dependencies[0].source_task_id == "task-a"
    assert restored.run_records == ()


def test_scheduler_state_snapshot_round_trips_edit_lease_lifecycle(tmp_path) -> None:
    state = SchedulerState(
        tasks={
            "task-a": _scheduled_task(
                "task-a",
                edit_lease=EditScopeLease(
                    lease_id="lease-a",
                    task_id="task-a",
                    allowed_artifacts=("src/app.py",),
                    lease_mode="write",
                ),
            )
        },
        edit_lease_lifecycle={
            "lease-a": EditLeaseLifecycleRecord(
                lease_id="lease-a",
                task_id="task-a",
                state="blocked",
                mode="write",
                allowed_artifacts=("src/app.py",),
                acquired_at="2026-06-20T12:00:00+08:00",
                reason="edit lease conflict with task-b: src/app.py",
                conflict_decision=classify_edit_lease_conflict(
                    SchedulerState(
                        tasks={
                            "task-a": _scheduled_task(
                                "task-a",
                                edit_lease=EditScopeLease(
                                    lease_id="lease-a",
                                    task_id="task-a",
                                    allowed_artifacts=("src/app.py",),
                                    lease_mode="write",
                                ),
                            )
                        }
                    ),
                    _scheduled_task(
                        "task-a",
                        edit_lease=EditScopeLease(
                            lease_id="lease-a",
                            task_id="task-a",
                            allowed_artifacts=("src/app.py",),
                            lease_mode="write",
                        ),
                    ),
                ),
            )
        },
    )
    path = tmp_path / "scheduler-state.json"

    write_scheduler_state_snapshot(state, path)
    restored = read_scheduler_state_snapshot(path)

    record = restored.edit_lease_lifecycle["lease-a"]
    assert record.state == "blocked"
    assert record.mode == "write"
    assert record.allowed_artifacts == ("src/app.py",)
    assert record.conflict_decision is not None
    assert record.conflict_decision.classification == "no_overlap"


def test_scheduler_state_snapshot_round_trips_merge_gates(tmp_path) -> None:
    state = SchedulerState(
        tasks={
            "task-a": _scheduled_task("task-a", state="complete"),
            "task-b": _scheduled_task("task-b", state="complete"),
            "task-c": _scheduled_task("task-c", state="waiting"),
        },
        dependencies=(
            TaskDependency(
                dependency_id="dep-a-c",
                source_task_id="task-a",
                target_task_id="task-c",
            ),
            TaskDependency(
                dependency_id="dep-b-c",
                source_task_id="task-b",
                target_task_id="task-c",
            ),
        ),
        merge_gates=(
            SchedulerMergeGate(
                gate_id="merge-c",
                title="Review merged contract",
                target_task_id="task-c",
                source_task_ids=("task-a", "task-b"),
                dependency_ids=("dep-a-c", "dep-b-c"),
                gate_kind="review",
                state="review_required",
                required_review=True,
                input_artifact_refs=(
                    ExchangeReference(ref_kind="exchange_artifact", ref_id="task-a:result", version="v1"),
                    ExchangeReference(ref_kind="exchange_artifact", ref_id="task-b:result", version="v1"),
                ),
                output_artifact_id="merge-c:decision",
                decision_artifact_ref=ExchangeReference(
                    ref_kind="exchange_artifact",
                    ref_id="merge-c:decision",
                    version="v1",
                ),
                blocked_reason="waiting for guide review",
                created_at="2026-06-17T02:00:00+08:00",
            ),
        ),
    )
    path = tmp_path / "scheduler-state.json"

    write_scheduler_state_snapshot(state, path)
    restored = read_scheduler_state_snapshot(path)

    assert len(restored.merge_gates) == 1
    gate = restored.merge_gates[0]
    assert gate.gate_id == "merge-c"
    assert gate.title == "Review merged contract"
    assert gate.target_task_id == "task-c"
    assert gate.source_task_ids == ("task-a", "task-b")
    assert gate.dependency_ids == ("dep-a-c", "dep-b-c")
    assert gate.gate_kind == "review"
    assert gate.state == "review_required"
    assert gate.required_review is True
    assert gate.input_artifact_refs[0].ref_id == "task-a:result"
    assert gate.output_artifact_id == "merge-c:decision"
    assert gate.decision_artifact_ref is not None
    assert gate.decision_artifact_ref.ref_id == "merge-c:decision"
    assert gate.blocked_reason == "waiting for guide review"
    assert gate.created_at == "2026-06-17T02:00:00+08:00"


def test_restored_scheduler_state_can_continue_ready_task_run(tmp_path) -> None:
    store = InMemoryArtifactVersionStore()
    store.put(_accepted_contract_artifact(version="v1"))
    task = _scheduled_task(
        "task-1",
        input_artifact_refs=(
            ExchangeReference(ref_kind="exchange_artifact", ref_id="server-api", version="v1"),
        ),
        output_artifact_id="task-1:result",
    )
    path = tmp_path / "scheduler-state.json"
    write_scheduler_state_snapshot(SchedulerState(tasks={"task-1": task}), path)
    restored = read_scheduler_state_snapshot(path)
    runtime = FakeAgentRuntimeAdapter(
        artifact_store=store,
        timestamp="2026-06-16T19:00:00+08:00",
    )

    updated, result = run_ready_task(restored, "task-1", runtime=runtime)

    assert updated.tasks["task-1"].state == "complete"
    assert updated.run_records[0].output_artifact_id == "task-1:result"
    assert result.output_artifact.version == "v1"


def test_scheduler_state_snapshot_rejects_unsupported_version(tmp_path) -> None:
    path = tmp_path / "scheduler-state.json"
    path.write_text(
        '{"schema_version": "999", "tasks": [], "dependencies": [], "run_records": []}',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="unsupported scheduler state snapshot version"):
        read_scheduler_state_snapshot(path)


def _accepted_contract_artifact(*, version: str) -> ExchangeArtifact:
    contract = ExchangeContract(
        contract_id="server-api",
        contract_kind="api",
        version=version,
        producer="agent:server",
        status="accepted",
        content={"endpoints": [{"method": "GET", "path": "/state"}]},
    )
    return ExchangeArtifact(
        artifact_id="server-api",
        kind="contract",
        intent="inform",
        producer="agent:server",
        version=version,
        parts=(ExchangePayloadPart(part_type="contract", contract=contract),),
    )


def _all_parts_exchange_artifact() -> ExchangeArtifact:
    contract = ExchangeContract(
        contract_id="server-api",
        contract_kind="api",
        version="v2",
        title="Maze server API",
        producer="agent:server",
        consumers=("agent:client", "agent:test"),
        status="accepted",
        schema_ref=ExchangeReference(
            ref_kind="file",
            ref_id="schema",
            path="docs/server-api.schema.json",
            label="schema",
        ),
        content={"endpoints": [{"method": "POST", "path": "/move"}]},
        compatibility=">=v2",
        supersedes=("server-api@v1",),
        effective_from="2026-06-18T23:00:00+08:00",
    )
    relation = ExchangeRelation(
        relation_id="rel-1",
        relation_kind="produces_contract",
        source=ExchangeReference(ref_kind="task", ref_id="task-server"),
        target=ExchangeReference(ref_kind="contract", ref_id="server-api", version="v2"),
        strength="required",
        reason="server task produced accepted API contract",
        since="2026-06-18T23:01:00+08:00",
    )
    log = ExchangeLog(
        timestamp="2026-06-18T23:02:00+08:00",
        actor="agent:server",
        action="artifact_recorded",
        channel="coordination-event-log",
        summary="Recorded server API contract and validation evidence.",
        related_artifact_ids=("exchange:server-api",),
        related_event_ids=("event:server-api",),
        related_run_ids=("run:server",),
        sequence=3,
        clock="wall",
    )
    return ExchangeArtifact(
        artifact_id="exchange:server-api",
        kind="contract",
        intent="inform",
        producer="agent:server",
        audience=("agent:client", "agent:test"),
        scope=ExchangeScope(
            trajectory_id="local-work:test",
            lane_id="lane:server",
            event_id="event:server-api",
            task_id="task-server",
            context_id="context:server",
            agent_id="agent:server",
            runtime_session_id="session:server",
        ),
        causality=ExchangeCausality(
            replies_to=("exchange:proposal",),
            depends_on=("exchange:maze-contract",),
            supersedes=("exchange:server-api@v1",),
            caused_by=("task-server",),
            correlation_id="corr:maze",
        ),
        lifecycle_state="accepted",
        visibility_policy=VisibilityPolicy(
            audience=("agent:client", "agent:test"),
            cross_lane=True,
            contains_sensitive_content=False,
            redaction_required=False,
        ),
        created_at="2026-06-18T23:00:00+08:00",
        version="v2",
        parts=(
            ExchangePayloadPart(part_type="text", text="Server API contract accepted."),
            ExchangePayloadPart(
                part_type="structured",
                data={"product_type": "api_summary", "endpoint_count": 1},
            ),
            ExchangePayloadPart(
                part_type="ref",
                ref=ExchangeReference(
                    ref_kind="file",
                    ref_id="docs/server-api.md",
                    version="v2",
                    path="docs/server-api.md",
                    label="API doc",
                ),
            ),
            ExchangePayloadPart(
                part_type="artifact_delta",
                data={
                    "artifact_id": "server-api",
                    "version": "v2",
                    "changed_refs": ["docs/server-api.md"],
                },
            ),
            ExchangePayloadPart(part_type="contract", contract=contract),
            ExchangePayloadPart(
                part_type="evidence",
                data={"command": "pytest tests/test_server_api.py", "status": "passed"},
            ),
            ExchangePayloadPart(part_type="relation", relation=relation),
            ExchangePayloadPart(
                part_type="storage_manifest",
                data={"product_type": "scratch_manifest", "entries": []},
            ),
            ExchangePayloadPart(part_type="log", log=log),
        ),
    )


def _scheduled_task(
    task_id: str,
    *,
    agent: AgentSpec | None = None,
    state: ScheduledTaskState = "proposed",
    context_scope: ContextScope | None = None,
    edit_lease: EditScopeLease | None = None,
    sandbox_profile: SandboxProfile | None = None,
    input_artifact_refs: tuple[ExchangeReference, ...] = (),
    output_artifact_id: str = "",
) -> ScheduledTask:
    return ScheduledTask(
        task_id=task_id,
        title=f"Task {task_id}",
        instruction=f"Instruction for {task_id}",
        agent=agent or AgentSpec(agent_id=f"agent:{task_id}", runtime_provider="fake"),
        state=state,
        context_scope=context_scope or ContextScope(context_id=f"context:{task_id}", lane_id="lane-main"),
        edit_lease=edit_lease,
        sandbox_profile=sandbox_profile
        or SandboxProfile(profile_id="shared-process", profile_kind="shared-process"),
        input_artifact_refs=input_artifact_refs,
        acceptance=("complete fake task",),
        output_artifact_id=output_artifact_id,
    )


def _git_worktree_task() -> ScheduledTask:
    return _scheduled_task(
        "task-1",
        state="ready",
        edit_lease=EditScopeLease(
            lease_id="lease-1",
            task_id="task-1",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
        sandbox_profile=SandboxProfile(
            profile_id="worktree",
            profile_kind="git-worktree",
            mount_policy="lease-scoped",
        ),
        input_artifact_refs=(
            ExchangeReference(ref_kind="file", ref_id="readme", path="README.md"),
        ),
    )


def _workflow_git_worktree_task() -> ScheduledTask:
    return _scheduled_task(
        "task-1",
        state="ready",
        edit_lease=EditScopeLease(
            lease_id="lease-1",
            task_id="task-1",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
        sandbox_profile=SandboxProfile(
            profile_id="worktree",
            profile_kind="git-worktree",
            mount_policy="lease-scoped",
        ),
        context_scope=ContextScope(
            context_id="context:task-1",
            lane_id="lane-main",
            required_refs=(
                ExchangeReference(ref_kind="file", ref_id="readme", path="README.md"),
            ),
        ),
        output_artifact_id="task-1:result",
    )


def _state_with_acquired_git_worktree_lease(task: ScheduledTask) -> SchedulerState:
    return SchedulerState(
        tasks={task.task_id: task},
        edit_lease_lifecycle={
            "lease-1": EditLeaseLifecycleRecord(
                lease_id="lease-1",
                task_id=task.task_id,
                state="acquired",
                mode="write",
                allowed_artifacts=("src/app.py",),
                acquired_at="2026-06-21T04:30:00+08:00",
            )
        },
    )


def _git_worktree_allocation(
    task: ScheduledTask,
    *,
    state: str = "allocated",
    cleanup_required: bool,
    cleanup_state: str,
    lifecycle_state: str = "acquired",
    authorized_mounts: tuple[str, ...] = ("src/app.py",),
    denied_mounts: tuple[str, ...] = (),
    reason: str = "",
    cleanup_returncode: int | None = None,
    branch_cleanup_returncode: int | None = None,
) -> SandboxAllocation:
    return SandboxAllocation(
        allocation_id=f"git-worktree:{task.task_id}:worktree",
        provider="git-worktree",
        task_id=task.task_id,
        profile=task.sandbox_profile,
        state=state,
        workspace_root="E:/workspace/project",
        scratch_path=".codex/scratch/task-1",
        visible_mounts=("README.md", *authorized_mounts),
        network_policy=task.sandbox_profile.network_policy,
        secret_policy=task.sandbox_profile.secret_policy,
        cleanup_required=cleanup_required,
        lease_authorized_mounts=(
            SandboxLeaseMountAuthorization(
                lease_id="lease-1",
                task_id=task.task_id,
                lifecycle_state=lifecycle_state,
                authorized_mounts=authorized_mounts,
                denied_mounts=denied_mounts,
                reason=reason or "lease-scoped mounts authorized by acquired edit lease lease-1",
            ),
        ),
        lease_authorization_state="rejected" if denied_mounts else "authorized",
        lease_authorization_reason=reason
        or "lease-scoped mounts authorized by acquired edit lease lease-1",
        git_worktree_receipt=GitWorktreeSandboxReceipt(
            source_repository_root="E:/workspace/project",
            sandbox_root="E:/workspace/sandboxes",
            worktree_path="E:/workspace/sandboxes/task-1-worktree",
            branch_name="dbc-sandbox/task-1-worktree",
            base_ref="HEAD",
            authorized_writable_paths=authorized_mounts,
            denied_writable_paths=denied_mounts,
            cleanup_state=cleanup_state,
            allocation=GitWorktreeCommandReceipt(
                command=("git", "-C", "E:/workspace/project", "worktree", "add"),
                returncode=0 if state == "allocated" else 128,
                stdout="allocated" if state == "allocated" else "",
                stderr="" if state == "allocated" else reason,
            ),
            cleanup=GitWorktreeCommandReceipt(
                command=("git", "worktree", "remove", "--force")
                if cleanup_returncode is not None
                else (),
                returncode=cleanup_returncode,
            ),
            branch_cleanup=GitWorktreeCommandReceipt(
                command=("git", "branch", "-D")
                if branch_cleanup_returncode is not None
                else (),
                returncode=branch_cleanup_returncode,
            ),
        ),
        reason=reason,
    )


def _allocated_git_worktree_for_cleanup(tmp_path: Path, repo: Path) -> SandboxAllocation:
    provider = GitWorktreeSandboxProvider(tmp_path / "sandboxes")
    allocation = provider.allocate(
        SandboxRequest(
            task_id="task-1",
            profile=SandboxProfile(
                profile_id="worktree",
                profile_kind="git-worktree",
                network_policy="disabled",
                secret_policy="deny",
                mount_policy="lease-scoped",
            ),
            edit_lease=EditScopeLease(
                lease_id="lease-1",
                task_id="task-1",
                allowed_artifacts=("src/app.py",),
                lease_mode="write",
            ),
            edit_lease_lifecycle=EditLeaseLifecycleRecord(
                lease_id="lease-1",
                task_id="task-1",
                state="acquired",
                mode="write",
                allowed_artifacts=("src/app.py",),
                acquired_at="2026-06-21T06:00:00+08:00",
            ),
            workspace_root=str(repo),
            scratch_path=".codex/scratch/task-1",
            required_mounts=("README.md",),
        )
    )
    assert allocation.state == "allocated"
    assert allocation.cleanup_required is True
    return allocation


def _git_repo(tmp_path: Path) -> Path:
    if shutil.which("git") is None:
        pytest.skip("git executable is required for git-worktree sandbox provider tests")
    repo = tmp_path / "repo"
    repo.parent.mkdir(parents=True, exist_ok=True)
    repo.mkdir()
    (repo / "README.md").write_text("# test repo\n", encoding="utf-8")
    (repo / "src").mkdir()
    (repo / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")
    _run_git(repo, "init")
    _run_git(repo, "config", "user.email", "tests@example.invalid")
    _run_git(repo, "config", "user.name", "Doc Based Coding Tests")
    _run_git(repo, "add", ".")
    _run_git(repo, "commit", "-m", "initial")
    return repo


def _worker_patch_review_store(
    tmp_path: Path,
    *,
    source_repo: Path,
    target_surface: str,
) -> tuple[Path, str]:
    registry = SandboxProviderRegistry()
    provider = GitWorktreeSandboxProvider(tmp_path / "sandboxes")
    registry.register(provider)
    task = _scheduled_task(
        "task-1",
        state="ready",
        agent=AgentSpec(agent_id="agent:codex-worker", runtime_provider="codex"),
        edit_lease=EditScopeLease(
            lease_id="lease-1",
            task_id="task-1",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
        sandbox_profile=SandboxProfile(
            profile_id="worktree",
            profile_kind="git-worktree",
            mount_policy="lease-scoped",
        ),
        output_artifact_id="task-1:result",
    )
    state = SchedulerState(
        tasks={"task-1": task},
        edit_lease_lifecycle={
            "lease-1": EditLeaseLifecycleRecord(
                lease_id="lease-1",
                task_id="task-1",
                state="acquired",
                mode="write",
                allowed_artifacts=("src/app.py",),
            )
        },
    )
    bundle = build_orchestration_preflight_bundle(
        task,
        sandbox_registry=registry,
        scheduler_state=state,
        workspace_root=str(source_repo),
    )
    receipt = bundle.sandbox_allocation.git_worktree_receipt
    assert receipt is not None
    app = Path(receipt.worktree_path) / "src" / "app.py"
    app.write_text("print('worker patch')\n", encoding="utf-8")
    run = PreflightedTaskRunResult(
        preflight=bundle,
        state=state,
        runtime_result=RuntimeRunResult(
            run_handle=RunHandle(
                run_id="codex-run-1",
                session_id="codex-session-1",
                task_id="task-1",
            ),
            output_artifact=ExchangeArtifact(
                artifact_id="task-1:result",
                kind="result",
                intent="inform",
                producer="agent:codex-worker",
                version="v1",
            ),
            artifact_delta=ArtifactDelta(
                artifact_id="task-1:result",
                version="v1",
                summary="worker changed src/app.py",
                changed_refs=(
                    ExchangeReference(
                        ref_kind="file",
                        ref_id="src/app.py",
                        path="src/app.py",
                    ),
                ),
            ),
        ),
    )
    review = build_worker_patch_review_artifact(
        run,
        timestamp="2026-06-24T23:58:00+08:00",
        guide_agent_id="agent:guide",
        target_task_id="task:merge-target",
    )
    store_path = tmp_path / "exchange-artifacts.json"
    JsonArtifactVersionStore(store_path).put(review.artifact)
    disposition_id = "task-1:patch-review-decision"
    decide_agent_exchange_action_candidate(
        store_path=store_path,
        candidate_id="task-1:patch-review@v1:merge",
        disposition_artifact_id=disposition_id,
        actor="agent:guide",
        disposition="accept",
        target_surface=target_surface,
        timestamp="2026-06-24T23:58:30+08:00",
    )
    provider.cleanup(bundle.sandbox_allocation)
    return store_path, disposition_id


def _patch_for_file_change(
    workspace_root: Path,
    *,
    relative_path: str,
    original: str,
    changed: str,
) -> str:
    repo = _git_repo(workspace_root)
    target = repo / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(original, encoding="utf-8")
    _run_git(repo, "add", ".")
    staged = subprocess.run(
        ("git", "-C", str(repo), "diff", "--cached", "--quiet"),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if staged.returncode == 1:
        _run_git(repo, "commit", "-m", "baseline for patch")
    target.write_text(changed, encoding="utf-8")
    return _run_git(repo, "diff", "--binary").stdout


def _store_worker_patch_artifact(
    store_path: Path,
    *,
    artifact_id: str,
    task_id: str,
    lane_id: str,
    worker_agent_id: str,
    changed_path: str,
    patch_text: str,
) -> None:
    JsonArtifactVersionStore(store_path).put(
        ExchangeArtifact(
            artifact_id=artifact_id,
            version="v1",
            kind="proposal",
            intent="request_merge",
            producer=worker_agent_id,
            audience=("agent:guide",),
            lifecycle_state="proposed",
            parts=(
                ExchangePayloadPart(part_type="text", text="Worker patch review proposal."),
                ExchangePayloadPart(
                    part_type="structured",
                    data={
                        "product_type": "worker_patch_review_proposal",
                        "task_id": task_id,
                        "lane_id": lane_id,
                        "worker_agent_id": worker_agent_id,
                        "runtime_provider": "codex",
                        "sandbox_provider": "git-worktree",
                        "sandbox_allocation_id": f"allocation:{task_id}",
                        "changed_paths": [changed_path],
                        "patch_state": "has_patch",
                    },
                ),
                ExchangePayloadPart(
                    part_type="evidence",
                    data={"git_diff": patch_text},
                ),
                ExchangePayloadPart(
                    part_type="relation",
                    relation=ExchangeRelation(
                        relation_id=f"relation:{task_id}:merge-target",
                        relation_kind="merges_into",
                        source=ExchangeReference(
                            ref_kind="exchange_artifact",
                            ref_id=artifact_id,
                            version="v1",
                        ),
                        target=ExchangeReference(ref_kind="scheduler_task", ref_id=task_id),
                    ),
                ),
            ),
        )
    )


def _run_git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        ("git", "-C", str(repo), *args),
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if completed.returncode != 0:
        raise AssertionError(
            f"git {' '.join(args)} failed with {completed.returncode}: "
            f"{completed.stderr or completed.stdout}"
        )
    return completed


def _supervisor_storage_binding_evidence_summary(
    tmp_path: Path,
) -> tuple[SupervisorStorageBindingEvidenceSummary, Path, object]:
    workflow = run_scheduler_supervisor_dogfood_workflow(
        SchedulerSupervisorDogfoodWorkflowRequest(
            project_root=tmp_path,
            fixture="simple",
            timestamp="2026-06-21T11:20:00+00:00",
            supervisor_id="supervisor:evidence",
            session_id="session:evidence",
            run_id="run:evidence",
            host_id="host:evidence",
            requested_by="agent:guide",
        )
    )
    binding = build_supervisor_dogfood_storage_binding(
        workflow,
        agent_id="agent:supervisor-evidence",
        context_session_id="context-session:evidence",
    )
    evidence = build_supervisor_storage_binding_evidence(
        binding,
        evidence_id="supervisor-binding:evidence",
        timestamp="2026-06-21T11:20:01+00:00",
        metadata={"workflow_surface": "supervisor-dogfood-workflow"},
    )
    evidence_path = default_supervisor_storage_binding_evidence_path(
        tmp_path,
        evidence.evidence_id,
    )
    write = write_supervisor_storage_binding_evidence(evidence, evidence_path)
    summary = read_supervisor_storage_binding_evidence_summary(write.evidence_path)
    return summary, evidence_path, workflow


class _FailingRuntime:
    def __init__(self, message: str) -> None:
        self.message = message

    def capabilities(self) -> RuntimeCapabilities:
        return RuntimeCapabilities(provider="fake")

    def start_session(self, agent: AgentSpec) -> SessionHandle:
        return SessionHandle(
            session_id=f"failed-session:{agent.agent_id}",
            provider="fake",
            agent_id=agent.agent_id,
        )

    def run_task(self, session: SessionHandle, task: TaskSpec) -> RuntimeRunResult:
        raise RuntimeError(self.message)


class _SelectiveFailingRuntime(FakeAgentRuntimeAdapter):
    def __init__(
        self,
        *,
        failing_task_ids: tuple[str, ...],
        artifact_store: InMemoryArtifactVersionStore,
        timestamp: str,
    ) -> None:
        super().__init__(artifact_store=artifact_store, timestamp=timestamp)
        self.failing_task_ids = set(failing_task_ids)

    def run_task(self, session: SessionHandle, task: TaskSpec) -> RuntimeRunResult:
        if task.task_id in self.failing_task_ids:
            raise RuntimeError(f"runtime failed task {task.task_id}")
        return super().run_task(session, task)


class _RecordingQoderClient:
    def __init__(self, result: QoderQueryResult) -> None:
        self.result = result
        self.requests: tuple[QoderQueryRequest, ...] = ()

    def query(self, request: QoderQueryRequest) -> QoderQueryResult:
        self.requests = self.requests + (request,)
        return self.result


class _RecordingCodexCliClient:
    def __init__(self, result: CodexCliResult) -> None:
        self.result = result
        self.requests: tuple[CodexCliRequest, ...] = ()

    def exec(self, request: CodexCliRequest) -> CodexCliResult:
        self.requests = self.requests + (request,)
        return self.result


class _RecordingOpenCodeCliClient:
    def __init__(self, result: OpenCodeCliResult) -> None:
        self.result = result
        self.requests: tuple[OpenCodeCliRequest, ...] = ()

    def exec(self, request: OpenCodeCliRequest) -> OpenCodeCliResult:
        self.requests = self.requests + (request,)
        return self.result


class _EditingCodexCliClient:
    def __init__(self, *, relative_path: str, content: str) -> None:
        self.relative_path = relative_path
        self.content = content
        self.requests: tuple[CodexCliRequest, ...] = ()

    def exec(self, request: CodexCliRequest) -> CodexCliResult:
        self.requests = self.requests + (request,)
        workspace = Path(request.task.runtime_workspace_root)
        if not workspace:
            raise AssertionError("editing Codex test client requires runtime workspace root")
        target = workspace / self.relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.content, encoding="utf-8")
        return CodexCliResult(
            summary=f"edited {self.relative_path}",
            output_text=f"edited {self.relative_path}",
            artifact_delta=ArtifactDelta(
                artifact_id=request.output_artifact_id or f"{request.task.task_id}:codex-result",
                version="v1",
                summary=f"edited {self.relative_path}",
                changed_refs=(
                    ExchangeReference(
                        ref_kind="file",
                        ref_id=self.relative_path,
                        path=self.relative_path,
                    ),
                ),
            ),
        )


class _EditingOpenCodeCliClient:
    def __init__(self, *, relative_path: str, content: str) -> None:
        self.relative_path = relative_path
        self.content = content
        self.requests: tuple[OpenCodeCliRequest, ...] = ()

    def exec(self, request: OpenCodeCliRequest) -> OpenCodeCliResult:
        self.requests = self.requests + (request,)
        workspace = Path(request.task.runtime_workspace_root)
        if not workspace:
            raise AssertionError("editing OpenCode test client requires runtime workspace root")
        target = workspace / self.relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.content, encoding="utf-8")
        return OpenCodeCliResult(
            summary=f"edited {self.relative_path}",
            output_text=f"edited {self.relative_path}",
            artifact_delta=ArtifactDelta(
                artifact_id=request.output_artifact_id or f"{request.task.task_id}:opencode-result",
                version="v1",
                summary=f"edited {self.relative_path}",
                changed_refs=(
                    ExchangeReference(
                        ref_kind="file",
                        ref_id=self.relative_path,
                        path=self.relative_path,
                    ),
                ),
            ),
        )


class _SequenceCodexCliClient:
    def __init__(self, results: tuple[CodexCliResult, ...]) -> None:
        self.results = results
        self.requests: tuple[CodexCliRequest, ...] = ()

    def exec(self, request: CodexCliRequest) -> CodexCliResult:
        self.requests = self.requests + (request,)
        index = len(self.requests) - 1
        if index >= len(self.results):
            raise AssertionError("Codex client was invoked more times than expected")
        return self.results[index]


class _SequenceOpenCodeCliClient:
    def __init__(self, results: tuple[OpenCodeCliResult, ...]) -> None:
        self.results = results
        self.requests: tuple[OpenCodeCliRequest, ...] = ()

    def exec(self, request: OpenCodeCliRequest) -> OpenCodeCliResult:
        self.requests = self.requests + (request,)
        index = len(self.requests) - 1
        if index >= len(self.results):
            raise AssertionError("OpenCode client was invoked more times than expected")
        return self.results[index]


class _UnavailableCodexCliClient:
    def __init__(self) -> None:
        self.requests: tuple[CodexCliRequest, ...] = ()

    def host_readiness_report(self) -> CodexCliHostReadinessReport:
        return CodexCliHostReadinessReport(
            executable="missing-codex",
            executable_resolved="",
            cli_available=False,
            ready=False,
            error_kind="cli_unavailable",
            raw_error_type="MissingExecutable",
            summary="Codex CLI executable is unavailable: missing-codex",
        )

    def exec(self, request: CodexCliRequest) -> CodexCliResult:
        self.requests = self.requests + (request,)
        raise AssertionError("unavailable Codex client should not be invoked")


class _UnavailableOpenCodeCliClient:
    def __init__(self) -> None:
        self.requests: tuple[OpenCodeCliRequest, ...] = ()

    def host_readiness_report(self) -> OpenCodeCliHostReadinessReport:
        return OpenCodeCliHostReadinessReport(
            executable="missing-opencode",
            executable_resolved="",
            cli_available=False,
            ready=False,
            error_kind="cli_unavailable",
            raw_error_type="MissingExecutable",
            summary="OpenCode CLI executable is unavailable: missing-opencode",
        )

    def exec(self, request: OpenCodeCliRequest) -> OpenCodeCliResult:
        self.requests = self.requests + (request,)
        raise AssertionError("unavailable OpenCode client should not be invoked")


class _FailingCodexCliClient:
    def __init__(self, exc: Exception) -> None:
        self.exc = exc
        self.requests: tuple[CodexCliRequest, ...] = ()

    def exec(self, request: CodexCliRequest) -> CodexCliResult:
        self.requests = self.requests + (request,)
        raise self.exc


class _SequenceCodexCliClientWithFailures:
    def __init__(self, outcomes: tuple[object, ...]) -> None:
        self.outcomes = outcomes
        self.requests: tuple[CodexCliRequest, ...] = ()

    def exec(self, request: CodexCliRequest) -> CodexCliResult:
        self.requests = self.requests + (request,)
        index = len(self.requests) - 1
        if index >= len(self.outcomes):
            raise AssertionError("Codex client was invoked more times than expected")
        outcome = self.outcomes[index]
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome  # type: ignore[return-value]


class _BarrierCodexCliClient:
    def __init__(
        self,
        *,
        expected_concurrent_calls: int,
        hold_after_barrier_seconds: float = 0.0,
    ) -> None:
        self.expected_concurrent_calls = expected_concurrent_calls
        self.hold_after_barrier_seconds = hold_after_barrier_seconds
        self.requests: tuple[CodexCliRequest, ...] = ()
        self.first_batch_task_ids: tuple[str, ...] = ()
        self.active_calls = 0
        self.max_active_calls = 0
        self._lock = threading.Lock()
        self._barrier = threading.Barrier(expected_concurrent_calls, timeout=5.0)

    def exec(self, request: CodexCliRequest) -> CodexCliResult:
        wait_for_batch = False
        with self._lock:
            self.requests = self.requests + (request,)
            self.active_calls += 1
            self.max_active_calls = max(self.max_active_calls, self.active_calls)
            if len(self.requests) <= self.expected_concurrent_calls:
                self.first_batch_task_ids = self.first_batch_task_ids + (
                    request.task.task_id,
                )
                wait_for_batch = True
        try:
            if wait_for_batch:
                self._barrier.wait()
                if self.hold_after_barrier_seconds:
                    time.sleep(self.hold_after_barrier_seconds)
            return CodexCliResult(
                summary=f"{request.task.task_id} complete",
                output_text=f"{request.task.task_id} complete",
            )
        finally:
            with self._lock:
                self.active_calls -= 1


class _BarrierOpenCodeCliClient:
    def __init__(
        self,
        *,
        expected_concurrent_calls: int,
        hold_after_barrier_seconds: float = 0.0,
    ) -> None:
        self.expected_concurrent_calls = expected_concurrent_calls
        self.hold_after_barrier_seconds = hold_after_barrier_seconds
        self.requests: tuple[OpenCodeCliRequest, ...] = ()
        self.first_batch_task_ids: tuple[str, ...] = ()
        self.active_calls = 0
        self.max_active_calls = 0
        self._lock = threading.Lock()
        self._barrier = threading.Barrier(expected_concurrent_calls, timeout=5.0)

    def exec(self, request: OpenCodeCliRequest) -> OpenCodeCliResult:
        wait_for_batch = False
        with self._lock:
            self.requests = self.requests + (request,)
            self.active_calls += 1
            self.max_active_calls = max(self.max_active_calls, self.active_calls)
            if len(self.requests) <= self.expected_concurrent_calls:
                self.first_batch_task_ids = self.first_batch_task_ids + (
                    request.task.task_id,
                )
                wait_for_batch = True
        try:
            if wait_for_batch:
                self._barrier.wait()
                if self.hold_after_barrier_seconds:
                    time.sleep(self.hold_after_barrier_seconds)
            return OpenCodeCliResult(
                summary=f"{request.task.task_id} complete",
                output_text=f"{request.task.task_id} complete",
            )
        finally:
            with self._lock:
                self.active_calls -= 1


class _BarrierFailingOpenCodeCliClient(_BarrierOpenCodeCliClient):
    def exec(self, request: OpenCodeCliRequest) -> OpenCodeCliResult:
        wait_for_batch = False
        with self._lock:
            self.requests = self.requests + (request,)
            self.active_calls += 1
            self.max_active_calls = max(self.max_active_calls, self.active_calls)
            if len(self.requests) <= self.expected_concurrent_calls:
                self.first_batch_task_ids = self.first_batch_task_ids + (
                    request.task.task_id,
                )
                wait_for_batch = True
        try:
            if wait_for_batch:
                self._barrier.wait()
                if self.hold_after_barrier_seconds:
                    time.sleep(self.hold_after_barrier_seconds)
            raise OpenCodeCliRuntimeError(
                error_kind="process_failed",
                summary=f"{request.task.task_id} failed after overlap",
                raw_error_type="SyntheticFailure",
                retryable=False,
            )
        finally:
            with self._lock:
                self.active_calls -= 1


def _state_counts_from_delivery_records(state) -> dict[str, int]:
    counts: dict[str, int] = {}
    for record in state.records.values():
        counts[record.delivery_state] = counts.get(record.delivery_state, 0) + 1
    return dict(sorted(counts.items()))


def _qoder_sdk_request() -> QoderQueryRequest:
    agent = AgentSpec(
        agent_id="agent:qoder-sdk",
        runtime_provider="qoder",
        model="agent-model",
        max_turns=4,
    )
    task = TaskSpec(
        task_id="task-qoder-sdk",
        title="Use Qoder SDK wrapper",
        instruction="Return a compact normalized result.",
        acceptance=("result is normalized", "no secrets are logged"),
        output_artifact_id="task-qoder-sdk:result",
    )
    session = SessionHandle(
        session_id="qoder-session-sdk",
        provider="qoder",
        agent_id=agent.agent_id,
    )
    return QoderQueryRequest(
        agent=agent,
        task=task,
        session=session,
        instruction=task.instruction,
        acceptance=task.acceptance,
        output_artifact_id=task.output_artifact_id,
    )


class _FakeQoderSDK:
    def __init__(
        self,
        *,
        messages,
        trigger_permission: bool = False,
        stream_override=None,
        query_exception: Exception | None = None,
    ) -> None:
        self.messages = tuple(messages)
        self.trigger_permission = trigger_permission
        self.stream_override = stream_override
        self.query_exception = query_exception
        self.auth_calls: list[str] = []
        self.option_kwargs = {}
        self.options_instance = object()
        self.query_prompt = ""
        self.query_options = None

    def access_token_from_env(self):
        self.auth_calls.append("from_env")
        return "auth:env"

    def access_token(self, token):
        self.auth_calls.append("token")
        return f"auth:{token}"

    def qodercli_auth(self):
        self.auth_calls.append("qodercli")
        return "auth:qodercli"

    def QoderAgentOptions(self, **kwargs):
        self.option_kwargs = kwargs
        return self.options_instance

    def query(self, *, prompt, options):
        if self.query_exception is not None:
            raise self.query_exception
        self.query_prompt = prompt
        self.query_options = options
        if self.trigger_permission:
            can_use_tool = self.option_kwargs["can_use_tool"]
            assert can_use_tool(
                {
                    "tool_name": "write",
                    "target": "src/app.py",
                    "summary": "Qoder wants to write src/app.py",
                }
            ) is False
        if self.stream_override is not None:
            return self.stream_override
        return _FakeAsyncMessageStream(self.messages)


class _FakeAsyncMessageStream:
    def __init__(self, messages) -> None:
        self._messages = tuple(messages)

    def __aiter__(self):
        self._iterator = iter(self._messages)
        return self

    async def __anext__(self):
        await asyncio.sleep(0)
        try:
            return next(self._iterator)
        except StopIteration as exc:
            raise StopAsyncIteration from exc


def test_runtime_invocation_audit_records_success(tmp_path: Path) -> None:
    log = JsonlRuntimeInvocationLog(tmp_path / "invocations.jsonl")

    result = run_with_runtime_invocation_audit(
        invocation_id="inv-1",
        provider="codex",
        operation=lambda: _RuntimeAuditResult(
            summary="completed",
            metadata={"stdout_bytes": 12, "stderr_bytes": 0},
        ),
        log=log,
        task_id="task-1",
        agent_id="agent:worker",
        timestamp_factory=_runtime_audit_clock(),
    )

    assert result.summary == "completed"
    records = log.read_all()
    assert len(records) == 1
    record = records[0]
    assert record.status == "succeeded"
    assert record.provider == "codex"
    assert record.task_id == "task-1"
    assert record.agent_id == "agent:worker"
    assert record.attempt_count == 1
    assert record.attempts[0].stdout_bytes == 12
    assert record.to_json_dict()["authority_split"]["raw_transcript_persisted"] is False


def test_runtime_invocation_audit_retries_retryable_failure(tmp_path: Path) -> None:
    log = JsonlRuntimeInvocationLog(tmp_path / "invocations.jsonl")
    calls = {"count": 0}

    def operation():
        calls["count"] += 1
        if calls["count"] == 1:
            raise _RetryableRuntimeAuditError("timeout")
        return _RuntimeAuditResult(summary="recovered")

    result = run_with_runtime_invocation_audit(
        invocation_id="inv-retry",
        provider="qoder",
        operation=operation,
        log=log,
        retry_policy=RuntimeRetryPolicy(max_attempts=2),
        timestamp_factory=_runtime_audit_clock(),
    )

    assert result.summary == "recovered"
    assert calls["count"] == 2
    record = log.read_all()[0]
    assert record.status == "succeeded"
    assert record.attempt_count == 2
    assert [attempt.status for attempt in record.attempts] == ["failed", "succeeded"]
    assert "secret" not in record.attempts[0].summary


def test_runtime_invocation_audit_fail_fast_for_non_retryable(tmp_path: Path) -> None:
    log = JsonlRuntimeInvocationLog(tmp_path / "invocations.jsonl")

    with pytest.raises(_FatalRuntimeAuditError):
        run_with_runtime_invocation_audit(
            invocation_id="inv-fatal",
            provider="codex",
            operation=lambda: (_ for _ in ()).throw(_FatalRuntimeAuditError("auth")),
            log=log,
            retry_policy=RuntimeRetryPolicy(max_attempts=3),
            timestamp_factory=_runtime_audit_clock(),
        )

    record = log.read_all()[0]
    assert record.status == "failed"
    assert record.attempt_count == 1
    assert record.final_error_kind == "authentication_failed"


def test_runtime_invocation_log_inspection_and_compaction(tmp_path: Path) -> None:
    log_path = tmp_path / "invocations.jsonl"
    log = JsonlRuntimeInvocationLog(log_path)
    for index in range(3):
        run_with_runtime_invocation_audit(
            invocation_id=f"inv-{index}",
            provider="fake",
            operation=lambda index=index: _RuntimeAuditResult(summary=f"ok {index}"),
            log=log,
            timestamp_factory=_runtime_audit_clock(),
        )

    summary = inspect_runtime_invocation_log(log_path, latest_limit=2)
    assert summary.record_count == 3
    assert summary.succeeded_count == 3
    assert [record.invocation_id for record in summary.latest_records] == ["inv-1", "inv-2"]

    compacted = compact_runtime_invocation_log(
        log_path,
        tmp_path / "archive.jsonl",
        retain_latest=1,
    )

    assert compacted.archived_count == 2
    assert compacted.retained_count == 1
    assert [record.invocation_id for record in JsonlRuntimeInvocationLog(log_path).read_all()] == ["inv-2"]


def test_worker_binding_promotion_candidate_readback_from_runtime_invocation_log(
    tmp_path: Path,
) -> None:
    log_path = tmp_path / ".codex/runtime/opencode-delivery-invocations.jsonl"
    JsonlRuntimeInvocationLog(log_path).append(
        RuntimeInvocationRecord(
            invocation_id="inv-opencode-server-api",
            provider="opencode",
            status="succeeded",
            started_at="2026-07-01T10:00:00+00:00",
            ended_at="2026-07-01T10:00:01+00:00",
            task_id="task-server",
            agent_id="agent:server",
            runtime_surface="opencode-delivery-supervisor",
            attempt_count=1,
            attempts=(
                RuntimeAttemptRecord(
                    attempt_index=1,
                    started_at="2026-07-01T10:00:00+00:00",
                    ended_at="2026-07-01T10:00:01+00:00",
                    status="succeeded",
                    metadata={
                        "transport": "server-api",
                        "base_url": "http://127.0.0.1:4096",
                        "session_id": "session-created-api",
                        "created_session": True,
                        "session_selector_source": "server_api_created",
                    },
                ),
            ),
            metadata={
                "lane_id": "lane:server",
                "context_id": "ctx:server",
                "session_selector_source": "none",
            },
        )
    )

    result = inspect_worker_binding_promotion_candidates(
        WorkerBindingPromotionCandidateReadbackRequest(
            runtime_invocation_log_path=log_path,
        )
    )

    assert result.ok is True
    assert result.exists is True
    assert result.candidate_count == 1
    candidate = result.candidates[0]
    assert candidate.provider == "opencode"
    assert candidate.session_selector_source == "server_api_created"
    assert candidate.attach_url == "http://127.0.0.1:4096"
    assert candidate.session_id == "session-created-api"
    assert candidate.source_audit_ref.endswith(
        "opencode-delivery-invocations.jsonl#inv-opencode-server-api:attempt-1"
    )
    assert candidate.suggested_worker_id == "worker:lane-server"
    assert candidate.suggested_scope_kind == "lane"
    assert candidate.suggested_scope_id == "lane:server"
    assert "--audit-ref" in candidate.suggested_command
    payload = result.to_json_dict()
    assert payload["authority_split"]["continuous_worker_binding_ledger_mutated"] is False
    assert payload["authority_split"]["runtime_invocation_log_mutated"] is False
    assert payload["authority_split"]["raw_transcript_exposed"] is False
    assert "transcript body" not in json.dumps(payload)
    assert "secret-token" not in json.dumps(payload)
    assert not (tmp_path / ".codex/runtime/continuous-worker-bindings.json").exists()


def test_worker_binding_promotion_candidate_readback_filters_non_created_sources(
    tmp_path: Path,
) -> None:
    log_path = tmp_path / ".codex/runtime/invocations.jsonl"
    log = JsonlRuntimeInvocationLog(log_path)
    log.append(
        RuntimeInvocationRecord(
            invocation_id="inv-explicit",
            provider="opencode",
            status="succeeded",
            started_at="2026-07-01T10:00:00+00:00",
            ended_at="2026-07-01T10:00:01+00:00",
            attempt_count=1,
            attempts=(
                RuntimeAttemptRecord(
                    attempt_index=1,
                    started_at="2026-07-01T10:00:00+00:00",
                    ended_at="2026-07-01T10:00:01+00:00",
                    status="succeeded",
                    metadata={
                        "base_url": "http://127.0.0.1:4096",
                        "session_id": "session-explicit",
                        "created_session": False,
                        "session_selector_source": "explicit_config",
                    },
                ),
            ),
        )
    )
    log.append(
        RuntimeInvocationRecord(
            invocation_id="inv-codex",
            provider="codex",
            status="succeeded",
            started_at="2026-07-01T10:00:02+00:00",
            ended_at="2026-07-01T10:00:03+00:00",
            attempt_count=1,
            attempts=(
                RuntimeAttemptRecord(
                    attempt_index=1,
                    started_at="2026-07-01T10:00:02+00:00",
                    ended_at="2026-07-01T10:00:03+00:00",
                    status="succeeded",
                    metadata={"session_selector_source": "server_api_created"},
                ),
            ),
        )
    )

    result = inspect_worker_binding_promotion_candidates(
        WorkerBindingPromotionCandidateReadbackRequest(runtime_invocation_log_path=log_path)
    )

    assert result.ok is True
    assert result.candidate_count == 0
    assert result.skipped_count == 2
    assert result.skip_reasons["not_server_api_created"] == 1
    assert result.skip_reasons["provider_not_opencode"] == 1


def test_leader_worker_policy_recommends_single_lane_and_requires_multilane() -> None:
    single = evaluate_leader_worker_policy(["lane:client"])
    multi = evaluate_leader_worker_policy(["lane:client", "lane:server"])

    assert single.leader_worker_recommended is True
    assert single.leader_worker_required is False
    assert multi.leader_worker_required is True


def test_leader_worker_activation_wakes_leader_on_new_worker_message_once() -> None:
    record = ArtifactVersionRecord(
        artifact_id="ex-worker-reply",
        version="v1",
        artifact=ExchangeArtifact(
            artifact_id="ex-worker-reply",
            version="v1",
            kind="message",
            intent="inform",
            producer="agent:worker",
            audience=("agent:guide",),
            lifecycle_state="proposed",
            parts=(ExchangePayloadPart(part_type="text", text="done"),),
        ),
    )

    first = run_leader_worker_activation_pass(
        scheduler_state=SchedulerState(),
        exchange_records=(record,),
        leader_agent_id="agent:guide",
        worker_agent_ids=("agent:worker",),
    )

    leader = next(item for item in first.lifecycles if item.agent_id == "agent:guide")
    assert leader.lifecycle_state == "runnable"
    assert leader.new_message_sources == ("ex-worker-reply@v1",)
    assert any(event.event_kind == "message_available" for event in first.events)

    second = run_leader_worker_activation_pass(
        scheduler_state=SchedulerState(),
        exchange_records=(record,),
        activation_state=first.next_state,
    )
    leader_second = next(item for item in second.lifecycles if item.agent_id == "agent:guide")
    assert leader_second.lifecycle_state == "waiting_message"
    assert leader_second.new_message_sources == ()


def test_leader_worker_activation_reports_ready_and_waiting_worker_tasks() -> None:
    state = SchedulerState(
        tasks={
            "task-ready": ScheduledTask(
                task_id="task-ready",
                title="Ready worker",
                instruction="Run ready worker",
                agent=AgentSpec(agent_id="agent:worker-a", runtime_provider="fake"),
                state="ready",
                context_scope=ContextScope(context_id="ctx-a", lane_id="lane:a"),
            ),
            "task-waiting": ScheduledTask(
                task_id="task-waiting",
                title="Waiting worker",
                instruction="Wait for dependency",
                agent=AgentSpec(agent_id="agent:worker-b", runtime_provider="fake"),
                state="waiting",
                context_scope=ContextScope(context_id="ctx-b", lane_id="lane:b"),
                blocked_reason="waiting for task-ready to complete",
            ),
        }
    )

    result = run_leader_worker_activation_pass(
        scheduler_state=state,
        exchange_records=(),
        worker_agent_ids=("agent:worker-a", "agent:worker-b"),
    )

    worker_a = next(item for item in result.lifecycles if item.agent_id == "agent:worker-a")
    worker_b = next(item for item in result.lifecycles if item.agent_id == "agent:worker-b")
    assert result.policy.leader_worker_required is True
    assert worker_a.lifecycle_state == "runnable"
    assert worker_a.ready_task_ids == ("task-ready",)
    assert worker_b.lifecycle_state == "waiting_dependency"
    assert worker_b.waiting_task_ids == ("task-waiting",)
    assert any(event.event_kind == "leader_required" for event in result.events)
    assert any(event.event_kind == "task_ready" for event in result.events)
    assert any(event.event_kind == "dependency_wait" for event in result.events)


def test_leader_worker_activation_honors_existing_mailbox_cursor() -> None:
    record = ArtifactVersionRecord(
        artifact_id="ex-old",
        version="v1",
        artifact=ExchangeArtifact(
            artifact_id="ex-old",
            version="v1",
            kind="message",
            intent="inform",
            producer="agent:worker",
            audience=("agent:guide",),
            lifecycle_state="proposed",
        ),
    )
    activation_state = LeaderWorkerActivationState(
        leader_agent_id="agent:guide",
        worker_agent_ids=("agent:worker",),
        mailbox_cursors={
            "agent:guide": AgentMailboxCursor(
                agent_id="agent:guide",
                consumed_sources=("ex-old@v1",),
            )
        },
    )

    result = run_leader_worker_activation_pass(
        scheduler_state=SchedulerState(),
        exchange_records=(record,),
        activation_state=activation_state,
    )

    leader = next(item for item in result.lifecycles if item.agent_id == "agent:guide")
    assert leader.new_message_sources == ()
    assert leader.lifecycle_state == "waiting_message"


def test_leader_worker_dispatcher_tick_persists_decisions_and_state(tmp_path: Path) -> None:
    paths = _seed_leader_worker_dispatcher_inputs(tmp_path)

    result = run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-25T12:00:00+00:00",
        )
    )
    state = read_leader_worker_dispatcher_state(paths["dispatcher_state"])
    records = JsonlLeaderWorkerDispatcherEventLog(paths["dispatch_log"]).read_all()

    assert result.tick_record.decision_count == 4
    assert {decision.event_kind for decision in result.decisions} == {
        "leader_required",
        "message_available",
        "task_ready",
        "dependency_wait",
    }
    assert state is not None
    assert state.tick_count == 1
    assert state.last_result_summary["decision_count"] == 4
    assert len(state.emitted_source_keys) == 4
    assert len(records) == 1
    assert records[0].decision_count == 4
    assert result.to_json_dict()["authority_split"]["provider_executed"] is False
    assert result.to_json_dict()["authority_split"]["scheduler_state_mutated"] is False


def test_leader_worker_dispatcher_tick_after_restart_suppresses_existing_decisions(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs(tmp_path)
    request = LeaderWorkerDispatcherTickRequest(
        dispatcher_state_path=paths["dispatcher_state"],
        dispatch_event_log_path=paths["dispatch_log"],
        scheduler_snapshot_path=paths["snapshot"],
        scheduler_event_log_path=paths["event_log"],
        artifact_store_path=paths["artifact_store"],
        worker_agent_ids=("agent:server", "agent:client"),
        timestamp="2026-06-25T12:00:00+00:00",
    )

    first = run_leader_worker_dispatcher_tick(request)
    second = run_leader_worker_dispatcher_tick(request)
    records = JsonlLeaderWorkerDispatcherEventLog(paths["dispatch_log"]).read_all()

    assert first.tick_record.decision_count == 4
    assert second.tick_record.decision_count == 0
    assert second.tick_record.suppressed_decision_count == 3
    assert (
        second.state_after.activation_state.mailbox_cursors["agent:guide"].consumed_sources
        == ("ex-server-report@v1",)
    )
    assert second.state_after.tick_count == 2
    assert len(records) == 2


def test_leader_worker_dispatcher_loop_stops_when_no_new_decisions(tmp_path: Path) -> None:
    paths = _seed_leader_worker_dispatcher_inputs(tmp_path)
    request = LeaderWorkerDispatcherLoopRequest(
        tick_request=LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-25T12:00:00+00:00",
        ),
        max_ticks=3,
    )

    result = run_leader_worker_dispatcher_loop(request)

    assert result.tick_count == 2
    assert result.total_decision_count == 4
    assert result.stop_reason == "no_new_dispatch_decisions"
    assert result.iterations[1].tick_record.decision_count == 0


def test_leader_worker_delivery_sync_is_idempotent_over_dispatch_log(tmp_path: Path) -> None:
    paths = _seed_leader_worker_dispatcher_inputs(tmp_path)
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-25T12:00:00+00:00",
        )
    )
    request = LeaderWorkerDeliverySyncRequest(
        delivery_state_path=paths["delivery_state"],
        delivery_event_log_path=paths["delivery_log"],
        dispatch_event_log_path=paths["dispatch_log"],
        timestamp="2026-06-25T12:00:01+00:00",
        host_id="host:test",
    )

    first = sync_leader_worker_delivery_from_dispatch_log(request)
    second = sync_leader_worker_delivery_from_dispatch_log(request)
    state = read_leader_worker_delivery_state(paths["delivery_state"])
    events = JsonlLeaderWorkerDeliveryEventLog(paths["delivery_log"]).read_all()

    assert first.synced_count == 4
    assert first.to_json_dict()["state_counts"] == {"pending": 4}
    assert second.synced_count == 0
    assert second.existing_count == 4
    assert state is not None
    assert len(state.records) == 4
    assert state.sync_count == 2
    assert len(events) == 4
    assert first.to_json_dict()["authority_split"]["provider_executed"] is False
    assert first.to_json_dict()["authority_split"]["dispatcher_state_mutated"] is False


def test_leader_worker_delivery_ack_updates_known_record(tmp_path: Path) -> None:
    paths = _seed_leader_worker_dispatcher_inputs(tmp_path)
    dispatch = run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-25T12:00:00+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-25T12:00:01+00:00",
        )
    )
    decision = next(decision for decision in dispatch.decisions if decision.event_kind == "task_ready")

    result = acknowledge_leader_worker_delivery(
        LeaderWorkerDeliveryAckRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            source_key=decision.source_key,
            target_state="acknowledged",
            timestamp="2026-06-25T12:00:02+00:00",
            host_id="host:runner",
            runtime_provider="codex",
            runtime_session_id="session-1",
            runtime_run_id="run-1",
            invocation_id="inv-1",
        )
    )
    inspection = inspect_leader_worker_delivery_state(paths["delivery_state"])
    events = JsonlLeaderWorkerDeliveryEventLog(paths["delivery_log"]).read_all()

    assert result.changed is True
    assert result.record.delivery_state == "acknowledged"
    assert result.record.runtime_provider == "codex"
    assert result.record.delivery_attempt_count == 1
    assert inspection.state_counts == {"acknowledged": 1, "pending": 3}
    assert len(events) == 5
    assert events[-1].event_kind == "delivery_acknowledged"
    assert result.to_json_dict()["authority_split"]["scheduler_state_mutated"] is False
    assert result.to_json_dict()["authority_split"]["provider_executed"] is False


def test_codex_delivery_supervisor_acknowledges_pending_codex_task(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs_with_provider(
        tmp_path,
        server_provider="codex",
        client_provider="fake",
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-26T08:00:00+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-26T08:00:01+00:00",
            host_id="host:test",
        )
    )
    client = _RecordingCodexCliClient(
        CodexCliResult(summary="codex delivery complete", output_text="ok")
    )

    result = run_codex_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            max_deliveries=1,
            timestamp="2026-06-26T08:00:02+00:00",
            host_id="host:codex-test",
            host_invocation_id="host-invocation:codex-test",
        ),
        codex_cli_client=client,
    )

    state = read_leader_worker_delivery_state(paths["delivery_state"])
    runtime_records = JsonlRuntimeInvocationLog(paths["runtime_log"]).read_all()

    assert result.ok is True
    assert result.executed_count == 1
    assert result.skipped_count == 2
    assert result.attempted_count == 1
    assert result.to_json_dict()["authority_split"]["provider_executed"] is True
    assert result.to_json_dict()["authority_split"]["scheduler_state_mutated"] is False
    assert client.requests[0].task.task_id == "task-server"
    assert client.requests[0].agent.runtime_provider == "codex"
    assert state is not None
    assert _state_counts_from_delivery_records(state) == {"acknowledged": 1, "pending": 3}
    acknowledged = next(
        record for record in state.records.values() if record.delivery_state == "acknowledged"
    )
    assert acknowledged.runtime_provider == "codex"
    assert acknowledged.runtime_session_id == "codex-session-1"
    assert acknowledged.runtime_run_id == "codex-run-1"
    assert acknowledged.invocation_id == "codex-delivery:host-invocation:codex-test:codex-session-1:task-server"
    assert runtime_records[0].provider == "codex"
    assert runtime_records[0].status == "succeeded"
    assert runtime_records[0].runtime_surface == "host-owned-codex-delivery-supervisor-once"


def test_opencode_delivery_supervisor_acknowledges_pending_opencode_task(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs_with_provider(
        tmp_path,
        server_provider="opencode",
        client_provider="fake",
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-29T08:00:00+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-29T08:00:01+00:00",
            host_id="host:test",
        )
    )
    client = _RecordingOpenCodeCliClient(
        OpenCodeCliResult(summary="opencode delivery complete", output_text="ok")
    )

    result = run_opencode_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            max_deliveries=1,
            timestamp="2026-06-29T08:00:02+00:00",
            host_id="host:opencode-test",
            host_invocation_id="host-invocation:opencode-test",
        ),
        opencode_cli_client=client,
    )

    state = read_leader_worker_delivery_state(paths["delivery_state"])
    runtime_records = JsonlRuntimeInvocationLog(paths["runtime_log"]).read_all()

    assert result.ok is True
    assert result.executed_count == 1
    assert result.skipped_count == 2
    assert result.attempted_count == 1
    assert result.to_json_dict()["runtime_provider"] == "opencode"
    assert result.to_json_dict()["authority_split"]["provider_executed"] is True
    assert result.to_json_dict()["authority_split"]["workflow_surface"] == (
        "host-owned-opencode-delivery-supervisor-once"
    )
    assert client.requests[0].task.task_id == "task-server"
    assert client.requests[0].agent.runtime_provider == "opencode"
    assert state is not None
    assert _state_counts_from_delivery_records(state) == {"acknowledged": 1, "pending": 3}
    acknowledged = next(
        record for record in state.records.values() if record.delivery_state == "acknowledged"
    )
    assert acknowledged.runtime_provider == "opencode"
    assert acknowledged.runtime_session_id == "opencode-session-1"
    assert acknowledged.runtime_run_id == "opencode-run-1"
    assert acknowledged.invocation_id == (
        "opencode-delivery:host-invocation:opencode-test:"
        "opencode-session-1:task-server"
    )
    assert runtime_records[0].provider == "opencode"
    assert runtime_records[0].status == "succeeded"
    assert runtime_records[0].runtime_surface == "host-owned-opencode-delivery-supervisor-once"


def test_opencode_delivery_supervisor_uses_lane_session_ledger_binding(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs_with_provider(
        tmp_path,
        server_provider="opencode",
        client_provider="fake",
    )
    ledger_path = tmp_path / ".codex/runtime/opencode-session-ledger.json"
    claim_opencode_session_binding(
        OpenCodeSessionClaimRequest(
            ledger_path=ledger_path,
            scope_kind="lane",
            scope_id="lane:server",
            attach_url="http://127.0.0.1:4096",
            session_id="session-server-lane",
        )
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-29T08:05:00+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-29T08:05:01+00:00",
            host_id="host:test",
        )
    )
    client = _RecordingOpenCodeCliClient(
        OpenCodeCliResult(summary="opencode delivery complete", output_text="ok")
    )

    result = run_opencode_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            max_deliveries=1,
            timestamp="2026-06-29T08:05:02+00:00",
            host_id="host:opencode-test",
            host_invocation_id="host-invocation:opencode-ledger-test",
            opencode_session_ledger_path=ledger_path,
            opencode_enable_session_lookup=True,
        ),
        opencode_cli_client=client,
    )
    runtime_records = JsonlRuntimeInvocationLog(paths["runtime_log"]).read_all()

    assert result.ok is True
    assert result.executed_count == 1
    assert client.requests[0].host_session is not None
    assert client.requests[0].host_session.session_id == "session-server-lane"
    assert client.requests[0].host_session.scope_kind == "lane"
    assert client.requests[0].host_session.scope_id == "lane:server"
    assert runtime_records[0].metadata["session_selector_source"] == "session_ledger"
    assert runtime_records[0].metadata["opencode_session_scope_id"] == "lane:server"


def test_opencode_delivery_supervisor_server_api_uses_lane_session_ledger_binding(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs_with_provider(
        tmp_path,
        server_provider="opencode",
        client_provider="fake",
    )
    ledger_path = tmp_path / ".codex/runtime/opencode-session-ledger.json"
    claim_opencode_session_binding(
        OpenCodeSessionClaimRequest(
            ledger_path=ledger_path,
            scope_kind="lane",
            scope_id="lane:server",
            attach_url="http://127.0.0.1:4096",
            session_id="session-server-api-lane",
        )
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-30T08:05:00+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-30T08:05:01+00:00",
            host_id="host:test",
        )
    )
    calls: list[str] = []

    def opener(request, **kwargs):
        calls.append(request.full_url)
        if request.full_url.endswith("/session/session-server-api-lane/message"):
            return _JsonHttpResponse({"content": "server api ledger done"})
        raise AssertionError(f"unexpected URL: {request.full_url}")

    client = OpenCodeServerApiClient(
        OpenCodeServerApiClientConfig(base_url="http://127.0.0.1:4096"),
        opener=opener,
    )

    result = run_opencode_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            max_deliveries=1,
            timestamp="2026-06-30T08:05:02+00:00",
            host_id="host:opencode-test",
            host_invocation_id="host-invocation:opencode-server-api-ledger-test",
            opencode_session_ledger_path=ledger_path,
            opencode_enable_session_lookup=True,
        ),
        opencode_cli_client=client,
    )
    runtime_records = JsonlRuntimeInvocationLog(paths["runtime_log"]).read_all()

    assert result.ok is True
    assert result.executed_count == 1
    assert calls == [
        "http://127.0.0.1:4096/session/session-server-api-lane/message"
    ]
    assert runtime_records[0].metadata["session_selector_source"] == "session_ledger"
    assert runtime_records[0].metadata["opencode_session_scope_id"] == "lane:server"
    assert runtime_records[0].attempts[0].metadata["transport"] == "server-api"
    assert runtime_records[0].attempts[0].metadata["created_session"] is False
    assert runtime_records[0].attempts[0].metadata["session_selector_source"] == (
        "session_ledger"
    )


def test_opencode_delivery_supervisor_prefers_task_binding_over_lane_binding(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs_with_provider(
        tmp_path,
        server_provider="opencode",
        client_provider="fake",
    )
    ledger_path = tmp_path / ".codex/runtime/opencode-session-ledger.json"
    claim_opencode_session_binding(
        OpenCodeSessionClaimRequest(
            ledger_path=ledger_path,
            scope_kind="lane",
            scope_id="lane:server",
            attach_url="http://127.0.0.1:4096",
            session_id="session-lane",
        )
    )
    claim_opencode_session_binding(
        OpenCodeSessionClaimRequest(
            ledger_path=ledger_path,
            scope_kind="task",
            scope_id="task-server",
            attach_url="http://127.0.0.1:4096",
            session_id="session-task",
        )
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-29T08:06:00+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-29T08:06:01+00:00",
            host_id="host:test",
        )
    )
    client = _RecordingOpenCodeCliClient(
        OpenCodeCliResult(summary="opencode delivery complete", output_text="ok")
    )

    result = run_opencode_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=None,
            max_deliveries=1,
            timestamp="2026-06-29T08:06:02+00:00",
            host_id="host:opencode-test",
            host_invocation_id="host-invocation:opencode-task-ledger-test",
            opencode_session_ledger_path=ledger_path,
            opencode_enable_session_lookup=True,
        ),
        opencode_cli_client=client,
    )

    assert result.ok is True
    assert client.requests[0].host_session is not None
    assert client.requests[0].host_session.session_id == "session-task"
    assert client.requests[0].host_session.scope_kind == "task"


def test_opencode_delivery_supervisor_server_api_http_failure_uses_audit_path(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs_with_provider(
        tmp_path,
        server_provider="opencode",
        client_provider="fake",
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-30T08:06:00+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-30T08:06:01+00:00",
            host_id="host:test",
        )
    )

    def opener(request, **kwargs):
        if request.full_url.endswith("/session"):
            return _JsonHttpResponse({"id": "session-created"})
        raise urllib.error.HTTPError(
            request.full_url,
            503,
            "unavailable",
            hdrs=None,
            fp=None,
        )

    client = OpenCodeServerApiClient(
        OpenCodeServerApiClientConfig(base_url="http://127.0.0.1:4096"),
        opener=opener,
    )

    result = run_opencode_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            max_deliveries=1,
            timestamp="2026-06-30T08:06:02+00:00",
            host_id="host:opencode-test",
            host_invocation_id="host-invocation:opencode-server-api-failure-test",
            runtime_invocation_max_attempts=1,
        ),
        opencode_cli_client=client,
    )
    runtime_records = JsonlRuntimeInvocationLog(paths["runtime_log"]).read_all()

    assert result.ok is False
    assert result.failed_count == 1
    failed_record = next(record for record in result.records if record.status == "failed")
    assert failed_record.failure_kind == "process_failed"
    assert runtime_records[0].provider == "opencode"
    assert runtime_records[0].status == "failed"
    assert runtime_records[0].final_error_kind == "process_failed"
    assert runtime_records[0].attempts[0].raw_error_type == "HTTP503"


def test_opencode_delivery_supervisor_server_api_uses_continuous_binding_before_session_ledger(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs_with_provider(
        tmp_path,
        server_provider="opencode",
        client_provider="fake",
    )
    worker_ledger_path = tmp_path / ".codex/runtime/continuous-worker-bindings.json"
    worker_event_log_path = tmp_path / ".codex/runtime/continuous-worker-binding-events.jsonl"
    session_ledger_path = tmp_path / ".codex/runtime/opencode-session-ledger.json"
    claim_opencode_session_binding(
        OpenCodeSessionClaimRequest(
            ledger_path=session_ledger_path,
            scope_kind="lane",
            scope_id="lane:server",
            attach_url="http://127.0.0.1:4096",
            session_id="session-legacy-lane",
        )
    )
    claim_continuous_worker_binding(
        ContinuousWorkerBindingClaimRequest(
            ledger_path=worker_ledger_path,
            event_log_path=worker_event_log_path,
            worker_id="worker:server-api",
            runtime_provider="opencode",
            scope_kind="lane",
            scope_id="lane:server",
            lane_ids=("lane:server",),
            active_session_selector=ContinuousWorkerSessionSelector(
                provider="opencode",
                attach_url="http://127.0.0.1:4096",
                session_id="session-continuous-server-api",
            ),
            compact_context_ref="dbc://context/server-api-worker-compact",
            timestamp="2026-06-30T08:07:00+00:00",
        )
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-30T08:07:01+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-30T08:07:02+00:00",
            host_id="host:test",
        )
    )
    calls: list[str] = []

    def opener(request, **kwargs):
        calls.append(request.full_url)
        if request.full_url.endswith("/session/session-continuous-server-api/message"):
            return _JsonHttpResponse({"content": "continuous server api done"})
        raise AssertionError(f"unexpected URL: {request.full_url}")

    client = OpenCodeServerApiClient(
        OpenCodeServerApiClientConfig(base_url="http://127.0.0.1:4096"),
        opener=opener,
    )

    result = run_opencode_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            max_deliveries=1,
            timestamp="2026-06-30T08:07:03+00:00",
            host_id="host:opencode-test",
            host_invocation_id="host-invocation:opencode-server-api-worker-binding-test",
            continuous_worker_binding_ledger_path=worker_ledger_path,
            continuous_worker_binding_event_log_path=worker_event_log_path,
            enable_continuous_worker_binding_lookup=True,
            opencode_session_ledger_path=session_ledger_path,
            opencode_enable_session_lookup=True,
        ),
        opencode_cli_client=client,
    )
    runtime_records = JsonlRuntimeInvocationLog(paths["runtime_log"]).read_all()
    binding_events = JsonlContinuousWorkerBindingEventLog(worker_event_log_path).read_all()

    assert result.ok is True
    assert calls == [
        "http://127.0.0.1:4096/session/session-continuous-server-api/message"
    ]
    assert runtime_records[0].metadata["session_selector_source"] == (
        "continuous_worker_binding"
    )
    assert runtime_records[0].metadata["continuous_worker_id"] == "worker:server-api"
    assert runtime_records[0].attempts[0].metadata["session_selector_source"] == (
        "continuous_worker_binding"
    )
    assert runtime_records[0].attempts[0].metadata["created_session"] is False
    assert [event.event_kind for event in binding_events] == [
        "binding_claimed",
        "binding_reused",
    ]


def test_opencode_delivery_supervisor_server_api_explicit_session_disables_ledger_lookup(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs_with_provider(
        tmp_path,
        server_provider="opencode",
        client_provider="fake",
    )
    worker_ledger_path = tmp_path / ".codex/runtime/continuous-worker-bindings.json"
    worker_event_log_path = tmp_path / ".codex/runtime/continuous-worker-binding-events.jsonl"
    session_ledger_path = tmp_path / ".codex/runtime/opencode-session-ledger.json"
    claim_opencode_session_binding(
        OpenCodeSessionClaimRequest(
            ledger_path=session_ledger_path,
            scope_kind="lane",
            scope_id="lane:server",
            attach_url="http://127.0.0.1:4096",
            session_id="session-legacy-lane",
        )
    )
    claim_continuous_worker_binding(
        ContinuousWorkerBindingClaimRequest(
            ledger_path=worker_ledger_path,
            event_log_path=worker_event_log_path,
            worker_id="worker:server-api",
            runtime_provider="opencode",
            scope_kind="lane",
            scope_id="lane:server",
            active_session_selector=ContinuousWorkerSessionSelector(
                provider="opencode",
                attach_url="http://127.0.0.1:4096",
                session_id="session-continuous-server-api",
            ),
            timestamp="2026-06-30T08:08:00+00:00",
        )
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-30T08:08:01+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-30T08:08:02+00:00",
            host_id="host:test",
        )
    )
    calls: list[str] = []

    def opener(request, **kwargs):
        calls.append(request.full_url)
        if request.full_url.endswith("/session/session-explicit-server-api/message"):
            return _JsonHttpResponse({"content": "explicit server api done"})
        raise AssertionError(f"unexpected URL: {request.full_url}")

    client = OpenCodeServerApiClient(
        OpenCodeServerApiClientConfig(
            base_url="http://127.0.0.1:4096",
            session_id="session-explicit-server-api",
        ),
        opener=opener,
    )

    result = run_opencode_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            max_deliveries=1,
            timestamp="2026-06-30T08:08:03+00:00",
            host_id="host:opencode-test",
            host_invocation_id="host-invocation:opencode-server-api-explicit-precedence-test",
            continuous_worker_binding_ledger_path=worker_ledger_path,
            continuous_worker_binding_event_log_path=worker_event_log_path,
            enable_continuous_worker_binding_lookup=True,
            opencode_session_ledger_path=session_ledger_path,
            opencode_enable_session_lookup=True,
        ),
        opencode_cli_client=client,
    )
    runtime_records = JsonlRuntimeInvocationLog(paths["runtime_log"]).read_all()
    binding_events = JsonlContinuousWorkerBindingEventLog(worker_event_log_path).read_all()

    assert result.ok is True
    assert calls == [
        "http://127.0.0.1:4096/session/session-explicit-server-api/message"
    ]
    assert runtime_records[0].metadata["session_selector_source"] == "explicit_config"
    assert runtime_records[0].metadata["continuous_worker_binding_id"] == ""
    assert runtime_records[0].attempts[0].metadata["created_session"] is False
    assert runtime_records[0].attempts[0].metadata["session_selector_source"] == (
        "explicit_config"
    )
    assert [event.event_kind for event in binding_events] == ["binding_claimed"]


def test_opencode_delivery_supervisor_server_api_created_session_does_not_write_ledgers(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs_with_provider(
        tmp_path,
        server_provider="opencode",
        client_provider="fake",
    )
    worker_ledger_path = tmp_path / ".codex/runtime/continuous-worker-bindings.json"
    worker_event_log_path = tmp_path / ".codex/runtime/continuous-worker-binding-events.jsonl"
    session_ledger_path = tmp_path / ".codex/runtime/opencode-session-ledger.json"
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-30T08:09:01+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-30T08:09:02+00:00",
            host_id="host:test",
        )
    )
    calls: list[str] = []

    def opener(request, **kwargs):
        calls.append(request.full_url)
        if request.full_url.endswith("/session"):
            return _JsonHttpResponse({"id": "session-created-unclaimed"})
        if request.full_url.endswith("/session/session-created-unclaimed/message"):
            return _JsonHttpResponse({"content": "created session done"})
        raise AssertionError(f"unexpected URL: {request.full_url}")

    client = OpenCodeServerApiClient(
        OpenCodeServerApiClientConfig(base_url="http://127.0.0.1:4096"),
        opener=opener,
    )

    result = run_opencode_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            max_deliveries=1,
            timestamp="2026-06-30T08:09:03+00:00",
            host_id="host:opencode-test",
            host_invocation_id="host-invocation:opencode-server-api-created-unclaimed-test",
            continuous_worker_binding_ledger_path=worker_ledger_path,
            continuous_worker_binding_event_log_path=worker_event_log_path,
            enable_continuous_worker_binding_lookup=True,
            opencode_session_ledger_path=session_ledger_path,
            opencode_enable_session_lookup=True,
        ),
        opencode_cli_client=client,
    )
    runtime_records = JsonlRuntimeInvocationLog(paths["runtime_log"]).read_all()

    assert result.ok is True
    assert calls == [
        "http://127.0.0.1:4096/session",
        "http://127.0.0.1:4096/session/session-created-unclaimed/message",
    ]
    assert runtime_records[0].metadata["session_selector_source"] == "none"
    assert runtime_records[0].attempts[0].metadata["session_selector_source"] == (
        "server_api_created"
    )
    assert runtime_records[0].attempts[0].metadata["created_session"] is True
    assert runtime_records[0].attempts[0].metadata["session_persistence"] == (
        "not_persisted_by_delivery"
    )
    assert runtime_records[0].attempts[0].metadata[
        "server_api_created_session_persisted"
    ] is False
    assert not session_ledger_path.exists()
    assert not worker_ledger_path.exists()
    assert not worker_event_log_path.exists()


def test_opencode_delivery_supervisor_uses_continuous_worker_binding_before_session_ledger(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs_with_provider(
        tmp_path,
        server_provider="opencode",
        client_provider="fake",
    )
    worker_ledger_path = tmp_path / ".codex/runtime/continuous-worker-bindings.json"
    worker_event_log_path = tmp_path / ".codex/runtime/continuous-worker-binding-events.jsonl"
    lease_ledger_path = tmp_path / ".codex/runtime/continuous-worker-delivery-leases.json"
    lease_event_log_path = tmp_path / ".codex/runtime/continuous-worker-delivery-lease-events.jsonl"
    session_ledger_path = tmp_path / ".codex/runtime/opencode-session-ledger.json"
    claim_opencode_session_binding(
        OpenCodeSessionClaimRequest(
            ledger_path=session_ledger_path,
            scope_kind="lane",
            scope_id="lane:server",
            attach_url="http://127.0.0.1:4096",
            session_id="session-legacy-lane",
        )
    )
    claim_continuous_worker_binding(
        ContinuousWorkerBindingClaimRequest(
            ledger_path=worker_ledger_path,
            event_log_path=worker_event_log_path,
            worker_id="worker:server",
            runtime_provider="opencode",
            scope_kind="lane",
            scope_id="lane:server",
            lane_ids=("lane:server",),
            active_session_selector=ContinuousWorkerSessionSelector(
                provider="opencode",
                attach_url="http://127.0.0.1:4096",
                session_id="session-continuous-worker",
            ),
            compact_context_ref="dbc://context/server-worker-compact",
            audit_refs=("audit:continuous-worker-claim",),
            timestamp="2026-06-29T09:20:00+00:00",
        )
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-29T09:20:01+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-29T09:20:02+00:00",
            host_id="host:test",
        )
    )
    client = _RecordingOpenCodeCliClient(
        OpenCodeCliResult(summary="opencode delivery complete", output_text="ok")
    )

    result = run_opencode_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            max_deliveries=1,
            timestamp="2026-06-29T09:20:03+00:00",
            host_id="host:opencode-test",
            host_invocation_id="host-invocation:opencode-worker-binding-test",
            continuous_worker_binding_ledger_path=worker_ledger_path,
            continuous_worker_binding_event_log_path=worker_event_log_path,
            continuous_worker_delivery_lease_ledger_path=lease_ledger_path,
            continuous_worker_delivery_lease_event_log_path=lease_event_log_path,
            enable_continuous_worker_binding_lookup=True,
            opencode_session_ledger_path=session_ledger_path,
            opencode_enable_session_lookup=True,
        ),
        opencode_cli_client=client,
    )
    runtime_records = JsonlRuntimeInvocationLog(paths["runtime_log"]).read_all()

    assert result.ok is True
    assert result.executed_count == 1
    assert client.requests[0].host_session is not None
    assert client.requests[0].host_session.session_id == "session-continuous-worker"
    assert client.requests[0].host_session.selector_source == "continuous_worker_binding"
    assert client.requests[0].host_session.worker_binding_id == (
        "continuous-worker:lane:lane-server"
    )
    assert client.requests[0].host_session.compact_context_ref == (
        "dbc://context/server-worker-compact"
    )
    assert runtime_records[0].metadata["session_selector_source"] == (
        "continuous_worker_binding"
    )
    assert runtime_records[0].metadata["continuous_worker_id"] == "worker:server"
    assert runtime_records[0].metadata["continuous_worker_compact_context_ref"] == (
        "dbc://context/server-worker-compact"
    )
    binding_events = JsonlContinuousWorkerBindingEventLog(
        worker_event_log_path
    ).read_all()
    lease_events = JsonlDeliveryLeaseEventLog(lease_event_log_path).read_all()
    leases = inspect_delivery_leases(DeliveryLeaseInspectRequest(ledger_path=lease_ledger_path))

    assert [event.event_kind for event in binding_events] == [
        "binding_claimed",
        "binding_reused",
    ]
    assert binding_events[-1].metadata["task_id"] == "task-server"
    assert [event.event_kind for event in lease_events] == [
        "delivery_lease_reserved",
        "delivery_lease_started",
        "delivery_lease_completed",
    ]
    assert len(leases.leases) == 1
    assert leases.leases[0].binding_id == "continuous-worker:lane:lane-server"
    assert leases.leases[0].status == "completed"


def test_opencode_delivery_supervisor_carries_continuous_worker_context_refs(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs_with_provider(
        tmp_path,
        server_provider="opencode",
        client_provider="fake",
    )
    worker_ledger_path = tmp_path / ".codex/runtime/continuous-worker-bindings.json"
    worker_event_log_path = tmp_path / ".codex/runtime/continuous-worker-binding-events.jsonl"
    lease_ledger_path = tmp_path / ".codex/runtime/continuous-worker-delivery-leases.json"
    lease_event_log_path = tmp_path / ".codex/runtime/continuous-worker-delivery-lease-events.jsonl"
    claimed = claim_continuous_worker_binding(
        ContinuousWorkerBindingClaimRequest(
            ledger_path=worker_ledger_path,
            event_log_path=worker_event_log_path,
            worker_id="worker:server",
            runtime_provider="opencode",
            scope_kind="lane",
            scope_id="lane:server",
            lane_ids=("lane:server",),
            active_session_selector=ContinuousWorkerSessionSelector(
                provider="opencode",
                attach_url="http://127.0.0.1:4096",
                session_id="session-continuous-worker",
            ),
            compact_context_ref="dbc://context/server-worker-v1",
            audit_refs=("audit:continuous-worker-claim",),
            timestamp="2026-07-01T14:00:00+00:00",
        )
    )
    assert claimed.binding is not None
    compacted = compact_continuous_worker_binding(
        ContinuousWorkerBindingCompactRequest(
            ledger_path=worker_ledger_path,
            event_log_path=worker_event_log_path,
            binding_id=claimed.binding.binding_id,
            compact_context_ref="dbc://context/server-worker-v2",
            mailbox_cursor_ref="dbc://mailbox/server@42",
            worker_report_refs=("report:server-previous", "report:server-latest"),
            audit_refs=("audit:continuous-worker-compact",),
            timestamp="2026-07-01T14:00:01+00:00",
        )
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-07-01T14:00:02+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-07-01T14:00:03+00:00",
            host_id="host:test",
        )
    )
    client = _RecordingOpenCodeCliClient(
        OpenCodeCliResult(summary="opencode delivery complete", output_text="ok")
    )

    result = run_opencode_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            max_deliveries=1,
            timestamp="2026-07-01T14:00:04+00:00",
            host_id="host:opencode-test",
            host_invocation_id="host-invocation:opencode-context-carry-over-test",
            continuous_worker_binding_ledger_path=worker_ledger_path,
            continuous_worker_binding_event_log_path=worker_event_log_path,
            continuous_worker_delivery_lease_ledger_path=lease_ledger_path,
            continuous_worker_delivery_lease_event_log_path=lease_event_log_path,
            enable_continuous_worker_binding_lookup=True,
            opencode_enable_session_lookup=False,
        ),
        opencode_cli_client=client,
    )
    runtime_records = JsonlRuntimeInvocationLog(paths["runtime_log"]).read_all()
    host_session = client.requests[0].host_session

    assert compacted.ok is True
    assert result.ok is True
    assert result.executed_count == 1
    assert host_session is not None
    assert host_session.selector_source == "continuous_worker_binding"
    assert host_session.worker_binding_id == claimed.binding.binding_id
    assert host_session.compact_context_ref == "dbc://context/server-worker-v2"
    assert host_session.mailbox_cursor_ref == "dbc://mailbox/server@42"
    assert host_session.worker_report_refs == (
        "report:server-previous",
        "report:server-latest",
    )
    assert "audit:continuous-worker-compact" in host_session.audit_refs
    assert host_session.to_metadata()["mailbox_cursor_ref"] == "dbc://mailbox/server@42"
    assert host_session.to_metadata()["worker_report_refs"] == [
        "report:server-previous",
        "report:server-latest",
    ]
    assert runtime_records[0].metadata["session_selector_source"] == (
        "continuous_worker_binding"
    )
    assert runtime_records[0].metadata["continuous_worker_compact_context_ref"] == (
        "dbc://context/server-worker-v2"
    )
    assert runtime_records[0].metadata["continuous_worker_mailbox_cursor_ref"] == (
        "dbc://mailbox/server@42"
    )
    assert runtime_records[0].metadata["continuous_worker_report_refs"] == [
        "report:server-previous",
        "report:server-latest",
    ]


def test_opencode_delivery_supervisor_hydrates_compact_context_bundle(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs_with_provider(
        tmp_path,
        server_provider="opencode",
        client_provider="fake",
    )
    worker_ledger_path = tmp_path / ".codex/runtime/continuous-worker-bindings.json"
    worker_event_log_path = tmp_path / ".codex/runtime/continuous-worker-binding-events.jsonl"
    context_bundle_dir = tmp_path / ".codex/runtime/continuous-worker-contexts"
    lease_ledger_path = tmp_path / ".codex/runtime/continuous-worker-delivery-leases.json"
    lease_event_log_path = tmp_path / ".codex/runtime/continuous-worker-delivery-lease-events.jsonl"
    claimed = claim_continuous_worker_binding(
        ContinuousWorkerBindingClaimRequest(
            ledger_path=worker_ledger_path,
            event_log_path=worker_event_log_path,
            worker_id="worker:server",
            runtime_provider="opencode",
            scope_kind="lane",
            scope_id="lane:server",
            lane_ids=("lane:server",),
            active_session_selector=ContinuousWorkerSessionSelector(
                provider="opencode",
                attach_url="http://127.0.0.1:4096",
                session_id="session-continuous-worker",
            ),
            mailbox_cursor_ref="dbc://mailbox/server@42",
            worker_report_refs=("report:server-previous",),
            audit_refs=("audit:continuous-worker-claim",),
            timestamp="2026-07-02T09:00:00+00:00",
        )
    )
    assert claimed.binding is not None
    built = build_continuous_worker_compact_context_bundle(
        ContinuousWorkerCompactContextBuildRequest(
            ledger_path=worker_ledger_path,
            bundle_dir_path=context_bundle_dir,
            binding_id=claimed.binding.binding_id,
            timestamp="2026-07-02T09:00:01+00:00",
            summary="Server worker already built the route skeleton.",
            key_decisions=("Keep server and client ports isolated.",),
            current_state="Needs route validation before merge.",
            artifact_refs=("server.js", "TEST_REPORT.md"),
            worker_report_refs=("report:server-latest",),
            audit_refs=("audit:continuous-worker-compact",),
        )
    )
    assert built.ok is True
    compacted = compact_continuous_worker_binding(
        ContinuousWorkerBindingCompactRequest(
            ledger_path=worker_ledger_path,
            event_log_path=worker_event_log_path,
            binding_id=claimed.binding.binding_id,
            compact_context_ref=built.compact_context_ref,
            mailbox_cursor_ref="dbc://mailbox/server@42",
            worker_report_refs=("report:server-latest",),
            audit_refs=("audit:continuous-worker-compact",),
            timestamp="2026-07-02T09:00:02+00:00",
        )
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-07-02T09:00:03+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-07-02T09:00:04+00:00",
            host_id="host:test",
        )
    )
    client = _RecordingOpenCodeCliClient(
        OpenCodeCliResult(summary="opencode delivery complete", output_text="ok")
    )

    result = run_opencode_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            max_deliveries=1,
            timestamp="2026-07-02T09:00:05+00:00",
            host_id="host:opencode-test",
            host_invocation_id="host-invocation:opencode-context-hydration-test",
            continuous_worker_binding_ledger_path=worker_ledger_path,
            continuous_worker_binding_event_log_path=worker_event_log_path,
            continuous_worker_context_bundle_dir_path=context_bundle_dir,
            continuous_worker_delivery_lease_ledger_path=lease_ledger_path,
            continuous_worker_delivery_lease_event_log_path=lease_event_log_path,
            enable_continuous_worker_binding_lookup=True,
            opencode_enable_session_lookup=False,
        ),
        opencode_cli_client=client,
    )
    runtime_records = JsonlRuntimeInvocationLog(paths["runtime_log"]).read_all()
    hydrated_instruction = client.requests[0].instruction

    assert compacted.ok is True
    assert result.ok is True
    assert "Continuous worker compact context:" in hydrated_instruction
    assert "Summary: Server worker already built the route skeleton." in hydrated_instruction
    assert "Current state: Needs route validation before merge." in hydrated_instruction
    assert "- Keep server and client ports isolated." in hydrated_instruction
    assert "- server.js" in hydrated_instruction
    assert "Mailbox cursor ref: dbc://mailbox/server@42" in hydrated_instruction
    assert "- report:server-previous" in hydrated_instruction
    assert "- report:server-latest" in hydrated_instruction
    assert f"Compact context ref: {built.compact_context_ref}" in hydrated_instruction
    assert runtime_records[0].metadata["continuous_worker_compact_context_ref"] == (
        built.compact_context_ref
    )


def test_opencode_delivery_supervisor_fails_closed_on_missing_compact_context_bundle(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs_with_provider(
        tmp_path,
        server_provider="opencode",
        client_provider="fake",
    )
    worker_ledger_path = tmp_path / ".codex/runtime/continuous-worker-bindings.json"
    worker_event_log_path = tmp_path / ".codex/runtime/continuous-worker-binding-events.jsonl"
    claim_continuous_worker_binding(
        ContinuousWorkerBindingClaimRequest(
            ledger_path=worker_ledger_path,
            event_log_path=worker_event_log_path,
            worker_id="worker:server",
            runtime_provider="opencode",
            scope_kind="lane",
            scope_id="lane:server",
            lane_ids=("lane:server",),
            active_session_selector=ContinuousWorkerSessionSelector(
                provider="opencode",
                attach_url="http://127.0.0.1:4096",
                session_id="session-continuous-worker",
            ),
            compact_context_ref="dbc://continuous-worker-context/missing-context",
            timestamp="2026-07-02T09:10:00+00:00",
        )
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-07-02T09:10:01+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-07-02T09:10:02+00:00",
            host_id="host:test",
        )
    )
    client = _RecordingOpenCodeCliClient(
        OpenCodeCliResult(summary="should not run", output_text="no")
    )

    result = run_opencode_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            max_deliveries=1,
            timestamp="2026-07-02T09:10:03+00:00",
            host_id="host:opencode-test",
            host_invocation_id="host-invocation:opencode-context-missing-test",
            continuous_worker_binding_ledger_path=worker_ledger_path,
            continuous_worker_binding_event_log_path=worker_event_log_path,
            continuous_worker_context_bundle_dir_path=(
                tmp_path / ".codex/runtime/continuous-worker-contexts"
            ),
            enable_continuous_worker_binding_lookup=True,
            opencode_enable_session_lookup=False,
            runtime_invocation_max_attempts=1,
        ),
        opencode_cli_client=client,
    )
    runtime_records = JsonlRuntimeInvocationLog(paths["runtime_log"]).read_all()

    assert result.ok is False
    assert result.failed_count == 1
    assert client.requests == ()
    failed = next(record for record in result.records if record.status == "failed")
    assert failed.failure_kind == "invalid_response"
    assert "compact context hydration failed" in failed.failure_detail
    assert runtime_records == ()


def test_opencode_delivery_supervisor_consumes_active_promoted_lane_ownership(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs_with_provider(
        tmp_path,
        server_provider="opencode",
        client_provider="fake",
    )
    worker_ledger_path = tmp_path / ".codex/runtime/continuous-worker-bindings.json"
    worker_event_log_path = tmp_path / ".codex/runtime/continuous-worker-binding-events.jsonl"
    ownership_ledger_path = tmp_path / ".codex/runtime/continuous-worker-lane-ownerships.json"
    ownership_event_log_path = tmp_path / ".codex/runtime/continuous-worker-lane-ownership-events.jsonl"
    lease_ledger_path = tmp_path / ".codex/runtime/continuous-worker-delivery-leases.json"
    lease_event_log_path = tmp_path / ".codex/runtime/continuous-worker-delivery-lease-events.jsonl"
    promoted = promote_server_api_created_session_to_continuous_worker_binding(
        ServerApiCreatedSessionPromotionRequest(
            ledger_path=worker_ledger_path,
            event_log_path=worker_event_log_path,
            attach_url="http://127.0.0.1:4096/",
            session_id="session-promoted-server-api",
            worker_id="worker:server",
            scope_kind="lane",
            scope_id="lane:server",
            lane_ids=("lane:server",),
            audit_refs=("audit:server-api-created",),
            timestamp="2026-07-01T13:00:00+00:00",
        )
    )
    assert promoted.ok is True
    assert promoted.binding is not None
    claimed = claim_lane_ownership(
        LaneOwnershipClaimRequest(
            ledger_path=ownership_ledger_path,
            event_log_path=ownership_event_log_path,
            scope_kind="lane",
            scope_id="lane:server",
            binding_id=promoted.binding.binding_id,
            worker_id="worker:server",
            timestamp="2026-07-01T13:00:01+00:00",
            audit_refs=("audit:server-api-created",),
        )
    )
    activated = activate_lane_ownership(
        LaneOwnershipActivateRequest(
            ledger_path=ownership_ledger_path,
            event_log_path=ownership_event_log_path,
            binding_id=promoted.binding.binding_id,
            activated_at="2026-07-01T13:00:02+00:00",
            delivery_id="delivery:first-success",
            task_id="task:first-success",
            audit_refs=("audit:first-success",),
        )
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-07-01T13:00:03+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-07-01T13:00:04+00:00",
            host_id="host:test",
        )
    )
    client = _RecordingOpenCodeCliClient(
        OpenCodeCliResult(summary="opencode delivery complete", output_text="ok")
    )

    result = run_opencode_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            max_deliveries=1,
            timestamp="2026-07-01T13:00:05+00:00",
            host_id="host:opencode-test",
            host_invocation_id="host-invocation:active-ownership-consumption-test",
            continuous_worker_binding_ledger_path=worker_ledger_path,
            continuous_worker_binding_event_log_path=worker_event_log_path,
            continuous_worker_delivery_lease_ledger_path=lease_ledger_path,
            continuous_worker_delivery_lease_event_log_path=lease_event_log_path,
            continuous_worker_lane_ownership_ledger_path=ownership_ledger_path,
            enable_continuous_worker_binding_lookup=True,
            opencode_enable_session_lookup=False,
        ),
        opencode_cli_client=client,
    )
    runtime_records = JsonlRuntimeInvocationLog(paths["runtime_log"]).read_all()
    binding_events = JsonlContinuousWorkerBindingEventLog(
        worker_event_log_path
    ).read_all()
    ownerships = inspect_lane_ownerships(
        LaneOwnershipInspectRequest(
            ledger_path=ownership_ledger_path,
            binding_id=promoted.binding.binding_id,
        )
    )
    leases = inspect_delivery_leases(
        DeliveryLeaseInspectRequest(ledger_path=lease_ledger_path)
    )

    assert claimed.ok is True
    assert activated.ok is True
    assert result.ok is True
    assert result.executed_count == 1
    assert client.requests[0].host_session is not None
    assert client.requests[0].host_session.session_id == "session-promoted-server-api"
    assert client.requests[0].host_session.selector_source == "continuous_worker_binding"
    assert client.requests[0].host_session.worker_binding_id == promoted.binding.binding_id
    assert runtime_records[0].metadata["session_selector_source"] == (
        "continuous_worker_binding"
    )
    assert runtime_records[0].metadata["continuous_worker_binding_id"] == (
        promoted.binding.binding_id
    )
    assert runtime_records[0].metadata["continuous_worker_id"] == "worker:server"
    assert ownerships.ownerships[0].status == "active"
    assert [event.event_kind for event in binding_events] == [
        "binding_claimed",
        "binding_reused",
    ]
    assert leases.leases[0].binding_id == promoted.binding.binding_id
    assert leases.leases[0].status == "completed"


def test_opencode_bounded_loop_reuses_same_continuous_worker_across_lane_chain(
    tmp_path: Path,
) -> None:
    worker_ledger_path = tmp_path / ".codex/runtime/continuous-worker-bindings.json"
    worker_event_log_path = tmp_path / ".codex/runtime/continuous-worker-binding-events.jsonl"
    smoke_request = CodexDeliveryE2ESmokeRequest(
        scheduler_snapshot_path=tmp_path / ".codex/scheduler/opencode-c2-state.json",
        scheduler_event_log_path=tmp_path / ".codex/scheduler/opencode-c2-events.jsonl",
        artifact_store_path=tmp_path / ".codex/orchestration/opencode-exchange-artifacts.json",
        dispatcher_state_path=tmp_path / ".codex/scheduler/opencode-dispatcher-state.json",
        dispatch_event_log_path=tmp_path / ".codex/scheduler/opencode-dispatcher-events.jsonl",
        delivery_state_path=tmp_path / ".codex/scheduler/opencode-delivery-state.json",
        delivery_event_log_path=tmp_path / ".codex/scheduler/opencode-delivery-events.jsonl",
        runtime_invocation_log_path=tmp_path / ".codex/runtime/opencode-invocations.jsonl",
        initialize_fixture=True,
        require_host_ready=False,
        timestamp="2026-06-29T11:20:00+00:00",
        runtime_invocation_max_attempts=1,
        host_id="host:opencode-continuous-loop-test",
        host_invocation_id="host-owned-opencode-continuous-loop-test",
        continuous_worker_binding_ledger_path=worker_ledger_path,
        continuous_worker_binding_event_log_path=worker_event_log_path,
        enable_continuous_worker_binding_lookup=True,
    )
    claim_continuous_worker_binding(
        ContinuousWorkerBindingClaimRequest(
            ledger_path=worker_ledger_path,
            event_log_path=worker_event_log_path,
            worker_id="worker:opencode-chain",
            runtime_provider="opencode",
            scope_kind="lane",
            scope_id=smoke_request.codex_lane_id,
            active_session_selector=ContinuousWorkerSessionSelector(
                provider="opencode",
                attach_url="http://127.0.0.1:4096",
                session_id="session-chain",
            ),
            timestamp="2026-06-29T11:19:00+00:00",
        )
    )
    client = _SequenceOpenCodeCliClient(
        (
            OpenCodeCliResult(summary="first complete", output_text="first complete"),
            OpenCodeCliResult(summary="followup complete", output_text="followup complete"),
        )
    )

    result = run_bounded_opencode_delivery_supervisor_loop(
        CodexDeliveryBoundedLoopRequest(
            smoke_request=smoke_request,
            max_ticks=4,
            max_deliveries=4,
            max_runtime_failures=1,
        ),
        opencode_cli_client=client,
    )
    events = JsonlContinuousWorkerBindingEventLog(worker_event_log_path).read_all()
    ledger = inspect_continuous_worker_bindings(
        ContinuousWorkerBindingInspectRequest(ledger_path=worker_ledger_path)
    )

    assert result.ok is True
    assert tuple(request.host_session.session_id for request in client.requests) == (
        "session-chain",
        "session-chain",
    )
    assert tuple(request.host_session.worker_binding_id for request in client.requests) == (
        "continuous-worker:lane:lane-codex-smoke",
        "continuous-worker:lane:lane-codex-smoke",
    )
    assert [event.event_kind for event in events] == [
        "binding_claimed",
        "binding_reused",
        "binding_reused",
    ]
    assert [event.metadata["task_id"] for event in events if event.event_kind == "binding_reused"] == [
        smoke_request.target_task_id,
        smoke_request.followup_task_id,
    ]
    assert ledger.bindings[0].last_used_at == "2026-06-29T11:20:00+00:00"


def test_opencode_delivery_supervisor_marks_continuous_worker_binding_stale_on_retryable_failure(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs_with_provider(
        tmp_path,
        server_provider="opencode",
        client_provider="fake",
    )
    worker_ledger_path = tmp_path / ".codex/runtime/continuous-worker-bindings.json"
    worker_event_log_path = tmp_path / ".codex/runtime/continuous-worker-binding-events.jsonl"
    lease_ledger_path = tmp_path / ".codex/runtime/continuous-worker-delivery-leases.json"
    lease_event_log_path = tmp_path / ".codex/runtime/continuous-worker-delivery-lease-events.jsonl"
    claim_continuous_worker_binding(
        ContinuousWorkerBindingClaimRequest(
            ledger_path=worker_ledger_path,
            event_log_path=worker_event_log_path,
            worker_id="worker:server",
            runtime_provider="opencode",
            scope_kind="lane",
            scope_id="lane:server",
            active_session_selector=ContinuousWorkerSessionSelector(
                provider="opencode",
                attach_url="http://127.0.0.1:4096",
                session_id="session-server",
            ),
            timestamp="2026-06-29T11:30:00+00:00",
        )
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-29T11:30:01+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-29T11:30:02+00:00",
            host_id="host:test",
        )
    )

    class _TimeoutOpenCodeCliClient:
        def exec(self, request) -> OpenCodeCliResult:
            raise OpenCodeCliRuntimeError(
                error_kind="timeout",
                summary="timed out",
                retryable=True,
            )

    result = run_opencode_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            max_deliveries=1,
            timestamp="2026-06-29T11:30:03+00:00",
            runtime_invocation_max_attempts=1,
            host_id="host:opencode-test",
            host_invocation_id="host-invocation:opencode-worker-binding-stale-test",
            continuous_worker_binding_ledger_path=worker_ledger_path,
            continuous_worker_binding_event_log_path=worker_event_log_path,
            continuous_worker_delivery_lease_ledger_path=lease_ledger_path,
            continuous_worker_delivery_lease_event_log_path=lease_event_log_path,
            enable_continuous_worker_binding_lookup=True,
        ),
        opencode_cli_client=_TimeoutOpenCodeCliClient(),
    )
    bindings = inspect_continuous_worker_bindings(
        ContinuousWorkerBindingInspectRequest(
            ledger_path=worker_ledger_path,
            include_inactive=True,
        )
    )
    events = JsonlContinuousWorkerBindingEventLog(worker_event_log_path).read_all()
    lease_events = JsonlDeliveryLeaseEventLog(lease_event_log_path).read_all()
    leases = inspect_delivery_leases(DeliveryLeaseInspectRequest(ledger_path=lease_ledger_path))

    assert result.ok is False
    assert result.failed_count == 1
    assert bindings.bindings[0].lifecycle_status == "stale"
    assert [event.event_kind for event in events] == [
        "binding_claimed",
        "binding_marked_stale",
    ]
    assert [event.event_kind for event in lease_events] == [
        "delivery_lease_reserved",
        "delivery_lease_started",
        "delivery_lease_failed_retryable",
    ]
    assert len(leases.leases) == 1
    assert leases.leases[0].status == "failed_retryable"


def test_opencode_delivery_supervisor_skips_binding_with_active_delivery_lease(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs_with_provider(
        tmp_path,
        server_provider="opencode",
        client_provider="fake",
    )
    worker_ledger_path = tmp_path / ".codex/runtime/continuous-worker-bindings.json"
    worker_event_log_path = tmp_path / ".codex/runtime/continuous-worker-binding-events.jsonl"
    lease_ledger_path = tmp_path / ".codex/runtime/continuous-worker-delivery-leases.json"
    lease_event_log_path = tmp_path / ".codex/runtime/continuous-worker-delivery-lease-events.jsonl"
    claim_continuous_worker_binding(
        ContinuousWorkerBindingClaimRequest(
            ledger_path=worker_ledger_path,
            event_log_path=worker_event_log_path,
            worker_id="worker:server",
            runtime_provider="opencode",
            scope_kind="lane",
            scope_id="lane:server",
            active_session_selector=ContinuousWorkerSessionSelector(
                provider="opencode",
                attach_url="http://127.0.0.1:4096",
                session_id="session-server",
            ),
            timestamp="2026-06-30T10:00:00+00:00",
        )
    )
    reserve_delivery_lease(
        DeliveryLeaseReserveRequest(
            ledger_path=lease_ledger_path,
            event_log_path=lease_event_log_path,
            binding_id="continuous-worker:lane:lane-server",
            task_id="task:already-running",
            delivery_id="delivery:already-running",
            reserved_at="2026-06-30T10:00:01+00:00",
        )
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-30T10:00:02+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-30T10:00:03+00:00",
            host_id="host:test",
        )
    )
    client = _RecordingOpenCodeCliClient(
        OpenCodeCliResult(summary="should not run", output_text="no")
    )

    result = run_opencode_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            max_deliveries=1,
            timestamp="2026-06-30T10:00:04+00:00",
            host_id="host:opencode-test",
            host_invocation_id="host-invocation:opencode-active-lease-skip-test",
            continuous_worker_binding_ledger_path=worker_ledger_path,
            continuous_worker_binding_event_log_path=worker_event_log_path,
            continuous_worker_delivery_lease_ledger_path=lease_ledger_path,
            continuous_worker_delivery_lease_event_log_path=lease_event_log_path,
            enable_continuous_worker_binding_lookup=True,
        ),
        opencode_cli_client=client,
    )
    lease_events = JsonlDeliveryLeaseEventLog(lease_event_log_path).read_all()

    assert result.ok is True
    assert result.executed_count == 0
    assert len(client.requests) == 0
    assert [event.event_kind for event in lease_events] == ["delivery_lease_reserved"]


def test_opencode_delivery_supervisor_skips_binding_with_suspended_lane_ownership(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs_with_provider(
        tmp_path,
        server_provider="opencode",
        client_provider="fake",
    )
    worker_ledger_path = tmp_path / ".codex/runtime/continuous-worker-bindings.json"
    worker_event_log_path = tmp_path / ".codex/runtime/continuous-worker-binding-events.jsonl"
    ownership_ledger_path = tmp_path / ".codex/runtime/continuous-worker-lane-ownerships.json"
    ownership_event_log_path = tmp_path / ".codex/runtime/continuous-worker-lane-ownership-events.jsonl"
    claim_continuous_worker_binding(
        ContinuousWorkerBindingClaimRequest(
            ledger_path=worker_ledger_path,
            event_log_path=worker_event_log_path,
            worker_id="worker:server",
            runtime_provider="opencode",
            scope_kind="lane",
            scope_id="lane:server",
            active_session_selector=ContinuousWorkerSessionSelector(
                provider="opencode",
                attach_url="http://127.0.0.1:4096",
                session_id="session-server",
            ),
            timestamp="2026-06-30T10:10:00+00:00",
        )
    )
    claim_lane_ownership(
        LaneOwnershipClaimRequest(
            ledger_path=ownership_ledger_path,
            event_log_path=ownership_event_log_path,
            scope_kind="lane",
            scope_id="lane:server",
            binding_id="continuous-worker:lane:lane-server",
            worker_id="worker:server",
            timestamp="2026-06-30T10:10:01+00:00",
        )
    )
    activated = activate_lane_ownership(
        LaneOwnershipActivateRequest(
            ledger_path=ownership_ledger_path,
            event_log_path=ownership_event_log_path,
            binding_id="continuous-worker:lane:lane-server",
            activated_at="2026-06-30T10:10:02+00:00",
            delivery_id="delivery:previous",
            task_id="task:previous",
        )
    )
    suspended = suspend_lane_ownership(
        LaneOwnershipSuspendRequest(
            ledger_path=ownership_ledger_path,
            event_log_path=ownership_event_log_path,
            binding_id="continuous-worker:lane:lane-server",
            timestamp="2026-06-30T10:10:03+00:00",
        )
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-30T10:10:04+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-30T10:10:05+00:00",
            host_id="host:test",
        )
    )
    client = _RecordingOpenCodeCliClient(
        OpenCodeCliResult(summary="should not run", output_text="no")
    )

    result = run_opencode_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            max_deliveries=1,
            timestamp="2026-06-30T10:10:06+00:00",
            host_id="host:opencode-test",
            host_invocation_id="host-invocation:opencode-suspended-ownership-skip-test",
            continuous_worker_binding_ledger_path=worker_ledger_path,
            continuous_worker_binding_event_log_path=worker_event_log_path,
            continuous_worker_lane_ownership_ledger_path=ownership_ledger_path,
            enable_continuous_worker_binding_lookup=True,
        ),
        opencode_cli_client=client,
    )

    assert activated.ok is True
    assert suspended.ok is True
    assert result.ok is True
    assert result.executed_count == 0
    assert len(client.requests) == 0


def test_opencode_delivery_supervisor_worker_binding_blocks_same_session_parallel_batch(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs_with_provider(
        tmp_path,
        server_provider="opencode",
        client_provider="opencode",
    )
    state = read_scheduler_state_snapshot(paths["snapshot"])
    client_task = state.tasks["task-client"]
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                **state.tasks,
                "task-client": replace(client_task, state="ready", blocked_reason=""),
            },
            dependencies=state.dependencies,
            run_records=state.run_records,
            merge_gates=state.merge_gates,
            edit_lease_lifecycle=state.edit_lease_lifecycle,
        ),
        paths["snapshot"],
    )
    worker_ledger_path = tmp_path / ".codex/runtime/continuous-worker-bindings.json"
    claim_continuous_worker_binding(
        ContinuousWorkerBindingClaimRequest(
            ledger_path=worker_ledger_path,
            worker_id="worker:web",
            runtime_provider="opencode",
            scope_kind="lane_group",
            scope_id="lane-group:web",
            lane_ids=("lane:server", "lane:client"),
            active_session_selector=ContinuousWorkerSessionSelector(
                provider="opencode",
                attach_url="http://127.0.0.1:4096",
                session_id="session-web-worker",
            ),
            timestamp="2026-06-29T09:30:00+00:00",
        )
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-29T09:30:01+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-29T09:30:02+00:00",
            host_id="host:test",
        )
    )
    client = _RecordingOpenCodeCliClient(
        OpenCodeCliResult(summary="opencode delivery complete", output_text="ok")
    )

    result = run_opencode_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=None,
            max_deliveries=2,
            max_concurrent_deliveries=2,
            timestamp="2026-06-29T09:30:03+00:00",
            host_id="host:opencode-test",
            host_invocation_id="host-invocation:opencode-worker-binding-parallel-test",
            continuous_worker_binding_ledger_path=worker_ledger_path,
            enable_continuous_worker_binding_lookup=True,
            opencode_enable_session_lookup=False,
        ),
        opencode_cli_client=client,
    )
    delivery_state = read_leader_worker_delivery_state(paths["delivery_state"])

    assert result.ok is True
    assert result.executed_count == 1
    assert len(client.requests) == 1
    assert client.requests[0].host_session is not None
    assert client.requests[0].host_session.worker_binding_id == (
        "continuous-worker:lane_group:lane-group-web"
    )
    assert set(client.requests[0].host_session.worker_lane_ids) == {
        "lane:client",
        "lane:server",
    }
    assert delivery_state is not None
    assert _state_counts_from_delivery_records(delivery_state) == {
        "acknowledged": 1,
        "pending": 3,
    }


def test_codex_result_consumer_stores_artifact_and_completion_event(
    tmp_path: Path,
) -> None:
    snapshot = tmp_path / ".codex/scheduler/state.json"
    event_log = tmp_path / ".codex/scheduler/events.jsonl"
    artifact_store = tmp_path / ".codex/orchestration/exchange-artifacts.json"
    task = ScheduledTask(
        task_id="task-consume",
        title="Consume result",
        instruction="Persist the result.",
        agent=AgentSpec(agent_id="agent:codex", runtime_provider="codex"),
        state="ready",
        context_scope=ContextScope(context_id="ctx-consume", lane_id="lane:codex"),
    )
    write_scheduler_state_snapshot(SchedulerState(tasks={task.task_id: task}), snapshot)
    event_log.parent.mkdir(parents=True, exist_ok=True)
    event_log.write_text("", encoding="utf-8")
    run_result = RuntimeRunResult(
        run_handle=RunHandle(
            run_id="run-consume",
            session_id="session-consume",
            task_id=task.task_id,
        ),
        output_artifact=ExchangeArtifact(
            artifact_id="task-consume:codex-result",
            version="v1",
            kind="result",
            intent="inform",
            producer="agent:codex",
            scope=ExchangeScope(context_id="ctx-consume", lane_id="lane:codex"),
            parts=(
                ExchangePayloadPart(part_type="text", text="done"),
                ExchangePayloadPart(
                    part_type="artifact_delta",
                    data={"summary": "done", "changed_refs": []},
                ),
            ),
        ),
        artifact_delta=ArtifactDelta(
            artifact_id="task-consume:codex-result",
            version="v1",
            summary="done",
        ),
    )

    result = consume_successful_codex_result(
        CodexResultConsumerRequest(
            artifact_store_path=artifact_store,
            scheduler_event_log_path=event_log,
            timestamp="2026-06-26T08:30:01+00:00",
            event_id_prefix="host-invocation:result-test",
        ),
        task=task,
        run_result=run_result,
    )

    stored = JsonArtifactVersionStore(artifact_store).get(
        "task-consume:codex-result",
        "v1",
    )
    events = JsonlSchedulerEventLog(event_log).read_all()
    recovery = recover_scheduler_state(snapshot, event_log)

    assert result.artifact_id == "task-consume:codex-result"
    assert stored.artifact.parts[0].text == "done"
    assert len(events) == 1
    assert events[0].event_kind == "task_completed"
    assert events[0].task_id == "task-consume"
    assert events[0].output_artifact_id == "task-consume:codex-result"
    assert recovery.recovered_state.tasks["task-consume"].state == "complete"
    assert (
        recovery.recovered_state.tasks["task-consume"].output_artifact_ref.ref_id
        == "task-consume:codex-result"
    )
    assert recovery.recovered_state.run_records[0].run_id == "run-consume"


def test_codex_delivery_supervisor_can_consume_success_result(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs_with_provider(
        tmp_path,
        server_provider="codex",
        client_provider="fake",
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-26T08:40:00+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-26T08:40:01+00:00",
            host_id="host:test",
        )
    )
    client = _RecordingCodexCliClient(
        CodexCliResult(summary="codex consumed", output_text="persisted")
    )

    result = run_codex_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            artifact_store_path=paths["artifact_store"],
            consume_success_results=True,
            max_deliveries=1,
            timestamp="2026-06-26T08:40:02+00:00",
            host_id="host:codex-test",
            host_invocation_id="host-invocation:codex-consume-test",
        ),
        codex_cli_client=client,
    )

    state = read_leader_worker_delivery_state(paths["delivery_state"])
    stored = JsonArtifactVersionStore(paths["artifact_store"]).get(
        "task-server:codex-result",
        "v1",
    )
    scheduler_events = JsonlSchedulerEventLog(paths["event_log"]).read_all()
    recovery = recover_scheduler_state(paths["snapshot"], paths["event_log"])

    assert result.ok is True
    assert result.executed_count == 1
    acknowledged_record = next(
        record for record in result.records if record.status == "acknowledged"
    )
    assert acknowledged_record.result_consumption is not None
    assert result.to_json_dict()["authority_split"]["scheduler_event_log_mutated"] is True
    assert result.to_json_dict()["authority_split"]["exchange_store_mutated"] is True
    assert stored.artifact.parts[0].text == "persisted"
    assert scheduler_events[-1].event_kind == "task_completed"
    assert scheduler_events[-1].task_id == "task-server"
    assert recovery.recovered_state.tasks["task-server"].state == "complete"
    assert recovery.recovered_state.tasks["task-server"].output_artifact_ref.ref_id == (
        "task-server:codex-result"
    )
    assert recovery.recovered_state.run_records[-1].output_artifact_id == (
        "task-server:codex-result"
    )
    assert state is not None
    assert _state_counts_from_delivery_records(state) == {"acknowledged": 1, "pending": 3}


def test_opencode_delivery_supervisor_can_consume_success_result(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs_with_provider(
        tmp_path,
        server_provider="opencode",
        client_provider="fake",
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-29T08:40:00+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-29T08:40:01+00:00",
            host_id="host:test",
        )
    )
    client = _RecordingOpenCodeCliClient(
        OpenCodeCliResult(summary="opencode consumed", output_text="persisted")
    )

    result = run_opencode_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            artifact_store_path=paths["artifact_store"],
            consume_success_results=True,
            max_deliveries=1,
            timestamp="2026-06-29T08:40:02+00:00",
            host_id="host:opencode-test",
            host_invocation_id="host-invocation:opencode-consume-test",
        ),
        opencode_cli_client=client,
    )

    state = read_leader_worker_delivery_state(paths["delivery_state"])
    stored = JsonArtifactVersionStore(paths["artifact_store"]).get(
        "task-server:opencode-result",
        "v1",
    )
    scheduler_events = JsonlSchedulerEventLog(paths["event_log"]).read_all()
    recovery = recover_scheduler_state(paths["snapshot"], paths["event_log"])
    acknowledged_record = next(
        record for record in result.records if record.status == "acknowledged"
    )

    assert result.ok is True
    assert result.executed_count == 1
    assert acknowledged_record.result_consumption is not None
    assert result.to_json_dict()["authority_split"]["scheduler_event_log_mutated"] is True
    assert result.to_json_dict()["authority_split"]["exchange_store_mutated"] is True
    assert stored.artifact.parts[0].text == "persisted"
    assert scheduler_events[-1].event_kind == "task_completed"
    assert scheduler_events[-1].task_id == "task-server"
    assert recovery.recovered_state.tasks["task-server"].state == "complete"
    assert recovery.recovered_state.tasks["task-server"].output_artifact_ref.ref_id == (
        "task-server:opencode-result"
    )
    assert state is not None
    assert _state_counts_from_delivery_records(state) == {"acknowledged": 1, "pending": 3}


def test_codex_delivery_supervisor_publishes_git_worktree_patch_review(
    tmp_path: Path,
) -> None:
    source_repo = _git_repo(tmp_path / "source")
    paths = _seed_codex_delivery_supervisor_git_worktree_project(
        tmp_path,
        source_repo=source_repo,
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-27T10:00:00+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-27T10:00:01+00:00",
            host_id="host:test",
        )
    )
    client = _EditingCodexCliClient(
        relative_path="src/app.py",
        content="print('codex sandbox patch')\n",
    )

    result = run_codex_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            artifact_store_path=paths["artifact_store"],
            consume_success_results=True,
            max_deliveries=1,
            timestamp="2026-06-27T10:00:02+00:00",
            host_id="host:codex-test",
            host_invocation_id="host-invocation:codex-patch-review-test",
            enable_sandbox_preflight=True,
            workspace_root=source_repo,
            git_worktree_sandbox_root=tmp_path / "sandboxes",
            publish_worker_patch_artifacts=True,
            worker_patch_target_task_id="task-server",
        ),
        codex_cli_client=client,
    )

    state = read_leader_worker_delivery_state(paths["delivery_state"])
    recovery = recover_scheduler_state(paths["snapshot"], paths["event_log"])
    store = JsonArtifactVersionStore(paths["artifact_store"])
    patch_record = store.get("task-server:patch-review", "v1")
    output_record = store.get("task-server:codex-result", "v1")
    acknowledged = next(record for record in result.records if record.status == "acknowledged")
    patch_payload = next(
        part.data
        for part in patch_record.artifact.parts
        if part.part_type == "structured"
    )
    evidence = next(
        part.data
        for part in patch_record.artifact.parts
        if part.part_type == "evidence"
    )

    assert result.ok is True
    assert result.executed_count == 1
    assert result.to_json_dict()["authority_split"]["worker_patch_review_artifacts_published"] is True
    assert acknowledged.worker_patch_review is not None
    assert acknowledged.worker_patch_review.artifact_id == "task-server:patch-review"
    assert acknowledged.worker_patch_review.patch_state == "has_patch"
    assert acknowledged.worker_patch_review.changed_paths == ("src/app.py",)
    assert client.requests[0].task.runtime_workspace_root
    assert client.requests[0].task.sandbox_provider == "git-worktree"
    assert client.requests[0].task.sandbox_allocation_id.startswith(
        "git-worktree:task-server:"
    )
    assert "src/app.py" in client.requests[0].task.visible_mounts
    assert output_record.artifact.parts[0].text == "edited src/app.py"
    assert patch_payload["product_type"] == "worker_patch_review_proposal"
    assert patch_payload["sandbox_provider"] == "git-worktree"
    assert patch_payload["patch_state"] == "has_patch"
    assert patch_payload["changed_paths"] == ["src/app.py"]
    assert "codex sandbox patch" in evidence["git_diff"]
    assert (source_repo / "src" / "app.py").read_text(encoding="utf-8") == "print('ok')\n"
    assert recovery.recovered_state.tasks["task-server"].state == "complete"
    assert state is not None
    delivered = next(
        record for record in state.records.values() if record.delivery_state == "acknowledged"
    )
    assert delivered.metadata["worker_patch_review"]["ref_id"] == "task-server:patch-review"


def test_opencode_delivery_supervisor_publishes_git_worktree_patch_review(
    tmp_path: Path,
) -> None:
    source_repo = _git_repo(tmp_path / "source")
    paths = _seed_codex_delivery_supervisor_git_worktree_project(
        tmp_path,
        source_repo=source_repo,
        provider="opencode",
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-29T10:00:00+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-29T10:00:01+00:00",
            host_id="host:test",
        )
    )
    client = _EditingOpenCodeCliClient(
        relative_path="src/app.py",
        content="print('opencode sandbox patch')\n",
    )

    result = run_opencode_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            artifact_store_path=paths["artifact_store"],
            consume_success_results=True,
            max_deliveries=1,
            timestamp="2026-06-29T10:00:02+00:00",
            host_id="host:opencode-test",
            host_invocation_id="host-invocation:opencode-patch-review-test",
            enable_sandbox_preflight=True,
            workspace_root=source_repo,
            git_worktree_sandbox_root=tmp_path / "sandboxes",
            publish_worker_patch_artifacts=True,
            worker_patch_target_task_id="task-server",
        ),
        opencode_cli_client=client,
    )

    state = read_leader_worker_delivery_state(paths["delivery_state"])
    recovery = recover_scheduler_state(paths["snapshot"], paths["event_log"])
    store = JsonArtifactVersionStore(paths["artifact_store"])
    patch_record = store.get("task-server:patch-review", "v1")
    output_record = store.get("task-server:opencode-result", "v1")
    acknowledged = next(record for record in result.records if record.status == "acknowledged")
    patch_payload = next(
        part.data
        for part in patch_record.artifact.parts
        if part.part_type == "structured"
    )
    evidence = next(
        part.data
        for part in patch_record.artifact.parts
        if part.part_type == "evidence"
    )

    assert result.ok is True
    assert result.executed_count == 1
    assert result.to_json_dict()["authority_split"]["worker_patch_review_artifacts_published"] is True
    assert acknowledged.worker_patch_review is not None
    assert acknowledged.worker_patch_review.artifact_id == "task-server:patch-review"
    assert acknowledged.worker_patch_review.patch_state == "has_patch"
    assert acknowledged.worker_patch_review.changed_paths == ("src/app.py",)
    assert client.requests[0].agent.runtime_provider == "opencode"
    assert client.requests[0].task.runtime_workspace_root
    assert client.requests[0].task.sandbox_provider == "git-worktree"
    assert client.requests[0].task.sandbox_allocation_id.startswith(
        "git-worktree:task-server:"
    )
    assert "src/app.py" in client.requests[0].task.visible_mounts
    assert output_record.artifact.parts[0].text == "edited src/app.py"
    assert patch_payload["product_type"] == "worker_patch_review_proposal"
    assert patch_payload["runtime_provider"] == "opencode"
    assert patch_payload["sandbox_provider"] == "git-worktree"
    assert patch_payload["patch_state"] == "has_patch"
    assert patch_payload["changed_paths"] == ["src/app.py"]
    assert "opencode sandbox patch" in evidence["git_diff"]
    assert (source_repo / "src" / "app.py").read_text(encoding="utf-8") == "print('ok')\n"
    assert recovery.recovered_state.tasks["task-server"].state == "complete"
    assert state is not None
    delivered = next(
        record for record in state.records.values() if record.delivery_state == "acknowledged"
    )
    assert delivered.runtime_provider == "opencode"
    assert delivered.metadata["worker_patch_review"]["ref_id"] == "task-server:patch-review"


def test_codex_delivery_supervisor_patch_publish_failure_does_not_complete_task(
    tmp_path: Path,
) -> None:
    source_repo = _git_repo(tmp_path / "source")
    paths = _seed_codex_delivery_supervisor_git_worktree_project(
        tmp_path,
        source_repo=source_repo,
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-27T10:10:00+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-27T10:10:01+00:00",
            host_id="host:test",
        )
    )
    JsonArtifactVersionStore(paths["artifact_store"]).put(
        ExchangeArtifact(
            artifact_id="task-server:patch-review",
            version="v1",
            kind="proposal",
            intent="request_merge",
            producer="agent:other",
            parts=(ExchangePayloadPart(part_type="text", text="collision"),),
        )
    )
    client = _EditingCodexCliClient(
        relative_path="src/app.py",
        content="print('collision path')\n",
    )

    result = run_codex_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            artifact_store_path=paths["artifact_store"],
            consume_success_results=True,
            max_deliveries=1,
            timestamp="2026-06-27T10:10:02+00:00",
            host_invocation_id="host-invocation:codex-patch-collision-test",
            enable_sandbox_preflight=True,
            workspace_root=source_repo,
            git_worktree_sandbox_root=tmp_path / "sandboxes",
            publish_worker_patch_artifacts=True,
        ),
        codex_cli_client=client,
    )

    state = read_leader_worker_delivery_state(paths["delivery_state"])
    scheduler_events = JsonlSchedulerEventLog(paths["event_log"]).read_all()
    recovery = recover_scheduler_state(paths["snapshot"], paths["event_log"])
    failed = next(record for record in result.records if record.status == "failed")

    assert result.ok is False
    assert failed.failure_kind == "worker_patch_review_publish_failed"
    assert "already exists" in failed.failure_detail
    assert not any(event.event_kind == "task_completed" for event in scheduler_events)
    assert recovery.recovered_state.tasks["task-server"].state == "ready"
    assert state is not None
    assert _state_counts_from_delivery_records(state) == {"failed": 1, "pending": 3}


def test_codex_delivery_supervisor_routes_permission_request_to_review_required(
    tmp_path: Path,
) -> None:
    paths = _seed_codex_delivery_supervisor_permission_project(tmp_path)
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-27T08:00:00+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-27T08:00:01+00:00",
            host_id="host:test",
        )
    )
    permission = PermissionRequest(
        request_id="permission:shell:test",
        request_kind="shell",
        run_id="",
        summary="Codex wants to run tests before finalizing.",
        target="npm test",
    )
    client = _RecordingCodexCliClient(
        CodexCliResult(
            summary="codex needs permission",
            output_text="Review evidence from Codex.",
            permission_requests=(permission,),
        )
    )

    result = run_codex_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            artifact_store_path=paths["artifact_store"],
            consume_success_results=True,
            max_deliveries=1,
            timestamp="2026-06-27T08:00:02+00:00",
            host_id="host:codex-test",
            host_invocation_id="host-invocation:codex-review-test",
        ),
        codex_cli_client=client,
    )

    state = read_leader_worker_delivery_state(paths["delivery_state"])
    scheduler_events = JsonlSchedulerEventLog(paths["event_log"]).read_all()
    recovery = recover_scheduler_state(paths["snapshot"], paths["event_log"])
    stored = JsonArtifactVersionStore(paths["artifact_store"]).get(
        "task-server:codex-result",
        "v1",
    )
    runtime_records = JsonlRuntimeInvocationLog(paths["runtime_log"]).read_all()
    record = next(record for record in result.records if record.status == "review_required")
    payload = result.to_json_dict()

    assert result.ok is True
    assert result.executed_count == 0
    assert result.review_required_count == 1
    assert record.permission_review is not None
    assert record.result_consumption is None
    assert record.permission_requests == (permission,)
    assert payload["review_required_count"] == 1
    assert payload["authority_split"]["scheduler_event_log_mutated"] is True
    assert payload["authority_split"]["exchange_store_mutated"] is True
    assert not any(
        event.event_kind == "task_completed" and event.task_id == "task-server"
        for event in scheduler_events
    )
    assert scheduler_events[-1].event_kind == "task_review_required"
    assert scheduler_events[-1].reason == "permission review required: shell npm test"
    assert recovery.recovered_state.tasks["task-server"].state == "review_required"
    assert recovery.recovered_state.tasks["task-server"].blocked_reason == (
        "permission review required: shell npm test"
    )
    assert recovery.recovered_state.tasks["task-client"].state == "waiting"
    assert recovery.recovered_state.run_records[-1].state == "review_required"
    assert stored.artifact.parts[0].text == "Review evidence from Codex."
    assert state is not None
    assert _state_counts_from_delivery_records(state) == {
        "pending": 3,
        "review_required": 1,
    }
    review_delivery = next(
        record for record in state.records.values()
        if record.delivery_state == "review_required"
    )
    assert review_delivery.metadata["permission_request_count"] == 1
    assert review_delivery.metadata["permission_requests"][0]["target"] == "npm test"
    assert runtime_records[0].status == "succeeded"


def test_codex_delivery_supervisor_fails_delivery_when_result_consumer_fails(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs_with_provider(
        tmp_path,
        server_provider="codex",
        client_provider="fake",
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-26T08:50:00+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-26T08:50:01+00:00",
            host_id="host:test",
        )
    )
    JsonArtifactVersionStore(paths["artifact_store"]).put(
        ExchangeArtifact(
            artifact_id="task-server:codex-result",
            version="v1",
            kind="result",
            intent="inform",
            producer="agent:other",
            parts=(
                ExchangePayloadPart(part_type="text", text="existing"),
                ExchangePayloadPart(
                    part_type="artifact_delta",
                    data={"summary": "existing", "changed_refs": []},
                ),
            ),
        )
    )
    client = _RecordingCodexCliClient(
        CodexCliResult(summary="codex collision", output_text="new output")
    )

    result = run_codex_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            artifact_store_path=paths["artifact_store"],
            consume_success_results=True,
            max_deliveries=1,
            timestamp="2026-06-26T08:50:02+00:00",
            host_id="host:codex-test",
            host_invocation_id="host-invocation:codex-consume-failed-test",
        ),
        codex_cli_client=client,
    )

    state = read_leader_worker_delivery_state(paths["delivery_state"])
    scheduler_events = JsonlSchedulerEventLog(paths["event_log"]).read_all()
    recovery = recover_scheduler_state(paths["snapshot"], paths["event_log"])

    assert result.ok is False
    assert result.failed_count == 1
    failed_record = next(record for record in result.records if record.status == "failed")
    assert failed_record.failure_kind == "result_consumer_failed"
    assert "already exists" in failed_record.failure_detail
    assert result.to_json_dict()["authority_split"]["exchange_store_mutated"] is False
    assert not any(event.event_kind == "task_completed" for event in scheduler_events)
    assert recovery.recovered_state.tasks["task-server"].state == "ready"
    assert state is not None
    assert _state_counts_from_delivery_records(state) == {"failed": 1, "pending": 3}


def test_codex_delivery_supervisor_skips_non_codex_tasks_without_state_change(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs(tmp_path)
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-26T08:10:00+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-26T08:10:01+00:00",
        )
    )
    client = _RecordingCodexCliClient(
        CodexCliResult(summary="should not run", output_text="unexpected")
    )

    result = run_codex_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            max_deliveries=2,
            timestamp="2026-06-26T08:10:02+00:00",
        ),
        codex_cli_client=client,
    )

    state = read_leader_worker_delivery_state(paths["delivery_state"])

    assert result.ok is True
    assert result.executed_count == 0
    assert result.failed_count == 0
    assert result.skipped_count == 4
    assert client.requests == ()
    assert state is not None
    assert _state_counts_from_delivery_records(state) == {"pending": 4}
    assert JsonlRuntimeInvocationLog(paths["runtime_log"]).read_all() == ()


def test_codex_delivery_supervisor_marks_runtime_failure(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs_with_provider(
        tmp_path,
        server_provider="codex",
        client_provider="fake",
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-26T08:20:00+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-26T08:20:01+00:00",
        )
    )
    client = _FailingCodexCliClient(
        CodexCliRuntimeError(
            error_kind="timeout",
            summary="temporary OPENAI_API_KEY=secret timeout",
            retryable=True,
        )
    )

    result = run_codex_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            max_deliveries=1,
            timestamp="2026-06-26T08:20:02+00:00",
            runtime_invocation_max_attempts=2,
            runtime_invocation_backoff_seconds=0,
        ),
        codex_cli_client=client,
    )

    state = read_leader_worker_delivery_state(paths["delivery_state"])
    runtime_records = JsonlRuntimeInvocationLog(paths["runtime_log"]).read_all()

    assert result.ok is False
    assert result.failed_count == 1
    assert result.executed_count == 0
    assert state is not None
    assert _state_counts_from_delivery_records(state) == {"failed": 1, "pending": 3}
    failed = next(record for record in state.records.values() if record.delivery_state == "failed")
    assert failed.failure_kind == "timeout"
    assert "OPENAI_API_KEY=[redacted]" in failed.failure_detail
    assert "secret" not in failed.failure_detail
    assert failed.runtime_session_id == "codex-session-1"
    assert runtime_records[0].status == "failed"
    assert runtime_records[0].attempt_count == 2
    assert runtime_records[0].final_error_kind == "timeout"
    assert "OPENAI_API_KEY=[redacted]" in runtime_records[0].final_summary


def test_codex_delivery_supervisor_retries_retryable_failed_delivery_after_restart(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs_with_provider(
        tmp_path,
        server_provider="codex",
        client_provider="fake",
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-27T09:00:00+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-27T09:00:01+00:00",
        )
    )
    client = _SequenceCodexCliClientWithFailures(
        (
            CodexCliRuntimeError(
                error_kind="timeout",
                summary="temporary timeout",
                retryable=True,
            ),
            CodexCliResult(summary="retry succeeded", output_text="done after retry"),
        )
    )

    first = run_codex_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            artifact_store_path=paths["artifact_store"],
            consume_success_results=True,
            max_deliveries=1,
            timestamp="2026-06-27T09:00:02+00:00",
            host_invocation_id="host-invocation:codex-retry-first",
            runtime_invocation_max_attempts=1,
        ),
        codex_cli_client=client,
    )
    second = run_codex_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            artifact_store_path=paths["artifact_store"],
            consume_success_results=True,
            max_deliveries=1,
            retry_failed_delivery=True,
            max_delivery_attempts_per_record=2,
            timestamp="2026-06-27T09:00:03+00:00",
            host_invocation_id="host-invocation:codex-retry-second",
            runtime_invocation_max_attempts=1,
        ),
        codex_cli_client=client,
    )

    state = read_leader_worker_delivery_state(paths["delivery_state"])
    scheduler_events = JsonlSchedulerEventLog(paths["event_log"]).read_all()
    recovery = recover_scheduler_state(paths["snapshot"], paths["event_log"])
    runtime_records = JsonlRuntimeInvocationLog(paths["runtime_log"]).read_all()
    retry_record = next(record for record in second.records if record.status == "acknowledged")

    assert first.ok is False
    assert first.failed_count == 1
    assert second.ok is True
    assert second.executed_count == 1
    assert retry_record.retry_attempt is True
    assert len(client.requests) == 2
    assert state is not None
    assert _state_counts_from_delivery_records(state) == {"acknowledged": 1, "pending": 3}
    acknowledged = next(
        record for record in state.records.values() if record.delivery_state == "acknowledged"
    )
    assert acknowledged.delivery_attempt_count == 2
    assert acknowledged.metadata["retry_attempt"] is True
    assert [
        event.event_kind for event in scheduler_events
        if event.task_id == "task-server"
    ] == ["task_completed"]
    assert recovery.recovered_state.tasks["task-server"].state == "complete"
    assert len(runtime_records) == 2
    assert [record.status for record in runtime_records] == ["failed", "succeeded"]


def test_codex_delivery_supervisor_does_not_retry_non_retryable_failed_delivery(
    tmp_path: Path,
) -> None:
    paths = _seed_leader_worker_dispatcher_inputs_with_provider(
        tmp_path,
        server_provider="codex",
        client_provider="fake",
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=paths["dispatcher_state"],
            dispatch_event_log_path=paths["dispatch_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            artifact_store_path=paths["artifact_store"],
            worker_agent_ids=("agent:server", "agent:client"),
            timestamp="2026-06-27T09:10:00+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            dispatch_event_log_path=paths["dispatch_log"],
            timestamp="2026-06-27T09:10:01+00:00",
        )
    )
    client = _SequenceCodexCliClientWithFailures(
        (
            CodexCliRuntimeError(
                error_kind="authentication_failed",
                summary="auth failed",
                retryable=False,
            ),
            CodexCliResult(summary="should not run", output_text="unexpected"),
        )
    )

    first = run_codex_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            artifact_store_path=paths["artifact_store"],
            consume_success_results=True,
            max_deliveries=1,
            timestamp="2026-06-27T09:10:02+00:00",
            host_invocation_id="host-invocation:codex-no-retry-first",
            runtime_invocation_max_attempts=1,
        ),
        codex_cli_client=client,
    )
    second = run_codex_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=paths["delivery_state"],
            delivery_event_log_path=paths["delivery_log"],
            scheduler_snapshot_path=paths["snapshot"],
            scheduler_event_log_path=paths["event_log"],
            runtime_invocation_log_path=paths["runtime_log"],
            artifact_store_path=paths["artifact_store"],
            consume_success_results=True,
            max_deliveries=1,
            retry_failed_delivery=True,
            max_delivery_attempts_per_record=2,
            timestamp="2026-06-27T09:10:03+00:00",
            host_invocation_id="host-invocation:codex-no-retry-second",
            runtime_invocation_max_attempts=1,
        ),
        codex_cli_client=client,
    )

    state = read_leader_worker_delivery_state(paths["delivery_state"])
    runtime_records = JsonlRuntimeInvocationLog(paths["runtime_log"]).read_all()

    assert first.ok is False
    assert first.failed_count == 1
    assert second.ok is True
    assert second.attempted_count == 0
    assert len(client.requests) == 1
    assert state is not None
    assert _state_counts_from_delivery_records(state) == {"failed": 1, "pending": 3}
    assert len(runtime_records) == 1


def test_codex_delivery_e2e_smoke_completes_one_codex_task(
    tmp_path: Path,
) -> None:
    request = CodexDeliveryE2ESmokeRequest(
        scheduler_snapshot_path=tmp_path / ".codex/scheduler/c1-state.json",
        scheduler_event_log_path=tmp_path / ".codex/scheduler/c1-events.jsonl",
        artifact_store_path=tmp_path / ".codex/orchestration/exchange-artifacts.json",
        dispatcher_state_path=tmp_path / ".codex/scheduler/dispatcher-state.json",
        dispatch_event_log_path=tmp_path / ".codex/scheduler/dispatcher-events.jsonl",
        delivery_state_path=tmp_path / ".codex/scheduler/delivery-state.json",
        delivery_event_log_path=tmp_path / ".codex/scheduler/delivery-events.jsonl",
        runtime_invocation_log_path=tmp_path / ".codex/runtime/invocations.jsonl",
        initialize_fixture=True,
        require_host_ready=False,
        timestamp="2026-06-26T10:00:00+00:00",
        runtime_invocation_max_attempts=1,
    )
    client = _RecordingCodexCliClient(
        CodexCliResult(summary="codex e2e complete", output_text="c1 complete")
    )

    result = run_codex_delivery_e2e_smoke(request, codex_cli_client=client)

    recovery = recover_scheduler_state(
        request.scheduler_snapshot_path,
        request.scheduler_event_log_path,
    )
    delivery_state = read_leader_worker_delivery_state(request.delivery_state_path)
    runtime_records = JsonlRuntimeInvocationLog(
        request.runtime_invocation_log_path
    ).read_all()
    stored = JsonArtifactVersionStore(request.artifact_store_path).get(
        f"{request.target_task_id}:codex-result",
        "v1",
    )
    payload = result.to_json_dict()

    assert result.ok is True
    assert result.stop_reason == "complete"
    assert result.fixture.initialized is True
    assert result.dispatcher_tick is not None
    assert result.dispatcher_tick.tick_record.decision_count >= 3
    assert result.delivery_sync is not None
    assert result.delivery_sync.synced_count >= 3
    assert result.codex_delivery is not None
    assert result.codex_delivery.executed_count == 1
    assert result.codex_delivery.skipped_count == 1
    assert recovery.recovered_state.tasks[request.target_task_id].state == "complete"
    assert (
        recovery.recovered_state.tasks[request.target_task_id].output_artifact_ref.ref_id
        == f"{request.target_task_id}:codex-result"
    )
    assert delivery_state is not None
    assert _state_counts_from_delivery_records(delivery_state) == {
        "acknowledged": 1,
        "pending": 3,
    }
    assert runtime_records[0].provider == "codex"
    assert runtime_records[0].status == "succeeded"
    assert stored.artifact.parts[0].text == "c1 complete"
    assert payload["counts"]["runtime_invocations"] == 1
    assert payload["authority_split"]["scheduler_event_log_mutated"] is True
    assert payload["authority_split"]["exchange_store_mutated"] is True
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False


def test_codex_delivery_e2e_smoke_fails_closed_when_codex_not_ready(
    tmp_path: Path,
) -> None:
    request = CodexDeliveryE2ESmokeRequest(
        scheduler_snapshot_path=tmp_path / ".codex/scheduler/c1-state.json",
        scheduler_event_log_path=tmp_path / ".codex/scheduler/c1-events.jsonl",
        artifact_store_path=tmp_path / ".codex/orchestration/exchange-artifacts.json",
        dispatcher_state_path=tmp_path / ".codex/scheduler/dispatcher-state.json",
        dispatch_event_log_path=tmp_path / ".codex/scheduler/dispatcher-events.jsonl",
        delivery_state_path=tmp_path / ".codex/scheduler/delivery-state.json",
        delivery_event_log_path=tmp_path / ".codex/scheduler/delivery-events.jsonl",
        runtime_invocation_log_path=tmp_path / ".codex/runtime/invocations.jsonl",
        initialize_fixture=False,
        require_host_ready=True,
    )
    client = _UnavailableCodexCliClient()

    result = run_codex_delivery_e2e_smoke(request, codex_cli_client=client)
    payload = result.to_json_dict()

    assert result.ok is False
    assert result.stop_reason == "codex_not_ready"
    assert result.readiness is not None
    assert result.readiness.ready is False
    assert payload["authority_split"]["dispatcher_state_mutated"] is False
    assert payload["authority_split"]["delivery_state_mutated"] is False
    assert payload["authority_split"]["scheduler_snapshot_mutated"] is False
    assert not Path(request.dispatcher_state_path).exists()
    assert not Path(request.delivery_state_path).exists()
    assert not Path(request.runtime_invocation_log_path).exists()


def test_opencode_delivery_e2e_smoke_completes_one_opencode_task(
    tmp_path: Path,
) -> None:
    request = CodexDeliveryE2ESmokeRequest(
        scheduler_snapshot_path=tmp_path / ".codex/scheduler/opencode-c1-state.json",
        scheduler_event_log_path=tmp_path / ".codex/scheduler/opencode-c1-events.jsonl",
        artifact_store_path=tmp_path / ".codex/orchestration/opencode-exchange-artifacts.json",
        dispatcher_state_path=tmp_path / ".codex/scheduler/opencode-dispatcher-state.json",
        dispatch_event_log_path=tmp_path / ".codex/scheduler/opencode-dispatcher-events.jsonl",
        delivery_state_path=tmp_path / ".codex/scheduler/opencode-delivery-state.json",
        delivery_event_log_path=tmp_path / ".codex/scheduler/opencode-delivery-events.jsonl",
        runtime_invocation_log_path=tmp_path / ".codex/runtime/opencode-invocations.jsonl",
        initialize_fixture=True,
        require_host_ready=False,
        timestamp="2026-06-29T12:00:00+00:00",
        runtime_invocation_max_attempts=1,
        host_id="host:opencode-c1-test",
        host_invocation_id="host-owned-opencode-c1-test",
    )
    client = _RecordingOpenCodeCliClient(
        OpenCodeCliResult(summary="opencode e2e complete", output_text="opencode c1 complete")
    )

    result = run_opencode_delivery_e2e_smoke(request, opencode_cli_client=client)

    recovery = recover_scheduler_state(
        request.scheduler_snapshot_path,
        request.scheduler_event_log_path,
    )
    delivery_state = read_leader_worker_delivery_state(request.delivery_state_path)
    runtime_records = JsonlRuntimeInvocationLog(
        request.runtime_invocation_log_path
    ).read_all()
    stored = JsonArtifactVersionStore(request.artifact_store_path).get(
        f"{request.target_task_id}:opencode-result",
        "v1",
    )
    payload = result.to_json_dict()

    assert result.ok is True
    assert result.stop_reason == "complete"
    assert result.fixture.initialized is True
    assert result.dispatcher_tick is not None
    assert result.delivery_sync is not None
    assert result.codex_delivery is not None
    assert result.codex_delivery.executed_count == 1
    assert recovery.recovered_state.tasks[request.target_task_id].state == "complete"
    assert (
        recovery.recovered_state.tasks[request.target_task_id].agent.runtime_provider
        == "opencode"
    )
    assert (
        recovery.recovered_state.tasks[request.target_task_id].output_artifact_ref.ref_id
        == f"{request.target_task_id}:opencode-result"
    )
    assert delivery_state is not None
    assert _state_counts_from_delivery_records(delivery_state) == {
        "acknowledged": 1,
        "pending": 3,
    }
    assert len(client.requests) == 1
    assert client.requests[0].agent.runtime_provider == "opencode"
    assert runtime_records[0].provider == "opencode"
    assert runtime_records[0].status == "succeeded"
    assert stored.artifact.parts[0].text == "opencode c1 complete"
    assert payload["runtime_provider"] == "opencode"
    assert payload["counts"]["provider_acknowledged"] == 1
    assert payload["authority_split"]["workflow_surface"] == (
        "host-owned-opencode-delivery-e2e-smoke"
    )
    assert payload["authority_split"]["runtime_provider"] == "opencode"
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False


def test_opencode_delivery_e2e_smoke_fails_closed_when_opencode_not_ready(
    tmp_path: Path,
) -> None:
    request = CodexDeliveryE2ESmokeRequest(
        scheduler_snapshot_path=tmp_path / ".codex/scheduler/opencode-c1-state.json",
        scheduler_event_log_path=tmp_path / ".codex/scheduler/opencode-c1-events.jsonl",
        artifact_store_path=tmp_path / ".codex/orchestration/opencode-exchange-artifacts.json",
        dispatcher_state_path=tmp_path / ".codex/scheduler/opencode-dispatcher-state.json",
        dispatch_event_log_path=tmp_path / ".codex/scheduler/opencode-dispatcher-events.jsonl",
        delivery_state_path=tmp_path / ".codex/scheduler/opencode-delivery-state.json",
        delivery_event_log_path=tmp_path / ".codex/scheduler/opencode-delivery-events.jsonl",
        runtime_invocation_log_path=tmp_path / ".codex/runtime/opencode-invocations.jsonl",
        initialize_fixture=False,
        require_host_ready=True,
    )
    client = _UnavailableOpenCodeCliClient()

    result = run_opencode_delivery_e2e_smoke(request, opencode_cli_client=client)
    payload = result.to_json_dict()

    assert result.ok is False
    assert result.stop_reason == "opencode_not_ready"
    assert result.readiness is not None
    assert result.readiness.ready is False
    assert payload["runtime_provider"] == "opencode"
    assert payload["authority_split"]["runtime_provider"] == "opencode"
    assert payload["authority_split"]["dispatcher_state_mutated"] is False
    assert payload["authority_split"]["delivery_state_mutated"] is False
    assert payload["authority_split"]["scheduler_snapshot_mutated"] is False
    assert not Path(request.dispatcher_state_path).exists()
    assert not Path(request.delivery_state_path).exists()
    assert not Path(request.runtime_invocation_log_path).exists()


def test_bounded_codex_delivery_supervisor_loop_completes_codex_chain(
    tmp_path: Path,
) -> None:
    smoke_request = CodexDeliveryE2ESmokeRequest(
        scheduler_snapshot_path=tmp_path / ".codex/scheduler/c2-state.json",
        scheduler_event_log_path=tmp_path / ".codex/scheduler/c2-events.jsonl",
        artifact_store_path=tmp_path / ".codex/orchestration/exchange-artifacts.json",
        dispatcher_state_path=tmp_path / ".codex/scheduler/dispatcher-state.json",
        dispatch_event_log_path=tmp_path / ".codex/scheduler/dispatcher-events.jsonl",
        delivery_state_path=tmp_path / ".codex/scheduler/delivery-state.json",
        delivery_event_log_path=tmp_path / ".codex/scheduler/delivery-events.jsonl",
        runtime_invocation_log_path=tmp_path / ".codex/runtime/invocations.jsonl",
        initialize_fixture=True,
        require_host_ready=False,
        timestamp="2026-06-26T11:00:00+00:00",
        runtime_invocation_max_attempts=1,
    )
    client = _SequenceCodexCliClient(
        (
            CodexCliResult(summary="first complete", output_text="first complete"),
            CodexCliResult(summary="followup complete", output_text="followup complete"),
        )
    )

    result = run_bounded_codex_delivery_supervisor_loop(
        CodexDeliveryBoundedLoopRequest(
            smoke_request=smoke_request,
            max_ticks=4,
            max_deliveries=4,
            max_runtime_failures=1,
        ),
        codex_cli_client=client,
    )

    recovery = recover_scheduler_state(
        smoke_request.scheduler_snapshot_path,
        smoke_request.scheduler_event_log_path,
    )
    runtime_records = JsonlRuntimeInvocationLog(
        smoke_request.runtime_invocation_log_path
    ).read_all()
    payload = result.to_json_dict()

    assert result.ok is True
    assert result.stop_reason == "all_targets_complete"
    assert result.tick_count == 2
    assert result.acknowledged_count == 2
    assert result.failed_count == 0
    assert tuple(request.task.task_id for request in client.requests) == (
        smoke_request.target_task_id,
        smoke_request.followup_task_id,
    )
    assert recovery.recovered_state.tasks[smoke_request.target_task_id].state == "complete"
    assert recovery.recovered_state.tasks[smoke_request.followup_task_id].state == "complete"
    assert len(runtime_records) == 2
    assert payload["target_task_states"] == {
        smoke_request.target_task_id: "complete",
        smoke_request.followup_task_id: "complete",
    }
    assert payload["task_state_counts"]["complete"] == 2
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False


def test_opencode_bounded_delivery_supervisor_loop_completes_chain(
    tmp_path: Path,
) -> None:
    smoke_request = CodexDeliveryE2ESmokeRequest(
        scheduler_snapshot_path=tmp_path / ".codex/scheduler/opencode-c2-state.json",
        scheduler_event_log_path=tmp_path / ".codex/scheduler/opencode-c2-events.jsonl",
        artifact_store_path=tmp_path / ".codex/orchestration/opencode-exchange-artifacts.json",
        dispatcher_state_path=tmp_path / ".codex/scheduler/opencode-dispatcher-state.json",
        dispatch_event_log_path=tmp_path / ".codex/scheduler/opencode-dispatcher-events.jsonl",
        delivery_state_path=tmp_path / ".codex/scheduler/opencode-delivery-state.json",
        delivery_event_log_path=tmp_path / ".codex/scheduler/opencode-delivery-events.jsonl",
        runtime_invocation_log_path=tmp_path / ".codex/runtime/opencode-invocations.jsonl",
        initialize_fixture=True,
        require_host_ready=False,
        timestamp="2026-06-29T11:00:00+00:00",
        runtime_invocation_max_attempts=1,
        host_id="host:opencode-loop-test",
        host_invocation_id="host-owned-opencode-loop-test",
    )
    client = _SequenceOpenCodeCliClient(
        (
            OpenCodeCliResult(summary="first complete", output_text="first complete"),
            OpenCodeCliResult(summary="followup complete", output_text="followup complete"),
        )
    )

    result = run_bounded_opencode_delivery_supervisor_loop(
        CodexDeliveryBoundedLoopRequest(
            smoke_request=smoke_request,
            max_ticks=4,
            max_deliveries=4,
            max_runtime_failures=1,
        ),
        opencode_cli_client=client,
    )

    recovery = recover_scheduler_state(
        smoke_request.scheduler_snapshot_path,
        smoke_request.scheduler_event_log_path,
    )
    runtime_records = JsonlRuntimeInvocationLog(
        smoke_request.runtime_invocation_log_path
    ).read_all()
    payload = result.to_json_dict()

    assert result.ok is True
    assert result.stop_reason == "all_targets_complete"
    assert result.tick_count == 2
    assert result.acknowledged_count == 2
    assert result.failed_count == 0
    assert tuple(request.task.task_id for request in client.requests) == (
        smoke_request.target_task_id,
        smoke_request.followup_task_id,
    )
    assert all(request.agent.runtime_provider == "opencode" for request in client.requests)
    assert recovery.recovered_state.tasks[smoke_request.target_task_id].state == "complete"
    assert recovery.recovered_state.tasks[smoke_request.followup_task_id].state == "complete"
    assert recovery.recovered_state.tasks[smoke_request.target_task_id].agent.runtime_provider == "opencode"
    assert recovery.recovered_state.tasks[smoke_request.followup_task_id].output_artifact_ref.ref_id == (
        f"{smoke_request.followup_task_id}:opencode-result"
    )
    assert len(runtime_records) == 2
    assert all(record.provider == "opencode" for record in runtime_records)
    assert all(record.runtime_surface == "host-owned-opencode-delivery-supervisor-once" for record in runtime_records)
    assert payload["runtime_provider"] == "opencode"
    assert payload["authority_split"]["runtime_provider"] == "opencode"
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False


def test_bounded_codex_delivery_supervisor_loop_multilane_fixture(
    tmp_path: Path,
) -> None:
    smoke_request = CodexDeliveryE2ESmokeRequest(
        scheduler_snapshot_path=tmp_path / ".codex/scheduler/c6-state.json",
        scheduler_event_log_path=tmp_path / ".codex/scheduler/c6-events.jsonl",
        artifact_store_path=tmp_path / ".codex/orchestration/exchange-artifacts.json",
        dispatcher_state_path=tmp_path / ".codex/scheduler/dispatcher-state.json",
        dispatch_event_log_path=tmp_path / ".codex/scheduler/dispatcher-events.jsonl",
        delivery_state_path=tmp_path / ".codex/scheduler/delivery-state.json",
        delivery_event_log_path=tmp_path / ".codex/scheduler/delivery-events.jsonl",
        runtime_invocation_log_path=tmp_path / ".codex/runtime/invocations.jsonl",
        initialize_fixture=True,
        fixture="multilane",
        require_host_ready=False,
        timestamp="2026-06-27T11:00:00+00:00",
        runtime_invocation_max_attempts=1,
    )
    client = _SequenceCodexCliClient(
        (
            CodexCliResult(summary="lane a complete", output_text="lane a complete"),
            CodexCliResult(summary="lane b complete", output_text="lane b complete"),
            CodexCliResult(summary="followup complete", output_text="followup complete"),
        )
    )

    result = run_bounded_codex_delivery_supervisor_loop(
        CodexDeliveryBoundedLoopRequest(
            smoke_request=smoke_request,
            max_ticks=4,
            max_deliveries=4,
            max_runtime_failures=1,
        ),
        codex_cli_client=client,
    )

    recovery = recover_scheduler_state(
        smoke_request.scheduler_snapshot_path,
        smoke_request.scheduler_event_log_path,
    )
    delivery_state = read_leader_worker_delivery_state(smoke_request.delivery_state_path)
    payload = result.to_json_dict()

    assert result.ok is True
    assert result.stop_reason == "all_targets_complete"
    assert result.acknowledged_count == 3
    assert result.fixture.fixture == "multilane"
    assert tuple(request.task.task_id for request in client.requests) == (
        smoke_request.target_task_id,
        smoke_request.parallel_task_id,
        smoke_request.followup_task_id,
    )
    assert tuple(request.task.scope.lane_id for request in client.requests[:2]) == (
        smoke_request.codex_lane_id,
        smoke_request.parallel_lane_id,
    )
    assert recovery.recovered_state.tasks[smoke_request.target_task_id].state == "complete"
    assert recovery.recovered_state.tasks[smoke_request.parallel_task_id].state == "complete"
    assert recovery.recovered_state.tasks[smoke_request.followup_task_id].state == "complete"
    assert payload["target_task_states"] == {
        smoke_request.target_task_id: "complete",
        smoke_request.parallel_task_id: "complete",
        smoke_request.followup_task_id: "complete",
    }
    assert payload["task_state_counts"]["complete"] == 3
    assert delivery_state is not None
    assert _state_counts_from_delivery_records(delivery_state)["acknowledged"] == 3
    assert payload["concurrency"]["requested_max_concurrent_deliveries"] == 1
    assert payload["concurrency"]["process_parallel_execution"] is False
    assert payload["concurrency"]["max_observed_concurrent_batch_size"] == 1
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False


def test_codex_delivery_supervisor_keeps_same_lane_records_out_of_concurrent_batch(
    tmp_path: Path,
) -> None:
    snapshot = tmp_path / ".codex/scheduler/state.json"
    event_log = tmp_path / ".codex/scheduler/events.jsonl"
    artifact_store = tmp_path / ".codex/orchestration/exchange-artifacts.json"
    dispatcher_state = tmp_path / ".codex/scheduler/dispatcher-state.json"
    dispatch_log = tmp_path / ".codex/scheduler/dispatcher-events.jsonl"
    delivery_state_path = tmp_path / ".codex/scheduler/delivery-state.json"
    delivery_log = tmp_path / ".codex/scheduler/delivery-events.jsonl"
    runtime_log = tmp_path / ".codex/runtime/invocations.jsonl"
    event_log.parent.mkdir(parents=True, exist_ok=True)
    event_log.write_text("", encoding="utf-8")
    JsonArtifactVersionStore(artifact_store)
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-same-lane-a": ScheduledTask(
                    task_id="task-same-lane-a",
                    title="Same lane A",
                    instruction="Run first same-lane Codex task",
                    agent=AgentSpec(agent_id="agent:same-lane-a", runtime_provider="codex"),
                    state="ready",
                    context_scope=ContextScope(context_id="ctx:same-lane", lane_id="lane:same"),
                    output_artifact_id="task-same-lane-a:result",
                ),
                "task-same-lane-b": ScheduledTask(
                    task_id="task-same-lane-b",
                    title="Same lane B",
                    instruction="Run second same-lane Codex task",
                    agent=AgentSpec(agent_id="agent:same-lane-b", runtime_provider="codex"),
                    state="ready",
                    context_scope=ContextScope(context_id="ctx:same-lane", lane_id="lane:same"),
                    output_artifact_id="task-same-lane-b:result",
                ),
            }
        ),
        snapshot,
    )
    run_leader_worker_dispatcher_tick(
        LeaderWorkerDispatcherTickRequest(
            dispatcher_state_path=dispatcher_state,
            dispatch_event_log_path=dispatch_log,
            scheduler_snapshot_path=snapshot,
            scheduler_event_log_path=event_log,
            artifact_store_path=artifact_store,
            worker_agent_ids=("agent:same-lane-a", "agent:same-lane-b"),
            timestamp="2026-06-28T10:00:00+00:00",
        )
    )
    sync_leader_worker_delivery_from_dispatch_log(
        LeaderWorkerDeliverySyncRequest(
            delivery_state_path=delivery_state_path,
            delivery_event_log_path=delivery_log,
            dispatch_event_log_path=dispatch_log,
            timestamp="2026-06-28T10:00:01+00:00",
            host_id="host:test",
        )
    )
    client = _RecordingCodexCliClient(
        CodexCliResult(summary="same lane A complete", output_text="same lane A complete")
    )

    result = run_codex_delivery_supervisor_once(
        CodexDeliverySupervisorRequest(
            delivery_state_path=delivery_state_path,
            delivery_event_log_path=delivery_log,
            scheduler_snapshot_path=snapshot,
            scheduler_event_log_path=event_log,
            runtime_invocation_log_path=runtime_log,
            artifact_store_path=artifact_store,
            consume_success_results=True,
            max_deliveries=2,
            max_concurrent_deliveries=2,
            timestamp="2026-06-28T10:00:02+00:00",
            host_id="host:codex-test",
            host_invocation_id="host-invocation:same-lane-batch",
        ),
        codex_cli_client=client,
    )

    state = read_leader_worker_delivery_state(delivery_state_path)
    payload = result.to_json_dict()

    assert result.ok is True
    assert result.attempted_count == 1
    assert tuple(request.task.task_id for request in client.requests) == (
        "task-same-lane-a",
    )
    assert payload["concurrency"]["process_parallel_execution"] is False
    assert payload["concurrency"]["max_observed_concurrent_batch_size"] == 1
    assert state is not None
    by_task_id = {
        record.task_id: record
        for record in state.records.values()
        if record.task_id
    }
    assert by_task_id["task-same-lane-a"].delivery_state == "acknowledged"
    assert by_task_id["task-same-lane-b"].delivery_state == "pending"


def test_bounded_codex_delivery_supervisor_loop_runs_lane_distinct_codex_concurrently(
    tmp_path: Path,
) -> None:
    smoke_request = CodexDeliveryE2ESmokeRequest(
        scheduler_snapshot_path=tmp_path / ".codex/scheduler/c8-state.json",
        scheduler_event_log_path=tmp_path / ".codex/scheduler/c8-events.jsonl",
        artifact_store_path=tmp_path / ".codex/orchestration/exchange-artifacts.json",
        dispatcher_state_path=tmp_path / ".codex/scheduler/dispatcher-state.json",
        dispatch_event_log_path=tmp_path / ".codex/scheduler/dispatcher-events.jsonl",
        delivery_state_path=tmp_path / ".codex/scheduler/delivery-state.json",
        delivery_event_log_path=tmp_path / ".codex/scheduler/delivery-events.jsonl",
        runtime_invocation_log_path=tmp_path / ".codex/runtime/invocations.jsonl",
        initialize_fixture=True,
        fixture="multilane",
        require_host_ready=False,
        timestamp="2026-06-28T09:00:00+00:00",
        runtime_invocation_max_attempts=1,
    )
    client = _BarrierCodexCliClient(
        expected_concurrent_calls=2,
        hold_after_barrier_seconds=0.05,
    )

    result = run_bounded_codex_delivery_supervisor_loop(
        CodexDeliveryBoundedLoopRequest(
            smoke_request=smoke_request,
            max_ticks=4,
            max_deliveries=4,
            max_runtime_failures=1,
            max_concurrent_deliveries=2,
        ),
        codex_cli_client=client,
    )

    recovery = recover_scheduler_state(
        smoke_request.scheduler_snapshot_path,
        smoke_request.scheduler_event_log_path,
    )
    runtime_records = JsonlRuntimeInvocationLog(
        smoke_request.runtime_invocation_log_path
    ).read_all()
    payload = result.to_json_dict()

    assert result.ok is True
    assert result.stop_reason == "all_targets_complete"
    assert client.max_active_calls >= 2
    assert tuple(sorted(client.first_batch_task_ids)) == tuple(
        sorted((smoke_request.target_task_id, smoke_request.parallel_task_id))
    )
    assert tuple(request.task.task_id for request in client.requests[:2]) == (
        smoke_request.target_task_id,
        smoke_request.parallel_task_id,
    )
    assert recovery.recovered_state.tasks[smoke_request.target_task_id].state == "complete"
    assert recovery.recovered_state.tasks[smoke_request.parallel_task_id].state == "complete"
    assert recovery.recovered_state.tasks[smoke_request.followup_task_id].state == "complete"
    assert len(runtime_records) == 3
    assert tuple(sorted(record.task_id for record in runtime_records[:2])) == tuple(
        sorted((smoke_request.target_task_id, smoke_request.parallel_task_id))
    )
    assert all(record.provider == "codex" for record in runtime_records)
    assert all(record.status == "succeeded" for record in runtime_records)
    assert all(
        record.to_json_dict()["authority_split"]["raw_transcript_persisted"] is False
        for record in runtime_records
    )
    assert payload["concurrency"]["requested_max_concurrent_deliveries"] == 2
    assert payload["concurrency"]["process_parallel_execution"] is True
    assert payload["concurrency"]["max_observed_concurrent_batch_size"] == 2
    assert payload["concurrency"]["serialized_writeback"] is True
    first_iteration = payload["iterations"][0]["codex_delivery"]
    assert first_iteration["concurrency"]["process_parallel_execution"] is True
    assert first_iteration["concurrency"]["max_observed_concurrent_batch_size"] == 2
    assert payload["authority_split"]["process_parallel_execution"] is True
    assert payload["authority_split"]["serialized_writeback"] is True
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False


def test_opencode_bounded_delivery_supervisor_loop_runs_lane_distinct_concurrently(
    tmp_path: Path,
) -> None:
    smoke_request = CodexDeliveryE2ESmokeRequest(
        scheduler_snapshot_path=tmp_path / ".codex/scheduler/opencode-c8-state.json",
        scheduler_event_log_path=tmp_path / ".codex/scheduler/opencode-c8-events.jsonl",
        artifact_store_path=tmp_path / ".codex/orchestration/opencode-c8-exchange-artifacts.json",
        dispatcher_state_path=tmp_path / ".codex/scheduler/opencode-c8-dispatcher-state.json",
        dispatch_event_log_path=tmp_path / ".codex/scheduler/opencode-c8-dispatcher-events.jsonl",
        delivery_state_path=tmp_path / ".codex/scheduler/opencode-c8-delivery-state.json",
        delivery_event_log_path=tmp_path / ".codex/scheduler/opencode-c8-delivery-events.jsonl",
        runtime_invocation_log_path=tmp_path / ".codex/runtime/opencode-c8-invocations.jsonl",
        initialize_fixture=True,
        fixture="multilane",
        require_host_ready=False,
        timestamp="2026-06-29T11:20:00+00:00",
        runtime_invocation_max_attempts=1,
        host_id="host:opencode-concurrent-test",
        host_invocation_id="host-owned-opencode-concurrent-test",
    )
    client = _BarrierOpenCodeCliClient(
        expected_concurrent_calls=2,
        hold_after_barrier_seconds=0.05,
    )

    result = run_bounded_opencode_delivery_supervisor_loop(
        CodexDeliveryBoundedLoopRequest(
            smoke_request=smoke_request,
            max_ticks=4,
            max_deliveries=4,
            max_runtime_failures=1,
            max_concurrent_deliveries=2,
        ),
        opencode_cli_client=client,
    )

    recovery = recover_scheduler_state(
        smoke_request.scheduler_snapshot_path,
        smoke_request.scheduler_event_log_path,
    )
    runtime_records = JsonlRuntimeInvocationLog(
        smoke_request.runtime_invocation_log_path
    ).read_all()
    payload = result.to_json_dict()

    assert result.ok is True
    assert result.stop_reason == "all_targets_complete"
    assert client.max_active_calls >= 2
    assert tuple(sorted(client.first_batch_task_ids)) == tuple(
        sorted((smoke_request.target_task_id, smoke_request.parallel_task_id))
    )
    assert tuple(request.task.task_id for request in client.requests[:2]) == (
        smoke_request.target_task_id,
        smoke_request.parallel_task_id,
    )
    assert recovery.recovered_state.tasks[smoke_request.target_task_id].state == "complete"
    assert recovery.recovered_state.tasks[smoke_request.parallel_task_id].state == "complete"
    assert recovery.recovered_state.tasks[smoke_request.followup_task_id].state == "complete"
    assert len(runtime_records) == 3
    assert all(record.provider == "opencode" for record in runtime_records)
    assert all(record.status == "succeeded" for record in runtime_records)
    assert payload["runtime_provider"] == "opencode"
    assert payload["concurrency"]["requested_max_concurrent_deliveries"] == 2
    assert payload["concurrency"]["process_parallel_execution"] is True
    assert payload["concurrency"]["max_observed_concurrent_batch_size"] == 2
    assert payload["concurrency"]["serialized_writeback"] is True
    assert payload["authority_split"]["runtime_provider"] == "opencode"
    assert payload["authority_split"]["process_parallel_execution"] is True
    assert payload["authority_split"]["serialized_writeback"] is True
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False


def test_live_codex_concurrent_worker_smoke_reports_audit_overlap(
    tmp_path: Path,
) -> None:
    smoke_request = CodexDeliveryE2ESmokeRequest(
        scheduler_snapshot_path=tmp_path / ".codex/scheduler/c9-state.json",
        scheduler_event_log_path=tmp_path / ".codex/scheduler/c9-events.jsonl",
        artifact_store_path=tmp_path / ".codex/orchestration/c9-exchange-artifacts.json",
        dispatcher_state_path=tmp_path / ".codex/scheduler/c9-dispatcher-state.json",
        dispatch_event_log_path=tmp_path / ".codex/scheduler/c9-dispatcher-events.jsonl",
        delivery_state_path=tmp_path / ".codex/scheduler/c9-delivery-state.json",
        delivery_event_log_path=tmp_path / ".codex/scheduler/c9-delivery-events.jsonl",
        runtime_invocation_log_path=tmp_path / ".codex/runtime/c9-invocations.jsonl",
        initialize_fixture=True,
        fixture="multilane",
        require_host_ready=False,
        timestamp="2026-06-28T10:00:00+00:00",
        runtime_invocation_max_attempts=1,
    )
    report_path = tmp_path / ".codex/scheduler/c9-report.json"
    client = _BarrierCodexCliClient(
        expected_concurrent_calls=2,
        hold_after_barrier_seconds=0.05,
    )

    result = run_live_codex_concurrent_worker_smoke(
        LiveCodexConcurrentWorkerSmokeRequest(
            loop_request=CodexDeliveryBoundedLoopRequest(
                smoke_request=smoke_request,
                max_ticks=4,
                max_deliveries=4,
                max_runtime_failures=1,
                max_concurrent_deliveries=2,
            ),
            report_path=report_path,
        ),
        codex_cli_client=client,
    )
    payload = result.to_json_dict()
    written = json.loads(report_path.read_text(encoding="utf-8"))

    assert result.ok is True
    assert payload["verdict"] == "passed"
    assert payload["counts"]["worker_tasks"] == 3
    assert payload["counts"]["attempted_live_codex_invocations"] == 3
    assert payload["counts"]["completed_workers"] == 3
    assert payload["counts"]["failed_workers"] == 0
    assert payload["counts"]["skipped_or_waiting_workers"] == 0
    assert payload["counts"]["overlap_pair_count"] >= 1
    assert tuple(sorted(payload["first_concurrent_batch"]["task_ids"])) == tuple(
        sorted((smoke_request.target_task_id, smoke_request.parallel_task_id))
    )
    assert payload["overlap"]["proven"] is True
    assert payload["bounded_loop"]["concurrency"]["serialized_writeback"] is True
    assert payload["authority_split"]["process_parallel_execution"] is True
    assert payload["authority_split"]["serialized_writeback"] is True
    assert payload["authority_split"]["worker_direct_local_trajectory_mutation"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert payload["authority_split"]["raw_transcript_persisted"] is False
    assert written["verdict"] == "passed"
    assert written["overlap"]["proven"] is True


def test_live_opencode_concurrent_worker_smoke_reports_audit_overlap(
    tmp_path: Path,
) -> None:
    smoke_request = CodexDeliveryE2ESmokeRequest(
        scheduler_snapshot_path=tmp_path / ".codex/scheduler/opencode-c9-state.json",
        scheduler_event_log_path=tmp_path / ".codex/scheduler/opencode-c9-events.jsonl",
        artifact_store_path=tmp_path / ".codex/orchestration/opencode-c9-exchange-artifacts.json",
        dispatcher_state_path=tmp_path / ".codex/scheduler/opencode-c9-dispatcher-state.json",
        dispatch_event_log_path=tmp_path / ".codex/scheduler/opencode-c9-dispatcher-events.jsonl",
        delivery_state_path=tmp_path / ".codex/scheduler/opencode-c9-delivery-state.json",
        delivery_event_log_path=tmp_path / ".codex/scheduler/opencode-c9-delivery-events.jsonl",
        runtime_invocation_log_path=tmp_path / ".codex/runtime/opencode-c9-invocations.jsonl",
        initialize_fixture=True,
        fixture="multilane",
        require_host_ready=False,
        timestamp="2026-06-29T10:00:00+00:00",
        runtime_invocation_max_attempts=1,
        runtime_provider="opencode",
        target_task_id="opencode-smoke:worker",
        parallel_task_id="opencode-smoke:parallel-worker",
        waiting_task_id="opencode-smoke:waiting-non-opencode",
        followup_task_id="opencode-smoke:followup",
        codex_agent_id="agent:opencode-smoke-worker",
        parallel_agent_id="agent:opencode-smoke-parallel-worker",
        followup_agent_id="agent:opencode-smoke-followup",
        waiting_agent_id="agent:opencode-smoke-waiting",
        codex_lane_id="lane:opencode-smoke",
        parallel_lane_id="lane:opencode-smoke-parallel",
        followup_lane_id="lane:opencode-smoke",
        host_id="host:opencode-c9-test",
        host_invocation_id="host-owned-opencode-c9-test",
        trajectory_id="opencode-live-concurrent-worker-smoke",
    )
    report_path = tmp_path / ".codex/scheduler/opencode-c9-report.json"
    client = _BarrierOpenCodeCliClient(
        expected_concurrent_calls=2,
        hold_after_barrier_seconds=0.05,
    )

    result = run_live_opencode_concurrent_worker_smoke(
        LiveOpenCodeConcurrentWorkerSmokeRequest(
            loop_request=CodexDeliveryBoundedLoopRequest(
                smoke_request=smoke_request,
                max_ticks=4,
                max_deliveries=4,
                max_runtime_failures=1,
                max_concurrent_deliveries=2,
            ),
            report_path=report_path,
        ),
        opencode_cli_client=client,
    )
    payload = result.to_json_dict()
    written = json.loads(report_path.read_text(encoding="utf-8"))

    assert result.ok is True
    assert payload["runtime_provider"] == "opencode"
    assert payload["verdict"] == "passed"
    assert payload["diagnostic"] == "live OpenCode invocation overlap proven"
    assert payload["counts"]["worker_tasks"] == 3
    assert payload["counts"]["attempted_live_provider_invocations"] == 3
    assert payload["counts"]["attempted_live_opencode_invocations"] == 3
    assert payload["counts"]["attempted_live_codex_invocations"] == 0
    assert payload["counts"]["completed_workers"] == 3
    assert payload["counts"]["failed_workers"] == 0
    assert payload["counts"]["skipped_or_waiting_workers"] == 0
    assert payload["counts"]["overlap_pair_count"] >= 1
    assert tuple(sorted(payload["first_concurrent_batch"]["task_ids"])) == tuple(
        sorted((smoke_request.target_task_id, smoke_request.parallel_task_id))
    )
    assert payload["overlap"]["proven"] is True
    assert payload["bounded_loop"]["runtime_provider"] == "opencode"
    assert payload["bounded_loop"]["concurrency"]["serialized_writeback"] is True
    assert payload["authority_split"]["runtime_provider"] == "opencode"
    assert payload["authority_split"]["workflow_surface"] == (
        "host-owned-live-opencode-concurrent-worker-smoke"
    )
    assert payload["authority_split"]["process_parallel_execution"] is True
    assert payload["authority_split"]["serialized_writeback"] is True
    assert payload["authority_split"]["worker_direct_local_trajectory_mutation"] is False
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert payload["authority_split"]["raw_transcript_persisted"] is False
    assert written["runtime_provider"] == "opencode"
    assert written["verdict"] == "passed"
    assert written["overlap"]["proven"] is True


def test_live_opencode_concurrent_worker_smoke_does_not_pass_failed_overlap(
    tmp_path: Path,
) -> None:
    smoke_request = CodexDeliveryE2ESmokeRequest(
        scheduler_snapshot_path=tmp_path / ".codex/scheduler/opencode-failed-c9-state.json",
        scheduler_event_log_path=tmp_path / ".codex/scheduler/opencode-failed-c9-events.jsonl",
        artifact_store_path=tmp_path / ".codex/orchestration/opencode-failed-c9-exchange-artifacts.json",
        dispatcher_state_path=tmp_path / ".codex/scheduler/opencode-failed-c9-dispatcher-state.json",
        dispatch_event_log_path=tmp_path / ".codex/scheduler/opencode-failed-c9-dispatcher-events.jsonl",
        delivery_state_path=tmp_path / ".codex/scheduler/opencode-failed-c9-delivery-state.json",
        delivery_event_log_path=tmp_path / ".codex/scheduler/opencode-failed-c9-delivery-events.jsonl",
        runtime_invocation_log_path=tmp_path / ".codex/runtime/opencode-failed-c9-invocations.jsonl",
        initialize_fixture=True,
        fixture="multilane",
        require_host_ready=False,
        timestamp="2026-06-29T10:05:00+00:00",
        runtime_invocation_max_attempts=1,
        runtime_provider="opencode",
        target_task_id="opencode-smoke:worker",
        parallel_task_id="opencode-smoke:parallel-worker",
        waiting_task_id="opencode-smoke:waiting-non-opencode",
        followup_task_id="opencode-smoke:followup",
        codex_agent_id="agent:opencode-smoke-worker",
        parallel_agent_id="agent:opencode-smoke-parallel-worker",
        followup_agent_id="agent:opencode-smoke-followup",
        waiting_agent_id="agent:opencode-smoke-waiting",
        codex_lane_id="lane:opencode-smoke",
        parallel_lane_id="lane:opencode-smoke-parallel",
        followup_lane_id="lane:opencode-smoke",
        host_id="host:opencode-failed-c9-test",
        host_invocation_id="host-owned-opencode-failed-c9-test",
        trajectory_id="opencode-live-concurrent-worker-smoke",
    )

    result = run_live_opencode_concurrent_worker_smoke(
        LiveOpenCodeConcurrentWorkerSmokeRequest(
            loop_request=CodexDeliveryBoundedLoopRequest(
                smoke_request=smoke_request,
                max_ticks=2,
                max_deliveries=2,
                max_runtime_failures=1,
                max_concurrent_deliveries=2,
            ),
            report_path=tmp_path / ".codex/scheduler/opencode-failed-c9-report.json",
        ),
        opencode_cli_client=_BarrierFailingOpenCodeCliClient(
            expected_concurrent_calls=2,
            hold_after_barrier_seconds=0.05,
        ),
    )
    payload = result.to_json_dict()

    assert result.overlap_proven is True
    assert result.ok is False
    assert payload["verdict"] == "inconclusive"
    assert payload["overlap"]["proven"] is True
    assert payload["counts"]["failed_workers"] == 2
    assert payload["bounded_loop"]["ok"] is False
    assert "bounded OpenCode supervisor loop did not complete successfully" in (
        payload["diagnostic"]
    )


def test_live_codex_concurrent_worker_smoke_replace_fixture_clears_auxiliary_state(
    tmp_path: Path,
) -> None:
    smoke_request = CodexDeliveryE2ESmokeRequest(
        scheduler_snapshot_path=tmp_path / ".codex/scheduler/c9-state.json",
        scheduler_event_log_path=tmp_path / ".codex/scheduler/c9-events.jsonl",
        artifact_store_path=tmp_path / ".codex/orchestration/c9-exchange-artifacts.json",
        dispatcher_state_path=tmp_path / ".codex/scheduler/c9-dispatcher-state.json",
        dispatch_event_log_path=tmp_path / ".codex/scheduler/c9-dispatcher-events.jsonl",
        delivery_state_path=tmp_path / ".codex/scheduler/c9-delivery-state.json",
        delivery_event_log_path=tmp_path / ".codex/scheduler/c9-delivery-events.jsonl",
        runtime_invocation_log_path=tmp_path / ".codex/runtime/c9-invocations.jsonl",
        initialize_fixture=True,
        replace_existing_fixture=True,
        fixture="multilane",
        require_host_ready=False,
        timestamp="2026-06-28T10:10:00+00:00",
        runtime_invocation_max_attempts=1,
    )
    request = LiveCodexConcurrentWorkerSmokeRequest(
        loop_request=CodexDeliveryBoundedLoopRequest(
            smoke_request=smoke_request,
            max_ticks=4,
            max_deliveries=4,
            max_runtime_failures=1,
            max_concurrent_deliveries=2,
        ),
        report_path=tmp_path / ".codex/scheduler/c9-report.json",
    )

    first = run_live_codex_concurrent_worker_smoke(
        request,
        codex_cli_client=_BarrierCodexCliClient(
            expected_concurrent_calls=2,
            hold_after_barrier_seconds=0.05,
        ),
    )
    second_client = _BarrierCodexCliClient(
        expected_concurrent_calls=2,
        hold_after_barrier_seconds=0.05,
    )
    second = run_live_codex_concurrent_worker_smoke(
        request,
        codex_cli_client=second_client,
    )

    assert first.ok is True
    assert second.ok is True
    assert second.loop_result.iterations[0].dispatcher_tick.tick_record.decision_count >= 2
    assert second_client.max_active_calls >= 2
    assert len(JsonlRuntimeInvocationLog(smoke_request.runtime_invocation_log_path).read_all()) == 3


def test_monitoring_api_summarizes_live_codex_smoke_without_mutation(
    tmp_path: Path,
) -> None:
    smoke_request = CodexDeliveryE2ESmokeRequest(
        scheduler_snapshot_path=tmp_path / ".codex/scheduler/monitor-state.json",
        scheduler_event_log_path=tmp_path / ".codex/scheduler/monitor-events.jsonl",
        artifact_store_path=tmp_path / ".codex/orchestration/monitor-exchange-artifacts.json",
        dispatcher_state_path=tmp_path / ".codex/scheduler/monitor-dispatcher-state.json",
        dispatch_event_log_path=tmp_path / ".codex/scheduler/monitor-dispatcher-events.jsonl",
        delivery_state_path=tmp_path / ".codex/scheduler/monitor-delivery-state.json",
        delivery_event_log_path=tmp_path / ".codex/scheduler/monitor-delivery-events.jsonl",
        runtime_invocation_log_path=tmp_path / ".codex/runtime/monitor-invocations.jsonl",
        initialize_fixture=True,
        fixture="multilane",
        require_host_ready=False,
        timestamp="2026-06-28T11:00:00+00:00",
        runtime_invocation_max_attempts=1,
    )
    report_path = tmp_path / ".codex/scheduler/monitor-live-smoke-report.json"
    run_live_codex_concurrent_worker_smoke(
        LiveCodexConcurrentWorkerSmokeRequest(
            loop_request=CodexDeliveryBoundedLoopRequest(
                smoke_request=smoke_request,
                max_ticks=4,
                max_deliveries=4,
                max_runtime_failures=1,
                max_concurrent_deliveries=2,
            ),
            report_path=report_path,
        ),
        codex_cli_client=_BarrierCodexCliClient(
            expected_concurrent_calls=2,
            hold_after_barrier_seconds=0.05,
        ),
    )
    event_count_before = len(
        JsonlSchedulerEventLog(smoke_request.scheduler_event_log_path).read_all()
    )
    runtime_count_before = len(
        JsonlRuntimeInvocationLog(smoke_request.runtime_invocation_log_path).read_all()
    )

    snapshot = inspect_monitoring_snapshot(
        MonitoringSnapshotRequest(
            scheduler_snapshot_path=smoke_request.scheduler_snapshot_path,
            scheduler_event_log_path=smoke_request.scheduler_event_log_path,
            delivery_state_path=smoke_request.delivery_state_path,
            runtime_invocation_log_path=smoke_request.runtime_invocation_log_path,
            artifact_store_path=smoke_request.artifact_store_path,
            live_codex_smoke_report_path=report_path,
            target_task_ids=(
                smoke_request.target_task_id,
                smoke_request.parallel_task_id,
                smoke_request.followup_task_id,
            ),
        )
    )
    payload = snapshot.to_json_dict()

    assert snapshot.ok is True
    assert payload["schema_version"] == "monitoring-snapshot.v1"
    assert payload["scheduler"]["task_state_counts"]["complete"] == 3
    assert payload["delivery"]["state_counts"]["acknowledged"] == 3
    assert payload["runtimeInvocations"]["counts"]["record_count"] == 3
    assert payload["runtimeInvocations"]["concurrency"]["liveOverlapProven"] is True
    assert payload["liveCodexSmoke"]["ok"] is True
    assert payload["liveCodexSmoke"]["verdict"] == "passed"
    assert payload["workerReports"]["mode"] == "leader-owned-consumer"
    assert any(
        signal["kind"] == "live_codex_overlap_proven"
        for signal in payload["operatorSignals"]
    )
    assert payload["authoritySplit"]["readModelOnly"] is True
    assert payload["authoritySplit"]["localWorkTrajectoryMutated"] is False
    assert len(JsonlSchedulerEventLog(smoke_request.scheduler_event_log_path).read_all()) == event_count_before
    assert len(JsonlRuntimeInvocationLog(smoke_request.runtime_invocation_log_path).read_all()) == runtime_count_before


def test_monitoring_api_handles_missing_live_smoke_report(
    tmp_path: Path,
) -> None:
    smoke_request = CodexDeliveryE2ESmokeRequest(
        scheduler_snapshot_path=tmp_path / ".codex/scheduler/monitor-state.json",
        scheduler_event_log_path=tmp_path / ".codex/scheduler/monitor-events.jsonl",
        artifact_store_path=tmp_path / ".codex/orchestration/monitor-exchange-artifacts.json",
        dispatcher_state_path=tmp_path / ".codex/scheduler/monitor-dispatcher-state.json",
        dispatch_event_log_path=tmp_path / ".codex/scheduler/monitor-dispatcher-events.jsonl",
        delivery_state_path=tmp_path / ".codex/scheduler/monitor-delivery-state.json",
        delivery_event_log_path=tmp_path / ".codex/scheduler/monitor-delivery-events.jsonl",
        runtime_invocation_log_path=tmp_path / ".codex/runtime/monitor-invocations.jsonl",
        initialize_fixture=True,
        fixture="multilane",
        require_host_ready=False,
        timestamp="2026-06-28T11:10:00+00:00",
        runtime_invocation_max_attempts=1,
    )
    run_bounded_codex_delivery_supervisor_loop(
        CodexDeliveryBoundedLoopRequest(
            smoke_request=smoke_request,
            max_ticks=4,
            max_deliveries=4,
            max_runtime_failures=1,
            max_concurrent_deliveries=2,
        ),
        codex_cli_client=_BarrierCodexCliClient(
            expected_concurrent_calls=2,
            hold_after_barrier_seconds=0.05,
        ),
    )

    snapshot = inspect_monitoring_snapshot(
        MonitoringSnapshotRequest(
            scheduler_snapshot_path=smoke_request.scheduler_snapshot_path,
            scheduler_event_log_path=smoke_request.scheduler_event_log_path,
            delivery_state_path=smoke_request.delivery_state_path,
            runtime_invocation_log_path=smoke_request.runtime_invocation_log_path,
            artifact_store_path=smoke_request.artifact_store_path,
            live_codex_smoke_report_path=tmp_path / ".codex/scheduler/missing-report.json",
        )
    )
    payload = snapshot.to_json_dict()

    assert snapshot.ok is True
    assert payload["liveCodexSmoke"]["exists"] is False
    assert payload["liveCodexSmoke"]["verdict"] == "unavailable"
    assert any(
        signal["kind"] == "live_codex_smoke_missing"
        for signal in payload["operatorSignals"]
    )


def test_codex_runtime_status_summarizes_multilane_loop_without_mutation(
    tmp_path: Path,
) -> None:
    smoke_request = CodexDeliveryE2ESmokeRequest(
        scheduler_snapshot_path=tmp_path / ".codex/scheduler/c7-state.json",
        scheduler_event_log_path=tmp_path / ".codex/scheduler/c7-events.jsonl",
        artifact_store_path=tmp_path / ".codex/orchestration/exchange-artifacts.json",
        dispatcher_state_path=tmp_path / ".codex/scheduler/dispatcher-state.json",
        dispatch_event_log_path=tmp_path / ".codex/scheduler/dispatcher-events.jsonl",
        delivery_state_path=tmp_path / ".codex/scheduler/delivery-state.json",
        delivery_event_log_path=tmp_path / ".codex/scheduler/delivery-events.jsonl",
        runtime_invocation_log_path=tmp_path / ".codex/runtime/invocations.jsonl",
        initialize_fixture=True,
        fixture="multilane",
        require_host_ready=False,
        timestamp="2026-06-27T12:00:00+00:00",
        runtime_invocation_max_attempts=1,
    )
    client = _SequenceCodexCliClient(
        (
            CodexCliResult(summary="lane a complete", output_text="lane a complete"),
            CodexCliResult(summary="lane b complete", output_text="lane b complete"),
            CodexCliResult(summary="followup complete", output_text="followup complete"),
        )
    )
    run_bounded_codex_delivery_supervisor_loop(
        CodexDeliveryBoundedLoopRequest(
            smoke_request=smoke_request,
            max_ticks=4,
            max_deliveries=4,
            max_runtime_failures=1,
        ),
        codex_cli_client=client,
    )
    event_count_before = len(
        JsonlSchedulerEventLog(smoke_request.scheduler_event_log_path).read_all()
    )
    runtime_count_before = len(
        JsonlRuntimeInvocationLog(smoke_request.runtime_invocation_log_path).read_all()
    )

    status = inspect_codex_runtime_status(
        CodexRuntimeStatusRequest(
            scheduler_snapshot_path=smoke_request.scheduler_snapshot_path,
            scheduler_event_log_path=smoke_request.scheduler_event_log_path,
            delivery_state_path=smoke_request.delivery_state_path,
            runtime_invocation_log_path=smoke_request.runtime_invocation_log_path,
            artifact_store_path=smoke_request.artifact_store_path,
            target_task_ids=(
                smoke_request.target_task_id,
                smoke_request.parallel_task_id,
                smoke_request.followup_task_id,
            ),
        )
    )
    payload = status.to_json_dict()

    assert status.ok is True
    assert status.next_action == "idle"
    assert status.scheduler_task_state_counts["complete"] == 3
    assert "waiting" not in status.scheduler_task_state_counts
    assert status.waiting_task_ids == ()
    assert status.target_task_states == {
        smoke_request.target_task_id: "complete",
        smoke_request.parallel_task_id: "complete",
        smoke_request.followup_task_id: "complete",
    }
    assert status.delivery_state_counts["acknowledged"] == 3
    assert status.actionable_pending_codex_delivery_count == 0
    assert status.runtime_invocation_counts["record_count"] == 3
    assert status.runtime_invocation_counts["succeeded"] == 3
    assert status.runtime_invocation_counts["provider:codex"] == 3
    assert {
        ref["ref_id"]
        for ref in status.output_artifact_refs
    } >= {
        f"{smoke_request.target_task_id}:codex-result",
        f"{smoke_request.parallel_task_id}:codex-result",
        f"{smoke_request.followup_task_id}:codex-result",
    }
    assert payload["authority_split"]["read_model_only"] is True
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert len(JsonlSchedulerEventLog(smoke_request.scheduler_event_log_path).read_all()) == event_count_before
    assert len(JsonlRuntimeInvocationLog(smoke_request.runtime_invocation_log_path).read_all()) == runtime_count_before


def test_opencode_runtime_status_summarizes_multilane_loop_without_mutation(
    tmp_path: Path,
) -> None:
    smoke_request = CodexDeliveryE2ESmokeRequest(
        scheduler_snapshot_path=tmp_path / ".codex/scheduler/opencode-status-state.json",
        scheduler_event_log_path=tmp_path / ".codex/scheduler/opencode-status-events.jsonl",
        artifact_store_path=tmp_path / ".codex/orchestration/opencode-exchange-artifacts.json",
        dispatcher_state_path=tmp_path / ".codex/scheduler/opencode-dispatcher-state.json",
        dispatch_event_log_path=tmp_path / ".codex/scheduler/opencode-dispatcher-events.jsonl",
        delivery_state_path=tmp_path / ".codex/scheduler/opencode-delivery-state.json",
        delivery_event_log_path=tmp_path / ".codex/scheduler/opencode-delivery-events.jsonl",
        runtime_invocation_log_path=tmp_path / ".codex/runtime/opencode-invocations.jsonl",
        initialize_fixture=True,
        fixture="multilane",
        require_host_ready=False,
        timestamp="2026-06-29T14:00:00+00:00",
        runtime_invocation_max_attempts=1,
        runtime_provider="opencode",
        target_task_id="opencode-status:worker",
        parallel_task_id="opencode-status:parallel-worker",
        waiting_task_id="opencode-status:waiting-non-opencode",
        followup_task_id="opencode-status:followup",
        codex_agent_id="agent:opencode-status-worker",
        parallel_agent_id="agent:opencode-status-parallel-worker",
        followup_agent_id="agent:opencode-status-followup",
        waiting_agent_id="agent:opencode-status-waiting",
        codex_lane_id="lane:opencode-status",
        parallel_lane_id="lane:opencode-status-parallel",
        followup_lane_id="lane:opencode-status",
    )
    client = _SequenceOpenCodeCliClient(
        (
            OpenCodeCliResult(summary="lane a complete", output_text="lane a complete"),
            OpenCodeCliResult(summary="lane b complete", output_text="lane b complete"),
            OpenCodeCliResult(summary="followup complete", output_text="followup complete"),
        )
    )
    run_bounded_opencode_delivery_supervisor_loop(
        CodexDeliveryBoundedLoopRequest(
            smoke_request=smoke_request,
            max_ticks=4,
            max_deliveries=4,
            max_runtime_failures=1,
        ),
        opencode_cli_client=client,
    )
    event_count_before = len(
        JsonlSchedulerEventLog(smoke_request.scheduler_event_log_path).read_all()
    )
    runtime_count_before = len(
        JsonlRuntimeInvocationLog(smoke_request.runtime_invocation_log_path).read_all()
    )

    status = inspect_opencode_runtime_status(
        OpenCodeRuntimeStatusRequest(
            scheduler_snapshot_path=smoke_request.scheduler_snapshot_path,
            scheduler_event_log_path=smoke_request.scheduler_event_log_path,
            delivery_state_path=smoke_request.delivery_state_path,
            runtime_invocation_log_path=smoke_request.runtime_invocation_log_path,
            artifact_store_path=smoke_request.artifact_store_path,
            target_task_ids=(
                smoke_request.target_task_id,
                smoke_request.parallel_task_id,
                smoke_request.followup_task_id,
            ),
        )
    )
    payload = status.to_json_dict()

    assert status.ok is True
    assert payload["runtime_provider"] == "opencode"
    assert status.next_action == "idle"
    assert status.scheduler_task_state_counts["complete"] == 3
    assert status.target_task_states == {
        smoke_request.target_task_id: "complete",
        smoke_request.parallel_task_id: "complete",
        smoke_request.followup_task_id: "complete",
    }
    assert status.delivery_state_counts["acknowledged"] == 3
    assert status.actionable_pending_delivery_count == 0
    assert status.actionable_pending_codex_delivery_count == 0
    assert status.runtime_invocation_counts["record_count"] == 3
    assert status.runtime_invocation_counts["succeeded"] == 3
    assert status.runtime_invocation_counts["provider:opencode"] == 3
    assert payload["delivery"]["actionable_pending_runtime_provider"] == "opencode"
    assert payload["delivery"]["actionable_pending_delivery_count"] == 0
    assert payload["delivery"]["actionable_pending_codex_delivery_count"] == 0
    assert payload["authority_split"]["read_model_only"] is True
    assert payload["authority_split"]["local_work_trajectory_mutated"] is False
    assert len(JsonlSchedulerEventLog(smoke_request.scheduler_event_log_path).read_all()) == event_count_before
    assert len(JsonlRuntimeInvocationLog(smoke_request.runtime_invocation_log_path).read_all()) == runtime_count_before


def test_bounded_codex_delivery_supervisor_loop_stops_at_max_deliveries(
    tmp_path: Path,
) -> None:
    smoke_request = CodexDeliveryE2ESmokeRequest(
        scheduler_snapshot_path=tmp_path / ".codex/scheduler/c2-state.json",
        scheduler_event_log_path=tmp_path / ".codex/scheduler/c2-events.jsonl",
        artifact_store_path=tmp_path / ".codex/orchestration/exchange-artifacts.json",
        dispatcher_state_path=tmp_path / ".codex/scheduler/dispatcher-state.json",
        dispatch_event_log_path=tmp_path / ".codex/scheduler/dispatcher-events.jsonl",
        delivery_state_path=tmp_path / ".codex/scheduler/delivery-state.json",
        delivery_event_log_path=tmp_path / ".codex/scheduler/delivery-events.jsonl",
        runtime_invocation_log_path=tmp_path / ".codex/runtime/invocations.jsonl",
        initialize_fixture=True,
        require_host_ready=False,
        timestamp="2026-06-26T11:10:00+00:00",
        runtime_invocation_max_attempts=1,
    )
    client = _SequenceCodexCliClient(
        (
            CodexCliResult(summary="first complete", output_text="first complete"),
            CodexCliResult(summary="followup complete", output_text="followup complete"),
        )
    )

    result = run_bounded_codex_delivery_supervisor_loop(
        CodexDeliveryBoundedLoopRequest(
            smoke_request=smoke_request,
            max_ticks=4,
            max_deliveries=1,
            max_runtime_failures=1,
        ),
        codex_cli_client=client,
    )

    recovery = recover_scheduler_state(
        smoke_request.scheduler_snapshot_path,
        smoke_request.scheduler_event_log_path,
    )

    assert result.ok is False
    assert result.stop_reason == "max_deliveries_reached"
    assert result.acknowledged_count == 1
    assert len(client.requests) == 1
    assert recovery.recovered_state.tasks[smoke_request.target_task_id].state == "complete"
    assert recovery.recovered_state.tasks[smoke_request.followup_task_id].state == "waiting"


def test_bounded_codex_delivery_supervisor_loop_retries_failed_delivery_after_restart(
    tmp_path: Path,
) -> None:
    smoke_request = CodexDeliveryE2ESmokeRequest(
        scheduler_snapshot_path=tmp_path / ".codex/scheduler/c4-state.json",
        scheduler_event_log_path=tmp_path / ".codex/scheduler/c4-events.jsonl",
        artifact_store_path=tmp_path / ".codex/orchestration/exchange-artifacts.json",
        dispatcher_state_path=tmp_path / ".codex/scheduler/dispatcher-state.json",
        dispatch_event_log_path=tmp_path / ".codex/scheduler/dispatcher-events.jsonl",
        delivery_state_path=tmp_path / ".codex/scheduler/delivery-state.json",
        delivery_event_log_path=tmp_path / ".codex/scheduler/delivery-events.jsonl",
        runtime_invocation_log_path=tmp_path / ".codex/runtime/invocations.jsonl",
        initialize_fixture=True,
        require_host_ready=False,
        timestamp="2026-06-27T09:20:00+00:00",
        runtime_invocation_max_attempts=1,
    )
    client = _SequenceCodexCliClientWithFailures(
        (
            CodexCliRuntimeError(
                error_kind="timeout",
                summary="temporary timeout",
                retryable=True,
            ),
            CodexCliResult(summary="retry completed", output_text="retry completed"),
            CodexCliResult(summary="followup completed", output_text="followup completed"),
        )
    )

    first = run_bounded_codex_delivery_supervisor_loop(
        CodexDeliveryBoundedLoopRequest(
            smoke_request=smoke_request,
            max_ticks=2,
            max_deliveries=1,
            max_runtime_failures=1,
            max_delivery_attempts_per_record=2,
        ),
        codex_cli_client=client,
    )
    second = run_bounded_codex_delivery_supervisor_loop(
        CodexDeliveryBoundedLoopRequest(
            smoke_request=replace(smoke_request, initialize_fixture=False),
            max_ticks=4,
            max_deliveries=4,
            max_runtime_failures=2,
            max_delivery_attempts_per_record=2,
        ),
        codex_cli_client=client,
    )

    recovery = recover_scheduler_state(
        smoke_request.scheduler_snapshot_path,
        smoke_request.scheduler_event_log_path,
    )
    delivery_state = read_leader_worker_delivery_state(smoke_request.delivery_state_path)
    scheduler_events = JsonlSchedulerEventLog(
        smoke_request.scheduler_event_log_path
    ).read_all()

    assert first.ok is False
    assert first.stop_reason == "max_runtime_failures_reached"
    assert second.ok is True
    assert second.stop_reason == "all_targets_complete"
    assert tuple(request.task.task_id for request in client.requests) == (
        smoke_request.target_task_id,
        smoke_request.target_task_id,
        smoke_request.followup_task_id,
    )
    assert recovery.recovered_state.tasks[smoke_request.target_task_id].state == "complete"
    assert recovery.recovered_state.tasks[smoke_request.followup_task_id].state == "complete"
    assert [
        event.event_kind for event in scheduler_events
        if event.task_id == smoke_request.target_task_id
    ] == ["task_completed"]
    assert delivery_state is not None
    assert _state_counts_from_delivery_records(delivery_state)["acknowledged"] == 2


class _RuntimeAuditResult:
    def __init__(
        self,
        summary: str,
        metadata: dict[str, object] | None = None,
    ) -> None:
        self.summary = summary
        self.metadata = metadata or {}


class _RetryableRuntimeAuditError(Exception):
    error_kind = "timeout"
    raw_error_type = "TimeoutExpired"
    retryable = True
    summary = "temporary timeout with OPENAI_API_KEY=secret"


class _FatalRuntimeAuditError(Exception):
    error_kind = "authentication_failed"
    raw_error_type = "AuthError"
    retryable = False
    summary = "auth failed"


def _runtime_audit_clock():
    counter = {"value": 0}

    def now() -> str:
        counter["value"] += 1
        return f"2026-06-25T00:00:{counter['value']:02d}+00:00"

    return now


def _seed_leader_worker_dispatcher_inputs(tmp_path: Path) -> dict[str, Path]:
    return _seed_leader_worker_dispatcher_inputs_with_provider(
        tmp_path,
        server_provider="fake",
        client_provider="fake",
    )


def _seed_leader_worker_dispatcher_inputs_with_provider(
    tmp_path: Path,
    *,
    server_provider,
    client_provider,
) -> dict[str, Path]:
    snapshot = tmp_path / ".codex/scheduler/state.json"
    event_log = tmp_path / ".codex/scheduler/events.jsonl"
    artifact_store = tmp_path / ".codex/orchestration/exchange-artifacts.json"
    dispatcher_state = tmp_path / ".codex/scheduler/leader-worker-dispatcher-state.json"
    dispatch_log = tmp_path / ".codex/scheduler/leader-worker-dispatcher-events.jsonl"
    delivery_state = tmp_path / ".codex/scheduler/leader-worker-delivery-state.json"
    delivery_log = tmp_path / ".codex/scheduler/leader-worker-delivery-events.jsonl"
    runtime_log = tmp_path / ".codex/runtime/invocations.jsonl"
    event_log.parent.mkdir(parents=True, exist_ok=True)
    event_log.write_text("", encoding="utf-8")
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-server": ScheduledTask(
                    task_id="task-server",
                    title="Server",
                    instruction="Implement server",
                    agent=AgentSpec(agent_id="agent:server", runtime_provider=server_provider),
                    state="ready",
                    context_scope=ContextScope(context_id="ctx-server", lane_id="lane:server"),
                ),
                "task-client": ScheduledTask(
                    task_id="task-client",
                    title="Client",
                    instruction="Implement client",
                    agent=AgentSpec(agent_id="agent:client", runtime_provider=client_provider),
                    state="waiting",
                    context_scope=ContextScope(context_id="ctx-client", lane_id="lane:client"),
                    blocked_reason="waiting for task-server",
                ),
            }
        ),
        snapshot,
    )
    JsonArtifactVersionStore(artifact_store).put(
        ExchangeArtifact(
            artifact_id="ex-server-report",
            version="v1",
            kind="message",
            intent="inform",
            producer="agent:server",
            audience=("agent:guide",),
            lifecycle_state="proposed",
            parts=(ExchangePayloadPart(part_type="text", text="server ready"),),
        )
    )
    return {
        "snapshot": snapshot,
        "event_log": event_log,
        "artifact_store": artifact_store,
        "dispatcher_state": dispatcher_state,
        "dispatch_log": dispatch_log,
        "delivery_state": delivery_state,
        "delivery_log": delivery_log,
        "runtime_log": runtime_log,
    }


def _seed_codex_delivery_supervisor_permission_project(tmp_path: Path) -> dict[str, Path]:
    snapshot = tmp_path / ".codex/scheduler/state.json"
    event_log = tmp_path / ".codex/scheduler/events.jsonl"
    artifact_store = tmp_path / ".codex/orchestration/exchange-artifacts.json"
    dispatcher_state = tmp_path / ".codex/scheduler/leader-worker-dispatcher-state.json"
    dispatch_log = tmp_path / ".codex/scheduler/leader-worker-dispatcher-events.jsonl"
    delivery_state = tmp_path / ".codex/scheduler/leader-worker-delivery-state.json"
    delivery_log = tmp_path / ".codex/scheduler/leader-worker-delivery-events.jsonl"
    runtime_log = tmp_path / ".codex/runtime/invocations.jsonl"
    event_log.parent.mkdir(parents=True, exist_ok=True)
    event_log.write_text("", encoding="utf-8")
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                "task-server": ScheduledTask(
                    task_id="task-server",
                    title="Server",
                    instruction="Implement server",
                    agent=AgentSpec(agent_id="agent:server", runtime_provider="codex"),
                    state="ready",
                    context_scope=ContextScope(
                        context_id="ctx-server",
                        lane_id="lane:server",
                    ),
                ),
                "task-client": ScheduledTask(
                    task_id="task-client",
                    title="Client",
                    instruction="Implement client after server is complete",
                    agent=AgentSpec(agent_id="agent:client", runtime_provider="codex"),
                    state="waiting",
                    context_scope=ContextScope(
                        context_id="ctx-client",
                        lane_id="lane:client",
                    ),
                    blocked_reason="waiting for task-server",
                ),
            },
            dependencies=(
                TaskDependency(
                    dependency_id="dep:client-after-server",
                    source_task_id="task-server",
                    target_task_id="task-client",
                    required_state="complete",
                ),
            ),
        ),
        snapshot,
    )
    JsonArtifactVersionStore(artifact_store).put(
        ExchangeArtifact(
            artifact_id="ex-server-report",
            version="v1",
            kind="message",
            intent="inform",
            producer="agent:server",
            audience=("agent:guide",),
            lifecycle_state="proposed",
            parts=(ExchangePayloadPart(part_type="text", text="server ready"),),
        )
    )
    return {
        "snapshot": snapshot,
        "event_log": event_log,
        "artifact_store": artifact_store,
        "dispatcher_state": dispatcher_state,
        "dispatch_log": dispatch_log,
        "delivery_state": delivery_state,
        "delivery_log": delivery_log,
        "runtime_log": runtime_log,
    }


def _seed_codex_delivery_supervisor_git_worktree_project(
    tmp_path: Path,
    *,
    source_repo: Path,
    provider: RuntimeProviderKind = "codex",
) -> dict[str, Path]:
    snapshot = tmp_path / ".codex/scheduler/state.json"
    event_log = tmp_path / ".codex/scheduler/events.jsonl"
    artifact_store = tmp_path / ".codex/orchestration/exchange-artifacts.json"
    dispatcher_state = tmp_path / ".codex/scheduler/leader-worker-dispatcher-state.json"
    dispatch_log = tmp_path / ".codex/scheduler/leader-worker-dispatcher-events.jsonl"
    delivery_state = tmp_path / ".codex/scheduler/leader-worker-delivery-state.json"
    delivery_log = tmp_path / ".codex/scheduler/leader-worker-delivery-events.jsonl"
    runtime_log = tmp_path / ".codex/runtime/invocations.jsonl"
    event_log.parent.mkdir(parents=True, exist_ok=True)
    event_log.write_text("", encoding="utf-8")
    server_task = ScheduledTask(
        task_id="task-server",
        title="Server",
        instruction="Edit src/app.py inside the sandbox.",
        agent=AgentSpec(agent_id="agent:server", runtime_provider=provider),
        state="ready",
        context_scope=ContextScope(
            context_id="ctx-server",
            lane_id="lane:server",
            required_refs=(
                ExchangeReference(ref_kind="file", ref_id="src/app.py", path="src/app.py"),
            ),
        ),
        edit_lease=EditScopeLease(
            lease_id="lease-server",
            task_id="task-server",
            allowed_artifacts=("src/app.py",),
            lease_mode="write",
        ),
        sandbox_profile=SandboxProfile(
            profile_id="worktree",
            profile_kind="git-worktree",
            mount_policy="lease-scoped",
        ),
        acceptance=("Edit only src/app.py.",),
        output_artifact_id=f"task-server:{provider}-result",
    )
    client_task = ScheduledTask(
        task_id="task-client",
        title="Client",
        instruction="Wait for server completion.",
        agent=AgentSpec(agent_id="agent:client", runtime_provider=provider),
        state="waiting",
        context_scope=ContextScope(context_id="ctx-client", lane_id="lane:client"),
        blocked_reason="waiting for task-server",
    )
    write_scheduler_state_snapshot(
        SchedulerState(
            tasks={
                server_task.task_id: server_task,
                client_task.task_id: client_task,
            },
            dependencies=(
                TaskDependency(
                    dependency_id="dep:client-after-server",
                    source_task_id="task-server",
                    target_task_id="task-client",
                    required_state="complete",
                ),
            ),
            edit_lease_lifecycle={
                "lease-server": EditLeaseLifecycleRecord(
                    lease_id="lease-server",
                    task_id="task-server",
                    state="acquired",
                    mode="write",
                    allowed_artifacts=("src/app.py",),
                    acquired_at="2026-06-27T10:00:00+00:00",
                ),
            },
        ),
        snapshot,
    )
    JsonArtifactVersionStore(artifact_store).put(
        ExchangeArtifact(
            artifact_id="ex-server-report",
            version="v1",
            kind="message",
            intent="inform",
            producer="agent:server",
            audience=("agent:guide",),
            lifecycle_state="proposed",
            parts=(
                ExchangePayloadPart(
                    part_type="text",
                    text=f"source repo: {source_repo}",
                ),
            ),
        )
    )
    return {
        "snapshot": snapshot,
        "event_log": event_log,
        "artifact_store": artifact_store,
        "dispatcher_state": dispatcher_state,
        "dispatch_log": dispatch_log,
        "delivery_state": delivery_state,
        "delivery_log": delivery_log,
        "runtime_log": runtime_log,
    }


def test_worker_trajectory_report_consumer_starts_missing_trajectory_from_append(
    tmp_path: Path,
) -> None:
    from tools.progress_graph import load_local_work_trajectory, trajectory_json_path

    report_path = tmp_path / ".codex" / "agent-output" / "report-worker.json"
    _write_worker_trajectory_report(report_path, suggested_action="append")

    result = consume_worker_trajectory_report(
        WorkerTrajectoryReportConsumerRequest(
            project_root=tmp_path,
            report_path=report_path,
            caller_role="leader",
            actor="agent:guide",
            title="Server lane complete",
            event_kind="validation",
            guide_context="test-guide",
        )
    )

    assert isinstance(result, WorkerTrajectoryReportConsumerResult)
    assert result.ok is True
    assert result.status == "consumed"
    assert result.consumed_action == "start"
    assert result.trajectory_created is True
    assert result.active_event_ids == ("event:001",)
    assert trajectory_json_path(tmp_path).exists()
    payload = result.to_json_dict()
    assert payload["authority_split"]["local_work_trajectory_mutated"] is True
    trajectory = load_local_work_trajectory(tmp_path)
    event = trajectory.events["event:001"]
    assert event.title == "Server lane complete"
    assert event.kind == "validation"
    assert event.metadata["worker_report_id"] == "report-worker-trajectory"
    assert event.metadata["worker_task_id"] == "task/server"
    assert event.metadata["worker_evidence_refs"] == ".codex/agent-output/report-worker.json"


def test_worker_trajectory_report_consumer_rejects_worker_role_before_mutation(
    tmp_path: Path,
) -> None:
    from tools.progress_graph import trajectory_json_path

    report_path = tmp_path / ".codex" / "agent-output" / "report-worker.json"
    _write_worker_trajectory_report(report_path, suggested_action="append")

    result = consume_worker_trajectory_report(
        WorkerTrajectoryReportConsumerRequest(
            project_root=tmp_path,
            report_path=report_path,
            caller_role="worker",
        )
    )

    assert result.ok is False
    assert result.status == "denied"
    assert "docs/worker-trajectory-update-reporting.md" in result.errors[0]
    assert not trajectory_json_path(tmp_path).exists()


def test_worker_trajectory_report_consumer_fails_invalid_report_without_mutation(
    tmp_path: Path,
) -> None:
    from tools.progress_graph import trajectory_json_path

    report_path = tmp_path / ".codex" / "agent-output" / "report-invalid.json"
    _write_worker_trajectory_report(report_path, suggested_action="append")
    payload = json.loads(report_path.read_text(encoding="utf-8"))
    payload["trajectory_update"]["localTrajectoryPayload"] = {"action": "advance"}
    report_path.write_text(json.dumps(payload), encoding="utf-8")

    result = consume_worker_trajectory_report(
        WorkerTrajectoryReportConsumerRequest(
            project_root=tmp_path,
            report_path=report_path,
            caller_role="leader",
        )
    )

    assert result.ok is False
    assert result.status == "validation_failed"
    assert any("localTrajectoryPayload" in error for error in result.errors)
    assert not trajectory_json_path(tmp_path).exists()


def test_worker_trajectory_report_consumer_advances_existing_trajectory(
    tmp_path: Path,
) -> None:
    from tools.progress_graph import load_local_work_trajectory, start_single_line_trajectory

    start_single_line_trajectory(
        tmp_path,
        first_event_title="Implement server",
        lane_label="server",
        lane_id="lane:server",
    )
    report_path = tmp_path / ".codex" / "agent-output" / "report-worker.json"
    _write_worker_trajectory_report(report_path, suggested_action="advance")

    result = consume_worker_trajectory_report(
        WorkerTrajectoryReportConsumerRequest(
            project_root=tmp_path,
            report_path=report_path,
            caller_role="supervisor",
            actor="agent:leader",
        )
    )

    assert result.ok is True
    assert result.status == "consumed"
    assert result.consumed_action == "advance"
    trajectory = load_local_work_trajectory(tmp_path)
    assert trajectory.events["event:001"].status == "completed"


def _write_worker_trajectory_report(
    report_path: Path,
    *,
    suggested_action: str,
) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "report_id": "report-worker-trajectory",
                "contract_id": "contract-worker-trajectory",
                "status": "completed",
                "changed_artifacts": ["server.js"],
                "verification_results": ["npm test passed"],
                "trajectory_update": {
                    "lane_id": "lane:server",
                    "task_id": "task/server",
                    "event_status": "completed",
                    "summary": "Server lane finished and validated.",
                    "suggested_action": suggested_action,
                    "evidence_refs": [".codex/agent-output/report-worker.json"],
                    "leader_notes": ["Review validation before advancing."],
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


class _JsonHttpResponse:
    def __init__(self, payload: object, *, status: int = 200) -> None:
        self.status = status
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def _request_json_payload(request) -> dict[str, object]:
    raw = getattr(request, "data", None)
    if not raw:
        return {}
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8")
    payload = json.loads(raw)
    return payload if isinstance(payload, dict) else {"value": payload}


def _opencode_server_api_request() -> OpenCodeCliRequest:
    return OpenCodeCliRequest(
        agent=AgentSpec(
            agent_id="agent:opencode-api",
            runtime_provider="opencode",
            model="test-model",
        ),
        task=TaskSpec(
            task_id="task-opencode-api",
            title="OpenCode API task",
            instruction="Use the direct server API.",
            acceptance=("Return a compact result.",),
        ),
        session=SessionHandle(
            session_id="runtime-session",
            provider="opencode",
            agent_id="agent:opencode-api",
        ),
        instruction="Use the direct server API.",
        acceptance=("Return a compact result.",),
    )
