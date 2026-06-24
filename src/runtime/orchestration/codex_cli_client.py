"""Host-owned Codex CLI process client wrapper.

The wrapper is intentionally optional and host-owned. Runtime adapters depend on
the ``CodexCliClient`` protocol; only host wiring constructs this process-backed
client after granting process-spawn permission.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from .runtime_adapter import (
    CodexCliRequest,
    CodexCliResult,
    CodexCliRuntimeError,
)

CodexCliApprovalPolicy = Literal["untrusted", "on-request", "never"]
CodexCliSandboxMode = Literal["read-only", "workspace-write", "danger-full-access"]


@dataclass(frozen=True, slots=True)
class CodexCliClientConfig:
    """Host-owned options for invoking ``codex exec``."""

    executable: str = "codex"
    cwd: str | Path = ""
    model: str = ""
    sandbox: CodexCliSandboxMode = "workspace-write"
    ask_for_approval: CodexCliApprovalPolicy = "never"
    profile: str = ""
    config_overrides: tuple[str, ...] = ()
    extra_args: tuple[str, ...] = ()
    timeout_seconds: int | None = None
    ephemeral: bool = True
    color: str = "never"
    metadata: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class CodexCliHostReadinessReport:
    """Credential-safe host readiness report for Codex CLI."""

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


class CodexCliProcessClient:
    """``CodexCliClient`` implementation backed by ``codex exec``."""

    def __init__(
        self,
        config: CodexCliClientConfig | None = None,
        *,
        runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
        which: Callable[[str], str | None] | None = None,
    ) -> None:
        self.config = config or CodexCliClientConfig()
        self._runner = runner or subprocess.run
        self._which = which or shutil.which

    def exec(self, request: CodexCliRequest) -> CodexCliResult:
        """Run one bounded Codex CLI task and return a compact result."""

        self.validate_host_ready()
        prompt = self._build_prompt(request)
        with tempfile.TemporaryDirectory(prefix="dbc-codex-cli-") as temp_dir:
            output_path = Path(temp_dir) / "last-message.txt"
            command = self._build_command(request, output_path)
            try:
                cwd = self._execution_cwd(request)
                completed = self._runner(
                    command,
                    input=prompt,
                    text=True,
                    capture_output=True,
                    cwd=cwd,
                    timeout=self.config.timeout_seconds,
                    check=False,
                )
            except subprocess.TimeoutExpired as exc:
                raise CodexCliRuntimeError(
                    error_kind="timeout",
                    summary="Codex CLI exec timed out.",
                    raw_error_type=type(exc).__name__,
                    retryable=True,
                ) from exc
            except FileNotFoundError as exc:
                raise CodexCliRuntimeError(
                    error_kind="cli_unavailable",
                    summary=f"Codex CLI executable is unavailable: {self.config.executable}",
                    raw_error_type=type(exc).__name__,
                ) from exc
            except Exception as exc:
                raise CodexCliRuntimeError(
                    error_kind="unknown",
                    summary=self._redact(str(exc) or "Codex CLI process failed."),
                    raw_error_type=type(exc).__name__,
                ) from exc
            if completed.returncode != 0:
                raise CodexCliRuntimeError(
                    error_kind=_error_kind_from_process_output(completed),
                    summary=self._redact(
                        _compact_summary(completed.stderr or completed.stdout)
                        or f"Codex CLI exited with code {completed.returncode}."
                    ),
                    raw_error_type=f"ExitCode{completed.returncode}",
                    retryable=completed.returncode in {124, 137},
                )
            output_text = ""
            if output_path.exists():
                output_text = output_path.read_text(encoding="utf-8").strip()
            if not output_text:
                output_text = (completed.stdout or "").strip()
            if not output_text:
                raise CodexCliRuntimeError(
                    error_kind="invalid_response",
                    summary="Codex CLI completed without a usable final message.",
                )
            return CodexCliResult(
                summary=_compact_summary(output_text),
                output_text=output_text,
                metadata=self._result_metadata(completed, request),
            )

    def validate_host_ready(self) -> None:
        """Fail closed before scheduler execution when Codex CLI is missing."""

        if not self._which(self.config.executable):
            raise CodexCliRuntimeError(
                error_kind="cli_unavailable",
                summary=f"Codex CLI executable is unavailable: {self.config.executable}",
                raw_error_type="MissingExecutable",
            )

    def host_readiness_report(self) -> CodexCliHostReadinessReport:
        """Return credential-safe readiness details without executing a task."""

        resolved = self._which(self.config.executable) or ""
        try:
            self.validate_host_ready()
        except CodexCliRuntimeError as exc:
            return CodexCliHostReadinessReport(
                executable=self.config.executable,
                executable_resolved=resolved,
                cli_available=bool(resolved),
                ready=False,
                error_kind=exc.error_kind,
                raw_error_type=exc.raw_error_type,
                summary=exc.summary,
            )
        return CodexCliHostReadinessReport(
            executable=self.config.executable,
            executable_resolved=resolved,
            cli_available=True,
            ready=True,
        )

    def _build_command(
        self,
        request: CodexCliRequest,
        output_path: Path,
    ) -> list[str]:
        command = [
            self.config.executable,
            "exec",
            "--output-last-message",
            str(output_path),
            "--color",
            self.config.color,
            "--sandbox",
            self.config.sandbox,
            "--ask-for-approval",
            self.config.ask_for_approval,
        ]
        cwd = str(self.config.cwd or "")
        if request.task.runtime_workspace_root:
            cwd = request.task.runtime_workspace_root
        if cwd:
            command.extend(["--cd", cwd])
        model = self.config.model or request.agent.model
        if model:
            command.extend(["--model", model])
        if self.config.profile:
            command.extend(["--profile", self.config.profile])
        if self.config.ephemeral:
            command.append("--ephemeral")
        for override in self.config.config_overrides:
            command.extend(["--config", override])
        command.extend(self.config.extra_args)
        command.append("-")
        return command

    def _build_prompt(self, request: CodexCliRequest) -> str:
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
        request: CodexCliRequest,
    ) -> dict[str, object]:
        metadata = {
            "cli": "codex",
            "executable": self.config.executable,
            "returncode": completed.returncode,
            "sandbox": self.config.sandbox,
            "ask_for_approval": self.config.ask_for_approval,
            "ephemeral": self.config.ephemeral,
            "stdout_bytes": len((completed.stdout or "").encode("utf-8")),
            "stderr_bytes": len((completed.stderr or "").encode("utf-8")),
        }
        if self.config.model:
            metadata["model"] = self.config.model
        metadata["cwd"] = self._execution_cwd(request) or ""
        metadata.update(dict(self.config.metadata))
        return metadata

    def _execution_cwd(self, request: CodexCliRequest) -> str | None:
        return self._execution_cwd_from_value(
            request.task.runtime_workspace_root or self.config.cwd
        )

    @staticmethod
    def _execution_cwd_from_value(value: str | Path) -> str | None:
        cwd = str(value or "")
        return cwd or None

    def _redact(self, value: str) -> str:
        redacted = value
        for key in ("OPENAI_API_KEY", "CODEX_AUTH_TOKEN", "QODER_PERSONAL_ACCESS_TOKEN"):
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


def _compact_summary(value: Any) -> str:
    text = str(value or "").strip().replace("\r\n", "\n")
    first_line = next((line.strip() for line in text.splitlines() if line.strip()), "")
    if len(first_line) <= 160:
        return first_line
    return first_line[:157].rstrip() + "..."
