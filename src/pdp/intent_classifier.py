"""Minimal rule-based intent classifier for the platform PDP."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..pack.override_resolver import RuleConfig

PLATFORM_INTENTS = {
    "question", "correction", "constraint", "scope-change",
    "protocol-change", "approval", "rejection",
    "request-for-writeback", "issue-report", "unknown", "ambiguous",
}

IMPACT_TABLE: dict[str, str] = {
    "question": "low",
    "correction": "medium",
    "constraint": "medium",
    "scope-change": "high",
    "protocol-change": "high",
    "approval": "medium",
    "rejection": "medium",
    "request-for-writeback": "medium",
    "issue-report": "medium",
}

_KEYWORD_MAP: dict[str, list[str]] = {
    "question": ["?", "what", "how", "why", "explain", "clarify",
                  "什么", "为什么", "怎么", "请问", "吗"],
    "approval": ["approve", "approved", "lgtm", "同意", "通过",
                 "审核通过", "批准"],
    "rejection": ["reject", "no", "denied", "拒绝", "不同意", "否决"],
    "correction": ["fix", "wrong", "error", "bug", "incorrect",
                   "修正", "错误", "修复"],
    "scope-change": ["scope", "expand", "change scope", "范围",
                     "扩展范围", "改变范围"],
    "protocol-change": ["protocol", "process", "workflow", "协议",
                        "流程", "规则"],
    "constraint": ["constraint", "must", "require", "约束", "要求",
                   "必须"],
    "request-for-writeback": ["write back", "writeback", "commit",
                              "save", "写回", "回写", "落地"],
    "issue-report": ["issue", "problem", "report", "问题", "报告"],
}


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
