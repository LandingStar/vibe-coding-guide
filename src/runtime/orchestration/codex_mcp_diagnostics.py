"""Credential-safe Codex MCP exposure diagnostics.

This module inspects host registration state only. It does not start the
doc-based-coding MCP server, call MCP tools, mutate Codex config, or read auth
material.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


_PROJECT_HEADER_RE = re.compile(
    r"^\s*\[projects\.(?P<quote>['\"])(?P<project>.*?)(?P=quote)\]\s*$"
)
_TRUST_LEVEL_RE = re.compile(r"^\s*trust_level\s*=\s*(?P<quote>['\"])(?P<value>.*?)(?P=quote)\s*$")


@dataclass(frozen=True, slots=True)
class CodexMcpExposureDiagnostic:
    """Safe summary of whether Codex can see the DBC MCP server."""

    project_root: str
    executable: str
    executable_resolved: str
    cli_available: bool
    diagnostic_status: str
    project_config_path: str
    project_config_exists: bool
    user_config_path: str
    user_config_exists: bool
    project_trusted: bool | None
    trust_match: str = ""
    mcp_list_ran: bool = False
    mcp_list_returncode: int | None = None
    mcp_list_summary: str = ""
    mcp_servers_zero_hint: bool = False
    doc_based_coding_server_visible: bool = False
    doc_based_coding_server_enabled: bool = False
    suspected_problem: str = ""
    remediation: tuple[str, ...] = ()
    command_preview: tuple[str, ...] = field(default_factory=tuple)

    def to_json_dict(self) -> dict[str, object]:
        return {
            "project_root": self.project_root,
            "executable": self.executable,
            "executable_resolved": self.executable_resolved,
            "cli_available": self.cli_available,
            "diagnostic_status": self.diagnostic_status,
            "project_config_path": self.project_config_path,
            "project_config_exists": self.project_config_exists,
            "user_config_path": self.user_config_path,
            "user_config_exists": self.user_config_exists,
            "project_trusted": self.project_trusted,
            "trust_match": self.trust_match,
            "mcp_list_ran": self.mcp_list_ran,
            "mcp_list_returncode": self.mcp_list_returncode,
            "mcp_list_summary": self.mcp_list_summary,
            "mcp_servers_zero_hint": self.mcp_servers_zero_hint,
            "doc_based_coding_server_visible": self.doc_based_coding_server_visible,
            "doc_based_coding_server_enabled": self.doc_based_coding_server_enabled,
            "suspected_problem": self.suspected_problem,
            "remediation": list(self.remediation),
            "command_preview": list(self.command_preview),
            "authority_split": {
                "provider_executed": False,
                "mcp_server_started": False,
                "mcp_tool_called": False,
                "codex_config_mutated": False,
                "secret_material_read": False,
            },
        }


def inspect_codex_mcp_exposure(
    project_root: str | Path,
    *,
    executable: str = "codex",
    user_config_path: str | Path | None = None,
    environment: Mapping[str, str] | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    which: Callable[[str], str | None] | None = None,
    timeout_seconds: int = 10,
) -> CodexMcpExposureDiagnostic:
    """Inspect whether Codex can see a doc-based-coding MCP registration."""

    project = Path(project_root).resolve()
    project_config = project / ".codex" / "config.toml"
    env = dict(os.environ if environment is None else environment)
    config_path = Path(user_config_path) if user_config_path else _default_user_config_path(env)
    resolved = (which or shutil.which)(executable) or ""
    trusted, trust_match = _read_project_trust(config_path, project)
    command_preview = (executable, "-C", str(project), "mcp", "list")

    base = {
        "project_root": str(project),
        "executable": executable,
        "executable_resolved": resolved,
        "cli_available": bool(resolved),
        "project_config_path": str(project_config),
        "project_config_exists": project_config.exists(),
        "user_config_path": str(config_path),
        "user_config_exists": config_path.exists(),
        "project_trusted": trusted,
        "trust_match": trust_match,
        "command_preview": command_preview,
    }

    if not resolved:
        return CodexMcpExposureDiagnostic(
            **base,
            diagnostic_status="skipped",
            suspected_problem="codex_cli_unavailable",
            remediation=(
                "Install Codex CLI or pass --executable to the Codex readiness command.",
                "After Codex CLI is available, rerun `doc-based-coding codex readiness`.",
            ),
        )

    try:
        completed = (runner or subprocess.run)(
            [executable, "-C", str(project), "mcp", "list"],
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
        )
    except FileNotFoundError:
        return CodexMcpExposureDiagnostic(
            **base,
            diagnostic_status="skipped",
            suspected_problem="codex_cli_unavailable",
            remediation=(
                "Codex CLI was not found when running `codex mcp list`.",
                "Install Codex CLI or pass --executable to the Codex readiness command.",
            ),
        )
    except subprocess.TimeoutExpired:
        return CodexMcpExposureDiagnostic(
            **base,
            diagnostic_status="warning",
            mcp_list_ran=True,
            suspected_problem="codex_mcp_list_timeout",
            remediation=(
                "`codex mcp list` timed out; rerun after the host is responsive.",
                "If the problem repeats, inspect Codex installation and workspace trust.",
            ),
        )
    except Exception as exc:
        return CodexMcpExposureDiagnostic(
            **base,
            diagnostic_status="warning",
            mcp_list_ran=True,
            suspected_problem="codex_mcp_list_failed",
            mcp_list_summary=_compact_summary(type(exc).__name__),
            remediation=(
                "`codex mcp list` failed before producing a usable report.",
                "Inspect Codex CLI installation, project trust, and project-level `.codex/config.toml`.",
            ),
        )

    combined = f"{completed.stdout or ''}\n{completed.stderr or ''}"
    summary = _compact_summary(combined)
    zero_hint = _has_zero_mcp_hint(combined)
    visible, enabled = _parse_doc_based_coding_server_visibility(combined)
    status, problem, remediation = _classify_diagnostic(
        project_config_exists=project_config.exists(),
        project_trusted=trusted,
        mcp_list_returncode=completed.returncode,
        mcp_servers_zero_hint=zero_hint,
        doc_based_coding_server_visible=visible,
        doc_based_coding_server_enabled=enabled,
    )

    return CodexMcpExposureDiagnostic(
        **base,
        diagnostic_status=status,
        mcp_list_ran=True,
        mcp_list_returncode=completed.returncode,
        mcp_list_summary=summary,
        mcp_servers_zero_hint=zero_hint,
        doc_based_coding_server_visible=visible,
        doc_based_coding_server_enabled=enabled,
        suspected_problem=problem,
        remediation=remediation,
    )


def _default_user_config_path(environment: Mapping[str, str]) -> Path:
    codex_home = environment.get("CODEX_HOME", "").strip()
    if codex_home:
        return Path(codex_home) / "config.toml"
    return Path.home() / ".codex" / "config.toml"


def _read_project_trust(config_path: Path, project: Path) -> tuple[bool | None, str]:
    if not config_path.exists():
        return None, "user_config_missing"
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError:
        return None, "user_config_unreadable"

    current_project = ""
    project_key = _normalize_project_path(project)
    for raw_line in text.splitlines():
        header = _PROJECT_HEADER_RE.match(raw_line)
        if header:
            current_project = _normalize_project_path(header.group("project"))
            continue
        if not current_project:
            continue
        trust = _TRUST_LEVEL_RE.match(raw_line)
        if trust and current_project == project_key:
            value = trust.group("value").strip().lower()
            return value == "trusted", "exact" if value == "trusted" else "not_trusted"
    return False, "not_found"


def _normalize_project_path(value: str | Path) -> str:
    text = str(value).strip().replace("/", "\\")
    try:
        text = str(Path(text).expanduser().resolve()).replace("/", "\\")
    except OSError:
        text = str(Path(text).expanduser()).replace("/", "\\")
    return text.rstrip("\\").lower()


def _parse_doc_based_coding_server_visibility(text: str) -> tuple[bool, bool]:
    visible = False
    enabled = False
    for line in text.splitlines():
        lowered = line.lower()
        if "doc-based-coding" in lowered or "doc_based_coding" in lowered:
            visible = True
            if "enabled" in lowered:
                enabled = True
    return visible, enabled


def _has_zero_mcp_hint(text: str) -> bool:
    lowered = text.lower()
    return "no mcp servers configured" in lowered or "mcp servers 0" in lowered


def _classify_diagnostic(
    *,
    project_config_exists: bool,
    project_trusted: bool | None,
    mcp_list_returncode: int,
    mcp_servers_zero_hint: bool,
    doc_based_coding_server_visible: bool,
    doc_based_coding_server_enabled: bool,
) -> tuple[str, str, tuple[str, ...]]:
    if doc_based_coding_server_visible and doc_based_coding_server_enabled:
        return (
            "ok",
            "",
            ("Codex can see an enabled doc-based-coding MCP server for this project.",),
        )
    if mcp_list_returncode != 0:
        return (
            "warning",
            "codex_mcp_list_failed",
            (
                "`codex mcp list` returned a non-zero exit code.",
                "Inspect Codex CLI installation, workspace trust, and MCP registration.",
            ),
        )
    if not project_config_exists:
        return (
            "warning",
            "project_codex_config_missing",
            (
                "Create a project-level `.codex/config.toml` that registers doc-based-coding MCP.",
                "Use `docs/installation-guide.md` for the installation-state MCP example.",
            ),
        )
    if project_trusted is not True:
        return (
            "warning",
            "project_not_trusted",
            (
                "Mark this project trusted in user-level `~/.codex/config.toml`.",
                "Restart the current Codex CLI / VS Code Codex plugin session after changing trust or MCP config.",
            ),
        )
    if mcp_servers_zero_hint:
        return (
            "warning",
            "codex_mcp_not_configured",
            (
                "`codex mcp list` reports no MCP servers for this project.",
                "Check project trust, project-level `.codex/config.toml`, and restart the Codex host session.",
            ),
        )
    return (
        "warning",
        "doc_based_coding_server_not_visible",
        (
            "`codex mcp list` did not show a doc-based-coding server.",
            "Check the MCP server name, command, args, cwd, and whether the Codex host session was restarted.",
        ),
    )


def _compact_summary(value: Any) -> str:
    text = str(value or "").strip().replace("\r\n", "\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return ""
    summary = " | ".join(lines[:3])
    if len(summary) <= 240:
        return summary
    return summary[:237].rstrip() + "..."
