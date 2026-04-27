---
handoff_id: 2026-04-20_0943_multica-borrowing-and-progression-tools_stage-close
entry_role: canonical
kind: stage-close
status: superseded
scope_key: multica-borrowing-and-progression-tools
safe_stop_kind: stage-complete
created_at: 2026-04-20T09:43:05+08:00
supersedes: 2026-04-19_0337_b-ref-series-close_stage-close
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
conditional_blocks: []
other_count: 0
---

# Summary

本次会话完成了 4 个 Multica 借鉴实施项 + 1 个 issue 解决（check_reply_progression），全部通过 dogfood 验证。测试基线从 1223 提升至 1256（+33 新测试）。

## Boundary

- 完成到哪里：条件化 always_on 加载、RuntimeBridge 注入、依赖方向反转（consumes 字段）、check_reply_progression MCP 工具
- 为什么这是安全停点：所有 feature 均已测试通过 + dogfood 验证 + write-back 完成；Checklist 剩余 Multica 项均为低优先级/长期/流程级
- 明确不在本次完成范围内的内容：MCP GovernanceTools 全面迁移 RuntimeBridge（待 worker 启用）、代码层依赖方向文档化、Multi-agent runtime、类型依赖图谱

## Authoritative Sources

- design_docs/Project Master Checklist.md
- design_docs/Global Phase Map and Current Position.md
- design_docs/runtime-bridge-direction-analysis.md
- issues/issue_conversation_progression_trigger_mechanism.md (closed)

## Session Delta

- 本轮新增：`src/runtime/__init__.py`、`src/runtime/bridge.py`、`src/workflow/reply_progression.py`、`tests/test_conditional_always_on.py`、`tests/test_runtime_bridge.py`、`tests/test_consumes.py`、`tests/test_reply_progression.py`、`design_docs/runtime-bridge-direction-analysis.md`
- 本轮修改：`src/__main__.py`（CLI→RuntimeBridge）、`src/pack/manifest_loader.py`（+consumes 字段 + check_consumes）、`src/pack/context_builder.py`（scope_path 过滤）、`src/workflow/pipeline.py`（+consumes_status）、`src/mcp/server.py`（+check_reply_progression tool）、`.codex/packs/project-local.pack.json`（+consumes）
- 本轮形成的新约束或新结论：RuntimeBridge 为统一入口但不强制迁移现有 MCP（等 worker 启用时自然切入）；consumes 为 warning-only 不阻塞

## Verification Snapshot

- 自动化：1256 passed, 2 skipped（全量 pytest）
- 手测：CLI info/check 通过 RuntimeBridge 正常工作；check_reply_progression 正确检测违规和通过
- 未完成验证：MCP server 端到端（需真实 MCP client 连接验证 check_reply_progression tool 注册）
- 仍未验证的结论：无

## Open Items

- 未决项：MCP GovernanceTools 何时迁移至 RuntimeBridge（条件：当 MCP 需要 worker 时）
- 已知风险：无
- 不能默认成立的假设：无

## Next Step Contract

- 下一会话建议只推进：代码层依赖方向文档化（低难度快速关闭） 或 类型依赖图谱 planning-gate 或 post-v1.0 backlog 证据收集组件化
- 下一会话明确不做：Multi-agent runtime（长期/条件触发）
- 为什么当前应在这里停下：4 个 feature + dogfood 验证已形成完整交付单元，剩余项均为独立 scope

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Why This Stage Can Close

- 当前大阶段到这里可以结束的原因：Multica 借鉴系列中可立即实施的项已全部完成，剩余项为低优先级/长期/流程级
- 当前不继续把更多内容塞进本阶段的原因：4 个 feature 已形成完整交付单元，继续下去会进入不同 scope（类型图谱或证据组件化）

## Planning-Gate Return

- 应回到的 planning-gate 位置：无活跃 planning-gate，可从 Checklist 选择下一项
- 下一阶段候选主线：代码层依赖方向文档化 / 类型依赖图谱 planning-gate / post-v1.0 证据收集组件化
- 下一阶段明确不做：Multi-agent runtime（条件触发项）

## Conditional Blocks

None.

## Other

None.
