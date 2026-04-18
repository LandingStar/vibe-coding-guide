"""Override resolver — merge pack rules into a consumable RuleConfig."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .context_builder import PackContext
from ..pdp.tool_permission_resolver import ToolPermissionConfig, parse_tool_permissions


@dataclass
class RuleConfig:
    """Unified rule configuration consumed by PDP resolvers.

    Each field corresponds to a hardcoded table in a resolver.
    When a pack does not override a field, the platform default is used.
    """

    # intent_classifier
    keyword_map: dict[str, list[str]] = field(default_factory=dict)
    impact_table: dict[str, str] = field(default_factory=dict)
    platform_intents: set[str] = field(default_factory=set)

    # gate_resolver
    gate_for_impact: dict[str, str] = field(default_factory=dict)
    entry_for_gate: dict[str, str] = field(default_factory=dict)
    allowed_gates: set[str] = field(default_factory=set)

    # delegation_resolver
    delegatable_intents: set[str] = field(default_factory=set)
    available_capabilities: list[str] = field(default_factory=list)

    # escalation_resolver
    low_confidence_set: set[str] = field(default_factory=set)

    # precedence_resolver
    layer_priority: dict[str, int] = field(default_factory=dict)

    # tool_permission_resolver (B-REF-4)
    tool_permissions: ToolPermissionConfig = field(default_factory=ToolPermissionConfig)

    # extra: pack-specific extensions (e.g. collaboration_mode)
    extra: dict[str, object] = field(default_factory=dict)


def default_rule_config() -> RuleConfig:
    """Return the platform default RuleConfig matching current hardcoded values."""
    from ..pdp import intent_classifier as ic

    return RuleConfig(
        keyword_map=dict(ic._KEYWORD_MAP),
        impact_table=dict(ic.IMPACT_TABLE),
        platform_intents=set(ic.PLATFORM_INTENTS),
        gate_for_impact={"low": "inform", "medium": "review", "high": "approve"},
        entry_for_gate={
            "inform": "proposed",
            "review": "waiting_review",
            "approve": "waiting_review",
        },
        delegatable_intents={
            "correction",
            "constraint",
            "request-for-writeback",
            "issue-report",
        },
        low_confidence_set={"low", "unknown"},
        layer_priority={"platform": 0, "instance": 1, "project-local": 2},
    )


def resolve(context: PackContext) -> RuleConfig:
    """Build a RuleConfig by merging pack rules over platform defaults.

    The merged_rules dict from PackContext may contain keys matching
    RuleConfig field names. Each key is applied as an override.
    Also wires merged_intents/merged_gates from PackContext into RuleConfig.
    """
    config = default_rule_config()

    # ── Wire PackContext merged fields into RuleConfig ────────────────
    # These apply regardless of whether merged_rules is empty.
    if context.merged_intents:
        config.platform_intents.update(context.merged_intents)
    if context.merged_gates:
        config.allowed_gates = set(context.merged_gates)
    if context.merged_provides:
        config.available_capabilities = list(context.merged_provides)

    rules = context.merged_rules
    if not rules:
        return config

    # Override keyword_map (merge: add new intents, extend existing keyword lists)
    if "keyword_map" in rules:
        for intent, keywords in rules["keyword_map"].items():
            if intent in config.keyword_map:
                # Extend existing keyword list (deduplicate)
                existing = set(config.keyword_map[intent])
                config.keyword_map[intent].extend(
                    kw for kw in keywords if kw not in existing
                )
            else:
                config.keyword_map[intent] = list(keywords)

    # Override impact_table (merge: add/overwrite entries)
    if "impact_table" in rules:
        config.impact_table.update(rules["impact_table"])

    # Override platform_intents (union)
    if "platform_intents" in rules:
        config.platform_intents.update(rules["platform_intents"])

    # Override gate_for_impact (merge)
    if "gate_for_impact" in rules:
        config.gate_for_impact.update(rules["gate_for_impact"])

    # Override entry_for_gate (merge)
    if "entry_for_gate" in rules:
        config.entry_for_gate.update(rules["entry_for_gate"])

    # Override delegatable_intents (replace if provided)
    if "delegatable_intents" in rules:
        config.delegatable_intents = set(rules["delegatable_intents"])

    # Override low_confidence_set (replace if provided)
    if "low_confidence_set" in rules:
        config.low_confidence_set = set(rules["low_confidence_set"])

    # Override layer_priority (merge)
    if "layer_priority" in rules:
        config.layer_priority.update(
            {k: int(v) for k, v in rules["layer_priority"].items()}
        )

    # Override tool_permissions (parse from raw dict)
    if "tool_permissions" in rules:
        config.tool_permissions = parse_tool_permissions(rules["tool_permissions"])

    return config
