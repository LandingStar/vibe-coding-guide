# Planning Gate — Completion Boundary Protocol

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-14-completion-boundary-protocol |
| Scope | 完成边界处 conversation progression contract 强制注入 |
| Status | **COMPLETED** |
| 来源 | 本轮 dogfood 实际违规 + `direction-candidates-after-phase-35.md` §K |
| 前置 | J (Conversation Progression Contract Stability) 已完成 |
| 测试基线 | 770 passed, 2 skipped |

## 问题陈述

Phase J 已部署 conversation progression contract 到 4 个层级（权威文档、pack 规则、MCP 工具、instructions generator），但本轮 overrides 实施结束后仍发生违规——AI 以"你是否还有其他想继续推进的方向，或者本轮可以收尾？"终结，违反 C1。

根因诊断：`interaction_contract` 仅在 AI 主动调用 MCP 工具时注入。在完成边界（所有 todo 已完成、无 active planning-gate），AI 跳过工具调用直接生成回复，合约在最需要时恰好缺席。

## 目标

在 pack 规则中新增 `completion_boundary_protocol`（方案 B），在 copilot-instructions.md 增加静态冗余（方案 A），形成多层叠加防护。

**不做**：

- 不新增 MCP 工具（`finalize_response` 属于储备方案 R-3）
- 不修改 Chat Participant 架构（属于储备方案 R-2）
- 不改变已有 conversation_progression contract 结构

## 交付物

### 1. Pack 规则扩展

在 `project-local.pack.json` 的 `conversation_progression` 块新增：

```json
"completion_boundary_protocol": {
  "trigger": "all_todos_completed_and_no_active_planning_gate",
  "mandatory_tool_call": "get_next_action",
  "rationale": "Re-inject interaction_contract at the exact moment the completion instinct is strongest"
}
```

同步更新 bootstrap 副本。

### 2. get_next_action 增强

`get_next_action()` 在返回"no active planning gate"场景时，新增 `completion_boundary_reminder` 字段：

```python
action["completion_boundary_reminder"] = (
    "CRITICAL: You are at a completion boundary. "
    "You MUST provide your own analysis of the next direction "
    "and end with a forward question that includes your recommendation. "
    "Do NOT ask the user whether to continue or stop."
)
```

### 3. Instructions Generator 静态冗余

`_conversation_progression_section()` 末尾新增完成边界专用提醒段：

```markdown
- **Completion Boundary Rule**: When all tasks are done and no planning gate is active,
  you MUST call `get_next_action` before composing your response.
  Never end with "shall we continue or stop?" — always provide your analysis of the next direction.
```

### 4. Document-Driven Workflow Standard 补充

对话推进规则段新增第 6 条：

> 当所有当前任务已完成且不存在活跃 planning-gate 时，agent 必须先调用 `get_next_action` 获取下一步推荐，再基于该推荐组装包含自身判断的 forward question。这是对话推进规则中发现的最高风险违规场景（完成边界失忆），此条规则有最高优先级。

### 5. Targeted Tests

- `test_completion_boundary_protocol_in_pack_rules`: 验证 `completion_boundary_protocol` 字段被正确加载到 merged_rules
- `test_get_next_action_completion_boundary_reminder`: 验证 get_next_action() 在无 active gate 时返回 `completion_boundary_reminder`
- `test_instructions_generator_completion_boundary`: 验证 instructions generator 渲染出 completion boundary rule 文本

## 验证门

- [x] Pack 规则中 `completion_boundary_protocol` 已存在且可被加载
- [x] `get_next_action()` 在 no-gate 场景返回 `completion_boundary_reminder`
- [x] Instructions generator 输出包含 completion boundary 提醒
- [x] Document-Driven Workflow Standard 已更新
- [x] Bootstrap 副本已同步
- [x] 全量回归测试通过且无新增 failure（779 passed, 2 skipped）

## 渐进加固路径

本切片 (B+A) → R-3 (`finalize_response` MCP 校验工具) → R-2 (Chat Participant output gate)

每一层都保留 @copilot 的使用，不改变用户与 Copilot 的交互模式。
