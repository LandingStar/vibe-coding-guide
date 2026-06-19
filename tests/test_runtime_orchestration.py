"""Targeted tests for orchestration runtime models."""

from __future__ import annotations

import asyncio
import json

import pytest

from src.runtime.orchestration import (
    BridgeGroupItem,
    BridgeWorkItem,
    CoordinationEvent,
    AgentSpec,
    AgentHomeRegistration,
    AgentScratchSpace,
    ArtifactDelta,
    CleanupReceipt,
    ContextScope,
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
    JsonlSchedulerEventLog,
    JsonlSchedulerMergeGateEventLog,
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
    RuntimeHostInvocation,
    RuntimeProviderPermissionGrant,
    RuntimeRegistryWiringConfig,
    RuntimeRegistryWiringResult,
    RuntimeRunResult,
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
    SchedulerLoopEvidence,
    SchedulerLoopEvidenceSummary,
    admit_exchange_artifact_version_to_scheduler,
    admit_exchange_artifact_version_with_ledger,
    agent_home_registration_to_artifact,
    cleanup_receipt_to_artifact,
    build_orchestration_preflight_bundle,
    build_host_scheduler_run_evidence,
    build_runtime_registry_from_config,
    build_scheduler_loop_evidence,
    drain_preflighted_ready_tasks,
    drain_ready_tasks,
    evaluate_stop_condition,
    evaluate_task_admission,
    exchange_artifact_from_json_dict,
    exchange_artifact_to_json_dict,
    inspect_exchange_artifact_admission_ledger,
    inspect_exchange_artifact_store,
    has_scheduler_readable_relation,
    mark_ready_tasks,
    part_types,
    qoder_runtime_capabilities,
    qoder_query_result_from_response,
    project_group_item_delivery_signal,
    project_group_item_surface,
    recover_scheduler_state,
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
    run_scheduler_daemon_tick,
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
    validate_exchange_artifact,
    summarize_scheduler_queue,
    wake_dependent_tasks,
    write_compacted_scheduler_snapshot,
    write_host_scheduler_run_evidence,
    read_scheduler_state_snapshot,
    read_host_scheduler_run_evidence_summaries,
    read_host_scheduler_run_evidence_summary,
    read_scheduler_loop_evidence_summary,
    write_scheduler_state_snapshot,
    write_scheduler_loop_evidence,
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
    assert updated.tasks["task-b"].state == "blocked"


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

    bundle = build_orchestration_preflight_bundle(
        task,
        sandbox_registry=registry,
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

    with pytest.raises(ValueError, match="references unknown task"):
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
