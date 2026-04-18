# Planning Gate — B-REF-1 Pack Progressive Loading (Slice 1)

> 日期：2026-04-17  
> 方向分析：`design_docs/b-ref-1-pack-progressive-loading-direction-analysis.md`  
> 状态：**DONE**

## Scope

引入三级加载概念（`LoadLevel` enum）+ `description` 字段 + `ContextBuilder.build(level=)` 分阶段 build + `PackContext.upgrade()` 升级方法。**不改变任何现有行为**——`FULL` 是默认值。实际成果超出 Slice 1 scope：预置的 Pipeline MANIFEST 降级（Slice 2）和 Pipeline.info level 参数（Slice 3）代码也被激活，46 测试全通过。

## 变更清单

| # | 文件 | 类型 | 说明 |
|---|------|------|------|
| 1 | `src/pack/manifest_loader.py` | 修改 | `PackManifest.description: str = ""` 字段 + `LoadLevel` enum |
| 2 | `src/pack/context_builder.py` | 修改 | `build(level=)` 参数 + `PackContext.load_level` 字段 + `PackContext.upgrade()` 方法 |
| 3 | `tests/test_pack_progressive_load.py` | 新建 | 三级加载 + upgrade 测试 |

## 不做清单

- 不修改 Pipeline 初始化流程（仍然 `LoadLevel.FULL`）
- 不修改 MCP 工具
- 不修改 on_demand 懒加载机制
- 不修改 `build_scoped()`（保持与 `build()` 一致的 level 默认值）
- 不实现 Pack 自动激活 / description 驱动选择

## 三级行为定义

| Level | 合并能力集 | 合并 rules | 读取 always_on 内容 | 收集 on_demand |
|-------|-----------|-----------|-------------------|---------------|
| METADATA | name/kind/provides/description only | ❌ | ❌ | ❌ |
| MANIFEST | intents/gates/document_types/provides 全部 | ✅ | ❌ | ✅ (路径) |
| FULL | 同 MANIFEST | ✅ | ✅ | ✅ (路径) |

## 验证门

- [x] `LoadLevel.METADATA` build → `always_on_content` 为空，`merged_rules` 为空，只有 name/kind/provides/description 合并
- [x] `LoadLevel.MANIFEST` build → `always_on_content` 为空，`merged_rules` 已合并，能力集完整
- [x] `LoadLevel.FULL` build → 行为与当前 `build()` 完全一致（向后兼容）
- [x] `PackContext.upgrade(FULL)` 从 MANIFEST 升级 → always_on_content 与直接 FULL build 一致
- [x] `description` 字段在 manifest JSON / dict 中正确解析，缺省时为 `""`
- [x] 全量回归 1133 passed, 2 skipped（基线 992 → +141）
