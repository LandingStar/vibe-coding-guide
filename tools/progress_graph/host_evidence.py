"""Read host scheduler run evidence for progress preview consumers."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Literal, TypeAlias

from src.runtime.orchestration import (
    HOST_SCHEDULER_RUN_EVIDENCE_PRODUCT_TYPE,
    SCHEDULER_LOOP_EVIDENCE_PRODUCT_TYPE,
    HostSchedulerRunEvidenceSummary,
    SchedulerLoopEvidenceSummary,
    read_host_scheduler_run_evidence_summary,
    read_scheduler_loop_evidence_summary,
)

HostEvidenceCardStatus = Literal[
    "completed",
    "permission-review",
    "partial",
    "failed",
    "unknown",
]
HostEvidenceBundleStatus = Literal["empty", "ok", "degraded", "failed"]
HostEvidenceSeverity = Literal["info", "warning", "error"]
HostEvidenceSummary: TypeAlias = HostSchedulerRunEvidenceSummary | SchedulerLoopEvidenceSummary


@dataclass(frozen=True, slots=True)
class HostEvidenceReadError:
    """Compact, secret-safe read error for one host evidence artifact."""

    evidence_path: Path
    error_kind: str
    message: str

    def to_json_dict(self) -> dict[str, object]:
        """Return a UI/resource-safe error summary without file contents."""

        return {
            "evidence_path": str(self.evidence_path),
            "error_kind": self.error_kind,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class HostEvidenceBundle:
    """Read-only view of host scheduler evidence artifacts."""

    project_root: Path
    evidence_dir: Path
    summaries: tuple[HostEvidenceSummary, ...]
    errors: tuple[HostEvidenceReadError, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        """Return a host/UI safe evidence bundle summary."""

        return {
            "project_root": str(self.project_root),
            "evidence_dir": str(self.evidence_dir),
            "evidence_count": len(self.summaries),
            "error_count": len(self.errors),
            "summaries": [summary.to_json_dict() for summary in self.summaries],
            "errors": [error.to_json_dict() for error in self.errors],
        }


@dataclass(frozen=True, slots=True)
class HostEvidencePresentationFact:
    """Small labeled value for host evidence presentation surfaces."""

    label: str
    value: str

    def to_json_dict(self) -> dict[str, str]:
        return {"label": self.label, "value": self.value}


@dataclass(frozen=True, slots=True)
class HostEvidencePresentationRef:
    """Path or artifact clue for host evidence presentation surfaces."""

    label: str
    target: str
    ref_kind: str = "path"

    def to_json_dict(self) -> dict[str, str]:
        return {
            "label": self.label,
            "target": self.target,
            "ref_kind": self.ref_kind,
        }


@dataclass(frozen=True, slots=True)
class HostEvidencePresentationCard:
    """UI/operator-facing card for one host evidence summary."""

    id: str
    title: str
    subtitle: str
    status: HostEvidenceCardStatus
    severity: HostEvidenceSeverity
    timestamp: str
    runtime_providers: tuple[str, ...]
    host_surface: str
    invocation_id: str
    requested_by: str
    stop_reason: str
    stop_detail: str
    run_count: int
    output_count: int
    permission_review_count: int
    key_facts: tuple[HostEvidencePresentationFact, ...] = ()
    refs: tuple[HostEvidencePresentationRef, ...] = ()
    authority_clues: tuple[HostEvidencePresentationFact, ...] = ()
    metadata: dict[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "title": self.title,
            "subtitle": self.subtitle,
            "status": self.status,
            "severity": self.severity,
            "timestamp": self.timestamp,
            "runtime_providers": list(self.runtime_providers),
            "host_surface": self.host_surface,
            "invocation_id": self.invocation_id,
            "requested_by": self.requested_by,
            "stop_reason": self.stop_reason,
            "stop_detail": self.stop_detail,
            "run_count": self.run_count,
            "output_count": self.output_count,
            "permission_review_count": self.permission_review_count,
            "key_facts": [fact.to_json_dict() for fact in self.key_facts],
            "refs": [ref.to_json_dict() for ref in self.refs],
            "authority_clues": [clue.to_json_dict() for clue in self.authority_clues],
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class HostEvidencePresentationErrorRow:
    """UI/operator-facing row for one isolated host evidence read error."""

    id: str
    status: Literal["read-error"]
    severity: Literal["error"]
    evidence_path: str
    error_kind: str
    message: str

    def to_json_dict(self) -> dict[str, str]:
        return {
            "id": self.id,
            "status": self.status,
            "severity": self.severity,
            "evidence_path": self.evidence_path,
            "error_kind": self.error_kind,
            "message": self.message,
        }


@dataclass(frozen=True, slots=True)
class HostEvidencePresentation:
    """Stable presentation contract over host evidence bundle data."""

    generated_at: str
    project_root: Path
    evidence_dir: Path
    status: HostEvidenceBundleStatus
    cards: tuple[HostEvidencePresentationCard, ...] = ()
    error_rows: tuple[HostEvidencePresentationErrorRow, ...] = ()
    empty_message: str = ""

    def to_json_dict(self) -> dict[str, object]:
        return {
            "generated_at": self.generated_at,
            "project_root": str(self.project_root),
            "evidence_dir": str(self.evidence_dir),
            "status": self.status,
            "card_count": len(self.cards),
            "error_count": len(self.error_rows),
            "cards": [card.to_json_dict() for card in self.cards],
            "error_rows": [row.to_json_dict() for row in self.error_rows],
            "empty_message": self.empty_message,
        }


def build_host_evidence_presentation(
    bundle: HostEvidenceBundle,
    *,
    generated_at: str = "",
) -> HostEvidencePresentation:
    """Build a stable UI/operator-facing view over a host evidence bundle."""

    cards = tuple(_host_evidence_presentation_card(summary) for summary in bundle.summaries)
    error_rows = tuple(
        _host_evidence_presentation_error_row(error, index=index)
        for index, error in enumerate(bundle.errors, start=1)
    )
    return HostEvidencePresentation(
        generated_at=generated_at,
        project_root=bundle.project_root,
        evidence_dir=bundle.evidence_dir,
        status=_host_evidence_bundle_status(cards, error_rows),
        cards=cards,
        error_rows=error_rows,
        empty_message=(
            "No host scheduler run evidence has been recorded."
            if not cards and not error_rows
            else ""
        ),
    )


def host_scheduler_evidence_dir(project_root: str | Path) -> Path:
    """Return the default host scheduler evidence directory."""

    return Path(project_root) / ".codex/scheduler/evidence"


def _host_evidence_presentation_card(
    summary: HostEvidenceSummary,
) -> HostEvidencePresentationCard:
    if isinstance(summary, SchedulerLoopEvidenceSummary):
        return _scheduler_loop_evidence_presentation_card(summary)
    return _host_scheduler_run_evidence_presentation_card(summary)


def _host_scheduler_run_evidence_presentation_card(
    summary: HostSchedulerRunEvidenceSummary,
) -> HostEvidencePresentationCard:
    status = _host_evidence_card_status(summary)
    output_refs = tuple(summary.output_artifact_refs)
    host_invocation = dict(summary.host_invocation)
    authority_split = dict(summary.authority_split)
    evidence_id = summary.evidence_id
    host_surface = _mapping_str(host_invocation, "surface")
    invocation_id = _mapping_str(host_invocation, "invocation_id")
    requested_by = _mapping_str(host_invocation, "requested_by")
    reason = _mapping_str(host_invocation, "reason")
    subtitle_parts = [
        part for part in (host_surface, summary.stop_reason, f"{summary.run_count} run(s)")
        if part
    ]

    key_facts = (
        HostEvidencePresentationFact("Stop reason", summary.stop_reason),
        HostEvidencePresentationFact("Run count", str(summary.run_count)),
        HostEvidencePresentationFact("Outputs", str(len(output_refs))),
        HostEvidencePresentationFact("Blocked tasks", str(len(summary.blocked_task_ids))),
        HostEvidencePresentationFact("Failed tasks", str(len(summary.failed_task_ids))),
        HostEvidencePresentationFact("Permission reviews", str(summary.permission_review_count)),
    )
    refs: list[HostEvidencePresentationRef] = [
        HostEvidencePresentationRef("Evidence", str(summary.evidence_path)),
        HostEvidencePresentationRef("Snapshot", summary.snapshot_path),
        HostEvidencePresentationRef("Event log", summary.event_log_path),
        HostEvidencePresentationRef("Scheduler projection", summary.scheduler_projection_path),
    ]
    for ref in output_refs:
        artifact_id = _mapping_str(ref, "artifact_id")
        if artifact_id:
            task_id = _mapping_str(ref, "task_id") or "task"
            version = _mapping_str(ref, "version")
            label = f"Output {task_id}" if not version else f"Output {task_id}@{version}"
            refs.append(
                HostEvidencePresentationRef(
                    label,
                    artifact_id,
                    ref_kind="exchange_artifact",
                )
            )

    authority_clues = tuple(
        HostEvidencePresentationFact(label, _object_to_text(authority_split.get(key)))
        for label, key in (
            ("Scheduler state", "scheduler_state_authority"),
            ("Scheduler projection", "scheduler_projection_role"),
            ("Local trajectory", "local_work_trajectory_role"),
            ("Local trajectory mutated", "local_work_trajectory_mutated"),
        )
        if key in authority_split
    )

    return HostEvidencePresentationCard(
        id=evidence_id,
        title=f"Host evidence {evidence_id}",
        subtitle=" · ".join(subtitle_parts),
        status=status,
        severity=_host_evidence_card_severity(status),
        timestamp=summary.timestamp,
        runtime_providers=summary.runtime_providers,
        host_surface=host_surface,
        invocation_id=invocation_id,
        requested_by=requested_by,
        stop_reason=summary.stop_reason,
        stop_detail=summary.stop_detail,
        run_count=summary.run_count,
        output_count=len(output_refs),
        permission_review_count=summary.permission_review_count,
        key_facts=key_facts,
        refs=tuple(refs),
        authority_clues=authority_clues,
        metadata={
            "reason": reason,
            "ready_task_ids": list(summary.ready_task_ids),
            "blocked_task_ids": list(summary.blocked_task_ids),
            "failed_task_ids": list(summary.failed_task_ids),
            "permission_review_task_ids": list(summary.permission_review_task_ids),
            "evidence_metadata": dict(summary.metadata),
        },
    )


def _scheduler_loop_evidence_presentation_card(
    summary: SchedulerLoopEvidenceSummary,
) -> HostEvidencePresentationCard:
    status = _scheduler_loop_evidence_card_status(summary)
    authority_split = dict(summary.authority_split)
    final_queue = dict(summary.final_queue_summary)
    ready_task_ids = tuple(str(item) for item in final_queue.get("ready_task_ids", ()) or ())
    blocked_task_ids = tuple(str(item) for item in final_queue.get("blocked_task_ids", ()) or ())
    failed_task_ids = tuple(str(item) for item in final_queue.get("failed_task_ids", ()) or ())
    completed_task_ids = tuple(str(item) for item in final_queue.get("completed_task_ids", ()) or ())
    subtitle_parts = [
        part for part in (
            "scheduler-loop",
            summary.stop_reason,
            f"{summary.total_run_count} run(s)",
        )
        if part
    ]
    key_facts = (
        HostEvidencePresentationFact("Stop reason", summary.stop_reason),
        HostEvidencePresentationFact("Ticks", str(summary.tick_count)),
        HostEvidencePresentationFact("Runs", str(summary.total_run_count)),
        HostEvidencePresentationFact("Scheduler events", str(summary.scheduler_event_count)),
        HostEvidencePresentationFact("Completed tasks", str(len(completed_task_ids))),
        HostEvidencePresentationFact("Ready tasks", str(len(ready_task_ids))),
        HostEvidencePresentationFact("Blocked tasks", str(len(blocked_task_ids))),
        HostEvidencePresentationFact("Failed tasks", str(len(failed_task_ids))),
    )
    refs = (
        HostEvidencePresentationRef("Evidence", str(summary.evidence_path)),
        HostEvidencePresentationRef("Snapshot", summary.snapshot_path),
        HostEvidencePresentationRef("Event log", summary.event_log_path),
    )
    authority_clues = tuple(
        HostEvidencePresentationFact(label, _object_to_text(authority_split.get(key)))
        for label, key in (
            ("Scheduler state", "scheduler_state_authority"),
            ("Scheduler state mutated", "scheduler_state_mutated"),
            ("Provider executed", "provider_executed"),
            ("Scheduler projection refreshed", "scheduler_projection_refreshed"),
            ("Local trajectory mutated", "local_work_trajectory_mutated"),
        )
        if key in authority_split
    )
    return HostEvidencePresentationCard(
        id=summary.evidence_id,
        title=f"Scheduler loop evidence {summary.evidence_id}",
        subtitle=" · ".join(subtitle_parts),
        status=status,
        severity=_host_evidence_card_severity(status),
        timestamp=summary.timestamp,
        runtime_providers=(summary.runtime_provider,),
        host_surface="scheduler-daemon-loop",
        invocation_id=summary.evidence_id,
        requested_by="operator-or-host",
        stop_reason=summary.stop_reason,
        stop_detail=summary.stop_detail,
        run_count=summary.total_run_count,
        output_count=0,
        permission_review_count=0,
        key_facts=key_facts,
        refs=refs,
        authority_clues=authority_clues,
        metadata={
            "evidence_product_type": summary.product_type,
            "tick_count": summary.tick_count,
            "scheduler_event_count": summary.scheduler_event_count,
            "stop_policy": dict(summary.stop_policy),
            "ready_task_ids": list(ready_task_ids),
            "blocked_task_ids": list(blocked_task_ids),
            "failed_task_ids": list(failed_task_ids),
            "completed_task_ids": list(completed_task_ids),
            "evidence_metadata": dict(summary.metadata),
        },
    )


def _host_evidence_presentation_error_row(
    error: HostEvidenceReadError,
    *,
    index: int,
) -> HostEvidencePresentationErrorRow:
    return HostEvidencePresentationErrorRow(
        id=f"host-evidence-error:{index}",
        status="read-error",
        severity="error",
        evidence_path=str(error.evidence_path),
        error_kind=error.error_kind,
        message=error.message,
    )


def _host_evidence_card_status(
    summary: HostSchedulerRunEvidenceSummary,
) -> HostEvidenceCardStatus:
    if summary.failed_task_ids or summary.stop_reason in {"task_failed", "completed_with_failures"}:
        return "failed"
    if summary.permission_review_count > 0:
        return "permission-review"
    if (
        summary.stop_reason in {"max_runs_reached", "blocked_tasks"}
        or summary.blocked_task_ids
    ):
        return "partial"
    if summary.stop_reason == "no_ready_tasks":
        return "completed"
    return "unknown"


def _scheduler_loop_evidence_card_status(
    summary: SchedulerLoopEvidenceSummary,
) -> HostEvidenceCardStatus:
    final_queue = dict(summary.final_queue_summary)
    failed_task_ids = tuple(final_queue.get("failed_task_ids", ()) or ())
    blocked_task_ids = tuple(final_queue.get("blocked_task_ids", ()) or ())
    if failed_task_ids or summary.stop_reason == "runtime_failure_limit_reached":
        return "failed"
    if blocked_task_ids or summary.stop_reason in {"max_ticks_reached", "blocked_tasks"}:
        return "partial"
    if summary.stop_reason == "no_ready_tasks":
        return "completed"
    if summary.stop_reason == "cancelled":
        return "partial"
    return "unknown"


def _host_evidence_card_severity(
    status: HostEvidenceCardStatus,
) -> HostEvidenceSeverity:
    if status == "failed":
        return "error"
    if status in {"permission-review", "partial", "unknown"}:
        return "warning"
    return "info"


def _host_evidence_bundle_status(
    cards: tuple[HostEvidencePresentationCard, ...],
    error_rows: tuple[HostEvidencePresentationErrorRow, ...],
) -> HostEvidenceBundleStatus:
    if not cards and not error_rows:
        return "empty"
    if any(card.status == "failed" for card in cards):
        return "failed"
    if error_rows or any(card.status in {"partial", "permission-review", "unknown"} for card in cards):
        return "degraded"
    return "ok"


def _mapping_str(mapping: dict[str, object] | HostSchedulerRunEvidenceSummary | object, key: str) -> str:
    if isinstance(mapping, dict):
        value = mapping.get(key)
    else:
        value = None
    return value if isinstance(value, str) else ""


def _object_to_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def read_host_evidence_bundle(
    project_root: str | Path,
    *,
    evidence_dir: str | Path | None = None,
    isolate_errors: bool = True,
) -> HostEvidenceBundle:
    """Read compact host-run evidence summaries without executing providers."""

    root = Path(project_root)
    target_dir = host_scheduler_evidence_dir(root) if evidence_dir is None else Path(evidence_dir)
    if not isolate_errors:
        return HostEvidenceBundle(
            project_root=root,
            evidence_dir=target_dir,
            summaries=_read_host_evidence_summaries_strict(target_dir),
        )
    summaries, errors = _read_host_evidence_bundle_isolated(target_dir)
    return HostEvidenceBundle(
        project_root=root,
        evidence_dir=target_dir,
        summaries=summaries,
        errors=errors,
    )


def _read_host_evidence_bundle_isolated(
    evidence_dir: Path,
) -> tuple[tuple[HostEvidenceSummary, ...], tuple[HostEvidenceReadError, ...]]:
    if not evidence_dir.exists():
        return (), ()
    if not evidence_dir.is_dir():
        return (), (
            HostEvidenceReadError(
                evidence_path=evidence_dir,
                error_kind="not_directory",
                message=f"host scheduler evidence path is not a directory: {evidence_dir}",
            ),
        )

    summaries: list[HostEvidenceSummary] = []
    errors: list[HostEvidenceReadError] = []
    for path in sorted(evidence_dir.glob("*.json")):
        try:
            summaries.append(_read_host_evidence_summary(path))
        except FileNotFoundError as exc:
            errors.append(_host_evidence_read_error(path, "not_found", exc))
        except ValueError as exc:
            errors.append(_host_evidence_read_error(path, "invalid_evidence", exc))
        except OSError as exc:
            errors.append(_host_evidence_read_error(path, "read_failed", exc))
    return tuple(summaries), tuple(errors)


def _read_host_evidence_summaries_strict(
    evidence_dir: Path,
) -> tuple[HostEvidenceSummary, ...]:
    if not evidence_dir.exists():
        return ()
    if not evidence_dir.is_dir():
        raise ValueError(f"host scheduler evidence path is not a directory: {evidence_dir}")
    return tuple(_read_host_evidence_summary(path) for path in sorted(evidence_dir.glob("*.json")))


def _read_host_evidence_summary(path: Path) -> HostEvidenceSummary:
    product_type = _peek_evidence_product_type(path)
    if product_type == HOST_SCHEDULER_RUN_EVIDENCE_PRODUCT_TYPE:
        return read_host_scheduler_run_evidence_summary(path)
    if product_type == SCHEDULER_LOOP_EVIDENCE_PRODUCT_TYPE:
        return read_scheduler_loop_evidence_summary(path)
    raise ValueError(
        "host scheduler evidence artifact has unsupported product_type "
        f"{product_type!r}: {path}"
    )


def _peek_evidence_product_type(path: Path) -> str:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise FileNotFoundError(f"host scheduler evidence artifact not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"host scheduler evidence artifact is not valid JSON: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"host scheduler evidence artifact must be a JSON object: {path}")
    product_type = payload.get("product_type")
    if not isinstance(product_type, str):
        raise ValueError(f"host scheduler evidence artifact field 'product_type' must be a string: {path}")
    return product_type


def _host_evidence_read_error(
    path: Path,
    error_kind: str,
    exc: BaseException,
) -> HostEvidenceReadError:
    return HostEvidenceReadError(
        evidence_path=path,
        error_kind=error_kind,
        message=str(exc),
    )
