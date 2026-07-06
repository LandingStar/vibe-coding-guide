"""Unified self-check / doctor framework."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from .artifact_paths import dbc_artifact_path, legacy_codex_artifact_path
from .codex_mcp_diagnostics import inspect_codex_mcp_exposure
from .opencode_cli_client import OpenCodeCliClientConfig, OpenCodeCliProcessClient
from .opencode_server_api_client import (
    OpenCodeServerApiClientConfig,
    inspect_opencode_server_api_readiness,
)


SelfCheckProfile = Literal["codex", "opencode", "vscode", "runtime", "scheduler", "mcp", "all"]
SelfCheckStatus = Literal["ok", "warning", "failed", "skipped"]

SELF_CHECK_REPORT_SCHEMA_VERSION = "self-check-report/v1"
SELF_CHECK_RESULT_SCHEMA_VERSION = "self-check-result/v1"
SELF_CHECK_PROFILES: tuple[str, ...] = (
    "codex",
    "opencode",
    "vscode",
    "runtime",
    "scheduler",
    "mcp",
    "all",
)


@dataclass(frozen=True, slots=True)
class SelfCheckAuthoritySplit:
    """Safety envelope reported by every doctor check."""

    read_only: bool = True
    provider_executed: bool = False
    mcp_server_started: bool = False
    mcp_tool_called: bool = False
    config_mutated: bool = False
    secret_material_read: bool = False

    def to_json_dict(self) -> dict[str, object]:
        return {
            "read_only": self.read_only,
            "provider_executed": self.provider_executed,
            "mcp_server_started": self.mcp_server_started,
            "mcp_tool_called": self.mcp_tool_called,
            "config_mutated": self.config_mutated,
            "secret_material_read": self.secret_material_read,
        }


@dataclass(frozen=True, slots=True)
class SelfCheckContext:
    """Injected context shared by self-check implementations."""

    project_root: Path
    environment: Mapping[str, str] = field(default_factory=lambda: dict(os.environ))
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run
    which: Callable[[str], str | None] = shutil.which
    timeout_seconds: int = 10
    user_config_path: Path | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def resolve_project_root(self) -> Path:
        return Path(self.project_root).resolve()


@dataclass(frozen=True, slots=True)
class SelfCheckResult:
    """One doctor check result."""

    check_id: str
    profiles: tuple[str, ...]
    title: str
    status: SelfCheckStatus
    summary: str
    evidence: Mapping[str, object] = field(default_factory=dict)
    suspected_problem: str = ""
    remediation: tuple[str, ...] = ()
    authority_split: SelfCheckAuthoritySplit = field(default_factory=SelfCheckAuthoritySplit)
    secret_safe: bool = True
    duration_ms: int = 0

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": SELF_CHECK_RESULT_SCHEMA_VERSION,
            "check_id": self.check_id,
            "profiles": list(self.profiles),
            "title": self.title,
            "status": self.status,
            "summary": self.summary,
            "evidence": dict(self.evidence),
            "suspected_problem": self.suspected_problem,
            "remediation": list(self.remediation),
            "authority_split": self.authority_split.to_json_dict(),
            "secret_safe": self.secret_safe,
            "duration_ms": self.duration_ms,
        }


@dataclass(frozen=True, slots=True)
class SelfCheckDefinition:
    """Registered doctor check definition."""

    check_id: str
    profiles: tuple[str, ...]
    title: str
    description: str
    run: Callable[[SelfCheckContext], SelfCheckResult]


@dataclass(frozen=True, slots=True)
class SelfCheckReport:
    """Aggregated doctor report."""

    profile: str
    project_root: str
    checks: tuple[SelfCheckResult, ...]
    overall_status: SelfCheckStatus
    counts: Mapping[str, int]
    next_actions: tuple[str, ...]
    authority_split: SelfCheckAuthoritySplit

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": SELF_CHECK_REPORT_SCHEMA_VERSION,
            "profile": self.profile,
            "project_root": self.project_root,
            "overall_status": self.overall_status,
            "counts": dict(self.counts),
            "checks": [check.to_json_dict() for check in self.checks],
            "next_actions": list(self.next_actions),
            "authority_split": self.authority_split.to_json_dict(),
        }


class SelfCheckRegistry:
    """Small in-process registry for doctor checks."""

    def __init__(self, checks: Sequence[SelfCheckDefinition] = ()) -> None:
        self._checks: dict[str, SelfCheckDefinition] = {}
        for check in checks:
            self.register(check)

    def register(self, check: SelfCheckDefinition) -> None:
        if check.check_id in self._checks:
            raise ValueError(f"Duplicate self-check id: {check.check_id}")
        unknown = sorted(set(check.profiles) - set(SELF_CHECK_PROFILES))
        if unknown:
            raise ValueError(
                f"Self-check {check.check_id} has unknown profile(s): {', '.join(unknown)}"
            )
        if "all" in check.profiles:
            raise ValueError("Self-check definitions must not include profile 'all'")
        self._checks[check.check_id] = check

    def checks_for_profile(self, profile: str) -> tuple[SelfCheckDefinition, ...]:
        if profile not in SELF_CHECK_PROFILES:
            raise ValueError(
                f"Unknown doctor profile: {profile}. Expected one of: {', '.join(SELF_CHECK_PROFILES)}"
            )
        checks = tuple(self._checks.values())
        if profile == "all":
            return checks
        return tuple(check for check in checks if profile in check.profiles)

    def run(self, profile: str, context: SelfCheckContext) -> SelfCheckReport:
        checks = tuple(_run_definition(definition, context) for definition in self.checks_for_profile(profile))
        counts = _status_counts(checks)
        overall = _overall_status(counts)
        next_actions = _next_actions(checks)
        return SelfCheckReport(
            profile=profile,
            project_root=str(context.resolve_project_root()),
            checks=checks,
            overall_status=overall,
            counts=counts,
            next_actions=next_actions,
            authority_split=_aggregate_authority_split(checks),
        )


def build_default_self_check_registry() -> SelfCheckRegistry:
    """Build the production registry."""

    return SelfCheckRegistry(
        (
            build_workspace_dbc_relay_check(),
            build_codex_mcp_exposure_check(),
            build_opencode_cli_readiness_check(),
            build_opencode_server_api_readiness_check(),
            build_scheduler_storage_visibility_check(),
        )
    )


def build_workspace_dbc_relay_check() -> SelfCheckDefinition:
    return SelfCheckDefinition(
        check_id="workspace.dbc_command_relay",
        profiles=("codex", "mcp", "runtime"),
        title="Workspace DBC Command Relay",
        description="Report the workspace-bound DBC relay surface for this MCP package instance.",
        run=run_workspace_dbc_relay_self_check,
    )


def build_codex_mcp_exposure_check() -> SelfCheckDefinition:
    return SelfCheckDefinition(
        check_id="codex.mcp_exposure",
        profiles=("codex", "mcp"),
        title="Codex MCP Exposure",
        description="Check whether Codex can see the doc-based-coding MCP server for this project.",
        run=run_codex_mcp_exposure_self_check,
    )


def build_opencode_cli_readiness_check() -> SelfCheckDefinition:
    return SelfCheckDefinition(
        check_id="opencode.cli_readiness",
        profiles=("opencode", "runtime"),
        title="OpenCode CLI Readiness",
        description="Check whether the OpenCode CLI executable is available without running a task.",
        run=run_opencode_cli_readiness_self_check,
    )


def build_opencode_server_api_readiness_check() -> SelfCheckDefinition:
    return SelfCheckDefinition(
        check_id="opencode.server_api_readiness",
        profiles=("opencode", "runtime"),
        title="OpenCode Server/API Readiness",
        description=(
            "Check whether a host-owned OpenCode server/API endpoint is reachable "
            "without creating sessions or running provider tasks."
        ),
        run=run_opencode_server_api_readiness_self_check,
    )


def build_scheduler_storage_visibility_check() -> SelfCheckDefinition:
    return SelfCheckDefinition(
        check_id="scheduler.storage_visibility",
        profiles=("scheduler",),
        title="Scheduler Storage Visibility",
        description="Check whether default scheduler storage artifacts are present and readable.",
        run=run_scheduler_storage_visibility_self_check,
    )


def run_workspace_dbc_relay_self_check(context: SelfCheckContext) -> SelfCheckResult:
    started = time.monotonic()
    project_root = context.resolve_project_root()
    evidence = {
        "tool_name": "workspaceDbcCommand",
        "project_root": str(project_root),
        "command_template": [sys.executable, "-m", "src", "<argv...>"],
        "cwd": str(project_root),
        "resolution_policy": "per-agent MCP server package instance",
        "path_fallback_required": False,
        "generic_shell": False,
    }
    return SelfCheckResult(
        check_id="workspace.dbc_command_relay",
        profiles=("codex", "mcp", "runtime"),
        title="Workspace DBC Command Relay",
        status="ok",
        summary=(
            "Workspace DBC relay is available as the standard CLI-equivalent "
            "surface when this MCP server is exposed."
        ),
        evidence=evidence,
        remediation=(
            "When MCP is available, call `workspaceDbcCommand` for DBC CLI-equivalent actions instead of relying on bare PATH resolution.",
        ),
        authority_split=SelfCheckAuthoritySplit(
            read_only=True,
            provider_executed=False,
            mcp_server_started=False,
            mcp_tool_called=False,
            config_mutated=False,
            secret_material_read=False,
        ),
        secret_safe=True,
        duration_ms=max(0, int((time.monotonic() - started) * 1000)),
    )


def run_codex_mcp_exposure_self_check(context: SelfCheckContext) -> SelfCheckResult:
    started = time.monotonic()
    diagnostic = inspect_codex_mcp_exposure(
        context.resolve_project_root(),
        executable=str(context.metadata.get("codex_executable") or "codex"),
        user_config_path=context.user_config_path,
        environment=context.environment,
        runner=context.runner,
        which=context.which,
        timeout_seconds=context.timeout_seconds,
    )
    payload = diagnostic.to_json_dict()
    status = _diagnostic_status_to_check_status(str(payload["diagnostic_status"]))
    summary = _codex_mcp_summary(payload)
    evidence = {
        "project_config_exists": payload["project_config_exists"],
        "user_config_exists": payload["user_config_exists"],
        "project_trusted": payload["project_trusted"],
        "mcp_list_ran": payload["mcp_list_ran"],
        "mcp_list_returncode": payload["mcp_list_returncode"],
        "mcp_servers_zero_hint": payload["mcp_servers_zero_hint"],
        "doc_based_coding_server_visible": payload["doc_based_coding_server_visible"],
        "doc_based_coding_server_enabled": payload["doc_based_coding_server_enabled"],
        "mcp_list_summary": payload["mcp_list_summary"],
        "command_preview": payload["command_preview"],
    }
    return SelfCheckResult(
        check_id="codex.mcp_exposure",
        profiles=("codex", "mcp"),
        title="Codex MCP Exposure",
        status=status,
        summary=summary,
        evidence=evidence,
        suspected_problem=str(payload["suspected_problem"]),
        remediation=tuple(str(item) for item in payload["remediation"]),
        authority_split=SelfCheckAuthoritySplit(
            read_only=True,
            provider_executed=False,
            mcp_server_started=bool(payload["authority_split"]["mcp_server_started"]),
            mcp_tool_called=bool(payload["authority_split"]["mcp_tool_called"]),
            config_mutated=bool(payload["authority_split"]["codex_config_mutated"]),
            secret_material_read=bool(payload["authority_split"]["secret_material_read"]),
        ),
        secret_safe=True,
        duration_ms=max(0, int((time.monotonic() - started) * 1000)),
    )


def run_opencode_cli_readiness_self_check(context: SelfCheckContext) -> SelfCheckResult:
    started = time.monotonic()
    executable = str(context.metadata.get("opencode_executable") or "opencode")
    report = OpenCodeCliProcessClient(
        OpenCodeCliClientConfig(executable=executable),
        runner=context.runner,
        which=context.which,
    ).host_readiness_report()
    payload = report.to_json_dict()
    ready = bool(payload["ready"])
    status: SelfCheckStatus = "ok" if ready else "skipped"
    suspected = "" if ready else str(payload["error_kind"] or "opencode_cli_unavailable")
    remediation = (
        ("OpenCode CLI is available to the host.",)
        if ready
        else (
            "Install OpenCode CLI or pass the expected executable through future doctor context.",
            "OpenCode doctor readiness does not run provider tasks; rerun after host provisioning.",
        )
    )
    return SelfCheckResult(
        check_id="opencode.cli_readiness",
        profiles=("opencode", "runtime"),
        title="OpenCode CLI Readiness",
        status=status,
        summary=(
            "OpenCode CLI is available."
            if ready
            else "OpenCode CLI is unavailable; readiness check was skipped."
        ),
        evidence={
            "executable": payload["executable"],
            "executable_resolved": payload["executable_resolved"],
            "cli_available": payload["cli_available"],
            "ready": payload["ready"],
            "error_kind": payload["error_kind"],
            "raw_error_type": payload["raw_error_type"],
            "summary": payload["summary"],
        },
        suspected_problem=suspected,
        remediation=remediation,
        authority_split=SelfCheckAuthoritySplit(
            read_only=True,
            provider_executed=False,
            mcp_server_started=False,
            mcp_tool_called=False,
            config_mutated=False,
            secret_material_read=False,
        ),
        secret_safe=True,
        duration_ms=max(0, int((time.monotonic() - started) * 1000)),
    )


def run_opencode_server_api_readiness_self_check(
    context: SelfCheckContext,
) -> SelfCheckResult:
    started = time.monotonic()
    metadata = context.metadata
    timeout = float(
        metadata.get("opencode_server_api_timeout_seconds")
        or context.timeout_seconds
        or 10
    )
    report = inspect_opencode_server_api_readiness(
        OpenCodeServerApiClientConfig(
            base_url=str(metadata.get("opencode_server_api_base_url") or ""),
            health_path=str(metadata.get("opencode_server_api_health_path") or "/global/health"),
            doc_path=str(metadata.get("opencode_server_api_doc_path") or "/doc"),
            timeout_seconds=timeout,
            username_env_var=str(
                metadata.get("opencode_server_api_username_env_var")
                or "OPENCODE_SERVER_USERNAME"
            ),
            password_env_var=str(
                metadata.get("opencode_server_api_password_env_var")
                or "OPENCODE_SERVER_PASSWORD"
            ),
        ),
        check_doc=bool(metadata.get("opencode_server_api_check_doc", False)),
        opener=metadata.get("opencode_server_api_opener"),
        environ=context.environment,
    )
    payload = report.to_json_dict()
    ready = bool(payload["ready"])
    status: SelfCheckStatus = "ok" if ready else "skipped"
    suspected = "" if ready else str(payload["error_kind"] or "opencode_server_api_unavailable")
    remediation = (
        ("OpenCode server/API endpoint is reachable.",)
        if ready
        else (
            "Start or provision `opencode serve` outside doc-based-coding if server/API transport is needed.",
            "Use `doc-based-coding opencode server-api-readiness --base-url URL --check-doc` for a focused endpoint probe.",
        )
    )
    return SelfCheckResult(
        check_id="opencode.server_api_readiness",
        profiles=("opencode", "runtime"),
        title="OpenCode Server/API Readiness",
        status=status,
        summary=(
            "OpenCode server/API endpoint is reachable."
            if ready
            else "OpenCode server/API endpoint is unreachable; server/API readiness was skipped."
        ),
        evidence={
            "base_url": payload["base_url"],
            "health_url": payload["health_url"],
            "doc_url": payload["doc_url"],
            "ready": payload["ready"],
            "healthy": payload["healthy"],
            "doc_checked": payload["doc_checked"],
            "doc_available": payload["doc_available"],
            "http_status": payload["http_status"],
            "doc_http_status": payload["doc_http_status"],
            "error_kind": payload["error_kind"],
            "raw_error_type": payload["raw_error_type"],
            "summary": payload["summary"],
            "auth_configured": payload["auth_configured"],
            "username_env_var": payload["username_env_var"],
            "password_env_var": payload["password_env_var"],
            "openapi_version": payload["openapi_version"],
            "api_title": payload["api_title"],
            "api_version": payload["api_version"],
        },
        suspected_problem=suspected,
        remediation=remediation,
        authority_split=SelfCheckAuthoritySplit(
            read_only=True,
            provider_executed=False,
            mcp_server_started=False,
            mcp_tool_called=False,
            config_mutated=False,
            secret_material_read=False,
        ),
        secret_safe=True,
        duration_ms=max(0, int((time.monotonic() - started) * 1000)),
    )


def run_scheduler_storage_visibility_self_check(context: SelfCheckContext) -> SelfCheckResult:
    started = time.monotonic()
    project = context.resolve_project_root()
    scheduler_dir = project / dbc_artifact_path("scheduler")
    legacy_scheduler_dir = project / legacy_codex_artifact_path("scheduler")
    snapshot_candidates = (
        scheduler_dir / "state.json",
        scheduler_dir / "scheduler-state.json",
        scheduler_dir / "leader-worker-dispatcher-state.json",
    )
    event_log_candidates = (
        scheduler_dir / "events.jsonl",
        scheduler_dir / "scheduler-events.jsonl",
        scheduler_dir / "leader-worker-dispatcher-events.jsonl",
    )
    existing_snapshots = tuple(path for path in snapshot_candidates if path.exists())
    existing_event_logs = tuple(path for path in event_log_candidates if path.exists())
    evidence: dict[str, object] = {
        "scheduler_dir": str(scheduler_dir),
        "scheduler_dir_exists": scheduler_dir.is_dir(),
        "legacy_scheduler_dir": str(legacy_scheduler_dir),
        "legacy_scheduler_dir_exists": legacy_scheduler_dir.is_dir(),
        "snapshot_candidates": [str(path) for path in snapshot_candidates],
        "event_log_candidates": [str(path) for path in event_log_candidates],
        "existing_snapshots": [str(path) for path in existing_snapshots],
        "existing_event_logs": [str(path) for path in existing_event_logs],
    }
    status: SelfCheckStatus = "ok"
    suspected = ""
    remediation: tuple[str, ...] = ("Scheduler storage artifacts are visible.",)
    if not scheduler_dir.is_dir():
        status = "warning"
        suspected = "scheduler_storage_missing"
        remediation = (
            "No `.dbc/scheduler` directory was found for this project.",
            "Run a scheduler/bootstrap flow that creates scheduler artifacts before expecting scheduler readback.",
            "If only `.codex/scheduler` exists, migrate legacy DBC runtime artifacts to `.dbc/scheduler`; `.codex/config.toml` remains the Codex host registration file.",
        )
    elif not existing_snapshots and not existing_event_logs:
        status = "warning"
        suspected = "scheduler_artifacts_missing"
        remediation = (
            "Scheduler directory exists but no default snapshot or event-log artifact was found.",
            "Check whether the project uses custom scheduler paths or has not run scheduler workflows yet.",
        )

    if existing_snapshots:
        first_snapshot = existing_snapshots[0]
        try:
            from .scheduler_store import read_scheduler_state_snapshot

            state = read_scheduler_state_snapshot(first_snapshot)
            evidence["readable_snapshot_path"] = str(first_snapshot)
            evidence["task_count"] = len(state.tasks)
            evidence["agent_count"] = len(
                {
                    task.agent.agent_id
                    for task in state.tasks.values()
                    if task.agent.agent_id
                }
            )
            evidence["context_scope_count"] = len(
                {
                    task.context_scope.context_id
                    for task in state.tasks.values()
                    if task.context_scope.context_id
                }
            )
        except Exception as exc:
            status = "failed"
            suspected = "scheduler_snapshot_unreadable"
            evidence["unreadable_snapshot_path"] = str(first_snapshot)
            evidence["snapshot_error_type"] = type(exc).__name__
            remediation = (
                "A scheduler snapshot exists but could not be read.",
                "Inspect the snapshot JSON/schema before running scheduler workflows.",
            )
    if existing_event_logs:
        first_log = existing_event_logs[0]
        try:
            lines = first_log.read_text(encoding="utf-8").splitlines()
            evidence["readable_event_log_path"] = str(first_log)
            evidence["event_log_line_count"] = len([line for line in lines if line.strip()])
        except Exception as exc:
            status = "failed"
            suspected = suspected or "scheduler_event_log_unreadable"
            evidence["unreadable_event_log_path"] = str(first_log)
            evidence["event_log_error_type"] = type(exc).__name__
            remediation = (
                "A scheduler event log exists but could not be read.",
                "Inspect the event log file permissions and encoding.",
            )

    return SelfCheckResult(
        check_id="scheduler.storage_visibility",
        profiles=("scheduler",),
        title="Scheduler Storage Visibility",
        status=status,
        summary=_scheduler_storage_summary(status, evidence, suspected),
        evidence=evidence,
        suspected_problem=suspected,
        remediation=remediation,
        authority_split=SelfCheckAuthoritySplit(
            read_only=True,
            provider_executed=False,
            mcp_server_started=False,
            mcp_tool_called=False,
            config_mutated=False,
            secret_material_read=False,
        ),
        secret_safe=True,
        duration_ms=max(0, int((time.monotonic() - started) * 1000)),
    )


def run_self_check_doctor(
    project_root: str | Path,
    *,
    profile: str = "all",
    registry: SelfCheckRegistry | None = None,
    context: SelfCheckContext | None = None,
    environment: Mapping[str, str] | None = None,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    which: Callable[[str], str | None] | None = None,
    timeout_seconds: int = 10,
    user_config_path: str | Path | None = None,
    metadata: Mapping[str, object] | None = None,
) -> SelfCheckReport:
    """Run doctor checks for a profile."""

    selected_registry = registry or build_default_self_check_registry()
    selected_context = context or SelfCheckContext(
        project_root=Path(project_root),
        environment=dict(os.environ if environment is None else environment),
        runner=runner or subprocess.run,
        which=which or shutil.which,
        timeout_seconds=timeout_seconds,
        user_config_path=Path(user_config_path) if user_config_path else None,
        metadata=dict(metadata or {}),
    )
    return selected_registry.run(profile, selected_context)


def doctor_exit_code(report: SelfCheckReport) -> int:
    """CLI exit code for a doctor report."""

    return 2 if report.overall_status == "failed" else 0


def _run_definition(definition: SelfCheckDefinition, context: SelfCheckContext) -> SelfCheckResult:
    started = time.monotonic()
    try:
        result = definition.run(context)
    except Exception as exc:
        return SelfCheckResult(
            check_id=definition.check_id,
            profiles=definition.profiles,
            title=definition.title,
            status="failed",
            summary=f"Self-check failed: {type(exc).__name__}",
            suspected_problem="self_check_runtime_error",
            remediation=("Inspect the check implementation and rerun with a focused profile.",),
            duration_ms=max(0, int((time.monotonic() - started) * 1000)),
        )
    return result


def _status_counts(checks: Sequence[SelfCheckResult]) -> dict[str, int]:
    counts = {"ok": 0, "warning": 0, "failed": 0, "skipped": 0}
    for check in checks:
        counts[check.status] += 1
    return counts


def _overall_status(counts: Mapping[str, int]) -> SelfCheckStatus:
    if counts["failed"]:
        return "failed"
    if counts["warning"]:
        return "warning"
    if counts["ok"]:
        return "ok"
    return "skipped"


def _next_actions(checks: Sequence[SelfCheckResult]) -> tuple[str, ...]:
    actions: list[str] = []
    seen: set[str] = set()
    for check in checks:
        if check.status == "ok":
            continue
        for item in check.remediation:
            if item not in seen:
                seen.add(item)
                actions.append(item)
    return tuple(actions)


def _aggregate_authority_split(checks: Sequence[SelfCheckResult]) -> SelfCheckAuthoritySplit:
    if not checks:
        return SelfCheckAuthoritySplit()
    return SelfCheckAuthoritySplit(
        read_only=all(check.authority_split.read_only for check in checks),
        provider_executed=any(check.authority_split.provider_executed for check in checks),
        mcp_server_started=any(check.authority_split.mcp_server_started for check in checks),
        mcp_tool_called=any(check.authority_split.mcp_tool_called for check in checks),
        config_mutated=any(check.authority_split.config_mutated for check in checks),
        secret_material_read=any(check.authority_split.secret_material_read for check in checks),
    )


def _diagnostic_status_to_check_status(status: str) -> SelfCheckStatus:
    if status in {"ok", "warning", "failed", "skipped"}:
        return status  # type: ignore[return-value]
    return "failed"


def _codex_mcp_summary(payload: Mapping[str, object]) -> str:
    if payload.get("doc_based_coding_server_enabled") is True:
        return "Codex can see an enabled doc-based-coding MCP server."
    suspected = str(payload.get("suspected_problem") or "")
    if suspected == "project_not_trusted":
        return "Codex project trust is missing, so project-level MCP config may not load."
    if suspected == "project_codex_config_missing":
        return "Project-level `.codex/config.toml` is missing."
    if suspected == "codex_cli_unavailable":
        return "Codex CLI is unavailable; MCP exposure check was skipped."
    return str(payload.get("mcp_list_summary") or "Codex MCP exposure needs attention.")


def _scheduler_storage_summary(
    status: SelfCheckStatus,
    evidence: Mapping[str, object],
    suspected_problem: str,
) -> str:
    if status == "ok":
        task_count = evidence.get("task_count")
        if isinstance(task_count, int):
            return f"Scheduler storage is visible; readable snapshot contains {task_count} task(s)."
        return "Scheduler storage artifacts are visible."
    if suspected_problem == "scheduler_storage_missing":
        if evidence.get("legacy_scheduler_dir_exists") is True:
            return "Current `.dbc/scheduler` storage is missing; legacy `.codex/scheduler` exists."
        return "Scheduler storage directory is missing."
    if suspected_problem == "scheduler_artifacts_missing":
        return "Scheduler storage directory exists but default artifacts are missing."
    if suspected_problem == "scheduler_snapshot_unreadable":
        return "Scheduler snapshot exists but is unreadable."
    if suspected_problem == "scheduler_event_log_unreadable":
        return "Scheduler event log exists but is unreadable."
    return "Scheduler storage visibility needs attention."
