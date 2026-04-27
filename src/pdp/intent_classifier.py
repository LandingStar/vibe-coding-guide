"""Minimal rule-based intent classifier for the platform PDP."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..interfaces import (
    IMPACT_TABLE,
    KEYWORD_MAP,
    PLATFORM_INTENTS,
)

if TYPE_CHECKING:
    from ..pack.override_resolver import RuleConfig

# Backward-compat alias (was module-level private name before extraction)
_KEYWORD_MAP = KEYWORD_MAP

_CORRECTION_CUES = (
    "fix", "please fix", "patch", "repair", "correct", "adjust",
    "修复", "请修复", "修复这个", "修正", "改正", "修一下", "帮我改",
)
_ISSUE_REPORT_CUES = (
    "report", "issue", "raises", "raise", "exception", "attributeerror",
    "traceback", "stack trace", "typeerror", "keyerror", "incident",
    "报错", "导致", "不支持", "异常", "崩溃", "故障", "缺陷", "回归",
)


def classify(input_text: str, *, rule_config: RuleConfig | None = None) -> dict:
    """Classify an input string and return an intent classification result.

    Args:
        input_text: The user input to classify.
        rule_config: Optional RuleConfig from pack loader. When None,
            uses module-level hardcoded defaults.

    Returns a dict conforming to intent-classification-result.schema.json.
    """
    keyword_map = rule_config.keyword_map if rule_config else _KEYWORD_MAP
    impact_table = rule_config.impact_table if rule_config else IMPACT_TABLE

    text_lower = input_text.strip().lower()

    if not text_lower:
        return _make_result("unknown", "low", "Empty input.", impact_table=impact_table)

    scores: dict[str, int] = {}
    for intent, keywords in keyword_map.items():
        score = sum(1 for kw in keywords if kw in text_lower)
        if score > 0:
            scores[intent] = score

    if not scores:
        return _make_result("unknown", "low", "No keyword match found.", impact_table=impact_table)

    sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_intent, top_score = sorted_intents[0]

    if len(sorted_intents) > 1 and sorted_intents[1][1] == top_score:
        tied = {sorted_intents[0][0], sorted_intents[1][0]}
        if tied == {"correction", "issue-report"}:
            if any(cue in text_lower for cue in _CORRECTION_CUES):
                top_intent = "correction"
            elif any(cue in text_lower for cue in _ISSUE_REPORT_CUES):
                top_intent = "issue-report"
            else:
                top_intent = "correction"

        if top_intent != "ambiguous" and top_intent in tied:
            confidence = "high" if top_score >= 2 else "medium" if top_score == 1 else "low"

            if (rule_config and rule_config.platform_intents
                    and top_intent not in rule_config.platform_intents):
                return _make_result("unknown", "low",
                    f"Intent '{top_intent}' not in declared platform_intents.",
                    impact_table=impact_table)

            return _make_result(top_intent, confidence, impact_table=impact_table)

        alternatives = [
            {"intent": i, "confidence": "low"} for i, _ in sorted_intents[:3]
        ]
        return _make_result(
            "ambiguous", "low",
            f"Multiple intents matched equally: {[i for i, _ in sorted_intents[:3]]}",
            alternatives=alternatives,
            impact_table=impact_table,
        )

    confidence = "high" if top_score >= 2 else "medium" if top_score == 1 else "low"

    # If rule_config provides a platform_intents set, restrict result
    if (rule_config and rule_config.platform_intents
            and top_intent not in rule_config.platform_intents):
        return _make_result("unknown", "low",
            f"Intent '{top_intent}' not in declared platform_intents.",
            impact_table=impact_table)

    return _make_result(top_intent, confidence, impact_table=impact_table)


def _make_result(
    intent: str,
    confidence: str,
    explanation: str | None = None,
    alternatives: list[dict] | None = None,
    *,
    impact_table: dict[str, str] | None = None,
) -> dict:
    _impact = impact_table if impact_table is not None else IMPACT_TABLE
    high_impact = _impact.get(intent) == "high"
    result: dict = {
        "intent": intent,
        "confidence": confidence,
    }
    if explanation:
        result["explanation"] = explanation
    if high_impact:
        result["high_impact"] = True
    if alternatives:
        result["alternatives"] = alternatives
    return result
