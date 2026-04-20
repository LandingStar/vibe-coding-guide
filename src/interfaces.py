"""Protocol and shared type definitions for cross-layer integration.

These protocols and data types break circular dependencies between modules
by providing a stable contract layer both sides can code against.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal, Protocol


# ── Intent / Impact constants (shared between pack and pdp layers) ────────

PLATFORM_INTENTS: set[str] = {
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

KEYWORD_MAP: dict[str, list[str]] = {
    "question": ["?", "what", "how", "why", "explain", "clarify",
                  "什么", "为什么", "怎么", "请问", "吗"],
    "approval": ["approve", "approved", "lgtm", "同意", "通过",
                 "审核通过", "批准"],
    "rejection": ["reject", "no", "denied", "拒绝", "不同意", "否决"],
    "correction": ["fix", "please fix", "wrong", "error", "bug", "incorrect",
                   "修正", "错误", "修复", "请修复", "修复这个"],
    "scope-change": ["scope", "expand", "change scope", "范围",
                     "扩展范围", "改变范围"],
    "protocol-change": ["protocol", "process", "workflow", "协议",
                        "流程", "规则"],
    "constraint": ["constraint", "must", "require", "约束", "要求",
                   "必须"],
    "request-for-writeback": ["write back", "writeback", "commit",
                              "save", "写回", "回写", "落地"],
    "issue-report": [
        "issue", "problem", "report", "bug", "error", "crash",
        "exception", "failure", "fails", "问题", "报告", "错误",
        "异常", "崩溃", "报错", "导致", "不支持",
    ],
}


# ── Tool Permission types (shared between pack and pdp layers) ────────────

PermissionLevel = Literal["allow", "ask", "deny"]


@dataclass
class ToolPolicy:
    """Permission policy for a specific action type."""

    permission: PermissionLevel = "allow"
    deny_message: str = ""


@dataclass
class ToolPermissionConfig:
    """Pack-level tool permission configuration."""

    default: PermissionLevel = "allow"
    policies: dict[str, ToolPolicy] = field(default_factory=dict)


@dataclass
class PermissionResult:
    """Result of a tool permission check."""

    permission: PermissionLevel
    deny_message: str = ""
    policy_source: str = ""  # Which pack or "platform_default"


def parse_tool_permissions(raw: dict) -> ToolPermissionConfig:
    """Parse a raw dict (from pack JSON rules.tool_permissions) into ToolPermissionConfig."""
    if not raw or not isinstance(raw, dict):
        return ToolPermissionConfig()

    default = raw.get("default", "allow")
    if default not in ("allow", "ask", "deny"):
        default = "allow"

    policies: dict[str, ToolPolicy] = {}
    raw_policies = raw.get("policies", {})
    if isinstance(raw_policies, dict):
        for action_type, pol in raw_policies.items():
            if isinstance(pol, dict):
                perm = pol.get("permission", "allow")
                if perm not in ("allow", "ask", "deny"):
                    perm = "allow"
                policies[action_type] = ToolPolicy(
                    permission=perm,
                    deny_message=pol.get("deny_message", ""),
                )

    return ToolPermissionConfig(default=default, policies=policies)


# ── Worker / Subagent Protocols ───────────────────────────────────────────


class WorkerBackend(Protocol):
    """Execute a subagent contract and return a report."""

    def execute(self, contract: dict) -> dict:
        """Accept a Subagent Contract dict and return a Subagent Report dict."""
        ...


class ContractFactory(Protocol):
    """Build a full Subagent Contract from a delegation decision."""

    def build(self, delegation_decision: dict) -> dict:
        """Transform delegation_decision (with contract_hints) into a
        complete contract conforming to subagent-contract.schema.json."""
        ...


class ReportValidator(Protocol):
    """Validate a Subagent Report against the schema."""

    def validate(self, report: dict) -> dict:
        """Return a structured validation result dict.

        Expected keys:
        - ``valid`` (bool): whether the report is schema-compliant.
        - ``errors`` (list[str]): human-readable error descriptions,
          empty when valid.
        """
        ...


class HandoffValidator(Protocol):
        """Validate a Handoff against schema and handoff-specific invariants."""

        def validate(self, handoff: dict, context: dict | None = None) -> dict:
                """Return a structured validation result dict.

                Expected keys:
                - ``valid`` (bool): whether the handoff is acceptable.
                - ``errors`` (list[str]): human-readable error descriptions,
                    empty when valid.
                """
                ...


class EscalationNotifier(Protocol):
    """Deliver an escalation notification to the target authority."""

    def notify(self, notification: dict) -> dict:
        """Send *notification* and return a delivery result dict.

        Expected keys:
        - ``delivered`` (bool): whether the notification was accepted.
        - ``channel`` (str): the delivery channel used.
        """
        ...
