# 设计草案 — Project Progress Graph Interactive Control Surface Slice 2 Graph Binding Contract

本文是 `design_docs/stages/planning-gate/2026-05-06-project-progress-graph-interactive-control-surface.md` 的 Slice 2 设计草案，建立在 `design_docs/project-progress-graph-interactive-control-surface-snapshot-schema-draft.md` 与 `design_docs/project-progress-graph-interactive-control-surface-slice2-projection-helper-contract-draft.md` 已固定的 snapshot producer owner 之上。

## 目标

当前目标不是立刻推 host overlay，而是先固定 graph binding 的最小 contract，使 runtime item 可以稳定挂到 graph-facing target，而不让 runtime primitive 反向拥有 graph-specific state：

1. 哪一层拥有 binding normalization
2. binding row 的 canonical target 字段应该长什么样
3. binding anchor 应该依附 raw graph target 还是 display proxy
4. 第一版需要哪些 deterministic validation rule

本文不定义：

1. overlay UI 的具体 section layout
2. automatic binding inference algorithm
3. direct mutation controls
4. graph/export artifact 的实际代码实现

## 当前输入证据面

当前已有三组证据足以固定 binding contract：

1. snapshot schema 目前已为 `bindings` 预留 root-object 入口，但仍只处于 placeholder 粒度
2. projection helper contract 已明确：`build_control_snapshot(...)` 只消费“已经规范化完成的 binding rows”，不负责推断绑定目标
3. `tools/progress_graph/export.py` 已固定 graph-facing key 语义：
   - raw node / cluster 都有 graph-local id
   - consumer-facing key 使用 `_scoped_key(graph_id, local_id)`
   - display collapse 通过 `display.mapping` 单独表达

因此，当前最重要的局部判断是：

1. binding anchor 必须锚定到 raw graph target，而不是 display proxy id
2. consumer-facing contract 必须同时保留 `graph_target_id` 与 `graph_target_key`
3. display proxy 的解析应留给后续 overlay consumer surface，而不是在 binding row 里混入当前 display state

## 当前推荐的模块 owner

当前推荐新增独立 helper 模块：

- `tools/progress_graph/control_binding.py`

原因：

1. binding normalization 需要理解 progress_graph/export key 语义，但不属于 runtime/orchestration primitive
2. `tools/progress_graph/control_snapshot.py` 已被 Slice 2 projection helper contract 预留为 snapshot producer owner；将 binding normalization 邻接放置，可以保持 graph-facing contract 在同一子域内闭合
3. 如果把 binding normalization 放进 `src/runtime/orchestration/`，runtime primitive 会被迫知道 graph-specific target id / scoped key，边界会变脏

当前不推荐的放置方式：

1. 放进 `src/runtime/orchestration/projection.py`
2. 放进 `vscode-extension/`
3. 直接并到 `tools/progress_graph/export.py`

第 3 条也不推荐，因为 export 当前只负责已有 graph/history surface 的 user-facing导出，不应同时拥有 runtime binding normalization。

## 当前推荐的 normalized binding row

第一版 `graph_binding` 当前建议固定以下字段：

1. `binding_id`
2. `binding_kind`
   - 允许值：`node`、`cluster`、`graph-section`、`unbound-runtime-panel`
3. `graph_id`
4. `graph_target_id`
5. `graph_target_key`
6. `work_item_ids`
7. `group_item_ids`
8. `binding_reason`

字段语义：

1. `binding_id`
   - snapshot 内唯一的 binding 行 id
2. `binding_kind`
   - 表示当前绑定的是 raw node、raw cluster、保留中的 graph section，或显式未绑定面板
3. `graph_id`
   - 目标 graph 的 id；仅当 `binding_kind != "unbound-runtime-panel"` 时允许出现
4. `graph_target_id`
   - raw graph target 的 local id，而不是 display proxy id
5. `graph_target_key`
   - consumer-facing canonical key，必须等于 `graph_id::graph_target_id`
6. `work_item_ids` / `group_item_ids`
   - 当前绑定覆盖到的 runtime item ids；至少一者非空
7. `binding_reason`
   - 当前为什么把这些 runtime items 绑定到该 graph target

## Raw target vs display target rule

当前 contract 明确固定：

1. binding row 只锚定 raw target，不锚定当前 display proxy
2. `node` binding 的 `graph_target_id` 必须是 raw node id
3. `cluster` binding 的 `graph_target_id` 必须是 raw cluster id
4. 当前不在 binding row 里保存 `display_target_id` / `display_target_key`

原因：

1. display proxy 会受 collapse state 影响，而 raw node / cluster id 才是稳定 anchor
2. 现有 export surface 已经单独提供 `display.mapping`
3. 后续 overlay consumer 可以按 export mapping 把 raw anchor 解析成当前 display target，而不需要 binding contract 自己携带 display state

## Binding kind boundary

第一版当前建议按以下边界使用：

1. `node`
   - 用于一个或多个 runtime item 明确归属于某个 raw progress node
2. `cluster`
   - 用于 runtime item 更自然地归属于一个 cluster，而不是某个成员 node
3. `unbound-runtime-panel`
   - 用于当前没有稳定 graph target 的 runtime item
4. `graph-section`
   - 当前保留，但不作为第一实现入口；具体 section id 命名继续留给 overlay consumer contract

这意味着当前第一版真正要落地的 binding kind 是：

1. `node`
2. `cluster`
3. `unbound-runtime-panel`

## Binding reason minimal set

当前建议先固定最小 reason 集合：

1. `explicit-node-ref`
2. `explicit-cluster-ref`
3. `dominant-group-anchor`
4. `unbound-no-stable-target`
5. `reserved-section-route`

其中第 5 条当前只作为保留值，不要求第一版就使用。

## Deterministic validation rule

当前 binding normalizer 至少应内建以下校验：

1. duplicate `binding_id` -> `ValueError`
2. `binding_kind == "unbound-runtime-panel"` 时，`graph_id` / `graph_target_id` / `graph_target_key` 必须为空或缺失
3. `binding_kind != "unbound-runtime-panel"` 时，`graph_id` / `graph_target_id` / `graph_target_key` 必须全部存在
4. `graph_target_key` 必须严格等于 `graph_id::graph_target_id`
5. `work_item_ids` 与 `group_item_ids` 至少一者非空
6. 所有 `work_item_ids` / `group_item_ids` 必须能在当前 snapshot 输入面中找到对应项
7. 第一版中，一个 `work_item_id` 或 `group_item_id` 最多只允许出现在一条 binding row 中

当前不在 binding normalizer 里做：

1. dominant-group 自动推导
2. graph-section id 命名全集校验
3. host overlay DOM attachment

## Projection helper 接口边界

当前 binding contract 与 projection helper 的边界应明确分离：

1. `tools/progress_graph/control_binding.py`
   - 负责把 raw binding input 规范化成 `graph_binding[]`
   - 负责 target field consistency 与 scoped-key consistency
2. `tools/progress_graph/control_snapshot.py`
   - 只负责消费规范化后的 `graph_binding[]`
   - 不再重复做 target normalization

因此当前推荐的实现顺序是：

1. 先固定这份 binding row contract
2. 再由 `build_control_snapshot(...)` 接收规范化后的 bindings
3. 最后才进入 overlay consumer surface，去把 raw anchor 解析成 display proxy

## Current no-change boundary

当前 binding contract 明确不做：

1. 不让 runtime primitive 自己拥有 graph-specific target fields
2. 不在当前 row 里携带 display proxy state
3. 不在这个阶段引入 automatic binding inference
4. 不为 graph-section 先发明 UI layout 规则

## 当前推荐

我当前推荐：

1. 先把 `tools/progress_graph/control_binding.py` 固定为 binding normalizer owner
2. 先把 binding row 稳定到 raw target + scoped key 这对 canonical fields
3. 保持 overlay consumer 只做 raw -> display 的映射消费，而不是反向改 binding contract

这样做可以把当前 interactive control surface 主线里的第二个结构性 blocker 收口掉，而不会过早把 UI 或推断逻辑混进 contract。