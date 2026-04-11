#!/usr/bin/env python3
"""
Promote a canonical handoff to active and refresh CURRENT.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_SCRIPTS_DIR = SCRIPT_DIR.parents[2] / "scripts"
if str(SHARED_SCRIPTS_DIR) not in sys.path:
    sys.path.append(str(SHARED_SCRIPTS_DIR))

from handoff_protocol import (  # noqa: E402
    ValidationError,
    extract_section,
    load_document,
    validate_canonical_handoff,
    write_document,
)


HISTORY_DIR = Path(".codex/handoffs/history")
CURRENT_PATH = Path(".codex/handoffs/CURRENT.md")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_result(
    *,
    status: str,
    handoff_path: Path,
    current_path: Path,
    selection_mode: str,
    handoff_id: str | None = None,
    superseded_handoff_id: str | None = None,
    superseded_path: Path | None = None,
    warnings: list[str] | None = None,
    blocking_issues: list[str] | None = None,
) -> dict:
    return {
        "status": status,
        "handoff_path": str(handoff_path),
        "current_path": str(current_path),
        "selection_mode": selection_mode,
        "handoff_id": handoff_id,
        "superseded_handoff_id": superseded_handoff_id,
        "superseded_path": str(superseded_path) if superseded_path else None,
        "warnings": warnings or [],
        "blocking_issues": blocking_issues or [],
    }


def draft_sort_key(path: Path, frontmatter: dict) -> tuple[str, str]:
    created_at = frontmatter.get("created_at")
    if not isinstance(created_at, str) or not created_at.strip():
        match = re.match(r"^(\d{4}-\d{2}-\d{2}_\d{4})_", path.name)
        created_at = match.group(1) if match else path.name
    return (created_at, path.name)


def resolve_latest_draft(history_root: Path) -> tuple[Path | None, list[str]]:
    candidates: list[tuple[tuple[str, str], Path]] = []
    warnings: list[str] = []
    for path in sorted(history_root.glob("*.md")):
        try:
            frontmatter, _body = load_document(path.resolve())
        except ValidationError:
            continue
        if (
            frontmatter.get("entry_role") == "canonical"
            and frontmatter.get("status") == "draft"
        ):
            candidates.append((draft_sort_key(path, frontmatter), path.resolve()))

    if not candidates:
        return None, warnings

    candidates.sort(key=lambda item: item[0])
    selected_path = candidates[-1][1]
    if len(candidates) > 1:
        warnings.append(
            f"auto-selected the latest draft from {len(candidates)} draft candidates: {selected_path}"
        )
    return selected_path, warnings


def find_active_canonical_handoffs(
    history_root: Path,
    target_path: Path,
) -> list[tuple[Path, dict, str]]:
    active_entries: list[tuple[Path, dict, str]] = []
    for path in sorted(history_root.glob("*.md")):
        resolved = path.resolve()
        if resolved == target_path.resolve():
            continue
        try:
            frontmatter, body = load_document(resolved)
        except ValidationError:
            continue
        if (
            frontmatter.get("entry_role") == "canonical"
            and frontmatter.get("status") == "active"
        ):
            active_entries.append((resolved, frontmatter, body))
    return active_entries


def build_current_body(
    canonical_path: Path,
    frontmatter: dict,
    body: str,
    repo_root: Path,
) -> str:
    summary = extract_section(body, "# Summary", "## Boundary").strip()
    relative_source = canonical_path.relative_to(repo_root)
    lines = [
        "# Current Handoff Mirror",
        "",
        "当前入口镜像当前 active canonical handoff。继续工作前，应回到 canonical handoff 与其 authoritative refs。",
        "",
        f"- Source handoff id: `{frontmatter['handoff_id']}`",
        f"- Source path: `{relative_source.as_posix()}`",
        "",
        "## Summary",
        "",
        summary,
        "",
        "## Authoritative Sources",
        "",
    ]
    for ref in frontmatter["authoritative_refs"]:
        lines.append(f"- `{ref}`")
    lines.append("")
    return "\n".join(lines)


def build_current_frontmatter(
    canonical_path: Path,
    frontmatter: dict,
    repo_root: Path,
) -> dict:
    source_path = canonical_path.relative_to(repo_root).as_posix()
    return {
        "handoff_id": frontmatter["handoff_id"],
        "entry_role": "current-mirror",
        "source_handoff_id": frontmatter["handoff_id"],
        "source_path": source_path,
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


def rotate_current(handoff_path: Path, repo_root: Path) -> dict:
    current_path = (repo_root / CURRENT_PATH).resolve()
    history_root = (repo_root / HISTORY_DIR).resolve()
    handoff_path = handoff_path.resolve()

    if not handoff_path.exists():
        return build_result(
            status="blocked",
            handoff_path=handoff_path,
            current_path=current_path,
            selection_mode="explicit-handoff",
            blocking_issues=[f"handoff file does not exist: {handoff_path}"],
        )

    try:
        handoff_path.relative_to(history_root)
    except ValueError:
        return build_result(
            status="blocked",
            handoff_path=handoff_path,
            current_path=current_path,
            selection_mode="explicit-handoff",
            blocking_issues=[
                "handoff path must live under .codex/handoffs/history/"
            ],
        )

    try:
        frontmatter, body = validate_canonical_handoff(handoff_path)
    except ValidationError as exc:
        return build_result(
            status="blocked",
            handoff_path=handoff_path,
            current_path=current_path,
            selection_mode="explicit-handoff",
            blocking_issues=[f"structural validation failed: {exc}"],
        )

    if frontmatter["status"] == "superseded":
        return build_result(
            status="blocked",
            handoff_path=handoff_path,
            current_path=current_path,
            selection_mode="explicit-handoff",
            handoff_id=frontmatter["handoff_id"],
            blocking_issues=["cannot rotate a superseded canonical handoff"],
        )

    active_entries = find_active_canonical_handoffs(history_root, handoff_path)
    if len(active_entries) > 1:
        return build_result(
            status="blocked",
            handoff_path=handoff_path,
            current_path=current_path,
            selection_mode="explicit-handoff",
            handoff_id=frontmatter["handoff_id"],
            blocking_issues=["multiple active canonical handoffs already exist"],
        )

    old_active_path: Path | None = None
    old_active_frontmatter: dict | None = None
    old_active_body: str | None = None
    if active_entries:
        old_active_path, old_active_frontmatter, old_active_body = active_entries[0]
        old_handoff_id = old_active_frontmatter["handoff_id"]
        target_supersedes = frontmatter.get("supersedes")
        if target_supersedes in (None, "", "null"):
            frontmatter["supersedes"] = old_handoff_id
        elif target_supersedes != old_handoff_id:
            return build_result(
                status="blocked",
                handoff_path=handoff_path,
                current_path=current_path,
                selection_mode="explicit-handoff",
                handoff_id=frontmatter["handoff_id"],
                superseded_handoff_id=old_handoff_id,
                superseded_path=old_active_path,
                blocking_issues=[
                    "target handoff supersedes does not match the current active canonical handoff"
                ],
            )

    if old_active_path and old_active_frontmatter and old_active_body:
        updated_old_frontmatter = dict(old_active_frontmatter)
        updated_old_frontmatter["status"] = "superseded"
        write_document(old_active_path, updated_old_frontmatter, old_active_body)

    updated_frontmatter = dict(frontmatter)
    updated_frontmatter["status"] = "active"
    write_document(handoff_path, updated_frontmatter, body)

    refreshed_frontmatter, refreshed_body = validate_canonical_handoff(handoff_path)
    current_frontmatter = build_current_frontmatter(
        handoff_path,
        refreshed_frontmatter,
        repo_root,
    )
    current_body = build_current_body(
        handoff_path,
        refreshed_frontmatter,
        refreshed_body,
        repo_root,
    )
    current_path.parent.mkdir(parents=True, exist_ok=True)
    write_document(current_path, current_frontmatter, current_body)

    return build_result(
        status="ok",
        handoff_path=handoff_path,
        current_path=current_path,
        selection_mode="explicit-handoff",
        handoff_id=refreshed_frontmatter["handoff_id"],
        superseded_handoff_id=(
            old_active_frontmatter["handoff_id"] if old_active_frontmatter else None
        ),
        superseded_path=old_active_path,
    )


def print_human(result: dict) -> None:
    prefix = "[OK]" if result["status"] == "ok" else "[ERROR]"
    print(f"{prefix} rotation_status={result['status']}")
    print(f"{prefix} selection_mode={result['selection_mode']}")
    print(f"{prefix} handoff_path={result['handoff_path']}")
    print(f"{prefix} current_path={result['current_path']}")
    if result.get("handoff_id"):
        print(f"{prefix} handoff_id={result['handoff_id']}")
    if result.get("superseded_handoff_id"):
        print(f"{prefix} superseded_handoff_id={result['superseded_handoff_id']}")
    for warning in result.get("warnings", []):
        print(f"[WARN] {warning}")
    for issue in result.get("blocking_issues", []):
        print(f"[ERROR] {issue}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Promote a canonical handoff and refresh CURRENT.md."
    )
    parser.add_argument(
        "--handoff",
        help="Path to the canonical handoff file",
    )
    parser.add_argument(
        "--latest-draft",
        action="store_true",
        help="Auto-select the latest canonical draft under .codex/handoffs/history/",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON result")
    args = parser.parse_args()

    repo_root = Path.cwd()
    current_path = (repo_root / CURRENT_PATH).resolve()
    history_root = (repo_root / HISTORY_DIR).resolve()
    if args.handoff and args.latest_draft:
        result = build_result(
            status="blocked",
            handoff_path=current_path,
            current_path=current_path,
            selection_mode="invalid",
            blocking_issues=["use either --handoff or --latest-draft, not both"],
        )
    elif args.handoff:
        handoff_path = Path(args.handoff)
        if not handoff_path.is_absolute():
            handoff_path = repo_root / handoff_path
        result = rotate_current(handoff_path, repo_root)
    else:
        selected_path, warnings = resolve_latest_draft(history_root)
        if selected_path is None:
            result = build_result(
                status="blocked",
                handoff_path=current_path,
                current_path=current_path,
                selection_mode="latest-draft",
                blocking_issues=["no draft canonical handoff is available under .codex/handoffs/history/"],
            )
        else:
            result = rotate_current(selected_path, repo_root)
            result["selection_mode"] = "latest-draft"
            if warnings:
                result.setdefault("warnings", [])
                result["warnings"].extend(warnings)
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
    else:
        print_human(result)
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
