# Planning Gate — Project Progress Richer Candidate-Doc Linkage Refinement

> 日期: 2026-04-26
> 状态: COMPLETE
> 关联方向分析: `design_docs/project-progress-global-direction-candidates-aggregation-followup-direction-analysis.md`

## 1. Why this gate exists

`design_docs/stages/planning-gate/2026-04-26-project-progress-global-direction-candidates-aggregation.md` 已完成并关闭。

当前已经有：

1. `direction-analysis-current` graph，可展示当前一跳方向候选
2. `direction-candidates-global` graph，可展示更长跨度的 `project progress` 候选块
3. `.codex/progress-graph/latest.html` 已能显示 factual graphs 与 candidate graphs

但当前图层仍有一个明显缺口：candidate graphs 与 factual graphs 之间的显式 linkage 仍然偏薄，导致“为什么某个候选与哪些事实面相关”在图里不够清楚。

## 2. Scope

本 gate 只处理：

1. 文档型 graph 的稳定 source-document entry node
2. candidate node `basis_refs` -> factual graph / candidate graph 的最小 explicit linkage
3. richer candidate-doc linkage targeted tests
4. 真实 workspace artifact 刷新

本 gate 不处理：

1. 新的 doc source projection
2. 更复杂的 title-based semantic matching
3. VS Code / host-specific preview integration
4. 非 `project progress` 主线的 direction-candidates 泛化聚合

## 3. Working hypothesis

当前最小可行路线应是：

1. 给 checklist / phase map / global direction-candidates 这类文档型 graph 增加稳定的 source-document node
2. 把 current/global candidate nodes 中已有的 `basis_refs` 翻译成 explicit cross-graph edges
3. 优先利用显式 doc ref，而不是引入新的模糊语义匹配
4. 第一刀只做最小 linkage，不扩到新的 parser 或 ranking 逻辑

## 4. Slices

### Slice 1 — Linkage contract

- 固定 source-document node、doc-ref target surface 与 explicit linkage boundary

当前状态：已完成；Slice 1 设计草案已创建为 `design_docs/project-progress-richer-candidate-doc-linkage-slice1-draft.md`。

### Slice 2 — Linkage implementation

- 在 `tools/progress_graph/doc_projection.py` 中新增 source-document nodes
- 将 `basis_refs` 翻译成 cross-graph linkages

当前状态：已完成；`tools/progress_graph/doc_projection.py` 已接入 source-document nodes 与 candidate-doc explicit linkage。

### Slice 3 — Targeted tests and artifact refresh

- 扩展 `tests/test_progress_graph_doc_projection.py`
- 刷新 `.codex/progress-graph/latest.json`、`.dot`、`.html`

当前状态：已完成；`tests/test_progress_graph_doc_projection.py` 已通过 2 个 targeted tests，`progress_graph` 全套验证已通过。

## 5. Validation gate

- `tests/test_progress_graph_doc_projection.py` 通过
- `progress_graph` 全套验证通过
- 刷新后的 `.json` / `.dot` / `.html` 已反映 richer candidate-doc linkage

## 6. Stop condition

- 当 source-document node、candidate-doc linkage、targeted tests 与真实 artifact refresh 都已成立后停止
- 不在本 gate 内直接扩到新的 doc source projection 或 host-specific integration