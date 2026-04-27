# Project Progress HTML Preview Slice 1 Draft

## 目标

把现有 progress export surface 变成一个可直接打开的自包含 HTML 预览文件，让用户无需 Graphviz 渲染步骤也能查看当前 progress graph。

## 当前建议的页面结构

1. 顶部 summary cards：graph 数量、ready nodes、cross-graph edge 数量
2. 每张 current graph 一个 section
3. 每个 graph section 内含：summary、inline SVG、ready node 列表
4. 页面底部保留 cross-graph edge 摘要列表

## 当前建议的 SVG boundary

1. 只消费 `display.nodes` / `display.edges`
2. 节点 x 轴按拓扑层；y 轴按层内顺序
3. cluster 节点保留单独样式，raw member 不直接绘制
4. 第一版不尝试全局跨图连线布局

## 当前建议的 artifact path

当前建议固定到：

1. `.codex/progress-graph/latest.html`

## 当前判断

这条 slice 足够窄，因为它只是在现有 export + DOT preview 之上补一个更直接可读的 HTML consumer，不引入前端框架、打包步骤或新数据来源。