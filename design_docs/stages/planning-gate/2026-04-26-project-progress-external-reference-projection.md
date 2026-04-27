# Planning Gate — Project Progress External Reference Projection

> 日期: 2026-04-26
> 状态: COMPLETE
> 关联方向分析: `design_docs/project-progress-richer-candidate-doc-linkage-followup-direction-analysis.md`

## 1. Why this gate exists

`design_docs/stages/planning-gate/2026-04-26-project-progress-richer-candidate-doc-linkage-refinement.md` 已完成并关闭。

当前已经有：

1. `direction-analysis-current` 与 `direction-candidates-global` 两层 candidate surface
2. checklist / phase map / direction-candidates 的 stable `source-document` 节点
3. candidate `basis_refs` -> factual graph 的 explicit linkage

但当前图层仍缺一个直接空洞：外部研究入口还没有进入 progress graph。这意味着当前候选虽然已经能连到内部事实面，但还不能直接连到 `review/research-compass.md` 及其稳定的外部参考入口。

## 2. Scope

本 gate 只处理：

1. `review/research-compass.md` 的最小 external-reference projection
2. external-reference graph 的 stable source-document node 与 research entry nodes
3. candidate `basis_refs` -> external-reference graph 的最小 explicit linkage
4. targeted tests 与真实 artifact refresh

本 gate 不处理：

1. `review/` 全目录的泛化聚合
2. 复杂 topic ranking 或语义匹配
3. VS Code / host-specific preview integration
4. 非 `project progress` 主线的 backlog 聚合

## 3. Working hypothesis

当前最小可行路线应是：

1. 为 `review/research-compass.md` 新增一张独立 graph
2. 第一版只投影 stable `source-document` 与 `全量研究地图` 中可解析的研究条目
3. 复用现有 `basis_refs` -> doc ref target mapping，而不是另起新的链接机制
4. 第一刀优先保证 `review/research-compass.md` 这类入口文档能直接进图，不扩到更宽的研究知识图谱

## 4. Slices

### Slice 1 — Projection contract

- 固定 external-reference graph id、entry node 与 doc-ref target surface

当前状态：已完成；Slice 1 设计草案已创建为 `design_docs/project-progress-external-reference-projection-slice1-draft.md`。

### Slice 2 — Projection implementation

- 在 `tools/progress_graph/doc_projection.py` 中新增 `research-compass-current` graph
- 将 `review/research-compass.md` 的稳定入口节点纳入 doc ref target mapping

当前状态：已完成；`tools/progress_graph/doc_projection.py` 已新增 `research-compass-current` graph，并把 `review/research-compass.md` 与稳定研究条目接入现有 doc ref target mapping。

### Slice 3 — Targeted tests and artifact refresh

- 扩展 `tests/test_progress_graph_doc_projection.py`
- 刷新 `.codex/progress-graph/latest.json`、`.dot`、`.html`

当前状态：已完成；`tests/test_progress_graph_doc_projection.py` 已覆盖 external-reference 正例，真实 artifact 已刷新。

## 5. Validation gate

- `tests/test_progress_graph_doc_projection.py` 通过
- `progress_graph` 全套验证通过
- 刷新的 `.json` / `.dot` / `.html` 已包含 external-reference graph 与 linkage

## 6. Stop condition

- 当 external-reference graph、candidate -> external reference linkage、targeted tests 与真实 artifact refresh 都已成立后停止
- 不在本 gate 内继续泛化到 `review/` 其他研究文档或更宽的 topic graph