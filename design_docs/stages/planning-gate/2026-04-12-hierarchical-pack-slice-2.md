# Planning Gate — Hierarchical Pack Topology Slice 2: Scoped Build + Chain Merge

- Scope: `hierarchical-pack-slice-2`
- Status: **COMPLETED**
- Created: 2026-04-12
- Direction Analysis: `design_docs/hierarchical-pack-topology-direction-analysis.md`
- Depends On: Slice 1 (COMPLETED)

## 目标

在 Slice 1 的 PackTree 基础设施上，实现作用域感知的 Pack 合并：

1. ContextBuilder 新增 `build_scoped(scope_path)` 方法
2. 作用域链序代替 kind 排序作为合并优先级
3. 原 `build()` 行为 100% 不变（向后兼容）

## 核心设计

### 关键洞察

在作用域模式下，PackTree 的 `resolve_scope()` 返回的链（如 `[platform, instance, root, backend, api]`）**已经是正确的优先级顺序**——从通用到具体。因此：

- **作用域模式下不需要按 kind 排序**——链序本身就是优先级
- **链式合并覆盖关系天然正确**——链中越靠后的 pack 优先级越高
- `override_resolver.resolve()` 和 `precedence_resolver.resolve()` **不需要修改**——它们消费的 PackContext 已经包含了正确排序的 manifests 和 merged_rules

### 变更清单

#### 1. `src/pack/context_builder.py`

**提取公共方法**：将当前 `build()` 的核心逻辑提取为 `_build_from_entries(entries)`。

**新增 `build_scoped(scope_path: str)` 方法**：

```python
def build_scoped(self, scope_path: str) -> PackContext:
    """Build a scoped PackContext for the given working path.

    Uses PackTree to determine which pack chain applies,
    then merges only packs in that chain, in tree order
    (root → leaf, i.e. general → specific).

    Falls back to `build()` if no pack has scope_paths
    or no scope matches.
    """
```

逻辑：
1. 从 `self._entries` 构建 PackTree
2. 调用 `tree.resolve_scope(scope_path)` 获取匹配的 pack 链
3. 若无匹配，fallback 到 `build()`
4. 过滤 `_entries` 只保留链中的 pack
5. **按链序**（而非 kind 优先级）合并
6. 返回 PackContext（manifests 按链序排列）

**重要**：PackTree 缓存在 ContextBuilder 内部，避免重复构建。

#### 2. 不修改 `src/pack/override_resolver.py`

`resolve(context)` 的输入是 PackContext，其中 `merged_rules` 已经按正确的链序合并好了。现有的 rule apply 逻辑（keyword_map extend、impact_table merge 等）不受影响。

#### 3. 不修改 `src/pdp/precedence_resolver.py`

当前 precedence_resolver 处理的是显式 `rules` 列表中的 `layer` 字段比较，与 pack 合并逻辑无关。scoped build 已在上游保证了正确合并。

## 不做什么

- 不修改 `Pipeline`（留给 Slice 3）
- 不修改 MCP / CLI 入口
- 不消费 `overrides` 字段（overrides 的语义设计可在 Slice 2 讨论中生成方向候选，但不在本 Slice 实现）
- 不更新权威文档（留给 Slice 4）
- 不修改 `PackRegistrar`

## 测试覆盖

新增或修改测试文件：`tests/test_context_builder.py`（或现有相关测试文件）

| 场景 | 描述 |
|------|------|
| build_scoped 基本功能 | 3 层链 + scope_path 匹配 → 只含链中 pack 的 PackContext |
| build_scoped 回退 | 无 scope 匹配时等同 build() |
| build_scoped 排除非链 pack | 多分支中非目标分支的 pack 不出现在结果中 |
| build_scoped 链序合并 | 子 pack 的 rules 覆盖父 pack 的 rules |
| build_scoped always_on 叠加 | 子 pack 的 always_on 覆盖父 pack 的同名文件 |
| build_scoped + resolve 一致 | build_scoped → resolve 产出正确 RuleConfig |
| build() 行为不变 | 有 parent/scope 的 manifest 存在时 build() 仍全局合并 |

## 验证门

- [ ] 新增测试全部通过
- [ ] `pytest tests/ -q` 全套回归通过（≥728 passed）
- [ ] `get_errors` 对所有修改文件返回无错误
- [ ] `build()` 在有 parent/scope_paths 的 manifest 存在时行为不变（通过已有测试确认）

## 预计变更量

| 文件 | 变更类型 | 行数估计 |
|------|---------|---------|
| `src/pack/context_builder.py` | 提取方法 + 新增 build_scoped | +50, ~20 重构 |
| 测试文件 | 新增 scoped build 测试 | ~120 |
| **合计** | | ~190 |
