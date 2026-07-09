"""Unified read-only inspection surface for readback envelopes."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from .agent_exchange_history import exchange_artifact_record_to_readback_envelope
from .exchange_store import JsonArtifactVersionStore, default_exchange_artifact_store_path
from .host_evidence_readback import host_evidence_presentation_to_readback_envelopes
from .runtime_invocation_audit import (
    JsonlRuntimeInvocationLog,
    runtime_invocation_record_to_readback_envelope,
)
from .scheduler_store import JsonlSchedulerEventLog, scheduler_event_to_readback_envelope
from .validation_readback import validation_receipt_to_readback_envelope
from .worker_trajectory_report_consumer import worker_report_to_readback_envelope

ReadbackInspectionKind = Literal[
    "worker-report",
    "validation-receipt",
    "runtime-invocation-log",
    "scheduler-event-log",
    "exchange-artifact",
    "host-evidence",
]

READBACK_INSPECTION_SUPPORTED_KINDS: tuple[str, ...] = (
    "worker-report",
    "validation-receipt",
    "runtime-invocation-log",
    "scheduler-event-log",
    "exchange-artifact",
    "host-evidence",
)


@dataclass(frozen=True, slots=True)
class ReadbackInspectionRequest:
    """Request for one read-only readback inspection."""

    project_root: str | Path
    kind: str
    path: str | Path = ""
    artifact_id: str = ""
    version: str = ""
    source_kind: str = ""
    latest_limit: int = 20
    actor: str = "readback-inspection"
    timestamp: str = ""


@dataclass(frozen=True, slots=True)
class ReadbackInspectionResult:
    """Result of a unified readback inspection."""

    ok: bool
    kind: str
    project_root: Path
    source_path: Path | None = None
    record_count: int = 0
    envelopes: tuple[Mapping[str, object], ...] = ()
    errors: tuple[str, ...] = ()
    selector: Mapping[str, object] | None = None

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "kind": self.kind,
            "project_root": str(self.project_root),
            "source_path": "" if self.source_path is None else str(self.source_path),
            "record_count": self.record_count,
            "envelopes": [dict(envelope) for envelope in self.envelopes],
            "errors": list(self.errors),
            "selector": dict(self.selector or {}),
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
            },
        }


def inspect_readback(request: ReadbackInspectionRequest) -> ReadbackInspectionResult:
    """Inspect one readback family through a read-only unified surface."""

    root = Path(request.project_root).resolve()
    kind = _normalize_kind(request.kind)
    if kind not in READBACK_INSPECTION_SUPPORTED_KINDS:
        return ReadbackInspectionResult(
            ok=False,
            kind=kind or request.kind,
            project_root=root,
            errors=(
                "unsupported readback kind "
                f"{request.kind!r}; supported kinds: "
                f"{', '.join(READBACK_INSPECTION_SUPPORTED_KINDS)}",
            ),
            selector=_selector(request),
        )
    try:
        if kind == "worker-report":
            return _inspect_worker_report(root, request)
        if kind == "validation-receipt":
            return _inspect_validation_receipt(root, request)
        if kind == "runtime-invocation-log":
            return _inspect_runtime_invocation_log(root, request)
        if kind == "scheduler-event-log":
            return _inspect_scheduler_event_log(root, request)
        if kind == "exchange-artifact":
            return _inspect_exchange_artifact(root, request)
        if kind == "host-evidence":
            return _inspect_host_evidence(root, request)
    except Exception as exc:
        return ReadbackInspectionResult(
            ok=False,
            kind=kind,
            project_root=root,
            source_path=_safe_optional_source_path(root, request.path),
            errors=(str(exc),),
            selector=_selector(request),
        )
    raise AssertionError(f"unhandled readback inspection kind: {kind}")


def _inspect_worker_report(
    root: Path,
    request: ReadbackInspectionRequest,
) -> ReadbackInspectionResult:
    path = _required_path(root, request.path, "--path is required for worker-report")
    report = _read_json_mapping(path, "worker report")
    envelope = worker_report_to_readback_envelope(
        report,
        report_path=path,
        timestamp=request.timestamp,
        actor=request.actor,
    ).to_json_dict()
    return _ok_result("worker-report", root, path, (envelope,), request)


def _inspect_validation_receipt(
    root: Path,
    request: ReadbackInspectionRequest,
) -> ReadbackInspectionResult:
    path = _required_path(
        root,
        request.path,
        "--path is required for validation-receipt",
    )
    receipt = _read_json_mapping(path, "validation receipt")
    envelope = validation_receipt_to_readback_envelope(
        receipt,
        source_kind=request.source_kind or None,
        receipt_path=path,
        timestamp=request.timestamp,
        actor=request.actor,
    ).to_json_dict()
    return _ok_result("validation-receipt", root, path, (envelope,), request)


def _inspect_runtime_invocation_log(
    root: Path,
    request: ReadbackInspectionRequest,
) -> ReadbackInspectionResult:
    path = _required_path(
        root,
        request.path,
        "--path is required for runtime-invocation-log",
    )
    records = JsonlRuntimeInvocationLog(path).read_all()
    latest = _latest(records, request.latest_limit)
    envelopes = tuple(
        runtime_invocation_record_to_readback_envelope(
            record,
            actor=request.actor,
        ).to_json_dict()
        for record in latest
    )
    return _ok_result("runtime-invocation-log", root, path, envelopes, request)


def _inspect_scheduler_event_log(
    root: Path,
    request: ReadbackInspectionRequest,
) -> ReadbackInspectionResult:
    path = _required_path(
        root,
        request.path,
        "--path is required for scheduler-event-log",
    )
    events = JsonlSchedulerEventLog(path).read_all()
    latest = _latest(events, request.latest_limit)
    envelopes = tuple(
        scheduler_event_to_readback_envelope(
            event,
            actor=request.actor,
        ).to_json_dict()
        for event in latest
    )
    return _ok_result("scheduler-event-log", root, path, envelopes, request)


def _inspect_exchange_artifact(
    root: Path,
    request: ReadbackInspectionRequest,
) -> ReadbackInspectionResult:
    path = _resolve_path(
        root,
        request.path or default_exchange_artifact_store_path(root),
    )
    if not request.artifact_id:
        raise ValueError("--artifact-id is required for exchange-artifact")
    store = JsonArtifactVersionStore(path)
    record = (
        store.get(request.artifact_id, request.version)
        if request.version
        else store.latest(request.artifact_id)
    )
    envelope = exchange_artifact_record_to_readback_envelope(
        record,
        actor=request.actor,
    ).to_json_dict()
    return _ok_result("exchange-artifact", root, path, (envelope,), request)


def _inspect_host_evidence(
    root: Path,
    request: ReadbackInspectionRequest,
) -> ReadbackInspectionResult:
    from tools.progress_graph import build_host_evidence_presentation, read_host_evidence_bundle

    evidence_dir = _resolve_path(root, request.path) if request.path else None
    bundle = read_host_evidence_bundle(root, evidence_dir=evidence_dir)
    presentation = build_host_evidence_presentation(
        bundle,
        generated_at=request.timestamp,
    )
    envelopes = tuple(
        envelope.to_json_dict()
        for envelope in host_evidence_presentation_to_readback_envelopes(
            presentation,
            actor=request.actor,
        )
    )
    return ReadbackInspectionResult(
        ok=True,
        kind="host-evidence",
        project_root=root,
        source_path=bundle.evidence_dir,
        record_count=len(envelopes),
        envelopes=envelopes,
        selector=_selector(request),
    )


def _ok_result(
    kind: str,
    root: Path,
    path: Path,
    envelopes: tuple[Mapping[str, object], ...],
    request: ReadbackInspectionRequest,
) -> ReadbackInspectionResult:
    return ReadbackInspectionResult(
        ok=True,
        kind=kind,
        project_root=root,
        source_path=path,
        record_count=len(envelopes),
        envelopes=envelopes,
        selector=_selector(request),
    )


def _read_json_mapping(path: Path, label: str) -> Mapping[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, Mapping):
        raise ValueError(f"{label} JSON must be an object: {path}")
    return payload


def _required_path(root: Path, value: str | Path, message: str) -> Path:
    if not str(value):
        raise ValueError(message)
    return _resolve_path(root, value)


def _optional_source_path(root: Path, value: str | Path) -> Path | None:
    return _resolve_path(root, value) if str(value) else None


def _safe_optional_source_path(root: Path, value: str | Path) -> Path | None:
    try:
        return _optional_source_path(root, value)
    except Exception:
        return None


def _resolve_path(root: Path, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path.resolve()
    resolved_root = root.resolve()
    resolved_path = (resolved_root / path).resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(
            f"path escapes project root: {value!s}; project_root={resolved_root}"
        ) from exc
    return resolved_path


def _latest(records: tuple[object, ...], latest_limit: int) -> tuple[object, ...]:
    if latest_limit < 0:
        return records
    if latest_limit == 0:
        return ()
    return records[-latest_limit:]


def _normalize_kind(kind: str) -> str:
    return kind.strip().lower().replace("_", "-")


def _selector(request: ReadbackInspectionRequest) -> dict[str, object]:
    return {
        "kind": _normalize_kind(request.kind),
        "path": str(request.path),
        "artifact_id": request.artifact_id,
        "version": request.version,
        "source_kind": request.source_kind,
        "latest_limit": request.latest_limit,
        "actor": request.actor,
        "timestamp": request.timestamp,
    }


__all__ = [
    "READBACK_INSPECTION_SUPPORTED_KINDS",
    "ReadbackInspectionKind",
    "ReadbackInspectionRequest",
    "ReadbackInspectionResult",
    "inspect_readback",
]
