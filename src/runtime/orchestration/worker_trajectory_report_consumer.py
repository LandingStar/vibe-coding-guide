"""Leader-side consumption of worker trajectory_update reports."""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import jsonschema

from .log_readback import LogRecordRef

WorkerTrajectoryReportConsumerStatus = Literal[
    "consumed",
    "skipped",
    "validation_failed",
    "denied",
    "failed",
]

_REPORT_SCHEMA_PATH = (
    Path(__file__).resolve().parents[3]
    / "docs"
    / "specs"
    / "subagent-report.schema.json"
)
_REPORT_SCHEMA: dict[str, Any] | None = None

_DENIED_CALLER_ROLES = {
    "worker",
    "subagent",
    "sub_agent",
    "lane_worker",
    "bounded_worker",
    "child_worker",
}
_ALLOWED_CALLER_ROLES = {"", "leader", "main", "supervisor", "guide"}
_SUPPORTED_ACTIONS = {"append", "advance", "block", "wait", "resume", "close", "none"}


@dataclass(frozen=True, slots=True)
class WorkerReportReadbackEnvelope:
    """Human/audit-oriented readback projection for one Subagent Report."""

    schema_version: str
    record_id: str
    record_kind: str
    timestamp: str
    actor: str
    action: str
    status: str
    summary: str
    reason: str = ""
    run_id: str = ""
    correlation_id: str = ""
    subject_refs: tuple[LogRecordRef, ...] = ()
    input_refs: tuple[LogRecordRef, ...] = ()
    output_refs: tuple[LogRecordRef, ...] = ()
    evidence_refs: tuple[LogRecordRef, ...] = ()
    related_record_ids: tuple[str, ...] = ()
    next_hint: str = ""
    sensitivity: str = "internal"
    redaction_state: str = "contains_no_raw_secret"
    raw_payload_persisted: bool = False
    contract_id: str = ""
    lane_id: str = ""
    task_id: str = ""
    event_status: str = ""
    suggested_action: str = ""
    trajectory_update_present: bool = False
    leader_consumption_required: bool = False
    worker_direct_mutation_allowed: bool = False
    changed_artifact_count: int = 0
    verification_count: int = 0
    unresolved_item_count: int = 0
    artifact_payload_count: int = 0

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "record_id": self.record_id,
            "record_kind": self.record_kind,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "action": self.action,
            "status": self.status,
            "summary": self.summary,
            "reason": self.reason,
            "run_id": self.run_id,
            "correlation_id": self.correlation_id,
            "subject_refs": [ref.to_json_dict() for ref in self.subject_refs],
            "input_refs": [ref.to_json_dict() for ref in self.input_refs],
            "output_refs": [ref.to_json_dict() for ref in self.output_refs],
            "evidence_refs": [ref.to_json_dict() for ref in self.evidence_refs],
            "related_record_ids": list(self.related_record_ids),
            "next_hint": self.next_hint,
            "sensitivity": self.sensitivity,
            "redaction_state": self.redaction_state,
            "raw_payload_persisted": self.raw_payload_persisted,
            "contract_id": self.contract_id,
            "lane_id": self.lane_id,
            "task_id": self.task_id,
            "event_status": self.event_status,
            "suggested_action": self.suggested_action,
            "trajectory_update_present": self.trajectory_update_present,
            "leader_consumption_required": self.leader_consumption_required,
            "worker_direct_mutation_allowed": self.worker_direct_mutation_allowed,
            "changed_artifact_count": self.changed_artifact_count,
            "verification_count": self.verification_count,
            "unresolved_item_count": self.unresolved_item_count,
            "artifact_payload_count": self.artifact_payload_count,
            "authority_split": {
                "source": "Subagent Report",
                "trajectory_update_source": "Subagent Report.trajectory_update",
                "leader_review_required": self.leader_consumption_required,
                "worker_report_read": True,
                "local_work_trajectory_mutated": False,
                "worker_direct_mutation_allowed": self.worker_direct_mutation_allowed,
                "provider_executed": False,
                "scheduler_state_mutated": False,
                "exchange_store_mutated": False,
            },
            "worker_report_procedure": "docs/worker-trajectory-update-reporting.md",
        }


@dataclass(frozen=True, slots=True)
class WorkerTrajectoryReportConsumerRequest:
    """Request to consume one worker report trajectory_update section."""

    project_root: str | Path
    report_path: str | Path
    caller_role: str = "leader"
    actor: str = "leader"
    current_event_id: str = ""
    title: str = ""
    event_kind: str = "task"
    start_if_missing: bool = True
    trajectory_title: str = "Local Work Trajectory"
    guide_context: str = "worker-trajectory-report-consumer"


@dataclass(frozen=True, slots=True)
class WorkerTrajectoryReportConsumerResult:
    """Auditable result of consuming or rejecting one report."""

    ok: bool
    status: WorkerTrajectoryReportConsumerStatus
    report_path: Path
    trajectory_path: Path
    report_id: str = ""
    contract_id: str = ""
    caller_role: str = ""
    actor: str = ""
    suggested_action: str = ""
    consumed_action: str = ""
    lane_id: str = ""
    task_id: str = ""
    event_status: str = ""
    summary: str = ""
    evidence_refs: tuple[str, ...] = ()
    leader_notes: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    trajectory_id: str = ""
    active_event_id: str = ""
    active_event_ids: tuple[str, ...] = ()
    event_count: int = 0
    lane_count: int = 0
    relation_count: int = 0
    trajectory_created: bool = False

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "status": self.status,
            "report_path": str(self.report_path),
            "trajectory_path": str(self.trajectory_path),
            "report_id": self.report_id,
            "contract_id": self.contract_id,
            "caller_role": self.caller_role,
            "actor": self.actor,
            "suggested_action": self.suggested_action,
            "consumed_action": self.consumed_action,
            "lane_id": self.lane_id,
            "task_id": self.task_id,
            "event_status": self.event_status,
            "summary": self.summary,
            "evidence_refs": list(self.evidence_refs),
            "leader_notes": list(self.leader_notes),
            "errors": list(self.errors),
            "trajectory_id": self.trajectory_id,
            "active_event_id": self.active_event_id,
            "active_event_ids": list(self.active_event_ids),
            "event_count": self.event_count,
            "lane_count": self.lane_count,
            "relation_count": self.relation_count,
            "trajectory_created": self.trajectory_created,
            "authority_split": {
                "source": "Subagent Report.trajectory_update",
                "leader_review_required": True,
                "worker_report_read": True,
                "schema_validated": self.status not in {"denied", "validation_failed"},
                "local_work_trajectory_mutated": self.status == "consumed",
                "worker_direct_mutation_allowed": False,
                "provider_executed": False,
                "scheduler_state_mutated": False,
                "exchange_store_mutated": False,
            },
            "worker_report_procedure": "docs/worker-trajectory-update-reporting.md",
        }


def consume_worker_trajectory_report(
    request: WorkerTrajectoryReportConsumerRequest,
) -> WorkerTrajectoryReportConsumerResult:
    """Consume one worker report's trajectory_update as leader-owned mutation."""

    from tools.progress_graph import (
        advance_single_line_event,
        append_single_line_event,
        block_single_line_event,
        close_single_line_trajectory,
        load_local_work_trajectory,
        resume_single_line_event,
        start_single_line_trajectory,
        trajectory_json_path,
    )

    project_root = Path(request.project_root)
    report_path = _resolve_under_root(project_root, request.report_path)
    target_path = trajectory_json_path(project_root)
    normalized_role = _normalize_role(request.caller_role)
    if normalized_role in _DENIED_CALLER_ROLES or normalized_role not in _ALLOWED_CALLER_ROLES:
        allowed = ", ".join(sorted(role for role in _ALLOWED_CALLER_ROLES if role))
        return WorkerTrajectoryReportConsumerResult(
            ok=False,
            status="denied",
            report_path=report_path,
            trajectory_path=target_path,
            caller_role=request.caller_role,
            actor=request.actor,
            errors=(
                "Worker/subagent roles cannot consume or mutate Local Work Trajectory. "
                "Write trajectory suggestions in Subagent Report.trajectory_update and "
                "let a leader/main/supervisor consume them; see "
                "docs/worker-trajectory-update-reporting.md.",
                f"caller_role must be one of: {allowed}.",
            ),
        )

    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except Exception as exc:
        return WorkerTrajectoryReportConsumerResult(
            ok=False,
            status="validation_failed",
            report_path=report_path,
            trajectory_path=target_path,
            caller_role=request.caller_role,
            actor=request.actor,
            errors=(f"failed to read worker report: {exc}",),
        )
    if not isinstance(report, dict):
        return WorkerTrajectoryReportConsumerResult(
            ok=False,
            status="validation_failed",
            report_path=report_path,
            trajectory_path=target_path,
            caller_role=request.caller_role,
            actor=request.actor,
            errors=("worker report must be a JSON object",),
        )

    report_id = str(report.get("report_id", ""))
    contract_id = str(report.get("contract_id", ""))
    schema_errors = _validate_report(report)
    if schema_errors:
        return WorkerTrajectoryReportConsumerResult(
            ok=False,
            status="validation_failed",
            report_path=report_path,
            trajectory_path=target_path,
            report_id=report_id,
            contract_id=contract_id,
            caller_role=request.caller_role,
            actor=request.actor,
            errors=tuple(schema_errors),
        )

    update = report.get("trajectory_update")
    if not isinstance(update, dict):
        return WorkerTrajectoryReportConsumerResult(
            ok=True,
            status="skipped",
            report_path=report_path,
            trajectory_path=target_path,
            report_id=report_id,
            contract_id=contract_id,
            caller_role=request.caller_role,
            actor=request.actor,
            errors=("report has no trajectory_update to consume",),
        )

    action = str(update.get("suggested_action", "")).strip()
    lane_id = str(update.get("lane_id", "")).strip()
    task_id = str(update.get("task_id", "")).strip()
    event_status = str(update.get("event_status", "")).strip()
    summary = str(update.get("summary", "")).strip()
    evidence_refs = _string_tuple(update.get("evidence_refs"))
    leader_notes = _string_tuple(update.get("leader_notes"))

    if action not in _SUPPORTED_ACTIONS:
        return WorkerTrajectoryReportConsumerResult(
            ok=False,
            status="validation_failed",
            report_path=report_path,
            trajectory_path=target_path,
            report_id=report_id,
            contract_id=contract_id,
            caller_role=request.caller_role,
            actor=request.actor,
            suggested_action=action,
            lane_id=lane_id,
            task_id=task_id,
            event_status=event_status,
            summary=summary,
            evidence_refs=evidence_refs,
            leader_notes=leader_notes,
            errors=(f"unsupported trajectory_update.suggested_action: {action}",),
        )
    if action == "none":
        return WorkerTrajectoryReportConsumerResult(
            ok=True,
            status="skipped",
            report_path=report_path,
            trajectory_path=target_path,
            report_id=report_id,
            contract_id=contract_id,
            caller_role=request.caller_role,
            actor=request.actor,
            suggested_action=action,
            lane_id=lane_id,
            task_id=task_id,
            event_status=event_status,
            summary=summary,
            evidence_refs=evidence_refs,
            leader_notes=leader_notes,
            errors=("trajectory_update suggested no Local Work Trajectory mutation",),
        )

    try:
        trajectory_created = False
        if action == "append" and request.start_if_missing and _should_start_for_append(project_root):
            start_single_line_trajectory(
                project_root,
                title=request.trajectory_title,
                lane_label=lane_id or "worker report",
                first_event_title=_event_title(request, task_id),
                first_event_kind=_event_kind(request.event_kind),
                first_event_summary=summary,
                guide_context=request.guide_context,
                lane_id=lane_id or "lane:main",
                metadata={
                    "consumer": "worker-trajectory-report",
                    "actor": request.actor,
                },
                event_metadata=_event_metadata(report_id, contract_id, task_id, evidence_refs, leader_notes),
            )
            trajectory_created = True
        elif action == "append":
            append_single_line_event(
                project_root,
                title=_event_title(request, task_id),
                kind=_event_kind(request.event_kind),
                status="pending",
                summary=summary,
                lane_id=lane_id,
                metadata=_event_metadata(report_id, contract_id, task_id, evidence_refs, leader_notes),
            )
        elif action == "advance":
            advance_single_line_event(
                project_root,
                current_event_id=request.current_event_id or None,
            )
        elif action == "block":
            block_single_line_event(
                project_root,
                current_event_id=request.current_event_id or None,
                reason=summary,
                waiting=False,
            )
        elif action == "wait":
            block_single_line_event(
                project_root,
                current_event_id=request.current_event_id or None,
                reason=summary,
                waiting=True,
            )
        elif action == "resume":
            resume_single_line_event(
                project_root,
                current_event_id=request.current_event_id or None,
                summary=summary,
            )
        elif action == "close":
            close_single_line_trajectory(
                project_root,
                current_event_id=request.current_event_id or None,
                summary=summary,
            )
    except Exception as exc:
        return WorkerTrajectoryReportConsumerResult(
            ok=False,
            status="failed",
            report_path=report_path,
            trajectory_path=target_path,
            report_id=report_id,
            contract_id=contract_id,
            caller_role=request.caller_role,
            actor=request.actor,
            suggested_action=action,
            lane_id=lane_id,
            task_id=task_id,
            event_status=event_status,
            summary=summary,
            evidence_refs=evidence_refs,
            leader_notes=leader_notes,
            errors=(
                f"failed to consume trajectory_update: {exc}",
                "For non-append actions, create/start the Local Work Trajectory first or pass a valid current event id.",
            ),
        )

    trajectory = load_local_work_trajectory(project_root)
    active_event_ids = _active_event_ids(trajectory)
    return WorkerTrajectoryReportConsumerResult(
        ok=True,
        status="consumed",
        report_path=report_path,
        trajectory_path=target_path,
        report_id=report_id,
        contract_id=contract_id,
        caller_role=request.caller_role,
        actor=request.actor,
        suggested_action=action,
        consumed_action="start" if trajectory_created else action,
        lane_id=lane_id,
        task_id=task_id,
        event_status=event_status,
        summary=summary,
        evidence_refs=evidence_refs,
        leader_notes=leader_notes,
        trajectory_id=trajectory.trajectory_id,
        active_event_id=active_event_ids[0] if active_event_ids else "",
        active_event_ids=tuple(active_event_ids),
        event_count=len(trajectory.events),
        lane_count=len(trajectory.lanes),
        relation_count=len(trajectory.relations),
        trajectory_created=trajectory_created,
    )


def worker_report_to_readback_envelope(
    report: Mapping[str, Any],
    *,
    report_path: str | Path = "",
    timestamp: str = "",
    actor: str = "worker-report",
) -> WorkerReportReadbackEnvelope:
    """Project one Subagent Report mapping into a draft readback envelope.

    This is a read-only projection. It does not validate/consume
    `trajectory_update`, mutate Local Work Trajectory, run providers, or expose
    raw `artifact_payloads.content`.
    """

    report_id = _mapping_text(report, "report_id")
    contract_id = _mapping_text(report, "contract_id")
    status = _mapping_text(report, "status") or "unknown"
    trajectory_update = report.get("trajectory_update")
    update = trajectory_update if isinstance(trajectory_update, Mapping) else {}
    lane_id = _mapping_text(update, "lane_id")
    task_id = _mapping_text(update, "task_id")
    event_status = _mapping_text(update, "event_status")
    suggested_action = _mapping_text(update, "suggested_action")
    update_summary = _mapping_text(update, "summary")
    changed_artifacts = _string_tuple(report.get("changed_artifacts"))
    artifact_payloads = _artifact_payload_refs(report.get("artifact_payloads"))
    verification_results = _string_tuple(report.get("verification_results"))
    unresolved_items = _string_tuple(report.get("unresolved_items"))
    evidence_ref_values = _string_tuple(update.get("evidence_refs"))
    leader_notes = _string_tuple(update.get("leader_notes"))
    record_id = report_id or _path_or_default(report_path, "worker-report")
    trajectory_update_present = bool(update)
    leader_consumption_required = bool(
        trajectory_update_present and suggested_action and suggested_action != "none"
    )
    action = (
        f"worker_report_suggests_{suggested_action}"
        if leader_consumption_required
        else f"worker_report_{status}"
    )
    return WorkerReportReadbackEnvelope(
        schema_version="worker-report-readback-envelope.v1",
        record_id=record_id,
        record_kind="worker_report",
        timestamp=timestamp,
        actor=actor,
        action=action,
        status=status,
        summary=_worker_report_summary(
            report_id=record_id,
            contract_id=contract_id,
            status=status,
            lane_id=lane_id,
            task_id=task_id,
            event_status=event_status,
            suggested_action=suggested_action,
            update_summary=update_summary,
        ),
        reason=_worker_report_reason(
            status=status,
            trajectory_update_present=trajectory_update_present,
            suggested_action=suggested_action,
            unresolved_items=unresolved_items,
        ),
        correlation_id=_first_non_empty(task_id, contract_id, report_id),
        subject_refs=_worker_report_subject_refs(
            report_id=record_id,
            contract_id=contract_id,
            lane_id=lane_id,
            task_id=task_id,
        ),
        input_refs=_worker_report_input_refs(contract_id=contract_id),
        output_refs=_worker_report_output_refs(changed_artifacts, artifact_payloads),
        evidence_refs=_worker_report_evidence_refs(
            report_id=record_id,
            report_path=report_path,
            verification_results=verification_results,
            evidence_ref_values=evidence_ref_values,
            leader_notes=leader_notes,
        ),
        related_record_ids=_worker_report_related_record_ids(
            report_id=record_id,
            contract_id=contract_id,
            lane_id=lane_id,
            task_id=task_id,
            changed_artifacts=changed_artifacts,
            evidence_ref_values=evidence_ref_values,
        ),
        next_hint=_worker_report_next_hint(
            report_id=record_id,
            suggested_action=suggested_action,
            status=status,
            unresolved_items=unresolved_items,
        ),
        raw_payload_persisted=False,
        contract_id=contract_id,
        lane_id=lane_id,
        task_id=task_id,
        event_status=event_status,
        suggested_action=suggested_action,
        trajectory_update_present=trajectory_update_present,
        leader_consumption_required=leader_consumption_required,
        worker_direct_mutation_allowed=False,
        changed_artifact_count=len(changed_artifacts),
        verification_count=len(verification_results),
        unresolved_item_count=len(unresolved_items),
        artifact_payload_count=len(artifact_payloads),
    )


def _resolve_under_root(root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return root / path


def _load_schema() -> dict[str, Any]:
    global _REPORT_SCHEMA
    if _REPORT_SCHEMA is None:
        _REPORT_SCHEMA = json.loads(_REPORT_SCHEMA_PATH.read_text(encoding="utf-8"))
    return _REPORT_SCHEMA


def _validate_report(report: dict[str, Any]) -> list[str]:
    validator = jsonschema.Draft202012Validator(_load_schema())
    errors = sorted(validator.iter_errors(report), key=lambda error: list(error.path))
    return [_format_schema_error(error) for error in errors]


def _format_schema_error(error: jsonschema.ValidationError) -> str:
    path = ".".join(str(part) for part in error.path)
    prefix = f"{path}: " if path else ""
    return f"{prefix}{error.message}"


def _normalize_role(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(str(item) for item in value if str(item))


def _event_title(
    request: WorkerTrajectoryReportConsumerRequest,
    task_id: str,
) -> str:
    return request.title.strip() or task_id or "Worker trajectory update"


def _event_kind(value: str) -> str:
    allowed = {
        "start",
        "task",
        "decision",
        "review",
        "wait",
        "validation",
        "writeback",
        "handoff",
        "compound",
        "merge",
        "close",
    }
    normalized = value.strip()
    if normalized not in allowed:
        return "task"
    return normalized


def _event_metadata(
    report_id: str,
    contract_id: str,
    task_id: str,
    evidence_refs: tuple[str, ...],
    leader_notes: tuple[str, ...],
) -> dict[str, str]:
    metadata = {
        "source": "worker-trajectory-report-consumer",
        "worker_report_id": report_id,
        "worker_contract_id": contract_id,
        "worker_task_id": task_id,
    }
    if evidence_refs:
        metadata["worker_evidence_refs"] = "\n".join(evidence_refs)
    if leader_notes:
        metadata["worker_leader_notes"] = "\n".join(leader_notes)
    return metadata


def _should_start_for_append(project_root: Path) -> bool:
    from tools.progress_graph import load_local_work_trajectory, trajectory_json_path

    path = trajectory_json_path(project_root)
    if not path.exists():
        return True
    try:
        trajectory = load_local_work_trajectory(project_root)
    except Exception:
        return False
    return (
        not trajectory.lanes
        and trajectory.metadata.get("projection") == "single-lane-lifecycle"
        and trajectory.metadata.get("lifecycle_state") == "empty"
    )


def _active_event_ids(trajectory: Any) -> list[str]:
    return [
        event_id
        for event_id, event in sorted(
            trajectory.events.items(),
            key=lambda item: (item[1].order, item[0]),
        )
        if event.status == "in_progress"
    ]


def _mapping_text(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key, "")
    if value is None or isinstance(value, (list, tuple, dict, set)):
        return ""
    return str(value).strip()


def _artifact_payload_refs(value: object) -> tuple[LogRecordRef, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    refs: list[LogRecordRef] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            continue
        path = _mapping_text(item, "path")
        operation = _mapping_text(item, "operation")
        content_type = _mapping_text(item, "content_type")
        refs.append(
            LogRecordRef(
                kind="artifact_payload",
                id=f"artifact-payload-{index}",
                path=path,
                label=", ".join(part for part in (operation, content_type) if part),
                role="output",
            )
        )
    return tuple(refs)


def _path_or_default(value: str | Path, default: str) -> str:
    if not value:
        return default
    return str(value)


def _worker_report_summary(
    *,
    report_id: str,
    contract_id: str,
    status: str,
    lane_id: str,
    task_id: str,
    event_status: str,
    suggested_action: str,
    update_summary: str,
) -> str:
    subject = report_id or "worker report"
    parts = [f"Worker report {subject} is {status}"]
    if contract_id:
        parts.append(f"for contract {contract_id}")
    if lane_id or task_id:
        parts.append(f"on {', '.join(item for item in (lane_id, task_id) if item)}")
    sentence = " ".join(parts) + "."
    if suggested_action:
        sentence += f" It suggests Local Work action {suggested_action}."
    if event_status and event_status != status:
        sentence += f" Worker-observed event status is {event_status}."
    if update_summary:
        sentence += f" Summary: {_bounded_redacted_text(update_summary)}"
    return sentence


def _worker_report_reason(
    *,
    status: str,
    trajectory_update_present: bool,
    suggested_action: str,
    unresolved_items: tuple[str, ...],
) -> str:
    if trajectory_update_present and suggested_action and suggested_action != "none":
        return (
            "Subagent Report.trajectory_update is advisory; leader/main/supervisor "
            "must review evidence before mutating Local Work Trajectory."
        )
    if trajectory_update_present:
        return "Worker report includes trajectory_update but requests no Local Work mutation."
    if status == "blocked":
        return "Worker reported a blocked outcome; inspect unresolved items and evidence."
    if unresolved_items:
        return "Worker report has unresolved items that require leader review."
    return "Worker report recorded for leader review and audit."


def _worker_report_subject_refs(
    *,
    report_id: str,
    contract_id: str,
    lane_id: str,
    task_id: str,
) -> tuple[LogRecordRef, ...]:
    refs: list[LogRecordRef] = [
        LogRecordRef(kind="worker_report", id=report_id, role="subject")
    ]
    if contract_id:
        refs.append(LogRecordRef(kind="contract", id=contract_id, role="subject"))
    if lane_id:
        refs.append(LogRecordRef(kind="lane", id=lane_id, role="subject"))
    if task_id:
        refs.append(LogRecordRef(kind="task", id=task_id, role="subject"))
    return tuple(refs)


def _worker_report_input_refs(*, contract_id: str) -> tuple[LogRecordRef, ...]:
    refs: list[LogRecordRef] = [
        LogRecordRef(
            kind="schema",
            path="docs/specs/subagent-report.schema.json",
            label="Subagent Report schema",
            role="input",
        ),
        LogRecordRef(
            kind="procedure",
            path="docs/worker-trajectory-update-reporting.md",
            label="Worker trajectory update reporting",
            role="input",
        ),
    ]
    if contract_id:
        refs.append(LogRecordRef(kind="contract", id=contract_id, role="input"))
    return tuple(refs)


def _worker_report_output_refs(
    changed_artifacts: tuple[str, ...],
    artifact_payloads: tuple[LogRecordRef, ...],
) -> tuple[LogRecordRef, ...]:
    refs = [
        LogRecordRef(kind="changed_artifact", path=path, role="output")
        for path in changed_artifacts
    ]
    refs.extend(artifact_payloads)
    return tuple(refs)


def _worker_report_evidence_refs(
    *,
    report_id: str,
    report_path: str | Path,
    verification_results: tuple[str, ...],
    evidence_ref_values: tuple[str, ...],
    leader_notes: tuple[str, ...],
) -> tuple[LogRecordRef, ...]:
    refs: list[LogRecordRef] = [
        LogRecordRef(
            kind="worker_report",
            id=report_id,
            path=str(report_path) if report_path else "",
            role="evidence",
        )
    ]
    refs.extend(
        LogRecordRef(
            kind="verification_result",
            id=f"{report_id}:verification-{index}",
            label=_bounded_redacted_text(result),
            role="evidence",
        )
        for index, result in enumerate(verification_results)
    )
    refs.extend(
        _evidence_ref_from_value(value, index)
        for index, value in enumerate(evidence_ref_values)
    )
    refs.extend(
        LogRecordRef(
            kind="leader_note",
            id=f"{report_id}:leader-note-{index}",
            label=_bounded_redacted_text(note),
            role="evidence",
        )
        for index, note in enumerate(leader_notes)
    )
    return tuple(refs)


def _evidence_ref_from_value(value: str, index: int) -> LogRecordRef:
    if "/" in value or "\\" in value or value.startswith("."):
        return LogRecordRef(kind="evidence", path=value, role="evidence")
    return LogRecordRef(kind="evidence", id=value or f"evidence-{index}", role="evidence")


def _worker_report_related_record_ids(
    *,
    report_id: str,
    contract_id: str,
    lane_id: str,
    task_id: str,
    changed_artifacts: tuple[str, ...],
    evidence_ref_values: tuple[str, ...],
) -> tuple[str, ...]:
    related: list[str] = []
    for kind, value in (
        ("worker_report", report_id),
        ("contract", contract_id),
        ("lane", lane_id),
        ("task", task_id),
    ):
        if value:
            related.append(_related_record_id(kind, value))
    related.extend(
        _related_record_id("changed_artifact", artifact)
        for artifact in changed_artifacts
    )
    related.extend(
        _related_record_id("evidence", evidence)
        for evidence in evidence_ref_values
    )
    return tuple(dict.fromkeys(related))


def _worker_report_next_hint(
    *,
    report_id: str,
    suggested_action: str,
    status: str,
    unresolved_items: tuple[str, ...],
) -> str:
    if suggested_action and suggested_action != "none":
        return (
            f"Leader/main/supervisor should review {report_id} and consume "
            f"trajectory_update.{suggested_action} through consumeWorkerTrajectoryReport "
            "or an equivalent host-owned call."
        )
    if status == "blocked" or unresolved_items:
        return f"Inspect unresolved items and evidence in worker report {report_id}."
    return f"Inspect changed artifacts and verification evidence in worker report {report_id}."


def _related_record_id(kind: str, value: str) -> str:
    if value.startswith(f"{kind}:"):
        return value
    return f"{kind}:{value}"


def _first_non_empty(*values: str) -> str:
    for value in values:
        if value:
            return value
    return ""


def _bounded_redacted_text(value: str, *, limit: int = 240) -> str:
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


__all__ = [
    "WorkerReportReadbackEnvelope",
    "WorkerTrajectoryReportConsumerRequest",
    "WorkerTrajectoryReportConsumerResult",
    "consume_worker_trajectory_report",
    "worker_report_to_readback_envelope",
]
