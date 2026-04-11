#!/usr/bin/env python3
"""
Create an isolated sandbox repo for manually rehearsing blocked-case rebuild.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
HANDOFF_SYSTEM_ROOT = SCRIPT_DIR.parent
REHEARSAL_ROOT = HANDOFF_SYSTEM_ROOT / "rehearsals" / "rebuild-blocked-demo"
SOURCE_HANDOFF = REHEARSAL_ROOT / "source" / "blocked-phase-close.md"
REHEARSAL_README = REHEARSAL_ROOT / "README.md"
SHARED_SCRIPTS_DIR = HANDOFF_SYSTEM_ROOT / "scripts"
if str(SHARED_SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SHARED_SCRIPTS_DIR))

from handoff_protocol import load_document, write_document  # noqa: E402


def resolve_skill_script(skill_suffix: str, script_name: str) -> Path:
    matches = sorted(
        HANDOFF_SYSTEM_ROOT.glob(f"skill/*-{skill_suffix}/scripts/{script_name}")
    )
    if not matches:
        raise RuntimeError(
            f"could not locate {skill_suffix} script: {script_name}"
        )
    return matches[0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a sandbox repo for manual rebuild rehearsal."
    )
    parser.add_argument(
        "--output-dir",
        help="Optional explicit sandbox output directory. Must not already exist.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON result")
    return parser.parse_args()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ensure_repo(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, capture_output=True, text=True)
    subprocess.run(["git", "config", "user.name", "Rebuild Rehearsal"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.email", "rebuild-rehearsal@example.com"], cwd=path, check=True)


def create_output_dir(output_dir: str | None) -> Path:
    if output_dir:
        path = Path(output_dir).expanduser().resolve()
        if path.exists():
            raise RuntimeError(f"output directory already exists: {path}")
        path.mkdir(parents=True, exist_ok=False)
        return path
    temp_path = Path(
        tempfile.mkdtemp(prefix="handoff-rebuild-demo-", dir=None)
    ).resolve()
    return temp_path


def create_minimal_doc(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    title = path.stem.replace("-", " ").title()
    path.write_text(f"# {title}\n\nRebuild rehearsal placeholder for `{path}`.\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    try:
        sandbox_root = create_output_dir(args.output_dir)
    except RuntimeError as exc:
        if args.json:
            print(json.dumps({"status": "blocked", "blocking_issues": [str(exc)]}, ensure_ascii=True, indent=2))
        else:
            print(f"[ERROR] {exc}")
        return 1

    ensure_repo(sandbox_root)

    frontmatter, body = load_document(SOURCE_HANDOFF)
    for ref in frontmatter["authoritative_refs"]:
        if ref == "design_docs/does-not-exist.md":
            continue
        create_minimal_doc(sandbox_root / ref)

    canonical_path = sandbox_root / ".codex/handoffs/history" / SOURCE_HANDOFF.name
    canonical_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(SOURCE_HANDOFF, canonical_path)

    current_path = sandbox_root / ".codex/handoffs/CURRENT.md"
    current_frontmatter = {
        "handoff_id": frontmatter["handoff_id"],
        "entry_role": "current-mirror",
        "source_handoff_id": frontmatter["handoff_id"],
        "source_path": canonical_path.relative_to(sandbox_root).as_posix(),
        "source_hash": f"sha256:{sha256_file(canonical_path)}",
        "kind": frontmatter["kind"],
        "status": "active",
        "scope_key": frontmatter["scope_key"],
        "safe_stop_kind": frontmatter["safe_stop_kind"],
        "created_at": frontmatter["created_at"],
        "authoritative_refs": list(frontmatter["authoritative_refs"]),
        "conditional_blocks": list(frontmatter["conditional_blocks"]),
        "other_count": frontmatter["other_count"],
    }
    current_body = "\n".join(
        [
            "# Current Handoff Mirror",
            "",
            "当前入口镜像 rebuild blocked demo 的 active canonical handoff。",
            "",
            f"- Source handoff id: `{frontmatter['handoff_id']}`",
            f"- Source path: `{canonical_path.relative_to(sandbox_root).as_posix()}`",
            "",
            "## Summary",
            "",
            body.split("## Boundary", 1)[0].replace("# Summary", "").strip(),
            "",
            "## Authoritative Sources",
            "",
            *[f"- `{ref}`" for ref in frontmatter["authoritative_refs"]],
            "",
        ]
    )
    write_document(current_path, current_frontmatter, current_body)

    reports_dir = sandbox_root / ".codex/handoffs/reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    (reports_dir / ".gitkeep").write_text("", encoding="utf-8")
    shutil.copy2(REHEARSAL_README, sandbox_root / "REHEARSAL_README.md")

    subprocess.run(["git", "add", "."], cwd=sandbox_root, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Initialize rebuild rehearsal sandbox"],
        cwd=sandbox_root,
        check=True,
        capture_output=True,
        text=True,
    )

    result = {
        "status": "ok",
        "sandbox_path": str(sandbox_root),
        "current_path": str(current_path),
        "source_handoff_path": str(canonical_path),
        "rehearsal_readme": str(sandbox_root / "REHEARSAL_README.md"),
        "suggested_commands": [
            f'"{sys.executable}" {resolve_skill_script("handoff-accept", "intake_handoff.py")} --current --json',
            f'"{sys.executable}" {resolve_skill_script("handoff-rebuild", "rebuild_handoff.py")} --current --json',
        ],
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
    else:
        print(f"[OK] sandbox_path={sandbox_root}")
        print(f"[OK] current_path={current_path}")
        print(f"[OK] source_handoff_path={canonical_path}")
        print(f"[OK] rehearsal_readme={sandbox_root / 'REHEARSAL_README.md'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
