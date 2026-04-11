#!/usr/bin/env python3
"""
Rebuild a blocked handoff into a new canonical draft and write a failure report.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import sys


SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_SCRIPTS_DIR = SCRIPT_DIR.parents[2] / "scripts"
SKILL_ROOT = SCRIPT_DIR.parents[1]


def resolve_accept_scripts_dir(skill_root: Path) -> Path:
    matches = sorted(
        path.parent
        for path in skill_root.glob("*-handoff-accept/scripts/intake_handoff.py")
    )
    if not matches:
        raise RuntimeError(
            f"could not locate sibling handoff accept script under: {skill_root}"
        )
    return matches[0]


ACCEPT_SCRIPTS_DIR = resolve_accept_scripts_dir(SKILL_ROOT)
for import_dir in (SHARED_SCRIPTS_DIR, ACCEPT_SCRIPTS_DIR):
    if str(import_dir) not in sys.path:
        sys.path.append(str(import_dir))

from handoff_protocol import (  # noqa: E402
    ValidationError,
    extract_section,
    load_document,
    validate_canonical_handoff,
    write_document,
)
from intake_handoff import inspect_current, inspect_handoff  # noqa: E402


DEFAULT_AUTHORITATIVE_REFS = (
    "design_docs/Project Master Checklist.md",
    "design_docs/Global Phase Map and Current Position.md",
)
HISTORY_DIR = Path(".codex/handoffs/history")
REPORTS_DIR = Path(".codex/handoffs/reports")
CURRENT_ENTRY_PATH = Path(".codex/handoffs/CURRENT.md")
ALLOWED_KINDS = {"stage-close", "phase-close"}
INVALID_FAILURE_MARKERS = (
    "structural validation failed",
    "current entry validation failed",
    "current entry does not exist",
    "bootstrap placeholder",
    "entry_role must be current-mirror",
    "mirror is missing source_path",
    "source_path cannot point to current.md itself",
    "handoff file does not exist",
)
REALITY_FAILURE_MARKERS = (
    "missing authoritative ref",
    "handoff status is superseded",
    "source_handoff_id does not match",
    "kind does not match",
    "scope_key does not match",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuild a blocked handoff into a new canonical draft."
    )
    parser.add_argument("--handoff", help="Path to the canonical handoff file")
    parser.add_argument(
        "--current",
        action="store_true",
        help="Rebuild from .codex/handoffs/CURRENT.md",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON result")
    return parser.parse_args()


def classify_failure(blocking_issues: list[str], intake_status: str) -> str:
    if intake_status != "blocked":
        return "not-blocked"
    lowered = "\n".join(blocking_issues).lower()
    if any(marker in lowered for marker in INVALID_FAILURE_MARKERS):
        return "invalid-handoff"
    if any(marker in lowered for marker in REALITY_FAILURE_MARKERS):
        return "reality-mismatch"
    return "blocked-other"


def lightweight_frontmatter(path: Path) -> tuple[dict, str]:
    if not path.exists():
        return {}, ""
    content = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n\n?(.*)$", content, re.DOTALL)
    if not match:
        return {}, content
    frontmatter_text, body = match.groups()
    result: dict[str, object] = {}
    current_list_key: str | None = None
    for raw_line in frontmatter_text.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        if line.startswith("  - ") and current_list_key is not None:
            result.setdefault(current_list_key, [])
            existing = result[current_list_key]
            if isinstance(existing, list):
                existing.append(line[4:])
            continue
        current_list_key = None
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == "":
            result[key] = []
            current_list_key = key
        elif value == "[]":
            result[key] = []
        elif value == "null":
            result[key] = None
        else:
            result[key] = value
    return result, body


def try_load_current_frontmatter(current_path: Path) -> dict:
    try:
        frontmatter, _body = load_document(current_path)
        return frontmatter
    except ValidationError:
        frontmatter, _body = lightweight_frontmatter(current_path)
        return frontmatter


def dedupe_preserve_order(items: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for item in items:
        normalized = item.strip()
        if normalized and normalized not in seen:
            deduped.append(normalized)
            seen.add(normalized)
    return deduped


def try_extract_section(
    body: str,
    heading: str,
    next_heading: str | None = None,
) -> str | None:
    try:
        section = extract_section(body, heading, next_heading).strip()
    except ValidationError:
        return None
    return section or None


def extract_markdown_refs(body: str) -> list[str]:
    authoritative_section = try_extract_section(
        body,
        "## Authoritative Sources",
        "## Session Delta",
    )
    if not authoritative_section:
        return []
    refs: list[str] = []
    for raw_line in authoritative_section.splitlines():
        line = raw_line.strip()
        if not line.startswith("- "):
            continue
        value = line[2:].strip()
        if value.startswith("`") and value.endswith("`") and len(value) >= 2:
            value = value[1:-1].strip()
        refs.append(value)
    return refs


def infer_kind(path: Path, source_frontmatter: dict, current_frontmatter: dict) -> str | None:
    for candidate in (
        source_frontmatter.get("kind"),
        current_frontmatter.get("kind"),
    ):
        if isinstance(candidate, str) and candidate in ALLOWED_KINDS:
            return candidate
    name = path.stem
    if name.endswith("_stage-close") or "_stage-close_" in name:
        return "stage-close"
    if name.endswith("_phase-close") or "_phase-close_" in name:
        return "phase-close"
    return None


def infer_scope_key(path: Path, source_frontmatter: dict, current_frontmatter: dict) -> str | None:
    for candidate in (
        source_frontmatter.get("scope_key"),
        current_frontmatter.get("scope_key"),
    ):
        if isinstance(candidate, str) and re.fullmatch(r"[a-z0-9-]+", candidate):
            return candidate
    match = re.match(r"^\d{4}-\d{2}-\d{2}_\d{4}_(.+)_(stage-close|phase-close)(?:_rebuild)?$", path.stem)
    if match:
        return match.group(1)
    return None


def collect_authoritative_refs(
    *,
    source_frontmatter: dict,
    source_body: str,
    repo_root: Path,
) -> tuple[list[str], list[str]]:
    refs: list[str] = []
    frontmatter_refs = source_frontmatter.get("authoritative_refs")
    if isinstance(frontmatter_refs, list):
        refs.extend(str(item) for item in frontmatter_refs if str(item).strip())
    refs.extend(extract_markdown_refs(source_body))
    refs.extend(DEFAULT_AUTHORITATIVE_REFS)
    deduped = dedupe_preserve_order(refs)

    existing_refs: list[str] = []
    dropped_refs: list[str] = []
    for ref in deduped:
        if (repo_root / ref).exists():
            existing_refs.append(ref)
        else:
            dropped_refs.append(ref)
    return existing_refs, dropped_refs


def build_boundary_section(source_body: str) -> str:
    section = try_extract_section(source_body, "## Boundary", "## Authoritative Sources")
    if section:
        return section
    return (
        "- 完成到哪里：当前重建仅恢复 handoff 的最小可接手结构。\n"
        "- 为什么这是安全停点：重建保留了原 handoff 的边界意图，但继续工作前仍需重读 authoritative refs。\n"
        "- 明确不在本次完成范围内的内容：不在本次重建中自动修复原 handoff。"
    )


def build_next_step_section(source_body: str) -> str:
    section = try_extract_section(source_body, "## Next Step Contract", "## Intake Checklist")
    if section:
        return section
    return (
        "- 下一会话建议只推进：先按 authoritative refs 重新确认当前主线。\n"
        "- 下一会话明确不做：不要把失败 source handoff 继续当作无条件真相。\n"
        "- 为什么当前应在这里停下：当前重建只恢复了可接手草稿，尚未重新激活。"
    )


def build_kind_section(kind: str, source_body: str) -> str:
    if kind == "stage-close":
        why_close = try_extract_section(source_body, "## Why This Stage Can Close", "## Planning-Gate Return")
        planning = try_extract_section(source_body, "## Planning-Gate Return", "## Conditional Blocks")
        why_close = why_close or (
            "- 当前大阶段到这里可以结束的原因：该重建保留了原 stage-close 的边界意图，但需要以 authoritative refs 复核。\n"
            "- 当前不继续把更多内容塞进本阶段的原因：当前重建仅处理接手恢复，不扩展范围。"
        )
        planning = planning or (
            "- 应回到的 planning-gate 位置：以当前 authoritative refs 为准。\n"
            "- 下一阶段候选主线：按当前正式文档重新确认。\n"
            "- 下一阶段明确不做：不要在未复核前直接扩大 scope。"
        )
        return f"## Why This Stage Can Close\n\n{why_close}\n\n## Planning-Gate Return\n\n{planning}\n"

    phase_check = try_extract_section(source_body, "## Phase Completion Check", "## Parent Stage Status")
    parent_status = try_extract_section(source_body, "## Parent Stage Status", "## Conditional Blocks")
    phase_check = phase_check or (
        "- 当前小 phase 的完成定义：以原 handoff 和 authoritative refs 的共同交集为准。\n"
        "- 当前小 phase 是否已满足完成定义：重建保留原边界，但需要由接手方复核。\n"
        "- 当前停点为何不属于半完成状态：重建只恢复接手结构，不额外宣称新完成项。"
    )
    parent_status = parent_status or (
        "- 所属大阶段当前状态：以当前 authoritative refs 和 workspace reality 为准。\n"
        "- 所属大阶段是否接近尾声：重建流程不做额外阶段判断。\n"
        "- 下一步继续哪条窄主线：按当前正式文档重新确认。"
    )
    return f"## Phase Completion Check\n\n{phase_check}\n\n## Parent Stage Status\n\n{parent_status}\n"


def build_conditional_blocks_section(
    source_frontmatter: dict,
    source_body: str,
    source_valid: bool,
) -> tuple[list[str], int, str, str]:
    if source_valid:
        blocks = source_frontmatter.get("conditional_blocks")
        if isinstance(blocks, list):
            conditional_blocks = [str(block) for block in blocks]
        else:
            conditional_blocks = []
        other_count = source_frontmatter.get("other_count")
        if not isinstance(other_count, int):
            other_count = 0
        conditional_section = try_extract_section(source_body, "## Conditional Blocks", "## Other")
        other_section = try_extract_section(source_body, "## Other")
        if conditional_section:
            conditional_body = conditional_section
        else:
            conditional_blocks = []
            conditional_body = "None."
        if other_count > 0 and other_section:
            other_body = other_section
        else:
            other_count = 0
            other_body = "None."
        return conditional_blocks, other_count, conditional_body, other_body

    return [], 0, "None.", "None."


def make_output_path(
    *,
    repo_root: Path,
    directory: Path,
    scope_key: str,
    kind: str,
    suffix: str,
    extension: str,
) -> tuple[Path, str]:
    created = datetime.now().astimezone()
    stamp = created.strftime("%Y-%m-%d_%H%M")
    base_name = f"{stamp}_{scope_key}_{kind}_{suffix}"
    candidate = repo_root / directory / f"{base_name}.{extension}"
    counter = 2
    while candidate.exists():
        candidate = repo_root / directory / f"{base_name}_{counter}.{extension}"
        counter += 1
    return candidate, created.isoformat(timespec="seconds")


def build_rebuilt_body(
    *,
    failure_class: str,
    source_path: Path,
    source_handoff_id: str | None,
    source_body: str,
    authoritative_refs: list[str],
    dropped_refs: list[str],
    kind: str,
    blocking_issues: list[str],
    source_valid: bool,
    conditional_section: str,
    other_section: str,
) -> str:
    boundary_section = build_boundary_section(source_body)
    next_step_section = build_next_step_section(source_body)
    kind_section = build_kind_section(kind, source_body)
    lines = [
        "# Summary",
        "",
        "这份 canonical handoff 由 rebuild 流程在 accept 失败后重建，用于替代原失败 handoff 作为后续恢复起点。",
        f"当前失败分类为 `{failure_class}`。继续工作时应优先重读 authoritative refs，并以当前 workspace reality 为准。",
        "",
        "## Boundary",
        "",
        boundary_section,
        "",
        "## Authoritative Sources",
        "",
    ]
    for ref in authoritative_refs:
        lines.append(f"- `{ref}`")
    lines.extend(
        [
            "",
            "## Session Delta",
            "",
            f"- 本轮新增：重建 canonical handoff，替代失败 source handoff `{source_path}`。",
            "- 本轮修改：未覆盖原失败 handoff；仅新增 failure report 与 replacement draft。",
            "- 本轮形成的新约束或新结论：blocked intake 后应从 authoritative refs 与 workspace reality 重建，而不是凭旧对话记忆修补。",
            "",
            "## Verification Snapshot",
            "",
            "- 自动化：已重新运行 accept intake，并写出 failure report。",
            "- 手测：未新增额外手测；本次仅执行重建。",
            "- 未完成验证：尚未重新 refresh CURRENT，也未重新验收为 active handoff。",
            "- 仍未验证的结论：重建 draft 中保留的边界和下一步约束仍需由接手方按 authoritative refs 复核。",
            "",
            "## Open Items",
            "",
        ]
    )
    if source_handoff_id:
        lines.append(f"- 未决项：若此重建 draft 最终要替代原 handoff，应在后续 refresh 时与 `{source_handoff_id}` 的状态关系再次确认。")
    else:
        lines.append("- 未决项：当前 source handoff_id 未完全可恢复，后续若要激活应再次确认来源关系。")
    if blocking_issues:
        lines.append("- 已知风险：" + "；".join(blocking_issues))
    else:
        lines.append("- 已知风险：原 blocked 原因已消解前，不应直接把本 draft 视为最终 truth。")
    if dropped_refs:
        lines.append(
            "- 不能默认成立的假设：以下原始 refs 已在重建中排除，因为当前 workspace 中不存在："
            + "，".join(f"`{ref}`" for ref in dropped_refs)
        )
    else:
        lines.append("- 不能默认成立的假设：即使 source handoff 结构可恢复，正文边界仍需以当前正式文档为准。")
    lines.extend(
        [
            "",
            "## Next Step Contract",
            "",
            next_step_section,
            "",
            "## Intake Checklist",
            "",
            "- 核对 `authoritative_refs` 是否仍是当前有效入口。",
            "- 核对当前 workspace 现实状态是否与 handoff 一致。",
            "- 核对 `conditional_blocks` 是否与当前任务仍相关。",
            "- 若存在 `Other`，逐条复核其归类理由。",
            "",
            kind_section.rstrip(),
            "",
            "## Conditional Blocks",
            "",
            conditional_section,
            "",
            "## Other",
            "",
            other_section,
            "",
        ]
    )
    return "\n".join(lines)


def build_failure_report(
    *,
    created_at: str,
    source_entry_mode: str,
    source_entry_path: str,
    source_handoff_path: str,
    source_handoff_id: str | None,
    source_kind: str | None,
    source_scope_key: str | None,
    intake_status: str,
    failure_class: str,
    blocking_issues: list[str],
    source_blocking_issues: list[str],
    warnings: list[str],
    kept_authoritative_refs: list[str],
    dropped_authoritative_refs: list[str],
    rebuilt_handoff_path: str | None,
    rebuilt_handoff_id: str | None,
) -> dict:
    return {
        "created_at": created_at,
        "source_entry_mode": source_entry_mode,
        "source_entry_path": source_entry_path,
        "source_handoff_path": source_handoff_path,
        "source_handoff_id": source_handoff_id,
        "source_kind": source_kind,
        "source_scope_key": source_scope_key,
        "intake_status": intake_status,
        "failure_class": failure_class,
        "blocking_issues": blocking_issues,
        "source_blocking_issues": source_blocking_issues,
        "warnings": warnings,
        "kept_authoritative_refs": kept_authoritative_refs,
        "dropped_authoritative_refs": dropped_authoritative_refs,
        "rebuilt_handoff_path": rebuilt_handoff_path,
        "rebuilt_handoff_id": rebuilt_handoff_id,
    }


def inspect_source_target(
    *,
    repo_root: Path,
    use_current: bool,
    handoff_arg: str | None,
) -> dict:
    if use_current:
        return inspect_current(repo_root)
    assert handoff_arg is not None
    handoff_path = Path(handoff_arg)
    if not handoff_path.is_absolute():
        handoff_path = repo_root / handoff_path
    return inspect_handoff(handoff_path.resolve(), repo_root)


def rebuild_handoff(*, repo_root: Path, use_current: bool, handoff_arg: str | None) -> dict:
    current_path = (repo_root / CURRENT_ENTRY_PATH).resolve()
    history_root = (repo_root / HISTORY_DIR).resolve()
    reports_root = (repo_root / REPORTS_DIR).resolve()
    reports_root.mkdir(parents=True, exist_ok=True)

    intake_result = inspect_source_target(
        repo_root=repo_root,
        use_current=use_current,
        handoff_arg=handoff_arg,
    )
    failure_class = classify_failure(
        intake_result.get("blocking_issues", []),
        intake_result.get("status", ""),
    )
    source_path = Path(intake_result["handoff_path"])
    entry_path = Path(intake_result["entry_path"])

    current_frontmatter: dict = {}
    if intake_result.get("entry_mode") == "current" and entry_path.exists():
        current_frontmatter = try_load_current_frontmatter(entry_path)

    source_valid = False
    source_frontmatter: dict = {}
    source_body = ""
    if source_path.exists():
        try:
            source_frontmatter, source_body = validate_canonical_handoff(source_path)
            source_valid = True
        except ValidationError:
            source_frontmatter, source_body = lightweight_frontmatter(source_path)

    kind = infer_kind(source_path, source_frontmatter, current_frontmatter)
    scope_key = infer_scope_key(source_path, source_frontmatter, current_frontmatter)
    source_handoff_id = None
    for candidate in (
        source_frontmatter.get("handoff_id"),
        current_frontmatter.get("source_handoff_id"),
        current_frontmatter.get("handoff_id"),
    ):
        if isinstance(candidate, str) and candidate.strip():
            source_handoff_id = candidate
            break

    authoritative_refs, dropped_refs = collect_authoritative_refs(
        source_frontmatter=source_frontmatter,
        source_body=source_body,
        repo_root=repo_root,
    )

    report_path, created_at = make_output_path(
        repo_root=repo_root,
        directory=REPORTS_DIR,
        scope_key=scope_key or "unknown-scope",
        kind=kind or "unknown-kind",
        suffix="accept-failure-report",
        extension="json",
    )

    rebuilt_path: Path | None = None
    rebuilt_handoff_id: str | None = None
    warnings = list(intake_result.get("warnings", []))
    source_blocking_issues = list(intake_result.get("blocking_issues", []))
    blocking_issues: list[str] = []

    if intake_result.get("status") != "blocked":
        blocking_issues.append("rebuild expects a blocked intake result")

    if not kind or not scope_key:
        blocking_issues.append("could not recover kind and scope_key for rebuild")

    if not authoritative_refs:
        blocking_issues.append("could not recover any existing authoritative refs for rebuild")

    if not blocking_issues:
        conditional_blocks, other_count, conditional_section, other_section = build_conditional_blocks_section(
            source_frontmatter,
            source_body,
            source_valid,
        )
        rebuilt_path, rebuilt_created_at = make_output_path(
            repo_root=repo_root,
            directory=HISTORY_DIR,
            scope_key=scope_key,
            kind=kind,
            suffix="rebuild",
            extension="md",
        )
        rebuilt_handoff_id = rebuilt_path.stem
        safe_stop_kind = (
            str(source_frontmatter.get("safe_stop_kind"))
            if source_frontmatter.get("safe_stop_kind")
            else ("stage-complete" if kind == "stage-close" else "phase-complete")
        )
        rebuilt_frontmatter = {
            "handoff_id": rebuilt_handoff_id,
            "entry_role": "canonical",
            "kind": kind,
            "status": "draft",
            "scope_key": scope_key,
            "safe_stop_kind": safe_stop_kind,
            "created_at": rebuilt_created_at,
            "supersedes": source_handoff_id,
            "authoritative_refs": authoritative_refs,
            "conditional_blocks": conditional_blocks,
            "other_count": other_count,
        }
        rebuilt_body = build_rebuilt_body(
            failure_class=failure_class,
            source_path=source_path,
            source_handoff_id=source_handoff_id,
            source_body=source_body,
            authoritative_refs=authoritative_refs,
            dropped_refs=dropped_refs,
            kind=kind,
            blocking_issues=source_blocking_issues,
            source_valid=source_valid,
            conditional_section=conditional_section,
            other_section=other_section,
        )
        write_document(rebuilt_path, rebuilt_frontmatter, rebuilt_body)
        try:
            validate_canonical_handoff(rebuilt_path)
        except ValidationError as exc:
            blocking_issues.append(f"rebuilt handoff validation failed: {exc}")
            rebuilt_path.unlink(missing_ok=True)
            rebuilt_path = None
            rebuilt_handoff_id = None

    report_payload = build_failure_report(
        created_at=created_at,
        source_entry_mode=intake_result.get("entry_mode", "handoff"),
        source_entry_path=intake_result.get("entry_path", str(current_path)),
        source_handoff_path=intake_result.get("handoff_path", str(current_path)),
        source_handoff_id=source_handoff_id,
        source_kind=kind,
        source_scope_key=scope_key,
        intake_status=intake_result.get("status", "blocked"),
        failure_class=failure_class,
        blocking_issues=blocking_issues,
        source_blocking_issues=source_blocking_issues,
        warnings=warnings,
        kept_authoritative_refs=authoritative_refs,
        dropped_authoritative_refs=dropped_refs,
        rebuilt_handoff_path=str(rebuilt_path) if rebuilt_path else None,
        rebuilt_handoff_id=rebuilt_handoff_id,
    )
    report_path.write_text(
        json.dumps(report_payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    return {
        "status": "ok" if rebuilt_path else "blocked",
        "failure_class": failure_class,
        "source_entry_mode": intake_result.get("entry_mode", "handoff"),
        "source_entry_path": intake_result.get("entry_path", str(current_path)),
        "source_handoff_path": intake_result.get("handoff_path", str(current_path)),
        "source_handoff_id": source_handoff_id,
        "report_path": str(report_path),
        "rebuilt_handoff_path": str(rebuilt_path) if rebuilt_path else None,
        "rebuilt_handoff_id": rebuilt_handoff_id,
        "warnings": warnings,
        "source_blocking_issues": source_blocking_issues,
        "blocking_issues": blocking_issues,
    }


def print_human(result: dict) -> None:
    prefix = "[OK]" if result["status"] == "ok" else "[ERROR]"
    print(f"{prefix} rebuild_status={result['status']}")
    print(f"{prefix} failure_class={result['failure_class']}")
    print(f"{prefix} report_path={result['report_path']}")
    if result.get("rebuilt_handoff_path"):
        print(f"{prefix} rebuilt_handoff_path={result['rebuilt_handoff_path']}")
    if result.get("rebuilt_handoff_id"):
        print(f"{prefix} rebuilt_handoff_id={result['rebuilt_handoff_id']}")
    for warning in result.get("warnings", []):
        print(f"[WARN] {warning}")
    for issue in result.get("blocking_issues", []):
        print(f"[ERROR] {issue}")


def main() -> int:
    args = parse_args()
    if args.handoff and args.current:
        result = {
            "status": "blocked",
            "failure_class": "invalid-handoff",
            "source_entry_mode": "invalid",
            "source_entry_path": "",
            "source_handoff_path": "",
            "source_handoff_id": None,
            "report_path": None,
            "rebuilt_handoff_path": None,
            "rebuilt_handoff_id": None,
            "warnings": [],
            "blocking_issues": ["use either --handoff or --current, not both"],
        }
    else:
        repo_root = Path.cwd()
        result = rebuild_handoff(
            repo_root=repo_root,
            use_current=args.current or not args.handoff,
            handoff_arg=args.handoff,
        )
    if args.json:
        print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
    else:
        print_human(result)
    return 0 if result["status"] == "ok" else 1


if __name__ == "__main__":
    sys.exit(main())
