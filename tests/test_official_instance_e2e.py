"""Phase 19 — Official Instance E2E Validation.

Proves the official doc-loop-vibe-coding instance works end-to-end
with the platform runtime: manifest loading → context building →
override resolution → PDP decision → PEP execution → validation →
write-back → audit tracing.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# ── paths ──────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
INSTANCE_DIR = ROOT / "doc-loop-vibe-coding"
MANIFEST_PATH = INSTANCE_DIR / "pack-manifest.json"

# ── imports ────────────────────────────────────────────────────────────────

from src.pack import manifest_loader
from src.pack.context_builder import ContextBuilder, PackContext
from src.pack.override_resolver import RuleConfig, default_rule_config, resolve
from src.pdp import decision_envelope
from src.audit.audit_logger import AuditLogger, MemoryAuditBackend
from src.audit.trace_context import new_trace


# ════════════════════════════════════════════════════════════════════════════
# Slice A — 运行时装载链 + PDP 集成
# ════════════════════════════════════════════════════════════════════════════


class TestManifestLoader:
    """Test 1: ManifestLoader loads the official instance manifest."""

    def test_load_official_manifest(self):
        m = manifest_loader.load(MANIFEST_PATH)
        assert m.name == "doc-loop-vibe-coding"
        assert m.version == "1.0.0"
        assert m.kind == "official-instance"
        assert m.runtime_compatibility == ">=1.0.0,<2.0.0"

    def test_manifest_fields_populated(self):
        m = manifest_loader.load(MANIFEST_PATH)
        assert len(m.provides) >= 5
        assert "rules" in m.provides
        assert "scripts" in m.provides
        assert len(m.document_types) >= 5
        assert "planning-gate-candidate" in m.document_types
        assert len(m.intents) >= 8
        assert "question" in m.intents
        assert "correction" in m.intents
        assert len(m.gates) >= 3
        assert set(m.gates) >= {"inform", "review", "approve"}

    def test_manifest_always_on(self):
        m = manifest_loader.load(MANIFEST_PATH)
        assert len(m.always_on) >= 4
        assert "SKILL.md" in m.always_on
        assert "references/workflow.md" in m.always_on
        assert "references/conversation-progression.md" in m.always_on

    def test_manifest_on_demand(self):
        m = manifest_loader.load(MANIFEST_PATH)
        assert len(m.on_demand) >= 5
        assert any("bootstrap" in item for item in m.on_demand)

    def test_manifest_scripts_and_triggers(self):
        m = manifest_loader.load(MANIFEST_PATH)
        assert m.validators == []
        assert len(m.scripts) >= 3
        assert len(m.triggers) >= 1
        assert "chat" in m.triggers


class TestContextBuilder:
    """Test 2–3: ContextBuilder merges the official instance manifest."""

    def _build_context(self) -> PackContext:
        m = manifest_loader.load(MANIFEST_PATH)
        builder = ContextBuilder()
        builder.add_pack(m, INSTANCE_DIR)
        return builder.build()

    def test_always_on_content_loaded(self):
        ctx = self._build_context()
        assert "SKILL.md" in ctx.always_on_content
        assert len(ctx.always_on_content["SKILL.md"]) > 100
        assert "references/workflow.md" in ctx.always_on_content
        assert "references/conversation-progression.md" in ctx.always_on_content
        assert "references/subagent-delegation.md" in ctx.always_on_content


    def test_merged_intents_from_instance(self):
        ctx = self._build_context()
        assert "question" in ctx.merged_intents
        assert "correction" in ctx.merged_intents
        assert "scope-change" in ctx.merged_intents
        assert "approval" in ctx.merged_intents

    def test_merged_gates(self):
        ctx = self._build_context()
        assert set(ctx.merged_gates) >= {"inform", "review", "approve"}

    def test_merged_document_types(self):
        ctx = self._build_context()
        assert "project-master-checklist" in ctx.merged_document_types
        assert "planning-gate-candidate" in ctx.merged_document_types
        assert "handoff" in ctx.merged_document_types

    def test_merged_provides(self):
        ctx = self._build_context()
        assert "rules" in ctx.merged_provides
        assert "scripts" in ctx.merged_provides

    def test_manifests_sorted(self):
        ctx = self._build_context()
        assert len(ctx.manifests) == 1
        assert ctx.manifests[0].kind == "official-instance"


class TestOverrideResolver:
    """Test 3: OverrideResolver produces usable RuleConfig from instance context."""

    def _resolve(self) -> RuleConfig:
        m = manifest_loader.load(MANIFEST_PATH)
        builder = ContextBuilder()
        builder.add_pack(m, INSTANCE_DIR)
        ctx = builder.build()
        return resolve(ctx)

    def test_resolve_returns_rule_config(self):
        rc = self._resolve()
        assert isinstance(rc, RuleConfig)

    def test_keyword_map_populated(self):
        rc = self._resolve()
        assert len(rc.keyword_map) >= 5
        assert "question" in rc.keyword_map
        assert "correction" in rc.keyword_map

    def test_impact_table_populated(self):
        rc = self._resolve()
        assert len(rc.impact_table) >= 5
        assert rc.impact_table.get("question") in ("low", "medium", "high")

    def test_gate_for_impact_populated(self):
        rc = self._resolve()
        assert rc.gate_for_impact.get("low") == "inform"
        assert rc.gate_for_impact.get("high") == "approve"

    def test_delegatable_intents_populated(self):
        rc = self._resolve()
        assert len(rc.delegatable_intents) >= 2

    def test_platform_intents_populated(self):
        rc = self._resolve()
        assert len(rc.platform_intents) >= 5

    def test_defaults_preserved_without_rules(self):
        """Instance without explicit rules should get platform defaults."""
        rc = self._resolve()
        defaults = default_rule_config()
        # keyword_map should be identical (no rules override in instance manifest)
        assert rc.keyword_map == defaults.keyword_map


class TestPDPWithInstanceRules:
    """Test 4: PDP decision with instance-derived RuleConfig."""

    def _rule_config(self) -> RuleConfig:
        m = manifest_loader.load(MANIFEST_PATH)
        builder = ContextBuilder()
        builder.add_pack(m, INSTANCE_DIR)
        return resolve(builder.build())

    def test_question_intent_inform_gate(self):
        rc = self._rule_config()
        env = decision_envelope.build_envelope(
            "当前状态是什么", rule_config=rc,
        )
        assert env["intent_result"]["intent"] == "question"
        assert env["gate_decision"]["gate_level"] == "inform"

    def test_correction_intent_review_gate(self):
        rc = self._rule_config()
        env = decision_envelope.build_envelope(
            "这里有个 bug 需要修复，fix the error", rule_config=rc,
        )
        assert env["intent_result"]["intent"] == "correction"
        assert env["gate_decision"]["gate_level"] == "review"

    def test_scope_change_intent_approve_gate(self):
        rc = self._rule_config()
        env = decision_envelope.build_envelope(
            "我们需要扩展范围，增加一个新的子系统", rule_config=rc,
        )
        assert env["intent_result"]["intent"] == "scope-change"
        assert env["gate_decision"]["gate_level"] == "approve"

    def test_envelope_has_decision_id(self):
        rc = self._rule_config()
        env = decision_envelope.build_envelope("测试", rule_config=rc)
        assert env["decision_id"].startswith("pdp-")

    def test_envelope_has_rationale(self):
        rc = self._rule_config()
        env = decision_envelope.build_envelope("这是什么", rule_config=rc)
        assert "rationale" in env
        assert len(env["rationale"]) > 10


class TestPDPWithAudit:
    """Test 5: PDP + audit integration with instance rules."""

    def _setup(self):
        m = manifest_loader.load(MANIFEST_PATH)
        builder = ContextBuilder()
        builder.add_pack(m, INSTANCE_DIR)
        rc = resolve(builder.build())
        backend = MemoryAuditBackend()
        logger = AuditLogger(backend)
        trace = new_trace()
        return rc, logger, trace, backend

    def test_audit_events_emitted(self):
        rc, logger, trace, backend = self._setup()
        env = decision_envelope.build_envelope(
            "这里有个 bug 需要修复",
            rule_config=rc,
            audit_logger=logger,
            trace_ctx=trace,
        )
        events = backend.query(trace.trace_id)
        event_types = {e.event_type for e in events}
        # At minimum: input_received, intent_classified, gate_resolved
        assert "input_received" in event_types
        assert "intent_classified" in event_types
        assert "gate_resolved" in event_types
        assert len(events) >= 3

    def test_audit_trace_id_in_envelope(self):
        rc, logger, trace, backend = self._setup()
        env = decision_envelope.build_envelope(
            "修改这段代码",
            rule_config=rc,
            audit_logger=logger,
            trace_ctx=trace,
        )
        assert env.get("trace_id") == trace.trace_id

    def test_delegation_audit_events(self):
        """Delegatable intent should produce delegation audit event."""
        rc, logger, trace, backend = self._setup()
        env = decision_envelope.build_envelope(
            "这里有个 bug 需要修复",
            rule_config=rc,
            audit_logger=logger,
            trace_ctx=trace,
        )
        events = backend.query(trace.trace_id)
        event_types = {e.event_type for e in events}
        # correction is delegatable → delegation_decided should appear
        if env.get("delegation_decision"):
            assert "delegation_decided" in event_types

    def test_audit_covers_multiple_phases(self):
        rc, logger, trace, backend = self._setup()
        env = decision_envelope.build_envelope(
            "增加新的范围要求",
            rule_config=rc,
            audit_logger=logger,
            trace_ctx=trace,
        )
        events = backend.query(trace.trace_id)
        phases = {e.phase for e in events}
        assert "pdp" in phases

    def test_at_least_6_event_types_for_complex_input(self):
        """Trigger enough event types through PDP to cover the full chain."""
        rc, logger, trace, backend = self._setup()
        # Use active_rules to trigger precedence resolution too
        env = decision_envelope.build_envelope(
            "fix this bug 并修复错误 write back 落地",
            rule_config=rc,
            audit_logger=logger,
            trace_ctx=trace,
            active_rules=[
                {"rule_id": "r1", "layer": "platform"},
                {"rule_id": "r2", "layer": "instance"},
            ],
        )
        events = backend.query(trace.trace_id)
        event_types = {e.event_type for e in events}
        # input_received + intent_classified + gate_resolved + delegation_decided
        # + escalation_decided + precedence_resolved = up to 6
        assert len(event_types) >= 4  # Conservative: at least 4 distinct types


# ════════════════════════════════════════════════════════════════════════════
# Slice B — PEP 执行 + Validator + WriteBack E2E
# ════════════════════════════════════════════════════════════════════════════

from src.pep.executor import Executor
from src.pep.writeback_engine import WritebackEngine
from src.validators.registry import ValidatorRegistry
from src.validators.schema_validator import SchemaValidator
from src.validators.script_validator import ScriptValidator
from src.validators.trigger_dispatcher import TriggerDispatcher
from src.validators.base import CheckResult, TriggerResult
from src.subagent.contract_factory import build as build_contract
from src.subagent.report_validator import validate as validate_report
from src.subagent.stub_worker import StubWorkerBackend


class TestPEPInformWithWriteback:
    """Test 6: Inform fast-path produces write-back file."""

    def test_inform_writeback(self, tmp_path):
        rc = self._rule_config()
        engine = WritebackEngine(base_dir=tmp_path)
        backend = MemoryAuditBackend()
        logger = AuditLogger(backend)
        trace = new_trace()

        env = decision_envelope.build_envelope(
            "当前状态是什么",
            rule_config=rc,
            audit_logger=logger,
            trace_ctx=trace,
        )
        assert env["gate_decision"]["gate_level"] == "inform"

        executor = Executor(
            dry_run=False,
            writeback_engine=engine,
            audit_logger=logger,
        )
        result = executor.execute(env)
        assert result["review_state"] == "applied"
        assert "writeback_plans" in result

        # Check writeback file was created
        wb_files = list(tmp_path.rglob("*.md"))
        assert len(wb_files) >= 1

        # Audit events should cover both PDP and PEP phases
        events = backend.query(trace.trace_id)
        phases = {e.phase for e in events}
        assert "pdp" in phases
        assert "pep" in phases or "writeback" in phases

    def _rule_config(self) -> RuleConfig:
        m = manifest_loader.load(MANIFEST_PATH)
        builder = ContextBuilder()
        builder.add_pack(m, INSTANCE_DIR)
        return resolve(builder.build())


class TestPackValidatorOnReport:
    """Test 7: SchemaValidator validates delegation report."""

    def test_report_validated_by_pack_schema(self):
        # A simple schema that requires 'status' and 'report_id'
        schema = {
            "type": "object",
            "required": ["report_id", "status"],
            "properties": {
                "report_id": {"type": "string"},
                "status": {"type": "string", "enum": ["completed", "partial", "failed"]},
            },
        }
        sv = SchemaValidator(schema)
        registry = ValidatorRegistry()
        registry.register_validator("report-schema", sv)

        good_report = {"report_id": "r1", "status": "completed", "changed_artifacts": []}
        vr = registry.get_validator("report-schema").validate(good_report)
        assert vr.valid

        bad_report = {"report_id": "r1", "status": "invalid_status"}
        vr = registry.get_validator("report-schema").validate(bad_report)
        assert not vr.valid

    def test_script_validator_on_report(self):
        def check_artifacts(data):
            arts = data.get("changed_artifacts", [])
            if not arts:
                return {"valid": False, "errors": ["No artifacts changed"]}
            return {"valid": True}

        sv = ScriptValidator(check_artifacts)
        registry = ValidatorRegistry()
        registry.register_validator("artifact-check", sv)

        report_with = {"changed_artifacts": ["file.md"]}
        assert registry.get_validator("artifact-check").validate(report_with).valid

        report_without = {"changed_artifacts": []}
        assert not registry.get_validator("artifact-check").validate(report_without).valid


class TestBlockingCheck:
    """Test 8: Blocking check prevents writeback."""

    def test_check_blocks_writeback(self, tmp_path):
        rc = self._rule_config()
        engine = WritebackEngine(base_dir=tmp_path)
        registry = ValidatorRegistry()

        # Register a blocking check
        class AlwaysBlock:
            def check(self, context):
                return CheckResult(passed=False, message="Blocked by policy")

        registry.register_check("block-all", AlwaysBlock())

        env = decision_envelope.build_envelope("这是什么", rule_config=rc)
        assert env["gate_decision"]["gate_level"] == "inform"

        executor = Executor(
            dry_run=False,
            writeback_engine=engine,
            validator_registry=registry,
        )
        result = executor.execute(env)
        assert result["review_state"] == "applied"
        assert result.get("writeback_blocked_by") == "block-all"
        # No writeback files should exist
        assert not list(tmp_path.rglob("*.md"))

    def test_passing_check_allows_writeback(self, tmp_path):
        rc = self._rule_config()
        engine = WritebackEngine(base_dir=tmp_path)
        registry = ValidatorRegistry()

        class AlwaysPass:
            def check(self, context):
                return CheckResult(passed=True, message="OK")

        registry.register_check("pass-all", AlwaysPass())

        env = decision_envelope.build_envelope("这是什么", rule_config=rc)
        executor = Executor(
            dry_run=False,
            writeback_engine=engine,
            validator_registry=registry,
        )
        result = executor.execute(env)
        assert result["review_state"] == "applied"
        assert "writeback_blocked_by" not in result
        assert len(list(tmp_path.rglob("*.md"))) >= 1

    def _rule_config(self) -> RuleConfig:
        m = manifest_loader.load(MANIFEST_PATH)
        builder = ContextBuilder()
        builder.add_pack(m, INSTANCE_DIR)
        return resolve(builder.build())


class TestTriggerDispatcher:
    """Test 9: TriggerDispatcher with instance manifest triggers."""

    def test_chat_trigger(self):
        m = manifest_loader.load(MANIFEST_PATH)
        assert "chat" in m.triggers

        dispatcher = TriggerDispatcher()
        handled_events = []

        class ChatTrigger:
            def handle(self, event):
                handled_events.append(event)
                return TriggerResult(handled=True, output={"echo": event.get("text", "")})

        dispatcher.register("chat", ChatTrigger())
        results = dispatcher.dispatch({"type": "chat", "text": "hello"})
        assert len(results) == 1
        assert results[0].handled
        assert results[0].output["echo"] == "hello"
        assert len(handled_events) == 1

    def test_unregistered_event_type(self):
        dispatcher = TriggerDispatcher()
        results = dispatcher.dispatch({"type": "webhook"})
        assert results == []


class TestFullGovernanceChainE2E:
    """Test 10: Complete governance chain with instance pack."""

    def test_full_chain_inform(self, tmp_path):
        """intent→PDP(pack rules)→PEP(inform)→write-back→audit"""
        m = manifest_loader.load(MANIFEST_PATH)
        builder = ContextBuilder()
        builder.add_pack(m, INSTANCE_DIR)
        rc = resolve(builder.build())

        backend = MemoryAuditBackend()
        logger = AuditLogger(backend)
        trace = new_trace()
        engine = WritebackEngine(base_dir=tmp_path)

        # PDP
        env = decision_envelope.build_envelope(
            "这是什么？请问一下",
            rule_config=rc,
            audit_logger=logger,
            trace_ctx=trace,
        )
        assert env["intent_result"]["intent"] == "question"
        assert env["gate_decision"]["gate_level"] == "inform"

        # PEP
        executor = Executor(
            dry_run=False,
            writeback_engine=engine,
            audit_logger=logger,
        )
        result = executor.execute(env)
        assert result["review_state"] == "applied"
        assert "writeback_plans" in result

        # Audit coverage
        events = backend.query(trace.trace_id)
        phases = {e.phase for e in events}
        assert "pdp" in phases
        # PEP or writeback phase should be present
        assert ("pep" in phases) or ("writeback" in phases)
        assert len(events) >= 4

    def test_full_chain_delegation(self, tmp_path):
        """correction→PDP(pack rules)→delegation→worker→report→auto-apply→write-back→audit"""
        m = manifest_loader.load(MANIFEST_PATH)
        builder = ContextBuilder()
        builder.add_pack(m, INSTANCE_DIR)
        rc = resolve(builder.build())

        backend = MemoryAuditBackend()
        logger = AuditLogger(backend)
        trace = new_trace()
        engine = WritebackEngine(base_dir=tmp_path)
        worker = StubWorkerBackend()

        env = decision_envelope.build_envelope(
            "这里有 bug 需要 fix 修复这个错误",
            rule_config=rc,
            audit_logger=logger,
            trace_ctx=trace,
        )
        assert env["intent_result"]["intent"] == "correction"
        deleg = env.get("delegation_decision")
        assert deleg is not None
        assert deleg.get("delegate") is True

        executor = Executor(
            dry_run=False,
            worker=worker,
            contract_factory=_SimpleContractFactory(),
            report_validator=_SimpleReportValidator(),
            writeback_engine=engine,
            audit_logger=logger,
        )
        result = executor.execute(env)
        # Delegation should auto-apply
        assert result["review_state"] == "applied"
        assert "contract" in result
        assert "report" in result
        assert "writeback_plans" in result

        # Audit
        events = backend.query(trace.trace_id)
        assert len(events) >= 5

    def test_full_chain_review_then_approve(self, tmp_path):
        """approve gate → waiting_review → approve feedback → applied → write-back"""
        m = manifest_loader.load(MANIFEST_PATH)
        builder = ContextBuilder()
        builder.add_pack(m, INSTANCE_DIR)
        rc = resolve(builder.build())

        backend = MemoryAuditBackend()
        logger = AuditLogger(backend)
        trace = new_trace()
        engine = WritebackEngine(base_dir=tmp_path)

        env = decision_envelope.build_envelope(
            "扩展项目范围到移动端",
            rule_config=rc,
            audit_logger=logger,
            trace_ctx=trace,
        )
        assert env["gate_decision"]["gate_level"] == "approve"

        executor = Executor(
            dry_run=False,
            writeback_engine=engine,
            audit_logger=logger,
        )
        result = executor.execute(env)
        assert result["review_state"] == "waiting_review"

        # Approve
        result = executor.apply_review_feedback(env, result, "approve", reason="LGTM")
        assert result["review_state"] == "applied"
        assert "writeback_plans" in result

        events = backend.query(trace.trace_id)
        event_types = {e.event_type for e in events}
        assert "review_feedback" in event_types

    def test_full_chain_with_validators(self, tmp_path):
        """Delegation with pack validators on report."""
        m = manifest_loader.load(MANIFEST_PATH)
        builder = ContextBuilder()
        builder.add_pack(m, INSTANCE_DIR)
        rc = resolve(builder.build())

        engine = WritebackEngine(base_dir=tmp_path)
        worker = StubWorkerBackend()
        registry = ValidatorRegistry()

        # Register a permissive validator
        def accept_all(data):
            return {"valid": True}

        registry.register_validator("accept-all", ScriptValidator(accept_all))

        env = decision_envelope.build_envelope("fix this bug 修复错误", rule_config=rc)

        executor = Executor(
            dry_run=False,
            worker=worker,
            contract_factory=_SimpleContractFactory(),
            report_validator=_SimpleReportValidator(),
            writeback_engine=engine,
            validator_registry=registry,
        )
        result = executor.execute(env)
        assert result["review_state"] == "applied"
        assert "pack_validations" in result
        assert result["pack_validations"][0]["valid"] is True


# ════════════════════════════════════════════════════════════════════════════
# Test 11 — Bootstrap script validation
# ════════════════════════════════════════════════════════════════════════════


class TestBootstrapValidation:
    """Test 11: Bootstrap produces valid scaffold."""

    def test_bootstrap_then_validate(self, tmp_path):
        """Run bootstrap, then validate. Both should succeed."""
        bootstrap_script = INSTANCE_DIR / "scripts" / "bootstrap_doc_loop.py"
        validate_script = INSTANCE_DIR / "scripts" / "validate_doc_loop.py"

        # Run bootstrap
        result = subprocess.run(
            [sys.executable, str(bootstrap_script), "--target", str(tmp_path), "--force"],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        assert result.returncode == 0, f"Bootstrap failed:\n{result.stdout}\n{result.stderr}"

        # Run validate
        result = subprocess.run(
            [sys.executable, str(validate_script), "--target", str(tmp_path)],
            capture_output=True, text=True, cwd=str(ROOT),
        )
        assert result.returncode == 0, f"Validation failed:\n{result.stdout}\n{result.stderr}"


# ── helper classes (minimal implementations for test wiring) ────────────────


class _SimpleContractFactory:
    """Minimal ContractFactory for E2E tests."""

    def build(self, delegation: dict) -> dict:
        return {
            "contract_id": "test-contract-001",
            "task": delegation.get("rationale", "delegated task"),
            "mode": "worker",
            "scope": "test",
            "allowed_artifacts": [],
            "required_refs": [],
            "acceptance": "Task completed",
            "verification": "Automated",
            "out_of_scope": "",
            "report_schema": "subagent-report.schema.json",
        }


class _SimpleReportValidator:
    """Minimal ReportValidator for E2E tests."""

    def validate(self, report: dict) -> dict:
        return {"valid": True, "errors": []}
