# Planning Gate — Project Progress Non-Project-Progress Candidate Aggregation

> 日期: 2026-04-26
> 状态: COMPLETE
> 关联方向分析: `design_docs/project-progress-preview-artifact-refresh-pipeline-integration-followup-direction-analysis.md`

## 1. Why this gate exists

`design_docs/stages/planning-gate/2026-04-26-project-progress-preview-artifact-refresh-pipeline-integration.md` 已完成并关闭。

当前已经有：

1. `tools/progress_graph/doc_projection.py` 已把 `direction-candidates-after-phase-35.md` 中标题含 `project progress` 的 section 投影进 `direction-candidates-global` graph
2. standalone preview 已具备 end-to-end regenerate + reload workflow
3. 当前 progress graph 已能稳定消费 project-progress 主线候选块

当前最值得补进图里的下一层，不是继续打磨宿主 refresh，也不是马上深化 topic linkage，而是 `design_docs/direction-candidates-after-phase-35.md` 中仍未进入图面的非 `project progress` 候选块。

## 2. Scope

本 gate 只处理：

1. `design_docs/direction-candidates-after-phase-35.md` 中非 `project progress` 且使用 `### 新候选 A/B/C` 候选块的 `##` section aggregation projection
2. 在现有 `direction-candidates-global` graph 中补 section node + lettered candidate node 的最小 contract
3. candidate-local `当前判断：**推荐**` 到 recommended surface 的最小映射
4. targeted tests 与真实 workspace artifact refresh

本 gate 不处理：

1. 整篇 `direction-candidates-after-phase-35.md` 的全格式全量聚合
2. 纯 `### A./B./C.` 或 `### D./E./F.` 旧格式 backlog section
3. `用户选定下一步` / `当前更窄的入口` 等 companion prose 的语义建模
4. richer cross-doc relevance ranking 或 topic-aware linkage

## 3. Working hypothesis

当前最小可行路线应是：

1. 继续复用 `direction-candidates-global` graph，而不是再造新 graph id
2. 先只选 `direction-candidates-after-phase-35.md` 中标题不含 `project progress`、且 section 内存在 `### 新候选 A/B/C` 的 `##` block
3. 每个 section 先投影成 section node，再把 `### 新候选 A/B/C` 投影成 candidate nodes
4. candidate-local `当前判断：**推荐**` 足以支撑第一刀的 recommended candidate surface，不需要先解析所有 section-level narrative

## 4. Slices

### Slice 1 — Non-project-progress aggregation contract

- 固定 section selection boundary、lettered candidate heading contract、recommended surface

当前状态：已完成；Slice 1 设计草案已按实现口径收口为 `design_docs/project-progress-non-project-progress-candidate-aggregation-slice1-draft.md`。

### Slice 2 — Projection implementation

- 在 `tools/progress_graph/doc_projection.py` 中扩展 `direction-candidates-global` graph builder
- 将新的 non-project-progress section/candidate nodes 接入 `build_doc_progress_history()` 的现有 global direction-candidates 路径

当前状态：已完成；`tools/progress_graph/doc_projection.py` 已支持非 `project progress` 且采用 `### 新候选 A/B/C` 的 section，并把 candidate-local `当前判断：**推荐**` 映射到 recommended surface。

### Slice 3 — Targeted tests and artifact refresh

- 扩展 `tests/test_progress_graph_doc_projection.py`
- 刷新 `.codex/progress-graph/latest.json`、`.dot`、`.html`

当前状态：已完成；`tests/test_progress_graph_doc_projection.py` 已通过（2 passed），真实 workspace artifacts 已刷新。

## 5. Validation gate

- `tests/test_progress_graph_doc_projection.py` 通过
- `.codex/progress-graph/latest.json` 能包含新增 non-project-progress section/candidate nodes
- 刷新后的 `.html` / `.dot` 能包含扩展后的 `direction-candidates-global` graph，且不回归已有 project-progress sections

## 6. Stop condition

- 当 contract、实现、targeted tests 与真实 artifact refresh 都已成立后停止
- 不在本 gate 内扩到整篇全量格式解析或跨文档 relevance 聚合