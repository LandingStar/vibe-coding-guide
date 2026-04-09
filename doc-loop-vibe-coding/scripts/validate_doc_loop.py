#!/usr/bin/env python3
"""
Validate that a target repository contains the expected doc-loop scaffold and
that its project-local overlay pack is wired coherently.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_FILES = [
    "AGENTS.md",
    "design_docs/Project Master Checklist.md",
    "design_docs/Global Phase Map and Current Position.md",
    "design_docs/stages/README.md",
    "design_docs/tooling/README.md",
    "design_docs/tooling/Document-Driven Workflow Standard.md",
    "design_docs/tooling/Session Handoff Standard.md",
    "design_docs/tooling/Subagent Delegation Standard.md",
    ".codex/handoffs/CURRENT.md",
    ".codex/packs/project-local.pack.json",
    ".codex/contracts/subagent-contract.template.json",
    ".codex/contracts/subagent-report.template.json",
    ".codex/contracts/handoff.template.json",
    ".codex/prompts/doc-loop/01-planning-gate.md",
    ".codex/prompts/doc-loop/02-execute-by-doc.md",
    ".codex/prompts/doc-loop/03-writeback.md",
    ".codex/prompts/doc-loop/04-subagent-contract.md",
]


REQUIRED_HEADINGS = {
    "design_docs/Project Master Checklist.md": [
        "## 当前快照",
        "## 当前待办与风险",
    ],
    "design_docs/Global Phase Map and Current Position.md": [
        "## 当前阶段判断",
        "## 阅读顺序",
    ],
    "design_docs/tooling/Document-Driven Workflow Standard.md": [
        "## 核心闭环",
        "## 权威文档分层",
    ],
    "design_docs/tooling/Session Handoff Standard.md": [
        "## 适用范围",
        "## 安全停点",
    ],
    "design_docs/tooling/Subagent Delegation Standard.md": [
        "## 责任边界",
        "## 委派合同",
    ],
}


REQUIRED_JSON_KEYS = {
    ".codex/packs/project-local.pack.json": [
        "name",
        "version",
        "kind",
        "scope",
        "provides",
        "document_types",
        "intents",
        "gates",
        "always_on",
        "on_demand",
        "depends_on",
        "overrides",
        "prompts",
        "templates",
        "validators",
        "checks",
        "scripts",
        "triggers",
    ],
    ".codex/contracts/subagent-contract.template.json": [
        "contract_id",
        "task",
        "mode",
        "scope",
        "allowed_artifacts",
        "required_refs",
        "acceptance",
        "verification",
        "out_of_scope",
        "report_schema",
    ],
    ".codex/contracts/subagent-report.template.json": [
        "report_id",
        "contract_id",
        "status",
        "changed_artifacts",
        "verification_results",
        "unresolved_items",
        "assumptions",
        "escalation_recommendation",
    ],
    ".codex/contracts/handoff.template.json": [
        "handoff_id",
        "from_role",
        "to_role",
        "reason",
        "active_scope",
        "authoritative_refs",
        "carried_constraints",
        "open_items",
        "current_gate_state",
        "intake_requirements",
    ],
}


PROJECT_LOCAL_PACK_SUBSETS = {
    "provides": [
        "rules",
        "document_types",
        "prompts",
        "templates",
    ],
    "always_on": [
        "AGENTS.md",
        "design_docs/Project Master Checklist.md",
        "design_docs/Global Phase Map and Current Position.md",
        "design_docs/tooling/Document-Driven Workflow Standard.md",
    ],
    "on_demand": [
        "design_docs/stages/README.md",
        "design_docs/stages/planning-gate/README.md",
        "design_docs/stages/_templates/Planning Gate Candidate Template.md",
        "design_docs/stages/_templates/Phase Slice Template.md",
        "design_docs/stages/_templates/Manual Test Guide Template.md",
        ".codex/contracts/subagent-contract.template.json",
        ".codex/contracts/subagent-report.template.json",
        ".codex/contracts/handoff.template.json",
    ],
    "prompts": [
        ".codex/prompts/doc-loop/01-planning-gate.md",
        ".codex/prompts/doc-loop/02-execute-by-doc.md",
        ".codex/prompts/doc-loop/03-writeback.md",
        ".codex/prompts/doc-loop/04-subagent-contract.md",
    ],
    "depends_on": [
        "doc-loop-vibe-coding",
    ],
    "triggers": [
        "chat",
    ],
}


PATH_LIST_FIELDS = [
    "always_on",
    "on_demand",
    "prompts",
    "templates",
    "validators",
    "checks",
    "scripts",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the required files, headings, and project-local pack "
            "semantics for the doc-loop scaffold."
        )
    )
    parser.add_argument(
        "--target",
        default=".",
        help="Target repository root. Defaults to the current working directory.",
    )
    return parser.parse_args()


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def check_file(root: Path, relative_path: str) -> bool:
    file_path = root / relative_path
    if not file_path.exists():
        print(f"[FAIL] Missing file: {relative_path}")
        return False
    print(f"[OK] Found file: {relative_path}")
    return True


def check_headings(root: Path, relative_path: str, headings: list[str]) -> bool:
    file_path = root / relative_path
    if not file_path.exists():
        return False

    text = file_path.read_text(encoding="utf-8")
    ok = True
    for heading in headings:
        if heading not in text:
            print(f"[FAIL] Missing heading '{heading}' in {relative_path}")
            ok = False
        else:
            print(f"[OK] Heading present in {relative_path}: {heading}")
    return ok


def check_json_keys(root: Path, relative_path: str, keys: list[str]) -> bool:
    file_path = root / relative_path
    if not file_path.exists():
        return False

    try:
        payload = load_json(file_path)
    except json.JSONDecodeError as error:
        print(f"[FAIL] Invalid JSON in {relative_path}: {error}")
        return False

    if not isinstance(payload, dict):
        print(f"[FAIL] Expected JSON object in {relative_path}")
        return False

    ok = True
    for key in keys:
        if key not in payload:
            print(f"[FAIL] Missing key '{key}' in {relative_path}")
            ok = False
        else:
            print(f"[OK] Key present in {relative_path}: {key}")
    return ok


def check_list_contains(
    payload: dict[str, object],
    field: str,
    required_items: list[str],
    label: str,
) -> bool:
    value = payload.get(field)
    if not isinstance(value, list):
        print(f"[FAIL] Expected list field '{field}' in {label}")
        return False

    ok = True
    for item in required_items:
        if item not in value:
            print(f"[FAIL] Missing '{item}' from {field} in {label}")
            ok = False
        else:
            print(f"[OK] {label} {field} contains: {item}")
    return ok


def check_field_equals(
    payload: dict[str, object],
    field: str,
    expected: object,
    label: str,
) -> bool:
    actual = payload.get(field)
    if actual != expected:
        print(f"[FAIL] Expected {label} {field} = {expected!r}, got {actual!r}")
        return False
    print(f"[OK] {label} {field} matches expected value: {expected!r}")
    return True


def check_manifest_paths(
    root: Path,
    payload: dict[str, object],
    manifest_path: str,
) -> bool:
    ok = True
    for field in PATH_LIST_FIELDS:
        value = payload.get(field, [])
        if not isinstance(value, list):
            print(f"[FAIL] Expected list field '{field}' in {manifest_path}")
            ok = False
            continue

        for relative_item in value:
            if not isinstance(relative_item, str):
                print(
                    f"[FAIL] Expected string path in {field} of {manifest_path}, "
                    f"got {type(relative_item).__name__}"
                )
                ok = False
                continue

            resolved = root / relative_item
            if not resolved.exists():
                print(
                    f"[FAIL] Referenced path missing from {field} in "
                    f"{manifest_path}: {relative_item}"
                )
                ok = False
            else:
                print(
                    f"[OK] Referenced path exists for {field} in {manifest_path}: "
                    f"{relative_item}"
                )
    return ok


def check_project_local_pack(root: Path) -> bool:
    relative_path = ".codex/packs/project-local.pack.json"
    file_path = root / relative_path
    if not file_path.exists():
        return False

    try:
        payload = load_json(file_path)
    except json.JSONDecodeError as error:
        print(f"[FAIL] Invalid JSON in {relative_path}: {error}")
        return False

    if not isinstance(payload, dict):
        print(f"[FAIL] Expected JSON object in {relative_path}")
        return False

    ok = True
    ok = check_field_equals(payload, "kind", "project-local", relative_path) and ok

    for field, required_items in PROJECT_LOCAL_PACK_SUBSETS.items():
        ok = check_list_contains(payload, field, required_items, relative_path) and ok

    for field in ("document_types", "intents", "gates"):
        value = payload.get(field)
        if not isinstance(value, list) or not value:
            print(f"[FAIL] Expected non-empty list field '{field}' in {relative_path}")
            ok = False
        else:
            print(f"[OK] {relative_path} has non-empty list field: {field}")

    ok = check_manifest_paths(root, payload, relative_path) and ok
    return ok


def main() -> int:
    args = parse_args()
    target_root = Path(args.target).resolve()
    passed = True

    for relative_path in REQUIRED_FILES:
        passed = check_file(target_root, relative_path) and passed

    for relative_path, headings in REQUIRED_HEADINGS.items():
        passed = check_headings(target_root, relative_path, headings) and passed

    for relative_path, keys in REQUIRED_JSON_KEYS.items():
        passed = check_json_keys(target_root, relative_path, keys) and passed

    passed = check_project_local_pack(target_root) and passed

    if passed:
        print(f"[OK] Validation passed for {target_root}")
        return 0

    print(f"[ERROR] Validation failed for {target_root}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
