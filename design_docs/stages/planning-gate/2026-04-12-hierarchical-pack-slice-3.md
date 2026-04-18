# Planning Gate — Hierarchical Pack Topology Slice 3: Pipeline Integration

- Scope: `hierarchical-pack-slice-3`
- Status: **COMPLETED**
- Created: 2026-04-12
- Direction Analysis: `design_docs/hierarchical-pack-topology-direction-analysis.md`
- Depends On: Slice 2 (COMPLETED)

## 目标

将 Slice 1-2 的 PackTree + scoped build 能力接入 Pipeline 和 MCP/CLI 入口，使治理链可按 scope_path 路由到不同的 RuleConfig。

## 变更清单

### 1. `src/workflow/pipeline.py`

- `Pipeline.__init__()` 中保存 `ContextBuilder` 实例（当前只保存了 build 结果 `PackContext`）
- 新增 `process_scoped(input_text: str, scope_path: str)` 方法：
  - 使用 `builder.build_scoped(scope_path)` 获取 scoped PackContext
  - 使用 `resolve_rules(scoped_context)` 获取 scoped RuleConfig
  - 其余流程与 `process()` 相同
- `process()` 行为不变
- `info()` 新增 `pack_tree` 字段：输出树结构概览（名称、parent、depth、scope_paths）

### 2. `src/mcp/tools.py`

- `governance_decide` tool 参数新增可选 `scope_path: str`
- 当 `scope_path` 提供时，调用 `pipeline.process_scoped(text, scope_path)` 而非 `pipeline.process(text)`
- 当 `scope_path` 未提供时，行为不变

### 3. CLI 适配（如需要）

- `src/workflow/cli.py` 或 CLI 入口新增可选 `--scope-path` 参数（若 CLI 有 process 命令）

## 不做什么

- 不修改 PDP resolvers / PEP executor
- 不修改 PackRegistrar（validator 注册仍全局）
- 不更新权威文档（留给 Slice 4）

## 验证门

- [x] `process_scoped()` 在有 scope 时返回正确的 scoped result
- [x] `process()` 行为不变
- [x] MCP `governance_decide` 透传 scope_path 正常
- [x] `info()` 输出 pack_tree 结构
- [x] 全套回归通过（`pytest tests/ -q` = 755 passed, 2 skipped）

## 预计变更量

| 文件 | 变更类型 | 行数估计 |
|------|---------|---------|
| `src/workflow/pipeline.py` | 保存 builder + process_scoped + info 扩展 | +40, ~15 修改 |
| `src/mcp/tools.py` | scope_path 参数 + 路由 | ~10 修改 |
| 测试文件 | 新增 pipeline scoped 测试 | ~80 |
| **合计** | | ~145 |
