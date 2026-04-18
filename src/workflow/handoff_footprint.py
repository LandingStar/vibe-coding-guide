"""Helpers for extracting the current canonical handoff footprint."""

from __future__ import annotations

from pathlib import Path


HANDOFF_FOOTPRINT_FIELDS = (
    "handoff_id",
    "source_path",
    "scope_key",
    "created_at",
)


def load_current_handoff_footprint(
    project_root: str | Path,
) -> dict[str, str] | None:
    """Return the minimal pointer footprint from .codex/handoffs/CURRENT.md."""
    current_path = Path(project_root) / ".codex" / "handoffs" / "CURRENT.md"
    return read_handoff_footprint(current_path)


def read_handoff_footprint(path: str | Path) -> dict[str, str] | None:
    """Parse a handoff file and return its minimal pointer footprint."""
    handoff_path = Path(path)
    if not handoff_path.is_file():
        return None

    try:
        text = handoff_path.read_text(encoding="utf-8")
    except OSError:
        return None

    metadata = _parse_front_matter(text)
    handoff_id = metadata.get("source_handoff_id") or metadata.get("handoff_id", "")
    source_path = metadata.get("source_path", "")
    scope_key = metadata.get("scope_key", "")
    created_at = metadata.get("created_at", "")

    if not all((handoff_id, source_path, scope_key, created_at)):
        return None

    return {
        "handoff_id": handoff_id,
        "source_path": source_path,
        "scope_key": scope_key,
        "created_at": created_at,
    }


def _parse_front_matter(text: str) -> dict[str, str]:
    """Parse the simple YAML-like front matter used by handoff files."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    metadata: dict[str, str] = {}
    for line in lines[1:]:
        stripped = line.strip()
        if stripped == "---":
            break
        if not stripped or stripped.startswith("- "):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            continue
        metadata[key.strip()] = value.strip()
    return metadata