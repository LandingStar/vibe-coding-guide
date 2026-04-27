# Planning Gate — Project Progress HTML Preview Consumer

> 日期: 2026-04-26
> 状态: COMPLETE
> 关联方向分析: `design_docs/project-progress-graphviz-preview-followup-direction-analysis.md`

## 1. Why this gate exists

`design_docs/stages/planning-gate/2026-04-26-project-progress-graphviz-preview-consumer.md` 已完成并关闭。

当前已经有：

1. `tools/progress_graph/export.py` 的稳定 raw + display export schema
2. `tools/progress_graph/graphviz.py` 的 DOT preview writer
3. `.codex/progress-graph/latest.dot` 的真实静态预览 artifact

但当前用户仍然拿到的是 DOT 文本，而不是可直接打开、无需额外渲染步骤的图形化预览。因此，图形展示功能还不能算“初步完成”。

## 2. Scope

本 gate 只处理：

1. 基于 export surface 的自包含 HTML preview writer
2. graph-level inline SVG 轻量布局
3. preview artifact path 与 write helper
4. HTML targeted tests

本 gate 不处理：

1. React Flow / 浏览器应用 / VS Code WebView 集成
2. Graphviz PNG/SVG 二进制渲染
3. 新的 doc source projection
4. scheduler / daemon / runtime integration

## 3. Working hypothesis

当前最小可行路线应是：

1. HTML preview 继续消费 export surface，而不是重新耦合底层 `ProgressGraph`
2. 每张 current graph 生成一个内联 SVG 画布，按 display node + 拓扑层做确定性轻量布局
3. cross-graph edge 先以摘要列表呈现，而不是在第一版里追求全局跨图空间布局
4. 第一版 artifact 固定写到 `.codex/progress-graph/latest.html`，不引入第三方前端依赖

## 4. Slices

### Slice 1 — HTML preview contract

- 固定 top-level 页面结构、SVG 布局边界、status/edge 样式映射
- 固定 artifact path 与 write helper boundary

当前状态：Slice 1 设计草案已创建为 `design_docs/project-progress-html-preview-slice1-draft.md`。

### Slice 2 — Writer implementation

- 新增 `tools/progress_graph/html_preview.py`
- 暴露 history -> HTML / file write helper
- 接入 `tools/progress_graph/__init__.py`

当前状态：已完成。`tools/progress_graph/html_preview.py` 已实现 `build_export_surface_html()`、`build_history_html()`、`write_history_html()` 与 `html_preview_path()`，并已接入 `tools/progress_graph/__init__.py`。

### Slice 3 — Targeted tests and real artifact write

- 新增 `tests/test_progress_graph_html_preview.py`
- 覆盖 graph section、collapsed cluster display、artifact write path

当前状态：已完成。`tests/test_progress_graph_html_preview.py` 已新增并通过 `3 passed`，真实 workspace 也已写出 `.codex/progress-graph/latest.html`。

## 5. Validation gate

- `tests/test_progress_graph_html_preview.py` 通过
- real workspace 能写出 `.codex/progress-graph/latest.html`
- preview artifact 不依赖外部 CDN、Graphviz binary 或前端打包步骤

当前结果：目标测试 `tests/test_progress_graph_html_preview.py` 已通过 `3 passed`；真实 workspace 中 `write_history_html(Path.cwd())` 已成功写出 `.codex/progress-graph/latest.html`。

## 6. Stop condition

- 当 HTML contract、writer、targeted tests 与 real artifact write 都已成立后停止
- 不在本 gate 内进入 richer interactive app、WebView host wiring 或数据补源

当前结果：stop condition 已满足；当前 `progress graph` 的轻量化图形展示已达到初步完成，后续方向已转入 `design_docs/project-progress-html-preview-followup-direction-analysis.md`。

## 7. Implementation results

本 gate 当前实际落地结果如下。

### 7.1 新增文件与职责

1. `tools/progress_graph/html_preview.py`
	- 实现 export surface -> self-contained HTML preview writer 与 artifact write helper
2. `tests/test_progress_graph_html_preview.py`
	- 实现 HTML preview targeted tests
3. `design_docs/project-progress-html-preview-slice1-draft.md`
	- 固定 HTML 页面结构、SVG 布局边界与 artifact path

### 7.2 已实现能力

当前已经实现：

1. self-contained HTML preview
	- 可直接把 current export surface 生成可打开的 `.html` 预览文件
2. graph-level inline SVG layout
	- 每张 current graph 现都可按 display node 与拓扑层生成确定性轻量布局
3. collapsed cluster friendly display
	- cluster 继续保留为单一 display node，raw member 不直接绘制
4. cross-graph edge summary
	- 第一版 HTML preview 以 display-aware 摘要列表表达跨图关系
5. 无外部依赖 artifact
	- 当前不依赖外部 CDN、Graphviz binary 或前端打包步骤即可产出 HTML preview

### 7.3 当前未做的内容

本 gate 明确未进入：

1. richer interactive app 或 VS Code WebView host wiring
2. Graphviz 图片渲染
3. 新的 doc source projection
4. scheduler / daemon / runtime integration