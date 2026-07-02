"""Leader-side consumption of worker trajectory_update reports."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import jsonschema

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


__all__ = [
    "WorkerTrajectoryReportConsumerRequest",
    "WorkerTrajectoryReportConsumerResult",
    "consume_worker_trajectory_report",
]
