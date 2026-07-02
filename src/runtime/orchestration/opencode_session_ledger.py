"""Durable host-owned OpenCode session binding ledger.

The ledger records reusable OpenCode session selectors for later
``opencode run --attach --session`` calls. It does not create sessions by
running OpenCode, store transcripts, or mutate scheduler state.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal


OPENCODE_SESSION_LEDGER_SCHEMA_VERSION = "opencode-session-ledger.v1"
DEFAULT_OPENCODE_SESSION_LEDGER_RELATIVE_PATH = (
    ".codex/runtime/opencode-session-ledger.json"
)
OpenCodeSessionBindingScope = Literal["lane", "agent", "task", "custom"]
OpenCodeSessionBindingStatus = Literal["active", "released", "expired"]


@dataclass(frozen=True, slots=True)
class OpenCodeSessionBinding:
    """One durable OpenCode session binding record."""

    binding_id: str
    scope_kind: OpenCodeSessionBindingScope
    scope_id: str
    attach_url: str
    session_id: str
    status: OpenCodeSessionBindingStatus = "active"
    created_at: str = ""
    updated_at: str = ""
    released_at: str = ""
    expires_at: str = ""
    owner_agent_id: str = ""
    lane_id: str = ""
    worker_agent_id: str = ""
    reason: str = ""
    metadata: dict[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "binding_id": self.binding_id,
            "scope_kind": self.scope_kind,
            "scope_id": self.scope_id,
            "attach_url": self.attach_url,
            "session_id": self.session_id,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "released_at": self.released_at,
            "expires_at": self.expires_at,
            "owner_agent_id": self.owner_agent_id,
            "lane_id": self.lane_id,
            "worker_agent_id": self.worker_agent_id,
            "reason": self.reason,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class OpenCodeSessionLedger:
    """Durable OpenCode session binding ledger."""

    bindings: tuple[OpenCodeSessionBinding, ...] = ()
    schema_version: str = OPENCODE_SESSION_LEDGER_SCHEMA_VERSION

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "bindings": [binding.to_json_dict() for binding in self.bindings],
        }


@dataclass(frozen=True, slots=True)
class OpenCodeSessionClaimRequest:
    """Request to claim or update one reusable OpenCode session binding."""

    ledger_path: str | Path = DEFAULT_OPENCODE_SESSION_LEDGER_RELATIVE_PATH
    scope_kind: OpenCodeSessionBindingScope = "lane"
    scope_id: str = ""
    attach_url: str = ""
    session_id: str = ""
    binding_id: str = ""
    owner_agent_id: str = ""
    lane_id: str = ""
    worker_agent_id: str = ""
    reason: str = ""
    timestamp: str = ""
    expires_at: str = ""
    replace_existing: bool = True
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class OpenCodeSessionReleaseRequest:
    """Request to release or expire one existing session binding."""

    ledger_path: str | Path = DEFAULT_OPENCODE_SESSION_LEDGER_RELATIVE_PATH
    binding_id: str = ""
    scope_kind: OpenCodeSessionBindingScope | str = ""
    scope_id: str = ""
    status: OpenCodeSessionBindingStatus = "released"
    timestamp: str = ""
    reason: str = ""


@dataclass(frozen=True, slots=True)
class OpenCodeSessionInspectRequest:
    """Read-only OpenCode session binding inspection request."""

    ledger_path: str | Path = DEFAULT_OPENCODE_SESSION_LEDGER_RELATIVE_PATH
    scope_kind: OpenCodeSessionBindingScope | str = ""
    scope_id: str = ""
    include_released: bool = False


@dataclass(frozen=True, slots=True)
class OpenCodeSessionRecoverStaleRequest:
    """Request to expire stale OpenCode session bindings explicitly."""

    ledger_path: str | Path = DEFAULT_OPENCODE_SESSION_LEDGER_RELATIVE_PATH
    now: str = ""
    timestamp: str = ""
    expire_unhealthy: bool = False
    health_path: str = "/global/health"
    health_timeout_seconds: float = 2.0
    reason: str = "stale OpenCode session binding recovery"
    username_env_var: str = "OPENCODE_SERVER_USERNAME"
    password_env_var: str = "OPENCODE_SERVER_PASSWORD"
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class OpenCodeSessionLedgerResult:
    """Result for OpenCode session ledger operations."""

    ok: bool
    action: str
    ledger_path: Path
    binding: OpenCodeSessionBinding | None = None
    bindings: tuple[OpenCodeSessionBinding, ...] = ()
    status: str = ""
    message: str = ""
    ledger_mutated: bool = False
    checked_count: int = 0
    expired_count: int = 0
    stale_reasons: dict[str, str] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "action": self.action,
            "status": self.status,
            "message": self.message,
            "ledger_path": str(self.ledger_path),
            "binding": None if self.binding is None else self.binding.to_json_dict(),
            "bindings": [binding.to_json_dict() for binding in self.bindings],
            "checked_count": self.checked_count,
            "expired_count": self.expired_count,
            "stale_reasons": dict(self.stale_reasons),
            "authority_split": {
                "host_owned": True,
                "session_ledger_mutated": self.ledger_mutated,
                "provider_executed": False,
                "server_started": False,
                "server_stopped": False,
                "scheduler_state_mutated": False,
                "delivery_state_mutated": False,
                "runtime_invocation_log_mutated": False,
                "local_work_trajectory_mutated": False,
                "raw_transcript_persisted": False,
                "secret_value_persisted": False,
            },
        }


def claim_opencode_session_binding(
    request: OpenCodeSessionClaimRequest,
) -> OpenCodeSessionLedgerResult:
    """Create or replace one active OpenCode session binding."""

    if not request.scope_id:
        raise ValueError("OpenCode session claim requires scope_id")
    if not request.attach_url:
        raise ValueError("OpenCode session claim requires attach_url")
    if not request.session_id:
        raise ValueError("OpenCode session claim requires session_id")
    _validate_scope_kind(request.scope_kind)
    ledger_path = Path(request.ledger_path)
    ledger = read_opencode_session_ledger(ledger_path)
    binding_id = request.binding_id or _binding_id(request.scope_kind, request.scope_id)
    existing = [
        binding
        for binding in ledger.bindings
        if binding.binding_id == binding_id
        or (
            binding.scope_kind == request.scope_kind
            and binding.scope_id == request.scope_id
            and binding.status == "active"
        )
    ]
    if existing and not request.replace_existing:
        return OpenCodeSessionLedgerResult(
            ok=False,
            action="claim",
            ledger_path=ledger_path,
            binding=existing[0],
            bindings=ledger.bindings,
            status="conflict",
            message="active OpenCode session binding already exists for this scope",
            ledger_mutated=False,
        )

    binding = OpenCodeSessionBinding(
        binding_id=binding_id,
        scope_kind=request.scope_kind,
        scope_id=request.scope_id,
        attach_url=request.attach_url.rstrip("/"),
        session_id=request.session_id,
        status="active",
        created_at=request.timestamp,
        updated_at=request.timestamp,
        expires_at=request.expires_at,
        owner_agent_id=request.owner_agent_id,
        lane_id=request.lane_id,
        worker_agent_id=request.worker_agent_id,
        reason=request.reason,
        metadata=dict(request.metadata),
    )
    retained = tuple(
        old
        for old in ledger.bindings
        if old.binding_id != binding_id
        and not (
            old.scope_kind == request.scope_kind
            and old.scope_id == request.scope_id
            and old.status == "active"
        )
    )
    updated = OpenCodeSessionLedger(bindings=(*retained, binding))
    write_opencode_session_ledger(updated, ledger_path)
    return OpenCodeSessionLedgerResult(
        ok=True,
        action="claim",
        ledger_path=ledger_path,
        binding=binding,
        bindings=updated.bindings,
        status="claimed",
        message="OpenCode session binding claimed",
        ledger_mutated=True,
    )


def release_opencode_session_binding(
    request: OpenCodeSessionReleaseRequest,
) -> OpenCodeSessionLedgerResult:
    """Mark an existing OpenCode session binding released or expired."""

    if request.status not in {"released", "expired"}:
        raise ValueError("OpenCode session release status must be released or expired")
    ledger_path = Path(request.ledger_path)
    ledger = read_opencode_session_ledger(ledger_path)
    target = _find_binding(
        ledger,
        binding_id=request.binding_id,
        scope_kind=request.scope_kind,
        scope_id=request.scope_id,
        include_released=False,
    )
    if target is None:
        return OpenCodeSessionLedgerResult(
            ok=False,
            action="release",
            ledger_path=ledger_path,
            bindings=ledger.bindings,
            status="not_found",
            message="active OpenCode session binding not found",
            ledger_mutated=False,
        )
    released = OpenCodeSessionBinding(
        binding_id=target.binding_id,
        scope_kind=target.scope_kind,
        scope_id=target.scope_id,
        attach_url=target.attach_url,
        session_id=target.session_id,
        status=request.status,
        created_at=target.created_at,
        updated_at=request.timestamp,
        released_at=request.timestamp,
        expires_at=target.expires_at,
        owner_agent_id=target.owner_agent_id,
        lane_id=target.lane_id,
        worker_agent_id=target.worker_agent_id,
        reason=request.reason or target.reason,
        metadata=dict(target.metadata),
    )
    updated = OpenCodeSessionLedger(
        bindings=tuple(
            released if binding.binding_id == target.binding_id else binding
            for binding in ledger.bindings
        )
    )
    write_opencode_session_ledger(updated, ledger_path)
    return OpenCodeSessionLedgerResult(
        ok=True,
        action="release",
        ledger_path=ledger_path,
        binding=released,
        bindings=updated.bindings,
        status=request.status,
        message=f"OpenCode session binding marked {request.status}",
        ledger_mutated=True,
    )


def inspect_opencode_session_bindings(
    request: OpenCodeSessionInspectRequest,
) -> OpenCodeSessionLedgerResult:
    """Inspect OpenCode session bindings without mutation."""

    ledger_path = Path(request.ledger_path)
    ledger = read_opencode_session_ledger(ledger_path)
    bindings = ledger.bindings
    if request.scope_kind:
        bindings = tuple(
            binding for binding in bindings if binding.scope_kind == request.scope_kind
        )
    if request.scope_id:
        bindings = tuple(binding for binding in bindings if binding.scope_id == request.scope_id)
    if not request.include_released:
        bindings = tuple(binding for binding in bindings if binding.status == "active")
    return OpenCodeSessionLedgerResult(
        ok=True,
        action="inspect",
        ledger_path=ledger_path,
        bindings=bindings,
        status="inspected",
        message=f"{len(bindings)} OpenCode session binding(s) matched",
        ledger_mutated=False,
    )


def recover_stale_opencode_session_bindings(
    request: OpenCodeSessionRecoverStaleRequest,
    *,
    health_inspector=None,
) -> OpenCodeSessionLedgerResult:
    """Expire active bindings whose receipt is stale by explicit policy."""

    if not request.now:
        raise ValueError("OpenCode stale session recovery requires now")
    if request.health_timeout_seconds <= 0:
        raise ValueError("OpenCode stale session recovery health timeout must be positive")
    now = _parse_timestamp(request.now, "now")
    ledger_path = Path(request.ledger_path)
    ledger = read_opencode_session_ledger(ledger_path)
    health_inspector = health_inspector or _default_health_inspector
    expired_ids: set[str] = set()
    stale_reasons: dict[str, str] = {}
    checked = 0

    for binding in ledger.bindings:
        if binding.status != "active":
            continue
        checked += 1
        reason = _binding_stale_reason_by_expiry(binding, now)
        if not reason and request.expire_unhealthy:
            reason = health_inspector(binding, request)
        if reason:
            expired_ids.add(binding.binding_id)
            stale_reasons[binding.binding_id] = reason

    if not expired_ids:
        return OpenCodeSessionLedgerResult(
            ok=True,
            action="recover-stale",
            ledger_path=ledger_path,
            bindings=ledger.bindings,
            status="no_stale_bindings",
            message="No stale OpenCode session bindings matched the recovery policy",
            ledger_mutated=False,
            checked_count=checked,
            expired_count=0,
            stale_reasons=stale_reasons,
        )

    timestamp = request.timestamp or request.now
    updated_bindings = tuple(
        _expire_binding(binding, timestamp=timestamp, reason=stale_reasons[binding.binding_id])
        if binding.binding_id in expired_ids
        else binding
        for binding in ledger.bindings
    )
    updated = OpenCodeSessionLedger(bindings=updated_bindings)
    write_opencode_session_ledger(updated, ledger_path)
    expired = tuple(binding for binding in updated_bindings if binding.binding_id in expired_ids)
    return OpenCodeSessionLedgerResult(
        ok=True,
        action="recover-stale",
        ledger_path=ledger_path,
        bindings=expired,
        status="expired_stale_bindings",
        message=f"Expired {len(expired)} stale OpenCode session binding(s)",
        ledger_mutated=True,
        checked_count=checked,
        expired_count=len(expired),
        stale_reasons=stale_reasons,
    )


def read_opencode_session_ledger(path: str | Path) -> OpenCodeSessionLedger:
    ledger_path = Path(path)
    if not ledger_path.exists():
        return OpenCodeSessionLedger()
    payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != OPENCODE_SESSION_LEDGER_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported OpenCode session ledger schema_version: "
            f"{payload.get('schema_version')!r}"
        )
    return OpenCodeSessionLedger(
        bindings=tuple(
            _binding_from_json_dict(item) for item in payload.get("bindings", [])
        )
    )


def write_opencode_session_ledger(
    ledger: OpenCodeSessionLedger,
    path: str | Path,
) -> None:
    ledger_path = Path(path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        json.dumps(ledger.to_json_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _find_binding(
    ledger: OpenCodeSessionLedger,
    *,
    binding_id: str = "",
    scope_kind: str = "",
    scope_id: str = "",
    include_released: bool,
) -> OpenCodeSessionBinding | None:
    for binding in ledger.bindings:
        if not include_released and binding.status != "active":
            continue
        if binding_id and binding.binding_id == binding_id:
            return binding
        if scope_kind and scope_id and binding.scope_kind == scope_kind and binding.scope_id == scope_id:
            return binding
    return None


def _binding_from_json_dict(payload: dict[str, object]) -> OpenCodeSessionBinding:
    scope_kind = str(payload.get("scope_kind", ""))
    _validate_scope_kind(scope_kind)
    status = str(payload.get("status", "active"))
    if status not in {"active", "released", "expired"}:
        raise ValueError(f"Invalid OpenCode session binding status: {status!r}")
    return OpenCodeSessionBinding(
        binding_id=str(payload.get("binding_id", "")),
        scope_kind=scope_kind,  # type: ignore[arg-type]
        scope_id=str(payload.get("scope_id", "")),
        attach_url=str(payload.get("attach_url", "")),
        session_id=str(payload.get("session_id", "")),
        status=status,  # type: ignore[arg-type]
        created_at=str(payload.get("created_at", "")),
        updated_at=str(payload.get("updated_at", "")),
        released_at=str(payload.get("released_at", "")),
        expires_at=str(payload.get("expires_at", "")),
        owner_agent_id=str(payload.get("owner_agent_id", "")),
        lane_id=str(payload.get("lane_id", "")),
        worker_agent_id=str(payload.get("worker_agent_id", "")),
        reason=str(payload.get("reason", "")),
        metadata=dict(payload.get("metadata", {}) or {}),
    )


def _expire_binding(
    binding: OpenCodeSessionBinding,
    *,
    timestamp: str,
    reason: str,
) -> OpenCodeSessionBinding:
    metadata = dict(binding.metadata)
    metadata["stale_recovery_reason"] = reason
    return OpenCodeSessionBinding(
        binding_id=binding.binding_id,
        scope_kind=binding.scope_kind,
        scope_id=binding.scope_id,
        attach_url=binding.attach_url,
        session_id=binding.session_id,
        status="expired",
        created_at=binding.created_at,
        updated_at=timestamp,
        released_at=timestamp,
        expires_at=binding.expires_at,
        owner_agent_id=binding.owner_agent_id,
        lane_id=binding.lane_id,
        worker_agent_id=binding.worker_agent_id,
        reason=reason,
        metadata=metadata,
    )


def _binding_stale_reason_by_expiry(
    binding: OpenCodeSessionBinding,
    now: datetime,
) -> str:
    if not binding.expires_at:
        return ""
    expires_at = _parse_timestamp(binding.expires_at, "expires_at")
    if expires_at <= now:
        return "expires_at elapsed"
    return ""


def _parse_timestamp(value: str, field_name: str) -> datetime:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(
            f"OpenCode stale session recovery {field_name} must be ISO-8601"
        ) from exc


def _default_health_inspector(
    binding: OpenCodeSessionBinding,
    request: OpenCodeSessionRecoverStaleRequest,
) -> str:
    from .opencode_serve_lifecycle import (
        OpenCodeServeReadinessRequest,
        inspect_opencode_serve_readiness,
    )

    report = inspect_opencode_serve_readiness(
        OpenCodeServeReadinessRequest(
            attach_url=binding.attach_url,
            health_path=request.health_path,
            health_timeout_seconds=request.health_timeout_seconds,
            require_healthy=True,
            username_env_var=request.username_env_var,
            password_env_var=request.password_env_var,
            metadata={
                "binding_id": binding.binding_id,
                "scope_kind": binding.scope_kind,
                "scope_id": binding.scope_id,
            },
        )
    )
    if report.ready:
        return ""
    return f"attach target unhealthy: {report.error_kind or report.summary}"


def _binding_id(scope_kind: str, scope_id: str) -> str:
    safe_scope = scope_id.replace("\\", "/").strip("/").replace("/", "-").replace(":", "-")
    return f"opencode-session:{scope_kind}:{safe_scope}"


def _validate_scope_kind(scope_kind: str) -> None:
    if scope_kind not in {"lane", "agent", "task", "custom"}:
        raise ValueError("OpenCode session scope_kind must be lane, agent, task, or custom")


__all__ = [
    "DEFAULT_OPENCODE_SESSION_LEDGER_RELATIVE_PATH",
    "OPENCODE_SESSION_LEDGER_SCHEMA_VERSION",
    "OpenCodeSessionBinding",
    "OpenCodeSessionBindingScope",
    "OpenCodeSessionBindingStatus",
    "OpenCodeSessionClaimRequest",
    "OpenCodeSessionInspectRequest",
    "OpenCodeSessionLedger",
    "OpenCodeSessionLedgerResult",
    "OpenCodeSessionRecoverStaleRequest",
    "OpenCodeSessionReleaseRequest",
    "claim_opencode_session_binding",
    "inspect_opencode_session_bindings",
    "read_opencode_session_ledger",
    "recover_stale_opencode_session_bindings",
    "release_opencode_session_binding",
    "write_opencode_session_ledger",
]
