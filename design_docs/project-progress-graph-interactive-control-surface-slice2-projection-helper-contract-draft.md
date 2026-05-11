# 设计草案 — Project Progress Graph Interactive Control Surface Slice 2 Projection Helper Contract

本文是 `design_docs/stages/planning-gate/2026-05-06-project-progress-graph-interactive-control-surface.md` 的 Slice 2 设计草案，建立在 `design_docs/project-progress-graph-interactive-control-surface-slice1-draft.md` 与 `design_docs/project-progress-graph-interactive-control-surface-snapshot-schema-draft.md` 已固定的 read-only control surface 边界之上。

## 目标

当前目标不是立即落 host overlay，而是先把 graph-facing control snapshot 的 producer contract 写成可直接落代码的最小 helper 面：

1. 哪个模块拥有 graph-facing snapshot producer
2. helper 接受哪些 runtime primitive 输入
3. helper 输出的 snapshot root object 如何稳定对齐当前 schema 草案
4. 哪些 graph 绑定语义仍要留给下一条 binding contract，而不是在这里偷跑

本文不定义：

1. graph node / cluster / graph section 的最终 binding 规则
2. read-only host overlay UI
3. direct mutation controls
4. daemon persistence / replay runtime

## 当前输入证据面

当前已有三组足够支撑 Slice 2 的局部现实：

1. `src/runtime/orchestration/models.py`
   - 已提供 `BridgeWorkItem` / `BridgeGroupItem`
   - 已固定 `latest_trace_id` / `latest_envelope_id` / lifecycle / delivery / governance compact surface
2. `src/runtime/orchestration/rollup.py` 与 `src/runtime/orchestration/projection.py`
   - 已提供 group-item compact projection 与 work-item roll-up helper
   - 说明 runtime primitive 已经足够表达“最少看见什么”
3. `tools/progress_graph/model.py` 与 `tools/progress_graph/export.py`
   - graph/export 侧已经统一输出 user-facing dict surface，并持有 scoped key、display mapping 与 export schema
   - 说明 graph-facing snapshot producer 更适合挂在 `tools/progress_graph/`，而不是反向塞回 runtime 包

因此，当前最稳的 owner 判断是：

1. runtime/orchestration 继续拥有 primitive 与 compact helper
2. progress_graph 侧新增 graph-facing snapshot producer
3. host preview 继续只消费 snapshot / artifact，而不拥有 runtime state

## 当前推荐的模块 owner

当前推荐新增独立 helper 模块：

- `tools/progress_graph/control_snapshot.py`

原因：

1. snapshot 输出已经包含 graph-facing `bindings` 与 `summary` 语义，这不是 runtime/orchestration 的职责
2. `tools/progress_graph/export.py` 已经在承担“面向 preview / host consumer 的 dict surface 导出”职责，新的 snapshot helper 与它同层更自然
3. 如果把 graph binding 语义塞进 `src/runtime/orchestration/`，runtime primitive 会反向拥有 graph-specific target id，边界会变脏

当前不推荐的放置方式：

1. 放进 `src/runtime/orchestration/projection.py`
2. 放进 `vscode-extension/`
3. 直接并到 `tools/progress_graph/doc_projection.py`

其中第 3 条尤其需要避免，因为 doc-loop projection 目前只消费 authority docs；control snapshot 是相邻数据面，但不应让当前 doc projection pipeline 直接承担 runtime owner 职责。

## 当前推荐的 public helper surface

当前推荐只暴露一个最小 public helper：

```python
def build_control_snapshot(
    *,
    work_items: tuple[BridgeWorkItem, ...],
    group_items: tuple[BridgeGroupItem, ...],
    bindings: tuple[dict[str, object], ...] = (),
    generated_at: str,
) -> dict[str, object]: ...
```

语义边界：

1. helper 是 pure function，返回新的 snapshot dict，不做 in-place mutate
2. helper 只消费已经成形的 runtime primitive，不直接消费 executor result、landing artifact 或 live process handle
3. helper 允许当前 `bindings=()`，用于表示 binding contract 尚未补齐的阶段性入口
4. helper 自己负责把 tuple-based runtime field 翻译成 graph-facing list/dict schema

## Input contract

### `work_items`

当前要求：

1. 每个 `work_item_id` 在输入中必须唯一
2. `rollup_*` 字段已经由 runtime helper 决定完成；snapshot producer 不重做 roll-up
3. `source_trace_id` 允许为空

### `group_items`

当前要求：

1. 每个 `group_item_id` 在输入中必须唯一
2. 每个 `group_item.work_item_id` 都必须能在 `work_items` 中找到对应项
3. producer 只镜像已存在字段，不推断缺失的 actor identity

### `bindings`

当前要求：

1. 当前 helper 把 `bindings` 视为“已经按 `design_docs/project-progress-graph-interactive-control-surface-slice2-graph-binding-contract-draft.md` 规范化完成的行”
2. 在 binding contract 落地前，允许传空元组
3. helper 当前最多只做 referential integrity 检查，不负责推断绑定目标

这意味着：

1. binding 的“怎么推出来”留给下一条 contract
2. projection helper 只处理“给定 bindings 后如何稳定写入 snapshot root object”

当前补充边界：

1. `bindings` 中的 target field normalization、`graph_target_key` 一致性、以及 raw target vs display target 语义，均不属于 `build_control_snapshot(...)` 的职责
2. 这些规则应先由 binding normalizer 收口，再由 snapshot producer 直接消费

## Output contract

helper 输出必须稳定对齐 `design_docs/project-progress-graph-interactive-control-surface-snapshot-schema-draft.md` 中的 root object：

1. `snapshot_version`
2. `snapshot_kind`
3. `generated_at`
4. `work_items`
5. `group_items`
6. `bindings`
7. `summary`

当前推荐固定值：

1. `snapshot_version = "v1alpha1"`
2. `snapshot_kind = "orchestration-bridge-compact"`

### `work_items` export rule

1. 按 `work_item_id` 排序后导出
2. tuple 字段一律翻译为 list
3. `source_trace_id` 允许为 `None`

### `group_items` export rule

1. 按 `group_item_id` 排序后导出
2. `child_task_ids` / `open_items` / `authoritative_refs` 一律导出为 list
3. `actor_label` 当前默认导出为 `None`

### `summary` derivation rule

当前推荐由 helper 在同一次 pure build 中同步导出：

1. `open_work_item_count`
   - `lifecycle_state` 不是 `completed` 且不是 `blocked` 的 work item 数量
2. `blocked_work_item_count`
   - `lifecycle_state == "blocked"` 的 work item 数量
3. `waiting_external_resolution_count`
   - `lifecycle_state == "waiting_external_resolution"` 的 work item 数量
4. `active_group_item_count`
   - `lifecycle_state != "settled"` 的 group item 数量
5. `unbound_group_item_count`
   - 未在任一 binding 的 `group_item_ids` 中出现的 group item 数量

当前推荐把 `summary` 和 root object 一起生成，而不是拆成第二个 public helper；原因是它本来就完全依赖同一组输入，拆出去只会制造第二份接口。

## Deterministic validation rule

helper 当前至少应内建以下 contract 校验：

1. duplicate `work_item_id` -> `ValueError`
2. duplicate `group_item_id` -> `ValueError`
3. orphan `group_item.work_item_id` -> `ValueError`
4. binding 引用不存在的 `work_item_id` / `group_item_id` -> `ValueError`

但当前不在 Slice 2 里做：

1. graph target id 是否真的存在于某个 graph artifact
2. binding reason 的允许值全集
3. automatic binding inference

这些当前已留给 `design_docs/project-progress-graph-interactive-control-surface-slice2-graph-binding-contract-draft.md` 处理。

## Current no-change boundary

当前 helper 明确不做：

1. 不改写 `ProgressGraph` / `ProgressMultiGraphHistory` 的现有 doc-loop 拓扑语义
2. 不把 snapshot producer 反向做成 runtime owner
3. 不把 host overlay UI 逻辑塞进 helper
4. 不加入 direct action payload

## 当前推荐

我当前推荐：

1. 先把 `tools/progress_graph/control_snapshot.py` 固定为 snapshot producer owner
2. 先用一个 public pure helper 把 runtime primitive 翻译成 graph-facing root object
3. 下一窄切口再单独固定 binding contract，而不是在这里提前发明自动绑定逻辑

这样做能保证当前 active gate 继续沿 groundwork 前进，但不会误把 projection helper 写成新的 graph/runtime 混合 owner。