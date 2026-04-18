# Planning Gate — 多实例共存冲突检测与报告

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-14-multi-instance-conflict-detection |
| Scope | 冲突检测 + 审计报告（方案 A） |
| Status | **COMPLETED** |
| 来源 | `design_docs/multi-instance-conflict-direction-analysis.md` 方案 A |
| 前置 | Pack Runtime Loader（Phase 16）、Hierarchical Pack Topology 已完成 |
| 测试基线 | 793 passed, 2 skipped |

## 目标

在 ContextBuilder 合并过程中检测同层规则冲突，在 PrecedenceResolver 中标记平局裁决，通过 Pipeline.info() 暴露冲突信息。

**不做**：

- 不改变现有合并行为（last-writer-wins 保持）
- 不引入强制声明（方案 B）
- 不实现完整仲裁引擎（方案 C）

## 交付物

### 1. ContextBuilder 冲突检测

修改 `src/pack/context_builder.py`：

- `_deep_merge()` 新增 `conflicts` 收集器参数
- 当 key 已存在且被覆盖时记录 `{path, old_value, new_value, old_source, new_source}`
- `PackContext` 新增 `merge_conflicts: list[dict]` 字段
- `_build_from_entries()` 传递冲突收集器并填充 `merge_conflicts`

### 2. PrecedenceResolver 平局标记

修改 `src/pdp/precedence_resolver.py`：

- 当 winner 和 runner-up 具有相同 layer priority 时，result 新增 `tie_broken_by: "insertion_order"` 字段
- 同层冲突也记录到 `conflicts` 列表中（当前只记录跨层冲突）

### 3. Pipeline.info() 暴露

修改 `src/workflow/pipeline.py`：

- `info()` 新增 `merge_conflicts` 字段（从 PackContext 获取）

### 4. Targeted Tests

- `test_deep_merge_detects_overwrite`: 验证 _deep_merge 冲突检测
- `test_context_builder_reports_merge_conflicts`: 验证 PackContext.merge_conflicts 包含冲突信息
- `test_precedence_tie_broken_by_insertion_order`: 验证同层平局标记
- `test_precedence_same_layer_conflict_recorded`: 验证同层冲突记录
- `test_pipeline_info_exposes_merge_conflicts`: 验证 Pipeline.info() 暴露冲突

## 验证门

- [ ] `_deep_merge()` 检测到覆盖时填充 conflicts 列表
- [ ] `PackContext.merge_conflicts` 字段正确反映冲突
- [ ] `PrecedenceResolver` 同层平局标记 `tie_broken_by`
- [ ] `Pipeline.info()` 包含 `merge_conflicts` 字段
- [ ] 全量回归测试通过
- [ ] research-compass "多实例共存" 空白标记为已完成
