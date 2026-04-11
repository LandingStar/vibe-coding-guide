#!/usr/bin/env python3
"""
Register project-local handoff skills into .github/skills via symlinks.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys


def discover_skill_names(skill_root: Path) -> list[str]:
    names: list[str] = []
    if not skill_root.exists():
        return names
    for skill_dir in sorted(path for path in skill_root.iterdir() if path.is_dir()):
        if (skill_dir / "SKILL.md").exists():
            names.append(skill_dir.name)
    return names


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Register project-local handoff skills.")
    parser.add_argument(
        "--scope",
        choices=("project", "user"),
        default="project",
        help="Registration scope; defaults to project-level .github/skills",
    )
    parser.add_argument(
        "--copilot-home",
        default=None,
        help="Copilot home directory when --scope=user; defaults to ~/.copilot",
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
        help="Replace an existing conflicting destination symlink",
    )
    return parser.parse_args()


def ensure_symlink(source: Path, destination: Path, *, force: bool) -> str:
    if destination.exists() or destination.is_symlink():
        if destination.is_symlink() and destination.resolve() == source.resolve():
            return "already-registered"
        if not force:
            raise RuntimeError(
                f"destination already exists and does not match source: {destination}"
            )
        if destination.is_dir() and not destination.is_symlink():
            raise RuntimeError(
                f"destination is a real directory and will not be replaced automatically: {destination}"
            )
        destination.unlink()
    destination.symlink_to(source)
    return "registered"


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[3]
    skill_root = repo_root / ".codex/handoff-system/skill"
    skill_names = discover_skill_names(skill_root)
    if not skill_names:
        print(f"[ERROR] No skills found under: {skill_root}", file=sys.stderr)
        return 1
    if args.scope == "project":
        skills_home = repo_root / ".github" / "skills"
    else:
        home_root = Path(
            args.copilot_home or args.legacy_home or (Path.home() / ".copilot")
        ).expanduser().resolve()
        skills_home = home_root / "skills"
    skills_home.mkdir(parents=True, exist_ok=True)

    results: list[tuple[str, str, Path]] = []
    for skill_name in skill_names:
        source = skill_root / skill_name
        if not (source / "SKILL.md").exists():
            print(f"[ERROR] Missing skill source: {source}", file=sys.stderr)
            return 1
        destination = skills_home / skill_name
        try:
            state = ensure_symlink(source, destination, force=args.force)
        except RuntimeError as exc:
            print(f"[ERROR] {exc}", file=sys.stderr)
            return 1
        results.append((skill_name, state, destination))

    for skill_name, state, destination in results:
        print(f"[OK] {skill_name}: {state} -> {destination}")
    if args.scope == "project":
        print("[OK] Registered project-local handoff skills into .github/skills")
    else:
        print("[OK] Registered project-local handoff skills into ~/.copilot/skills")
    return 0


if __name__ == "__main__":
    sys.exit(main())
