# Planning Gate: 对话中临时规则突破 / 修改能力

## Status: COMPLETED

## 来源

- `design_docs/direction-candidates-after-phase-35.md` §BL-4
- `design_docs/Project Master Checklist.md` 活跃待办 "对话中临时规则突破/修改能力"
- `design_docs/tooling/Document-Driven Workflow Standard.md` 对话推进规则
- `design_docs/stages/planning-gate/2026-04-12-conversation-progression-contract-stability.md`（J 切片，已完成）

## 背景

当前对话中用户偶尔需要临时授权突破或修改某条默认行为规则（例如"这轮不用以提问结尾"、"暂时允许你跳过 planning-gate 检查"）。这类授权目前仅靠 model 上下文记忆维持，存在以下问题：

1. 无持久化 — 上下文压缩后丢失
2. 无审计 — 事后无法追溯哪些规则被突破过
3. 无自动过期 — 临时授权可能意外延续到后续会话
4. 无边界 — model 不确定哪些规则允许被临时突破

## Scope

本切片**只做**：

1. 在权威文档中定义约束的可突破性分类（overridable / non-overridable）
2. 定义临时 override 的数据模型（TemporaryOverride schema）
3. 在 `ConstraintResult` 中添加 `active_overrides` 字段
4. 提供 `_load_temporary_overrides` / `_save_temporary_override` 的轻量持久化（`.codex/temporary-overrides.json`）
5. 在 `check_constraints` 输出中展示当前活跃的临时 override
6. 在 MCP `check_constraints` tool 返回值中包含 override 信息
7. 提供一个 MCP tool（`governance_override`）用于 model 在获得用户口头授权后注册 / 撤销 / 查看临时 override
8. 在 `instructions_generator` 中生成临时 override 相关指引段落
9. 在 safe-stop writeback 时自动过期所有 session-scoped override
10. 更新 pack rules 与官方实例 reference 文档

本切片**不做**：

- 不做完整的 conversational rule engine
- 不做 UI 交互面
- 不修改 machine-checked 约束（C4/C5）的检查逻辑
- 不允许临时 override 跨 session 存活（除非用户显式声明 persistent）
- 不做 override 嵌套或冲突解析

## 约束可突破性分类

| 约束 | 层级 | 可突破？ | 理由 |
|------|------|---------|------|
| C1 | instruction-layer | ✅ overridable | 用户可主动声明"本轮不强制推进式提问" |
| C2 | instruction-layer | ✅ overridable | 用户可临时放宽方向文档引用要求 |
| C3 | instruction-layer | ✅ overridable | 用户可声明暂停 phase 完成后的自动推进 |
| C4 | machine-checked | ❌ non-overridable | 文件存在性是客观事实，不可绕过 |
| C5 | machine-checked | ❌ non-overridable | planning-gate 存在性是工作流硬约束，不可绕过 |
| C6 | instruction-layer | ✅ overridable | 用户可声明"允许本轮扩大 scope" |
| C7 | instruction-layer | ✅ overridable | 用户可声明"跳过本设计节点审核" |
| C8 | instruction-layer | ❌ non-overridable | subagent 职责边界不应被临时绕过 |

## 数据模型

```python
@dataclass
class TemporaryOverride:
    """一条临时规则突破记录。"""
    override_id: str          # UUID
    constraint: str           # "C1", "C5", "conversation_progression.final_reply_requires_forward_question" 等
    reason: str               # 用户授权的理由摘要
    scope: str                # "turn" | "session" | "until-next-safe-stop"
    created_at: str           # ISO 8601
    expires_at: str | None    # ISO 8601 or None (scope-based)
    status: str               # "active" | "expired" | "revoked"
    revoked_at: str | None    # ISO 8601 or None
```

持久化格式（`.codex/temporary-overrides.json`）：

```json
{
  "schema_version": "1.0",
  "overrides": [
    {
      "override_id": "...",
      "constraint": "C1",
      "reason": "用户声明本轮不需要推进式提问",
      "scope": "turn",
      "created_at": "2026-04-12T10:00:00+08:00",
      "expires_at": null,
      "status": "active",
      "revoked_at": null
    }
  ]
}
```

## 实现切片

### Slice A: Schema + 约束分类 + 持久化

1. 在 `src/workflow/` 下新增 `temporary_override.py`：
   - `TemporaryOverride` dataclass
   - `OVERRIDABLE_CONSTRAINTS` / `NON_OVERRIDABLE_CONSTRAINTS` 常量
   - `load_overrides(project_root) -> list[TemporaryOverride]`
   - `save_override(project_root, override) -> None`
   - `revoke_override(project_root, override_id) -> None`
   - `expire_session_overrides(project_root) -> list[str]`（返回过期的 override_id 列表）
   - `get_active_overrides(project_root) -> list[TemporaryOverride]`

2. 在 `ConstraintResult` 中新增 `active_overrides: list[dict]` 字段
3. 在 `_check_constraints` 中调用 `get_active_overrides` 并填充字段
4. 当被突破的约束本应产生 violation 时，将 severity 从 `block` 降为 `warn`（仅对 overridable 约束）

### Slice B: MCP tool + instructions generator + pack rules

1. 在 MCP governance tools 中新增 `governance_override` tool：
   - action: `register` / `revoke` / `list`
   - register 时要求提供 constraint + reason + scope
   - 对 non-overridable 约束返回拒绝
2. 在 `check_constraints` 返回值中包含 `active_overrides` 段
3. 在 `instructions_generator.py` 中新增 `_temporary_override_section`：
   - 列出当前活跃的临时 override
   - 提醒 model 在 safe-stop / session-end 时 override 将自动过期
4. 更新 `.codex/packs/project-local.pack.json` 的 rules 段，新增 `temporary_override` 规则
5. 更新 `doc-loop-vibe-coding/references/` 新增 `temporary-override.md` 参考文档

### Slice C: Safe-stop 集成 + 审计 + 文档

1. 在 `safe_stop_writeback.py` 的 bundle contract 中新增 override 过期步骤
2. 在审计事件中记录 override 的注册、撤销与过期
3. 更新权威文档：
   - `design_docs/tooling/Document-Driven Workflow Standard.md` 新增临时 override 段
   - `docs/governance-flow.md` 补充 override 决策路径
4. 测试覆盖

## 验证门

- [x] `TemporaryOverride` 数据模型与持久化 round-trip 测试通过
- [x] `governance_override` MCP tool 的 register / revoke / list 正常工作
- [x] overridable 约束被突破后，`check_constraints` 展示 active overrides
- [x] non-overridable 约束的 override 请求被拒绝
- [x] safe-stop writeback bundle 包含 override 过期步骤
- [x] override 生命周期记录保留在持久化存储
- [x] `instructions_generator` 输出包含活跃 override 段
- [x] 现有 pytest 全量通过（650 passed, 1 pre-existing failure），无 regression

## 风险

- 若可突破约束列表设计过松，可能导致安全规则被轻易绕过 → 通过 `NON_OVERRIDABLE_CONSTRAINTS` 硬编码边界
- 若 override 持久化文件被手动篡改 → 通过 schema 校验 + 审计日志互参
- 若 override scope 定义不清导致跨 session 泄漏 → safe-stop writeback bundle 的过期步骤兜底

## 影响范围

- 新增文件：`src/workflow/temporary_override.py`、`doc-loop-vibe-coding/references/temporary-override.md`
- 修改文件：`src/workflow/pipeline.py`、`src/workflow/instructions_generator.py`、`src/workflow/safe_stop_writeback.py`、`.codex/packs/project-local.pack.json`、MCP governance tools
- 权威文档更新：`design_docs/tooling/Document-Driven Workflow Standard.md`、`docs/governance-flow.md`
