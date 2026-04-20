"""Reply progression checker — validates AI reply endings.

Checks whether a reply's ending conforms to the conversation progression
contract: must end with AI's own analysis/judgment followed by a
forward-driving question (not yes/no, not passive waiting).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# Patterns indicating forbidden ending styles
_FORBIDDEN_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("pure_confirmation", re.compile(
        r"(你确认吗|是否确认|你同意吗|可以吗\?|行吗\?|好吗\?)", re.IGNORECASE
    )),
    ("passive_waiting", re.compile(
        r"(你是否希望|你要我.*吗|需要我.*吗|你想让我.*吗|是否需要)", re.IGNORECASE
    )),
    ("pure_option_listing", re.compile(
        r"^(请选择|请从.*中选择|你想选哪个)", re.MULTILINE | re.IGNORECASE
    )),
    ("continue_or_stop", re.compile(
        r"(是否继续|要不要继续|是否收尾|需要继续吗)", re.IGNORECASE
    )),
]

# Patterns indicating good forward-driving content
_FORWARD_INDICATORS: list[re.Pattern[str]] = [
    # askQuestions tool usage
    re.compile(r"vscode_askQuestions|askQuestions", re.IGNORECASE),
    # Question mark in the last paragraph with analytical tone
    re.compile(r"(我倾向|我的分析|我判断|从.*角度看|基于.*考虑).*[？?]", re.DOTALL),
    # Explicit recommendation + question
    re.compile(r"(推荐|建议|倾向).{0,100}[？?]", re.DOTALL),
]

# Analysis indicators — shows AI gave its own judgment
_ANALYSIS_INDICATORS: list[re.Pattern[str]] = [
    re.compile(r"(我的分析|我倾向|我判断|我认为|从.*角度|基于.*分析|推荐方案)"),
    re.compile(r"(理由|原因|因为|考虑到)"),
    re.compile(r"\*\*(推荐|分析|判断)\*\*"),
]


@dataclass
class ProgressionCheckResult:
    """Result of checking a reply for progression compliance."""

    passed: bool
    violations: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    has_analysis: bool = False
    has_forward_question: bool = False

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "violations": self.violations,
            "warnings": self.warnings,
            "has_analysis": self.has_analysis,
            "has_forward_question": self.has_forward_question,
        }


def _get_tail(text: str, tail_lines: int = 15) -> str:
    """Extract the tail portion of the reply for checking."""
    lines = text.strip().splitlines()
    return "\n".join(lines[-tail_lines:])


def check_reply_progression(reply_text: str) -> ProgressionCheckResult:
    """Check if a reply ending conforms to the progression contract.

    Examines the last ~15 lines of the reply for:
    1. Forbidden patterns (pure confirmation, passive waiting, etc.)
    2. Presence of AI analysis/judgment
    3. Presence of forward-driving question

    Returns a ProgressionCheckResult with pass/fail and details.
    """
    if not reply_text.strip():
        return ProgressionCheckResult(
            passed=False,
            violations=["Reply is empty"],
        )

    tail = _get_tail(reply_text)

    violations: list[str] = []
    warnings: list[str] = []

    # Check forbidden patterns
    for name, pattern in _FORBIDDEN_PATTERNS:
        if pattern.search(tail):
            violations.append(
                f"Forbidden ending pattern detected: {name}"
            )

    # Check for analysis
    has_analysis = any(p.search(tail) for p in _ANALYSIS_INDICATORS)
    if not has_analysis:
        warnings.append(
            "No AI analysis/judgment detected in the tail. "
            "Reply should include AI's own reasoning before the question."
        )

    # Check for forward-driving question
    has_forward = any(p.search(tail) for p in _FORWARD_INDICATORS)
    if not has_forward:
        # Also check for any question mark as a softer indicator
        if "？" in tail or "?" in tail:
            has_forward = True
            warnings.append(
                "Question mark found but no strong forward-driving pattern. "
                "Ensure the question drives work forward."
            )
        else:
            violations.append(
                "No forward-driving question detected at the end of the reply."
            )

    passed = len(violations) == 0

    return ProgressionCheckResult(
        passed=passed,
        violations=violations,
        warnings=warnings,
        has_analysis=has_analysis,
        has_forward_question=has_forward,
    )
