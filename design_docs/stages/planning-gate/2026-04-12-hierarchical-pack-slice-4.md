# Planning Gate — Hierarchical Pack Topology Slice 4: Authority Docs + State Sync

- Scope: `hierarchical-pack-slice-4`
- Status: **COMPLETED**
- Created: 2026-04-12
- Direction Analysis: `design_docs/hierarchical-pack-topology-direction-analysis.md`
- Depends On: Slice 3 (COMPLETED)

## 目标

把已经落地的层级化 Pack 语义同步回权威文档与状态板，避免 runtime 行为与文档说明继续漂移。

本 Slice 只做文档与状态写回，不再改动运行时代码。

## 变更清单

### 1. `docs/pack-manifest.md`

- 新增 `parent` 字段说明：单继承树中的父 pack 名称，空串表示根节点或独立 pack
- 新增 `scope_paths` 字段说明：作用域前缀列表，采用简单前缀匹配
- 明确 `scope` 与 `scope_paths` 的分工：
  - `scope` 是人类可读的适用范围描述
  - `scope_paths` 是 runtime 路由用的机器可消费路径前缀
- 明确当前 `manifest_version` 仍保持 `"1.0"`，因为 `parent` / `scope_paths` 为可选字段，未引入不兼容格式变化

### 2. `docs/precedence-resolution.md`

- 补充层级化 pack 下的 precedence 口径：
  - 全局 adoption 层次仍然存在
  - 当显式传入 `scope_path` 时，runtime 先解析匹配的 pack 链，再按链序（root → leaf）合并
  - 同一条链中越深的 pack 优先级越高
- 明确当前实现中 `scope_path` 是调用方显式传入，而非 runtime 自动推断
- 明确同级 sibling 的 `scope_paths` 重叠属于配置错误，而不是运行时 review 决策

### 3. `docs/plugin-model.md`

- 补充 pack 可形成树状拓扑，而不仅是扁平三层来源
- 说明所有 kind（`platform-default` / `official-instance` / `project-local`）当前都允许参与树
- 说明当前已支持：单继承树 + 显式 scope 路由
- 说明当前未支持：mixin / DAG 多继承

### 4. `docs/project-adoption.md`

- 补充大型项目 / monorepo 的 adoption 形状：root pack + 分区 pack + 子模块 pack
- 说明项目级 pack 可以按 `parent` 与 `scope_paths` 形成局部层级
- 说明调用方在需要作用域化治理时，应显式传入 `scope_path`
- 说明未传入 `scope_path` 时，runtime 仍保持全局合并（向后兼容）

### 5. 状态板与方向文档收口

- `design_docs/Project Master Checklist.md`：记录 hierarchical pack topology 已完成（Slice 1-4）
- `design_docs/Global Phase Map and Current Position.md`：追加 post-v1.0 已完成的窄切片记录
- `.codex/checkpoints/latest.md`：同步当前 safe-stop 结论与下一方向

## 不做什么

- 不修改 `src/` 运行时代码
- 不新增新的 pack 语义（如 mixin、DAG、auto scope inference）
- 不改动 `overrides` 语义
- 不扩大到新的 Phase 编号

## 验证门

- [x] 四份 authority docs 与当前实现保持一致
- [x] 文档中明确区分 `scope` 与 `scope_paths`
- [x] 文档中不再把 pack 模型描述为只能扁平三层合并
- [x] Checklist / Phase Map / checkpoint 写回完成
- [x] 未引入新的代码变更；复用 Slice 3 回归基线（`pytest tests/ -q` = 755 passed, 2 skipped）

## 预计变更量

| 文件 | 变更类型 | 行数估计 |
|------|---------|---------|
| `docs/pack-manifest.md` | 字段与语义更新 | ~35 |
| `docs/precedence-resolution.md` | precedence 语义更新 | ~25 |
| `docs/plugin-model.md` | plugin/pack topology 更新 | ~25 |
| `docs/project-adoption.md` | adoption 形状更新 | ~25 |
| 状态板 / checkpoint | 收口写回 | ~20 |
| **合计** | | ~130 |