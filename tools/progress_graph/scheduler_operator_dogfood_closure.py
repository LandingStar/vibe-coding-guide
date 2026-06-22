"""Deterministic scheduler operator dogfood execution closure."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Mapping

from src.runtime.orchestration import (
    DEFAULT_SCHEDULER_OPERATOR_BINDING_CONSUMER_DOGFOOD_ARTIFACT_ID,
    DEFAULT_SCHEDULER_OPERATOR_BINDING_CONSUMER_DOGFOOD_VERSION,
    DEFAULT_SCHEDULER_OPERATOR_DOGFOOD_ARTIFACT_ID,
    DEFAULT_SCHEDULER_OPERATOR_DOGFOOD_VERSION,
    DEFAULT_SCHEDULER_OPERATOR_MULTILANE_DOGFOOD_ARTIFACT_ID,
    DEFAULT_SCHEDULER_OPERATOR_MULTILANE_DOGFOOD_VERSION,
    default_exchange_artifact_admission_ledger_path,
    inspect_exchange_artifact_store,
    seed_scheduler_operator_binding_consumer_dogfood_fixture,
    seed_scheduler_operator_dogfood_fixture,
    seed_scheduler_operator_multilane_dogfood_fixture,
)

from .scheduler_operator_workflow import (
    DEFAULT_SCHEDULER_OPERATOR_EVIDENCE_ID,
    DEFAULT_SCHEDULER_OPERATOR_EVENT_LOG_RELATIVE_PATH,
    DEFAULT_SCHEDULER_OPERATOR_SNAPSHOT_RELATIVE_PATH,
    SchedulerOperatorWorkflowRequest,
    run_scheduler_operator_workflow,
)


OperatorDogfoodClosureFixture = Literal["binding-consumer", "simple", "multilane"]
OperatorDogfoodClosureStepStatus = Literal["completed", "skipped", "failed"]

DEFAULT_OPERATOR_DOGFOOD_CLOSURE_EVIDENCE_ID = "operator-dogfood-closure-loop"


@dataclass(frozen=True, slots=True)
class SchedulerOperatorDogfoodClosureRequest:
    """Request for a bounded fake-runtime operator dogfood closure."""

    project_root: str | Path
    fixture: OperatorDogfoodClosureFixture = "binding-consumer"
    artifact_id: str = ""
    version: str = ""
    artifact_store_path: str | Path | None = None
    admission_ledger_path: str | Path | None = None
    snapshot_path: str | Path | None = None
    event_log_path: str | Path | None = None
    merge_gate_event_log_path: str | Path | None = None
    projection_output_path: str | Path | None = None
    evidence_id: str = DEFAULT_OPERATOR_DOGFOOD_CLOSURE_EVIDENCE_ID
    evidence_path: str | Path | None = None
    runtime_provider: str = "fake"
    max_ticks: int = 3
    max_runs_per_tick: int | None = 1
    max_runtime_failures: int | None = 1
    replace_existing: bool = False
    inspect_binding_refs: bool = True
    mark_consumed_on_success: bool = True
    actor: str = "operator-dogfood-closure"
    timestamp: str = ""
    created_at: str = ""
    guide_context: str = ""
    source_graph_id: str = ""
    source_node_id: str = ""


@dataclass(frozen=True, slots=True)
class SchedulerOperatorDogfoodClosureStep:
    """One ordered closure step."""

    name: str
    status: OperatorDogfoodClosureStepStatus
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
class SchedulerOperatorDogfoodClosureResult:
    """Result of the deterministic operator dogfood closure."""

    request: SchedulerOperatorDogfoodClosureRequest
    project_root: Path
    artifact_id: str
    version: str
    steps: tuple[SchedulerOperatorDogfoodClosureStep, ...]
    fixture_result: Mapping[str, object] = field(default_factory=dict)
    workflow_result: Mapping[str, object] = field(default_factory=dict)
    final_candidate_summary: Mapping[str, object] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not any(step.status == "failed" for step in self.steps)

    @property
    def authority_split(self) -> dict[str, object]:
        fixture_authority = _mapping(self.fixture_result.get("authority_split"))
        workflow_authority = _mapping(self.workflow_result.get("authority_split"))
        return {
            "workflow_surface": "scheduler-operator-dogfood-closure",
            "fixture_seeded": _step_mutated(self.steps, "seedFixture"),
            "exchange_store_mutated": bool(fixture_authority.get("exchange_store_mutated"))
            or bool(workflow_authority.get("exchange_store_mutated")),
            "admission_ledger_mutated": bool(
                workflow_authority.get("admission_ledger_mutated")
            ),
            "scheduler_state_mutated": bool(workflow_authority.get("scheduler_state_mutated")),
            "provider_executed": bool(workflow_authority.get("provider_executed")),
            "evidence_written": bool(workflow_authority.get("evidence_written")),
            "scheduler_projection_refreshed": bool(
                workflow_authority.get("scheduler_projection_refreshed")
            ),
            "host_evidence_read": bool(workflow_authority.get("host_evidence_read")),
            "starts_os_service": False,
            "starts_background_process": False,
            "uses_timers_or_watchers": False,
            "cleanup_executed": False,
            "agent_home_directory_created": False,
            "scratch_directories_created": False,
            "local_work_trajectory_mutated": False,
        }

    def to_json_dict(self) -> dict[str, object]:
        workflow = dict(self.workflow_result)
        loop_result = _mapping(workflow.get("loop_result"))
        projection_result = _mapping(workflow.get("projection_result"))
        host_evidence = _mapping(workflow.get("host_evidence_presentation"))
        admission_result = _mapping(workflow.get("admission_result"))
        binding_summary = _mapping(admission_result.get("binding_reference_summary"))
        consumption_state = _mapping(admission_result.get("consumption_state"))
        final_summary = dict(self.final_candidate_summary)
        final_admission_state = _mapping(final_summary.get("admission_state"))
        return {
            "ok": self.ok,
            "workflow_surface": "scheduler-operator-dogfood-closure",
            "project_root": str(self.project_root),
            "request": {
                "fixture": self.request.fixture,
                "artifact_id": self.artifact_id,
                "version": self.version,
                "runtime_provider": self.request.runtime_provider,
                "inspect_binding_refs": self.request.inspect_binding_refs,
                "mark_consumed_on_success": self.request.mark_consumed_on_success,
                "replace_existing": self.request.replace_existing,
                "actor": self.request.actor,
                "evidence_id": self.request.evidence_id,
            },
            "steps": [step.to_json_dict() for step in self.steps],
            "fixture_result": dict(self.fixture_result),
            "workflow_result": workflow,
            "closure_summary": {
                "artifact_id": self.artifact_id,
                "version": self.version,
                "fixture": self.request.fixture,
                "lifecycle_state": str(final_summary.get("lifecycle_state", "")),
                "admission_status": str(final_admission_state.get("status", "")),
                "latest_admission_status": str(
                    final_admission_state.get("latest_status", "")
                ),
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
                "scheduler_projection_event_count": projection_result.get("event_count", 0),
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


def run_scheduler_operator_dogfood_closure(
    request: SchedulerOperatorDogfoodClosureRequest,
) -> SchedulerOperatorDogfoodClosureResult:
    """Run fixture seed through shared operator workflow and compact readback."""

    project_root = Path(request.project_root).resolve()
    artifact_id = request.artifact_id or _default_artifact_id(request.fixture)
    version = request.version or _default_version(request.fixture)
    steps: list[SchedulerOperatorDogfoodClosureStep] = []
    fixture_result: Mapping[str, object] = {}
    workflow_result: Mapping[str, object] = {}
    final_candidate_summary: Mapping[str, object] = {}

    runtime_provider = (request.runtime_provider or "fake").strip().lower()
    if runtime_provider != "fake":
        steps.append(
            SchedulerOperatorDogfoodClosureStep(
                name="preflightRuntime",
                status="failed",
                error=(
                    "scheduler operator dogfood closure currently supports "
                    "runtimeProvider='fake' only; real providers require a "
                    "separate live-runtime planning gate."
                ),
            )
        )
        return SchedulerOperatorDogfoodClosureResult(
            request=request,
            project_root=project_root,
            artifact_id=artifact_id,
            version=version,
            steps=tuple(steps),
        )

    try:
        fixture = _seed_fixture(request, project_root, artifact_id, version)
        fixture_result = fixture.to_json_dict()
        steps.append(
            SchedulerOperatorDogfoodClosureStep(
                name="seedFixture",
                status="completed",
                mutated=True,
                result=fixture_result,
            )
        )
    except Exception as exc:
        steps.append(
            SchedulerOperatorDogfoodClosureStep(
                name="seedFixture",
                status="failed",
                error=str(exc),
            )
        )

    if _has_failed(steps):
        steps.append(_skipped("operatorWorkflow", "fixture seeding failed"))
    else:
        workflow = run_scheduler_operator_workflow(
            SchedulerOperatorWorkflowRequest(
                project_root=project_root,
                artifact_id=artifact_id,
                version=version,
                admit=True,
                run_loop=True,
                refresh_projection=True,
                inspect_binding_refs=_should_inspect_binding_refs(request),
                artifact_store_path=request.artifact_store_path,
                admission_ledger_path=request.admission_ledger_path,
                snapshot_path=request.snapshot_path
                or DEFAULT_SCHEDULER_OPERATOR_SNAPSHOT_RELATIVE_PATH,
                event_log_path=request.event_log_path
                or DEFAULT_SCHEDULER_OPERATOR_EVENT_LOG_RELATIVE_PATH,
                merge_gate_event_log_path=request.merge_gate_event_log_path,
                projection_output_path=request.projection_output_path,
                evidence_id=request.evidence_id or DEFAULT_SCHEDULER_OPERATOR_EVIDENCE_ID,
                evidence_path=request.evidence_path,
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
            SchedulerOperatorDogfoodClosureStep(
                name="operatorWorkflow",
                status="completed" if workflow.ok else "failed",
                mutated=bool(
                    _mapping(workflow_result.get("authority_split")).get(
                        "scheduler_state_mutated"
                    )
                )
                or bool(
                    _mapping(workflow_result.get("authority_split")).get(
                        "exchange_store_mutated"
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
            bundle = inspect_exchange_artifact_store(
                _artifact_store_path(request, project_root),
                admission_ledger_path=_admission_ledger_path(request, project_root),
            ).to_json_dict()
            final_candidate_summary = _find_summary(bundle, artifact_id, version)
            steps.append(
                SchedulerOperatorDogfoodClosureStep(
                    name="readClosureSummary",
                    status="completed",
                    result=final_candidate_summary,
                )
            )
        except Exception as exc:
            steps.append(
                SchedulerOperatorDogfoodClosureStep(
                    name="readClosureSummary",
                    status="failed",
                    error=str(exc),
                )
            )

    return SchedulerOperatorDogfoodClosureResult(
        request=request,
        project_root=project_root,
        artifact_id=artifact_id,
        version=version,
        steps=tuple(steps),
        fixture_result=fixture_result,
        workflow_result=workflow_result,
        final_candidate_summary=final_candidate_summary,
    )


def _seed_fixture(
    request: SchedulerOperatorDogfoodClosureRequest,
    project_root: Path,
    artifact_id: str,
    version: str,
):
    kwargs = {
        "artifact_store_path": request.artifact_store_path,
        "artifact_id": artifact_id,
        "version": version,
        "replace_existing": request.replace_existing,
        "created_at": request.created_at or request.timestamp or "2026-06-22T00:00:00+00:00",
    }
    if request.fixture == "binding-consumer":
        return seed_scheduler_operator_binding_consumer_dogfood_fixture(
            project_root,
            **kwargs,
        )
    if request.fixture == "simple":
        return seed_scheduler_operator_dogfood_fixture(project_root, **kwargs)
    if request.fixture == "multilane":
        return seed_scheduler_operator_multilane_dogfood_fixture(project_root, **kwargs)
    raise ValueError(
        "scheduler operator dogfood closure fixture must be binding-consumer, "
        "simple, or multilane"
    )


def _should_inspect_binding_refs(request: SchedulerOperatorDogfoodClosureRequest) -> bool:
    return request.inspect_binding_refs or request.fixture == "binding-consumer"


def _artifact_store_path(
    request: SchedulerOperatorDogfoodClosureRequest,
    project_root: Path,
) -> Path:
    if request.artifact_store_path is not None:
        path = Path(request.artifact_store_path)
        return path if path.is_absolute() else project_root / path
    from src.runtime.orchestration import default_exchange_artifact_store_path

    return default_exchange_artifact_store_path(project_root)


def _admission_ledger_path(
    request: SchedulerOperatorDogfoodClosureRequest,
    project_root: Path,
) -> Path:
    if request.admission_ledger_path is not None:
        path = Path(request.admission_ledger_path)
        return path if path.is_absolute() else project_root / path
    return default_exchange_artifact_admission_ledger_path(project_root)


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


def _default_artifact_id(fixture: str) -> str:
    if fixture == "simple":
        return DEFAULT_SCHEDULER_OPERATOR_DOGFOOD_ARTIFACT_ID
    if fixture == "multilane":
        return DEFAULT_SCHEDULER_OPERATOR_MULTILANE_DOGFOOD_ARTIFACT_ID
    return DEFAULT_SCHEDULER_OPERATOR_BINDING_CONSUMER_DOGFOOD_ARTIFACT_ID


def _default_version(fixture: str) -> str:
    if fixture == "simple":
        return DEFAULT_SCHEDULER_OPERATOR_DOGFOOD_VERSION
    if fixture == "multilane":
        return DEFAULT_SCHEDULER_OPERATOR_MULTILANE_DOGFOOD_VERSION
    return DEFAULT_SCHEDULER_OPERATOR_BINDING_CONSUMER_DOGFOOD_VERSION


def _workflow_error(workflow: Mapping[str, object]) -> str:
    for step in workflow.get("steps", ()):
        if isinstance(step, Mapping) and step.get("status") == "failed":
            error = step.get("error")
            return str(error) if error else "operator workflow failed"
    return "operator workflow failed"


def _mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def _skipped(name: str, reason: str) -> SchedulerOperatorDogfoodClosureStep:
    return SchedulerOperatorDogfoodClosureStep(name=name, status="skipped", error=reason)


def _has_failed(steps: list[SchedulerOperatorDogfoodClosureStep]) -> bool:
    return any(step.status == "failed" for step in steps)


def _step_mutated(
    steps: tuple[SchedulerOperatorDogfoodClosureStep, ...],
    name: str,
) -> bool:
    return any(step.name == name and step.mutated for step in steps)
