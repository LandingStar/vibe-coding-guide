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


def resolve(
    rules: list[dict],
    *,
    rule_config: RuleConfig | None = None,
    override_declarations: dict[str, list[str]] | None = None,
) -> dict | None:
    """Resolve precedence among a list of rules.

    Each rule should be a dict with at least:
      - "rule_id": str
      - "layer": "platform" | "instance" | "project-local"

    When *override_declarations* is provided (pack_name → override
    targets), the result may contain ``explicit_override: True`` if the
    winning pack's overrides include any of the other evaluated packs.

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
    tie_broken = False
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
                else:
                    conflicts.append({
                        "rule_a": ra["rule_id"],
                        "rule_b": rb["rule_id"],
                        "resolution": (
                            f"same layer '{ra['layer']}': "
                            f"insertion order wins."
                        ),
                    })

        # Detect same-layer tie between winner and runner-up
        runner_up = sorted_rules[1]
        winner_priority = layer_priority.get(winner.get("layer", "platform"), 0)
        runner_priority = layer_priority.get(runner_up.get("layer", "platform"), 0)
        if winner_priority == runner_priority:
            tie_broken = True

    result: dict = {
        "evaluated_rules": evaluated,
        "winning_rule": winner["rule_id"],
        "adoption_layer": winner.get("layer", "platform"),
        "resolution_strategy": "adoption-layer-priority",
    }
    if tie_broken:
        result["tie_broken_by"] = "insertion_order"
    if conflicts:
        result["conflicts"] = conflicts

    # Check for explicit override declaration
    if override_declarations:
        winner_id = winner["rule_id"]
        other_ids = {r["rule_id"] for r in rules if r is not winner}
        # Find override targets declared by the winning pack
        winner_targets = set(override_declarations.get(winner_id, []))
        if winner_targets & other_ids:
            result["explicit_override"] = True
            result["resolution_strategy"] = "explicit-override adoption-layer-priority"

    return result
