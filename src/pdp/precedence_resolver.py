"""Minimal precedence resolver for the platform PDP.

Evaluates a set of rule identifiers and determines which rule wins
based on the platform's three-layer adoption hierarchy:
  platform < instance < project-local
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..pack.override_resolver import RuleConfig

_LAYER_PRIORITY = {
    "platform": 0,
    "instance": 1,
    "project-local": 2,
}


def resolve(rules: list[dict], *, rule_config: RuleConfig | None = None) -> dict | None:
    """Resolve precedence among a list of rules.

    Each rule should be a dict with at least:
      - "rule_id": str
      - "layer": "platform" | "instance" | "project-local"

    Returns a dict conforming to precedence-resolution-result.schema.json,
    or None if there are no rules to evaluate.
    """
    layer_priority = rule_config.layer_priority if rule_config else _LAYER_PRIORITY
    if not rules:
        return None

    evaluated = [r["rule_id"] for r in rules]
    sorted_rules = sorted(
        rules,
        key=lambda r: layer_priority.get(r.get("layer", "platform"), 0),
        reverse=True,
    )
    winner = sorted_rules[0]

    conflicts: list[dict] = []
    if len(rules) > 1:
        for i, ra in enumerate(rules):
            for rb in rules[i + 1:]:
                if ra["layer"] != rb["layer"]:
                    conflicts.append({
                        "rule_a": ra["rule_id"],
                        "rule_b": rb["rule_id"],
                        "resolution": (
                            f"'{ra['layer']}' vs '{rb['layer']}': "
                            f"higher-layer rule wins."
                        ),
                    })

    result: dict = {
        "evaluated_rules": evaluated,
        "winning_rule": winner["rule_id"],
        "adoption_layer": winner.get("layer", "platform"),
        "resolution_strategy": "adoption-layer-priority",
    }
    if conflicts:
        result["conflicts"] = conflicts
    return result
