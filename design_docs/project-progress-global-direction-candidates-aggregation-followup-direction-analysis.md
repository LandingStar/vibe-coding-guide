# Project Progress Global Direction Candidates Aggregation Follow-up Direction Analysis

## 当前已完成边界

`design_docs/stages/planning-gate/2026-04-26-project-progress-global-direction-candidates-aggregation.md` 已完成并关闭。

当前已经具备：

1. `tools/progress_graph/doc_projection.py` 已新增 `direction-candidates-global` graph，可把 `design_docs/direction-candidates-after-phase-35.md` 中与 `project progress` 主线直接相关的 section 投影到 current history
2. 每个相关 section 已可作为 section node 进入 graph，并把 `- 候选 1/2/3` 投影成 candidate nodes
3. 当前最新 section 的 recommended candidate 已可在 graph 中直接显示
4. `.codex/progress-graph/latest.json`、`.dot`、`.html` 已可展示更长跨度的候选分支面

因此，当前最重要的问题已经不再是“更长跨度的候选面能不能进图”，而是“这些候选面与已发生事实、planning-gate、phase map、current direction-analysis 之间是否已经形成足够清晰的 linkage”。

## 候选路线

### A. richer candidate-doc linkage refinement（推荐）

- 做什么：继续在 `direction-candidates-global`、`direction-analysis-current`、`phase-map-current-position`、`planning-gates-index`、`project-checklist-current` 之间补更细的显式 linkage，让候选分支与已发生事实之间的对应关系更清楚。
- 依据：
  - [design_docs/project-progress-global-direction-candidates-aggregation-slice1-draft.md](design_docs/project-progress-global-direction-candidates-aggregation-slice1-draft.md)
  - [design_docs/project-progress-direction-analysis-candidate-projection-followup-direction-analysis.md](design_docs/project-progress-direction-analysis-candidate-projection-followup-direction-analysis.md)
  - [design_docs/Global Phase Map and Current Position.md](design_docs/Global Phase Map and Current Position.md)
- 风险：中。
- 当前判断：**推荐**。因为 current 与 global 两层 candidate surface 都已经有了，但 graph 之间的语义连接仍然偏薄。

### B. research-compass / external-reference projection

- 做什么：继续把 [review/research-compass.md](review/research-compass.md) 这类外部研究入口的相关参考面投影到 progress graph，让候选方向与外部借鉴来源也能直接出现在图里。
- 依据：
  - [review/research-compass.md](review/research-compass.md)
  - [design_docs/project-progress-global-direction-candidates-aggregation-slice1-draft.md](design_docs/project-progress-global-direction-candidates-aggregation-slice1-draft.md)
  - [design_docs/project-progress-global-direction-candidates-aggregation.md](design_docs/stages/planning-gate/2026-04-26-project-progress-global-direction-candidates-aggregation.md)
- 风险：中。
- 当前判断：值得做，但默认优先级低于候选 A。因为在现有 candidate graphs 还没和事实图层对齐前，继续补外部参考层的收益更低。

### C. VS Code / host-specific preview integration

- 做什么：把现有 export / DOT / HTML preview 接到 VS Code WebView 或其他宿主展示面。
- 依据：
  - [design_docs/project-progress-html-preview-followup-direction-analysis.md](design_docs/project-progress-html-preview-followup-direction-analysis.md)
  - [docs/host-interaction-model.md](docs/host-interaction-model.md)
  - [vscode-extension/src/views/configPanel.ts](vscode-extension/src/views/configPanel.ts)
- 风险：中。
- 当前判断：仍有价值，但默认优先级低于候选 A/B。因为当前独立 artifact 已能直接打开，继续扩宿主 UI 不如先把 graph 语义连接补完整。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. 当前 graph 已经覆盖“当前一跳方向候选”和“更长跨度候选面”两层 candidate surface
2. 现在最明显的缺口已经变成 candidate graphs 与 factual graphs 之间的 linkage 质量
3. 若先把 linkage 收紧，后续无论继续补 research-compass 参考层还是做宿主内集成，信息增益都会更高