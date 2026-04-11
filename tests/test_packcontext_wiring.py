"""Tests for Phase 23: PackContext downstream wiring.

Verifies that merged_intents and merged_gates from PackContext
actually influence PDP behavior through RuleConfig.
"""

from __future__ import annotations

import pytest

from src.pack.context_builder import ContextBuilder, PackContext
from src.pack.manifest_loader import load_dict
from src.pack.override_resolver import RuleConfig, default_rule_config, resolve
from src.pdp import gate_resolver, intent_classifier


# ── Helpers ──────────────────────────────────────────────────────────────


def _manifest(**overrides):
    base = {"name": "test", "version": "1.0", "kind": "official-instance"}
    base.update(overrides)
    return load_dict(base)


def _build_context(*manifests):
    builder = ContextBuilder()
    for m in manifests:
        builder.add_pack(m, ".")
    return builder.build()


# ── Slice C: OverrideResolver wiring ─────────────────────────────────────


class TestOverrideResolverWiring:
    def test_merged_intents_injected_into_platform_intents(self):
        """merged_intents should be unioned into RuleConfig.platform_intents."""
        m = _manifest(intents=["question", "custom-intent-x"])
        ctx = _build_context(m)
        rc = resolve(ctx)
        assert "custom-intent-x" in rc.platform_intents
        assert "question" in rc.platform_intents

    def test_merged_gates_injected_into_allowed_gates(self):
        """merged_gates should populate RuleConfig.allowed_gates."""
        m = _manifest(gates=["inform", "review"])
        ctx = _build_context(m)
        rc = resolve(ctx)
        assert rc.allowed_gates == {"inform", "review"}

    def test_no_merged_intents_keeps_defaults(self):
        """When pack declares no intents, platform defaults remain."""
        m = _manifest()
        ctx = _build_context(m)
        rc = resolve(ctx)
        # Should have at least the default intents
        assert "question" in rc.platform_intents
        assert "unknown" in rc.platform_intents

    def test_no_merged_gates_empty_allowed(self):
        """When pack declares no gates, allowed_gates stays empty."""
        m = _manifest()
        ctx = _build_context(m)
        rc = resolve(ctx)
        assert rc.allowed_gates == set()

    def test_multi_pack_intents_merged(self):
        """Multiple packs' intents should be unioned."""
        m1 = _manifest(name="p1", intents=["question", "custom-a"])
        m2 = _manifest(name="p2", intents=["question", "custom-b"], kind="project-local")
        ctx = _build_context(m1, m2)
        rc = resolve(ctx)
        assert "custom-a" in rc.platform_intents
        assert "custom-b" in rc.platform_intents
        assert "question" in rc.platform_intents


# ── Slice A: intent_classifier respects platform_intents ─────────────────


class TestIntentClassifierWithPlatformIntents:
    def test_known_intent_passes(self):
        """Intent in platform_intents should be classified normally."""
        rc = default_rule_config()
        result = intent_classifier.classify("what is this?", rule_config=rc)
        assert result["intent"] == "question"

    def test_custom_keyword_intent_passes(self):
        """Intent added to keyword_map AND platform_intents should work."""
        rc = default_rule_config()
        rc.keyword_map["deploy"] = ["deploy", "部署"]
        rc.impact_table["deploy"] = "high"
        rc.platform_intents.add("deploy")
        result = intent_classifier.classify("请部署到生产环境", rule_config=rc)
        assert result["intent"] == "deploy"

    def test_restricted_intent_set(self):
        """When platform_intents is restricted, non-keyword intents fall to unknown."""
        rc = default_rule_config()
        # If we remove "question" from both keyword_map and platform_intents,
        # and add a custom keyword that maps to a non-declared intent...
        # Actually test: classify with a very narrow platform_intents
        rc.platform_intents = {"correction", "unknown"}
        # Classify something as "question" → should become unknown
        result = intent_classifier.classify("what is this?", rule_config=rc)
        assert result["intent"] == "unknown"

    def test_no_rule_config_uses_defaults(self):
        """rule_config=None should use hardcoded defaults (backward compat)."""
        result = intent_classifier.classify("what is this?")
        assert result["intent"] == "question"

    def test_pack_declared_intent_recognized(self):
        """Full integration: pack declares custom intent → classifier recognizes it."""
        m = _manifest(
            intents=["question", "deploy", "unknown"],
            rules={
                "keyword_map": {
                    "deploy": ["deploy", "部署", "发布"],
                },
                "impact_table": {
                    "deploy": "high",
                },
            },
        )
        ctx = _build_context(m)
        rc = resolve(ctx)
        result = intent_classifier.classify("请部署到生产", rule_config=rc)
        assert result["intent"] == "deploy"
        assert result.get("high_impact") is True


# ── Slice B: gate_resolver respects allowed_gates ────────────────────────


class TestGateResolverWithAllowedGates:
    def test_gate_in_allowed_set_passes(self):
        """Gate in allowed_gates should be used as-is."""
        rc = default_rule_config()
        rc.allowed_gates = {"inform", "review", "approve"}
        result = gate_resolver.resolve(
            {"intent": "question", "confidence": "high"}, rule_config=rc
        )
        assert result["gate_level"] == "inform"

    def test_gate_not_in_allowed_set_fallback(self):
        """Gate not in allowed_gates should fallback to highest available."""
        rc = default_rule_config()
        rc.allowed_gates = {"inform", "review"}  # no approve
        # scope-change → high impact → approve → should fallback to review
        result = gate_resolver.resolve(
            {"intent": "scope-change", "confidence": "high", "high_impact": True},
            rule_config=rc,
        )
        assert result["gate_level"] == "review"

    def test_only_inform_gate(self):
        """When only inform is allowed, everything falls back to inform."""
        rc = default_rule_config()
        rc.allowed_gates = {"inform"}
        result = gate_resolver.resolve(
            {"intent": "scope-change", "confidence": "high", "high_impact": True},
            rule_config=rc,
        )
        assert result["gate_level"] == "inform"

    def test_empty_allowed_gates_no_restriction(self):
        """Empty allowed_gates means no restriction (backward compat)."""
        rc = default_rule_config()
        rc.allowed_gates = set()
        result = gate_resolver.resolve(
            {"intent": "scope-change", "confidence": "high", "high_impact": True},
            rule_config=rc,
        )
        assert result["gate_level"] == "approve"

    def test_no_rule_config_no_restriction(self):
        """rule_config=None uses defaults with no gate restriction."""
        result = gate_resolver.resolve(
            {"intent": "scope-change", "confidence": "high", "high_impact": True}
        )
        assert result["gate_level"] == "approve"

    def test_pack_declared_gates_enforced(self):
        """Full integration: pack declares gates=["inform","review"] → approve fallback to review."""
        m = _manifest(gates=["inform", "review"])
        ctx = _build_context(m)
        rc = resolve(ctx)
        result = gate_resolver.resolve(
            {"intent": "scope-change", "confidence": "high", "high_impact": True},
            rule_config=rc,
        )
        assert result["gate_level"] == "review"


# ── Integration: Pipeline-level ──────────────────────────────────────────


class TestPipelineIntegration:
    def test_pipeline_passes_pack_intents_to_pdp(self):
        """Pipeline should wire PackContext intents through RuleConfig to PDP."""
        from src.workflow.pipeline import Pipeline
        from pathlib import Path

        root = Path(__file__).parent.parent
        pipeline = Pipeline.from_project(root, dry_run=True, audit=False)

        # RuleConfig should contain intents from the official-instance pack
        rc = pipeline.rule_config
        expected_intents = {
            "question", "correction", "constraint", "scope-change",
            "protocol-change", "approval", "rejection",
            "request-for-writeback", "issue-report", "unknown",
        }
        for intent in expected_intents:
            assert intent in rc.platform_intents, f"Missing intent: {intent}"

    def test_pipeline_passes_pack_gates_to_pdp(self):
        """Pipeline should wire PackContext gates through RuleConfig."""
        from src.workflow.pipeline import Pipeline
        from pathlib import Path

        root = Path(__file__).parent.parent
        pipeline = Pipeline.from_project(root, dry_run=True, audit=False)
        rc = pipeline.rule_config
        assert "inform" in rc.allowed_gates
        assert "review" in rc.allowed_gates
        assert "approve" in rc.allowed_gates
