#!/usr/bin/env python3
"""
Prepare a canonical draft handoff skeleton for project-handoff-generate.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import re
import sys


ALLOWED_KINDS = {"stage-close", "phase-close"}
DEFAULT_AUTHORITATIVE_REFS = (
    "design_docs/Project Master Checklist.md",
    "design_docs/Global Phase Map and Current Position.md",
)
BLOCK_FIELDS = {
    "code-change": [
        "Touched Files",
        "Intent of Change",
        "Tests Run",
        "Untested Areas",
    ],
    "cli-change": [
        "Changed Commands",
        "Help Sync Status",
        "Command Reference Sync Status",
        "CLI Regression Status",
    ],
    "transport-recovery-change": [
        "Changed Recovery Surface",
        "Asymmetric Verification Status",
        "Manual Recovery Check",
        "Known Recovery Risks",
    ],
    "authoring-surface-change": [
        "Changed Authoring Surface",
        "Usage Guide Sync Status",
        "Discovery Surface Status",
        "Authoring Boundary Notes",
    ],
    "phase-acceptance-close": [
        "Acceptance Basis",
        "Automation Status",
        "Manual Test Status",
        "Checklist/Board Writeback Status",
    ],
    "dirty-worktree": [
        "Dirty Scope",
        "Relevance to Current Handoff",
        "Do Not Revert Notes",
        "Need-to-Inspect Paths",
    ],
}


def normalize_scope_key(value: str) -> str:
    normalized = value.strip().lower()
    if not re.fullmatch(r"[a-z0-9-]+", normalized):
        raise ValueError(
            "scope_key must use lowercase letters, digits, and hyphens only"
        )
    return normalized


def unique_preserve_order(items: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for item in items:
        if item not in seen:
            deduped.append(item)
            seen.add(item)
    return deduped


def build_block_section(blocks: list[str]) -> str:
    if not blocks:
        return "## Conditional Blocks\n\nNone.\n"

    lines = ["## Conditional Blocks", ""]
    for block in blocks:
        lines.append(f"### {block}")
        lines.append("")
        lines.append("Trigger:")
        lines.append("<replace with why this block is present>")
        lines.append("")
        lines.append("Required fields:")
        lines.append("")
        for field in BLOCK_FIELDS[block]:
            lines.append(f"- {field}:")
        lines.append("")
        lines.append("Verification expectation:")
        lines.append("<replace with how this block was verified or what is still missing>")
        lines.append("")
        lines.append("Refs:")
        lines.append("")
        lines.append("- <replace with relevant paths or docs>")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def build_extra_sections(kind: str) -> str:
    if kind == "stage-close":
        return (
            "## Why This Stage Can Close\n\n"
            "- 当前大阶段到这里可以结束的原因：\n"
            "- 当前不继续把更多内容塞进本阶段的原因：\n\n"
            "## Planning-Gate Return\n\n"
            "- 应回到的 planning-gate 位置：\n"
            "- 下一阶段候选主线：\n"
            "- 下一阶段明确不做：\n"
        )
    return (
        "## Phase Completion Check\n\n"
        "- 当前小 phase 的完成定义：\n"
        "- 当前小 phase 是否已满足完成定义：\n"
        "- 当前停点为何不属于半完成状态：\n\n"
        "## Parent Stage Status\n\n"
        "- 所属大阶段当前状态：\n"
        "- 所属大阶段是否接近尾声：\n"
        "- 下一步继续哪条窄主线：\n"
    )


def build_body(kind: str, blocks: list[str]) -> str:
    parts = [
        "# Summary",
        "",
        "<replace with a concise summary of the completed boundary and why this is a safe stop>",
        "",
        "## Boundary",
        "",
        "- 完成到哪里：",
        "- 为什么这是安全停点：",
        "- 明确不在本次完成范围内的内容：",
        "",
        "## Authoritative Sources",
        "",
        "- <replace with required authoritative ref 1>",
        "- <replace with required authoritative ref 2>",
        "",
        "## Session Delta",
        "",
        "- 本轮新增：",
        "- 本轮修改：",
        "- 本轮形成的新约束或新结论：",
        "",
        "## Verification Snapshot",
        "",
        "- 自动化：",
        "- 手测：",
        "- 未完成验证：",
        "- 仍未验证的结论：",
        "",
        "## Open Items",
        "",
        "- 未决项：",
        "- 已知风险：",
        "- 不能默认成立的假设：",
        "",
        "## Next Step Contract",
        "",
        "- 下一会话建议只推进：",
        "- 下一会话明确不做：",
        "- 为什么当前应在这里停下：",
        "",
        "## Intake Checklist",
        "",
        "- 核对 `authoritative_refs` 是否仍是当前有效入口。",
        "- 核对当前 workspace 现实状态是否与 handoff 一致。",
        "- 核对 `conditional_blocks` 是否与当前任务仍相关。",
        "- 若存在 `Other`，逐条复核其归类理由。",
        "",
        build_extra_sections(kind).rstrip(),
        "",
        build_block_section(blocks).rstrip(),
        "",
        "## Other",
        "",
        "None.",
        "",
    ]
    return "\n".join(parts)


def build_frontmatter(
    *,
    handoff_id: str,
    kind: str,
    scope_key: str,
    created_at: str,
    supersedes: str,
    authoritative_refs: list[str],
    conditional_blocks: list[str],
) -> str:
    lines = [
        "---",
        f"handoff_id: {handoff_id}",
        "entry_role: canonical",
        f"kind: {kind}",
        "status: draft",
        f"scope_key: {scope_key}",
        f"safe_stop_kind: {'stage-complete' if kind == 'stage-close' else 'phase-complete'}",
        f"created_at: {created_at}",
        f"supersedes: {supersedes}",
        "authoritative_refs:",
    ]
    for ref in authoritative_refs:
        lines.append(f"  - {ref}")
    if conditional_blocks:
        lines.append("conditional_blocks:")
        for block in conditional_blocks:
            lines.append(f"  - {block}")
    else:
        lines.append("conditional_blocks: []")
    lines.append("other_count: 0")
    lines.append("---")
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare a draft handoff skeleton.")
    parser.add_argument("--kind", required=True, choices=sorted(ALLOWED_KINDS))
    parser.add_argument("--scope-key", required=True)
    parser.add_argument("--supersedes", default="null")
    parser.add_argument(
        "--authoritative-ref",
        action="append",
        default=[],
        help="Repeatable authoritative ref path",
    )
    parser.add_argument(
        "--conditional-block",
        action="append",
        default=[],
        help="Repeatable conditional block key",
    )
    parser.add_argument(
        "--output-dir",
        default=".codex/handoffs/history",
        help="Directory for canonical handoff drafts",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing file if the timestamped name collides",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        scope_key = normalize_scope_key(args.scope_key)
    except ValueError as exc:
        print(f"[ERROR] {exc}")
        return 1

    blocks = unique_preserve_order(args.conditional_block)
    unknown_blocks = [block for block in blocks if block not in BLOCK_FIELDS]
    if unknown_blocks:
        print(f"[ERROR] Unknown conditional block(s): {', '.join(unknown_blocks)}")
        return 1

    authoritative_refs = unique_preserve_order(args.authoritative_ref or list(DEFAULT_AUTHORITATIVE_REFS))
    created = datetime.now().astimezone()
    created_at = created.isoformat(timespec="seconds")
    stamp = created.strftime("%Y-%m-%d_%H%M")
    handoff_id = f"{stamp}_{scope_key}_{args.kind}"
    file_name = f"{handoff_id}.md"
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / file_name
    if output_path.exists() and not args.force:
        print(f"[ERROR] Output already exists: {output_path}")
        print("       Re-run with --force if you really want to overwrite it.")
        return 1

    frontmatter = build_frontmatter(
        handoff_id=handoff_id,
        kind=args.kind,
        scope_key=scope_key,
        created_at=created_at,
        supersedes=args.supersedes,
        authoritative_refs=authoritative_refs,
        conditional_blocks=blocks,
    )
    body = build_body(args.kind, blocks)
    output_path.write_text(frontmatter + "\n\n" + body, encoding="utf-8")

    print(f"[OK] Created draft handoff skeleton: {output_path}")
    print(f"[OK] handoff_id={handoff_id}")
    print(f"[OK] created_at={created_at}")
    if blocks:
        print(f"[OK] conditional_blocks={','.join(blocks)}")
    else:
        print("[OK] conditional_blocks=<none>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
