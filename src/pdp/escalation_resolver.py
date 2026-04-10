"""Minimal escalation resolver for the platform PDP.

Evaluates platform-level trigger conditions to determine whether the
current decision should be escalated to a higher authority.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..pack.override_resolver import RuleConfig

# Trigger conditions mapped from docs/escalation-decision.md
_LOW_CONFIDENCE = {"low", "unknown"}


def resolve(intent_result: dict, gate_decision: dict, *, rule_config: RuleConfig | None = None) -> dict | None:
    """Decide whether escalation to a higher authority is needed.

    Returns a dict conforming to escalation-decision-result.schema.json,
    or None if escalation analysis is not triggered.
    """
    low_confidence_set = rule_config.low_confidence_set if rule_config else _LOW_CONFIDENCE

    triggers: list[str] = []

    confidence = intent_result.get("confidence", "high")
    if confidence in low_confidence_set:
        triggers.append("low_confidence_classification")

    high_impact = intent_result.get("high_impact", False)
    gate_level = gate_decision.get("gate_level", "review")

    if high_impact:
        triggers.append("high_impact_intent")

    if gate_level == "approve":
        triggers.append("approve_gate_hit")

    intent = intent_result.get("intent", "unknown")
    if intent in ("unknown", "ambiguous"):
        triggers.append("unresolved_intent")

    if not triggers:
        return {"escalate": False}

    # Determine target: human_reviewer for approve gate or high impact,
    # main_agent for low confidence or unresolved intent.
    if "approve_gate_hit" in triggers or "high_impact_intent" in triggers:
        target = "human_reviewer"
    else:
        target = "main_agent"

    return {
        "escalate": True,
        "reason": f"Triggered by: {', '.join(triggers)}.",
        "target_authority": target,
        "triggering_condition": triggers[0],
        "context_summary": (
            f"Intent='{intent}', confidence='{confidence}', "
            f"gate='{gate_level}'."
        ),
    }
