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
    "[--artifact-store-path PATH] [--replace-existing] [--timestamp TIMESTAMP]"
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
            "  admit-exchange-artifact  Admit one exact stored ExchangeArtifact version into scheduler state\n",
        )
        return 0

    sub = args[0]
    if sub != "admit-exchange-artifact":
        print(f"Unknown scheduler subcommand: {sub}", file=sys.stderr)
        print("Usage: doc-based-coding scheduler <admit-exchange-artifact> [args]", file=sys.stderr)
        return 1

    return cmd_scheduler_admit_exchange_artifact(args[1:])


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
    artifact_id = ""
    version = ""
    snapshot_path = ""
    event_log_path = ""
    replace_existing = False
    timestamp = ""

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
            "--snapshot-path",
            "--event-log-path",
            "--timestamp",
        }:
            if i + 1 >= len(args):
                print(_SCHEDULER_ADMIT_USAGE, file=sys.stderr)
                print(f"Missing value for {arg}", file=sys.stderr)
                return 1
            value = args[i + 1]
            if arg == "--artifact-store-path":
                artifact_store_path = value
            elif arg == "--artifact-id":
                artifact_id = value
            elif arg == "--version":
                version = value
            elif arg == "--snapshot-path":
                snapshot_path = value
            elif arg == "--event-log-path":
                event_log_path = value
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
            admit_exchange_artifact_version_to_scheduler,
            default_exchange_artifact_store_path,
        )

        store = (
            _resolve_project_path(root, artifact_store_path)
            if artifact_store_path
            else default_exchange_artifact_store_path(root)
        )
        result = admit_exchange_artifact_version_to_scheduler(
            artifact_store_path=store,
            artifact_id=artifact_id,
            version=version,
            snapshot_path=_resolve_project_path(root, snapshot_path),
            event_log_path=_resolve_project_path(root, event_log_path),
            replace_existing=replace_existing,
            timestamp=timestamp,
        )
    except Exception as e:
        return _handle_error(
            "Error admitting exchange artifact",
            e,
            category="scheduler_admission_failed",
        )

    payload = {"ok": True}
    payload.update(result.to_json_dict())
    _print_json(payload)
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
