"""Durable sandbox allocation receipt evidence products."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from .sandbox import (
    GitWorktreeCommandReceipt,
    GitWorktreeSandboxReceipt,
    SandboxAllocation,
    SandboxLeaseMountAuthorization,
)
from .scheduler import SandboxProfile

SANDBOX_ALLOCATION_RECEIPT_EVIDENCE_PRODUCT_TYPE = "sandbox_allocation_receipt_evidence"
SANDBOX_ALLOCATION_RECEIPT_EVIDENCE_SCHEMA_VERSION = "1"


@dataclass(frozen=True, slots=True)
class SandboxAllocationReceiptEvidence:
    """Durable evidence artifact for sandbox allocation receipts."""

    evidence_id: str
    timestamp: str
    allocations: tuple[SandboxAllocation, ...]
    evidence_path: str | Path | None = None
    product_type: str = SANDBOX_ALLOCATION_RECEIPT_EVIDENCE_PRODUCT_TYPE
    schema_version: str = SANDBOX_ALLOCATION_RECEIPT_EVIDENCE_SCHEMA_VERSION
    metadata: Mapping[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-serializable sandbox allocation receipt evidence artifact."""

        return {
            "product_type": self.product_type,
            "schema_version": self.schema_version,
            "evidence_id": self.evidence_id,
            "timestamp": self.timestamp,
            "allocation_count": len(self.allocations),
            "allocations": [
                sandbox_allocation_to_json_dict(allocation)
                for allocation in self.allocations
            ],
            "authority_split": {
                "scheduler_state_read": False,
                "scheduler_state_mutated": False,
                "runtime_provider_executed": False,
                "sandbox_provider_executed": False,
                "cleanup_executed": False,
                "evidence_written": self.evidence_path is not None,
                "local_work_trajectory_mutated": False,
            },
            "metadata": dict(self.metadata),
        }

    def to_json(self) -> str:
        """Serialize this evidence artifact to stable JSON."""

        return json.dumps(self.to_json_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"


@dataclass(frozen=True, slots=True)
class SandboxAllocationReceiptEvidenceWriteResult:
    """Result of writing sandbox allocation receipt evidence to disk."""

    evidence: SandboxAllocationReceiptEvidence
    evidence_path: Path

    def to_json_dict(self) -> dict[str, object]:
        payload = self.evidence.to_json_dict()
        payload["evidence_path"] = str(self.evidence_path)
        return payload


@dataclass(frozen=True, slots=True)
class SandboxAllocationReceiptEvidenceSummary:
    """Read-only compact projection of one sandbox allocation evidence artifact."""

    evidence_path: Path
    evidence_id: str
    timestamp: str
    allocations: tuple[SandboxAllocation, ...]
    authority_split: Mapping[str, object]
    metadata: Mapping[str, object] = field(default_factory=dict)
    product_type: str = SANDBOX_ALLOCATION_RECEIPT_EVIDENCE_PRODUCT_TYPE
    schema_version: str = SANDBOX_ALLOCATION_RECEIPT_EVIDENCE_SCHEMA_VERSION

    @property
    def allocation_count(self) -> int:
        """Return allocation count in this evidence artifact."""

        return len(self.allocations)

    @property
    def allocations_by_task_id(self) -> dict[str, SandboxAllocation]:
        """Return allocations keyed by task id."""

        return {allocation.task_id: allocation for allocation in self.allocations}

    def to_json_dict(self) -> dict[str, object]:
        """Return a JSON-safe compact summary."""

        return {
            "product_type": self.product_type,
            "schema_version": self.schema_version,
            "evidence_path": str(self.evidence_path),
            "evidence_id": self.evidence_id,
            "timestamp": self.timestamp,
            "allocation_count": self.allocation_count,
            "allocations": [
                sandbox_allocation_to_json_dict(allocation)
                for allocation in self.allocations
            ],
            "authority_split": dict(self.authority_split),
            "metadata": dict(self.metadata),
        }


def default_sandbox_allocation_receipt_evidence_path(
    project_root: str | Path,
    evidence_id: str,
) -> Path:
    """Return the default path for one sandbox allocation receipt evidence artifact."""

    safe_id = "".join(
        character if character.isalnum() or character in {"-", "_"} else "-"
        for character in evidence_id
    )
    safe_id = safe_id.strip("-") or "sandbox-allocation-receipt"
    return Path(project_root) / ".codex/scheduler/evidence" / f"{safe_id}.json"


def build_sandbox_allocation_receipt_evidence(
    allocations: tuple[SandboxAllocation, ...],
    *,
    evidence_id: str,
    timestamp: str = "",
    evidence_path: str | Path | None = None,
    metadata: Mapping[str, object] | None = None,
) -> SandboxAllocationReceiptEvidence:
    """Build a durable sandbox allocation receipt evidence artifact."""

    return SandboxAllocationReceiptEvidence(
        evidence_id=evidence_id,
        timestamp=timestamp,
        evidence_path=evidence_path,
        allocations=allocations,
        metadata={} if metadata is None else metadata,
    )


def read_sandbox_allocation_receipt_evidence_summary(
    evidence_path: str | Path,
) -> SandboxAllocationReceiptEvidenceSummary:
    """Read sandbox allocation receipt evidence from JSON."""

    path = Path(evidence_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise FileNotFoundError(f"sandbox allocation receipt evidence artifact not found: {path}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"sandbox allocation receipt evidence artifact is not valid JSON: {path}: {exc}"
        ) from exc
    if not isinstance(payload, dict):
        raise ValueError(f"sandbox allocation receipt evidence artifact must be a JSON object: {path}")
    return _sandbox_allocation_receipt_evidence_summary_from_payload(path, payload)


def write_sandbox_allocation_receipt_evidence(
    evidence: SandboxAllocationReceiptEvidence,
    evidence_path: str | Path,
) -> SandboxAllocationReceiptEvidenceWriteResult:
    """Write sandbox allocation receipt evidence JSON without mutating scheduler state."""

    target = Path(evidence_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    written = SandboxAllocationReceiptEvidence(
        evidence_id=evidence.evidence_id,
        timestamp=evidence.timestamp,
        allocations=evidence.allocations,
        evidence_path=target,
        product_type=evidence.product_type,
        schema_version=evidence.schema_version,
        metadata=evidence.metadata,
    )
    target.write_text(written.to_json(), encoding="utf-8")
    return SandboxAllocationReceiptEvidenceWriteResult(
        evidence=written,
        evidence_path=target,
    )


def sandbox_allocation_to_json_dict(allocation: SandboxAllocation) -> dict[str, object]:
    """Return a JSON-safe sandbox allocation payload."""

    return {
        "allocation_id": allocation.allocation_id,
        "provider": allocation.provider,
        "task_id": allocation.task_id,
        "profile": _sandbox_profile_to_json_dict(allocation.profile),
        "state": allocation.state,
        "workspace_root": allocation.workspace_root,
        "scratch_path": allocation.scratch_path,
        "visible_mounts": list(allocation.visible_mounts),
        "network_policy": allocation.network_policy,
        "secret_policy": allocation.secret_policy,
        "cleanup_required": allocation.cleanup_required,
        "lease_authorized_mounts": [
            _lease_authorization_to_json_dict(item)
            for item in allocation.lease_authorized_mounts
        ],
        "lease_authorization_state": allocation.lease_authorization_state,
        "lease_authorization_reason": allocation.lease_authorization_reason,
        "git_worktree_receipt": (
            _git_worktree_receipt_to_json_dict(allocation.git_worktree_receipt)
            if allocation.git_worktree_receipt is not None
            else None
        ),
        "reason": allocation.reason,
    }


def sandbox_allocation_from_json_dict(payload: Mapping[str, Any], path: Path | str = "<memory>") -> SandboxAllocation:
    """Build a sandbox allocation from a JSON-safe evidence payload."""

    origin = Path(path) if not isinstance(path, str) or path != "<memory>" else Path("<memory>")
    return SandboxAllocation(
        allocation_id=_required_str(payload, "allocation_id", origin),
        provider=_required_str(payload, "provider", origin),
        task_id=_required_str(payload, "task_id", origin),
        profile=_sandbox_profile_from_payload(_required_mapping(payload, "profile", origin), origin),
        state=_required_str(payload, "state", origin),
        workspace_root=_optional_str(payload, "workspace_root", origin),
        scratch_path=_optional_str(payload, "scratch_path", origin),
        visible_mounts=_required_str_tuple(payload, "visible_mounts", origin),
        network_policy=_optional_str(payload, "network_policy", origin),
        secret_policy=_optional_str(payload, "secret_policy", origin),
        cleanup_required=_required_bool(payload, "cleanup_required", origin),
        lease_authorized_mounts=tuple(
            _lease_authorization_from_payload(item, origin)
            for item in _required_mapping_tuple(payload, "lease_authorized_mounts", origin)
        ),
        lease_authorization_state=_optional_str(payload, "lease_authorization_state", origin),
        lease_authorization_reason=_optional_str(payload, "lease_authorization_reason", origin),
        git_worktree_receipt=_git_worktree_receipt_from_payload(
            payload.get("git_worktree_receipt"),
            origin,
        ),
        reason=_optional_str(payload, "reason", origin),
    )


def _sandbox_allocation_receipt_evidence_summary_from_payload(
    path: Path,
    payload: Mapping[str, Any],
) -> SandboxAllocationReceiptEvidenceSummary:
    product_type = _required_str(payload, "product_type", path)
    if product_type != SANDBOX_ALLOCATION_RECEIPT_EVIDENCE_PRODUCT_TYPE:
        raise ValueError(
            "sandbox allocation receipt evidence artifact has product_type "
            f"{product_type!r}; expected {SANDBOX_ALLOCATION_RECEIPT_EVIDENCE_PRODUCT_TYPE!r}: {path}"
        )
    schema_version = _required_str(payload, "schema_version", path)
    if schema_version != SANDBOX_ALLOCATION_RECEIPT_EVIDENCE_SCHEMA_VERSION:
        raise ValueError(
            "sandbox allocation receipt evidence artifact has schema_version "
            f"{schema_version!r}; expected {SANDBOX_ALLOCATION_RECEIPT_EVIDENCE_SCHEMA_VERSION!r}: {path}"
        )
    allocations = tuple(
        sandbox_allocation_from_json_dict(item, path)
        for item in _required_mapping_tuple(payload, "allocations", path)
    )
    return SandboxAllocationReceiptEvidenceSummary(
        evidence_path=path,
        product_type=product_type,
        schema_version=schema_version,
        evidence_id=_required_str(payload, "evidence_id", path),
        timestamp=_required_str(payload, "timestamp", path),
        allocations=allocations,
        authority_split=_required_mapping(payload, "authority_split", path),
        metadata=_required_mapping(payload, "metadata", path),
    )


def _sandbox_profile_to_json_dict(profile: SandboxProfile) -> dict[str, object]:
    return {
        "profile_id": profile.profile_id,
        "profile_kind": profile.profile_kind,
        "network_policy": profile.network_policy,
        "secret_policy": profile.secret_policy,
        "mount_policy": profile.mount_policy,
    }


def _sandbox_profile_from_payload(payload: Mapping[str, Any], path: Path) -> SandboxProfile:
    return SandboxProfile(
        profile_id=_required_str(payload, "profile_id", path),
        profile_kind=_required_str(payload, "profile_kind", path),
        network_policy=_optional_str(payload, "network_policy", path),
        secret_policy=_optional_str(payload, "secret_policy", path),
        mount_policy=_optional_str(payload, "mount_policy", path) or "lease-scoped",
    )


def _lease_authorization_to_json_dict(
    authorization: SandboxLeaseMountAuthorization,
) -> dict[str, object]:
    return {
        "lease_id": authorization.lease_id,
        "task_id": authorization.task_id,
        "lifecycle_state": authorization.lifecycle_state,
        "authorized_mounts": list(authorization.authorized_mounts),
        "denied_mounts": list(authorization.denied_mounts),
        "reason": authorization.reason,
    }


def _lease_authorization_from_payload(
    payload: Mapping[str, Any],
    path: Path,
) -> SandboxLeaseMountAuthorization:
    return SandboxLeaseMountAuthorization(
        lease_id=_optional_str(payload, "lease_id", path),
        task_id=_optional_str(payload, "task_id", path),
        lifecycle_state=_optional_str(payload, "lifecycle_state", path),
        authorized_mounts=_required_str_tuple(payload, "authorized_mounts", path),
        denied_mounts=_required_str_tuple(payload, "denied_mounts", path),
        reason=_optional_str(payload, "reason", path),
    )


def _git_worktree_receipt_to_json_dict(
    receipt: GitWorktreeSandboxReceipt,
) -> dict[str, object]:
    return {
        "source_repository_root": receipt.source_repository_root,
        "sandbox_root": receipt.sandbox_root,
        "worktree_path": receipt.worktree_path,
        "branch_name": receipt.branch_name,
        "base_ref": receipt.base_ref,
        "authorized_writable_paths": list(receipt.authorized_writable_paths),
        "denied_writable_paths": list(receipt.denied_writable_paths),
        "cleanup_state": receipt.cleanup_state,
        "allocation": _git_command_receipt_to_json_dict(receipt.allocation),
        "cleanup": _git_command_receipt_to_json_dict(receipt.cleanup),
        "branch_cleanup": _git_command_receipt_to_json_dict(receipt.branch_cleanup),
    }


def _git_worktree_receipt_from_payload(
    value: object,
    path: Path,
) -> GitWorktreeSandboxReceipt | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError(f"sandbox allocation receipt evidence field 'git_worktree_receipt' must be an object or null: {path}")
    return GitWorktreeSandboxReceipt(
        source_repository_root=_optional_str(value, "source_repository_root", path),
        sandbox_root=_optional_str(value, "sandbox_root", path),
        worktree_path=_optional_str(value, "worktree_path", path),
        branch_name=_optional_str(value, "branch_name", path),
        base_ref=_optional_str(value, "base_ref", path) or "HEAD",
        authorized_writable_paths=_required_str_tuple(value, "authorized_writable_paths", path),
        denied_writable_paths=_required_str_tuple(value, "denied_writable_paths", path),
        cleanup_state=_optional_str(value, "cleanup_state", path),
        allocation=_git_command_receipt_from_payload(
            _required_mapping(value, "allocation", path),
            path,
        ),
        cleanup=_git_command_receipt_from_payload(
            _required_mapping(value, "cleanup", path),
            path,
        ),
        branch_cleanup=_git_command_receipt_from_payload(
            _required_mapping(value, "branch_cleanup", path),
            path,
        ),
    )


def _git_command_receipt_to_json_dict(
    receipt: GitWorktreeCommandReceipt,
) -> dict[str, object]:
    return {
        "command": list(receipt.command),
        "returncode": receipt.returncode,
        "stdout": receipt.stdout,
        "stderr": receipt.stderr,
    }


def _git_command_receipt_from_payload(
    payload: Mapping[str, Any],
    path: Path,
) -> GitWorktreeCommandReceipt:
    return GitWorktreeCommandReceipt(
        command=_required_str_tuple(payload, "command", path),
        returncode=_optional_int(payload, "returncode", path),
        stdout=_optional_str(payload, "stdout", path),
        stderr=_optional_str(payload, "stderr", path),
    )


def _required_str(payload: Mapping[str, Any], key: str, path: Path) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(f"sandbox allocation receipt evidence artifact field {key!r} must be a string: {path}")
    return value


def _optional_str(payload: Mapping[str, Any], key: str, path: Path) -> str:
    value = payload.get(key, "")
    if not isinstance(value, str):
        raise ValueError(f"sandbox allocation receipt evidence artifact field {key!r} must be a string: {path}")
    return value


def _required_bool(payload: Mapping[str, Any], key: str, path: Path) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"sandbox allocation receipt evidence artifact field {key!r} must be a boolean: {path}")
    return value


def _optional_int(payload: Mapping[str, Any], key: str, path: Path) -> int | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, int):
        raise ValueError(f"sandbox allocation receipt evidence artifact field {key!r} must be an integer or null: {path}")
    return value


def _required_mapping(payload: Mapping[str, Any], key: str, path: Path) -> Mapping[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"sandbox allocation receipt evidence artifact field {key!r} must be an object: {path}")
    return dict(value)


def _required_str_tuple(payload: Mapping[str, Any], key: str, path: Path) -> tuple[str, ...]:
    value = payload.get(key, [])
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ValueError(f"sandbox allocation receipt evidence artifact field {key!r} must be a string list: {path}")
    return tuple(value)


def _required_mapping_tuple(payload: Mapping[str, Any], key: str, path: Path) -> tuple[Mapping[str, Any], ...]:
    value = payload.get(key)
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError(f"sandbox allocation receipt evidence artifact field {key!r} must be an object list: {path}")
    return tuple(dict(item) for item in value)
