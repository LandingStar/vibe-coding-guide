"""Helpers for the safe-stop writeback bundle contract."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


_DIRECTION_DOC_PATTERN = re.compile(r"direction-candidates-after-phase-(\d+)\.md$", re.IGNORECASE)


def _step(
    *,
    key: str,
    label: str,
    step_type: str,
    paths: list[str],
    rationale: str,
    condition: str = "",
) -> dict[str, Any]:
    step: dict[str, Any] = {
        "key": key,
        "label": label,
        "type": step_type,
        "paths": paths,
        "rationale": rationale,
    }
    if condition:
        step["condition"] = condition
    return step


def _direction_doc_sort_key(path: Path) -> tuple[int, str]:
    match = _DIRECTION_DOC_PATTERN.search(path.name)
    phase_num = int(match.group(1)) if match else -1
    return (phase_num, path.name)


def find_latest_direction_candidates_doc(project_root: str | Path) -> str | None:
    """Return the latest direction-candidates doc relative to project root."""
    root = Path(project_root)
    design_docs_dir = root / "design_docs"
    if not design_docs_dir.is_dir():
        return None

    candidates = [
        path for path in design_docs_dir.glob("direction-candidates-after-phase-*.md")
        if path.is_file()
    ]
    if not candidates:
        return None

    candidates.sort(key=_direction_doc_sort_key)
    return candidates[-1].relative_to(root).as_posix()


def build_safe_stop_writeback_bundle(project_root: str | Path) -> dict[str, Any]:
    """Build the explicit safe-stop writeback bundle contract."""
    direction_doc = find_latest_direction_candidates_doc(project_root)

    required_steps: list[dict[str, Any]] = [
        _step(
            key="generate-canonical-handoff",
            label="Generate canonical handoff",
            step_type="action",
            paths=[".codex/handoffs/history/*.md"],
            rationale="A safe stop needs a canonical handoff artifact before the recovery mirror can be rotated.",
        ),
        _step(
            key="refresh-current-mirror",
            label="Refresh CURRENT mirror",
            step_type="document-sync",
            paths=[".codex/handoffs/CURRENT.md"],
            rationale="The default recovery entrypoint must mirror the latest active canonical handoff.",
        ),
        _step(
            key="sync-checklist",
            label="Sync Project Master Checklist",
            step_type="document-sync",
            paths=["design_docs/Project Master Checklist.md"],
            rationale="The status board must reflect the closed slice and resulting safe-stop state.",
        ),
        _step(
            key="sync-phase-map",
            label="Sync Global Phase Map",
            step_type="document-sync",
            paths=["design_docs/Global Phase Map and Current Position.md"],
            rationale="The phase narrative must match the new safe-stop boundary and next-step position.",
        ),
        _step(
            key="sync-checkpoint",
            label="Sync checkpoint",
            step_type="document-sync",
            paths=[".codex/checkpoints/latest.md"],
            rationale="Checkpoint recovery must reflect the same safe-stop state as the long-lived docs.",
        ),
    ]

    conditional_steps: list[dict[str, Any]] = [
        _step(
            key="clear-active-slice-markers",
            label="Clear active-slice markers",
            step_type="state-sync",
            paths=[
                "design_docs/Project Master Checklist.md",
                "design_docs/Global Phase Map and Current Position.md",
                ".codex/checkpoints/latest.md",
            ],
            rationale="A closed safe stop must not leave stale active planning-gate markers behind.",
            condition="When the safe stop returns the repo to no active slice.",
        ),
        _step(
            key="supersede-previous-active-handoff",
            label="Supersede previous active canonical handoff",
            step_type="handoff-lifecycle",
            paths=[".codex/handoffs/history/*.md"],
            rationale="Only one canonical handoff may remain active after mirror rotation.",
            condition="When another canonical handoff is currently active.",
        ),
        _step(
            key="sync-safe-stop-protocols",
            label="Sync workflow and handoff protocols",
            step_type="document-sync",
            paths=[
                "design_docs/tooling/Document-Driven Workflow Standard.md",
                "design_docs/tooling/Session Handoff Standard.md",
            ],
            rationale="Protocol surfaces must stay aligned if the safe-stop close behavior itself changed.",
            condition="When the slice changes safe-stop or handoff workflow semantics.",
        ),
    ]

    if direction_doc:
        required_steps.insert(
            4,
            _step(
                key="sync-direction-candidates",
                label="Sync current direction candidates doc",
                step_type="document-sync",
                paths=[direction_doc],
                rationale="The safe stop should hand control back to the latest direction-analysis surface.",
            ),
        )
    else:
        conditional_steps.insert(
            0,
            _step(
                key="sync-direction-candidates",
                label="Sync current direction candidates doc",
                step_type="document-sync",
                paths=["design_docs/direction-candidates-after-phase-*.md"],
                rationale="The safe stop should hand control back to the repo's current direction-analysis surface.",
                condition="When the repo tracks a direction-candidates document for post-safe-stop selection.",
            ),
        )

    files_to_update: list[str] = []
    for step in required_steps:
        if step["type"] != "document-sync":
            continue
        for path in step["paths"]:
            if path not in files_to_update:
                files_to_update.append(path)

    return {
        "bundle_name": "safe-stop-writeback",
        "trigger": "safe-stop close",
        "required_steps": required_steps,
        "conditional_steps": conditional_steps,
        "direction_candidates_path": direction_doc or "",
        "files_to_update": files_to_update,
    }