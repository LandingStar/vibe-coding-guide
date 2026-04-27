# Planning Gate — Project Progress User-Facing Graph Export Surface

> 日期: 2026-04-26
> 状态: COMPLETE
> 关联方向分析: `design_docs/project-progress-doc-loop-projection-followup-direction-analysis.md`

## 1. Why this gate exists

`design_docs/stages/planning-gate/2026-04-26-project-progress-doc-loop-projection-and-snapshot-persistence.md` 已完成并关闭。

当前已经有：

1. `tools/progress_graph/model.py` 的 authority multigraph model
2. `tools/progress_graph/query.py` 的查询面
3. `tools/progress_graph/doc_projection.py` 把 checkpoint / planning-gate / checklist 投影到 `.codex/progress-graph/latest.json`

但当前仍没有稳定的 user-facing export surface，因此真实 snapshot history 还不能作为 Graphviz / React Flow / compound-graph-friendly consumer 的直接输入。

## 2. Scope

本 gate 只处理：

1. 面向展示消费的稳定 export schema
2. 当前 graph snapshot 的 raw + display 双视图导出
3. cross-graph edge 的 display-aware export
4. export targeted tests

本 gate 不处理：

1. Graphviz DOT renderer 或 React Flow UI 组件
2. 新的 doc source projection
3. scheduler / daemon / orchestration bridge runtime integration
4. 基于完整历史链的 replay / diff UI

## 3. Working hypothesis

当前最小可行路线应是：

1. 复用 `ProgressGraph.summary()` 与 `build_condensed_view()` 形成稳定 display surface
2. 导出层显式保留 raw node id 与 display proxy id，避免 cluster 折叠后丢失可追溯性
3. 跨图 edge 必须同时暴露 raw endpoint 与 display endpoint，避免 consumer 自行重建 cluster 映射
4. 第一版只围绕 current graphs 导出；snapshot history 继续保存在 `.codex/progress-graph/latest.json`，不在本 gate 内重做另一套历史格式

## 4. Slices

### Slice 1 — Export contract

- 固定 top-level export schema、graph-level raw/display surface、scoped key 约定
- 固定 cross-graph edge 的 raw/display 双 endpoint 表达

当前状态：Slice 1 设计草案已创建为 `design_docs/project-progress-export-surface-slice1-draft.md`。

### Slice 2 — Pure helper implementation

- 新增 `tools/progress_graph/export.py`
- 暴露 graph-level / history-level export helper
- 将 export helper 接入 `tools/progress_graph/__init__.py`

当前状态：已完成。`tools/progress_graph/export.py` 已实现 `export_graph_surface()`、`export_history_surface()` 与 `load_export_surface()`，并已接入 `tools/progress_graph/__init__.py`。

### Slice 3 — Targeted tests

- 新增 `tests/test_progress_graph_export.py`
- 覆盖 cluster collapse mapping、cross-graph display endpoint、history-level summary surface

当前状态：已完成。`tests/test_progress_graph_export.py` 已新增并通过 `3 passed`。

## 5. Validation gate

- `tests/test_progress_graph_export.py` 通过
- export helper 能把当前 `ProgressMultiGraphHistory` 转成稳定 dict surface
- 导出层不需要修改 `.codex/progress-graph/latest.json` 的 authority format

当前结果：目标测试 `tests/test_progress_graph_export.py` 已通过 `3 passed`；新增 helper 可直接读取 history JSON 并输出稳定 export surface。

## 6. Stop condition

- 当 export contract、pure helper 与 targeted tests 都已落地并通过窄验证后停止
- 不在本 gate 内进入具体 UI renderer、layout engine 或 runtime consumer

当前结果：stop condition 已满足；后续方向已转入 `design_docs/project-progress-export-surface-followup-direction-analysis.md`。

## 7. Implementation results

本 gate 当前实际落地结果如下。

### 7.1 新增文件与职责

1. `tools/progress_graph/export.py`
	- 实现 graph-level / history-level export helper 与 history JSON load helper
2. `tests/test_progress_graph_export.py`
	- 实现 export targeted tests
3. `design_docs/project-progress-export-surface-slice1-draft.md`
	- 固定 export schema 与 scoped key 约定

### 7.2 已实现能力

当前已经实现：

1. graph-level raw export
	- 为 node / edge / cluster 暴露稳定 raw surface，并附带 scoped key
2. graph-level display export
	- 复用 `build_condensed_view()` 生成 display node / edge / mapping surface，并补 graph-scoped display key
3. cross-graph display-aware export
	- cross-graph edge 现同时暴露 raw endpoint 与 display endpoint，避免 consumer 重新推导 cluster 折叠映射
4. history-level export entry
	- 可把 current graphs、history summary、independent graph sets 与 global ready nodes 统一导出为单一 dict surface
5. history JSON load helper
	- `load_export_surface()` 可直接从 `.codex/progress-graph/latest.json` 一类 history 文件读出 export surface

### 7.3 当前未做的内容

本 gate 明确未进入：

1. Graphviz DOT writer 或 React Flow renderer
2. 新的 doc source projection
3. scheduler-facing runtime integration
4. 基于 snapshot history 的 replay / diff consumer