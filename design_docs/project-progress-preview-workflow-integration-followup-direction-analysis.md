# Project Progress Preview Workflow Integration Follow-up Direction Analysis

## 当前已完成边界

`design_docs/stages/planning-gate/2026-04-26-project-progress-preview-workflow-integration.md` 已完成并关闭。

当前已经具备：

1. `vscode-extension/src/views/progressGraphPreview.ts` 已升级为 singleton `WebviewPanel` controller
2. progress graph preview 保持在 editor area 独立打开，不进入左侧窄侧栏
3. panel 内已经具备 `Refresh Preview` 与 `Reveal Artifact` 两个宿主工作流动作
4. `vscode-extension` 的 `npm run build` 已通过

因此，当前最重要的问题已经不再是“能不能单开一个 WebView”，而是“下一步应该优先打通 end-to-end 刷新链路，还是继续扩大 graph coverage / linkage depth”。

## 候选路线

### A. preview artifact refresh pipeline integration（推荐）

- 做什么：把当前 preview 的 `Refresh Preview` 从“重载现有 `.codex/progress-graph/latest.html`”继续推进到“先触发 artifact regenerate，再刷新 panel”的 end-to-end 宿主工作流。
- 依据：
  - [design_docs/stages/planning-gate/2026-04-26-project-progress-preview-workflow-integration.md](design_docs/stages/planning-gate/2026-04-26-project-progress-preview-workflow-integration.md)
  - [docs/host-interaction-model.md](docs/host-interaction-model.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
- 风险：中。
- 当前判断：**推荐**。因为当前 panel workflow 已经成立，但 `Refresh Preview` 仍然只会重载旧 artifact；把 regenerate + reload 打通，会比继续扩 parser 更快提升真实使用价值。

### B. non-project-progress candidate aggregation

- 做什么：继续把 `design_docs/direction-candidates-after-phase-35.md` 中非 `project progress` 主线的候选块也纳入 projection。
- 依据：
  - [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md)
  - [design_docs/project-progress-research-compass-topic-projection-followup-direction-analysis.md](design_docs/project-progress-research-compass-topic-projection-followup-direction-analysis.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
- 风险：中到高。
- 当前判断：值得保留，但默认优先级低于候选 A。因为它会扩大 projection scope，而当前 preview workflow 仍有明显的 end-to-end 缺口。

### C. topic-aware linkage refinement

- 做什么：围绕现有 `research-compass-current` topic layer，继续评估 preview / candidate linkage 是否要给 topic nodes 提供更直接的 landing 与交叉引用入口。
- 依据：
  - [design_docs/project-progress-research-compass-topic-projection-slice1-draft.md](design_docs/project-progress-research-compass-topic-projection-slice1-draft.md)
  - [review/research-compass.md](review/research-compass.md)
  - [design_docs/project-progress-richer-candidate-doc-linkage-slice1-draft.md](design_docs/project-progress-richer-candidate-doc-linkage-slice1-draft.md)
- 风险：中。
- 当前判断：可以作为 topic layer 成立后的自然深化方向，但默认优先级仍低于候选 A，因为当前更直接的用户价值缺口在 preview refresh 仍未打通 regenerate。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. “独立 WebView” 这一宿主承载问题已经收口
2. 当前剩余最直接的不顺滑点，是 panel refresh 还依赖外部先手动刷新 artifact
3. 先补 end-to-end refresh，再继续扩大 projection coverage 或 topic linkage，会让后续所有 graph 增量都更容易被直接消费