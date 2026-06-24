"""Dogfood closure from durable storage binding evidence to consumer task."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

from src.runtime.orchestration import (
    AgentSpec,
    ContextScope,
    ExchangeArtifact,
    ExchangeReference,
    JsonArtifactVersionStore,
    SchedulerState,
    SchedulerTaskBatchSubmission,
    SchedulerTaskSubmission,
    SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
    SupervisorAgentStorageBindingRequest,
    build_supervisor_agent_storage_binding,
    build_supervisor_storage_binding_evidence,
    default_exchange_artifact_store_path,
    default_supervisor_storage_binding_evidence_path,
    publish_supervisor_storage_binding_artifact_from_evidence,
    read_supervisor_storage_binding_evidence_summary,
    scheduler_task_batch_submission_to_artifact,
    write_supervisor_storage_binding_evidence,
)

from .scheduler_operator_workflow import (
    DEFAULT_SCHEDULER_OPERATOR_EVENT_LOG_RELATIVE_PATH,
    DEFAULT_SCHEDULER_OPERATOR_SNAPSHOT_RELATIVE_PATH,
    SchedulerOperatorWorkflowRequest,
    run_scheduler_operator_workflow,
)


DEFAULT_EVIDENCE_PUBLISH_CONSUMER_ARTIFACT_ID = (
    "fixture:evidence-publish-binding-consumer"
)
DEFAULT_EVIDENCE_PUBLISH_CONSUMER_VERSION = "v1"
DEFAULT_EVIDENCE_PUBLISH_BINDING_ARTIFACT_ID = (
    "fixture:evidence-publish-supervisor-storage-binding"
)
DEFAULT_EVIDENCE_PUBLISH_BINDING_ARTIFACT_VERSION = "v1"
DEFAULT_EVIDENCE_PUBLISH_BINDING_EVIDENCE_ID = "evidence-publish-storage-binding"
DEFAULT_EVIDENCE_PUBLISH_LOOP_EVIDENCE_ID = "evidence-publish-consumer-loop"


@dataclass(frozen=True, slots=True)
class EvidencePublishToConsumerClosureRequest:
    """Request for the durable evidence publish to scheduler consumer closure."""

    project_root: str | Path
    artifact_store_path: str | Path | None = None
    admission_ledger_path: str | Path | None = None
    snapshot_path: str | Path | None = None
    event_log_path: str | Path | None = None
    merge_gate_event_log_path: str | Path | None = None
    projection_output_path: str | Path | None = None
    binding_evidence_id: str = DEFAULT_EVIDENCE_PUBLISH_BINDING_EVIDENCE_ID
    binding_evidence_path: str | Path | None = None
    binding_artifact_id: str = DEFAULT_EVIDENCE_PUBLISH_BINDING_ARTIFACT_ID
    binding_artifact_version: str = DEFAULT_EVIDENCE_PUBLISH_BINDING_ARTIFACT_VERSION
    consumer_artifact_id: str = DEFAULT_EVIDENCE_PUBLISH_CONSUMER_ARTIFACT_ID
    consumer_version: str = DEFAULT_EVIDENCE_PUBLISH_CONSUMER_VERSION
    loop_evidence_id: str = DEFAULT_EVIDENCE_PUBLISH_LOOP_EVIDENCE_ID
    loop_evidence_path: str | Path | None = None
    runtime_provider: str = "fake"
    max_ticks: int = 3
    max_runs_per_tick: int | None = 1
    max_runtime_failures: int | None = 1
    replace_existing: bool = False
    mark_consumed_on_success: bool = True
    actor: str = "evidence-publish-consumer-closure"
    timestamp: str = ""
    created_at: str = ""
    guide_context: str = ""
    source_graph_id: str = ""
    source_node_id: str = ""


@dataclass(frozen=True, slots=True)
class EvidencePublishToConsumerClosureStep:
    """One step in the publish-to-consumer closure."""

    name: str
    status: str
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
class EvidencePublishToConsumerClosureResult:
    """Result of durable evidence publish to consumer dogfood closure."""

    request: EvidencePublishToConsumerClosureRequest
    project_root: Path
    artifact_store_path: Path
    binding_evidence_path: Path
    binding_artifact_id: str
    binding_artifact_version: str
    consumer_artifact_id: str
    consumer_version: str
    steps: tuple[EvidencePublishToConsumerClosureStep, ...]
    evidence_write: Mapping[str, object] = field(default_factory=dict)
    publish_result: Mapping[str, object] = field(default_factory=dict)
    consumer_seed_result: Mapping[str, object] = field(default_factory=dict)
    workflow_result: Mapping[str, object] = field(default_factory=dict)
    final_candidate_summary: Mapping[str, object] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not any(step.status == "failed" for step in self.steps)

    @property
    def authority_split(self) -> dict[str, object]:
        workflow_authority = _mapping(self.workflow_result.get("authority_split"))
        return {
            "workflow_surface": "evidence-publish-to-consumer-closure",
            "binding_evidence_written": _step_mutated(self.steps, "writeBindingEvidence"),
            "binding_artifact_published": _step_mutated(self.steps, "publishBindingArtifact"),
            "consumer_submission_seeded": _step_mutated(self.steps, "seedConsumerSubmission"),
            "exchange_store_mutated": _step_mutated(self.steps, "publishBindingArtifact")
            or _step_mutated(self.steps, "seedConsumerSubmission")
            or bool(workflow_authority.get("exchange_store_mutated")),
            "admission_ledger_mutated": bool(
                workflow_authority.get("admission_ledger_mutated")
            ),
            "scheduler_state_mutated": bool(workflow_authority.get("scheduler_state_mutated")),
            "provider_executed": bool(workflow_authority.get("provider_executed")),
            "loop_evidence_written": bool(workflow_authority.get("evidence_written")),
            "scheduler_projection_refreshed": bool(
                workflow_authority.get("scheduler_projection_refreshed")
            ),
            "host_evidence_read": bool(workflow_authority.get("host_evidence_read")),
            "starts_os_service": False,
            "starts_background_process": False,
            "uses_timers_or_watchers": False,
            "cleanup_executed": False,
            "agent_home_registration_persisted": False,
            "agent_home_directory_created": False,
            "scratch_directories_created": False,
            "scratch_manifest_written": False,
            "raw_binding_payload_embedded_in_exchange": False,
            "local_work_trajectory_mutated": False,
        }

    def to_json_dict(self) -> dict[str, object]:
        workflow = dict(self.workflow_result)
        admission_result = _mapping(workflow.get("admission_result"))
        binding_summary = _mapping(admission_result.get("binding_reference_summary"))
        consumption_state = _mapping(admission_result.get("consumption_state"))
        loop_result = _mapping(workflow.get("loop_result"))
        projection_result = _mapping(workflow.get("projection_result"))
        host_evidence = _mapping(workflow.get("host_evidence_presentation"))
        final_summary = dict(self.final_candidate_summary)
        final_admission_state = _mapping(final_summary.get("admission_state"))
        return {
            "ok": self.ok,
            "workflow_surface": "evidence-publish-to-consumer-closure",
            "project_root": str(self.project_root),
            "paths": {
                "artifact_store_path": str(self.artifact_store_path),
                "binding_evidence_path": str(self.binding_evidence_path),
            },
            "request": {
                "binding_evidence_id": self.request.binding_evidence_id,
                "binding_artifact_id": self.binding_artifact_id,
                "binding_artifact_version": self.binding_artifact_version,
                "consumer_artifact_id": self.consumer_artifact_id,
                "consumer_version": self.consumer_version,
                "runtime_provider": self.request.runtime_provider,
                "mark_consumed_on_success": self.request.mark_consumed_on_success,
                "replace_existing": self.request.replace_existing,
                "actor": self.request.actor,
                "loop_evidence_id": self.request.loop_evidence_id,
            },
            "steps": [step.to_json_dict() for step in self.steps],
            "evidence_write": dict(self.evidence_write),
            "publish_result": dict(self.publish_result),
            "consumer_seed_result": dict(self.consumer_seed_result),
            "workflow_result": workflow,
            "closure_summary": {
                "binding_evidence_id": self.request.binding_evidence_id,
                "binding_evidence_path": str(self.binding_evidence_path),
                "binding_artifact_id": self.binding_artifact_id,
                "binding_artifact_version": self.binding_artifact_version,
                "consumer_artifact_id": self.consumer_artifact_id,
                "consumer_version": self.consumer_version,
                "consumer_references_published_artifact": _consumer_refs_published_artifact(
                    self.consumer_seed_result,
                    self.binding_artifact_id,
                    self.binding_artifact_version,
                ),
                "lifecycle_state": str(final_summary.get("lifecycle_state", "")),
                "admission_status": str(final_admission_state.get("status", "")),
                "binding_summary_ok": binding_summary.get("ok", False),
                "binding_summary_enabled": binding_summary.get("enabled", False),
                "consumed": bool(consumption_state.get("consumed", False)),
                "loop_evidence_id": loop_result.get("evidence_id", ""),
                "loop_evidence_path": loop_result.get("evidence_path", ""),
                "loop_stop_reason": loop_result.get("stop_reason", ""),
                "scheduler_projection_path": projection_result.get(
                    "scheduler_projection_path",
                    "",
                ),
                "scheduler_projection_event_count": projection_result.get(
                    "event_count",
                    0,
                ),
                "scheduler_projection_lane_count": projection_result.get("lane_count", 0),
                "scheduler_projection_relation_count": projection_result.get(
                    "relation_count",
                    0,
                ),
                "host_evidence_status": host_evidence.get("status", ""),
                "host_evidence_card_count": host_evidence.get("card_count", 0),
            },
            "final_candidate_summary": final_summary,
            "authority_split": self.authority_split,
        }


def run_evidence_publish_to_consumer_closure(
    request: EvidencePublishToConsumerClosureRequest,
) -> EvidencePublishToConsumerClosureResult:
    """Run durable storage binding evidence through a downstream consumer closure."""

    paths = _ResolvedEvidencePublishToConsumerPaths.from_request(request)
    steps: list[EvidencePublishToConsumerClosureStep] = []
    evidence_write: Mapping[str, object] = {}
    publish_result: Mapping[str, object] = {}
    consumer_seed_result: Mapping[str, object] = {}
    workflow_result: Mapping[str, object] = {}
    final_candidate_summary: Mapping[str, object] = {}

    if (request.runtime_provider or "fake").strip().lower() != "fake":
        steps.append(
            EvidencePublishToConsumerClosureStep(
                name="preflightRuntime",
                status="failed",
                error=(
                    "evidence publish to consumer closure currently supports "
                    "runtimeProvider='fake' only; real providers require a "
                    "separate live-runtime planning gate."
                ),
            )
        )
        return EvidencePublishToConsumerClosureResult(
            request=request,
            project_root=paths.project_root,
            artifact_store_path=paths.artifact_store_path,
            binding_evidence_path=paths.binding_evidence_path,
            binding_artifact_id=request.binding_artifact_id,
            binding_artifact_version=request.binding_artifact_version,
            consumer_artifact_id=request.consumer_artifact_id,
            consumer_version=request.consumer_version,
            steps=tuple(steps),
        )

    try:
        evidence_write = _write_binding_evidence(request, paths)
        steps.append(
            EvidencePublishToConsumerClosureStep(
                name="writeBindingEvidence",
                status="completed",
                mutated=True,
                result=evidence_write,
            )
        )
    except Exception as exc:
        steps.append(
            EvidencePublishToConsumerClosureStep(
                name="writeBindingEvidence",
                status="failed",
                error=str(exc),
            )
        )

    if _has_failed(steps):
        steps.append(_skipped("publishBindingArtifact", "binding evidence write failed"))
    else:
        try:
            published = publish_supervisor_storage_binding_artifact_from_evidence(
                evidence_path=paths.binding_evidence_path,
                artifact_store_path=paths.artifact_store_path,
                artifact_id=request.binding_artifact_id,
                version=request.binding_artifact_version,
                producer=request.actor,
                created_at=request.created_at or request.timestamp,
                replace_existing=request.replace_existing,
            )
            publish_result = published.to_json_dict()
            steps.append(
                EvidencePublishToConsumerClosureStep(
                    name="publishBindingArtifact",
                    status="completed",
                    mutated=True,
                    result=publish_result,
                )
            )
        except Exception as exc:
            steps.append(
                EvidencePublishToConsumerClosureStep(
                    name="publishBindingArtifact",
                    status="failed",
                    error=str(exc),
                )
            )

    if _has_failed(steps):
        steps.append(_skipped("seedConsumerSubmission", "binding artifact publish failed"))
    else:
        try:
            consumer_seed_result = _seed_consumer_submission(request, paths)
            steps.append(
                EvidencePublishToConsumerClosureStep(
                    name="seedConsumerSubmission",
                    status="completed",
                    mutated=True,
                    result=consumer_seed_result,
                )
            )
        except Exception as exc:
            steps.append(
                EvidencePublishToConsumerClosureStep(
                    name="seedConsumerSubmission",
                    status="failed",
                    error=str(exc),
                )
            )

    if _has_failed(steps):
        steps.append(_skipped("operatorWorkflow", "consumer submission seed failed"))
    else:
        workflow = run_scheduler_operator_workflow(
            SchedulerOperatorWorkflowRequest(
                project_root=paths.project_root,
                artifact_id=request.consumer_artifact_id,
                version=request.consumer_version,
                admit=True,
                run_loop=True,
                refresh_projection=True,
                inspect_binding_refs=True,
                artifact_store_path=paths.artifact_store_path,
                admission_ledger_path=request.admission_ledger_path,
                snapshot_path=request.snapshot_path
                or DEFAULT_SCHEDULER_OPERATOR_SNAPSHOT_RELATIVE_PATH,
                event_log_path=request.event_log_path
                or DEFAULT_SCHEDULER_OPERATOR_EVENT_LOG_RELATIVE_PATH,
                merge_gate_event_log_path=request.merge_gate_event_log_path,
                projection_output_path=request.projection_output_path,
                evidence_id=request.loop_evidence_id,
                evidence_path=request.loop_evidence_path,
                runtime_provider="fake",
                max_ticks=request.max_ticks,
                max_runs_per_tick=request.max_runs_per_tick,
                max_runtime_failures=request.max_runtime_failures,
                allow_duplicate_admission=False,
                replace_existing=False,
                mark_consumed_on_success=request.mark_consumed_on_success,
                actor=request.actor,
                timestamp=request.timestamp,
                guide_context=request.guide_context,
                source_graph_id=request.source_graph_id,
                source_node_id=request.source_node_id,
            )
        )
        workflow_result = workflow.to_json_dict()
        steps.append(
            EvidencePublishToConsumerClosureStep(
                name="operatorWorkflow",
                status="completed" if workflow.ok else "failed",
                mutated=bool(
                    _mapping(workflow_result.get("authority_split")).get(
                        "scheduler_state_mutated"
                    )
                ),
                error="" if workflow.ok else _workflow_error(workflow_result),
                result=workflow_result,
            )
        )

    if _has_failed(steps):
        steps.append(_skipped("readClosureSummary", "previous step failed"))
    else:
        try:
            from src.runtime.orchestration import inspect_exchange_artifact_store

            bundle = inspect_exchange_artifact_store(
                paths.artifact_store_path,
                admission_ledger_path=paths.admission_ledger_path,
            ).to_json_dict()
            final_candidate_summary = _find_summary(
                bundle,
                request.consumer_artifact_id,
                request.consumer_version,
            )
            steps.append(
                EvidencePublishToConsumerClosureStep(
                    name="readClosureSummary",
                    status="completed",
                    result=final_candidate_summary,
                )
            )
        except Exception as exc:
            steps.append(
                EvidencePublishToConsumerClosureStep(
                    name="readClosureSummary",
                    status="failed",
                    error=str(exc),
                )
            )

    return EvidencePublishToConsumerClosureResult(
        request=request,
        project_root=paths.project_root,
        artifact_store_path=paths.artifact_store_path,
        binding_evidence_path=paths.binding_evidence_path,
        binding_artifact_id=request.binding_artifact_id,
        binding_artifact_version=request.binding_artifact_version,
        consumer_artifact_id=request.consumer_artifact_id,
        consumer_version=request.consumer_version,
        steps=tuple(steps),
        evidence_write=evidence_write,
        publish_result=publish_result,
        consumer_seed_result=consumer_seed_result,
        workflow_result=workflow_result,
        final_candidate_summary=final_candidate_summary,
    )


@dataclass(frozen=True, slots=True)
class _ResolvedEvidencePublishToConsumerPaths:
    project_root: Path
    artifact_store_path: Path
    admission_ledger_path: Path
    binding_evidence_path: Path

    @classmethod
    def from_request(
        cls,
        request: EvidencePublishToConsumerClosureRequest,
    ) -> "_ResolvedEvidencePublishToConsumerPaths":
        project_root = Path(request.project_root).resolve()
        artifact_store_path = (
            _resolve(project_root, request.artifact_store_path)
            if request.artifact_store_path is not None
            else default_exchange_artifact_store_path(project_root)
        )
        from src.runtime.orchestration import default_exchange_artifact_admission_ledger_path

        admission_ledger_path = (
            _resolve(project_root, request.admission_ledger_path)
            if request.admission_ledger_path is not None
            else default_exchange_artifact_admission_ledger_path(project_root)
        )
        binding_evidence_path = (
            _resolve(project_root, request.binding_evidence_path)
            if request.binding_evidence_path is not None
            else default_supervisor_storage_binding_evidence_path(
                project_root,
                request.binding_evidence_id,
            )
        )
        return cls(
            project_root=project_root,
            artifact_store_path=artifact_store_path,
            admission_ledger_path=admission_ledger_path,
            binding_evidence_path=binding_evidence_path,
        )


def _write_binding_evidence(
    request: EvidencePublishToConsumerClosureRequest,
    paths: _ResolvedEvidencePublishToConsumerPaths,
) -> Mapping[str, object]:
    binding = build_supervisor_agent_storage_binding(
        SupervisorAgentStorageBindingRequest(
            supervisor_id="supervisor:evidence-publish",
            session_id="session:evidence-publish",
            run_id="run:evidence-publish",
            host_id="host:evidence-publish-closure",
            requested_by=request.actor,
            agent_id="agent:evidence-publish-consumer",
            context_session_id="context-session:evidence-publish-consumer",
            created_at=request.created_at or request.timestamp,
            purpose="Dogfood durable evidence publish to scheduler consumer closure.",
            capability_domain="scheduler-storage-binding-publish",
        ),
        SchedulerState(),
        source_snapshot_path=(
            paths.project_root / DEFAULT_SCHEDULER_OPERATOR_SNAPSHOT_RELATIVE_PATH
        ),
    )
    written = write_supervisor_storage_binding_evidence(
        build_supervisor_storage_binding_evidence(
            binding,
            evidence_id=request.binding_evidence_id,
            timestamp=request.created_at or request.timestamp,
            metadata={
                "surface": "evidence-publish-to-consumer-closure",
                "raw_evidence_json_written": True,
            },
        ),
        paths.binding_evidence_path,
    )
    summary = read_supervisor_storage_binding_evidence_summary(written.evidence_path)
    payload = summary.to_json_dict()
    payload["evidence_written"] = True
    return payload


def _seed_consumer_submission(
    request: EvidencePublishToConsumerClosureRequest,
    paths: _ResolvedEvidencePublishToConsumerPaths,
) -> Mapping[str, object]:
    batch = _build_consumer_batch(
        binding_artifact_id=request.binding_artifact_id,
        binding_artifact_version=request.binding_artifact_version,
    )
    artifact = scheduler_task_batch_submission_to_artifact(
        batch,
        artifact_id=request.consumer_artifact_id,
        producer=request.actor,
        created_at=request.created_at or request.timestamp,
        version=request.consumer_version,
    )
    _store_artifact(
        paths.artifact_store_path,
        artifact,
        replace_existing=request.replace_existing,
    )
    return {
        "ok": True,
        "artifact_store_path": str(paths.artifact_store_path),
        "artifact_id": artifact.artifact_id,
        "version": artifact.version,
        "product_type": "scheduler_task_batch_submission",
        "batch_id": batch.batch_id,
        "task_ids": [task.task_id for task in batch.tasks],
        "dependency_ids": [
            dependency.dependency_id
            for task in batch.tasks
            for dependency in task.dependencies
        ],
        "lane_ids": [
            lane_id
            for lane_id in dict.fromkeys(
                task.context_scope.lane_id
                for task in batch.tasks
                if task.context_scope.lane_id
            )
        ],
        "binding_artifact_ids": [request.binding_artifact_id],
        "binding_artifact_versions": [request.binding_artifact_version],
        "candidate_created": True,
        "authority_split": {
            "exchange_store_mutated": True,
            "scheduler_state_mutated": False,
            "admission_ledger_mutated": False,
            "provider_executed": False,
            "scheduler_projection_refreshed": False,
            "host_evidence_written": False,
            "local_work_trajectory_mutated": False,
        },
    }


def _build_consumer_batch(
    *,
    binding_artifact_id: str,
    binding_artifact_version: str,
) -> SchedulerTaskBatchSubmission:
    consumer = SchedulerTaskSubmission(
        task_id="dogfood:evidence-publish-binding-consumer",
        title="Consume published supervisor storage binding artifact",
        instruction=(
            "Use the fake runtime only after the operator has published durable "
            "supervisor storage binding evidence and inspected this exact binding "
            "artifact reference."
        ),
        agent=AgentSpec(
            agent_id="agent:evidence-publish-binding-consumer",
            runtime_provider="fake",
            display_name="Evidence Publish Binding Consumer Agent",
            tools=("read",),
            max_turns=1,
        ),
        context_scope=ContextScope(
            context_id="context:evidence-publish-binding-consumer",
            lane_id="lane:evidence-publish-binding-consumer",
        ),
        input_artifact_refs=(
            ExchangeReference(
                ref_kind=SUPERVISOR_STORAGE_BINDING_ARTIFACT_REF_KIND,
                ref_id=binding_artifact_id,
                version=binding_artifact_version,
                label="Published supervisor storage binding artifact",
            ),
        ),
        acceptance=(
            "operator workflow inspectBindingRefs validates the published binding artifact ref",
            "fake runtime completes dogfood:evidence-publish-binding-consumer after admission",
        ),
        output_artifact_id="dogfood:evidence-publish-binding-consumer:result",
    )
    return SchedulerTaskBatchSubmission(
        batch_id="batch:evidence-publish-binding-consumer",
        title="Evidence publish binding consumer dogfood fixture",
        summary=(
            "One fake-runtime task that consumes a supervisor storage binding "
            "artifact produced from durable evidence through the publish surface."
        ),
        tasks=(consumer,),
    )


def _store_artifact(
    artifact_store_path: Path,
    artifact: ExchangeArtifact,
    *,
    replace_existing: bool,
) -> None:
    JsonArtifactVersionStore(artifact_store_path).put(
        artifact,
        replace_existing=replace_existing,
    )


def _find_summary(
    bundle: Mapping[str, object],
    artifact_id: str,
    version: str,
) -> Mapping[str, object]:
    for summary in bundle.get("summaries", ()):
        if not isinstance(summary, Mapping):
            continue
        if summary.get("artifact_id") == artifact_id and summary.get("version") == version:
            return summary
    raise ValueError(f"exchange artifact summary not found: {artifact_id}@{version}")


def _consumer_refs_published_artifact(
    consumer_seed_result: Mapping[str, object],
    binding_artifact_id: str,
    binding_artifact_version: str,
) -> bool:
    return (
        consumer_seed_result.get("binding_artifact_ids") == [binding_artifact_id]
        and consumer_seed_result.get("binding_artifact_versions")
        == [binding_artifact_version]
    )


def _workflow_error(workflow: Mapping[str, object]) -> str:
    for step in workflow.get("steps", ()):
        if isinstance(step, Mapping) and step.get("status") == "failed":
            error = step.get("error")
            return str(error) if error else "operator workflow failed"
    return "operator workflow failed"


def _resolve(project_root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return project_root / path


def _mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def _skipped(name: str, reason: str) -> EvidencePublishToConsumerClosureStep:
    return EvidencePublishToConsumerClosureStep(
        name=name,
        status="skipped",
        error=reason,
    )


def _has_failed(steps: list[EvidencePublishToConsumerClosureStep]) -> bool:
    return any(step.status == "failed" for step in steps)


def _step_mutated(
    steps: tuple[EvidencePublishToConsumerClosureStep, ...],
    name: str,
) -> bool:
    return any(step.name == name and step.mutated for step in steps)
