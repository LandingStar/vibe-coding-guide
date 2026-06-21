"""Durable evidence products for supervisor storage binding readback."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .supervisor_storage_binding import SupervisorAgentStorageBinding

SUPERVISOR_STORAGE_BINDING_EVIDENCE_PRODUCT_TYPE = (
    "supervisor_storage_binding_evidence"
)
SUPERVISOR_STORAGE_BINDING_EVIDENCE_SCHEMA_VERSION = "1"


@dataclass(frozen=True, slots=True)
class SupervisorStorageBindingEvidence:
    """Durable evidence artifact for one supervisor storage binding."""

    evidence_id: str
    timestamp: str
    binding: SupervisorAgentStorageBinding
    evidence_path: str | Path | None = None
    product_type: str = SUPERVISOR_STORAGE_BINDING_EVIDENCE_PRODUCT_TYPE
    schema_version: str = SUPERVISOR_STORAGE_BINDING_EVIDENCE_SCHEMA_VERSION
    metadata: Mapping[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-serializable supervisor storage binding evidence artifact."""

        binding_payload = self.binding.to_json_dict()
        authority_split = {
            "binding_authority": "supervisor-agent-storage-binding-product",
            "evidence_authority": "supervisor-storage-binding-evidence",
            "scheduler_state_mutated": False,
            "agent_home_registration_persisted": False,
            "agent_home_directory_created": False,
            "scratch_directories_created": False,
            "scratch_manifest_written": False,
            "cleanup_executed": False,
            "scheduler_projection_refreshed": False,
            "local_work_trajectory_mutated": False,
            "evidence_written": self.evidence_path is not None,
        }
        authority_split.update(dict(binding_payload.get("authority_split", {})))
        authority_split["evidence_written"] = self.evidence_path is not None
        return {
            "product_type": self.product_type,
            "schema_version": self.schema_version,
            "evidence_id": self.evidence_id,
            "timestamp": self.timestamp,
            "binding_id": self.binding.binding_id,
            "supervisor_id": self.binding.supervisor_id,
            "session_id": self.binding.session_id,
            "run_id": self.binding.run_id,
            "host_id": self.binding.host_id,
            "requested_by": self.binding.requested_by,
            "agent_id": self.binding.agent_id,
            "context_session_id": self.binding.context_session_id,
            "scheduler_task_ids": list(self.binding.scheduler_task_ids),
            "scheduler_context_ids": list(self.binding.scheduler_context_ids),
            "scheduler_lane_ids": list(self.binding.scheduler_lane_ids),
            "runtime_session_ids": list(self.binding.runtime_session_ids),
            "home_registration_id": (
                ""
                if self.binding.home_registration is None
                else self.binding.home_registration.registration_id
            ),
            "home_registration_audit_state": (
                ""
                if self.binding.home_registration is None
                else self.binding.home_registration.audit_state
            ),
            "scratch_count": len(self.binding.scratch_spaces),
            "scratch_ids": [scratch.scratch_id for scratch in self.binding.scratch_spaces],
            "source_snapshot_path": self.binding.source_snapshot_path,
            "authority_split": authority_split,
            "binding": binding_payload,
            "metadata": dict(self.metadata),
        }

    def to_json(self) -> str:
        """Serialize this evidence artifact to stable JSON."""

        return json.dumps(self.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


@dataclass(frozen=True, slots=True)
class SupervisorStorageBindingEvidenceWriteResult:
    """Result of writing supervisor storage binding evidence to disk."""

    evidence: SupervisorStorageBindingEvidence
    evidence_path: Path

    def to_json_dict(self) -> dict[str, object]:
        payload = self.evidence.to_json_dict()
        payload["evidence_path"] = str(self.evidence_path)
        return payload


@dataclass(frozen=True, slots=True)
class SupervisorStorageBindingEvidenceSummary:
    """Compact read-only summary of one supervisor storage binding evidence artifact."""

    evidence_path: Path
    evidence_id: str
    timestamp: str
    binding_id: str
    supervisor_id: str
    session_id: str
    run_id: str
    host_id: str
    requested_by: str
    agent_id: str
    context_session_id: str
    scheduler_task_ids: tuple[str, ...]
    scheduler_context_ids: tuple[str, ...]
    scheduler_lane_ids: tuple[str, ...]
    runtime_session_ids: tuple[str, ...]
    home_registration_id: str
    home_registration_audit_state: str
    scratch_count: int
    scratch_ids: tuple[str, ...]
    source_snapshot_path: str
    authority_split: Mapping[str, object]
    metadata: Mapping[str, object] = field(default_factory=dict)
    product_type: str = SUPERVISOR_STORAGE_BINDING_EVIDENCE_PRODUCT_TYPE
    schema_version: str = SUPERVISOR_STORAGE_BINDING_EVIDENCE_SCHEMA_VERSION

    def to_json_dict(self) -> dict[str, object]:
        """Return a compact JSON-safe summary without embedded binding payload."""

        return {
            "product_type": self.product_type,
            "schema_version": self.schema_version,
            "evidence_path": str(self.evidence_path),
            "evidence_id": self.evidence_id,
            "timestamp": self.timestamp,
            "binding_id": self.binding_id,
            "supervisor_id": self.supervisor_id,
            "session_id": self.session_id,
            "run_id": self.run_id,
            "host_id": self.host_id,
            "requested_by": self.requested_by,
            "agent_id": self.agent_id,
            "context_session_id": self.context_session_id,
            "scheduler_task_ids": list(self.scheduler_task_ids),
            "scheduler_context_ids": list(self.scheduler_context_ids),
            "scheduler_lane_ids": list(self.scheduler_lane_ids),
            "runtime_session_ids": list(self.runtime_session_ids),
            "home_registration_id": self.home_registration_id,
            "home_registration_audit_state": self.home_registration_audit_state,
            "scratch_count": self.scratch_count,
            "scratch_ids": list(self.scratch_ids),
            "source_snapshot_path": self.source_snapshot_path,
            "authority_split": dict(self.authority_split),
            "metadata": dict(self.metadata),
        }


def default_supervisor_storage_binding_evidence_path(
    project_root: str | Path,
    evidence_id: str,
) -> Path:
    """Return the default path for supervisor storage binding evidence."""

    safe_id = "".join(
        character if character.isalnum() or character in {"-", "_"} else "-"
        for character in evidence_id
    )
    safe_id = safe_id.strip("-") or "supervisor-storage-binding"
    return Path(project_root) / ".codex/scheduler/evidence" / f"{safe_id}.json"


def build_supervisor_storage_binding_evidence(
    binding: SupervisorAgentStorageBinding,
    *,
    evidence_id: str,
    timestamp: str = "",
    evidence_path: str | Path | None = None,
    metadata: Mapping[str, object] | None = None,
) -> SupervisorStorageBindingEvidence:
    """Build durable evidence from a supervisor storage binding."""

    return SupervisorStorageBindingEvidence(
        evidence_id=evidence_id,
        timestamp=timestamp,
        evidence_path=evidence_path,
        binding=binding,
        metadata={} if metadata is None else metadata,
    )


def write_supervisor_storage_binding_evidence(
    evidence: SupervisorStorageBindingEvidence,
    evidence_path: str | Path,
) -> SupervisorStorageBindingEvidenceWriteResult:
    """Write supervisor storage binding evidence JSON."""

    target = Path(evidence_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    written = SupervisorStorageBindingEvidence(
        evidence_id=evidence.evidence_id,
        timestamp=evidence.timestamp,
        binding=evidence.binding,
        evidence_path=target,
        product_type=evidence.product_type,
        schema_version=evidence.schema_version,
        metadata=evidence.metadata,
    )
    target.write_text(written.to_json(), encoding="utf-8")
    return SupervisorStorageBindingEvidenceWriteResult(
        evidence=written,
        evidence_path=target,
    )


def read_supervisor_storage_binding_evidence_summary(
    evidence_path: str | Path,
) -> SupervisorStorageBindingEvidenceSummary:
    """Read a compact supervisor storage binding evidence summary from JSON."""

    path = Path(evidence_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise FileNotFoundError(
            f"supervisor storage binding evidence artifact not found: {path}"
        ) from None
    except json.JSONDecodeError as exc:
        raise ValueError(
            "supervisor storage binding evidence artifact is not valid JSON: "
            f"{path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError(
            f"supervisor storage binding evidence artifact must be a JSON object: {path}"
        )
    return _supervisor_storage_binding_evidence_summary_from_payload(path, payload)


def _supervisor_storage_binding_evidence_summary_from_payload(
    path: Path,
    payload: Mapping[str, Any],
) -> SupervisorStorageBindingEvidenceSummary:
    product_type = _required_str(payload, "product_type", path)
    if product_type != SUPERVISOR_STORAGE_BINDING_EVIDENCE_PRODUCT_TYPE:
        raise ValueError(
            "supervisor storage binding evidence artifact has product_type "
            f"{product_type!r}; expected "
            f"{SUPERVISOR_STORAGE_BINDING_EVIDENCE_PRODUCT_TYPE!r}: {path}"
        )
    schema_version = _required_str(payload, "schema_version", path)
    if schema_version != SUPERVISOR_STORAGE_BINDING_EVIDENCE_SCHEMA_VERSION:
        raise ValueError(
            "supervisor storage binding evidence artifact has schema_version "
            f"{schema_version!r}; expected "
            f"{SUPERVISOR_STORAGE_BINDING_EVIDENCE_SCHEMA_VERSION!r}: {path}"
        )
    return SupervisorStorageBindingEvidenceSummary(
        evidence_path=path,
        product_type=product_type,
        schema_version=schema_version,
        evidence_id=_required_str(payload, "evidence_id", path),
        timestamp=_required_str(payload, "timestamp", path),
        binding_id=_required_str(payload, "binding_id", path),
        supervisor_id=_required_str(payload, "supervisor_id", path),
        session_id=_required_str(payload, "session_id", path),
        run_id=_required_str(payload, "run_id", path),
        host_id=_required_str(payload, "host_id", path),
        requested_by=_required_str(payload, "requested_by", path),
        agent_id=_required_str(payload, "agent_id", path),
        context_session_id=_required_str(payload, "context_session_id", path),
        scheduler_task_ids=_required_str_tuple(payload, "scheduler_task_ids", path),
        scheduler_context_ids=_required_str_tuple(payload, "scheduler_context_ids", path),
        scheduler_lane_ids=_required_str_tuple(payload, "scheduler_lane_ids", path),
        runtime_session_ids=_required_str_tuple(payload, "runtime_session_ids", path),
        home_registration_id=_required_str(payload, "home_registration_id", path),
        home_registration_audit_state=_required_str(
            payload,
            "home_registration_audit_state",
            path,
        ),
        scratch_count=_required_int(payload, "scratch_count", path),
        scratch_ids=_required_str_tuple(payload, "scratch_ids", path),
        source_snapshot_path=_required_str(payload, "source_snapshot_path", path),
        authority_split=_required_mapping(payload, "authority_split", path),
        metadata=_required_mapping(payload, "metadata", path),
    )


def _required_str(payload: Mapping[str, Any], key: str, path: Path) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(
            f"supervisor storage binding evidence artifact field {key!r} "
            f"must be a string: {path}"
        )
    return value


def _required_int(payload: Mapping[str, Any], key: str, path: Path) -> int:
    value = payload.get(key)
    if not isinstance(value, int):
        raise ValueError(
            f"supervisor storage binding evidence artifact field {key!r} "
            f"must be an integer: {path}"
        )
    return value


def _required_mapping(payload: Mapping[str, Any], key: str, path: Path) -> Mapping[str, object]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(
            f"supervisor storage binding evidence artifact field {key!r} "
            f"must be an object: {path}"
        )
    return dict(value)


def _required_str_tuple(payload: Mapping[str, Any], key: str, path: Path) -> tuple[str, ...]:
    value = payload.get(key)
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(
            f"supervisor storage binding evidence artifact field {key!r} "
            f"must be a string list: {path}"
        )
    return tuple(value)
