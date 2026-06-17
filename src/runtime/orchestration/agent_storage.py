"""Agent-private storage governance product models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from .exchange import (
    ExchangeArtifact,
    ExchangeLog,
    ExchangePayloadPart,
    ExchangeReference,
    ExchangeScope,
    VisibilityPolicy,
)

AgentHomeAuditState = Literal["requested", "approved", "rejected", "changes_requested"]
AgentScratchAuditState = Literal["active", "pending_review", "archived", "cleaned"]
ScratchCleanupDisposition = Literal["archive", "promote", "delete", "retain"]


@dataclass(frozen=True, slots=True)
class AgentHomeRegistration:
    """Auditable request or decision for a persistent agent home."""

    registration_id: str
    agent_id: str
    requested_by: str
    purpose: str
    capability_domain: str = ""
    storage_scope: str = "project-local"
    requested_path_hint: str = ""
    registered_path: str = ""
    retention_policy: str = ""
    quota: str = ""
    allowed_content_types: tuple[str, ...] = ()
    denied_content_types: tuple[str, ...] = ("secret", "credential")
    allowed_sources: tuple[str, ...] = ()
    denied_sources: tuple[str, ...] = ()
    secret_policy: str = "deny"
    audit_state: AgentHomeAuditState = "requested"
    approved_by: str = ""
    created_at: str = ""
    updated_at: str = ""


@dataclass(frozen=True, slots=True)
class AgentScratchSpace:
    """Temporary private storage allocated for a run, task, or lane."""

    scratch_id: str
    agent_id: str
    run_id: str = ""
    task_id: str = ""
    lane_id: str = ""
    context_id: str = ""
    path: str = ""
    created_at: str = ""
    expires_at: str = ""
    archive_policy: str = ""
    cleanup_policy: str = ""
    manifest_path: str = ""
    audit_state: AgentScratchAuditState = "active"


@dataclass(frozen=True, slots=True)
class ScratchManifestEntry:
    """One item declared in a scratch manifest."""

    path: str
    content_type: str = ""
    source: str = ""
    disposition: ScratchCleanupDisposition = "retain"
    summary: str = ""
    contains_sensitive_content: bool = False


@dataclass(frozen=True, slots=True)
class ScratchManifest:
    """Reviewable inventory of temporary scratch content."""

    manifest_id: str
    scratch_id: str
    agent_id: str
    entries: tuple[ScratchManifestEntry, ...] = ()
    produced_at: str = ""
    review_state: str = "pending_review"
    notes: str = ""


@dataclass(frozen=True, slots=True)
class CleanupReceipt:
    """Compact record of scratch archival, promotion, retention, and deletion."""

    receipt_id: str
    scratch_id: str
    agent_id: str
    cleaned_at: str
    archived_paths: tuple[str, ...] = ()
    promoted_paths: tuple[str, ...] = ()
    deleted_paths: tuple[str, ...] = ()
    retained_paths: tuple[str, ...] = ()
    reviewed_by: str = ""
    summary: str = ""


def agent_home_registration_to_artifact(
    registration: AgentHomeRegistration,
    *,
    artifact_id: str = "",
    version: str = "v1",
) -> ExchangeArtifact:
    """Represent an agent home registration request or decision as an artifact."""

    return ExchangeArtifact(
        artifact_id=artifact_id or f"agent-home-registration:{registration.registration_id}",
        kind="retention",
        intent="request_registration",
        producer=registration.requested_by,
        audience=("workspace-registration",),
        scope=ExchangeScope(agent_id=registration.agent_id),
        lifecycle_state=("accepted" if registration.audit_state == "approved" else "proposed"),
        visibility_policy=VisibilityPolicy(
            audience=("workspace-registration", registration.agent_id),
            contains_sensitive_content=False,
            redaction_required=False,
        ),
        created_at=registration.created_at,
        version=version,
        parts=(
            ExchangePayloadPart(
                part_type="structured",
                data=_agent_home_registration_data(registration),
            ),
            ExchangePayloadPart(
                part_type="storage_manifest",
                data={
                    "product_type": "agent_home_registration",
                    **_agent_home_registration_data(registration),
                },
            ),
            ExchangePayloadPart(
                part_type="log",
                log=ExchangeLog(
                    timestamp=registration.updated_at or registration.created_at,
                    actor=registration.approved_by or registration.requested_by,
                    action=f"agent_home_{registration.audit_state}",
                    channel="agent-storage-governance",
                    summary=registration.purpose,
                    related_artifact_ids=(),
                ),
            ),
        ),
    )


def scratch_manifest_to_artifact(
    manifest: ScratchManifest,
    scratch: AgentScratchSpace,
    *,
    artifact_id: str = "",
    version: str = "v1",
) -> ExchangeArtifact:
    """Represent a scratch manifest as a retention review artifact."""

    return ExchangeArtifact(
        artifact_id=artifact_id or f"scratch-manifest:{manifest.manifest_id}",
        kind="retention",
        intent="request_retention",
        producer=scratch.agent_id,
        audience=("workspace-registration",),
        scope=ExchangeScope(
            lane_id=scratch.lane_id,
            task_id=scratch.task_id,
            context_id=scratch.context_id,
            agent_id=scratch.agent_id,
            runtime_session_id=scratch.run_id,
        ),
        visibility_policy=VisibilityPolicy(
            audience=("workspace-registration", scratch.agent_id),
            contains_sensitive_content=any(entry.contains_sensitive_content for entry in manifest.entries),
            redaction_required=any(entry.contains_sensitive_content for entry in manifest.entries),
        ),
        created_at=manifest.produced_at,
        version=version,
        parts=(
            ExchangePayloadPart(
                part_type="structured",
                data={
                    "product_type": "scratch_manifest",
                    "scratch": _scratch_space_data(scratch),
                    "manifest": _scratch_manifest_data(manifest),
                },
            ),
            ExchangePayloadPart(
                part_type="storage_manifest",
                data={
                    "product_type": "scratch_manifest",
                    "scratch_id": scratch.scratch_id,
                    "manifest_id": manifest.manifest_id,
                    "entries": [_scratch_entry_data(entry) for entry in manifest.entries],
                },
            ),
            ExchangePayloadPart(
                part_type="log",
                log=ExchangeLog(
                    timestamp=manifest.produced_at,
                    actor=manifest.agent_id,
                    action="scratch_manifest_submitted",
                    channel="agent-storage-governance",
                    summary=manifest.notes or f"Submitted scratch manifest {manifest.manifest_id}.",
                ),
            ),
        ),
    )


def cleanup_receipt_to_artifact(
    receipt: CleanupReceipt,
    scratch: AgentScratchSpace,
    *,
    artifact_id: str = "",
    version: str = "v1",
) -> ExchangeArtifact:
    """Represent scratch cleanup as a cleanup receipt artifact."""

    return ExchangeArtifact(
        artifact_id=artifact_id or f"cleanup-receipt:{receipt.receipt_id}",
        kind="cleanup",
        intent="inform",
        producer=receipt.reviewed_by or receipt.agent_id,
        audience=("workspace-registration", scratch.agent_id),
        scope=ExchangeScope(
            lane_id=scratch.lane_id,
            task_id=scratch.task_id,
            context_id=scratch.context_id,
            agent_id=scratch.agent_id,
            runtime_session_id=scratch.run_id,
        ),
        created_at=receipt.cleaned_at,
        version=version,
        parts=(
            ExchangePayloadPart(
                part_type="storage_manifest",
                data={
                    "product_type": "cleanup_receipt",
                    "scratch": _scratch_space_data(scratch),
                    "receipt": _cleanup_receipt_data(receipt),
                },
            ),
            ExchangePayloadPart(
                part_type="log",
                log=ExchangeLog(
                    timestamp=receipt.cleaned_at,
                    actor=receipt.reviewed_by or receipt.agent_id,
                    action="scratch_cleanup_recorded",
                    channel="agent-storage-governance",
                    summary=receipt.summary,
                ),
            ),
        ),
    )


def _agent_home_registration_data(registration: AgentHomeRegistration) -> dict[str, object]:
    return {
        "registration_id": registration.registration_id,
        "agent_id": registration.agent_id,
        "requested_by": registration.requested_by,
        "purpose": registration.purpose,
        "capability_domain": registration.capability_domain,
        "storage_scope": registration.storage_scope,
        "requested_path_hint": registration.requested_path_hint,
        "registered_path": registration.registered_path,
        "retention_policy": registration.retention_policy,
        "quota": registration.quota,
        "allowed_content_types": list(registration.allowed_content_types),
        "denied_content_types": list(registration.denied_content_types),
        "allowed_sources": list(registration.allowed_sources),
        "denied_sources": list(registration.denied_sources),
        "secret_policy": registration.secret_policy,
        "audit_state": registration.audit_state,
        "approved_by": registration.approved_by,
        "created_at": registration.created_at,
        "updated_at": registration.updated_at,
    }


def _scratch_space_data(scratch: AgentScratchSpace) -> dict[str, object]:
    return {
        "scratch_id": scratch.scratch_id,
        "agent_id": scratch.agent_id,
        "run_id": scratch.run_id,
        "task_id": scratch.task_id,
        "lane_id": scratch.lane_id,
        "context_id": scratch.context_id,
        "path": scratch.path,
        "created_at": scratch.created_at,
        "expires_at": scratch.expires_at,
        "archive_policy": scratch.archive_policy,
        "cleanup_policy": scratch.cleanup_policy,
        "manifest_path": scratch.manifest_path,
        "audit_state": scratch.audit_state,
    }


def _scratch_entry_data(entry: ScratchManifestEntry) -> dict[str, object]:
    return {
        "path": entry.path,
        "content_type": entry.content_type,
        "source": entry.source,
        "disposition": entry.disposition,
        "summary": entry.summary,
        "contains_sensitive_content": entry.contains_sensitive_content,
    }


def _scratch_manifest_data(manifest: ScratchManifest) -> dict[str, object]:
    return {
        "manifest_id": manifest.manifest_id,
        "scratch_id": manifest.scratch_id,
        "agent_id": manifest.agent_id,
        "entries": [_scratch_entry_data(entry) for entry in manifest.entries],
        "produced_at": manifest.produced_at,
        "review_state": manifest.review_state,
        "notes": manifest.notes,
    }


def _cleanup_receipt_data(receipt: CleanupReceipt) -> dict[str, object]:
    return {
        "receipt_id": receipt.receipt_id,
        "scratch_id": receipt.scratch_id,
        "agent_id": receipt.agent_id,
        "cleaned_at": receipt.cleaned_at,
        "archived_paths": list(receipt.archived_paths),
        "promoted_paths": list(receipt.promoted_paths),
        "deleted_paths": list(receipt.deleted_paths),
        "retained_paths": list(receipt.retained_paths),
        "reviewed_by": receipt.reviewed_by,
        "summary": receipt.summary,
    }
