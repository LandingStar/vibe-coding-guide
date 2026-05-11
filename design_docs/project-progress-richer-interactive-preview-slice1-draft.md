# Project Progress Richer Interactive Preview Slice 1 Draft

## 目标

把现有 `progress_graph` preview 从“可打开的静态 artifact”提升到“可直接探索当前项目推进状态的最小交互面”，同时保持当前 export / projection / host wiring 不变。

## 当前建议的交互 bundle

1. graph-local text filter
   - 允许按 node title / id / summary 做本图内搜索
2. graph-local status filter
   - 允许按 pending / in-progress / blocked / completed / archived 收窄当前图面
3. selected node detail
   - 点击 SVG node、ready item 或相关入口后，显示当前节点的 id、title、kind、status、summary、tags / metadata 摘要
4. focused reveal
   - 当前被选中的 node 在 SVG 与 detail panel 中同步高亮；必要时支持从 ready list 快速定位到图上对应节点

## 当前建议的数据边界

1. 只消费 `build_export_surface_html(...)` 当前已拿到的 `surface` 数据
2. 具体只依赖：`graphs[*].raw`、`graphs[*].display`、`graphs[*].ready_nodes`、`cross_graph_edges`
3. 不新增 `doc_projection.py` parser、`export.py` schema 字段或 extension host message

## 当前建议的 UI boundary

1. control strip 放在 graph section 内，而不是新增全局复杂 toolbar
2. detail panel 优先作为 graph section 侧栏中的新卡片，不重做整页布局
3. SVG layout 继续保持当前 deterministic static layout，不在本 slice 内重排节点

## 当前明确不做

1. cluster expand / collapse
2. preview freshness、dirty badge、artifact staleness hint
3. handoff / safe-stop projection
4. cross-graph interactive routing 或第二宿主差异化 UI

## 当前判断

这条 slice 足够窄，因为它只在现有 HTML artifact 里增加最小 client-side state；它既不需要新数据源，也不需要新宿主接口，能直接用 `tests/test_progress_graph_html_preview.py` 做窄验证。

## 2026-04-30 Implementation Note

当前草案对应的第一版实现已经落地：

1. graph section 内新增了 graph-local search + status chips
2. SVG node 与 ready item 现在可驱动 selected node detail 和 focused reveal
3. 交互层继续只消费现有 `graphs[*].raw` / `graphs[*].display` / `ready_nodes`
4. 当前 targeted validation 为 `tests/test_progress_graph_html_preview.py` 4 passed，默认 `.codex/progress-graph/latest.html` 已刷新