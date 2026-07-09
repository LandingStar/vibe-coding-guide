"""Read-only host/screenshot evidence readback projections."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .log_readback import LogRecordRef


@dataclass(frozen=True, slots=True)
class HostEvidenceReadbackEnvelope:
    """Human/audit-oriented readback projection for host evidence."""

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
    evidence_product_type: str = ""
    evidence_path: str = ""
    host_surface: str = ""
    runtime_providers: tuple[str, ...] = ()
    severity: str = ""
    stop_reason: str = ""
    stop_detail: str = ""
    screenshot_paths: tuple[str, ...] = ()
    viewport: Mapping[str, object] | None = None
    visual_validation_summary: str = ""
    run_count: int = 0
    output_count: int = 0
    permission_review_count: int = 0
    key_fact_count: int = 0
    reference_count: int = 0
    authority_clue_count: int = 0

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
            "evidence_product_type": self.evidence_product_type,
            "evidence_path": self.evidence_path,
            "host_surface": self.host_surface,
            "runtime_providers": list(self.runtime_providers),
            "severity": self.severity,
            "stop_reason": self.stop_reason,
            "stop_detail": self.stop_detail,
            "screenshot_paths": list(self.screenshot_paths),
            "viewport": dict(self.viewport or {}),
            "visual_validation_summary": self.visual_validation_summary,
            "run_count": self.run_count,
            "output_count": self.output_count,
            "permission_review_count": self.permission_review_count,
            "key_fact_count": self.key_fact_count,
            "reference_count": self.reference_count,
            "authority_clue_count": self.authority_clue_count,
            "authority_split": {
                "source": "host_evidence_summary_or_presentation",
                "read_model_only": True,
                "browser_executed": False,
                "screenshot_captured": False,
                "raw_screenshot_bytes_persisted_inline": False,
                "raw_payload_persisted": self.raw_payload_persisted,
                "provider_executed": False,
                "sandbox_cleanup_executed": False,
                "scheduler_state_mutated": False,
                "exchange_store_mutated": False,
                "local_work_trajectory_mutated": False,
            },
        }


@dataclass(frozen=True, slots=True)
class HostEvidenceErrorReadbackEnvelope:
    """Human/audit-oriented readback projection for one evidence read error."""

    schema_version: str
    record_id: str
    record_kind: str
    timestamp: str
    actor: str
    action: str
    status: str
    summary: str
    reason: str
    evidence_path: str
    error_kind: str
    subject_refs: tuple[LogRecordRef, ...] = ()
    evidence_refs: tuple[LogRecordRef, ...] = ()
    related_record_ids: tuple[str, ...] = ()
    next_hint: str = ""
    sensitivity: str = "internal"
    redaction_state: str = "contains_no_raw_secret"
    raw_payload_persisted: bool = False

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
            "run_id": "",
            "correlation_id": self.evidence_path or self.record_id,
            "subject_refs": [ref.to_json_dict() for ref in self.subject_refs],
            "input_refs": [],
            "output_refs": [],
            "evidence_refs": [ref.to_json_dict() for ref in self.evidence_refs],
            "related_record_ids": list(self.related_record_ids),
            "next_hint": self.next_hint,
            "sensitivity": self.sensitivity,
            "redaction_state": self.redaction_state,
            "raw_payload_persisted": self.raw_payload_persisted,
            "evidence_path": self.evidence_path,
            "error_kind": self.error_kind,
            "authority_split": {
                "source": "host_evidence_read_error",
                "read_model_only": True,
                "browser_executed": False,
                "screenshot_captured": False,
                "raw_screenshot_bytes_persisted_inline": False,
                "raw_payload_persisted": self.raw_payload_persisted,
                "provider_executed": False,
                "sandbox_cleanup_executed": False,
                "scheduler_state_mutated": False,
                "exchange_store_mutated": False,
                "local_work_trajectory_mutated": False,
            },
        }


def host_evidence_summary_to_readback_envelope(
    summary: Mapping[str, Any] | object,
    *,
    timestamp: str = "",
    actor: str = "host-evidence-readback",
) -> HostEvidenceReadbackEnvelope:
    """Project one compact host evidence summary into a draft envelope.

    This is a read-only projection. It does not run browsers, capture
    screenshots, execute providers, clean sandboxes, mutate evidence artifacts,
    or expose raw image bytes inline.
    """

    payload = _to_mapping(summary)
    card = _summary_card_like_payload(payload)
    return host_evidence_card_to_readback_envelope(card, timestamp=timestamp, actor=actor)


def host_evidence_card_to_readback_envelope(
    card: Mapping[str, Any] | object,
    *,
    timestamp: str = "",
    actor: str = "host-evidence-readback",
) -> HostEvidenceReadbackEnvelope:
    """Project one host evidence presentation card into a draft envelope."""

    payload = _to_mapping(card)
    record_id = _text(payload, "id") or _text(payload, "evidence_id") or "host-evidence"
    evidence_product_type = _evidence_product_type(payload)
    evidence_path = _first_ref_target(payload, labels=("Evidence",), ref_kinds=("path",))
    screenshot_paths = _screenshot_paths(payload)
    viewport = _viewport(payload)
    status = _text(payload, "status") or "unknown"
    severity = _text(payload, "severity")
    stop_reason = _text(payload, "stop_reason")
    stop_detail = _text(payload, "stop_detail")
    host_surface = _text(payload, "host_surface")
    runtime_providers = _string_tuple(payload.get("runtime_providers"))
    run_id = _run_id(payload)
    visual_summary = _visual_validation_summary(payload, screenshot_paths=screenshot_paths)
    return HostEvidenceReadbackEnvelope(
        schema_version="host-evidence-readback-envelope.v1",
        record_id=record_id,
        record_kind="host_evidence",
        timestamp=timestamp or _text(payload, "timestamp"),
        actor=actor,
        action=_host_evidence_action(evidence_product_type, status),
        status=status,
        summary=_host_evidence_summary(payload, evidence_product_type=evidence_product_type),
        reason=_host_evidence_reason(
            status=status,
            severity=severity,
            stop_reason=stop_reason,
            stop_detail=stop_detail,
        ),
        run_id=run_id,
        correlation_id=_first_non_empty(run_id, _text(payload, "invocation_id"), record_id),
        subject_refs=_host_evidence_subject_refs(
            record_id=record_id,
            evidence_product_type=evidence_product_type,
            host_surface=host_surface,
            runtime_providers=runtime_providers,
        ),
        input_refs=_host_evidence_input_refs(payload),
        output_refs=_host_evidence_output_refs(payload),
        evidence_refs=_host_evidence_evidence_refs(
            record_id=record_id,
            evidence_path=evidence_path,
            refs=_mapping_sequence(payload.get("refs")),
            screenshot_paths=screenshot_paths,
        ),
        related_record_ids=_host_evidence_related_ids(
            record_id=record_id,
            payload=payload,
            evidence_product_type=evidence_product_type,
            screenshot_paths=screenshot_paths,
        ),
        next_hint=_host_evidence_next_hint(
            record_id=record_id,
            evidence_path=evidence_path,
            status=status,
            screenshot_paths=screenshot_paths,
        ),
        raw_payload_persisted=False,
        evidence_product_type=evidence_product_type,
        evidence_path=evidence_path,
        host_surface=host_surface,
        runtime_providers=runtime_providers,
        severity=severity,
        stop_reason=stop_reason,
        stop_detail=stop_detail,
        screenshot_paths=screenshot_paths,
        viewport=viewport,
        visual_validation_summary=visual_summary,
        run_count=_int(payload.get("run_count")),
        output_count=_int(payload.get("output_count")),
        permission_review_count=_int(payload.get("permission_review_count")),
        key_fact_count=len(_mapping_sequence(payload.get("key_facts"))),
        reference_count=len(_mapping_sequence(payload.get("refs"))),
        authority_clue_count=len(_mapping_sequence(payload.get("authority_clues"))),
    )


def host_evidence_error_to_readback_envelope(
    error: Mapping[str, Any] | object,
    *,
    timestamp: str = "",
    actor: str = "host-evidence-readback",
    index: int = 0,
) -> HostEvidenceErrorReadbackEnvelope:
    """Project one isolated host evidence read error into a draft envelope."""

    payload = _to_mapping(error)
    evidence_path = _text(payload, "evidence_path")
    error_kind = _text(payload, "error_kind") or "read_error"
    record_id = _text(payload, "id") or f"host-evidence-error:{index or evidence_path or error_kind}"
    message = _bounded_redacted_text(_text(payload, "message"))
    return HostEvidenceErrorReadbackEnvelope(
        schema_version="host-evidence-readback-envelope.v1",
        record_id=record_id,
        record_kind="host_evidence_error",
        timestamp=timestamp,
        actor=actor,
        action="host_evidence_read_error",
        status="failed",
        summary=f"Host evidence read failed for {evidence_path or record_id}.",
        reason=message or f"Host evidence read failed with {error_kind}.",
        evidence_path=evidence_path,
        error_kind=error_kind,
        subject_refs=(
            LogRecordRef(kind="host_evidence_error", id=record_id, role="subject"),
        ),
        evidence_refs=(
            LogRecordRef(kind="file", path=evidence_path, role="evidence"),
        ) if evidence_path else (),
        related_record_ids=(
            _related_record_id("host_evidence_error", record_id),
            *(
                (_related_record_id("file", evidence_path),)
                if evidence_path
                else ()
            ),
        ),
        next_hint="Inspect the evidence artifact path and producer that wrote it.",
        raw_payload_persisted=False,
    )


def host_evidence_presentation_to_readback_envelopes(
    presentation: Mapping[str, Any] | object,
    *,
    actor: str = "host-evidence-readback",
) -> tuple[HostEvidenceReadbackEnvelope | HostEvidenceErrorReadbackEnvelope, ...]:
    """Project a whole host evidence presentation into readback envelopes."""

    payload = _to_mapping(presentation)
    timestamp = _text(payload, "generated_at")
    envelopes: list[HostEvidenceReadbackEnvelope | HostEvidenceErrorReadbackEnvelope] = []
    for card in _mapping_sequence(payload.get("cards")):
        envelopes.append(
            host_evidence_card_to_readback_envelope(
                card,
                timestamp=timestamp or _text(card, "timestamp"),
                actor=actor,
            )
        )
    for index, error in enumerate(_mapping_sequence(payload.get("error_rows")), start=1):
        envelopes.append(
            host_evidence_error_to_readback_envelope(
                error,
                timestamp=timestamp,
                actor=actor,
                index=index,
            )
        )
    return tuple(envelopes)


def _summary_card_like_payload(payload: Mapping[str, Any]) -> dict[str, object]:
    product_type = _text(payload, "product_type")
    evidence_id = _text(payload, "evidence_id")
    metadata = _mapping(payload.get("metadata"))
    authority = _mapping(payload.get("authority_split"))
    refs: list[dict[str, str]] = []
    evidence_path = _text(payload, "evidence_path")
    if evidence_path:
        refs.append({"label": "Evidence", "target": evidence_path, "ref_kind": "path"})
    for label, key in (
        ("Snapshot", "snapshot_path"),
        ("Event log", "event_log_path"),
        ("Scheduler projection", "scheduler_projection_path"),
        ("Source snapshot", "source_snapshot_path"),
    ):
        value = _text(payload, key)
        if value:
            refs.append({"label": label, "target": value, "ref_kind": "path"})

    host_invocation = _mapping(payload.get("host_invocation"))
    host_surface = (
        _text(host_invocation, "surface")
        or _metadata_text(metadata, "runtime_host_surface")
        or _metadata_text(metadata, "surface")
        or _metadata_text(metadata, "workflow_surface")
        or product_type
    )
    invocation_id = (
        _text(host_invocation, "invocation_id")
        or _metadata_text(metadata, "host_invocation_id")
        or _text(payload, "run_id")
        or evidence_id
    )
    requested_by = (
        _text(host_invocation, "requested_by")
        or _text(payload, "requested_by")
        or "operator-or-host"
    )
    runtime_providers = _runtime_providers_from_summary(payload)
    status, severity = _summary_status_and_severity(payload, product_type=product_type)
    stop_reason = _summary_stop_reason(payload, product_type=product_type)
    stop_detail = _summary_stop_detail(payload, product_type=product_type)
    key_facts = _summary_key_facts(payload, product_type=product_type)
    authority_clues = [
        {"label": key, "value": _object_text(value)}
        for key, value in sorted(authority.items())
        if key
    ]
    return {
        "id": evidence_id,
        "title": f"Host evidence {evidence_id}" if evidence_id else "Host evidence",
        "subtitle": " · ".join(
            part
            for part in (
                host_surface,
                stop_reason,
                f"{_summary_run_count(payload)} run(s)",
            )
            if part
        ),
        "status": status,
        "severity": severity,
        "timestamp": _text(payload, "timestamp"),
        "runtime_providers": list(runtime_providers),
        "host_surface": host_surface,
        "invocation_id": invocation_id,
        "requested_by": requested_by,
        "stop_reason": stop_reason,
        "stop_detail": stop_detail,
        "run_count": _summary_run_count(payload),
        "output_count": _summary_output_count(payload),
        "permission_review_count": _int(payload.get("permission_review_count")),
        "key_facts": key_facts,
        "refs": refs,
        "authority_clues": authority_clues,
        "metadata": {
            "evidence_product_type": product_type,
            "evidence_metadata": dict(metadata),
            "final_queue_summary": dict(_mapping(payload.get("final_queue_summary"))),
        },
    }


def _summary_status_and_severity(
    payload: Mapping[str, Any],
    *,
    product_type: str,
) -> tuple[str, str]:
    if product_type == "sandbox_allocation_receipt_evidence":
        cleanup_failed = _summary_cleanup_failed_count(payload)
        cleanup_required = _summary_cleanup_required_count(payload)
        if cleanup_failed:
            return "failed", "error"
        if cleanup_required:
            return "partial", "warning"
        if _int(payload.get("allocation_count")):
            return "completed", "info"
        return "unknown", "warning"
    if product_type == "supervisor_storage_binding_evidence":
        return "completed", "info"
    failed_ids = _string_tuple(payload.get("failed_task_ids"))
    final_queue = _mapping(payload.get("final_queue_summary"))
    final_failed = _string_tuple(final_queue.get("failed_task_ids"))
    blocked_ids = _string_tuple(payload.get("blocked_task_ids")) or _string_tuple(
        final_queue.get("blocked_task_ids")
    )
    stop_reason = _text(payload, "stop_reason")
    permission_review_count = _int(payload.get("permission_review_count"))
    if failed_ids or final_failed or stop_reason in {"task_failed", "completed_with_failures", "runtime_failure_limit_reached"}:
        return "failed", "error"
    if permission_review_count:
        return "permission-review", "warning"
    if blocked_ids or stop_reason in {"max_runs_reached", "max_ticks_reached", "blocked_tasks", "cancelled"}:
        return "partial", "warning"
    if stop_reason == "no_ready_tasks":
        return "completed", "info"
    return "unknown", "warning"


def _summary_stop_reason(payload: Mapping[str, Any], *, product_type: str) -> str:
    if product_type == "sandbox_allocation_receipt_evidence":
        if _summary_cleanup_failed_count(payload):
            return "cleanup_failed"
        if _summary_cleanup_required_count(payload):
            return "cleanup_required"
        return "cleanup_settled"
    if product_type == "supervisor_storage_binding_evidence":
        return "readback_available"
    return _text(payload, "stop_reason")


def _summary_stop_detail(payload: Mapping[str, Any], *, product_type: str) -> str:
    if product_type == "sandbox_allocation_receipt_evidence":
        failed = _summary_cleanup_failed_count(payload)
        required = _summary_cleanup_required_count(payload)
        if failed:
            return f"{failed} sandbox cleanup attempt(s) failed."
        if required:
            return f"{required} sandbox allocation(s) still require explicit cleanup."
        return "Sandbox allocation receipt evidence is settled."
    if product_type == "supervisor_storage_binding_evidence":
        return "Supervisor storage binding evidence was read successfully."
    return _text(payload, "stop_detail")


def _summary_key_facts(
    payload: Mapping[str, Any],
    *,
    product_type: str,
) -> list[dict[str, str]]:
    facts = [
        {"label": "Evidence product", "value": product_type},
    ]
    for label, key in (
        ("Stop reason", "stop_reason"),
        ("Run count", "run_count"),
        ("Tick count", "tick_count"),
        ("Total runs", "total_run_count"),
        ("Scheduler events", "scheduler_event_count"),
        ("Allocation count", "allocation_count"),
        ("Scratch count", "scratch_count"),
    ):
        value = payload.get(key)
        if value not in (None, ""):
            facts.append({"label": label, "value": _object_text(value)})
    return facts


def _summary_cleanup_failed_count(payload: Mapping[str, Any]) -> int:
    count = 0
    for allocation in _mapping_sequence(payload.get("allocations")):
        receipt = _mapping(allocation.get("git_worktree_receipt"))
        if _text(receipt, "cleanup_state") == "failed":
            count += 1
    return count


def _summary_cleanup_required_count(payload: Mapping[str, Any]) -> int:
    count = 0
    for allocation in _mapping_sequence(payload.get("allocations")):
        receipt = _mapping(allocation.get("git_worktree_receipt"))
        cleanup_state = _text(receipt, "cleanup_state")
        if bool(allocation.get("cleanup_required")) or cleanup_state == "required":
            count += 1
    return count


def _summary_run_count(payload: Mapping[str, Any]) -> int:
    return _int(payload.get("run_count")) or _int(payload.get("total_run_count")) or len(
        _string_tuple(payload.get("runtime_session_ids"))
    )


def _summary_output_count(payload: Mapping[str, Any]) -> int:
    return len(_mapping_sequence(payload.get("output_artifact_refs"))) or _int(
        payload.get("scratch_count")
    )


def _runtime_providers_from_summary(payload: Mapping[str, Any]) -> tuple[str, ...]:
    providers = _string_tuple(payload.get("runtime_providers"))
    if providers:
        return providers
    provider = _text(payload, "runtime_provider")
    if provider:
        return (provider,)
    if _text(payload, "product_type") == "sandbox_allocation_receipt_evidence":
        allocation_providers = tuple(
            _text(allocation, "provider")
            for allocation in _mapping_sequence(payload.get("allocations"))
            if _text(allocation, "provider")
        )
        return tuple(dict.fromkeys(allocation_providers))
    return ()


def _host_evidence_action(evidence_product_type: str, status: str) -> str:
    prefix = evidence_product_type.replace("-", "_") if evidence_product_type else "host_evidence"
    return f"{prefix}_{status or 'recorded'}"


def _host_evidence_summary(
    payload: Mapping[str, Any],
    *,
    evidence_product_type: str,
) -> str:
    title = _text(payload, "title") or _text(payload, "id") or "Host evidence"
    subtitle = _text(payload, "subtitle")
    status = _text(payload, "status") or "unknown"
    if subtitle:
        return f"{title} is {status}: {subtitle}."
    if evidence_product_type:
        return f"{title} is {status} for evidence product {evidence_product_type}."
    return f"{title} is {status}."


def _host_evidence_reason(
    *,
    status: str,
    severity: str,
    stop_reason: str,
    stop_detail: str,
) -> str:
    if stop_detail:
        return _bounded_redacted_text(stop_detail)
    if stop_reason:
        return f"Evidence stop reason is {stop_reason}."
    if status in {"failed", "partial", "permission-review", "unknown"}:
        return f"Evidence status is {status}; severity is {severity or 'unknown'}."
    return "Host evidence was read successfully."


def _host_evidence_subject_refs(
    *,
    record_id: str,
    evidence_product_type: str,
    host_surface: str,
    runtime_providers: tuple[str, ...],
) -> tuple[LogRecordRef, ...]:
    refs = [LogRecordRef(kind="host_evidence", id=record_id, role="subject")]
    if evidence_product_type:
        refs.append(
            LogRecordRef(kind="evidence_product", id=evidence_product_type, role="subject")
        )
    if host_surface:
        refs.append(LogRecordRef(kind="host_surface", id=host_surface, role="subject"))
    refs.extend(
        LogRecordRef(kind="provider", id=provider, role="subject")
        for provider in runtime_providers
    )
    return tuple(refs)


def _host_evidence_input_refs(payload: Mapping[str, Any]) -> tuple[LogRecordRef, ...]:
    refs: list[LogRecordRef] = []
    for ref in _mapping_sequence(payload.get("refs")):
        label = _text(ref, "label").lower()
        if label in {"snapshot", "event log", "source snapshot"}:
            refs.append(_presentation_ref_to_log_ref(ref, role="input"))
    return tuple(refs)


def _host_evidence_output_refs(payload: Mapping[str, Any]) -> tuple[LogRecordRef, ...]:
    refs: list[LogRecordRef] = []
    for ref in _mapping_sequence(payload.get("refs")):
        label = _text(ref, "label").lower()
        ref_kind = _text(ref, "ref_kind")
        if ref_kind == "exchange_artifact" or label.startswith("output"):
            refs.append(_presentation_ref_to_log_ref(ref, role="output"))
        elif label in {"scheduler projection", "home registration"}:
            refs.append(_presentation_ref_to_log_ref(ref, role="output"))
    return tuple(refs)


def _host_evidence_evidence_refs(
    *,
    record_id: str,
    evidence_path: str,
    refs: tuple[Mapping[str, Any], ...],
    screenshot_paths: tuple[str, ...],
) -> tuple[LogRecordRef, ...]:
    evidence_refs: list[LogRecordRef] = [
        LogRecordRef(
            kind="host_evidence",
            id=record_id,
            path=evidence_path,
            role="evidence",
        )
    ]
    for ref in refs:
        label = _text(ref, "label").lower()
        if label == "evidence" or _is_screenshot_path(_text(ref, "target")):
            evidence_refs.append(_presentation_ref_to_log_ref(ref, role="evidence"))
    evidence_refs.extend(
        LogRecordRef(kind="screenshot", path=path, role="evidence")
        for path in screenshot_paths
        if path and all(existing.path != path for existing in evidence_refs)
    )
    return tuple(evidence_refs)


def _host_evidence_related_ids(
    *,
    record_id: str,
    payload: Mapping[str, Any],
    evidence_product_type: str,
    screenshot_paths: tuple[str, ...],
) -> tuple[str, ...]:
    related = [_related_record_id("host_evidence", record_id)]
    for kind, value in (
        ("evidence_product", evidence_product_type),
        ("host_surface", _text(payload, "host_surface")),
        ("host_invocation", _text(payload, "invocation_id")),
    ):
        if value:
            related.append(_related_record_id(kind, value))
    metadata = _mapping(payload.get("metadata"))
    for key in (
        "binding_id",
        "host_id",
        "scheduler_task_ids",
        "scheduler_lane_ids",
        "runtime_session_ids",
        "completed_task_ids",
        "blocked_task_ids",
        "failed_task_ids",
    ):
        value = metadata.get(key)
        if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            related.extend(_related_record_id(key.removesuffix("_ids"), str(item)) for item in value)
        elif value:
            related.append(_related_record_id(key.removesuffix("_id"), str(value)))
    related.extend(_related_record_id("screenshot", path) for path in screenshot_paths)
    return tuple(dict.fromkeys(related))


def _host_evidence_next_hint(
    *,
    record_id: str,
    evidence_path: str,
    status: str,
    screenshot_paths: tuple[str, ...],
) -> str:
    if screenshot_paths:
        return f"Inspect screenshot evidence {screenshot_paths[0]} for visual validation."
    if status in {"failed", "partial", "permission-review", "unknown"} and evidence_path:
        return f"Inspect host evidence artifact {evidence_path} and related scheduler/runtime records."
    if evidence_path:
        return f"Inspect host evidence artifact {evidence_path} for full compact evidence."
    return f"Inspect host evidence record {record_id}."


def _presentation_ref_to_log_ref(ref: Mapping[str, Any], *, role: str) -> LogRecordRef:
    ref_kind = _text(ref, "ref_kind") or "path"
    target = _text(ref, "target")
    label = _text(ref, "label")
    if ref_kind == "path" or "/" in target or "\\" in target or target.startswith("."):
        kind = "screenshot" if _is_screenshot_path(target) else "file"
        return LogRecordRef(kind=kind, path=target, label=label, role=role)
    return LogRecordRef(kind=ref_kind, id=target, label=label, role=role)


def _evidence_product_type(payload: Mapping[str, Any]) -> str:
    metadata = _mapping(payload.get("metadata"))
    product_type = _text(metadata, "evidence_product_type")
    if product_type:
        return product_type
    evidence_metadata = _mapping(metadata.get("evidence_metadata"))
    return _text(evidence_metadata, "product_type")


def _screenshot_paths(payload: Mapping[str, Any]) -> tuple[str, ...]:
    paths: list[str] = []
    metadata = _mapping(payload.get("metadata"))
    evidence_metadata = _mapping(metadata.get("evidence_metadata"))
    for source in (payload, metadata, evidence_metadata):
        for key in ("screenshot_path", "screenshot"):
            value = _text(source, key)
            if value and _is_screenshot_path(value):
                paths.append(value)
        for key in ("screenshot_paths", "screenshots"):
            paths.extend(
                value
                for value in _string_tuple(source.get(key))
                if _is_screenshot_path(value)
            )
    for ref in _mapping_sequence(payload.get("refs")):
        target = _text(ref, "target")
        if target and _is_screenshot_path(target):
            paths.append(target)
    return tuple(dict.fromkeys(paths))


def _viewport(payload: Mapping[str, Any]) -> Mapping[str, object]:
    metadata = _mapping(payload.get("metadata"))
    evidence_metadata = _mapping(metadata.get("evidence_metadata"))
    for source in (payload, metadata, evidence_metadata):
        viewport = _mapping(source.get("viewport"))
        if viewport:
            return viewport
    width = _first_non_empty(
        _metadata_text(metadata, "viewport_width"),
        _metadata_text(evidence_metadata, "viewport_width"),
    )
    height = _first_non_empty(
        _metadata_text(metadata, "viewport_height"),
        _metadata_text(evidence_metadata, "viewport_height"),
    )
    viewport: dict[str, object] = {}
    if width:
        viewport["width"] = width
    if height:
        viewport["height"] = height
    return viewport


def _visual_validation_summary(
    payload: Mapping[str, Any],
    *,
    screenshot_paths: tuple[str, ...],
) -> str:
    metadata = _mapping(payload.get("metadata"))
    evidence_metadata = _mapping(metadata.get("evidence_metadata"))
    for source in (payload, metadata, evidence_metadata):
        for key in ("visual_validation_summary", "assertion_summary", "screenshot_summary"):
            value = _text(source, key)
            if value:
                return _bounded_redacted_text(value)
    if screenshot_paths:
        return f"{len(screenshot_paths)} screenshot evidence artifact(s) referenced."
    return ""


def _run_id(payload: Mapping[str, Any]) -> str:
    metadata = _mapping(payload.get("metadata"))
    evidence_metadata = _mapping(metadata.get("evidence_metadata"))
    return _first_non_empty(
        _text(payload, "run_id"),
        _metadata_text(metadata, "run_id"),
        _metadata_text(evidence_metadata, "run_id"),
        _metadata_text(metadata, "host_invocation_id"),
        _text(payload, "invocation_id"),
    )


def _first_ref_target(
    payload: Mapping[str, Any],
    *,
    labels: tuple[str, ...],
    ref_kinds: tuple[str, ...] = (),
) -> str:
    allowed_labels = {label.lower() for label in labels}
    allowed_kinds = {kind.lower() for kind in ref_kinds}
    for ref in _mapping_sequence(payload.get("refs")):
        label = _text(ref, "label").lower()
        ref_kind = _text(ref, "ref_kind").lower()
        if label in allowed_labels and (not allowed_kinds or ref_kind in allowed_kinds):
            return _text(ref, "target")
    return ""


def _is_screenshot_path(value: str) -> bool:
    lower = value.lower()
    return (
        bool(value)
        and (
            "screenshot" in lower
            or "playwright" in lower
            or lower.endswith((".png", ".jpg", ".jpeg", ".webp"))
        )
    )


def _to_mapping(value: Mapping[str, Any] | object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    to_json = getattr(value, "to_json_dict", None)
    if callable(to_json):
        payload = to_json()
        if isinstance(payload, Mapping):
            return payload
    return {}


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _mapping_sequence(value: object) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return ()
    return tuple(str(item) for item in value if str(item))


def _text(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key, "")
    if value is None or isinstance(value, (list, tuple, dict, set)):
        return ""
    return str(value).strip()


def _metadata_text(metadata: Mapping[str, Any], key: str) -> str:
    return _text(metadata, key)


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _object_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _first_non_empty(*values: str) -> str:
    for value in values:
        if value:
            return value
    return ""


def _related_record_id(kind: str, value: str) -> str:
    if value.startswith(f"{kind}:"):
        return value
    return f"{kind}:{value}"


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
    "HostEvidenceErrorReadbackEnvelope",
    "HostEvidenceReadbackEnvelope",
    "host_evidence_card_to_readback_envelope",
    "host_evidence_error_to_readback_envelope",
    "host_evidence_presentation_to_readback_envelopes",
    "host_evidence_summary_to_readback_envelope",
]
