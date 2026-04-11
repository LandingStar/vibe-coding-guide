#!/usr/bin/env python3
"""
Install the project handoff system into another repository as a portable kit.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
HANDOFF_SYSTEM_ROOT = SCRIPT_DIR.parent
REPO_ROOT = SCRIPT_DIR.parents[2]
PROTOCOL_DOCS = (
    "design_docs/tooling/Session Handoff Standard.md",
    "design_docs/tooling/Session Handoff Conditional Blocks.md",
)
PLACEHOLDER_DOCS = {
    "design_docs/Project Master Checklist.md": (
        "# Project Master Checklist\n\n"
        "本文件由 portable handoff installer 初始化。\n\n"
        "- 在这里记录项目总入口、阶段状态与 handoff 入口。\n"
        "- 首次正式使用 generate handoff 前，应补齐当前阶段口径与读取顺序。\n"
    ),
    "design_docs/Global Phase Map and Current Position.md": (
        "# Global Phase Map and Current Position\n\n"
        "本文件由 portable handoff installer 初始化。\n\n"
        "- 在这里记录当前处于哪个阶段或 planning gate。\n"
        "- 首次正式生成 handoff 前，应补齐当前窄主线与下一步建议。\n"
    ),
}
SKILL_SUFFIXES = (
    "handoff-generate",
    "handoff-accept",
    "handoff-refresh-current",
    "handoff-rebuild",
)
TEXT_EXTENSIONS = {".md", ".py", ".yaml", ".yml", ".txt", ".json"}

if str(SCRIPT_DIR) not in sys.path:
    sys.path.append(str(SCRIPT_DIR))

from handoff_protocol import write_document  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install the project handoff system into another repository."
    )
    parser.add_argument(
        "--target-repo",
        required=True,
        help="Target repository root where the handoff kit should be installed.",
    )
    parser.add_argument(
        "--skill-prefix",
        help="Prefix for slash skill names. Defaults to a sanitized target repo name.",
    )
    parser.add_argument(
        "--register",
        action="store_true",
        help="Run the target-local register script after installation.",
    )
    parser.add_argument(
        "--copilot-home",
        default=None,
        help="Copilot home directory used when --register is set. Defaults to ~/.copilot.",
    )
    parser.add_argument(
        "--codex-home",
        dest="legacy_home",
        default=None,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace existing protocol docs or handoff-system assets when safe to do so.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON result")
    return parser.parse_args()


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return normalized or "project"


def titleize_prefix(prefix: str) -> str:
    return " ".join(part.capitalize() for part in prefix.split("-") if part) or "Project"


def copy_file(src: Path, dst: Path, *, force: bool) -> str:
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        if dst.read_text(encoding="utf-8") == src.read_text(encoding="utf-8"):
            return "already-present"
        if not force:
            raise RuntimeError(f"destination file already exists: {dst}")
    shutil.copy2(src, dst)
    return "copied"


def copy_tree(src: Path, dst: Path, *, force: bool) -> str:
    if dst.exists():
        if not force:
            raise RuntimeError(f"destination directory already exists: {dst}")
        shutil.rmtree(dst)
    shutil.copytree(
        src,
        dst,
        ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"),
    )
    return "copied"


def write_placeholder(path: Path, content: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return "already-present"
    path.write_text(content, encoding="utf-8")
    return "created"


def ensure_gitkeep(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text("", encoding="utf-8")


def ensure_bootstrap_current(path: Path, *, force: bool) -> str:
    if path.exists() and not force:
        raise RuntimeError(f"handoff current entry already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    write_document(
        path,
        {
            "handoff_id": "bootstrap",
            "entry_role": "current-bootstrap",
            "status": "bootstrap-placeholder",
        },
        "# Current Handoff Bootstrap\n\n当前项目尚未生成正式 handoff。\n",
    )
    return "created"


def rename_skill_dirs(skill_root: Path, name_map: dict[str, str]) -> None:
    for old_name, new_name in name_map.items():
        old_path = skill_root / old_name
        if not old_path.exists() or old_name == new_name:
            continue
        old_path.rename(skill_root / new_name)


def replace_text_in_tree(root: Path, replacements: dict[str, str]) -> None:
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in TEXT_EXTENSIONS:
            continue
        content = path.read_text(encoding="utf-8")
        updated = content
        for old, new in replacements.items():
            updated = updated.replace(old, new)
        if updated != content:
            path.write_text(updated, encoding="utf-8")


def build_skill_name_map(prefix: str) -> dict[str, str]:
    return {
        f"project-{suffix}": f"{prefix}-{suffix}"
        for suffix in SKILL_SUFFIXES
    }


def build_display_replacements(prefix: str) -> dict[str, str]:
    display_prefix = titleize_prefix(prefix)
    return {
        "Project Handoff Generate": f"{display_prefix} Handoff Generate",
        "Project Handoff Accept": f"{display_prefix} Handoff Accept",
        "Project Handoff Refresh Current": f"{display_prefix} Handoff Refresh Current",
        "Project Handoff Rebuild": f"{display_prefix} Handoff Rebuild",
    }


def run_registration(target_repo: Path) -> list[str]:
    register_script = target_repo / ".codex/handoff-system/scripts/register_project_skills.py"
    result = subprocess.run(
        [sys.executable, str(register_script), "--scope", "project"],
        cwd=target_repo,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "registration failed")
    return [line for line in result.stdout.splitlines() if line.strip()]


def main() -> int:
    args = parse_args()
    target_repo = Path(args.target_repo).expanduser().resolve()
    target_repo.mkdir(parents=True, exist_ok=True)
    skill_prefix = slugify(args.skill_prefix or target_repo.name)
    skill_name_map = build_skill_name_map(skill_prefix)

    protocol_states: dict[str, str] = {}
    try:
        for relative_path in PROTOCOL_DOCS:
            protocol_states[relative_path] = copy_file(
                REPO_ROOT / relative_path,
                target_repo / relative_path,
                force=args.force,
            )

        handoff_system_state = copy_tree(
            REPO_ROOT / ".codex/handoff-system",
            target_repo / ".codex/handoff-system",
            force=args.force,
        )

        for relative_path, content in PLACEHOLDER_DOCS.items():
            write_placeholder(target_repo / relative_path, content)

        history_dir = target_repo / ".codex/handoffs/history"
        reports_dir = target_repo / ".codex/handoffs/reports"
        history_dir.mkdir(parents=True, exist_ok=True)
        reports_dir.mkdir(parents=True, exist_ok=True)
        ensure_gitkeep(history_dir / ".gitkeep")
        ensure_gitkeep(reports_dir / ".gitkeep")
        current_state = ensure_bootstrap_current(
            target_repo / ".codex/handoffs/CURRENT.md",
            force=args.force,
        )

        target_handoff_system = target_repo / ".codex/handoff-system"
        rename_skill_dirs(target_handoff_system / "skill", skill_name_map)
        replace_text_in_tree(
            target_handoff_system,
            {
                **skill_name_map,
                **build_display_replacements(skill_prefix),
            },
        )

        registration_output: list[str] = []
        if args.register:
            registration_output = run_registration(target_repo)
    except RuntimeError as exc:
        payload = {"status": "blocked", "blocking_issues": [str(exc)]}
        if args.json:
            print(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True))
        else:
            print(f"[ERROR] {exc}")
        return 1

    payload = {
        "status": "ok",
        "target_repo": str(target_repo),
        "skill_prefix": skill_prefix,
        "skill_names": [skill_name_map[f"project-{suffix}"] for suffix in SKILL_SUFFIXES],
        "protocol_docs": protocol_states,
        "handoff_system": handoff_system_state,
        "current_state": current_state,
        "register_output": registration_output,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True))
    else:
        print(f"[OK] target_repo={target_repo}")
        print(f"[OK] skill_prefix={skill_prefix}")
        print(f"[OK] current_state={current_state}")
        for skill_name in payload["skill_names"]:
            print(f"[OK] installed_skill={skill_name}")
        if registration_output:
            for line in registration_output:
                print(line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
