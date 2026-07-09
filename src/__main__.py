"""CLI entry point for the doc-based-coding platform.

Installed entry point:
    doc-based-coding process "input text"      — Run full governance chain
    doc-based-coding info                      — Show loaded pack info
    doc-based-coding validate                  — Check project constraints
    doc-based-coding check [input text]        — Run constraint/state check only
    doc-based-coding resources <subcommand>    — Inspect MCP resources
    doc-based-coding readback inspect          — Inspect readback envelopes
    doc-based-coding codex readiness           — Check Codex CLI host readiness
    doc-based-coding opencode readiness        — Check OpenCode CLI host readiness
    doc-based-coding qoder readiness           — Check Qoder SDK host readiness
    doc-based-coding qoder smoke               — Run host-owned Qoder smoke helper
    doc-based-coding worker-binding <subcommand> — Maintain continuous worker bindings
    doc-based-coding scheduler <subcommand>    — Scheduler operator helpers
    doc-based-coding doctor                    — Run unified self-check diagnostics
    doc-based-coding generate-instructions     — Generate agent instructions segment

Module entry point:
    python -m src process "input text"

Global flags:
    --debug                                    — Show full traceback on errors
"""

from __future__ import annotations

import json
import sys
import traceback
from datetime import UTC, datetime
from pathlib import Path

from .runtime.bridge import RuntimeBridge
from .workflow.pipeline import ErrorInfo, Pipeline

_DEBUG = False


def _find_project_root() -> Path:
    """Walk up from CWD to find a directory with design_docs/ or .codex/."""
    cwd = Path.cwd().resolve()
    for p in [cwd, *cwd.parents]:
        if (p / "design_docs").is_dir() or (p / ".codex").is_dir():
            return p
    return cwd


def _handle_error(message: str, exc: Exception, *, category: str = "unknown", source: str = "cli") -> int:
    """Print error message and optionally full traceback."""
    print(f"{message}: {exc}", file=sys.stderr)
    if _DEBUG:
        traceback.print_exc(file=sys.stderr)
        err = ErrorInfo(
            category=category,
            message=f"{message}: {exc}",
            source=source,
            detail=traceback.format_exc(),
        )
        print(json.dumps(err.to_dict(), ensure_ascii=False), file=sys.stderr)
    return 1


def _print_json(data: dict) -> None:
    """Pretty-print a dict as JSON."""
    print(json.dumps(data, indent=2, ensure_ascii=False, default=str))


def cmd_process(args: list[str]) -> int:
    """Run full governance chain on the given input text."""
    if not args:
        print("Usage: doc-based-coding process \"input text\"", file=sys.stderr)
        return 1

    input_text = " ".join(args)
    root = _find_project_root()

    try:
        bridge = RuntimeBridge(root, dry_run=True)
    except Exception as e:
        return _handle_error("Error initializing pipeline", e, category="init_failed")

    result = bridge.pipeline.process(input_text)
    _print_json(result.to_dict())
    return 0


def cmd_info(args: list[str]) -> int:
    """Show loaded pack info."""
    root = _find_project_root()

    try:
        bridge = RuntimeBridge(root, dry_run=True)
    except Exception as e:
        return _handle_error("Error initializing pipeline", e, category="init_failed")

    _print_json(bridge.pipeline.info())
    return 0


def cmd_validate(args: list[str]) -> int:
    """Check project constraints."""
    root = _find_project_root()

    try:
        bridge = RuntimeBridge(root, dry_run=True)
    except Exception as e:
        return _handle_error("Error initializing pipeline", e, category="init_failed")

    result = bridge.pipeline.check_constraints()
    _print_json(result.to_dict())

    if result.has_violations:
        blocking = [v for v in result.violations if v.severity == "block"]
        print("\n✓ Validation completed successfully.", file=sys.stderr)
        print("⚠ Governance status: BLOCKED", file=sys.stderr)
        for v in blocking:
            print(f"  → {v.constraint}: {v.message}", file=sys.stderr)
        return 2
    print("\n✓ Validation completed successfully. No governance blocks.", file=sys.stderr)
    return 0


def cmd_check(args: list[str]) -> int:
    """Run operator-oriented constraint/state checks without full governance."""
    requested_input = " ".join(args).strip()
    root = _find_project_root()

    try:
        bridge = RuntimeBridge(root, dry_run=True)
    except Exception as e:
        return _handle_error("Error initializing pipeline", e, category="init_failed")

    constraints = bridge.pipeline.check_constraints()
    output = {"constraints": constraints.to_dict()}
    if requested_input:
        output["requested_input"] = requested_input
        output["note"] = (
            "check no longer runs the governance chain. "
            "Use `doc-based-coding process <text>` for full PDP -> PEP execution."
        )
    _print_json(output)

    if constraints.has_violations:
        blocking = [v for v in constraints.violations if v.severity == "block"]
        print("\n✓ Check completed successfully.", file=sys.stderr)
        print("⚠ Governance status: BLOCKED", file=sys.stderr)
        for v in blocking:
            print(f"  → {v.constraint}: {v.message}", file=sys.stderr)
        return 2
    print("\n✓ Check completed successfully. No governance blocks.", file=sys.stderr)
    return 0


def cmd_generate_instructions(args: list[str]) -> int:
    """Generate agent instructions from loaded packs."""
    root = _find_project_root()

    output_path = None
    explicit_target = None

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--output":
            if i + 1 >= len(args):
                print("Usage: doc-based-coding generate-instructions [--target generic|codex|copilot] [--output PATH]", file=sys.stderr)
                return 1
            output_path = Path(args[i + 1])
            i += 2
            continue
        if arg == "--target":
            if i + 1 >= len(args):
                print("Usage: doc-based-coding generate-instructions [--target generic|codex|copilot] [--output PATH]", file=sys.stderr)
                return 1
            explicit_target = args[i + 1]
            i += 2
            continue
        print(f"Unknown generate-instructions option: {arg}", file=sys.stderr)
        print("Usage: doc-based-coding generate-instructions [--target generic|codex|copilot] [--output PATH]", file=sys.stderr)
        return 1

    try:
        from .workflow.instructions_generator import (
            generate_instructions_from_project,
            infer_instruction_target,
        )

        target = explicit_target or infer_instruction_target(output_path) or "generic"
        text = generate_instructions_from_project(root, target=target)
    except Exception as e:
        return _handle_error("Error generating instructions", e, category="process_failed")

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        print(f"Instructions written to {output_path}", file=sys.stderr)
    else:
        print(text)
    return 0


def cmd_resources(args: list[str]) -> int:
    """Inspect read-only MCP resources without starting an MCP host."""
    if not args or args[0] in ("-h", "--help"):
        print(
            "Usage: doc-based-coding resources <subcommand> [args]\n\n"
            "Subcommands:\n"
            "  list                    List read-only resources\n"
            "  read <uri>              Read a resource by URI\n",
        )
        return 0

    sub = args[0]
    root = _find_project_root()

    try:
        from .mcp.tools import GovernanceTools

        tools = GovernanceTools(root, dry_run=True)
    except Exception as e:
        return _handle_error("Error initializing resource inspector", e, category="init_failed")

    if sub == "list":
        resources = tools.list_resources()
        if isinstance(resources, dict) and resources.get("category"):
            _print_json(resources)
            return 1
        print(json.dumps(resources, indent=2, ensure_ascii=False, default=str))
        return 0

    if sub == "read":
        if len(args) < 2:
            print("Usage: doc-based-coding resources read <uri>", file=sys.stderr)
            return 1
        uri = args[1]
        content = tools.read_resource(uri)
        if content is None:
            print(f"Resource not found: {uri}", file=sys.stderr)
            return 1
        if isinstance(content, dict):
            _print_json(content)
        else:
            print(content)
        return 0

    print(f"Unknown resources subcommand: {sub}", file=sys.stderr)
    print("Usage: doc-based-coding resources <list|read> [args]", file=sys.stderr)
    return 1


_QODER_READINESS_USAGE = (
    "Usage: doc-based-coding qoder readiness "
    "[--auth-mode env|qodercli] [--auth-env-var NAME] [--sdk-module NAME]"
)

_QODER_SMOKE_USAGE = (
    "Usage: doc-based-coding qoder smoke "
    "[--auth-mode env|qodercli] [--auth-env-var NAME] [--sdk-module NAME] "
    "[--cwd PATH] [--model NAME] [--max-turns N] "
    "[--permission-request-policy deny|surface] "
    "[--snapshot-path PATH] [--event-log-path PATH] "
    "[--evidence-id ID] [--evidence-path PATH] "
    "[--projection-output-path PATH] [--host-invocation-id ID] "
    "[--reason TEXT] [--reset-snapshot] [--no-initialize-snapshot] "
    "[--timestamp TIMESTAMP]"
)

_QODER_GUIDE_WORKER_SMOKE_USAGE = (
    "Usage: doc-based-coding qoder guide-worker-smoke "
    "[--auth-mode env|qodercli] [--auth-env-var NAME] [--sdk-module NAME] "
    "[--cwd PATH] [--model NAME] [--max-turns N] "
    "[--permission-request-policy deny|surface] "
    "[--artifact-store-path PATH] [--admission-ledger-path PATH] "
    "[--snapshot-path PATH] [--event-log-path PATH] "
    "[--evidence-id ID] [--evidence-path PATH] "
    "[--git-worktree-sandbox-root PATH] [--sandbox-allocation-evidence-id ID] "
    "[--sandbox-allocation-evidence-path PATH] "
    "[--host-invocation-id ID] [--reason TEXT] "
    "[--runtime-invocation-log-path PATH] [--runtime-invocation-max-attempts N] "
    "[--runtime-invocation-backoff-seconds N] "
    "[--guide-task-title TEXT] [--guide-task-summary TEXT] "
    "[--planner-lane LANE_ID=LABEL:FOCUS[:ARTIFACT,ARTIFACT[:SANDBOX_KIND]]] "
    "[--max-parallel-lanes N] [--max-waves N] "
    "[--wave-execution-mode serial|threaded] [--timestamp TIMESTAMP]"
)

_CODEX_READINESS_USAGE = (
    "Usage: doc-based-coding codex readiness [--executable PATH] [--project-root PATH]"
)

_DOCTOR_USAGE = (
    "Usage: doc-based-coding doctor "
    "[--profile codex|opencode|vscode|runtime|scheduler|mcp|all] "
    "[--project-root PATH] [--timeout-seconds N]"
)

_READBACK_INSPECT_USAGE = (
    "Usage: doc-based-coding readback inspect "
    "--kind worker-report|validation-receipt|runtime-invocation-log|scheduler-event-log|exchange-artifact|host-evidence "
    "[--path PATH] [--artifact-id ID] [--version VERSION] "
    "[--source-kind KIND] [--latest-limit N] [--actor ACTOR] [--timestamp TIMESTAMP]"
)

_CODEX_GUIDE_WORKER_SMOKE_USAGE = (
    "Usage: doc-based-coding codex guide-worker-smoke "
    "[--executable PATH] [--cwd PATH] [--model NAME] "
    "[--sandbox read-only|workspace-write|danger-full-access] "
    "[--ask-for-approval untrusted|on-request|never] "
    "[--artifact-store-path PATH] [--admission-ledger-path PATH] "
    "[--snapshot-path PATH] [--event-log-path PATH] "
    "[--evidence-id ID] [--evidence-path PATH] "
    "[--git-worktree-sandbox-root PATH] [--sandbox-allocation-evidence-id ID] "
    "[--sandbox-allocation-evidence-path PATH] "
    "[--host-invocation-id ID] [--reason TEXT] "
    "[--runtime-invocation-log-path PATH] [--runtime-invocation-max-attempts N] "
    "[--runtime-invocation-backoff-seconds N] "
    "[--guide-task-title TEXT] [--guide-task-summary TEXT] "
    "[--planner-lane LANE_ID=LABEL:FOCUS[:ARTIFACT,ARTIFACT[:SANDBOX_KIND]]] "
    "[--max-parallel-lanes N] [--max-waves N] "
    "[--wave-execution-mode serial|threaded] [--timestamp TIMESTAMP]"
)

_OPENCODE_READINESS_USAGE = (
    "Usage: doc-based-coding opencode readiness [--executable PATH]"
)

_OPENCODE_SERVE_READINESS_USAGE = (
    "Usage: doc-based-coding opencode serve-readiness "
    "[--executable PATH] [--hostname HOST] [--port N] [--attach-url URL] "
    "[--health-path PATH] [--health-timeout-seconds N] [--require-healthy] "
    "[--username-env-var NAME] [--password-env-var NAME]"
)

_OPENCODE_SERVER_API_READINESS_USAGE = (
    "Usage: doc-based-coding opencode server-api-readiness "
    "[--base-url URL] [--health-path PATH] [--doc-path PATH] [--check-doc] "
    "[--timeout-seconds N] [--username-env-var NAME] [--password-env-var NAME]"
)

_OPENCODE_SERVE_LIFECYCLE_USAGE = (
    "Usage: doc-based-coding opencode serve-lifecycle <record|inspect> [args]"
)

_OPENCODE_SERVE_LIFECYCLE_RECORD_USAGE = (
    "Usage: doc-based-coding opencode serve-lifecycle record "
    "--action start|stop|restart|status|external "
    "[--status planned|observed|succeeded|failed] "
    "[--ledger-path PATH] [--executable PATH] [--hostname HOST] [--port N] "
    "[--attach-url URL] [--receipt-id ID] [--timestamp TIMESTAMP] "
    "[--pid PID] [--process-ref REF] [--actor ID] [--reason TEXT] "
    "[--note TEXT] [--no-command-preview]"
)

_OPENCODE_SERVE_LIFECYCLE_INSPECT_USAGE = (
    "Usage: doc-based-coding opencode serve-lifecycle inspect "
    "[--ledger-path PATH] [--action start|stop|restart|status|external] "
    "[--status planned|observed|succeeded|failed] [--latest-limit N]"
)

_OPENCODE_SESSION_USAGE = (
    "Usage: doc-based-coding opencode session "
    "<claim|release|inspect|recover-stale> [args]"
)

_OPENCODE_SESSION_CLAIM_USAGE = (
    "Usage: doc-based-coding opencode session claim "
    "--scope-kind lane|agent|task|custom --scope-id ID "
    "--attach-url URL --session-id ID "
    "[--ledger-path PATH] [--binding-id ID] [--owner-agent-id ID] "
    "[--lane-id ID] [--worker-agent-id ID] [--reason TEXT] "
    "[--timestamp TIMESTAMP] [--expires-at TIMESTAMP] [--no-replace-existing]"
)

_OPENCODE_SESSION_RELEASE_USAGE = (
    "Usage: doc-based-coding opencode session release "
    "(--binding-id ID | --scope-kind lane|agent|task|custom --scope-id ID) "
    "[--ledger-path PATH] [--status released|expired] "
    "[--timestamp TIMESTAMP] [--reason TEXT]"
)

_OPENCODE_SESSION_INSPECT_USAGE = (
    "Usage: doc-based-coding opencode session inspect "
    "[--ledger-path PATH] [--scope-kind lane|agent|task|custom] "
    "[--scope-id ID] [--include-released]"
)

_OPENCODE_SESSION_RECOVER_STALE_USAGE = (
    "Usage: doc-based-coding opencode session recover-stale "
    "--now TIMESTAMP [--ledger-path PATH] [--timestamp TIMESTAMP] "
    "[--expire-unhealthy] [--health-path PATH] [--health-timeout-seconds N] "
    "[--username-env-var NAME] [--password-env-var NAME] [--reason TEXT]"
)

_WORKER_BINDING_USAGE = (
    "Usage: doc-based-coding worker-binding "
    "<claim|promote-server-api-session|inspect-promotion-candidates|lane-ownership|reuse|fork|compact|release|inspect|recover-stale> [args]"
)

_WORKER_BINDING_CLAIM_USAGE = (
    "Usage: doc-based-coding worker-binding claim "
    "--worker-id ID --runtime-provider fake|qoder|codex|opencode "
    "--scope-kind lane|lane_group|agent|task --scope-id ID "
    "[--lane-id ID ...] [--ledger-path PATH] [--event-log-path PATH] "
    "[--binding-id ID] [--session-attach-url URL] [--session-id ID] "
    "[--continue-session] [--fork-session] "
    "[--compact-context-ref REF] [--mailbox-cursor-ref REF] "
    "[--worker-report-ref REF ...] [--audit-ref REF ...] "
    "[--timestamp TIMESTAMP] [--expires-at TIMESTAMP] [--reason TEXT] "
    "[--no-replace-existing]"
)

_WORKER_BINDING_PROMOTE_SERVER_API_SESSION_USAGE = (
    "Usage: doc-based-coding worker-binding promote-server-api-session "
    "--worker-id ID --scope-kind lane|lane_group|agent|task --scope-id ID "
    "--attach-url URL --session-id ID "
    "[--session-selector-source server_api_created] "
    "[--lane-id ID ...] [--ledger-path PATH] [--event-log-path PATH] "
    "[--claim-lane-ownership] [--lane-ownership-ledger-path PATH] "
    "[--lane-ownership-event-log-path PATH] "
    "[--binding-id ID] [--compact-context-ref REF] [--mailbox-cursor-ref REF] "
    "[--worker-report-ref REF ...] [--audit-ref REF ...] "
    "[--timestamp TIMESTAMP] [--expires-at TIMESTAMP] [--reason TEXT] "
    "[--no-replace-existing]"
)

_WORKER_BINDING_LANE_OWNERSHIP_USAGE = (
    "Usage: doc-based-coding worker-binding lane-ownership "
    "<inspect|activate> [args]"
)

_WORKER_BINDING_LANE_OWNERSHIP_INSPECT_USAGE = (
    "Usage: doc-based-coding worker-binding lane-ownership inspect "
    "[--ledger-path PATH] [--ownership-id ID] [--scope-kind lane|lane_group] "
    "[--scope-id ID] [--lane-id ID] [--binding-id ID] [--worker-id ID] "
    "[--include-inactive]"
)

_WORKER_BINDING_LANE_OWNERSHIP_ACTIVATE_USAGE = (
    "Usage: doc-based-coding worker-binding lane-ownership activate "
    "(--ownership-id ID | --binding-id ID) --delivery-id ID --task-id ID "
    "[--ledger-path PATH] [--event-log-path PATH] [--activated-at TIMESTAMP] "
    "[--audit-ref REF ...] [--reason TEXT]"
)

_WORKER_BINDING_INSPECT_PROMOTION_CANDIDATES_USAGE = (
    "Usage: doc-based-coding worker-binding inspect-promotion-candidates "
    "[--runtime-invocation-log-path PATH] [--latest-limit N] "
    "[--include-incomplete] [--command-prefix TEXT]"
)

_WORKER_BINDING_REUSE_USAGE = (
    "Usage: doc-based-coding worker-binding reuse "
    "--binding-id ID [--ledger-path PATH] [--event-log-path PATH] "
    "[--task-id ID] [--agent-id ID] [--lane-id ID] "
    "[--audit-ref REF ...] [--timestamp TIMESTAMP] [--reason TEXT]"
)

_WORKER_BINDING_FORK_USAGE = (
    "Usage: doc-based-coding worker-binding fork "
    "--source-binding-id ID --scope-kind lane|lane_group|agent|task --scope-id ID "
    "[--worker-id ID] [--new-binding-id ID] [--lane-id ID ...] "
    "[--ledger-path PATH] [--event-log-path PATH] "
    "[--session-attach-url URL] [--session-id ID] [--continue-session] [--fork-session] "
    "[--compact-context-ref REF] [--mailbox-cursor-ref REF] "
    "[--worker-report-ref REF ...] [--audit-ref REF ...] "
    "[--timestamp TIMESTAMP] [--expires-at TIMESTAMP] [--reason TEXT]"
)

_WORKER_BINDING_COMPACT_USAGE = (
    "Usage: doc-based-coding worker-binding compact "
    "(--compact-context-ref REF | --build-context-bundle --summary TEXT) "
    "(--binding-id ID | --scope-kind lane|lane_group|agent|task --scope-id ID) "
    "[--ledger-path PATH] [--event-log-path PATH] "
    "[--context-bundle-dir PATH] [--context-bundle-path PATH] [--bundle-id ID] "
    "[--key-decision TEXT ...] [--current-state TEXT] [--artifact-ref REF ...] "
    "[--mailbox-cursor-ref REF] [--worker-report-ref REF ...] "
    "[--audit-ref REF ...] [--timestamp TIMESTAMP] [--reason TEXT]"
)

_WORKER_BINDING_RELEASE_USAGE = (
    "Usage: doc-based-coding worker-binding release "
    "(--binding-id ID | --scope-kind lane|lane_group|agent|task --scope-id ID) "
    "[--ledger-path PATH] [--event-log-path PATH] "
    "[--status released|stale|archived] [--timestamp TIMESTAMP] [--reason TEXT]"
)

_WORKER_BINDING_INSPECT_USAGE = (
    "Usage: doc-based-coding worker-binding inspect "
    "[--ledger-path PATH] [--runtime-provider fake|qoder|codex|opencode] "
    "[--scope-kind lane|lane_group|agent|task] [--scope-id ID] "
    "[--worker-id ID] [--lane-id ID] [--include-inactive]"
)

_WORKER_BINDING_RECOVER_STALE_USAGE = (
    "Usage: doc-based-coding worker-binding recover-stale "
    "--now TIMESTAMP [--ledger-path PATH] [--event-log-path PATH] "
    "[--timestamp TIMESTAMP] [--reason TEXT]"
)

_OPENCODE_GUIDE_WORKER_SMOKE_USAGE = (
    "Usage: doc-based-coding opencode guide-worker-smoke "
    "[--executable PATH] [--cwd PATH] [--model NAME] "
    "[--output-format text|json] "
    "[--attach-url URL] [--session-id ID] [--continue-session] [--fork-session] "
    "[--artifact-store-path PATH] [--admission-ledger-path PATH] "
    "[--snapshot-path PATH] [--event-log-path PATH] "
    "[--evidence-id ID] [--evidence-path PATH] "
    "[--git-worktree-sandbox-root PATH] [--sandbox-allocation-evidence-id ID] "
    "[--sandbox-allocation-evidence-path PATH] "
    "[--host-invocation-id ID] [--reason TEXT] "
    "[--runtime-invocation-log-path PATH] [--runtime-invocation-max-attempts N] "
    "[--runtime-invocation-backoff-seconds N] "
    "[--guide-task-title TEXT] [--guide-task-summary TEXT] "
    "[--planner-lane LANE_ID=LABEL:FOCUS[:ARTIFACT,ARTIFACT[:SANDBOX_KIND]]] "
    "[--max-parallel-lanes N] [--max-waves N] "
    "[--wave-execution-mode serial|threaded] [--timestamp TIMESTAMP]"
)

_PROVIDER_GUIDE_WORKER_SMOKE_USAGE = (
    "Usage: doc-based-coding provider guide-worker-smoke "
    "[--providers codex,opencode] "
    "[--codex-executable PATH] [--codex-cwd PATH] [--codex-model NAME] "
    "[--codex-sandbox read-only|workspace-write|danger-full-access] "
    "[--codex-ask-for-approval untrusted|on-request|never] "
    "[--opencode-executable PATH] [--opencode-cwd PATH] [--opencode-model NAME] "
    "[--opencode-output-format text|json] "
    "[--opencode-attach-url URL] [--opencode-session-id ID] "
    "[--opencode-continue-session] [--opencode-fork-session] "
    "[--artifact-store-path PATH] [--admission-ledger-path PATH] "
    "[--snapshot-path PATH] [--event-log-path PATH] "
    "[--evidence-id ID] [--evidence-path PATH] "
    "[--git-worktree-sandbox-root PATH] [--sandbox-allocation-evidence-id ID] "
    "[--sandbox-allocation-evidence-path PATH] "
    "[--host-invocation-id ID] [--reason TEXT] "
    "[--runtime-invocation-log-path PATH] [--runtime-invocation-max-attempts N] "
    "[--runtime-invocation-backoff-seconds N] "
    "[--guide-task-title TEXT] [--guide-task-summary TEXT] "
    "[--planner-lane LANE_ID=LABEL:FOCUS[:ARTIFACT,ARTIFACT[:SANDBOX_KIND]]] "
    "[--planner-lane-provider LANE_ID=codex|opencode|qoder|fake] "
    "[--max-parallel-lanes N] [--max-waves N] "
    "[--wave-execution-mode serial|threaded] [--timestamp TIMESTAMP]"
)


def cmd_codex(args: list[str]) -> int:
    """Codex CLI host-runtime helper subcommands."""
    if not args or args[0] in ("-h", "--help"):
        print(
            "Usage: doc-based-coding codex <subcommand> [args]\n\n"
            "Codex CLI host readiness helpers.\n\n"
            "Subcommands:\n"
            "  readiness [--executable PATH]\n"
            "      Check Codex CLI host readiness without running a task\n"
            "  guide-worker-smoke [--executable PATH] [--cwd PATH] [--model NAME]\n"
            "      Run host-owned Codex CLI guide-worker lane-wave execution\n",
        )
        return 0

    sub = args[0]
    if sub == "readiness":
        return cmd_codex_readiness(args[1:])
    if sub == "guide-worker-smoke":
        return cmd_codex_guide_worker_smoke(args[1:])

    print(f"Unknown codex subcommand: {sub}", file=sys.stderr)
    print("Usage: doc-based-coding codex <readiness|guide-worker-smoke> [args]", file=sys.stderr)
    return 1


def cmd_codex_readiness(args: list[str]) -> int:
    """Check Codex CLI host readiness without executing a task."""

    if args and args[0] in ("-h", "--help"):
        print(
            _CODEX_READINESS_USAGE + "\n\n"
            "This command checks whether Codex CLI is available to the host "
            "runtime and whether Codex can see a doc-based-coding MCP server "
            "for the project. It prints only credential-safe executable and "
            "configuration exposure information; it does not run providers, "
            "start MCP servers, call MCP tools, write scheduler state, write "
            "evidence, or mutate Local Work Trajectory.",
        )
        return 0

    executable = "codex"
    project_root = ""
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--executable":
            if i + 1 >= len(args):
                print(_CODEX_READINESS_USAGE, file=sys.stderr)
                return 1
            executable = args[i + 1]
            i += 2
            continue
        if arg == "--project-root":
            if i + 1 >= len(args):
                print(_CODEX_READINESS_USAGE, file=sys.stderr)
                return 1
            project_root = args[i + 1]
            i += 2
            continue
        print(f"Unknown codex readiness option: {arg}", file=sys.stderr)
        print(_CODEX_READINESS_USAGE, file=sys.stderr)
        return 1

    try:
        from .runtime.orchestration import (
            CodexCliClientConfig,
            CodexCliProcessClient,
            run_self_check_doctor,
        )

        report = CodexCliProcessClient(
            CodexCliClientConfig(executable=executable)
        ).host_readiness_report()
        doctor_report = run_self_check_doctor(
            Path(project_root) if project_root else _find_project_root(),
            profile="codex",
            metadata={"codex_executable": executable},
        )
    except Exception as e:
        return _handle_error("Error checking Codex CLI readiness", e, category="codex_readiness_failed")

    payload = report.to_json_dict()
    payload["mcp_exposure"] = _doctor_codex_mcp_exposure_compat(doctor_report)
    _print_json(payload)
    return 0


def _doctor_codex_mcp_exposure_compat(doctor_report) -> dict[str, object]:
    for check in doctor_report.checks:
        if check.check_id == "codex.mcp_exposure":
            evidence = dict(check.evidence)
            authority = check.authority_split.to_json_dict()
            return {
                "diagnostic_status": check.status,
                "project_config_exists": evidence.get("project_config_exists"),
                "user_config_exists": evidence.get("user_config_exists"),
                "project_trusted": evidence.get("project_trusted"),
                "mcp_list_ran": evidence.get("mcp_list_ran"),
                "mcp_list_returncode": evidence.get("mcp_list_returncode"),
                "mcp_list_summary": evidence.get("mcp_list_summary"),
                "mcp_servers_zero_hint": evidence.get("mcp_servers_zero_hint"),
                "doc_based_coding_server_visible": evidence.get("doc_based_coding_server_visible"),
                "doc_based_coding_server_enabled": evidence.get("doc_based_coding_server_enabled"),
                "suspected_problem": check.suspected_problem,
                "remediation": list(check.remediation),
                "command_preview": evidence.get("command_preview", []),
                "doctor_check_id": check.check_id,
                "authority_split": {
                    "provider_executed": authority["provider_executed"],
                    "mcp_server_started": authority["mcp_server_started"],
                    "mcp_tool_called": authority["mcp_tool_called"],
                    "codex_config_mutated": authority["config_mutated"],
                    "secret_material_read": authority["secret_material_read"],
                },
            }
    return {
        "diagnostic_status": "skipped",
        "suspected_problem": "codex_mcp_exposure_check_missing",
        "remediation": ["Run `doc-based-coding doctor --profile codex` for the unified report."],
        "doctor_check_id": "",
        "authority_split": {
            "provider_executed": False,
            "mcp_server_started": False,
            "mcp_tool_called": False,
            "codex_config_mutated": False,
            "secret_material_read": False,
        },
    }


def cmd_doctor(args: list[str]) -> int:
    """Run unified self-check diagnostics."""

    if args and args[0] in ("-h", "--help"):
        print(
            _DOCTOR_USAGE + "\n\n"
            "Runs credential-safe, read-only self-check diagnostics. The default "
            "profile is all. Doctor does not run provider tasks, call MCP tools, "
            "start MCP servers, mutate config, or print secret values.",
        )
        return 0

    profile = "all"
    project_root = ""
    timeout_seconds = 10
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--profile":
            if i + 1 >= len(args):
                print(_DOCTOR_USAGE, file=sys.stderr)
                return 1
            profile = args[i + 1]
            i += 2
            continue
        if arg == "--project-root":
            if i + 1 >= len(args):
                print(_DOCTOR_USAGE, file=sys.stderr)
                return 1
            project_root = args[i + 1]
            i += 2
            continue
        if arg == "--timeout-seconds":
            if i + 1 >= len(args):
                print(_DOCTOR_USAGE, file=sys.stderr)
                return 1
            try:
                timeout_seconds = int(args[i + 1])
            except ValueError:
                print(_DOCTOR_USAGE, file=sys.stderr)
                print("--timeout-seconds must be an integer", file=sys.stderr)
                return 1
            i += 2
            continue
        print(f"Unknown doctor option: {arg}", file=sys.stderr)
        print(_DOCTOR_USAGE, file=sys.stderr)
        return 1

    try:
        from .runtime.orchestration import doctor_exit_code, run_self_check_doctor

        report = run_self_check_doctor(
            Path(project_root) if project_root else _find_project_root(),
            profile=profile,
            timeout_seconds=timeout_seconds,
        )
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    except Exception as e:
        return _handle_error("Error running doctor self-checks", e, category="doctor_failed")

    _print_json(report.to_json_dict())
    return doctor_exit_code(report)


def cmd_readback(args: list[str]) -> int:
    """Unified read-only readback inspection helpers."""

    if not args or args[0] in ("-h", "--help"):
        print(
            "Usage: doc-based-coding readback <subcommand> [args]\n\n"
            "Subcommands:\n"
            "  inspect    Project known log/evidence records into readback envelopes\n",
        )
        return 0

    sub = args[0]
    if sub == "inspect":
        return cmd_readback_inspect(args[1:])

    print(f"Unknown readback subcommand: {sub}", file=sys.stderr)
    print("Usage: doc-based-coding readback <inspect> [args]", file=sys.stderr)
    return 1


def cmd_readback_inspect(args: list[str]) -> int:
    """Inspect one readback family without mutation."""

    if args and args[0] in ("-h", "--help"):
        print(
            _READBACK_INSPECT_USAGE + "\n\n"
            "This command reads existing records and returns draft readback "
            "envelopes. It does not consume worker trajectory reports, run "
            "validation or doctor, execute providers, launch browsers, capture "
            "screenshots, mutate scheduler/exchange/evidence/config state, or "
            "mutate Local Work Trajectory.",
        )
        return 0

    kind = ""
    path = ""
    artifact_id = ""
    version = ""
    source_kind = ""
    latest_limit = 20
    actor = "readback-inspection-cli"
    timestamp = ""
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {
            "--kind",
            "--path",
            "--artifact-id",
            "--version",
            "--source-kind",
            "--latest-limit",
            "--actor",
            "--timestamp",
        }:
            if i + 1 >= len(args):
                print(_READBACK_INSPECT_USAGE, file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--kind":
                kind = value
            elif arg == "--path":
                path = value
            elif arg == "--artifact-id":
                artifact_id = value
            elif arg == "--version":
                version = value
            elif arg == "--source-kind":
                source_kind = value
            elif arg == "--latest-limit":
                try:
                    latest_limit = int(value)
                except ValueError:
                    print("--latest-limit must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--actor":
                actor = value
            elif arg == "--timestamp":
                timestamp = value
            i += 2
            continue
        print(f"Unknown readback inspect option: {arg}", file=sys.stderr)
        print(_READBACK_INSPECT_USAGE, file=sys.stderr)
        return 1

    if not kind:
        print(_READBACK_INSPECT_USAGE, file=sys.stderr)
        return 1

    try:
        from .runtime.orchestration import ReadbackInspectionRequest, inspect_readback

        result = inspect_readback(
            ReadbackInspectionRequest(
                project_root=_find_project_root(),
                kind=kind,
                path=path,
                artifact_id=artifact_id,
                version=version,
                source_kind=source_kind,
                latest_limit=latest_limit,
                actor=actor,
                timestamp=timestamp,
            )
        )
    except Exception as e:
        return _handle_error(
            "Error inspecting readback",
            e,
            category="readback_inspection_failed",
        )

    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def cmd_codex_guide_worker_smoke(args: list[str]) -> int:
    """Run host-owned Codex CLI guide-worker provider execution through CLI."""

    if args and args[0] in ("-h", "--help"):
        print(
            _CODEX_GUIDE_WORKER_SMOKE_USAGE + "\n\n"
            "This command is a host-owned live-provider guide-worker smoke "
            "surface for Codex CLI. It delegates to "
            "run_host_owned_guide_worker_provider_execution(), uses explicit "
            "host-authorized adapter wiring and a Codex process-spawn grant. "
            "It is not an MCP real-provider execution surface, does not persist "
            "raw transcripts, and does not mutate agent-owned Local Work "
            "Trajectory. Runtime invocations are audited to compact JSONL by "
            "default and retry retryable provider failures. Git-worktree "
            "worker changes are exported as review-only worker patch artifacts "
            "and merge candidates; they are not applied automatically.",
        )
        return 0

    executable = "codex"
    cwd = ""
    model = ""
    sandbox = "workspace-write"
    ask_for_approval = "never"
    artifact_store_path = ""
    admission_ledger_path = ""
    snapshot_path = ""
    event_log_path = ""
    evidence_id = ""
    evidence_path = ""
    git_worktree_sandbox_root = ""
    sandbox_allocation_evidence_id = ""
    sandbox_allocation_evidence_path = ""
    host_invocation_id = ""
    reason = ""
    runtime_invocation_log_path = ".dbc/runtime/invocations.jsonl"
    runtime_invocation_max_attempts = 2
    runtime_invocation_backoff_seconds = 0.0
    guide_task_title = ""
    guide_task_summary = ""
    planner_lane_specs: list[str] = []
    max_parallel_lanes = 2
    max_waves = 1
    wave_execution_mode = "threaded"
    timestamp = ""

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {
            "--executable",
            "--cwd",
            "--model",
            "--sandbox",
            "--ask-for-approval",
            "--artifact-store-path",
            "--admission-ledger-path",
            "--snapshot-path",
            "--event-log-path",
            "--evidence-id",
            "--evidence-path",
            "--git-worktree-sandbox-root",
            "--sandbox-allocation-evidence-id",
            "--sandbox-allocation-evidence-path",
            "--host-invocation-id",
            "--reason",
            "--runtime-invocation-log-path",
            "--runtime-invocation-max-attempts",
            "--runtime-invocation-backoff-seconds",
            "--guide-task-title",
            "--guide-task-summary",
            "--planner-lane",
            "--max-parallel-lanes",
            "--max-waves",
            "--wave-execution-mode",
            "--timestamp",
        }:
            if i + 1 >= len(args):
                print(_CODEX_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--executable":
                executable = value
            elif arg == "--cwd":
                cwd = value
            elif arg == "--model":
                model = value
            elif arg == "--sandbox":
                sandbox = value
            elif arg == "--ask-for-approval":
                ask_for_approval = value
            elif arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--admission-ledger-path":
                admission_ledger_path = value
            elif arg == "--snapshot-path":
                snapshot_path = value
            elif arg == "--event-log-path":
                event_log_path = value
            elif arg == "--evidence-id":
                evidence_id = value
            elif arg == "--evidence-path":
                evidence_path = value
            elif arg == "--git-worktree-sandbox-root":
                git_worktree_sandbox_root = value
            elif arg == "--sandbox-allocation-evidence-id":
                sandbox_allocation_evidence_id = value
            elif arg == "--sandbox-allocation-evidence-path":
                sandbox_allocation_evidence_path = value
            elif arg == "--host-invocation-id":
                host_invocation_id = value
            elif arg == "--reason":
                reason = value
            elif arg == "--runtime-invocation-log-path":
                runtime_invocation_log_path = value
            elif arg == "--runtime-invocation-max-attempts":
                try:
                    runtime_invocation_max_attempts = int(value)
                except ValueError:
                    print(_CODEX_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
                    print("--runtime-invocation-max-attempts must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--runtime-invocation-backoff-seconds":
                try:
                    runtime_invocation_backoff_seconds = float(value)
                except ValueError:
                    print(_CODEX_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
                    print("--runtime-invocation-backoff-seconds must be a number", file=sys.stderr)
                    return 1
            elif arg == "--guide-task-title":
                guide_task_title = value
            elif arg == "--guide-task-summary":
                guide_task_summary = value
            elif arg == "--planner-lane":
                planner_lane_specs.append(value)
            elif arg == "--max-parallel-lanes":
                try:
                    max_parallel_lanes = int(value)
                except ValueError:
                    print(_CODEX_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
                    print("--max-parallel-lanes must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--max-waves":
                try:
                    max_waves = int(value)
                except ValueError:
                    print(_CODEX_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
                    print("--max-waves must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--wave-execution-mode":
                wave_execution_mode = value
            elif arg == "--timestamp":
                timestamp = value
            i += 2
            continue
        print(f"Unknown codex guide-worker-smoke option: {arg}", file=sys.stderr)
        print(_CODEX_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
        return 1

    if sandbox not in {"read-only", "workspace-write", "danger-full-access"}:
        print(
            "codex guide-worker-smoke --sandbox must be read-only, workspace-write, or danger-full-access",
            file=sys.stderr,
        )
        return 1
    if ask_for_approval not in {"untrusted", "on-request", "never"}:
        print(
            "codex guide-worker-smoke --ask-for-approval must be untrusted, on-request, or never",
            file=sys.stderr,
        )
        return 1
    if max_parallel_lanes < 1:
        print("codex guide-worker-smoke --max-parallel-lanes must be positive", file=sys.stderr)
        return 1
    if max_waves < 1:
        print("codex guide-worker-smoke --max-waves must be positive", file=sys.stderr)
        return 1
    if runtime_invocation_max_attempts < 1:
        print("codex guide-worker-smoke --runtime-invocation-max-attempts must be positive", file=sys.stderr)
        return 1
    if runtime_invocation_backoff_seconds < 0:
        print(
            "codex guide-worker-smoke --runtime-invocation-backoff-seconds must be non-negative",
            file=sys.stderr,
        )
        return 1
    if wave_execution_mode not in {"serial", "threaded"}:
        print(
            "codex guide-worker-smoke --wave-execution-mode must be serial or threaded",
            file=sys.stderr,
        )
        return 1

    root = _find_project_root()
    try:
        from .runtime.orchestration import (
            CodexCliClientConfig,
            GuideWorkerPlannerLaneSpec,
            GuideWorkerPlanningRequest,
        )
        from tools.progress_graph import (
            HostOwnedGuideWorkerProviderExecutionConfig,
            run_host_owned_guide_worker_provider_execution,
        )

        codex_config = CodexCliClientConfig(
            executable=executable,
            cwd=cwd,
            model=model,
            sandbox=sandbox,  # type: ignore[arg-type]
            ask_for_approval=ask_for_approval,  # type: ignore[arg-type]
        )
        planning_request = GuideWorkerPlanningRequest(
            task_title=guide_task_title,
            task_summary=guide_task_summary,
            lane_specs=tuple(
                _parse_guide_worker_planner_lane_spec(
                    item,
                    GuideWorkerPlannerLaneSpec,
                )
                for item in planner_lane_specs
            ),
        )
        config_kwargs = {
            "evidence_id": evidence_id or "codex-guide-worker-provider-execution",
            "timestamp": timestamp,
            "artifact_store_path": artifact_store_path or ".dbc/orchestration/exchange-artifacts.json",
            "admission_ledger_path": (
                admission_ledger_path
                or ".dbc/orchestration/exchange-artifact-admissions.json"
            ),
            "snapshot_path": (
                snapshot_path
                or ".dbc/scheduler/codex-guide-worker-provider-execution-state.json"
            ),
            "event_log_path": (
                event_log_path
                or ".dbc/scheduler/codex-guide-worker-provider-execution-events.jsonl"
            ),
            "evidence_output_path": evidence_path or None,
            "workspace_root": str(root),
            "git_worktree_sandbox_root": git_worktree_sandbox_root or None,
            "sandbox_allocation_evidence_id": sandbox_allocation_evidence_id,
            "sandbox_allocation_evidence_path": sandbox_allocation_evidence_path or None,
            "providers": ("codex",),
            "codex_cli_client_config": codex_config,
            "host_invocation_id": (
                host_invocation_id
                or "host-owned-codex-guide-worker-provider-execution-cli"
            ),
            "requested_by": "cli:codex-guide-worker-smoke",
            "reason": reason or "host-owned Codex CLI guide-worker smoke run from CLI",
            "runtime_invocation_log_path": runtime_invocation_log_path or None,
            "runtime_invocation_max_attempts": runtime_invocation_max_attempts,
            "runtime_invocation_backoff_seconds": runtime_invocation_backoff_seconds,
            "grant_id": (
                f"grant-{host_invocation_id}"
                if host_invocation_id
                else "grant-host-owned-codex-guide-worker-provider-execution-cli"
            ),
            "approved_by": "cli:codex-guide-worker-smoke",
            "approved_at": timestamp,
            "planning_request": planning_request,
            "planner_worker_runtime_provider": "codex",
            "max_parallel_lanes": max_parallel_lanes,
            "max_waves": max_waves,
            "wave_execution_mode": wave_execution_mode,
        }
        if planner_lane_specs:
            config_kwargs["worker_instructions"] = ()
        config = HostOwnedGuideWorkerProviderExecutionConfig(**config_kwargs)
        result = run_host_owned_guide_worker_provider_execution(root, config=config)
    except Exception as e:
        return _handle_error(
            "Error running Codex guide-worker smoke",
            e,
            category="codex_guide_worker_smoke_failed",
        )

    _print_json(result.to_json_dict())
    return 0 if result.orchestration.ok else 1


def cmd_opencode(args: list[str]) -> int:
    """OpenCode CLI host-runtime helper subcommands."""
    if not args or args[0] in ("-h", "--help"):
        print(
            "Usage: doc-based-coding opencode <subcommand> [args]\n\n"
            "OpenCode CLI host readiness helpers.\n\n"
            "Subcommands:\n"
            "  readiness [--executable PATH]\n"
            "      Check OpenCode CLI host readiness without running a task\n"
            "  serve-readiness [--executable PATH] [--attach-url URL]\n"
            "      Check host-owned OpenCode serve attach target readiness\n"
            "  server-api-readiness [--base-url URL] [--check-doc]\n"
            "      Check host-owned OpenCode direct server/API readiness\n"
            "  serve-lifecycle <record|inspect>\n"
            "      Record or inspect host-owned OpenCode serve lifecycle receipts\n"
            "  session <claim|release|inspect>\n"
            "      Maintain host-owned OpenCode session binding receipts\n"
            "  guide-worker-smoke [--executable PATH] [--cwd PATH] [--model NAME]\n"
            "      Run host-owned OpenCode CLI guide-worker lane-wave execution\n",
        )
        return 0

    sub = args[0]
    if sub == "readiness":
        return cmd_opencode_readiness(args[1:])
    if sub == "serve-readiness":
        return cmd_opencode_serve_readiness(args[1:])
    if sub == "server-api-readiness":
        return cmd_opencode_server_api_readiness(args[1:])
    if sub == "serve-lifecycle":
        return cmd_opencode_serve_lifecycle(args[1:])
    if sub == "session":
        return cmd_opencode_session(args[1:])
    if sub == "guide-worker-smoke":
        return cmd_opencode_guide_worker_smoke(args[1:])

    print(f"Unknown opencode subcommand: {sub}", file=sys.stderr)
    print(
        "Usage: doc-based-coding opencode <readiness|serve-readiness|server-api-readiness|serve-lifecycle|session|guide-worker-smoke> [args]",
        file=sys.stderr,
    )
    return 1


def cmd_opencode_readiness(args: list[str]) -> int:
    """Check OpenCode CLI host readiness without executing a task."""

    if args and args[0] in ("-h", "--help"):
        print(
            _OPENCODE_READINESS_USAGE + "\n\n"
            "This command checks whether OpenCode CLI is available to the host "
            "runtime. It prints only credential-safe executable information; "
            "it does not run providers, write scheduler state, write evidence, "
            "or mutate Local Work Trajectory.",
        )
        return 0

    executable = "opencode"
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--executable":
            if i + 1 >= len(args):
                print(_OPENCODE_READINESS_USAGE, file=sys.stderr)
                return 1
            executable = args[i + 1]
            i += 2
            continue
        print(f"Unknown opencode readiness option: {arg}", file=sys.stderr)
        print(_OPENCODE_READINESS_USAGE, file=sys.stderr)
        return 1

    try:
        from .runtime.orchestration import OpenCodeCliClientConfig, OpenCodeCliProcessClient

        report = OpenCodeCliProcessClient(
            OpenCodeCliClientConfig(executable=executable)
        ).host_readiness_report()
    except Exception as e:
        return _handle_error(
            "Error checking OpenCode CLI readiness",
            e,
            category="opencode_readiness_failed",
        )

    _print_json(report.to_json_dict())
    return 0


def cmd_opencode_serve_readiness(args: list[str]) -> int:
    """Inspect host-owned OpenCode serve attach target readiness."""

    if args and args[0] in ("-h", "--help"):
        print(
            _OPENCODE_SERVE_READINESS_USAGE + "\n\n"
            "This command inspects a host-owned OpenCode serve target for use "
            "with opencode run --attach. It checks the OpenCode CLI executable "
            "and probes the serve health endpoint, but it does not start, stop, "
            "restart, or supervise opencode serve. Basic-auth credentials are "
            "read only from named environment variables when configured and "
            "secret values are never printed. It does not run providers, write "
            "scheduler state, write runtime invocation logs, or mutate Local "
            "Work Trajectory.",
        )
        return 0

    parsed: dict[str, object] = {
        "executable": "opencode",
        "hostname": "127.0.0.1",
        "port": 4096,
        "attach_url": "",
        "health_path": "/global/health",
        "health_timeout_seconds": 2.0,
        "require_healthy": False,
        "username_env_var": "OPENCODE_SERVER_USERNAME",
        "password_env_var": "OPENCODE_SERVER_PASSWORD",
    }
    cli_to_key = {
        "--executable": "executable",
        "--hostname": "hostname",
        "--port": "port",
        "--attach-url": "attach_url",
        "--health-path": "health_path",
        "--health-timeout-seconds": "health_timeout_seconds",
        "--username-env-var": "username_env_var",
        "--password-env-var": "password_env_var",
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--require-healthy":
            parsed["require_healthy"] = True
            i += 1
            continue
        if arg not in cli_to_key:
            print(f"Unknown opencode serve-readiness option: {arg}", file=sys.stderr)
            print(_OPENCODE_SERVE_READINESS_USAGE, file=sys.stderr)
            return 1
        if i + 1 >= len(args):
            print(_OPENCODE_SERVE_READINESS_USAGE, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return 1
        key = cli_to_key[arg]
        value = args[i + 1]
        if key == "port":
            try:
                parsed[key] = int(value)
            except ValueError:
                print(_OPENCODE_SERVE_READINESS_USAGE, file=sys.stderr)
                print("--port must be an integer", file=sys.stderr)
                return 1
        elif key == "health_timeout_seconds":
            try:
                parsed[key] = float(value)
            except ValueError:
                print(_OPENCODE_SERVE_READINESS_USAGE, file=sys.stderr)
                print("--health-timeout-seconds must be a number", file=sys.stderr)
                return 1
        else:
            parsed[key] = value
        i += 2

    try:
        from .runtime.orchestration import (
            OpenCodeServeReadinessRequest,
            inspect_opencode_serve_readiness,
        )

        report = inspect_opencode_serve_readiness(
            OpenCodeServeReadinessRequest(
                executable=str(parsed["executable"]),
                hostname=str(parsed["hostname"]),
                port=int(parsed["port"]),
                attach_url=str(parsed["attach_url"]),
                health_path=str(parsed["health_path"]),
                health_timeout_seconds=float(parsed["health_timeout_seconds"]),
                require_healthy=bool(parsed["require_healthy"]),
                username_env_var=str(parsed["username_env_var"]),
                password_env_var=str(parsed["password_env_var"]),
            )
        )
    except Exception as e:
        return _handle_error(
            "Error checking OpenCode serve readiness",
            e,
            category="opencode_serve_readiness_failed",
        )

    _print_json(report.to_json_dict())
    return 0 if report.ready else 1


def cmd_opencode_server_api_readiness(args: list[str]) -> int:
    """Inspect host-owned OpenCode direct server/API readiness."""

    if args and args[0] in ("-h", "--help"):
        print(
            _OPENCODE_SERVER_API_READINESS_USAGE + "\n\n"
            "This command inspects a host-owned running OpenCode server/API "
            "target for direct HTTP adapter use. It probes health and, when "
            "--check-doc is set, the OpenAPI document endpoint. It does not "
            "start, stop, restart, or supervise opencode serve, does not run "
            "provider tasks, and does not write scheduler state, delivery "
            "state, runtime invocation logs, or Local Work Trajectory. Basic "
            "auth credentials are read only from named environment variables "
            "when configured and secret values are never printed.",
        )
        return 0

    parsed: dict[str, object] = {
        "base_url": "http://127.0.0.1:4096",
        "health_path": "/global/health",
        "doc_path": "/doc",
        "check_doc": False,
        "timeout_seconds": 2.0,
        "username_env_var": "OPENCODE_SERVER_USERNAME",
        "password_env_var": "OPENCODE_SERVER_PASSWORD",
    }
    cli_to_key = {
        "--base-url": "base_url",
        "--health-path": "health_path",
        "--doc-path": "doc_path",
        "--timeout-seconds": "timeout_seconds",
        "--username-env-var": "username_env_var",
        "--password-env-var": "password_env_var",
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--check-doc":
            parsed["check_doc"] = True
            i += 1
            continue
        if arg not in cli_to_key:
            print(f"Unknown opencode server-api-readiness option: {arg}", file=sys.stderr)
            print(_OPENCODE_SERVER_API_READINESS_USAGE, file=sys.stderr)
            return 1
        if i + 1 >= len(args):
            print(_OPENCODE_SERVER_API_READINESS_USAGE, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return 1
        key = cli_to_key[arg]
        value = args[i + 1]
        if key == "timeout_seconds":
            try:
                parsed[key] = float(value)
            except ValueError:
                print(_OPENCODE_SERVER_API_READINESS_USAGE, file=sys.stderr)
                print("--timeout-seconds must be a number", file=sys.stderr)
                return 1
        else:
            parsed[key] = value
        i += 2

    try:
        from .runtime.orchestration import (
            OpenCodeServerApiClientConfig,
            inspect_opencode_server_api_readiness,
        )

        report = inspect_opencode_server_api_readiness(
            OpenCodeServerApiClientConfig(
                base_url=str(parsed["base_url"]),
                health_path=str(parsed["health_path"]),
                doc_path=str(parsed["doc_path"]),
                timeout_seconds=float(parsed["timeout_seconds"]),
                username_env_var=str(parsed["username_env_var"]),
                password_env_var=str(parsed["password_env_var"]),
            ),
            check_doc=bool(parsed["check_doc"]),
        )
    except Exception as e:
        return _handle_error(
            "Error checking OpenCode server/API readiness",
            e,
            category="opencode_server_api_readiness_failed",
        )

    _print_json(report.to_json_dict())
    return 0 if report.ready else 1


def cmd_opencode_serve_lifecycle(args: list[str]) -> int:
    """Maintain host-owned OpenCode serve lifecycle receipts."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _OPENCODE_SERVE_LIFECYCLE_USAGE + "\n\n"
            "This command records or inspects durable host-owned OpenCode "
            "serve lifecycle receipts. It is an audit surface for external "
            "start/stop/restart/status decisions; it does not start, stop, "
            "restart, supervise, or health-monitor opencode serve, does not "
            "run providers, write scheduler or delivery state, write runtime "
            "invocation logs, or mutate Local Work Trajectory.\n\n"
            "Subcommands:\n"
            "  record   Append one lifecycle receipt\n"
            "  inspect  Read lifecycle receipts without mutation\n",
        )
        return 0

    sub = args[0]
    if sub == "record":
        return cmd_opencode_serve_lifecycle_record(args[1:])
    if sub == "inspect":
        return cmd_opencode_serve_lifecycle_inspect(args[1:])
    print(f"Unknown opencode serve-lifecycle subcommand: {sub}", file=sys.stderr)
    print(_OPENCODE_SERVE_LIFECYCLE_USAGE, file=sys.stderr)
    return 1


def cmd_opencode_serve_lifecycle_record(args: list[str]) -> int:
    if args and args[0] in ("-h", "--help"):
        print(
            _OPENCODE_SERVE_LIFECYCLE_RECORD_USAGE + "\n\n"
            "Record appends one host-owned OpenCode serve lifecycle receipt. "
            "Use it after an external host script or operator starts/stops a "
            "serve process, or before a planned action that should be audited. "
            "The command writes only the lifecycle ledger receipt. It does not "
            "spawn or terminate opencode serve and never stores secret values.",
        )
        return 0

    parsed: dict[str, object] = {
        "ledger_path": ".dbc/runtime/opencode-serve-lifecycle-ledger.json",
        "action": "",
        "status": "observed",
        "executable": "opencode",
        "hostname": "127.0.0.1",
        "port": 4096,
        "attach_url": "",
        "receipt_id": "",
        "timestamp": "",
        "pid": "",
        "process_ref": "",
        "actor": "",
        "reason": "",
        "note": "",
        "include_command_preview": True,
    }
    cli_to_key = {
        "--ledger-path": "ledger_path",
        "--action": "action",
        "--status": "status",
        "--executable": "executable",
        "--hostname": "hostname",
        "--port": "port",
        "--attach-url": "attach_url",
        "--receipt-id": "receipt_id",
        "--timestamp": "timestamp",
        "--pid": "pid",
        "--process-ref": "process_ref",
        "--actor": "actor",
        "--reason": "reason",
        "--note": "note",
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--no-command-preview":
            parsed["include_command_preview"] = False
            i += 1
            continue
        if arg not in cli_to_key:
            print(f"Unknown opencode serve-lifecycle record option: {arg}", file=sys.stderr)
            print(_OPENCODE_SERVE_LIFECYCLE_RECORD_USAGE, file=sys.stderr)
            return 1
        if i + 1 >= len(args):
            print(_OPENCODE_SERVE_LIFECYCLE_RECORD_USAGE, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return 1
        key = cli_to_key[arg]
        value = args[i + 1]
        if key == "port":
            try:
                parsed[key] = int(value)
            except ValueError:
                print(_OPENCODE_SERVE_LIFECYCLE_RECORD_USAGE, file=sys.stderr)
                print("--port must be an integer", file=sys.stderr)
                return 1
        else:
            parsed[key] = value
        i += 2
    if not parsed["action"]:
        print(_OPENCODE_SERVE_LIFECYCLE_RECORD_USAGE, file=sys.stderr)
        print("serve-lifecycle record requires --action", file=sys.stderr)
        return 1

    try:
        from .runtime.orchestration import (
            OpenCodeServeLifecycleRecordRequest,
            record_opencode_serve_lifecycle_receipt,
        )

        root = _find_project_root()
        result = record_opencode_serve_lifecycle_receipt(
            OpenCodeServeLifecycleRecordRequest(
                ledger_path=_resolve_project_path(root, str(parsed["ledger_path"])),
                action=str(parsed["action"]),  # type: ignore[arg-type]
                status=str(parsed["status"]),  # type: ignore[arg-type]
                executable=str(parsed["executable"]),
                hostname=str(parsed["hostname"]),
                port=int(parsed["port"]),
                attach_url=str(parsed["attach_url"]),
                receipt_id=str(parsed["receipt_id"]),
                timestamp=str(parsed["timestamp"]),
                pid=str(parsed["pid"]),
                process_ref=str(parsed["process_ref"]),
                actor=str(parsed["actor"]),
                reason=str(parsed["reason"]),
                note=str(parsed["note"]),
                include_command_preview=bool(parsed["include_command_preview"]),
            )
        )
    except Exception as e:
        return _handle_error(
            "Error recording OpenCode serve lifecycle receipt",
            e,
            category="opencode_serve_lifecycle_record_failed",
        )
    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def cmd_opencode_serve_lifecycle_inspect(args: list[str]) -> int:
    if args and args[0] in ("-h", "--help"):
        print(
            _OPENCODE_SERVE_LIFECYCLE_INSPECT_USAGE + "\n\n"
            "Inspect reads the OpenCode serve lifecycle ledger without "
            "mutation. It does not probe health, run providers, or manage "
            "opencode serve.",
        )
        return 0

    parsed: dict[str, object] = {
        "ledger_path": ".dbc/runtime/opencode-serve-lifecycle-ledger.json",
        "action": "",
        "status": "",
        "latest_limit": 0,
    }
    cli_to_key = {
        "--ledger-path": "ledger_path",
        "--action": "action",
        "--status": "status",
        "--latest-limit": "latest_limit",
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg not in cli_to_key:
            print(f"Unknown opencode serve-lifecycle inspect option: {arg}", file=sys.stderr)
            print(_OPENCODE_SERVE_LIFECYCLE_INSPECT_USAGE, file=sys.stderr)
            return 1
        if i + 1 >= len(args):
            print(_OPENCODE_SERVE_LIFECYCLE_INSPECT_USAGE, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return 1
        key = cli_to_key[arg]
        value = args[i + 1]
        if key == "latest_limit":
            try:
                parsed[key] = int(value)
            except ValueError:
                print(_OPENCODE_SERVE_LIFECYCLE_INSPECT_USAGE, file=sys.stderr)
                print("--latest-limit must be an integer", file=sys.stderr)
                return 1
        else:
            parsed[key] = value
        i += 2

    try:
        from .runtime.orchestration import (
            OpenCodeServeLifecycleInspectRequest,
            inspect_opencode_serve_lifecycle_receipts,
        )

        root = _find_project_root()
        result = inspect_opencode_serve_lifecycle_receipts(
            OpenCodeServeLifecycleInspectRequest(
                ledger_path=_resolve_project_path(root, str(parsed["ledger_path"])),
                action=str(parsed["action"]),
                status=str(parsed["status"]),
                latest_limit=int(parsed["latest_limit"]),
            )
        )
    except Exception as e:
        return _handle_error(
            "Error inspecting OpenCode serve lifecycle receipts",
            e,
            category="opencode_serve_lifecycle_inspect_failed",
        )
    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def cmd_opencode_session(args: list[str]) -> int:
    """Maintain host-owned OpenCode session binding receipts."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _OPENCODE_SESSION_USAGE + "\n\n"
            "This command maintains durable OpenCode session binding receipts "
            "for later opencode run --attach --session use. It does not create "
            "OpenCode sessions, run providers, store transcripts, write "
            "scheduler state, or mutate Local Work Trajectory.\n\n"
            "Subcommands:\n"
            "  claim    Create or replace one active binding\n"
            "  release  Mark one active binding released or expired\n"
            "  inspect  Read bindings without mutation\n"
            "  recover-stale  Expire stale bindings by explicit policy\n",
        )
        return 0

    sub = args[0]
    if sub == "claim":
        return cmd_opencode_session_claim(args[1:])
    if sub == "release":
        return cmd_opencode_session_release(args[1:])
    if sub == "inspect":
        return cmd_opencode_session_inspect(args[1:])
    if sub == "recover-stale":
        return cmd_opencode_session_recover_stale(args[1:])
    print(f"Unknown opencode session subcommand: {sub}", file=sys.stderr)
    print(_OPENCODE_SESSION_USAGE, file=sys.stderr)
    return 1


def cmd_opencode_session_claim(args: list[str]) -> int:
    if args and args[0] in ("-h", "--help"):
        print(
            _OPENCODE_SESSION_CLAIM_USAGE + "\n\n"
            "Claiming records a reusable OpenCode session selector for a scope. "
            "Recommended default scope is lane when a worker should continue "
            "across same-lane tasks. The command writes only the session ledger "
            "receipt and does not run OpenCode.",
        )
        return 0

    parsed: dict[str, object] = {
        "ledger_path": ".dbc/runtime/opencode-session-ledger.json",
        "scope_kind": "",
        "scope_id": "",
        "attach_url": "",
        "session_id": "",
        "binding_id": "",
        "owner_agent_id": "",
        "lane_id": "",
        "worker_agent_id": "",
        "reason": "",
        "timestamp": "",
        "expires_at": "",
        "replace_existing": True,
    }
    cli_to_key = {
        "--ledger-path": "ledger_path",
        "--scope-kind": "scope_kind",
        "--scope-id": "scope_id",
        "--attach-url": "attach_url",
        "--session-id": "session_id",
        "--binding-id": "binding_id",
        "--owner-agent-id": "owner_agent_id",
        "--lane-id": "lane_id",
        "--worker-agent-id": "worker_agent_id",
        "--reason": "reason",
        "--timestamp": "timestamp",
        "--expires-at": "expires_at",
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--no-replace-existing":
            parsed["replace_existing"] = False
            i += 1
            continue
        if arg not in cli_to_key:
            print(f"Unknown opencode session claim option: {arg}", file=sys.stderr)
            print(_OPENCODE_SESSION_CLAIM_USAGE, file=sys.stderr)
            return 1
        if i + 1 >= len(args):
            print(_OPENCODE_SESSION_CLAIM_USAGE, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return 1
        parsed[cli_to_key[arg]] = args[i + 1]
        i += 2

    try:
        from .runtime.orchestration import (
            OpenCodeSessionClaimRequest,
            claim_opencode_session_binding,
        )

        result = claim_opencode_session_binding(
            OpenCodeSessionClaimRequest(
                ledger_path=_resolve_project_path(_find_project_root(), str(parsed["ledger_path"])),
                scope_kind=str(parsed["scope_kind"]),  # type: ignore[arg-type]
                scope_id=str(parsed["scope_id"]),
                attach_url=str(parsed["attach_url"]),
                session_id=str(parsed["session_id"]),
                binding_id=str(parsed["binding_id"]),
                owner_agent_id=str(parsed["owner_agent_id"]),
                lane_id=str(parsed["lane_id"]),
                worker_agent_id=str(parsed["worker_agent_id"]),
                reason=str(parsed["reason"]),
                timestamp=str(parsed["timestamp"]),
                expires_at=str(parsed["expires_at"]),
                replace_existing=bool(parsed["replace_existing"]),
            )
        )
    except Exception as e:
        return _handle_error(
            "Error claiming OpenCode session binding",
            e,
            category="opencode_session_claim_failed",
        )
    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def cmd_opencode_session_release(args: list[str]) -> int:
    if args and args[0] in ("-h", "--help"):
        print(
            _OPENCODE_SESSION_RELEASE_USAGE + "\n\n"
            "Release marks a binding inactive in the local ledger. It does not "
            "terminate OpenCode server processes or delete provider state.",
        )
        return 0

    parsed: dict[str, object] = {
        "ledger_path": ".dbc/runtime/opencode-session-ledger.json",
        "binding_id": "",
        "scope_kind": "",
        "scope_id": "",
        "status": "released",
        "timestamp": "",
        "reason": "",
    }
    cli_to_key = {
        "--ledger-path": "ledger_path",
        "--binding-id": "binding_id",
        "--scope-kind": "scope_kind",
        "--scope-id": "scope_id",
        "--status": "status",
        "--timestamp": "timestamp",
        "--reason": "reason",
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg not in cli_to_key:
            print(f"Unknown opencode session release option: {arg}", file=sys.stderr)
            print(_OPENCODE_SESSION_RELEASE_USAGE, file=sys.stderr)
            return 1
        if i + 1 >= len(args):
            print(_OPENCODE_SESSION_RELEASE_USAGE, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return 1
        parsed[cli_to_key[arg]] = args[i + 1]
        i += 2
    if not parsed["binding_id"] and not (parsed["scope_kind"] and parsed["scope_id"]):
        print(_OPENCODE_SESSION_RELEASE_USAGE, file=sys.stderr)
        print("release requires --binding-id or --scope-kind with --scope-id", file=sys.stderr)
        return 1

    try:
        from .runtime.orchestration import (
            OpenCodeSessionReleaseRequest,
            release_opencode_session_binding,
        )

        result = release_opencode_session_binding(
            OpenCodeSessionReleaseRequest(
                ledger_path=_resolve_project_path(_find_project_root(), str(parsed["ledger_path"])),
                binding_id=str(parsed["binding_id"]),
                scope_kind=str(parsed["scope_kind"]),
                scope_id=str(parsed["scope_id"]),
                status=str(parsed["status"]),  # type: ignore[arg-type]
                timestamp=str(parsed["timestamp"]),
                reason=str(parsed["reason"]),
            )
        )
    except Exception as e:
        return _handle_error(
            "Error releasing OpenCode session binding",
            e,
            category="opencode_session_release_failed",
        )
    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def cmd_opencode_session_inspect(args: list[str]) -> int:
    if args and args[0] in ("-h", "--help"):
        print(
            _OPENCODE_SESSION_INSPECT_USAGE + "\n\n"
            "Inspect reads the local OpenCode session binding ledger without "
            "mutation. Released and expired bindings are hidden unless "
            "--include-released is passed.",
        )
        return 0

    parsed: dict[str, object] = {
        "ledger_path": ".dbc/runtime/opencode-session-ledger.json",
        "scope_kind": "",
        "scope_id": "",
        "include_released": False,
    }
    cli_to_key = {
        "--ledger-path": "ledger_path",
        "--scope-kind": "scope_kind",
        "--scope-id": "scope_id",
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--include-released":
            parsed["include_released"] = True
            i += 1
            continue
        if arg not in cli_to_key:
            print(f"Unknown opencode session inspect option: {arg}", file=sys.stderr)
            print(_OPENCODE_SESSION_INSPECT_USAGE, file=sys.stderr)
            return 1
        if i + 1 >= len(args):
            print(_OPENCODE_SESSION_INSPECT_USAGE, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return 1
        parsed[cli_to_key[arg]] = args[i + 1]
        i += 2

    try:
        from .runtime.orchestration import (
            OpenCodeSessionInspectRequest,
            inspect_opencode_session_bindings,
        )

        result = inspect_opencode_session_bindings(
            OpenCodeSessionInspectRequest(
                ledger_path=_resolve_project_path(_find_project_root(), str(parsed["ledger_path"])),
                scope_kind=str(parsed["scope_kind"]),
                scope_id=str(parsed["scope_id"]),
                include_released=bool(parsed["include_released"]),
            )
        )
    except Exception as e:
        return _handle_error(
            "Error inspecting OpenCode session bindings",
            e,
            category="opencode_session_inspect_failed",
        )
    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def cmd_opencode_session_recover_stale(args: list[str]) -> int:
    if args and args[0] in ("-h", "--help"):
        print(
            _OPENCODE_SESSION_RECOVER_STALE_USAGE + "\n\n"
            "Recover-stale expires active local ledger bindings whose expires_at "
            "is not later than --now. With --expire-unhealthy it also probes the "
            "binding attach target health endpoint. The command does not create "
            "sessions, start or stop opencode serve, run providers, mutate "
            "scheduler or delivery state, or mutate Local Work Trajectory.",
        )
        return 0

    parsed: dict[str, object] = {
        "ledger_path": ".dbc/runtime/opencode-session-ledger.json",
        "now": "",
        "timestamp": "",
        "expire_unhealthy": False,
        "health_path": "/global/health",
        "health_timeout_seconds": 2.0,
        "username_env_var": "OPENCODE_SERVER_USERNAME",
        "password_env_var": "OPENCODE_SERVER_PASSWORD",
        "reason": "stale OpenCode session binding recovery",
    }
    cli_to_key = {
        "--ledger-path": "ledger_path",
        "--now": "now",
        "--timestamp": "timestamp",
        "--health-path": "health_path",
        "--health-timeout-seconds": "health_timeout_seconds",
        "--username-env-var": "username_env_var",
        "--password-env-var": "password_env_var",
        "--reason": "reason",
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--expire-unhealthy":
            parsed["expire_unhealthy"] = True
            i += 1
            continue
        if arg not in cli_to_key:
            print(f"Unknown opencode session recover-stale option: {arg}", file=sys.stderr)
            print(_OPENCODE_SESSION_RECOVER_STALE_USAGE, file=sys.stderr)
            return 1
        if i + 1 >= len(args):
            print(_OPENCODE_SESSION_RECOVER_STALE_USAGE, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return 1
        key = cli_to_key[arg]
        value = args[i + 1]
        if key == "health_timeout_seconds":
            try:
                parsed[key] = float(value)
            except ValueError:
                print(_OPENCODE_SESSION_RECOVER_STALE_USAGE, file=sys.stderr)
                print(f"{arg} must be a number", file=sys.stderr)
                return 1
        else:
            parsed[key] = value
        i += 2
    if not parsed["now"]:
        print(_OPENCODE_SESSION_RECOVER_STALE_USAGE, file=sys.stderr)
        print("recover-stale requires --now", file=sys.stderr)
        return 1

    try:
        from .runtime.orchestration import (
            OpenCodeSessionRecoverStaleRequest,
            recover_stale_opencode_session_bindings,
        )

        result = recover_stale_opencode_session_bindings(
            OpenCodeSessionRecoverStaleRequest(
                ledger_path=_resolve_project_path(_find_project_root(), str(parsed["ledger_path"])),
                now=str(parsed["now"]),
                timestamp=str(parsed["timestamp"]),
                expire_unhealthy=bool(parsed["expire_unhealthy"]),
                health_path=str(parsed["health_path"]),
                health_timeout_seconds=float(parsed["health_timeout_seconds"]),
                username_env_var=str(parsed["username_env_var"]),
                password_env_var=str(parsed["password_env_var"]),
                reason=str(parsed["reason"]),
            )
        )
    except Exception as e:
        return _handle_error(
            "Error recovering stale OpenCode session bindings",
            e,
            category="opencode_session_recover_stale_failed",
        )
    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def cmd_worker_binding(args: list[str]) -> int:
    """Maintain provider-neutral continuous worker binding receipts."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _WORKER_BINDING_USAGE + "\n\n"
            "This command maintains durable continuous worker binding receipts. "
            "Bindings let scheduler-owned delivery reuse a worker identity across "
            "same-lane or lane-group tasks. The command does not create runtime "
            "sessions, run providers, mutate scheduler state, patch merge state, "
            "or Local Work Trajectory.\n\n"
            "Subcommands:\n"
            "  claim          Create or replace one active binding\n"
            "  promote-server-api-session\n"
            "                 Promote an explicit OpenCode server/API-created session\n"
            "  inspect-promotion-candidates\n"
            "                 Read runtime audit and suggest explicit promotions\n"
            "  lane-ownership\n"
            "                 Inspect or activate continuous worker lane ownership\n"
            "  reuse          Record delivery-time reuse of one binding\n"
            "  fork           Derive a new binding from an active binding\n"
            "  compact        Attach compact context/report refs to a binding\n"
            "  release        Mark one active binding released, stale, or archived\n"
            "  inspect        Read bindings without mutation\n"
            "  recover-stale  Mark elapsed bindings stale by explicit policy\n",
        )
        return 0

    sub = args[0]
    if sub == "claim":
        return cmd_worker_binding_claim(args[1:])
    if sub == "promote-server-api-session":
        return cmd_worker_binding_promote_server_api_session(args[1:])
    if sub == "inspect-promotion-candidates":
        return cmd_worker_binding_inspect_promotion_candidates(args[1:])
    if sub == "lane-ownership":
        return cmd_worker_binding_lane_ownership(args[1:])
    if sub == "reuse":
        return cmd_worker_binding_reuse(args[1:])
    if sub == "fork":
        return cmd_worker_binding_fork(args[1:])
    if sub == "compact":
        return cmd_worker_binding_compact(args[1:])
    if sub == "release":
        return cmd_worker_binding_release(args[1:])
    if sub == "inspect":
        return cmd_worker_binding_inspect(args[1:])
    if sub == "recover-stale":
        return cmd_worker_binding_recover_stale(args[1:])
    print(f"Unknown worker-binding subcommand: {sub}", file=sys.stderr)
    print(_WORKER_BINDING_USAGE, file=sys.stderr)
    return 1


def cmd_worker_binding_claim(args: list[str]) -> int:
    if args and args[0] in ("-h", "--help"):
        print(
            _WORKER_BINDING_CLAIM_USAGE + "\n\n"
            "Claiming records a project-owned worker continuity binding. For "
            "OpenCode, --session-id and optional --session-attach-url are copied "
            "into the provider-specific selector used at delivery time. The "
            "binding ledger remains the continuity source; OpenCode session "
            "state remains provider-owned.",
        )
        return 0

    parsed: dict[str, object] = {
        "ledger_path": ".dbc/runtime/continuous-worker-bindings.json",
        "event_log_path": ".dbc/runtime/continuous-worker-binding-events.jsonl",
        "worker_id": "",
        "runtime_provider": "opencode",
        "scope_kind": "",
        "scope_id": "",
        "lane_ids": [],
        "binding_id": "",
        "session_attach_url": "",
        "session_id": "",
        "continue_session": False,
        "fork_session": False,
        "compact_context_ref": "",
        "mailbox_cursor_ref": "",
        "worker_report_refs": [],
        "audit_refs": [],
        "timestamp": "",
        "expires_at": "",
        "reason": "",
        "replace_existing": True,
    }
    cli_to_key = {
        "--ledger-path": "ledger_path",
        "--event-log-path": "event_log_path",
        "--worker-id": "worker_id",
        "--runtime-provider": "runtime_provider",
        "--scope-kind": "scope_kind",
        "--scope-id": "scope_id",
        "--binding-id": "binding_id",
        "--session-attach-url": "session_attach_url",
        "--session-id": "session_id",
        "--compact-context-ref": "compact_context_ref",
        "--mailbox-cursor-ref": "mailbox_cursor_ref",
        "--timestamp": "timestamp",
        "--expires-at": "expires_at",
        "--reason": "reason",
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--no-replace-existing":
            parsed["replace_existing"] = False
            i += 1
            continue
        if arg == "--continue-session":
            parsed["continue_session"] = True
            i += 1
            continue
        if arg == "--fork-session":
            parsed["fork_session"] = True
            i += 1
            continue
        if arg in {"--lane-id", "--worker-report-ref", "--audit-ref"}:
            if i + 1 >= len(args):
                print(_WORKER_BINDING_CLAIM_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            key = {
                "--lane-id": "lane_ids",
                "--worker-report-ref": "worker_report_refs",
                "--audit-ref": "audit_refs",
            }[arg]
            parsed[key].append(args[i + 1])  # type: ignore[union-attr]
            i += 2
            continue
        if arg not in cli_to_key:
            print(f"Unknown worker-binding claim option: {arg}", file=sys.stderr)
            print(_WORKER_BINDING_CLAIM_USAGE, file=sys.stderr)
            return 1
        if i + 1 >= len(args):
            print(_WORKER_BINDING_CLAIM_USAGE, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return 1
        parsed[cli_to_key[arg]] = args[i + 1]
        i += 2

    try:
        from .runtime.orchestration import (
            ContinuousWorkerBindingClaimRequest,
            ContinuousWorkerSessionSelector,
            claim_continuous_worker_binding,
        )

        provider = str(parsed["runtime_provider"])
        session_selector = None
        if str(parsed["session_id"]) or bool(parsed["continue_session"]):
            session_selector = ContinuousWorkerSessionSelector(
                provider=provider,  # type: ignore[arg-type]
                attach_url=str(parsed["session_attach_url"]),
                session_id=str(parsed["session_id"]),
                continue_session=bool(parsed["continue_session"]),
                fork_session=bool(parsed["fork_session"]),
            )
        root = _find_project_root()
        result = claim_continuous_worker_binding(
            ContinuousWorkerBindingClaimRequest(
                ledger_path=_resolve_project_path(root, str(parsed["ledger_path"])),
                event_log_path=_resolve_project_path(root, str(parsed["event_log_path"])),
                worker_id=str(parsed["worker_id"]),
                runtime_provider=provider,  # type: ignore[arg-type]
                scope_kind=str(parsed["scope_kind"]),  # type: ignore[arg-type]
                scope_id=str(parsed["scope_id"]),
                lane_ids=tuple(parsed["lane_ids"]),  # type: ignore[arg-type]
                binding_id=str(parsed["binding_id"]),
                active_session_selector=session_selector,
                timestamp=str(parsed["timestamp"]),
                expires_at=str(parsed["expires_at"]),
                compact_context_ref=str(parsed["compact_context_ref"]),
                mailbox_cursor_ref=str(parsed["mailbox_cursor_ref"]),
                worker_report_refs=tuple(parsed["worker_report_refs"]),  # type: ignore[arg-type]
                audit_refs=tuple(parsed["audit_refs"]),  # type: ignore[arg-type]
                reason=str(parsed["reason"]),
                replace_existing=bool(parsed["replace_existing"]),
            )
        )
    except Exception as e:
        return _handle_error(
            "Error claiming continuous worker binding",
            e,
            category="worker_binding_claim_failed",
        )
    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def cmd_worker_binding_promote_server_api_session(args: list[str]) -> int:
    if args and args[0] in ("-h", "--help"):
        print(
            _WORKER_BINDING_PROMOTE_SERVER_API_SESSION_USAGE + "\n\n"
            "Promote is an explicit host/leader continuity decision. It takes "
            "an OpenCode server/API-created session selector and claims a "
            "provider-neutral continuous worker binding. It does not create "
            "sessions, run providers, mutate delivery or scheduler state, or "
            "mutate Local Work Trajectory. Pass --claim-lane-ownership to also "
            "claim continuous lane ownership for the promoted binding as the "
            "same explicit host/leader decision.",
        )
        return 0

    parsed: dict[str, object] = {
        "ledger_path": ".dbc/runtime/continuous-worker-bindings.json",
        "event_log_path": ".dbc/runtime/continuous-worker-binding-events.jsonl",
        "lane_ownership_ledger_path": ".dbc/runtime/continuous-worker-lane-ownerships.json",
        "lane_ownership_event_log_path": ".dbc/runtime/continuous-worker-lane-ownership-events.jsonl",
        "session_selector_source": "server_api_created",
        "attach_url": "",
        "session_id": "",
        "worker_id": "",
        "scope_kind": "",
        "scope_id": "",
        "lane_ids": [],
        "binding_id": "",
        "compact_context_ref": "",
        "mailbox_cursor_ref": "",
        "worker_report_refs": [],
        "audit_refs": [],
        "timestamp": "",
        "expires_at": "",
        "reason": "",
        "replace_existing": True,
        "claim_lane_ownership": False,
    }
    cli_to_key = {
        "--ledger-path": "ledger_path",
        "--event-log-path": "event_log_path",
        "--lane-ownership-ledger-path": "lane_ownership_ledger_path",
        "--lane-ownership-event-log-path": "lane_ownership_event_log_path",
        "--session-selector-source": "session_selector_source",
        "--attach-url": "attach_url",
        "--session-id": "session_id",
        "--worker-id": "worker_id",
        "--scope-kind": "scope_kind",
        "--scope-id": "scope_id",
        "--binding-id": "binding_id",
        "--compact-context-ref": "compact_context_ref",
        "--mailbox-cursor-ref": "mailbox_cursor_ref",
        "--timestamp": "timestamp",
        "--expires-at": "expires_at",
        "--reason": "reason",
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--no-replace-existing":
            parsed["replace_existing"] = False
            i += 1
            continue
        if arg == "--claim-lane-ownership":
            parsed["claim_lane_ownership"] = True
            i += 1
            continue
        if arg in {"--lane-id", "--worker-report-ref", "--audit-ref"}:
            if i + 1 >= len(args):
                print(_WORKER_BINDING_PROMOTE_SERVER_API_SESSION_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            key = {
                "--lane-id": "lane_ids",
                "--worker-report-ref": "worker_report_refs",
                "--audit-ref": "audit_refs",
            }[arg]
            parsed[key].append(args[i + 1])  # type: ignore[union-attr]
            i += 2
            continue
        if arg not in cli_to_key:
            print(f"Unknown worker-binding promote-server-api-session option: {arg}", file=sys.stderr)
            print(_WORKER_BINDING_PROMOTE_SERVER_API_SESSION_USAGE, file=sys.stderr)
            return 1
        if i + 1 >= len(args):
            print(_WORKER_BINDING_PROMOTE_SERVER_API_SESSION_USAGE, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return 1
        parsed[cli_to_key[arg]] = args[i + 1]
        i += 2

    missing = [
        name
        for name in ("--worker-id", "--scope-kind", "--scope-id", "--attach-url", "--session-id")
        if not parsed[
            {
                "--worker-id": "worker_id",
                "--scope-kind": "scope_kind",
                "--scope-id": "scope_id",
                "--attach-url": "attach_url",
                "--session-id": "session_id",
            }[name]
        ]
    ]
    if missing:
        print(_WORKER_BINDING_PROMOTE_SERVER_API_SESSION_USAGE, file=sys.stderr)
        print(f"Missing required option(s): {', '.join(missing)}", file=sys.stderr)
        return 1
    if bool(parsed["claim_lane_ownership"]) and str(parsed["scope_kind"]) not in {
        "lane",
        "lane_group",
    }:
        print(_WORKER_BINDING_PROMOTE_SERVER_API_SESSION_USAGE, file=sys.stderr)
        print(
            "--claim-lane-ownership requires --scope-kind lane or lane_group",
            file=sys.stderr,
        )
        return 1

    try:
        from .runtime.orchestration import (
            LaneOwnershipClaimRequest,
            ServerApiCreatedSessionPromotionRequest,
            claim_lane_ownership,
            promote_server_api_created_session_to_continuous_worker_binding,
        )

        root = _find_project_root()
        result = promote_server_api_created_session_to_continuous_worker_binding(
            ServerApiCreatedSessionPromotionRequest(
                ledger_path=_resolve_project_path(root, str(parsed["ledger_path"])),
                event_log_path=_resolve_project_path(root, str(parsed["event_log_path"])),
                session_selector_source=str(parsed["session_selector_source"]),
                attach_url=str(parsed["attach_url"]),
                session_id=str(parsed["session_id"]),
                worker_id=str(parsed["worker_id"]),
                scope_kind=str(parsed["scope_kind"]),  # type: ignore[arg-type]
                scope_id=str(parsed["scope_id"]),
                lane_ids=tuple(parsed["lane_ids"]),  # type: ignore[arg-type]
                binding_id=str(parsed["binding_id"]),
                compact_context_ref=str(parsed["compact_context_ref"]),
                mailbox_cursor_ref=str(parsed["mailbox_cursor_ref"]),
                worker_report_refs=tuple(parsed["worker_report_refs"]),  # type: ignore[arg-type]
                audit_refs=tuple(parsed["audit_refs"]),  # type: ignore[arg-type]
                timestamp=str(parsed["timestamp"]),
                expires_at=str(parsed["expires_at"]),
                reason=str(parsed["reason"]) or "server/API-created OpenCode session promoted",
                replace_existing=bool(parsed["replace_existing"]),
            )
        )
        payload = result.to_json_dict()
        if bool(parsed["claim_lane_ownership"]) and result.ok and result.binding is not None:
            ownership_result = claim_lane_ownership(
                LaneOwnershipClaimRequest(
                    ledger_path=_resolve_project_path(
                        root,
                        str(parsed["lane_ownership_ledger_path"]),
                    ),
                    event_log_path=_resolve_project_path(
                        root,
                        str(parsed["lane_ownership_event_log_path"]),
                    ),
                    scope_kind="lane_group" if str(parsed["scope_kind"]) == "lane_group" else "lane",
                    scope_id=str(parsed["scope_id"]),
                    lane_ids=tuple(parsed["lane_ids"]),  # type: ignore[arg-type]
                    binding_id=result.binding.binding_id,
                    worker_id=str(parsed["worker_id"]),
                    timestamp=str(parsed["timestamp"]),
                    requested_by="host:worker-binding-promote-server-api-session",
                    reason="lane ownership claimed during server/API session promotion",
                    audit_refs=tuple(parsed["audit_refs"]),  # type: ignore[arg-type]
                    metadata={
                        "promotion_source": "server_api_created",
                        "promotion_binding_id": result.binding.binding_id,
                    },
                )
            )
            payload["lane_ownership_claimed"] = ownership_result.ok
            payload["lane_ownership_result"] = ownership_result.to_json_dict()
    except Exception as e:
        return _handle_error(
            "Error promoting server/API-created session to continuous worker binding",
            e,
            category="worker_binding_promote_server_api_session_failed",
        )
    lane_ownership_payload = payload.get("lane_ownership_result")
    lane_ownership_ok = (
        True
        if not isinstance(lane_ownership_payload, dict)
        else bool(lane_ownership_payload.get("ok"))
    )
    _print_json(payload)
    return 0 if payload.get("ok") and lane_ownership_ok else 1


def cmd_worker_binding_inspect_promotion_candidates(args: list[str]) -> int:
    if args and args[0] in ("-h", "--help"):
        print(
            _WORKER_BINDING_INSPECT_PROMOTION_CANDIDATES_USAGE + "\n\n"
            "This is a read-only helper. It scans compact runtime invocation "
            "audit records for OpenCode server_api_created sessions and emits "
            "structured promotion candidates plus copyable "
            "worker-binding promote-server-api-session commands. It does not "
            "promote automatically, create sessions, run providers, mutate "
            "ledgers, or mutate Local Work Trajectory.\n\n"
            "Relative --runtime-invocation-log-path values are resolved against "
            "the detected project root/current workspace. Run from the intended "
            "workspace or pass an absolute audit path.",
        )
        return 0

    parsed: dict[str, object] = {
        "runtime_invocation_log_path": ".dbc/runtime/invocations.jsonl",
        "latest_limit": 100,
        "include_incomplete": False,
        "command_prefix": "doc-based-coding",
    }
    cli_to_key = {
        "--runtime-invocation-log-path": "runtime_invocation_log_path",
        "--latest-limit": "latest_limit",
        "--command-prefix": "command_prefix",
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--include-incomplete":
            parsed["include_incomplete"] = True
            i += 1
            continue
        if arg not in cli_to_key:
            print(f"Unknown worker-binding inspect-promotion-candidates option: {arg}", file=sys.stderr)
            print(_WORKER_BINDING_INSPECT_PROMOTION_CANDIDATES_USAGE, file=sys.stderr)
            return 1
        if i + 1 >= len(args):
            print(_WORKER_BINDING_INSPECT_PROMOTION_CANDIDATES_USAGE, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return 1
        value = args[i + 1]
        if arg == "--latest-limit":
            try:
                parsed["latest_limit"] = int(value)
            except ValueError:
                print(_WORKER_BINDING_INSPECT_PROMOTION_CANDIDATES_USAGE, file=sys.stderr)
                print("--latest-limit must be an integer", file=sys.stderr)
                return 1
        else:
            parsed[cli_to_key[arg]] = value
        i += 2

    try:
        from .runtime.orchestration import (
            WorkerBindingPromotionCandidateReadbackRequest,
            inspect_worker_binding_promotion_candidates,
        )

        root = _find_project_root()
        result = inspect_worker_binding_promotion_candidates(
            WorkerBindingPromotionCandidateReadbackRequest(
                runtime_invocation_log_path=_resolve_project_path(
                    root,
                    str(parsed["runtime_invocation_log_path"]),
                ),
                latest_limit=int(parsed["latest_limit"]),
                include_incomplete=bool(parsed["include_incomplete"]),
                command_prefix=tuple(str(parsed["command_prefix"]).split()),
            )
        )
    except Exception as e:
        return _handle_error(
            "Error inspecting worker-binding promotion candidates",
            e,
            category="worker_binding_promotion_candidate_inspect_failed",
        )
    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def cmd_worker_binding_reuse(args: list[str]) -> int:
    if args and args[0] in ("-h", "--help"):
        print(
            _WORKER_BINDING_REUSE_USAGE + "\n\n"
            "Reuse records that scheduler-owned delivery reused a continuous "
            "worker binding. It updates last_used_at and compact audit refs, "
            "but does not run providers or mutate Local Work Trajectory.",
        )
        return 0

    parsed: dict[str, object] = {
        "ledger_path": ".dbc/runtime/continuous-worker-bindings.json",
        "event_log_path": ".dbc/runtime/continuous-worker-binding-events.jsonl",
        "binding_id": "",
        "task_id": "",
        "agent_id": "",
        "lane_id": "",
        "audit_refs": [],
        "timestamp": "",
        "reason": "continuous worker binding reused for delivery",
    }
    cli_to_key = {
        "--ledger-path": "ledger_path",
        "--event-log-path": "event_log_path",
        "--binding-id": "binding_id",
        "--task-id": "task_id",
        "--agent-id": "agent_id",
        "--lane-id": "lane_id",
        "--timestamp": "timestamp",
        "--reason": "reason",
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--audit-ref":
            if i + 1 >= len(args):
                print(_WORKER_BINDING_REUSE_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            parsed["audit_refs"].append(args[i + 1])  # type: ignore[union-attr]
            i += 2
            continue
        if arg not in cli_to_key:
            print(f"Unknown worker-binding reuse option: {arg}", file=sys.stderr)
            print(_WORKER_BINDING_REUSE_USAGE, file=sys.stderr)
            return 1
        if i + 1 >= len(args):
            print(_WORKER_BINDING_REUSE_USAGE, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return 1
        parsed[cli_to_key[arg]] = args[i + 1]
        i += 2
    if not parsed["binding_id"]:
        print(_WORKER_BINDING_REUSE_USAGE, file=sys.stderr)
        print("reuse requires --binding-id", file=sys.stderr)
        return 1

    try:
        from .runtime.orchestration import (
            ContinuousWorkerBindingReuseRequest,
            record_continuous_worker_binding_reuse,
        )

        root = _find_project_root()
        result = record_continuous_worker_binding_reuse(
            ContinuousWorkerBindingReuseRequest(
                ledger_path=_resolve_project_path(root, str(parsed["ledger_path"])),
                event_log_path=_resolve_project_path(root, str(parsed["event_log_path"])),
                binding_id=str(parsed["binding_id"]),
                task_id=str(parsed["task_id"]),
                agent_id=str(parsed["agent_id"]),
                lane_id=str(parsed["lane_id"]),
                timestamp=str(parsed["timestamp"]),
                audit_refs=tuple(parsed["audit_refs"]),  # type: ignore[arg-type]
                reason=str(parsed["reason"]),
            )
        )
    except Exception as e:
        return _handle_error(
            "Error recording continuous worker binding reuse",
            e,
            category="worker_binding_reuse_failed",
        )
    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def cmd_worker_binding_fork(args: list[str]) -> int:
    if args and args[0] in ("-h", "--help"):
        print(
            _WORKER_BINDING_FORK_USAGE + "\n\n"
            "Fork records a new project-owned continuous worker binding derived "
            "from an existing active binding. It may carry an OpenCode "
            "fork_session selector, but it does not create provider sessions.",
        )
        return 0

    parsed: dict[str, object] = {
        "ledger_path": ".dbc/runtime/continuous-worker-bindings.json",
        "event_log_path": ".dbc/runtime/continuous-worker-binding-events.jsonl",
        "source_binding_id": "",
        "new_binding_id": "",
        "worker_id": "",
        "scope_kind": "",
        "scope_id": "",
        "lane_ids": [],
        "session_attach_url": "",
        "session_id": "",
        "continue_session": False,
        "fork_session": False,
        "compact_context_ref": "",
        "mailbox_cursor_ref": "",
        "worker_report_refs": [],
        "audit_refs": [],
        "timestamp": "",
        "expires_at": "",
        "reason": "continuous worker binding forked",
    }
    cli_to_key = {
        "--ledger-path": "ledger_path",
        "--event-log-path": "event_log_path",
        "--source-binding-id": "source_binding_id",
        "--new-binding-id": "new_binding_id",
        "--worker-id": "worker_id",
        "--scope-kind": "scope_kind",
        "--scope-id": "scope_id",
        "--session-attach-url": "session_attach_url",
        "--session-id": "session_id",
        "--compact-context-ref": "compact_context_ref",
        "--mailbox-cursor-ref": "mailbox_cursor_ref",
        "--timestamp": "timestamp",
        "--expires-at": "expires_at",
        "--reason": "reason",
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--continue-session":
            parsed["continue_session"] = True
            i += 1
            continue
        if arg == "--fork-session":
            parsed["fork_session"] = True
            i += 1
            continue
        if arg in {"--lane-id", "--worker-report-ref", "--audit-ref"}:
            if i + 1 >= len(args):
                print(_WORKER_BINDING_FORK_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            key = {
                "--lane-id": "lane_ids",
                "--worker-report-ref": "worker_report_refs",
                "--audit-ref": "audit_refs",
            }[arg]
            parsed[key].append(args[i + 1])  # type: ignore[union-attr]
            i += 2
            continue
        if arg not in cli_to_key:
            print(f"Unknown worker-binding fork option: {arg}", file=sys.stderr)
            print(_WORKER_BINDING_FORK_USAGE, file=sys.stderr)
            return 1
        if i + 1 >= len(args):
            print(_WORKER_BINDING_FORK_USAGE, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return 1
        parsed[cli_to_key[arg]] = args[i + 1]
        i += 2
    if not parsed["source_binding_id"] or not parsed["scope_kind"] or not parsed["scope_id"]:
        print(_WORKER_BINDING_FORK_USAGE, file=sys.stderr)
        print("fork requires --source-binding-id, --scope-kind, and --scope-id", file=sys.stderr)
        return 1

    try:
        from .runtime.orchestration import (
            ContinuousWorkerBindingForkRequest,
            ContinuousWorkerSessionSelector,
            fork_continuous_worker_binding,
        )

        session_selector = None
        if str(parsed["session_id"]) or bool(parsed["continue_session"]):
            session_selector = ContinuousWorkerSessionSelector(
                provider="opencode",
                attach_url=str(parsed["session_attach_url"]),
                session_id=str(parsed["session_id"]),
                continue_session=bool(parsed["continue_session"]),
                fork_session=bool(parsed["fork_session"]),
            )
        root = _find_project_root()
        result = fork_continuous_worker_binding(
            ContinuousWorkerBindingForkRequest(
                ledger_path=_resolve_project_path(root, str(parsed["ledger_path"])),
                event_log_path=_resolve_project_path(root, str(parsed["event_log_path"])),
                source_binding_id=str(parsed["source_binding_id"]),
                new_binding_id=str(parsed["new_binding_id"]),
                worker_id=str(parsed["worker_id"]),
                scope_kind=str(parsed["scope_kind"]),  # type: ignore[arg-type]
                scope_id=str(parsed["scope_id"]),
                lane_ids=tuple(parsed["lane_ids"]),  # type: ignore[arg-type]
                active_session_selector=session_selector,
                timestamp=str(parsed["timestamp"]),
                expires_at=str(parsed["expires_at"]),
                compact_context_ref=str(parsed["compact_context_ref"]),
                mailbox_cursor_ref=str(parsed["mailbox_cursor_ref"]),
                worker_report_refs=tuple(parsed["worker_report_refs"]),  # type: ignore[arg-type]
                audit_refs=tuple(parsed["audit_refs"]),  # type: ignore[arg-type]
                reason=str(parsed["reason"]),
            )
        )
    except Exception as e:
        return _handle_error(
            "Error forking continuous worker binding",
            e,
            category="worker_binding_fork_failed",
        )
    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def cmd_worker_binding_compact(args: list[str]) -> int:
    if args and args[0] in ("-h", "--help"):
        print(
            _WORKER_BINDING_COMPACT_USAGE + "\n\n"
            "Compact records a project-owned compact context snapshot reference "
            "for an active binding. It does not persist raw transcript text.",
        )
        return 0

    parsed: dict[str, object] = {
        "ledger_path": ".dbc/runtime/continuous-worker-bindings.json",
        "event_log_path": ".dbc/runtime/continuous-worker-binding-events.jsonl",
        "binding_id": "",
        "scope_kind": "",
        "scope_id": "",
        "compact_context_ref": "",
        "build_context_bundle": False,
        "context_bundle_dir": ".dbc/runtime/continuous-worker-contexts",
        "context_bundle_path": "",
        "bundle_id": "",
        "summary": "",
        "key_decisions": [],
        "current_state": "",
        "artifact_refs": [],
        "mailbox_cursor_ref": "",
        "worker_report_refs": [],
        "audit_refs": [],
        "timestamp": "",
        "reason": "continuous worker binding compacted",
    }
    cli_to_key = {
        "--ledger-path": "ledger_path",
        "--event-log-path": "event_log_path",
        "--binding-id": "binding_id",
        "--scope-kind": "scope_kind",
        "--scope-id": "scope_id",
        "--compact-context-ref": "compact_context_ref",
        "--context-bundle-dir": "context_bundle_dir",
        "--context-bundle-path": "context_bundle_path",
        "--bundle-id": "bundle_id",
        "--summary": "summary",
        "--current-state": "current_state",
        "--mailbox-cursor-ref": "mailbox_cursor_ref",
        "--timestamp": "timestamp",
        "--reason": "reason",
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--build-context-bundle":
            parsed["build_context_bundle"] = True
            i += 1
            continue
        if arg in {"--worker-report-ref", "--audit-ref", "--key-decision", "--artifact-ref"}:
            if i + 1 >= len(args):
                print(_WORKER_BINDING_COMPACT_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            key = {
                "--worker-report-ref": "worker_report_refs",
                "--audit-ref": "audit_refs",
                "--key-decision": "key_decisions",
                "--artifact-ref": "artifact_refs",
            }[arg]
            parsed[key].append(args[i + 1])  # type: ignore[union-attr]
            i += 2
            continue
        if arg not in cli_to_key:
            print(f"Unknown worker-binding compact option: {arg}", file=sys.stderr)
            print(_WORKER_BINDING_COMPACT_USAGE, file=sys.stderr)
            return 1
        if i + 1 >= len(args):
            print(_WORKER_BINDING_COMPACT_USAGE, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return 1
        parsed[cli_to_key[arg]] = args[i + 1]
        i += 2
    if not parsed["compact_context_ref"] and not parsed["build_context_bundle"]:
        print(_WORKER_BINDING_COMPACT_USAGE, file=sys.stderr)
        print("compact requires --compact-context-ref or --build-context-bundle", file=sys.stderr)
        return 1
    if parsed["build_context_bundle"] and not parsed["summary"]:
        print(_WORKER_BINDING_COMPACT_USAGE, file=sys.stderr)
        print("--build-context-bundle requires --summary", file=sys.stderr)
        return 1
    if not parsed["binding_id"] and not (parsed["scope_kind"] and parsed["scope_id"]):
        print(_WORKER_BINDING_COMPACT_USAGE, file=sys.stderr)
        print("compact requires --binding-id or --scope-kind with --scope-id", file=sys.stderr)
        return 1

    try:
        from .runtime.orchestration import (
            ContinuousWorkerBindingCompactRequest,
            ContinuousWorkerCompactContextBuildRequest,
            build_continuous_worker_compact_context_bundle,
            compact_continuous_worker_binding,
        )

        root = _find_project_root()
        compact_context_ref = str(parsed["compact_context_ref"])
        context_result = None
        if parsed["build_context_bundle"]:
            context_result = build_continuous_worker_compact_context_bundle(
                ContinuousWorkerCompactContextBuildRequest(
                    ledger_path=_resolve_project_path(root, str(parsed["ledger_path"])),
                    bundle_dir_path=_resolve_project_path(root, str(parsed["context_bundle_dir"])),
                    bundle_path=(
                        _resolve_project_path(root, str(parsed["context_bundle_path"]))
                        if str(parsed["context_bundle_path"])
                        else ""
                    ),
                    binding_id=str(parsed["binding_id"]),
                    scope_kind=str(parsed["scope_kind"]),
                    scope_id=str(parsed["scope_id"]),
                    bundle_id=str(parsed["bundle_id"]),
                    timestamp=str(parsed["timestamp"]),
                    summary=str(parsed["summary"]),
                    key_decisions=tuple(parsed["key_decisions"]),  # type: ignore[arg-type]
                    current_state=str(parsed["current_state"]),
                    artifact_refs=tuple(parsed["artifact_refs"]),  # type: ignore[arg-type]
                    mailbox_cursor_ref=str(parsed["mailbox_cursor_ref"]),
                    worker_report_refs=tuple(parsed["worker_report_refs"]),  # type: ignore[arg-type]
                    audit_refs=tuple(parsed["audit_refs"]),  # type: ignore[arg-type]
                )
            )
            if not context_result.ok:
                _print_json(context_result.to_json_dict())
                return 1
            compact_context_ref = context_result.compact_context_ref
        result = compact_continuous_worker_binding(
            ContinuousWorkerBindingCompactRequest(
                ledger_path=_resolve_project_path(root, str(parsed["ledger_path"])),
                event_log_path=_resolve_project_path(root, str(parsed["event_log_path"])),
                binding_id=str(parsed["binding_id"]),
                scope_kind=str(parsed["scope_kind"]),
                scope_id=str(parsed["scope_id"]),
                compact_context_ref=compact_context_ref,
                mailbox_cursor_ref=str(parsed["mailbox_cursor_ref"]),
                worker_report_refs=tuple(parsed["worker_report_refs"]),  # type: ignore[arg-type]
                audit_refs=tuple(parsed["audit_refs"]),  # type: ignore[arg-type]
                timestamp=str(parsed["timestamp"]),
                reason=str(parsed["reason"]),
            )
        )
    except Exception as e:
        return _handle_error(
            "Error compacting continuous worker binding",
            e,
            category="worker_binding_compact_failed",
        )
    payload = result.to_json_dict()
    if "context_result" in locals() and context_result is not None:
        payload["context_bundle"] = context_result.to_json_dict()
    _print_json(payload)
    return 0 if result.ok else 1


def cmd_worker_binding_release(args: list[str]) -> int:
    if args and args[0] in ("-h", "--help"):
        print(
            _WORKER_BINDING_RELEASE_USAGE + "\n\n"
            "Release marks a continuous worker binding inactive in the project "
            "ledger. It does not stop provider sessions or delete provider state.",
        )
        return 0

    parsed: dict[str, object] = {
        "ledger_path": ".dbc/runtime/continuous-worker-bindings.json",
        "event_log_path": ".dbc/runtime/continuous-worker-binding-events.jsonl",
        "binding_id": "",
        "scope_kind": "",
        "scope_id": "",
        "status": "released",
        "timestamp": "",
        "reason": "",
    }
    cli_to_key = {
        "--ledger-path": "ledger_path",
        "--event-log-path": "event_log_path",
        "--binding-id": "binding_id",
        "--scope-kind": "scope_kind",
        "--scope-id": "scope_id",
        "--status": "status",
        "--timestamp": "timestamp",
        "--reason": "reason",
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg not in cli_to_key:
            print(f"Unknown worker-binding release option: {arg}", file=sys.stderr)
            print(_WORKER_BINDING_RELEASE_USAGE, file=sys.stderr)
            return 1
        if i + 1 >= len(args):
            print(_WORKER_BINDING_RELEASE_USAGE, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return 1
        parsed[cli_to_key[arg]] = args[i + 1]
        i += 2
    if not parsed["binding_id"] and not (parsed["scope_kind"] and parsed["scope_id"]):
        print(_WORKER_BINDING_RELEASE_USAGE, file=sys.stderr)
        print("release requires --binding-id or --scope-kind with --scope-id", file=sys.stderr)
        return 1

    try:
        from .runtime.orchestration import (
            ContinuousWorkerBindingReleaseRequest,
            release_continuous_worker_binding,
        )

        root = _find_project_root()
        result = release_continuous_worker_binding(
            ContinuousWorkerBindingReleaseRequest(
                ledger_path=_resolve_project_path(root, str(parsed["ledger_path"])),
                event_log_path=_resolve_project_path(root, str(parsed["event_log_path"])),
                binding_id=str(parsed["binding_id"]),
                scope_kind=str(parsed["scope_kind"]),
                scope_id=str(parsed["scope_id"]),
                lifecycle_status=str(parsed["status"]),  # type: ignore[arg-type]
                timestamp=str(parsed["timestamp"]),
                reason=str(parsed["reason"]),
            )
        )
    except Exception as e:
        return _handle_error(
            "Error releasing continuous worker binding",
            e,
            category="worker_binding_release_failed",
        )
    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def cmd_worker_binding_inspect(args: list[str]) -> int:
    if args and args[0] in ("-h", "--help"):
        print(
            _WORKER_BINDING_INSPECT_USAGE + "\n\n"
            "Inspect reads the continuous worker binding ledger without mutation. "
            "Released, stale, and archived bindings are hidden unless "
            "--include-inactive is passed.",
        )
        return 0

    parsed: dict[str, object] = {
        "ledger_path": ".dbc/runtime/continuous-worker-bindings.json",
        "runtime_provider": "",
        "scope_kind": "",
        "scope_id": "",
        "worker_id": "",
        "lane_id": "",
        "include_inactive": False,
    }
    cli_to_key = {
        "--ledger-path": "ledger_path",
        "--runtime-provider": "runtime_provider",
        "--scope-kind": "scope_kind",
        "--scope-id": "scope_id",
        "--worker-id": "worker_id",
        "--lane-id": "lane_id",
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--include-inactive":
            parsed["include_inactive"] = True
            i += 1
            continue
        if arg not in cli_to_key:
            print(f"Unknown worker-binding inspect option: {arg}", file=sys.stderr)
            print(_WORKER_BINDING_INSPECT_USAGE, file=sys.stderr)
            return 1
        if i + 1 >= len(args):
            print(_WORKER_BINDING_INSPECT_USAGE, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return 1
        parsed[cli_to_key[arg]] = args[i + 1]
        i += 2

    try:
        from .runtime.orchestration import (
            ContinuousWorkerBindingInspectRequest,
            inspect_continuous_worker_bindings,
        )

        result = inspect_continuous_worker_bindings(
            ContinuousWorkerBindingInspectRequest(
                ledger_path=_resolve_project_path(_find_project_root(), str(parsed["ledger_path"])),
                runtime_provider=str(parsed["runtime_provider"]),  # type: ignore[arg-type]
                scope_kind=str(parsed["scope_kind"]),
                scope_id=str(parsed["scope_id"]),
                worker_id=str(parsed["worker_id"]),
                lane_id=str(parsed["lane_id"]),
                include_inactive=bool(parsed["include_inactive"]),
            )
        )
    except Exception as e:
        return _handle_error(
            "Error inspecting continuous worker bindings",
            e,
            category="worker_binding_inspect_failed",
        )
    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def cmd_worker_binding_lane_ownership(args: list[str]) -> int:
    """Inspect or activate continuous worker lane ownership records."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _WORKER_BINDING_LANE_OWNERSHIP_USAGE + "\n\n"
            "Lane ownership maps a lane or lane group to a continuous worker "
            "binding. This surface is host/leader-owned and does not run "
            "providers, mutate delivery or scheduler state, or mutate Local "
            "Work Trajectory.\n\n"
            "Subcommands:\n"
            "  inspect   Read lane ownership records without mutation\n"
            "  activate  Mark a claimed ownership active after successful delivery\n",
        )
        return 0
    sub = args[0]
    if sub == "inspect":
        return cmd_worker_binding_lane_ownership_inspect(args[1:])
    if sub == "activate":
        return cmd_worker_binding_lane_ownership_activate(args[1:])
    print(f"Unknown worker-binding lane-ownership subcommand: {sub}", file=sys.stderr)
    print(_WORKER_BINDING_LANE_OWNERSHIP_USAGE, file=sys.stderr)
    return 1


def cmd_worker_binding_lane_ownership_inspect(args: list[str]) -> int:
    if args and args[0] in ("-h", "--help"):
        print(
            _WORKER_BINDING_LANE_OWNERSHIP_INSPECT_USAGE + "\n\n"
            "Inspect reads the continuous worker lane ownership ledger without "
            "mutation. Transferred and released ownerships are hidden unless "
            "--include-inactive is passed.",
        )
        return 0

    parsed: dict[str, object] = {
        "ledger_path": ".dbc/runtime/continuous-worker-lane-ownerships.json",
        "ownership_id": "",
        "scope_kind": "",
        "scope_id": "",
        "lane_id": "",
        "binding_id": "",
        "worker_id": "",
        "include_inactive": False,
    }
    cli_to_key = {
        "--ledger-path": "ledger_path",
        "--ownership-id": "ownership_id",
        "--scope-kind": "scope_kind",
        "--scope-id": "scope_id",
        "--lane-id": "lane_id",
        "--binding-id": "binding_id",
        "--worker-id": "worker_id",
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--include-inactive":
            parsed["include_inactive"] = True
            i += 1
            continue
        if arg not in cli_to_key:
            print(f"Unknown worker-binding lane-ownership inspect option: {arg}", file=sys.stderr)
            print(_WORKER_BINDING_LANE_OWNERSHIP_INSPECT_USAGE, file=sys.stderr)
            return 1
        if i + 1 >= len(args):
            print(_WORKER_BINDING_LANE_OWNERSHIP_INSPECT_USAGE, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return 1
        parsed[cli_to_key[arg]] = args[i + 1]
        i += 2

    try:
        from .runtime.orchestration import (
            LaneOwnershipInspectRequest,
            inspect_lane_ownerships,
        )

        root = _find_project_root()
        result = inspect_lane_ownerships(
            LaneOwnershipInspectRequest(
                ledger_path=_resolve_project_path(root, str(parsed["ledger_path"])),
                ownership_id=str(parsed["ownership_id"]),
                scope_kind=str(parsed["scope_kind"]),
                scope_id=str(parsed["scope_id"]),
                lane_id=str(parsed["lane_id"]),
                binding_id=str(parsed["binding_id"]),
                worker_id=str(parsed["worker_id"]),
                include_inactive=bool(parsed["include_inactive"]),
            )
        )
    except Exception as e:
        return _handle_error(
            "Error inspecting continuous worker lane ownership",
            e,
            category="worker_binding_lane_ownership_inspect_failed",
        )
    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def cmd_worker_binding_lane_ownership_activate(args: list[str]) -> int:
    if args and args[0] in ("-h", "--help"):
        print(
            _WORKER_BINDING_LANE_OWNERSHIP_ACTIVATE_USAGE + "\n\n"
            "Activate moves a claimed lane ownership to active after the host "
            "has evidence of a successful delivery. It records compact audit "
            "metadata only and does not run providers.",
        )
        return 0

    parsed: dict[str, object] = {
        "ledger_path": ".dbc/runtime/continuous-worker-lane-ownerships.json",
        "event_log_path": ".dbc/runtime/continuous-worker-lane-ownership-events.jsonl",
        "ownership_id": "",
        "binding_id": "",
        "delivery_id": "",
        "task_id": "",
        "activated_at": "",
        "audit_refs": [],
        "reason": "lane ownership activated",
    }
    cli_to_key = {
        "--ledger-path": "ledger_path",
        "--event-log-path": "event_log_path",
        "--ownership-id": "ownership_id",
        "--binding-id": "binding_id",
        "--delivery-id": "delivery_id",
        "--task-id": "task_id",
        "--activated-at": "activated_at",
        "--reason": "reason",
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--audit-ref":
            if i + 1 >= len(args):
                print(_WORKER_BINDING_LANE_OWNERSHIP_ACTIVATE_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            parsed["audit_refs"].append(args[i + 1])  # type: ignore[union-attr]
            i += 2
            continue
        if arg not in cli_to_key:
            print(f"Unknown worker-binding lane-ownership activate option: {arg}", file=sys.stderr)
            print(_WORKER_BINDING_LANE_OWNERSHIP_ACTIVATE_USAGE, file=sys.stderr)
            return 1
        if i + 1 >= len(args):
            print(_WORKER_BINDING_LANE_OWNERSHIP_ACTIVATE_USAGE, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return 1
        parsed[cli_to_key[arg]] = args[i + 1]
        i += 2

    if not parsed["ownership_id"] and not parsed["binding_id"]:
        print(_WORKER_BINDING_LANE_OWNERSHIP_ACTIVATE_USAGE, file=sys.stderr)
        print("lane-ownership activate requires --ownership-id or --binding-id", file=sys.stderr)
        return 1
    missing = [
        name
        for name in ("--delivery-id", "--task-id")
        if not parsed[{"--delivery-id": "delivery_id", "--task-id": "task_id"}[name]]
    ]
    if missing:
        print(_WORKER_BINDING_LANE_OWNERSHIP_ACTIVATE_USAGE, file=sys.stderr)
        print(f"Missing required option(s): {', '.join(missing)}", file=sys.stderr)
        return 1

    try:
        from .runtime.orchestration import (
            LaneOwnershipActivateRequest,
            activate_lane_ownership,
        )

        root = _find_project_root()
        result = activate_lane_ownership(
            LaneOwnershipActivateRequest(
                ledger_path=_resolve_project_path(root, str(parsed["ledger_path"])),
                event_log_path=_resolve_project_path(root, str(parsed["event_log_path"])),
                ownership_id=str(parsed["ownership_id"]),
                binding_id=str(parsed["binding_id"]),
                activated_at=str(parsed["activated_at"]),
                delivery_id=str(parsed["delivery_id"]),
                task_id=str(parsed["task_id"]),
                reason=str(parsed["reason"]),
                audit_refs=tuple(parsed["audit_refs"]),  # type: ignore[arg-type]
                metadata={"activation_authority": "explicit_host_owned_action"},
            )
        )
    except Exception as e:
        return _handle_error(
            "Error activating continuous worker lane ownership",
            e,
            category="worker_binding_lane_ownership_activate_failed",
        )
    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def cmd_worker_binding_recover_stale(args: list[str]) -> int:
    if args and args[0] in ("-h", "--help"):
        print(
            _WORKER_BINDING_RECOVER_STALE_USAGE + "\n\n"
            "Recover-stale marks active bindings stale whose expires_at is not "
            "later than --now. It does not create replacement sessions.",
        )
        return 0

    parsed: dict[str, object] = {
        "ledger_path": ".dbc/runtime/continuous-worker-bindings.json",
        "event_log_path": ".dbc/runtime/continuous-worker-binding-events.jsonl",
        "now": "",
        "timestamp": "",
        "reason": "continuous worker binding stale recovery",
    }
    cli_to_key = {
        "--ledger-path": "ledger_path",
        "--event-log-path": "event_log_path",
        "--now": "now",
        "--timestamp": "timestamp",
        "--reason": "reason",
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg not in cli_to_key:
            print(f"Unknown worker-binding recover-stale option: {arg}", file=sys.stderr)
            print(_WORKER_BINDING_RECOVER_STALE_USAGE, file=sys.stderr)
            return 1
        if i + 1 >= len(args):
            print(_WORKER_BINDING_RECOVER_STALE_USAGE, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return 1
        parsed[cli_to_key[arg]] = args[i + 1]
        i += 2
    if not parsed["now"]:
        print(_WORKER_BINDING_RECOVER_STALE_USAGE, file=sys.stderr)
        print("recover-stale requires --now", file=sys.stderr)
        return 1

    try:
        from .runtime.orchestration import (
            ContinuousWorkerBindingRecoverStaleRequest,
            recover_stale_continuous_worker_bindings,
        )

        root = _find_project_root()
        result = recover_stale_continuous_worker_bindings(
            ContinuousWorkerBindingRecoverStaleRequest(
                ledger_path=_resolve_project_path(root, str(parsed["ledger_path"])),
                event_log_path=_resolve_project_path(root, str(parsed["event_log_path"])),
                now=str(parsed["now"]),
                timestamp=str(parsed["timestamp"]),
                reason=str(parsed["reason"]),
            )
        )
    except Exception as e:
        return _handle_error(
            "Error recovering stale continuous worker bindings",
            e,
            category="worker_binding_recover_stale_failed",
        )
    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def cmd_opencode_guide_worker_smoke(args: list[str]) -> int:
    """Run host-owned OpenCode CLI guide-worker provider execution through CLI."""

    if args and args[0] in ("-h", "--help"):
        print(
            _OPENCODE_GUIDE_WORKER_SMOKE_USAGE + "\n\n"
            "This command is a host-owned live-provider guide-worker smoke "
            "surface for OpenCode CLI. It delegates to "
            "run_host_owned_guide_worker_provider_execution(), uses explicit "
            "host-authorized adapter wiring and an OpenCode process-spawn "
            "grant. It is not an MCP real-provider execution surface, does "
            "not persist raw transcripts, and does not mutate agent-owned "
            "Local Work Trajectory. Runtime invocations are audited to compact "
            "JSONL by default and retry retryable provider failures. "
            "Git-worktree worker changes are exported as review-only worker "
            "patch artifacts and merge candidates; they are not applied "
            "automatically.",
        )
        return 0

    executable = "opencode"
    cwd = ""
    model = ""
    output_format = "json"
    attach_url = ""
    session_id = ""
    continue_session = False
    fork_session = False
    artifact_store_path = ""
    admission_ledger_path = ""
    snapshot_path = ""
    event_log_path = ""
    evidence_id = ""
    evidence_path = ""
    git_worktree_sandbox_root = ""
    sandbox_allocation_evidence_id = ""
    sandbox_allocation_evidence_path = ""
    host_invocation_id = ""
    reason = ""
    runtime_invocation_log_path = ".dbc/runtime/invocations.jsonl"
    runtime_invocation_max_attempts = 2
    runtime_invocation_backoff_seconds = 0.0
    guide_task_title = ""
    guide_task_summary = ""
    planner_lane_specs: list[str] = []
    max_parallel_lanes = 2
    max_waves = 1
    wave_execution_mode = "threaded"
    timestamp = ""

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {
            "--executable",
            "--cwd",
            "--model",
            "--output-format",
            "--attach-url",
            "--session-id",
            "--artifact-store-path",
            "--admission-ledger-path",
            "--snapshot-path",
            "--event-log-path",
            "--evidence-id",
            "--evidence-path",
            "--git-worktree-sandbox-root",
            "--sandbox-allocation-evidence-id",
            "--sandbox-allocation-evidence-path",
            "--host-invocation-id",
            "--reason",
            "--runtime-invocation-log-path",
            "--runtime-invocation-max-attempts",
            "--runtime-invocation-backoff-seconds",
            "--guide-task-title",
            "--guide-task-summary",
            "--planner-lane",
            "--max-parallel-lanes",
            "--max-waves",
            "--wave-execution-mode",
            "--timestamp",
        }:
            if i + 1 >= len(args):
                print(_OPENCODE_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--executable":
                executable = value
            elif arg == "--cwd":
                cwd = value
            elif arg == "--model":
                model = value
            elif arg == "--output-format":
                output_format = value
            elif arg == "--attach-url":
                attach_url = value
            elif arg == "--session-id":
                session_id = value
            elif arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--admission-ledger-path":
                admission_ledger_path = value
            elif arg == "--snapshot-path":
                snapshot_path = value
            elif arg == "--event-log-path":
                event_log_path = value
            elif arg == "--evidence-id":
                evidence_id = value
            elif arg == "--evidence-path":
                evidence_path = value
            elif arg == "--git-worktree-sandbox-root":
                git_worktree_sandbox_root = value
            elif arg == "--sandbox-allocation-evidence-id":
                sandbox_allocation_evidence_id = value
            elif arg == "--sandbox-allocation-evidence-path":
                sandbox_allocation_evidence_path = value
            elif arg == "--host-invocation-id":
                host_invocation_id = value
            elif arg == "--reason":
                reason = value
            elif arg == "--runtime-invocation-log-path":
                runtime_invocation_log_path = value
            elif arg == "--runtime-invocation-max-attempts":
                try:
                    runtime_invocation_max_attempts = int(value)
                except ValueError:
                    print(_OPENCODE_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
                    print("--runtime-invocation-max-attempts must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--runtime-invocation-backoff-seconds":
                try:
                    runtime_invocation_backoff_seconds = float(value)
                except ValueError:
                    print(_OPENCODE_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
                    print("--runtime-invocation-backoff-seconds must be a number", file=sys.stderr)
                    return 1
            elif arg == "--guide-task-title":
                guide_task_title = value
            elif arg == "--guide-task-summary":
                guide_task_summary = value
            elif arg == "--planner-lane":
                planner_lane_specs.append(value)
            elif arg == "--max-parallel-lanes":
                try:
                    max_parallel_lanes = int(value)
                except ValueError:
                    print(_OPENCODE_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
                    print("--max-parallel-lanes must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--max-waves":
                try:
                    max_waves = int(value)
                except ValueError:
                    print(_OPENCODE_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
                    print("--max-waves must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--wave-execution-mode":
                wave_execution_mode = value
            elif arg == "--timestamp":
                timestamp = value
            i += 2
            continue
        if arg == "--continue-session":
            continue_session = True
            i += 1
            continue
        if arg == "--fork-session":
            fork_session = True
            i += 1
            continue
        print(f"Unknown opencode guide-worker-smoke option: {arg}", file=sys.stderr)
        print(_OPENCODE_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
        return 1

    if output_format not in {"text", "json"}:
        print("opencode guide-worker-smoke --output-format must be text or json", file=sys.stderr)
        return 1
    if session_id and continue_session:
        print("opencode guide-worker-smoke cannot use --session-id with --continue-session", file=sys.stderr)
        return 1
    if fork_session and not (session_id or continue_session):
        print(
            "opencode guide-worker-smoke --fork-session requires --session-id or --continue-session",
            file=sys.stderr,
        )
        return 1
    if max_parallel_lanes < 1:
        print("opencode guide-worker-smoke --max-parallel-lanes must be positive", file=sys.stderr)
        return 1
    if max_waves < 1:
        print("opencode guide-worker-smoke --max-waves must be positive", file=sys.stderr)
        return 1
    if runtime_invocation_max_attempts < 1:
        print("opencode guide-worker-smoke --runtime-invocation-max-attempts must be positive", file=sys.stderr)
        return 1
    if runtime_invocation_backoff_seconds < 0:
        print(
            "opencode guide-worker-smoke --runtime-invocation-backoff-seconds must be non-negative",
            file=sys.stderr,
        )
        return 1
    if wave_execution_mode not in {"serial", "threaded"}:
        print(
            "opencode guide-worker-smoke --wave-execution-mode must be serial or threaded",
            file=sys.stderr,
        )
        return 1

    root = _find_project_root()
    try:
        from .runtime.orchestration import (
            GuideWorkerPlannerLaneSpec,
            GuideWorkerPlanningRequest,
            OpenCodeCliClientConfig,
        )
        from tools.progress_graph import (
            HostOwnedGuideWorkerProviderExecutionConfig,
            run_host_owned_guide_worker_provider_execution,
        )

        opencode_config = OpenCodeCliClientConfig(
            executable=executable,
            cwd=cwd,
            model=model,
            output_format=output_format,  # type: ignore[arg-type]
            attach_url=attach_url,
            session_id=session_id,
            continue_session=continue_session,
            fork_session=fork_session,
        )
        planning_request = GuideWorkerPlanningRequest(
            task_title=guide_task_title,
            task_summary=guide_task_summary,
            lane_specs=tuple(
                _parse_guide_worker_planner_lane_spec(
                    item,
                    GuideWorkerPlannerLaneSpec,
                )
                for item in planner_lane_specs
            ),
        )
        config_kwargs = {
            "evidence_id": evidence_id or "opencode-guide-worker-provider-execution",
            "timestamp": timestamp,
            "artifact_store_path": artifact_store_path or ".dbc/orchestration/exchange-artifacts.json",
            "admission_ledger_path": (
                admission_ledger_path
                or ".dbc/orchestration/exchange-artifact-admissions.json"
            ),
            "snapshot_path": (
                snapshot_path
                or ".dbc/scheduler/opencode-guide-worker-provider-execution-state.json"
            ),
            "event_log_path": (
                event_log_path
                or ".dbc/scheduler/opencode-guide-worker-provider-execution-events.jsonl"
            ),
            "evidence_output_path": evidence_path or None,
            "workspace_root": str(root),
            "git_worktree_sandbox_root": git_worktree_sandbox_root or None,
            "sandbox_allocation_evidence_id": sandbox_allocation_evidence_id,
            "sandbox_allocation_evidence_path": sandbox_allocation_evidence_path or None,
            "providers": ("opencode",),
            "opencode_cli_client_config": opencode_config,
            "host_invocation_id": (
                host_invocation_id
                or "host-owned-opencode-guide-worker-provider-execution-cli"
            ),
            "requested_by": "cli:opencode-guide-worker-smoke",
            "reason": reason or "host-owned OpenCode CLI guide-worker smoke run from CLI",
            "runtime_invocation_log_path": runtime_invocation_log_path or None,
            "runtime_invocation_max_attempts": runtime_invocation_max_attempts,
            "runtime_invocation_backoff_seconds": runtime_invocation_backoff_seconds,
            "grant_id": (
                f"grant-{host_invocation_id}"
                if host_invocation_id
                else "grant-host-owned-opencode-guide-worker-provider-execution-cli"
            ),
            "approved_by": "cli:opencode-guide-worker-smoke",
            "approved_at": timestamp,
            "planning_request": planning_request,
            "planner_worker_runtime_provider": "opencode",
            "max_parallel_lanes": max_parallel_lanes,
            "max_waves": max_waves,
            "wave_execution_mode": wave_execution_mode,
        }
        if planner_lane_specs:
            config_kwargs["worker_instructions"] = ()
        config = HostOwnedGuideWorkerProviderExecutionConfig(**config_kwargs)
        result = run_host_owned_guide_worker_provider_execution(root, config=config)
    except Exception as e:
        return _handle_error(
            "Error running OpenCode guide-worker smoke",
            e,
            category="opencode_guide_worker_smoke_failed",
        )

    _print_json(result.to_json_dict())
    return 0 if result.orchestration.ok else 1


def cmd_qoder(args: list[str]) -> int:
    """Qoder host-runtime helper subcommands."""
    if not args or args[0] in ("-h", "--help"):
        print(
            "Usage: doc-based-coding qoder <subcommand> [args]\n\n"
            "Subcommands:\n"
            "  readiness [--auth-mode env|qodercli] [--auth-env-var NAME] [--sdk-module NAME]\n"
            "      Check optional qoder-agent-sdk host readiness without printing secrets\n",
            "  smoke [--auth-mode env|qodercli] [--auth-env-var NAME] [--sdk-module NAME]\n"
            "      Run the host-owned Qoder smoke helper with explicit host authorization\n",
            "  guide-worker-smoke [--auth-mode env|qodercli] [--auth-env-var NAME] [--sdk-module NAME]\n"
            "      Run host-owned Qoder guide-worker lane-wave execution\n",
        )
        return 0

    sub = args[0]
    if sub == "readiness":
        return cmd_qoder_readiness(args[1:])
    if sub == "smoke":
        return cmd_qoder_smoke(args[1:])
    if sub == "guide-worker-smoke":
        return cmd_qoder_guide_worker_smoke(args[1:])

    print(f"Unknown qoder subcommand: {sub}", file=sys.stderr)
    print(
        "Usage: doc-based-coding qoder <readiness|smoke|guide-worker-smoke> [args]",
        file=sys.stderr,
    )
    return 1


def cmd_qoder_readiness(args: list[str]) -> int:
    """Check optional Qoder SDK host readiness without executing a query."""

    if args and args[0] in ("-h", "--help"):
        print(
            _QODER_READINESS_USAGE + "\n\n"
            "This command checks whether the optional qoder-agent-sdk wrapper can "
            "be constructed by the host runtime. It prints only credential-safe "
            "booleans and redacted error clues; it does not run providers, write "
            "scheduler state, write evidence, or mutate Local Work Trajectory.",
        )
        return 0

    auth_mode = "env"
    auth_env_var = ""
    sdk_module_name = ""
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--auth-mode":
            if i + 1 >= len(args):
                print(_QODER_READINESS_USAGE, file=sys.stderr)
                return 1
            auth_mode = args[i + 1]
            i += 2
            continue
        if arg == "--auth-env-var":
            if i + 1 >= len(args):
                print(_QODER_READINESS_USAGE, file=sys.stderr)
                return 1
            auth_env_var = args[i + 1]
            i += 2
            continue
        if arg == "--sdk-module":
            if i + 1 >= len(args):
                print(_QODER_READINESS_USAGE, file=sys.stderr)
                return 1
            sdk_module_name = args[i + 1]
            i += 2
            continue
        print(f"Unknown qoder readiness option: {arg}", file=sys.stderr)
        print(_QODER_READINESS_USAGE, file=sys.stderr)
        return 1

    if auth_mode not in {"env", "qodercli"}:
        print("qoder readiness --auth-mode must be env or qodercli", file=sys.stderr)
        return 1

    try:
        from .runtime.orchestration import (
            DEFAULT_QODER_TOKEN_ENV,
            QoderSDKQueryClient,
            QoderSDKQueryClientConfig,
        )

        config = QoderSDKQueryClientConfig(
            auth_mode=auth_mode,  # type: ignore[arg-type]
            auth_env_var=auth_env_var or DEFAULT_QODER_TOKEN_ENV,
            sdk_module_name=sdk_module_name or "qoder_agent_sdk",
        )
        report = QoderSDKQueryClient(config).host_readiness_report()
    except Exception as e:
        return _handle_error("Error checking Qoder readiness", e, category="qoder_readiness_failed")

    _print_json(report.to_json_dict())
    return 0


def cmd_qoder_smoke(args: list[str]) -> int:
    """Run the host-owned Qoder smoke helper through a CLI surface."""

    if args and args[0] in ("-h", "--help"):
        print(
            _QODER_SMOKE_USAGE + "\n\n"
            "This command is a host-owned live-provider smoke surface. It delegates "
            "to run_host_owned_qoder_smoke(), uses the existing host-authorized "
            "adapter and Qoder permission grant contracts, and never accepts a raw "
            "token value. If SDK/auth readiness is missing, it fails before host "
            "evidence or scheduler projection writes. It is not an MCP real-provider "
            "execution surface and does not mutate agent-owned Local Work Trajectory.",
        )
        return 0

    auth_mode = "env"
    auth_env_var = ""
    sdk_module_name = ""
    cwd = ""
    model = ""
    max_turns: int | None = None
    permission_request_policy = "deny"
    snapshot_path = ""
    event_log_path = ""
    evidence_id = ""
    evidence_path = ""
    projection_output_path = ""
    host_invocation_id = ""
    reason = ""
    reset_snapshot = False
    initialize_snapshot = True
    timestamp = ""

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--reset-snapshot":
            reset_snapshot = True
            i += 1
            continue
        if arg == "--no-initialize-snapshot":
            initialize_snapshot = False
            i += 1
            continue
        if arg in {
            "--auth-mode",
            "--auth-env-var",
            "--sdk-module",
            "--cwd",
            "--model",
            "--max-turns",
            "--permission-request-policy",
            "--snapshot-path",
            "--event-log-path",
            "--evidence-id",
            "--evidence-path",
            "--projection-output-path",
            "--host-invocation-id",
            "--reason",
            "--timestamp",
        }:
            if i + 1 >= len(args):
                print(_QODER_SMOKE_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--auth-mode":
                auth_mode = value
            elif arg == "--auth-env-var":
                auth_env_var = value
            elif arg == "--sdk-module":
                sdk_module_name = value
            elif arg == "--cwd":
                cwd = value
            elif arg == "--model":
                model = value
            elif arg == "--max-turns":
                try:
                    max_turns = int(value)
                except ValueError:
                    print(_QODER_SMOKE_USAGE, file=sys.stderr)
                    print("--max-turns must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--permission-request-policy":
                permission_request_policy = value
            elif arg == "--snapshot-path":
                snapshot_path = value
            elif arg == "--event-log-path":
                event_log_path = value
            elif arg == "--evidence-id":
                evidence_id = value
            elif arg == "--evidence-path":
                evidence_path = value
            elif arg == "--projection-output-path":
                projection_output_path = value
            elif arg == "--host-invocation-id":
                host_invocation_id = value
            elif arg == "--reason":
                reason = value
            elif arg == "--timestamp":
                timestamp = value
            i += 2
            continue
        print(f"Unknown qoder smoke option: {arg}", file=sys.stderr)
        print(_QODER_SMOKE_USAGE, file=sys.stderr)
        return 1

    if auth_mode not in {"env", "qodercli"}:
        print("qoder smoke --auth-mode must be env or qodercli", file=sys.stderr)
        return 1
    if permission_request_policy not in {"deny", "surface"}:
        print(
            "qoder smoke --permission-request-policy must be deny or surface",
            file=sys.stderr,
        )
        return 1
    if max_turns is not None and max_turns < 1:
        print("qoder smoke --max-turns must be positive", file=sys.stderr)
        return 1

    root = _find_project_root()
    try:
        from .runtime.orchestration import (
            DEFAULT_QODER_TOKEN_ENV,
            QoderSDKQueryClientConfig,
        )
        from tools.progress_graph import (
            HostOwnedQoderSmokeRunConfig,
            QoderSmokeTaskConfig,
            run_host_owned_qoder_smoke,
        )

        qoder_config = QoderSDKQueryClientConfig(
            cwd=cwd,
            model=model,
            max_turns=max_turns,
            auth_mode=auth_mode,  # type: ignore[arg-type]
            auth_env_var=auth_env_var or DEFAULT_QODER_TOKEN_ENV,
            permission_request_policy=permission_request_policy,  # type: ignore[arg-type]
            sdk_module_name=sdk_module_name or "qoder_agent_sdk",
        )
        if max_turns is None:
            task = QoderSmokeTaskConfig(model=model)
        else:
            task = QoderSmokeTaskConfig(model=model, max_turns=max_turns)
        config = HostOwnedQoderSmokeRunConfig(
            evidence_id=evidence_id or "qoder-smoke",
            timestamp=timestamp,
            snapshot_path=snapshot_path or ".dbc/scheduler/qoder-smoke-state.json",
            event_log_path=event_log_path or ".dbc/scheduler/qoder-smoke-events.jsonl",
            evidence_output_path=evidence_path or None,
            projection_output_path=projection_output_path or None,
            initialize_snapshot=initialize_snapshot,
            reset_snapshot=reset_snapshot,
            task=task,
            qoder_client_config=qoder_config,
            host_invocation_id=host_invocation_id or "host-owned-qoder-smoke-cli",
            requested_by="cli:qoder-smoke",
            reason=reason or "host-owned Qoder SDK smoke run from CLI",
            grant_id=f"grant-{host_invocation_id or 'host-owned-qoder-smoke-cli'}",
            approved_by="cli:qoder-smoke",
            approved_at=timestamp,
            guide_context="doc-based-coding qoder smoke",
        )
        result = run_host_owned_qoder_smoke(root, config=config)
    except Exception as e:
        return _handle_error("Error running Qoder smoke", e, category="qoder_smoke_failed")

    _print_json(result.to_json_dict())
    return 0


def cmd_qoder_guide_worker_smoke(args: list[str]) -> int:
    """Run host-owned Qoder guide-worker provider execution through CLI."""

    if args and args[0] in ("-h", "--help"):
        print(
            _QODER_GUIDE_WORKER_SMOKE_USAGE + "\n\n"
            "This command is a host-owned live-provider guide-worker smoke "
            "surface. It delegates to "
            "run_host_owned_guide_worker_provider_execution(), uses explicit "
            "host-authorized adapter wiring and a Qoder permission grant, and "
            "never accepts a raw token value. If SDK/auth readiness is missing, "
            "it fails before evidence writes. It is not an MCP real-provider "
            "execution surface and does not mutate agent-owned Local Work "
            "Trajectory. Runtime invocations are audited to compact JSONL by "
            "default and retry retryable provider failures. Git-worktree "
            "worker changes are exported as review-only worker patch artifacts "
            "and merge candidates; they are not applied automatically.",
        )
        return 0

    auth_mode = "env"
    auth_env_var = ""
    sdk_module_name = ""
    cwd = ""
    model = ""
    max_turns: int | None = None
    permission_request_policy = "deny"
    artifact_store_path = ""
    admission_ledger_path = ""
    snapshot_path = ""
    event_log_path = ""
    evidence_id = ""
    evidence_path = ""
    git_worktree_sandbox_root = ""
    sandbox_allocation_evidence_id = ""
    sandbox_allocation_evidence_path = ""
    host_invocation_id = ""
    reason = ""
    runtime_invocation_log_path = ".dbc/runtime/invocations.jsonl"
    runtime_invocation_max_attempts = 2
    runtime_invocation_backoff_seconds = 0.0
    guide_task_title = ""
    guide_task_summary = ""
    planner_lane_specs: list[str] = []
    max_parallel_lanes = 2
    max_waves = 1
    wave_execution_mode = "threaded"
    timestamp = ""

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {
            "--auth-mode",
            "--auth-env-var",
            "--sdk-module",
            "--cwd",
            "--model",
            "--max-turns",
            "--permission-request-policy",
            "--artifact-store-path",
            "--admission-ledger-path",
            "--snapshot-path",
            "--event-log-path",
            "--evidence-id",
            "--evidence-path",
            "--git-worktree-sandbox-root",
            "--sandbox-allocation-evidence-id",
            "--sandbox-allocation-evidence-path",
            "--host-invocation-id",
            "--reason",
            "--runtime-invocation-log-path",
            "--runtime-invocation-max-attempts",
            "--runtime-invocation-backoff-seconds",
            "--guide-task-title",
            "--guide-task-summary",
            "--planner-lane",
            "--max-parallel-lanes",
            "--max-waves",
            "--wave-execution-mode",
            "--timestamp",
        }:
            if i + 1 >= len(args):
                print(_QODER_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--auth-mode":
                auth_mode = value
            elif arg == "--auth-env-var":
                auth_env_var = value
            elif arg == "--sdk-module":
                sdk_module_name = value
            elif arg == "--cwd":
                cwd = value
            elif arg == "--model":
                model = value
            elif arg == "--max-turns":
                try:
                    max_turns = int(value)
                except ValueError:
                    print(_QODER_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
                    print("--max-turns must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--permission-request-policy":
                permission_request_policy = value
            elif arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--admission-ledger-path":
                admission_ledger_path = value
            elif arg == "--snapshot-path":
                snapshot_path = value
            elif arg == "--event-log-path":
                event_log_path = value
            elif arg == "--evidence-id":
                evidence_id = value
            elif arg == "--evidence-path":
                evidence_path = value
            elif arg == "--git-worktree-sandbox-root":
                git_worktree_sandbox_root = value
            elif arg == "--sandbox-allocation-evidence-id":
                sandbox_allocation_evidence_id = value
            elif arg == "--sandbox-allocation-evidence-path":
                sandbox_allocation_evidence_path = value
            elif arg == "--host-invocation-id":
                host_invocation_id = value
            elif arg == "--reason":
                reason = value
            elif arg == "--runtime-invocation-log-path":
                runtime_invocation_log_path = value
            elif arg == "--runtime-invocation-max-attempts":
                try:
                    runtime_invocation_max_attempts = int(value)
                except ValueError:
                    print(_QODER_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
                    print("--runtime-invocation-max-attempts must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--runtime-invocation-backoff-seconds":
                try:
                    runtime_invocation_backoff_seconds = float(value)
                except ValueError:
                    print(_QODER_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
                    print("--runtime-invocation-backoff-seconds must be a number", file=sys.stderr)
                    return 1
            elif arg == "--guide-task-title":
                guide_task_title = value
            elif arg == "--guide-task-summary":
                guide_task_summary = value
            elif arg == "--planner-lane":
                planner_lane_specs.append(value)
            elif arg == "--max-parallel-lanes":
                try:
                    max_parallel_lanes = int(value)
                except ValueError:
                    print(_QODER_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
                    print("--max-parallel-lanes must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--max-waves":
                try:
                    max_waves = int(value)
                except ValueError:
                    print(_QODER_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
                    print("--max-waves must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--wave-execution-mode":
                wave_execution_mode = value
            elif arg == "--timestamp":
                timestamp = value
            i += 2
            continue
        print(f"Unknown qoder guide-worker-smoke option: {arg}", file=sys.stderr)
        print(_QODER_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
        return 1

    if auth_mode not in {"env", "qodercli"}:
        print("qoder guide-worker-smoke --auth-mode must be env or qodercli", file=sys.stderr)
        return 1
    if permission_request_policy not in {"deny", "surface"}:
        print(
            "qoder guide-worker-smoke --permission-request-policy must be deny or surface",
            file=sys.stderr,
        )
        return 1
    if max_turns is not None and max_turns < 1:
        print("qoder guide-worker-smoke --max-turns must be positive", file=sys.stderr)
        return 1
    if max_parallel_lanes < 1:
        print("qoder guide-worker-smoke --max-parallel-lanes must be positive", file=sys.stderr)
        return 1
    if max_waves < 1:
        print("qoder guide-worker-smoke --max-waves must be positive", file=sys.stderr)
        return 1
    if runtime_invocation_max_attempts < 1:
        print("qoder guide-worker-smoke --runtime-invocation-max-attempts must be positive", file=sys.stderr)
        return 1
    if runtime_invocation_backoff_seconds < 0:
        print(
            "qoder guide-worker-smoke --runtime-invocation-backoff-seconds must be non-negative",
            file=sys.stderr,
        )
        return 1
    if wave_execution_mode not in {"serial", "threaded"}:
        print(
            "qoder guide-worker-smoke --wave-execution-mode must be serial or threaded",
            file=sys.stderr,
        )
        return 1

    root = _find_project_root()
    try:
        from .runtime.orchestration import (
            DEFAULT_QODER_TOKEN_ENV,
            GuideWorkerPlannerLaneSpec,
            GuideWorkerPlanningRequest,
            QoderSDKQueryClientConfig,
        )
        from tools.progress_graph import (
            HostOwnedGuideWorkerProviderExecutionConfig,
            run_host_owned_guide_worker_provider_execution,
        )

        qoder_config = QoderSDKQueryClientConfig(
            cwd=cwd,
            model=model,
            max_turns=max_turns,
            auth_mode=auth_mode,  # type: ignore[arg-type]
            auth_env_var=auth_env_var or DEFAULT_QODER_TOKEN_ENV,
            permission_request_policy=permission_request_policy,  # type: ignore[arg-type]
            sdk_module_name=sdk_module_name or "qoder_agent_sdk",
        )
        planning_request = GuideWorkerPlanningRequest(
            task_title=guide_task_title,
            task_summary=guide_task_summary,
            lane_specs=tuple(
                _parse_guide_worker_planner_lane_spec(
                    item,
                    GuideWorkerPlannerLaneSpec,
                )
                for item in planner_lane_specs
            ),
        )
        config_kwargs = {
            "evidence_id": evidence_id or "guide-worker-provider-execution",
            "timestamp": timestamp,
            "artifact_store_path": artifact_store_path or ".dbc/orchestration/exchange-artifacts.json",
            "admission_ledger_path": (
                admission_ledger_path
                or ".dbc/orchestration/exchange-artifact-admissions.json"
            ),
            "snapshot_path": (
                snapshot_path
                or ".dbc/scheduler/guide-worker-provider-execution-state.json"
            ),
            "event_log_path": (
                event_log_path
                or ".dbc/scheduler/guide-worker-provider-execution-events.jsonl"
            ),
            "evidence_output_path": evidence_path or None,
            "workspace_root": str(root),
            "git_worktree_sandbox_root": git_worktree_sandbox_root or None,
            "sandbox_allocation_evidence_id": sandbox_allocation_evidence_id,
            "sandbox_allocation_evidence_path": sandbox_allocation_evidence_path or None,
            "qoder_client_config": qoder_config,
            "host_invocation_id": (
                host_invocation_id
                or "host-owned-guide-worker-provider-execution-cli"
            ),
            "requested_by": "cli:qoder-guide-worker-smoke",
            "reason": reason or "host-owned Qoder guide-worker smoke run from CLI",
            "runtime_invocation_log_path": runtime_invocation_log_path or None,
            "runtime_invocation_max_attempts": runtime_invocation_max_attempts,
            "runtime_invocation_backoff_seconds": runtime_invocation_backoff_seconds,
            "grant_id": (
                f"grant-{host_invocation_id}"
                if host_invocation_id
                else "grant-host-owned-guide-worker-provider-execution-cli"
            ),
            "approved_by": "cli:qoder-guide-worker-smoke",
            "approved_at": timestamp,
            "planning_request": planning_request,
            "max_parallel_lanes": max_parallel_lanes,
            "max_waves": max_waves,
            "wave_execution_mode": wave_execution_mode,
        }
        if planner_lane_specs:
            config_kwargs["worker_instructions"] = ()
            config_kwargs["planner_worker_runtime_provider"] = "qoder"
        config = HostOwnedGuideWorkerProviderExecutionConfig(**config_kwargs)
        result = run_host_owned_guide_worker_provider_execution(root, config=config)
    except Exception as e:
        return _handle_error(
            "Error running Qoder guide-worker smoke",
            e,
            category="qoder_guide_worker_smoke_failed",
        )

    _print_json(result.to_json_dict())
    return 0 if result.orchestration.ok else 1


def cmd_provider(args: list[str]) -> int:
    """Mixed runtime-provider host helper subcommands."""
    if not args or args[0] in ("-h", "--help"):
        print(
            "Usage: doc-based-coding provider <subcommand> [args]\n\n"
            "Mixed runtime provider host helpers.\n\n"
            "Subcommands:\n"
            "  guide-worker-smoke [--providers codex,opencode]\n"
            "      Run host-owned mixed-provider guide-worker lane-wave execution\n",
        )
        return 0

    sub = args[0]
    if sub == "guide-worker-smoke":
        return cmd_provider_guide_worker_smoke(args[1:])

    print(f"Unknown provider subcommand: {sub}", file=sys.stderr)
    print("Usage: doc-based-coding provider <guide-worker-smoke> [args]", file=sys.stderr)
    return 1


def cmd_provider_guide_worker_smoke(args: list[str]) -> int:
    """Run host-owned mixed-provider guide-worker execution through CLI."""

    if args and args[0] in ("-h", "--help"):
        print(
            _PROVIDER_GUIDE_WORKER_SMOKE_USAGE + "\n\n"
            "This command is a host-owned mixed-provider guide-worker smoke "
            "surface. It defaults to providers=codex,opencode and lets "
            "--planner-lane-provider assign a provider per lane. It delegates "
            "to run_host_owned_guide_worker_provider_execution(), uses explicit "
            "host-authorized adapter wiring and provider grants, is not an MCP "
            "real-provider execution surface, does not persist raw transcripts, "
            "and does not mutate agent-owned Local Work Trajectory.",
        )
        return 0

    providers_text = "codex,opencode"
    codex_executable = "codex"
    codex_cwd = ""
    codex_model = ""
    codex_sandbox = "workspace-write"
    codex_ask_for_approval = "never"
    opencode_executable = "opencode"
    opencode_cwd = ""
    opencode_model = ""
    opencode_output_format = "json"
    opencode_attach_url = ""
    opencode_session_id = ""
    opencode_continue_session = False
    opencode_fork_session = False
    artifact_store_path = ""
    admission_ledger_path = ""
    snapshot_path = ""
    event_log_path = ""
    evidence_id = ""
    evidence_path = ""
    git_worktree_sandbox_root = ""
    sandbox_allocation_evidence_id = ""
    sandbox_allocation_evidence_path = ""
    host_invocation_id = ""
    reason = ""
    runtime_invocation_log_path = ".dbc/runtime/invocations.jsonl"
    runtime_invocation_max_attempts = 2
    runtime_invocation_backoff_seconds = 0.0
    guide_task_title = ""
    guide_task_summary = ""
    planner_lane_specs: list[str] = []
    planner_lane_providers: list[str] = []
    max_parallel_lanes = 2
    max_waves = 1
    wave_execution_mode = "threaded"
    timestamp = ""

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {
            "--providers",
            "--codex-executable",
            "--codex-cwd",
            "--codex-model",
            "--codex-sandbox",
            "--codex-ask-for-approval",
            "--opencode-executable",
            "--opencode-cwd",
            "--opencode-model",
            "--opencode-output-format",
            "--opencode-attach-url",
            "--opencode-session-id",
            "--artifact-store-path",
            "--admission-ledger-path",
            "--snapshot-path",
            "--event-log-path",
            "--evidence-id",
            "--evidence-path",
            "--git-worktree-sandbox-root",
            "--sandbox-allocation-evidence-id",
            "--sandbox-allocation-evidence-path",
            "--host-invocation-id",
            "--reason",
            "--runtime-invocation-log-path",
            "--runtime-invocation-max-attempts",
            "--runtime-invocation-backoff-seconds",
            "--guide-task-title",
            "--guide-task-summary",
            "--planner-lane",
            "--planner-lane-provider",
            "--max-parallel-lanes",
            "--max-waves",
            "--wave-execution-mode",
            "--timestamp",
        }:
            if i + 1 >= len(args):
                print(_PROVIDER_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--providers":
                providers_text = value
            elif arg == "--codex-executable":
                codex_executable = value
            elif arg == "--codex-cwd":
                codex_cwd = value
            elif arg == "--codex-model":
                codex_model = value
            elif arg == "--codex-sandbox":
                codex_sandbox = value
            elif arg == "--codex-ask-for-approval":
                codex_ask_for_approval = value
            elif arg == "--opencode-executable":
                opencode_executable = value
            elif arg == "--opencode-cwd":
                opencode_cwd = value
            elif arg == "--opencode-model":
                opencode_model = value
            elif arg == "--opencode-output-format":
                opencode_output_format = value
            elif arg == "--opencode-attach-url":
                opencode_attach_url = value
            elif arg == "--opencode-session-id":
                opencode_session_id = value
            elif arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--admission-ledger-path":
                admission_ledger_path = value
            elif arg == "--snapshot-path":
                snapshot_path = value
            elif arg == "--event-log-path":
                event_log_path = value
            elif arg == "--evidence-id":
                evidence_id = value
            elif arg == "--evidence-path":
                evidence_path = value
            elif arg == "--git-worktree-sandbox-root":
                git_worktree_sandbox_root = value
            elif arg == "--sandbox-allocation-evidence-id":
                sandbox_allocation_evidence_id = value
            elif arg == "--sandbox-allocation-evidence-path":
                sandbox_allocation_evidence_path = value
            elif arg == "--host-invocation-id":
                host_invocation_id = value
            elif arg == "--reason":
                reason = value
            elif arg == "--runtime-invocation-log-path":
                runtime_invocation_log_path = value
            elif arg == "--runtime-invocation-max-attempts":
                try:
                    runtime_invocation_max_attempts = int(value)
                except ValueError:
                    print(_PROVIDER_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
                    print("--runtime-invocation-max-attempts must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--runtime-invocation-backoff-seconds":
                try:
                    runtime_invocation_backoff_seconds = float(value)
                except ValueError:
                    print(_PROVIDER_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
                    print("--runtime-invocation-backoff-seconds must be a number", file=sys.stderr)
                    return 1
            elif arg == "--guide-task-title":
                guide_task_title = value
            elif arg == "--guide-task-summary":
                guide_task_summary = value
            elif arg == "--planner-lane":
                planner_lane_specs.append(value)
            elif arg == "--planner-lane-provider":
                planner_lane_providers.append(value)
            elif arg == "--max-parallel-lanes":
                try:
                    max_parallel_lanes = int(value)
                except ValueError:
                    print(_PROVIDER_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
                    print("--max-parallel-lanes must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--max-waves":
                try:
                    max_waves = int(value)
                except ValueError:
                    print(_PROVIDER_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
                    print("--max-waves must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--wave-execution-mode":
                wave_execution_mode = value
            elif arg == "--timestamp":
                timestamp = value
            i += 2
            continue
        if arg == "--opencode-continue-session":
            opencode_continue_session = True
            i += 1
            continue
        if arg == "--opencode-fork-session":
            opencode_fork_session = True
            i += 1
            continue
        print(f"Unknown provider guide-worker-smoke option: {arg}", file=sys.stderr)
        print(_PROVIDER_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
        return 1

    try:
        providers = _parse_runtime_provider_csv(providers_text)
        lane_provider_map = _parse_planner_lane_provider_overrides(
            planner_lane_providers,
            providers=providers,
        )
    except ValueError as exc:
        print(_PROVIDER_GUIDE_WORKER_SMOKE_USAGE, file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    if "codex" not in providers or "opencode" not in providers:
        print(
            "provider guide-worker-smoke currently requires default mixed providers codex and opencode",
            file=sys.stderr,
        )
        return 1
    if codex_sandbox not in {"read-only", "workspace-write", "danger-full-access"}:
        print(
            "provider guide-worker-smoke --codex-sandbox must be read-only, workspace-write, or danger-full-access",
            file=sys.stderr,
        )
        return 1
    if codex_ask_for_approval not in {"untrusted", "on-request", "never"}:
        print(
            "provider guide-worker-smoke --codex-ask-for-approval must be untrusted, on-request, or never",
            file=sys.stderr,
        )
        return 1
    if opencode_output_format not in {"text", "json"}:
        print(
            "provider guide-worker-smoke --opencode-output-format must be text or json",
            file=sys.stderr,
        )
        return 1
    if opencode_session_id and opencode_continue_session:
        print(
            "provider guide-worker-smoke cannot use --opencode-session-id with --opencode-continue-session",
            file=sys.stderr,
        )
        return 1
    if opencode_fork_session and not (opencode_session_id or opencode_continue_session):
        print(
            "provider guide-worker-smoke --opencode-fork-session requires --opencode-session-id or --opencode-continue-session",
            file=sys.stderr,
        )
        return 1
    if max_parallel_lanes < 1:
        print("provider guide-worker-smoke --max-parallel-lanes must be positive", file=sys.stderr)
        return 1
    if max_waves < 1:
        print("provider guide-worker-smoke --max-waves must be positive", file=sys.stderr)
        return 1
    if runtime_invocation_max_attempts < 1:
        print("provider guide-worker-smoke --runtime-invocation-max-attempts must be positive", file=sys.stderr)
        return 1
    if runtime_invocation_backoff_seconds < 0:
        print(
            "provider guide-worker-smoke --runtime-invocation-backoff-seconds must be non-negative",
            file=sys.stderr,
        )
        return 1
    if wave_execution_mode not in {"serial", "threaded"}:
        print(
            "provider guide-worker-smoke --wave-execution-mode must be serial or threaded",
            file=sys.stderr,
        )
        return 1

    root = _find_project_root()
    try:
        from .runtime.orchestration import (
            CodexCliClientConfig,
            GuideWorkerPlannerLaneSpec,
            GuideWorkerPlanningRequest,
            OpenCodeCliClientConfig,
        )
        from tools.progress_graph import (
            HostOwnedGuideWorkerProviderExecutionConfig,
            run_host_owned_guide_worker_provider_execution,
        )

        parsed_lane_specs = [
            _parse_guide_worker_planner_lane_spec(item, GuideWorkerPlannerLaneSpec)
            for item in planner_lane_specs
        ]
        if not parsed_lane_specs:
            parsed_lane_specs = [
                GuideWorkerPlannerLaneSpec(
                    lane_id="lane:codex",
                    label="Codex lane",
                    focus="Codex worker validates backend/runtime changes",
                    worker_runtime_provider="codex",
                ),
                GuideWorkerPlannerLaneSpec(
                    lane_id="lane:opencode",
                    label="OpenCode lane",
                    focus="OpenCode worker validates frontend/integration changes",
                    worker_runtime_provider="opencode",
                ),
            ]
        parsed_lane_specs = _apply_lane_provider_overrides(
            parsed_lane_specs,
            lane_provider_map,
        )
        planning_request = GuideWorkerPlanningRequest(
            task_title=guide_task_title,
            task_summary=guide_task_summary,
            lane_specs=tuple(parsed_lane_specs),
        )
        codex_config = CodexCliClientConfig(
            executable=codex_executable,
            cwd=codex_cwd,
            model=codex_model,
            sandbox=codex_sandbox,  # type: ignore[arg-type]
            ask_for_approval=codex_ask_for_approval,  # type: ignore[arg-type]
        )
        opencode_config = OpenCodeCliClientConfig(
            executable=opencode_executable,
            cwd=opencode_cwd,
            model=opencode_model,
            output_format=opencode_output_format,  # type: ignore[arg-type]
            attach_url=opencode_attach_url,
            session_id=opencode_session_id,
            continue_session=opencode_continue_session,
            fork_session=opencode_fork_session,
        )
        host_id = host_invocation_id or "host-owned-mixed-provider-guide-worker-smoke-cli"
        config = HostOwnedGuideWorkerProviderExecutionConfig(
            evidence_id=evidence_id or "mixed-provider-guide-worker-smoke",
            timestamp=timestamp,
            artifact_store_path=artifact_store_path or ".dbc/orchestration/exchange-artifacts.json",
            admission_ledger_path=(
                admission_ledger_path
                or ".dbc/orchestration/exchange-artifact-admissions.json"
            ),
            snapshot_path=(
                snapshot_path
                or ".dbc/scheduler/mixed-provider-guide-worker-smoke-state.json"
            ),
            event_log_path=(
                event_log_path
                or ".dbc/scheduler/mixed-provider-guide-worker-smoke-events.jsonl"
            ),
            evidence_output_path=evidence_path or None,
            workspace_root=str(root),
            git_worktree_sandbox_root=git_worktree_sandbox_root or None,
            sandbox_allocation_evidence_id=sandbox_allocation_evidence_id,
            sandbox_allocation_evidence_path=sandbox_allocation_evidence_path or None,
            providers=providers,
            codex_cli_client_config=codex_config,
            opencode_cli_client_config=opencode_config,
            host_invocation_id=host_id,
            requested_by="cli:provider-guide-worker-smoke",
            reason=reason or "host-owned mixed-provider guide-worker smoke run from CLI",
            runtime_invocation_log_path=runtime_invocation_log_path or None,
            runtime_invocation_max_attempts=runtime_invocation_max_attempts,
            runtime_invocation_backoff_seconds=runtime_invocation_backoff_seconds,
            grant_id=f"grant-{host_id}",
            approved_by="cli:provider-guide-worker-smoke",
            approved_at=timestamp,
            planning_request=planning_request,
            worker_instructions=(),
            max_parallel_lanes=max_parallel_lanes,
            max_waves=max_waves,
            wave_execution_mode=wave_execution_mode,
        )
        result = run_host_owned_guide_worker_provider_execution(root, config=config)
    except Exception as e:
        return _handle_error(
            "Error running mixed-provider guide-worker smoke",
            e,
            category="provider_guide_worker_smoke_failed",
        )

    _print_json(result.to_json_dict())
    return 0 if result.orchestration.ok else 1


_SCHEDULER_ADMIT_USAGE = (
    "Usage: doc-based-coding scheduler admit-exchange-artifact "
    "--artifact-id ID --version VERSION --snapshot-path PATH --event-log-path PATH "
    "[--artifact-store-path PATH] [--admission-ledger-path PATH] "
    "[--allow-duplicate-admission] [--actor ACTOR] [--replace-existing] "
    "[--mark-consumed-on-success] [--timestamp TIMESTAMP]"
)

_SCHEDULER_INSPECT_ADMISSIONS_USAGE = (
    "Usage: doc-based-coding scheduler inspect-admissions "
    "[--admission-ledger-path PATH] [--artifact-id ID] [--version VERSION]"
)

_SCHEDULER_INSPECT_BINDING_REFS_USAGE = (
    "Usage: doc-based-coding scheduler inspect-binding-refs "
    "--artifact-id ID --version VERSION [--artifact-store-path PATH]"
)

_SCHEDULER_INSPECT_AGENT_MAILBOX_USAGE = (
    "Usage: doc-based-coding scheduler inspect-agent-mailbox "
    "--agent-id ID [--artifact-store-path PATH] [--include-archived]"
)

_SCHEDULER_INSPECT_AGENT_HISTORY_USAGE = (
    "Usage: doc-based-coding scheduler inspect-agent-history "
    "[--agent-id ID] [--correlation-id ID] [--artifact-store-path PATH] "
    "[--include-archived]"
)

_SCHEDULER_INSPECT_RUNTIME_INVOCATIONS_USAGE = (
    "Usage: doc-based-coding scheduler inspect-runtime-invocations "
    "[--path PATH] [--latest-limit N]"
)

_SCHEDULER_INSPECT_LEADER_WORKER_ACTIVATION_USAGE = (
    "Usage: doc-based-coding scheduler inspect-leader-worker-activation "
    "--snapshot-path PATH [--artifact-store-path PATH] [--leader-agent-id AGENT] "
    "[--worker-agent-id AGENT]..."
)

_SCHEDULER_LEADER_WORKER_DISPATCHER_TICK_USAGE = (
    "Usage: doc-based-coding scheduler leader-worker-dispatcher-tick "
    "--snapshot-path PATH --event-log-path PATH [--artifact-store-path PATH] "
    "[--dispatcher-state-path PATH] [--dispatch-event-log-path PATH] "
    "[--dispatcher-id ID] [--trajectory-id ID] [--leader-agent-id AGENT] "
    "[--worker-agent-id AGENT]... [--timestamp TIMESTAMP]"
)

_SCHEDULER_LEADER_WORKER_DISPATCHER_LOOP_USAGE = (
    "Usage: doc-based-coding scheduler leader-worker-dispatcher-loop "
    "--snapshot-path PATH --event-log-path PATH [--artifact-store-path PATH] "
    "[--dispatcher-state-path PATH] [--dispatch-event-log-path PATH] "
    "[--dispatcher-id ID] [--trajectory-id ID] [--leader-agent-id AGENT] "
    "[--worker-agent-id AGENT]... [--max-ticks N] [--timestamp TIMESTAMP]"
)

_SCHEDULER_LEADER_WORKER_DELIVERY_SYNC_USAGE = (
    "Usage: doc-based-coding scheduler leader-worker-delivery-sync "
    "--dispatch-event-log-path PATH [--delivery-state-path PATH] "
    "[--delivery-event-log-path PATH] [--delivery-id ID] [--dispatcher-id ID] "
    "[--host-id ID] [--timestamp TIMESTAMP]"
)

_SCHEDULER_LEADER_WORKER_DELIVERY_ACK_USAGE = (
    "Usage: doc-based-coding scheduler leader-worker-delivery-ack "
    "--target-state delivered|acknowledged|failed "
    "(--source-key KEY | --delivery-record-id ID) "
    "[--delivery-state-path PATH] [--delivery-event-log-path PATH] "
    "[--host-id ID] [--runtime-provider PROVIDER] "
    "[--runtime-session-id ID] [--runtime-run-id ID] [--invocation-id ID] "
    "[--failure-kind KIND] [--failure-detail TEXT] [--timestamp TIMESTAMP]"
)

_SCHEDULER_INSPECT_LEADER_WORKER_DELIVERY_USAGE = (
    "Usage: doc-based-coding scheduler inspect-leader-worker-delivery "
    "[--delivery-state-path PATH] [--latest-limit N]"
)

_SCHEDULER_INSPECT_CODEX_RUNTIME_STATUS_USAGE = (
    "Usage: doc-based-coding scheduler inspect-codex-runtime-status "
    "--snapshot-path PATH --event-log-path PATH "
    "[--delivery-state-path PATH] [--runtime-invocation-log-path PATH] "
    "[--artifact-store-path PATH] [--target-task-id ID]... [--latest-limit N]"
)

_SCHEDULER_INSPECT_OPENCODE_RUNTIME_STATUS_USAGE = (
    "Usage: doc-based-coding scheduler inspect-opencode-runtime-status "
    "--snapshot-path PATH --event-log-path PATH "
    "[--delivery-state-path PATH] [--runtime-invocation-log-path PATH] "
    "[--artifact-store-path PATH] [--target-task-id ID]... [--latest-limit N]"
)

_SCHEDULER_INSPECT_MONITORING_SNAPSHOT_USAGE = (
    "Usage: doc-based-coding scheduler inspect-monitoring-snapshot "
    "--snapshot-path PATH --event-log-path PATH "
    "[--delivery-state-path PATH] [--runtime-invocation-log-path PATH] "
    "[--artifact-store-path PATH] [--live-codex-smoke-report-path PATH] "
    "[--target-task-id ID]... [--latest-limit N]"
)

_SCHEDULER_CONSUME_WORKER_TRAJECTORY_REPORT_USAGE = (
    "Usage: doc-based-coding scheduler consume-worker-trajectory-report "
    "--report-path PATH [--caller-role leader|main|supervisor|guide] "
    "[--actor ACTOR] [--current-event-id ID] [--title TITLE] "
    "[--event-kind task|review|validation|writeback|wait|decision|handoff|close] "
    "[--no-start-if-missing] [--trajectory-title TITLE] [--guide-context LABEL]"
)

_SCHEDULER_TRAJECTORY_TEAM_USAGE = (
    "Usage: doc-based-coding scheduler trajectory-team "
    "<inspect|resolve|assign|activate|suspend|resume|transfer|fork|release|noContinuity> "
    "[--trajectory-id ID] [--lane-id ID] [--leader-id ID] [--worker-id ID] "
    "[--caller-role leader|main|supervisor|guide|worker|subagent|lane_worker|bounded_worker] "
    "[--runtime-provider fake|qoder|codex|opencode] [--binding-id ID] "
    "[--ownership-id ID] [--replacement-binding-id ID] [--new-binding-id ID] "
    "[--source-binding-id ID] [--no-continuity-reason REASON] "
    "[--task-id ID] [--delivery-id ID] [--reason TEXT] [--timestamp TIMESTAMP] "
    "[--binding-ledger-path PATH] [--binding-event-log-path PATH] "
    "[--ownership-ledger-path PATH] [--ownership-event-log-path PATH] "
    "[--lease-ledger-path PATH] [--team-event-log-path PATH] "
    "[--scheduler-event-log-path PATH] [--attach-url URL] [--session-id ID] "
    "[--continue-session] [--fork-session] [--compact-context-ref REF] "
    "[--mailbox-cursor-ref REF] [--worker-report-ref REF]... [--audit-ref REF]... "
    "[--active-only]"
)

_SCHEDULER_CODEX_DELIVERY_SUPERVISOR_USAGE = (
    "Usage: doc-based-coding scheduler codex-delivery-supervisor-once "
    "--snapshot-path PATH --event-log-path PATH "
    "[--delivery-state-path PATH] [--delivery-event-log-path PATH] "
    "[--runtime-invocation-log-path PATH] [--artifact-store-path PATH] "
    "[--consume-success-results] [--replace-existing-result-artifact] "
    "[--max-deliveries N] [--retry-failed-delivery] "
    "[--max-delivery-attempts-per-record N] "
    "[--enable-sandbox-preflight] [--workspace-root PATH] "
    "[--scratch-root PATH] [--git-worktree-sandbox-root PATH] "
    "[--git-executable PATH] [--publish-worker-patch-artifacts] "
    "[--worker-patch-guide-agent-id ID] [--worker-patch-target-task-id ID] "
    "[--executable PATH] [--cwd PATH] [--model MODEL] "
    "[--sandbox read-only|workspace-write|danger-full-access] "
    "[--ask-for-approval untrusted|on-request|never] "
    "[--host-id ID] [--host-invocation-id ID] [--reason TEXT] "
    "[--timestamp TIMESTAMP] [--runtime-invocation-max-attempts N] "
    "[--runtime-invocation-backoff-seconds N]"
)

_SCHEDULER_OPENCODE_DELIVERY_SUPERVISOR_USAGE = (
    "Usage: doc-based-coding scheduler opencode-delivery-supervisor-once "
    "--snapshot-path PATH --event-log-path PATH "
    "[--delivery-state-path PATH] [--delivery-event-log-path PATH] "
    "[--runtime-invocation-log-path PATH] [--artifact-store-path PATH] "
    "[--consume-success-results] [--replace-existing-result-artifact] "
    "[--max-deliveries N] [--retry-failed-delivery] "
    "[--max-delivery-attempts-per-record N] "
    "[--enable-sandbox-preflight] [--workspace-root PATH] "
    "[--scratch-root PATH] [--git-worktree-sandbox-root PATH] "
    "[--git-executable PATH] [--publish-worker-patch-artifacts] "
    "[--worker-patch-guide-agent-id ID] [--worker-patch-target-task-id ID] "
    "[--opencode-transport cli|server-api] "
    "[--executable PATH] [--cwd PATH] [--model MODEL] "
    "[--output-format text|json] "
    "[--attach-url URL] [--session-id ID] [--continue-session] [--fork-session] "
    "[--server-api-base-url URL] [--server-api-session-id ID] "
    "[--server-api-health-path PATH] [--server-api-doc-path PATH] "
    "[--server-api-timeout-seconds N] "
    "[--server-api-username-env-var NAME] [--server-api-password-env-var NAME] "
    "[--worker-binding-ledger-path PATH] [--worker-binding-event-log-path PATH] "
    "[--no-worker-binding-lookup] "
    "[--session-ledger-path PATH] [--no-session-ledger-lookup] "
    "[--host-id ID] [--host-invocation-id ID] [--reason TEXT] "
    "[--timestamp TIMESTAMP] [--runtime-invocation-max-attempts N] "
    "[--runtime-invocation-backoff-seconds N]"
)

_SCHEDULER_CODEX_DELIVERY_E2E_SMOKE_USAGE = (
    "Usage: doc-based-coding scheduler codex-delivery-e2e-smoke "
    "[--snapshot-path PATH] [--event-log-path PATH] "
    "[--artifact-store-path PATH] [--dispatcher-state-path PATH] "
    "[--dispatch-event-log-path PATH] [--delivery-state-path PATH] "
    "[--delivery-event-log-path PATH] [--runtime-invocation-log-path PATH] "
    "[--initialize-fixture] [--replace-existing-fixture] "
    "[--fixture simple|multilane] "
    "[--replace-existing-result-artifact] "
    "[--target-task-id ID] [--waiting-task-id ID] "
    "[--executable PATH] [--cwd PATH] [--model MODEL] "
    "[--sandbox read-only|workspace-write|danger-full-access] "
    "[--ask-for-approval untrusted|on-request|never] "
    "[--host-id ID] [--host-invocation-id ID] [--timestamp TIMESTAMP] "
    "[--runtime-invocation-max-attempts N] "
    "[--runtime-invocation-backoff-seconds N]"
)

_SCHEDULER_OPENCODE_DELIVERY_E2E_SMOKE_USAGE = (
    "Usage: doc-based-coding scheduler opencode-delivery-e2e-smoke "
    "[--snapshot-path PATH] [--event-log-path PATH] "
    "[--artifact-store-path PATH] [--dispatcher-state-path PATH] "
    "[--dispatch-event-log-path PATH] [--delivery-state-path PATH] "
    "[--delivery-event-log-path PATH] [--runtime-invocation-log-path PATH] "
    "[--initialize-fixture] [--replace-existing-fixture] "
    "[--fixture simple|multilane] "
    "[--replace-existing-result-artifact] "
    "[--target-task-id ID] [--waiting-task-id ID] "
    "[--executable PATH] [--cwd PATH] [--model MODEL] "
    "[--output-format text|json] "
    "[--opencode-transport cli|server-api] "
    "[--attach-url URL] [--session-id ID] [--continue-session] [--fork-session] "
    "[--server-api-base-url URL] [--server-api-session-id ID] "
    "[--server-api-health-path PATH] [--server-api-doc-path PATH] "
    "[--server-api-timeout-seconds N] "
    "[--server-api-username-env-var NAME] [--server-api-password-env-var NAME] "
    "[--worker-binding-ledger-path PATH] [--worker-binding-event-log-path PATH] "
    "[--no-worker-binding-lookup] "
    "[--session-ledger-path PATH] [--no-session-ledger-lookup] "
    "[--host-id ID] [--host-invocation-id ID] [--timestamp TIMESTAMP] "
    "[--runtime-invocation-max-attempts N] "
    "[--runtime-invocation-backoff-seconds N]"
)

_SCHEDULER_CODEX_DELIVERY_SUPERVISOR_LOOP_USAGE = (
    "Usage: doc-based-coding scheduler codex-delivery-supervisor-loop "
    "[--snapshot-path PATH] [--event-log-path PATH] "
    "[--artifact-store-path PATH] [--dispatcher-state-path PATH] "
    "[--dispatch-event-log-path PATH] [--delivery-state-path PATH] "
    "[--delivery-event-log-path PATH] [--runtime-invocation-log-path PATH] "
    "[--initialize-fixture] [--replace-existing-fixture] "
    "[--fixture simple|multilane] "
    "[--replace-existing-result-artifact] "
    "[--max-ticks N] [--max-deliveries N] [--max-runtime-failures N] "
    "[--max-delivery-attempts-per-record N] [--max-concurrent-deliveries N] "
    "[--enable-sandbox-preflight] [--workspace-root PATH] "
    "[--scratch-root PATH] [--git-worktree-sandbox-root PATH] "
    "[--git-executable PATH] [--publish-worker-patch-artifacts] "
    "[--worker-patch-guide-agent-id ID] [--worker-patch-target-task-id ID] "
    "[--target-task-id ID] [--parallel-task-id ID] "
    "[--waiting-task-id ID] [--followup-task-id ID] "
    "[--executable PATH] [--cwd PATH] [--model MODEL] "
    "[--sandbox read-only|workspace-write|danger-full-access] "
    "[--ask-for-approval untrusted|on-request|never] "
    "[--host-id ID] [--host-invocation-id ID] [--timestamp TIMESTAMP] "
    "[--runtime-invocation-max-attempts N] "
    "[--runtime-invocation-backoff-seconds N]"
)

_SCHEDULER_OPENCODE_DELIVERY_SUPERVISOR_LOOP_USAGE = (
    "Usage: doc-based-coding scheduler opencode-delivery-supervisor-loop "
    "[--snapshot-path PATH] [--event-log-path PATH] "
    "[--artifact-store-path PATH] [--dispatcher-state-path PATH] "
    "[--dispatch-event-log-path PATH] [--delivery-state-path PATH] "
    "[--delivery-event-log-path PATH] [--runtime-invocation-log-path PATH] "
    "[--initialize-fixture] [--replace-existing-fixture] "
    "[--fixture simple|multilane] "
    "[--replace-existing-result-artifact] "
    "[--max-ticks N] [--max-deliveries N] [--max-runtime-failures N] "
    "[--max-delivery-attempts-per-record N] [--max-concurrent-deliveries N] "
    "[--enable-sandbox-preflight] [--workspace-root PATH] "
    "[--scratch-root PATH] [--git-worktree-sandbox-root PATH] "
    "[--git-executable PATH] [--publish-worker-patch-artifacts] "
    "[--worker-patch-guide-agent-id ID] [--worker-patch-target-task-id ID] "
    "[--target-task-id ID] [--parallel-task-id ID] "
    "[--waiting-task-id ID] [--followup-task-id ID] "
    "[--executable PATH] [--cwd PATH] [--model MODEL] "
    "[--output-format text|json] "
    "[--opencode-transport cli|server-api] "
    "[--attach-url URL] [--session-id ID] [--continue-session] [--fork-session] "
    "[--server-api-base-url URL] [--server-api-session-id ID] "
    "[--server-api-health-path PATH] [--server-api-doc-path PATH] "
    "[--server-api-timeout-seconds N] "
    "[--server-api-username-env-var NAME] [--server-api-password-env-var NAME] "
    "[--worker-binding-ledger-path PATH] [--worker-binding-event-log-path PATH] "
    "[--no-worker-binding-lookup] "
    "[--session-ledger-path PATH] [--no-session-ledger-lookup] "
    "[--host-id ID] [--host-invocation-id ID] [--timestamp TIMESTAMP] "
    "[--runtime-invocation-max-attempts N] "
    "[--runtime-invocation-backoff-seconds N]"
)

_SCHEDULER_LIVE_CODEX_CONCURRENT_WORKER_SMOKE_USAGE = (
    "Usage: doc-based-coding scheduler live-codex-concurrent-worker-smoke "
    "[--snapshot-path PATH] [--event-log-path PATH] "
    "[--artifact-store-path PATH] [--dispatcher-state-path PATH] "
    "[--dispatch-event-log-path PATH] [--delivery-state-path PATH] "
    "[--delivery-event-log-path PATH] [--runtime-invocation-log-path PATH] "
    "[--initialize-fixture] [--replace-existing-fixture] "
    "[--fixture multilane] [--report-path PATH] "
    "[--replace-existing-result-artifact] "
    "[--max-ticks N] [--max-deliveries N] [--max-runtime-failures N] "
    "[--max-delivery-attempts-per-record N] [--max-concurrent-deliveries N] "
    "[--enable-sandbox-preflight] [--workspace-root PATH] "
    "[--scratch-root PATH] [--git-worktree-sandbox-root PATH] "
    "[--git-executable PATH] [--publish-worker-patch-artifacts] "
    "[--worker-patch-guide-agent-id ID] [--worker-patch-target-task-id ID] "
    "[--target-task-id ID] [--parallel-task-id ID] "
    "[--waiting-task-id ID] [--followup-task-id ID] "
    "[--executable PATH] [--cwd PATH] [--model MODEL] "
    "[--sandbox read-only|workspace-write|danger-full-access] "
    "[--ask-for-approval untrusted|on-request|never] "
    "[--host-id ID] [--host-invocation-id ID] [--timestamp TIMESTAMP] "
    "[--runtime-invocation-max-attempts N] "
    "[--runtime-invocation-backoff-seconds N]"
)

_SCHEDULER_LIVE_OPENCODE_CONCURRENT_WORKER_SMOKE_USAGE = (
    "Usage: doc-based-coding scheduler live-opencode-concurrent-worker-smoke "
    "[--snapshot-path PATH] [--event-log-path PATH] "
    "[--artifact-store-path PATH] [--dispatcher-state-path PATH] "
    "[--dispatch-event-log-path PATH] [--delivery-state-path PATH] "
    "[--delivery-event-log-path PATH] [--runtime-invocation-log-path PATH] "
    "[--initialize-fixture] [--replace-existing-fixture] "
    "[--fixture multilane] [--report-path PATH] "
    "[--replace-existing-result-artifact] "
    "[--max-ticks N] [--max-deliveries N] [--max-runtime-failures N] "
    "[--max-delivery-attempts-per-record N] [--max-concurrent-deliveries N] "
    "[--enable-sandbox-preflight] [--workspace-root PATH] "
    "[--scratch-root PATH] [--git-worktree-sandbox-root PATH] "
    "[--git-executable PATH] [--publish-worker-patch-artifacts] "
    "[--worker-patch-guide-agent-id ID] [--worker-patch-target-task-id ID] "
    "[--target-task-id ID] [--parallel-task-id ID] "
    "[--waiting-task-id ID] [--followup-task-id ID] "
    "[--executable PATH] [--cwd PATH] [--model MODEL] "
    "[--output-format text|json] "
    "[--attach-url URL] [--session-id ID] [--continue-session] [--fork-session] "
    "[--host-id ID] [--host-invocation-id ID] [--timestamp TIMESTAMP] "
    "[--runtime-invocation-max-attempts N] "
    "[--runtime-invocation-backoff-seconds N]"
)

_SCHEDULER_INSPECT_AGENT_ACTION_CANDIDATES_USAGE = (
    "Usage: doc-based-coding scheduler inspect-agent-action-candidates "
    "[--agent-id ID] [--candidate-type TYPE] [--artifact-store-path PATH] "
    "[--admission-ledger-path PATH] [--include-archived]"
)

_SCHEDULER_DECIDE_AGENT_ACTION_CANDIDATE_USAGE = (
    "Usage: doc-based-coding scheduler decide-agent-action-candidate "
    "--candidate-id ID --disposition-artifact-id ID --actor ID "
    "--disposition accept|reject|defer|supersede [--artifact-store-path PATH] "
    "[--disposition-version VERSION] [--reason TEXT] [--target-surface SURFACE] "
    "[--replacement-artifact-id ID] [--replacement-version VERSION] "
    "[--timestamp TIMESTAMP] [--replace-existing]"
)

_SCHEDULER_CONSUME_ACCEPTED_SCHEDULER_CANDIDATE_USAGE = (
    "Usage: doc-based-coding scheduler consume-accepted-scheduler-candidate "
    "--disposition-artifact-id ID --disposition-version VERSION "
    "--snapshot-path PATH --event-log-path PATH [--artifact-store-path PATH] "
    "[--admission-ledger-path PATH] [--allow-duplicate-admission] "
    "[--replace-existing] [--validate-binding-artifact-refs] "
    "[--mark-consumed-on-success] [--actor ACTOR] [--timestamp TIMESTAMP]"
)

_SCHEDULER_GUIDE_WORKER_EXCHANGE_DOGFOOD_USAGE = (
    "Usage: doc-based-coding scheduler guide-worker-exchange-dogfood "
    "[--artifact-store-path PATH] [--admission-ledger-path PATH] "
    "[--snapshot-path PATH] [--event-log-path PATH] "
    "[--guide-agent-id ID] [--worker-agent-id ID] [--artifact-id-prefix ID] "
    "[--timestamp TIMESTAMP] [--replace-existing] [--allow-duplicate-admission]"
)

_SCHEDULER_GUIDE_WORKER_LOCAL_ORCHESTRATION_USAGE = (
    "Usage: doc-based-coding scheduler guide-worker-local-orchestration "
    "[--artifact-store-path PATH] [--admission-ledger-path PATH] "
    "[--snapshot-path PATH] [--event-log-path PATH] [--trajectory-id ID] "
    "[--guide-agent-id ID] [--worker-agent-id ID] [--artifact-id-prefix ID] "
    "[--max-parallel-lanes N] [--max-waves N] [--timestamp TIMESTAMP] "
    "[--guide-task-title TEXT] [--guide-task-summary TEXT] "
    "[--planner-lane LANE_ID=LABEL:FOCUS] "
    "[--replace-existing] [--allow-duplicate-admission]"
)

_SCHEDULER_CONSUME_ACCEPTED_REVIEW_CANDIDATE_USAGE = (
    "Usage: doc-based-coding scheduler consume-accepted-review-candidate "
    "--disposition-artifact-id ID --disposition-version VERSION "
    "[--artifact-store-path PATH] [--actor ACTOR]"
)

_SCHEDULER_CONSUME_ACCEPTED_HANDOFF_CANDIDATE_USAGE = (
    "Usage: doc-based-coding scheduler consume-accepted-handoff-candidate "
    "--disposition-artifact-id ID --disposition-version VERSION --handoff-dir PATH "
    "[--artifact-store-path PATH] [--actor ACTOR]"
)

_SCHEDULER_CONSUME_ACCEPTED_MERGE_CANDIDATE_USAGE = (
    "Usage: doc-based-coding scheduler consume-accepted-merge-candidate "
    "--disposition-artifact-id ID --disposition-version VERSION "
    "--snapshot-path PATH --gate-id ID (--approved | --rejected) "
    "[--merge-gate-event-log-path PATH] [--artifact-store-path PATH] "
    "[--reason TEXT] [--actor ACTOR] [--resolved-at TIMESTAMP] [--timestamp TIMESTAMP]"
)

_SCHEDULER_CONSUME_WORKER_PATCH_REVIEW_USAGE = (
    "Usage: doc-based-coding scheduler consume-worker-patch-review "
    "--disposition-artifact-id ID --disposition-version VERSION "
    "--action check|apply|reject [--source-workspace-root PATH] "
    "[--artifact-store-path PATH] [--reason TEXT] [--actor ACTOR] "
    "[--timestamp TIMESTAMP] [--git-executable PATH]"
)

_SCHEDULER_REVIEW_WORKER_PATCH_USAGE = (
    "Usage: doc-based-coding scheduler review-worker-patch "
    "--candidate-id ID --action check|reject [--source-workspace-root PATH] "
    "[--artifact-store-path PATH] [--disposition-artifact-id ID] "
    "[--disposition-version VERSION] [--reason TEXT] [--actor ACTOR] "
    "[--timestamp TIMESTAMP] [--git-executable PATH]"
)

_SCHEDULER_PREFLIGHT_WORKER_PATCH_COMPOSITION_USAGE = (
    "Usage: doc-based-coding scheduler preflight-worker-patch-composition "
    "--patch-ref ARTIFACT_ID@VERSION --patch-ref ARTIFACT_ID@VERSION "
    "--source-workspace-root PATH [--artifact-store-path PATH] "
    "[--scratch-root PATH] [--git-executable PATH]"
)

_SCHEDULER_CONSUME_ACCEPTED_BLOCKER_CANDIDATE_USAGE = (
    "Usage: doc-based-coding scheduler consume-accepted-blocker-candidate "
    "--disposition-artifact-id ID --disposition-version VERSION "
    "--snapshot-path PATH --task-id ID --reason TEXT "
    "[--event-log-path PATH] [--artifact-store-path PATH] [--actor ACTOR] "
    "[--timestamp TIMESTAMP]"
)

_SCHEDULER_REPLY_EXCHANGE_ARTIFACT_USAGE = (
    "Usage: doc-based-coding scheduler reply-exchange-artifact "
    "--source-artifact-id ID --source-version VERSION --reply-artifact-id ID "
    "--producer ID (--text TEXT | --structured-json JSON) "
    "[--reply-version VERSION] [--artifact-store-path PATH] "
    "[--kind message|request|query|proposal|blocker|result|review|contract|handoff|retention|cleanup] "
    "[--intent ask|inform|propose|require_review|request_merge|declare_blocked|unblock|supersede|request_registration|request_retention] "
    "[--audience A[,B]] [--created-at TIMESTAMP] [--replace-existing]"
)

_SCHEDULER_TRANSITION_EXCHANGE_ARTIFACT_USAGE = (
    "Usage: doc-based-coding scheduler transition-exchange-artifact "
    "--artifact-id ID --version VERSION --target-state accepted|rejected|consumed|superseded|archived "
    "--actor ACTOR [--artifact-store-path PATH] [--reason TEXT] [--timestamp TIMESTAMP]"
)

_SCHEDULER_PUBLISH_STORAGE_BINDING_ARTIFACT_USAGE = (
    "Usage: doc-based-coding scheduler publish-storage-binding-artifact "
    "--evidence-path PATH [--artifact-store-path PATH] [--artifact-id ID] "
    "[--version VERSION] [--producer ID] [--audience A[,B]] "
    "[--created-at TIMESTAMP] [--replace-existing]"
)

_SCHEDULER_INSPECT_STATE_USAGE = (
    "Usage: doc-based-coding scheduler inspect-state --snapshot-path PATH "
    "[--event-log-path PATH] [--merge-gate-event-log-path PATH]"
)

_SCHEDULER_TICK_USAGE = (
    "Usage: doc-based-coding scheduler tick --snapshot-path PATH --event-log-path PATH "
    "[--max-runs N] [--runtime-provider fake] [--timestamp TIMESTAMP]"
)

_SCHEDULER_DAEMON_LOOP_USAGE = (
    "Usage: doc-based-coding scheduler daemon-loop --snapshot-path PATH --event-log-path PATH "
    "[--max-ticks N] [--max-runs-per-tick N] [--max-runtime-failures N] "
    "[--runtime-provider fake] [--timestamp TIMESTAMP] "
    "[--evidence-id ID] [--evidence-path PATH]"
)

_SCHEDULER_PROJECT_USAGE = (
    "Usage: doc-based-coding scheduler project --snapshot-path PATH "
    "[--event-log-path PATH] [--merge-gate-event-log-path PATH] [--output-path PATH] "
    "[--trajectory-id ID] [--title TITLE] [--guide-context PATH_OR_LABEL] "
    "[--source-graph-id ID] [--source-node-id ID]"
)

_SCHEDULER_SEED_DOGFOOD_FIXTURE_USAGE = (
    "Usage: doc-based-coding scheduler seed-dogfood-fixture "
    "[--fixture simple|multilane|binding-consumer] "
    "[--artifact-store-path PATH] [--artifact-id ID] [--version VERSION] "
    "[--replace-existing] [--created-at TIMESTAMP]"
)

_SCHEDULER_OPERATOR_WORKFLOW_USAGE = (
    "Usage: doc-based-coding scheduler operator-workflow "
    "[--artifact-id ID --version VERSION] [--inspect-binding-refs] "
    "[--admit] [--run-loop] [--refresh-projection] "
    "[--artifact-store-path PATH] [--admission-ledger-path PATH] "
    "[--snapshot-path PATH] [--event-log-path PATH] [--merge-gate-event-log-path PATH] "
    "[--projection-output-path PATH] [--evidence-id ID] [--evidence-path PATH] "
    "[--runtime-provider fake] [--max-ticks N] [--max-runs-per-tick N] "
    "[--max-runtime-failures N] [--allow-duplicate-admission] [--replace-existing] "
    "[--mark-consumed-on-success] [--actor ACTOR] [--timestamp TIMESTAMP] "
    "[--guide-context PATH_OR_LABEL] "
    "[--source-graph-id ID] [--source-node-id ID]"
)

_SCHEDULER_OPERATOR_DOGFOOD_CLOSURE_USAGE = (
    "Usage: doc-based-coding scheduler operator-dogfood-closure "
    "[--fixture binding-consumer|simple|multilane] [--artifact-id ID --version VERSION] "
    "[--artifact-store-path PATH] [--admission-ledger-path PATH] "
    "[--snapshot-path PATH] [--event-log-path PATH] [--merge-gate-event-log-path PATH] "
    "[--projection-output-path PATH] [--evidence-id ID] [--evidence-path PATH] "
    "[--runtime-provider fake] [--max-ticks N] [--max-runs-per-tick N] "
    "[--max-runtime-failures N] [--replace-existing] [--no-inspect-binding-refs] "
    "[--no-mark-consumed-on-success] [--actor ACTOR] [--timestamp TIMESTAMP] "
    "[--created-at TIMESTAMP] [--guide-context PATH_OR_LABEL] "
    "[--source-graph-id ID] [--source-node-id ID]"
)

_SCHEDULER_EVIDENCE_PUBLISH_CONSUMER_CLOSURE_USAGE = (
    "Usage: doc-based-coding scheduler evidence-publish-consumer-closure "
    "[--binding-evidence-id ID] [--binding-evidence-path PATH] "
    "[--binding-artifact-id ID] [--binding-artifact-version VERSION] "
    "[--consumer-artifact-id ID] [--consumer-version VERSION] "
    "[--artifact-store-path PATH] [--admission-ledger-path PATH] "
    "[--snapshot-path PATH] [--event-log-path PATH] [--merge-gate-event-log-path PATH] "
    "[--projection-output-path PATH] [--loop-evidence-id ID] [--loop-evidence-path PATH] "
    "[--runtime-provider fake] [--max-ticks N] [--max-runs-per-tick N] "
    "[--max-runtime-failures N] [--replace-existing] "
    "[--no-mark-consumed-on-success] [--actor ACTOR] [--timestamp TIMESTAMP] "
    "[--created-at TIMESTAMP] [--guide-context PATH_OR_LABEL] "
    "[--source-graph-id ID] [--source-node-id ID]"
)

_SCHEDULER_SUPERVISOR_DOGFOOD_WORKFLOW_USAGE = (
    "Usage: doc-based-coding scheduler supervisor-dogfood-workflow "
    "[--fixture simple|multilane] [--artifact-id ID --version VERSION] "
    "[--artifact-store-path PATH] [--admission-ledger-path PATH] "
    "[--snapshot-path PATH] [--event-log-path PATH] [--control-path PATH] "
    "[--runtime-provider fake] [--max-cycles N] [--max-loop-failures N] "
    "[--max-ticks N] [--max-runs-per-tick N] [--max-runtime-failures N] "
    "[--max-attempts N] [--retry-stop-reasons REASON[,REASON...]] "
    "[--allow-duplicate-admission] [--replace-existing] "
    "[--actor ACTOR] [--timestamp TIMESTAMP] [--created-at TIMESTAMP] "
    "[--daemon-id ID] [--lifecycle-run-id ID] [--supervisor-id ID] "
    "[--session-id ID] [--run-id ID] [--host-id ID] [--requested-by ACTOR] "
    "[--status-readback-at TIMESTAMP]"
)

_SCHEDULER_CLEANUP_RECEIPTS_USAGE = (
    "Usage: doc-based-coding scheduler cleanup-receipts "
    "--input-evidence-path PATH [--output-evidence-path PATH] "
    "[--output-evidence-id ID] [--timestamp TIMESTAMP] [--git-executable PATH]"
)

_SCHEDULER_SANDBOX_RECEIPT_WORKFLOW_USAGE = (
    "Usage: doc-based-coding scheduler sandbox-receipt-workflow "
    "--mode run-once|daemon-loop --snapshot-path PATH --event-log-path PATH "
    "--workspace-root PATH --git-worktree-sandbox-root PATH "
    "--allocation-evidence-id ID [--allocation-evidence-path PATH] "
    "[--cleanup] [--cleanup-evidence-id ID] [--cleanup-evidence-path PATH] "
    "[--runtime-provider fake] [--max-runs N] [--max-ticks N] "
    "[--max-runs-per-tick N] [--max-runtime-failures N] "
    "[--timestamp TIMESTAMP] [--git-executable PATH]"
)

_SCHEDULER_LIFECYCLE_USAGE = (
    "Usage: doc-based-coding scheduler lifecycle "
    "<inspect|start|heartbeat|pause|resume|cancel|shutdown|run-once|harness|supervisor-step> "
    "--control-path PATH [--snapshot-path PATH] [--event-log-path PATH] "
    "[--daemon-id ID] [--run-id ID] [--timestamp TIMESTAMP] "
    "[--stale-after-seconds N] [--now-epoch-seconds N] "
    "[--runtime-provider fake] [--max-ticks N] [--max-runs-per-tick N] "
    "[--max-runtime-failures N] [--max-cycles N] [--max-loop-failures N] "
    "[--policy-cancelled] [--deadline-epoch-seconds N] "
    "[--max-attempts N] [--retry-stop-reasons REASON[,REASON...]] "
    "[--supervisor-id ID] [--session-id ID] [--host-id ID] "
    "[--requested-by ACTOR] [--status-readback-at TIMESTAMP] "
    "[--cancellation-source SOURCE] [--cancellation-reason REASON]"
)


def _resolve_project_path(root: Path, value: str | Path) -> Path:
    """Resolve CLI paths relative to the detected project root."""

    path = Path(value)
    if path.is_absolute():
        return path
    return root / path


def cmd_scheduler(args: list[str]) -> int:
    """Scheduler operator helper subcommands."""
    if not args or args[0] in ("-h", "--help"):
        print(
            "Usage: doc-based-coding scheduler <subcommand> [args]\n\n"
            "Subcommands:\n"
            "  admit-exchange-artifact  Admit one exact stored ExchangeArtifact version into scheduler state\n"
            "  inspect-admissions       Read ExchangeArtifact admission ledger summary without mutation\n"
            "  inspect-binding-refs     Read supervisor storage binding refs in one stored scheduler submission\n"
            "  inspect-agent-mailbox    Read per-agent ExchangeArtifact inbox/outbox without mutation\n"
            "  inspect-agent-history    Read compact ExchangeArtifact communication history without mutation\n"
            "  inspect-runtime-invocations Read compact runtime invocation audit records without mutation\n"
            "  inspect-leader-worker-activation Project leader/worker activation state without mutation\n"
            "  leader-worker-dispatcher-tick Persist one activation dispatcher tick without running providers\n"
            "  leader-worker-dispatcher-loop Run bounded activation dispatcher ticks without running providers\n"
            "  leader-worker-delivery-sync Sync dispatcher decisions into host-owned delivery state\n"
            "  leader-worker-delivery-ack Record host/runtime delivery acknowledgement for one decision\n"
            "  inspect-leader-worker-delivery Read host-owned delivery acknowledgement state without mutation\n"
            "  inspect-codex-runtime-status Read compact Codex scheduler/delivery/runtime status without mutation\n"
            "  inspect-opencode-runtime-status Read compact OpenCode scheduler/delivery/runtime status without mutation\n"
            "  inspect-monitoring-snapshot Read frontend-oriented orchestration monitoring snapshot without mutation\n"
            "  consume-worker-trajectory-report Consume worker report trajectory_update as leader-owned trajectory mutation\n"
            "  trajectory-team       Inspect or mutate leader/operator trajectory team continuity roster\n"
            "  codex-delivery-supervisor-once Run one host-owned Codex pass over pending delivery records\n"
            "  opencode-delivery-supervisor-once Run one host-owned OpenCode pass over pending delivery records\n"
            "  codex-delivery-e2e-smoke Run C1 Codex delivery/result-consumer smoke\n"
            "  opencode-delivery-e2e-smoke Run C1 OpenCode delivery/result-consumer smoke\n"
            "  codex-delivery-supervisor-loop Run bounded C2 Codex supervisor loop\n"
            "  opencode-delivery-supervisor-loop Run bounded OpenCode supervisor loop\n"
            "  live-codex-concurrent-worker-smoke Run C9 live Codex concurrent worker evidence smoke\n"
            "  live-opencode-concurrent-worker-smoke Run live OpenCode concurrent worker evidence smoke\n"
            "  inspect-agent-action-candidates Read communication artifacts as action candidates without mutation\n"
            "  decide-agent-action-candidate Record an action-candidate disposition ExchangeArtifact\n"
            "  consume-accepted-scheduler-candidate Consume accepted scheduler candidate disposition via exact admission\n"
            "  consume-accepted-review-candidate Consume accepted review candidate disposition via review intake\n"
            "  consume-accepted-handoff-candidate Consume accepted handoff candidate disposition via handoff delivery\n"
            "  consume-accepted-merge-candidate Consume accepted merge candidate disposition via explicit merge gate resolution\n"
            "  consume-worker-patch-review Consume accepted worker patch proposal with explicit check/apply/reject\n"
            "  review-worker-patch  Create disposition and check/reject one worker patch candidate\n"
            "  preflight-worker-patch-composition Check multiple worker patch proposals in order without mutating source\n"
            "  consume-accepted-blocker-candidate Consume accepted blocker candidate disposition via explicit task blocking\n"
            "  guide-worker-exchange-dogfood Run deterministic guide/worker exchange product dogfood\n"
            "  guide-worker-local-orchestration Run guide-assigned worker tasks with lane-limited waves\n"
            "  reply-exchange-artifact  Create an exact-version reply ExchangeArtifact\n"
            "  transition-exchange-artifact Change one exact ExchangeArtifact lifecycle state\n"
            "  publish-storage-binding-artifact Publish compact supervisor storage binding evidence into ExchangeArtifact store\n"
            "  inspect-state            Read scheduler snapshot/event-log summary without mutation\n"
            "  tick                     Run one bounded fake-runtime scheduler tick without projection refresh\n"
            "  daemon-loop              Run a bounded fake-runtime scheduler loop without projection refresh\n"
            "  lifecycle                Read or mutate scheduler daemon lifecycle control state\n"
            "  project                  Refresh scheduler-derived trajectory projection without running providers\n"
            "  seed-dogfood-fixture     Seed one controlled ExchangeArtifact admission candidate\n"
            "  operator-workflow        Run shared explicit operator workflow with opt-in mutation steps\n"
            "  operator-dogfood-closure Seed and run deterministic operator evidence closure\n"
            "  evidence-publish-consumer-closure Publish durable binding evidence and run consumer closure\n"
            "  supervisor-dogfood-workflow Run deterministic fake supervisor dogfood sequence\n"
            "  cleanup-receipts         Explicitly clean git-worktree sandboxes from durable receipt evidence\n"
            "  sandbox-receipt-workflow Run host allocation/readback/cleanup/readback receipt workflow\n",
        )
        return 0

    sub = args[0]
    if sub == "admit-exchange-artifact":
        return cmd_scheduler_admit_exchange_artifact(args[1:])
    if sub == "inspect-admissions":
        return cmd_scheduler_inspect_admissions(args[1:])
    if sub == "inspect-binding-refs":
        return cmd_scheduler_inspect_binding_refs(args[1:])
    if sub == "inspect-agent-mailbox":
        return cmd_scheduler_inspect_agent_mailbox(args[1:])
    if sub == "inspect-agent-history":
        return cmd_scheduler_inspect_agent_history(args[1:])
    if sub == "inspect-runtime-invocations":
        return cmd_scheduler_inspect_runtime_invocations(args[1:])
    if sub == "inspect-leader-worker-activation":
        return cmd_scheduler_inspect_leader_worker_activation(args[1:])
    if sub == "leader-worker-dispatcher-tick":
        return cmd_scheduler_leader_worker_dispatcher_tick(args[1:])
    if sub == "leader-worker-dispatcher-loop":
        return cmd_scheduler_leader_worker_dispatcher_loop(args[1:])
    if sub == "leader-worker-delivery-sync":
        return cmd_scheduler_leader_worker_delivery_sync(args[1:])
    if sub == "leader-worker-delivery-ack":
        return cmd_scheduler_leader_worker_delivery_ack(args[1:])
    if sub == "inspect-leader-worker-delivery":
        return cmd_scheduler_inspect_leader_worker_delivery(args[1:])
    if sub == "inspect-codex-runtime-status":
        return cmd_scheduler_inspect_codex_runtime_status(args[1:])
    if sub == "inspect-opencode-runtime-status":
        return cmd_scheduler_inspect_opencode_runtime_status(args[1:])
    if sub == "inspect-monitoring-snapshot":
        return cmd_scheduler_inspect_monitoring_snapshot(args[1:])
    if sub == "consume-worker-trajectory-report":
        return cmd_scheduler_consume_worker_trajectory_report(args[1:])
    if sub == "trajectory-team":
        return cmd_scheduler_trajectory_team(args[1:])
    if sub == "codex-delivery-supervisor-once":
        return cmd_scheduler_codex_delivery_supervisor_once(args[1:])
    if sub == "opencode-delivery-supervisor-once":
        return cmd_scheduler_opencode_delivery_supervisor_once(args[1:])
    if sub == "codex-delivery-e2e-smoke":
        return cmd_scheduler_codex_delivery_e2e_smoke(args[1:])
    if sub == "opencode-delivery-e2e-smoke":
        return cmd_scheduler_opencode_delivery_e2e_smoke(args[1:])
    if sub == "codex-delivery-supervisor-loop":
        return cmd_scheduler_codex_delivery_supervisor_loop(args[1:])
    if sub == "opencode-delivery-supervisor-loop":
        return cmd_scheduler_opencode_delivery_supervisor_loop(args[1:])
    if sub == "live-codex-concurrent-worker-smoke":
        return cmd_scheduler_live_codex_concurrent_worker_smoke(args[1:])
    if sub == "live-opencode-concurrent-worker-smoke":
        return cmd_scheduler_live_opencode_concurrent_worker_smoke(args[1:])
    if sub == "inspect-agent-action-candidates":
        return cmd_scheduler_inspect_agent_action_candidates(args[1:])
    if sub == "decide-agent-action-candidate":
        return cmd_scheduler_decide_agent_action_candidate(args[1:])
    if sub == "consume-accepted-scheduler-candidate":
        return cmd_scheduler_consume_accepted_scheduler_candidate(args[1:])
    if sub == "consume-accepted-review-candidate":
        return cmd_scheduler_consume_accepted_review_candidate(args[1:])
    if sub == "consume-accepted-handoff-candidate":
        return cmd_scheduler_consume_accepted_handoff_candidate(args[1:])
    if sub == "consume-accepted-merge-candidate":
        return cmd_scheduler_consume_accepted_merge_candidate(args[1:])
    if sub == "consume-worker-patch-review":
        return cmd_scheduler_consume_worker_patch_review(args[1:])
    if sub == "review-worker-patch":
        return cmd_scheduler_review_worker_patch(args[1:])
    if sub == "preflight-worker-patch-composition":
        return cmd_scheduler_preflight_worker_patch_composition(args[1:])
    if sub == "consume-accepted-blocker-candidate":
        return cmd_scheduler_consume_accepted_blocker_candidate(args[1:])
    if sub == "guide-worker-exchange-dogfood":
        return cmd_scheduler_guide_worker_exchange_dogfood(args[1:])
    if sub == "guide-worker-local-orchestration":
        return cmd_scheduler_guide_worker_local_orchestration(args[1:])
    if sub == "reply-exchange-artifact":
        return cmd_scheduler_reply_exchange_artifact(args[1:])
    if sub == "transition-exchange-artifact":
        return cmd_scheduler_transition_exchange_artifact(args[1:])
    if sub == "publish-storage-binding-artifact":
        return cmd_scheduler_publish_storage_binding_artifact(args[1:])
    if sub == "inspect-state":
        return cmd_scheduler_inspect_state(args[1:])
    if sub == "tick":
        return cmd_scheduler_tick(args[1:])
    if sub == "daemon-loop":
        return cmd_scheduler_daemon_loop(args[1:])
    if sub == "lifecycle":
        return cmd_scheduler_lifecycle(args[1:])
    if sub == "project":
        return cmd_scheduler_project(args[1:])
    if sub == "seed-dogfood-fixture":
        return cmd_scheduler_seed_dogfood_fixture(args[1:])
    if sub == "operator-workflow":
        return cmd_scheduler_operator_workflow(args[1:])
    if sub == "operator-dogfood-closure":
        return cmd_scheduler_operator_dogfood_closure(args[1:])
    if sub == "evidence-publish-consumer-closure":
        return cmd_scheduler_evidence_publish_consumer_closure(args[1:])
    if sub == "supervisor-dogfood-workflow":
        return cmd_scheduler_supervisor_dogfood_workflow(args[1:])
    if sub == "cleanup-receipts":
        return cmd_scheduler_cleanup_receipts(args[1:])
    if sub == "sandbox-receipt-workflow":
        return cmd_scheduler_sandbox_receipt_workflow(args[1:])

    print(f"Unknown scheduler subcommand: {sub}", file=sys.stderr)
    print(
        "Usage: doc-based-coding scheduler <admit-exchange-artifact|inspect-admissions|inspect-binding-refs|inspect-agent-mailbox|inspect-agent-history|inspect-runtime-invocations|inspect-leader-worker-activation|leader-worker-dispatcher-tick|leader-worker-dispatcher-loop|leader-worker-delivery-sync|leader-worker-delivery-ack|inspect-leader-worker-delivery|inspect-codex-runtime-status|inspect-opencode-runtime-status|inspect-monitoring-snapshot|consume-worker-trajectory-report|trajectory-team|codex-delivery-supervisor-once|opencode-delivery-supervisor-once|codex-delivery-e2e-smoke|opencode-delivery-e2e-smoke|codex-delivery-supervisor-loop|opencode-delivery-supervisor-loop|live-codex-concurrent-worker-smoke|live-opencode-concurrent-worker-smoke|inspect-agent-action-candidates|decide-agent-action-candidate|consume-accepted-scheduler-candidate|consume-accepted-review-candidate|consume-accepted-handoff-candidate|consume-accepted-merge-candidate|consume-worker-patch-review|preflight-worker-patch-composition|consume-accepted-blocker-candidate|guide-worker-exchange-dogfood|guide-worker-local-orchestration|reply-exchange-artifact|transition-exchange-artifact|publish-storage-binding-artifact|inspect-state|tick|daemon-loop|lifecycle|project|seed-dogfood-fixture|operator-workflow|operator-dogfood-closure|evidence-publish-consumer-closure|supervisor-dogfood-workflow|cleanup-receipts|sandbox-receipt-workflow> [args]",
        file=sys.stderr,
    )
    return 1


def cmd_scheduler_admit_exchange_artifact(args: list[str]) -> int:
    """Admit one exact stored ExchangeArtifact version into scheduler state."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_ADMIT_USAGE + "\n\n"
            "This writes scheduler snapshot/event-log state and admission ledger state. "
            "By default it does not run providers, refresh scheduler projection, mark "
            "exchange artifacts consumed, or mutate Local Work Trajectory. Pass "
            "--mark-consumed-on-success to mark the exact admitted artifact version "
            "consumed only after successful admission.",
        )
        return 0

    artifact_store_path = ""
    admission_ledger_path = ""
    artifact_id = ""
    version = ""
    snapshot_path = ""
    event_log_path = ""
    replace_existing = False
    allow_duplicate_admission = False
    mark_consumed_on_success = False
    actor = "operator-cli"
    timestamp = ""

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--replace-existing":
            replace_existing = True
            i += 1
            continue
        if arg == "--allow-duplicate-admission":
            allow_duplicate_admission = True
            i += 1
            continue
        if arg == "--mark-consumed-on-success":
            mark_consumed_on_success = True
            i += 1
            continue
        if arg in {
            "--artifact-store-path",
            "--admission-ledger-path",
            "--artifact-id",
            "--version",
            "--snapshot-path",
            "--event-log-path",
            "--actor",
            "--timestamp",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_ADMIT_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--admission-ledger-path":
                admission_ledger_path = value
            elif arg == "--artifact-id":
                artifact_id = value
            elif arg == "--version":
                version = value
            elif arg == "--snapshot-path":
                snapshot_path = value
            elif arg == "--event-log-path":
                event_log_path = value
            elif arg == "--actor":
                actor = value
            elif arg == "--timestamp":
                timestamp = value
            i += 2
            continue
        print(f"Unknown scheduler admit-exchange-artifact option: {arg}", file=sys.stderr)
        print(_SCHEDULER_ADMIT_USAGE, file=sys.stderr)
        return 1

    missing = [
        name
        for name, value in (
            ("--artifact-id", artifact_id),
            ("--version", version),
            ("--snapshot-path", snapshot_path),
            ("--event-log-path", event_log_path),
        )
        if not value
    ]
    if missing:
        print(_SCHEDULER_ADMIT_USAGE, file=sys.stderr)
        print(f"Missing required option(s): {', '.join(missing)}", file=sys.stderr)
        return 1

    root = _find_project_root()

    try:
        from .runtime.orchestration import (
            admit_exchange_artifact_version_with_ledger,
            default_exchange_artifact_admission_ledger_path,
            default_exchange_artifact_store_path,
        )

        store = (
            _resolve_project_path(root, artifact_store_path)
            if artifact_store_path
            else default_exchange_artifact_store_path(root)
        )
        ledger_path = (
            _resolve_project_path(root, admission_ledger_path)
            if admission_ledger_path
            else default_exchange_artifact_admission_ledger_path(root)
        )
        snapshot = _resolve_project_path(root, snapshot_path)
        event_log = _resolve_project_path(root, event_log_path)
        payload = admit_exchange_artifact_version_with_ledger(
            artifact_store_path=store,
            artifact_id=artifact_id,
            version=version,
            snapshot_path=snapshot,
            event_log_path=event_log,
            admission_ledger_path=ledger_path,
            allow_duplicate_admission=allow_duplicate_admission,
            replace_existing=replace_existing,
            mark_consumed_on_success=mark_consumed_on_success,
            actor=actor,
            surface="cli:scheduler admit-exchange-artifact",
            timestamp=timestamp,
        )
    except Exception as e:
        return _handle_error(
            "Error admitting exchange artifact",
            e,
            category="scheduler_admission_failed",
        )

    _print_json(payload)
    if not payload.get("ok"):
        print(str(payload.get("error", "exchange artifact admission failed")), file=sys.stderr)
        return 1
    return 0


def cmd_scheduler_seed_dogfood_fixture(args: list[str]) -> int:
    """Seed one controlled ExchangeArtifact candidate for scheduler operator dogfood."""

    if args and args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_SEED_DOGFOOD_FIXTURE_USAGE + "\n\n"
            "This writes only a controlled ExchangeArtifact scheduler-admission candidate. "
            "The default fixture is simple; --fixture multilane writes a richer fake-runtime "
            "cross-lane candidate; --fixture binding-consumer writes a compact supervisor "
            "storage binding artifact and a scheduler submission that consumes it. It does "
            "not admit tasks, run providers, refresh scheduler projection, write raw binding "
            "evidence JSON, write Host Evidence, or mutate Local Work Trajectory.",
        )
        return 0

    fixture = "simple"
    artifact_store_path = ""
    artifact_id = ""
    version = ""
    created_at = ""
    replace_existing = False

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--replace-existing":
            replace_existing = True
            i += 1
            continue
        if arg in {
            "--artifact-store-path",
            "--artifact-id",
            "--version",
            "--created-at",
            "--fixture",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_SEED_DOGFOOD_FIXTURE_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--artifact-id":
                artifact_id = value
            elif arg == "--version":
                version = value
            elif arg == "--created-at":
                created_at = value
            elif arg == "--fixture":
                fixture = value
            i += 2
            continue
        print(f"Unknown scheduler seed-dogfood-fixture option: {arg}", file=sys.stderr)
        print(_SCHEDULER_SEED_DOGFOOD_FIXTURE_USAGE, file=sys.stderr)
        return 1

    root = _find_project_root()
    try:
        from .runtime.orchestration import (
            DEFAULT_SCHEDULER_OPERATOR_BINDING_CONSUMER_DOGFOOD_ARTIFACT_ID,
            DEFAULT_SCHEDULER_OPERATOR_BINDING_CONSUMER_DOGFOOD_VERSION,
            DEFAULT_SCHEDULER_OPERATOR_DOGFOOD_ARTIFACT_ID,
            DEFAULT_SCHEDULER_OPERATOR_DOGFOOD_VERSION,
            DEFAULT_SCHEDULER_OPERATOR_MULTILANE_DOGFOOD_ARTIFACT_ID,
            DEFAULT_SCHEDULER_OPERATOR_MULTILANE_DOGFOOD_VERSION,
            seed_scheduler_operator_binding_consumer_dogfood_fixture,
            seed_scheduler_operator_dogfood_fixture,
            seed_scheduler_operator_multilane_dogfood_fixture,
        )

        if fixture not in {"simple", "multilane", "binding-consumer"}:
            print(_SCHEDULER_SEED_DOGFOOD_FIXTURE_USAGE, file=sys.stderr)
            print(
                "--fixture must be simple, multilane, or binding-consumer",
                file=sys.stderr,
            )
            return 1
        target_store = (
            _resolve_project_path(root, artifact_store_path)
            if artifact_store_path
            else None
        )
        if fixture == "multilane":
            result = seed_scheduler_operator_multilane_dogfood_fixture(
                root,
                artifact_store_path=target_store,
                artifact_id=artifact_id
                or DEFAULT_SCHEDULER_OPERATOR_MULTILANE_DOGFOOD_ARTIFACT_ID,
                version=version or DEFAULT_SCHEDULER_OPERATOR_MULTILANE_DOGFOOD_VERSION,
                replace_existing=replace_existing,
                created_at=created_at or "2026-06-19T00:00:00+00:00",
            )
        elif fixture == "binding-consumer":
            result = seed_scheduler_operator_binding_consumer_dogfood_fixture(
                root,
                artifact_store_path=target_store,
                artifact_id=artifact_id
                or DEFAULT_SCHEDULER_OPERATOR_BINDING_CONSUMER_DOGFOOD_ARTIFACT_ID,
                version=version
                or DEFAULT_SCHEDULER_OPERATOR_BINDING_CONSUMER_DOGFOOD_VERSION,
                replace_existing=replace_existing,
                created_at=created_at or "2026-06-22T00:00:00+00:00",
            )
        else:
            result = seed_scheduler_operator_dogfood_fixture(
                root,
                artifact_store_path=target_store,
                artifact_id=artifact_id or DEFAULT_SCHEDULER_OPERATOR_DOGFOOD_ARTIFACT_ID,
                version=version or DEFAULT_SCHEDULER_OPERATOR_DOGFOOD_VERSION,
                replace_existing=replace_existing,
                created_at=created_at or "2026-06-19T00:00:00+00:00",
            )
    except Exception as e:
        return _handle_error(
            "Error seeding scheduler operator dogfood fixture",
            e,
            category="scheduler_fixture_failed",
        )

    _print_json(result.to_json_dict())
    return 0


def cmd_scheduler_operator_workflow(args: list[str]) -> int:
    """Run the shared explicit scheduler operator workflow."""

    if args and args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_OPERATOR_WORKFLOW_USAGE + "\n\n"
            "This is a shared host/operator workflow surface. It always inspects "
            "candidates and Host Evidence presentation. --inspect-binding-refs "
            "adds a read-only supervisor storage binding reference check before "
            "admission. Scheduler mutations are opt-in through --admit, "
            "--run-loop, and --refresh-projection. --mark-consumed-on-success "
            "marks the exact admitted ExchangeArtifact version consumed only "
            "after successful admission. It does not mutate agent-owned Local "
            "Work Trajectory.",
        )
        return 0

    artifact_id = ""
    version = ""
    artifact_store_path = ""
    admission_ledger_path = ""
    snapshot_path = ""
    event_log_path = ""
    merge_gate_event_log_path = ""
    projection_output_path = ""
    evidence_id = ""
    evidence_path = ""
    runtime_provider = "fake"
    actor = "operator-cli"
    timestamp = ""
    guide_context = ""
    source_graph_id = ""
    source_node_id = ""
    admit = False
    run_loop = False
    refresh_projection = False
    inspect_binding_refs = False
    allow_duplicate_admission = False
    replace_existing = False
    mark_consumed_on_success = False
    max_ticks = 3
    max_runs_per_tick: int | None = 1
    max_runtime_failures: int | None = 1

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--admit":
            admit = True
            i += 1
            continue
        if arg == "--inspect-binding-refs":
            inspect_binding_refs = True
            i += 1
            continue
        if arg == "--run-loop":
            run_loop = True
            i += 1
            continue
        if arg == "--refresh-projection":
            refresh_projection = True
            i += 1
            continue
        if arg == "--allow-duplicate-admission":
            allow_duplicate_admission = True
            i += 1
            continue
        if arg == "--replace-existing":
            replace_existing = True
            i += 1
            continue
        if arg == "--mark-consumed-on-success":
            mark_consumed_on_success = True
            i += 1
            continue
        if arg in {
            "--artifact-id",
            "--version",
            "--artifact-store-path",
            "--admission-ledger-path",
            "--snapshot-path",
            "--event-log-path",
            "--merge-gate-event-log-path",
            "--projection-output-path",
            "--evidence-id",
            "--evidence-path",
            "--runtime-provider",
            "--max-ticks",
            "--max-runs-per-tick",
            "--max-runtime-failures",
            "--actor",
            "--timestamp",
            "--guide-context",
            "--source-graph-id",
            "--source-node-id",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_OPERATOR_WORKFLOW_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--artifact-id":
                artifact_id = value
            elif arg == "--version":
                version = value
            elif arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--admission-ledger-path":
                admission_ledger_path = value
            elif arg == "--snapshot-path":
                snapshot_path = value
            elif arg == "--event-log-path":
                event_log_path = value
            elif arg == "--merge-gate-event-log-path":
                merge_gate_event_log_path = value
            elif arg == "--projection-output-path":
                projection_output_path = value
            elif arg == "--evidence-id":
                evidence_id = value
            elif arg == "--evidence-path":
                evidence_path = value
            elif arg == "--runtime-provider":
                runtime_provider = value
            elif arg == "--actor":
                actor = value
            elif arg == "--timestamp":
                timestamp = value
            elif arg == "--guide-context":
                guide_context = value
            elif arg == "--source-graph-id":
                source_graph_id = value
            elif arg == "--source-node-id":
                source_node_id = value
            elif arg == "--max-ticks":
                try:
                    max_ticks = int(value)
                except ValueError:
                    print(_SCHEDULER_OPERATOR_WORKFLOW_USAGE, file=sys.stderr)
                    print("--max-ticks must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--max-runs-per-tick":
                try:
                    max_runs_per_tick = int(value)
                except ValueError:
                    print(_SCHEDULER_OPERATOR_WORKFLOW_USAGE, file=sys.stderr)
                    print("--max-runs-per-tick must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--max-runtime-failures":
                try:
                    max_runtime_failures = int(value)
                except ValueError:
                    print(_SCHEDULER_OPERATOR_WORKFLOW_USAGE, file=sys.stderr)
                    print("--max-runtime-failures must be an integer", file=sys.stderr)
                    return 1
            i += 2
            continue
        print(f"Unknown scheduler operator-workflow option: {arg}", file=sys.stderr)
        print(_SCHEDULER_OPERATOR_WORKFLOW_USAGE, file=sys.stderr)
        return 1

    root = _find_project_root()
    try:
        from tools.progress_graph import (
            SchedulerOperatorWorkflowRequest,
            run_scheduler_operator_workflow,
        )

        result = run_scheduler_operator_workflow(
            SchedulerOperatorWorkflowRequest(
                project_root=root,
                artifact_id=artifact_id,
                version=version,
                admit=admit,
                run_loop=run_loop,
                refresh_projection=refresh_projection,
                inspect_binding_refs=inspect_binding_refs,
                artifact_store_path=artifact_store_path or None,
                admission_ledger_path=admission_ledger_path or None,
                snapshot_path=snapshot_path or None,
                event_log_path=event_log_path or None,
                merge_gate_event_log_path=merge_gate_event_log_path or None,
                projection_output_path=projection_output_path or None,
                evidence_id=evidence_id,
                evidence_path=evidence_path or None,
                runtime_provider=runtime_provider,
                max_ticks=max_ticks,
                max_runs_per_tick=max_runs_per_tick,
                max_runtime_failures=max_runtime_failures,
                allow_duplicate_admission=allow_duplicate_admission,
                replace_existing=replace_existing,
                mark_consumed_on_success=mark_consumed_on_success,
                actor=actor,
                timestamp=timestamp,
                guide_context=guide_context,
                source_graph_id=source_graph_id,
                source_node_id=source_node_id,
            )
        )
    except Exception as e:
        return _handle_error(
            "Error running scheduler operator workflow",
            e,
            category="scheduler_operator_workflow_failed",
        )

    payload = result.to_json_dict()
    _print_json(payload)
    return 0 if payload.get("ok") else 1


def cmd_scheduler_operator_dogfood_closure(args: list[str]) -> int:
    """Run deterministic fake-runtime operator dogfood execution closure."""

    if args and args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_OPERATOR_DOGFOOD_CLOSURE_USAGE + "\n\n"
            "This closure seeds a deterministic fixture, runs the shared Scheduler "
            "Operator workflow with explicit admit/run/project steps, reads Host "
            "Evidence presentation, and returns compact review facts. It is "
            "fake-runtime-only. It does not run live providers, start services, "
            "create agent home or scratch directories, run cleanup, add Host UX "
            "controls, or mutate agent-owned Local Work Trajectory.",
        )
        return 0

    fixture = "binding-consumer"
    artifact_id = ""
    version = ""
    artifact_store_path = ""
    admission_ledger_path = ""
    snapshot_path = ""
    event_log_path = ""
    merge_gate_event_log_path = ""
    projection_output_path = ""
    evidence_id = ""
    evidence_path = ""
    runtime_provider = "fake"
    max_ticks = 3
    max_runs_per_tick: int | None = 1
    max_runtime_failures: int | None = 1
    replace_existing = False
    inspect_binding_refs = True
    mark_consumed_on_success = True
    actor = "operator-cli"
    timestamp = ""
    created_at = ""
    guide_context = ""
    source_graph_id = ""
    source_node_id = ""

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--replace-existing":
            replace_existing = True
            i += 1
            continue
        if arg == "--no-inspect-binding-refs":
            inspect_binding_refs = False
            i += 1
            continue
        if arg == "--no-mark-consumed-on-success":
            mark_consumed_on_success = False
            i += 1
            continue
        if arg in {
            "--fixture",
            "--artifact-id",
            "--version",
            "--artifact-store-path",
            "--admission-ledger-path",
            "--snapshot-path",
            "--event-log-path",
            "--merge-gate-event-log-path",
            "--projection-output-path",
            "--evidence-id",
            "--evidence-path",
            "--runtime-provider",
            "--max-ticks",
            "--max-runs-per-tick",
            "--max-runtime-failures",
            "--actor",
            "--timestamp",
            "--created-at",
            "--guide-context",
            "--source-graph-id",
            "--source-node-id",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_OPERATOR_DOGFOOD_CLOSURE_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--fixture":
                fixture = value
            elif arg == "--artifact-id":
                artifact_id = value
            elif arg == "--version":
                version = value
            elif arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--admission-ledger-path":
                admission_ledger_path = value
            elif arg == "--snapshot-path":
                snapshot_path = value
            elif arg == "--event-log-path":
                event_log_path = value
            elif arg == "--merge-gate-event-log-path":
                merge_gate_event_log_path = value
            elif arg == "--projection-output-path":
                projection_output_path = value
            elif arg == "--evidence-id":
                evidence_id = value
            elif arg == "--evidence-path":
                evidence_path = value
            elif arg == "--runtime-provider":
                runtime_provider = value
            elif arg == "--actor":
                actor = value
            elif arg == "--timestamp":
                timestamp = value
            elif arg == "--created-at":
                created_at = value
            elif arg == "--guide-context":
                guide_context = value
            elif arg == "--source-graph-id":
                source_graph_id = value
            elif arg == "--source-node-id":
                source_node_id = value
            else:
                try:
                    parsed = int(value)
                except ValueError:
                    print(_SCHEDULER_OPERATOR_DOGFOOD_CLOSURE_USAGE, file=sys.stderr)
                    print(f"{arg} must be an integer", file=sys.stderr)
                    return 1
                if arg == "--max-ticks":
                    max_ticks = parsed
                elif arg == "--max-runs-per-tick":
                    max_runs_per_tick = parsed
                elif arg == "--max-runtime-failures":
                    max_runtime_failures = parsed
            i += 2
            continue
        print(f"Unknown scheduler operator-dogfood-closure option: {arg}", file=sys.stderr)
        print(_SCHEDULER_OPERATOR_DOGFOOD_CLOSURE_USAGE, file=sys.stderr)
        return 1

    if fixture not in {"binding-consumer", "simple", "multilane"}:
        print(_SCHEDULER_OPERATOR_DOGFOOD_CLOSURE_USAGE, file=sys.stderr)
        print("--fixture must be binding-consumer, simple, or multilane", file=sys.stderr)
        return 1
    if runtime_provider != "fake":
        print(
            "scheduler operator-dogfood-closure currently supports only "
            "--runtime-provider fake; real providers require a separate planning gate",
            file=sys.stderr,
        )
        return 1

    root = _find_project_root()
    try:
        from tools.progress_graph import (
            DEFAULT_OPERATOR_DOGFOOD_CLOSURE_EVIDENCE_ID,
            SchedulerOperatorDogfoodClosureRequest,
            run_scheduler_operator_dogfood_closure,
        )

        result = run_scheduler_operator_dogfood_closure(
            SchedulerOperatorDogfoodClosureRequest(
                project_root=root,
                fixture=fixture,  # type: ignore[arg-type]
                artifact_id=artifact_id,
                version=version,
                artifact_store_path=artifact_store_path or None,
                admission_ledger_path=admission_ledger_path or None,
                snapshot_path=snapshot_path or None,
                event_log_path=event_log_path or None,
                merge_gate_event_log_path=merge_gate_event_log_path or None,
                projection_output_path=projection_output_path or None,
                evidence_id=evidence_id or DEFAULT_OPERATOR_DOGFOOD_CLOSURE_EVIDENCE_ID,
                evidence_path=evidence_path or None,
                runtime_provider=runtime_provider,
                max_ticks=max_ticks,
                max_runs_per_tick=max_runs_per_tick,
                max_runtime_failures=max_runtime_failures,
                replace_existing=replace_existing,
                inspect_binding_refs=inspect_binding_refs,
                mark_consumed_on_success=mark_consumed_on_success,
                actor=actor,
                timestamp=timestamp,
                created_at=created_at,
                guide_context=guide_context,
                source_graph_id=source_graph_id,
                source_node_id=source_node_id,
            )
        )
    except Exception as e:
        return _handle_error(
            "Error running scheduler operator dogfood closure",
            e,
            category="scheduler_operator_dogfood_closure_failed",
        )

    payload = result.to_json_dict()
    _print_json(payload)
    return 0 if payload.get("ok") else 1


def cmd_scheduler_evidence_publish_consumer_closure(args: list[str]) -> int:
    """Run durable evidence publish into a fake-runtime consumer closure."""

    if args and args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_EVIDENCE_PUBLISH_CONSUMER_CLOSURE_USAGE + "\n\n"
            "This closure writes durable supervisor storage binding evidence, "
            "publishes it through the compact binding artifact publish surface, "
            "seeds a consumer scheduler submission that references that exact "
            "published artifact, then runs binding-ref inspection, exact admission, "
            "consume, bounded fake loop, projection refresh, and Host Evidence "
            "readback. It is fake-runtime-only. It does not create real agent home "
            "or scratch directories, write scratch manifests, run cleanup, add Host "
            "UX controls, or mutate agent-owned Local Work Trajectory.",
        )
        return 0

    artifact_store_path = ""
    admission_ledger_path = ""
    snapshot_path = ""
    event_log_path = ""
    merge_gate_event_log_path = ""
    projection_output_path = ""
    binding_evidence_id = ""
    binding_evidence_path = ""
    binding_artifact_id = ""
    binding_artifact_version = ""
    consumer_artifact_id = ""
    consumer_version = ""
    loop_evidence_id = ""
    loop_evidence_path = ""
    runtime_provider = "fake"
    max_ticks = 3
    max_runs_per_tick: int | None = 1
    max_runtime_failures: int | None = 1
    replace_existing = False
    mark_consumed_on_success = True
    actor = "evidence-publish-consumer-cli"
    timestamp = ""
    created_at = ""
    guide_context = ""
    source_graph_id = ""
    source_node_id = ""

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--replace-existing":
            replace_existing = True
            i += 1
            continue
        if arg == "--no-mark-consumed-on-success":
            mark_consumed_on_success = False
            i += 1
            continue
        if arg in {
            "--artifact-store-path",
            "--admission-ledger-path",
            "--snapshot-path",
            "--event-log-path",
            "--merge-gate-event-log-path",
            "--projection-output-path",
            "--binding-evidence-id",
            "--binding-evidence-path",
            "--binding-artifact-id",
            "--binding-artifact-version",
            "--consumer-artifact-id",
            "--consumer-version",
            "--loop-evidence-id",
            "--loop-evidence-path",
            "--runtime-provider",
            "--max-ticks",
            "--max-runs-per-tick",
            "--max-runtime-failures",
            "--actor",
            "--timestamp",
            "--created-at",
            "--guide-context",
            "--source-graph-id",
            "--source-node-id",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_EVIDENCE_PUBLISH_CONSUMER_CLOSURE_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--admission-ledger-path":
                admission_ledger_path = value
            elif arg == "--snapshot-path":
                snapshot_path = value
            elif arg == "--event-log-path":
                event_log_path = value
            elif arg == "--merge-gate-event-log-path":
                merge_gate_event_log_path = value
            elif arg == "--projection-output-path":
                projection_output_path = value
            elif arg == "--binding-evidence-id":
                binding_evidence_id = value
            elif arg == "--binding-evidence-path":
                binding_evidence_path = value
            elif arg == "--binding-artifact-id":
                binding_artifact_id = value
            elif arg == "--binding-artifact-version":
                binding_artifact_version = value
            elif arg == "--consumer-artifact-id":
                consumer_artifact_id = value
            elif arg == "--consumer-version":
                consumer_version = value
            elif arg == "--loop-evidence-id":
                loop_evidence_id = value
            elif arg == "--loop-evidence-path":
                loop_evidence_path = value
            elif arg == "--runtime-provider":
                runtime_provider = value
            elif arg == "--actor":
                actor = value
            elif arg == "--timestamp":
                timestamp = value
            elif arg == "--created-at":
                created_at = value
            elif arg == "--guide-context":
                guide_context = value
            elif arg == "--source-graph-id":
                source_graph_id = value
            elif arg == "--source-node-id":
                source_node_id = value
            else:
                try:
                    parsed = int(value)
                except ValueError:
                    print(_SCHEDULER_EVIDENCE_PUBLISH_CONSUMER_CLOSURE_USAGE, file=sys.stderr)
                    print(f"{arg} must be an integer", file=sys.stderr)
                    return 1
                if arg == "--max-ticks":
                    max_ticks = parsed
                elif arg == "--max-runs-per-tick":
                    max_runs_per_tick = parsed
                elif arg == "--max-runtime-failures":
                    max_runtime_failures = parsed
            i += 2
            continue
        print(
            f"Unknown scheduler evidence-publish-consumer-closure option: {arg}",
            file=sys.stderr,
        )
        print(_SCHEDULER_EVIDENCE_PUBLISH_CONSUMER_CLOSURE_USAGE, file=sys.stderr)
        return 1

    if runtime_provider != "fake":
        print(
            "scheduler evidence-publish-consumer-closure currently supports only "
            "--runtime-provider fake; real providers require a separate planning gate",
            file=sys.stderr,
        )
        return 1

    root = _find_project_root()
    try:
        from tools.progress_graph import (
            DEFAULT_EVIDENCE_PUBLISH_BINDING_ARTIFACT_ID,
            DEFAULT_EVIDENCE_PUBLISH_BINDING_ARTIFACT_VERSION,
            DEFAULT_EVIDENCE_PUBLISH_BINDING_EVIDENCE_ID,
            DEFAULT_EVIDENCE_PUBLISH_CONSUMER_ARTIFACT_ID,
            DEFAULT_EVIDENCE_PUBLISH_CONSUMER_VERSION,
            DEFAULT_EVIDENCE_PUBLISH_LOOP_EVIDENCE_ID,
            EvidencePublishToConsumerClosureRequest,
            run_evidence_publish_to_consumer_closure,
        )

        result = run_evidence_publish_to_consumer_closure(
            EvidencePublishToConsumerClosureRequest(
                project_root=root,
                artifact_store_path=artifact_store_path or None,
                admission_ledger_path=admission_ledger_path or None,
                snapshot_path=snapshot_path or None,
                event_log_path=event_log_path or None,
                merge_gate_event_log_path=merge_gate_event_log_path or None,
                projection_output_path=projection_output_path or None,
                binding_evidence_id=(
                    binding_evidence_id or DEFAULT_EVIDENCE_PUBLISH_BINDING_EVIDENCE_ID
                ),
                binding_evidence_path=binding_evidence_path or None,
                binding_artifact_id=(
                    binding_artifact_id or DEFAULT_EVIDENCE_PUBLISH_BINDING_ARTIFACT_ID
                ),
                binding_artifact_version=(
                    binding_artifact_version
                    or DEFAULT_EVIDENCE_PUBLISH_BINDING_ARTIFACT_VERSION
                ),
                consumer_artifact_id=(
                    consumer_artifact_id or DEFAULT_EVIDENCE_PUBLISH_CONSUMER_ARTIFACT_ID
                ),
                consumer_version=consumer_version or DEFAULT_EVIDENCE_PUBLISH_CONSUMER_VERSION,
                loop_evidence_id=loop_evidence_id or DEFAULT_EVIDENCE_PUBLISH_LOOP_EVIDENCE_ID,
                loop_evidence_path=loop_evidence_path or None,
                runtime_provider=runtime_provider,
                max_ticks=max_ticks,
                max_runs_per_tick=max_runs_per_tick,
                max_runtime_failures=max_runtime_failures,
                replace_existing=replace_existing,
                mark_consumed_on_success=mark_consumed_on_success,
                actor=actor,
                timestamp=timestamp,
                created_at=created_at,
                guide_context=guide_context,
                source_graph_id=source_graph_id,
                source_node_id=source_node_id,
            )
        )
    except Exception as e:
        return _handle_error(
            "Error running scheduler evidence publish consumer closure",
            e,
            category="scheduler_evidence_publish_consumer_closure_failed",
        )

    payload = result.to_json_dict()
    _print_json(payload)
    return 0 if payload.get("ok") else 1


def cmd_scheduler_supervisor_dogfood_workflow(args: list[str]) -> int:
    """Run deterministic fake-runtime supervisor dogfood workflow."""

    if args and args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_SUPERVISOR_DOGFOOD_WORKFLOW_USAGE + "\n\n"
            "This shared workflow seeds a deterministic fixture, admits it into "
            "scheduler state, starts lifecycle control, runs one host-managed "
            "supervisor step, and reads back final scheduler/supervisor facts. "
            "It is fake-runtime-only and does not refresh scheduler projection, "
            "run cleanup, start a service, or mutate agent-owned Local Work Trajectory.",
        )
        return 0

    fixture = "simple"
    artifact_id = ""
    version = ""
    artifact_store_path = ""
    admission_ledger_path = ""
    snapshot_path = ""
    event_log_path = ""
    control_path = ""
    runtime_provider = "fake"
    max_cycles = 1
    max_loop_failures: int | None = 1
    max_ticks = 3
    max_runs_per_tick: int | None = 1
    max_runtime_failures: int | None = 1
    max_attempts = 1
    retry_stop_reasons: tuple[str, ...] = ()
    allow_duplicate_admission = False
    replace_existing = False
    actor = "operator-cli"
    timestamp = ""
    created_at = ""
    daemon_id = ""
    lifecycle_run_id = ""
    supervisor_id = ""
    session_id = ""
    run_id = ""
    host_id = ""
    requested_by = ""
    status_readback_at = ""

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--allow-duplicate-admission":
            allow_duplicate_admission = True
            i += 1
            continue
        if arg == "--replace-existing":
            replace_existing = True
            i += 1
            continue
        if arg in {
            "--fixture",
            "--artifact-id",
            "--version",
            "--artifact-store-path",
            "--admission-ledger-path",
            "--snapshot-path",
            "--event-log-path",
            "--control-path",
            "--runtime-provider",
            "--max-cycles",
            "--max-loop-failures",
            "--max-ticks",
            "--max-runs-per-tick",
            "--max-runtime-failures",
            "--max-attempts",
            "--retry-stop-reasons",
            "--actor",
            "--timestamp",
            "--created-at",
            "--daemon-id",
            "--lifecycle-run-id",
            "--supervisor-id",
            "--session-id",
            "--run-id",
            "--host-id",
            "--requested-by",
            "--status-readback-at",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_SUPERVISOR_DOGFOOD_WORKFLOW_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--fixture":
                fixture = value
            elif arg == "--artifact-id":
                artifact_id = value
            elif arg == "--version":
                version = value
            elif arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--admission-ledger-path":
                admission_ledger_path = value
            elif arg == "--snapshot-path":
                snapshot_path = value
            elif arg == "--event-log-path":
                event_log_path = value
            elif arg == "--control-path":
                control_path = value
            elif arg == "--runtime-provider":
                runtime_provider = value
            elif arg == "--actor":
                actor = value
            elif arg == "--timestamp":
                timestamp = value
            elif arg == "--created-at":
                created_at = value
            elif arg == "--daemon-id":
                daemon_id = value
            elif arg == "--lifecycle-run-id":
                lifecycle_run_id = value
            elif arg == "--supervisor-id":
                supervisor_id = value
            elif arg == "--session-id":
                session_id = value
            elif arg == "--run-id":
                run_id = value
            elif arg == "--host-id":
                host_id = value
            elif arg == "--requested-by":
                requested_by = value
            elif arg == "--status-readback-at":
                status_readback_at = value
            elif arg == "--retry-stop-reasons":
                retry_stop_reasons = tuple(
                    item.strip()
                    for item in value.split(",")
                    if item.strip()
                )
            else:
                try:
                    parsed = int(value)
                except ValueError:
                    print(_SCHEDULER_SUPERVISOR_DOGFOOD_WORKFLOW_USAGE, file=sys.stderr)
                    print(f"{arg} must be an integer", file=sys.stderr)
                    return 1
                if arg == "--max-cycles":
                    max_cycles = parsed
                elif arg == "--max-loop-failures":
                    max_loop_failures = parsed
                elif arg == "--max-ticks":
                    max_ticks = parsed
                elif arg == "--max-runs-per-tick":
                    max_runs_per_tick = parsed
                elif arg == "--max-runtime-failures":
                    max_runtime_failures = parsed
                elif arg == "--max-attempts":
                    max_attempts = parsed
            i += 2
            continue
        print(f"Unknown scheduler supervisor-dogfood-workflow option: {arg}", file=sys.stderr)
        print(_SCHEDULER_SUPERVISOR_DOGFOOD_WORKFLOW_USAGE, file=sys.stderr)
        return 1

    if fixture not in {"simple", "multilane"}:
        print(_SCHEDULER_SUPERVISOR_DOGFOOD_WORKFLOW_USAGE, file=sys.stderr)
        print("--fixture must be simple or multilane", file=sys.stderr)
        return 1
    if runtime_provider != "fake":
        print(
            "scheduler supervisor-dogfood-workflow currently supports only "
            "--runtime-provider fake; real providers require host-owned injected runtime wiring",
            file=sys.stderr,
        )
        return 1

    root = _find_project_root()
    try:
        from tools.progress_graph import (
            SchedulerSupervisorDogfoodWorkflowRequest,
            run_scheduler_supervisor_dogfood_workflow,
        )

        result = run_scheduler_supervisor_dogfood_workflow(
            SchedulerSupervisorDogfoodWorkflowRequest(
                project_root=root,
                fixture=fixture,  # type: ignore[arg-type]
                artifact_id=artifact_id,
                version=version,
                artifact_store_path=artifact_store_path or None,
                admission_ledger_path=admission_ledger_path or None,
                snapshot_path=snapshot_path or None,
                event_log_path=event_log_path or None,
                control_path=control_path or None,
                runtime_provider=runtime_provider,
                max_cycles=max_cycles,
                max_loop_failures=max_loop_failures,
                max_ticks=max_ticks,
                max_runs_per_tick=max_runs_per_tick,
                max_runtime_failures=max_runtime_failures,
                max_attempts=max_attempts,
                retry_stop_reasons=retry_stop_reasons,
                allow_duplicate_admission=allow_duplicate_admission,
                replace_existing=replace_existing,
                actor=actor,
                timestamp=timestamp,
                created_at=created_at,
                daemon_id=daemon_id or "daemon:supervisor-dogfood",
                lifecycle_run_id=lifecycle_run_id or "lifecycle-run:supervisor-dogfood",
                supervisor_id=supervisor_id or "supervisor:dogfood",
                session_id=session_id,
                run_id=run_id or "supervisor-run:dogfood",
                host_id=host_id,
                requested_by=requested_by,
                status_readback_at=status_readback_at,
            )
        )
    except Exception as e:
        return _handle_error(
            "Error running scheduler supervisor dogfood workflow",
            e,
            category="scheduler_supervisor_dogfood_workflow_failed",
        )

    payload = result.to_json_dict()
    _print_json(payload)
    return 0 if payload.get("ok") else 1


def cmd_scheduler_cleanup_receipts(args: list[str]) -> int:
    """Explicitly clean git-worktree sandboxes from durable receipt evidence."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_CLEANUP_RECEIPTS_USAGE + "\n\n"
            "This explicitly runs cleanup for cleanup-required git-worktree sandbox "
            "allocations recorded in one durable sandbox allocation receipt evidence "
            "artifact. It writes updated receipt evidence. It does not mutate scheduler "
            "state, run host tasks, refresh projection, start a daemon, or mutate "
            "Local Work Trajectory.",
        )
        return 0

    input_evidence_path = ""
    output_evidence_path = ""
    output_evidence_id = ""
    timestamp = ""
    git_executable = "git"

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {
            "--input-evidence-path",
            "--output-evidence-path",
            "--output-evidence-id",
            "--timestamp",
            "--git-executable",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_CLEANUP_RECEIPTS_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--input-evidence-path":
                input_evidence_path = value
            elif arg == "--output-evidence-path":
                output_evidence_path = value
            elif arg == "--output-evidence-id":
                output_evidence_id = value
            elif arg == "--timestamp":
                timestamp = value
            elif arg == "--git-executable":
                git_executable = value
            i += 2
            continue
        print(f"Unknown scheduler cleanup-receipts option: {arg}", file=sys.stderr)
        print(_SCHEDULER_CLEANUP_RECEIPTS_USAGE, file=sys.stderr)
        return 1

    if not input_evidence_path:
        print(_SCHEDULER_CLEANUP_RECEIPTS_USAGE, file=sys.stderr)
        print("Missing required option(s): --input-evidence-path", file=sys.stderr)
        return 1

    root = _find_project_root()
    try:
        from .runtime.orchestration import run_sandbox_allocation_cleanup_over_receipts

        result = run_sandbox_allocation_cleanup_over_receipts(
            _resolve_project_path(root, input_evidence_path),
            output_evidence_path=(
                _resolve_project_path(root, output_evidence_path)
                if output_evidence_path
                else None
            ),
            output_evidence_id=output_evidence_id,
            timestamp=timestamp,
            git_executable=git_executable,
            metadata={"surface": "cli:scheduler cleanup-receipts"},
        )
        payload = result.to_json_dict()
    except Exception as e:
        return _handle_error(
            "Error running scheduler cleanup receipts",
            e,
            category="scheduler_cleanup_receipts_failed",
        )

    _print_json(payload)
    return 0 if payload.get("ok") else 1


def cmd_scheduler_sandbox_receipt_workflow(args: list[str]) -> int:
    """Run host sandbox receipt allocate/read/cleanup/read workflow."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_SANDBOX_RECEIPT_WORKFLOW_USAGE + "\n\n"
            "This composes host allocation, durable sandbox allocation receipt "
            "evidence readback, explicit cleanup, and post-cleanup Host Evidence "
            "readback. Cleanup runs only with --cleanup. This does not refresh "
            "projection, start a daemon service, run real providers, mutate "
            "ExchangeArtifact/admission ledger state, or mutate Local Work Trajectory.",
        )
        return 0

    mode = ""
    snapshot_path = ""
    event_log_path = ""
    workspace_root = ""
    git_worktree_sandbox_root = ""
    allocation_evidence_id = ""
    allocation_evidence_path = ""
    cleanup = False
    cleanup_evidence_id = ""
    cleanup_evidence_path = ""
    runtime_provider = "fake"
    timestamp = ""
    git_executable = "git"
    max_runs: int | None = 1
    max_ticks = 1
    max_runs_per_tick: int | None = 1
    max_runtime_failures: int | None = 1

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--cleanup":
            cleanup = True
            i += 1
            continue
        if arg in {
            "--mode",
            "--snapshot-path",
            "--event-log-path",
            "--workspace-root",
            "--git-worktree-sandbox-root",
            "--allocation-evidence-id",
            "--allocation-evidence-path",
            "--cleanup-evidence-id",
            "--cleanup-evidence-path",
            "--runtime-provider",
            "--max-runs",
            "--max-ticks",
            "--max-runs-per-tick",
            "--max-runtime-failures",
            "--timestamp",
            "--git-executable",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_SANDBOX_RECEIPT_WORKFLOW_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--mode":
                mode = value
            elif arg == "--snapshot-path":
                snapshot_path = value
            elif arg == "--event-log-path":
                event_log_path = value
            elif arg == "--workspace-root":
                workspace_root = value
            elif arg == "--git-worktree-sandbox-root":
                git_worktree_sandbox_root = value
            elif arg == "--allocation-evidence-id":
                allocation_evidence_id = value
            elif arg == "--allocation-evidence-path":
                allocation_evidence_path = value
            elif arg == "--cleanup-evidence-id":
                cleanup_evidence_id = value
            elif arg == "--cleanup-evidence-path":
                cleanup_evidence_path = value
            elif arg == "--runtime-provider":
                runtime_provider = value
            elif arg == "--timestamp":
                timestamp = value
            elif arg == "--git-executable":
                git_executable = value
            elif arg == "--max-runs":
                try:
                    max_runs = int(value)
                except ValueError:
                    print(_SCHEDULER_SANDBOX_RECEIPT_WORKFLOW_USAGE, file=sys.stderr)
                    print("--max-runs must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--max-ticks":
                try:
                    max_ticks = int(value)
                except ValueError:
                    print(_SCHEDULER_SANDBOX_RECEIPT_WORKFLOW_USAGE, file=sys.stderr)
                    print("--max-ticks must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--max-runs-per-tick":
                try:
                    max_runs_per_tick = int(value)
                except ValueError:
                    print(_SCHEDULER_SANDBOX_RECEIPT_WORKFLOW_USAGE, file=sys.stderr)
                    print("--max-runs-per-tick must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--max-runtime-failures":
                try:
                    max_runtime_failures = int(value)
                except ValueError:
                    print(_SCHEDULER_SANDBOX_RECEIPT_WORKFLOW_USAGE, file=sys.stderr)
                    print("--max-runtime-failures must be an integer", file=sys.stderr)
                    return 1
            i += 2
            continue
        print(f"Unknown scheduler sandbox-receipt-workflow option: {arg}", file=sys.stderr)
        print(_SCHEDULER_SANDBOX_RECEIPT_WORKFLOW_USAGE, file=sys.stderr)
        return 1

    normalized_mode = mode.replace("_", "-")
    missing = [
        name
        for name, value in (
            ("--mode", normalized_mode),
            ("--snapshot-path", snapshot_path),
            ("--event-log-path", event_log_path),
            ("--workspace-root", workspace_root),
            ("--git-worktree-sandbox-root", git_worktree_sandbox_root),
            ("--allocation-evidence-id", allocation_evidence_id),
        )
        if not value
    ]
    if missing:
        print(_SCHEDULER_SANDBOX_RECEIPT_WORKFLOW_USAGE, file=sys.stderr)
        print(f"Missing required option(s): {', '.join(missing)}", file=sys.stderr)
        return 1
    if normalized_mode not in {"run-once", "daemon-loop"}:
        print(_SCHEDULER_SANDBOX_RECEIPT_WORKFLOW_USAGE, file=sys.stderr)
        print("--mode must be run-once or daemon-loop", file=sys.stderr)
        return 1
    if runtime_provider != "fake":
        print(
            "scheduler sandbox-receipt-workflow currently supports only "
            "--runtime-provider fake; real providers require host-owned injected runtime wiring",
            file=sys.stderr,
        )
        return 1

    root = _find_project_root()
    snapshot = _resolve_project_path(root, snapshot_path)
    event_log = _resolve_project_path(root, event_log_path)
    source_repo = _resolve_project_path(root, workspace_root)
    sandbox_root = _resolve_project_path(root, git_worktree_sandbox_root)
    allocation_path = (
        _resolve_project_path(root, allocation_evidence_path)
        if allocation_evidence_path
        else None
    )
    cleanup_path = (
        _resolve_project_path(root, cleanup_evidence_path)
        if cleanup_evidence_path
        else None
    )

    try:
        from .runtime.orchestration import (
            HostSchedulerDaemonLoopRequest,
            HostSchedulerRunRequest,
            RuntimeHostInvocation,
            RuntimeRegistryWiringConfig,
            SchedulerDaemonLoopStopPolicy,
        )
        from tools.progress_graph import (
            HostSandboxReceiptWorkflowRequest,
            run_host_sandbox_receipt_workflow,
        )

        runtime_config = RuntimeRegistryWiringConfig(
            providers=("fake",),
            timestamp=timestamp,
            host_invocation=RuntimeHostInvocation(
                surface="host-authorized-adapter",
                invocation_id=f"cli:scheduler sandbox-receipt-workflow:{normalized_mode}",
                requested_providers=("fake",),
                requested_by="operator-cli",
                reason="scheduler sandbox receipt workflow",
            ),
        )
        workflow_mode = "run_once" if normalized_mode == "run-once" else "daemon_loop"
        run_once_request = None
        daemon_loop_request = None
        if workflow_mode == "run_once":
            run_once_request = HostSchedulerRunRequest(
                snapshot_path=snapshot,
                event_log_path=event_log,
                runtime_config=runtime_config,
                max_runs=max_runs,
                workspace_root=str(source_repo),
                git_worktree_sandbox_root=sandbox_root,
                sandbox_allocation_evidence_id=allocation_evidence_id,
                sandbox_allocation_evidence_path=allocation_path,
                timestamp=timestamp,
            )
        else:
            daemon_loop_request = HostSchedulerDaemonLoopRequest(
                snapshot_path=snapshot,
                event_log_path=event_log,
                runtime_config=runtime_config,
                stop_policy=SchedulerDaemonLoopStopPolicy(
                    max_ticks=max_ticks,
                    max_runs_per_tick=max_runs_per_tick,
                    max_runtime_failures=max_runtime_failures,
                ),
                workspace_root=str(source_repo),
                git_worktree_sandbox_root=sandbox_root,
                sandbox_allocation_evidence_id=allocation_evidence_id,
                sandbox_allocation_evidence_path=allocation_path,
                timestamp=timestamp,
                metadata={"surface": "cli:scheduler sandbox-receipt-workflow"},
            )
        result = run_host_sandbox_receipt_workflow(
            HostSandboxReceiptWorkflowRequest(
                project_root=root,
                mode=workflow_mode,
                run_once_request=run_once_request,
                daemon_loop_request=daemon_loop_request,
                cleanup=cleanup,
                cleanup_evidence_id=cleanup_evidence_id,
                cleanup_evidence_path=cleanup_path,
                timestamp=timestamp,
                git_executable=git_executable,
                cleanup_metadata={"surface": "cli:scheduler sandbox-receipt-workflow"},
            )
        )
        payload = result.to_json_dict()
    except Exception as e:
        return _handle_error(
            "Error running scheduler sandbox receipt workflow",
            e,
            category="scheduler_sandbox_receipt_workflow_failed",
        )

    _print_json(payload)
    return 0 if payload.get("ok") else 1


def cmd_scheduler_inspect_admissions(args: list[str]) -> int:
    """Read ExchangeArtifact admission ledger records without mutation."""

    if args and args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_INSPECT_ADMISSIONS_USAGE + "\n\n"
            "This is a readback command. It does not write scheduler state, exchange "
            "artifacts, projection artifacts, or Local Work Trajectory.",
        )
        return 0

    admission_ledger_path = ""
    artifact_id = ""
    version = ""

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {"--admission-ledger-path", "--artifact-id", "--version"}:
            if i + 1 >= len(args):
                print(_SCHEDULER_INSPECT_ADMISSIONS_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--admission-ledger-path":
                admission_ledger_path = value
            elif arg == "--artifact-id":
                artifact_id = value
            elif arg == "--version":
                version = value
            i += 2
            continue
        print(f"Unknown scheduler inspect-admissions option: {arg}", file=sys.stderr)
        print(_SCHEDULER_INSPECT_ADMISSIONS_USAGE, file=sys.stderr)
        return 1

    root = _find_project_root()

    try:
        from .runtime.orchestration import (
            default_exchange_artifact_admission_ledger_path,
            inspect_exchange_artifact_admission_ledger,
        )

        ledger_path = (
            _resolve_project_path(root, admission_ledger_path)
            if admission_ledger_path
            else default_exchange_artifact_admission_ledger_path(root)
        )
        inspection = inspect_exchange_artifact_admission_ledger(
            ledger_path,
            artifact_id=artifact_id,
            artifact_version=version,
        )
    except Exception as e:
        return _handle_error(
            "Error inspecting exchange artifact admissions",
            e,
            category="scheduler_admission_inspect_failed",
        )

    payload = {"ok": inspection.error_count == 0}
    payload.update(inspection.to_json_dict())
    _print_json(payload)
    return 1 if inspection.error_count else 0


def cmd_scheduler_inspect_binding_refs(args: list[str]) -> int:
    """Read supervisor storage binding refs in one stored scheduler submission."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_INSPECT_BINDING_REFS_USAGE + "\n\n"
            "This is a readback command. It reads one exact stored scheduler "
            "submission artifact and validates supervisor storage binding artifact "
            "refs without writing scheduler state, exchange artifacts, admission "
            "ledgers, projections, raw evidence JSON, or Local Work Trajectory.",
        )
        return 0

    artifact_store_path = ""
    artifact_id = ""
    version = ""

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {"--artifact-store-path", "--artifact-id", "--version"}:
            if i + 1 >= len(args):
                print(_SCHEDULER_INSPECT_BINDING_REFS_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--artifact-id":
                artifact_id = value
            elif arg == "--version":
                version = value
            i += 2
            continue
        print(f"Unknown scheduler inspect-binding-refs option: {arg}", file=sys.stderr)
        print(_SCHEDULER_INSPECT_BINDING_REFS_USAGE, file=sys.stderr)
        return 1

    if not artifact_id or not version:
        missing = []
        if not artifact_id:
            missing.append("--artifact-id")
        if not version:
            missing.append("--version")
        print(_SCHEDULER_INSPECT_BINDING_REFS_USAGE, file=sys.stderr)
        print(f"Missing required option(s): {', '.join(missing)}", file=sys.stderr)
        return 1

    root = _find_project_root()

    try:
        from .runtime.orchestration import (
            default_exchange_artifact_store_path,
            inspect_supervisor_storage_binding_artifact_refs_for_submission,
        )

        store_path = (
            _resolve_project_path(root, artifact_store_path)
            if artifact_store_path
            else default_exchange_artifact_store_path(root)
        )
        inspection = inspect_supervisor_storage_binding_artifact_refs_for_submission(
            artifact_store_path=store_path,
            artifact_id=artifact_id,
            version=version,
        )
    except Exception as e:
        return _handle_error(
            "Error inspecting supervisor storage binding references",
            e,
            category="scheduler_binding_ref_inspect_failed",
        )

    payload = inspection.to_json_dict()
    _print_json(payload)
    return 0 if inspection.ok else 1


def cmd_scheduler_inspect_agent_mailbox(args: list[str]) -> int:
    """Read one agent's ExchangeArtifact mailbox without mutation."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_INSPECT_AGENT_MAILBOX_USAGE + "\n\n"
            "This is a readback command. It builds a per-agent inbox/outbox/"
            "related read model over the local ExchangeArtifact store. It does "
            "not write scheduler state, exchange artifacts, admission ledgers, "
            "projection artifacts, consume artifacts, or mutate Local Work "
            "Trajectory.",
        )
        return 0

    artifact_store_path = ""
    agent_id = ""
    include_archived = False

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--include-archived":
            include_archived = True
            i += 1
            continue
        if arg in {"--artifact-store-path", "--agent-id"}:
            if i + 1 >= len(args):
                print(_SCHEDULER_INSPECT_AGENT_MAILBOX_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--agent-id":
                agent_id = value
            i += 2
            continue
        print(f"Unknown scheduler inspect-agent-mailbox option: {arg}", file=sys.stderr)
        print(_SCHEDULER_INSPECT_AGENT_MAILBOX_USAGE, file=sys.stderr)
        return 1

    if not agent_id:
        print(_SCHEDULER_INSPECT_AGENT_MAILBOX_USAGE, file=sys.stderr)
        print("Missing required option(s): --agent-id", file=sys.stderr)
        return 1

    root = _find_project_root()

    try:
        from .runtime.orchestration import (
            default_exchange_artifact_store_path,
            inspect_agent_exchange_mailbox,
        )

        store_path = (
            _resolve_project_path(root, artifact_store_path)
            if artifact_store_path
            else default_exchange_artifact_store_path(root)
        )
        mailbox = inspect_agent_exchange_mailbox(
            store_path,
            agent_id=agent_id,
            include_archived=include_archived,
        )
    except Exception as e:
        return _handle_error(
            "Error inspecting agent exchange mailbox",
            e,
            category="scheduler_agent_mailbox_inspect_failed",
        )

    payload = {"ok": not mailbox.errors}
    payload.update(mailbox.to_json_dict())
    _print_json(payload)
    return 1 if mailbox.errors else 0


def cmd_scheduler_inspect_agent_history(args: list[str]) -> int:
    """Read compact ExchangeArtifact communication history without mutation."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_INSPECT_AGENT_HISTORY_USAGE + "\n\n"
            "This is a readback command. It summarizes exact-version "
            "ExchangeArtifact causality, compact log parts, participants, and "
            "lifecycle counts. It does not expose raw sensitive payload content "
            "and does not write scheduler state, exchange artifacts, admission "
            "ledgers, projection artifacts, consume artifacts, or mutate Local "
            "Work Trajectory.",
        )
        return 0

    artifact_store_path = ""
    agent_id = ""
    correlation_id = ""
    include_archived = False

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--include-archived":
            include_archived = True
            i += 1
            continue
        if arg in {"--artifact-store-path", "--agent-id", "--correlation-id"}:
            if i + 1 >= len(args):
                print(_SCHEDULER_INSPECT_AGENT_HISTORY_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--agent-id":
                agent_id = value
            elif arg == "--correlation-id":
                correlation_id = value
            i += 2
            continue
        print(f"Unknown scheduler inspect-agent-history option: {arg}", file=sys.stderr)
        print(_SCHEDULER_INSPECT_AGENT_HISTORY_USAGE, file=sys.stderr)
        return 1

    root = _find_project_root()

    try:
        from .runtime.orchestration import (
            default_exchange_artifact_store_path,
            inspect_agent_exchange_history_summary,
        )

        store_path = (
            _resolve_project_path(root, artifact_store_path)
            if artifact_store_path
            else default_exchange_artifact_store_path(root)
        )
        summary = inspect_agent_exchange_history_summary(
            store_path,
            agent_id=agent_id,
            correlation_id=correlation_id,
            include_archived=include_archived,
        )
    except Exception as e:
        return _handle_error(
            "Error inspecting agent exchange history",
            e,
            category="scheduler_agent_history_inspect_failed",
        )

    payload = {"ok": not summary.errors}
    payload.update(summary.to_json_dict())
    _print_json(payload)
    return 1 if summary.errors else 0


def cmd_scheduler_inspect_runtime_invocations(args: list[str]) -> int:
    """Read compact runtime invocation audit records without mutation."""

    if args and args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_INSPECT_RUNTIME_INVOCATIONS_USAGE + "\n\n"
            "This is a readback command. It summarizes compact runtime "
            "invocation audit records and does not expose raw transcripts, "
            "scheduler state, exchange artifacts, providers, or Local Work "
            "Trajectory.",
        )
        return 0

    path = ""
    latest_limit = 20

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {"--path", "--latest-limit"}:
            if i + 1 >= len(args):
                print(_SCHEDULER_INSPECT_RUNTIME_INVOCATIONS_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--path":
                path = value
            else:
                try:
                    latest_limit = int(value)
                except ValueError:
                    print("--latest-limit must be an integer", file=sys.stderr)
                    return 1
            i += 2
            continue
        print(f"Unknown scheduler inspect-runtime-invocations option: {arg}", file=sys.stderr)
        print(_SCHEDULER_INSPECT_RUNTIME_INVOCATIONS_USAGE, file=sys.stderr)
        return 1

    root = _find_project_root()

    try:
        from .runtime.orchestration import (
            DEFAULT_RUNTIME_INVOCATION_LOG_RELATIVE_PATH,
            inspect_runtime_invocation_log,
        )

        log_path = (
            _resolve_project_path(root, path)
            if path
            else _resolve_project_path(root, DEFAULT_RUNTIME_INVOCATION_LOG_RELATIVE_PATH)
        )
        summary = inspect_runtime_invocation_log(log_path, latest_limit=latest_limit)
    except Exception as e:
        return _handle_error(
            "Error inspecting runtime invocations",
            e,
            category="runtime_invocation_inspect_failed",
        )

    payload = {"ok": not summary.errors}
    payload.update(summary.to_json_dict())
    _print_json(payload)
    return 1 if summary.errors else 0


def cmd_scheduler_inspect_leader_worker_activation(args: list[str]) -> int:
    """Project leader/worker activation state without mutation."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_INSPECT_LEADER_WORKER_ACTIVATION_USAGE + "\n\n"
            "This is a readback command. It projects leader/worker activation "
            "state from scheduler snapshot and ExchangeArtifact messages. It "
            "does not run providers or mutate scheduler, exchange, projection, "
            "or Local Work Trajectory state.",
        )
        return 0

    snapshot_path = ""
    artifact_store_path = ""
    leader_agent_id = "agent:guide"
    worker_agent_ids: list[str] = []

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {"--snapshot-path", "--artifact-store-path", "--leader-agent-id", "--worker-agent-id"}:
            if i + 1 >= len(args):
                print(_SCHEDULER_INSPECT_LEADER_WORKER_ACTIVATION_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--snapshot-path":
                snapshot_path = value
            elif arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--leader-agent-id":
                leader_agent_id = value
            else:
                worker_agent_ids.append(value)
            i += 2
            continue
        print(f"Unknown scheduler inspect-leader-worker-activation option: {arg}", file=sys.stderr)
        print(_SCHEDULER_INSPECT_LEADER_WORKER_ACTIVATION_USAGE, file=sys.stderr)
        return 1

    if not snapshot_path:
        print(_SCHEDULER_INSPECT_LEADER_WORKER_ACTIVATION_USAGE, file=sys.stderr)
        print("inspect-leader-worker-activation requires --snapshot-path", file=sys.stderr)
        return 1

    root = _find_project_root()

    try:
        from .runtime.orchestration import (
            JsonArtifactVersionStore,
            default_exchange_artifact_store_path,
            read_scheduler_state_snapshot,
            run_leader_worker_activation_pass,
        )

        resolved_snapshot = _resolve_project_path(root, snapshot_path)
        store_path = (
            _resolve_project_path(root, artifact_store_path)
            if artifact_store_path
            else default_exchange_artifact_store_path(root)
        )
        exchange_records = (
            JsonArtifactVersionStore(store_path).list_records()
            if store_path.exists()
            else ()
        )
        result = run_leader_worker_activation_pass(
            scheduler_state=read_scheduler_state_snapshot(resolved_snapshot),
            exchange_records=exchange_records,
            leader_agent_id=leader_agent_id,
            worker_agent_ids=tuple(worker_agent_ids),
        )
    except Exception as e:
        return _handle_error(
            "Error inspecting leader-worker activation",
            e,
            category="leader_worker_activation_inspect_failed",
        )

    payload = {"ok": True}
    payload.update(result.to_json_dict())
    _print_json(payload)
    return 0


def cmd_scheduler_trajectory_team(args: list[str]) -> int:
    """Inspect or mutate leader/operator trajectory team continuity roster."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_TRAJECTORY_TEAM_USAGE + "\n\n"
            "This is a leader/operator-owned team continuity surface. It uses "
            "the shared runtime dispatcher to inspect or update trajectory-team "
            "roster, binding, ownership, and audit evidence. It does not run "
            "providers, mutate scheduler task state, or mutate Local Work "
            "Trajectory. Workers must report requested changes through "
            "docs/worker-trajectory-update-reporting.md.",
        )
        return 0

    action = args[0]
    parsed: dict[str, object] = {
        "trajectory_id": "",
        "lane_id": "",
        "leader_id": "agent:guide",
        "worker_id": "",
        "caller_role": "leader",
        "runtime_provider": "opencode",
        "binding_id": "",
        "ownership_id": "",
        "replacement_binding_id": "",
        "new_binding_id": "",
        "source_binding_id": "",
        "no_continuity_reason": "",
        "task_id": "",
        "delivery_id": "",
        "reason": "",
        "timestamp": "",
        "binding_ledger_path": ".dbc/runtime/continuous-worker-bindings.json",
        "binding_event_log_path": ".dbc/runtime/continuous-worker-binding-events.jsonl",
        "ownership_ledger_path": ".dbc/runtime/continuous-worker-lane-ownerships.json",
        "ownership_event_log_path": ".dbc/runtime/continuous-worker-lane-ownership-events.jsonl",
        "lease_ledger_path": ".dbc/runtime/continuous-worker-delivery-leases.json",
        "team_event_log_path": ".dbc/runtime/trajectory-team-continuity-events.jsonl",
        "scheduler_event_log_path": "",
        "attach_url": "",
        "session_id": "",
        "continue_session": False,
        "fork_session": False,
        "compact_context_ref": "",
        "mailbox_cursor_ref": "",
        "worker_report_refs": [],
        "audit_refs": [],
        "include_inactive": True,
    }
    option_map = {
        "--trajectory-id": "trajectory_id",
        "--lane-id": "lane_id",
        "--leader-id": "leader_id",
        "--worker-id": "worker_id",
        "--caller-role": "caller_role",
        "--runtime-provider": "runtime_provider",
        "--binding-id": "binding_id",
        "--ownership-id": "ownership_id",
        "--replacement-binding-id": "replacement_binding_id",
        "--new-binding-id": "new_binding_id",
        "--source-binding-id": "source_binding_id",
        "--no-continuity-reason": "no_continuity_reason",
        "--task-id": "task_id",
        "--delivery-id": "delivery_id",
        "--reason": "reason",
        "--timestamp": "timestamp",
        "--binding-ledger-path": "binding_ledger_path",
        "--binding-event-log-path": "binding_event_log_path",
        "--ownership-ledger-path": "ownership_ledger_path",
        "--ownership-event-log-path": "ownership_event_log_path",
        "--lease-ledger-path": "lease_ledger_path",
        "--team-event-log-path": "team_event_log_path",
        "--scheduler-event-log-path": "scheduler_event_log_path",
        "--attach-url": "attach_url",
        "--session-id": "session_id",
        "--compact-context-ref": "compact_context_ref",
        "--mailbox-cursor-ref": "mailbox_cursor_ref",
    }

    i = 1
    while i < len(args):
        arg = args[i]
        if arg == "--continue-session":
            parsed["continue_session"] = True
            i += 1
            continue
        if arg == "--fork-session":
            parsed["fork_session"] = True
            i += 1
            continue
        if arg == "--active-only":
            parsed["include_inactive"] = False
            i += 1
            continue
        if arg in {"--worker-report-ref", "--audit-ref"}:
            if i + 1 >= len(args):
                print(_SCHEDULER_TRAJECTORY_TEAM_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            key = "worker_report_refs" if arg == "--worker-report-ref" else "audit_refs"
            parsed[key].append(args[i + 1])  # type: ignore[union-attr]
            i += 2
            continue
        if arg in option_map:
            if i + 1 >= len(args):
                print(_SCHEDULER_TRAJECTORY_TEAM_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            parsed[option_map[arg]] = args[i + 1]
            i += 2
            continue
        print(f"Unknown scheduler trajectory-team option: {arg}", file=sys.stderr)
        print(_SCHEDULER_TRAJECTORY_TEAM_USAGE, file=sys.stderr)
        return 1

    root = _find_project_root()
    try:
        from .runtime.orchestration import (
            TrajectoryTeamContinuitySurfaceRequest,
            run_trajectory_team_continuity_surface,
        )

        result = run_trajectory_team_continuity_surface(
            TrajectoryTeamContinuitySurfaceRequest(
                action=action,  # type: ignore[arg-type]
                project_root=root,
                caller_role=str(parsed["caller_role"]),
                trajectory_id=str(parsed["trajectory_id"]),
                lane_id=str(parsed["lane_id"]),
                leader_id=str(parsed["leader_id"]),
                worker_id=str(parsed["worker_id"]),
                runtime_provider=str(parsed["runtime_provider"]),
                binding_id=str(parsed["binding_id"]),
                ownership_id=str(parsed["ownership_id"]),
                replacement_binding_id=str(parsed["replacement_binding_id"]),
                new_binding_id=str(parsed["new_binding_id"]),
                source_binding_id=str(parsed["source_binding_id"]),
                no_continuity_reason=str(parsed["no_continuity_reason"]),
                task_id=str(parsed["task_id"]),
                delivery_id=str(parsed["delivery_id"]),
                timestamp=str(parsed["timestamp"]),
                reason=str(parsed["reason"]),
                binding_ledger_path=str(parsed["binding_ledger_path"]),
                binding_event_log_path=str(parsed["binding_event_log_path"]),
                ownership_ledger_path=str(parsed["ownership_ledger_path"]),
                ownership_event_log_path=str(parsed["ownership_event_log_path"]),
                lease_ledger_path=str(parsed["lease_ledger_path"]),
                team_event_log_path=str(parsed["team_event_log_path"]),
                scheduler_event_log_path=str(parsed["scheduler_event_log_path"]),
                attach_url=str(parsed["attach_url"]),
                session_id=str(parsed["session_id"]),
                continue_session=bool(parsed["continue_session"]),
                fork_session=bool(parsed["fork_session"]),
                compact_context_ref=str(parsed["compact_context_ref"]),
                mailbox_cursor_ref=str(parsed["mailbox_cursor_ref"]),
                worker_report_refs=tuple(parsed["worker_report_refs"]),  # type: ignore[arg-type]
                audit_refs=tuple(parsed["audit_refs"]),  # type: ignore[arg-type]
                include_inactive=bool(parsed["include_inactive"]),
            )
        )
    except Exception as e:
        return _handle_error(
            "Error running scheduler trajectory-team",
            e,
            category="scheduler_trajectory_team_failed",
        )

    payload = result.to_json_dict()
    _print_json(payload)
    return 0 if payload.get("ok") else 1


def cmd_scheduler_leader_worker_dispatcher_tick(args: list[str]) -> int:
    """Persist one leader/worker dispatcher tick without running providers."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_LEADER_WORKER_DISPATCHER_TICK_USAGE + "\n\n"
            "This command persists activation dispatcher state and a compact "
            "dispatch event log. It derives decisions from scheduler recovery "
            "and ExchangeArtifact messages, but does not run providers or mutate "
            "scheduler, exchange, projection, or Local Work Trajectory state.",
        )
        return 0

    parsed = _parse_leader_worker_dispatcher_args(
        args,
        usage=_SCHEDULER_LEADER_WORKER_DISPATCHER_TICK_USAGE,
        allow_max_ticks=False,
    )
    if parsed is None:
        return 1

    root = _find_project_root()
    try:
        from .runtime.orchestration import (
            LeaderWorkerDispatcherTickRequest,
            run_leader_worker_dispatcher_tick,
        )

        request = LeaderWorkerDispatcherTickRequest(
            **_leader_worker_dispatcher_request_kwargs(root, parsed),
        )
        result = run_leader_worker_dispatcher_tick(request)
    except Exception as e:
        return _handle_error(
            "Error running leader-worker dispatcher tick",
            e,
            category="leader_worker_dispatcher_tick_failed",
        )

    _print_json(result.to_json_dict())
    return 0


def cmd_scheduler_leader_worker_dispatcher_loop(args: list[str]) -> int:
    """Run bounded leader/worker dispatcher ticks without running providers."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_LEADER_WORKER_DISPATCHER_LOOP_USAGE + "\n\n"
            "This command runs bounded activation dispatcher ticks until "
            "max-ticks or no new dispatch decisions. It persists dispatcher "
            "state/logs and does not run providers or mutate scheduler, "
            "exchange, projection, or Local Work Trajectory state.",
        )
        return 0

    parsed = _parse_leader_worker_dispatcher_args(
        args,
        usage=_SCHEDULER_LEADER_WORKER_DISPATCHER_LOOP_USAGE,
        allow_max_ticks=True,
    )
    if parsed is None:
        return 1

    root = _find_project_root()
    try:
        from .runtime.orchestration import (
            LeaderWorkerDispatcherLoopRequest,
            LeaderWorkerDispatcherTickRequest,
            run_leader_worker_dispatcher_loop,
        )

        tick_request = LeaderWorkerDispatcherTickRequest(
            **_leader_worker_dispatcher_request_kwargs(root, parsed),
        )
        result = run_leader_worker_dispatcher_loop(
            LeaderWorkerDispatcherLoopRequest(
                tick_request=tick_request,
                max_ticks=int(parsed["max_ticks"]),
            )
        )
    except Exception as e:
        return _handle_error(
            "Error running leader-worker dispatcher loop",
            e,
            category="leader_worker_dispatcher_loop_failed",
        )

    _print_json(result.to_json_dict())
    return 0


def _parse_leader_worker_dispatcher_args(
    args: list[str],
    *,
    usage: str,
    allow_max_ticks: bool,
) -> dict[str, object] | None:
    parsed: dict[str, object] = {
        "snapshot_path": "",
        "event_log_path": "",
        "artifact_store_path": "",
        "dispatcher_state_path": "",
        "dispatch_event_log_path": "",
        "dispatcher_id": "leader-worker-dispatcher",
        "trajectory_id": "",
        "leader_agent_id": "agent:guide",
        "worker_agent_ids": [],
        "timestamp": "",
        "max_ticks": 1,
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {
            "--snapshot-path",
            "--event-log-path",
            "--artifact-store-path",
            "--dispatcher-state-path",
            "--dispatch-event-log-path",
            "--dispatcher-id",
            "--trajectory-id",
            "--leader-agent-id",
            "--worker-agent-id",
            "--timestamp",
            "--max-ticks",
        }:
            if arg == "--max-ticks" and not allow_max_ticks:
                print(f"Unknown scheduler leader-worker dispatcher option: {arg}", file=sys.stderr)
                print(usage, file=sys.stderr)
                return None
            if i + 1 >= len(args):
                print(usage, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return None
            value = args[i + 1]
            if arg == "--snapshot-path":
                parsed["snapshot_path"] = value
            elif arg == "--event-log-path":
                parsed["event_log_path"] = value
            elif arg == "--artifact-store-path":
                parsed["artifact_store_path"] = value
            elif arg == "--dispatcher-state-path":
                parsed["dispatcher_state_path"] = value
            elif arg == "--dispatch-event-log-path":
                parsed["dispatch_event_log_path"] = value
            elif arg == "--dispatcher-id":
                parsed["dispatcher_id"] = value
            elif arg == "--trajectory-id":
                parsed["trajectory_id"] = value
            elif arg == "--leader-agent-id":
                parsed["leader_agent_id"] = value
            elif arg == "--worker-agent-id":
                parsed["worker_agent_ids"] = [*parsed["worker_agent_ids"], value]  # type: ignore[index]
            elif arg == "--timestamp":
                parsed["timestamp"] = value
            elif arg == "--max-ticks":
                try:
                    parsed["max_ticks"] = int(value)
                except ValueError:
                    print(usage, file=sys.stderr)
                    print("--max-ticks must be an integer", file=sys.stderr)
                    return None
            i += 2
            continue
        print(f"Unknown scheduler leader-worker dispatcher option: {arg}", file=sys.stderr)
        print(usage, file=sys.stderr)
        return None

    if not parsed["snapshot_path"] or not parsed["event_log_path"]:
        print(usage, file=sys.stderr)
        print("leader-worker dispatcher requires --snapshot-path and --event-log-path", file=sys.stderr)
        return None
    if int(parsed["max_ticks"]) < 0:
        print("--max-ticks must be non-negative", file=sys.stderr)
        return None
    return parsed


def _leader_worker_dispatcher_request_kwargs(
    root: Path,
    parsed: dict[str, object],
) -> dict[str, object]:
    from .runtime.orchestration import (
        DEFAULT_LEADER_WORKER_DISPATCHER_EVENT_LOG_RELATIVE_PATH,
        DEFAULT_LEADER_WORKER_DISPATCHER_STATE_RELATIVE_PATH,
        default_exchange_artifact_store_path,
    )

    return {
        "dispatcher_state_path": (
            _resolve_project_path(root, str(parsed["dispatcher_state_path"]))
            if parsed["dispatcher_state_path"]
            else _resolve_project_path(root, DEFAULT_LEADER_WORKER_DISPATCHER_STATE_RELATIVE_PATH)
        ),
        "dispatch_event_log_path": (
            _resolve_project_path(root, str(parsed["dispatch_event_log_path"]))
            if parsed["dispatch_event_log_path"]
            else _resolve_project_path(root, DEFAULT_LEADER_WORKER_DISPATCHER_EVENT_LOG_RELATIVE_PATH)
        ),
        "scheduler_snapshot_path": _resolve_project_path(root, str(parsed["snapshot_path"])),
        "scheduler_event_log_path": _resolve_project_path(root, str(parsed["event_log_path"])),
        "artifact_store_path": (
            _resolve_project_path(root, str(parsed["artifact_store_path"]))
            if parsed["artifact_store_path"]
            else default_exchange_artifact_store_path(root)
        ),
        "dispatcher_id": str(parsed["dispatcher_id"]),
        "trajectory_id": str(parsed["trajectory_id"]),
        "leader_agent_id": str(parsed["leader_agent_id"]),
        "worker_agent_ids": tuple(str(item) for item in parsed["worker_agent_ids"]),  # type: ignore[arg-type]
        "timestamp": str(parsed["timestamp"]),
    }


def cmd_scheduler_leader_worker_delivery_sync(args: list[str]) -> int:
    """Sync dispatcher decisions into host-owned delivery acknowledgement state."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_LEADER_WORKER_DELIVERY_SYNC_USAGE + "\n\n"
            "This command reads the leader-worker dispatcher event log and "
            "creates missing pending delivery records. It writes only the "
            "host-owned delivery state/log and does not run providers, mutate "
            "scheduler or exchange state, mutate dispatcher state, or mutate "
            "Local Work Trajectory.",
        )
        return 0

    parsed = _parse_leader_worker_delivery_common_args(
        args,
        usage=_SCHEDULER_LEADER_WORKER_DELIVERY_SYNC_USAGE,
        mode="sync",
    )
    if parsed is None:
        return 1
    if not parsed["dispatch_event_log_path"]:
        print(_SCHEDULER_LEADER_WORKER_DELIVERY_SYNC_USAGE, file=sys.stderr)
        print("leader-worker delivery sync requires --dispatch-event-log-path", file=sys.stderr)
        return 1

    root = _find_project_root()
    try:
        from .runtime.orchestration import (
            LeaderWorkerDeliverySyncRequest,
            sync_leader_worker_delivery_from_dispatch_log,
        )

        result = sync_leader_worker_delivery_from_dispatch_log(
            LeaderWorkerDeliverySyncRequest(
                delivery_state_path=_leader_worker_delivery_state_path(root, parsed),
                delivery_event_log_path=_leader_worker_delivery_log_path(root, parsed),
                dispatch_event_log_path=_resolve_project_path(
                    root,
                    str(parsed["dispatch_event_log_path"]),
                ),
                delivery_id=str(parsed["delivery_id"]),
                dispatcher_id=str(parsed["dispatcher_id"]),
                timestamp=str(parsed["timestamp"]),
                host_id=str(parsed["host_id"]),
            )
        )
    except Exception as e:
        return _handle_error(
            "Error syncing leader-worker delivery state",
            e,
            category="leader_worker_delivery_sync_failed",
        )

    _print_json(result.to_json_dict())
    return 0


def cmd_scheduler_leader_worker_delivery_ack(args: list[str]) -> int:
    """Record one host/runtime delivery acknowledgement."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_LEADER_WORKER_DELIVERY_ACK_USAGE + "\n\n"
            "This command updates one existing delivery record to delivered, "
            "acknowledged, or failed. It writes only the host-owned delivery "
            "state/log. It does not run providers or mutate scheduler, "
            "exchange, dispatcher, projection, or Local Work Trajectory state.",
        )
        return 0

    parsed = _parse_leader_worker_delivery_common_args(
        args,
        usage=_SCHEDULER_LEADER_WORKER_DELIVERY_ACK_USAGE,
        mode="ack",
    )
    if parsed is None:
        return 1
    if not parsed["target_state"]:
        print(_SCHEDULER_LEADER_WORKER_DELIVERY_ACK_USAGE, file=sys.stderr)
        print("leader-worker delivery ack requires --target-state", file=sys.stderr)
        return 1
    if parsed["target_state"] not in {"delivered", "acknowledged", "failed"}:
        print(_SCHEDULER_LEADER_WORKER_DELIVERY_ACK_USAGE, file=sys.stderr)
        print("--target-state must be delivered, acknowledged, or failed", file=sys.stderr)
        return 1
    if not parsed["source_key"] and not parsed["delivery_record_id"]:
        print(_SCHEDULER_LEADER_WORKER_DELIVERY_ACK_USAGE, file=sys.stderr)
        print("leader-worker delivery ack requires --source-key or --delivery-record-id", file=sys.stderr)
        return 1

    root = _find_project_root()
    try:
        from .runtime.orchestration import (
            LeaderWorkerDeliveryAckRequest,
            acknowledge_leader_worker_delivery,
        )

        result = acknowledge_leader_worker_delivery(
            LeaderWorkerDeliveryAckRequest(
                delivery_state_path=_leader_worker_delivery_state_path(root, parsed),
                delivery_event_log_path=_leader_worker_delivery_log_path(root, parsed),
                target_state=str(parsed["target_state"]),  # type: ignore[arg-type]
                source_key=str(parsed["source_key"]),
                delivery_record_id=str(parsed["delivery_record_id"]),
                timestamp=str(parsed["timestamp"]),
                host_id=str(parsed["host_id"]),
                runtime_provider=str(parsed["runtime_provider"]),
                runtime_session_id=str(parsed["runtime_session_id"]),
                runtime_run_id=str(parsed["runtime_run_id"]),
                invocation_id=str(parsed["invocation_id"]),
                failure_kind=str(parsed["failure_kind"]),
                failure_detail=str(parsed["failure_detail"]),
            )
        )
    except Exception as e:
        return _handle_error(
            "Error acknowledging leader-worker delivery",
            e,
            category="leader_worker_delivery_ack_failed",
        )

    _print_json(result.to_json_dict())
    return 0


def cmd_scheduler_inspect_leader_worker_delivery(args: list[str]) -> int:
    """Read host-owned delivery acknowledgement state without mutation."""

    if args and args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_INSPECT_LEADER_WORKER_DELIVERY_USAGE + "\n\n"
            "This is a readback command. It summarizes host-owned "
            "leader-worker delivery acknowledgement state and does not run "
            "providers or mutate scheduler, exchange, dispatcher, projection, "
            "or Local Work Trajectory state.",
        )
        return 0

    parsed = _parse_leader_worker_delivery_common_args(
        args,
        usage=_SCHEDULER_INSPECT_LEADER_WORKER_DELIVERY_USAGE,
        mode="inspect",
    )
    if parsed is None:
        return 1

    latest_limit = int(parsed["latest_limit"])
    root = _find_project_root()
    try:
        from .runtime.orchestration import inspect_leader_worker_delivery_state

        summary = inspect_leader_worker_delivery_state(
            _leader_worker_delivery_state_path(root, parsed),
            latest_limit=latest_limit,
        )
    except Exception as e:
        return _handle_error(
            "Error inspecting leader-worker delivery",
            e,
            category="leader_worker_delivery_inspect_failed",
        )

    payload = {"ok": not summary.errors}
    payload.update(summary.to_json_dict())
    _print_json(payload)
    return 1 if summary.errors else 0


def cmd_scheduler_inspect_codex_runtime_status(args: list[str]) -> int:
    """Read compact Codex scheduler/delivery/runtime status without mutation."""

    return _cmd_scheduler_inspect_provider_runtime_status(
        args,
        runtime_provider="codex",
        usage=_SCHEDULER_INSPECT_CODEX_RUNTIME_STATUS_USAGE,
        command_name="inspect-codex-runtime-status",
        provider_label="Codex",
    )


def cmd_scheduler_inspect_opencode_runtime_status(args: list[str]) -> int:
    """Read compact OpenCode scheduler/delivery/runtime status without mutation."""

    return _cmd_scheduler_inspect_provider_runtime_status(
        args,
        runtime_provider="opencode",
        usage=_SCHEDULER_INSPECT_OPENCODE_RUNTIME_STATUS_USAGE,
        command_name="inspect-opencode-runtime-status",
        provider_label="OpenCode",
    )


def _cmd_scheduler_inspect_provider_runtime_status(
    args: list[str],
    *,
    runtime_provider: str,
    usage: str,
    command_name: str,
    provider_label: str,
) -> int:
    """Read compact provider scheduler/delivery/runtime status without mutation."""

    if not args or args[0] in ("-h", "--help"):
        print(
            usage + "\n\n"
            "This is a read-only operator / guide-agent status surface. It "
            "recovers scheduler state, inspects leader-worker delivery, reads "
            "compact runtime invocation audit records, summarizes ExchangeArtifact "
            f"refs, and reports a safe next_action clue. It does not run {provider_label}, "
            "does not apply patches, does not mutate scheduler/delivery/artifact "
            "state, does not expose raw transcripts, and does not mutate Local "
            "Work Trajectory.",
        )
        return 0

    parsed = _parse_provider_runtime_status_args(
        args,
        usage=usage,
        command_name=command_name,
    )
    if parsed is None:
        return 1
    if not parsed["snapshot_path"] or not parsed["event_log_path"]:
        print(usage, file=sys.stderr)
        print("--snapshot-path and --event-log-path are required", file=sys.stderr)
        return 1
    if int(parsed["latest_limit"]) < 0:
        print(usage, file=sys.stderr)
        print("--latest-limit must be non-negative", file=sys.stderr)
        return 1

    root = _find_project_root()
    try:
        from .runtime.orchestration import (
            DEFAULT_EXCHANGE_ARTIFACT_STORE_RELATIVE_PATH,
            DEFAULT_LEADER_WORKER_DELIVERY_STATE_RELATIVE_PATH,
            DEFAULT_RUNTIME_INVOCATION_LOG_RELATIVE_PATH,
            ProviderRuntimeStatusRequest,
            inspect_provider_runtime_status,
        )

        result = inspect_provider_runtime_status(
            ProviderRuntimeStatusRequest(
                scheduler_snapshot_path=_resolve_project_path(
                    root,
                    str(parsed["snapshot_path"]),
                ),
                scheduler_event_log_path=_resolve_project_path(
                    root,
                    str(parsed["event_log_path"]),
                ),
                runtime_provider=runtime_provider,  # type: ignore[arg-type]
                delivery_state_path=_resolve_project_path(
                    root,
                    str(parsed["delivery_state_path"])
                    or DEFAULT_LEADER_WORKER_DELIVERY_STATE_RELATIVE_PATH,
                ),
                runtime_invocation_log_path=_resolve_project_path(
                    root,
                    str(parsed["runtime_invocation_log_path"])
                    or DEFAULT_RUNTIME_INVOCATION_LOG_RELATIVE_PATH,
                ),
                artifact_store_path=_resolve_project_path(
                    root,
                    str(parsed["artifact_store_path"])
                    or DEFAULT_EXCHANGE_ARTIFACT_STORE_RELATIVE_PATH,
                ),
                target_task_ids=tuple(parsed["target_task_ids"]),  # type: ignore[arg-type]
                latest_limit=int(parsed["latest_limit"]),
            )
        )
    except Exception as e:
        return _handle_error(
            f"Error inspecting {provider_label} runtime status",
            e,
            category=f"scheduler_{runtime_provider}_runtime_status_failed",
        )

    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def cmd_scheduler_inspect_monitoring_snapshot(args: list[str]) -> int:
    """Read frontend-oriented orchestration monitoring snapshot without mutation."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_INSPECT_MONITORING_SNAPSHOT_USAGE + "\n\n"
            "This is a read-only backend API surface for a future monitoring "
            "UI. It recovers scheduler state, inspects leader-worker delivery, "
            "reads compact runtime invocation audit records, summarizes the "
            "optional live Codex concurrent-worker smoke report, and returns "
            "frontend-oriented JSON sections for scheduler, delivery, "
            "runtimeInvocations, liveCodexSmoke, workerReports, and "
            "operatorSignals. It does not run providers, does not mutate "
            "scheduler/delivery/runtime/artifact state, does not expose raw "
            "transcripts, and does not mutate Local Work Trajectory.",
        )
        return 0

    parsed = _parse_monitoring_snapshot_args(args)
    if parsed is None:
        return 1
    if not parsed["snapshot_path"] or not parsed["event_log_path"]:
        print(_SCHEDULER_INSPECT_MONITORING_SNAPSHOT_USAGE, file=sys.stderr)
        print("--snapshot-path and --event-log-path are required", file=sys.stderr)
        return 1
    if int(parsed["latest_limit"]) < 0:
        print(_SCHEDULER_INSPECT_MONITORING_SNAPSHOT_USAGE, file=sys.stderr)
        print("--latest-limit must be non-negative", file=sys.stderr)
        return 1

    root = _find_project_root()
    try:
        from .runtime.orchestration import (
            DEFAULT_EXCHANGE_ARTIFACT_STORE_RELATIVE_PATH,
            DEFAULT_LEADER_WORKER_DELIVERY_STATE_RELATIVE_PATH,
            DEFAULT_LIVE_CODEX_CONCURRENT_WORKER_SMOKE_REPORT_RELATIVE_PATH,
            DEFAULT_RUNTIME_INVOCATION_LOG_RELATIVE_PATH,
            MonitoringSnapshotRequest,
            inspect_monitoring_snapshot,
        )

        result = inspect_monitoring_snapshot(
            MonitoringSnapshotRequest(
                scheduler_snapshot_path=_resolve_project_path(
                    root,
                    str(parsed["snapshot_path"]),
                ),
                scheduler_event_log_path=_resolve_project_path(
                    root,
                    str(parsed["event_log_path"]),
                ),
                delivery_state_path=_resolve_project_path(
                    root,
                    str(parsed["delivery_state_path"])
                    or DEFAULT_LEADER_WORKER_DELIVERY_STATE_RELATIVE_PATH,
                ),
                runtime_invocation_log_path=_resolve_project_path(
                    root,
                    str(parsed["runtime_invocation_log_path"])
                    or DEFAULT_RUNTIME_INVOCATION_LOG_RELATIVE_PATH,
                ),
                artifact_store_path=_resolve_project_path(
                    root,
                    str(parsed["artifact_store_path"])
                    or DEFAULT_EXCHANGE_ARTIFACT_STORE_RELATIVE_PATH,
                ),
                live_codex_smoke_report_path=_resolve_project_path(
                    root,
                    str(parsed["live_codex_smoke_report_path"])
                    or DEFAULT_LIVE_CODEX_CONCURRENT_WORKER_SMOKE_REPORT_RELATIVE_PATH,
                ),
                target_task_ids=tuple(parsed["target_task_ids"]),  # type: ignore[arg-type]
                latest_limit=int(parsed["latest_limit"]),
            )
        )
    except Exception as e:
        return _handle_error(
            "Error inspecting monitoring snapshot",
            e,
            category="scheduler_monitoring_snapshot_failed",
        )

    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def cmd_scheduler_consume_worker_trajectory_report(args: list[str]) -> int:
    """Consume worker report trajectory_update as leader-owned mutation."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_CONSUME_WORKER_TRAJECTORY_REPORT_USAGE + "\n\n"
            "This leader/main/supervisor surface reads one worker Subagent "
            "Report JSON file, validates it against the report schema, and "
            "consumes only the first-version trajectory_update suggested actions "
            "append, advance, block, wait, resume, close, or none. Worker/"
            "subagent caller roles are rejected. It does not run providers, "
            "mutate scheduler state, or consume ExchangeArtifact lifecycle state.",
        )
        return 0

    report_path = ""
    caller_role = "leader"
    actor = "leader"
    current_event_id = ""
    title = ""
    event_kind = "task"
    start_if_missing = True
    trajectory_title = "Local Work Trajectory"
    guide_context = "worker-trajectory-report-consumer"

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--no-start-if-missing":
            start_if_missing = False
            i += 1
            continue
        if arg in {
            "--report-path",
            "--caller-role",
            "--actor",
            "--current-event-id",
            "--title",
            "--event-kind",
            "--trajectory-title",
            "--guide-context",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_CONSUME_WORKER_TRAJECTORY_REPORT_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--report-path":
                report_path = value
            elif arg == "--caller-role":
                caller_role = value
            elif arg == "--actor":
                actor = value
            elif arg == "--current-event-id":
                current_event_id = value
            elif arg == "--title":
                title = value
            elif arg == "--event-kind":
                event_kind = value
            elif arg == "--trajectory-title":
                trajectory_title = value
            elif arg == "--guide-context":
                guide_context = value
            i += 2
            continue
        print(f"Unknown scheduler consume-worker-trajectory-report option: {arg}", file=sys.stderr)
        print(_SCHEDULER_CONSUME_WORKER_TRAJECTORY_REPORT_USAGE, file=sys.stderr)
        return 1

    if not report_path:
        print(_SCHEDULER_CONSUME_WORKER_TRAJECTORY_REPORT_USAGE, file=sys.stderr)
        print("Missing required option(s): --report-path", file=sys.stderr)
        return 1

    root = _find_project_root()
    try:
        from .runtime.orchestration import (
            WorkerTrajectoryReportConsumerRequest,
            consume_worker_trajectory_report,
        )

        result = consume_worker_trajectory_report(
            WorkerTrajectoryReportConsumerRequest(
                project_root=root,
                report_path=_resolve_project_path(root, report_path),
                caller_role=caller_role,
                actor=actor,
                current_event_id=current_event_id,
                title=title,
                event_kind=event_kind,
                start_if_missing=start_if_missing,
                trajectory_title=trajectory_title,
                guide_context=guide_context,
            )
        )
    except Exception as e:
        return _handle_error(
            "Error consuming worker trajectory report",
            e,
            category="scheduler_worker_trajectory_report_consume_failed",
        )

    payload = result.to_json_dict()
    _print_json(payload)
    return 0 if payload.get("ok") else 1


def _parse_provider_runtime_status_args(
    args: list[str],
    *,
    usage: str,
    command_name: str,
) -> dict[str, object] | None:
    parsed: dict[str, object] = {
        "snapshot_path": "",
        "event_log_path": "",
        "delivery_state_path": "",
        "runtime_invocation_log_path": "",
        "artifact_store_path": "",
        "target_task_ids": [],
        "latest_limit": 10,
    }
    cli_to_key = {
        "--snapshot-path": "snapshot_path",
        "--event-log-path": "event_log_path",
        "--delivery-state-path": "delivery_state_path",
        "--runtime-invocation-log-path": "runtime_invocation_log_path",
        "--artifact-store-path": "artifact_store_path",
        "--latest-limit": "latest_limit",
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--target-task-id":
            if i + 1 >= len(args):
                print(usage, file=sys.stderr)
                print("Missing value for --target-task-id", file=sys.stderr)
                return None
            target_ids = parsed["target_task_ids"]
            assert isinstance(target_ids, list)
            target_ids.append(args[i + 1])
            i += 2
            continue
        if arg not in cli_to_key:
            print(f"Unknown scheduler {command_name} option: {arg}", file=sys.stderr)
            print(usage, file=sys.stderr)
            return None
        if i + 1 >= len(args):
            print(usage, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return None
        key = cli_to_key[arg]
        value = args[i + 1]
        if key == "latest_limit":
            try:
                parsed[key] = int(value)
            except ValueError:
                print(usage, file=sys.stderr)
                print("--latest-limit must be an integer", file=sys.stderr)
                return None
        else:
            parsed[key] = value
        i += 2
    return parsed


def _parse_codex_runtime_status_args(args: list[str]) -> dict[str, object] | None:
    return _parse_provider_runtime_status_args(
        args,
        usage=_SCHEDULER_INSPECT_CODEX_RUNTIME_STATUS_USAGE,
        command_name="inspect-codex-runtime-status",
    )


def _parse_monitoring_snapshot_args(args: list[str]) -> dict[str, object] | None:
    parsed: dict[str, object] = {
        "snapshot_path": "",
        "event_log_path": "",
        "delivery_state_path": "",
        "runtime_invocation_log_path": "",
        "artifact_store_path": "",
        "live_codex_smoke_report_path": "",
        "target_task_ids": [],
        "latest_limit": 10,
    }
    cli_to_key = {
        "--snapshot-path": "snapshot_path",
        "--event-log-path": "event_log_path",
        "--delivery-state-path": "delivery_state_path",
        "--runtime-invocation-log-path": "runtime_invocation_log_path",
        "--artifact-store-path": "artifact_store_path",
        "--live-codex-smoke-report-path": "live_codex_smoke_report_path",
        "--latest-limit": "latest_limit",
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--target-task-id":
            if i + 1 >= len(args):
                print(_SCHEDULER_INSPECT_MONITORING_SNAPSHOT_USAGE, file=sys.stderr)
                print("Missing value for --target-task-id", file=sys.stderr)
                return None
            target_ids = parsed["target_task_ids"]
            assert isinstance(target_ids, list)
            target_ids.append(args[i + 1])
            i += 2
            continue
        if arg not in cli_to_key:
            print(f"Unknown scheduler inspect-monitoring-snapshot option: {arg}", file=sys.stderr)
            print(_SCHEDULER_INSPECT_MONITORING_SNAPSHOT_USAGE, file=sys.stderr)
            return None
        if i + 1 >= len(args):
            print(_SCHEDULER_INSPECT_MONITORING_SNAPSHOT_USAGE, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return None
        key = cli_to_key[arg]
        value = args[i + 1]
        if key == "latest_limit":
            try:
                parsed[key] = int(value)
            except ValueError:
                print(_SCHEDULER_INSPECT_MONITORING_SNAPSHOT_USAGE, file=sys.stderr)
                print("--latest-limit must be an integer", file=sys.stderr)
                return None
        else:
            parsed[key] = value
        i += 2
    return parsed


def cmd_scheduler_codex_delivery_supervisor_once(args: list[str]) -> int:
    """Run one bounded host-owned Codex pass over pending delivery records."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_CODEX_DELIVERY_SUPERVISOR_USAGE + "\n\n"
            "This command is a host-owned live Codex delivery supervisor pass. "
            "It consumes pending leader-worker delivery records for ready Codex "
            "scheduler tasks, invokes Codex through explicit host-authorized "
            "runtime wiring, and writes delivery acknowledgement plus compact "
            "runtime invocation audit. With --consume-success-results it first "
            "stores the successful output ExchangeArtifact and appends a "
            "task_completed scheduler event, then acknowledges delivery. If Codex "
            "surfaces permission requests, it instead stores review evidence, "
            "appends task_review_required, and marks delivery review_required. "
            "With explicit sandbox preflight and worker patch publication, "
            "git-worktree worker edits are exported as review-only "
            "worker_patch_review_proposal artifacts and are not applied. "
            "It does not mutate scheduler snapshots, expose MCP live-provider "
            "execution, persist raw transcripts, or mutate Local Work Trajectory.",
        )
        return 0

    parsed = _parse_codex_delivery_supervisor_args(args)
    if parsed is None:
        return 1
    if not parsed["snapshot_path"] or not parsed["event_log_path"]:
        print(_SCHEDULER_CODEX_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
        print("--snapshot-path and --event-log-path are required", file=sys.stderr)
        return 1
    if parsed["sandbox"] not in {"read-only", "workspace-write", "danger-full-access"}:
        print(_SCHEDULER_CODEX_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
        print("--sandbox must be read-only, workspace-write, or danger-full-access", file=sys.stderr)
        return 1
    if parsed["ask_for_approval"] not in {"untrusted", "on-request", "never"}:
        print(_SCHEDULER_CODEX_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
        print("--ask-for-approval must be untrusted, on-request, or never", file=sys.stderr)
        return 1
    if int(parsed["max_deliveries"]) < 0:
        print(_SCHEDULER_CODEX_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
        print("--max-deliveries must be non-negative", file=sys.stderr)
        return 1
    if int(parsed["runtime_invocation_max_attempts"]) < 1:
        print(_SCHEDULER_CODEX_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
        print("--runtime-invocation-max-attempts must be positive", file=sys.stderr)
        return 1
    if int(parsed["max_delivery_attempts_per_record"]) < 1:
        print(_SCHEDULER_CODEX_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
        print("--max-delivery-attempts-per-record must be positive", file=sys.stderr)
        return 1
    if float(parsed["runtime_invocation_backoff_seconds"]) < 0:
        print(_SCHEDULER_CODEX_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
        print("--runtime-invocation-backoff-seconds must be non-negative", file=sys.stderr)
        return 1
    if bool(parsed["publish_worker_patch_artifacts"]) and not bool(
        parsed["enable_sandbox_preflight"]
    ):
        print(_SCHEDULER_CODEX_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
        print(
            "--publish-worker-patch-artifacts requires --enable-sandbox-preflight",
            file=sys.stderr,
        )
        return 1

    root = _find_project_root()
    try:
        from .runtime.orchestration import (
            CodexCliClientConfig,
            CodexCliProcessClient,
            CodexDeliverySupervisorRequest,
            DEFAULT_EXCHANGE_ARTIFACT_STORE_RELATIVE_PATH,
            DEFAULT_LEADER_WORKER_DELIVERY_EVENT_LOG_RELATIVE_PATH,
            DEFAULT_LEADER_WORKER_DELIVERY_STATE_RELATIVE_PATH,
            DEFAULT_RUNTIME_INVOCATION_LOG_RELATIVE_PATH,
            run_codex_delivery_supervisor_once,
        )

        delivery_state_path = _resolve_project_path(
            root,
            str(parsed["delivery_state_path"])
            or DEFAULT_LEADER_WORKER_DELIVERY_STATE_RELATIVE_PATH,
        )
        delivery_log_path = _resolve_project_path(
            root,
            str(parsed["delivery_event_log_path"])
            or DEFAULT_LEADER_WORKER_DELIVERY_EVENT_LOG_RELATIVE_PATH,
        )
        runtime_log_path = (
            None
            if parsed["runtime_invocation_log_path"] is None
            else _resolve_project_path(
                root,
                str(parsed["runtime_invocation_log_path"])
                or DEFAULT_RUNTIME_INVOCATION_LOG_RELATIVE_PATH,
            )
        )
        artifact_store_path = _resolve_project_path(
            root,
            str(parsed["artifact_store_path"])
            or DEFAULT_EXCHANGE_ARTIFACT_STORE_RELATIVE_PATH,
        )
        codex_config = CodexCliClientConfig(
            executable=str(parsed["executable"]),
            cwd=str(parsed["cwd"]),
            model=str(parsed["model"]),
            sandbox=str(parsed["sandbox"]),  # type: ignore[arg-type]
            ask_for_approval=str(parsed["ask_for_approval"]),  # type: ignore[arg-type]
        )
        result = run_codex_delivery_supervisor_once(
            CodexDeliverySupervisorRequest(
                delivery_state_path=delivery_state_path,
                delivery_event_log_path=delivery_log_path,
                scheduler_snapshot_path=_resolve_project_path(root, str(parsed["snapshot_path"])),
                scheduler_event_log_path=_resolve_project_path(root, str(parsed["event_log_path"])),
                runtime_invocation_log_path=runtime_log_path,
                artifact_store_path=artifact_store_path,
                consume_success_results=bool(parsed["consume_success_results"]),
                replace_existing_result_artifact=bool(
                    parsed["replace_existing_result_artifact"]
                ),
                max_deliveries=int(parsed["max_deliveries"]),
                retry_failed_delivery=bool(parsed["retry_failed_delivery"]),
                max_delivery_attempts_per_record=int(
                    parsed["max_delivery_attempts_per_record"]
                ),
                timestamp=str(parsed["timestamp"]),
                host_id=str(parsed["host_id"]),
                host_invocation_id=str(parsed["host_invocation_id"]),
                requested_by="cli:codex-delivery-supervisor-once",
                reason=str(parsed["reason"]),
                grant_id=f"grant-{parsed['host_invocation_id']}",
                approved_by="cli:codex-delivery-supervisor-once",
                approved_at=str(parsed["timestamp"]),
                runtime_invocation_max_attempts=int(parsed["runtime_invocation_max_attempts"]),
                runtime_invocation_backoff_seconds=float(
                    parsed["runtime_invocation_backoff_seconds"]
                ),
                enable_sandbox_preflight=bool(parsed["enable_sandbox_preflight"]),
                workspace_root=(
                    _resolve_project_path(root, str(parsed["workspace_root"]))
                    if str(parsed["workspace_root"])
                    else root
                ),
                scratch_root=str(parsed["scratch_root"]),
                git_worktree_sandbox_root=(
                    None
                    if not str(parsed["git_worktree_sandbox_root"])
                    else _resolve_project_path(root, str(parsed["git_worktree_sandbox_root"]))
                ),
                git_executable=str(parsed["git_executable"]),
                publish_worker_patch_artifacts=bool(parsed["publish_worker_patch_artifacts"]),
                worker_patch_guide_agent_id=str(parsed["worker_patch_guide_agent_id"]),
                worker_patch_target_task_id=str(parsed["worker_patch_target_task_id"]),
            ),
            codex_cli_client=CodexCliProcessClient(codex_config),
        )
    except Exception as e:
        return _handle_error(
            "Error running Codex delivery supervisor",
            e,
            category="scheduler_codex_delivery_supervisor_failed",
        )

    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def cmd_scheduler_opencode_delivery_supervisor_once(args: list[str]) -> int:
    """Run one bounded host-owned OpenCode pass over pending delivery records."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_OPENCODE_DELIVERY_SUPERVISOR_USAGE + "\n\n"
            "This command is a host-owned live OpenCode delivery supervisor pass. "
            "It consumes pending leader-worker delivery records for ready OpenCode "
            "scheduler tasks, invokes OpenCode through explicit host-authorized "
            "runtime wiring, and writes delivery acknowledgement plus compact "
            "runtime invocation audit. With --consume-success-results it first "
            "stores the successful output ExchangeArtifact and appends a "
            "task_completed scheduler event, then acknowledges delivery. If "
            "OpenCode surfaces permission requests, it instead stores review "
            "evidence, appends task_review_required, and marks delivery "
            "review_required. This surface intentionally uses OpenCode host "
            "options such as --output-format instead of Codex sandbox or approval "
            "flags. By default it invokes `opencode run`; pass "
            "--opencode-transport server-api to call a host-owned running "
            "OpenCode server/API endpoint through the same runtime seam. With "
            "explicit sandbox preflight and worker patch publication, git-worktree "
            "worker edits are exported as review-only worker_patch_review_proposal "
            "artifacts and are not applied. "
            "It does not mutate scheduler snapshots, expose MCP live-provider "
            "execution, persist raw transcripts, apply source workspace patches, "
            "or mutate Local Work Trajectory.",
        )
        return 0

    parsed = _parse_opencode_delivery_supervisor_args(args)
    if parsed is None:
        return 1
    if not parsed["snapshot_path"] or not parsed["event_log_path"]:
        print(_SCHEDULER_OPENCODE_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
        print("--snapshot-path and --event-log-path are required", file=sys.stderr)
        return 1
    if parsed["output_format"] not in {"text", "json"}:
        print(_SCHEDULER_OPENCODE_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
        print("--output-format must be text or json", file=sys.stderr)
        return 1
    if parsed["opencode_transport"] not in {"cli", "server-api"}:
        print(_SCHEDULER_OPENCODE_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
        print("--opencode-transport must be cli or server-api", file=sys.stderr)
        return 1
    if float(parsed["server_api_timeout_seconds"]) <= 0:
        print(_SCHEDULER_OPENCODE_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
        print("--server-api-timeout-seconds must be positive", file=sys.stderr)
        return 1
    if parsed["session_id"] and parsed["continue_session"]:
        print(_SCHEDULER_OPENCODE_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
        print("cannot use --session-id with --continue-session", file=sys.stderr)
        return 1
    if parsed["fork_session"] and not (parsed["session_id"] or parsed["continue_session"]):
        print(_SCHEDULER_OPENCODE_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
        print("--fork-session requires --session-id or --continue-session", file=sys.stderr)
        return 1
    if int(parsed["max_deliveries"]) < 0:
        print(_SCHEDULER_OPENCODE_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
        print("--max-deliveries must be non-negative", file=sys.stderr)
        return 1
    if int(parsed["runtime_invocation_max_attempts"]) < 1:
        print(_SCHEDULER_OPENCODE_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
        print("--runtime-invocation-max-attempts must be positive", file=sys.stderr)
        return 1
    if int(parsed["max_delivery_attempts_per_record"]) < 1:
        print(_SCHEDULER_OPENCODE_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
        print("--max-delivery-attempts-per-record must be positive", file=sys.stderr)
        return 1
    if float(parsed["runtime_invocation_backoff_seconds"]) < 0:
        print(_SCHEDULER_OPENCODE_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
        print("--runtime-invocation-backoff-seconds must be non-negative", file=sys.stderr)
        return 1
    if bool(parsed["publish_worker_patch_artifacts"]) and not bool(
        parsed["enable_sandbox_preflight"]
    ):
        print(_SCHEDULER_OPENCODE_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
        print(
            "--publish-worker-patch-artifacts requires --enable-sandbox-preflight",
            file=sys.stderr,
        )
        return 1

    root = _find_project_root()
    try:
        from .runtime.orchestration import (
            CodexDeliverySupervisorRequest,
            DEFAULT_EXCHANGE_ARTIFACT_STORE_RELATIVE_PATH,
            DEFAULT_LEADER_WORKER_DELIVERY_EVENT_LOG_RELATIVE_PATH,
            DEFAULT_LEADER_WORKER_DELIVERY_STATE_RELATIVE_PATH,
            DEFAULT_RUNTIME_INVOCATION_LOG_RELATIVE_PATH,
            OpenCodeCliClientConfig,
            run_opencode_delivery_supervisor_once,
        )

        delivery_state_path = _resolve_project_path(
            root,
            str(parsed["delivery_state_path"])
            or DEFAULT_LEADER_WORKER_DELIVERY_STATE_RELATIVE_PATH,
        )
        delivery_log_path = _resolve_project_path(
            root,
            str(parsed["delivery_event_log_path"])
            or DEFAULT_LEADER_WORKER_DELIVERY_EVENT_LOG_RELATIVE_PATH,
        )
        runtime_log_path = (
            None
            if parsed["runtime_invocation_log_path"] is None
            else _resolve_project_path(
                root,
                str(parsed["runtime_invocation_log_path"])
                or DEFAULT_RUNTIME_INVOCATION_LOG_RELATIVE_PATH,
            )
        )
        artifact_store_path = _resolve_project_path(
            root,
            str(parsed["artifact_store_path"])
            or DEFAULT_EXCHANGE_ARTIFACT_STORE_RELATIVE_PATH,
        )
        opencode_config = OpenCodeCliClientConfig(
            executable=str(parsed["executable"]),
            cwd=str(parsed["cwd"]),
            model=str(parsed["model"]),
            output_format=str(parsed["output_format"]),  # type: ignore[arg-type]
            attach_url=str(parsed["attach_url"]),
            session_id=str(parsed["session_id"]),
            continue_session=bool(parsed["continue_session"]),
            fork_session=bool(parsed["fork_session"]),
        )
        opencode_client = _opencode_client_from_parsed_transport(
            parsed,
            opencode_config,
            cli_surface="opencode-delivery-supervisor-once",
        )
        result = run_opencode_delivery_supervisor_once(
            CodexDeliverySupervisorRequest(
                delivery_state_path=delivery_state_path,
                delivery_event_log_path=delivery_log_path,
                scheduler_snapshot_path=_resolve_project_path(root, str(parsed["snapshot_path"])),
                scheduler_event_log_path=_resolve_project_path(root, str(parsed["event_log_path"])),
                runtime_invocation_log_path=runtime_log_path,
                artifact_store_path=artifact_store_path,
                consume_success_results=bool(parsed["consume_success_results"]),
                replace_existing_result_artifact=bool(
                    parsed["replace_existing_result_artifact"]
                ),
                max_deliveries=int(parsed["max_deliveries"]),
                retry_failed_delivery=bool(parsed["retry_failed_delivery"]),
                max_delivery_attempts_per_record=int(
                    parsed["max_delivery_attempts_per_record"]
                ),
                timestamp=str(parsed["timestamp"]),
                host_id=str(parsed["host_id"]),
                host_invocation_id=str(parsed["host_invocation_id"]),
                requested_by="cli:opencode-delivery-supervisor-once",
                reason=str(parsed["reason"]),
                grant_id=f"grant-{parsed['host_invocation_id']}",
                approved_by="cli:opencode-delivery-supervisor-once",
                approved_at=str(parsed["timestamp"]),
                runtime_invocation_max_attempts=int(parsed["runtime_invocation_max_attempts"]),
                runtime_invocation_backoff_seconds=float(
                    parsed["runtime_invocation_backoff_seconds"]
                ),
                enable_sandbox_preflight=bool(parsed["enable_sandbox_preflight"]),
                workspace_root=(
                    _resolve_project_path(root, str(parsed["workspace_root"]))
                    if str(parsed["workspace_root"])
                    else root
                ),
                scratch_root=str(parsed["scratch_root"]),
                git_worktree_sandbox_root=(
                    None
                    if not str(parsed["git_worktree_sandbox_root"])
                    else _resolve_project_path(root, str(parsed["git_worktree_sandbox_root"]))
                ),
                git_executable=str(parsed["git_executable"]),
                publish_worker_patch_artifacts=bool(parsed["publish_worker_patch_artifacts"]),
                worker_patch_guide_agent_id=str(parsed["worker_patch_guide_agent_id"]),
                worker_patch_target_task_id=str(parsed["worker_patch_target_task_id"]),
                continuous_worker_binding_ledger_path=_resolve_project_path(
                    root,
                    str(parsed["worker_binding_ledger_path"]),
                ),
                continuous_worker_binding_event_log_path=_resolve_project_path(
                    root,
                    str(parsed["worker_binding_event_log_path"]),
                ),
                enable_continuous_worker_binding_lookup=bool(
                    parsed["worker_binding_lookup"]
                ),
                opencode_session_ledger_path=_resolve_project_path(
                    root,
                    str(parsed["session_ledger_path"]),
                ),
                opencode_enable_session_lookup=bool(parsed["session_ledger_lookup"]),
            ),
            opencode_cli_client=opencode_client,
        )
    except Exception as e:
        return _handle_error(
            "Error running OpenCode delivery supervisor",
            e,
            category="scheduler_opencode_delivery_supervisor_failed",
        )

    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def _parse_codex_delivery_supervisor_args(args: list[str]) -> dict[str, object] | None:
    parsed: dict[str, object] = {
        "snapshot_path": "",
        "event_log_path": "",
        "delivery_state_path": "",
        "delivery_event_log_path": "",
        "runtime_invocation_log_path": ".dbc/runtime/invocations.jsonl",
        "artifact_store_path": ".dbc/orchestration/exchange-artifacts.json",
        "consume_success_results": False,
        "replace_existing_result_artifact": False,
        "max_deliveries": 1,
        "retry_failed_delivery": False,
        "max_delivery_attempts_per_record": 2,
        "executable": "codex",
        "cwd": "",
        "model": "",
        "sandbox": "workspace-write",
        "ask_for_approval": "never",
        "host_id": "host:codex-delivery-supervisor",
        "host_invocation_id": "host-owned-codex-delivery-supervisor-once",
        "reason": "host-owned Codex delivery supervisor pass from CLI",
        "timestamp": "",
        "runtime_invocation_max_attempts": 2,
        "runtime_invocation_backoff_seconds": 0.0,
        "enable_sandbox_preflight": False,
        "workspace_root": "",
        "scratch_root": ".dbc/scratch",
        "git_worktree_sandbox_root": "",
        "git_executable": "git",
        "publish_worker_patch_artifacts": False,
        "worker_patch_guide_agent_id": "agent:guide",
        "worker_patch_target_task_id": "",
    }
    options = set(parsed)
    cli_to_key = {
        "--snapshot-path": "snapshot_path",
        "--event-log-path": "event_log_path",
        "--delivery-state-path": "delivery_state_path",
        "--delivery-event-log-path": "delivery_event_log_path",
        "--runtime-invocation-log-path": "runtime_invocation_log_path",
        "--artifact-store-path": "artifact_store_path",
        "--max-deliveries": "max_deliveries",
        "--max-delivery-attempts-per-record": "max_delivery_attempts_per_record",
        "--executable": "executable",
        "--cwd": "cwd",
        "--model": "model",
        "--sandbox": "sandbox",
        "--ask-for-approval": "ask_for_approval",
        "--host-id": "host_id",
        "--host-invocation-id": "host_invocation_id",
        "--reason": "reason",
        "--timestamp": "timestamp",
        "--runtime-invocation-max-attempts": "runtime_invocation_max_attempts",
        "--runtime-invocation-backoff-seconds": "runtime_invocation_backoff_seconds",
        "--workspace-root": "workspace_root",
        "--scratch-root": "scratch_root",
        "--git-worktree-sandbox-root": "git_worktree_sandbox_root",
        "--git-executable": "git_executable",
        "--worker-patch-guide-agent-id": "worker_patch_guide_agent_id",
        "--worker-patch-target-task-id": "worker_patch_target_task_id",
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--consume-success-results":
            parsed["consume_success_results"] = True
            i += 1
            continue
        if arg == "--replace-existing-result-artifact":
            parsed["replace_existing_result_artifact"] = True
            i += 1
            continue
        if arg == "--retry-failed-delivery":
            parsed["retry_failed_delivery"] = True
            i += 1
            continue
        if arg == "--enable-sandbox-preflight":
            parsed["enable_sandbox_preflight"] = True
            i += 1
            continue
        if arg == "--publish-worker-patch-artifacts":
            parsed["publish_worker_patch_artifacts"] = True
            i += 1
            continue
        if arg not in cli_to_key:
            print(f"Unknown scheduler codex-delivery-supervisor-once option: {arg}", file=sys.stderr)
            print(_SCHEDULER_CODEX_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
            return None
        if i + 1 >= len(args):
            print(_SCHEDULER_CODEX_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return None
        key = cli_to_key[arg]
        value = args[i + 1]
        if key in {
            "max_deliveries",
            "max_delivery_attempts_per_record",
            "runtime_invocation_max_attempts",
        }:
            try:
                parsed[key] = int(value)
            except ValueError:
                print(_SCHEDULER_CODEX_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
                print(f"{arg} must be an integer", file=sys.stderr)
                return None
        elif key == "runtime_invocation_backoff_seconds":
            try:
                parsed[key] = float(value)
            except ValueError:
                print(_SCHEDULER_CODEX_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
                print(f"{arg} must be a number", file=sys.stderr)
                return None
        else:
            parsed[key] = value
        i += 2
    unknown_internal = set(parsed) - options
    if unknown_internal:
        raise AssertionError(f"unexpected codex delivery parser keys: {unknown_internal}")
    return parsed


def _parse_opencode_delivery_supervisor_args(args: list[str]) -> dict[str, object] | None:
    parsed: dict[str, object] = {
        "snapshot_path": "",
        "event_log_path": "",
        "delivery_state_path": "",
        "delivery_event_log_path": "",
        "runtime_invocation_log_path": ".dbc/runtime/opencode-delivery-invocations.jsonl",
        "artifact_store_path": ".dbc/orchestration/exchange-artifacts.json",
        "consume_success_results": False,
        "replace_existing_result_artifact": False,
        "max_deliveries": 1,
        "retry_failed_delivery": False,
        "max_delivery_attempts_per_record": 2,
        "executable": "opencode",
        "cwd": "",
        "model": "",
        "output_format": "json",
        "opencode_transport": "cli",
        "attach_url": "",
        "session_id": "",
        "continue_session": False,
        "fork_session": False,
        "server_api_base_url": "http://127.0.0.1:4096",
        "server_api_session_id": "",
        "server_api_health_path": "/global/health",
        "server_api_doc_path": "/doc",
        "server_api_timeout_seconds": 30.0,
        "server_api_username_env_var": "OPENCODE_SERVER_USERNAME",
        "server_api_password_env_var": "OPENCODE_SERVER_PASSWORD",
        "worker_binding_ledger_path": ".dbc/runtime/continuous-worker-bindings.json",
        "worker_binding_event_log_path": ".dbc/runtime/continuous-worker-binding-events.jsonl",
        "worker_binding_lookup": True,
        "session_ledger_path": ".dbc/runtime/opencode-session-ledger.json",
        "session_ledger_lookup": True,
        "host_id": "host:opencode-delivery-supervisor",
        "host_invocation_id": "host-owned-opencode-delivery-supervisor-once",
        "reason": "host-owned OpenCode delivery supervisor pass from CLI",
        "timestamp": "",
        "runtime_invocation_max_attempts": 2,
        "runtime_invocation_backoff_seconds": 0.0,
        "enable_sandbox_preflight": False,
        "workspace_root": "",
        "scratch_root": ".dbc/scratch",
        "git_worktree_sandbox_root": "",
        "git_executable": "git",
        "publish_worker_patch_artifacts": False,
        "worker_patch_guide_agent_id": "agent:guide",
        "worker_patch_target_task_id": "",
    }
    options = set(parsed)
    cli_to_key = {
        "--snapshot-path": "snapshot_path",
        "--event-log-path": "event_log_path",
        "--delivery-state-path": "delivery_state_path",
        "--delivery-event-log-path": "delivery_event_log_path",
        "--runtime-invocation-log-path": "runtime_invocation_log_path",
        "--artifact-store-path": "artifact_store_path",
        "--max-deliveries": "max_deliveries",
        "--max-delivery-attempts-per-record": "max_delivery_attempts_per_record",
        "--executable": "executable",
        "--cwd": "cwd",
        "--model": "model",
        "--output-format": "output_format",
        "--opencode-transport": "opencode_transport",
        "--attach-url": "attach_url",
        "--session-id": "session_id",
        "--server-api-base-url": "server_api_base_url",
        "--server-api-session-id": "server_api_session_id",
        "--server-api-health-path": "server_api_health_path",
        "--server-api-doc-path": "server_api_doc_path",
        "--server-api-timeout-seconds": "server_api_timeout_seconds",
        "--server-api-username-env-var": "server_api_username_env_var",
        "--server-api-password-env-var": "server_api_password_env_var",
        "--worker-binding-ledger-path": "worker_binding_ledger_path",
        "--worker-binding-event-log-path": "worker_binding_event_log_path",
        "--session-ledger-path": "session_ledger_path",
        "--host-id": "host_id",
        "--host-invocation-id": "host_invocation_id",
        "--reason": "reason",
        "--timestamp": "timestamp",
        "--runtime-invocation-max-attempts": "runtime_invocation_max_attempts",
        "--runtime-invocation-backoff-seconds": "runtime_invocation_backoff_seconds",
        "--workspace-root": "workspace_root",
        "--scratch-root": "scratch_root",
        "--git-worktree-sandbox-root": "git_worktree_sandbox_root",
        "--git-executable": "git_executable",
        "--worker-patch-guide-agent-id": "worker_patch_guide_agent_id",
        "--worker-patch-target-task-id": "worker_patch_target_task_id",
    }
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--consume-success-results":
            parsed["consume_success_results"] = True
            i += 1
            continue
        if arg == "--replace-existing-result-artifact":
            parsed["replace_existing_result_artifact"] = True
            i += 1
            continue
        if arg == "--retry-failed-delivery":
            parsed["retry_failed_delivery"] = True
            i += 1
            continue
        if arg == "--enable-sandbox-preflight":
            parsed["enable_sandbox_preflight"] = True
            i += 1
            continue
        if arg == "--publish-worker-patch-artifacts":
            parsed["publish_worker_patch_artifacts"] = True
            i += 1
            continue
        if arg == "--continue-session":
            parsed["continue_session"] = True
            i += 1
            continue
        if arg == "--fork-session":
            parsed["fork_session"] = True
            i += 1
            continue
        if arg == "--no-session-ledger-lookup":
            parsed["session_ledger_lookup"] = False
            i += 1
            continue
        if arg == "--no-worker-binding-lookup":
            parsed["worker_binding_lookup"] = False
            i += 1
            continue
        if arg in {"--sandbox", "--ask-for-approval"}:
            print(
                f"{arg} is Codex-specific and is not supported by opencode-delivery-supervisor-once",
                file=sys.stderr,
            )
            print(_SCHEDULER_OPENCODE_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
            return None
        if arg not in cli_to_key:
            print(f"Unknown scheduler opencode-delivery-supervisor-once option: {arg}", file=sys.stderr)
            print(_SCHEDULER_OPENCODE_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
            return None
        if i + 1 >= len(args):
            print(_SCHEDULER_OPENCODE_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return None
        key = cli_to_key[arg]
        value = args[i + 1]
        if key in {
            "max_deliveries",
            "max_delivery_attempts_per_record",
            "runtime_invocation_max_attempts",
        }:
            try:
                parsed[key] = int(value)
            except ValueError:
                print(_SCHEDULER_OPENCODE_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
                print(f"{arg} must be an integer", file=sys.stderr)
                return None
        elif key in {"runtime_invocation_backoff_seconds", "server_api_timeout_seconds"}:
            try:
                parsed[key] = float(value)
            except ValueError:
                print(_SCHEDULER_OPENCODE_DELIVERY_SUPERVISOR_USAGE, file=sys.stderr)
                print(f"{arg} must be a number", file=sys.stderr)
                return None
        else:
            parsed[key] = value
        i += 2
    unknown_internal = set(parsed) - options
    if unknown_internal:
        raise AssertionError(f"unexpected opencode delivery parser keys: {unknown_internal}")
    return parsed


def _parse_opencode_delivery_loop_args(
    args: list[str],
    *,
    usage: str = _SCHEDULER_OPENCODE_DELIVERY_SUPERVISOR_LOOP_USAGE,
    command_name: str = "opencode-delivery-supervisor-loop",
    include_report_options: bool = False,
    default_initialize_fixture: bool = False,
    default_fixture: str = "simple",
    default_host_id: str = "host:opencode-delivery-supervisor-loop",
    default_host_invocation_id: str = "host-owned-opencode-delivery-supervisor-loop",
    default_max_ticks: int = 3,
    default_max_deliveries: int = 3,
    default_max_runtime_failures: int = 1,
    default_max_concurrent_deliveries: int = 1,
    default_runtime_invocation_log_path: str = ".dbc/runtime/opencode-delivery-loop-invocations.jsonl",
) -> dict[str, object] | None:
    parsed: dict[str, object] = {
        "snapshot_path": "",
        "event_log_path": "",
        "artifact_store_path": "",
        "dispatcher_state_path": "",
        "dispatch_event_log_path": "",
        "delivery_state_path": "",
        "delivery_event_log_path": "",
        "runtime_invocation_log_path": default_runtime_invocation_log_path,
        "initialize_fixture": default_initialize_fixture,
        "replace_existing_fixture": False,
        "fixture": default_fixture,
        "replace_existing_result_artifact": False,
        "target_task_id": "opencode-smoke:worker",
        "parallel_task_id": "opencode-smoke:parallel-worker",
        "waiting_task_id": "opencode-smoke:waiting-non-opencode",
        "followup_task_id": "opencode-smoke:followup",
        "executable": "opencode",
        "cwd": "",
        "model": "",
        "output_format": "json",
        "opencode_transport": "cli",
        "attach_url": "",
        "session_id": "",
        "continue_session": False,
        "fork_session": False,
        "server_api_base_url": "http://127.0.0.1:4096",
        "server_api_session_id": "",
        "server_api_health_path": "/global/health",
        "server_api_doc_path": "/doc",
        "server_api_timeout_seconds": 30.0,
        "server_api_username_env_var": "OPENCODE_SERVER_USERNAME",
        "server_api_password_env_var": "OPENCODE_SERVER_PASSWORD",
        "worker_binding_ledger_path": ".dbc/runtime/continuous-worker-bindings.json",
        "worker_binding_event_log_path": ".dbc/runtime/continuous-worker-binding-events.jsonl",
        "worker_binding_lookup": True,
        "session_ledger_path": ".dbc/runtime/opencode-session-ledger.json",
        "session_ledger_lookup": True,
        "host_id": default_host_id,
        "host_invocation_id": default_host_invocation_id,
        "timestamp": "",
        "runtime_invocation_max_attempts": 2,
        "runtime_invocation_backoff_seconds": 0.0,
        "enable_sandbox_preflight": False,
        "workspace_root": "",
        "scratch_root": ".dbc/scratch",
        "git_worktree_sandbox_root": "",
        "git_executable": "git",
        "publish_worker_patch_artifacts": False,
        "worker_patch_guide_agent_id": "agent:guide",
        "worker_patch_target_task_id": "",
        "max_ticks": default_max_ticks,
        "max_deliveries": default_max_deliveries,
        "max_runtime_failures": default_max_runtime_failures,
        "max_delivery_attempts_per_record": 2,
        "max_concurrent_deliveries": default_max_concurrent_deliveries,
        "report_path": "",
    }
    if not include_report_options:
        parsed.pop("report_path")
    options = set(parsed)
    cli_to_key = {
        "--snapshot-path": "snapshot_path",
        "--event-log-path": "event_log_path",
        "--artifact-store-path": "artifact_store_path",
        "--dispatcher-state-path": "dispatcher_state_path",
        "--dispatch-event-log-path": "dispatch_event_log_path",
        "--delivery-state-path": "delivery_state_path",
        "--delivery-event-log-path": "delivery_event_log_path",
        "--runtime-invocation-log-path": "runtime_invocation_log_path",
        "--fixture": "fixture",
        "--target-task-id": "target_task_id",
        "--parallel-task-id": "parallel_task_id",
        "--waiting-task-id": "waiting_task_id",
        "--followup-task-id": "followup_task_id",
        "--executable": "executable",
        "--cwd": "cwd",
        "--model": "model",
        "--output-format": "output_format",
        "--opencode-transport": "opencode_transport",
        "--attach-url": "attach_url",
        "--session-id": "session_id",
        "--server-api-base-url": "server_api_base_url",
        "--server-api-session-id": "server_api_session_id",
        "--server-api-health-path": "server_api_health_path",
        "--server-api-doc-path": "server_api_doc_path",
        "--server-api-timeout-seconds": "server_api_timeout_seconds",
        "--server-api-username-env-var": "server_api_username_env_var",
        "--server-api-password-env-var": "server_api_password_env_var",
        "--worker-binding-ledger-path": "worker_binding_ledger_path",
        "--worker-binding-event-log-path": "worker_binding_event_log_path",
        "--session-ledger-path": "session_ledger_path",
        "--host-id": "host_id",
        "--host-invocation-id": "host_invocation_id",
        "--timestamp": "timestamp",
        "--runtime-invocation-max-attempts": "runtime_invocation_max_attempts",
        "--runtime-invocation-backoff-seconds": "runtime_invocation_backoff_seconds",
        "--workspace-root": "workspace_root",
        "--scratch-root": "scratch_root",
        "--git-worktree-sandbox-root": "git_worktree_sandbox_root",
        "--git-executable": "git_executable",
        "--worker-patch-guide-agent-id": "worker_patch_guide_agent_id",
        "--worker-patch-target-task-id": "worker_patch_target_task_id",
        "--max-ticks": "max_ticks",
        "--max-deliveries": "max_deliveries",
        "--max-runtime-failures": "max_runtime_failures",
        "--max-delivery-attempts-per-record": "max_delivery_attempts_per_record",
        "--max-concurrent-deliveries": "max_concurrent_deliveries",
    }
    if include_report_options:
        cli_to_key["--report-path"] = "report_path"
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--initialize-fixture":
            parsed["initialize_fixture"] = True
            i += 1
            continue
        if arg == "--replace-existing-fixture":
            parsed["replace_existing_fixture"] = True
            i += 1
            continue
        if arg == "--replace-existing-result-artifact":
            parsed["replace_existing_result_artifact"] = True
            i += 1
            continue
        if arg == "--enable-sandbox-preflight":
            parsed["enable_sandbox_preflight"] = True
            i += 1
            continue
        if arg == "--publish-worker-patch-artifacts":
            parsed["publish_worker_patch_artifacts"] = True
            i += 1
            continue
        if arg == "--continue-session":
            parsed["continue_session"] = True
            i += 1
            continue
        if arg == "--fork-session":
            parsed["fork_session"] = True
            i += 1
            continue
        if arg == "--no-session-ledger-lookup":
            parsed["session_ledger_lookup"] = False
            i += 1
            continue
        if arg == "--no-worker-binding-lookup":
            parsed["worker_binding_lookup"] = False
            i += 1
            continue
        if arg in {
            "--sandbox",
            "--ask-for-approval",
        }:
            print(
                f"{arg} is Codex-specific and is not supported by {command_name}",
                file=sys.stderr,
            )
            print(usage, file=sys.stderr)
            return None
        if arg not in cli_to_key:
            print(f"Unknown scheduler {command_name} option: {arg}", file=sys.stderr)
            print(usage, file=sys.stderr)
            return None
        if i + 1 >= len(args):
            print(usage, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return None
        key = cli_to_key[arg]
        value = args[i + 1]
        if key in {
            "runtime_invocation_max_attempts",
            "max_ticks",
            "max_deliveries",
            "max_runtime_failures",
            "max_delivery_attempts_per_record",
            "max_concurrent_deliveries",
        }:
            try:
                parsed[key] = int(value)
            except ValueError:
                print(usage, file=sys.stderr)
                print(f"{arg} must be an integer", file=sys.stderr)
                return None
        elif key in {"runtime_invocation_backoff_seconds", "server_api_timeout_seconds"}:
            try:
                parsed[key] = float(value)
            except ValueError:
                print(usage, file=sys.stderr)
                print(f"{arg} must be a number", file=sys.stderr)
                return None
        else:
            parsed[key] = value
        i += 2
    unknown_internal = set(parsed) - options
    if unknown_internal:
        raise AssertionError(f"unexpected {command_name} parser keys: {unknown_internal}")
    return parsed


def _validate_opencode_delivery_loop_parsed_args(
    parsed: dict[str, object],
    *,
    usage: str,
) -> str:
    if parsed["fixture"] not in {"simple", "multilane"}:
        return "--fixture must be simple or multilane"
    if parsed["output_format"] not in {"text", "json"}:
        return "--output-format must be text or json"
    if parsed["opencode_transport"] not in {"cli", "server-api"}:
        return "--opencode-transport must be cli or server-api"
    if float(parsed["server_api_timeout_seconds"]) <= 0:
        return "--server-api-timeout-seconds must be positive"
    if parsed["session_id"] and parsed["continue_session"]:
        return "cannot use --session-id with --continue-session"
    if parsed["fork_session"] and not (parsed["session_id"] or parsed["continue_session"]):
        return "--fork-session requires --session-id or --continue-session"
    if int(parsed["runtime_invocation_max_attempts"]) < 1:
        return "--runtime-invocation-max-attempts must be positive"
    if float(parsed["runtime_invocation_backoff_seconds"]) < 0:
        return "--runtime-invocation-backoff-seconds must be non-negative"
    if int(parsed["max_ticks"]) < 0:
        return "--max-ticks must be non-negative"
    if int(parsed["max_deliveries"]) < 0:
        return "--max-deliveries must be non-negative"
    if int(parsed["max_runtime_failures"]) < 0:
        return "--max-runtime-failures must be non-negative"
    if int(parsed["max_delivery_attempts_per_record"]) < 1:
        return "--max-delivery-attempts-per-record must be positive"
    if int(parsed["max_concurrent_deliveries"]) < 1:
        return "--max-concurrent-deliveries must be positive"
    if bool(parsed["publish_worker_patch_artifacts"]) and not bool(
        parsed["enable_sandbox_preflight"]
    ):
        return "--publish-worker-patch-artifacts requires --enable-sandbox-preflight"
    return ""


def cmd_scheduler_codex_delivery_e2e_smoke(args: list[str]) -> int:
    """Run the C1 Codex delivery/result-consumer E2E smoke."""

    if args and args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_CODEX_DELIVERY_E2E_SMOKE_USAGE + "\n\n"
            "This command is a host-owned C1 smoke for Codex CLI as a "
            "scheduler-owned worker runtime. It can initialize one narrow "
            "scheduler fixture, then runs dispatcher tick, delivery sync, "
            "Codex delivery with result consumption, and scheduler recovery. "
            "It fails closed before mutation when Codex readiness is negative. "
            "It is not the continuous supervisor loop, does not resume "
            "interrupted sessions, does not expose MCP live-provider execution, "
            "does not apply source-workspace patches, and does not mutate "
            "Local Work Trajectory.",
        )
        return 0

    parsed = _parse_codex_delivery_e2e_smoke_args(args)
    if parsed is None:
        return 1
    validation_error = _validate_codex_delivery_smoke_parsed_args(
        parsed,
        usage=_SCHEDULER_CODEX_DELIVERY_E2E_SMOKE_USAGE,
    )
    if validation_error:
        print(_SCHEDULER_CODEX_DELIVERY_E2E_SMOKE_USAGE, file=sys.stderr)
        print(validation_error, file=sys.stderr)
        return 1

    try:
        from .runtime.orchestration import (
            run_codex_delivery_e2e_smoke,
        )

        request, codex_config = _codex_delivery_smoke_cli_objects(parsed)
        result = run_codex_delivery_e2e_smoke(
            request,
            codex_cli_client=_codex_process_client_from_config(codex_config),
        )
    except Exception as e:
        return _handle_error(
            "Error running Codex delivery E2E smoke",
            e,
            category="scheduler_codex_delivery_e2e_smoke_failed",
        )

    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def cmd_scheduler_opencode_delivery_e2e_smoke(args: list[str]) -> int:
    """Run the C1 OpenCode delivery/result-consumer E2E smoke."""

    if args and args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_OPENCODE_DELIVERY_E2E_SMOKE_USAGE + "\n\n"
            "This command is a host-owned C1 smoke for OpenCode CLI as a "
            "scheduler-owned worker runtime. It can initialize one narrow "
            "scheduler fixture, then runs dispatcher tick, delivery sync, "
            "OpenCode delivery with result consumption, and scheduler recovery. "
            "It fails closed before mutation when OpenCode readiness is negative. "
            "This surface intentionally uses OpenCode host options such as "
            "--output-format and attach/session selectors instead of Codex "
            "sandbox or approval flags. It is not the bounded supervisor loop, "
            "does not start or manage opencode serve, does not expose MCP "
            "live-provider execution, does not apply source-workspace patches, "
            "and does not mutate Local Work Trajectory.",
        )
        return 0

    parsed = _parse_opencode_delivery_loop_args(
        args,
        usage=_SCHEDULER_OPENCODE_DELIVERY_E2E_SMOKE_USAGE,
        command_name="opencode-delivery-e2e-smoke",
        default_host_id="host:opencode-delivery-e2e-smoke",
        default_host_invocation_id="host-owned-opencode-delivery-e2e-smoke",
        default_runtime_invocation_log_path=(
            ".dbc/runtime/opencode-delivery-e2e-smoke-invocations.jsonl"
        ),
    )
    if parsed is None:
        return 1
    validation_error = _validate_opencode_delivery_loop_parsed_args(
        parsed,
        usage=_SCHEDULER_OPENCODE_DELIVERY_E2E_SMOKE_USAGE,
    )
    if validation_error:
        print(_SCHEDULER_OPENCODE_DELIVERY_E2E_SMOKE_USAGE, file=sys.stderr)
        print(validation_error, file=sys.stderr)
        return 1

    try:
        from .runtime.orchestration import (
            run_opencode_delivery_e2e_smoke,
        )

        smoke_request, opencode_config = _opencode_delivery_loop_cli_objects(
            parsed,
            default_snapshot_path=".dbc/scheduler/opencode-delivery-e2e-smoke-state.json",
            default_event_log_path=".dbc/scheduler/opencode-delivery-e2e-smoke-events.jsonl",
            default_runtime_invocation_log_path=(
                ".dbc/runtime/opencode-delivery-e2e-smoke-invocations.jsonl"
            ),
            trajectory_id="opencode-delivery-e2e-smoke",
        )
        result = run_opencode_delivery_e2e_smoke(
            smoke_request,
            opencode_cli_client=_opencode_client_from_parsed_transport(
                parsed,
                opencode_config,
                cli_surface="opencode-delivery-e2e-smoke",
            ),
        )
    except Exception as e:
        return _handle_error(
            "Error running OpenCode delivery E2E smoke",
            e,
            category="scheduler_opencode_delivery_e2e_smoke_failed",
        )

    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def cmd_scheduler_codex_delivery_supervisor_loop(args: list[str]) -> int:
    """Run the bounded C2 Codex supervisor loop."""

    if args and args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_CODEX_DELIVERY_SUPERVISOR_LOOP_USAGE + "\n\n"
            "This command is a bounded host-owned C2 loop for Codex CLI as a "
            "scheduler-owned worker runtime. Each iteration recovers scheduler "
            "state, marks newly admissible tasks ready, persists dispatcher "
            "decisions, syncs delivery records, runs Codex delivery with result "
            "consumption, and recovers again. It has explicit max ticks, "
            "deliveries, and runtime failures. It is not a background daemon, "
            "and --fixture multilane seeds a repeatable multi-lane fixture "
            "for lane-aware continuous progress validation. By default the "
            "loop runs deliveries serially; pass --max-concurrent-deliveries "
            "above 1 to run independent lane-distinct Codex invocations "
            "concurrently while keeping writeback serialized. It "
            "can retry eligible failed Codex delivery records after restart, "
            "can publish git-worktree worker edits as review-only patch "
            "artifacts when sandbox preflight is explicitly enabled, "
            "does not resume a live process mid-turn, does not expose MCP "
            "live-provider execution, does not apply source-workspace patches, "
            "and does not mutate Local Work Trajectory.",
        )
        return 0

    parsed = _parse_codex_delivery_e2e_smoke_args(
        args,
        usage=_SCHEDULER_CODEX_DELIVERY_SUPERVISOR_LOOP_USAGE,
        command_name="codex-delivery-supervisor-loop",
        include_loop_options=True,
    )
    if parsed is None:
        return 1
    validation_error = _validate_codex_delivery_smoke_parsed_args(
        parsed,
        usage=_SCHEDULER_CODEX_DELIVERY_SUPERVISOR_LOOP_USAGE,
    )
    if validation_error:
        print(_SCHEDULER_CODEX_DELIVERY_SUPERVISOR_LOOP_USAGE, file=sys.stderr)
        print(validation_error, file=sys.stderr)
        return 1
    if int(parsed["max_ticks"]) < 0:
        print(_SCHEDULER_CODEX_DELIVERY_SUPERVISOR_LOOP_USAGE, file=sys.stderr)
        print("--max-ticks must be non-negative", file=sys.stderr)
        return 1
    if int(parsed["max_deliveries"]) < 0:
        print(_SCHEDULER_CODEX_DELIVERY_SUPERVISOR_LOOP_USAGE, file=sys.stderr)
        print("--max-deliveries must be non-negative", file=sys.stderr)
        return 1
    if int(parsed["max_runtime_failures"]) < 0:
        print(_SCHEDULER_CODEX_DELIVERY_SUPERVISOR_LOOP_USAGE, file=sys.stderr)
        print("--max-runtime-failures must be non-negative", file=sys.stderr)
        return 1
    if int(parsed["max_delivery_attempts_per_record"]) < 1:
        print(_SCHEDULER_CODEX_DELIVERY_SUPERVISOR_LOOP_USAGE, file=sys.stderr)
        print("--max-delivery-attempts-per-record must be positive", file=sys.stderr)
        return 1
    if int(parsed["max_concurrent_deliveries"]) < 1:
        print(_SCHEDULER_CODEX_DELIVERY_SUPERVISOR_LOOP_USAGE, file=sys.stderr)
        print("--max-concurrent-deliveries must be positive", file=sys.stderr)
        return 1

    try:
        from .runtime.orchestration import (
            CodexDeliveryBoundedLoopRequest,
            run_bounded_codex_delivery_supervisor_loop,
        )

        smoke_request, codex_config = _codex_delivery_smoke_cli_objects(parsed)
        result = run_bounded_codex_delivery_supervisor_loop(
            CodexDeliveryBoundedLoopRequest(
                smoke_request=smoke_request,
                max_ticks=int(parsed["max_ticks"]),
                max_deliveries=int(parsed["max_deliveries"]),
                max_runtime_failures=int(parsed["max_runtime_failures"]),
                max_delivery_attempts_per_record=int(
                    parsed["max_delivery_attempts_per_record"]
                ),
                max_concurrent_deliveries=int(parsed["max_concurrent_deliveries"]),
            ),
            codex_cli_client=_codex_process_client_from_config(codex_config),
        )
    except Exception as e:
        return _handle_error(
            "Error running bounded Codex delivery supervisor loop",
            e,
            category="scheduler_codex_delivery_supervisor_loop_failed",
        )

    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def cmd_scheduler_opencode_delivery_supervisor_loop(args: list[str]) -> int:
    """Run the bounded OpenCode supervisor loop."""

    if args and args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_OPENCODE_DELIVERY_SUPERVISOR_LOOP_USAGE + "\n\n"
            "This command is a bounded host-owned loop for OpenCode CLI as a "
            "scheduler-owned worker runtime. Each iteration recovers scheduler "
            "state, marks newly admissible tasks ready, persists dispatcher "
            "decisions, syncs delivery records, runs OpenCode delivery with "
            "result consumption, and recovers again. It has explicit max ticks, "
            "deliveries, and runtime failures. By default the loop runs "
            "deliveries serially; pass --max-concurrent-deliveries above 1 to "
            "run independent lane-distinct OpenCode invocations concurrently "
            "while keeping writeback serialized. This surface intentionally "
            "uses OpenCode host options such as --output-format instead of "
            "Codex sandbox or approval flags. It does not resume a live process "
            "mid-turn. With explicit sandbox preflight and worker patch "
            "publication, git-worktree worker edits are exported as review-only "
            "patch artifacts and are not applied. It does not expose MCP "
            "live-provider execution, does not apply source workspace patches, "
            "and does not mutate Local Work Trajectory.",
        )
        return 0

    parsed = _parse_opencode_delivery_loop_args(args)
    if parsed is None:
        return 1
    validation_error = _validate_opencode_delivery_loop_parsed_args(
        parsed,
        usage=_SCHEDULER_OPENCODE_DELIVERY_SUPERVISOR_LOOP_USAGE,
    )
    if validation_error:
        print(_SCHEDULER_OPENCODE_DELIVERY_SUPERVISOR_LOOP_USAGE, file=sys.stderr)
        print(validation_error, file=sys.stderr)
        return 1

    try:
        from .runtime.orchestration import (
            CodexDeliveryBoundedLoopRequest,
            run_bounded_opencode_delivery_supervisor_loop,
        )

        smoke_request, opencode_config = _opencode_delivery_loop_cli_objects(parsed)
        result = run_bounded_opencode_delivery_supervisor_loop(
            CodexDeliveryBoundedLoopRequest(
                smoke_request=smoke_request,
                max_ticks=int(parsed["max_ticks"]),
                max_deliveries=int(parsed["max_deliveries"]),
                max_runtime_failures=int(parsed["max_runtime_failures"]),
                max_delivery_attempts_per_record=int(
                    parsed["max_delivery_attempts_per_record"]
                ),
                max_concurrent_deliveries=int(parsed["max_concurrent_deliveries"]),
            ),
            opencode_cli_client=_opencode_client_from_parsed_transport(
                parsed,
                opencode_config,
                cli_surface="opencode-delivery-supervisor-loop",
            ),
        )
    except Exception as e:
        return _handle_error(
            "Error running bounded OpenCode delivery supervisor loop",
            e,
            category="scheduler_opencode_delivery_supervisor_loop_failed",
        )

    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def cmd_scheduler_live_codex_concurrent_worker_smoke(args: list[str]) -> int:
    """Run the C9 live Codex concurrent worker smoke."""

    if args and args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_LIVE_CODEX_CONCURRENT_WORKER_SMOKE_USAGE + "\n\n"
            "This command is a host-owned C9 evidence smoke for the C8 "
            "concurrent delivery path. It seeds a multi-lane scheduler fixture "
            "by default, runs the bounded Codex supervisor with at least two "
            "lane-distinct concurrent deliveries, reads compact runtime "
            "invocation audit records, computes real started-at/ended-at "
            "overlap, and writes a final smoke report. It distinguishes "
            "scheduler batch parallelism from audited live process overlap. "
            "Result consumption, delivery acknowledgement, scheduler writes, "
            "and exchange artifact writes stay serialized after runtime "
            "completion. It does not expose MCP live-provider execution, does "
            "not apply source-workspace patches, does not store raw "
            "transcripts, and does not mutate Local Work Trajectory.",
        )
        return 0

    parsed = _parse_codex_delivery_e2e_smoke_args(
        args,
        usage=_SCHEDULER_LIVE_CODEX_CONCURRENT_WORKER_SMOKE_USAGE,
        command_name="live-codex-concurrent-worker-smoke",
        include_loop_options=True,
        include_report_options=True,
        default_initialize_fixture=True,
        default_fixture="multilane",
        default_host_id="host:live-codex-concurrent-worker-smoke",
        default_host_invocation_id="host-owned-live-codex-concurrent-worker-smoke",
        default_max_ticks=4,
        default_max_deliveries=4,
        default_max_runtime_failures=2,
        default_max_concurrent_deliveries=2,
        default_runtime_invocation_log_path=(
            ".dbc/runtime/live-codex-concurrent-worker-smoke-invocations.jsonl"
        ),
    )
    if parsed is None:
        return 1
    _apply_live_codex_concurrent_worker_smoke_defaults(parsed)
    validation_error = _validate_codex_delivery_smoke_parsed_args(
        parsed,
        usage=_SCHEDULER_LIVE_CODEX_CONCURRENT_WORKER_SMOKE_USAGE,
    )
    if validation_error:
        print(_SCHEDULER_LIVE_CODEX_CONCURRENT_WORKER_SMOKE_USAGE, file=sys.stderr)
        print(validation_error, file=sys.stderr)
        return 1
    if str(parsed["fixture"]) != "multilane":
        print(_SCHEDULER_LIVE_CODEX_CONCURRENT_WORKER_SMOKE_USAGE, file=sys.stderr)
        print("--fixture must be multilane for live concurrent worker smoke", file=sys.stderr)
        return 1
    if int(parsed["max_ticks"]) < 0:
        print(_SCHEDULER_LIVE_CODEX_CONCURRENT_WORKER_SMOKE_USAGE, file=sys.stderr)
        print("--max-ticks must be non-negative", file=sys.stderr)
        return 1
    if int(parsed["max_deliveries"]) < 0:
        print(_SCHEDULER_LIVE_CODEX_CONCURRENT_WORKER_SMOKE_USAGE, file=sys.stderr)
        print("--max-deliveries must be non-negative", file=sys.stderr)
        return 1
    if int(parsed["max_runtime_failures"]) < 0:
        print(_SCHEDULER_LIVE_CODEX_CONCURRENT_WORKER_SMOKE_USAGE, file=sys.stderr)
        print("--max-runtime-failures must be non-negative", file=sys.stderr)
        return 1
    if int(parsed["max_delivery_attempts_per_record"]) < 1:
        print(_SCHEDULER_LIVE_CODEX_CONCURRENT_WORKER_SMOKE_USAGE, file=sys.stderr)
        print("--max-delivery-attempts-per-record must be positive", file=sys.stderr)
        return 1
    if int(parsed["max_concurrent_deliveries"]) < 2:
        print(_SCHEDULER_LIVE_CODEX_CONCURRENT_WORKER_SMOKE_USAGE, file=sys.stderr)
        print("--max-concurrent-deliveries must be at least 2", file=sys.stderr)
        return 1

    try:
        from .runtime.orchestration import (
            CodexDeliveryBoundedLoopRequest,
            LiveCodexConcurrentWorkerSmokeRequest,
            run_live_codex_concurrent_worker_smoke,
        )

        smoke_request, codex_config = _codex_delivery_smoke_cli_objects(parsed)
        result = run_live_codex_concurrent_worker_smoke(
            LiveCodexConcurrentWorkerSmokeRequest(
                loop_request=CodexDeliveryBoundedLoopRequest(
                    smoke_request=smoke_request,
                    max_ticks=int(parsed["max_ticks"]),
                    max_deliveries=int(parsed["max_deliveries"]),
                    max_runtime_failures=int(parsed["max_runtime_failures"]),
                    max_delivery_attempts_per_record=int(
                        parsed["max_delivery_attempts_per_record"]
                    ),
                    max_concurrent_deliveries=int(parsed["max_concurrent_deliveries"]),
                ),
                report_path=_resolve_project_path(
                    _find_project_root(),
                    str(parsed["report_path"]),
                ),
            ),
            codex_cli_client=_codex_process_client_from_config(codex_config),
        )
    except Exception as e:
        return _handle_error(
            "Error running live Codex concurrent worker smoke",
            e,
            category="scheduler_live_codex_concurrent_worker_smoke_failed",
        )

    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def cmd_scheduler_live_opencode_concurrent_worker_smoke(args: list[str]) -> int:
    """Run the live OpenCode concurrent worker smoke."""

    if args and args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_LIVE_OPENCODE_CONCURRENT_WORKER_SMOKE_USAGE + "\n\n"
            "This command is a host-owned live evidence smoke for the OpenCode "
            "concurrent delivery path. It seeds a multi-lane scheduler fixture "
            "by default, runs the bounded OpenCode supervisor with at least two "
            "lane-distinct concurrent deliveries, reads compact runtime "
            "invocation audit records, computes real started-at/ended-at "
            "overlap, and writes a final smoke report. It distinguishes "
            "scheduler batch parallelism from audited live process overlap. "
            "Result consumption, delivery acknowledgement, scheduler writes, "
            "and exchange artifact writes stay serialized after runtime "
            "completion. This surface intentionally uses OpenCode host options "
            "such as --output-format instead of Codex sandbox or approval flags. "
            "It does not expose MCP live-provider execution, does not apply "
            "source-workspace patches, does not store raw transcripts, and does "
            "not mutate Local Work Trajectory.",
        )
        return 0

    parsed = _parse_opencode_delivery_loop_args(
        args,
        usage=_SCHEDULER_LIVE_OPENCODE_CONCURRENT_WORKER_SMOKE_USAGE,
        command_name="live-opencode-concurrent-worker-smoke",
        include_report_options=True,
        default_initialize_fixture=True,
        default_fixture="multilane",
        default_host_id="host:live-opencode-concurrent-worker-smoke",
        default_host_invocation_id="host-owned-live-opencode-concurrent-worker-smoke",
        default_max_ticks=4,
        default_max_deliveries=4,
        default_max_runtime_failures=2,
        default_max_concurrent_deliveries=2,
        default_runtime_invocation_log_path=(
            ".dbc/runtime/live-opencode-concurrent-worker-smoke-invocations.jsonl"
        ),
    )
    if parsed is None:
        return 1
    _apply_live_opencode_concurrent_worker_smoke_defaults(parsed)
    validation_error = _validate_opencode_delivery_loop_parsed_args(
        parsed,
        usage=_SCHEDULER_LIVE_OPENCODE_CONCURRENT_WORKER_SMOKE_USAGE,
    )
    if validation_error:
        print(_SCHEDULER_LIVE_OPENCODE_CONCURRENT_WORKER_SMOKE_USAGE, file=sys.stderr)
        print(validation_error, file=sys.stderr)
        return 1
    if str(parsed["fixture"]) != "multilane":
        print(_SCHEDULER_LIVE_OPENCODE_CONCURRENT_WORKER_SMOKE_USAGE, file=sys.stderr)
        print("--fixture must be multilane for live concurrent worker smoke", file=sys.stderr)
        return 1
    if int(parsed["max_concurrent_deliveries"]) < 2:
        print(_SCHEDULER_LIVE_OPENCODE_CONCURRENT_WORKER_SMOKE_USAGE, file=sys.stderr)
        print("--max-concurrent-deliveries must be at least 2", file=sys.stderr)
        return 1

    try:
        from .runtime.orchestration import (
            CodexDeliveryBoundedLoopRequest,
            LiveOpenCodeConcurrentWorkerSmokeRequest,
            run_live_opencode_concurrent_worker_smoke,
        )

        smoke_request, opencode_config = _opencode_delivery_loop_cli_objects(parsed)
        result = run_live_opencode_concurrent_worker_smoke(
            LiveOpenCodeConcurrentWorkerSmokeRequest(
                loop_request=CodexDeliveryBoundedLoopRequest(
                    smoke_request=smoke_request,
                    max_ticks=int(parsed["max_ticks"]),
                    max_deliveries=int(parsed["max_deliveries"]),
                    max_runtime_failures=int(parsed["max_runtime_failures"]),
                    max_delivery_attempts_per_record=int(
                        parsed["max_delivery_attempts_per_record"]
                    ),
                    max_concurrent_deliveries=int(parsed["max_concurrent_deliveries"]),
                ),
                report_path=_resolve_project_path(
                    _find_project_root(),
                    str(parsed["report_path"]),
                ),
            ),
            opencode_cli_client=_opencode_process_client_from_config(opencode_config),
        )
    except Exception as e:
        return _handle_error(
            "Error running live OpenCode concurrent worker smoke",
            e,
            category="scheduler_live_opencode_concurrent_worker_smoke_failed",
        )

    _print_json(result.to_json_dict())
    return 0 if result.ok else 1


def _parse_codex_delivery_e2e_smoke_args(
    args: list[str],
    *,
    usage: str = _SCHEDULER_CODEX_DELIVERY_E2E_SMOKE_USAGE,
    command_name: str = "codex-delivery-e2e-smoke",
    include_loop_options: bool = False,
    include_report_options: bool = False,
    default_initialize_fixture: bool = False,
    default_fixture: str = "simple",
    default_host_id: str = "host:codex-delivery-e2e-smoke",
    default_host_invocation_id: str = "host-owned-codex-delivery-e2e-smoke",
    default_max_ticks: int = 3,
    default_max_deliveries: int = 3,
    default_max_runtime_failures: int = 1,
    default_max_concurrent_deliveries: int = 1,
    default_runtime_invocation_log_path: str = ".dbc/runtime/invocations.jsonl",
) -> dict[str, object] | None:
    parsed: dict[str, object] = {
        "snapshot_path": "",
        "event_log_path": "",
        "artifact_store_path": "",
        "dispatcher_state_path": "",
        "dispatch_event_log_path": "",
        "delivery_state_path": "",
        "delivery_event_log_path": "",
        "runtime_invocation_log_path": default_runtime_invocation_log_path,
        "initialize_fixture": default_initialize_fixture,
        "replace_existing_fixture": False,
        "fixture": default_fixture,
        "replace_existing_result_artifact": False,
        "target_task_id": "codex-smoke:worker",
        "parallel_task_id": "codex-smoke:parallel-worker",
        "waiting_task_id": "codex-smoke:waiting-non-codex",
        "followup_task_id": "codex-smoke:followup",
        "executable": "codex",
        "cwd": "",
        "model": "",
        "sandbox": "workspace-write",
        "ask_for_approval": "never",
        "host_id": default_host_id,
        "host_invocation_id": default_host_invocation_id,
        "timestamp": "",
        "runtime_invocation_max_attempts": 2,
        "runtime_invocation_backoff_seconds": 0.0,
        "enable_sandbox_preflight": False,
        "workspace_root": "",
        "scratch_root": ".dbc/scratch",
        "git_worktree_sandbox_root": "",
        "git_executable": "git",
        "publish_worker_patch_artifacts": False,
        "worker_patch_guide_agent_id": "agent:guide",
        "worker_patch_target_task_id": "",
        "max_ticks": default_max_ticks,
        "max_deliveries": default_max_deliveries,
        "max_runtime_failures": default_max_runtime_failures,
        "max_delivery_attempts_per_record": 2,
        "max_concurrent_deliveries": default_max_concurrent_deliveries,
        "report_path": "",
    }
    if not include_loop_options:
        parsed.pop("max_ticks")
        parsed.pop("max_deliveries")
        parsed.pop("max_runtime_failures")
        parsed.pop("max_delivery_attempts_per_record")
    if not include_report_options:
        parsed.pop("report_path")
    options = set(parsed)
    cli_to_key = {
        "--snapshot-path": "snapshot_path",
        "--event-log-path": "event_log_path",
        "--artifact-store-path": "artifact_store_path",
        "--dispatcher-state-path": "dispatcher_state_path",
        "--dispatch-event-log-path": "dispatch_event_log_path",
        "--delivery-state-path": "delivery_state_path",
        "--delivery-event-log-path": "delivery_event_log_path",
        "--runtime-invocation-log-path": "runtime_invocation_log_path",
        "--fixture": "fixture",
        "--target-task-id": "target_task_id",
        "--parallel-task-id": "parallel_task_id",
        "--waiting-task-id": "waiting_task_id",
        "--followup-task-id": "followup_task_id",
        "--executable": "executable",
        "--cwd": "cwd",
        "--model": "model",
        "--sandbox": "sandbox",
        "--ask-for-approval": "ask_for_approval",
        "--host-id": "host_id",
        "--host-invocation-id": "host_invocation_id",
        "--timestamp": "timestamp",
        "--runtime-invocation-max-attempts": "runtime_invocation_max_attempts",
        "--runtime-invocation-backoff-seconds": "runtime_invocation_backoff_seconds",
        "--workspace-root": "workspace_root",
        "--scratch-root": "scratch_root",
        "--git-worktree-sandbox-root": "git_worktree_sandbox_root",
        "--git-executable": "git_executable",
        "--worker-patch-guide-agent-id": "worker_patch_guide_agent_id",
        "--worker-patch-target-task-id": "worker_patch_target_task_id",
    }
    if include_loop_options:
        cli_to_key.update(
            {
                "--max-ticks": "max_ticks",
                "--max-deliveries": "max_deliveries",
                "--max-runtime-failures": "max_runtime_failures",
                "--max-delivery-attempts-per-record": "max_delivery_attempts_per_record",
                "--max-concurrent-deliveries": "max_concurrent_deliveries",
            }
        )
    if include_report_options:
        cli_to_key["--report-path"] = "report_path"
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--initialize-fixture":
            parsed["initialize_fixture"] = True
            i += 1
            continue
        if arg == "--replace-existing-fixture":
            parsed["replace_existing_fixture"] = True
            i += 1
            continue
        if arg == "--replace-existing-result-artifact":
            parsed["replace_existing_result_artifact"] = True
            i += 1
            continue
        if arg == "--enable-sandbox-preflight":
            parsed["enable_sandbox_preflight"] = True
            i += 1
            continue
        if arg == "--publish-worker-patch-artifacts":
            parsed["publish_worker_patch_artifacts"] = True
            i += 1
            continue
        if arg not in cli_to_key:
            print(f"Unknown scheduler {command_name} option: {arg}", file=sys.stderr)
            print(usage, file=sys.stderr)
            return None
        if i + 1 >= len(args):
            print(usage, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return None
        key = cli_to_key[arg]
        value = args[i + 1]
        if key in {
            "runtime_invocation_max_attempts",
            "max_ticks",
            "max_deliveries",
            "max_runtime_failures",
            "max_delivery_attempts_per_record",
            "max_concurrent_deliveries",
        }:
            try:
                parsed[key] = int(value)
            except ValueError:
                print(usage, file=sys.stderr)
                print(f"{arg} must be an integer", file=sys.stderr)
                return None
        elif key == "runtime_invocation_backoff_seconds":
            try:
                parsed[key] = float(value)
            except ValueError:
                print(usage, file=sys.stderr)
                print(f"{arg} must be a number", file=sys.stderr)
                return None
        else:
            parsed[key] = value
        i += 2
    unknown_internal = set(parsed) - options
    if unknown_internal:
        raise AssertionError(f"unexpected codex delivery smoke parser keys: {unknown_internal}")
    return parsed


def _validate_codex_delivery_smoke_parsed_args(
    parsed: dict[str, object],
    *,
    usage: str,
) -> str:
    if parsed["sandbox"] not in {"read-only", "workspace-write", "danger-full-access"}:
        return "--sandbox must be read-only, workspace-write, or danger-full-access"
    if parsed["ask_for_approval"] not in {"untrusted", "on-request", "never"}:
        return "--ask-for-approval must be untrusted, on-request, or never"
    if parsed["fixture"] not in {"simple", "multilane"}:
        return "--fixture must be simple or multilane"
    if int(parsed["runtime_invocation_max_attempts"]) < 1:
        return "--runtime-invocation-max-attempts must be positive"
    if float(parsed["runtime_invocation_backoff_seconds"]) < 0:
        return "--runtime-invocation-backoff-seconds must be non-negative"
    if bool(parsed["publish_worker_patch_artifacts"]) and not bool(
        parsed["enable_sandbox_preflight"]
    ):
        return "--publish-worker-patch-artifacts requires --enable-sandbox-preflight"
    return ""


def _codex_process_client_from_config(config) -> object:
    from .runtime.orchestration import CodexCliProcessClient

    return CodexCliProcessClient(config)


def _opencode_process_client_from_config(config) -> object:
    from .runtime.orchestration import OpenCodeCliProcessClient

    return OpenCodeCliProcessClient(config)


def _opencode_client_from_parsed_transport(
    parsed: dict[str, object],
    cli_config,
    *,
    cli_surface: str,
) -> object:
    if parsed.get("opencode_transport", "cli") == "server-api":
        from .runtime.orchestration import (
            OpenCodeServerApiClient,
            OpenCodeServerApiClientConfig,
        )

        return OpenCodeServerApiClient(
            OpenCodeServerApiClientConfig(
                base_url=str(parsed["server_api_base_url"]),
                health_path=str(parsed["server_api_health_path"]),
                doc_path=str(parsed["server_api_doc_path"]),
                session_id=str(parsed["server_api_session_id"]),
                model=str(parsed["model"]),
                timeout_seconds=float(parsed["server_api_timeout_seconds"]),
                username_env_var=str(parsed["server_api_username_env_var"]),
                password_env_var=str(parsed["server_api_password_env_var"]),
                metadata={
                    "transport": "server-api",
                    "cli_surface": cli_surface,
                },
            )
        )
    return _opencode_process_client_from_config(cli_config)


def _apply_live_codex_concurrent_worker_smoke_defaults(
    parsed: dict[str, object],
) -> None:
    defaults = {
        "snapshot_path": ".dbc/scheduler/live-codex-concurrent-worker-smoke-state.json",
        "event_log_path": ".dbc/scheduler/live-codex-concurrent-worker-smoke-events.jsonl",
        "artifact_store_path": ".dbc/orchestration/live-codex-concurrent-worker-smoke-exchange-artifacts.json",
        "dispatcher_state_path": ".dbc/scheduler/live-codex-concurrent-worker-smoke-dispatcher-state.json",
        "dispatch_event_log_path": ".dbc/scheduler/live-codex-concurrent-worker-smoke-dispatcher-events.jsonl",
        "delivery_state_path": ".dbc/scheduler/live-codex-concurrent-worker-smoke-delivery-state.json",
        "delivery_event_log_path": ".dbc/scheduler/live-codex-concurrent-worker-smoke-delivery-events.jsonl",
        "runtime_invocation_log_path": ".dbc/runtime/live-codex-concurrent-worker-smoke-invocations.jsonl",
        "report_path": ".dbc/scheduler/live-codex-concurrent-worker-smoke-report.json",
    }
    for key, value in defaults.items():
        if key in parsed and not str(parsed[key]):
            parsed[key] = value
    if not str(parsed.get("timestamp", "")):
        parsed["timestamp"] = datetime.now(UTC).isoformat()


def _apply_live_opencode_concurrent_worker_smoke_defaults(
    parsed: dict[str, object],
) -> None:
    defaults = {
        "snapshot_path": ".dbc/scheduler/live-opencode-concurrent-worker-smoke-state.json",
        "event_log_path": ".dbc/scheduler/live-opencode-concurrent-worker-smoke-events.jsonl",
        "artifact_store_path": ".dbc/orchestration/live-opencode-concurrent-worker-smoke-exchange-artifacts.json",
        "dispatcher_state_path": ".dbc/scheduler/live-opencode-concurrent-worker-smoke-dispatcher-state.json",
        "dispatch_event_log_path": ".dbc/scheduler/live-opencode-concurrent-worker-smoke-dispatcher-events.jsonl",
        "delivery_state_path": ".dbc/scheduler/live-opencode-concurrent-worker-smoke-delivery-state.json",
        "delivery_event_log_path": ".dbc/scheduler/live-opencode-concurrent-worker-smoke-delivery-events.jsonl",
        "runtime_invocation_log_path": ".dbc/runtime/live-opencode-concurrent-worker-smoke-invocations.jsonl",
        "report_path": ".dbc/scheduler/live-opencode-concurrent-worker-smoke-report.json",
    }
    for key, value in defaults.items():
        if key in parsed and not str(parsed[key]):
            parsed[key] = value
    if not str(parsed.get("timestamp", "")):
        parsed["timestamp"] = datetime.now(UTC).isoformat()


def _codex_delivery_smoke_cli_objects(parsed: dict[str, object]):
    root = _find_project_root()
    from .runtime.orchestration import (
        CodexCliClientConfig,
        CodexDeliveryE2ESmokeRequest,
        DEFAULT_CODEX_DELIVERY_E2E_SMOKE_EVENT_LOG_RELATIVE_PATH,
        DEFAULT_CODEX_DELIVERY_E2E_SMOKE_SNAPSHOT_RELATIVE_PATH,
        DEFAULT_EXCHANGE_ARTIFACT_STORE_RELATIVE_PATH,
        DEFAULT_LEADER_WORKER_DELIVERY_EVENT_LOG_RELATIVE_PATH,
        DEFAULT_LEADER_WORKER_DELIVERY_STATE_RELATIVE_PATH,
        DEFAULT_LEADER_WORKER_DISPATCHER_EVENT_LOG_RELATIVE_PATH,
        DEFAULT_LEADER_WORKER_DISPATCHER_STATE_RELATIVE_PATH,
        DEFAULT_RUNTIME_INVOCATION_LOG_RELATIVE_PATH,
    )

    request = CodexDeliveryE2ESmokeRequest(
        scheduler_snapshot_path=_resolve_project_path(
            root,
            str(parsed["snapshot_path"])
            or DEFAULT_CODEX_DELIVERY_E2E_SMOKE_SNAPSHOT_RELATIVE_PATH,
        ),
        scheduler_event_log_path=_resolve_project_path(
            root,
            str(parsed["event_log_path"])
            or DEFAULT_CODEX_DELIVERY_E2E_SMOKE_EVENT_LOG_RELATIVE_PATH,
        ),
        artifact_store_path=_resolve_project_path(
            root,
            str(parsed["artifact_store_path"])
            or DEFAULT_EXCHANGE_ARTIFACT_STORE_RELATIVE_PATH,
        ),
        dispatcher_state_path=_resolve_project_path(
            root,
            str(parsed["dispatcher_state_path"])
            or DEFAULT_LEADER_WORKER_DISPATCHER_STATE_RELATIVE_PATH,
        ),
        dispatch_event_log_path=_resolve_project_path(
            root,
            str(parsed["dispatch_event_log_path"])
            or DEFAULT_LEADER_WORKER_DISPATCHER_EVENT_LOG_RELATIVE_PATH,
        ),
        delivery_state_path=_resolve_project_path(
            root,
            str(parsed["delivery_state_path"])
            or DEFAULT_LEADER_WORKER_DELIVERY_STATE_RELATIVE_PATH,
        ),
        delivery_event_log_path=_resolve_project_path(
            root,
            str(parsed["delivery_event_log_path"])
            or DEFAULT_LEADER_WORKER_DELIVERY_EVENT_LOG_RELATIVE_PATH,
        ),
        runtime_invocation_log_path=(
            None
            if parsed["runtime_invocation_log_path"] is None
            else _resolve_project_path(
                root,
                str(parsed["runtime_invocation_log_path"])
                or DEFAULT_RUNTIME_INVOCATION_LOG_RELATIVE_PATH,
            )
        ),
        initialize_fixture=bool(parsed["initialize_fixture"]),
        replace_existing_fixture=bool(parsed["replace_existing_fixture"]),
        fixture=str(parsed["fixture"]),
        replace_existing_result_artifact=bool(parsed["replace_existing_result_artifact"]),
        target_task_id=str(parsed["target_task_id"]),
        parallel_task_id=str(parsed["parallel_task_id"]),
        waiting_task_id=str(parsed["waiting_task_id"]),
        followup_task_id=str(parsed["followup_task_id"]),
        timestamp=str(parsed["timestamp"]),
        host_id=str(parsed["host_id"]),
        host_invocation_id=str(parsed["host_invocation_id"]),
        runtime_invocation_max_attempts=int(parsed["runtime_invocation_max_attempts"]),
        runtime_invocation_backoff_seconds=float(parsed["runtime_invocation_backoff_seconds"]),
        enable_sandbox_preflight=bool(parsed["enable_sandbox_preflight"]),
        workspace_root=(
            _resolve_project_path(root, str(parsed["workspace_root"]))
            if str(parsed["workspace_root"])
            else root
        ),
        scratch_root=str(parsed["scratch_root"]),
        git_worktree_sandbox_root=(
            None
            if not str(parsed["git_worktree_sandbox_root"])
            else _resolve_project_path(root, str(parsed["git_worktree_sandbox_root"]))
        ),
        git_executable=str(parsed["git_executable"]),
        publish_worker_patch_artifacts=bool(parsed["publish_worker_patch_artifacts"]),
        worker_patch_guide_agent_id=str(parsed["worker_patch_guide_agent_id"]),
        worker_patch_target_task_id=str(parsed["worker_patch_target_task_id"]),
    )
    codex_config = CodexCliClientConfig(
        executable=str(parsed["executable"]),
        cwd=str(parsed["cwd"]),
        model=str(parsed["model"]),
        sandbox=str(parsed["sandbox"]),  # type: ignore[arg-type]
        ask_for_approval=str(parsed["ask_for_approval"]),  # type: ignore[arg-type]
    )
    return request, codex_config


def _opencode_delivery_loop_cli_objects(
    parsed: dict[str, object],
    *,
    default_snapshot_path: str = ".dbc/scheduler/opencode-delivery-supervisor-loop-state.json",
    default_event_log_path: str = ".dbc/scheduler/opencode-delivery-supervisor-loop-events.jsonl",
    default_runtime_invocation_log_path: str = ".dbc/runtime/opencode-delivery-loop-invocations.jsonl",
    trajectory_id: str = "opencode-delivery-supervisor-loop",
):
    root = _find_project_root()
    from .runtime.orchestration import (
        CodexDeliveryE2ESmokeRequest,
        DEFAULT_EXCHANGE_ARTIFACT_STORE_RELATIVE_PATH,
        DEFAULT_LEADER_WORKER_DELIVERY_EVENT_LOG_RELATIVE_PATH,
        DEFAULT_LEADER_WORKER_DELIVERY_STATE_RELATIVE_PATH,
        DEFAULT_LEADER_WORKER_DISPATCHER_EVENT_LOG_RELATIVE_PATH,
        DEFAULT_LEADER_WORKER_DISPATCHER_STATE_RELATIVE_PATH,
        OpenCodeCliClientConfig,
    )

    request = CodexDeliveryE2ESmokeRequest(
        scheduler_snapshot_path=_resolve_project_path(
            root,
            str(parsed["snapshot_path"]) or default_snapshot_path,
        ),
        scheduler_event_log_path=_resolve_project_path(
            root,
            str(parsed["event_log_path"]) or default_event_log_path,
        ),
        artifact_store_path=_resolve_project_path(
            root,
            str(parsed["artifact_store_path"])
            or DEFAULT_EXCHANGE_ARTIFACT_STORE_RELATIVE_PATH,
        ),
        dispatcher_state_path=_resolve_project_path(
            root,
            str(parsed["dispatcher_state_path"])
            or DEFAULT_LEADER_WORKER_DISPATCHER_STATE_RELATIVE_PATH,
        ),
        dispatch_event_log_path=_resolve_project_path(
            root,
            str(parsed["dispatch_event_log_path"])
            or DEFAULT_LEADER_WORKER_DISPATCHER_EVENT_LOG_RELATIVE_PATH,
        ),
        delivery_state_path=_resolve_project_path(
            root,
            str(parsed["delivery_state_path"])
            or DEFAULT_LEADER_WORKER_DELIVERY_STATE_RELATIVE_PATH,
        ),
        delivery_event_log_path=_resolve_project_path(
            root,
            str(parsed["delivery_event_log_path"])
            or DEFAULT_LEADER_WORKER_DELIVERY_EVENT_LOG_RELATIVE_PATH,
        ),
        runtime_invocation_log_path=(
            None
            if parsed["runtime_invocation_log_path"] is None
            else _resolve_project_path(
                root,
                str(parsed["runtime_invocation_log_path"])
                or default_runtime_invocation_log_path,
            )
        ),
        initialize_fixture=bool(parsed["initialize_fixture"]),
        replace_existing_fixture=bool(parsed["replace_existing_fixture"]),
        fixture=str(parsed["fixture"]),
        replace_existing_result_artifact=bool(parsed["replace_existing_result_artifact"]),
        target_task_id=str(parsed["target_task_id"]),
        parallel_task_id=str(parsed["parallel_task_id"]),
        waiting_task_id=str(parsed["waiting_task_id"]),
        followup_task_id=str(parsed["followup_task_id"]),
        timestamp=str(parsed["timestamp"]),
        host_id=str(parsed["host_id"]),
        host_invocation_id=str(parsed["host_invocation_id"]),
        runtime_invocation_max_attempts=int(parsed["runtime_invocation_max_attempts"]),
        runtime_invocation_backoff_seconds=float(parsed["runtime_invocation_backoff_seconds"]),
        enable_sandbox_preflight=bool(parsed["enable_sandbox_preflight"]),
        workspace_root=(
            _resolve_project_path(root, str(parsed["workspace_root"]))
            if str(parsed["workspace_root"])
            else root
        ),
        scratch_root=str(parsed["scratch_root"]),
        git_worktree_sandbox_root=(
            None
            if not str(parsed["git_worktree_sandbox_root"])
            else _resolve_project_path(root, str(parsed["git_worktree_sandbox_root"]))
        ),
        git_executable=str(parsed["git_executable"]),
        publish_worker_patch_artifacts=bool(parsed["publish_worker_patch_artifacts"]),
        worker_patch_guide_agent_id=str(parsed["worker_patch_guide_agent_id"]),
        worker_patch_target_task_id=str(parsed["worker_patch_target_task_id"]),
        continuous_worker_binding_ledger_path=_resolve_project_path(
            root,
            str(parsed["worker_binding_ledger_path"]),
        ),
        continuous_worker_binding_event_log_path=_resolve_project_path(
            root,
            str(parsed["worker_binding_event_log_path"]),
        ),
        enable_continuous_worker_binding_lookup=bool(parsed["worker_binding_lookup"]),
        opencode_session_ledger_path=_resolve_project_path(
            root,
            str(parsed["session_ledger_path"]),
        ),
        opencode_enable_session_lookup=bool(parsed["session_ledger_lookup"]),
        runtime_provider="opencode",
        codex_agent_id="agent:opencode-smoke-worker",
        parallel_agent_id="agent:opencode-smoke-parallel-worker",
        followup_agent_id="agent:opencode-smoke-followup",
        waiting_agent_id="agent:opencode-smoke-waiting",
        codex_lane_id="lane:opencode-smoke",
        parallel_lane_id="lane:opencode-smoke-parallel",
        followup_lane_id="lane:opencode-smoke",
        trajectory_id=trajectory_id,
    )
    opencode_config = OpenCodeCliClientConfig(
        executable=str(parsed["executable"]),
        cwd=str(parsed["cwd"]),
        model=str(parsed["model"]),
        output_format=str(parsed["output_format"]),  # type: ignore[arg-type]
        attach_url=str(parsed["attach_url"]),
        session_id=str(parsed["session_id"]),
        continue_session=bool(parsed["continue_session"]),
        fork_session=bool(parsed["fork_session"]),
    )
    return request, opencode_config


def _parse_leader_worker_delivery_common_args(
    args: list[str],
    *,
    usage: str,
    mode: str,
) -> dict[str, object] | None:
    parsed: dict[str, object] = {
        "delivery_state_path": "",
        "delivery_event_log_path": "",
        "dispatch_event_log_path": "",
        "delivery_id": "leader-worker-delivery",
        "dispatcher_id": "leader-worker-dispatcher",
        "host_id": "",
        "timestamp": "",
        "target_state": "",
        "source_key": "",
        "delivery_record_id": "",
        "runtime_provider": "",
        "runtime_session_id": "",
        "runtime_run_id": "",
        "invocation_id": "",
        "failure_kind": "",
        "failure_detail": "",
        "latest_limit": 20,
    }
    common_options = {
        "--delivery-state-path",
        "--delivery-event-log-path",
        "--host-id",
        "--timestamp",
    }
    sync_options = {
        "--dispatch-event-log-path",
        "--delivery-id",
        "--dispatcher-id",
    }
    ack_options = {
        "--target-state",
        "--source-key",
        "--delivery-record-id",
        "--runtime-provider",
        "--runtime-session-id",
        "--runtime-run-id",
        "--invocation-id",
        "--failure-kind",
        "--failure-detail",
    }
    inspect_options = {"--latest-limit"}
    allowed = set(common_options)
    if mode == "sync":
        allowed |= sync_options
    elif mode == "ack":
        allowed |= ack_options
    elif mode == "inspect":
        allowed |= inspect_options
    else:
        raise ValueError(f"unsupported leader-worker delivery CLI parse mode: {mode!r}")

    i = 0
    while i < len(args):
        arg = args[i]
        if arg not in allowed:
            print(f"Unknown scheduler leader-worker delivery option: {arg}", file=sys.stderr)
            print(usage, file=sys.stderr)
            return None
        if i + 1 >= len(args):
            print(usage, file=sys.stderr)
            print(f"Missing value for {arg}", file=sys.stderr)
            return None
        value = args[i + 1]
        if arg == "--delivery-state-path":
            parsed["delivery_state_path"] = value
        elif arg == "--delivery-event-log-path":
            parsed["delivery_event_log_path"] = value
        elif arg == "--dispatch-event-log-path":
            parsed["dispatch_event_log_path"] = value
        elif arg == "--delivery-id":
            parsed["delivery_id"] = value
        elif arg == "--dispatcher-id":
            parsed["dispatcher_id"] = value
        elif arg == "--host-id":
            parsed["host_id"] = value
        elif arg == "--timestamp":
            parsed["timestamp"] = value
        elif arg == "--target-state":
            parsed["target_state"] = value
        elif arg == "--source-key":
            parsed["source_key"] = value
        elif arg == "--delivery-record-id":
            parsed["delivery_record_id"] = value
        elif arg == "--runtime-provider":
            parsed["runtime_provider"] = value
        elif arg == "--runtime-session-id":
            parsed["runtime_session_id"] = value
        elif arg == "--runtime-run-id":
            parsed["runtime_run_id"] = value
        elif arg == "--invocation-id":
            parsed["invocation_id"] = value
        elif arg == "--failure-kind":
            parsed["failure_kind"] = value
        elif arg == "--failure-detail":
            parsed["failure_detail"] = value
        elif arg == "--latest-limit":
            try:
                parsed["latest_limit"] = int(value)
            except ValueError:
                print(usage, file=sys.stderr)
                print("--latest-limit must be an integer", file=sys.stderr)
                return None
        i += 2
    return parsed


def _leader_worker_delivery_state_path(
    root: Path,
    parsed: dict[str, object],
) -> Path:
    from .runtime.orchestration import DEFAULT_LEADER_WORKER_DELIVERY_STATE_RELATIVE_PATH

    value = str(parsed["delivery_state_path"])
    return _resolve_project_path(
        root,
        value or DEFAULT_LEADER_WORKER_DELIVERY_STATE_RELATIVE_PATH,
    )


def _leader_worker_delivery_log_path(
    root: Path,
    parsed: dict[str, object],
) -> Path:
    from .runtime.orchestration import DEFAULT_LEADER_WORKER_DELIVERY_EVENT_LOG_RELATIVE_PATH

    value = str(parsed["delivery_event_log_path"])
    return _resolve_project_path(
        root,
        value or DEFAULT_LEADER_WORKER_DELIVERY_EVENT_LOG_RELATIVE_PATH,
    )


def cmd_scheduler_inspect_agent_action_candidates(args: list[str]) -> int:
    """Read ExchangeArtifact action candidates without mutation."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_INSPECT_AGENT_ACTION_CANDIDATES_USAGE + "\n\n"
            "This is a readback command. It classifies exact-version "
            "ExchangeArtifact records into scheduler, review, handoff, blocker, "
            "and merge action candidates. It does not admit scheduler tasks, "
            "open reviews, write handoffs, mutate exchange artifacts, write "
            "admission ledgers, run providers, refresh projections, or mutate "
            "Local Work Trajectory.",
        )
        return 0

    artifact_store_path = ""
    admission_ledger_path = ""
    agent_id = ""
    candidate_type = ""
    include_archived = False

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--include-archived":
            include_archived = True
            i += 1
            continue
        if arg in {
            "--artifact-store-path",
            "--admission-ledger-path",
            "--agent-id",
            "--candidate-type",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_INSPECT_AGENT_ACTION_CANDIDATES_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--admission-ledger-path":
                admission_ledger_path = value
            elif arg == "--agent-id":
                agent_id = value
            elif arg == "--candidate-type":
                candidate_type = value
            i += 2
            continue
        print(f"Unknown scheduler inspect-agent-action-candidates option: {arg}", file=sys.stderr)
        print(_SCHEDULER_INSPECT_AGENT_ACTION_CANDIDATES_USAGE, file=sys.stderr)
        return 1

    root = _find_project_root()

    try:
        from .runtime.orchestration import (
            default_exchange_artifact_admission_ledger_path,
            default_exchange_artifact_store_path,
            inspect_agent_exchange_action_candidates,
        )

        store_path = (
            _resolve_project_path(root, artifact_store_path)
            if artifact_store_path
            else default_exchange_artifact_store_path(root)
        )
        ledger_path = (
            _resolve_project_path(root, admission_ledger_path)
            if admission_ledger_path
            else default_exchange_artifact_admission_ledger_path(root)
        )
        summary = inspect_agent_exchange_action_candidates(
            store_path,
            agent_id=agent_id,
            candidate_type=candidate_type,
            include_archived=include_archived,
            admission_ledger_path=ledger_path,
        )
    except Exception as e:
        return _handle_error(
            "Error inspecting agent exchange action candidates",
            e,
            category="scheduler_agent_action_candidates_inspect_failed",
        )

    payload = {"ok": not summary.errors}
    payload.update(summary.to_json_dict())
    _print_json(payload)
    return 1 if summary.errors else 0


def cmd_scheduler_decide_agent_action_candidate(args: list[str]) -> int:
    """Record an action-candidate disposition ExchangeArtifact."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_DECIDE_AGENT_ACTION_CANDIDATE_USAGE + "\n\n"
            "This writes one coordination-product ExchangeArtifact that records "
            "the disposition for an existing action candidate. It does not admit "
            "scheduler tasks, open reviews, write handoffs, resolve merge gates, "
            "mutate the source ExchangeArtifact, run providers, refresh "
            "projections, or mutate Local Work Trajectory.",
        )
        return 0

    artifact_store_path = ""
    candidate_id = ""
    disposition_artifact_id = ""
    actor = ""
    disposition = ""
    disposition_version = "v1"
    reason = ""
    target_surface = ""
    replacement_artifact_id = ""
    replacement_version = ""
    timestamp = ""
    replace_existing = False

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--replace-existing":
            replace_existing = True
            i += 1
            continue
        if arg in {
            "--artifact-store-path",
            "--candidate-id",
            "--disposition-artifact-id",
            "--actor",
            "--disposition",
            "--disposition-version",
            "--reason",
            "--target-surface",
            "--replacement-artifact-id",
            "--replacement-version",
            "--timestamp",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_DECIDE_AGENT_ACTION_CANDIDATE_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--candidate-id":
                candidate_id = value
            elif arg == "--disposition-artifact-id":
                disposition_artifact_id = value
            elif arg == "--actor":
                actor = value
            elif arg == "--disposition":
                disposition = value
            elif arg == "--disposition-version":
                disposition_version = value
            elif arg == "--reason":
                reason = value
            elif arg == "--target-surface":
                target_surface = value
            elif arg == "--replacement-artifact-id":
                replacement_artifact_id = value
            elif arg == "--replacement-version":
                replacement_version = value
            elif arg == "--timestamp":
                timestamp = value
            i += 2
            continue
        print(f"Unknown scheduler decide-agent-action-candidate option: {arg}", file=sys.stderr)
        print(_SCHEDULER_DECIDE_AGENT_ACTION_CANDIDATE_USAGE, file=sys.stderr)
        return 1

    missing = [
        name
        for name, value in (
            ("--candidate-id", candidate_id),
            ("--disposition-artifact-id", disposition_artifact_id),
            ("--actor", actor),
            ("--disposition", disposition),
        )
        if not value
    ]
    if missing:
        print(_SCHEDULER_DECIDE_AGENT_ACTION_CANDIDATE_USAGE, file=sys.stderr)
        print(f"Missing required option(s): {', '.join(missing)}", file=sys.stderr)
        return 1

    root = _find_project_root()

    try:
        from .runtime.orchestration import (
            decide_agent_exchange_action_candidate,
            default_exchange_artifact_store_path,
        )

        store_path = (
            _resolve_project_path(root, artifact_store_path)
            if artifact_store_path
            else default_exchange_artifact_store_path(root)
        )
        result = decide_agent_exchange_action_candidate(
            store_path=store_path,
            candidate_id=candidate_id,
            disposition_artifact_id=disposition_artifact_id,
            disposition_version=disposition_version,
            actor=actor,
            disposition=disposition,  # type: ignore[arg-type]
            reason=reason,
            target_surface=target_surface,
            replacement_artifact_id=replacement_artifact_id,
            replacement_version=replacement_version,
            timestamp=timestamp,
            replace_existing=replace_existing,
        )
    except Exception as e:
        return _handle_error(
            "Error deciding agent exchange action candidate",
            e,
            category="scheduler_agent_action_candidate_decide_failed",
        )

    _print_json(result.to_json_dict())
    return 0


def cmd_scheduler_consume_accepted_scheduler_candidate(args: list[str]) -> int:
    """Consume an accepted scheduler action-candidate disposition."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_CONSUME_ACCEPTED_SCHEDULER_CANDIDATE_USAGE + "\n\n"
            "This consumes one accepted scheduler_submission_candidate disposition "
            "by calling the existing exact-version admission helper. It may write "
            "scheduler snapshot/event-log state and the admission ledger. It does "
            "not open reviews, write handoffs, resolve merge gates, run providers, "
            "refresh projections, or mutate Local Work Trajectory.",
        )
        return 0

    artifact_store_path = ""
    admission_ledger_path = ""
    disposition_artifact_id = ""
    disposition_version = ""
    snapshot_path = ""
    event_log_path = ""
    replace_existing = False
    allow_duplicate_admission = False
    validate_binding_artifact_refs = False
    mark_consumed_on_success = False
    actor = "operator-cli"
    timestamp = ""

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--replace-existing":
            replace_existing = True
            i += 1
            continue
        if arg == "--allow-duplicate-admission":
            allow_duplicate_admission = True
            i += 1
            continue
        if arg == "--validate-binding-artifact-refs":
            validate_binding_artifact_refs = True
            i += 1
            continue
        if arg == "--mark-consumed-on-success":
            mark_consumed_on_success = True
            i += 1
            continue
        if arg in {
            "--artifact-store-path",
            "--admission-ledger-path",
            "--disposition-artifact-id",
            "--disposition-version",
            "--snapshot-path",
            "--event-log-path",
            "--actor",
            "--timestamp",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_CONSUME_ACCEPTED_SCHEDULER_CANDIDATE_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--admission-ledger-path":
                admission_ledger_path = value
            elif arg == "--disposition-artifact-id":
                disposition_artifact_id = value
            elif arg == "--disposition-version":
                disposition_version = value
            elif arg == "--snapshot-path":
                snapshot_path = value
            elif arg == "--event-log-path":
                event_log_path = value
            elif arg == "--actor":
                actor = value
            elif arg == "--timestamp":
                timestamp = value
            i += 2
            continue
        print(f"Unknown scheduler consume-accepted-scheduler-candidate option: {arg}", file=sys.stderr)
        print(_SCHEDULER_CONSUME_ACCEPTED_SCHEDULER_CANDIDATE_USAGE, file=sys.stderr)
        return 1

    missing = [
        name
        for name, value in (
            ("--disposition-artifact-id", disposition_artifact_id),
            ("--disposition-version", disposition_version),
            ("--snapshot-path", snapshot_path),
            ("--event-log-path", event_log_path),
        )
        if not value
    ]
    if missing:
        print(_SCHEDULER_CONSUME_ACCEPTED_SCHEDULER_CANDIDATE_USAGE, file=sys.stderr)
        print(f"Missing required option(s): {', '.join(missing)}", file=sys.stderr)
        return 1

    root = _find_project_root()

    try:
        from .runtime.orchestration import (
            consume_accepted_scheduler_action_candidate,
            default_exchange_artifact_admission_ledger_path,
            default_exchange_artifact_store_path,
        )

        store = (
            _resolve_project_path(root, artifact_store_path)
            if artifact_store_path
            else default_exchange_artifact_store_path(root)
        )
        ledger_path = (
            _resolve_project_path(root, admission_ledger_path)
            if admission_ledger_path
            else default_exchange_artifact_admission_ledger_path(root)
        )
        result = consume_accepted_scheduler_action_candidate(
            artifact_store_path=store,
            disposition_artifact_id=disposition_artifact_id,
            disposition_version=disposition_version,
            snapshot_path=_resolve_project_path(root, snapshot_path),
            event_log_path=_resolve_project_path(root, event_log_path),
            admission_ledger_path=ledger_path,
            allow_duplicate_admission=allow_duplicate_admission,
            replace_existing=replace_existing,
            validate_binding_artifact_refs=validate_binding_artifact_refs,
            mark_consumed_on_success=mark_consumed_on_success,
            actor=actor,
            timestamp=timestamp,
        )
    except Exception as e:
        return _handle_error(
            "Error consuming accepted scheduler action candidate",
            e,
            category="scheduler_accepted_candidate_consume_failed",
        )

    payload = result.to_json_dict()
    _print_json(payload)
    return 0 if payload.get("ok") else 1


def cmd_scheduler_guide_worker_exchange_dogfood(args: list[str]) -> int:
    """Run deterministic guide/worker exchange product dogfood."""

    if args and args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_GUIDE_WORKER_EXCHANGE_DOGFOOD_USAGE + "\n\n"
            "This seeds a guide-addressed coordination artifact, proves worker "
            "mailbox and reply readback, records a scheduler_submission_candidate "
            "disposition, and consumes the accepted disposition through exact "
            "scheduler admission. It is fake-runtime-safe: it does not run live "
            "providers, refresh projections, persist raw transcripts, or mutate "
            "Local Work Trajectory from runtime/CLI code.",
        )
        return 0

    artifact_store_path = ""
    admission_ledger_path = ""
    snapshot_path = ""
    event_log_path = ""
    guide_agent_id = "agent:guide"
    worker_agent_id = "agent:worker"
    artifact_id_prefix = ""
    timestamp = "2026-06-23T00:00:00Z"
    replace_existing = False
    allow_duplicate_admission = False

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--replace-existing":
            replace_existing = True
            i += 1
            continue
        if arg == "--allow-duplicate-admission":
            allow_duplicate_admission = True
            i += 1
            continue
        if arg in {
            "--artifact-store-path",
            "--admission-ledger-path",
            "--snapshot-path",
            "--event-log-path",
            "--guide-agent-id",
            "--worker-agent-id",
            "--artifact-id-prefix",
            "--timestamp",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_GUIDE_WORKER_EXCHANGE_DOGFOOD_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--admission-ledger-path":
                admission_ledger_path = value
            elif arg == "--snapshot-path":
                snapshot_path = value
            elif arg == "--event-log-path":
                event_log_path = value
            elif arg == "--guide-agent-id":
                guide_agent_id = value
            elif arg == "--worker-agent-id":
                worker_agent_id = value
            elif arg == "--artifact-id-prefix":
                artifact_id_prefix = value
            elif arg == "--timestamp":
                timestamp = value
            i += 2
            continue
        print(f"Unknown scheduler guide-worker-exchange-dogfood option: {arg}", file=sys.stderr)
        print(_SCHEDULER_GUIDE_WORKER_EXCHANGE_DOGFOOD_USAGE, file=sys.stderr)
        return 1

    root = _find_project_root()

    try:
        from .runtime.orchestration import (
            DEFAULT_GUIDE_WORKER_EXCHANGE_DOGFOOD_EVENT_LOG_RELATIVE_PATH,
            DEFAULT_GUIDE_WORKER_EXCHANGE_DOGFOOD_PREFIX,
            DEFAULT_GUIDE_WORKER_EXCHANGE_DOGFOOD_SNAPSHOT_RELATIVE_PATH,
            GuideWorkerExchangeDogfoodRequest,
            default_exchange_artifact_admission_ledger_path,
            default_exchange_artifact_store_path,
            run_guide_worker_exchange_dogfood,
        )

        store = (
            _resolve_project_path(root, artifact_store_path)
            if artifact_store_path
            else default_exchange_artifact_store_path(root)
        )
        ledger_path = (
            _resolve_project_path(root, admission_ledger_path)
            if admission_ledger_path
            else default_exchange_artifact_admission_ledger_path(root)
        )
        snapshot = (
            _resolve_project_path(root, snapshot_path)
            if snapshot_path
            else _resolve_project_path(
                root,
                DEFAULT_GUIDE_WORKER_EXCHANGE_DOGFOOD_SNAPSHOT_RELATIVE_PATH,
            )
        )
        event_log = (
            _resolve_project_path(root, event_log_path)
            if event_log_path
            else _resolve_project_path(
                root,
                DEFAULT_GUIDE_WORKER_EXCHANGE_DOGFOOD_EVENT_LOG_RELATIVE_PATH,
            )
        )
        result = run_guide_worker_exchange_dogfood(
            GuideWorkerExchangeDogfoodRequest(
                artifact_store_path=store,
                admission_ledger_path=ledger_path,
                snapshot_path=snapshot,
                event_log_path=event_log,
                guide_agent_id=guide_agent_id,
                worker_agent_id=worker_agent_id,
                artifact_id_prefix=artifact_id_prefix
                or DEFAULT_GUIDE_WORKER_EXCHANGE_DOGFOOD_PREFIX,
                timestamp=timestamp,
                replace_existing=replace_existing,
                allow_duplicate_admission=allow_duplicate_admission,
            )
        )
    except Exception as e:
        return _handle_error(
            "Error running guide/worker exchange dogfood",
            e,
            category="scheduler_guide_worker_exchange_dogfood_failed",
        )

    payload = result.to_json_dict()
    _print_json(payload)
    return 0 if payload.get("ok") else 1


def _parse_guide_worker_planner_lane_spec(value: str, lane_spec_type):
    """Parse CLI planner lane spec.

    Format: ``LANE_ID=LABEL:FOCUS[:ARTIFACT,ARTIFACT[:SANDBOX_KIND]]``.
    The sandbox kind is optional and defaults to ``shared-process``.
    """

    if "=" not in value:
        raise ValueError("--planner-lane must use LANE_ID=LABEL:FOCUS")
    lane_id, rest = value.split("=", 1)
    parts = rest.split(":", 3)
    if len(parts) < 2:
        raise ValueError("--planner-lane must include label and focus")
    label = parts[0].strip()
    focus = parts[1].strip()
    artifacts = ()
    if len(parts) >= 3 and parts[2].strip():
        artifacts = tuple(
            item.strip()
            for item in parts[2].split(",")
            if item.strip()
        )
    sandbox_kind = "shared-process"
    if len(parts) == 4 and parts[3].strip():
        sandbox_kind = parts[3].strip()
    if sandbox_kind not in {"none", "shared-process", "git-worktree", "docker", "remote-vm"}:
        raise ValueError(
            "--planner-lane SANDBOX_KIND must be one of none, shared-process, "
            "git-worktree, docker, or remote-vm"
        )
    from .runtime.orchestration import SandboxProfile

    return lane_spec_type(
        lane_id=lane_id.strip(),
        label=label,
        focus=focus,
        allowed_artifacts=artifacts,
        sandbox_profile=SandboxProfile(
            profile_id=sandbox_kind,
            profile_kind=sandbox_kind,  # type: ignore[arg-type]
        ),
    )


def _parse_runtime_provider_csv(value: str):
    providers = tuple(
        item.strip()
        for item in value.split(",")
        if item.strip()
    )
    if not providers:
        raise ValueError("--providers requires at least one provider")
    allowed = {"fake", "qoder", "codex", "opencode"}
    for provider in providers:
        if provider not in allowed:
            raise ValueError(
                "--providers values must be fake, qoder, codex, or opencode; "
                f"got {provider!r}"
            )
    normalized: list[str] = []
    for provider in providers:
        if provider not in normalized:
            normalized.append(provider)
    return tuple(normalized)


def _parse_planner_lane_provider_overrides(values: list[str], *, providers: tuple[str, ...]) -> dict[str, str]:
    overrides: dict[str, str] = {}
    allowed = set(providers)
    for value in values:
        if "=" not in value:
            raise ValueError("--planner-lane-provider must use LANE_ID=PROVIDER")
        lane_id, provider = value.split("=", 1)
        lane_id = lane_id.strip()
        provider = provider.strip()
        if not lane_id:
            raise ValueError("--planner-lane-provider requires a non-empty LANE_ID")
        if provider not in {"fake", "qoder", "codex", "opencode"}:
            raise ValueError(
                "--planner-lane-provider PROVIDER must be fake, qoder, codex, or opencode; "
                f"got {provider!r}"
            )
        if provider not in allowed:
            raise ValueError(
                f"--planner-lane-provider for {lane_id!r} requests {provider!r}, "
                f"but --providers is {', '.join(providers)}"
            )
        if lane_id in overrides:
            raise ValueError(f"duplicate --planner-lane-provider for lane {lane_id!r}")
        overrides[lane_id] = provider
    return overrides


def _apply_lane_provider_overrides(lane_specs: list[object], overrides: dict[str, str]) -> list[object]:
    if not overrides:
        return lane_specs
    from dataclasses import replace

    lane_ids = {getattr(spec, "lane_id", "") for spec in lane_specs}
    unknown = sorted(set(overrides) - lane_ids)
    if unknown:
        raise ValueError(
            "--planner-lane-provider references unknown lane(s): "
            + ", ".join(unknown)
        )
    return [
        replace(
            spec,
            worker_runtime_provider=overrides.get(
                getattr(spec, "lane_id", ""),
                getattr(spec, "worker_runtime_provider", ""),
            ),
        )
        for spec in lane_specs
    ]


def cmd_scheduler_guide_worker_local_orchestration(args: list[str]) -> int:
    """Run guide-assigned worker tasks with lane-limited waves."""

    if args and args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_GUIDE_WORKER_LOCAL_ORCHESTRATION_USAGE + "\n\n"
            "This creates a guide instruction artifact, admits a scheduler batch "
            "of worker tasks, and runs a bounded fake-runtime wave with at most "
            "one ready worker task per lane. When explicit worker instructions "
            "are not supplied by lower-level callers, this command uses a narrow "
            "deterministic guide planner from --guide-task-* and --planner-lane "
            "inputs. It defines scheduling parallelism for different lanes, but "
            "does not refresh projections, persist raw transcripts, or mutate "
            "agent-owned Local Work Trajectory.",
        )
        return 0

    artifact_store_path = ""
    admission_ledger_path = ""
    snapshot_path = ""
    event_log_path = ""
    trajectory_id = "local-work:current"
    guide_agent_id = "agent:guide"
    worker_agent_id = "agent:worker"
    artifact_id_prefix = ""
    timestamp = "2026-06-23T00:00:00Z"
    guide_task_title = ""
    guide_task_summary = ""
    planner_lane_specs: list[str] = []
    max_parallel_lanes = 2
    max_waves = 1
    replace_existing = False
    allow_duplicate_admission = False

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--replace-existing":
            replace_existing = True
            i += 1
            continue
        if arg == "--allow-duplicate-admission":
            allow_duplicate_admission = True
            i += 1
            continue
        if arg in {
            "--artifact-store-path",
            "--admission-ledger-path",
            "--snapshot-path",
            "--event-log-path",
            "--trajectory-id",
            "--guide-agent-id",
            "--worker-agent-id",
            "--artifact-id-prefix",
            "--timestamp",
            "--guide-task-title",
            "--guide-task-summary",
            "--planner-lane",
            "--max-parallel-lanes",
            "--max-waves",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_GUIDE_WORKER_LOCAL_ORCHESTRATION_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--admission-ledger-path":
                admission_ledger_path = value
            elif arg == "--snapshot-path":
                snapshot_path = value
            elif arg == "--event-log-path":
                event_log_path = value
            elif arg == "--trajectory-id":
                trajectory_id = value
            elif arg == "--guide-agent-id":
                guide_agent_id = value
            elif arg == "--worker-agent-id":
                worker_agent_id = value
            elif arg == "--artifact-id-prefix":
                artifact_id_prefix = value
            elif arg == "--timestamp":
                timestamp = value
            elif arg == "--guide-task-title":
                guide_task_title = value
            elif arg == "--guide-task-summary":
                guide_task_summary = value
            elif arg == "--planner-lane":
                planner_lane_specs.append(value)
            elif arg == "--max-parallel-lanes":
                try:
                    max_parallel_lanes = int(value)
                except ValueError:
                    print(_SCHEDULER_GUIDE_WORKER_LOCAL_ORCHESTRATION_USAGE, file=sys.stderr)
                    print("--max-parallel-lanes must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--max-waves":
                try:
                    max_waves = int(value)
                except ValueError:
                    print(_SCHEDULER_GUIDE_WORKER_LOCAL_ORCHESTRATION_USAGE, file=sys.stderr)
                    print("--max-waves must be an integer", file=sys.stderr)
                    return 1
            i += 2
            continue
        print(f"Unknown scheduler guide-worker-local-orchestration option: {arg}", file=sys.stderr)
        print(_SCHEDULER_GUIDE_WORKER_LOCAL_ORCHESTRATION_USAGE, file=sys.stderr)
        return 1

    root = _find_project_root()

    try:
        from .runtime.orchestration import (
            DEFAULT_GUIDE_WORKER_LOCAL_ORCHESTRATION_EVENT_LOG_RELATIVE_PATH,
            DEFAULT_GUIDE_WORKER_LOCAL_ORCHESTRATION_PREFIX,
            DEFAULT_GUIDE_WORKER_LOCAL_ORCHESTRATION_SNAPSHOT_RELATIVE_PATH,
            GuideWorkerLocalOrchestrationRequest,
            GuideWorkerPlannerLaneSpec,
            GuideWorkerPlanningRequest,
            default_exchange_artifact_admission_ledger_path,
            default_exchange_artifact_store_path,
            run_guide_worker_local_trajectory_orchestration,
        )

        store = (
            _resolve_project_path(root, artifact_store_path)
            if artifact_store_path
            else default_exchange_artifact_store_path(root)
        )
        ledger_path = (
            _resolve_project_path(root, admission_ledger_path)
            if admission_ledger_path
            else default_exchange_artifact_admission_ledger_path(root)
        )
        snapshot = (
            _resolve_project_path(root, snapshot_path)
            if snapshot_path
            else _resolve_project_path(
                root,
                DEFAULT_GUIDE_WORKER_LOCAL_ORCHESTRATION_SNAPSHOT_RELATIVE_PATH,
            )
        )
        event_log = (
            _resolve_project_path(root, event_log_path)
            if event_log_path
            else _resolve_project_path(
                root,
                DEFAULT_GUIDE_WORKER_LOCAL_ORCHESTRATION_EVENT_LOG_RELATIVE_PATH,
            )
        )
        result = run_guide_worker_local_trajectory_orchestration(
            GuideWorkerLocalOrchestrationRequest(
                artifact_store_path=store,
                admission_ledger_path=ledger_path,
                snapshot_path=snapshot,
                event_log_path=event_log,
                trajectory_id=trajectory_id,
                guide_agent_id=guide_agent_id,
                worker_agent_id=worker_agent_id,
                artifact_id_prefix=artifact_id_prefix
                or DEFAULT_GUIDE_WORKER_LOCAL_ORCHESTRATION_PREFIX,
                timestamp=timestamp,
                planning_request=GuideWorkerPlanningRequest(
                    task_title=guide_task_title,
                    task_summary=guide_task_summary,
                    lane_specs=tuple(
                        _parse_guide_worker_planner_lane_spec(
                            item,
                            GuideWorkerPlannerLaneSpec,
                        )
                        for item in planner_lane_specs
                    ),
                ),
                max_parallel_lanes=max_parallel_lanes,
                max_waves=max_waves,
                replace_existing=replace_existing,
                allow_duplicate_admission=allow_duplicate_admission,
                workspace_root=str(root),
            )
        )
    except Exception as e:
        return _handle_error(
            "Error running guide/worker local orchestration",
            e,
            category="scheduler_guide_worker_local_orchestration_failed",
        )

    payload = result.to_json_dict()
    _print_json(payload)
    return 0 if payload.get("ok") else 1


def cmd_scheduler_consume_accepted_review_candidate(args: list[str]) -> int:
    """Consume an accepted review action-candidate disposition."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_CONSUME_ACCEPTED_REVIEW_CANDIDATE_USAGE + "\n\n"
            "This consumes one accepted review_candidate disposition by dispatching "
            "a review intake payload to the existing FeedbackAPI review intake "
            "adapter. It does not admit scheduler tasks, write handoffs, resolve "
            "merge gates, run providers, refresh projections, or mutate Local Work "
            "Trajectory.",
        )
        return 0

    artifact_store_path = ""
    disposition_artifact_id = ""
    disposition_version = ""
    actor = "operator-cli"

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {
            "--artifact-store-path",
            "--disposition-artifact-id",
            "--disposition-version",
            "--actor",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_CONSUME_ACCEPTED_REVIEW_CANDIDATE_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--disposition-artifact-id":
                disposition_artifact_id = value
            elif arg == "--disposition-version":
                disposition_version = value
            elif arg == "--actor":
                actor = value
            i += 2
            continue
        print(f"Unknown scheduler consume-accepted-review-candidate option: {arg}", file=sys.stderr)
        print(_SCHEDULER_CONSUME_ACCEPTED_REVIEW_CANDIDATE_USAGE, file=sys.stderr)
        return 1

    missing = [
        name
        for name, value in (
            ("--disposition-artifact-id", disposition_artifact_id),
            ("--disposition-version", disposition_version),
        )
        if not value
    ]
    if missing:
        print(_SCHEDULER_CONSUME_ACCEPTED_REVIEW_CANDIDATE_USAGE, file=sys.stderr)
        print(f"Missing required option(s): {', '.join(missing)}", file=sys.stderr)
        return 1

    root = _find_project_root()

    try:
        from .pep.executor import Executor
        from .review.feedback_api import FeedbackAPI
        from .runtime.orchestration import (
            FeedbackAPIReviewIntakeConsumer,
            consume_accepted_review_action_candidate,
            default_exchange_artifact_store_path,
        )

        store = (
            _resolve_project_path(root, artifact_store_path)
            if artifact_store_path
            else default_exchange_artifact_store_path(root)
        )
        feedback_api = FeedbackAPI(Executor(dry_run=True))
        result = consume_accepted_review_action_candidate(
            artifact_store_path=store,
            disposition_artifact_id=disposition_artifact_id,
            disposition_version=disposition_version,
            review_intake_consumer=FeedbackAPIReviewIntakeConsumer(feedback_api),
            actor=actor,
        )
    except Exception as e:
        return _handle_error(
            "Error consuming accepted review action candidate",
            e,
            category="scheduler_accepted_review_candidate_consume_failed",
        )

    payload = result.to_json_dict()
    payload["review_pending"] = feedback_api.list_pending()
    _print_json(payload)
    return 0 if payload.get("ok") else 1


def cmd_scheduler_consume_accepted_handoff_candidate(args: list[str]) -> int:
    """Consume an accepted handoff action-candidate disposition."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_CONSUME_ACCEPTED_HANDOFF_CANDIDATE_USAGE + "\n\n"
            "This consumes one accepted handoff_candidate disposition by dispatching "
            "a schema-valid Handoff payload to the existing handoff delivery "
            "adapter. It does not admit scheduler tasks, open reviews, resolve "
            "merge gates, run providers, refresh projections, or mutate Local Work "
            "Trajectory.",
        )
        return 0

    artifact_store_path = ""
    disposition_artifact_id = ""
    disposition_version = ""
    handoff_dir = ""
    actor = "operator-cli"

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {
            "--artifact-store-path",
            "--disposition-artifact-id",
            "--disposition-version",
            "--handoff-dir",
            "--actor",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_CONSUME_ACCEPTED_HANDOFF_CANDIDATE_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--disposition-artifact-id":
                disposition_artifact_id = value
            elif arg == "--disposition-version":
                disposition_version = value
            elif arg == "--handoff-dir":
                handoff_dir = value
            elif arg == "--actor":
                actor = value
            i += 2
            continue
        print(f"Unknown scheduler consume-accepted-handoff-candidate option: {arg}", file=sys.stderr)
        print(_SCHEDULER_CONSUME_ACCEPTED_HANDOFF_CANDIDATE_USAGE, file=sys.stderr)
        return 1

    missing = [
        name
        for name, value in (
            ("--disposition-artifact-id", disposition_artifact_id),
            ("--disposition-version", disposition_version),
            ("--handoff-dir", handoff_dir),
        )
        if not value
    ]
    if missing:
        print(_SCHEDULER_CONSUME_ACCEPTED_HANDOFF_CANDIDATE_USAGE, file=sys.stderr)
        print(f"Missing required option(s): {', '.join(missing)}", file=sys.stderr)
        return 1

    root = _find_project_root()

    try:
        from .runtime.orchestration import (
            FileHandoffConsumer,
            consume_accepted_handoff_action_candidate,
            default_exchange_artifact_store_path,
        )

        store = (
            _resolve_project_path(root, artifact_store_path)
            if artifact_store_path
            else default_exchange_artifact_store_path(root)
        )
        result = consume_accepted_handoff_action_candidate(
            artifact_store_path=store,
            disposition_artifact_id=disposition_artifact_id,
            disposition_version=disposition_version,
            handoff_consumer=FileHandoffConsumer(_resolve_project_path(root, handoff_dir)),
            actor=actor,
        )
    except Exception as e:
        return _handle_error(
            "Error consuming accepted handoff action candidate",
            e,
            category="scheduler_accepted_handoff_candidate_consume_failed",
        )

    payload = result.to_json_dict()
    _print_json(payload)
    return 0 if payload.get("ok") else 1


def cmd_scheduler_consume_accepted_merge_candidate(args: list[str]) -> int:
    """Consume an accepted merge action-candidate disposition."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_CONSUME_ACCEPTED_MERGE_CANDIDATE_USAGE + "\n\n"
            "This consumes one accepted merge_candidate disposition by resolving "
            "an explicit scheduler merge gate. The gate id and approval decision "
            "must be supplied by the caller; the command does not infer a gate "
            "from ExchangeArtifact relations. It does not admit scheduler tasks, "
            "open reviews, write handoffs, run providers, refresh projections, or "
            "mutate Local Work Trajectory.",
        )
        return 0

    artifact_store_path = ""
    disposition_artifact_id = ""
    disposition_version = ""
    snapshot_path = ""
    merge_gate_event_log_path = ""
    gate_id = ""
    approved: bool | None = None
    reason = ""
    actor = "operator-cli"
    resolved_at = ""
    timestamp = ""

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--approved":
            approved = True
            i += 1
            continue
        if arg == "--rejected":
            approved = False
            i += 1
            continue
        if arg in {
            "--artifact-store-path",
            "--disposition-artifact-id",
            "--disposition-version",
            "--snapshot-path",
            "--merge-gate-event-log-path",
            "--gate-id",
            "--reason",
            "--actor",
            "--resolved-at",
            "--timestamp",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_CONSUME_ACCEPTED_MERGE_CANDIDATE_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--disposition-artifact-id":
                disposition_artifact_id = value
            elif arg == "--disposition-version":
                disposition_version = value
            elif arg == "--snapshot-path":
                snapshot_path = value
            elif arg == "--merge-gate-event-log-path":
                merge_gate_event_log_path = value
            elif arg == "--gate-id":
                gate_id = value
            elif arg == "--reason":
                reason = value
            elif arg == "--actor":
                actor = value
            elif arg == "--resolved-at":
                resolved_at = value
            elif arg == "--timestamp":
                timestamp = value
            i += 2
            continue
        print(f"Unknown scheduler consume-accepted-merge-candidate option: {arg}", file=sys.stderr)
        print(_SCHEDULER_CONSUME_ACCEPTED_MERGE_CANDIDATE_USAGE, file=sys.stderr)
        return 1

    missing = [
        name
        for name, value in (
            ("--disposition-artifact-id", disposition_artifact_id),
            ("--disposition-version", disposition_version),
            ("--snapshot-path", snapshot_path),
            ("--gate-id", gate_id),
        )
        if not value
    ]
    if approved is None:
        missing.append("--approved|--rejected")
    if missing:
        print(_SCHEDULER_CONSUME_ACCEPTED_MERGE_CANDIDATE_USAGE, file=sys.stderr)
        print(f"Missing required option(s): {', '.join(missing)}", file=sys.stderr)
        return 1

    root = _find_project_root()

    try:
        from .runtime.orchestration import (
            consume_accepted_merge_action_candidate,
            default_exchange_artifact_store_path,
        )

        store = (
            _resolve_project_path(root, artifact_store_path)
            if artifact_store_path
            else default_exchange_artifact_store_path(root)
        )
        result = consume_accepted_merge_action_candidate(
            artifact_store_path=store,
            disposition_artifact_id=disposition_artifact_id,
            disposition_version=disposition_version,
            snapshot_path=_resolve_project_path(root, snapshot_path),
            gate_id=gate_id,
            approved=bool(approved),
            reason=reason,
            merge_gate_event_log_path=(
                _resolve_project_path(root, merge_gate_event_log_path)
                if merge_gate_event_log_path
                else None
            ),
            actor=actor,
            resolved_at=resolved_at,
            timestamp=timestamp,
        )
    except Exception as e:
        return _handle_error(
            "Error consuming accepted merge action candidate",
            e,
            category="scheduler_accepted_merge_candidate_consume_failed",
        )

    payload = result.to_json_dict()
    _print_json(payload)
    return 0 if payload.get("ok") else 1


def cmd_scheduler_consume_worker_patch_review(args: list[str]) -> int:
    """Consume an accepted worker patch review proposal disposition."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_CONSUME_WORKER_PATCH_REVIEW_USAGE + "\n\n"
            "This consumes one accepted merge_candidate disposition only when "
            "its source artifact is a worker_patch_review_proposal. The command "
            "can check, apply, or reject the patch explicitly. It does not resolve "
            "scheduler merge gates, run providers, clean sandboxes, refresh "
            "projections, or mutate Local Work Trajectory. Sandbox cleanup remains "
            "a separate explicit cleanup-receipts step.",
        )
        return 0

    artifact_store_path = ""
    disposition_artifact_id = ""
    disposition_version = ""
    action = ""
    source_workspace_root = ""
    reason = ""
    actor = "operator-cli"
    timestamp = ""
    git_executable = "git"

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {
            "--artifact-store-path",
            "--disposition-artifact-id",
            "--disposition-version",
            "--action",
            "--source-workspace-root",
            "--reason",
            "--actor",
            "--timestamp",
            "--git-executable",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_CONSUME_WORKER_PATCH_REVIEW_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--disposition-artifact-id":
                disposition_artifact_id = value
            elif arg == "--disposition-version":
                disposition_version = value
            elif arg == "--action":
                action = value
            elif arg == "--source-workspace-root":
                source_workspace_root = value
            elif arg == "--reason":
                reason = value
            elif arg == "--actor":
                actor = value
            elif arg == "--timestamp":
                timestamp = value
            elif arg == "--git-executable":
                git_executable = value
            i += 2
            continue
        print(f"Unknown scheduler consume-worker-patch-review option: {arg}", file=sys.stderr)
        print(_SCHEDULER_CONSUME_WORKER_PATCH_REVIEW_USAGE, file=sys.stderr)
        return 1

    missing = [
        name
        for name, value in (
            ("--disposition-artifact-id", disposition_artifact_id),
            ("--disposition-version", disposition_version),
            ("--action", action),
        )
        if not value
    ]
    if action in {"check", "apply"} and not source_workspace_root:
        missing.append("--source-workspace-root")
    if missing:
        print(_SCHEDULER_CONSUME_WORKER_PATCH_REVIEW_USAGE, file=sys.stderr)
        print(f"Missing required option(s): {', '.join(missing)}", file=sys.stderr)
        return 1

    root = _find_project_root()

    try:
        from .runtime.orchestration import (
            consume_worker_patch_review_decision,
            default_exchange_artifact_store_path,
        )

        store = (
            _resolve_project_path(root, artifact_store_path)
            if artifact_store_path
            else default_exchange_artifact_store_path(root)
        )
        result = consume_worker_patch_review_decision(
            artifact_store_path=store,
            disposition_artifact_id=disposition_artifact_id,
            disposition_version=disposition_version,
            action=action,  # type: ignore[arg-type]
            source_workspace_root=(
                _resolve_project_path(root, source_workspace_root)
                if source_workspace_root
                else None
            ),
            actor=actor,
            reason=reason,
            timestamp=timestamp,
            git_executable=git_executable,
        )
    except Exception as e:
        return _handle_error(
            "Error consuming worker patch review proposal",
            e,
            category="scheduler_worker_patch_review_consume_failed",
        )

    payload = result.to_json_dict()
    _print_json(payload)
    return 0 if payload.get("ok") else 1


def cmd_scheduler_review_worker_patch(args: list[str]) -> int:
    """Create a disposition and check/reject one worker patch candidate."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_REVIEW_WORKER_PATCH_USAGE + "\n\n"
            "This Host UX friendly operator surface creates an accepted "
            "agent_exchange_action_candidate_disposition for one worker patch "
            "merge_candidate and immediately consumes it through the existing "
            "worker patch review consumer. This narrowed surface supports only "
            "check and reject; source-workspace apply remains available only "
            "through the lower-level consume-worker-patch-review command. It "
            "does not resolve scheduler merge gates, run providers, clean "
            "sandboxes, refresh projections, or mutate Local Work Trajectory.",
        )
        return 0

    artifact_store_path = ""
    candidate_id = ""
    action = ""
    source_workspace_root = ""
    disposition_artifact_id = ""
    disposition_version = "v1"
    reason = ""
    actor = "operator-cli"
    timestamp = ""
    git_executable = "git"

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {
            "--artifact-store-path",
            "--candidate-id",
            "--action",
            "--source-workspace-root",
            "--disposition-artifact-id",
            "--disposition-version",
            "--reason",
            "--actor",
            "--timestamp",
            "--git-executable",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_REVIEW_WORKER_PATCH_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--candidate-id":
                candidate_id = value
            elif arg == "--action":
                action = value
            elif arg == "--source-workspace-root":
                source_workspace_root = value
            elif arg == "--disposition-artifact-id":
                disposition_artifact_id = value
            elif arg == "--disposition-version":
                disposition_version = value
            elif arg == "--reason":
                reason = value
            elif arg == "--actor":
                actor = value
            elif arg == "--timestamp":
                timestamp = value
            elif arg == "--git-executable":
                git_executable = value
            i += 2
            continue
        print(f"Unknown scheduler review-worker-patch option: {arg}", file=sys.stderr)
        print(_SCHEDULER_REVIEW_WORKER_PATCH_USAGE, file=sys.stderr)
        return 1

    missing = [
        name
        for name, value in (
            ("--candidate-id", candidate_id),
            ("--action", action),
        )
        if not value
    ]
    if action not in {"check", "reject"}:
        missing.append("--action check|reject")
    if action == "check" and not source_workspace_root:
        missing.append("--source-workspace-root")
    if missing:
        print(_SCHEDULER_REVIEW_WORKER_PATCH_USAGE, file=sys.stderr)
        print(f"Missing required option(s): {', '.join(missing)}", file=sys.stderr)
        return 1

    root = _find_project_root()

    try:
        from .runtime.orchestration import (
            default_exchange_artifact_store_path,
            review_worker_patch_action_candidate,
        )

        store = (
            _resolve_project_path(root, artifact_store_path)
            if artifact_store_path
            else default_exchange_artifact_store_path(root)
        )
        result = review_worker_patch_action_candidate(
            artifact_store_path=store,
            candidate_id=candidate_id,
            action=action,  # type: ignore[arg-type]
            source_workspace_root=(
                _resolve_project_path(root, source_workspace_root)
                if source_workspace_root
                else None
            ),
            actor=actor,
            disposition_artifact_id=disposition_artifact_id,
            disposition_version=disposition_version,
            reason=reason,
            timestamp=timestamp,
            git_executable=git_executable,
        )
    except Exception as e:
        return _handle_error(
            "Error reviewing worker patch candidate",
            e,
            category="scheduler_worker_patch_review_operator_failed",
        )

    payload = result.to_json_dict()
    _print_json(payload)
    return 0 if payload.get("ok") else 1


def cmd_scheduler_preflight_worker_patch_composition(args: list[str]) -> int:
    """Preflight multiple worker patch proposals without mutating source."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_PREFLIGHT_WORKER_PATCH_COMPOSITION_USAGE + "\n\n"
            "This reads exact worker_patch_review_proposal artifacts and checks "
            "whether they compose in caller order using a temporary workspace. "
            "It runs git apply --check and git apply only in the temporary copy; "
            "it does not mutate the source workspace, write dispositions, resolve "
            "merge gates, clean sandboxes, run providers, or mutate Local Work "
            "Trajectory.",
        )
        return 0

    artifact_store_path = ""
    patch_ref_tokens: list[str] = []
    source_workspace_root = ""
    scratch_root = ""
    git_executable = "git"

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {
            "--artifact-store-path",
            "--patch-ref",
            "--source-workspace-root",
            "--scratch-root",
            "--git-executable",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_PREFLIGHT_WORKER_PATCH_COMPOSITION_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--patch-ref":
                patch_ref_tokens.append(value)
            elif arg == "--source-workspace-root":
                source_workspace_root = value
            elif arg == "--scratch-root":
                scratch_root = value
            elif arg == "--git-executable":
                git_executable = value
            i += 2
            continue
        print(f"Unknown scheduler preflight-worker-patch-composition option: {arg}", file=sys.stderr)
        print(_SCHEDULER_PREFLIGHT_WORKER_PATCH_COMPOSITION_USAGE, file=sys.stderr)
        return 1

    missing = []
    if len(patch_ref_tokens) < 2:
        missing.append("--patch-ref (at least two)")
    if not source_workspace_root:
        missing.append("--source-workspace-root")
    if missing:
        print(_SCHEDULER_PREFLIGHT_WORKER_PATCH_COMPOSITION_USAGE, file=sys.stderr)
        print(f"Missing required option(s): {', '.join(missing)}", file=sys.stderr)
        return 1

    root = _find_project_root()

    try:
        from .runtime.orchestration import (
            default_exchange_artifact_store_path,
            preflight_worker_patch_composition,
            worker_patch_composition_refs_from_tokens,
        )

        store = (
            _resolve_project_path(root, artifact_store_path)
            if artifact_store_path
            else default_exchange_artifact_store_path(root)
        )
        result = preflight_worker_patch_composition(
            artifact_store_path=store,
            patch_refs=worker_patch_composition_refs_from_tokens(tuple(patch_ref_tokens)),
            source_workspace_root=_resolve_project_path(root, source_workspace_root),
            scratch_root=(
                _resolve_project_path(root, scratch_root)
                if scratch_root
                else None
            ),
            git_executable=git_executable,
        )
    except Exception as e:
        return _handle_error(
            "Error preflighting worker patch composition",
            e,
            category="scheduler_worker_patch_composition_preflight_failed",
        )

    payload = result.to_json_dict()
    _print_json(payload)
    return 0 if payload.get("ok") else 1


def cmd_scheduler_consume_accepted_blocker_candidate(args: list[str]) -> int:
    """Consume an accepted blocker action-candidate disposition."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_CONSUME_ACCEPTED_BLOCKER_CANDIDATE_USAGE + "\n\n"
            "This consumes one accepted blocker_candidate disposition by blocking "
            "an explicit scheduler task. The task id and reason must be supplied "
            "by the caller; the command does not infer a task from ExchangeArtifact "
            "relations. It does not admit scheduler tasks, open reviews, write "
            "handoffs, resolve merge gates, run providers, refresh projections, or "
            "mutate Local Work Trajectory.",
        )
        return 0

    artifact_store_path = ""
    disposition_artifact_id = ""
    disposition_version = ""
    snapshot_path = ""
    event_log_path = ""
    task_id = ""
    reason = ""
    actor = "operator-cli"
    timestamp = ""

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {
            "--artifact-store-path",
            "--disposition-artifact-id",
            "--disposition-version",
            "--snapshot-path",
            "--event-log-path",
            "--task-id",
            "--reason",
            "--actor",
            "--timestamp",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_CONSUME_ACCEPTED_BLOCKER_CANDIDATE_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--disposition-artifact-id":
                disposition_artifact_id = value
            elif arg == "--disposition-version":
                disposition_version = value
            elif arg == "--snapshot-path":
                snapshot_path = value
            elif arg == "--event-log-path":
                event_log_path = value
            elif arg == "--task-id":
                task_id = value
            elif arg == "--reason":
                reason = value
            elif arg == "--actor":
                actor = value
            elif arg == "--timestamp":
                timestamp = value
            i += 2
            continue
        print(f"Unknown scheduler consume-accepted-blocker-candidate option: {arg}", file=sys.stderr)
        print(_SCHEDULER_CONSUME_ACCEPTED_BLOCKER_CANDIDATE_USAGE, file=sys.stderr)
        return 1

    missing = [
        name
        for name, value in (
            ("--disposition-artifact-id", disposition_artifact_id),
            ("--disposition-version", disposition_version),
            ("--snapshot-path", snapshot_path),
            ("--task-id", task_id),
            ("--reason", reason),
        )
        if not value
    ]
    if missing:
        print(_SCHEDULER_CONSUME_ACCEPTED_BLOCKER_CANDIDATE_USAGE, file=sys.stderr)
        print(f"Missing required option(s): {', '.join(missing)}", file=sys.stderr)
        return 1

    root = _find_project_root()

    try:
        from .runtime.orchestration import (
            consume_accepted_blocker_action_candidate,
            default_exchange_artifact_store_path,
        )

        store = (
            _resolve_project_path(root, artifact_store_path)
            if artifact_store_path
            else default_exchange_artifact_store_path(root)
        )
        result = consume_accepted_blocker_action_candidate(
            artifact_store_path=store,
            disposition_artifact_id=disposition_artifact_id,
            disposition_version=disposition_version,
            snapshot_path=_resolve_project_path(root, snapshot_path),
            task_id=task_id,
            reason=reason,
            event_log_path=(
                _resolve_project_path(root, event_log_path)
                if event_log_path
                else None
            ),
            actor=actor,
            timestamp=timestamp,
        )
    except Exception as e:
        return _handle_error(
            "Error consuming accepted blocker action candidate",
            e,
            category="scheduler_accepted_blocker_candidate_consume_failed",
        )

    payload = result.to_json_dict()
    _print_json(payload)
    return 0 if payload.get("ok") else 1


def cmd_scheduler_reply_exchange_artifact(args: list[str]) -> int:
    """Create a reply ExchangeArtifact in the local store."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_REPLY_EXCHANGE_ARTIFACT_USAGE + "\n\n"
            "This writes one exact-version reply artifact to the local "
            "ExchangeArtifact store. It does not admit scheduler tasks, run "
            "providers, refresh projections, write admission ledgers, or mutate "
            "Local Work Trajectory.",
        )
        return 0

    artifact_store_path = ""
    source_artifact_id = ""
    source_version = ""
    reply_artifact_id = ""
    reply_version = "v1"
    producer = ""
    text = ""
    structured_json = ""
    kind = "message"
    intent = "inform"
    audience: tuple[str, ...] = ()
    created_at = ""
    replace_existing = False

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--replace-existing":
            replace_existing = True
            i += 1
            continue
        if arg in {
            "--artifact-store-path",
            "--source-artifact-id",
            "--source-version",
            "--reply-artifact-id",
            "--reply-version",
            "--producer",
            "--text",
            "--structured-json",
            "--kind",
            "--intent",
            "--audience",
            "--created-at",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_REPLY_EXCHANGE_ARTIFACT_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--source-artifact-id":
                source_artifact_id = value
            elif arg == "--source-version":
                source_version = value
            elif arg == "--reply-artifact-id":
                reply_artifact_id = value
            elif arg == "--reply-version":
                reply_version = value
            elif arg == "--producer":
                producer = value
            elif arg == "--text":
                text = value
            elif arg == "--structured-json":
                structured_json = value
            elif arg == "--kind":
                kind = value
            elif arg == "--intent":
                intent = value
            elif arg == "--audience":
                audience = tuple(item.strip() for item in value.split(",") if item.strip())
            elif arg == "--created-at":
                created_at = value
            i += 2
            continue
        print(f"Unknown scheduler reply-exchange-artifact option: {arg}", file=sys.stderr)
        print(_SCHEDULER_REPLY_EXCHANGE_ARTIFACT_USAGE, file=sys.stderr)
        return 1

    missing = []
    for value, name in (
        (source_artifact_id, "--source-artifact-id"),
        (source_version, "--source-version"),
        (reply_artifact_id, "--reply-artifact-id"),
        (producer, "--producer"),
    ):
        if not value:
            missing.append(name)
    if not text and not structured_json:
        missing.append("--text or --structured-json")
    if missing:
        print(_SCHEDULER_REPLY_EXCHANGE_ARTIFACT_USAGE, file=sys.stderr)
        print(f"Missing required option(s): {', '.join(missing)}", file=sys.stderr)
        return 1

    root = _find_project_root()

    try:
        from .runtime.orchestration import (
            default_exchange_artifact_store_path,
            reply_to_exchange_artifact,
        )

        structured = {}
        if structured_json:
            parsed = json.loads(structured_json)
            if not isinstance(parsed, dict):
                raise ValueError("--structured-json must be a JSON object")
            structured = parsed
        store_path = (
            _resolve_project_path(root, artifact_store_path)
            if artifact_store_path
            else default_exchange_artifact_store_path(root)
        )
        result = reply_to_exchange_artifact(
            store_path=store_path,
            source_artifact_id=source_artifact_id,
            source_version=source_version,
            reply_artifact_id=reply_artifact_id,
            reply_version=reply_version,
            producer=producer,
            text=text,
            structured=structured,
            kind=kind,  # type: ignore[arg-type]
            intent=intent,  # type: ignore[arg-type]
            audience=audience,
            created_at=created_at,
            replace_existing=replace_existing,
        )
    except Exception as e:
        return _handle_error(
            "Error replying to exchange artifact",
            e,
            category="scheduler_exchange_reply_failed",
        )

    _print_json(result.to_json_dict())
    return 0


def cmd_scheduler_transition_exchange_artifact(args: list[str]) -> int:
    """Transition one exact ExchangeArtifact lifecycle state."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_TRANSITION_EXCHANGE_ARTIFACT_USAGE + "\n\n"
            "This rewrites only one exact ExchangeArtifact store version and "
            "appends a compact log part. It does not admit scheduler tasks, run "
            "providers, refresh projections, write admission ledgers, or mutate "
            "Local Work Trajectory.",
        )
        return 0

    artifact_store_path = ""
    artifact_id = ""
    version = ""
    target_state = ""
    actor = ""
    reason = ""
    timestamp = ""

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {
            "--artifact-store-path",
            "--artifact-id",
            "--version",
            "--target-state",
            "--actor",
            "--reason",
            "--timestamp",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_TRANSITION_EXCHANGE_ARTIFACT_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--artifact-id":
                artifact_id = value
            elif arg == "--version":
                version = value
            elif arg == "--target-state":
                target_state = value
            elif arg == "--actor":
                actor = value
            elif arg == "--reason":
                reason = value
            elif arg == "--timestamp":
                timestamp = value
            i += 2
            continue
        print(f"Unknown scheduler transition-exchange-artifact option: {arg}", file=sys.stderr)
        print(_SCHEDULER_TRANSITION_EXCHANGE_ARTIFACT_USAGE, file=sys.stderr)
        return 1

    missing = []
    for value, name in (
        (artifact_id, "--artifact-id"),
        (version, "--version"),
        (target_state, "--target-state"),
        (actor, "--actor"),
    ):
        if not value:
            missing.append(name)
    if missing:
        print(_SCHEDULER_TRANSITION_EXCHANGE_ARTIFACT_USAGE, file=sys.stderr)
        print(f"Missing required option(s): {', '.join(missing)}", file=sys.stderr)
        return 1

    root = _find_project_root()

    try:
        from .runtime.orchestration import (
            default_exchange_artifact_store_path,
            transition_exchange_artifact_lifecycle,
        )

        store_path = (
            _resolve_project_path(root, artifact_store_path)
            if artifact_store_path
            else default_exchange_artifact_store_path(root)
        )
        result = transition_exchange_artifact_lifecycle(
            store_path=store_path,
            artifact_id=artifact_id,
            version=version,
            target_state=target_state,  # type: ignore[arg-type]
            actor=actor,
            reason=reason,
            timestamp=timestamp,
        )
    except Exception as e:
        return _handle_error(
            "Error transitioning exchange artifact lifecycle",
            e,
            category="scheduler_exchange_transition_failed",
        )

    _print_json(result.to_json_dict())
    return 0


def cmd_scheduler_publish_storage_binding_artifact(args: list[str]) -> int:
    """Publish compact supervisor storage binding evidence as an ExchangeArtifact."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_PUBLISH_STORAGE_BINDING_ARTIFACT_USAGE + "\n\n"
            "This reads one durable supervisor storage binding evidence summary, "
            "projects it into a compact ExchangeArtifact, and writes that exact "
            "artifact version to the local ExchangeArtifact store. It does not "
            "create agent home or scratch directories, write scratch manifests, "
            "admit scheduler tasks, run providers, refresh projection, read raw "
            "binding payloads into exchange artifacts, or mutate Local Work "
            "Trajectory.",
        )
        return 0

    evidence_path = ""
    artifact_store_path = ""
    artifact_id = ""
    version = "v1"
    producer = ""
    audience = ("scheduler", "workspace-registration")
    created_at = ""
    replace_existing = False

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--replace-existing":
            replace_existing = True
            i += 1
            continue
        if arg in {
            "--evidence-path",
            "--artifact-store-path",
            "--artifact-id",
            "--version",
            "--producer",
            "--audience",
            "--created-at",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_PUBLISH_STORAGE_BINDING_ARTIFACT_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--evidence-path":
                evidence_path = value
            elif arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--artifact-id":
                artifact_id = value
            elif arg == "--version":
                version = value
            elif arg == "--producer":
                producer = value
            elif arg == "--audience":
                audience = tuple(item.strip() for item in value.split(",") if item.strip())
            elif arg == "--created-at":
                created_at = value
            i += 2
            continue
        print(
            f"Unknown scheduler publish-storage-binding-artifact option: {arg}",
            file=sys.stderr,
        )
        print(_SCHEDULER_PUBLISH_STORAGE_BINDING_ARTIFACT_USAGE, file=sys.stderr)
        return 1

    if not evidence_path:
        print(_SCHEDULER_PUBLISH_STORAGE_BINDING_ARTIFACT_USAGE, file=sys.stderr)
        print("Missing required option(s): --evidence-path", file=sys.stderr)
        return 1

    root = _find_project_root()

    try:
        from .runtime.orchestration import (
            default_exchange_artifact_store_path,
            publish_supervisor_storage_binding_artifact_from_evidence,
        )

        store_path = (
            _resolve_project_path(root, artifact_store_path)
            if artifact_store_path
            else default_exchange_artifact_store_path(root)
        )
        result = publish_supervisor_storage_binding_artifact_from_evidence(
            evidence_path=_resolve_project_path(root, evidence_path),
            artifact_store_path=store_path,
            artifact_id=artifact_id,
            version=version,
            producer=producer,
            audience=audience,
            created_at=created_at,
            replace_existing=replace_existing,
        )
    except Exception as e:
        return _handle_error(
            "Error publishing supervisor storage binding artifact",
            e,
            category="scheduler_storage_binding_artifact_publish_failed",
        )

    _print_json(result.to_json_dict())
    return 0


def cmd_scheduler_inspect_state(args: list[str]) -> int:
    """Read scheduler snapshot and optional event logs without mutation."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_INSPECT_STATE_USAGE + "\n\n"
            "This is a readback command. It does not write scheduler state, refresh projection, "
            "run providers, or mutate Local Work Trajectory.",
        )
        return 0

    snapshot_path = ""
    event_log_path = ""
    merge_gate_event_log_path = ""

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {"--snapshot-path", "--event-log-path", "--merge-gate-event-log-path"}:
            if i + 1 >= len(args):
                print(_SCHEDULER_INSPECT_STATE_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--snapshot-path":
                snapshot_path = value
            elif arg == "--event-log-path":
                event_log_path = value
            elif arg == "--merge-gate-event-log-path":
                merge_gate_event_log_path = value
            i += 2
            continue
        print(f"Unknown scheduler inspect-state option: {arg}", file=sys.stderr)
        print(_SCHEDULER_INSPECT_STATE_USAGE, file=sys.stderr)
        return 1

    if not snapshot_path:
        print(_SCHEDULER_INSPECT_STATE_USAGE, file=sys.stderr)
        print("Missing required option(s): --snapshot-path", file=sys.stderr)
        return 1

    root = _find_project_root()
    snapshot = _resolve_project_path(root, snapshot_path)
    scheduler_log = _resolve_project_path(root, event_log_path) if event_log_path else None
    merge_gate_log = (
        _resolve_project_path(root, merge_gate_event_log_path)
        if merge_gate_event_log_path
        else None
    )

    try:
        from .runtime.orchestration import (
            JsonlSchedulerEventLog,
            JsonlSchedulerMergeGateEventLog,
            read_scheduler_state_snapshot,
        )

        state = read_scheduler_state_snapshot(snapshot)
        scheduler_events = (
            JsonlSchedulerEventLog(scheduler_log).read_all()
            if scheduler_log is not None
            else ()
        )
        merge_gate_events = (
            JsonlSchedulerMergeGateEventLog(merge_gate_log).read_all()
            if merge_gate_log is not None
            else ()
        )
    except Exception as e:
        return _handle_error(
            "Error inspecting scheduler state",
            e,
            category="scheduler_inspect_failed",
        )

    state_counts: dict[str, int] = {}
    task_ids_by_state: dict[str, list[str]] = {}
    for task_id, task in sorted(state.tasks.items()):
        state_counts[task.state] = state_counts.get(task.state, 0) + 1
        task_ids_by_state.setdefault(task.state, []).append(task_id)
    event_kind_counts: dict[str, int] = {}
    for event in scheduler_events:
        event_kind_counts[event.event_kind] = event_kind_counts.get(event.event_kind, 0) + 1
    merge_gate_event_kind_counts: dict[str, int] = {}
    for event in merge_gate_events:
        merge_gate_event_kind_counts[event.event_kind] = (
            merge_gate_event_kind_counts.get(event.event_kind, 0) + 1
        )

    _print_json(
        {
            "ok": True,
            "snapshot_path": str(snapshot),
            "snapshot_exists": snapshot.exists(),
            "scheduler_event_log_path": "" if scheduler_log is None else str(scheduler_log),
            "scheduler_event_log_exists": False if scheduler_log is None else scheduler_log.exists(),
            "merge_gate_event_log_path": "" if merge_gate_log is None else str(merge_gate_log),
            "merge_gate_event_log_exists": False if merge_gate_log is None else merge_gate_log.exists(),
            "task_count": len(state.tasks),
            "dependency_count": len(state.dependencies),
            "run_record_count": len(state.run_records),
            "merge_gate_count": len(state.merge_gates),
            "task_state_counts": state_counts,
            "task_ids_by_state": task_ids_by_state,
            "dependency_ids": [dependency.dependency_id for dependency in state.dependencies],
            "run_record_task_ids": [record.task_id for record in state.run_records],
            "merge_gate_ids": [gate.gate_id for gate in state.merge_gates],
            "scheduler_event_count": len(scheduler_events),
            "scheduler_event_ids": [event.event_id for event in scheduler_events],
            "scheduler_event_kind_counts": event_kind_counts,
            "merge_gate_event_count": len(merge_gate_events),
            "merge_gate_event_ids": [event.event_id for event in merge_gate_events],
            "merge_gate_event_kind_counts": merge_gate_event_kind_counts,
            "ran_tasks": False,
            "refreshed_projection": False,
            "authority_split": {
                "scheduler_state_authority": "scheduler_snapshot",
                "scheduler_state_mutated": False,
                "provider_executed": False,
                "scheduler_projection_refreshed": False,
                "local_work_trajectory_mutated": False,
            },
        }
    )
    return 0


def cmd_scheduler_tick(args: list[str]) -> int:
    """Run one bounded daemon-ready fake-runtime scheduler tick."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_TICK_USAGE + "\n\n"
            "This writes scheduler snapshot/event-log state through one bounded fake-runtime "
            "tick. It does not refresh scheduler projection, run real providers, mutate "
            "exchange artifacts, or mutate Local Work Trajectory.",
        )
        return 0

    snapshot_path = ""
    event_log_path = ""
    runtime_provider = "fake"
    timestamp = ""
    max_runs: int | None = 1

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {
            "--snapshot-path",
            "--event-log-path",
            "--runtime-provider",
            "--timestamp",
            "--max-runs",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_TICK_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--snapshot-path":
                snapshot_path = value
            elif arg == "--event-log-path":
                event_log_path = value
            elif arg == "--runtime-provider":
                runtime_provider = value
            elif arg == "--timestamp":
                timestamp = value
            elif arg == "--max-runs":
                try:
                    max_runs = int(value)
                except ValueError:
                    print(_SCHEDULER_TICK_USAGE, file=sys.stderr)
                    print("--max-runs must be an integer", file=sys.stderr)
                    return 1
            i += 2
            continue
        print(f"Unknown scheduler tick option: {arg}", file=sys.stderr)
        print(_SCHEDULER_TICK_USAGE, file=sys.stderr)
        return 1

    missing = [
        name
        for name, value in (
            ("--snapshot-path", snapshot_path),
            ("--event-log-path", event_log_path),
        )
        if not value
    ]
    if missing:
        print(_SCHEDULER_TICK_USAGE, file=sys.stderr)
        print(f"Missing required option(s): {', '.join(missing)}", file=sys.stderr)
        return 1
    if runtime_provider != "fake":
        print(
            "scheduler tick currently supports only --runtime-provider fake; "
            "real providers require host-owned injected runtime wiring",
            file=sys.stderr,
        )
        return 1

    root = _find_project_root()
    snapshot = _resolve_project_path(root, snapshot_path)
    event_log = _resolve_project_path(root, event_log_path)

    try:
        from .runtime.orchestration import (
            SchedulerDaemonTickRequest,
            run_scheduler_daemon_tick,
        )

        result = run_scheduler_daemon_tick(
            SchedulerDaemonTickRequest(
                snapshot_path=snapshot,
                event_log_path=event_log,
                max_runs=max_runs,
                runtime_provider=runtime_provider,
                timestamp=timestamp,
                workspace_root=str(root),
            )
        )
    except Exception as e:
        return _handle_error(
            "Error running scheduler tick",
            e,
            category="scheduler_tick_failed",
        )

    _print_json(result.to_json_dict())
    return 0


def cmd_scheduler_daemon_loop(args: list[str]) -> int:
    """Run a bounded daemon loop over fake-runtime scheduler ticks."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_DAEMON_LOOP_USAGE + "\n\n"
            "This writes scheduler snapshot/event-log state through a repeated bounded "
            "fake-runtime loop. It does not refresh scheduler projection, run real providers, "
            "mutate exchange artifacts, or mutate Local Work Trajectory.",
        )
        return 0

    snapshot_path = ""
    event_log_path = ""
    runtime_provider = "fake"
    timestamp = ""
    max_ticks = 1
    max_runs_per_tick: int | None = 1
    max_runtime_failures: int | None = 1
    evidence_id = ""
    evidence_path = ""

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {
            "--snapshot-path",
            "--event-log-path",
            "--runtime-provider",
            "--timestamp",
            "--max-ticks",
            "--max-runs-per-tick",
            "--max-runtime-failures",
            "--evidence-id",
            "--evidence-path",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_DAEMON_LOOP_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--snapshot-path":
                snapshot_path = value
            elif arg == "--event-log-path":
                event_log_path = value
            elif arg == "--runtime-provider":
                runtime_provider = value
            elif arg == "--timestamp":
                timestamp = value
            elif arg == "--max-ticks":
                try:
                    max_ticks = int(value)
                except ValueError:
                    print(_SCHEDULER_DAEMON_LOOP_USAGE, file=sys.stderr)
                    print("--max-ticks must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--max-runs-per-tick":
                try:
                    max_runs_per_tick = int(value)
                except ValueError:
                    print(_SCHEDULER_DAEMON_LOOP_USAGE, file=sys.stderr)
                    print("--max-runs-per-tick must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--max-runtime-failures":
                try:
                    max_runtime_failures = int(value)
                except ValueError:
                    print(_SCHEDULER_DAEMON_LOOP_USAGE, file=sys.stderr)
                    print("--max-runtime-failures must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--evidence-id":
                evidence_id = value
            elif arg == "--evidence-path":
                evidence_path = value
            i += 2
            continue
        print(f"Unknown scheduler daemon-loop option: {arg}", file=sys.stderr)
        print(_SCHEDULER_DAEMON_LOOP_USAGE, file=sys.stderr)
        return 1

    missing = [
        name
        for name, value in (
            ("--snapshot-path", snapshot_path),
            ("--event-log-path", event_log_path),
        )
        if not value
    ]
    if missing:
        print(_SCHEDULER_DAEMON_LOOP_USAGE, file=sys.stderr)
        print(f"Missing required option(s): {', '.join(missing)}", file=sys.stderr)
        return 1
    if runtime_provider != "fake":
        print(
            "scheduler daemon-loop currently supports only --runtime-provider fake; "
            "real providers require host-owned injected runtime wiring",
            file=sys.stderr,
        )
        return 1

    root = _find_project_root()
    snapshot = _resolve_project_path(root, snapshot_path)
    event_log = _resolve_project_path(root, event_log_path)

    try:
        from .runtime.orchestration import (
            SchedulerDaemonLoopRequest,
            SchedulerDaemonLoopStopPolicy,
            build_scheduler_loop_evidence,
            default_scheduler_loop_evidence_path,
            run_scheduler_daemon_loop,
            write_scheduler_loop_evidence,
        )

        result = run_scheduler_daemon_loop(
            SchedulerDaemonLoopRequest(
                snapshot_path=snapshot,
                event_log_path=event_log,
                stop_policy=SchedulerDaemonLoopStopPolicy(
                    max_ticks=max_ticks,
                    max_runs_per_tick=max_runs_per_tick,
                    max_runtime_failures=max_runtime_failures,
                ),
                runtime_provider=runtime_provider,
                timestamp=timestamp,
                workspace_root=str(root),
            )
        )
        payload = result.to_json_dict()
        payload["evidence_written"] = False
        payload["evidence_path"] = ""
        if evidence_id:
            target = (
                _resolve_project_path(root, evidence_path)
                if evidence_path
                else default_scheduler_loop_evidence_path(root, evidence_id)
            )
            written = write_scheduler_loop_evidence(
                build_scheduler_loop_evidence(
                    result,
                    evidence_id=evidence_id,
                    timestamp=timestamp,
                    evidence_path=target,
                    metadata={"surface": "cli:scheduler daemon-loop"},
                ),
                target,
            )
            payload["evidence_written"] = True
            payload["evidence_path"] = str(written.evidence_path)
            payload["authority_split"]["evidence_written"] = True
            payload["authority_split"]["evidence_path"] = str(written.evidence_path)
    except Exception as e:
        return _handle_error(
            "Error running scheduler daemon loop",
            e,
            category="scheduler_daemon_loop_failed",
        )

    _print_json(payload)
    return 0


def cmd_scheduler_lifecycle(args: list[str]) -> int:
    """Read or mutate scheduler daemon lifecycle control state."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_LIFECYCLE_USAGE + "\n\n"
            "This reads or writes only the scheduler daemon lifecycle control file, "
            "except run-once and harness, which may mutate scheduler snapshot/event-log state "
            "through bounded fake-runtime daemon loops. It does not refresh "
            "scheduler projection, run real providers, mutate exchange artifacts, "
            "or mutate Local Work Trajectory.",
        )
        return 0

    lifecycle_action = args[0]
    allowed_actions = {
        "inspect",
        "start",
        "heartbeat",
        "pause",
        "resume",
        "cancel",
        "shutdown",
        "run-once",
        "harness",
        "supervisor-step",
    }
    if lifecycle_action not in allowed_actions:
        print(_SCHEDULER_LIFECYCLE_USAGE, file=sys.stderr)
        print(f"Unknown scheduler lifecycle action: {lifecycle_action}", file=sys.stderr)
        return 1

    control_path = ""
    snapshot_path = ""
    event_log_path = ""
    daemon_id = ""
    run_id = ""
    timestamp = ""
    runtime_provider = "fake"
    stale_after_seconds: int | None = None
    now_epoch_seconds: int | None = None
    max_ticks = 1
    max_runs_per_tick: int | None = 1
    max_runtime_failures: int | None = 1
    max_cycles = 1
    max_loop_failures: int | None = 1
    policy_cancelled = False
    deadline_epoch_seconds: int | None = None
    max_attempts = 1
    retry_stop_reasons: tuple[str, ...] = ()
    supervisor_id = ""
    session_id = ""
    host_id = ""
    requested_by = ""
    status_readback_at = ""
    cancellation_source = ""
    cancellation_reason = ""

    i = 1
    while i < len(args):
        arg = args[i]
        if arg == "--policy-cancelled":
            policy_cancelled = True
            i += 1
            continue
        if arg in {
            "--control-path",
            "--snapshot-path",
            "--event-log-path",
            "--daemon-id",
            "--run-id",
            "--timestamp",
            "--runtime-provider",
            "--stale-after-seconds",
            "--now-epoch-seconds",
            "--max-ticks",
            "--max-runs-per-tick",
            "--max-runtime-failures",
            "--max-cycles",
            "--max-loop-failures",
            "--deadline-epoch-seconds",
            "--max-attempts",
            "--retry-stop-reasons",
            "--supervisor-id",
            "--session-id",
            "--host-id",
            "--requested-by",
            "--status-readback-at",
            "--cancellation-source",
            "--cancellation-reason",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_LIFECYCLE_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--control-path":
                control_path = value
            elif arg == "--snapshot-path":
                snapshot_path = value
            elif arg == "--event-log-path":
                event_log_path = value
            elif arg == "--daemon-id":
                daemon_id = value
            elif arg == "--run-id":
                run_id = value
            elif arg == "--timestamp":
                timestamp = value
            elif arg == "--runtime-provider":
                runtime_provider = value
            elif arg == "--stale-after-seconds":
                try:
                    stale_after_seconds = int(value)
                except ValueError:
                    print(_SCHEDULER_LIFECYCLE_USAGE, file=sys.stderr)
                    print("--stale-after-seconds must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--now-epoch-seconds":
                try:
                    now_epoch_seconds = int(value)
                except ValueError:
                    print(_SCHEDULER_LIFECYCLE_USAGE, file=sys.stderr)
                    print("--now-epoch-seconds must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--max-ticks":
                try:
                    max_ticks = int(value)
                except ValueError:
                    print(_SCHEDULER_LIFECYCLE_USAGE, file=sys.stderr)
                    print("--max-ticks must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--max-runs-per-tick":
                try:
                    max_runs_per_tick = int(value)
                except ValueError:
                    print(_SCHEDULER_LIFECYCLE_USAGE, file=sys.stderr)
                    print("--max-runs-per-tick must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--max-runtime-failures":
                try:
                    max_runtime_failures = int(value)
                except ValueError:
                    print(_SCHEDULER_LIFECYCLE_USAGE, file=sys.stderr)
                    print("--max-runtime-failures must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--max-cycles":
                try:
                    max_cycles = int(value)
                except ValueError:
                    print(_SCHEDULER_LIFECYCLE_USAGE, file=sys.stderr)
                    print("--max-cycles must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--max-loop-failures":
                try:
                    max_loop_failures = int(value)
                except ValueError:
                    print(_SCHEDULER_LIFECYCLE_USAGE, file=sys.stderr)
                    print("--max-loop-failures must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--deadline-epoch-seconds":
                try:
                    deadline_epoch_seconds = int(value)
                except ValueError:
                    print(_SCHEDULER_LIFECYCLE_USAGE, file=sys.stderr)
                    print("--deadline-epoch-seconds must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--max-attempts":
                try:
                    max_attempts = int(value)
                except ValueError:
                    print(_SCHEDULER_LIFECYCLE_USAGE, file=sys.stderr)
                    print("--max-attempts must be an integer", file=sys.stderr)
                    return 1
            elif arg == "--retry-stop-reasons":
                retry_stop_reasons = tuple(
                    item.strip()
                    for item in value.split(",")
                    if item.strip()
                )
            elif arg == "--supervisor-id":
                supervisor_id = value
            elif arg == "--session-id":
                session_id = value
            elif arg == "--host-id":
                host_id = value
            elif arg == "--requested-by":
                requested_by = value
            elif arg == "--status-readback-at":
                status_readback_at = value
            elif arg == "--cancellation-source":
                cancellation_source = value
            elif arg == "--cancellation-reason":
                cancellation_reason = value
            i += 2
            continue
        print(f"Unknown scheduler lifecycle option: {arg}", file=sys.stderr)
        print(_SCHEDULER_LIFECYCLE_USAGE, file=sys.stderr)
        return 1

    if not control_path:
        print(_SCHEDULER_LIFECYCLE_USAGE, file=sys.stderr)
        print("Missing required option(s): --control-path", file=sys.stderr)
        return 1
    if lifecycle_action == "start":
        missing = [
            name
            for name, value in (
                ("--snapshot-path", snapshot_path),
                ("--event-log-path", event_log_path),
                ("--daemon-id", daemon_id),
            )
            if not value
        ]
        if missing:
            print(_SCHEDULER_LIFECYCLE_USAGE, file=sys.stderr)
            print(f"Missing required option(s): {', '.join(missing)}", file=sys.stderr)
            return 1
    if lifecycle_action in {"run-once", "harness", "supervisor-step"} and runtime_provider != "fake":
        print(
            f"scheduler lifecycle {lifecycle_action} currently supports only --runtime-provider fake; "
            "real providers require host-owned injected runtime wiring",
            file=sys.stderr,
        )
        return 1
    if lifecycle_action == "supervisor-step" and not supervisor_id:
        print(_SCHEDULER_LIFECYCLE_USAGE, file=sys.stderr)
        print("Missing required option(s): --supervisor-id", file=sys.stderr)
        return 1

    root = _find_project_root()
    control = _resolve_project_path(root, control_path)

    try:
        from .runtime.orchestration import (
            SchedulerDaemonLifecycleRequest,
            SchedulerDaemonLifecycleRunOnceRequest,
            SchedulerDaemonLoopStopPolicy,
            SchedulerDaemonHarnessRequest,
            SchedulerDaemonHarnessPolicy,
            SchedulerDaemonSupervisorRequest,
            apply_scheduler_daemon_lifecycle_action,
            inspect_scheduler_daemon_lifecycle_control,
            run_scheduler_daemon_harness_with_policy,
            run_scheduler_daemon_lifecycle_once,
            run_scheduler_daemon_supervisor_step,
        )

        if lifecycle_action == "inspect":
            result = inspect_scheduler_daemon_lifecycle_control(
                control,
                now_epoch_seconds=now_epoch_seconds,
                stale_after_seconds=stale_after_seconds,
            )
        elif lifecycle_action == "run-once":
            result = run_scheduler_daemon_lifecycle_once(
                SchedulerDaemonLifecycleRunOnceRequest(
                    control_path=control,
                    stop_policy=SchedulerDaemonLoopStopPolicy(
                        max_ticks=max_ticks,
                        max_runs_per_tick=max_runs_per_tick,
                        max_runtime_failures=max_runtime_failures,
                    ),
                    runtime_provider=runtime_provider,
                    timestamp=timestamp,
                    workspace_root=str(root),
                )
            )
        elif lifecycle_action == "harness":
            result = run_scheduler_daemon_harness_with_policy(
                SchedulerDaemonHarnessRequest(
                    control_path=control,
                    max_cycles=max_cycles,
                    stop_policy=SchedulerDaemonLoopStopPolicy(
                        max_ticks=max_ticks,
                        max_runs_per_tick=max_runs_per_tick,
                        max_runtime_failures=max_runtime_failures,
                    ),
                    runtime_provider=runtime_provider,
                    timestamp=timestamp,
                    workspace_root=str(root),
                    stale_now_epoch_seconds=now_epoch_seconds,
                    stale_after_seconds=stale_after_seconds,
                    max_loop_failures=max_loop_failures,
                ),
                SchedulerDaemonHarnessPolicy(
                    cancelled=policy_cancelled,
                    deadline_epoch_seconds=deadline_epoch_seconds,
                    now_epoch_seconds=now_epoch_seconds,
                    max_attempts=max_attempts,
                    retry_stop_reasons=retry_stop_reasons,
                )
            )
        elif lifecycle_action == "supervisor-step":
            result = run_scheduler_daemon_supervisor_step(
                SchedulerDaemonSupervisorRequest(
                    supervisor_id=supervisor_id,
                    session_id=session_id,
                    run_id=run_id,
                    host_id=host_id,
                    requested_by=requested_by,
                    status_readback_at=status_readback_at,
                    cancellation_source=cancellation_source,
                    cancellation_reason=cancellation_reason,
                    harness_request=SchedulerDaemonHarnessRequest(
                        control_path=control,
                        max_cycles=max_cycles,
                        stop_policy=SchedulerDaemonLoopStopPolicy(
                            max_ticks=max_ticks,
                            max_runs_per_tick=max_runs_per_tick,
                            max_runtime_failures=max_runtime_failures,
                        ),
                        runtime_provider=runtime_provider,
                        timestamp=timestamp,
                        workspace_root=str(root),
                        stale_now_epoch_seconds=now_epoch_seconds,
                        stale_after_seconds=stale_after_seconds,
                        max_loop_failures=max_loop_failures,
                    ),
                    policy=SchedulerDaemonHarnessPolicy(
                        cancelled=policy_cancelled,
                        deadline_epoch_seconds=deadline_epoch_seconds,
                        now_epoch_seconds=now_epoch_seconds,
                        max_attempts=max_attempts,
                        retry_stop_reasons=retry_stop_reasons,
                    ),
                )
            )
        else:
            runtime_action = "cancel" if lifecycle_action == "cancel" else lifecycle_action
            result = apply_scheduler_daemon_lifecycle_action(
                SchedulerDaemonLifecycleRequest(
                    control_path=control,
                    action=runtime_action,  # type: ignore[arg-type]
                    daemon_id=daemon_id,
                    snapshot_path=(
                        _resolve_project_path(root, snapshot_path)
                        if snapshot_path
                        else None
                    ),
                    event_log_path=(
                        _resolve_project_path(root, event_log_path)
                        if event_log_path
                        else None
                    ),
                    run_id=run_id,
                    timestamp=timestamp,
                    stale_after_seconds=stale_after_seconds,
                    now_epoch_seconds=now_epoch_seconds,
                )
            )
        payload = result.to_json_dict()
    except Exception as e:
        return _handle_error(
            "Error running scheduler lifecycle action",
            e,
            category="scheduler_lifecycle_failed",
        )

    _print_json(payload)
    return 0


def cmd_scheduler_project(args: list[str]) -> int:
    """Refresh scheduler-derived trajectory projection without running providers."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_PROJECT_USAGE + "\n\n"
            "This writes only the scheduler-derived trajectory projection artifact. "
            "It does not run providers or mutate Local Work Trajectory.",
        )
        return 0

    snapshot_path = ""
    event_log_path = ""
    merge_gate_event_log_path = ""
    output_path = ""
    trajectory_id = ""
    title = ""
    guide_context = ""
    source_graph_id = ""
    source_node_id = ""

    i = 0
    while i < len(args):
        arg = args[i]
        if arg in {
            "--snapshot-path",
            "--event-log-path",
            "--merge-gate-event-log-path",
            "--output-path",
            "--trajectory-id",
            "--title",
            "--guide-context",
            "--source-graph-id",
            "--source-node-id",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_PROJECT_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--snapshot-path":
                snapshot_path = value
            elif arg == "--event-log-path":
                event_log_path = value
            elif arg == "--merge-gate-event-log-path":
                merge_gate_event_log_path = value
            elif arg == "--output-path":
                output_path = value
            elif arg == "--trajectory-id":
                trajectory_id = value
            elif arg == "--title":
                title = value
            elif arg == "--guide-context":
                guide_context = value
            elif arg == "--source-graph-id":
                source_graph_id = value
            elif arg == "--source-node-id":
                source_node_id = value
            i += 2
            continue
        print(f"Unknown scheduler project option: {arg}", file=sys.stderr)
        print(_SCHEDULER_PROJECT_USAGE, file=sys.stderr)
        return 1

    if not snapshot_path:
        print(_SCHEDULER_PROJECT_USAGE, file=sys.stderr)
        print("Missing required option(s): --snapshot-path", file=sys.stderr)
        return 1

    root = _find_project_root()
    snapshot = _resolve_project_path(root, snapshot_path)
    scheduler_log = _resolve_project_path(root, event_log_path) if event_log_path else None
    merge_gate_log = (
        _resolve_project_path(root, merge_gate_event_log_path)
        if merge_gate_event_log_path
        else None
    )
    target = _resolve_project_path(root, output_path) if output_path else None

    try:
        from .runtime.orchestration import read_scheduler_state_snapshot
        from tools.progress_graph import (
            LocalWorkTrajectory,
            scheduler_work_trajectory_json_path,
            write_scheduler_work_trajectory_artifact,
        )

        state = read_scheduler_state_snapshot(snapshot)
        written = write_scheduler_work_trajectory_artifact(
            root,
            state,
            scheduler_event_log_path=scheduler_log,
            merge_gate_event_log_path=merge_gate_log,
            output_path=target,
            trajectory_id=trajectory_id or "local-work:scheduler-projection",
            title=title or "Scheduler Local Work Trajectory",
            guide_context=guide_context,
            source_graph_id=source_graph_id,
            source_node_id=source_node_id,
        )
        trajectory = LocalWorkTrajectory.from_json(written.read_text(encoding="utf-8"))
    except Exception as e:
        return _handle_error(
            "Error refreshing scheduler projection",
            e,
            category="scheduler_projection_failed",
        )

    _print_json(
        {
            "ok": True,
            "snapshot_path": str(snapshot),
            "scheduler_event_log_path": "" if scheduler_log is None else str(scheduler_log),
            "merge_gate_event_log_path": "" if merge_gate_log is None else str(merge_gate_log),
            "scheduler_projection_path": str(written),
            "default_scheduler_projection_path": str(scheduler_work_trajectory_json_path(root)),
            "trajectory_id": trajectory.trajectory_id,
            "title": trajectory.title,
            "event_count": len(trajectory.events),
            "lane_count": len(trajectory.lanes),
            "relation_count": len(trajectory.relations),
            "metadata": dict(trajectory.metadata),
            "ran_tasks": False,
            "refreshed_projection": True,
            "authority_split": {
                "scheduler_state_authority": "scheduler_snapshot",
                "scheduler_state_mutated": False,
                "provider_executed": False,
                "scheduler_projection_refreshed": True,
                "local_work_trajectory_mutated": False,
            },
        }
    )
    return 0


def cmd_pack(args: list[str]) -> int:
    """Pack management subcommands: list, install, remove, info."""
    from .pack.pack_manager import install_pack, remove_pack, list_packs, get_pack_info

    if not args or args[0] in ("-h", "--help"):
        print(
            "Usage: doc-based-coding pack <subcommand> [args]\n\n"
            "Subcommands:\n"
            "  list                    List all discovered packs\n"
            "  install <path>          Install pack from local path\n"
            "  remove <name>           Remove installed pack\n"
            "  info <name>             Show pack details\n",
        )
        return 0

    sub = args[0]
    root = _find_project_root()

    if sub == "list":
        try:
            packs = list_packs(root)
        except Exception as e:
            return _handle_error("Error listing packs", e, category="pack_error")
        if not packs:
            print("No packs discovered.")
            return 0
        for p in packs:
            print(f"  {p.name}  v{p.version}  [{p.source}]  {p.kind}  ({p.path})")
        return 0

    if sub == "install":
        if len(args) < 2:
            print("Usage: doc-based-coding pack install <path>", file=sys.stderr)
            return 1
        source = Path(args[1]).resolve()
        try:
            info = install_pack(source, root)
        except (FileNotFoundError, ValueError) as e:
            print(f"Install failed: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            return _handle_error("Error installing pack", e, category="pack_error")
        print(f"Installed pack '{info.name}' v{info.version} → {info.path}")
        return 0

    if sub == "remove":
        if len(args) < 2:
            print("Usage: doc-based-coding pack remove <name>", file=sys.stderr)
            return 1
        name = args[1]
        try:
            removed = remove_pack(name, root)
        except ValueError as e:
            print(f"Remove failed: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            return _handle_error("Error removing pack", e, category="pack_error")
        if removed:
            print(f"Removed pack '{name}'.")
        else:
            print(f"Pack '{name}' not found in .codex/packs/.", file=sys.stderr)
            return 1
        return 0

    if sub == "info":
        if len(args) < 2:
            print("Usage: doc-based-coding pack info <name>", file=sys.stderr)
            return 1
        name = args[1]
        try:
            info = get_pack_info(name, root)
        except Exception as e:
            return _handle_error("Error getting pack info", e, category="pack_error")
        if info is None:
            print(f"Pack '{name}' not found.", file=sys.stderr)
            return 1
        _print_json(info.to_dict())
        return 0

    print(f"Unknown pack subcommand: {sub}", file=sys.stderr)
    return 1


_COMMANDS = {
    "process": cmd_process,
    "info": cmd_info,
    "validate": cmd_validate,
    "check": cmd_check,
    "resources": cmd_resources,
    "readback": cmd_readback,
    "codex": cmd_codex,
    "opencode": cmd_opencode,
    "provider": cmd_provider,
    "qoder": cmd_qoder,
    "worker-binding": cmd_worker_binding,
    "scheduler": cmd_scheduler,
    "doctor": cmd_doctor,
    "generate-instructions": cmd_generate_instructions,
    "pack": cmd_pack,
}


def main() -> int:
    global _DEBUG

    args = sys.argv[1:]

    # Extract global flags
    if "--debug" in args:
        _DEBUG = True
        args = [a for a in args if a != "--debug"]

    if not args or args[0] in ("-h", "--help"):
        print(
            "Usage: doc-based-coding [--debug] <command> [args]\n\n"
            "Commands:\n"
            "  process <text>          Run full governance chain (dry-run)\n"
            "  info                    Show loaded pack info\n"
            "  validate                Check project constraints\n"
            "  check [text]            Constraint/state check only\n"
            "  resources <sub>         Inspect MCP resources (list/read)\n"
            "  readback <sub>          Inspect readback envelopes\n"
            "  codex <sub>             Codex CLI host readiness helpers\n"
            "  opencode <sub>          OpenCode CLI host readiness helpers\n"
            "  provider <sub>          Mixed runtime provider host helpers\n"
            "  qoder <sub>             Qoder host readiness helpers\n"
            "  worker-binding <sub>    Continuous worker binding helpers\n"
            "  scheduler <sub>         Scheduler operator helpers\n"
            "  doctor                  Unified self-check diagnostics\n"
            "  generate-instructions   Generate agent instructions segment\n"
            "  pack <sub>              Pack management (list/install/remove/info)\n\n"
            "Global flags:\n"
            "  --debug                 Show full traceback on errors\n\n"
            "Exit codes:\n"
            "  0  Success, no governance blocks\n"
            "  1  Runtime error (init failure, file error, etc.)\n"
            "  2  Success, but governance constraints block (validate/check)\n",
        )
        return 0

    cmd_name = args[0]
    cmd_func = _COMMANDS.get(cmd_name)
    if cmd_func is None:
        print(f"Unknown command: {cmd_name}", file=sys.stderr)
        print(f"Available: {', '.join(_COMMANDS)}", file=sys.stderr)
        return 1

    return cmd_func(args[1:])


if __name__ == "__main__":
    sys.exit(main())
