"""CLI entry point for the doc-based-coding platform.

Installed entry point:
    doc-based-coding process "input text"      — Run full governance chain
    doc-based-coding info                      — Show loaded pack info
    doc-based-coding validate                  — Check project constraints
    doc-based-coding check [input text]        — Run constraint/state check only
    doc-based-coding resources <subcommand>    — Inspect MCP resources
    doc-based-coding qoder readiness           — Check Qoder SDK host readiness
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


def cmd_qoder(args: list[str]) -> int:
    """Qoder host-runtime helper subcommands."""
    if not args or args[0] in ("-h", "--help"):
        print(
            "Usage: doc-based-coding qoder <subcommand> [args]\n\n"
            "Subcommands:\n"
            "  readiness [--auth-mode env|qodercli] [--auth-env-var NAME] [--sdk-module NAME]\n"
            "      Check optional qoder-agent-sdk host readiness without printing secrets\n",
        )
        return 0

    sub = args[0]
    if sub != "readiness":
        print(f"Unknown qoder subcommand: {sub}", file=sys.stderr)
        print("Usage: doc-based-coding qoder <readiness> [args]", file=sys.stderr)
        return 1

    auth_mode = "env"
    auth_env_var = ""
    sdk_module_name = ""
    i = 1
    while i < len(args):
        arg = args[i]
        if arg == "--auth-mode":
            if i + 1 >= len(args):
                print("Usage: doc-based-coding qoder readiness [--auth-mode env|qodercli] [--auth-env-var NAME] [--sdk-module NAME]", file=sys.stderr)
                return 1
            auth_mode = args[i + 1]
            i += 2
            continue
        if arg == "--auth-env-var":
            if i + 1 >= len(args):
                print("Usage: doc-based-coding qoder readiness [--auth-mode env|qodercli] [--auth-env-var NAME] [--sdk-module NAME]", file=sys.stderr)
                return 1
            auth_env_var = args[i + 1]
            i += 2
            continue
        if arg == "--sdk-module":
            if i + 1 >= len(args):
                print("Usage: doc-based-coding qoder readiness [--auth-mode env|qodercli] [--auth-env-var NAME] [--sdk-module NAME]", file=sys.stderr)
                return 1
            sdk_module_name = args[i + 1]
            i += 2
            continue
        print(f"Unknown qoder readiness option: {arg}", file=sys.stderr)
        print("Usage: doc-based-coding qoder readiness [--auth-mode env|qodercli] [--auth-env-var NAME] [--sdk-module NAME]", file=sys.stderr)
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


_SCHEDULER_ADMIT_USAGE = (
    "Usage: doc-based-coding scheduler admit-exchange-artifact "
    "--artifact-id ID --version VERSION --snapshot-path PATH --event-log-path PATH "
    "[--artifact-store-path PATH] [--admission-ledger-path PATH] "
    "[--allow-duplicate-admission] [--actor ACTOR] [--replace-existing] "
    "[--timestamp TIMESTAMP]"
)

_SCHEDULER_INSPECT_ADMISSIONS_USAGE = (
    "Usage: doc-based-coding scheduler inspect-admissions "
    "[--admission-ledger-path PATH] [--artifact-id ID] [--version VERSION]"
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
    "[--artifact-store-path PATH] [--artifact-id ID] [--version VERSION] "
    "[--replace-existing] [--created-at TIMESTAMP]"
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
            "  inspect-state            Read scheduler snapshot/event-log summary without mutation\n"
            "  tick                     Run one bounded fake-runtime scheduler tick without projection refresh\n"
            "  daemon-loop              Run a bounded fake-runtime scheduler loop without projection refresh\n"
            "  project                  Refresh scheduler-derived trajectory projection without running providers\n"
            "  seed-dogfood-fixture     Seed one controlled ExchangeArtifact admission candidate\n",
        )
        return 0

    sub = args[0]
    if sub == "admit-exchange-artifact":
        return cmd_scheduler_admit_exchange_artifact(args[1:])
    if sub == "inspect-admissions":
        return cmd_scheduler_inspect_admissions(args[1:])
    if sub == "inspect-state":
        return cmd_scheduler_inspect_state(args[1:])
    if sub == "tick":
        return cmd_scheduler_tick(args[1:])
    if sub == "daemon-loop":
        return cmd_scheduler_daemon_loop(args[1:])
    if sub == "project":
        return cmd_scheduler_project(args[1:])
    if sub == "seed-dogfood-fixture":
        return cmd_scheduler_seed_dogfood_fixture(args[1:])

    print(f"Unknown scheduler subcommand: {sub}", file=sys.stderr)
    print(
        "Usage: doc-based-coding scheduler <admit-exchange-artifact|inspect-admissions|inspect-state|tick|daemon-loop|project|seed-dogfood-fixture> [args]",
        file=sys.stderr,
    )
    return 1


def cmd_scheduler_admit_exchange_artifact(args: list[str]) -> int:
    """Admit one exact stored ExchangeArtifact version into scheduler state."""

    if not args or args[0] in ("-h", "--help"):
        print(
            _SCHEDULER_ADMIT_USAGE + "\n\n"
            "This writes scheduler snapshot/event-log state only. It does not run providers, "
            "refresh scheduler projection, mark exchange artifacts consumed, or mutate Local Work Trajectory.",
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
            "It does not admit tasks, run providers, refresh scheduler projection, write "
            "Host Evidence, or mutate Local Work Trajectory.",
        )
        return 0

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
            i += 2
            continue
        print(f"Unknown scheduler seed-dogfood-fixture option: {arg}", file=sys.stderr)
        print(_SCHEDULER_SEED_DOGFOOD_FIXTURE_USAGE, file=sys.stderr)
        return 1

    root = _find_project_root()
    try:
        from .runtime.orchestration import (
            DEFAULT_SCHEDULER_OPERATOR_DOGFOOD_ARTIFACT_ID,
            DEFAULT_SCHEDULER_OPERATOR_DOGFOOD_VERSION,
            seed_scheduler_operator_dogfood_fixture,
        )

        target_store = (
            _resolve_project_path(root, artifact_store_path)
            if artifact_store_path
            else None
        )
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
