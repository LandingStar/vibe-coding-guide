# Planning Gate — Project Progress Phase Map Current Position Projection

> 日期: 2026-04-26
> 状态: COMPLETE
> 关联方向分析: `design_docs/project-progress-html-preview-followup-direction-analysis.md`

## 1. Why this gate exists

`design_docs/stages/planning-gate/2026-04-26-project-progress-html-preview-consumer.md` 已完成并关闭。

当前已经有：

1. `tools/progress_graph/doc_projection.py` 把 checkpoint / planning-gate / checklist 投影到 `.codex/progress-graph/latest.json`
2. `tools/progress_graph/export.py` / `graphviz.py` / `html_preview.py` 已把 current history 变成可直接查看的展示 artifact
3. `.codex/progress-graph/latest.html` 已提供第一版轻量化图形展示

但当前 preview 的主要缺口已经不再是“能不能展示”，而是“展示面里是否覆盖足够高价值的推进来源”。当前最稳定、最权威、且最适合先补的一类来源，是 `design_docs/Global Phase Map and Current Position.md` 中的 recent history / current position timeline。

## 2. Scope

本 gate 只处理：

1. `Global Phase Map and Current Position.md` 的 recent history projection
2. phase map entry -> planning-gate 的最小 linkage
3. phase map projection targeted tests
4. 真实 workspace artifact 刷新

本 gate 不处理：

1. direction-analysis 文档 projection
2. richer dependency inference beyond explicit planning-gate refs
3. HTML/WebView 继续扩展
4. scheduler / daemon / runtime integration

## 3. Working hypothesis

当前最小可行路线应是：

1. 只从 `Global Phase Map and Current Position.md` 提取 recent date-prefixed timeline entries，而不是试图完整理解整篇 phase narrative
2. recent history 应投影成独立 graph snapshot，先服务于展示与历史回看
3. 若 phase-map entry 文本显式提到某个 planning-gate 路径，则可建立最小 cross-graph linkage
4. 第一刀不需要通用 markdown parser；复用现有 regex + heading helper 即可完成

## 4. Slices

### Slice 1 — Phase map projection contract

- 固定 graph id、recent-entry selection boundary、node id 约定、planning-gate linkage boundary

当前状态：已完成；Slice 1 设计草案已创建为 `design_docs/project-progress-phase-map-projection-slice1-draft.md`，并据此固定 `phase-map-current-position` graph contract。

### Slice 2 — Projection implementation

- 在 `tools/progress_graph/doc_projection.py` 中新增 phase map graph builder
- 将 phase map snapshot 接入 `build_doc_progress_history()`
- 扩展 cross-graph linkage builder

当前状态：已完成；`tools/progress_graph/doc_projection.py` 已新增 phase map recent-history projection，并把显式 planning-gate 引用接入 cross-graph linkage。

### Slice 3 — Targeted tests and real artifact refresh

- 扩展 `tests/test_progress_graph_doc_projection.py`
- 刷新 `.codex/progress-graph/latest.json`、`.dot`、`.html`

当前状态：已完成；`tests/test_progress_graph_doc_projection.py` 已通过 2 个 targeted tests，`progress_graph` 全套 17 个测试通过，真实 workspace artifact 已刷新。

## 5. Validation gate

- `tests/test_progress_graph_doc_projection.py` 通过
- 新 graph 能被 `.codex/progress-graph/latest.json` 正常持久化并读回
- 刷新后的 `.html` / `.dot` 能包含新增 source graph

## 6. Stop condition

- 当 phase map projection contract、实现、targeted tests 与真实 artifact refresh 都已成立后停止
- 不在本 gate 内直接进入 direction-analysis 或 richer inference 主线