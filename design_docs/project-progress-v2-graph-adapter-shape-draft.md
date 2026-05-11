# Project Progress V2 Graph Adapter Shape Draft

本文服务于 `design_docs/stages/planning-gate/2026-05-07-sigma-graphology-v2-graph-view-poc.md`，用于固定一个最小问题：

当前若以 `Sigma.js + Graphology` 做第一轮 V2 graph-view PoC，那么现有 export / control snapshot 应如何被适配成一个 graph renderer 可消费、同时不破坏上游 contract 的最小 graph model？

## Adapter goal

当前 adapter 不应该承担业务解释器或新的 source-of-truth owner，而只回答三件事：

1. 哪些 export 数据进入 graph structure
2. 哪些 control snapshot 数据进入 runtime overlay
3. 哪些 V2 局部状态仍留给 renderer 本地管理

## Input A — graph export surface

当前 adapter 继续复用 export surface 中的这些字段：

1. graph id
2. nodes
3. edges
4. clusters
5. display mapping
6. scoped key / raw target identity

这些字段负责生成 V2 graph 的结构底图。

## Input B — control snapshot

当前 adapter 继续复用 `control-snapshot.json` 中的这些字段：

1. summary
2. work items
3. group items
4. bindings

这些字段不改变 graph structure，而是作为 runtime overlay signal：

1. 哪些节点存在 runtime binding
2. 哪些 group/work item 当前 unbound
3. 哪些状态需要在 detail / highlight / panel 中抬升

## Adapter output shape

当前建议 PoC adapter 输出一个最小三段式对象：

1. `graph`
   - renderer 直接消费的 nodes / edges
2. `runtimeOverlay`
   - 由 control snapshot 投影出的 binding / summary / detail 索引
3. `meta`
   - graph id、generated time、freshness-adjacent 元信息

### graph.nodes

每个 node 当前至少需要：

1. `id`
2. `label`
3. `kind`
4. `status`
5. `rawTargetIds`
6. `clusterId`（若存在）
7. `scopedKey`

其中：

1. `id` 是 V2 renderer 使用的 display node id
2. `rawTargetIds` 保留当前 display mapping 对应的 raw member ids
3. `status` 继续复用 export / source graph 当前已经显式可见的状态语义

### graph.edges

每个 edge 当前至少需要：

1. `id`
2. `source`
3. `target`
4. `kind`
5. `directed`

这里不引入额外 workflow 语义推断，继续复用当前 export 已有边类型。

### runtimeOverlay.bindingIndex

当前建议预计算：

1. `byDisplayNodeId`
2. `byRawTargetId`
3. `unboundRows`

目的：

1. renderer 不直接遍历整个 snapshot 去找绑定
2. detail / hover / adjacency 高亮可以直接查索引

### runtimeOverlay.itemIndex

当前建议预计算：

1. `workItemsById`
2. `groupItemsById`

目的：

1. detail panel / companion block 可直接读取 runtime 摘要
2. 避免 graph layer 自己承担 snapshot normalization

## Explicit no-change boundary

当前 adapter 明确不做：

1. 不从 graph view 反写 export 或 control snapshot
2. 不在 adapter 中定义 control panel action semantics
3. 不在 adapter 中实现 graph-to-work 接口补洞
4. 不在 adapter 中持有 viewport / animation / drag 等纯 renderer 本地状态

## Interface preflight hook

当前 adapter shape 应为后续接口检查保留一个显式入口：

1. 当未来准备进入 control panel 深化时，先检查 runtimeOverlay 中现有 binding / work-item / group-item 索引是否已足够支撑目标状态与动作
2. 若不够，则问题归类为“接口缺口”，回到接口处理切片，而不是继续把逻辑压进 adapter 或 panel

## Current recommendation

当前第一版 PoC adapter 应保持足够薄：

1. export 只负责 graph structure
2. control snapshot 只负责 runtime overlay
3. renderer 本地状态继续留在 Sigma.js + Graphology 层

这样后面无论继续走 Sigma.js 还是转向 Cytoscape.js，都还能复用同一批 adapter 输入与边界判断。