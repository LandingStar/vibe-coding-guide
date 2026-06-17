"""Host-runtime scheduler dogfood evidence products."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

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


def default_host_scheduler_run_evidence_path(
    project_root: str | Path,
    evidence_id: str,
) -> Path:
    """Return the default review artifact path for one host scheduler run."""

    safe_id = "".join(character if character.isalnum() or character in {"-", "_"} else "-" for character in evidence_id)
    safe_id = safe_id.strip("-") or "host-scheduler-run"
    return Path(project_root) / ".codex/scheduler/evidence" / f"{safe_id}.json"


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
