"""Tests for Phase 21 — Checkpoint persistence utilities.

Covers:
- write_checkpoint: generates well-formed checkpoint file
- read_checkpoint: parses checkpoint back to structured dict
- validate_checkpoint: detects missing/invalid checkpoints
- Round-trip: write → read → verify
"""

from __future__ import annotations

import pytest
from pathlib import Path

from src.workflow.checkpoint import (
    write_checkpoint,
    read_checkpoint,
    sync_checkpoint_phase,
    validate_checkpoint,
)


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    """Provide a temporary project root."""
    return tmp_path


class TestWriteCheckpoint:

    def test_creates_file(self, project_root: Path):
        path = write_checkpoint(
            project_root,
            phase="Phase 21: Checkpoint, Slice A, status: in-progress",
        )
        assert path.exists()
        assert path.name == "latest.md"

    def test_creates_directory(self, project_root: Path):
        write_checkpoint(project_root, phase="Phase 21")
        assert (project_root / ".codex" / "checkpoints").is_dir()

    def test_contains_required_sections(self, project_root: Path):
        path = write_checkpoint(project_root, phase="Phase 21")
        text = path.read_text(encoding="utf-8")
        assert "## Current Phase" in text
        assert "## Active Planning Gate" in text
        assert "## Current Todo" in text
        assert "## Key Context Files" in text

    def test_phase_written(self, project_root: Path):
        path = write_checkpoint(project_root, phase="Phase 21: Checkpoint, Slice A, status: in-progress")
        text = path.read_text(encoding="utf-8")
        assert "Phase 21: Checkpoint, Slice A, status: in-progress" in text

    def test_todos_written(self, project_root: Path):
        todos = [
            {"title": "Task A", "status": "done"},
            {"title": "Task B", "status": "in-progress"},
            {"title": "Task C", "status": "not-started"},
        ]
        path = write_checkpoint(project_root, phase="Phase 21", todos=todos)
        text = path.read_text(encoding="utf-8")
        assert "- [x] Task A" in text
        assert "- [-] Task B" in text
        assert "- [ ] Task C" in text

    def test_direction_candidates_written(self, project_root: Path):
        candidates = [
            {"name": "Opt A", "description": "Do X", "source": "docs/foo.md"},
            {"name": "Opt B", "description": "Do Y", "source": "docs/bar.md"},
        ]
        path = write_checkpoint(project_root, phase="Phase 21", direction_candidates=candidates)
        text = path.read_text(encoding="utf-8")
        assert "Opt A: Do X — source: docs/foo.md" in text
        assert "Opt B: Do Y — source: docs/bar.md" in text

    def test_key_files_default(self, project_root: Path):
        path = write_checkpoint(project_root, phase="Phase 21")
        text = path.read_text(encoding="utf-8")
        assert "Project Master Checklist.md" in text
        assert "Global Phase Map" in text
        assert "CURRENT.md" in text

    def test_key_files_custom(self, project_root: Path):
        path = write_checkpoint(project_root, phase="Phase 21", key_files=["a.md", "b.md"])
        text = path.read_text(encoding="utf-8")
        assert "- a.md" in text
        assert "- b.md" in text

    def test_pending_decision_written(self, project_root: Path):
        path = write_checkpoint(
            project_root, phase="Phase 21",
            pending_decision="Waiting for user to pick direction",
        )
        text = path.read_text(encoding="utf-8")
        assert "Waiting for user to pick direction" in text

    def test_planning_gate_written(self, project_root: Path):
        path = write_checkpoint(
            project_root, phase="Phase 21",
            planning_gate="design_docs/stages/planning-gate/foo.md",
        )
        text = path.read_text(encoding="utf-8")
        assert "design_docs/stages/planning-gate/foo.md" in text


class TestReadCheckpoint:

    def test_round_trip(self, project_root: Path):
        write_checkpoint(
            project_root,
            phase="Phase 21: Checkpoint, Slice A, status: in-progress",
            planning_gate="design_docs/stages/planning-gate/test.md",
            todos=[
                {"title": "Alpha", "status": "done"},
                {"title": "Beta", "status": "in-progress"},
            ],
            pending_decision="Pick a direction",
            direction_candidates=[
                {"name": "X", "description": "desc X", "source": "src/x.md"},
            ],
            key_files=["file1.md", "file2.md"],
        )
        path = project_root / ".codex" / "checkpoints" / "latest.md"
        data = read_checkpoint(path)

        assert "Phase 21" in data["phase"]
        assert data["planning_gate"] == "design_docs/stages/planning-gate/test.md"
        assert len(data["todos"]) == 2
        assert data["todos"][0]["status"] == "done"
        assert data["todos"][1]["status"] == "in-progress"
        assert data["pending_decision"] == "Pick a direction"
        assert len(data["direction_candidates"]) == 1
        assert data["direction_candidates"][0]["name"] == "X"
        assert data["key_files"] == ["file1.md", "file2.md"]
        assert data["timestamp"]  # non-empty

    def test_empty_optional_fields(self, project_root: Path):
        write_checkpoint(project_root, phase="Phase 21")
        path = project_root / ".codex" / "checkpoints" / "latest.md"
        data = read_checkpoint(path)

        assert data["phase"] == "Phase 21"
        assert data["planning_gate"] == ""
        assert data["todos"] == []
        assert data["pending_decision"] == ""
        assert data["direction_candidates"] == []
        assert len(data["key_files"]) == 3  # defaults

    def test_em_dash_planning_gate_is_treated_as_empty(self, project_root: Path):
        cp_path = project_root / ".codex" / "checkpoints" / "latest.md"
        cp_path.parent.mkdir(parents=True, exist_ok=True)
        cp_path.write_text(
            "# Checkpoint — 2026-04-10\n"
            "## Current Phase\n"
            "Phase 35\n"
            "## Active Planning Gate\n"
            "—\n"
            "## Current Todo\n"
            "(no todos)\n"
            "## Pending User Decision\n"
            "(none)\n"
            "## Direction Candidates\n"
            "(none)\n"
            "## Key Context Files\n"
            "- a.md\n",
            encoding="utf-8",
        )

        data = read_checkpoint(cp_path)
        assert data["planning_gate"] == ""


class TestValidateCheckpoint:

    def test_valid_checkpoint(self, project_root: Path):
        write_checkpoint(project_root, phase="Phase 21", key_files=["a.md"])
        path = project_root / ".codex" / "checkpoints" / "latest.md"
        result = validate_checkpoint(path)

        assert result["valid"] is True
        assert result["errors"] == []
        assert result["data"] is not None

    def test_missing_file(self, project_root: Path):
        result = validate_checkpoint(project_root / "nonexistent.md")
        assert result["valid"] is False
        assert "does not exist" in result["errors"][0]

    def test_empty_phase(self, project_root: Path):
        # Write a checkpoint then corrupt it
        cp_path = project_root / ".codex" / "checkpoints" / "latest.md"
        cp_path.parent.mkdir(parents=True, exist_ok=True)
        cp_path.write_text(
            "# Checkpoint — 2026-04-10\n"
            "## Current Phase\n"
            "\n"
            "## Active Planning Gate\n"
            "(none)\n"
            "## Current Todo\n"
            "(no todos)\n"
            "## Key Context Files\n"
            "- a.md\n",
            encoding="utf-8",
        )
        result = validate_checkpoint(cp_path)
        assert result["valid"] is False
        assert any("Phase is empty" in e for e in result["errors"])

    def test_missing_section(self, project_root: Path):
        cp_path = project_root / ".codex" / "checkpoints" / "latest.md"
        cp_path.parent.mkdir(parents=True, exist_ok=True)
        cp_path.write_text(
            "# Checkpoint — 2026-04-10\n"
            "## Current Phase\n"
            "Phase 21\n",
            encoding="utf-8",
        )
        result = validate_checkpoint(cp_path)
        assert result["valid"] is False
        assert any("Missing" in e for e in result["errors"])

    def test_overwrite_existing(self, project_root: Path):
        """Writing a new checkpoint overwrites the previous one."""
        write_checkpoint(project_root, phase="Phase A")
        write_checkpoint(project_root, phase="Phase B")
        path = project_root / ".codex" / "checkpoints" / "latest.md"
        data = read_checkpoint(path)
        assert data["phase"] == "Phase B"


class TestSyncCheckpointPhase:

    def test_sync_updates_phase_and_preserves_fields(self, project_root: Path):
        write_checkpoint(
            project_root,
            phase="Phase 27",
            planning_gate="design_docs/stages/planning-gate/phase-27.md",
            todos=[{"title": "Task A", "status": "done"}],
            pending_decision="Pick next phase",
            direction_candidates=[
                {"name": "A", "description": "desc", "source": "docs/a.md"}
            ],
            key_files=["a.md", "b.md"],
        )

        sync_checkpoint_phase(
            project_root,
            phase="Phase 28",
            planning_gate="",
        )

        data = read_checkpoint(project_root / ".codex" / "checkpoints" / "latest.md")
        assert data["phase"] == "Phase 28"
        assert data["planning_gate"] == ""
        assert data["todos"] == [{"title": "Task A", "status": "done"}]
        assert data["pending_decision"] == "Pick next phase"
        assert data["direction_candidates"][0]["name"] == "A"
        assert data["key_files"] == ["a.md", "b.md"]

    def test_sync_creates_checkpoint_if_missing(self, project_root: Path):
        path = sync_checkpoint_phase(project_root, phase="Phase 28")
        assert path.exists()
        data = read_checkpoint(path)
        assert data["phase"] == "Phase 28"
