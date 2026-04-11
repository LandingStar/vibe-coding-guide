"""Minimal gate resolver for the platform PDP."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .intent_classifier import IMPACT_TABLE

if TYPE_CHECKING:
    from ..pack.override_resolver import RuleConfig

_GATE_FOR_IMPACT: dict[str, str] = {
    "low": "inform",
    "medium": "review",
    "high": "approve",
}

_ENTRY_FOR_GATE: dict[str, str] = {
    "inform": "proposed",
    "review": "waiting_review",
    "approve": "waiting_review",
}


def resolve(intent_result: dict, *, rule_config: RuleConfig | None = None) -> dict:
    """Determine gate decision from an intent classification result.

    Returns a dict conforming to gate-decision-result.schema.json.
    """
    gate_for_impact = rule_config.gate_for_impact if rule_config else _GATE_FOR_IMPACT
    entry_for_gate = rule_config.entry_for_gate if rule_config else _ENTRY_FOR_GATE
    impact_table = rule_config.impact_table if rule_config else IMPACT_TABLE

    intent = intent_result.get("intent", "unknown")
    high_impact = intent_result.get("high_impact", False)

    impact = impact_table.get(intent, "medium")

    if high_impact:
        impact = "high"

    gate_level = gate_for_impact.get(impact, "review")

    if high_impact and gate_level == "inform":
        gate_level = "review"

    # Validate gate_level against allowed_gates (from pack merged_gates)
    if rule_config and rule_config.allowed_gates and gate_level not in rule_config.allowed_gates:
        # Fallback: pick highest available gate
        for fallback in ("approve", "review", "inform"):
            if fallback in rule_config.allowed_gates:
                gate_level = fallback
                break

    review_state_entry = entry_for_gate.get(gate_level, "waiting_review")

    rationale = (
        f"Intent '{intent}' has impact level '{impact}', "
        f"mapped to gate '{gate_level}'."
    )

    result: dict = {
        "gate_level": gate_level,
        "review_state_entry": review_state_entry,
        "rationale": rationale,
    }
    return result
