# Planning Gate — Hierarchical Pack Topology Slice 1: Manifest + PackTree

- Scope: `hierarchical-pack-slice-1`
- Status: **COMPLETED**
- Created: 2026-04-12
- Direction Analysis: `design_docs/hierarchical-pack-topology-direction-analysis.md`

## 目标

在不改变任何现有合并逻辑的前提下，完成层级化 Pack 的基础设施：

1. PackManifest 新增 `parent` 和 `scope_paths` 字段
2. 新建 PackTree 类——从 manifest 列表构建单继承树
3. `manifest_version` 从 `"1.0"` bump 到 `"1.1"`
4. 单元测试覆盖树构建与异常情况

## 不做什么

- 不改变 `ContextBuilder.build()` 的任何合并逻辑
- 不改变 `override_resolver.resolve()` 的任何优先级逻辑
- 不改变 `Pipeline._load_packs` 或 `process()`
- 不改变 MCP / CLI 入口
- 不更新权威文档（留给 Slice 4）

## 变更清单

### 1. `src/pack/manifest_loader.py`

- `PackManifest` 新增字段：
  - `parent: str = ""`：父 pack 名称，空串表示无父节点（树根或独立 pack）
  - `scope_paths: list[str] = field(default_factory=list)`：该 pack 生效的路径前缀列表
- `load_dict()` 解析新字段
- `CURRENT_MANIFEST_VERSION` 保持 `"1.0"` 不变（`parent` / `scope_paths` 为可选字段，无需 bump minor）
  - 注：方向分析中原计划 bump 到 1.1，但可选字段新增不改变现有 manifest 的含义，loader 行为不变，因此不需要 bump

### 2. 新文件 `src/pack/pack_tree.py`

新建 `PackTree` 类，职责：

- **构建**：从 `list[PackManifest]` 构建内部树结构
  - 所有 kind 的 pack 都参与树（platform-default / official-instance / project-local）
  - 无 `parent` 的 pack 自动成为树根
  - 支持多棵树（forest）——不同 kind 的根节点自然独立
- **验证**：
  - 循环引用检测（A→B→C→A）→ 抛出 ValueError
  - 孤儿引用检测（parent 指向不存在的 pack）→ 记录警告，孤儿 pack 视为独立根
  - 重复 pack 名称检测 → 抛出 ValueError
- **查询 API**：
  - `roots() -> list[PackManifest]`：返回所有树根节点
  - `children(pack_name: str) -> list[PackManifest]`：返回直接子节点
  - `ancestors(pack_name: str) -> list[PackManifest]`：返回从根到父的有序祖先链（不含自身）
  - `chain(pack_name: str) -> list[PackManifest]`：返回从根到自身的完整链
  - `depth(pack_name: str) -> int`：返回节点深度（根 = 0）
  - `resolve_scope(scope_path: str) -> list[PackManifest] | None`：给定路径，返回包含匹配的最深叶节点的完整链，无匹配返回 None
- **scope_paths 匹配语义**：
  - 简单前缀匹配：`"backend/"` 匹配所有以 `"backend/"` 开头的路径
  - 无 `scope_paths` 的 pack 对所有路径生效（类似通配符）
  - 多个同级 pack 的 `scope_paths` 重叠时，抛出 ValueError（配置错误）

### 3. 测试文件 `tests/test_pack_tree.py`

覆盖以下场景：

- 无 parent 时所有 pack 均为根（向后兼容）
- 简单单链：root → child → grandchild
- 多分支：root → (frontend, backend)
- 循环检测抛 ValueError
- 孤儿 parent 引用降级为根 + 警告
- 重复名称检测
- scope_paths 前缀匹配
- scope 重叠检测
- `chain()` 返回正确的祖先链
- `depth()` 返回正确的深度值
- `resolve_scope()` 选择最深匹配

## 验证门

- [ ] `pytest tests/test_pack_tree.py` 全部通过
- [ ] `pytest tests/ -q` 全套回归通过（≥694 passed）
- [ ] `get_errors` 对所有修改文件返回无错误
- [ ] 现有 pack manifest（`doc-loop-vibe-coding/pack-manifest.json`、`.codex/packs/project-local.pack.json`）无需修改即可正常加载
- [ ] 新增 `parent` 和 `scope_paths` 字段的 manifest 可以正常解析

## 预计变更量

| 文件 | 变更类型 | 行数估计 |
|------|---------|---------|
| `src/pack/manifest_loader.py` | 新增字段 + 解析 | +6 |
| `src/pack/pack_tree.py` | 新文件 | ~140 |
| `tests/test_pack_tree.py` | 新文件 | ~200 |
| **合计** | | ~346 |
