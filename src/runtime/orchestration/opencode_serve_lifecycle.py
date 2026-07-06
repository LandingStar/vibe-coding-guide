"""Host-owned OpenCode serve readiness and attach-target inspection.

This module intentionally does not make the scheduler own ``opencode serve``.
It provides a credential-safe readback surface that a host can use before
running OpenCode workers with ``opencode run --attach``.
"""

from __future__ import annotations

import base64
import json
import os
import shutil
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from typing import Literal
from urllib.parse import urljoin

from .artifact_paths import dbc_artifact_path


DEFAULT_OPENCODE_SERVE_HOSTNAME = "127.0.0.1"
DEFAULT_OPENCODE_SERVE_PORT = 4096
DEFAULT_OPENCODE_SERVE_HEALTH_PATH = "/global/health"
DEFAULT_OPENCODE_SERVER_USERNAME_ENV_VAR = "OPENCODE_SERVER_USERNAME"
DEFAULT_OPENCODE_SERVER_PASSWORD_ENV_VAR = "OPENCODE_SERVER_PASSWORD"
DEFAULT_OPENCODE_SERVE_LIFECYCLE_LEDGER_RELATIVE_PATH = (
    dbc_artifact_path("runtime", "opencode-serve-lifecycle-ledger.json")
)
OPENCODE_SERVE_LIFECYCLE_LEDGER_SCHEMA_VERSION = "opencode-serve-lifecycle-ledger.v1"
OpenCodeServeLifecycleAction = Literal["start", "stop", "restart", "status", "external"]
OpenCodeServeLifecycleStatus = Literal["planned", "observed", "succeeded", "failed"]


@dataclass(frozen=True, slots=True)
class OpenCodeServeReadinessRequest:
    """Request for credential-safe OpenCode serve readiness inspection."""

    executable: str = "opencode"
    hostname: str = DEFAULT_OPENCODE_SERVE_HOSTNAME
    port: int = DEFAULT_OPENCODE_SERVE_PORT
    attach_url: str = ""
    health_path: str = DEFAULT_OPENCODE_SERVE_HEALTH_PATH
    health_timeout_seconds: float = 2.0
    require_healthy: bool = False
    username_env_var: str = DEFAULT_OPENCODE_SERVER_USERNAME_ENV_VAR
    password_env_var: str = DEFAULT_OPENCODE_SERVER_PASSWORD_ENV_VAR
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class OpenCodeServeReadinessReport:
    """Credential-safe OpenCode serve readiness report."""

    executable: str
    executable_resolved: str
    cli_available: bool
    attach_url: str
    health_url: str
    health_checked: bool
    healthy: bool
    ready: bool
    http_status: int | None = None
    error_kind: str = ""
    raw_error_type: str = ""
    summary: str = ""
    auth_configured: bool = False
    username_env_var: str = DEFAULT_OPENCODE_SERVER_USERNAME_ENV_VAR
    password_env_var: str = DEFAULT_OPENCODE_SERVER_PASSWORD_ENV_VAR
    metadata: Mapping[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "executable": self.executable,
            "executable_resolved": self.executable_resolved,
            "cli_available": self.cli_available,
            "attach_url": self.attach_url,
            "health_url": self.health_url,
            "health_checked": self.health_checked,
            "healthy": self.healthy,
            "ready": self.ready,
            "http_status": self.http_status,
            "error_kind": self.error_kind,
            "raw_error_type": self.raw_error_type,
            "summary": self.summary,
            "auth_configured": self.auth_configured,
            "username_env_var": self.username_env_var,
            "password_env_var": self.password_env_var,
            "metadata": dict(self.metadata),
            "authority_split": {
                "host_owned": True,
                "server_started": False,
                "server_stopped": False,
                "server_process_owned_by_scheduler": False,
                "provider_executed": False,
                "scheduler_state_mutated": False,
                "delivery_state_mutated": False,
                "runtime_invocation_log_mutated": False,
                "local_work_trajectory_mutated": False,
                "raw_transcript_persisted": False,
                "secret_value_persisted": False,
            },
        }


@dataclass(frozen=True, slots=True)
class OpenCodeServeLifecycleReceipt:
    """One host-owned OpenCode serve lifecycle receipt."""

    receipt_id: str
    action: OpenCodeServeLifecycleAction
    status: OpenCodeServeLifecycleStatus
    attach_url: str
    command_preview: tuple[str, ...] = ()
    timestamp: str = ""
    hostname: str = DEFAULT_OPENCODE_SERVE_HOSTNAME
    port: int = DEFAULT_OPENCODE_SERVE_PORT
    executable: str = "opencode"
    pid: str = ""
    process_ref: str = ""
    actor: str = ""
    reason: str = ""
    note: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "receipt_id": self.receipt_id,
            "action": self.action,
            "status": self.status,
            "attach_url": self.attach_url,
            "command_preview": list(self.command_preview),
            "timestamp": self.timestamp,
            "hostname": self.hostname,
            "port": self.port,
            "executable": self.executable,
            "pid": self.pid,
            "process_ref": self.process_ref,
            "actor": self.actor,
            "reason": self.reason,
            "note": self.note,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class OpenCodeServeLifecycleLedger:
    """Append-only OpenCode serve lifecycle receipt ledger."""

    receipts: tuple[OpenCodeServeLifecycleReceipt, ...] = ()
    schema_version: str = OPENCODE_SERVE_LIFECYCLE_LEDGER_SCHEMA_VERSION

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "receipts": [receipt.to_json_dict() for receipt in self.receipts],
        }


@dataclass(frozen=True, slots=True)
class OpenCodeServeLifecycleRecordRequest:
    """Request to append one host-owned serve lifecycle receipt."""

    ledger_path: str | Path = DEFAULT_OPENCODE_SERVE_LIFECYCLE_LEDGER_RELATIVE_PATH
    action: OpenCodeServeLifecycleAction = "status"
    status: OpenCodeServeLifecycleStatus = "observed"
    executable: str = "opencode"
    hostname: str = DEFAULT_OPENCODE_SERVE_HOSTNAME
    port: int = DEFAULT_OPENCODE_SERVE_PORT
    attach_url: str = ""
    receipt_id: str = ""
    timestamp: str = ""
    pid: str = ""
    process_ref: str = ""
    actor: str = ""
    reason: str = ""
    note: str = ""
    include_command_preview: bool = True
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class OpenCodeServeLifecycleInspectRequest:
    """Read-only request for OpenCode serve lifecycle receipt inspection."""

    ledger_path: str | Path = DEFAULT_OPENCODE_SERVE_LIFECYCLE_LEDGER_RELATIVE_PATH
    action: OpenCodeServeLifecycleAction | str = ""
    status: OpenCodeServeLifecycleStatus | str = ""
    latest_limit: int = 0


@dataclass(frozen=True, slots=True)
class OpenCodeServeLifecycleLedgerResult:
    """Result for OpenCode serve lifecycle ledger operations."""

    ok: bool
    action: str
    ledger_path: Path
    receipt: OpenCodeServeLifecycleReceipt | None = None
    receipts: tuple[OpenCodeServeLifecycleReceipt, ...] = ()
    status: str = ""
    message: str = ""
    ledger_mutated: bool = False

    def to_json_dict(self) -> dict[str, object]:
        return {
            "ok": self.ok,
            "action": self.action,
            "status": self.status,
            "message": self.message,
            "ledger_path": str(self.ledger_path),
            "receipt": None if self.receipt is None else self.receipt.to_json_dict(),
            "receipts": [receipt.to_json_dict() for receipt in self.receipts],
            "authority_split": {
                "host_owned": True,
                "serve_lifecycle_ledger_mutated": self.ledger_mutated,
                "server_started": False,
                "server_stopped": False,
                "server_restarted": False,
                "server_process_owned_by_scheduler": False,
                "provider_executed": False,
                "scheduler_state_mutated": False,
                "delivery_state_mutated": False,
                "runtime_invocation_log_mutated": False,
                "local_work_trajectory_mutated": False,
                "raw_transcript_persisted": False,
                "secret_value_persisted": False,
            },
        }


def inspect_opencode_serve_readiness(
    request: OpenCodeServeReadinessRequest,
    *,
    which: Callable[[str], str | None] | None = None,
    opener: Callable[..., Any] | None = None,
    environ: Mapping[str, str] | None = None,
) -> OpenCodeServeReadinessReport:
    """Inspect CLI and optional attach-target health without mutation."""

    if request.port < 1 or request.port > 65535:
        raise ValueError("OpenCode serve port must be between 1 and 65535")
    if request.health_timeout_seconds <= 0:
        raise ValueError("OpenCode serve health timeout must be positive")

    which = which or shutil.which
    opener = opener or urllib.request.urlopen
    environ = environ or os.environ
    executable_resolved = which(request.executable) or ""
    attach_url = _normalize_attach_url(request)
    health_url = _health_url(attach_url, request.health_path)
    auth_configured = bool(environ.get(request.password_env_var, ""))

    if not executable_resolved:
        return OpenCodeServeReadinessReport(
            executable=request.executable,
            executable_resolved="",
            cli_available=False,
            attach_url=attach_url,
            health_url=health_url,
            health_checked=False,
            healthy=False,
            ready=False,
            error_kind="cli_unavailable",
            raw_error_type="MissingExecutable",
            summary=f"OpenCode CLI executable is unavailable: {request.executable}",
            auth_configured=auth_configured,
            username_env_var=request.username_env_var,
            password_env_var=request.password_env_var,
            metadata=request.metadata,
        )

    try:
        probe = urllib.request.Request(health_url)
        if auth_configured:
            probe.add_header(
                "Authorization",
                _basic_auth_header(
                    username=environ.get(request.username_env_var, "") or "opencode",
                    password=environ.get(request.password_env_var, ""),
                ),
            )
        response = opener(probe, timeout=request.health_timeout_seconds)
        status = int(getattr(response, "status", 200) or 200)
        healthy = 200 <= status < 300
        summary = "OpenCode serve health check succeeded." if healthy else (
            f"OpenCode serve health check returned HTTP {status}."
        )
        return OpenCodeServeReadinessReport(
            executable=request.executable,
            executable_resolved=executable_resolved,
            cli_available=True,
            attach_url=attach_url,
            health_url=health_url,
            health_checked=True,
            healthy=healthy,
            ready=healthy or not request.require_healthy,
            http_status=status,
            error_kind="" if healthy else "server_unhealthy",
            raw_error_type="" if healthy else f"HTTP{status}",
            summary=summary,
            auth_configured=auth_configured,
            username_env_var=request.username_env_var,
            password_env_var=request.password_env_var,
            metadata=request.metadata,
        )
    except urllib.error.HTTPError as exc:
        return _serve_health_failure_report(
            request,
            executable_resolved=executable_resolved,
            attach_url=attach_url,
            health_url=health_url,
            auth_configured=auth_configured,
            error_kind="authentication_required" if exc.code in {401, 403} else "server_unhealthy",
            raw_error_type=f"HTTP{exc.code}",
            summary=f"OpenCode serve health check returned HTTP {exc.code}.",
            http_status=int(exc.code),
        )
    except Exception as exc:
        return _serve_health_failure_report(
            request,
            executable_resolved=executable_resolved,
            attach_url=attach_url,
            health_url=health_url,
            auth_configured=auth_configured,
            error_kind="server_unreachable",
            raw_error_type=type(exc).__name__,
            summary="OpenCode serve health check failed or server is unreachable.",
        )


def opencode_serve_command_preview(
    request: OpenCodeServeReadinessRequest,
) -> tuple[str, ...]:
    """Return the host command shape for starting the serve target."""

    command = [
        request.executable,
        "serve",
        "--hostname",
        request.hostname,
        "--port",
        str(request.port),
    ]
    return tuple(command)


def record_opencode_serve_lifecycle_receipt(
    request: OpenCodeServeLifecycleRecordRequest,
) -> OpenCodeServeLifecycleLedgerResult:
    """Append one host-owned serve lifecycle receipt without process control."""

    _validate_lifecycle_action(request.action)
    _validate_lifecycle_status(request.status)
    if request.port < 1 or request.port > 65535:
        raise ValueError("OpenCode serve lifecycle port must be between 1 and 65535")

    ledger_path = Path(request.ledger_path)
    attach_url = _normalize_attach_url(
        OpenCodeServeReadinessRequest(
            executable=request.executable,
            hostname=request.hostname,
            port=request.port,
            attach_url=request.attach_url,
        )
    )
    receipt = OpenCodeServeLifecycleReceipt(
        receipt_id=request.receipt_id
        or _serve_lifecycle_receipt_id(
            action=request.action,
            attach_url=attach_url,
            timestamp=request.timestamp,
            existing_count=len(read_opencode_serve_lifecycle_ledger(ledger_path).receipts),
        ),
        action=request.action,
        status=request.status,
        attach_url=attach_url,
        command_preview=(
            opencode_serve_command_preview(
                OpenCodeServeReadinessRequest(
                    executable=request.executable,
                    hostname=request.hostname,
                    port=request.port,
                    attach_url=request.attach_url,
                )
            )
            if request.include_command_preview and request.action in {"start", "restart", "status", "external"}
            else ()
        ),
        timestamp=request.timestamp,
        hostname=request.hostname,
        port=request.port,
        executable=request.executable,
        pid=request.pid,
        process_ref=request.process_ref,
        actor=request.actor,
        reason=request.reason,
        note=request.note,
        metadata=dict(request.metadata),
    )
    ledger = read_opencode_serve_lifecycle_ledger(ledger_path)
    updated = OpenCodeServeLifecycleLedger(receipts=(*ledger.receipts, receipt))
    write_opencode_serve_lifecycle_ledger(updated, ledger_path)
    return OpenCodeServeLifecycleLedgerResult(
        ok=True,
        action="record",
        ledger_path=ledger_path,
        receipt=receipt,
        receipts=updated.receipts,
        status="recorded",
        message="OpenCode serve lifecycle receipt recorded",
        ledger_mutated=True,
    )


def inspect_opencode_serve_lifecycle_receipts(
    request: OpenCodeServeLifecycleInspectRequest,
) -> OpenCodeServeLifecycleLedgerResult:
    """Inspect host-owned serve lifecycle receipts without mutation."""

    if request.action:
        _validate_lifecycle_action(str(request.action))
    if request.status:
        _validate_lifecycle_status(str(request.status))
    if request.latest_limit < 0:
        raise ValueError("OpenCode serve lifecycle latest_limit must be non-negative")

    ledger_path = Path(request.ledger_path)
    ledger = read_opencode_serve_lifecycle_ledger(ledger_path)
    receipts = ledger.receipts
    if request.action:
        receipts = tuple(receipt for receipt in receipts if receipt.action == request.action)
    if request.status:
        receipts = tuple(receipt for receipt in receipts if receipt.status == request.status)
    if request.latest_limit:
        receipts = receipts[-request.latest_limit :]
    return OpenCodeServeLifecycleLedgerResult(
        ok=True,
        action="inspect",
        ledger_path=ledger_path,
        receipts=receipts,
        status="inspected",
        message=f"{len(receipts)} OpenCode serve lifecycle receipt(s) matched",
        ledger_mutated=False,
    )


def read_opencode_serve_lifecycle_ledger(
    path: str | Path,
) -> OpenCodeServeLifecycleLedger:
    ledger_path = Path(path)
    if not ledger_path.exists():
        return OpenCodeServeLifecycleLedger()
    payload = json.loads(ledger_path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != OPENCODE_SERVE_LIFECYCLE_LEDGER_SCHEMA_VERSION:
        raise ValueError(
            "Unsupported OpenCode serve lifecycle ledger schema_version: "
            f"{payload.get('schema_version')!r}"
        )
    return OpenCodeServeLifecycleLedger(
        receipts=tuple(
            _serve_lifecycle_receipt_from_json_dict(item)
            for item in payload.get("receipts", [])
        )
    )


def write_opencode_serve_lifecycle_ledger(
    ledger: OpenCodeServeLifecycleLedger,
    path: str | Path,
) -> None:
    ledger_path = Path(path)
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger_path.write_text(
        json.dumps(ledger.to_json_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def _serve_health_failure_report(
    request: OpenCodeServeReadinessRequest,
    *,
    executable_resolved: str,
    attach_url: str,
    health_url: str,
    auth_configured: bool,
    error_kind: str,
    raw_error_type: str,
    summary: str,
    http_status: int | None = None,
) -> OpenCodeServeReadinessReport:
    return OpenCodeServeReadinessReport(
        executable=request.executable,
        executable_resolved=executable_resolved,
        cli_available=True,
        attach_url=attach_url,
        health_url=health_url,
        health_checked=True,
        healthy=False,
        ready=not request.require_healthy,
        http_status=http_status,
        error_kind=error_kind,
        raw_error_type=raw_error_type,
        summary=summary,
        auth_configured=auth_configured,
        username_env_var=request.username_env_var,
        password_env_var=request.password_env_var,
        metadata=request.metadata,
    )


def _normalize_attach_url(request: OpenCodeServeReadinessRequest) -> str:
    if request.attach_url:
        return request.attach_url.rstrip("/")
    return f"http://{request.hostname}:{request.port}"


def _health_url(attach_url: str, health_path: str) -> str:
    path = health_path or DEFAULT_OPENCODE_SERVE_HEALTH_PATH
    if not path.startswith("/"):
        path = f"/{path}"
    return urljoin(f"{attach_url.rstrip('/')}/", path.lstrip("/"))


def _basic_auth_header(*, username: str, password: str) -> str:
    token = f"{username}:{password}".encode("utf-8")
    return "Basic " + base64.b64encode(token).decode("ascii")


def _serve_lifecycle_receipt_from_json_dict(
    payload: dict[str, object],
) -> OpenCodeServeLifecycleReceipt:
    action = str(payload.get("action", ""))
    status = str(payload.get("status", ""))
    _validate_lifecycle_action(action)
    _validate_lifecycle_status(status)
    return OpenCodeServeLifecycleReceipt(
        receipt_id=str(payload.get("receipt_id", "")),
        action=action,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        attach_url=str(payload.get("attach_url", "")),
        command_preview=tuple(str(item) for item in payload.get("command_preview", []) or []),
        timestamp=str(payload.get("timestamp", "")),
        hostname=str(payload.get("hostname", DEFAULT_OPENCODE_SERVE_HOSTNAME)),
        port=int(payload.get("port", DEFAULT_OPENCODE_SERVE_PORT) or DEFAULT_OPENCODE_SERVE_PORT),
        executable=str(payload.get("executable", "opencode")),
        pid=str(payload.get("pid", "")),
        process_ref=str(payload.get("process_ref", "")),
        actor=str(payload.get("actor", "")),
        reason=str(payload.get("reason", "")),
        note=str(payload.get("note", "")),
        metadata=dict(payload.get("metadata", {}) or {}),
    )


def _serve_lifecycle_receipt_id(
    *,
    action: str,
    attach_url: str,
    timestamp: str,
    existing_count: int,
) -> str:
    safe_attach = (
        attach_url.replace("\\", "/")
        .replace("://", "-")
        .replace("/", "-")
        .replace(":", "-")
        .strip("-")
    )
    safe_timestamp = (
        timestamp.replace(":", "")
        .replace("+", "")
        .replace(".", "")
        .replace("-", "")
        .replace("T", "t")
        .replace("Z", "z")
    )
    suffix = safe_timestamp or f"{existing_count + 1:06d}"
    return f"opencode-serve:{action}:{safe_attach}:{suffix}"


def _validate_lifecycle_action(action: str) -> None:
    if action not in {"start", "stop", "restart", "status", "external"}:
        raise ValueError(
            "OpenCode serve lifecycle action must be start, stop, restart, status, or external"
        )


def _validate_lifecycle_status(status: str) -> None:
    if status not in {"planned", "observed", "succeeded", "failed"}:
        raise ValueError(
            "OpenCode serve lifecycle status must be planned, observed, succeeded, or failed"
        )


__all__ = [
    "DEFAULT_OPENCODE_SERVE_LIFECYCLE_LEDGER_RELATIVE_PATH",
    "DEFAULT_OPENCODE_SERVE_HEALTH_PATH",
    "DEFAULT_OPENCODE_SERVE_HOSTNAME",
    "DEFAULT_OPENCODE_SERVE_PORT",
    "DEFAULT_OPENCODE_SERVER_PASSWORD_ENV_VAR",
    "DEFAULT_OPENCODE_SERVER_USERNAME_ENV_VAR",
    "OPENCODE_SERVE_LIFECYCLE_LEDGER_SCHEMA_VERSION",
    "OpenCodeServeLifecycleAction",
    "OpenCodeServeLifecycleInspectRequest",
    "OpenCodeServeLifecycleLedger",
    "OpenCodeServeLifecycleLedgerResult",
    "OpenCodeServeLifecycleReceipt",
    "OpenCodeServeLifecycleRecordRequest",
    "OpenCodeServeLifecycleStatus",
    "OpenCodeServeReadinessReport",
    "OpenCodeServeReadinessRequest",
    "inspect_opencode_serve_readiness",
    "inspect_opencode_serve_lifecycle_receipts",
    "opencode_serve_command_preview",
    "read_opencode_serve_lifecycle_ledger",
    "record_opencode_serve_lifecycle_receipt",
    "write_opencode_serve_lifecycle_ledger",
]
