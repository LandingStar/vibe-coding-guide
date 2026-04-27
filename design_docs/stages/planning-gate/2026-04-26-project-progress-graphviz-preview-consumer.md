# Planning Gate — Project Progress Graphviz Preview Consumer

> 日期: 2026-04-26
> 状态: COMPLETE
> 关联方向分析: `design_docs/project-progress-export-surface-followup-direction-analysis.md`

## 1. Why this gate exists

`design_docs/stages/planning-gate/2026-04-26-project-progress-user-facing-graph-export-surface.md` 已完成并关闭。

当前已经有：

1. `tools/progress_graph/export.py` 的稳定 raw + display export schema
2. `load_export_surface()` 可直接读取 `.codex/progress-graph/latest.json`
3. `tests/test_progress_graph_export.py` 已验证 export contract

但当前仍没有真正把 export surface 变成可读展示产物的最小 consumer，因此用户仍无法直接查看一个静态图预览。

## 2. Scope

本 gate 只处理：

1. 基于 export surface 的最小 Graphviz DOT writer
2. preview artifact path 与 write helper
3. Graphviz targeted tests

本 gate 不处理：

1. Graphviz 二进制调用或图片渲染
2. React Flow / 前端 UI
3. 新的 doc source projection
4. scheduler / daemon / runtime integration

## 3. Working hypothesis

当前最小可行路线应是：

1. writer 应消费 export surface，而不是重新耦合底层 `ProgressGraph` 内部结构
2. 每张 current graph 在 DOT 中映射为一个 `subgraph cluster_*`
3. graph 内部边使用 display nodes / display edges；跨图 edge 使用 display-aware endpoint
4. 第一版 preview artifact 固定写到 `.codex/progress-graph/latest.dot`，不引入额外第三方依赖

## 4. Slices

### Slice 1 — DOT contract

- 固定 graph / cluster / node / edge 的 DOT 命名与 label 约定
- 固定 preview artifact path 与 write helper boundary

当前状态：Slice 1 设计草案已创建为 `design_docs/project-progress-graphviz-preview-slice1-draft.md`。

### Slice 2 — Writer implementation

- 新增 `tools/progress_graph/graphviz.py`
- 暴露 history -> DOT / file write helper
- 接入 `tools/progress_graph/__init__.py`

当前状态：已完成。`tools/progress_graph/graphviz.py` 已实现 `build_export_surface_dot()`、`build_history_dot()`、`write_history_dot()` 与 `dot_preview_path()`，并已接入 `tools/progress_graph/__init__.py`。

### Slice 3 — Targeted tests and real artifact write

- 新增 `tests/test_progress_graph_graphviz.py`
- 覆盖 graph cluster、display-aware edge、artifact write path

当前状态：已完成。`tests/test_progress_graph_graphviz.py` 已新增并通过 `3 passed`，真实 workspace 也已写出 `.codex/progress-graph/latest.dot`。

## 5. Validation gate

- `tests/test_progress_graph_graphviz.py` 通过
- real workspace 能写出 `.codex/progress-graph/latest.dot`
- writer 不需要依赖 Graphviz Python package 或外部 binary

当前结果：目标测试 `tests/test_progress_graph_graphviz.py` 已通过 `3 passed`；真实 workspace 中 `write_history_dot(Path.cwd())` 已成功写出 `.codex/progress-graph/latest.dot`。

## 6. Stop condition

- 当 DOT contract、writer、targeted tests 与 real artifact write 都已成立后停止
- 不在本 gate 内进入图片渲染、浏览器 UI 或 richer layout engine

当前结果：stop condition 已满足；后续方向已转入 `design_docs/project-progress-graphviz-preview-followup-direction-analysis.md`。

## 7. Implementation results

本 gate 当前实际落地结果如下。

### 7.1 新增文件与职责

1. `tools/progress_graph/graphviz.py`
	- 实现 export surface -> Graphviz DOT preview writer 与 artifact write helper
2. `tests/test_progress_graph_graphviz.py`
	- 实现 Graphviz targeted tests
3. `design_docs/project-progress-graphviz-preview-slice1-draft.md`
	- 固定 DOT contract 与 preview artifact path

### 7.2 已实现能力

当前已经实现：

1. export-surface-backed DOT writer
	- writer 直接消费 export surface，而不是重新耦合底层 graph model
2. graph cluster preview
	- 每张 current graph 现可映射为 DOT 中的 `subgraph cluster_*`
3. display-aware edge rendering
	- graph 内部边消费 `display.edges`，跨图边消费 `cross_graph_edges` 的 display endpoint
4. preview artifact write
	- 可直接写出 `.codex/progress-graph/latest.dot`
5. 无外部依赖 preview
	- 当前不依赖 Graphviz Python package 或外部 binary 即可产出 DOT artifact

### 7.3 当前未做的内容

本 gate 明确未进入：

1. Graphviz 图片渲染或 PNG/SVG 产物
2. React Flow / 浏览器 UI
3. 新的 doc source projection
4. scheduler-facing runtime integration