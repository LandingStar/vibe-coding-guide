from __future__ import annotations

from pathlib import Path

from src.workflow.safe_stop_writeback import (
    build_safe_stop_writeback_bundle,
    find_latest_direction_candidates_doc,
)


def test_find_latest_direction_candidates_doc_uses_highest_phase(tmp_path: Path) -> None:
    design_docs = tmp_path / "design_docs"
    design_docs.mkdir(parents=True)
    (design_docs / "direction-candidates-after-phase-31.md").write_text("old", encoding="utf-8")
    (design_docs / "direction-candidates-after-phase-35.md").write_text("new", encoding="utf-8")

    result = find_latest_direction_candidates_doc(tmp_path)

    assert result == "design_docs/direction-candidates-after-phase-35.md"


def test_build_safe_stop_writeback_bundle_includes_required_sinks(tmp_path: Path) -> None:
    design_docs = tmp_path / "design_docs"
    design_docs.mkdir(parents=True)
    (design_docs / "direction-candidates-after-phase-35.md").write_text("x", encoding="utf-8")

    bundle = build_safe_stop_writeback_bundle(tmp_path)
    required_keys = {step["key"] for step in bundle["required_steps"]}

    assert bundle["bundle_name"] == "safe-stop-writeback"
    assert "generate-canonical-handoff" in required_keys
    assert "refresh-current-mirror" in required_keys
    assert "sync-checklist" in required_keys
    assert "sync-phase-map" in required_keys
    assert "sync-direction-candidates" in required_keys
    assert "sync-checkpoint" in required_keys
    assert ".codex/handoffs/CURRENT.md" in bundle["files_to_update"]
    assert ".codex/checkpoints/latest.md" in bundle["files_to_update"]
    assert "design_docs/direction-candidates-after-phase-35.md" in bundle["files_to_update"]


def test_build_safe_stop_writeback_bundle_uses_conditional_direction_step_when_missing(tmp_path: Path) -> None:
    bundle = build_safe_stop_writeback_bundle(tmp_path)

    required_keys = {step["key"] for step in bundle["required_steps"]}
    conditional_keys = {step["key"] for step in bundle["conditional_steps"]}

    assert "sync-direction-candidates" not in required_keys
    assert "sync-direction-candidates" in conditional_keys
    assert bundle["direction_candidates_path"] == ""