"""Write consumer payloads to target documents.

Implements Slice B of the dogfood pipeline workflow integration:
each ConsumerPayload is appended to its designated target document
per the dispatch matrix in dogfood-pipeline-workflow-integration-direction-analysis.md.

Only 4 consumers are auto-written; phase-map and handoff are skip-by-design.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from .models import ConsumerName

_log = logging.getLogger(__name__)

# Consumers that support automatic writeback
_WRITEBACK_CONSUMERS: dict[ConsumerName, str] = {
    ConsumerName.DIRECTION_CANDIDATES: "design_docs/direction-candidates-after-phase-35.md",
    ConsumerName.CHECKLIST: "design_docs/Project Master Checklist.md",
    ConsumerName.CHECKPOINT: ".codex/checkpoints/latest.md",
    # PLANNING_GATE uses dynamic path — resolved at call time
}

_SKIP_CONSUMERS = frozenset({ConsumerName.PHASE_MAP, ConsumerName.HANDOFF})


def _packet_already_written(content: str, packet_id: str) -> bool:
    """Return True if *packet_id* already appears in *content*."""
    return packet_id in content


def _build_feedback_section(payload_fields: dict[str, Any], packet_id: str) -> str:
    """Build a Markdown section from payload fields."""
    lines = [
        f"\n### Dogfood Feedback — {packet_id}\n",
    ]
    for key, value in payload_fields.items():
        if isinstance(value, list):
            lines.append(f"- **{key}**: {', '.join(str(v) for v in value)}")
        else:
            lines.append(f"- **{key}**: {value}")
    lines.append("")
    return "\n".join(lines)


def _append_to_file(path: Path, section: str) -> bool:
    """Append *section* to end of file. Returns True on success."""
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(section)
        return True
    except OSError as exc:
        _log.warning("Failed to write to %s: %s", path, exc)
        return False


def _write_checklist(
    project_root: Path, fields: dict[str, Any], packet_id: str
) -> dict[str, Any]:
    """Append feedback to the Checklist's active todo section."""
    path = project_root / _WRITEBACK_CONSUMERS[ConsumerName.CHECKLIST]
    if not path.exists():
        return {"consumer": "checklist", "status": "skipped", "reason": "file not found"}

    content = path.read_text(encoding="utf-8")
    if _packet_already_written(content, packet_id):
        return {"consumer": "checklist", "status": "skipped", "reason": "already written"}

    judgment = fields.get("judgment", "")
    affected_docs = fields.get("affected_docs", [])
    if isinstance(affected_docs, list):
        affected_docs = ", ".join(str(d) for d in affected_docs)

    entry = f"\n- [ ] Dogfood feedback ({packet_id}): {judgment}"
    if affected_docs:
        entry += f" — affected: {affected_docs}"
    entry += "\n"

    # Insert before "### 研究参考待办" or "### 已完成里程碑", whichever comes first
    for marker in ("### 研究参考待办", "### 已完成里程碑"):
        idx = content.find(marker)
        if idx != -1:
            new_content = content[:idx] + entry + "\n" + content[idx:]
            path.write_text(new_content, encoding="utf-8")
            return {"consumer": "checklist", "status": "written"}

    # Fallback: append to end
    _append_to_file(path, entry)
    return {"consumer": "checklist", "status": "written"}


def _write_checkpoint(
    project_root: Path, fields: dict[str, Any], packet_id: str
) -> dict[str, Any]:
    """Append feedback section to the checkpoint file."""
    path = project_root / _WRITEBACK_CONSUMERS[ConsumerName.CHECKPOINT]
    if not path.exists():
        return {"consumer": "checkpoint", "status": "skipped", "reason": "file not found"}

    content = path.read_text(encoding="utf-8")
    if _packet_already_written(content, packet_id):
        return {"consumer": "checkpoint", "status": "skipped", "reason": "already written"}

    section = _build_feedback_section(fields, packet_id)
    _append_to_file(path, section)
    return {"consumer": "checkpoint", "status": "written"}


def _write_direction_candidates(
    project_root: Path, fields: dict[str, Any], packet_id: str
) -> dict[str, Any]:
    """Append feedback section to the direction candidates file."""
    path = project_root / _WRITEBACK_CONSUMERS[ConsumerName.DIRECTION_CANDIDATES]
    if not path.exists():
        return {"consumer": "direction-candidates", "status": "skipped", "reason": "file not found"}

    content = path.read_text(encoding="utf-8")
    if _packet_already_written(content, packet_id):
        return {"consumer": "direction-candidates", "status": "skipped", "reason": "already written"}

    section = _build_feedback_section(fields, packet_id)
    _append_to_file(path, section)
    return {"consumer": "direction-candidates", "status": "written"}


def _write_planning_gate(
    project_root: Path,
    fields: dict[str, Any],
    packet_id: str,
    active_gate_path: str | None = None,
) -> dict[str, Any]:
    """Append feedback reference to the active planning gate."""
    if not active_gate_path:
        return {"consumer": "planning-gate", "status": "skipped", "reason": "no active gate"}

    path = project_root / active_gate_path
    if not path.exists():
        return {"consumer": "planning-gate", "status": "skipped", "reason": "file not found"}

    content = path.read_text(encoding="utf-8")
    if _packet_already_written(content, packet_id):
        return {"consumer": "planning-gate", "status": "skipped", "reason": "already written"}

    section = _build_feedback_section(fields, packet_id)
    _append_to_file(path, section)
    return {"consumer": "planning-gate", "status": "written"}


def write_consumer_payloads(
    project_root: Path,
    consumer_payloads: dict[str, dict[str, Any]],
    packet_id: str,
    *,
    active_gate_path: str | None = None,
    dry_run: bool = False,
) -> list[dict[str, Any]]:
    """Write consumer payloads to their target documents.

    Parameters
    ----------
    project_root:
        Workspace root directory.
    consumer_payloads:
        Mapping of consumer name (string) → payload fields dict.
        Keys use the ConsumerName.value strings (e.g. ``"checklist"``).
    packet_id:
        Feedback packet ID for idempotency checks.
    active_gate_path:
        Relative path to the current active planning-gate file, if any.
    dry_run:
        If True, return the writeback plan without actually writing.

    Returns
    -------
    List of result dicts, one per consumer, with keys: consumer, status, reason (optional).
    """
    results: list[dict[str, Any]] = []

    _DISPATCH = {
        "direction-candidates": (ConsumerName.DIRECTION_CANDIDATES, _write_direction_candidates),
        "checklist": (ConsumerName.CHECKLIST, _write_checklist),
        "checkpoint": (ConsumerName.CHECKPOINT, _write_checkpoint),
        "planning-gate": (ConsumerName.PLANNING_GATE, _write_planning_gate),
    }

    for consumer_str, fields in consumer_payloads.items():
        if consumer_str in ("phase-map", "handoff"):
            results.append({
                "consumer": consumer_str,
                "status": "skipped",
                "reason": "not auto-written by design",
            })
            continue

        entry = _DISPATCH.get(consumer_str)
        if entry is None:
            results.append({
                "consumer": consumer_str,
                "status": "skipped",
                "reason": "unknown consumer",
            })
            continue

        _consumer_name, write_fn = entry

        if dry_run:
            results.append({
                "consumer": consumer_str,
                "status": "planned",
                "fields": list(fields.keys()),
            })
            continue

        if consumer_str == "planning-gate":
            result = write_fn(project_root, fields, packet_id, active_gate_path)
        else:
            result = write_fn(project_root, fields, packet_id)
        results.append(result)

    return results
