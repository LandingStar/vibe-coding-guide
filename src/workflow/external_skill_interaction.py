"""Helpers for the external skill interaction contract and companion drift-check."""

from __future__ import annotations

from pathlib import Path
from typing import Any


DEFAULT_EXTERNAL_SKILL_INTERACTION_CONTRACT: dict[str, Any] = {
    "model_may_initiate_when_rules_allow": True,
    "slash_is_explicit_route_not_only_surface": True,
    "automatic_stop_signal": "blocked",
    "non_blocked_results_may_continue": True,
    "result_payload_may_be_skill_specific": True,
    "authority_transfer_requires_primitives": ["handoff", "escalation"],
    "reference_implementation_family": "project-handoff-*",
    "companion_distribution_rule": "authority-to-shipped-copies-drift-check",
}

REQUIRED_EXTERNAL_SKILL_INTERACTION_MARKERS = [
    "model-initiated entry is allowed when the governing workflow says this skill is the next required step.",
    "explicit slash routing is valid but is not the only invocation surface.",
    "blocked is the only automatic stop signal.",
    "if the result is not blocked, the model may continue to the next directly relevant step.",
    "this skill does not widen authority, write scope, or control ownership on its own.",
]

_AUTHORITY_SOURCE_FILES = [
    "docs/external-skill-interaction.md",
]

_REFERENCE_IMPLEMENTATION_FILES = [
    ".github/skills/project-handoff-generate/SKILL.md",
    ".github/skills/project-handoff-accept/SKILL.md",
    ".github/skills/project-handoff-refresh-current/SKILL.md",
    ".github/skills/project-handoff-rebuild/SKILL.md",
]

_SHIPPED_COPY_FILES = [
    * _REFERENCE_IMPLEMENTATION_FILES,
    "doc-loop-vibe-coding/references/external-skill-interaction.md",
]


def _copy_contract(value: dict[str, Any]) -> dict[str, Any]:
    copied: dict[str, Any] = {}
    for key, item in value.items():
        if isinstance(item, list):
            copied[key] = list(item)
        elif isinstance(item, dict):
            copied[key] = dict(item)
        else:
            copied[key] = item
    return copied


def _merge_contract(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = _copy_contract(base)
    for key, value in override.items():
        if isinstance(value, list):
            merged[key] = list(value)
        elif isinstance(value, dict) and isinstance(merged.get(key), dict):
            nested = dict(merged[key])
            nested.update(value)
            merged[key] = nested
        else:
            merged[key] = value
    return merged


def _existing_relative_paths(project_root: str | Path, paths: list[str]) -> list[str]:
    root = Path(project_root)
    return [path for path in paths if (root / path).exists()]


def build_external_skill_interaction_contract(
    project_root: str | Path,
    merged_rules: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the structured external skill interaction contract."""
    contract_rules = {}
    if isinstance(merged_rules, dict):
        value = merged_rules.get("external_skill_interaction")
        if isinstance(value, dict):
            contract_rules = value

    contract = _merge_contract(DEFAULT_EXTERNAL_SKILL_INTERACTION_CONTRACT, contract_rules)
    reference_files = _existing_relative_paths(project_root, list(_REFERENCE_IMPLEMENTATION_FILES))
    shipped_copies = _existing_relative_paths(project_root, list(_SHIPPED_COPY_FILES))
    authority_sources = _existing_relative_paths(project_root, list(_AUTHORITY_SOURCE_FILES))

    contract["reference_implementation"] = {
        "family": contract.get("reference_implementation_family", "project-handoff-*"),
        "files": reference_files,
    }
    contract["companion_distribution_rule"] = {
        "rule_name": contract.get(
            "companion_distribution_rule", "authority-to-shipped-copies-drift-check"
        ),
        "authority_sources": authority_sources,
        "shipped_copies": shipped_copies,
        "required_markers": list(REQUIRED_EXTERNAL_SKILL_INTERACTION_MARKERS),
    }
    return contract