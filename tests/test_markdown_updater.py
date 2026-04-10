"""Tests for markdown_updater and directive-based WritebackEngine (Phase 14 Slice A)."""

from __future__ import annotations

import pytest

from src.pep.markdown_updater import (
    SectionSpan,
    append_to_section,
    find_section,
    insert_after_line,
    replace_line,
    replace_section,
)
from src.pep.writeback_engine import WritebackEngine, WritebackPlan


# ── Sample document ─────────────────────────────────────

SAMPLE_DOC = """\
# Project Title

Some intro text.

## Current Status

- Phase 1: done
- Phase 2: done
- Phase 3: in progress

## Next Steps

- Do something
- Do another thing

## Notes

Random notes here.
"""

SAMPLE_LINES = SAMPLE_DOC.splitlines(keepends=True)


# ── find_section ────────────────────────────────────────

class TestFindSection:
    def test_finds_h2_section(self):
        span = find_section(SAMPLE_LINES, "Current Status")
        assert span is not None
        assert span.heading_level == 2
        assert "## Current Status\n" == SAMPLE_LINES[span.start]

    def test_section_end_at_next_h2(self):
        span = find_section(SAMPLE_LINES, "Current Status")
        assert span is not None
        assert "## Next Steps\n" == SAMPLE_LINES[span.end]

    def test_finds_h1_section(self):
        span = find_section(SAMPLE_LINES, "Project Title")
        assert span is not None
        assert span.heading_level == 1
        # h1 section ends at EOF since no other h1 exists
        assert span.end == len(SAMPLE_LINES)

    def test_case_insensitive(self):
        span = find_section(SAMPLE_LINES, "current status")
        assert span is not None

    def test_not_found(self):
        span = find_section(SAMPLE_LINES, "Nonexistent")
        assert span is None

    def test_last_section_ends_at_eof(self):
        span = find_section(SAMPLE_LINES, "Notes")
        assert span is not None
        assert span.end == len(SAMPLE_LINES)


# ── replace_section ────────────────────────────────────

class TestReplaceSection:
    def test_replace_body_keep_heading(self):
        result = replace_section(SAMPLE_LINES, "Current Status", "- All done!\n")
        text = "".join(result)
        assert "## Current Status\n" in text
        assert "- All done!" in text
        assert "Phase 3: in progress" not in text

    def test_replace_body_remove_heading(self):
        result = replace_section(
            SAMPLE_LINES, "Current Status", "## New Heading\n\nNew body.\n",
            keep_heading=False,
        )
        text = "".join(result)
        assert "## New Heading" in text
        assert "## Current Status" not in text

    def test_replace_preserves_surrounding(self):
        result = replace_section(SAMPLE_LINES, "Current Status", "- replaced\n")
        text = "".join(result)
        assert "# Project Title" in text
        assert "## Next Steps" in text
        assert "Random notes here." in text

    def test_not_found_raises(self):
        with pytest.raises(KeyError):
            replace_section(SAMPLE_LINES, "Missing", "content")


# ── append_to_section ──────────────────────────────────

class TestAppendToSection:
    def test_appends_before_next_section(self):
        result = append_to_section(SAMPLE_LINES, "Current Status", "- Phase 4: planned\n")
        text = "".join(result)
        # The new line should appear between Phase 3 and ## Next Steps
        idx_new = text.index("Phase 4: planned")
        idx_next = text.index("## Next Steps")
        assert idx_new < idx_next

    def test_appends_to_last_section(self):
        result = append_to_section(SAMPLE_LINES, "Notes", "- Extra note\n")
        text = "".join(result)
        assert text.endswith("- Extra note\n")

    def test_not_found_raises(self):
        with pytest.raises(KeyError):
            append_to_section(SAMPLE_LINES, "Missing", "content")


# ── insert_after_line ──────────────────────────────────

class TestInsertAfterLine:
    def test_inserts_after_matching_line(self):
        result = insert_after_line(SAMPLE_LINES, r"Phase 2: done", "- Phase 2.5: new\n")
        text = "".join(result)
        idx_p2 = text.index("Phase 2: done")
        idx_new = text.index("Phase 2.5: new")
        idx_p3 = text.index("Phase 3: in progress")
        assert idx_p2 < idx_new < idx_p3

    def test_first_only_default(self):
        # Document with duplicate lines
        lines = ["aaa\n", "bbb\n", "aaa\n", "ccc\n"]
        result = insert_after_line(lines, r"^aaa$", "INSERTED\n")
        text = "".join(result)
        assert text.count("INSERTED") == 1

    def test_all_matches(self):
        lines = ["aaa\n", "bbb\n", "aaa\n", "ccc\n"]
        result = insert_after_line(lines, r"^aaa$", "INSERTED\n", first_only=False)
        text = "".join(result)
        assert text.count("INSERTED") == 2

    def test_not_found_raises(self):
        with pytest.raises(KeyError):
            insert_after_line(SAMPLE_LINES, r"^NOMATCH$", "content")


# ── replace_line ────────────────────────────────────────

class TestReplaceLine:
    def test_replaces_matching_line(self):
        result = replace_line(
            SAMPLE_LINES,
            r"Phase 3: in progress",
            "- Phase 3: done\n",
        )
        text = "".join(result)
        assert "Phase 3: done" in text
        assert "Phase 3: in progress" not in text

    def test_first_only_default(self):
        lines = ["aaa\n", "bbb\n", "aaa\n"]
        result = replace_line(lines, r"^aaa$", "xxx\n")
        text = "".join(result)
        assert text.count("xxx") == 1
        assert text.count("aaa") == 1

    def test_not_found_raises(self):
        with pytest.raises(KeyError):
            replace_line(SAMPLE_LINES, r"^NOMATCH$", "replacement")


# ── WritebackEngine directive ops ──────────────────────

class TestDirectiveEngine:
    def test_section_replace(self, tmp_path):
        doc_path = tmp_path / "doc.md"
        doc_path.write_text(SAMPLE_DOC, encoding="utf-8")

        engine = WritebackEngine(base_dir=tmp_path)
        plan = WritebackPlan(
            target_path="doc.md",
            content="- Everything complete!\n",
            operation="section_replace",
            match="Current Status",
        )
        result = engine.execute_plan(plan, dry_run=False)
        assert result.success
        text = doc_path.read_text(encoding="utf-8")
        assert "Everything complete!" in text
        assert "Phase 3: in progress" not in text

    def test_section_append(self, tmp_path):
        doc_path = tmp_path / "doc.md"
        doc_path.write_text(SAMPLE_DOC, encoding="utf-8")

        engine = WritebackEngine(base_dir=tmp_path)
        plan = WritebackPlan(
            target_path="doc.md",
            content="- Phase 4: planned\n",
            operation="section_append",
            match="Current Status",
        )
        result = engine.execute_plan(plan, dry_run=False)
        assert result.success
        text = doc_path.read_text(encoding="utf-8")
        assert "Phase 4: planned" in text
        # Original content still present
        assert "Phase 3: in progress" in text

    def test_line_insert(self, tmp_path):
        doc_path = tmp_path / "doc.md"
        doc_path.write_text(SAMPLE_DOC, encoding="utf-8")

        engine = WritebackEngine(base_dir=tmp_path)
        plan = WritebackPlan(
            target_path="doc.md",
            content="- Phase 2.5: inserted\n",
            operation="line_insert",
            match=r"Phase 2: done",
        )
        result = engine.execute_plan(plan, dry_run=False)
        assert result.success
        text = doc_path.read_text(encoding="utf-8")
        assert "Phase 2.5: inserted" in text

    def test_line_replace(self, tmp_path):
        doc_path = tmp_path / "doc.md"
        doc_path.write_text(SAMPLE_DOC, encoding="utf-8")

        engine = WritebackEngine(base_dir=tmp_path)
        plan = WritebackPlan(
            target_path="doc.md",
            content="- Phase 3: DONE\n",
            operation="line_replace",
            match=r"Phase 3: in progress",
        )
        result = engine.execute_plan(plan, dry_run=False)
        assert result.success
        text = doc_path.read_text(encoding="utf-8")
        assert "Phase 3: DONE" in text
        assert "Phase 3: in progress" not in text

    def test_directive_dry_run(self, tmp_path):
        doc_path = tmp_path / "doc.md"
        doc_path.write_text(SAMPLE_DOC, encoding="utf-8")

        engine = WritebackEngine(base_dir=tmp_path)
        plan = WritebackPlan(
            target_path="doc.md",
            content="- replaced\n",
            operation="section_replace",
            match="Current Status",
        )
        result = engine.execute_plan(plan, dry_run=True)
        assert result.success
        assert "dry-run" in result.detail
        # File should remain unchanged
        assert "Phase 3: in progress" in doc_path.read_text(encoding="utf-8")

    def test_directive_missing_file(self, tmp_path):
        engine = WritebackEngine(base_dir=tmp_path)
        plan = WritebackPlan(
            target_path="nonexistent.md",
            content="content",
            operation="section_replace",
            match="Heading",
        )
        result = engine.execute_plan(plan, dry_run=False)
        assert not result.success
        assert "does not exist" in result.error

    def test_directive_section_not_found(self, tmp_path):
        doc_path = tmp_path / "doc.md"
        doc_path.write_text(SAMPLE_DOC, encoding="utf-8")

        engine = WritebackEngine(base_dir=tmp_path)
        plan = WritebackPlan(
            target_path="doc.md",
            content="content",
            operation="section_replace",
            match="Nonexistent Section",
        )
        result = engine.execute_plan(plan, dry_run=False)
        assert not result.success
        assert "not found" in result.error.lower()

    def test_directive_in_history(self, tmp_path):
        doc_path = tmp_path / "doc.md"
        doc_path.write_text(SAMPLE_DOC, encoding="utf-8")

        engine = WritebackEngine(base_dir=tmp_path)
        plan = WritebackPlan(
            target_path="doc.md",
            content="- new\n",
            operation="section_append",
            match="Notes",
        )
        engine.execute_plan(plan, dry_run=False)
        assert len(engine.history) == 1
        assert engine.history[0]["operation"] == "section_append"
