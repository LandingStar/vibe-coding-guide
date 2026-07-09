"""Explicit-source timeline projection for readback envelopes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from .readback_inspection import ReadbackInspectionRequest, inspect_readback

ReadbackTimelineOrderingConfidence = Literal[
    "timestamp",
    "source_order",
    "unknown_timestamp",
]


@dataclass(frozen=True, slots=True)
class ReadbackTimelineSource:
    """One explicit source for timeline projection."""

    kind: str
    path: str | Path = ""
    artifact_id: str = ""
    version: str = ""
    source_kind: str = ""
    latest_limit: int = 20
    actor: str = "readback-timeline"
    timestamp: str = ""
    label: str = ""

    def to_inspection_request(self, project_root: str | Path) -> ReadbackInspectionRequest:
        """Convert this explicit source into a unified readback inspection request."""

        return ReadbackInspectionRequest(
            project_root=project_root,
            kind=self.kind,
            path=self.path,
            artifact_id=self.artifact_id,
            version=self.version,
            source_kind=self.source_kind,
            latest_limit=self.latest_limit,
            actor=self.actor,
            timestamp=self.timestamp,
        )

    def to_json_dict(self) -> dict[str, object]:
        return {
            "kind": self.kind,
            "path": str(self.path),
            "artifact_id": self.artifact_id,
            "version": self.version,
            "source_kind": self.source_kind,
            "latest_limit": self.latest_limit,
            "actor": self.actor,
            "timestamp": self.timestamp,
            "label": self.label,
        }


@dataclass(frozen=True, slots=True)
class ReadbackTimelineRow:
    """Compact timeline row derived from one readback envelope."""

    row_id: str
    source_index: int
    source_kind: str
    source_path: str
    source_label: str
    record_index: int
    record_id: str
    record_kind: str
    timestamp: str
    ordering_confidence: ReadbackTimelineOrderingConfidence
    actor: str = ""
    action: str = ""
    status: str = ""
    summary: str = ""
    reason: str = ""
    next_hint: str = ""
    run_id: str = ""
    correlation_id: str = ""
    subject_refs: tuple[dict[str, object], ...] = ()
    input_refs: tuple[dict[str, object], ...] = ()
    output_refs: tuple[dict[str, object], ...] = ()
    evidence_refs: tuple[dict[str, object], ...] = ()
    related_record_ids: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        return {
            "row_id": self.row_id,
            "source_index": self.source_index,
            "source_kind": self.source_kind,
            "source_path": self.source_path,
            "source_label": self.source_label,
            "record_index": self.record_index,
            "record_id": self.record_id,
            "record_kind": self.record_kind,
            "timestamp": self.timestamp,
            "ordering_confidence": self.ordering_confidence,
            "actor": self.actor,
            "action": self.action,
            "status": self.status,
            "summary": self.summary,
            "reason": self.reason,
            "next_hint": self.next_hint,
            "run_id": self.run_id,
            "correlation_id": self.correlation_id,
            "subject_refs": [dict(ref) for ref in self.subject_refs],
            "input_refs": [dict(ref) for ref in self.input_refs],
            "output_refs": [dict(ref) for ref in self.output_refs],
            "evidence_refs": [dict(ref) for ref in self.evidence_refs],
            "related_record_ids": list(self.related_record_ids),
        }


@dataclass(frozen=True, slots=True)
class ReadbackTimelineInspectionRequest:
    """Request for explicit-source readback timeline projection."""

    project_root: str | Path
    sources: tuple[ReadbackTimelineSource, ...]


@dataclass(frozen=True, slots=True)
class ReadbackTimelineInspectionResult:
    """Result of explicit-source readback timeline projection."""

    ok: bool
    project_root: Path
    source_count: int = 0
    successful_source_count: int = 0
    failed_source_count: int = 0
    record_count: int = 0
    rows: tuple[ReadbackTimelineRow, ...] = ()
    source_results: tuple[dict[str, object], ...] = ()
    errors: tuple[str, ...] = ()

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "project_root": str(self.project_root),
            "source_count": self.source_count,
            "successful_source_count": self.successful_source_count,
            "failed_source_count": self.failed_source_count,
            "record_count": self.record_count,
            "rows": [row.to_json_dict() for row in self.rows],
            "source_results": [dict(result) for result in self.source_results],
            "errors": list(self.errors),
            "authority_split": {
                "read_model_only": True,
                "worker_report_consumed": False,
                "validation_or_doctor_ran": False,
                "provider_executed": False,
                "browser_executed": False,
                "screenshot_captured": False,
                "scheduler_state_mutated": False,
                "exchange_store_mutated": False,
                "exchange_lifecycle_mutated": False,
                "evidence_mutated": False,
                "config_mutated": False,
                "local_work_trajectory_mutated": False,
                "persistent_manifest_written": False,
                "workspace_scanned": False,
            },
        }


def inspect_readback_timeline(
    request: ReadbackTimelineInspectionRequest,
) -> ReadbackTimelineInspectionResult:
    """Project explicit readback sources into one read-only timeline."""

    root = Path(request.project_root).resolve()
    if not request.sources:
        return ReadbackTimelineInspectionResult(
            ok=False,
            project_root=root,
            errors=("at least one explicit readback timeline source is required",),
        )

    source_results: list[dict[str, object]] = []
    rows: list[tuple[datetime | None, int, int, ReadbackTimelineRow]] = []
    errors: list[str] = []
    successful = 0
    failed = 0

    for source_index, source in enumerate(request.sources):
        result = inspect_readback(source.to_inspection_request(root))
        result_payload = result.to_json_dict()
        result_payload["source_index"] = source_index
        result_payload["source_label"] = source.label
        source_results.append(result_payload)
        if result.ok:
            successful += 1
        else:
            failed += 1
            errors.extend(
                f"source[{source_index}] {message}" for message in result.errors
            )

        for record_index, envelope in enumerate(result.envelopes):
            row = _row_from_envelope(
                envelope,
                source=source,
                source_index=source_index,
                source_path="" if result.source_path is None else str(result.source_path),
                record_index=record_index,
            )
            parsed = _parse_timestamp(row.timestamp)
            rows.append((parsed, source_index, record_index, row))

    ordered_rows = tuple(row for _parsed, _source_index, _record_index, row in sorted(rows, key=_row_sort_key))
    return ReadbackTimelineInspectionResult(
        ok=successful > 0,
        project_root=root,
        source_count=len(request.sources),
        successful_source_count=successful,
        failed_source_count=failed,
        record_count=len(ordered_rows),
        rows=ordered_rows,
        source_results=tuple(source_results),
        errors=tuple(errors),
    )


def _row_from_envelope(
    envelope: object,
    *,
    source: ReadbackTimelineSource,
    source_index: int,
    source_path: str,
    record_index: int,
) -> ReadbackTimelineRow:
    payload = dict(envelope) if isinstance(envelope, dict) else {}
    record_id = _text(payload, "record_id") or f"source-{source_index}:record-{record_index}"
    record_kind = _text(payload, "record_kind") or "unknown"
    timestamp = _text(payload, "timestamp")
    parsed = _parse_timestamp(timestamp)
    if parsed is not None:
        confidence: ReadbackTimelineOrderingConfidence = "timestamp"
    elif timestamp:
        confidence = "unknown_timestamp"
    else:
        confidence = "source_order"
    return ReadbackTimelineRow(
        row_id=f"timeline:{source_index}:{record_index}:{record_id}",
        source_index=source_index,
        source_kind=str(source.kind),
        source_path=source_path,
        source_label=source.label,
        record_index=record_index,
        record_id=record_id,
        record_kind=record_kind,
        timestamp=timestamp,
        ordering_confidence=confidence,
        actor=_text(payload, "actor"),
        action=_text(payload, "action"),
        status=_text(payload, "status"),
        summary=_text(payload, "summary"),
        reason=_text(payload, "reason"),
        next_hint=_text(payload, "next_hint"),
        run_id=_text(payload, "run_id"),
        correlation_id=_text(payload, "correlation_id"),
        subject_refs=_refs(payload.get("subject_refs")),
        input_refs=_refs(payload.get("input_refs")),
        output_refs=_refs(payload.get("output_refs")),
        evidence_refs=_refs(payload.get("evidence_refs")),
        related_record_ids=_strings(payload.get("related_record_ids")),
    )


def _row_sort_key(
    item: tuple[datetime | None, int, int, ReadbackTimelineRow],
) -> tuple[int, datetime, int, int]:
    parsed, source_index, record_index, _row = item
    if parsed is None:
        return (1, datetime.max.replace(tzinfo=UTC), source_index, record_index)
    return (0, parsed, source_index, record_index)


def _parse_timestamp(value: str) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _text(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    return "" if value is None else str(value)


def _refs(value: object) -> tuple[dict[str, object], ...]:
    if not isinstance(value, list | tuple):
        return ()
    refs: list[dict[str, object]] = []
    for item in value:
        if isinstance(item, dict):
            refs.append(dict(item))
    return tuple(refs)


def _strings(value: object) -> tuple[str, ...]:
    if not isinstance(value, list | tuple):
        return ()
    return tuple(str(item) for item in value)


__all__ = [
    "ReadbackTimelineInspectionRequest",
    "ReadbackTimelineInspectionResult",
    "ReadbackTimelineOrderingConfidence",
    "ReadbackTimelineRow",
    "ReadbackTimelineSource",
    "inspect_readback_timeline",
]
