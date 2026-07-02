"""Host-owned OpenCode direct server/API client wrapper.

The wrapper talks to a running ``opencode serve`` instance. It deliberately
does not start, stop, restart, or supervise that server; host provisioning stays
outside the scheduler/runtime core.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urljoin

from .opencode_serve_lifecycle import (
    DEFAULT_OPENCODE_SERVE_HEALTH_PATH,
    DEFAULT_OPENCODE_SERVE_HOSTNAME,
    DEFAULT_OPENCODE_SERVE_PORT,
    DEFAULT_OPENCODE_SERVER_PASSWORD_ENV_VAR,
    DEFAULT_OPENCODE_SERVER_USERNAME_ENV_VAR,
)
from .runtime_adapter import (
    OpenCodeCliRequest,
    OpenCodeCliResult,
    OpenCodeCliRuntimeError,
)


DEFAULT_OPENCODE_SERVER_API_DOC_PATH = "/doc"
DEFAULT_OPENCODE_SERVER_API_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True, slots=True)
class OpenCodeServerApiClientConfig:
    """Host-owned options for a running OpenCode server/API target."""

    base_url: str = f"http://{DEFAULT_OPENCODE_SERVE_HOSTNAME}:{DEFAULT_OPENCODE_SERVE_PORT}"
    health_path: str = DEFAULT_OPENCODE_SERVE_HEALTH_PATH
    doc_path: str = DEFAULT_OPENCODE_SERVER_API_DOC_PATH
    session_id: str = ""
    model: str = ""
    timeout_seconds: float = DEFAULT_OPENCODE_SERVER_API_TIMEOUT_SECONDS
    username_env_var: str = DEFAULT_OPENCODE_SERVER_USERNAME_ENV_VAR
    password_env_var: str = DEFAULT_OPENCODE_SERVER_PASSWORD_ENV_VAR
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError("OpenCode server/API timeout_seconds must be positive")


@dataclass(frozen=True, slots=True)
class OpenCodeServerApiReadinessReport:
    """Credential-safe direct OpenCode server/API readiness report."""

    base_url: str
    health_url: str
    doc_url: str
    ready: bool
    health_checked: bool
    healthy: bool
    doc_checked: bool
    doc_available: bool
    http_status: int | None = None
    doc_http_status: int | None = None
    error_kind: str = ""
    raw_error_type: str = ""
    summary: str = ""
    auth_configured: bool = False
    username_env_var: str = DEFAULT_OPENCODE_SERVER_USERNAME_ENV_VAR
    password_env_var: str = DEFAULT_OPENCODE_SERVER_PASSWORD_ENV_VAR
    openapi_version: str = ""
    api_title: str = ""
    api_version: str = ""
    metadata: Mapping[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "base_url": self.base_url,
            "health_url": self.health_url,
            "doc_url": self.doc_url,
            "ready": self.ready,
            "health_checked": self.health_checked,
            "healthy": self.healthy,
            "doc_checked": self.doc_checked,
            "doc_available": self.doc_available,
            "http_status": self.http_status,
            "doc_http_status": self.doc_http_status,
            "error_kind": self.error_kind,
            "raw_error_type": self.raw_error_type,
            "summary": self.summary,
            "auth_configured": self.auth_configured,
            "username_env_var": self.username_env_var,
            "password_env_var": self.password_env_var,
            "openapi_version": self.openapi_version,
            "api_title": self.api_title,
            "api_version": self.api_version,
            "metadata": dict(self.metadata),
            "authority_split": {
                "host_owned": True,
                "server_started": False,
                "server_stopped": False,
                "server_restarted": False,
                "server_process_owned_by_scheduler": False,
                "provider_executed": False,
                "server_api_called": self.health_checked or self.doc_checked,
                "scheduler_state_mutated": False,
                "delivery_state_mutated": False,
                "runtime_invocation_log_mutated": False,
                "local_work_trajectory_mutated": False,
                "raw_transcript_persisted": False,
                "secret_value_persisted": False,
            },
        }


class OpenCodeServerApiClient:
    """``OpenCodeCliClient``-compatible client backed by OpenCode HTTP API."""

    def __init__(
        self,
        config: OpenCodeServerApiClientConfig | None = None,
        *,
        opener: Callable[..., Any] | None = None,
        environ: Mapping[str, str] | None = None,
    ) -> None:
        self.config = config or OpenCodeServerApiClientConfig()
        self._opener = opener or urllib.request.urlopen
        self._environ = environ or os.environ

    def inspect_readiness(
        self,
        *,
        check_doc: bool = False,
    ) -> OpenCodeServerApiReadinessReport:
        """Inspect server health and optionally OpenAPI docs without mutation."""

        base_url = _normalize_base_url(self.config.base_url)
        health_url = _join_url(base_url, self.config.health_path)
        doc_url = _join_url(base_url, self.config.doc_path)
        auth_configured = bool(self._environ.get(self.config.password_env_var, ""))

        health_status: int | None = None
        try:
            health_response = self._request("GET", health_url)
            health_status = _response_status(health_response)
            healthy = 200 <= health_status < 300
            if not healthy:
                return self._readiness_failure(
                    base_url=base_url,
                    health_url=health_url,
                    doc_url=doc_url,
                    auth_configured=auth_configured,
                    health_checked=True,
                    http_status=health_status,
                    error_kind="server_unhealthy",
                    raw_error_type=f"HTTP{health_status}",
                    summary=f"OpenCode server/API health returned HTTP {health_status}.",
                )
        except urllib.error.HTTPError as exc:
            return self._readiness_failure(
                base_url=base_url,
                health_url=health_url,
                doc_url=doc_url,
                auth_configured=auth_configured,
                health_checked=True,
                http_status=int(exc.code),
                error_kind="authentication_required" if exc.code in {401, 403} else "server_unhealthy",
                raw_error_type=f"HTTP{exc.code}",
                summary=f"OpenCode server/API health returned HTTP {exc.code}.",
            )
        except Exception as exc:
            return self._readiness_failure(
                base_url=base_url,
                health_url=health_url,
                doc_url=doc_url,
                auth_configured=auth_configured,
                health_checked=True,
                error_kind="server_unreachable",
                raw_error_type=type(exc).__name__,
                summary="OpenCode server/API health check failed or server is unreachable.",
            )

        doc_payload: dict[str, object] = {}
        doc_status: int | None = None
        doc_available = False
        if check_doc:
            try:
                doc_response = self._request("GET", doc_url)
                doc_status = _response_status(doc_response)
                doc_payload = _json_response(doc_response)
                doc_available = 200 <= doc_status < 300
            except urllib.error.HTTPError as exc:
                doc_status = int(exc.code)
            except Exception:
                doc_status = None

        info = doc_payload.get("info", {}) if isinstance(doc_payload, dict) else {}
        info_dict = info if isinstance(info, dict) else {}
        return OpenCodeServerApiReadinessReport(
            base_url=base_url,
            health_url=health_url,
            doc_url=doc_url,
            ready=True,
            health_checked=True,
            healthy=True,
            doc_checked=check_doc,
            doc_available=doc_available,
            http_status=health_status,
            doc_http_status=doc_status,
            summary=(
                "OpenCode server/API health check succeeded"
                + (" and OpenAPI docs are available." if doc_available else ".")
            ),
            auth_configured=auth_configured,
            username_env_var=self.config.username_env_var,
            password_env_var=self.config.password_env_var,
            openapi_version=str(doc_payload.get("openapi", "")) if doc_payload else "",
            api_title=str(info_dict.get("title", "")),
            api_version=str(info_dict.get("version", "")),
            metadata=self.config.metadata,
        )

    def exec(self, request: OpenCodeCliRequest) -> OpenCodeCliResult:
        """Run one OpenCode task through a running server/API target."""

        base_url = _normalize_base_url(self.config.base_url)
        session_id = self._session_id_from_request(request)
        created_session = False
        if not session_id:
            session_response = self._request(
                "POST",
                _join_url(base_url, "/session"),
                payload=_without_empty(
                    {
                        "title": request.task.title or request.task.task_id,
                        "model": self.config.model or request.agent.model,
                    }
                ),
            )
            session_payload = _json_response(session_response)
            session_id = _extract_session_id(session_payload)
            created_session = True
        if not session_id:
            raise OpenCodeCliRuntimeError(
                error_kind="invalid_response",
                summary="OpenCode server/API did not return a session id.",
            )

        prompt = _build_prompt(request)
        message_payload = _without_empty(
            {
                "message": prompt,
                "prompt": prompt,
                "text": prompt,
                "model": self.config.model or request.agent.model,
            }
        )
        try:
            message_response = self._request(
                "POST",
                _join_url(base_url, f"/session/{session_id}/message"),
                payload=message_payload,
            )
        except urllib.error.HTTPError as exc:
            raise OpenCodeCliRuntimeError(
                error_kind=_error_kind_from_http_status(int(exc.code)),
                summary=f"OpenCode server/API message request returned HTTP {exc.code}.",
                raw_error_type=f"HTTP{exc.code}",
                retryable=int(exc.code) in {408, 409, 425, 429, 500, 502, 503, 504},
            ) from exc
        except Exception as exc:
            raise OpenCodeCliRuntimeError(
                error_kind="server_unreachable",
                summary="OpenCode server/API message request failed or server is unreachable.",
                raw_error_type=type(exc).__name__,
                retryable=True,
            ) from exc

        message_payload_result = _json_response(message_response)
        output_text = "\n".join(_text_chunks_from_json_value(message_payload_result)).strip()
        if not output_text:
            output_text = json.dumps(message_payload_result, ensure_ascii=False)
        return OpenCodeCliResult(
            summary=_compact_summary(output_text),
            output_text=output_text,
            metadata={
                "transport": "server-api",
                "base_url": base_url,
                "session_id": session_id,
                "created_session": created_session,
                "session_persistence": (
                    "not_persisted_by_delivery"
                    if created_session
                    else "preexisting_selector"
                ),
                "session_persistence_required_action": (
                    "Use an explicit host-owned claim action, such as "
                    "`doc-based-coding opencode session claim` or "
                    "`doc-based-coding worker-binding claim`, before expecting "
                    "reuse across later deliveries."
                    if created_session
                    else ""
                ),
                "server_api_created_session_persisted": False,
                "server_api_created_session_persistence_authority": (
                    "explicit_host_owned_claim_required" if created_session else ""
                ),
                "health_path": self.config.health_path,
                "doc_path": self.config.doc_path,
                "session_selector_source": self._session_selector_source(request),
                **dict(self.config.metadata),
            },
        )

    def _request(
        self,
        method: str,
        url: str,
        *,
        payload: Mapping[str, object] | None = None,
    ) -> Any:
        data = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            data = json.dumps(dict(payload), ensure_ascii=False).encode("utf-8")
            headers["Content-Type"] = "application/json"
        password = self._environ.get(self.config.password_env_var, "")
        if password:
            username = self._environ.get(self.config.username_env_var, "") or "opencode"
            token = f"{username}:{password}".encode("utf-8")
            headers["Authorization"] = "Basic " + base64.b64encode(token).decode("ascii")
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        return self._opener(request, timeout=self.config.timeout_seconds)

    def _session_id_from_request(self, request: OpenCodeCliRequest) -> str:
        if self.config.session_id:
            return self.config.session_id
        if request.host_session is not None:
            return request.host_session.session_id
        return ""

    def _session_selector_source(self, request: OpenCodeCliRequest) -> str:
        if self.config.session_id:
            return "explicit_config"
        if request.host_session is not None:
            return request.host_session.selector_source or "session_ledger"
        return "server_api_created"

    def _readiness_failure(
        self,
        *,
        base_url: str,
        health_url: str,
        doc_url: str,
        auth_configured: bool,
        health_checked: bool,
        error_kind: str,
        raw_error_type: str,
        summary: str,
        http_status: int | None = None,
    ) -> OpenCodeServerApiReadinessReport:
        return OpenCodeServerApiReadinessReport(
            base_url=base_url,
            health_url=health_url,
            doc_url=doc_url,
            ready=False,
            health_checked=health_checked,
            healthy=False,
            doc_checked=False,
            doc_available=False,
            http_status=http_status,
            error_kind=error_kind,
            raw_error_type=raw_error_type,
            summary=summary,
            auth_configured=auth_configured,
            username_env_var=self.config.username_env_var,
            password_env_var=self.config.password_env_var,
            metadata=self.config.metadata,
        )


def inspect_opencode_server_api_readiness(
    config: OpenCodeServerApiClientConfig | None = None,
    *,
    check_doc: bool = False,
    opener: Callable[..., Any] | None = None,
    environ: Mapping[str, str] | None = None,
) -> OpenCodeServerApiReadinessReport:
    """Convenience helper for host-owned server/API readiness inspection."""

    return OpenCodeServerApiClient(
        config,
        opener=opener,
        environ=environ,
    ).inspect_readiness(check_doc=check_doc)


def _build_prompt(request: OpenCodeCliRequest) -> str:
    sections = [
        f"Task ID: {request.task.task_id}",
        f"Title: {request.task.title}",
        "",
        request.instruction,
    ]
    if request.acceptance:
        sections.extend(["", "Acceptance criteria:"])
        sections.extend(f"- {item}" for item in request.acceptance)
    if request.input_artifact_refs:
        sections.extend(["", "Input artifact refs:"])
        sections.extend(
            f"- {ref.ref_kind}:{ref.ref_id}@{ref.version or 'latest'}"
            for ref in request.input_artifact_refs
        )
    if request.task.runtime_workspace_root:
        sections.extend(
            [
                "",
                f"Runtime workspace root: {request.task.runtime_workspace_root}",
                f"Sandbox provider: {request.task.sandbox_provider}",
                f"Sandbox allocation id: {request.task.sandbox_allocation_id}",
            ]
        )
    if request.task.visible_mounts:
        sections.extend(["", "Visible or writable mounts:"])
        sections.extend(f"- {mount}" for mount in request.task.visible_mounts)
    if request.task.scratch_path:
        sections.extend(["", f"Scratch path: {request.task.scratch_path}"])
    if request.output_artifact_id:
        sections.extend(["", f"Expected output artifact id: {request.output_artifact_id}"])
    sections.extend(
        [
            "",
            "Return a compact final response suitable for a scheduler result artifact.",
            "Do not include secrets or raw credential material.",
        ]
    )
    return "\n".join(sections)


def _normalize_base_url(value: str) -> str:
    return (value or f"http://{DEFAULT_OPENCODE_SERVE_HOSTNAME}:{DEFAULT_OPENCODE_SERVE_PORT}").rstrip("/")


def _join_url(base_url: str, path: str) -> str:
    normalized_path = path or "/"
    if not normalized_path.startswith("/"):
        normalized_path = "/" + normalized_path
    return urljoin(base_url.rstrip("/") + "/", normalized_path.lstrip("/"))


def _response_status(response: Any) -> int:
    return int(getattr(response, "status", None) or getattr(response, "code", None) or 200)


def _json_response(response: Any) -> dict[str, object]:
    raw = response.read()
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    if not str(raw).strip():
        return {}
    payload = json.loads(str(raw))
    return payload if isinstance(payload, dict) else {"value": payload}


def _extract_session_id(payload: Mapping[str, object]) -> str:
    for key in ("id", "sessionID", "sessionId", "session_id"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    session = payload.get("session")
    if isinstance(session, Mapping):
        return _extract_session_id(session)
    return ""


def _without_empty(payload: Mapping[str, object]) -> dict[str, object]:
    return {
        key: value
        for key, value in payload.items()
        if value not in ("", None, (), [], {})
    }


def _error_kind_from_http_status(status: int) -> str:
    if status in {401, 403}:
        return "authentication_failed"
    if status == 408 or status == 504:
        return "timeout"
    if status in {429, 500, 502, 503}:
        return "process_failed"
    if status == 404:
        return "invalid_response"
    return "unknown"


def _text_chunks_from_json_value(value: Any) -> list[str]:
    chunks: list[str] = []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        for item in value:
            chunks.extend(_text_chunks_from_json_value(item))
        return chunks
    if not isinstance(value, dict):
        return chunks
    for key in ("text", "message", "content", "summary", "title"):
        raw = value.get(key)
        if isinstance(raw, str) and raw.strip():
            chunks.append(raw.strip())
        elif isinstance(raw, (dict, list)):
            chunks.extend(_text_chunks_from_json_value(raw))
    for key in ("parts", "data", "delta", "response", "output"):
        raw = value.get(key)
        if isinstance(raw, (dict, list)):
            chunks.extend(_text_chunks_from_json_value(raw))
    return chunks


def _compact_summary(value: Any) -> str:
    text = str(value or "").strip().replace("\r\n", "\n")
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if len(first_line) <= 160:
        return first_line
    return first_line[:157].rstrip() + "..."


__all__ = [
    "DEFAULT_OPENCODE_SERVER_API_DOC_PATH",
    "DEFAULT_OPENCODE_SERVER_API_TIMEOUT_SECONDS",
    "OpenCodeServerApiClient",
    "OpenCodeServerApiClientConfig",
    "OpenCodeServerApiReadinessReport",
    "inspect_opencode_server_api_readiness",
]
