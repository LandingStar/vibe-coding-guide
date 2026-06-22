"""CLI entry point for the doc-based-coding platform.

Installed entry point:
    doc-based-coding process "input text"      — Run full governance chain
    doc-based-coding info                      — Show loaded pack info
    doc-based-coding validate                  — Check project constraints
    doc-based-coding check [input text]        — Run constraint/state check only
    doc-based-coding resources <subcommand>    — Inspect MCP resources
    doc-based-coding qoder readiness           — Check Qoder SDK host readiness
    doc-based-coding qoder smoke               — Run host-owned Qoder smoke helper
    doc-based-coding scheduler <subcommand>    — Scheduler operator helpers
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
        )
        return 0

    sub = args[0]
    if sub == "readiness":
        return cmd_qoder_readiness(args[1:])
    if sub == "smoke":
        return cmd_qoder_smoke(args[1:])

    print(f"Unknown qoder subcommand: {sub}", file=sys.stderr)
    print("Usage: doc-based-coding qoder <readiness|smoke> [args]", file=sys.stderr)
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
            snapshot_path=snapshot_path or ".codex/scheduler/qoder-smoke-state.json",
            event_log_path=event_log_path or ".codex/scheduler/qoder-smoke-events.jsonl",
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
            "  inspect-state            Read scheduler snapshot/event-log summary without mutation\n"
            "  tick                     Run one bounded fake-runtime scheduler tick without projection refresh\n"
            "  daemon-loop              Run a bounded fake-runtime scheduler loop without projection refresh\n"
            "  lifecycle                Read or mutate scheduler daemon lifecycle control state\n"
            "  project                  Refresh scheduler-derived trajectory projection without running providers\n"
            "  seed-dogfood-fixture     Seed one controlled ExchangeArtifact admission candidate\n"
            "  operator-workflow        Run shared explicit operator workflow with opt-in mutation steps\n"
            "  operator-dogfood-closure Seed and run deterministic operator evidence closure\n"
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
    if sub == "supervisor-dogfood-workflow":
        return cmd_scheduler_supervisor_dogfood_workflow(args[1:])
    if sub == "cleanup-receipts":
        return cmd_scheduler_cleanup_receipts(args[1:])
    if sub == "sandbox-receipt-workflow":
        return cmd_scheduler_sandbox_receipt_workflow(args[1:])

    print(f"Unknown scheduler subcommand: {sub}", file=sys.stderr)
    print(
        "Usage: doc-based-coding scheduler <admit-exchange-artifact|inspect-admissions|inspect-binding-refs|inspect-state|tick|daemon-loop|lifecycle|project|seed-dogfood-fixture|operator-workflow|operator-dogfood-closure|supervisor-dogfood-workflow|cleanup-receipts|sandbox-receipt-workflow> [args]",
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
    "qoder": cmd_qoder,
    "scheduler": cmd_scheduler,
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
            "  qoder <sub>             Qoder host readiness helpers\n"
            "  scheduler <sub>         Scheduler operator helpers\n"
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
