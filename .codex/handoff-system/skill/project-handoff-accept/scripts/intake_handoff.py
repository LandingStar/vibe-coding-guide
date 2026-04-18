#!/usr/bin/env python3
"""
Run first-pass intake checks against a canonical handoff file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
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
)


CURRENT_ENTRY_PATH = Path(".codex/handoffs/CURRENT.md")
HISTORY_DIR = Path(".codex/handoffs/history")
CURRENT_BOOTSTRAP_ENTRY_ROLE = "current-bootstrap"
CURRENT_BOOTSTRAP_STATUS = "bootstrap-placeholder"
CURRENT_MIRROR_ENTRY_ROLE = "current-mirror"
STALE_ACTIVE_BODY_PATTERNS = (
    (
        "active handoff body still mentions canonical draft state",
        re.compile(
            r"(当前\s*handoff|this\s*handoff).{0,120}canonical\s+`?draft`?",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
    (
        "active handoff body still says CURRENT.md was not refreshed",
        re.compile(
            r"(当前\s*handoff|this\s*handoff).{0,160}(未刷新|not refreshed).{0,120}CURRENT\.md",
            re.IGNORECASE | re.DOTALL,
        ),
    ),
)


def git_dirty_status(repo_root: Path) -> tuple[bool | None, list[str]]:
    try:
        result = subprocess.run(
            ["git", "status", "--short"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None, []
    if result.returncode != 0:
        return None, []
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    return bool(lines), lines


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def collect_active_canonical_handoffs(repo_root: Path) -> list[tuple[Path, dict]]:
    history_root = (repo_root / HISTORY_DIR).resolve()
    if not history_root.exists():
        return []

    active_entries: list[tuple[Path, dict]] = []
    for path in sorted(history_root.glob("*.md")):
        resolved = path.resolve()
        try:
            frontmatter, _body = load_document(resolved)
        except ValidationError:
            continue
        if (
            frontmatter.get("entry_role") == "canonical"
            and frontmatter.get("status") == "active"
        ):
            active_entries.append((resolved, frontmatter))
    return active_entries


def describe_active_handoffs(entries: list[tuple[Path, dict]], repo_root: Path) -> str:
    parts: list[str] = []
    for path, frontmatter in entries:
        try:
            display_path = path.relative_to(repo_root).as_posix()
        except ValueError:
            display_path = str(path)
        parts.append(f"{frontmatter.get('handoff_id', 'unknown')} ({display_path})")
    return ", ".join(parts)


def normalize_markdown_ref(value: str) -> str:
    normalized = value.strip()
    if " — " in normalized:
        normalized = normalized.split(" — ", 1)[0].strip()
    link_match = re.match(r"^\[[^\]]+\]\(([^)]+)\)$", normalized)
    if link_match:
        normalized = link_match.group(1).strip()
    if normalized.startswith("`") and normalized.endswith("`") and len(normalized) >= 2:
        normalized = normalized[1:-1].strip()
    return normalized


def extract_markdown_bullets(section: str) -> list[str]:
    items: list[str] = []
    for raw_line in section.splitlines():
        line = raw_line.strip()
        if not line.startswith("- "):
            continue
        items.append(normalize_markdown_ref(line[2:]))
    return items


def collect_advisory_warnings(frontmatter: dict, body: str) -> list[str]:
    warnings: list[str] = []

    try:
        authoritative_section = extract_section(
            body,
            "## Authoritative Sources",
            "## Session Delta",
        )
    except ValidationError:
        authoritative_section = ""
    body_refs = extract_markdown_bullets(authoritative_section)
    frontmatter_refs = [str(ref) for ref in frontmatter.get("authoritative_refs", [])]

    missing_in_body = [ref for ref in frontmatter_refs if ref not in body_refs]
    extra_in_body = [ref for ref in body_refs if ref not in frontmatter_refs]
    if missing_in_body:
        warnings.append(
            "Authoritative Sources section is missing refs from frontmatter: "
            + ", ".join(missing_in_body)
        )
    if extra_in_body:
        warnings.append(
            "Authoritative Sources section lists refs not present in frontmatter: "
            + ", ".join(extra_in_body)
        )

    if frontmatter.get("status") == "active":
        for message, pattern in STALE_ACTIVE_BODY_PATTERNS:
            if pattern.search(body):
                warnings.append(message)

    return warnings


def build_result(
    *,
    handoff_path: Path,
    status: str,
    entry_mode: str = "handoff",
    entry_path: Path | None = None,
    frontmatter: dict | None = None,
    warnings: list[str] | None = None,
    blocking_issues: list[str] | None = None,
) -> dict:
    frontmatter = frontmatter or {}
    warnings = warnings or []
    blocking_issues = blocking_issues or []
    return {
        "status": status,
        "entry_mode": entry_mode,
        "entry_path": str(entry_path or handoff_path),
        "handoff_path": str(handoff_path),
        "handoff_id": frontmatter.get("handoff_id"),
        "kind": frontmatter.get("kind"),
        "scope_key": frontmatter.get("scope_key"),
        "handoff_status": frontmatter.get("status"),
        "authoritative_refs": frontmatter.get("authoritative_refs", []),
        "conditional_blocks": frontmatter.get("conditional_blocks", []),
        "warnings": warnings,
        "blocking_issues": blocking_issues,
    }


def inspect_handoff(
    handoff_path: Path,
    repo_root: Path,
    *,
    entry_mode: str = "handoff",
    entry_path: Path | None = None,
) -> dict:
    if not handoff_path.exists():
        return build_result(
            handoff_path=handoff_path,
            status="blocked",
            entry_mode=entry_mode,
            entry_path=entry_path,
            blocking_issues=[f"handoff file does not exist: {handoff_path}"],
        )

    try:
        frontmatter, body = validate_canonical_handoff(handoff_path)
    except ValidationError as exc:
        return build_result(
            handoff_path=handoff_path,
            status="blocked",
            entry_mode=entry_mode,
            entry_path=entry_path,
            blocking_issues=[f"structural validation failed: {exc}"],
        )

    blocking_issues: list[str] = []
    warnings: list[str] = []

    if frontmatter["status"] == "superseded":
        blocking_issues.append("handoff status is superseded")

    missing_refs: list[str] = []
    for ref in frontmatter["authoritative_refs"]:
        ref_path = repo_root / ref
        if not ref_path.exists():
            missing_refs.append(ref)
    if missing_refs:
        blocking_issues.extend(
            [f"missing authoritative ref: {ref}" for ref in missing_refs]
        )

    dirty, dirty_lines = git_dirty_status(repo_root)
    blocks = set(frontmatter["conditional_blocks"])
    if frontmatter["status"] == "draft":
        warnings.append("handoff status is draft")
    if dirty is True and "dirty-worktree" in blocks:
        warnings.append("workspace is dirty and handoff declares dirty-worktree")
    if dirty is True and "dirty-worktree" not in blocks:
        warnings.append("workspace is dirty but handoff does not declare dirty-worktree")
    if dirty is None:
        warnings.append("git dirty-state check was unavailable")
    warnings.extend(collect_advisory_warnings(frontmatter, body))

    result_status = "blocked" if blocking_issues else ("ready-with-warnings" if warnings else "ready")
    result = build_result(
        handoff_path=handoff_path,
        status=result_status,
        entry_mode=entry_mode,
        entry_path=entry_path,
        frontmatter=frontmatter,
        warnings=warnings,
        blocking_issues=blocking_issues,
    )
    if dirty_lines:
        result["dirty_lines"] = dirty_lines
    return result


def inspect_current(repo_root: Path) -> dict:
    current_path = (repo_root / CURRENT_ENTRY_PATH).resolve()
    if not current_path.exists():
        return build_result(
            handoff_path=current_path,
            status="blocked",
            entry_mode="current",
            entry_path=current_path,
            blocking_issues=[f"current entry does not exist: {current_path}"],
        )

    try:
        current_frontmatter, _body = load_document(current_path)
    except ValidationError as exc:
        return build_result(
            handoff_path=current_path,
            status="blocked",
            entry_mode="current",
            entry_path=current_path,
            blocking_issues=[f"current entry validation failed: {exc}"],
        )

    entry_role = current_frontmatter.get("entry_role")
    entry_status = current_frontmatter.get("status")
    if (
        entry_role == CURRENT_BOOTSTRAP_ENTRY_ROLE
        or entry_status == CURRENT_BOOTSTRAP_STATUS
    ):
        return build_result(
            handoff_path=current_path,
            status="blocked",
            entry_mode="current",
            entry_path=current_path,
            blocking_issues=["CURRENT.md is still a bootstrap placeholder"],
        )

    if entry_role != CURRENT_MIRROR_ENTRY_ROLE:
        return build_result(
            handoff_path=current_path,
            status="blocked",
            entry_mode="current",
            entry_path=current_path,
            blocking_issues=[
                "CURRENT.md entry_role must be current-mirror for accept intake"
            ],
        )

    if entry_status != "active":
        return build_result(
            handoff_path=current_path,
            status="blocked",
            entry_mode="current",
            entry_path=current_path,
            blocking_issues=["CURRENT.md mirror status must be active"],
        )

    source_path = current_frontmatter.get("source_path")
    if not isinstance(source_path, str) or not source_path.strip():
        return build_result(
            handoff_path=current_path,
            status="blocked",
            entry_mode="current",
            entry_path=current_path,
            blocking_issues=["CURRENT.md mirror is missing source_path"],
        )

    resolved_source_path = Path(source_path)
    if not resolved_source_path.is_absolute():
        resolved_source_path = (repo_root / resolved_source_path).resolve()
    else:
        resolved_source_path = resolved_source_path.resolve()

    if resolved_source_path == current_path:
        return build_result(
            handoff_path=current_path,
            status="blocked",
            entry_mode="current",
            entry_path=current_path,
            blocking_issues=["CURRENT.md mirror source_path cannot point to CURRENT.md itself"],
        )

    result = inspect_handoff(
        resolved_source_path,
        repo_root,
        entry_mode="current",
        entry_path=current_path,
    )
    result["current_source_path"] = source_path

    current_source_hash = current_frontmatter.get("source_hash")
    if not isinstance(current_source_hash, str) or not current_source_hash.strip():
        result["blocking_issues"].append("CURRENT.md mirror is missing source_hash")
    elif resolved_source_path.exists():
        actual_source_hash = f"sha256:{sha256_file(resolved_source_path)}"
        if current_source_hash != actual_source_hash:
            result["blocking_issues"].append(
                "CURRENT.md source_hash does not match the resolved canonical handoff"
            )

    active_entries = collect_active_canonical_handoffs(repo_root)
    if not active_entries:
        result["blocking_issues"].append(
            "no active canonical handoff exists under .codex/handoffs/history/"
        )
    elif len(active_entries) > 1:
        detail = describe_active_handoffs(active_entries, repo_root)
        result["blocking_issues"].append(
            "multiple active canonical handoffs exist: " + detail
        )
    else:
        active_path, active_frontmatter = active_entries[0]
        if active_path != resolved_source_path:
            result["blocking_issues"].append(
                "CURRENT.md source_path does not point to the unique active canonical handoff: "
                f"{active_frontmatter.get('handoff_id', 'unknown')}"
            )

    expected_handoff_id = current_frontmatter.get("source_handoff_id")
    if (
        expected_handoff_id
        and result.get("handoff_id")
        and expected_handoff_id != result["handoff_id"]
    ):
        result["blocking_issues"].append(
            "CURRENT.md source_handoff_id does not match the resolved canonical handoff"
        )

    for key in ("kind", "scope_key"):
        current_value = current_frontmatter.get(key)
        handoff_value = result.get(key)
        if current_value and handoff_value and current_value != handoff_value:
            result["blocking_issues"].append(
                f"CURRENT.md {key} does not match the resolved canonical handoff"
            )

    if result["blocking_issues"]:
        result["status"] = "blocked"
    return result


def print_human(result: dict) -> None:
    prefix = {
        "ready": "[OK]",
        "ready-with-warnings": "[WARN]",
        "blocked": "[ERROR]",
    }[result["status"]]
    print(f"{prefix} intake_status={result['status']}")
    print(f"{prefix} entry_mode={result['entry_mode']}")
    print(f"{prefix} entry_path={result['entry_path']}")
    if result["entry_path"] != result["handoff_path"]:
        print(f"{prefix} resolved_handoff_path={result['handoff_path']}")
    if result.get("handoff_id"):
        print(f"{prefix} handoff_id={result['handoff_id']}")
    if result.get("kind"):
        print(f"{prefix} kind={result['kind']}")
    if result.get("scope_key"):
        print(f"{prefix} scope_key={result['scope_key']}")
    for warning in result.get("warnings", []):
        print(f"[WARN] {warning}")
    for issue in result.get("blocking_issues", []):
        print(f"[ERROR] {issue}")
    refs = result.get("authoritative_refs", [])
    if refs:
        print("[INFO] authoritative_refs:")
        for ref in refs:
            print(f"[INFO] - {ref}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect a handoff intake entry.")
    target_group = parser.add_mutually_exclusive_group(required=True)
    target_group.add_argument(
        "--handoff",
        help="Path to the canonical handoff file",
    )
    target_group.add_argument(
        "--current",
        action="store_true",
        help="Inspect .codex/handoffs/CURRENT.md and resolve it to the canonical handoff",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON result")
    args = parser.parse_args()

    repo_root = Path.cwd()
    if args.current:
        result = inspect_current(repo_root)
    else:
        handoff_path = Path(args.handoff)
        if not handoff_path.is_absolute():
            handoff_path = repo_root / handoff_path
        result = inspect_handoff(handoff_path.resolve(), repo_root)
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
    else:
        print_human(result)
    return 0 if result["status"] != "blocked" else 1


if __name__ == "__main__":
    sys.exit(main())
