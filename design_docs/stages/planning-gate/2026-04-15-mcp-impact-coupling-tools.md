# Planning Gate — MCP 变更影响与耦合检查工具集成（Slice 3）

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-15-mcp-impact-coupling-tools |
| Scope | 将 Slice 2 的 ImpactAnalyzer + CouplingChecker 注册为 MCP 工具 |
| Status | **DONE** |
| 来源 | `issues/issue_type_dependency_and_coupling_tracking.md` FR-1/FR-2 → Slice 3 |
| 前置 | Slice 2 `tools/dependency_graph/impact.py + coupling.py` 已完成（872 passed） |
| 测试基线 | 881 passed, 2 skipped |

## 问题陈述

Slice 2 实现了 ImpactAnalyzer 和 CouplingChecker，但它们目前只能通过 CLI 或 Python API 调用。Agent 在 MCP 会话中无法直接使用这些能力。需要将它们注册为 MCP 工具，使 agent 在日常 dogfood 中可以直接调用。

## 目标

**做**：

1. **MCP 工具 `impact_analysis`**
   - 输入：`changed_files`（列表）、`changed_symbols`（列表）、`max_depth`（整数，默认 2）
   - 使用 baseline graph（`tools/dependency_graph/baseline_graph.json`）
   - 返回：直接/间接受影响节点 + 传播路径

2. **MCP 工具 `coupling_check`**
   - 输入：`changed_files`（列表）、`changed_symbols`（列表）
   - 使用 coupling annotations（`tools/dependency_graph/coupling_annotations.json`）
   - 返回：触发的耦合提醒列表

3. **GovernanceTools 方法实现**
   - `impact_analysis()` — 调用 `query_impact()`
   - `coupling_check()` — 调用 `query_coupling()`

4. **server.py 注册与分发**
   - `list_tools` 新增 2 个 Tool 对象
   - `call_tool` 新增 2 个分发分支

**不做**：

1. 不做与 `check_constraints` 的自动联动（留给未来切片）
2. 不做 baseline graph 自动刷新（当前使用静态快照）
3. 不做依赖图谱的实时构建（超出 MCP 工具范围）

## 模块改动

```
src/mcp/tools.py     — 新增 impact_analysis() / coupling_check() 方法
src/mcp/server.py    — list_tools + call_tool 各新增 2 条
```

## 验证门

- [x] `impact_analysis` MCP 工具可调用，返回格式正确（4 tests）
- [x] `coupling_check` MCP 工具可调用，返回格式正确（5 tests）
- [x] 无 baseline graph 时返回优雅错误（test_impact_analysis_no_baseline passed）
- [x] 无 coupling annotations 时返回空列表（test_coupling_check_no_annotations_file passed）
- [x] 测试通过数 881 ≥ 基线 872（881 passed, 2 skipped）

## 风险

1. **baseline graph 路径**：MCP server 运行时的工作目录可能与仓库根不同——需要用 Pipeline 可配置路径或相对路径解析
2. **大型 graph 性能**：当前 186 节点量级无性能风险，但需为未来大仓库预留 timeout 考虑
