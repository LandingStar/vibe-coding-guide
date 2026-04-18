# Planning Gate: Pack Manifest 版本化规范

- **日期**: 2026-04-13
- **状态**: COMPLETED
- **来源**: [review/research-compass.md](../../review/research-compass.md) 研究空白 — "版本化 pack manifest 规范"
- **权威参考**:
  - [docs/pack-manifest.md](../../docs/pack-manifest.md)
  - [docs/plugin-model.md](../../docs/plugin-model.md)
  - [src/pack/manifest_loader.py](../../src/pack/manifest_loader.py)
  - [src/pack/context_builder.py](../../src/pack/context_builder.py)

## 问题

当前 pack manifest (`pack-manifest.json`) 缺少 **manifest 格式本身的版本号**：

1. `version` 字段描述 pack 内容版本（如 `"1.0.0"`），但不代表 manifest JSON 结构的版本
2. 随着功能演进，manifest 中已新增 `shipped_copies`、`runtime_compatibility`、`rules.temporary_override` 等字段，但没有指示这些字段何时引入、loader 如何区分新旧格式
3. 若后续添加破坏性字段变更（如重命名 `always_on` 为 `context_files`），当前 loader 没有版本感知的处理路径
4. `temporary-overrides.json` 已有 `schema_version: "1.0"` 的先例，manifest 应保持一致

## 目标

1. **定义 manifest schema 版本**：在 pack-manifest.json 中增加 `manifest_version` 字段
2. **版本感知加载**：loader 识别 `manifest_version`，对未知高版本给出警告而非静默忽略
3. **文档化兼容策略**：在 `docs/pack-manifest.md` 中明确何为兼容性变更、何为破坏性变更
4. **最小侵入**：不改变现有字段语义，不改变合并逻辑

## 设计

### manifest_version 字段

```json
{
  "manifest_version": "1.0",
  "name": "doc-loop-vibe-coding",
  "version": "1.0.0",
  "kind": "official-instance",
  ...
}
```

- 固定格式：`"<major>.<minor>"`，不含 patch（manifest 格式变更粒度不需要三段）
- `manifest_version` 与 `version` 的区别：
  - `manifest_version`：manifest JSON 结构的格式版本
  - `version`：pack 内容的语义版本

### 兼容策略

| 变更类型 | 版本影响 | 示例 |
|---------|---------|------|
| 新增可选字段 | minor bump | 加 `shipped_copies` |
| 修改字段语义 | major bump | `always_on` 从文件路径改为对象数组 |
| 移除字段 | major bump | 删除 `triggers` |
| 新增必需字段 | major bump | 要求 `manifest_version` 必须存在 |

### Loader 行为

| 场景 | 行为 |
|------|------|
| `manifest_version` 缺失 | 视为 `"1.0"`（向后兼容） |
| `manifest_version` == `"1.0"` | 正常加载 |
| `manifest_version` major > 当前支持 | 抛出 ValueError |
| `manifest_version` minor > 当前支持 | 正常加载 + 返回警告（未知字段被忽略） |

## 实施切片

### Slice A: schema + loader + 测试

1. `src/pack/manifest_loader.py`：
   - `PackManifest` 增加 `manifest_version: str = "1.0"` 字段
   - `load_dict()` 读取 `manifest_version`，缺失时默认 `"1.0"`
   - Major version 不匹配时抛出 `ValueError`
   - Minor version 不匹配时记录 warning（返回 `PackManifest` 的 `_warnings` 列表）
2. `doc-loop-vibe-coding/pack-manifest.json`：增加 `"manifest_version": "1.0"`
3. `.codex/packs/project-local.pack.json`：增加 `"manifest_version": "1.0"`
4. `doc-loop-vibe-coding/assets/bootstrap/.codex/packs/project-local.pack.json`：增加 `"manifest_version": "1.0"`
5. `doc-loop-vibe-coding/examples/project-local.pack.json`：增加 `"manifest_version": "1.0"`
6. 测试：版本缺失回退、正常加载、major 不匹配、minor 不匹配

### Slice B: 文档化

1. `docs/pack-manifest.md`：增加 Schema Versioning 章节
2. `review/research-compass.md`：标记 "版本化 pack manifest 规范" 为已研究/已落地

## 验证项

- [x] `manifest_version` 字段存在于所有现有 manifest 文件
- [x] loader 对缺失版本的后向兼容正常工作
- [x] major version 不匹配抛出 ValueError
- [x] minor version 不匹配产生 warning 但不阻断加载
- [x] 全量测试通过（669 passed, 2 skipped, 0 failures）
- [x] `docs/pack-manifest.md` 包含 Schema Versioning 章节

## 风险

| 风险 | 严重性 | 缓解 |
|------|--------|------|
| 过度设计版本迁移机制 | 低 | 当前只支持单一 major=1，迁移机制留到 2.0 |
| 现有 manifest 加载中断 | 低 | 缺失 manifest_version 默认为 "1.0"，完全后向兼容 |
