# Planning Gate — Project Progress Direction Analysis Candidate Projection

> 日期: 2026-04-26
> 状态: COMPLETE
> 关联方向分析: `design_docs/project-progress-phase-map-projection-followup-direction-analysis.md`

## 1. Why this gate exists

`design_docs/stages/planning-gate/2026-04-26-project-progress-phase-map-current-position-projection.md` 已完成并关闭。

当前已经有：

1. `tools/progress_graph/doc_projection.py` 已把 checkpoint / planning-gate / checklist / phase map 投影进 `.codex/progress-graph/latest.json`
2. `tools/progress_graph/export.py` / `graphviz.py` / `html_preview.py` 已把 current history 转成可直接查看的展示 artifact
3. `.codex/progress-graph/latest.html` 已能显示“已发生的推进事实”

但当前 preview 仍然缺少一类高价值信息：当前推荐的后续方向候选。最窄、最稳定、也最适合第一刀补进图里的来源，不是全局 `direction-candidates-after-phase-35.md`，而是当前 active 的 follow-up direction-analysis 文档 `design_docs/project-progress-phase-map-projection-followup-direction-analysis.md`。

## 2. Scope

本 gate 只处理：

1. 当前 active follow-up direction-analysis 文档的 candidate projection
2. candidate graph 的最小 graph contract 与推荐候选标记
3. direction candidate projection targeted tests
4. 真实 workspace artifact 刷新

本 gate 不处理：

1. `design_docs/direction-candidates-after-phase-35.md` 的全量 projection
2. 多篇 direction-analysis 自动发现或 ranking
3. richer doc-to-doc dependency inference
4. VS Code / WebView integration

## 3. Working hypothesis

当前最小可行路线应是：

1. 先只投影单篇当前 active 的 follow-up direction-analysis 文档
2. 把 `### A/B/C` 候选项投影成独立 candidate nodes，而不是一开始就支持任意候选文档集合
3. 把“当前 AI 倾向判断”映射成 recommended candidate 的状态或 metadata
4. 第一刀不需要方向文档自动发现；只需从 `design_docs/Project Master Checklist.md` 中解析最新的 `project-progress-*-followup-direction-analysis.md` 记录，即可形成可用的 current future-branch surface

## 4. Slices

### Slice 1 — Candidate projection contract

- 固定 graph id、source path、candidate node id、recommended candidate 表达方式

当前状态：已完成；Slice 1 设计草案已创建为 `design_docs/project-progress-direction-analysis-candidate-projection-slice1-draft.md`，并据此固定 `direction-analysis-current` graph contract。

### Slice 2 — Projection implementation

- 在 `tools/progress_graph/doc_projection.py` 中新增 direction-analysis graph builder
- 将新的 graph snapshot 接入 `build_doc_progress_history()`

当前状态：已完成；`tools/progress_graph/doc_projection.py` 已新增 `direction-analysis-current` graph，并从 Checklist 解析当前 `project-progress` follow-up direction-analysis source path。

### Slice 3 — Targeted tests and artifact refresh

- 扩展 `tests/test_progress_graph_doc_projection.py`
- 刷新 `.codex/progress-graph/latest.json`、`.dot`、`.html`

当前状态：已完成；`tests/test_progress_graph_doc_projection.py` 已通过 2 个 targeted tests，真实 workspace artifact 已刷新。

## 5. Validation gate

- `tests/test_progress_graph_doc_projection.py` 通过
- 新 candidate graph 能被 `.codex/progress-graph/latest.json` 正常持久化并读回
- 刷新后的 `.html` / `.dot` 能包含新增 direction-analysis graph

## 6. Stop condition

- 当 candidate projection contract、实现、targeted tests 与真实 artifact refresh 都已成立后停止
- 不在本 gate 内直接扩到全局 direction-candidates 聚合或自动发现