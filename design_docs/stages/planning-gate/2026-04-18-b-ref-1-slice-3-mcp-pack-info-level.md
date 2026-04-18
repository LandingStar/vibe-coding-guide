# Planning Gate — B-REF-1 Slice 3: MCP get_pack_info 分级返回

> 日期：2026-04-18
> 前置：B-REF-1 Slice 2（Pipeline MANIFEST 降级，1087 passed）
> 权威文档：[b-ref-1-pack-progressive-loading-direction-analysis.md](../../b-ref-1-pack-progressive-loading-direction-analysis.md)

## 目标

让 MCP `get_pack_info` 工具支持分级返回和 scope 过滤，使 AI 能够：
1. 按 scope_path 查询特定目录下的 pack 信息
2. 按 level 控制返回详细度（METADATA / MANIFEST / FULL）
3. 通过 description 字段快速了解 pack 用途

## 变更清单

### 1. `Pipeline.info()` 输出添加 description 字段
- 文件：`src/workflow/pipeline.py`
- 改动：`manifests_info` 添加 `"description": m.description`
- 影响：所有调用 `info()` 的路径自动获得 description

### 2. MCP `get_pack_info` 暴露 scope_path 参数
- 文件：`src/mcp/server.py` + `src/mcp/tools.py`
- 改动：inputSchema 添加 `scope_path` 可选参数；`tools.get_info()` 接受并转发给 `Pipeline.info(scope_path=)`
- 影响：AI 可以查询特定目录的 pack chain

### 3. MCP `get_pack_info` 暴露 level 参数
- 文件：`src/mcp/server.py` + `src/mcp/tools.py` + `src/workflow/pipeline.py`
- 改动：
  - inputSchema 添加 `level` 可选参数（"metadata" / "manifest" / "full"，默认 "manifest"）
  - `Pipeline.info()` 接受 `level: LoadLevel = LoadLevel.MANIFEST` 参数
  - METADATA 级别：packs 只返回 name/kind/provides/description，不含 merged_intents 等
  - MANIFEST 级别：当前行为（默认）
  - FULL 级别：同 MANIFEST + always_on_content summary
- 影响：AI 可以控制返回的详细程度

## 不做

- 不修改 `ContextBuilder` 或 `PackContext`（Slice 1/2 已稳定）
- 不修改 `Pipeline.process()` 或 `Pipeline.process_scoped()`
- 不引入 B-REF-2 description 质量标准（独立切片）

## 验收条件

- [x] `Pipeline.info()` 返回的 packs 列表包含 description 字段
- [x] MCP `get_pack_info` 接受 scope_path 参数并返回 scope 过滤后的结果
- [x] MCP `get_pack_info` 接受 level 参数，"metadata" 级别只返回基础信息
- [x] MCP `get_pack_info` level="full" 包含 always_on_content 摘要
- [x] 现有测试全部通过（向后兼容）— 1095 passed, 2 skipped
- [x] 新增测试覆盖三个级别 + scope_path（8 个新测试）

## 文件变更预估

| 文件 | 变更 |
|------|------|
| `src/workflow/pipeline.py` | `info()` 加 description + level 参数 |
| `src/mcp/server.py` | `get_pack_info` inputSchema 加参数 |
| `src/mcp/tools.py` | `get_info()` 加参数转发 |
| `tests/test_pack_progressive_load.py` | 新测试 |
