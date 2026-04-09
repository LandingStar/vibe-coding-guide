#!/usr/bin/env python3
"""
Validate the doc-loop official instance prototype artifacts and the consistency
between the instance manifest, the example project-local pack, and the
bootstrap overlay pack template.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


REQUIRED_JSON_KEYS = {
    "pack-manifest.json": [
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
    "examples/subagent-contract.worker.json": [
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
    "examples/subagent-report.worker.json": [
        "report_id",
        "contract_id",
        "status",
        "changed_artifacts",
        "verification_results",
        "unresolved_items",
        "assumptions",
        "escalation_recommendation",
    ],
    "examples/handoff.phase-close.json": [
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
    "examples/project-local.pack.json": [
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
    "assets/bootstrap/.codex/packs/project-local.pack.json": [
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
}


INSTANCE_PATH_FIELDS = [
    "always_on",
    "on_demand",
    "prompts",
    "templates",
    "validators",
    "checks",
    "scripts",
]


PROJECT_LOCAL_EXPECTED_SUBSETS = {
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


PROJECT_LOCAL_COMPARE_FIELDS = [
    "kind",
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
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate the doc-loop instance manifest and the consistency of its "
            "JSON schema examples."
        )
    )
    parser.add_argument(
        "--target",
        default=".",
        help="Path to the doc-loop pack root. Defaults to the current working directory.",
    )
    return parser.parse_args()


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def check_json_keys(root: Path, relative_path: str, keys: list[str]) -> bool:
    file_path = root / relative_path
    if not file_path.exists():
        print(f"[FAIL] Missing file: {relative_path}")
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


def check_manifest_paths(
    root: Path,
    payload: dict[str, object],
    manifest_path: str,
) -> bool:
    ok = True
    for field in INSTANCE_PATH_FIELDS:
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


def validate_instance_manifest(root: Path) -> bool:
    relative_path = "pack-manifest.json"
    payload = load_json(root / relative_path)
    if not isinstance(payload, dict):
        print(f"[FAIL] Expected JSON object in {relative_path}")
        return False

    ok = True
    ok = check_field_equals(payload, "kind", "official-instance", relative_path) and ok
    ok = check_list_contains(
        payload,
        "depends_on",
        ["platform-core-defaults"],
        relative_path,
    ) and ok
    ok = check_list_contains(payload, "triggers", ["chat"], relative_path) and ok
    ok = check_manifest_paths(root, payload, relative_path) and ok
    return ok


def validate_project_local_shape(root: Path, relative_path: str) -> bool:
    payload = load_json(root / relative_path)
    if not isinstance(payload, dict):
        print(f"[FAIL] Expected JSON object in {relative_path}")
        return False

    ok = True
    ok = check_field_equals(payload, "kind", "project-local", relative_path) and ok
    for field, required_items in PROJECT_LOCAL_EXPECTED_SUBSETS.items():
        ok = check_list_contains(payload, field, required_items, relative_path) and ok
    return ok


def compare_project_local_example_and_template(root: Path) -> bool:
    example_path = "examples/project-local.pack.json"
    template_path = "assets/bootstrap/.codex/packs/project-local.pack.json"

    example_payload = load_json(root / example_path)
    template_payload = load_json(root / template_path)
    if not isinstance(example_payload, dict) or not isinstance(template_payload, dict):
        print("[FAIL] Expected JSON objects for project-local pack comparison")
        return False

    ok = True
    for field in PROJECT_LOCAL_COMPARE_FIELDS:
        if example_payload.get(field) != template_payload.get(field):
            print(
                f"[FAIL] Field mismatch between {example_path} and {template_path}: "
                f"{field}"
            )
            ok = False
        else:
            print(
                f"[OK] {example_path} and {template_path} match on field: {field}"
            )

    template_name = template_payload.get("name")
    if not isinstance(template_name, str) or "{{PROJECT_NAME}}" not in template_name:
        print(
            f"[FAIL] Expected bootstrap project-local pack name to contain "
            f"'{{{{PROJECT_NAME}}}}', got {template_name!r}"
        )
        ok = False
    else:
        print("[OK] Bootstrap project-local pack keeps the project-name placeholder")

    return ok


def main() -> int:
    args = parse_args()
    root = Path(args.target).resolve()
    passed = True

    for relative_path, keys in REQUIRED_JSON_KEYS.items():
        passed = check_json_keys(root, relative_path, keys) and passed

    passed = validate_instance_manifest(root) and passed
    passed = validate_project_local_shape(root, "examples/project-local.pack.json") and passed
    passed = validate_project_local_shape(
        root,
        "assets/bootstrap/.codex/packs/project-local.pack.json",
    ) and passed
    passed = compare_project_local_example_and_template(root) and passed

    if passed:
        print(f"[OK] Instance pack validation passed for {root}")
        return 0

    print(f"[ERROR] Instance pack validation failed for {root}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
