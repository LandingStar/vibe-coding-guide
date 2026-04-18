# Planning Gate — B-REF-1 Slice 1: LoadLevel 三级加载测试覆盖

> 日期：2026-04-17
> 前置：`design_docs/b-ref-1-pack-progressive-loading-direction-analysis.md` Slice 1
> 触发：实现代码已存在但测试覆盖为零

## 背景

B-REF-1 Slice 1 的核心实现已在先前阶段落地：

- `LoadLevel` 枚举（METADATA=1, MANIFEST=2, FULL=3）
- `PackManifest.description` 字段
- `ContextBuilder.build(level=)` / `build_scoped(level=)` 三级分支
- `PackContext.load_level` + `upgrade(target, builder=)` 方法

但当前整个测试套件中没有任何测试引用 `LoadLevel`，方向分析中的 3 条验证门也均未勾选。

## Scope

补充测试覆盖，验证三级加载语义正确性。不修改实现代码。

## 切片内容

### 测试文件：`tests/test_pack_progressive_load.py`（新建）

| 类 | 测试用例 | 验证内容 |
|---|---|---|
| `TestLoadLevelEnum` | 值、排序、比较 | IntEnum 语义 |
| `TestMetadataLevel` | build(METADATA) 只含 name/kind/provides/description | 方向分析验证门 1 |
| `TestManifestLevel` | build(MANIFEST) 含 intents/gates/rules 但 always_on_content 为空 | 方向分析验证门 2 |
| `TestFullLevel` | build(FULL) 行为与无 level 参数一致 | 方向分析验证门 3 |
| `TestBuildScopedLevel` | build_scoped(path, level=METADATA/MANIFEST) | scoped 场景三级 |
| `TestUpgrade` | METADATA→MANIFEST→FULL 升级、已满足不重建、无 builder 报错 | upgrade() 合约 |

## 验收条件

- [x] `LoadLevel.METADATA` build 只包含 name/kind/provides/description
- [x] `LoadLevel.MANIFEST` build 不读取文件内容（always_on_content 为空）
- [x] `LoadLevel.FULL` build 行为与当前完全一致
- [x] `upgrade()` 从低级升到高级正确、已满足则返回 self、无 builder 报错
- [x] `build_scoped(level=)` 三级均正确
- [x] 全量回归无降级（1082 passed, 2 skipped）
