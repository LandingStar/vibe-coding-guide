"""Tests for PEP ↔ WritebackEngine integration (Phase 12 Slice B)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.pep.executor import Executor
from src.pep.writeback_engine import WritebackEngine
from src.pdp.decision_envelope import build_envelope


# ── Helpers ─────────────────────────────────────────────

def _envelope_for(text: str, **kw) -> dict:
    return build_envelope(text, **kw)


# ── Inform gate → applied → writeback triggered ───────

class TestInformWriteback:
    def test_inform_dry_run_generates_plans(self):
        engine = WritebackEngine()
        exe = Executor(dry_run=True, writeback_engine=engine)
        env = _envelope_for("当前状态是什么")
        result = exe.execute(env)
        assert "writeback_plans" in result
        assert len(result["writeback_plans"]) == 1
        assert result["writeback_plans"][0]["operation"] == "create"

    def test_inform_dry_run_no_files(self, tmp_path):
        engine = WritebackEngine(base_dir=tmp_path)
        exe = Executor(dry_run=True, writeback_engine=engine)
        env = _envelope_for("当前状态是什么")
        exe.execute(env)
        # No .codex/writebacks/ directory should be created
        assert not (tmp_path / ".codex" / "writebacks").exists()

    def test_inform_non_dry_run_writes_file(self, tmp_path):
        engine = WritebackEngine(base_dir=tmp_path)
        exe = Executor(dry_run=False, writeback_engine=engine)
        env = _envelope_for("当前状态是什么")
        result = exe.execute(env)
        assert "writeback_results" in result
        assert result["writeback_results"][0]["success"] is True
        # Verify file was actually written
        wb_dir = tmp_path / ".codex" / "writebacks"
        assert wb_dir.exists()
        files = list(wb_dir.glob("*.md"))
        assert len(files) == 1


# ── Review gate → waiting_review → no writeback ───────

class TestReviewNoWriteback:
    def test_review_gate_no_writeback(self):
        engine = WritebackEngine()
        exe = Executor(dry_run=True, writeback_engine=engine)
        env = _envelope_for("fix this error in the code")
        result = exe.execute(env)
        assert "writeback_plans" not in result

    def test_approve_gate_no_writeback(self):
        engine = WritebackEngine()
        exe = Executor(dry_run=True, writeback_engine=engine)
        env = _envelope_for("scope change request")
        result = exe.execute(env)
        assert "writeback_plans" not in result


# ── Delegation completed → applied → writeback ────────

class TestDelegationWriteback:
    def test_delegation_applied_triggers_writeback(self, tmp_path):
        from src.subagent import contract_factory, report_validator
        from src.subagent.stub_worker import StubWorkerBackend

        engine = WritebackEngine(base_dir=tmp_path)
        exe = Executor(
            dry_run=False,
            worker=StubWorkerBackend(),
            contract_factory=contract_factory,
            report_validator=report_validator,
            writeback_engine=engine,
        )
        env = _envelope_for("fix this error in the code")
        result = exe.execute(env)
        # Delegation completed → applied → writeback
        assert result["review_state"] == "applied"
        assert "writeback_plans" in result
        assert result["writeback_results"][0]["success"] is True


# ── No writeback engine → no writeback fields ─────────

class TestNoEngineConfigured:
    def test_no_engine_no_writeback_fields(self):
        exe = Executor(dry_run=True)
        env = _envelope_for("当前状态是什么")
        result = exe.execute(env)
        assert "writeback_plans" not in result
        assert "writeback_results" not in result


# ── Action log records writeback ──────────────────────

class TestWritebackActionLog:
    def test_dry_run_log_entry(self):
        engine = WritebackEngine()
        exe = Executor(dry_run=True, writeback_engine=engine)
        env = _envelope_for("当前状态是什么")
        exe.execute(env)
        log_entries = exe.log.entries
        wb_entries = [e for e in log_entries if "writeback" in e["action"]]
        assert len(wb_entries) >= 1
        assert wb_entries[0]["action"] == "writeback-dry-run"

    def test_non_dry_run_log_entry(self, tmp_path):
        engine = WritebackEngine(base_dir=tmp_path)
        exe = Executor(dry_run=False, writeback_engine=engine)
        env = _envelope_for("当前状态是什么")
        exe.execute(env)
        log_entries = exe.log.entries
        wb_entries = [e for e in log_entries if "writeback" in e["action"]]
        assert len(wb_entries) >= 1
        assert wb_entries[0]["action"] == "writeback-executed"
