"""CLI entry point for the doc-based-coding platform.

Installed entry point:
    doc-based-coding process "input text"      — Run full governance chain
    doc-based-coding info                      — Show loaded pack info
    doc-based-coding validate                  — Check project constraints
    doc-based-coding check [input text]        — Run constraint/state check only
    doc-based-coding generate-instructions     — Generate copilot-instructions segment

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
        pipeline = Pipeline.from_project(root, dry_run=True)
    except Exception as e:
        return _handle_error("Error initializing pipeline", e, category="init_failed")

    result = pipeline.process(input_text)
    _print_json(result.to_dict())
    return 0


def cmd_info(args: list[str]) -> int:
    """Show loaded pack info."""
    root = _find_project_root()

    try:
        pipeline = Pipeline.from_project(root, dry_run=True)
    except Exception as e:
        return _handle_error("Error initializing pipeline", e, category="init_failed")

    _print_json(pipeline.info())
    return 0


def cmd_validate(args: list[str]) -> int:
    """Check project constraints."""
    root = _find_project_root()

    try:
        pipeline = Pipeline.from_project(root, dry_run=True)
    except Exception as e:
        return _handle_error("Error initializing pipeline", e, category="init_failed")

    result = pipeline.check_constraints()
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
        pipeline = Pipeline.from_project(root, dry_run=True)
    except Exception as e:
        return _handle_error("Error initializing pipeline", e, category="init_failed")

    constraints = pipeline.check_constraints()
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
    """Generate copilot-instructions.md segment from loaded packs."""
    root = _find_project_root()

    # Optional output path
    output_path = None
    if args and args[0] == "--output" and len(args) > 1:
        output_path = Path(args[1])

    try:
        from .workflow.instructions_generator import generate_instructions_from_project

        text = generate_instructions_from_project(root)
    except Exception as e:
        return _handle_error("Error generating instructions", e, category="process_failed")

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(text, encoding="utf-8")
        print(f"Instructions written to {output_path}", file=sys.stderr)
    else:
        print(text)
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
            "  generate-instructions   Generate copilot-instructions segment\n"
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
