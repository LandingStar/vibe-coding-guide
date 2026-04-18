# Planning Gate — Dogfood Consumer Writeback (Slice B)

> 日期：2026-04-16  
> 方向分析：`design_docs/dogfood-pipeline-workflow-integration-direction-analysis.md`  
> 前置完成：Slice A（`promote_dogfood_evidence` MCP 工具 — 976 passed, 2 skipped）  
> 状态：**DONE** (2026-04-16)

## Scope

实现 `ConsumerPayload` → 目标文档的自动写回逻辑。当 `promote_dogfood_evidence` 返回 promoted issues 时，可选择自动将 consumer payloads 落盘到相应文档。

## 写回范围

| Consumer | 目标文件 | 写回方式 | 本切片实现 |
|----------|---------|---------|-----------|
| direction-candidates | `design_docs/direction-candidates-after-phase-{N}.md` | 追加 "## Dogfood Feedback" 小节 | ✅ |
| checklist | `design_docs/Project Master Checklist.md` | 追加到活跃待办区域 | ✅ |
| checkpoint | `.codex/checkpoints/latest.md` | 追加 `## Dogfood Feedback` 小节 | ✅ |
| planning-gate | 当前 active gate（如果存在） | 追加 feedback 引用 | ✅ |
| phase-map | `design_docs/Global Phase Map and Current Position.md` | 仅 MCP 返回，不自动写 | ❌ |
| handoff | `.codex/handoffs/CURRENT.md` | 仅 MCP 返回，不自动写 | ❌ |

## 变更清单

| # | 文件 | 类型 | 说明 |
|---|------|------|------|
| 1 | `src/dogfood/writeback.py` | 新建 | `write_consumer_payloads()` — 按消费者类型将 payload 追加到目标文档 |
| 2 | `src/mcp/tools.py` | 修改 | `promote_dogfood_evidence()` 增加 `auto_writeback: bool` 可选参数 |
| 3 | `src/mcp/server.py` | 修改 | inputSchema 增加 `auto_writeback` 字段 |
| 4 | `tests/test_dogfood_writeback.py` | 新建 | writeback 单元测试 |
| 5 | `tests/test_dogfood_mcp.py` | 修改 | 增加 auto_writeback=True 集成测试 |

## 不做清单

- 不修改 `Pipeline.process()` 后处理
- 不实现 phase-map / handoff 自动写回
- 不修改现有文档的格式或结构（只追加新小节）
- 不实现 evidence 自动提取
- 不修改 dispatcher.py 的字段矩阵

## 设计约束

1. **追加-only**：写回操作只在目标文档末尾追加（或指定标记位置之前），不修改已有内容
2. **幂等性**：同一个 `packet_id` 的写回不重复追加（检查已有 packet_id）
3. **安全降级**：目标文件不存在时，跳过该 consumer 并在返回值中标记 `skipped`
4. **dry_run 兼容**：MCP GovernanceTools 的 `dry_run` 模式下，只返回写回计划但不执行

## 验证门

- [x] `write_consumer_payloads()` 对 4 个目标消费者均能正确追加
- [x] 同一 packet_id 不重复写入（幂等性）
- [x] 目标文件不存在时 graceful skip
- [x] `auto_writeback=True` 时 MCP 工具调用后目标文档有新内容
- [x] `auto_writeback=False`（默认）时行为与 Slice A 完全一致
- [x] 全量回归 ≥ 976 passed, ≤ 2 skipped → **992 passed, 2 skipped**
