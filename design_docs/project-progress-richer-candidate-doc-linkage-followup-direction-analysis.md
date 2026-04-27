# Project Progress Richer Candidate-Doc Linkage Follow-up Direction Analysis

## 当前已完成边界

`design_docs/stages/planning-gate/2026-04-26-project-progress-richer-candidate-doc-linkage-refinement.md` 已完成并关闭。

当前已经具备：

1. `direction-analysis-current` 与 `direction-candidates-global` 两层 candidate surface 都已进图
2. `basis_refs` 已能翻译成到 checklist / phase map / planning-gate / current direction-analysis 的 explicit linkage
3. `.codex/progress-graph/latest.json`、`.dot`、`.html` 已能显示 richer candidate-doc linkage
4. `progress_graph` 全套验证 17 passed

因此，当前最重要的问题已经不再是“candidate graphs 能不能和 factual graphs 连起来”，而是“接下来更该补外部参考层，还是直接把当前 preview 带进宿主内展示面”。

## 候选路线

### A. research-compass / external-reference projection（推荐）

- 做什么：继续把 [review/research-compass.md](review/research-compass.md) 这类外部研究入口的相关参考面投影到 progress graph，让当前候选方向不仅连到内部事实，还能连到外部借鉴来源。
- 依据：
  - [review/research-compass.md](review/research-compass.md)
  - [design_docs/project-progress-global-direction-candidates-aggregation-followup-direction-analysis.md](design_docs/project-progress-global-direction-candidates-aggregation-followup-direction-analysis.md)
  - [design_docs/project-progress-richer-candidate-doc-linkage-slice1-draft.md](design_docs/project-progress-richer-candidate-doc-linkage-slice1-draft.md)
- 风险：中。
- 当前判断：**推荐**。因为当前内部 doc surfaces 与 linkage 已经足够丰富，下一步最值得增加的信息是外部参考层。

### B. VS Code / host-specific preview integration

- 做什么：把现有 export / DOT / HTML preview 接到 VS Code WebView 或其他宿主展示面。
- 依据：
  - [design_docs/project-progress-html-preview-followup-direction-analysis.md](design_docs/project-progress-html-preview-followup-direction-analysis.md)
  - [docs/host-interaction-model.md](docs/host-interaction-model.md)
  - [vscode-extension/src/views/configPanel.ts](vscode-extension/src/views/configPanel.ts)
- 风险：中。
- 当前判断：仍有价值，但默认优先级低于候选 A。因为当前 preview 的数据层和链接层刚形成较完整闭环，先补外部参考层的收益更高。

### C. non-project-progress candidate aggregation

- 做什么：继续把 `design_docs/direction-candidates-after-phase-35.md` 中非 `project progress` 主线的候选块也纳入 projection。
- 依据：
  - [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md)
  - [design_docs/project-progress-global-direction-candidates-aggregation-slice1-draft.md](design_docs/project-progress-global-direction-candidates-aggregation-slice1-draft.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
- 风险：中到高。
- 当前判断：值得保留，但默认优先级低于候选 A/B。因为那会把当前窄 scope 从 progress 主线扩到整篇 backlog。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. 当前内部 doc surfaces 和 explicit linkage 已经形成较完整闭环
2. 现在最缺的不是新的内部 candidate 节点，而是这些候选与外部借鉴来源之间的可见关联
3. 若先把 research-compass 参考层补进来，后续无论继续做宿主内展示还是扩更宽的 candidate aggregation，信息增益都会更高