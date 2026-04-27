---
handoff_id: 2026-04-19_0337_b-ref-series-close_stage-close
entry_role: canonical
kind: stage-close
status: superseded
scope_key: b-ref-series-close
safe_stop_kind: stage-complete
created_at: 2026-04-19T03:37:42+08:00
supersedes: 2026-04-19_0243_hardcoded-git-push-guard_stage-close
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
  - review/claude-managed-agents-platform.md
  - docs/subagent-management.md
conditional_blocks:
  - code-change
  - phase-acceptance-close
other_count: 0
---

# Summary

B-REF 系列（Claude Managed Agents 参考借鉴）全部收口。本轮会话完成 4 项：子 agent model 管理（VS Code 配置 + 命令）、B-REF-4 Permission policy 分层覆盖（ToolPermissionResolver + 21 测试）、B-REF-5 工作流中断原语（workflow_interrupt MCP tool + 7 测试）、B-REF-6 上下文隔离评估（评估报告，结论：当前三层隔离模型合理）。B-REF-1/2/3/7 此前已完成。测试基线 1161 passed, 2 skipped。

## Boundary

- 完成到哪里：B-REF-1 ~ B-REF-7 全部 checked，Claude 参考系列闭环
- 为什么这是安全停点：所有 B-REF planning-gate 均 CLOSED，Checklist 已 writeback，测试全通过
- 明确不在本次完成范围内的内容：全局记忆/文档/规则支持（跨工作区）、Multica 架构研究、持续 dogfood 进程

## Authoritative Sources

- `design_docs/Project Master Checklist.md` — 状态板入口
- `design_docs/Global Phase Map and Current Position.md` — 阶段口径
- `review/claude-managed-agents-platform.md` — B-REF 系列的来源参考
- `docs/subagent-management.md` — 子 agent 管理权威文档

## Session Delta

- 本轮新增：
  - `vscode-extension/src/extension.ts`: `selectModel` 命令 + `onDidChangeConfiguration` 监听
  - `vscode-extension/package.json`: `docBasedCoding.llm.family` 配置 + 命令注册
  - `src/pdp/tool_permission_resolver.py`: ToolPermissionResolver 完整实现
  - `tests/test_tool_permission_resolver.py`: 21 测试
  - `src/mcp/tools.py`: `workflow_interrupt()` 方法
  - `tests/test_workflow_interrupt.py`: 7 测试
  - `design_docs/subagent-context-isolation-evaluation.md`: B-REF-6 评估报告
  - 3 个 planning-gate 文档（均 CLOSED）
- 本轮修改：
  - `src/mcp/server.py`: 新增 `workflow_interrupt` tool + `governance_decide` 增加 `action_type` 参数
  - `src/mcp/tools.py`: `governance_decide()` 增加 action_type + tool_permissions 检查
  - `src/pack/override_resolver.py`: `RuleConfig` 增加 `tool_permissions` 字段
  - `vscode-extension/src/llm/copilot.ts`: `initialize()` 支持 family 配置
  - `design_docs/Project Master Checklist.md`: B-REF-4/5/6 checked + 基线更新
- 本轮形成的新约束或新结论：
  - Permission policy 三层模型：deny > ask > allow（最严格胜出）
  - 隔离评估结论：当前模型合理，无需架构变更
  - workflow_interrupt 是建议性（guidance）而非强制性

## Verification Snapshot

- 自动化：`python -m pytest --tb=short -q` → 1161 passed, 2 skipped (62s)
- 自动化：`npm run build` (vscode-extension) → esbuild 成功
- 手测：无（本轮均为逻辑层实现，不涉及 UI 交互）
- 未完成验证：VS Code 插件 model 切换的端到端手动验证未做
- 仍未验证的结论：B-REF-6 评估报告中建议的 `allowed_artifacts` 路径硬校验未实施

## Open Items

- 未决项：
  - `report_validator` 增加 `allowed_artifacts` 路径校验（B-REF-6 建议，中等优先级）
  - 全局记忆/文档/规则支持（Checklist 剩余项，架构设计）
  - Multica 架构研究（Checklist 剩余项，纯研究）
- 已知风险：无新增
- 不能默认成立的假设：VS Code 端 `vscode.lm.selectChatModels({vendor:'copilot'})` 在所有环境下都能返回完整模型列表（依赖 Copilot 扩展版本）

## Next Step Contract

- 下一会话建议只推进：全局记忆/文档/规则支持（跨工作区继承机制设计），可先做 Multica 架构研究作为输入
- 下一会话明确不做：不改变现有 B-REF 实现、不重构 subagent isolation 架构
- 为什么当前应在这里停下：B-REF 系列是一个完整的借鉴块，已全部收口；剩余项为独立的架构设计轨道

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 运行 `python -m pytest --tb=short -q` 确认测试基线仍为 1161 passed。
- 确认 `design_docs/Project Master Checklist.md` 中 B-REF 系列全部 `[x]`。

## Why This Stage Can Close

- 当前大阶段到这里可以结束的原因：B-REF-1 ~ B-REF-7 全部完成，Claude Managed Agents 参考借鉴系列闭环
- 当前不继续把更多内容塞进本阶段的原因：剩余 Checklist 项属于不同轨道（全局记忆=架构设计，Multica=研究），不应混入 B-REF 收口

## Planning-Gate Return

- 应回到的 planning-gate 位置：无 active planning-gate（所有 B-REF gate 均 CLOSED）
- 下一阶段候选主线：
  1. 全局记忆/文档/规则支持（跨工作区）— 架构设计
  2. Multica 架构研究 — 可作为 1 的前置输入
  3. report_validator 增加 allowed_artifacts 硬校验 — 小增量优化
- 下一阶段明确不做：不重开已 CLOSED 的 B-REF gate、不重构 subagent isolation

## Conditional Blocks

### code-change

Trigger:
本轮新增 4 个源文件 + 修改 5 个源文件，涉及 MCP tool 注册、PDP resolver、VS Code 扩展配置。

Required fields:

- Touched Files:
  - `src/pdp/tool_permission_resolver.py` (NEW)
  - `src/mcp/tools.py` (workflow_interrupt + action_type)
  - `src/mcp/server.py` (workflow_interrupt tool + action_type param)
  - `src/pack/override_resolver.py` (tool_permissions field)
  - `vscode-extension/src/extension.ts` (selectModel + config listener)
  - `vscode-extension/src/llm/copilot.ts` (family config)
  - `vscode-extension/package.json` (llm.family + command)
  - `tests/test_tool_permission_resolver.py` (NEW, 21 tests)
  - `tests/test_workflow_interrupt.py` (NEW, 7 tests)
- Intent of Change: 实现 B-REF-4 permission policy + B-REF-5 interrupt primitive + 子 agent model 管理
- Tests Run: 1161 passed, 2 skipped (pytest) + esbuild build pass
- Untested Areas: VS Code 端到端手动交互测试（model Quick Pick）

Verification expectation:
`python -m pytest --tb=short -q` 全通过即验收。

Refs:

- `design_docs/stages/planning-gate/2026-04-19-permission-policy-layered-override.md` (CLOSED)
- `design_docs/stages/planning-gate/2026-04-19-workflow-interrupt-primitive.md` (CLOSED)
- `design_docs/stages/planning-gate/2026-04-19-subagent-model-management.md` (CLOSED)

### phase-acceptance-close

Trigger:
B-REF 系列 7 项全部完成，阶段验收通过。

Required fields:

- Acceptance Basis: Checklist B-REF-1 ~ B-REF-7 全部 `[x]`，每项有对应 planning-gate CLOSED
- Automation Status: 1161 passed, 2 skipped
- Manual Test Status: 无需额外手测（评估报告类不需要）
- Checklist/Board Writeback Status: `Project Master Checklist.md` 已更新，测试基线已同步

Verification expectation:
确认 Checklist 中 B-REF 行全部 checked + 测试基线匹配。

Refs:

- `design_docs/Project Master Checklist.md`
- `design_docs/subagent-context-isolation-evaluation.md`

## Other

None.
