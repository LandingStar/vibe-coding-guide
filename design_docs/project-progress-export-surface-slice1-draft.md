# Project Progress Export Surface Slice 1 Draft

## 目标

把当前 `.codex/progress-graph/latest.json` 的 authority history 转成稳定、可展示、对 cluster 友好的 export schema，同时保持 raw node identity 可追溯。

## Top-level export surface

当前建议固定为：

1. `schema_version`
2. `history_metadata`
3. `history_summary`
4. `graphs`
5. `cross_graph_edges`
6. `independent_graph_sets`
7. `ready_nodes`

## Graph-level export surface

每张 current graph 当前建议同时暴露：

1. `graph_id` / `snapshot_id` / `title` / `recorded_at`
2. `summary`
3. `raw.nodes`
4. `raw.edges`
5. `raw.clusters`
6. `display.nodes`
7. `display.edges`
8. `display.mapping`
9. `ready_nodes`
10. `topological_layers`

## Key convention

当前建议固定：

1. `key = "{graph_id}::{local_id}"`
2. raw node / cluster / edge endpoint 保留本地 id，同时附 scoped key
3. cross-graph edge 同时暴露：
   - raw endpoint：`source_node_id` / `target_node_id`
   - display endpoint：`source_display_id` / `target_display_id`
   - scoped key：`source_key` / `target_key` / `source_display_key` / `target_display_key`

## 当前判断

这条 slice 足够窄，因为它只把既有 history 变成稳定消费面，不新增 doc projection，不进入 UI，不引入新的 persistence artifact。