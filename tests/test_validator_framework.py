"""Tests for the Validator / Check / Trigger framework (Phase 18)."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.validators.base import (
    CheckResult,
    TriggerResult,
    ValidationResult,
)
from src.validators.registry import ValidatorRegistry
from src.validators.schema_validator import SchemaValidator
from src.validators.script_validator import ScriptValidator
from src.validators.trigger_dispatcher import TriggerDispatcher


# ── dataclass basics ──────────────────────────────────────────────

class TestValidationResult:
    def test_defaults(self):
        r = ValidationResult(valid=True)
        assert r.valid is True
        assert r.errors == []
        assert r.warnings == []

    def test_with_errors(self):
        r = ValidationResult(valid=False, errors=["e1", "e2"])
        assert not r.valid
        assert len(r.errors) == 2


class TestCheckResult:
    def test_defaults(self):
        r = CheckResult(passed=True)
        assert r.passed is True
        assert r.message == ""


class TestTriggerResult:
    def test_defaults(self):
        r = TriggerResult(handled=True)
        assert r.handled is True
        assert r.output == {}

    def test_with_output(self):
        r = TriggerResult(handled=True, output={"key": "val"})
        assert r.output["key"] == "val"


# ── ValidatorRegistry ────────────────────────────────────────────

class _StubValidator:
    def validate(self, data: dict) -> ValidationResult:
        return ValidationResult(valid=True)


class _StubCheck:
    def check(self, context: dict) -> CheckResult:
        return CheckResult(passed=True)


class _StubTrigger:
    def handle(self, event: dict) -> TriggerResult:
        return TriggerResult(handled=True)


class TestValidatorRegistry:
    def test_register_and_get_validator(self):
        reg = ValidatorRegistry()
        v = _StubValidator()
        reg.register_validator("v1", v)
        assert reg.get_validator("v1") is v
        assert reg.get_validator("missing") is None

    def test_list_validators(self):
        reg = ValidatorRegistry()
        reg.register_validator("a", _StubValidator())
        reg.register_validator("b", _StubValidator())
        assert set(reg.list_validators()) == {"a", "b"}

    def test_register_and_get_check(self):
        reg = ValidatorRegistry()
        c = _StubCheck()
        reg.register_check("c1", c)
        assert reg.get_check("c1") is c
        assert reg.get_check("missing") is None

    def test_list_checks(self):
        reg = ValidatorRegistry()
        reg.register_check("x", _StubCheck())
        assert reg.list_checks() == ["x"]

    def test_register_and_get_trigger(self):
        reg = ValidatorRegistry()
        t = _StubTrigger()
        reg.register_trigger("t1", t)
        assert reg.get_trigger("t1") is t

    def test_list_triggers(self):
        reg = ValidatorRegistry()
        reg.register_trigger("a", _StubTrigger())
        reg.register_trigger("b", _StubTrigger())
        assert set(reg.list_triggers()) == {"a", "b"}

    def test_empty_registry(self):
        reg = ValidatorRegistry()
        assert reg.list_validators() == []
        assert reg.list_checks() == []
        assert reg.list_triggers() == []


# ── SchemaValidator ──────────────────────────────────────────────

class TestSchemaValidator:
    SCHEMA = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0},
        },
        "required": ["name"],
    }

    def test_valid_data(self):
        sv = SchemaValidator(self.SCHEMA)
        r = sv.validate({"name": "Alice", "age": 30})
        assert r.valid is True
        assert r.errors == []

    def test_missing_required(self):
        sv = SchemaValidator(self.SCHEMA)
        r = sv.validate({"age": 30})
        assert r.valid is False
        assert any("name" in e for e in r.errors)

    def test_wrong_type(self):
        sv = SchemaValidator(self.SCHEMA)
        r = sv.validate({"name": "Alice", "age": "not-a-number"})
        assert r.valid is False

    def test_empty_object(self):
        sv = SchemaValidator(self.SCHEMA)
        r = sv.validate({})
        assert r.valid is False


# ── ScriptValidator ──────────────────────────────────────────────

class TestScriptValidator:
    def test_passing_function(self):
        def ok_func(data: dict) -> dict:
            return {"valid": True}

        sv = ScriptValidator(ok_func)
        r = sv.validate({"x": 1})
        assert r.valid is True
        assert r.errors == []

    def test_failing_function(self):
        def fail_func(data: dict) -> dict:
            return {"valid": False, "errors": ["bad data"]}

        sv = ScriptValidator(fail_func)
        r = sv.validate({"x": 1})
        assert r.valid is False
        assert r.errors == ["bad data"]

    def test_warnings(self):
        def warn_func(data: dict) -> dict:
            return {"valid": True, "warnings": ["maybe bad"]}

        sv = ScriptValidator(warn_func)
        r = sv.validate({})
        assert r.valid is True
        assert r.warnings == ["maybe bad"]

    def test_function_receives_data(self):
        received = {}

        def capture_func(data: dict) -> dict:
            received.update(data)
            return {"valid": True}

        sv = ScriptValidator(capture_func)
        sv.validate({"key": "value"})
        assert received == {"key": "value"}


# ── TriggerDispatcher ───────────────────────────────────────────

class _CountingTrigger:
    def __init__(self):
        self.calls: list[dict] = []

    def handle(self, event: dict) -> TriggerResult:
        self.calls.append(event)
        return TriggerResult(handled=True, output={"count": len(self.calls)})


class TestTriggerDispatcher:
    def test_dispatch_to_handler(self):
        td = TriggerDispatcher()
        t = _CountingTrigger()
        td.register("my_event", t)
        results = td.dispatch({"type": "my_event", "payload": "x"})
        assert len(results) == 1
        assert results[0].handled is True
        assert t.calls == [{"type": "my_event", "payload": "x"}]

    def test_dispatch_no_handlers(self):
        td = TriggerDispatcher()
        results = td.dispatch({"type": "unknown"})
        assert results == []

    def test_multiple_handlers(self):
        td = TriggerDispatcher()
        t1 = _CountingTrigger()
        t2 = _CountingTrigger()
        td.register("evt", t1)
        td.register("evt", t2)
        results = td.dispatch({"type": "evt"})
        assert len(results) == 2
        assert len(t1.calls) == 1
        assert len(t2.calls) == 1

    def test_list_event_types(self):
        td = TriggerDispatcher()
        td.register("a", _CountingTrigger())
        td.register("b", _CountingTrigger())
        assert set(td.list_event_types()) == {"a", "b"}

    def test_dispatch_missing_type_field(self):
        td = TriggerDispatcher()
        td.register("", _CountingTrigger())
        # event without 'type' key defaults to ""
        results = td.dispatch({"payload": "test"})
        assert len(results) == 1


# ── Protocol conformance ─────────────────────────────────────────

class TestProtocolConformance:
    """Verify that concrete classes satisfy the Protocol contracts."""

    def test_schema_validator_is_validator(self):
        from src.validators.base import Validator
        sv = SchemaValidator({"type": "object"})
        # duck-type check — SchemaValidator has .validate(dict) -> ValidationResult
        assert hasattr(sv, "validate")
        r = sv.validate({})
        assert isinstance(r, ValidationResult)

    def test_script_validator_is_validator(self):
        sv = ScriptValidator(lambda d: {"valid": True})
        r = sv.validate({})
        assert isinstance(r, ValidationResult)

    def test_stub_check_conformance(self):
        c = _StubCheck()
        r = c.check({})
        assert isinstance(r, CheckResult)

    def test_stub_trigger_conformance(self):
        t = _StubTrigger()
        r = t.handle({})
        assert isinstance(r, TriggerResult)


# ── PEP Integration ─────────────────────────────────────────────

from src.pep.executor import Executor
from src.pep.writeback_engine import WritebackEngine
from src.pdp.decision_envelope import build_envelope


class _AlwaysPassValidator:
    def validate(self, data: dict) -> ValidationResult:
        return ValidationResult(valid=True)


class _AlwaysFailValidator:
    def validate(self, data: dict) -> ValidationResult:
        return ValidationResult(valid=False, errors=["blocked by pack validator"])


class _AlwaysPassCheck:
    def __init__(self):
        self.called = False

    def check(self, context: dict) -> CheckResult:
        self.called = True
        return CheckResult(passed=True, message="ok")


class _BlockingCheck:
    def check(self, context: dict) -> CheckResult:
        return CheckResult(passed=False, message="writeback not allowed")


class TestPEPValidatorIntegration:
    """Test executor with validator_registry injected."""

    def _make_delegation_envelope(self):
        """Build an envelope that triggers delegation."""
        env = build_envelope("请把这部分工作交给子 agent 处理")
        # Force delegation
        env["delegation_decision"] = {
            "delegate": True,
            "allow_handoff": False,
            "delegatable_intent": "implementation",
        }
        return env

    def test_executor_no_registry_backward_compatible(self):
        exe = Executor(dry_run=True)
        env = build_envelope("当前状态是什么")
        result = exe.execute(env)
        assert "pack_validations" not in result

    def test_pack_validator_runs_on_delegation(self):
        reg = ValidatorRegistry()
        reg.register_validator("pass_v", _AlwaysPassValidator())

        class FakeFactory:
            def build(self, d):
                return {"contract_id": "c1"}

        class FakeWorker:
            def execute(self, c):
                return {"report_id": "r1", "status": "completed"}

        exe = Executor(
            dry_run=True,
            worker=FakeWorker(),
            contract_factory=FakeFactory(),
            validator_registry=reg,
        )
        env = self._make_delegation_envelope()
        result = exe.execute(env)
        assert "pack_validations" in result
        assert len(result["pack_validations"]) == 1
        assert result["pack_validations"][0]["valid"] is True
        assert result["pack_validations"][0]["name"] == "pass_v"

    def test_pack_validator_fail_records_errors(self):
        reg = ValidatorRegistry()
        reg.register_validator("fail_v", _AlwaysFailValidator())

        class FakeFactory:
            def build(self, d):
                return {"contract_id": "c1"}

        class FakeWorker:
            def execute(self, c):
                return {"report_id": "r1", "status": "completed"}

        exe = Executor(
            dry_run=True,
            worker=FakeWorker(),
            contract_factory=FakeFactory(),
            validator_registry=reg,
        )
        env = self._make_delegation_envelope()
        result = exe.execute(env)
        assert result["pack_validations"][0]["valid"] is False
        assert "blocked by pack validator" in result["pack_validations"][0]["errors"]

    def test_pack_check_before_writeback_pass(self, tmp_path):
        reg = ValidatorRegistry()
        chk = _AlwaysPassCheck()
        reg.register_check("pre_wb", chk)

        engine = WritebackEngine(base_dir=tmp_path)
        exe = Executor(dry_run=False, writeback_engine=engine, validator_registry=reg)
        env = build_envelope("当前状态是什么")  # inform → applied → writeback
        result = exe.execute(env)
        assert chk.called is True
        assert "writeback_results" in result
        assert "writeback_blocked_by" not in result

    def test_pack_check_before_writeback_block(self, tmp_path):
        reg = ValidatorRegistry()
        reg.register_check("blocker", _BlockingCheck())

        engine = WritebackEngine(base_dir=tmp_path)
        exe = Executor(dry_run=False, writeback_engine=engine, validator_registry=reg)
        env = build_envelope("当前状态是什么")
        result = exe.execute(env)
        assert result.get("writeback_blocked_by") == "blocker"
        assert result.get("writeback_block_message") == "writeback not allowed"
        assert "writeback_results" not in result

    def test_trigger_dispatcher_standalone(self):
        """Trigger dispatcher works independently of executor."""
        td = TriggerDispatcher()
        calls = []

        class _Trigger:
            def handle(self, event):
                calls.append(event)
                return TriggerResult(handled=True)

        td.register("phase_complete", _Trigger())
        results = td.dispatch({"type": "phase_complete", "phase": "18"})
        assert len(results) == 1
        assert results[0].handled
        assert calls[0]["phase"] == "18"
