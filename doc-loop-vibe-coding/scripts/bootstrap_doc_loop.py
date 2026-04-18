#!/usr/bin/env python3
"""
Bootstrap a minimal document-driven coding scaffold into a target repository.
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path


PLACEHOLDERS = {
    "{{CURRENT_DATE}}": date.today().isoformat(),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy the doc-loop bootstrap scaffold into a target repository."
    )
    parser.add_argument(
        "--target",
        default=".",
        help="Target repository root. Defaults to the current working directory.",
    )
    parser.add_argument(
        "--project-name",
        default=None,
        help="Project name to inject into template files. Defaults to the target directory name.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing files instead of failing on conflicts.",
    )
    return parser.parse_args()


def render_template(raw_text: str, project_name: str) -> str:
    rendered = raw_text.replace("{{PROJECT_NAME}}", project_name)
    for placeholder, value in PLACEHOLDERS.items():
        rendered = rendered.replace(placeholder, value)
    return rendered


def copy_scaffold(target_root: Path, project_name: str, force: bool) -> int:
    asset_root = Path(__file__).resolve().parent.parent / "assets" / "bootstrap"
    created = 0
    sources = [source for source in sorted(asset_root.rglob("*")) if source.is_file()]
    skipped = []

    if not force:
        for source in sources:
            relative_path = source.relative_to(asset_root)
            destination = target_root / relative_path
            if destination.exists():
                skipped.append(str(relative_path))

        if skipped:
            print("[ERROR] Refusing to overwrite existing files without --force:")
            for item in skipped:
                print(f"  - {item}")
            return 1

    for source in sources:
        relative_path = source.relative_to(asset_root)
        destination = target_root / relative_path

        existed_before = destination.exists()

        destination.parent.mkdir(parents=True, exist_ok=True)
        text = source.read_text(encoding="utf-8")
        destination.write_text(
            render_template(text, project_name),
            encoding="utf-8",
        )
        created += 1
        verb = "updated" if existed_before else "created"
        print(f"[OK] {verb}: {relative_path}")

    print(f"[OK] Bootstrap completed. {created} files copied into {target_root}")
    print()
    print("Next steps:")
    print(f"  1. Run: doc-based-coding validate")
    print(f"     → Should pass with no blocking issues.")
    print(f"  2. Edit: design_docs/stages/planning-gate/initial-project-setup.md")
    print(f"     → Replace with your first real work slice when ready.")
    print(f"  3. Run: doc-based-coding info")
    print(f"     → Verify pack loading and governance status.")
    return 0


def main() -> int:
    args = parse_args()
    target_root = Path(args.target).resolve()
    project_name = args.project_name or target_root.name
    target_root.mkdir(parents=True, exist_ok=True)
    return copy_scaffold(target_root, project_name, args.force)


if __name__ == "__main__":
    raise SystemExit(main())
