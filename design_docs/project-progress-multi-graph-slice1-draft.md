# 设计草案 — Project Progress Multi-Graph Slice 1

本文是 `design_docs/stages/planning-gate/2026-04-26-project-progress-multi-graph-foundation.md` 的 Slice 1 设计草案。

## 目标

当前只固定 foundation contract：

1. graph 是 snapshot-backed 的，而不是只存当前状态
2. 多图之间允许完全独立，也允许通过 cross-graph edge 联动
3. `workflow` / `dependency` 负责调度顺序；`linkage` 负责联动语义，不进入 ready frontier 拓扑
4. cluster 提供第一版“节点团 -> 大节点”的压缩与展开能力

## 当前推荐的数据对象

当前推荐最小对象为：

1. `ProgressNode`
2. `ProgressEdge`
3. `ProgressCluster`
4. `CrossGraphEdge`
5. `ProgressGraph`
6. `ProgressMultiGraphHistory`

## 当前推荐的基础查询

当前推荐先固定以下 query primitive：

1. `ready_nodes()`
2. `topological_layers()`
3. `history_for(graph_id)`
4. `independent_graph_sets()`
5. `global_ready_nodes()`
6. `build_condensed_view()`

## 数学与现成结果映射

当前推荐直接借用：

1. DAG / topological sort：workflow、dependency
2. connected components：独立图集合
3. cluster / compound graph：展示与压缩
4. SCC / condensation：后续 cluster suggestion 与循环联动压缩的增强方向

## 当前判断

我当前判断这条 slice 值得优先，因为它能在不引入 UI 或调度 runtime 的前提下，先把 progress graph 的 authority data model 固定下来。