"""Tests for WritebackEngine (Phase 12 Slice A)."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from src.pep.writeback_engine import WritebackEngine, WritebackPlan, WritebackResult


# ── Helpers ─────────────────────────────────────────────

def _make_envelope(intent: str = "question", gate: str = "inform") -> dict:
    return {
        "decision_id": "env-test-001",
        "intent_result": {"intent": intent},
        "gate_decision": {"gate_level": gate},
    }


def _applied_result(**overrides) -> dict:
    base = {
        "envelope_id": "env-test-001",
        "execution_status": "applied",
        "detail": "Gate=inform, fast path.",
        "review_state": "applied",
        "review_history": [],
    }
    base.update(overrides)
    return base


def _waiting_result() -> dict:
    return {
        "envelope_id": "env-test-002",
        "execution_status": "waiting_review",
        "detail": "Gate=review.",
        "review_state": "waiting_review",
        "review_history": [],
    }


# ── Plan generation ────────────────────────────────────

class TestPlanGeneration:
    def test_applied_generates_plan(self):
        engine = WritebackEngine()
        plans = engine.plan(_make_envelope(), _applied_result())
        assert len(plans) == 1
        assert plans[0].target_path == ".codex/writebacks/env-test-001.md"
        assert plans[0].operation == "create"
        assert plans[0].content_type == "markdown"

    def test_non_applied_generates_no_plan(self):
        engine = WritebackEngine()
        plans = engine.plan(_make_envelope(), _waiting_result())
        assert plans == []

    def test_plan_content_includes_envelope_info(self):
        engine = WritebackEngine()
        plans = engine.plan(
            _make_envelope(intent="correction", gate="review"),
            _applied_result(),
        )
        content = plans[0].content
        assert "correction" in content
        assert "review" in content
        assert "env-test-001" in content


# ── Dry-run execution ──────────────────────────────────

class TestDryRunExecution:
    def test_dry_run_returns_success(self):
        engine = WritebackEngine()
        plan = WritebackPlan(
            target_path="test/output.md",
            content="# Hello",
            operation="create",
        )
        result = engine.execute_plan(plan, dry_run=True)
        assert result.success is True
        assert "dry-run" in result.detail

    def test_dry_run_does_not_write_file(self, tmp_path):
        engine = WritebackEngine(base_dir=tmp_path)
        plan = WritebackPlan(
            target_path="test/output.md",
            content="# Hello",
            operation="create",
        )
        engine.execute_plan(plan, dry_run=True)
        assert not (tmp_path / "test" / "output.md").exists()

    def test_dry_run_records_history(self):
        engine = WritebackEngine()
        plan = WritebackPlan(
            target_path="test/output.md",
            content="# Hello",
        )
        engine.execute_plan(plan, dry_run=True)
        assert len(engine.history) == 1
        assert engine.history[0]["dry_run"] is True

    def test_execute_all_dry_run(self):
        engine = WritebackEngine()
        plans = [
            WritebackPlan(target_path="a.md", content="A"),
            WritebackPlan(target_path="b.md", content="B"),
        ]
        results = engine.execute_all(plans, dry_run=True)
        assert len(results) == 2
        assert all(r.success for r in results)


# ── Real write execution ───────────────────────────────

class TestRealExecution:
    def test_create_writes_file(self, tmp_path):
        engine = WritebackEngine(base_dir=tmp_path)
        plan = WritebackPlan(
            target_path="output/test.md",
            content="# Created",
            operation="create",
        )
        result = engine.execute_plan(plan, dry_run=False)
        assert result.success is True
        written = (tmp_path / "output" / "test.md").read_text(encoding="utf-8")
        assert written == "# Created"

    def test_update_existing_file(self, tmp_path):
        target = tmp_path / "existing.md"
        target.write_text("old content", encoding="utf-8")
        engine = WritebackEngine(base_dir=tmp_path)
        plan = WritebackPlan(
            target_path="existing.md",
            content="new content",
            operation="update",
        )
        result = engine.execute_plan(plan, dry_run=False)
        assert result.success is True
        assert target.read_text(encoding="utf-8") == "new content"

    def test_update_nonexistent_fails(self, tmp_path):
        engine = WritebackEngine(base_dir=tmp_path)
        plan = WritebackPlan(
            target_path="nonexistent.md",
            content="data",
            operation="update",
        )
        result = engine.execute_plan(plan, dry_run=False)
        assert result.success is False
        assert "does not exist" in result.error

    def test_append_to_existing(self, tmp_path):
        target = tmp_path / "log.md"
        target.write_text("line1\n", encoding="utf-8")
        engine = WritebackEngine(base_dir=tmp_path)
        plan = WritebackPlan(
            target_path="log.md",
            content="line2\n",
            operation="append",
        )
        result = engine.execute_plan(plan, dry_run=False)
        assert result.success is True
        assert target.read_text(encoding="utf-8") == "line1\nline2\n"

    def test_append_creates_if_missing(self, tmp_path):
        engine = WritebackEngine(base_dir=tmp_path)
        plan = WritebackPlan(
            target_path="new.md",
            content="first line\n",
            operation="append",
        )
        result = engine.execute_plan(plan, dry_run=False)
        assert result.success is True
        assert (tmp_path / "new.md").read_text(encoding="utf-8") == "first line\n"

    def test_unknown_operation_fails(self, tmp_path):
        engine = WritebackEngine(base_dir=tmp_path)
        plan = WritebackPlan(
            target_path="x.md",
            content="data",
            operation="delete",
        )
        result = engine.execute_plan(plan, dry_run=False)
        assert result.success is False
        assert "Unknown operation" in result.error

    def test_creates_nested_directories(self, tmp_path):
        engine = WritebackEngine(base_dir=tmp_path)
        plan = WritebackPlan(
            target_path="a/b/c/deep.md",
            content="deep content",
            operation="create",
        )
        result = engine.execute_plan(plan, dry_run=False)
        assert result.success is True
        assert (tmp_path / "a" / "b" / "c" / "deep.md").exists()


# ── Audit trail ────────────────────────────────────────

class TestAuditTrail:
    def test_history_records_operations(self, tmp_path):
        engine = WritebackEngine(base_dir=tmp_path)
        plan = WritebackPlan(
            target_path="audit.md",
            content="data",
            operation="create",
        )
        engine.execute_plan(plan, dry_run=False)
        assert len(engine.history) == 1
        entry = engine.history[0]
        assert entry["target_path"] == "audit.md"
        assert entry["operation"] == "create"
        assert entry["dry_run"] is False
        assert entry["success"] is True
        assert "timestamp" in entry

    def test_history_is_copy(self):
        engine = WritebackEngine()
        plan = WritebackPlan(target_path="x.md", content="x")
        engine.execute_plan(plan, dry_run=True)
        h = engine.history
        h.clear()
        assert len(engine.history) == 1


# ── Unicode content ────────────────────────────────────

class TestUnicodeContent:
    def test_chinese_content(self, tmp_path):
        engine = WritebackEngine(base_dir=tmp_path)
        plan = WritebackPlan(
            target_path="中文.md",
            content="# 测试文档\n\n这是中文内容。",
            operation="create",
        )
        result = engine.execute_plan(plan, dry_run=False)
        assert result.success is True
        written = (tmp_path / "中文.md").read_text(encoding="utf-8")
        assert "测试文档" in written
