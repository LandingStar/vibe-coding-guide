# Project Progress Phase Map Projection Follow-up Direction Analysis

## 当前已完成边界

`design_docs/stages/planning-gate/2026-04-26-project-progress-phase-map-current-position-projection.md` 已完成并关闭。

当前已经具备：

1. `tools/progress_graph/doc_projection.py` 已新增 `phase-map-current-position` graph，把 `design_docs/Global Phase Map and Current Position.md` 的 recent date-prefixed timeline entries 投影进 current history
2. phase-map entry 中显式提到的 `design_docs/stages/planning-gate/*.md` 已可投影成到 `planning-gates-index` 的最小 cross-graph linkage
3. `.codex/progress-graph/latest.json`、`.dot`、`.html` 已按新 graph 刷新
4. `tests/test_progress_graph_doc_projection.py` 已通过 2 个 targeted tests，`progress_graph` 全套 17 个测试通过

因此，当前最重要的问题已经不再是“phase map recent history 能不能进图”，而是“接下来更该补未来方向候选面，还是继续只做现有 source 之间的 richer linkage”。

## 候选路线

### A. direction-analysis candidate projection（推荐）

- 做什么：继续把当前有效的 follow-up direction-analysis / direction-candidates 文档投影到 progress graph，让图里不仅有 recent history，还有下一步候选分支与当前推荐方向。
- 依据：
  - [design_docs/project-progress-html-preview-followup-direction-analysis.md](design_docs/project-progress-html-preview-followup-direction-analysis.md)
  - [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md)
  - [design_docs/Global Phase Map and Current Position.md](design_docs/Global Phase Map and Current Position.md)
- 风险：中。
- 当前判断：**推荐**。因为 recent history 已补进图，当前最大的可见信息缺口已经转为“未来方向/候选分支是否也能直接出现在图里”。

### B. richer linkage refinement over existing sources

- 做什么：继续在 checkpoint / checklist / planning-gate / phase map 之间补更多显式 dependency/linkage，让现有图的 cross-graph 断裂更少。
- 依据：
  - [design_docs/project-progress-phase-map-projection-slice1-draft.md](design_docs/project-progress-phase-map-projection-slice1-draft.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
  - [design_docs/Global Phase Map and Current Position.md](design_docs/Global Phase Map and Current Position.md)
- 风险：中。
- 当前判断：值得做，但默认优先级低于候选 A。因为在没有 future-branch surface 之前，继续只补 linkage 的边际收益会更低。

### C. VS Code / host-specific preview integration

- 做什么：把现有 export / DOT / HTML preview 接到 VS Code WebView 或其他宿主展示面。
- 依据：
  - [design_docs/project-progress-html-preview-followup-direction-analysis.md](design_docs/project-progress-html-preview-followup-direction-analysis.md)
  - [docs/host-interaction-model.md](docs/host-interaction-model.md)
  - [vscode-extension/src/views/configPanel.ts](vscode-extension/src/views/configPanel.ts)
- 风险：中。
- 当前判断：仍然有价值，但默认优先级低于候选 A/B。因为当前独立 HTML artifact 已能直接打开，先补方向候选面的信息密度更划算。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. checkpoint / planning-gate / checklist / phase map 这几类“已发生的推进事实”已经开始形成更完整的 current history
2. 当前图里最明显缺的已经不是过去事实，而是“下一步会往哪里走”的候选分支面
3. 若先把 direction-analysis candidate surface 投影出来，后续无论继续补 linkage 还是做宿主内集成，收益都会更高