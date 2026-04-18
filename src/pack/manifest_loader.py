"""Pack manifest loader — parse pack-manifest.json into PackManifest dataclass."""

from __future__ import annotations

import enum
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Current supported manifest schema version
CURRENT_MANIFEST_VERSION = "1.0"


class LoadLevel(enum.IntEnum):
    """How much of a pack to load.

    METADATA  — only name/kind/provides/description (no rules, no files)
    MANIFEST  — full manifest fields (rules, intents, gates, …) but no file content
    FULL      — manifest + always_on file content (current default)
    """

    METADATA = 1
    MANIFEST = 2
    FULL = 3


@dataclass
class PackManifest:
    """Represents a parsed pack manifest."""

    name: str
    version: str
    kind: str  # "platform-default" | "official-instance" | "project-local"
    manifest_version: str = CURRENT_MANIFEST_VERSION
    description: str = ""
    scope: str = ""

    # Capability declarations
    provides: list[str] = field(default_factory=list)
    document_types: list[str] = field(default_factory=list)
    intents: list[str] = field(default_factory=list)
    gates: list[str] = field(default_factory=list)

    # Context loading
    always_on: list[str] = field(default_factory=list)
    on_demand: list[str] = field(default_factory=list)

    # Hierarchy
    parent: str = ""  # parent pack name for tree inheritance
    scope_paths: list[str] = field(default_factory=list)  # path prefixes where this pack applies

    # Dependencies & overrides
    depends_on: list[str] = field(default_factory=list)
    runtime_compatibility: str = ""
    overrides: list[str] = field(default_factory=list)

    # Extension artifacts
    prompts: list[str] = field(default_factory=list)
    templates: list[str] = field(default_factory=list)
    validators: list[str] = field(default_factory=list)
    checks: list[str] = field(default_factory=list)
    scripts: list[str] = field(default_factory=list)
    triggers: list[str] = field(default_factory=list)

    # Rule overrides (optional, pack-specific rule config)
    rules: dict[str, Any] = field(default_factory=dict)


_REQUIRED_FIELDS = {"name", "version", "kind"}


def load(path: str | Path) -> PackManifest:
    """Load a PackManifest from a JSON file path.

    Raises:
        FileNotFoundError: if file does not exist.
        ValueError: if JSON is invalid or required fields missing.
    """
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Manifest not found: {p}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {p}: {exc}") from exc
    return load_dict(data)


def load_dict(data: dict[str, Any]) -> PackManifest:
    """Build a PackManifest from a dict (test-friendly).

    Raises:
        ValueError: if required fields missing, data is not a dict,
            or manifest_version major is unsupported.
    """
    if not isinstance(data, dict):
        raise ValueError("Manifest data must be a dict")
    missing = _REQUIRED_FIELDS - set(data.keys())
    if missing:
        raise ValueError(f"Missing required fields: {sorted(missing)}")

    manifest_version = str(data.get("manifest_version", CURRENT_MANIFEST_VERSION))
    _check_manifest_version(manifest_version)

    return PackManifest(
        name=str(data["name"]),
        version=str(data["version"]),
        kind=str(data["kind"]),
        manifest_version=manifest_version,
        description=str(data.get("description", "")),
        scope=str(data.get("scope", "")),
        provides=_as_str_list(data.get("provides", [])),
        document_types=_as_str_list(data.get("document_types", [])),
        intents=_as_str_list(data.get("intents", [])),
        gates=_as_str_list(data.get("gates", [])),
        always_on=_as_str_list(data.get("always_on", [])),
        on_demand=_as_str_list(data.get("on_demand", [])),
        parent=str(data.get("parent", "")),
        scope_paths=_as_str_list(data.get("scope_paths", [])),
        depends_on=_as_str_list(data.get("depends_on", [])),
        runtime_compatibility=str(data.get("runtime_compatibility", "")),
        overrides=_as_str_list(data.get("overrides", [])),
        prompts=_as_str_list(data.get("prompts", [])),
        templates=_as_str_list(data.get("templates", [])),
        validators=_as_str_list(data.get("validators", [])),
        checks=_as_str_list(data.get("checks", [])),
        scripts=_as_str_list(data.get("scripts", [])),
        triggers=_as_str_list(data.get("triggers", [])),
        rules=data.get("rules", {}),
    )


_DESC_MIN_LENGTH = 20
_DESC_MAX_LENGTH = 500


def validate_description(description: str, *, pack_name: str = "") -> list[str]:
    """Return warnings about description quality.

    Non-empty return means the description is sub-optimal but not invalid.
    """
    warnings: list[str] = []
    if not description:
        warnings.append("description is empty; consider adding a 2-4 sentence summary of what this pack does and when to use it")
        return warnings
    if len(description) < _DESC_MIN_LENGTH:
        warnings.append(
            f"description is too short ({len(description)} chars, minimum {_DESC_MIN_LENGTH}); "
            "include what the pack does and when to use it"
        )
    if len(description) > _DESC_MAX_LENGTH:
        warnings.append(
            f"description is too long ({len(description)} chars, maximum {_DESC_MAX_LENGTH}); "
            "keep it concise — use always_on files for detailed documentation"
        )
    if pack_name and description.strip().lower() == pack_name.strip().lower():
        warnings.append(
            "description is identical to pack name; "
            "add a meaningful summary of what the pack does and when to use it"
        )
    return warnings


_TOC_LINE_THRESHOLD = 100
"""Reference files exceeding this many lines should have a TOC."""

# Patterns that suggest a reference file is trying to include/expand another file.
# Kept intentionally conservative to avoid false positives on plain markdown links.
import re as _re

_NESTED_REF_PATTERNS = [
    _re.compile(r"^\s*\{%\s*include\b", _re.MULTILINE),       # Jinja-style include
    _re.compile(r"^\s*<<\[", _re.MULTILINE),                   # Markua transclusion
    _re.compile(r"^\s*!include\b", _re.MULTILINE),             # mdbook / custom include
]


def validate_pack_organization(
    manifest: PackManifest,
    base_dir: str | Path,
) -> list[str]:
    """Validate the internal file organization of a pack.

    Checks applied:
    - always_on / on_demand files exist under *base_dir*
    - Files over ``_TOC_LINE_THRESHOLD`` lines contain a TOC marker
    - Files do not contain nested-reference patterns (depth > 1)

    Returns a list of human-readable warning strings (empty = clean).
    """
    warnings: list[str] = []
    base = Path(base_dir)

    all_refs = list(manifest.always_on) + list(manifest.on_demand)
    for rel_path in all_refs:
        full = base / rel_path
        if not full.exists():
            warnings.append(f"referenced file not found: {rel_path}")
            continue

        # Only inspect text-like files
        if full.suffix.lower() not in (
            ".md", ".txt", ".json", ".yaml", ".yml", ".toml", ".py", ".sh",
        ):
            continue

        try:
            content = full.read_text(encoding="utf-8")
        except Exception:  # noqa: BLE001
            continue

        lines = content.splitlines()
        line_count = len(lines)

        # TOC check for always_on files only (on_demand are loaded selectively)
        if rel_path in manifest.always_on and line_count > _TOC_LINE_THRESHOLD:
            has_toc = any(
                "目录" in ln or "table of contents" in ln.lower() or "toc" == ln.strip().lower()
                for ln in lines[:30]
            )
            if not has_toc:
                warnings.append(
                    f"{rel_path} has {line_count} lines but no TOC in the first 30 lines; "
                    f"add a table of contents for agent discoverability"
                )

        # Nested reference check
        for pattern in _NESTED_REF_PATTERNS:
            if pattern.search(content):
                warnings.append(
                    f"{rel_path} contains a nested reference pattern "
                    f"({pattern.pattern!r}); keep reference depth ≤ 1"
                )
                break

    return warnings


def _as_str_list(value: Any) -> list[str]:
    """Coerce a value to a list of strings."""
    if isinstance(value, list):
        return [str(v) for v in value]
    return []


def _parse_major_minor(version_str: str) -> tuple[int, int]:
    """Parse a '<major>.<minor>' version string into (major, minor)."""
    parts = version_str.strip().split(".")
    if len(parts) != 2:
        raise ValueError(
            f"Invalid manifest_version format: {version_str!r} (expected '<major>.<minor>')"
        )
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        raise ValueError(
            f"Invalid manifest_version format: {version_str!r} (non-integer components)"
        )


# Virtual dependency names that are always considered resolved.
_ALWAYS_RESOLVED_DEPS = frozenset({"platform-core-defaults"})


def check_dependencies(manifests: list[PackManifest]) -> dict:
    """Check that all depends_on entries resolve to a loaded pack.

    Returns a dict with ``resolved`` and ``unresolved`` lists.
    ``platform-core-defaults`` is treated as always resolved.
    """
    known_names = {m.name for m in manifests} | _ALWAYS_RESOLVED_DEPS
    resolved: list[str] = []
    unresolved: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for m in manifests:
        for dep in m.depends_on:
            key = (m.name, dep)
            if key in seen:
                continue
            seen.add(key)
            if dep in known_names:
                resolved.append(dep)
            else:
                unresolved.append({"pack": m.name, "missing_dep": dep})
                logger.warning(
                    "Pack %r declares dependency %r which is not found among loaded packs",
                    m.name,
                    dep,
                )

    return {"resolved": sorted(set(resolved)), "unresolved": unresolved}


def check_overrides(manifests: list[PackManifest]) -> dict:
    """Check that all overrides entries resolve to a loaded pack.

    Returns a dict with ``declared`` and ``warnings`` lists.
    """
    known_names = {m.name for m in manifests}
    declared: list[dict[str, str]] = []
    warnings: list[str] = []

    for m in manifests:
        for target in m.overrides:
            declared.append({"pack": m.name, "overrides": target})
            if target not in known_names:
                msg = (
                    f"Pack {m.name!r} declares override target {target!r} "
                    f"which is not found among loaded packs"
                )
                warnings.append(msg)
                logger.warning(msg)

    return {"declared": declared, "warnings": warnings}


def _check_manifest_version(version_str: str) -> None:
    """Validate manifest_version against the current supported version.

    Raises ValueError if the major version exceeds the current supported major.
    Logs a warning if the minor version exceeds the current supported minor.
    """
    file_major, file_minor = _parse_major_minor(version_str)
    current_major, current_minor = _parse_major_minor(CURRENT_MANIFEST_VERSION)

    if file_major > current_major:
        raise ValueError(
            f"Unsupported manifest_version {version_str!r}: "
            f"this loader supports up to major version {current_major}"
        )

    if file_major == current_major and file_minor > current_minor:
        logger.warning(
            "manifest_version %s is newer than the current supported %s; "
            "unknown fields may be ignored",
            version_str,
            CURRENT_MANIFEST_VERSION,
        )
