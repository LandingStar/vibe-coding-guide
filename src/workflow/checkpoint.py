"""Checkpoint read/write utilities for context persistence.

Checkpoints capture current work state at key moments so that
AI can recover after context compression without relying on
conversation history alone.

File format: Markdown with structured sections.
Location: .codex/checkpoints/latest.md
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .handoff_footprint import (
    HANDOFF_FOOTPRINT_FIELDS,
    load_current_handoff_footprint,
)

# Default checkpoint directory relative to project root
_DEFAULT_DIR = ".codex/checkpoints"
_LATEST = "latest.md"

# Required sections for a valid checkpoint
_REQUIRED_SECTIONS = frozenset({
    "Current Phase",
    "Active Planning Gate",
    "Current Todo",
    "Key Context Files",
})

_EMPTY_PLANNING_GATE_MARKERS = frozenset({"", "(none)", "—", "-"})


def write_checkpoint(
    project_root: str | Path,
    *,
    phase: str,
    planning_gate: str = "",
    todos: list[dict[str, str]] | None = None,
    pending_decision: str = "",
    direction_candidates: list[dict[str, str]] | None = None,
    key_files: list[str] | None = None,
    current_handoff: dict[str, str] | None = None,
) -> Path:
    """Write a checkpoint file to .codex/checkpoints/latest.md.

    Args:
        project_root: Absolute path to the project root.
        phase: Current phase description, e.g. "Phase 21: Checkpoint, Slice A, status: in-progress"
        planning_gate: Path to active planning gate file.
        todos: List of dicts with keys 'title' and 'status' (one of 'done', 'in-progress', 'not-started').
        pending_decision: Description of what user input is being awaited (empty if none).
        direction_candidates: List of dicts with keys 'name', 'description', 'source'.
        key_files: List of file paths that should be re-read on recovery.
        current_handoff: Minimal pointer footprint of the latest canonical handoff.

    Returns:
        Path to the written checkpoint file.
    """
    root = Path(project_root)
    cp_dir = root / _DEFAULT_DIR
    cp_dir.mkdir(parents=True, exist_ok=True)
    cp_path = cp_dir / _LATEST
    current_handoff = current_handoff or load_current_handoff_footprint(root)

    lines: list[str] = []
    ts = datetime.now(timezone.utc).isoformat()
    lines.append(f"# Checkpoint — {ts}\n")

    # Current Phase
    lines.append("## Current Phase\n")
    lines.append(f"{phase}\n")

    # Active Planning Gate
    lines.append("## Active Planning Gate\n")
    lines.append(f"{planning_gate or '(none)'}\n")

    # Current Handoff
    lines.append("## Current Handoff\n")
    if current_handoff:
        for field in HANDOFF_FOOTPRINT_FIELDS:
            lines.append(f"- {field}: {current_handoff.get(field, '')}\n")
    else:
        lines.append("(none)\n")

    # Current Todo
    lines.append("## Current Todo\n")
    if todos:
        for t in todos:
            status = t.get("status", "not-started")
            marker = {"done": "x", "in-progress": "-", "not-started": " "}.get(status, " ")
            lines.append(f"- [{marker}] {t.get('title', '')}\n")
    else:
        lines.append("(no todos)\n")

    # Pending User Decision
    lines.append("## Pending User Decision\n")
    lines.append(f"{pending_decision or '(none)'}\n")

    # Direction Candidates
    lines.append("## Direction Candidates\n")
    if direction_candidates:
        for d in direction_candidates:
            name = d.get("name", "")
            desc = d.get("description", "")
            source = d.get("source", "")
            lines.append(f"- {name}: {desc} — source: {source}\n")
    else:
        lines.append("(none)\n")

    # Key Context Files
    lines.append("## Key Context Files\n")
    if key_files:
        for f in key_files:
            lines.append(f"- {f}\n")
    else:
        lines.append("- design_docs/Project Master Checklist.md\n")
        lines.append("- design_docs/Global Phase Map and Current Position.md\n")
        lines.append("- .codex/handoffs/CURRENT.md\n")

    cp_path.write_text("".join(lines), encoding="utf-8")
    return cp_path


def sync_checkpoint_phase(
    project_root: str | Path,
    *,
    phase: str,
    planning_gate: str = "",
) -> Path:
    """Update the latest checkpoint's phase while preserving other fields.

    If no checkpoint exists yet, create a minimal one with the provided phase.
    This is intended for post-writeback synchronization so that recovery tools
    see the same current phase as Checklist/Phase Map.
    """
    root = Path(project_root)
    cp_path = root / _DEFAULT_DIR / _LATEST

    existing: dict[str, Any] = {
        "todos": [],
        "pending_decision": "",
        "direction_candidates": [],
        "key_files": None,
        "current_handoff": None,
    }
    if cp_path.exists():
        existing = read_checkpoint(cp_path)

    current_handoff = load_current_handoff_footprint(root) or existing.get(
        "current_handoff"
    )

    return write_checkpoint(
        root,
        phase=phase,
        planning_gate=planning_gate,
        todos=existing.get("todos") or None,
        pending_decision=existing.get("pending_decision", ""),
        direction_candidates=existing.get("direction_candidates") or None,
        key_files=existing.get("key_files") or None,
        current_handoff=current_handoff,
    )


def read_checkpoint(path: str | Path) -> dict[str, Any]:
    """Parse a checkpoint file and return structured data.

    Returns a dict with keys:
    - timestamp: str
    - phase: str
    - planning_gate: str
    - todos: list[dict] with 'title' and 'status'
    - pending_decision: str
    - direction_candidates: list[dict] with 'name', 'description', 'source'
    - key_files: list[str]
    - current_handoff: dict[str, str] | None
    """
    text = Path(path).read_text(encoding="utf-8")
    result: dict[str, Any] = {
        "timestamp": "",
        "phase": "",
        "planning_gate": "",
        "todos": [],
        "pending_decision": "",
        "direction_candidates": [],
        "key_files": [],
        "current_handoff": None,
    }

    # Extract timestamp from heading
    for line in text.splitlines():
        if line.startswith("# Checkpoint"):
            parts = line.split("—", 1)
            if len(parts) > 1:
                result["timestamp"] = parts[1].strip()
            break

    # Parse sections
    sections = _parse_sections(text)

    result["phase"] = sections.get("Current Phase", "").strip()
    result["planning_gate"] = sections.get("Active Planning Gate", "").strip()
    if result["planning_gate"] in _EMPTY_PLANNING_GATE_MARKERS:
        result["planning_gate"] = ""

    # Current handoff footprint
    handoff_text = sections.get("Current Handoff", "")
    current_handoff: dict[str, str] = {}
    for line in handoff_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("- "):
            continue
        key, _, value = stripped[2:].partition(":")
        key = key.strip()
        if key in HANDOFF_FOOTPRINT_FIELDS:
            current_handoff[key] = value.strip()
    if current_handoff:
        result["current_handoff"] = current_handoff

    # Parse todos
    todo_text = sections.get("Current Todo", "")
    for line in todo_text.splitlines():
        line = line.strip()
        if line.startswith("- ["):
            marker = line[3] if len(line) > 3 else " "
            status = {"x": "done", "-": "in-progress"}.get(marker, "not-started")
            title = line[6:].strip() if len(line) > 6 else ""
            result["todos"].append({"title": title, "status": status})

    # Pending decision
    pd = sections.get("Pending User Decision", "").strip()
    result["pending_decision"] = "" if pd == "(none)" else pd

    # Direction candidates
    dc_text = sections.get("Direction Candidates", "")
    for line in dc_text.splitlines():
        line = line.strip()
        if line.startswith("- ") and line != "- (none)":
            entry = line[2:]
            # Parse "Name: description — source: ref"
            name, _, rest = entry.partition(":")
            if " — source: " in rest:
                desc, _, source = rest.partition(" — source: ")
            else:
                desc = rest
                source = ""
            result["direction_candidates"].append({
                "name": name.strip(),
                "description": desc.strip(),
                "source": source.strip(),
            })

    # Key files
    kf_text = sections.get("Key Context Files", "")
    for line in kf_text.splitlines():
        line = line.strip()
        if line.startswith("- "):
            result["key_files"].append(line[2:].strip())

    return result


def validate_checkpoint(path: str | Path) -> dict[str, Any]:
    """Validate a checkpoint file.

    Returns a dict with:
    - valid: bool
    - errors: list[str]
    - data: parsed checkpoint dict (if valid)
    """
    p = Path(path)
    errors: list[str] = []

    if not p.exists():
        return {"valid": False, "errors": ["Checkpoint file does not exist."], "data": None}

    try:
        data = read_checkpoint(p)
    except Exception as e:
        return {"valid": False, "errors": [f"Parse error: {e}"], "data": None}

    text = p.read_text(encoding="utf-8")
    sections = _parse_sections(text)

    for sect in _REQUIRED_SECTIONS:
        if sect not in sections:
            errors.append(f"Missing required section: {sect}")

    if not data.get("phase"):
        errors.append("Current Phase is empty.")

    if not data.get("key_files"):
        errors.append("Key Context Files is empty.")

    handoff_text = sections.get("Current Handoff", "").strip()
    if handoff_text and handoff_text != "(none)":
        current_handoff = data.get("current_handoff") or {}
        for field in HANDOFF_FOOTPRINT_FIELDS:
            if not current_handoff.get(field):
                errors.append(f"Current Handoff is missing {field}.")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "data": data if not errors else None,
    }


def _parse_sections(text: str) -> dict[str, str]:
    """Parse markdown text into a dict of section_name -> content."""
    sections: dict[str, str] = {}
    current_section: str | None = None
    current_lines: list[str] = []

    for line in text.splitlines():
        if line.startswith("## "):
            if current_section is not None:
                sections[current_section] = "\n".join(current_lines)
            current_section = line[3:].strip()
            current_lines = []
        elif current_section is not None:
            current_lines.append(line)

    if current_section is not None:
        sections[current_section] = "\n".join(current_lines)

    return sections
