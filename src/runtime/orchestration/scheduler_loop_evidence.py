"""Scheduler daemon loop evidence products."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .scheduler_daemon import SchedulerDaemonLoopResult

SCHEDULER_LOOP_EVIDENCE_PRODUCT_TYPE = "scheduler_loop_evidence"
SCHEDULER_LOOP_EVIDENCE_SCHEMA_VERSION = "1"


@dataclass(frozen=True, slots=True)
class SchedulerLoopEvidence:
    """Durable review artifact for one bounded scheduler daemon loop."""

    evidence_id: str
    timestamp: str
    loop_result: SchedulerDaemonLoopResult
    evidence_path: str | Path | None = None
    product_type: str = SCHEDULER_LOOP_EVIDENCE_PRODUCT_TYPE
    schema_version: str = SCHEDULER_LOOP_EVIDENCE_SCHEMA_VERSION
    metadata: Mapping[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-serializable scheduler loop evidence artifact."""

        loop_payload = self.loop_result.to_json_dict()
        stop_policy = self.loop_result.request.stop_policy
        return {
            "product_type": self.product_type,
            "schema_version": self.schema_version,
            "evidence_id": self.evidence_id,
            "timestamp": self.timestamp,
            "snapshot_path": loop_payload["snapshot_path"],
            "event_log_path": loop_payload["event_log_path"],
            "runtime_provider": loop_payload["runtime_provider"],
            "stop_policy": {
                "max_ticks": stop_policy.max_ticks,
                "max_runs_per_tick": stop_policy.max_runs_per_tick,
                "max_runtime_failures": stop_policy.max_runtime_failures,
                "cancelled": stop_policy.cancelled,
            },
            "tick_count": loop_payload["tick_count"],
            "total_run_count": loop_payload["total_run_count"],
            "stop_reason": loop_payload["stop_reason"],
            "stop_detail": loop_payload["stop_detail"],
            "scheduler_event_count": loop_payload["scheduler_event_count"],
            "iterations": loop_payload["iterations"],
            "final_queue_summary": loop_payload["final_queue_summary"],
            "authority_split": loop_payload["authority_split"],
            "loop_result": loop_payload,
            "metadata": dict(self.metadata),
        }

    def to_json(self) -> str:
        """Serialize this evidence artifact to stable JSON."""

        return json.dumps(self.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


@dataclass(frozen=True, slots=True)
class SchedulerLoopEvidenceWriteResult:
    """Result of writing scheduler loop evidence to disk."""

    evidence: SchedulerLoopEvidence
    evidence_path: Path

    def to_json_dict(self) -> dict[str, object]:
        payload = self.evidence.to_json_dict()
        payload["evidence_path"] = str(self.evidence_path)
        return payload


@dataclass(frozen=True, slots=True)
class SchedulerLoopEvidenceSummary:
    """Read-only compact projection of one scheduler-loop evidence JSON artifact."""

    evidence_path: Path
    evidence_id: str
    timestamp: str
    runtime_provider: str
    stop_policy: Mapping[str, object]
    tick_count: int
    total_run_count: int
    stop_reason: str
    stop_detail: str
    scheduler_event_count: int
    iterations: tuple[Mapping[str, object], ...]
    final_queue_summary: Mapping[str, object]
    snapshot_path: str
    event_log_path: str
    authority_split: Mapping[str, object]
    metadata: Mapping[str, object] = field(default_factory=dict)
    product_type: str = SCHEDULER_LOOP_EVIDENCE_PRODUCT_TYPE
    schema_version: str = SCHEDULER_LOOP_EVIDENCE_SCHEMA_VERSION

    def to_json_dict(self) -> dict[str, object]:
        """Return a UI-safe compact summary without embedded loop_result."""

        return {
            "product_type": self.product_type,
            "schema_version": self.schema_version,
            "evidence_path": str(self.evidence_path),
            "evidence_id": self.evidence_id,
            "timestamp": self.timestamp,
            "runtime_provider": self.runtime_provider,
            "stop_policy": dict(self.stop_policy),
            "tick_count": self.tick_count,
            "total_run_count": self.total_run_count,
            "stop_reason": self.stop_reason,
            "stop_detail": self.stop_detail,
            "scheduler_event_count": self.scheduler_event_count,
            "iterations": [dict(item) for item in self.iterations],
            "final_queue_summary": dict(self.final_queue_summary),
            "snapshot_path": self.snapshot_path,
            "event_log_path": self.event_log_path,
            "authority_split": dict(self.authority_split),
            "metadata": dict(self.metadata),
        }


def default_scheduler_loop_evidence_path(
    project_root: str | Path,
    evidence_id: str,
) -> Path:
    """Return the default review artifact path for one scheduler loop run."""

    safe_id = "".join(character if character.isalnum() or character in {"-", "_"} else "-" for character in evidence_id)
    safe_id = safe_id.strip("-") or "scheduler-loop"
    return Path(project_root) / ".codex/scheduler/evidence" / f"{safe_id}.json"


def build_scheduler_loop_evidence(
    loop_result: SchedulerDaemonLoopResult,
    *,
    evidence_id: str,
    timestamp: str = "",
    evidence_path: str | Path | None = None,
    metadata: Mapping[str, object] | None = None,
) -> SchedulerLoopEvidence:
    """Build a durable evidence artifact from a scheduler daemon loop result."""

    return SchedulerLoopEvidence(
        evidence_id=evidence_id,
        timestamp=timestamp or loop_result.request.timestamp,
        evidence_path=evidence_path,
        loop_result=loop_result,
        metadata={} if metadata is None else metadata,
    )


def read_scheduler_loop_evidence_summary(
    evidence_path: str | Path,
) -> SchedulerLoopEvidenceSummary:
    """Read a compact scheduler-loop evidence summary from JSON."""

    path = Path(evidence_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise FileNotFoundError(f"scheduler loop evidence artifact not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"scheduler loop evidence artifact is not valid JSON: {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"scheduler loop evidence artifact must be a JSON object: {path}")
    return _scheduler_loop_evidence_summary_from_payload(path, payload)


def write_scheduler_loop_evidence(
    evidence: SchedulerLoopEvidence,
    evidence_path: str | Path,
) -> SchedulerLoopEvidenceWriteResult:
    """Write scheduler loop evidence JSON without mutating scheduler state."""

    target = Path(evidence_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(evidence.to_json(), encoding="utf-8")
    written = SchedulerLoopEvidence(
        evidence_id=evidence.evidence_id,
        timestamp=evidence.timestamp,
        loop_result=evidence.loop_result,
        evidence_path=target,
        product_type=evidence.product_type,
        schema_version=evidence.schema_version,
        metadata=evidence.metadata,
    )
    return SchedulerLoopEvidenceWriteResult(evidence=written, evidence_path=target)


def _scheduler_loop_evidence_summary_from_payload(
    path: Path,
    payload: Mapping[str, Any],
) -> SchedulerLoopEvidenceSummary:
    product_type = _required_str(payload, "product_type", path)
    if product_type != SCHEDULER_LOOP_EVIDENCE_PRODUCT_TYPE:
        raise ValueError(
            "scheduler loop evidence artifact has product_type "
            f"{product_type!r}; expected {SCHEDULER_LOOP_EVIDENCE_PRODUCT_TYPE!r}: {path}"
        )
    schema_version = _required_str(payload, "schema_version", path)
    if schema_version != SCHEDULER_LOOP_EVIDENCE_SCHEMA_VERSION:
        raise ValueError(
            "scheduler loop evidence artifact has schema_version "
            f"{schema_version!r}; expected {SCHEDULER_LOOP_EVIDENCE_SCHEMA_VERSION!r}: {path}"
        )
    return SchedulerLoopEvidenceSummary(
        evidence_path=path,
        product_type=product_type,
        schema_version=schema_version,
        evidence_id=_required_str(payload, "evidence_id", path),
        timestamp=_required_str(payload, "timestamp", path),
        runtime_provider=_required_str(payload, "runtime_provider", path),
        stop_policy=_required_mapping(payload, "stop_policy", path),
        tick_count=_required_int(payload, "tick_count", path),
        total_run_count=_required_int(payload, "total_run_count", path),
        stop_reason=_required_str(payload, "stop_reason", path),
        stop_detail=_required_str(payload, "stop_detail", path),
        scheduler_event_count=_required_int(payload, "scheduler_event_count", path),
        iterations=_required_mapping_tuple(payload, "iterations", path),
        final_queue_summary=_required_mapping(payload, "final_queue_summary", path),
        snapshot_path=_required_str(payload, "snapshot_path", path),
        event_log_path=_required_str(payload, "event_log_path", path),
        authority_split=_required_mapping(payload, "authority_split", path),
        metadata=_required_mapping(payload, "metadata", path),
    )


def _required_str(payload: Mapping[str, Any], key: str, path: Path) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(f"scheduler loop evidence artifact field {key!r} must be a string: {path}")
    return value


def _required_int(payload: Mapping[str, Any], key: str, path: Path) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise ValueError(f"scheduler loop evidence artifact field {key!r} must be an integer: {path}")
    return value


def _required_mapping(payload: Mapping[str, Any], key: str, path: Path) -> Mapping[str, object]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"scheduler loop evidence artifact field {key!r} must be an object: {path}")
    return dict(value)


def _required_mapping_tuple(payload: Mapping[str, Any], key: str, path: Path) -> tuple[Mapping[str, object], ...]:
    value = payload.get(key)
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError(f"scheduler loop evidence artifact field {key!r} must be an object list: {path}")
    return tuple(dict(item) for item in value)

