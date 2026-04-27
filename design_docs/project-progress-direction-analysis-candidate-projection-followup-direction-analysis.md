# Project Progress Direction Analysis Candidate Projection Follow-up Direction Analysis

## 当前已完成边界

`design_docs/stages/planning-gate/2026-04-26-project-progress-direction-analysis-candidate-projection.md` 已完成并关闭。

当前已经具备：

1. `tools/progress_graph/doc_projection.py` 已新增 `direction-analysis-current` graph，可把当前 `project-progress` follow-up direction-analysis 文档投影到 current history
2. 当前 source path 不再写死在单一文档，而是从 `design_docs/Project Master Checklist.md` 中解析最新的 `project-progress-*-followup-direction-analysis.md` 记录
3. `.codex/progress-graph/latest.json`、`.dot`、`.html` 已可展示当前 future-branch surface
4. `tests/test_progress_graph_doc_projection.py` 已通过 2 个 targeted tests

因此，当前最重要的问题已经不再是“单篇当前 direction-analysis 能不能进图”，而是“接下来更该补全局候选面，还是继续深挖当前 source 之间的 linkage / display 质量”。

## 候选路线

### A. global direction-candidates aggregation（推荐）

- 做什么：继续把 `design_docs/direction-candidates-after-phase-35.md` 中与 progress graph 主线直接相关的候选块投影到 progress graph，让图里不仅有当前一跳方向，还能看到更长跨度的候选分支面。
- 依据：
  - [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md)
  - [design_docs/project-progress-direction-analysis-candidate-projection-slice1-draft.md](design_docs/project-progress-direction-analysis-candidate-projection-slice1-draft.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
- 风险：中。
- 当前判断：**推荐**。因为当前只投影了单篇 current follow-up analysis，future-branch surface 仍然偏窄。

### B. richer candidate-doc linkage refinement

- 做什么：继续在 direction-analysis candidate graph 与已有 checkpoint / checklist / planning-gate / phase map graph 之间补更细的显式 linkage，让当前方向候选和已发生事实之间的对应关系更清楚。
- 依据：
  - [design_docs/project-progress-direction-analysis-candidate-projection-slice1-draft.md](design_docs/project-progress-direction-analysis-candidate-projection-slice1-draft.md)
  - [design_docs/project-progress-phase-map-projection-followup-direction-analysis.md](design_docs/project-progress-phase-map-projection-followup-direction-analysis.md)
  - [design_docs/Global Phase Map and Current Position.md](design_docs/Global Phase Map and Current Position.md)
- 风险：中。
- 当前判断：值得做，但默认优先级低于候选 A。因为在 future-branch surface 仍偏窄时，先补更长跨度的候选面信息增益更大。

### C. VS Code / host-specific preview integration

- 做什么：把现有 export / DOT / HTML preview 接到 VS Code WebView 或其他宿主展示面。
- 依据：
  - [design_docs/project-progress-html-preview-followup-direction-analysis.md](design_docs/project-progress-html-preview-followup-direction-analysis.md)
  - [docs/host-interaction-model.md](docs/host-interaction-model.md)
  - [vscode-extension/src/views/configPanel.ts](vscode-extension/src/views/configPanel.ts)
- 风险：中。
- 当前判断：仍有价值，但默认优先级低于候选 A/B。因为当前独立 artifact 已可直接打开，继续扩宿主 UI 不如先补更完整的数据覆盖。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. 当前 graph 已经首次具备“当前一跳方向候选”显示能力
2. 现在最明显的缺口已经变成“更长跨度的候选分支面是否也能直接进入图”
3. 若先把全局 direction-candidates 聚合面补进来，后续无论继续补 linkage 还是做宿主内集成，信息收益都会更高