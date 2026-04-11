"""Tests for pack runtime: ManifestLoader, ContextBuilder, OverrideResolver, PDP integration."""

from __future__ import annotations

import json
import os
import pytest
from pathlib import Path

from src.pack.manifest_loader import PackManifest, load, load_dict
from src.pack.context_builder import ContextBuilder, PackContext
from src.pack.override_resolver import RuleConfig, default_rule_config, resolve as override_resolve
from src.pdp import (
    intent_classifier,
    gate_resolver,
    delegation_resolver,
    escalation_resolver,
    precedence_resolver,
    decision_envelope,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def minimal_manifest_dict():
    return {"name": "test-pack", "version": "1.0.0", "kind": "project-local"}


@pytest.fixture
def full_manifest_dict():
    return {
        "name": "full-pack",
        "version": "2.0.0",
        "kind": "official-instance",
        "scope": "test scope",
        "provides": ["rules", "prompts"],
        "document_types": ["checklist", "phase-map"],
        "intents": ["question", "correction", "custom-intent"],
        "gates": ["inform", "review", "approve"],
        "always_on": ["README.md"],
        "on_demand": ["scripts/validate.py"],
        "depends_on": ["platform-core-defaults"],
        "overrides": [],
        "prompts": ["prompt1.md"],
        "templates": ["tmpl/"],
        "validators": ["val.py"],
        "checks": ["check.py"],
        "scripts": ["run.py"],
        "triggers": ["on-push"],
        "rules": {
            "keyword_map": {"custom-intent": ["custom", "特殊"]},
            "impact_table": {"custom-intent": "high"},
        },
    }


@pytest.fixture
def platform_manifest_dict():
    return {
        "name": "platform-core",
        "version": "1.0.0",
        "kind": "platform-default",
        "intents": ["question", "correction"],
        "gates": ["inform", "review"],
        "rules": {
            "impact_table": {"question": "low", "correction": "medium"},
        },
    }


# ===========================================================================
# ManifestLoader tests
# ===========================================================================


class TestManifestLoader:
    def test_load_minimal(self, minimal_manifest_dict):
        m = load_dict(minimal_manifest_dict)
        assert m.name == "test-pack"
        assert m.version == "1.0.0"
        assert m.kind == "project-local"
        assert m.intents == []
        assert m.rules == {}

    def test_load_full(self, full_manifest_dict):
        m = load_dict(full_manifest_dict)
        assert m.name == "full-pack"
        assert m.kind == "official-instance"
        assert "custom-intent" in m.intents
        assert m.rules["keyword_map"]["custom-intent"] == ["custom", "特殊"]

    def test_missing_required_fields(self):
        with pytest.raises(ValueError, match="Missing required fields"):
            load_dict({"name": "x"})

    def test_invalid_data_type(self):
        with pytest.raises(ValueError, match="must be a dict"):
            load_dict("not a dict")

    def test_load_from_file(self, tmp_path, full_manifest_dict):
        path = tmp_path / "pack-manifest.json"
        path.write_text(json.dumps(full_manifest_dict), encoding="utf-8")
        m = load(path)
        assert m.name == "full-pack"

    def test_load_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            load("/nonexistent/path.json")

    def test_load_invalid_json(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{invalid", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid JSON"):
            load(path)

    def test_load_official_instance_manifest(self):
        """Load the real doc-loop-vibe-coding pack manifest."""
        manifest_path = REPO_ROOT / "doc-loop-vibe-coding" / "pack-manifest.json"
        if not manifest_path.exists():
            pytest.skip("Official instance manifest not found")
        m = load(manifest_path)
        assert m.name == "doc-loop-vibe-coding"
        assert m.kind == "official-instance"
        assert len(m.intents) > 0
        assert len(m.always_on) > 0

    def test_optional_fields_default_empty(self):
        m = load_dict({"name": "x", "version": "1", "kind": "platform-default"})
        assert m.provides == []
        assert m.always_on == []
        assert m.rules == {}
        assert m.scope == ""


# ===========================================================================
# ContextBuilder tests
# ===========================================================================


class TestContextBuilder:
    def test_single_pack(self, full_manifest_dict, tmp_path):
        # Create an always_on file
        (tmp_path / "README.md").write_text("# Hello", encoding="utf-8")

        m = load_dict(full_manifest_dict)
        builder = ContextBuilder()
        builder.add_pack(m, tmp_path)
        ctx = builder.build()

        assert len(ctx.manifests) == 1
        assert ctx.manifests[0].name == "full-pack"
        assert "README.md" in ctx.always_on_content
        assert ctx.always_on_content["README.md"] == "# Hello"

    def test_multi_layer_ordering(self, platform_manifest_dict, full_manifest_dict, minimal_manifest_dict, tmp_path):
        builder = ContextBuilder()
        builder.add_pack(load_dict(minimal_manifest_dict), tmp_path)  # project-local
        builder.add_pack(load_dict(platform_manifest_dict), tmp_path)  # platform
        builder.add_pack(load_dict(full_manifest_dict), tmp_path)  # instance

        ctx = builder.build()
        kinds = [m.kind for m in ctx.manifests]
        assert kinds == ["platform-default", "official-instance", "project-local"]

    def test_merged_intents_deduplicated(self, platform_manifest_dict, full_manifest_dict, tmp_path):
        builder = ContextBuilder()
        builder.add_pack(load_dict(platform_manifest_dict), tmp_path)
        builder.add_pack(load_dict(full_manifest_dict), tmp_path)
        ctx = builder.build()

        # "question" and "correction" appear in both, should be deduplicated
        assert ctx.merged_intents.count("question") == 1
        assert "custom-intent" in ctx.merged_intents

    def test_missing_always_on_file_skipped(self, tmp_path):
        m = load_dict({
            "name": "x", "version": "1", "kind": "platform-default",
            "always_on": ["nonexistent.md"],
        })
        builder = ContextBuilder()
        builder.add_pack(m, tmp_path)
        ctx = builder.build()
        assert ctx.always_on_content == {}

    def test_rules_deep_merge(self, tmp_path):
        m1 = load_dict({
            "name": "base", "version": "1", "kind": "platform-default",
            "rules": {"impact_table": {"question": "low"}, "nested": {"a": 1}},
        })
        m2 = load_dict({
            "name": "overlay", "version": "1", "kind": "project-local",
            "rules": {"impact_table": {"custom": "high"}, "nested": {"b": 2}},
        })
        builder = ContextBuilder()
        builder.add_pack(m1, tmp_path)
        builder.add_pack(m2, tmp_path)
        ctx = builder.build()

        assert ctx.merged_rules["impact_table"]["question"] == "low"
        assert ctx.merged_rules["impact_table"]["custom"] == "high"
        assert ctx.merged_rules["nested"] == {"a": 1, "b": 2}

    def test_empty_builder(self):
        ctx = ContextBuilder().build()
        assert ctx.manifests == []
        assert ctx.merged_intents == []

    def test_load_official_instance_context(self):
        """Build context from the real official instance pack."""
        pack_dir = REPO_ROOT / "doc-loop-vibe-coding"
        manifest_path = pack_dir / "pack-manifest.json"
        if not manifest_path.exists():
            pytest.skip("Official instance manifest not found")
        m = load(manifest_path)
        builder = ContextBuilder()
        builder.add_pack(m, pack_dir)
        ctx = builder.build()

        assert len(ctx.manifests) == 1
        # always_on files should be loadable
        assert len(ctx.always_on_content) > 0


# ===========================================================================
# OverrideResolver tests
# ===========================================================================


class TestOverrideResolver:
    def test_default_rule_config_matches_hardcoded(self):
        rc = default_rule_config()
        # Verify key fields match module-level constants
        assert rc.gate_for_impact == {"low": "inform", "medium": "review", "high": "approve"}
        assert rc.entry_for_gate == {"inform": "proposed", "review": "waiting_review", "approve": "waiting_review"}
        assert "correction" in rc.delegatable_intents
        assert rc.low_confidence_set == {"low", "unknown"}
        assert rc.layer_priority["project-local"] == 2

    def test_resolve_with_empty_context(self, tmp_path):
        ctx = ContextBuilder().build()
        rc = override_resolve(ctx)
        default = default_rule_config()
        assert rc.gate_for_impact == default.gate_for_impact
        assert rc.delegatable_intents == default.delegatable_intents

    def test_keyword_map_extension(self, tmp_path):
        m = load_dict({
            "name": "x", "version": "1", "kind": "project-local",
            "rules": {
                "keyword_map": {
                    "question": ["extra-keyword"],
                    "new-intent": ["new1", "new2"],
                },
            },
        })
        builder = ContextBuilder()
        builder.add_pack(m, tmp_path)
        ctx = builder.build()
        rc = override_resolve(ctx)

        assert "extra-keyword" in rc.keyword_map["question"]
        assert "?" in rc.keyword_map["question"]  # original preserved
        assert rc.keyword_map["new-intent"] == ["new1", "new2"]

    def test_impact_table_override(self, tmp_path):
        m = load_dict({
            "name": "x", "version": "1", "kind": "project-local",
            "rules": {"impact_table": {"question": "high", "custom": "medium"}},
        })
        builder = ContextBuilder()
        builder.add_pack(m, tmp_path)
        rc = override_resolve(builder.build())

        assert rc.impact_table["question"] == "high"  # overridden
        assert rc.impact_table["custom"] == "medium"  # new
        assert rc.impact_table["correction"] == "medium"  # original preserved

    def test_delegatable_intents_replace(self, tmp_path):
        m = load_dict({
            "name": "x", "version": "1", "kind": "project-local",
            "rules": {"delegatable_intents": ["correction", "custom-intent"]},
        })
        builder = ContextBuilder()
        builder.add_pack(m, tmp_path)
        rc = override_resolve(builder.build())

        assert rc.delegatable_intents == {"correction", "custom-intent"}
        assert "constraint" not in rc.delegatable_intents  # removed

    def test_gate_for_impact_override(self, tmp_path):
        m = load_dict({
            "name": "x", "version": "1", "kind": "project-local",
            "rules": {"gate_for_impact": {"low": "review"}},  # override: low→review instead of inform
        })
        builder = ContextBuilder()
        builder.add_pack(m, tmp_path)
        rc = override_resolve(builder.build())

        assert rc.gate_for_impact["low"] == "review"
        assert rc.gate_for_impact["medium"] == "review"  # original preserved


# ===========================================================================
# PDP Integration with RuleConfig tests
# ===========================================================================


class TestPDPWithRuleConfig:
    """Verify PDP resolvers work correctly with custom RuleConfig."""

    def test_intent_classifier_custom_keywords(self):
        rc = default_rule_config()
        rc.keyword_map["deploy"] = ["deploy", "部署", "发布"]
        rc.impact_table["deploy"] = "high"
        rc.platform_intents.add("deploy")

        result = intent_classifier.classify("请部署到生产环境", rule_config=rc)
        assert result["intent"] == "deploy"
        assert result.get("high_impact") is True

    def test_intent_classifier_without_rule_config(self):
        """Backward compat: None rule_config uses defaults."""
        result = intent_classifier.classify("what is this?")
        assert result["intent"] == "question"

    def test_gate_resolver_custom_mapping(self):
        rc = default_rule_config()
        rc.gate_for_impact["low"] = "review"  # all questions need review

        intent_result = {"intent": "question", "confidence": "high"}
        gate = gate_resolver.resolve(intent_result, rule_config=rc)
        assert gate["gate_level"] == "review"

    def test_gate_resolver_without_rule_config(self):
        intent_result = {"intent": "question", "confidence": "high"}
        gate = gate_resolver.resolve(intent_result)
        assert gate["gate_level"] == "inform"

    def test_delegation_resolver_custom_set(self):
        rc = default_rule_config()
        rc.delegatable_intents = {"question", "custom"}

        intent_result = {"intent": "question", "confidence": "high"}
        gate_decision = {"gate_level": "review"}
        deleg = delegation_resolver.resolve(intent_result, gate_decision, rule_config=rc)
        assert deleg is not None
        assert deleg["delegate"] is True

    def test_delegation_resolver_without_rule_config(self):
        intent_result = {"intent": "question", "confidence": "high"}
        gate_decision = {"gate_level": "review"}
        deleg = delegation_resolver.resolve(intent_result, gate_decision)
        assert deleg is not None
        assert deleg["delegate"] is False  # question not in default delegatable set

    def test_escalation_resolver_custom_confidence(self):
        rc = default_rule_config()
        rc.low_confidence_set = {"low"}  # remove "unknown" from low confidence

        intent_result = {"intent": "unknown", "confidence": "unknown"}
        gate_decision = {"gate_level": "review"}
        esc = escalation_resolver.resolve(intent_result, gate_decision, rule_config=rc)
        # "unknown" confidence not in low_confidence_set, but "unresolved_intent" still triggers
        assert esc["escalate"] is True
        assert "unresolved_intent" in esc.get("reason", "")

    def test_precedence_resolver_custom_layers(self):
        rc = default_rule_config()
        rc.layer_priority["organization"] = 3  # new layer above project-local

        rules = [
            {"rule_id": "r1", "layer": "project-local"},
            {"rule_id": "r2", "layer": "organization"},
        ]
        result = precedence_resolver.resolve(rules, rule_config=rc)
        assert result["winning_rule"] == "r2"
        assert result["adoption_layer"] == "organization"

    def test_envelope_with_rule_config(self):
        rc = default_rule_config()
        rc.keyword_map["deploy"] = ["deploy", "部署"]
        rc.impact_table["deploy"] = "high"
        rc.platform_intents.add("deploy")
        rc.delegatable_intents.add("deploy")

        envelope = decision_envelope.build_envelope(
            "请部署新版本", rule_config=rc
        )
        assert envelope["intent_result"]["intent"] == "deploy"
        assert envelope["gate_decision"]["gate_level"] == "approve"
        assert envelope.get("delegation_decision", {}).get("delegate") is True

    def test_envelope_without_rule_config(self):
        """Backward compat: no rule_config produces same results as before."""
        envelope = decision_envelope.build_envelope("what is this?")
        assert envelope["intent_result"]["intent"] == "question"
        assert envelope["gate_decision"]["gate_level"] == "inform"


# ===========================================================================
# End-to-end: Pack → Context → RuleConfig → PDP
# ===========================================================================


class TestPackToPDP:
    """Full pipeline: load pack manifest → build context → resolve rules → PDP."""

    def test_custom_pack_changes_classification(self, tmp_path):
        manifest = {
            "name": "custom-project",
            "version": "1.0.0",
            "kind": "project-local",
            "intents": ["deploy"],
            "rules": {
                "keyword_map": {"deploy": ["deploy", "部署", "发布"]},
                "impact_table": {"deploy": "high"},
                "delegatable_intents": ["correction", "deploy"],
            },
        }
        path = tmp_path / "pack-manifest.json"
        path.write_text(json.dumps(manifest), encoding="utf-8")

        m = load(path)
        builder = ContextBuilder()
        builder.add_pack(m, tmp_path)
        ctx = builder.build()
        rc = override_resolve(ctx)

        # Classify with custom rules
        result = intent_classifier.classify("请部署到生产环境", rule_config=rc)
        assert result["intent"] == "deploy"

        # Gate should be approve (high impact)
        gate = gate_resolver.resolve(result, rule_config=rc)
        assert gate["gate_level"] == "approve"

        # Delegation should work for deploy
        deleg = delegation_resolver.resolve(result, gate, rule_config=rc)
        assert deleg["delegate"] is True

    def test_multi_layer_pack_override(self, tmp_path):
        platform = load_dict({
            "name": "platform",
            "version": "1.0.0",
            "kind": "platform-default",
            "rules": {"impact_table": {"question": "low"}},
        })
        project = load_dict({
            "name": "project",
            "version": "1.0.0",
            "kind": "project-local",
            "rules": {"impact_table": {"question": "high"}},  # override: question is high impact
        })

        builder = ContextBuilder()
        builder.add_pack(platform, tmp_path)
        builder.add_pack(project, tmp_path)
        ctx = builder.build()
        rc = override_resolve(ctx)

        # Project override wins
        assert rc.impact_table["question"] == "high"

        result = intent_classifier.classify("what is this?", rule_config=rc)
        assert result["intent"] == "question"
        assert result.get("high_impact") is True

    def test_official_instance_full_pipeline(self):
        """Load official instance → build context → resolve rules → classify."""
        pack_dir = REPO_ROOT / "doc-loop-vibe-coding"
        manifest_path = pack_dir / "pack-manifest.json"
        if not manifest_path.exists():
            pytest.skip("Official instance manifest not found")

        m = load(manifest_path)
        builder = ContextBuilder()
        builder.add_pack(m, pack_dir)
        ctx = builder.build()
        rc = override_resolve(ctx)

        # Should still classify normally with official instance rules
        result = intent_classifier.classify("what is this?", rule_config=rc)
        assert result["intent"] == "question"

        envelope = decision_envelope.build_envelope("fix this bug please", rule_config=rc)
        assert envelope["intent_result"]["intent"] == "correction"
