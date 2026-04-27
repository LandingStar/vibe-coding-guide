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
    "request-for-writeback", "issue-report", "implementation",
    "unknown", "ambiguous",
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
    "implementation": "medium",
}

KEYWORD_MAP: dict[str, list[str]] = {
    "question": [
        "?", "what", "how", "why", "explain", "clarify", "describe",
        "show", "tell me", "help me understand", "overview", "summary",
        "analyze", "analyse", "review", "check", "inspect", "look at",
        "find", "search", "list", "which", "where", "when", "who",
        "什么", "为什么", "怎么", "请问", "吗", "哪个", "哪些",
        "看看", "看一下", "分析", "查看", "检查", "查找", "搜索",
        "帮我看", "帮我找", "告诉我", "解释", "说明", "总结",
        "概述", "简述", "列出", "了解",
    ],
    "approval": [
        "approve", "approved", "lgtm", "looks good", "ship it",
        "go ahead", "proceed", "confirm", "confirmed", "yes",
        "agree", "accepted", "merge", "merge it",
        "同意", "通过", "审核通过", "批准", "确认", "可以",
        "没问题", "行", "好的", "继续", "合并",
    ],
    "rejection": [
        "reject", "no", "denied", "nack", "do not", "don't",
        "stop", "cancel", "abort", "revert", "rollback", "undo",
        "拒绝", "不同意", "否决", "不行", "不要", "取消",
        "停止", "撤销", "回滚", "撤回",
    ],
    "correction": [
        "fix", "please fix", "wrong", "error", "bug", "incorrect",
        "broken", "repair", "patch", "correct", "adjust", "tweak",
        "modify", "edit", "revise", "amend",
        "improve", "optimize", "refactor", "rename", "move",
        "修正", "错误", "修复", "请修复", "修复这个", "改正",
        "调整", "修改", "改一下", "改改", "优化", "重构",
        "更新", "编辑", "调优", "修一下", "帮我改",
    ],
    "scope-change": [
        "scope", "expand", "change scope", "add feature", "new feature",
        "extend", "broaden", "enlarge", "include", "new requirement",
        "additional", "also need", "on top of", "besides",
        "范围", "扩展范围", "改变范围", "新功能", "增加功能",
        "扩展", "新需求", "额外", "还需要", "另外",
    ],
    "protocol-change": [
        "protocol", "process", "workflow", "rule", "policy",
        "convention", "standard", "guideline", "methodology",
        "协议", "流程", "规则", "策略", "规范", "标准",
        "方法论", "约定", "改流程", "改规则",
    ],
    "constraint": [
        "constraint", "must", "require", "requirement", "mandatory",
        "enforce", "restrict", "limit", "boundary", "precondition",
        "约束", "要求", "必须", "强制", "限制", "边界",
        "前提条件", "前置条件",
    ],
    "request-for-writeback": [
        "write back", "writeback", "commit", "save", "persist",
        "record", "document", "log", "note down", "write to file",
        "update document", "update doc", "sync", "flush",
        "写回", "回写", "落地", "保存", "持久化", "记录",
        "写入", "存档", "同步", "写文档", "更新文档",
    ],
    "issue-report": [
        "issue", "problem", "report", "bug", "error", "crash",
        "exception", "failure", "fails", "broken", "traceback",
        "stack trace", "attributeerror", "typeerror", "keyerror",
        "raises", "unexpected", "regression", "incident",
        "问题", "报告", "错误", "异常", "崩溃", "报错",
        "导致", "不支持", "不工作", "不正常", "出错",
        "故障", "失败", "回归", "缺陷",
    ],
    "implementation": [
        "implement", "create", "build", "make", "generate", "write",
        "code", "develop", "add", "set up", "setup", "init",
        "initialize", "scaffold", "bootstrap", "start", "begin",
        "draft", "design", "architect", "plan", "construct",
        "实现", "创建", "构建", "编写", "开发", "添加",
        "新建", "搭建", "初始化", "生成", "起草", "设计",
        "开始", "着手", "编码", "写代码", "帮我写",
        "帮我创建", "帮我实现",
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


@dataclass
class ParallelChildTask:
    """Descriptor for a single child task in a parent-managed fan-out."""

    child_task_id: str
    contract: dict
    namespace: str
    allowed_artifacts: list[str] = field(default_factory=list)
    required_refs: list[str] = field(default_factory=list)
    shared_review_zone_id: str = ""
    priority: int = 0


@dataclass
class TaskGroup:
    """Minimal orchestration object for a parent-managed child group."""

    task_group_id: str
    parent_envelope_id: str
    parent_trace_id: str | None
    mode: str = "subgraph-fanout"
    children: list[ParallelChildTask] = field(default_factory=list)
    join_policy: str = "wait-all"
    merge_policy: str = "conflict-classification"


@dataclass
class ChildExecutionRecord:
    """Execution evidence for a single child result."""

    child_task_id: str
    task_group_id: str
    trace_id: str | None
    namespace: str
    status: str
    report: dict
    started_at: str = ""
    finished_at: str = ""


@dataclass
class MergeBarrierOutcome:
    """Barrier classification result for a parent-managed child group."""

    task_group_id: str
    child_statuses: dict[str, str]
    conflict_classification: str
    review_outcome: str
    review_driver: str = ""
    shared_review_zone_ids: list[str] = field(default_factory=list)
    merged_delta: dict = field(default_factory=dict)
    blocked_reason: str = ""


@dataclass
class GroupedReviewOutcome:
    """Grouped review surface derived from child execution evidence."""

    task_group_id: str
    outcome: str
    review_driver: str = ""
    shared_review_zone_ids: list[str] = field(default_factory=list)
    child_reviews: dict[str, dict] = field(default_factory=dict)
    changed_artifacts: list[str] = field(default_factory=list)
    unresolved_items: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    blocked_reason: str = ""


@dataclass
class GroupTerminalOutcome:
    """Terminal bundle for group-level handoff or escalation semantics."""

    task_group_id: str
    terminal_kind: str
    source_child_ids: list[str] = field(default_factory=list)
    trigger_evidence: list[dict] = field(default_factory=list)
    suppressed_surfaces: list[str] = field(default_factory=list)
    authoritative_refs: list[str] = field(default_factory=list)
    open_items: list[str] = field(default_factory=list)
    current_gate_state: str = ""
    blocked_reason: str = ""


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
