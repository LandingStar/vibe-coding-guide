"""Workspace-bound DBC command relay.

The relay is intentionally narrower than a shell: it runs the current package's
DBC CLI module for the MCP project root so agents do not need to resolve PATH,
virtualenv, or checkout details themselves.
"""

from __future__ import annotations

import os
import subprocess
import sys
import threading
from contextlib import redirect_stderr, redirect_stdout
import logging
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from io import StringIO
from pathlib import Path
from typing import Literal


WorkspaceDbcRelayMode = Literal["read", "mutate"]

WORKSPACE_DBC_RELAY_SCHEMA_VERSION = "workspace-dbc-command-relay/v1"

_READ_MODE_COMMANDS = frozenset(
    {
        "check",
        "codex",
        "doctor",
        "info",
        "opencode",
        "provider",
        "qoder",
        "resources",
        "validate",
        "worker-binding",
    }
)

_MUTATING_COMMANDS = frozenset(
    {
        "generate-instructions",
        "pack",
        "process",
        "scheduler",
    }
)

_MAX_CAPTURE_CHARS = 24_000
_IN_PROCESS_COMMANDS = frozenset(
    {
        "check",
        "codex",
        "doctor",
        "info",
        "opencode",
        "provider",
        "qoder",
        "resources",
        "validate",
        "worker-binding",
    }
)
_IN_PROCESS_LOCK = threading.RLock()


@dataclass(frozen=True, slots=True)
class WorkspaceDbcCommandRelayRequest:
    """Request for a workspace-bound DBC CLI invocation."""

    project_root: Path
    argv: tuple[str, ...]
    mode: WorkspaceDbcRelayMode = "read"
    timeout_seconds: int = 30
    python_executable: str = sys.executable
    package_root: Path = field(default_factory=lambda: Path(__file__).resolve().parents[3])
    environment: Mapping[str, str] | None = None


@dataclass(frozen=True, slots=True)
class WorkspaceDbcCommandRelayResult:
    """Secret-safe, bounded relay result."""

    ok: bool
    status: str
    argv: tuple[str, ...]
    mode: WorkspaceDbcRelayMode
    project_root: str
    command_preview: tuple[str, ...]
    cwd: str
    returncode: int | None = None
    execution_strategy: str = "in_process"
    stdout: str = ""
    stderr: str = ""
    error: str = ""
    denied_reason: str = ""
    timed_out: bool = False
    authority_split: Mapping[str, object] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": WORKSPACE_DBC_RELAY_SCHEMA_VERSION,
            "ok": self.ok,
            "status": self.status,
            "argv": list(self.argv),
            "mode": self.mode,
            "project_root": self.project_root,
            "command_preview": list(self.command_preview),
            "cwd": self.cwd,
            "returncode": self.returncode,
            "execution_strategy": self.execution_strategy,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "error": self.error,
            "denied_reason": self.denied_reason,
            "timed_out": self.timed_out,
            "authority_split": dict(self.authority_split),
        }


def run_workspace_dbc_command_relay(
    request: WorkspaceDbcCommandRelayRequest,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> WorkspaceDbcCommandRelayResult:
    """Run a DBC CLI argv through the current workspace MCP package instance."""

    project_root = Path(request.project_root).resolve()
    package_root = Path(request.package_root).resolve()
    argv = tuple(str(item) for item in request.argv)
    command = (str(request.python_executable), "-m", "src", *argv)
    base = {
        "argv": argv,
        "mode": request.mode,
        "project_root": str(project_root),
        "command_preview": command,
        "cwd": str(project_root),
        "authority_split": _authority_split_for_mode(
            request.mode,
            subprocess_executed=False,
        ),
    }

    validation_error = _validate_request(argv, request.mode, request.timeout_seconds)
    if validation_error:
        return WorkspaceDbcCommandRelayResult(
            ok=False,
            status="denied",
            denied_reason=validation_error,
            **base,
        )

    if argv[0] in _IN_PROCESS_COMMANDS:
        return _run_in_process(argv, base)

    base = {
        **base,
        "authority_split": _authority_split_for_mode(
            request.mode,
            subprocess_executed=True,
        ),
    }
    env = dict(os.environ if request.environment is None else request.environment)
    existing_pythonpath = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = (
        str(package_root)
        if not existing_pythonpath
        else f"{package_root}{os.pathsep}{existing_pythonpath}"
    )

    try:
        completed = runner(
            list(command),
            cwd=str(project_root),
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=request.timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        return WorkspaceDbcCommandRelayResult(
            ok=False,
            status="timeout",
            execution_strategy="subprocess",
            stdout=_bounded_text(exc.stdout or ""),
            stderr=_bounded_text(exc.stderr or ""),
            error=f"DBC relay timed out after {request.timeout_seconds} second(s).",
            timed_out=True,
            **base,
        )
    except FileNotFoundError as exc:
        return WorkspaceDbcCommandRelayResult(
            ok=False,
            status="failed",
            execution_strategy="subprocess",
            error=f"Python executable not found: {exc}",
            **base,
        )
    except Exception as exc:
        return WorkspaceDbcCommandRelayResult(
            ok=False,
            status="failed",
            execution_strategy="subprocess",
            error=f"{type(exc).__name__}: {exc}",
            **base,
        )

    return WorkspaceDbcCommandRelayResult(
        ok=completed.returncode == 0,
        status="ok" if completed.returncode == 0 else "command_failed",
        execution_strategy="subprocess",
        returncode=completed.returncode,
        stdout=_bounded_text(completed.stdout),
        stderr=_bounded_text(completed.stderr),
        **base,
    )


def _run_in_process(
    argv: tuple[str, ...],
    base: Mapping[str, object],
) -> WorkspaceDbcCommandRelayResult:
    """Run read-mode DBC commands in-process to avoid MCP stdio nested-spawn stalls."""

    stdout = StringIO()
    stderr = StringIO()
    project_root = Path(str(base["cwd"]))
    try:
        from ... import __main__ as dbc_cli
    except Exception as exc:
        return WorkspaceDbcCommandRelayResult(
            ok=False,
            status="failed",
            returncode=None,
            execution_strategy="in_process",
            error=f"Failed to import DBC CLI module: {type(exc).__name__}: {exc}",
            **base,
        )

    with _IN_PROCESS_LOCK:
        previous_cwd = Path.cwd()
        root_logger = logging.getLogger()
        previous_handlers = list(root_logger.handlers)
        previous_level = root_logger.level
        capture_handler = logging.StreamHandler(stderr)
        capture_handler.setFormatter(logging.Formatter("%(message)s"))
        try:
            os.chdir(project_root)
            root_logger.handlers = [capture_handler]
            if root_logger.level > logging.WARNING:
                root_logger.setLevel(logging.WARNING)
            command = argv[0]
            handler = getattr(dbc_cli, "_COMMANDS", {}).get(command)
            if handler is None:
                return WorkspaceDbcCommandRelayResult(
                    ok=False,
                    status="denied",
                    returncode=None,
                    execution_strategy="in_process",
                    denied_reason=f"unsupported DBC command for in-process relay: {command}",
                    **base,
                )
            with redirect_stdout(stdout), redirect_stderr(stderr):
                returncode = int(handler(list(argv[1:])))
        except SystemExit as exc:
            code = exc.code if isinstance(exc.code, int) else 1
            returncode = int(code)
        except Exception as exc:
            return WorkspaceDbcCommandRelayResult(
                ok=False,
                status="failed",
                returncode=None,
                execution_strategy="in_process",
                stdout=_bounded_text(stdout.getvalue()),
                stderr=_bounded_text(stderr.getvalue()),
                error=f"{type(exc).__name__}: {exc}",
                **base,
            )
        finally:
            root_logger.handlers = previous_handlers
            root_logger.setLevel(previous_level)
            os.chdir(previous_cwd)

    return WorkspaceDbcCommandRelayResult(
        ok=returncode == 0,
        status="ok" if returncode == 0 else "command_failed",
        returncode=returncode,
        execution_strategy="in_process",
        stdout=_bounded_text(stdout.getvalue()),
        stderr=_bounded_text(stderr.getvalue()),
        **base,
    )


def _validate_request(
    argv: Sequence[str],
    mode: WorkspaceDbcRelayMode,
    timeout_seconds: int,
) -> str:
    if mode not in {"read", "mutate"}:
        return "mode must be 'read' or 'mutate'"
    if timeout_seconds < 1 or timeout_seconds > 300:
        return "timeoutSeconds must be between 1 and 300"
    if not argv:
        return "argv must contain a DBC command name"
    if any(not isinstance(item, str) or not item.strip() for item in argv):
        return "argv must contain only non-empty strings"
    command = argv[0].strip()
    if command.startswith("-"):
        return "argv[0] must be a DBC command name, not a global flag"
    if command not in _READ_MODE_COMMANDS and command not in _MUTATING_COMMANDS:
        return f"unsupported DBC command for relay: {command}"
    if mode == "read" and command in _MUTATING_COMMANDS:
        return f"DBC command '{command}' requires mode='mutate'"
    return ""


def _bounded_text(value: object) -> str:
    text = str(value or "")
    if len(text) <= _MAX_CAPTURE_CHARS:
        return text
    omitted = len(text) - _MAX_CAPTURE_CHARS
    return text[:_MAX_CAPTURE_CHARS] + f"\n...[truncated {omitted} chars]"


def _authority_split_for_mode(
    mode: WorkspaceDbcRelayMode,
    *,
    subprocess_executed: bool,
) -> dict[str, object]:
    return {
        "read_only": mode == "read",
        "provider_executed": False,
        "mcp_server_started": False,
        "mcp_tool_called": False,
        "config_mutated": False,
        "secret_material_read": False,
        "subprocess_executed": subprocess_executed,
        "generic_shell": False,
        "workspace_bound": True,
    }
