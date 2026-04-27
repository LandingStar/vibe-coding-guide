# Project Progress Graphviz Preview Slice 1 Draft

## 目标

把现有 progress export surface 变成一个稳定的 DOT preview artifact，让用户无需前端 UI 即可查看当前 progress graph 的静态结构。

## 当前建议的 DOT boundary

1. 顶层使用单一 `digraph`
2. 每张 current graph 使用一个 `subgraph cluster_*`
3. graph 内只消费 `display.nodes` / `display.edges`
4. 跨图 edge 使用 `cross_graph_edges` 的 display endpoint

## 当前建议的 artifact path

当前建议固定到：

1. `.codex/progress-graph/latest.dot`

## 当前建议的样式约定

1. cluster 节点与普通节点使用不同 shape/style
2. node status 映射到有限的 fillcolor 集合
3. `workflow` / `dependency` / `linkage` 使用稳定的 line style 区分

## 当前判断

这条 slice 足够窄，因为它只是为现有 export contract 增加第一个静态 consumer，不进入外部图形依赖、UI 或新的数据来源。