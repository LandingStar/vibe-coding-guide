"""Minimal delegation resolver for the platform PDP.

This resolver only produces a delegation decision result; it does NOT
invoke any subagent.  The actual delegation/contract generation is a
downstream concern that belongs to the PEP layer and future subagent
runtime (not yet designed).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..pack.override_resolver import RuleConfig

# Intents that typically benefit from delegation to a subagent.
_DELEGATABLE_INTENTS = {
    "correction",
    "constraint",
    "request-for-writeback",
    "issue-report",
}


def resolve(intent_result: dict, gate_decision: dict, *, rule_config: RuleConfig | None = None) -> dict | None:
    """Decide whether to delegate work to a subagent.

    Returns a dict conforming to delegation-decision-result.schema.json,
    or None if delegation analysis is not applicable (e.g. ``inform`` gate).
    """
    delegatable = rule_config.delegatable_intents if rule_config else _DELEGATABLE_INTENTS

    intent = intent_result.get("intent", "unknown")
    gate_level = gate_decision.get("gate_level", "review")

    # Fast-path: inform gate never triggers delegation in current rules.
    if gate_level == "inform":
        return None

    should_delegate = intent in delegatable

    if not should_delegate:
        return {
            "delegate": False,
            "rejection_reason": (
                f"Intent '{intent}' is not in the delegatable set; "
                "main agent handles directly."
            ),
        }

    # Build a delegation decision with contract hints.
    requires_review = gate_level == "approve"
    
    # Select collaboration mode (rule_config can override)
    mode = _select_mode(intent, gate_level, rule_config=rule_config)
    
    result: dict = {
        "delegate": True,
        "mode": mode,
        "scope_summary": f"Execute narrowly scoped work for intent '{intent}'.",
        "worker_only": mode == "supervisor-worker",
        "requires_review": requires_review or mode in ("handoff", "subgraph"),
        "allow_handoff": mode == "handoff",
        "rationale": (
            f"Intent '{intent}' is delegatable. "
            f"Gate '{gate_level}' determines review requirement. "
            f"Mode '{mode}' selected."
        ),
        "contract_hints": {
            "suggested_task": f"Handle '{intent}' as bounded worker.",
            "out_of_scope": [
                "Do not modify authoritative platform docs.",
                "Do not update global status boards.",
            ],
        },
    }
    if requires_review:
        result["review_gate_level"] = "approve"
    return result


def _select_mode(
    intent: str, gate_level: str, *, rule_config: RuleConfig | None = None,
) -> str:
    """Select collaboration mode based on intent, gate level, and pack rules.

    Priority:
    1. Explicit mode in rule_config.extra (pack can force a mode)
    2. Default: supervisor-worker
    """
    # Pack rules can override via extra config
    if rule_config and hasattr(rule_config, "extra"):
        explicit = rule_config.extra.get("collaboration_mode")
        if explicit in ("supervisor-worker", "handoff", "subgraph"):
            return explicit

    return "supervisor-worker"
