"""Host-runtime scheduler dogfood evidence products."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .artifact_paths import dbc_artifact_path
from .scheduler_host_runner import HostSchedulerRunResult

HOST_SCHEDULER_RUN_EVIDENCE_PRODUCT_TYPE = "host_scheduler_run_evidence"
HOST_SCHEDULER_RUN_EVIDENCE_SCHEMA_VERSION = "1"


@dataclass(frozen=True, slots=True)
class HostSchedulerRunEvidence:
    """Compact review artifact for one host-authorized scheduler dogfood run."""

    evidence_id: str
    timestamp: str
    host_result: HostSchedulerRunResult
    evidence_path: str | Path | None = None
    product_type: str = HOST_SCHEDULER_RUN_EVIDENCE_PRODUCT_TYPE
    schema_version: str = HOST_SCHEDULER_RUN_EVIDENCE_SCHEMA_VERSION
    metadata: Mapping[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-serializable evidence artifact."""

        host_payload = self.host_result.to_json_dict()
        authority_split = host_payload.get("authority_split", {})
        history_summary = host_payload.get("history_summary", {})
        return {
            "product_type": self.product_type,
            "schema_version": self.schema_version,
            "evidence_id": self.evidence_id,
            "timestamp": self.timestamp,
            "snapshot_path": host_payload["snapshot_path"],
            "event_log_path": host_payload["event_log_path"],
            "merge_gate_event_log_path": host_payload["merge_gate_event_log_path"],
            "scheduler_projection_path": host_payload["scheduler_projection_path"],
            "runtime_providers": host_payload["runtime_registry_providers"],
            "host_invocation": {
                "surface": host_payload["runtime_host_surface"],
                "invocation_id": host_payload["host_invocation_id"],
                "requested_by": host_payload["host_requested_by"],
                "reason": self._host_invocation_reason(),
            },
            "run_count": host_payload["run_count"],
            "stop_reason": host_payload["stop_reason"],
            "stop_detail": host_payload["stop_detail"],
            "ready_task_ids": host_payload["ready_task_ids"],
            "blocked_task_ids": host_payload["blocked_task_ids"],
            "failed_task_ids": host_payload["failed_task_ids"],
            "permission_review_task_ids": host_payload["permission_review_task_ids"],
            "permission_review_count": host_payload["permission_review_count"],
            "output_artifact_refs": host_payload["output_artifact_refs"],
            "history_summary": history_summary,
            "authority_split": authority_split,
            "host_result": host_payload,
            "metadata": dict(self.metadata),
        }

    def to_json(self) -> str:
        """Serialize this evidence artifact to stable JSON."""

        return json.dumps(self.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    def _host_invocation_reason(self) -> str:
        invocation = self.host_result.request.runtime_config.host_invocation
        return "" if invocation is None else invocation.reason


@dataclass(frozen=True, slots=True)
class HostSchedulerRunEvidenceWriteResult:
    """Result of writing host-run evidence to disk."""

    evidence: HostSchedulerRunEvidence
    evidence_path: Path

    def to_json_dict(self) -> dict[str, object]:
        payload = self.evidence.to_json_dict()
        payload["evidence_path"] = str(self.evidence_path)
        return payload


@dataclass(frozen=True, slots=True)
class HostSchedulerRunEvidenceSummary:
    """Read-only compact projection of one host-run evidence JSON artifact."""

    evidence_path: Path
    evidence_id: str
    timestamp: str
    runtime_providers: tuple[str, ...]
    host_invocation: Mapping[str, object]
    run_count: int
    stop_reason: str
    stop_detail: str
    ready_task_ids: tuple[str, ...]
    blocked_task_ids: tuple[str, ...]
    failed_task_ids: tuple[str, ...]
    permission_review_task_ids: tuple[str, ...]
    permission_review_count: int
    output_artifact_refs: tuple[Mapping[str, object], ...]
    snapshot_path: str
    event_log_path: str
    scheduler_projection_path: str
    authority_split: Mapping[str, object]
    history_summary: Mapping[str, object]
    metadata: Mapping[str, object] = field(default_factory=dict)
    product_type: str = HOST_SCHEDULER_RUN_EVIDENCE_PRODUCT_TYPE
    schema_version: str = HOST_SCHEDULER_RUN_EVIDENCE_SCHEMA_VERSION

    def to_json_dict(self) -> dict[str, object]:
        """Return a UI-safe compact summary without embedded host_result."""

        return {
            "product_type": self.product_type,
            "schema_version": self.schema_version,
            "evidence_path": str(self.evidence_path),
            "evidence_id": self.evidence_id,
            "timestamp": self.timestamp,
            "runtime_providers": list(self.runtime_providers),
            "host_invocation": dict(self.host_invocation),
            "run_count": self.run_count,
            "stop_reason": self.stop_reason,
            "stop_detail": self.stop_detail,
            "ready_task_ids": list(self.ready_task_ids),
            "blocked_task_ids": list(self.blocked_task_ids),
            "failed_task_ids": list(self.failed_task_ids),
            "permission_review_task_ids": list(self.permission_review_task_ids),
            "permission_review_count": self.permission_review_count,
            "output_artifact_refs": [dict(ref) for ref in self.output_artifact_refs],
            "snapshot_path": self.snapshot_path,
            "event_log_path": self.event_log_path,
            "scheduler_projection_path": self.scheduler_projection_path,
            "authority_split": dict(self.authority_split),
            "history_summary": dict(self.history_summary),
            "metadata": dict(self.metadata),
        }


def default_host_scheduler_run_evidence_path(
    project_root: str | Path,
    evidence_id: str,
) -> Path:
    """Return the default review artifact path for one host scheduler run."""

    safe_id = "".join(character if character.isalnum() or character in {"-", "_"} else "-" for character in evidence_id)
    safe_id = safe_id.strip("-") or "host-scheduler-run"
    return Path(project_root) / dbc_artifact_path("scheduler", "evidence", f"{safe_id}.json")


def build_host_scheduler_run_evidence(
    host_result: HostSchedulerRunResult,
    *,
    evidence_id: str,
    timestamp: str = "",
    evidence_path: str | Path | None = None,
    metadata: Mapping[str, object] | None = None,
) -> HostSchedulerRunEvidence:
    """Build a compact evidence artifact from a host scheduler result."""

    return HostSchedulerRunEvidence(
        evidence_id=evidence_id,
        timestamp=timestamp or host_result.request.timestamp or host_result.request.created_at,
        evidence_path=evidence_path,
        host_result=host_result,
        metadata={} if metadata is None else metadata,
    )


def read_host_scheduler_run_evidence_summary(
    evidence_path: str | Path,
) -> HostSchedulerRunEvidenceSummary:
    """Read a compact host-run evidence summary from a persisted JSON artifact."""

    path = Path(evidence_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise FileNotFoundError(f"host scheduler evidence artifact not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"host scheduler evidence artifact is not valid JSON: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"host scheduler evidence artifact must be a JSON object: {path}")
    return _host_scheduler_run_evidence_summary_from_payload(path, payload)


def read_host_scheduler_run_evidence_summaries(
    evidence_dir: str | Path,
) -> tuple[HostSchedulerRunEvidenceSummary, ...]:
    """Read all valid host-run evidence summaries under an evidence directory."""

    root = Path(evidence_dir)
    if not root.exists():
        return ()
    if not root.is_dir():
        raise ValueError(f"host scheduler evidence path is not a directory: {root}")
    summaries = []
    for path in sorted(root.glob("*.json")):
        summaries.append(read_host_scheduler_run_evidence_summary(path))
    return tuple(summaries)


def write_host_scheduler_run_evidence(
    evidence: HostSchedulerRunEvidence,
    evidence_path: str | Path,
) -> HostSchedulerRunEvidenceWriteResult:
    """Write host scheduler run evidence JSON without mutating scheduler state."""

    target = Path(evidence_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(evidence.to_json(), encoding="utf-8")
    written = HostSchedulerRunEvidence(
        evidence_id=evidence.evidence_id,
        timestamp=evidence.timestamp,
        host_result=evidence.host_result,
        evidence_path=target,
        product_type=evidence.product_type,
        schema_version=evidence.schema_version,
        metadata=evidence.metadata,
    )
    return HostSchedulerRunEvidenceWriteResult(evidence=written, evidence_path=target)


def _host_scheduler_run_evidence_summary_from_payload(
    path: Path,
    payload: Mapping[str, Any],
) -> HostSchedulerRunEvidenceSummary:
    product_type = _required_str(payload, "product_type", path)
    if product_type != HOST_SCHEDULER_RUN_EVIDENCE_PRODUCT_TYPE:
        raise ValueError(
            "host scheduler evidence artifact has product_type "
            f"{product_type!r}; expected {HOST_SCHEDULER_RUN_EVIDENCE_PRODUCT_TYPE!r}: {path}"
        )
    schema_version = _required_str(payload, "schema_version", path)
    if schema_version != HOST_SCHEDULER_RUN_EVIDENCE_SCHEMA_VERSION:
        raise ValueError(
            "host scheduler evidence artifact has schema_version "
            f"{schema_version!r}; expected {HOST_SCHEDULER_RUN_EVIDENCE_SCHEMA_VERSION!r}: {path}"
        )
    return HostSchedulerRunEvidenceSummary(
        evidence_path=path,
        product_type=product_type,
        schema_version=schema_version,
        evidence_id=_required_str(payload, "evidence_id", path),
        timestamp=_required_str(payload, "timestamp", path),
        runtime_providers=_required_str_tuple(payload, "runtime_providers", path),
        host_invocation=_required_mapping(payload, "host_invocation", path),
        run_count=_required_int(payload, "run_count", path),
        stop_reason=_required_str(payload, "stop_reason", path),
        stop_detail=_required_str(payload, "stop_detail", path),
        ready_task_ids=_required_str_tuple(payload, "ready_task_ids", path),
        blocked_task_ids=_required_str_tuple(payload, "blocked_task_ids", path),
        failed_task_ids=_required_str_tuple(payload, "failed_task_ids", path),
        permission_review_task_ids=_required_str_tuple(payload, "permission_review_task_ids", path),
        permission_review_count=_required_int(payload, "permission_review_count", path),
        output_artifact_refs=_required_mapping_tuple(payload, "output_artifact_refs", path),
        snapshot_path=_required_str(payload, "snapshot_path", path),
        event_log_path=_required_str(payload, "event_log_path", path),
        scheduler_projection_path=_required_str(payload, "scheduler_projection_path", path),
        authority_split=_required_mapping(payload, "authority_split", path),
        history_summary=_required_mapping(payload, "history_summary", path),
        metadata=_required_mapping(payload, "metadata", path),
    )


def _required_str(payload: Mapping[str, Any], key: str, path: Path) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(f"host scheduler evidence artifact field {key!r} must be a string: {path}")
    return value


def _required_int(payload: Mapping[str, Any], key: str, path: Path) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise ValueError(f"host scheduler evidence artifact field {key!r} must be an integer: {path}")
    return value


def _required_mapping(payload: Mapping[str, Any], key: str, path: Path) -> Mapping[str, object]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"host scheduler evidence artifact field {key!r} must be an object: {path}")
    return dict(value)


def _required_str_tuple(payload: Mapping[str, Any], key: str, path: Path) -> tuple[str, ...]:
    value = payload.get(key)
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"host scheduler evidence artifact field {key!r} must be a string list: {path}")
    return tuple(value)


def _required_mapping_tuple(payload: Mapping[str, Any], key: str, path: Path) -> tuple[Mapping[str, object], ...]:
    value = payload.get(key)
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError(f"host scheduler evidence artifact field {key!r} must be an object list: {path}")
    return tuple(dict(item) for item in value)
