"""Shared scheduler operator workflow surface.

This module composes existing scheduler operator primitives into one
host-neutral workflow result. It deliberately stays outside core orchestration
runtime because it also reads progress-graph projection and Host Evidence
presentation artifacts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Mapping

from src.runtime.orchestration.artifact_paths import dbc_artifact_path
from src.runtime.orchestration import (
    InMemoryArtifactVersionStore,
    JsonArtifactVersionStore,
    SchedulerDaemonLoopRequest,
    SchedulerDaemonLoopStopPolicy,
    admit_exchange_artifact_version_with_ledger,
    build_scheduler_loop_evidence,
    default_exchange_artifact_admission_ledger_path,
    default_exchange_artifact_store_path,
    default_scheduler_loop_evidence_path,
    inspect_exchange_artifact_store,
    inspect_supervisor_storage_binding_artifact_refs_for_submission,
    read_scheduler_state_snapshot,
    run_scheduler_daemon_loop,
    write_scheduler_loop_evidence,
)

from .host_evidence import build_host_evidence_presentation, read_host_evidence_bundle
from .scheduler_projection import (
    scheduler_work_trajectory_json_path,
    write_scheduler_work_trajectory_artifact,
)
from .trajectory import LocalWorkTrajectory


SchedulerOperatorWorkflowStepStatus = Literal["completed", "skipped", "failed"]

DEFAULT_SCHEDULER_OPERATOR_SNAPSHOT_RELATIVE_PATH = Path(
    dbc_artifact_path("scheduler", "scheduler-state.json")
)
DEFAULT_SCHEDULER_OPERATOR_EVENT_LOG_RELATIVE_PATH = Path(
    dbc_artifact_path("scheduler", "scheduler-events.jsonl")
)
DEFAULT_SCHEDULER_OPERATOR_EVIDENCE_ID = "scheduler-operator-workflow-loop"


@dataclass(frozen=True, slots=True)
class SchedulerOperatorWorkflowRequest:
    """Request for the explicit scheduler operator workflow."""

    project_root: str | Path
    artifact_id: str = ""
    version: str = ""
    admit: bool = False
    run_loop: bool = False
    refresh_projection: bool = False
    inspect_binding_refs: bool = False
    artifact_store_path: str | Path | None = None
    admission_ledger_path: str | Path | None = None
    snapshot_path: str | Path | None = None
    event_log_path: str | Path | None = None
    merge_gate_event_log_path: str | Path | None = None
    projection_output_path: str | Path | None = None
    evidence_id: str = ""
    evidence_path: str | Path | None = None
    runtime_provider: str = "fake"
    max_ticks: int = 3
    max_runs_per_tick: int | None = 1
    max_runtime_failures: int | None = 1
    allow_duplicate_admission: bool = False
    replace_existing: bool = False
    mark_consumed_on_success: bool = False
    actor: str = "operator-workflow"
    timestamp: str = ""
    guide_context: str = ""
    source_graph_id: str = ""
    source_node_id: str = ""


@dataclass(frozen=True, slots=True)
class SchedulerOperatorWorkflowStep:
    """One ordered workflow step with isolated status."""

    name: str
    status: SchedulerOperatorWorkflowStepStatus
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
class SchedulerOperatorWorkflowResult:
    """Result of the shared scheduler operator workflow."""

    request: SchedulerOperatorWorkflowRequest
    project_root: Path
    artifact_store_path: Path
    admission_ledger_path: Path
    snapshot_path: Path
    event_log_path: Path
    merge_gate_event_log_path: Path | None
    projection_output_path: Path
    evidence_path: Path
    evidence_id: str
    steps: tuple[SchedulerOperatorWorkflowStep, ...]
    candidate_bundle: Mapping[str, object]
    binding_reference_inspection: Mapping[str, object] = field(default_factory=dict)
    admission_result: Mapping[str, object] = field(default_factory=dict)
    loop_result: Mapping[str, object] = field(default_factory=dict)
    projection_result: Mapping[str, object] = field(default_factory=dict)
    host_evidence_presentation: Mapping[str, object] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return not any(step.status == "failed" for step in self.steps)

    @property
    def authority_split(self) -> dict[str, object]:
        admission_authority = _mapping(self.admission_result.get("authority_split"))
        loop_authority = _mapping(self.loop_result.get("authority_split"))
        projection_authority = _mapping(self.projection_result.get("authority_split"))
        return {
            "workflow_surface": "scheduler-operator-workflow",
            "exchange_store_mutated": bool(admission_authority.get("exchange_store_mutated")),
            "admission_ledger_mutated": _step_mutated(self.steps, "admit"),
            "scheduler_state_mutated": (
                bool(admission_authority.get("scheduler_state_mutated"))
                or bool(loop_authority.get("scheduler_state_mutated"))
            ),
            "provider_executed": bool(loop_authority.get("provider_executed")),
            "scheduler_projection_refreshed": (
                bool(projection_authority.get("scheduler_projection_refreshed"))
                or _step_completed(self.steps, "refreshProjection")
            ),
            "evidence_written": _step_mutated(self.steps, "runLoop"),
            "host_evidence_read": _step_completed(self.steps, "readHostEvidencePresentation"),
            "local_work_trajectory_mutated": False,
        }

    def to_json_dict(self) -> dict[str, object]:
        """Return the stable host/MCP/CLI JSON-compatible payload."""

        return {
            "ok": self.ok,
            "workflow_surface": "scheduler-operator-workflow",
            "project_root": str(self.project_root),
            "paths": {
                "artifact_store_path": str(self.artifact_store_path),
                "admission_ledger_path": str(self.admission_ledger_path),
                "snapshot_path": str(self.snapshot_path),
                "event_log_path": str(self.event_log_path),
                "merge_gate_event_log_path": (
                    "" if self.merge_gate_event_log_path is None else str(self.merge_gate_event_log_path)
                ),
                "scheduler_projection_path": str(self.projection_output_path),
                "evidence_path": str(self.evidence_path),
            },
            "request": {
                "artifact_id": self.request.artifact_id,
                "version": self.request.version,
                "admit": self.request.admit,
                "run_loop": self.request.run_loop,
                "refresh_projection": self.request.refresh_projection,
                "inspect_binding_refs": self.request.inspect_binding_refs,
                "runtime_provider": self.request.runtime_provider,
                "max_ticks": self.request.max_ticks,
                "max_runs_per_tick": self.request.max_runs_per_tick,
                "max_runtime_failures": self.request.max_runtime_failures,
                "allow_duplicate_admission": self.request.allow_duplicate_admission,
                "replace_existing": self.request.replace_existing,
                "mark_consumed_on_success": self.request.mark_consumed_on_success,
                "actor": self.request.actor,
                "evidence_id": self.evidence_id,
            },
            "steps": [step.to_json_dict() for step in self.steps],
            "candidate_bundle": dict(self.candidate_bundle),
            "binding_reference_inspection": dict(self.binding_reference_inspection),
            "admission_result": dict(self.admission_result),
            "loop_result": dict(self.loop_result),
            "projection_result": dict(self.projection_result),
            "host_evidence_presentation": dict(self.host_evidence_presentation),
            "authority_split": self.authority_split,
        }


def run_scheduler_operator_workflow(
    request: SchedulerOperatorWorkflowRequest,
) -> SchedulerOperatorWorkflowResult:
    """Run the explicit scheduler operator workflow with per-step isolation."""

    paths = _ResolvedSchedulerOperatorWorkflowPaths.from_request(request)
    steps: list[SchedulerOperatorWorkflowStep] = []
    candidate_bundle: Mapping[str, object] = {}
    binding_reference_inspection: Mapping[str, object] = {}
    admission_result: Mapping[str, object] = {}
    loop_result: Mapping[str, object] = {}
    projection_result: Mapping[str, object] = {}
    host_evidence_presentation: Mapping[str, object] = {}

    try:
        bundle = inspect_exchange_artifact_store(
            paths.artifact_store_path,
            admission_ledger_path=paths.admission_ledger_path,
        )
        candidate_bundle = bundle.to_json_dict()
        steps.append(
            SchedulerOperatorWorkflowStep(
                name="inspectCandidates",
                status="completed",
                mutated=False,
                result=candidate_bundle,
            )
        )
    except Exception as exc:
        steps.append(
            SchedulerOperatorWorkflowStep(
                name="inspectCandidates",
                status="failed",
                error=str(exc),
            )
        )

    inspection_failed = False
    if request.inspect_binding_refs:
        if _has_failed(steps):
            inspection_failed = True
            steps.append(_skipped("inspectBindingRefs", "candidate inspection failed"))
        elif not request.artifact_id or not request.version:
            inspection_failed = True
            steps.append(
                SchedulerOperatorWorkflowStep(
                    name="inspectBindingRefs",
                    status="failed",
                    error=(
                        "scheduler operator workflow inspectBindingRefs requires "
                        "artifactId and version."
                    ),
                )
            )
        else:
            try:
                inspection = inspect_supervisor_storage_binding_artifact_refs_for_submission(
                    artifact_store_path=paths.artifact_store_path,
                    artifact_id=request.artifact_id,
                    version=request.version,
                )
                binding_reference_inspection = inspection.to_json_dict()
                inspection_failed = not bool(binding_reference_inspection.get("ok"))
                steps.append(
                    SchedulerOperatorWorkflowStep(
                        name="inspectBindingRefs",
                        status="completed" if not inspection_failed else "failed",
                        mutated=False,
                        error=(
                            ""
                            if not inspection_failed
                            else str(
                                binding_reference_inspection.get(
                                    "errors",
                                    ["binding reference inspection failed"],
                                )[0]
                            )
                        ),
                        result=binding_reference_inspection,
                    )
                )
            except Exception as exc:
                inspection_failed = True
                steps.append(
                    SchedulerOperatorWorkflowStep(
                        name="inspectBindingRefs",
                        status="failed",
                        error=str(exc),
                    )
                )
    admission_failed = False
    if request.admit:
        if _has_failed(steps):
            admission_failed = True
            reason = (
                "binding reference inspection failed"
                if inspection_failed
                else "candidate inspection failed"
            )
            steps.append(_skipped("admit", reason))
        elif not request.artifact_id or not request.version:
            admission_failed = True
            steps.append(
                SchedulerOperatorWorkflowStep(
                    name="admit",
                    status="failed",
                    error="scheduler operator workflow admit requires artifactId and version.",
                )
            )
        else:
            admission_result = admit_exchange_artifact_version_with_ledger(
                artifact_store_path=paths.artifact_store_path,
                artifact_id=request.artifact_id,
                version=request.version,
                snapshot_path=paths.snapshot_path,
                event_log_path=paths.event_log_path,
                admission_ledger_path=paths.admission_ledger_path,
                allow_duplicate_admission=request.allow_duplicate_admission,
                replace_existing=request.replace_existing,
                validate_binding_artifact_refs=request.inspect_binding_refs,
                mark_consumed_on_success=request.mark_consumed_on_success,
                actor=request.actor or "operator-workflow",
                surface="operator-workflow:scheduler",
                timestamp=request.timestamp,
            )
            admission_ok = bool(admission_result.get("ok"))
            admission_failed = not admission_ok
            steps.append(
                SchedulerOperatorWorkflowStep(
                    name="admit",
                    status="completed" if admission_ok else "failed",
                    mutated=_admission_result_mutated(admission_result),
                    error="" if admission_ok else str(admission_result.get("error", "admission failed")),
                    result=admission_result,
                )
            )
    else:
        steps.append(_skipped("admit", "admit=false"))

    loop_failed = False
    if request.run_loop:
        if admission_failed:
            loop_failed = True
            steps.append(_skipped("runLoop", "admission failed"))
        elif _has_failed(steps):
            loop_failed = True
            steps.append(_skipped("runLoop", "previous workflow step failed"))
        elif (request.runtime_provider or "fake").strip().lower() != "fake":
            loop_failed = True
            steps.append(
                SchedulerOperatorWorkflowStep(
                    name="runLoop",
                    status="failed",
                    error=(
                        "scheduler operator workflow currently supports "
                        "runtimeProvider='fake' only; real providers require "
                        "a host-owned runtime surface."
                    ),
                )
            )
        else:
            try:
                loop_result = _run_loop_and_write_evidence(request, paths)
                steps.append(
                    SchedulerOperatorWorkflowStep(
                        name="runLoop",
                        status="completed",
                        mutated=True,
                        result=loop_result,
                    )
                )
            except Exception as exc:
                loop_failed = True
                steps.append(
                    SchedulerOperatorWorkflowStep(
                        name="runLoop",
                        status="failed",
                        error=str(exc),
                    )
                )
    else:
        steps.append(_skipped("runLoop", "runLoop=false"))

    if request.refresh_projection:
        if admission_failed or loop_failed:
            reason = "admission failed" if admission_failed else "scheduler loop failed"
            steps.append(_skipped("refreshProjection", reason))
        elif _has_failed(steps):
            steps.append(_skipped("refreshProjection", "previous workflow step failed"))
        else:
            try:
                projection_result = _refresh_projection(request, paths)
                loop_result = _enrich_loop_evidence_after_projection(
                    loop_result,
                    projection_result,
                    paths,
                )
                steps.append(
                    SchedulerOperatorWorkflowStep(
                        name="refreshProjection",
                        status="completed",
                        mutated=True,
                        result=projection_result,
                    )
                )
            except Exception as exc:
                steps.append(
                    SchedulerOperatorWorkflowStep(
                        name="refreshProjection",
                        status="failed",
                        error=str(exc),
                    )
                )
    else:
        steps.append(_skipped("refreshProjection", "refreshProjection=false"))

    try:
        presentation = build_host_evidence_presentation(
            read_host_evidence_bundle(paths.project_root)
        )
        host_evidence_presentation = presentation.to_json_dict()
        steps.append(
            SchedulerOperatorWorkflowStep(
                name="readHostEvidencePresentation",
                status="completed",
                result=host_evidence_presentation,
            )
        )
    except Exception as exc:
        steps.append(
            SchedulerOperatorWorkflowStep(
                name="readHostEvidencePresentation",
                status="failed",
                error=str(exc),
            )
        )

    return SchedulerOperatorWorkflowResult(
        request=request,
        project_root=paths.project_root,
        artifact_store_path=paths.artifact_store_path,
        admission_ledger_path=paths.admission_ledger_path,
        snapshot_path=paths.snapshot_path,
        event_log_path=paths.event_log_path,
        merge_gate_event_log_path=paths.merge_gate_event_log_path,
        projection_output_path=paths.projection_output_path,
        evidence_path=paths.evidence_path,
        evidence_id=paths.evidence_id,
        steps=tuple(steps),
        candidate_bundle=candidate_bundle,
        binding_reference_inspection=binding_reference_inspection,
        admission_result=admission_result,
        loop_result=loop_result,
        projection_result=projection_result,
        host_evidence_presentation=host_evidence_presentation,
    )


@dataclass(frozen=True, slots=True)
class _ResolvedSchedulerOperatorWorkflowPaths:
    project_root: Path
    artifact_store_path: Path
    admission_ledger_path: Path
    snapshot_path: Path
    event_log_path: Path
    merge_gate_event_log_path: Path | None
    projection_output_path: Path
    evidence_id: str
    evidence_path: Path

    @classmethod
    def from_request(
        cls,
        request: SchedulerOperatorWorkflowRequest,
    ) -> "_ResolvedSchedulerOperatorWorkflowPaths":
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
        merge_gate_log = (
            _resolve(project_root, request.merge_gate_event_log_path)
            if request.merge_gate_event_log_path is not None
            else None
        )
        projection_output = (
            _resolve(project_root, request.projection_output_path)
            if request.projection_output_path is not None
            else scheduler_work_trajectory_json_path(project_root)
        )
        evidence_id = request.evidence_id or DEFAULT_SCHEDULER_OPERATOR_EVIDENCE_ID
        evidence_path = (
            _resolve(project_root, request.evidence_path)
            if request.evidence_path is not None
            else default_scheduler_loop_evidence_path(project_root, evidence_id)
        )
        return cls(
            project_root=project_root,
            artifact_store_path=artifact_store,
            admission_ledger_path=admission_ledger,
            snapshot_path=snapshot,
            event_log_path=event_log,
            merge_gate_event_log_path=merge_gate_log,
            projection_output_path=projection_output,
            evidence_id=evidence_id,
            evidence_path=evidence_path,
        )


def _run_loop_and_write_evidence(
    request: SchedulerOperatorWorkflowRequest,
    paths: _ResolvedSchedulerOperatorWorkflowPaths,
) -> Mapping[str, object]:
    artifact_store = _runtime_artifact_store_from_exchange_store(paths.artifact_store_path)
    loop = run_scheduler_daemon_loop(
        SchedulerDaemonLoopRequest(
            snapshot_path=paths.snapshot_path,
            event_log_path=paths.event_log_path,
            stop_policy=SchedulerDaemonLoopStopPolicy(
                max_ticks=request.max_ticks,
                max_runs_per_tick=request.max_runs_per_tick,
                max_runtime_failures=request.max_runtime_failures,
            ),
            runtime_provider="fake",
            timestamp=request.timestamp,
            workspace_root=str(paths.project_root),
        ),
        artifact_store=artifact_store,
    )
    payload = loop.to_json_dict()
    written = write_scheduler_loop_evidence(
        build_scheduler_loop_evidence(
            loop,
            evidence_id=paths.evidence_id,
            timestamp=request.timestamp,
            evidence_path=paths.evidence_path,
            metadata={
                "surface": "scheduler-operator-workflow",
                "workflow_surface": "scheduler-operator-workflow",
                "runtime_host_surface": "scheduler-operator-workflow",
                "host_invocation_id": f"schedulerOperatorWorkflow:{paths.evidence_id}",
            },
        ),
        paths.evidence_path,
    )
    authority = _mapping(payload.get("authority_split"))
    authority.update(
        {
            "evidence_written": True,
            "evidence_path": str(written.evidence_path),
        }
    )
    payload["authority_split"] = authority
    payload["evidence_written"] = True
    payload["evidence_id"] = paths.evidence_id
    payload["evidence_path"] = str(written.evidence_path)
    return payload


def _runtime_artifact_store_from_exchange_store(
    artifact_store_path: Path,
) -> InMemoryArtifactVersionStore:
    """Mirror durable ExchangeArtifacts into the fake runtime input store."""

    runtime_store = InMemoryArtifactVersionStore()
    for record in JsonArtifactVersionStore(artifact_store_path).list_records():
        runtime_store.put(record.artifact)
    return runtime_store


def _refresh_projection(
    request: SchedulerOperatorWorkflowRequest,
    paths: _ResolvedSchedulerOperatorWorkflowPaths,
) -> Mapping[str, object]:
    state = read_scheduler_state_snapshot(paths.snapshot_path)
    written = write_scheduler_work_trajectory_artifact(
        paths.project_root,
        state,
        scheduler_event_log_path=paths.event_log_path,
        merge_gate_event_log_path=paths.merge_gate_event_log_path,
        output_path=paths.projection_output_path,
        recorded_at=request.timestamp,
        guide_context=request.guide_context,
        source_graph_id=request.source_graph_id,
        source_node_id=request.source_node_id,
    )
    trajectory = LocalWorkTrajectory.from_json(written.read_text(encoding="utf-8"))
    return {
        "ok": True,
        "snapshot_path": str(paths.snapshot_path),
        "scheduler_event_log_path": str(paths.event_log_path),
        "merge_gate_event_log_path": (
            "" if paths.merge_gate_event_log_path is None else str(paths.merge_gate_event_log_path)
        ),
        "scheduler_projection_path": str(written),
        "trajectory_id": trajectory.trajectory_id,
        "title": trajectory.title,
        "guide_context": trajectory.guide_context,
        "event_count": len(trajectory.events),
        "lane_count": len(trajectory.lanes),
        "relation_count": len(trajectory.relations),
        "metadata": dict(trajectory.metadata),
        "authority_split": {
            "scheduler_state_authority": "scheduler_snapshot",
            "scheduler_state_mutated": False,
            "provider_executed": False,
            "scheduler_projection_refreshed": True,
            "scheduler_projection_role": "read-only-view",
            "scheduler_projection_path": str(written),
            "local_work_trajectory_mutated": False,
        },
    }


def _enrich_loop_evidence_after_projection(
    loop_result: Mapping[str, object],
    projection_result: Mapping[str, object],
    paths: _ResolvedSchedulerOperatorWorkflowPaths,
) -> Mapping[str, object]:
    if not loop_result or not bool(loop_result.get("evidence_written")):
        return loop_result
    try:
        import json

        payload = json.loads(paths.evidence_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            return loop_result
        metadata = _mapping(payload.get("metadata"))
        metadata.update(
            {
                "scheduler_projection_path": str(paths.projection_output_path),
                "scheduler_projection_role": "read-only-view",
                "scheduler_projection_refreshed": True,
                "scheduler_projection_summary": {
                    "event_count": projection_result.get("event_count", 0),
                    "lane_count": projection_result.get("lane_count", 0),
                    "relation_count": projection_result.get("relation_count", 0),
                },
            }
        )
        authority = _mapping(payload.get("authority_split"))
        authority.update(
            {
                "scheduler_projection_refreshed": True,
                "scheduler_projection_role": "read-only-view",
                "scheduler_projection_path": str(paths.projection_output_path),
            }
        )
        payload["metadata"] = metadata
        payload["authority_split"] = authority
        embedded_loop = payload.get("loop_result")
        if isinstance(embedded_loop, dict):
            embedded_authority = _mapping(embedded_loop.get("authority_split"))
            embedded_authority.update(authority)
            embedded_loop["authority_split"] = embedded_authority
            embedded_loop["scheduler_projection_path"] = str(paths.projection_output_path)
        paths.evidence_path.write_text(
            _json_dumps_with_newline(payload),
            encoding="utf-8",
        )
    except Exception:
        return loop_result

    updated = dict(loop_result)
    authority = _mapping(updated.get("authority_split"))
    authority.update(
        {
            "scheduler_projection_refreshed": True,
            "scheduler_projection_role": "read-only-view",
            "scheduler_projection_path": str(paths.projection_output_path),
        }
    )
    updated["authority_split"] = authority
    updated["scheduler_projection_path"] = str(paths.projection_output_path)
    return updated


def _admission_result_mutated(result: Mapping[str, object]) -> bool:
    if result.get("admission_ledger_record_id"):
        return True
    authority = _mapping(result.get("authority_split"))
    return bool(authority.get("scheduler_state_mutated"))


def _resolve(project_root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return project_root / path


def _mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, Mapping) else {}


def _skipped(name: str, reason: str) -> SchedulerOperatorWorkflowStep:
    return SchedulerOperatorWorkflowStep(
        name=name,
        status="skipped",
        error=reason,
    )


def _has_failed(steps: list[SchedulerOperatorWorkflowStep]) -> bool:
    return any(step.status == "failed" for step in steps)


def _step_completed(
    steps: tuple[SchedulerOperatorWorkflowStep, ...],
    name: str,
) -> bool:
    return any(step.name == name and step.status == "completed" for step in steps)


def _step_mutated(
    steps: tuple[SchedulerOperatorWorkflowStep, ...],
    name: str,
) -> bool:
    return any(step.name == name and step.mutated for step in steps)


def _json_dumps_with_newline(payload: Mapping[str, object]) -> str:
    import json

    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
