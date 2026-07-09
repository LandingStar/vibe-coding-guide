"""Read-only validation / doctor receipt readback projections."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .log_readback import LogRecordRef


@dataclass(frozen=True, slots=True)
class ValidationReceiptReadbackEnvelope:
    """Human/audit-oriented readback projection for validation receipts."""

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
    source_kind: str = ""
    profile: str = ""
    check_id: str = ""
    governance_status: str = ""
    overall_status: str = ""
    has_blocking: bool = False
    counts: Mapping[str, int] | None = None
    remediation_count: int = 0
    evidence_key_count: int = 0
    read_only: bool = True
    provider_executed: bool = False
    mcp_server_started: bool = False
    mcp_tool_called: bool = False
    config_mutated: bool = False
    secret_material_read: bool = False

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
            "source_kind": self.source_kind,
            "profile": self.profile,
            "check_id": self.check_id,
            "governance_status": self.governance_status,
            "overall_status": self.overall_status,
            "has_blocking": self.has_blocking,
            "counts": dict(self.counts or {}),
            "remediation_count": self.remediation_count,
            "evidence_key_count": self.evidence_key_count,
            "read_only": self.read_only,
            "provider_executed": self.provider_executed,
            "mcp_server_started": self.mcp_server_started,
            "mcp_tool_called": self.mcp_tool_called,
            "config_mutated": self.config_mutated,
            "secret_material_read": self.secret_material_read,
            "authority_split": {
                "read_model_only": True,
                "validation_semantics_changed": False,
                "doctor_profile_changed": False,
                "provider_executed": self.provider_executed,
                "mcp_server_started": self.mcp_server_started,
                "mcp_tool_called": self.mcp_tool_called,
                "config_mutated": self.config_mutated,
                "secret_material_read": self.secret_material_read,
                "scheduler_state_mutated": False,
                "exchange_store_mutated": False,
                "local_work_trajectory_mutated": False,
            },
        }


def validation_receipt_to_readback_envelope(
    receipt: Mapping[str, Any],
    *,
    source_kind: str | None = None,
    receipt_path: str | Path = "",
    timestamp: str = "",
    actor: str = "validation-readback",
) -> ValidationReceiptReadbackEnvelope:
    """Project a validation/doctor/self-check receipt into a draft envelope.

    This is a read-only projection. It does not rerun validation, change doctor
    profiles, mutate configuration, execute providers, or expose raw evidence
    values.
    """

    kind = source_kind or _infer_source_kind(receipt)
    if kind == "self_check_result":
        return _self_check_result_envelope(
            receipt,
            receipt_path=receipt_path,
            timestamp=timestamp,
            actor=actor,
        )
    if kind == "constraint_result":
        return _constraint_result_envelope(
            receipt,
            receipt_path=receipt_path,
            timestamp=timestamp,
            actor=actor,
        )
    return _self_check_report_envelope(
        receipt,
        receipt_path=receipt_path,
        timestamp=timestamp,
        actor=actor,
    )


def _self_check_report_envelope(
    receipt: Mapping[str, Any],
    *,
    receipt_path: str | Path,
    timestamp: str,
    actor: str,
) -> ValidationReceiptReadbackEnvelope:
    profile = _text(receipt, "profile")
    overall_status = _text(receipt, "overall_status") or "unknown"
    project_root = _text(receipt, "project_root")
    counts = _int_mapping(receipt.get("counts"))
    checks = _mapping_sequence(receipt.get("checks"))
    next_actions = _string_tuple(receipt.get("next_actions"))
    authority = _authority(receipt.get("authority_split"))
    record_id = _first_non_empty(profile and f"doctor:{profile}", _path_or_default(receipt_path, "doctor-report"))
    failed_count = counts.get("failed", 0)
    warning_count = counts.get("warning", 0)
    skipped_count = counts.get("skipped", 0)
    return ValidationReceiptReadbackEnvelope(
        schema_version="validation-receipt-readback-envelope.v1",
        record_id=record_id,
        record_kind="validation_receipt",
        timestamp=timestamp,
        actor=actor,
        action=f"doctor_profile_{overall_status}",
        status=overall_status,
        summary=_doctor_report_summary(profile, overall_status, counts, check_count=len(checks)),
        reason=_doctor_report_reason(
            overall_status,
            failed_count=failed_count,
            warning_count=warning_count,
            skipped_count=skipped_count,
        ),
        correlation_id=_first_non_empty(project_root, profile, record_id),
        subject_refs=_doctor_report_subject_refs(record_id, profile, project_root),
        input_refs=_doctor_report_input_refs(profile),
        output_refs=(),
        evidence_refs=_doctor_report_evidence_refs(
            record_id=record_id,
            receipt_path=receipt_path,
            checks=checks,
            next_actions=next_actions,
        ),
        related_record_ids=_doctor_report_related_ids(
            profile=profile,
            project_root=project_root,
            checks=checks,
        ),
        next_hint=_doctor_report_next_hint(overall_status, next_actions),
        source_kind="self_check_report",
        profile=profile,
        overall_status=overall_status,
        has_blocking=overall_status == "failed",
        counts=counts,
        remediation_count=len(next_actions),
        evidence_key_count=sum(len(_evidence_keys(check)) for check in checks),
        **authority,
    )


def _self_check_result_envelope(
    receipt: Mapping[str, Any],
    *,
    receipt_path: str | Path,
    timestamp: str,
    actor: str,
) -> ValidationReceiptReadbackEnvelope:
    check_id = _text(receipt, "check_id")
    status = _text(receipt, "status") or "unknown"
    profiles = _string_tuple(receipt.get("profiles"))
    title = _text(receipt, "title")
    suspected_problem = _text(receipt, "suspected_problem")
    remediation = _string_tuple(receipt.get("remediation"))
    evidence_keys = _evidence_keys(receipt)
    authority = _authority(receipt.get("authority_split"))
    record_id = _first_non_empty(
        check_id and f"doctor-check:{check_id}",
        _path_or_default(receipt_path, "doctor-check"),
    )
    return ValidationReceiptReadbackEnvelope(
        schema_version="validation-receipt-readback-envelope.v1",
        record_id=record_id,
        record_kind="validation_receipt",
        timestamp=timestamp,
        actor=actor,
        action=f"doctor_check_{status}",
        status=status,
        summary=_self_check_result_summary(check_id, title, status, receipt),
        reason=_self_check_result_reason(status, suspected_problem, remediation),
        correlation_id=_first_non_empty(check_id, profiles[0] if profiles else "", record_id),
        subject_refs=_self_check_result_subject_refs(check_id, profiles),
        input_refs=_self_check_result_input_refs(profiles),
        output_refs=(),
        evidence_refs=_self_check_result_evidence_refs(
            record_id=record_id,
            receipt_path=receipt_path,
            evidence_keys=evidence_keys,
            remediation=remediation,
        ),
        related_record_ids=_self_check_result_related_ids(check_id, profiles),
        next_hint=_self_check_result_next_hint(status, remediation),
        source_kind="self_check_result",
        profile=profiles[0] if len(profiles) == 1 else ",".join(profiles),
        check_id=check_id,
        overall_status=status,
        has_blocking=status == "failed",
        remediation_count=len(remediation),
        evidence_key_count=len(evidence_keys),
        **authority,
    )


def _constraint_result_envelope(
    receipt: Mapping[str, Any],
    *,
    receipt_path: str | Path,
    timestamp: str,
    actor: str,
) -> ValidationReceiptReadbackEnvelope:
    governance_status = _text(receipt, "governance_status") or "unknown"
    command_status = _text(receipt, "command_status") or "unknown"
    has_blocking = bool(receipt.get("has_blocking"))
    current_phase = _text(receipt, "current_phase")
    active_gate = _text(receipt, "active_planning_gate")
    state_source = _text(receipt, "state_source")
    blocking_constraints = _string_tuple(receipt.get("blocking_constraints"))
    violations = _mapping_sequence(receipt.get("violations"))
    reread = _string_tuple(receipt.get("files_to_reread"))
    machine_checked = _mapping_sequence(receipt.get("machine_checked_constraints"))
    instruction_layer = _mapping_sequence(receipt.get("instruction_layer_constraints"))
    record_id = _first_non_empty(
        state_source and f"validate:{state_source}",
        _path_or_default(receipt_path, "validate-result"),
    )
    return ValidationReceiptReadbackEnvelope(
        schema_version="validation-receipt-readback-envelope.v1",
        record_id=record_id,
        record_kind="validation_receipt",
        timestamp=timestamp,
        actor=actor,
        action=f"validate_{governance_status}",
        status=governance_status,
        summary=_constraint_result_summary(
            governance_status=governance_status,
            current_phase=current_phase,
            active_gate=active_gate,
            blocking_constraints=blocking_constraints,
        ),
        reason=_constraint_result_reason(
            has_blocking=has_blocking,
            violations=violations,
            state_source=state_source,
        ),
        correlation_id=_first_non_empty(active_gate, current_phase, state_source, record_id),
        subject_refs=_constraint_result_subject_refs(
            record_id=record_id,
            current_phase=current_phase,
            active_gate=active_gate,
            state_source=state_source,
        ),
        input_refs=_constraint_result_input_refs(reread),
        output_refs=(),
        evidence_refs=_constraint_result_evidence_refs(
            record_id=record_id,
            receipt_path=receipt_path,
            blocking_constraints=blocking_constraints,
            violations=violations,
            machine_checked=machine_checked,
            instruction_layer=instruction_layer,
        ),
        related_record_ids=_constraint_result_related_ids(
            current_phase=current_phase,
            active_gate=active_gate,
            blocking_constraints=blocking_constraints,
            reread=reread,
        ),
        next_hint=_constraint_result_next_hint(has_blocking, violations),
        source_kind="constraint_result",
        governance_status=governance_status,
        overall_status=command_status,
        has_blocking=has_blocking,
        counts={
            "blocking_constraints": len(blocking_constraints),
            "violations": len(violations),
            "files_to_reread": len(reread),
            "machine_checked_constraints": len(machine_checked),
            "instruction_layer_constraints": len(instruction_layer),
        },
        remediation_count=len(violations),
        evidence_key_count=len(blocking_constraints) + len(violations),
    )


def _infer_source_kind(receipt: Mapping[str, Any]) -> str:
    schema_version = _text(receipt, "schema_version")
    if schema_version == "self-check-result/v1" or "check_id" in receipt:
        return "self_check_result"
    if schema_version == "self-check-report/v1" or "checks" in receipt:
        return "self_check_report"
    if "governance_status" in receipt or "blocking_constraints" in receipt:
        return "constraint_result"
    return "self_check_report"


def _doctor_report_summary(
    profile: str,
    overall_status: str,
    counts: Mapping[str, int],
    *,
    check_count: int,
) -> str:
    return (
        f"Doctor profile {profile or 'unknown'} completed with status "
        f"{overall_status}; {check_count} check(s), "
        f"{counts.get('ok', 0)} ok, {counts.get('warning', 0)} warning, "
        f"{counts.get('failed', 0)} failed, {counts.get('skipped', 0)} skipped."
    )


def _doctor_report_reason(
    overall_status: str,
    *,
    failed_count: int,
    warning_count: int,
    skipped_count: int,
) -> str:
    if overall_status == "failed":
        return f"At least one doctor check failed; failed check count is {failed_count}."
    if overall_status == "warning":
        return f"Doctor reported warning-level issues; warning count is {warning_count}."
    if overall_status == "skipped":
        return f"Doctor checks were skipped or unavailable; skipped count is {skipped_count}."
    return "Doctor checks completed without warning or failure status."


def _doctor_report_subject_refs(
    record_id: str,
    profile: str,
    project_root: str,
) -> tuple[LogRecordRef, ...]:
    refs = [LogRecordRef(kind="doctor_report", id=record_id, role="subject")]
    if profile:
        refs.append(LogRecordRef(kind="doctor_profile", id=profile, role="subject"))
    if project_root:
        refs.append(LogRecordRef(kind="workspace", path=project_root, role="subject"))
    return tuple(refs)


def _doctor_report_input_refs(profile: str) -> tuple[LogRecordRef, ...]:
    refs = [
        LogRecordRef(
            kind="contract",
            path="docs/self-check-doctor-contract.md",
            label="Self-check / Doctor Contract",
            role="input",
        )
    ]
    if profile:
        refs.append(LogRecordRef(kind="doctor_profile", id=profile, role="input"))
    return tuple(refs)


def _doctor_report_evidence_refs(
    *,
    record_id: str,
    receipt_path: str | Path,
    checks: tuple[Mapping[str, Any], ...],
    next_actions: tuple[str, ...],
) -> tuple[LogRecordRef, ...]:
    refs = [
        LogRecordRef(
            kind="doctor_report",
            id=record_id,
            path=str(receipt_path) if receipt_path else "",
            role="evidence",
        )
    ]
    refs.extend(
        LogRecordRef(
            kind="doctor_check",
            id=_text(check, "check_id"),
            label=_text(check, "status"),
            role="evidence",
        )
        for check in checks
        if _text(check, "check_id")
    )
    refs.extend(
        LogRecordRef(
            kind="remediation",
            id=f"{record_id}:remediation-{index}",
            label=_bounded_text(action),
            role="evidence",
        )
        for index, action in enumerate(next_actions)
    )
    return tuple(refs)


def _doctor_report_related_ids(
    *,
    profile: str,
    project_root: str,
    checks: tuple[Mapping[str, Any], ...],
) -> tuple[str, ...]:
    related: list[str] = []
    if profile:
        related.append(_related_record_id("doctor_profile", profile))
    if project_root:
        related.append(_related_record_id("workspace", project_root))
    related.extend(
        _related_record_id("doctor_check", _text(check, "check_id"))
        for check in checks
        if _text(check, "check_id")
    )
    return tuple(dict.fromkeys(related))


def _doctor_report_next_hint(overall_status: str, next_actions: tuple[str, ...]) -> str:
    if next_actions:
        return _bounded_text(next_actions[0])
    if overall_status == "ok":
        return "No doctor remediation is required; inspect individual checks for evidence."
    return "Inspect doctor checks for remediation details."


def _self_check_result_summary(
    check_id: str,
    title: str,
    status: str,
    receipt: Mapping[str, Any],
) -> str:
    provided = _text(receipt, "summary")
    if provided:
        return _bounded_text(provided)
    return f"Doctor check {check_id or title or 'unknown'} completed with status {status}."


def _self_check_result_reason(
    status: str,
    suspected_problem: str,
    remediation: tuple[str, ...],
) -> str:
    if suspected_problem:
        return f"Suspected problem: {suspected_problem}."
    if status in {"failed", "warning", "skipped"} and remediation:
        return "Check did not complete as ok; remediation is available."
    if status == "ok":
        return "Check completed successfully."
    return "Check recorded for readback and audit."


def _self_check_result_subject_refs(
    check_id: str,
    profiles: tuple[str, ...],
) -> tuple[LogRecordRef, ...]:
    refs: list[LogRecordRef] = []
    if check_id:
        refs.append(LogRecordRef(kind="doctor_check", id=check_id, role="subject"))
    refs.extend(
        LogRecordRef(kind="doctor_profile", id=profile, role="subject")
        for profile in profiles
    )
    return tuple(refs)


def _self_check_result_input_refs(profiles: tuple[str, ...]) -> tuple[LogRecordRef, ...]:
    refs = [
        LogRecordRef(
            kind="contract",
            path="docs/self-check-doctor-contract.md",
            label="Self-check / Doctor Contract",
            role="input",
        )
    ]
    refs.extend(
        LogRecordRef(kind="doctor_profile", id=profile, role="input")
        for profile in profiles
    )
    return tuple(refs)


def _self_check_result_evidence_refs(
    *,
    record_id: str,
    receipt_path: str | Path,
    evidence_keys: tuple[str, ...],
    remediation: tuple[str, ...],
) -> tuple[LogRecordRef, ...]:
    refs = [
        LogRecordRef(
            kind="doctor_check",
            id=record_id,
            path=str(receipt_path) if receipt_path else "",
            role="evidence",
        )
    ]
    refs.extend(
        LogRecordRef(
            kind="evidence_key",
            id=key,
            label="value omitted",
            role="evidence",
        )
        for key in evidence_keys
    )
    refs.extend(
        LogRecordRef(
            kind="remediation",
            id=f"{record_id}:remediation-{index}",
            label=_bounded_text(item),
            role="evidence",
        )
        for index, item in enumerate(remediation)
    )
    return tuple(refs)


def _self_check_result_related_ids(
    check_id: str,
    profiles: tuple[str, ...],
) -> tuple[str, ...]:
    related: list[str] = []
    if check_id:
        related.append(_related_record_id("doctor_check", check_id))
    related.extend(_related_record_id("doctor_profile", profile) for profile in profiles)
    return tuple(dict.fromkeys(related))


def _self_check_result_next_hint(status: str, remediation: tuple[str, ...]) -> str:
    if remediation:
        return _bounded_text(remediation[0])
    if status == "ok":
        return "No remediation is required; inspect evidence keys if needed."
    return "Inspect the doctor check evidence keys and host configuration."


def _constraint_result_summary(
    *,
    governance_status: str,
    current_phase: str,
    active_gate: str,
    blocking_constraints: tuple[str, ...],
) -> str:
    target = current_phase or "project"
    if governance_status == "blocked":
        return (
            f"Validation for {target} is blocked by "
            f"{', '.join(blocking_constraints) or 'governance constraints'}."
        )
    if active_gate:
        return f"Validation for {target} passed with active gate {active_gate}."
    return f"Validation for {target} passed with no active planning gate."


def _constraint_result_reason(
    *,
    has_blocking: bool,
    violations: tuple[Mapping[str, Any], ...],
    state_source: str,
) -> str:
    if has_blocking:
        first = violations[0] if violations else {}
        message = _text(first, "message")
        return _bounded_text(message or "Validation reported blocking constraints.")
    if state_source:
        return f"Validation state was read from {state_source}."
    return "Validation completed without blocking governance constraints."


def _constraint_result_subject_refs(
    *,
    record_id: str,
    current_phase: str,
    active_gate: str,
    state_source: str,
) -> tuple[LogRecordRef, ...]:
    refs = [LogRecordRef(kind="validation_result", id=record_id, role="subject")]
    if current_phase:
        refs.append(LogRecordRef(kind="phase", id=current_phase, role="subject"))
    if active_gate:
        refs.append(LogRecordRef(kind="planning_gate", path=active_gate, role="subject"))
    if state_source:
        refs.append(LogRecordRef(kind="state_source", id=state_source, role="subject"))
    return tuple(refs)


def _constraint_result_input_refs(reread: tuple[str, ...]) -> tuple[LogRecordRef, ...]:
    refs = [
        LogRecordRef(
            kind="contract",
            path="design_docs/Project Master Checklist.md",
            label="Checklist hot state",
            role="input",
        )
    ]
    refs.extend(LogRecordRef(kind="file", path=path, role="input") for path in reread)
    seen: set[tuple[str, str, str, str]] = set()
    unique: list[LogRecordRef] = []
    for ref in refs:
        key = (ref.kind, ref.id, ref.path, ref.role)
        if key in seen:
            continue
        seen.add(key)
        unique.append(ref)
    return tuple(unique)


def _constraint_result_evidence_refs(
    *,
    record_id: str,
    receipt_path: str | Path,
    blocking_constraints: tuple[str, ...],
    violations: tuple[Mapping[str, Any], ...],
    machine_checked: tuple[Mapping[str, Any], ...],
    instruction_layer: tuple[Mapping[str, Any], ...],
) -> tuple[LogRecordRef, ...]:
    refs = [
        LogRecordRef(
            kind="validation_result",
            id=record_id,
            path=str(receipt_path) if receipt_path else "",
            role="evidence",
        )
    ]
    refs.extend(
        LogRecordRef(kind="constraint", id=constraint, label="blocking", role="evidence")
        for constraint in blocking_constraints
    )
    refs.extend(
        LogRecordRef(
            kind="constraint_violation",
            id=_first_non_empty(_text(violation, "constraint"), f"violation-{index}"),
            label=_text(violation, "severity"),
            role="evidence",
        )
        for index, violation in enumerate(violations)
    )
    refs.extend(
        LogRecordRef(
            kind="constraint_scope",
            id=_text(scope, "constraint"),
            label=_text(scope, "enforcement"),
            role="evidence",
        )
        for scope in (*machine_checked, *instruction_layer)
        if _text(scope, "constraint")
    )
    return tuple(refs)


def _constraint_result_related_ids(
    *,
    current_phase: str,
    active_gate: str,
    blocking_constraints: tuple[str, ...],
    reread: tuple[str, ...],
) -> tuple[str, ...]:
    related: list[str] = []
    if current_phase:
        related.append(_related_record_id("phase", current_phase))
    if active_gate:
        related.append(_related_record_id("planning_gate", active_gate))
    related.extend(_related_record_id("constraint", item) for item in blocking_constraints)
    related.extend(_related_record_id("file", item) for item in reread)
    return tuple(dict.fromkeys(related))


def _constraint_result_next_hint(
    has_blocking: bool,
    violations: tuple[Mapping[str, Any], ...],
) -> str:
    if has_blocking:
        first = violations[0] if violations else {}
        message = _text(first, "message")
        if message:
            return _bounded_text(message)
        return "Resolve blocking governance constraints before implementation."
    return "Proceed according to Checklist current focus and active planning gate state."


def _authority(value: object) -> dict[str, bool]:
    payload = value if isinstance(value, Mapping) else {}
    return {
        "read_only": bool(payload.get("read_only", True)),
        "provider_executed": bool(payload.get("provider_executed", False)),
        "mcp_server_started": bool(payload.get("mcp_server_started", False)),
        "mcp_tool_called": bool(payload.get("mcp_tool_called", False)),
        "config_mutated": bool(payload.get("config_mutated", False)),
        "secret_material_read": bool(payload.get("secret_material_read", False)),
    }


def _evidence_keys(receipt: Mapping[str, Any]) -> tuple[str, ...]:
    evidence = receipt.get("evidence")
    if not isinstance(evidence, Mapping):
        return ()
    return tuple(str(key) for key in evidence.keys())


def _mapping_sequence(value: object) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return ()
    return tuple(item for item in value if isinstance(item, Mapping))


def _int_mapping(value: object) -> dict[str, int]:
    if not isinstance(value, Mapping):
        return {}
    result: dict[str, int] = {}
    for key, raw in value.items():
        try:
            result[str(key)] = int(raw)
        except (TypeError, ValueError):
            result[str(key)] = 0
    return result


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes, bytearray)):
        return ()
    return tuple(str(item) for item in value if str(item))


def _text(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key, "")
    if value is None or isinstance(value, (list, tuple, dict, set)):
        return ""
    return str(value).strip()


def _path_or_default(value: str | Path, default: str) -> str:
    if not value:
        return default
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


def _bounded_text(value: str, *, limit: int = 240) -> str:
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
    "ValidationReceiptReadbackEnvelope",
    "validation_receipt_to_readback_envelope",
]
