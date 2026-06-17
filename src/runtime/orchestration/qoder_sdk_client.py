"""Optional Qoder Python SDK query client wrapper.

The wrapper is intentionally host-owned and optional: importing this module
does not import the real Qoder SDK. Hosts construct ``QoderSDKQueryClient`` only
after granting provider-level runtime wiring permission.
"""

from __future__ import annotations

import asyncio
import importlib
import inspect
import os
import threading
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from .runtime_adapter import (
    PermissionRequest,
    PermissionRequestKind,
    QoderQueryRequest,
    QoderQueryResult,
    QoderRuntimeError,
    qoder_query_result_from_response,
)

QoderSdkAuthMode = Literal["env", "qodercli"]
QoderPermissionRequestPolicy = Literal["deny", "surface"]

DEFAULT_QODER_TOKEN_ENV = "QODER_PERSONAL_ACCESS_TOKEN"


@dataclass(frozen=True, slots=True)
class QoderSDKQueryClientConfig:
    """Host-owned options for constructing the optional Qoder SDK wrapper."""

    cwd: str | Path = ""
    model: str = ""
    max_turns: int | None = None
    auth_mode: QoderSdkAuthMode = "env"
    auth_env_var: str = DEFAULT_QODER_TOKEN_ENV
    allowed_tools: tuple[str, ...] = ()
    disallowed_tools: tuple[str, ...] = ()
    permission_mode: str = ""
    permission_request_policy: QoderPermissionRequestPolicy = "deny"
    sdk_module_name: str = "qoder_agent_sdk"
    metadata: Mapping[str, object] = field(default_factory=dict)


class QoderSDKQueryClient:
    """``QoderQueryClient`` implementation backed by the Python Qoder SDK.

    The implementation dynamically imports the SDK and normalizes its async
    stream into the project-owned ``QoderQueryResult`` seam.
    """

    def __init__(
        self,
        config: QoderSDKQueryClientConfig | None = None,
        *,
        sdk_importer: Callable[[str], Any] | None = None,
        environment: Mapping[str, str] | None = None,
    ) -> None:
        self.config = config or QoderSDKQueryClientConfig()
        self._sdk_importer = sdk_importer or importlib.import_module
        self._environment = environment if environment is not None else os.environ

    def query(self, request: QoderQueryRequest) -> QoderQueryResult:
        """Run one bounded SDK query and return a compact normalized result."""

        token = self._validated_auth_token()
        sdk = self._load_sdk()
        auth = self._build_auth(sdk, token)
        permission_requests: list[PermissionRequest] = []
        options = self._build_options(
            sdk,
            auth=auth,
            request=request,
            permission_requests=permission_requests,
        )
        prompt = self._build_prompt(request)

        try:
            result = _run_async(
                self._collect_query_result(
                    sdk,
                    prompt=prompt,
                    options=options,
                    request=request,
                    permission_requests=permission_requests,
                )
            )
        except QoderRuntimeError:
            raise
        except Exception as exc:
            raise self._runtime_error_from_exception(exc) from exc

        if permission_requests and self.config.permission_request_policy == "deny":
            first = permission_requests[0]
            raise QoderRuntimeError(
                error_kind="permission_denied",
                summary=f"Qoder SDK requested permission and the wrapper denied it: {first.summary}",
                raw_error_type="PermissionRequest",
            )
        return result

    def validate_host_ready(self) -> None:
        """Fail closed before scheduler execution when host SDK setup is missing."""

        token = self._validated_auth_token()
        sdk = self._load_sdk()
        if not callable(getattr(sdk, "query", None)):
            raise QoderRuntimeError(
                error_kind="sdk_unavailable",
                summary="Qoder Python SDK is missing query().",
                raw_error_type="AttributeError",
            )
        if not callable(getattr(sdk, "QoderAgentOptions", None)):
            raise QoderRuntimeError(
                error_kind="sdk_unavailable",
                summary="Qoder Python SDK is missing QoderAgentOptions.",
                raw_error_type="AttributeError",
            )
        if self.config.auth_mode == "qodercli":
            if not callable(getattr(sdk, "qodercli_auth", None)):
                raise QoderRuntimeError(
                    error_kind="authentication_failed",
                    summary="Qoder SDK qodercli_auth helper is unavailable.",
                    raw_error_type="MissingAuthFactory",
                )
            return
        if (
            self.config.auth_env_var == DEFAULT_QODER_TOKEN_ENV
            and callable(getattr(sdk, "access_token_from_env", None))
        ):
            return
        if token and callable(getattr(sdk, "access_token", None)):
            return
        raise QoderRuntimeError(
            error_kind="authentication_failed",
            summary="Qoder SDK access_token helper is unavailable.",
            raw_error_type="MissingAuthFactory",
        )

    def _load_sdk(self) -> Any:
        try:
            return self._sdk_importer(self.config.sdk_module_name)
        except (ImportError, ModuleNotFoundError) as exc:
            raise QoderRuntimeError(
                error_kind="sdk_unavailable",
                summary=(
                    "Qoder Python SDK is unavailable. Install qoder-agent-sdk "
                    "in the host runtime environment before constructing the real wrapper."
                ),
                raw_error_type=type(exc).__name__,
            ) from exc

    def _validated_auth_token(self) -> str:
        if self.config.auth_mode == "qodercli":
            return ""
        env_var = self.config.auth_env_var or DEFAULT_QODER_TOKEN_ENV
        token = self._environment.get(env_var, "")
        if not token:
            raise QoderRuntimeError(
                error_kind="authentication_failed",
                summary=(
                    f"Qoder SDK auth is unavailable: environment variable {env_var} "
                    "is not set for the host runtime."
                ),
                raw_error_type="MissingEnvironmentVariable",
            )
        return token

    def _build_auth(self, sdk: Any, token: str) -> Any:
        try:
            if self.config.auth_mode == "qodercli":
                factory = getattr(sdk, "qodercli_auth")
                return factory()
            if (
                self.config.auth_env_var == DEFAULT_QODER_TOKEN_ENV
                and hasattr(sdk, "access_token_from_env")
            ):
                return sdk.access_token_from_env()
            if hasattr(sdk, "access_token"):
                return sdk.access_token(token)
        except Exception as exc:
            raise QoderRuntimeError(
                error_kind="authentication_failed",
                summary=self._redact(f"Qoder SDK auth construction failed: {exc}"),
                raw_error_type=type(exc).__name__,
            ) from exc
        raise QoderRuntimeError(
            error_kind="authentication_failed",
            summary="Qoder SDK auth helper is unavailable on the imported SDK module.",
            raw_error_type="MissingAuthFactory",
        )

    def _build_options(
        self,
        sdk: Any,
        *,
        auth: Any,
        request: QoderQueryRequest,
        permission_requests: list[PermissionRequest],
    ) -> Any:
        try:
            options_factory = getattr(sdk, "QoderAgentOptions")
        except AttributeError as exc:
            raise QoderRuntimeError(
                error_kind="sdk_unavailable",
                summary="Qoder Python SDK is missing QoderAgentOptions.",
                raw_error_type="AttributeError",
            ) from exc

        kwargs: dict[str, Any] = {
            "auth": auth,
            "can_use_tool": self._permission_callback(request, permission_requests),
        }
        cwd = str(self.config.cwd or "")
        model = self.config.model or request.agent.model
        max_turns = self.config.max_turns if self.config.max_turns is not None else request.agent.max_turns
        if cwd:
            kwargs["cwd"] = cwd
        if model:
            kwargs["model"] = model
        if max_turns is not None:
            kwargs["max_turns"] = max_turns
        if self.config.allowed_tools:
            kwargs["allowed_tools"] = list(self.config.allowed_tools)
        if self.config.disallowed_tools:
            kwargs["disallowed_tools"] = list(self.config.disallowed_tools)
        if self.config.permission_mode:
            kwargs["permission_mode"] = self.config.permission_mode

        try:
            return options_factory(**kwargs)
        except TypeError as exc:
            raise QoderRuntimeError(
                error_kind="sdk_unavailable",
                summary=self._redact(f"QoderAgentOptions rejected wrapper options: {exc}"),
                raw_error_type=type(exc).__name__,
            ) from exc

    def _permission_callback(
        self,
        request: QoderQueryRequest,
        permission_requests: list[PermissionRequest],
    ) -> Callable[..., bool]:
        def can_use_tool(*args: Any, **kwargs: Any) -> bool:
            permission_requests.append(
                _permission_request_from_callback(
                    args,
                    kwargs,
                    request=request,
                    index=len(permission_requests) + 1,
                )
            )
            return False

        return can_use_tool

    async def _collect_query_result(
        self,
        sdk: Any,
        *,
        prompt: str,
        options: Any,
        request: QoderQueryRequest,
        permission_requests: list[PermissionRequest],
    ) -> QoderQueryResult:
        query_function = getattr(sdk, "query", None)
        if query_function is None:
            raise QoderRuntimeError(
                error_kind="sdk_unavailable",
                summary="Qoder Python SDK is missing query().",
                raw_error_type="AttributeError",
            )

        try:
            stream = query_function(prompt=prompt, options=options)
            if inspect.isawaitable(stream):
                stream = await stream
        except Exception as exc:
            raise self._runtime_error_from_exception(exc) from exc

        if not hasattr(stream, "__aiter__"):
            raise QoderRuntimeError(
                error_kind="invalid_response",
                summary="Qoder SDK query() did not return an async message stream.",
                raw_error_type=type(stream).__name__,
            )

        text_parts: list[str] = []
        final_response: dict[str, Any] | None = None
        message_count = 0

        try:
            async for message in stream:
                message_count += 1
                normalized = _message_to_mapping(message)
                if _is_permission_message(message, normalized):
                    permission_requests.append(
                        _permission_request_from_message(
                            message,
                            normalized,
                            request=request,
                            index=len(permission_requests) + 1,
                        )
                    )
                    continue
                candidate = _response_candidate(normalized)
                if candidate is not None:
                    final_response = candidate
                extracted = _extract_text(message, normalized)
                if extracted:
                    text_parts.append(extracted)
        except Exception as exc:
            raise self._runtime_error_from_exception(exc) from exc

        if final_response is not None:
            result = qoder_query_result_from_response(final_response)
            metadata = self._result_metadata(message_count=message_count)
            metadata.update(result.metadata)
            return QoderQueryResult(
                summary=result.summary,
                output_text=result.output_text,
                artifact_delta=result.artifact_delta,
                permission_requests=(*result.permission_requests, *permission_requests),
                metadata=metadata,
            )

        output_text = "".join(part for part in text_parts if part).strip()
        if not output_text and permission_requests and self.config.permission_request_policy == "surface":
            return QoderQueryResult(
                summary="Qoder SDK requested permission review.",
                output_text="",
                permission_requests=tuple(permission_requests),
                metadata=self._result_metadata(message_count=message_count),
            )
        if not output_text:
            raise QoderRuntimeError(
                error_kind="invalid_response",
                summary="Qoder SDK stream ended without a usable text or result message.",
            )

        return QoderQueryResult(
            summary=_compact_summary(output_text),
            output_text=output_text,
            permission_requests=tuple(permission_requests),
            metadata=self._result_metadata(message_count=message_count),
        )

    def _build_prompt(self, request: QoderQueryRequest) -> str:
        sections = [
            f"Task ID: {request.task.task_id}",
            f"Title: {request.task.title}",
            "",
            request.instruction,
        ]
        if request.acceptance:
            sections.extend(
                [
                    "",
                    "Acceptance criteria:",
                    *(f"- {item}" for item in request.acceptance),
                ]
            )
        if request.input_artifact_refs:
            sections.extend(
                [
                    "",
                    "Input artifact references supplied by orchestration:",
                    *(
                        f"- {ref.ref_kind}:{ref.ref_id}"
                        + (f"@{ref.version}" if ref.version else "")
                        + (f" ({ref.path})" if ref.path else "")
                        for ref in request.input_artifact_refs
                    ),
                ]
            )
        return "\n".join(sections).strip()

    def _result_metadata(self, *, message_count: int) -> dict[str, object]:
        metadata = {
            "sdk": "qoder-agent-sdk",
            "message_count": message_count,
            "auth_mode": self.config.auth_mode,
            "permission_request_policy": self.config.permission_request_policy,
        }
        if self.config.cwd:
            metadata["cwd"] = str(self.config.cwd)
        if self.config.model:
            metadata["model"] = self.config.model
        if self.config.max_turns is not None:
            metadata["max_turns"] = self.config.max_turns
        if self.config.allowed_tools:
            metadata["allowed_tool_count"] = len(self.config.allowed_tools)
        if self.config.disallowed_tools:
            metadata["disallowed_tool_count"] = len(self.config.disallowed_tools)
        metadata.update(dict(self.config.metadata))
        return metadata

    def _runtime_error_from_exception(self, exc: Exception) -> QoderRuntimeError:
        if isinstance(exc, QoderRuntimeError):
            return exc
        kind = _classify_sdk_exception(exc)
        return QoderRuntimeError(
            error_kind=kind,
            summary=self._redact(str(exc) or f"Qoder SDK failed with {type(exc).__name__}."),
            raw_error_type=type(exc).__name__,
            retryable=kind == "timeout",
        )

    def _redact(self, text: str) -> str:
        redacted = text
        for candidate in _sensitive_values(self._environment):
            redacted = redacted.replace(candidate, "[redacted]")
        return redacted


def _run_async(coro: Any) -> Any:
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    result: dict[str, Any] = {}

    def worker() -> None:
        try:
            result["value"] = asyncio.run(coro)
        except Exception as exc:  # pragma: no cover - re-raised in caller thread
            result["error"] = exc

    thread = threading.Thread(target=worker, name="qoder-sdk-query-client", daemon=True)
    thread.start()
    thread.join()
    if "error" in result:
        raise result["error"]
    return result.get("value")


def _message_to_mapping(message: Any) -> dict[str, Any]:
    if isinstance(message, dict):
        return dict(message)
    for method_name in ("model_dump", "dict", "to_dict"):
        method = getattr(message, method_name, None)
        if callable(method):
            try:
                value = method()
            except TypeError:
                continue
            if isinstance(value, dict):
                return dict(value)
    raw_dict = getattr(message, "__dict__", None)
    if isinstance(raw_dict, dict):
        return dict(raw_dict)
    return {}


def _is_permission_message(message: Any, normalized: Mapping[str, Any]) -> bool:
    marker = " ".join(
        str(value).lower()
        for value in (
            normalized.get("type", ""),
            normalized.get("kind", ""),
            normalized.get("event", ""),
            type(message).__name__,
        )
    )
    return "permission" in marker and any(token in marker for token in ("request", "tool", "use"))


def _permission_request_from_callback(
    args: tuple[Any, ...],
    kwargs: Mapping[str, Any],
    *,
    request: QoderQueryRequest,
    index: int,
) -> PermissionRequest:
    payload: dict[str, Any] = {}
    if args:
        first = args[0]
        if isinstance(first, Mapping):
            payload.update(first)
        else:
            payload["tool_name"] = getattr(first, "name", None) or getattr(first, "tool_name", None) or str(first)
    payload.update(kwargs)
    return _permission_request_from_payload(payload, request=request, index=index)


def _permission_request_from_message(
    message: Any,
    normalized: Mapping[str, Any],
    *,
    request: QoderQueryRequest,
    index: int,
) -> PermissionRequest:
    payload: dict[str, Any] = dict(normalized)
    if not payload:
        payload["tool_name"] = type(message).__name__
    return _permission_request_from_payload(payload, request=request, index=index)


def _permission_request_from_payload(
    payload: Mapping[str, Any],
    *,
    request: QoderQueryRequest,
    index: int,
) -> PermissionRequest:
    tool_name = _first_string(
        payload,
        "tool_name",
        "toolName",
        "name",
        "tool",
        "command",
    )
    target = _first_string(payload, "target", "path", "command", "url")
    if not target:
        target = _nested_target(payload)
    summary = _first_string(payload, "summary", "description", "reason")
    if not summary:
        summary = f"Qoder SDK requested permission for {tool_name or target or 'a tool'}."
    return PermissionRequest(
        request_id=_first_string(payload, "request_id", "requestId", "id")
        or f"qoder-permission-{index}",
        request_kind=_permission_kind(tool_name, target),
        run_id="",
        summary=summary,
        target=target,
    )


def _nested_target(payload: Mapping[str, Any]) -> str:
    for key in ("input", "args", "arguments"):
        value = payload.get(key)
        if isinstance(value, Mapping):
            nested = _first_string(value, "command", "path", "file", "url", "target")
            if nested:
                return nested
    return ""


def _permission_kind(tool_name: str, target: str) -> PermissionRequestKind:
    text = f"{tool_name} {target}".lower()
    if any(token in text for token in ("bash", "shell", "command", "terminal", "cmd", "powershell")):
        return "shell"
    if any(token in text for token in ("write", "edit", "patch", "create", "delete", "move")):
        return "artifact_write"
    if any(token in text for token in ("read", "grep", "search", "file")):
        return "artifact_read"
    if any(token in text for token in ("http", "https", "web", "fetch", "network")):
        return "network"
    return "tool"


def _response_candidate(normalized: Mapping[str, Any]) -> dict[str, Any] | None:
    if _looks_like_response(normalized):
        return dict(normalized)
    for key in ("result", "response", "final", "data"):
        value = normalized.get(key)
        if isinstance(value, dict) and _looks_like_response(value):
            return dict(value)
    return None


def _looks_like_response(value: Mapping[str, Any]) -> bool:
    return isinstance(value.get("summary"), str) and bool(value.get("summary"))


def _extract_text(message: Any, normalized: Mapping[str, Any]) -> str:
    for key in ("output_text", "content", "text", "message", "delta"):
        value = normalized.get(key)
        extracted = _text_from_value(value)
        if extracted:
            return extracted
    if isinstance(message, str):
        return message
    return ""


def _text_from_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts = [_text_from_value(item) for item in value]
        return "".join(part for part in parts if part)
    if isinstance(value, Mapping):
        for key in ("text", "content", "value"):
            extracted = _text_from_value(value.get(key))
            if extracted:
                return extracted
    return ""


def _first_string(payload: Mapping[str, Any], *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _compact_summary(text: str) -> str:
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if not first_line:
        return "Qoder SDK completed the task."
    if len(first_line) <= 160:
        return first_line
    return first_line[:157].rstrip() + "..."


def _classify_sdk_exception(exc: Exception) -> str:
    text = f"{type(exc).__name__} {exc}".lower()
    if "permission" in text or "denied" in text:
        return "permission_denied"
    if any(token in text for token in ("auth", "token", "credential", "unauthorized", "forbidden")):
        return "authentication_failed"
    if "timeout" in text or "timed out" in text:
        return "timeout"
    if "cancel" in text or "aborted" in text:
        return "policy_cancelled"
    if "tool" in text and "fail" in text:
        return "tool_execution_failed"
    return "unknown"


def _sensitive_values(environment: Mapping[str, str]) -> tuple[str, ...]:
    values: list[str] = []
    for key, value in environment.items():
        if not value or len(value) < 8:
            continue
        lowered = key.lower()
        if any(token in lowered for token in ("token", "key", "secret", "credential", "password")):
            values.append(value)
    return tuple(values)
