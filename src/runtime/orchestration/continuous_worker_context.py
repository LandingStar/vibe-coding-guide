"""Project-owned compact context bundles for continuous workers.

Compact context bundles are durable, provider-neutral summaries that help a
worker continue across scheduler nodes without treating a provider session as
the source of truth. They store refs and compact summaries, not raw transcripts
or secret values.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from .artifact_paths import dbc_artifact_path
from .continuous_worker_binding import (
    ContinuousWorkerBinding,
    ContinuousWorkerScopeKind,
    DEFAULT_CONTINUOUS_WORKER_BINDING_LEDGER_RELATIVE_PATH,
    read_continuous_worker_binding_ledger,
)
from .runtime_adapter import RuntimeProviderKind


CONTINUOUS_WORKER_COMPACT_CONTEXT_SCHEMA_VERSION = (
    "continuous-worker-compact-context.v1"
)
DEFAULT_CONTINUOUS_WORKER_COMPACT_CONTEXT_DIR_RELATIVE_PATH = (
    dbc_artifact_path("runtime", "continuous-worker-contexts")
)


@dataclass(frozen=True, slots=True)
class ContinuousWorkerCompactContextBundle:
    """One compact project-owned continuity bundle for a worker binding."""

    bundle_id: str
    binding_id: str
    worker_id: str
    runtime_provider: RuntimeProviderKind
    scope_kind: ContinuousWorkerScopeKind
    scope_id: str
    lane_ids: tuple[str, ...] = ()
    created_at: str = ""
    summary: str = ""
    key_decisions: tuple[str, ...] = ()
    current_state: str = ""
    artifact_refs: tuple[str, ...] = ()
    mailbox_cursor_ref: str = ""
    worker_report_refs: tuple[str, ...] = ()
    audit_refs: tuple[str, ...] = ()
    source_context_refs: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)
    schema_version: str = CONTINUOUS_WORKER_COMPACT_CONTEXT_SCHEMA_VERSION

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "bundle_id": self.bundle_id,
            "binding_id": self.binding_id,
            "worker_id": self.worker_id,
            "runtime_provider": self.runtime_provider,
            "scope_kind": self.scope_kind,
            "scope_id": self.scope_id,
            "lane_ids": list(self.lane_ids),
            "created_at": self.created_at,
            "summary": self.summary,
            "key_decisions": list(self.key_decisions),
            "current_state": self.current_state,
            "artifact_refs": list(self.artifact_refs),
            "mailbox_cursor_ref": self.mailbox_cursor_ref,
            "worker_report_refs": list(self.worker_report_refs),
            "audit_refs": list(self.audit_refs),
            "source_context_refs": list(self.source_context_refs),
            "metadata": dict(self.metadata),
            "authority_split": _authority_split(bundle_written=False),
        }


@dataclass(frozen=True, slots=True)
class ContinuousWorkerCompactContextBuildRequest:
    """Request to build one compact context bundle from project-owned refs."""

    ledger_path: str | Path = DEFAULT_CONTINUOUS_WORKER_BINDING_LEDGER_RELATIVE_PATH
    bundle_dir_path: str | Path = DEFAULT_CONTINUOUS_WORKER_COMPACT_CONTEXT_DIR_RELATIVE_PATH
    bundle_path: str | Path = ""
    binding_id: str = ""
    scope_kind: ContinuousWorkerScopeKind | str = ""
    scope_id: str = ""
    bundle_id: str = ""
    timestamp: str = ""
    summary: str = ""
    key_decisions: tuple[str, ...] = ()
    current_state: str = ""
    artifact_refs: tuple[str, ...] = ()
    mailbox_cursor_ref: str = ""
    worker_report_refs: tuple[str, ...] = ()
    audit_refs: tuple[str, ...] = ()
    source_context_refs: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ContinuousWorkerCompactContextBuildResult:
    """Result of writing or reading one compact context bundle."""

    ok: bool
    action: str
    bundle_path: Path
    bundle: ContinuousWorkerCompactContextBundle | None = None
    compact_context_ref: str = ""
    status: str = ""
    message: str = ""
    bundle_written: bool = False

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "action": self.action,
            "status": self.status,
            "message": self.message,
            "bundle_path": str(self.bundle_path),
            "compact_context_ref": self.compact_context_ref,
            "bundle": None if self.bundle is None else self.bundle.to_json_dict(),
            "authority_split": _authority_split(bundle_written=self.bundle_written),
        }


def build_continuous_worker_compact_context_bundle(
    request: ContinuousWorkerCompactContextBuildRequest,
) -> ContinuousWorkerCompactContextBuildResult:
    """Write a compact context bundle for an active continuous worker binding."""

    if not request.summary:
        raise ValueError("continuous worker compact context requires summary")
    ledger = read_continuous_worker_binding_ledger(request.ledger_path)
    binding = _find_active_binding(
        ledger.bindings,
        binding_id=request.binding_id,
        scope_kind=request.scope_kind,
        scope_id=request.scope_id,
    )
    if binding is None:
        return ContinuousWorkerCompactContextBuildResult(
            ok=False,
            action="build",
            bundle_path=_requested_bundle_path(request, "missing-binding"),
            status="binding_not_found",
            message="active continuous worker binding not found for compact context",
            bundle_written=False,
        )

    bundle_id = request.bundle_id or _default_bundle_id(binding, request.timestamp)
    bundle_path = _requested_bundle_path(request, bundle_id)
    bundle = ContinuousWorkerCompactContextBundle(
        bundle_id=bundle_id,
        binding_id=binding.binding_id,
        worker_id=binding.worker_id,
        runtime_provider=binding.runtime_provider,
        scope_kind=binding.scope_kind,
        scope_id=binding.scope_id,
        lane_ids=binding.lane_ids,
        created_at=request.timestamp,
        summary=request.summary,
        key_decisions=_unique_nonempty(request.key_decisions),
        current_state=request.current_state,
        artifact_refs=_unique_nonempty(request.artifact_refs),
        mailbox_cursor_ref=request.mailbox_cursor_ref or binding.mailbox_cursor_ref,
        worker_report_refs=_unique_nonempty(
            (*binding.worker_report_refs, *request.worker_report_refs)
        ),
        audit_refs=_unique_nonempty((*binding.audit_refs, *request.audit_refs)),
        source_context_refs=_unique_nonempty(
            (
                *(
                    (binding.compact_context_ref,)
                    if binding.compact_context_ref
                    else ()
                ),
                *request.source_context_refs,
            )
        ),
        metadata=dict(request.metadata),
    )
    bundle_path.parent.mkdir(parents=True, exist_ok=True)
    bundle_path.write_text(
        json.dumps(bundle.to_json_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return ContinuousWorkerCompactContextBuildResult(
        ok=True,
        action="build",
        bundle_path=bundle_path,
        bundle=bundle,
        compact_context_ref=_compact_context_ref(bundle_id),
        status="built",
        message="continuous worker compact context bundle written",
        bundle_written=True,
    )


def read_continuous_worker_compact_context_bundle(
    path: str | Path,
) -> ContinuousWorkerCompactContextBundle:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("schema_version") != CONTINUOUS_WORKER_COMPACT_CONTEXT_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported continuous worker compact context schema_version: "
            f"{payload.get('schema_version')!r}"
        )
    runtime_provider = str(payload.get("runtime_provider", "opencode"))
    scope_kind = str(payload.get("scope_kind", "lane"))
    return ContinuousWorkerCompactContextBundle(
        bundle_id=str(payload.get("bundle_id", "")),
        binding_id=str(payload.get("binding_id", "")),
        worker_id=str(payload.get("worker_id", "")),
        runtime_provider=runtime_provider,  # type: ignore[arg-type]
        scope_kind=scope_kind,  # type: ignore[arg-type]
        scope_id=str(payload.get("scope_id", "")),
        lane_ids=_tuple_of_strings(payload.get("lane_ids", ())),
        created_at=str(payload.get("created_at", "")),
        summary=str(payload.get("summary", "")),
        key_decisions=_tuple_of_strings(payload.get("key_decisions", ())),
        current_state=str(payload.get("current_state", "")),
        artifact_refs=_tuple_of_strings(payload.get("artifact_refs", ())),
        mailbox_cursor_ref=str(payload.get("mailbox_cursor_ref", "")),
        worker_report_refs=_tuple_of_strings(payload.get("worker_report_refs", ())),
        audit_refs=_tuple_of_strings(payload.get("audit_refs", ())),
        source_context_refs=_tuple_of_strings(payload.get("source_context_refs", ())),
        metadata=dict(payload.get("metadata", {}) or {}),
    )


def _find_active_binding(
    bindings: tuple[ContinuousWorkerBinding, ...],
    *,
    binding_id: str,
    scope_kind: str,
    scope_id: str,
) -> ContinuousWorkerBinding | None:
    for binding in bindings:
        if binding.lifecycle_status not in {"active", "idle"}:
            continue
        if binding_id and binding.binding_id == binding_id:
            return binding
        if scope_kind and scope_id and binding.scope_kind == scope_kind and binding.scope_id == scope_id:
            return binding
    return None


def _requested_bundle_path(
    request: ContinuousWorkerCompactContextBuildRequest,
    bundle_id: str,
) -> Path:
    if request.bundle_path:
        return Path(request.bundle_path)
    return Path(request.bundle_dir_path) / f"{_safe_id(bundle_id)}.json"


def _default_bundle_id(binding: ContinuousWorkerBinding, timestamp: str) -> str:
    suffix = _safe_id(timestamp) if timestamp else "latest"
    return f"continuous-worker-context:{binding.binding_id}:{suffix}"


def _compact_context_ref(bundle_id: str) -> str:
    return f"dbc://continuous-worker-context/{bundle_id}"


def _safe_id(value: str) -> str:
    safe = value.replace("\\", "/").strip("/").replace("/", "-").replace(":", "-")
    safe = safe.replace("+", "-").replace(".", "-")
    return safe or "context"


def _tuple_of_strings(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return _unique_nonempty(tuple(str(item) for item in value))
    if isinstance(value, list):
        return _unique_nonempty(tuple(str(item) for item in value))
    return (str(value),) if str(value) else ()


def _unique_nonempty(values: tuple[str, ...]) -> tuple[str, ...]:
    normalized: list[str] = []
    for value in values:
        if value and value not in normalized:
            normalized.append(value)
    return tuple(normalized)


def _authority_split(*, bundle_written: bool) -> dict[str, object]:
    return {
        "host_owned": True,
        "compact_context_bundle_written": bundle_written,
        "provider_executed": False,
        "server_started": False,
        "server_stopped": False,
        "scheduler_state_mutated": False,
        "delivery_state_mutated": False,
        "runtime_invocation_log_mutated": False,
        "local_work_trajectory_mutated": False,
        "raw_transcript_persisted": False,
        "secret_value_persisted": False,
    }


__all__ = [
    "CONTINUOUS_WORKER_COMPACT_CONTEXT_SCHEMA_VERSION",
    "DEFAULT_CONTINUOUS_WORKER_COMPACT_CONTEXT_DIR_RELATIVE_PATH",
    "ContinuousWorkerCompactContextBuildRequest",
    "ContinuousWorkerCompactContextBuildResult",
    "ContinuousWorkerCompactContextBundle",
    "build_continuous_worker_compact_context_bundle",
    "read_continuous_worker_compact_context_bundle",
]
