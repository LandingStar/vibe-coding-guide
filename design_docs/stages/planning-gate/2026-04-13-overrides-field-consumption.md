# Planning Gate — overrides 字段消费

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-13-overrides-field-consumption |
| Scope | Pack 名称级 overrides 声明消费 |
| Status | COMPLETED |
| 来源 | `design_docs/overrides-field-consumption-direction-analysis.md` 方案 A |
| 前置 | hierarchical pack topology 完成（✅） |
| 测试基线 | 755 passed, 2 skipped |

## 目标

把 `PackManifest.overrides: list[str]` 从"已加载但未消费"变为"已加载、已验证、已注入审计、已暴露"。

**不做**：

- 不改变 overrides 字段类型
- 不改变合并行为（`_deep_merge` 仍由排序顺序决定）
- 不 bump `manifest_version`
- 不修改 MCP tool 参数
- 方案 C（结构化覆盖）标记为未来储备，不在本切片实施

## 交付物

### 1. PackContext 扩展

- `PackContext` 新增 `merged_overrides: dict[str, list[str]]`
  - key = pack name, value = 该 pack 声明的 overrides 目标列表
  - 示例：`{"backend": ["root"], "api": ["backend"]}`
- `_build_from_entries()` 中从 manifests 提取 overrides 声明

### 2. Override 目标存在性验证

- 在 `_build_from_entries()` 或独立函数中执行：
  - 若 pack X 声明 `overrides: ["Y"]`，但 Y 不在已加载的 pack 名集合中 → 警告
- 模式与 `check_dependencies()` 一致：warning-only，不阻塞加载

### 3. PrecedenceResolver 注入

- `resolve()` 结果新增可选字段 `explicit_override: bool`
  - 当 winning pack 的 `overrides` 列表包含任一 evaluated rules 所属 pack → `True`
  - 否则不含该字段或为 `False`
- `resolution_strategy` 可附加前缀如 `"explicit-override adoption-layer-priority"`

### 4. Pipeline.info() 暴露

- `info()` 返回新增：
  - `override_declarations: dict[str, list[str]]` — 等同 `merged_overrides`
  - `override_warnings: list[str]` — 目标不存在等验证警告

### 5. 权威文档同步

- `docs/pack-manifest.md`：回答开放问题（当前不需要覆盖理由，但预留方案 C 升级路径）
- `docs/precedence-resolution.md`：补充 explicit-override 注解说明

### 6. Targeted Tests

- override 目标存在 → 正常通过
- override 目标不存在 → warning 生成
- scoped build 中 override 声明正确传播
- precedence 结果中 explicit_override 正确标注
- Pipeline.info() 暴露 override_declarations 与 warnings
- 现有全部 755 测试不回归

## 验证门

- [x] `PackContext.merged_overrides` 正确提取
- [x] override 目标存在性警告按预期生成
- [x] PrecedenceResolver 结果包含 `explicit_override` 标注
- [x] `Pipeline.info()` 暴露 `override_declarations` 和 `override_warnings`
- [x] `docs/pack-manifest.md` 开放问题已回答
- [x] `docs/precedence-resolution.md` explicit-override 已补充
- [x] pytest 全部通过，无回归（770 passed, 2 skipped）
- [x] 附带修复：`override_resolver.py` 重复 `available_capabilities` 字段声明已清理

## 风险

| 风险 | 严重度 | 缓解 |
|------|--------|------|
| 当前所有 manifest overrides 皆为空，无法验证真实覆盖场景 | 中 | 测试用构造数据充分覆盖；真实场景待 dogfood |
| 与 depends_on 校验逻辑重复 | 低 | 语义不同（依赖 vs 覆盖意图），实现可复用校验模式 |
