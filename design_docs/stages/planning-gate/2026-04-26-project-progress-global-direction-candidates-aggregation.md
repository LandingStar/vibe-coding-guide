# Planning Gate — Project Progress Global Direction Candidates Aggregation

> 日期: 2026-04-26
> 状态: COMPLETE
> 关联方向分析: `design_docs/project-progress-direction-analysis-candidate-projection-followup-direction-analysis.md`

## 1. Why this gate exists

`design_docs/stages/planning-gate/2026-04-26-project-progress-direction-analysis-candidate-projection.md` 已完成并关闭。

当前已经有：

1. `tools/progress_graph/doc_projection.py` 已把 checkpoint / planning-gate / checklist / phase map / current direction-analysis 投影进 `.codex/progress-graph/latest.json`
2. `.codex/progress-graph/latest.html` 已可同时展示“已发生的推进事实”与“当前一跳方向候选”
3. 当前 progress graph 仍缺少更长跨度的候选分支面

当前最值得补进图里的下一层，不是新的宿主 UI，也不是更细的 linkage，而是 `design_docs/direction-candidates-after-phase-35.md` 中已经沉淀下来的 `project progress` 主线候选块。

## 2. Scope

本 gate 只处理：

1. `design_docs/direction-candidates-after-phase-35.md` 中 `project progress` 相关 section 的 aggregation projection
2. section node + candidate node 的最小 graph contract
3. global direction candidates projection targeted tests
4. 真实 workspace artifact 刷新

本 gate 不处理：

1. 整篇 `direction-candidates-after-phase-35.md` 的全量聚合
2. 非 `project progress` 主线 section 的 relevance 判定
3. richer cross-graph linkage inference
4. VS Code / host-specific preview integration

## 3. Working hypothesis

当前最小可行路线应是：

1. 只投影 `direction-candidates-after-phase-35.md` 中标题含 `project progress` 的 section
2. 每个 section 先投影成一个 section node，再把 `- 候选 1/2/3` 投影成 candidate nodes
3. `- 当前倾向` 可映射为 section metadata 与 recommended candidate status
4. 第一刀不需要全局 relevance ranking；只抓稳定的 progress-graph 主线块即可

## 4. Slices

### Slice 1 — Aggregation contract

- 固定 graph id、section boundary、candidate node id、recommended candidate 表达方式

当前状态：已完成；Slice 1 设计草案已创建为 `design_docs/project-progress-global-direction-candidates-aggregation-slice1-draft.md`，并据此固定 `direction-candidates-global` graph contract。

### Slice 2 — Projection implementation

- 在 `tools/progress_graph/doc_projection.py` 中新增 global direction-candidates graph builder
- 将新的 graph snapshot 接入 `build_doc_progress_history()`

当前状态：已完成；`tools/progress_graph/doc_projection.py` 已新增 `direction-candidates-global` graph，并把 `direction-candidates-after-phase-35.md` 中标题含 `project progress` 的 section 投影成 section + candidate nodes。

### Slice 3 — Targeted tests and artifact refresh

- 扩展 `tests/test_progress_graph_doc_projection.py`
- 刷新 `.codex/progress-graph/latest.json`、`.dot`、`.html`

当前状态：已完成；`tests/test_progress_graph_doc_projection.py` 已通过 2 个 targeted tests，真实 workspace artifact 已刷新。

## 5. Validation gate

- `tests/test_progress_graph_doc_projection.py` 通过
- 新 graph 能被 `.codex/progress-graph/latest.json` 正常持久化并读回
- 刷新后的 `.html` / `.dot` 能包含新增 global direction-candidates graph

## 6. Stop condition

- 当 aggregation contract、实现、targeted tests 与真实 artifact refresh 都已成立后停止
- 不在本 gate 内扩到整篇全局 candidate backlog 的自动 relevance 聚合