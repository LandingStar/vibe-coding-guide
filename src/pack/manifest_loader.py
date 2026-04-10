"""Pack manifest loader — parse pack-manifest.json into PackManifest dataclass."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class PackManifest:
    """Represents a parsed pack manifest."""

    name: str
    version: str
    kind: str  # "platform-default" | "official-instance" | "project-local"
    scope: str = ""

    # Capability declarations
    provides: list[str] = field(default_factory=list)
    document_types: list[str] = field(default_factory=list)
    intents: list[str] = field(default_factory=list)
    gates: list[str] = field(default_factory=list)

    # Context loading
    always_on: list[str] = field(default_factory=list)
    on_demand: list[str] = field(default_factory=list)

    # Dependencies & overrides
    depends_on: list[str] = field(default_factory=list)
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
        ValueError: if required fields missing or data is not a dict.
    """
    if not isinstance(data, dict):
        raise ValueError("Manifest data must be a dict")
    missing = _REQUIRED_FIELDS - set(data.keys())
    if missing:
        raise ValueError(f"Missing required fields: {sorted(missing)}")

    return PackManifest(
        name=str(data["name"]),
        version=str(data["version"]),
        kind=str(data["kind"]),
        scope=str(data.get("scope", "")),
        provides=_as_str_list(data.get("provides", [])),
        document_types=_as_str_list(data.get("document_types", [])),
        intents=_as_str_list(data.get("intents", [])),
        gates=_as_str_list(data.get("gates", [])),
        always_on=_as_str_list(data.get("always_on", [])),
        on_demand=_as_str_list(data.get("on_demand", [])),
        depends_on=_as_str_list(data.get("depends_on", [])),
        overrides=_as_str_list(data.get("overrides", [])),
        prompts=_as_str_list(data.get("prompts", [])),
        templates=_as_str_list(data.get("templates", [])),
        validators=_as_str_list(data.get("validators", [])),
        checks=_as_str_list(data.get("checks", [])),
        scripts=_as_str_list(data.get("scripts", [])),
        triggers=_as_str_list(data.get("triggers", [])),
        rules=data.get("rules", {}),
    )


def _as_str_list(value: Any) -> list[str]:
    """Coerce a value to a list of strings."""
    if isinstance(value, list):
        return [str(v) for v in value]
    return []
