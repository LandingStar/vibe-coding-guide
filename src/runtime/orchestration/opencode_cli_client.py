"""Host-owned OpenCode CLI process client wrapper.

The wrapper is optional and host-owned. Runtime adapters depend on the
``OpenCodeCliClient`` protocol; only host wiring constructs this process-backed
client after granting process-spawn permission.
"""

from __future__ import annotations

import shutil
import subprocess
import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from .runtime_adapter import (
    OpenCodeCliRequest,
    OpenCodeCliResult,
    OpenCodeCliRuntimeError,
)

OpenCodeCliOutputFormat = Literal["text", "json"]


@dataclass(frozen=True, slots=True)
class OpenCodeCliClientConfig:
    """Host-owned options for invoking ``opencode run``."""

    executable: str = "opencode"
    cwd: str | Path = ""
    model: str = ""
    output_format: OpenCodeCliOutputFormat = "json"
    attach_url: str = ""
    session_id: str = ""
    continue_session: bool = False
    fork_session: bool = False
    extra_args: tuple[str, ...] = ()
    timeout_seconds: int | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.session_id and self.continue_session:
            raise ValueError("OpenCode CLI config cannot set both session_id and continue_session")
        if self.fork_session and not (self.session_id or self.continue_session):
            raise ValueError(
                "OpenCode CLI config fork_session requires session_id or continue_session"
            )


@dataclass(frozen=True, slots=True)
class OpenCodeCliHostReadinessReport:
    """Credential-safe host readiness report for OpenCode CLI."""

    executable: str
    executable_resolved: str
    cli_available: bool
    ready: bool
    error_kind: str = ""
    raw_error_type: str = ""
    summary: str = ""

    def to_json_dict(self) -> dict[str, object]:
        return {
            "executable": self.executable,
            "executable_resolved": self.executable_resolved,
            "cli_available": self.cli_available,
            "ready": self.ready,
            "error_kind": self.error_kind,
            "raw_error_type": self.raw_error_type,
            "summary": self.summary,
        }


class OpenCodeCliProcessClient:
    """``OpenCodeCliClient`` implementation backed by ``opencode run``."""

    def __init__(
        self,
        config: OpenCodeCliClientConfig | None = None,
        *,
        runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
        which: Callable[[str], str | None] | None = None,
    ) -> None:
        self.config = config or OpenCodeCliClientConfig()
        self._runner = runner or subprocess.run
        self._which = which or shutil.which

    def exec(self, request: OpenCodeCliRequest) -> OpenCodeCliResult:
        """Run one bounded OpenCode CLI task and return a compact result."""

        executable = self.validate_host_ready()
        prompt = self._build_prompt(request)
        command = self._build_command(request, executable=executable)
        try:
            cwd = self._execution_cwd(request)
            completed = self._runner(
                command,
                input=None,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                cwd=cwd,
                timeout=self.config.timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise OpenCodeCliRuntimeError(
                error_kind="timeout",
                summary="OpenCode CLI run timed out.",
                raw_error_type=type(exc).__name__,
                retryable=True,
            ) from exc
        except FileNotFoundError as exc:
            raise OpenCodeCliRuntimeError(
                error_kind="cli_unavailable",
                summary=f"OpenCode CLI executable is unavailable: {self.config.executable}",
                raw_error_type=type(exc).__name__,
            ) from exc
        except Exception as exc:
            raise OpenCodeCliRuntimeError(
                error_kind="unknown",
                summary=self._redact(str(exc) or "OpenCode CLI process failed."),
                raw_error_type=type(exc).__name__,
            ) from exc
        if completed.returncode != 0:
            raise OpenCodeCliRuntimeError(
                error_kind=_error_kind_from_process_output(completed),
                summary=self._redact(
                    _compact_summary(completed.stderr or completed.stdout)
                    or f"OpenCode CLI exited with code {completed.returncode}."
                ),
                raw_error_type=f"ExitCode{completed.returncode}",
                retryable=completed.returncode in {124, 137},
            )
        output_text = (completed.stdout or "").strip()
        if not output_text:
            raise OpenCodeCliRuntimeError(
                error_kind="invalid_response",
                summary="OpenCode CLI completed without stdout output.",
            )
        normalized_output = _extract_output_text(output_text, self.config.output_format)
        return OpenCodeCliResult(
            summary=_compact_summary(normalized_output),
            output_text=normalized_output,
            metadata=self._result_metadata(completed, request),
        )

    def validate_host_ready(self) -> str:
        """Fail closed before scheduler execution when OpenCode CLI is missing."""

        resolved = self._which(self.config.executable)
        if not resolved:
            raise OpenCodeCliRuntimeError(
                error_kind="cli_unavailable",
                summary=f"OpenCode CLI executable is unavailable: {self.config.executable}",
                raw_error_type="MissingExecutable",
            )
        return resolved

    def host_readiness_report(self) -> OpenCodeCliHostReadinessReport:
        """Return credential-safe readiness details without executing a task."""

        resolved = self._which(self.config.executable) or ""
        try:
            self.validate_host_ready()
        except OpenCodeCliRuntimeError as exc:
            return OpenCodeCliHostReadinessReport(
                executable=self.config.executable,
                executable_resolved=resolved,
                cli_available=bool(resolved),
                ready=False,
                error_kind=exc.error_kind,
                raw_error_type=exc.raw_error_type,
                summary=exc.summary,
            )
        return OpenCodeCliHostReadinessReport(
            executable=self.config.executable,
            executable_resolved=resolved,
            cli_available=True,
            ready=True,
        )

    def _build_command(
        self,
        request: OpenCodeCliRequest,
        *,
        executable: str | None = None,
    ) -> list[str]:
        command = [executable or self.config.executable, "run"]
        attach_url, session_id, continue_session, fork_session = self._session_options(request)
        cwd = str(self.config.cwd or "")
        if request.task.runtime_workspace_root:
            cwd = request.task.runtime_workspace_root
        if cwd:
            command.extend(["--dir", cwd])
        model = self.config.model or request.agent.model
        if model:
            command.extend(["--model", model])
        if attach_url:
            command.extend(["--attach", attach_url])
        if session_id:
            command.extend(["--session", session_id])
        elif continue_session:
            command.append("--continue")
        if fork_session:
            command.append("--fork")
        if self.config.output_format:
            command.extend(["--format", _cli_output_format(self.config.output_format)])
        command.extend(self.config.extra_args)
        command.append(self._build_prompt(request))
        return command

    def _build_prompt(self, request: OpenCodeCliRequest) -> str:
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

    def _result_metadata(
        self,
        completed: subprocess.CompletedProcess[str],
        request: OpenCodeCliRequest,
    ) -> dict[str, object]:
        attach_url, session_id, continue_session, fork_session = self._session_options(request)
        host_session_selector = (
            {}
            if request.host_session is None
            else request.host_session.to_metadata()
        )
        metadata = {
            "cli": "opencode",
            "executable": self.config.executable,
            "returncode": completed.returncode,
            "output_format": self.config.output_format,
            "attached_to_server": bool(attach_url),
            "attach_url": attach_url,
            "session_id": session_id,
            "continue_session": continue_session,
            "fork_session": fork_session,
            "session_selector_source": self._session_selector_source(request),
            "host_session_selector": host_session_selector,
            "stdout_bytes": len((completed.stdout or "").encode("utf-8")),
            "stderr_bytes": len((completed.stderr or "").encode("utf-8")),
        }
        if self.config.model:
            metadata["model"] = self.config.model
        metadata["cwd"] = self._execution_cwd(request) or ""
        metadata.update(dict(self.config.metadata))
        return metadata

    def _execution_cwd(self, request: OpenCodeCliRequest) -> str | None:
        cwd = str(request.task.runtime_workspace_root or self.config.cwd or "")
        return cwd or None

    def _session_options(
        self,
        request: OpenCodeCliRequest,
    ) -> tuple[str, str, bool, bool]:
        if (
            self.config.attach_url
            or self.config.session_id
            or self.config.continue_session
            or self.config.fork_session
        ):
            return (
                self.config.attach_url,
                self.config.session_id,
                self.config.continue_session,
                self.config.fork_session,
            )
        if request.host_session is None:
            return ("", "", False, False)
        return (
            request.host_session.attach_url,
            request.host_session.session_id,
            request.host_session.continue_session,
            request.host_session.fork_session,
        )

    def _session_selector_source(self, request: OpenCodeCliRequest) -> str:
        if (
            self.config.attach_url
            or self.config.session_id
            or self.config.continue_session
            or self.config.fork_session
        ):
            return "explicit_config"
        if request.host_session is not None:
            return request.host_session.selector_source or "session_ledger"
        return "none"

    def _redact(self, value: str) -> str:
        redacted = value
        for key in (
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "OPENCODE_API_KEY",
            "QODER_PERSONAL_ACCESS_TOKEN",
            "CODEX_AUTH_TOKEN",
        ):
            redacted = redacted.replace(key + "=", key + "=[redacted]")
        return redacted


def _error_kind_from_process_output(
    completed: subprocess.CompletedProcess[str],
) -> str:
    text = f"{completed.stderr}\n{completed.stdout}".lower()
    if "auth" in text or "login" in text or "api key" in text:
        return "authentication_failed"
    if "permission" in text or "approval" in text:
        return "permission_denied"
    return "process_failed"


def _extract_output_text(output: str, output_format: OpenCodeCliOutputFormat) -> str:
    if output_format != "json":
        return output
    chunks: list[str] = []
    for line in output.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            event = json.loads(stripped)
        except json.JSONDecodeError:
            continue
        chunks.extend(_text_chunks_from_json_value(event))
    normalized = "\n".join(chunk for chunk in chunks if chunk).strip()
    return normalized or output


def _cli_output_format(output_format: OpenCodeCliOutputFormat) -> str:
    if output_format == "text":
        return "default"
    return output_format


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
