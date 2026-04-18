# Planning Gate — Dogfood Pipeline MCP Exposure (Slice A)

> 日期：2026-04-16  
> 方向分析：`design_docs/dogfood-pipeline-workflow-integration-direction-analysis.md`  
> 状态：**DONE** (2026-04-16)

## Scope

新增 1 个 MCP 工具 `promote_dogfood_evidence`，将 dogfood pipeline 的完整 4 步流（evaluate → build → assemble → dispatch）暴露为单次 MCP 调用。

## 变更清单

| # | 文件 | 类型 | 说明 |
|---|------|------|------|
| 1 | `src/dogfood/__init__.py` | 修改 | 新增 `run_full_pipeline()` 协调函数 |
| 2 | `src/mcp/tools.py` | 修改 | 新增 `promote_dogfood_evidence()` 方法 |
| 3 | `src/mcp/server.py` | 修改 | 注册新工具到 `list_tools` + `call_tool` |
| 4 | `tests/test_dogfood_mcp.py` | 新建 | MCP 工具集成测试 |

## 不做清单

- 不修改 `Pipeline.process()`
- 不持久化 ConsumerPayload 到文件
- 不修改 checkpoint / handoff / CURRENT.md
- 不实现 evidence 自动提取
- 不修改现有 MCP 工具签名

## 验证门

- [x] MCP tool `promote_dogfood_evidence` 注册并可调用
- [x] 传入 ≥2 symptoms（其中 1 个命中 T1），返回 PROMOTE/SUPPRESS
- [x] 传入 0 个 PROMOTE 时，packet 和 payloads 为 None
- [x] 全量回归 ≥ 964 passed, ≤ 2 skipped → **976 passed, 2 skipped**
