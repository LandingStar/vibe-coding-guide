# MCP Tool Surface Audit

> 长期有效的 MCP 接口治理文档
> 来源：B-REF-7（Claude best practices — consolidate related operations）
> 审计日期：2026-04-18
> 审计范围：`src/mcp/server.py` + `src/mcp/tools.py` 全部 11 个 tools（含 `analyze_changes` 统一入口）

## 工具清单

| # | Tool Name | 参数数量 | 核心职责 | 领域 |
|---|-----------|---------|---------|------|
| 1 | `governance_decide` | 2 (input_text*, scope_path) | PDP→PEP 治理链 | 治理核心 |
| 2 | `check_constraints` | 0 | C1-C8 约束状态 | 治理核心 |
| 3 | `get_next_action` | 0 | 基于项目状态推荐下一步 | 工作流导航 |
| 4 | `writeback_notify` | 1 (phase_description*) | 阶段完成通知 + 自动推进 | 工作流导航 |
| 5 | `get_pack_info` | 2 (scope_path, level) | Pack 信息查询 | Pack 信息 |
| 6 | `governance_override` | 5 (action*, constraint, reason, scope, override_id) | 临时规则豁免 CRUD | 治理辅助 |
| 7 | `query_decision_logs` | 4 (trace_id, decision, intent, limit) | 决策日志查询 | 审计/可观测 |
| 8 | `impact_analysis` | 3 (changed_files, changed_symbols, max_depth) | 依赖图传播分析 | 变更分析（别名） |
| 9 | `coupling_check` | 2 (changed_files, changed_symbols) | 耦合注解检查 | 变更分析（别名） |
| 10 | `analyze_changes` | 3 (changed_files, changed_symbols, max_depth) | 统一变更分析 | 变更分析 |
| 11 | `promote_dogfood_evidence` | 10 (symptoms*, ...) | Dogfood 全链路 pipeline | Dogfood |

（`*` = required）

## 职责分组

### Group A: 治理核心（必须独立）
- `governance_decide` — 主入口，每次重要操作前调用
- `check_constraints` — 状态检查，与 governance_decide 中的约束检查有重叠但调用时机不同

**分析**：`governance_decide` 内部已调用 `check_constraints`。但 `check_constraints` 作为独立工具有明确的独立使用场景（上下文恢复、session 开始时），保持独立是合理的。

**结论：保持独立** ✅

### Group B: 工作流导航
- `get_next_action` — 推荐下一步
- `writeback_notify` — 阶段完成后推荐下一步

**分析**：两者都返回 "下一步推荐"，但触发时机完全不同：
- `get_next_action`：被动查询（"我不知道该做什么了"）
- `writeback_notify`：主动通知（"我刚完成了 X"），附带 checkpoint 写入和 planning-gate 扫描

**重叠度**：输出格式有重叠（都包含 instruction + files_to_update），但触发语义不同。如果合并为一个带 `mode: "query" | "notify"` 的工具，会增加参数复杂度而不减少调用次数。

**结论：保持独立** ✅

### Group C: Pack 信息
- `get_pack_info` — 单独的 pack 信息查询

**分析**：独立且职责单一。`governance_decide` 的返回值中也包含 `pack_info`，但 `get_pack_info` 支持 level 控制和独立调用（无需提供 input_text）。

**结论：保持独立** ✅

### Group D: 治理辅助
- `governance_override` — 三个子操作通过 `action` 参数复用一个 tool

**分析**：这是一个正确的合并示例 — register/revoke/list 共享 override 的领域概念，用 `action` 参数区分比拆成 3 个 tools 更好。

**结论：已正确合并** ✅

### Group E: 审计/可观测
- `query_decision_logs` — 决策日志查询

**分析**：独立且职责单一。不与其他 tool 重叠。

**结论：保持独立** ✅

### Group F: 变更分析 ⚠️ **可合并候选**
- `impact_analysis` — 依赖图传播
- `coupling_check` — 耦合注解匹配

**分析**：
- 两者的输入参数**完全相同**：`changed_files` + `changed_symbols`
- 两者的使用场景**完全重叠**："我改了这些文件/符号，还需要改什么？"
- 实际使用中，agent 几乎总是**同时调用两者**
- 两者的底层数据源不同（baseline_graph.json vs coupling_annotations.json），但这是实现细节

**合并建议**：合并为 `analyze_changes`，在输出中分两个 section 返回：
```json
{
  "impact": { "direct": [...], "transitive": [...] },
  "coupling_alerts": [...]
}
```

**状态：已实施** ✅ — `analyze_changes` 已添加为统一入口；旧工具名保留为向后兼容别名。

### Group G: Dogfood Pipeline
- `promote_dogfood_evidence` — 全链路 dogfood pipeline

**分析**：这是最重的 tool（10 个参数），但它封装了一条完整的 4 步 pipeline（evaluate → build → assemble → dispatch），遵循了"合并相关操作"的原则。参数多是因为 pipeline 本身的领域复杂度，不是过度拆分。

**结论：保持独立** ✅（但参数量需关注）

## 功能重叠矩阵

| Tool A ↓ / Tool B → | governance_decide | check_constraints | get_next_action | writeback_notify |
|---------------------|-------------------|-------------------|-----------------|------------------|
| **governance_decide** | — | 内部调用 ⚠️ | 无 | 无 |
| **check_constraints** | 被调用 | — | 内部调用 ⚠️ | 内部调用 ⚠️ |
| **get_next_action** | 无 | 内部调用 | — | 输出格式重叠 |
| **writeback_notify** | 无 | 内部调用 | 输出格式重叠 | — |

| Tool A ↓ / Tool B → | impact_analysis | coupling_check |
|---------------------|-----------------|----------------|
| **impact_analysis** | — | 输入完全相同 ⚠️ |
| **coupling_check** | 输入完全相同 ⚠️ | — |

## 合并建议总结

| 建议 | 涉及 Tools | 行动 | 优先级 | 破坏性 |
|------|-----------|------|--------|--------|
| **合并变更分析工具** | impact_analysis + coupling_check → `analyze_changes` | ✅ 已实施 | 中 | 低（旧名保留为别名） |
| **保持治理核心独立** | governance_decide + check_constraints | 不合并 | — | — |
| **保持导航独立** | get_next_action + writeback_notify | 不合并 | — | — |
| **关注参数膨胀** | promote_dogfood_evidence (10 params) | 监控但不改 | 低 | — |

## 整体评价

当前 10 个 tools 的拆分总体**合理**：

- **7/10 tools 职责清晰、不可合并**
- **1 组** (impact_analysis + coupling_check) 存在明确的合并机会（输入完全相同 + 使用场景重叠）
- **1 个** (governance_override) 已正确使用了 action 参数合并模式
- **1 个** (promote_dogfood_evidence) 参数较多但领域复杂度要求如此

对比 Claude best practices 的"consolidate related operations"原则：
- 当前 surface 没有严重的过度拆分问题
- 唯一明确的合并点是变更分析工具
- 如果未来新增 tools，应优先考虑是否可以作为现有 tool 的参数扩展

## 长期演进建议

1. **合并 impact_analysis + coupling_check**（可在后续切片实施）
2. **如果新增"pack 验证"工具**（validate_description + validate_pack_organization），应合并为一个 `validate_pack` 工具
3. **考虑为 governance_decide 添加 `include_pack_info: bool` 参数**，减少 agent 需要额外调用 get_pack_info 的情况
4. **promote_dogfood_evidence 的参数**：如果 pipeline 继续变复杂，考虑接受一个结构化的 `config` 对象而非平铺参数
