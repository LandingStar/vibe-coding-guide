# Project Progress Preview Artifact Refresh Pipeline Integration Follow-up Direction Analysis

## 当前已完成边界

`design_docs/stages/planning-gate/2026-04-26-project-progress-preview-artifact-refresh-pipeline-integration.md` 已完成并关闭。

当前已经具备：

1. standalone progress graph preview 已保持 singleton `WebviewPanel`
2. `Refresh Preview` 已从单纯 reload 提升为 regenerate `.codex/progress-graph/latest.json` / `.dot` / `.html` 后再 reload panel
3. extension 已复用当前 workspace Python 与现有 `tools.progress_graph` 生成链
4. `npm run build` 已通过，且真实 regenerate 验证已成功写出三类 artifacts

因此，当前最重要的问题已经不再是“preview 刷新是不是端到端”，而是“下一步应优先扩大 graph coverage，还是继续深化现有 topic/linkage / host workflow”。

## 候选路线

### A. non-project-progress candidate aggregation（推荐）

- 做什么：继续把 `design_docs/direction-candidates-after-phase-35.md` 中非 `project progress` 主线的候选块也纳入 projection，让当前 multigraph 更接近最初“多方向推进历史”的目标。
- 依据：
  - [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
  - [design_docs/project-progress-preview-artifact-refresh-pipeline-integration-followup-direction-analysis.md](design_docs/project-progress-preview-artifact-refresh-pipeline-integration-followup-direction-analysis.md)
- 风险：中。
- 当前判断：**推荐**。因为 host preview 的最小消费链已经顺了，当前更值得把 graph breadth 扩到更多真实方向，而不是继续围绕同一宿主动作打转。

### B. topic-aware linkage refinement

- 做什么：围绕现有 `research-compass-current` topic layer，继续评估是否要为 topic nodes 提供更直接的 preview landing / candidate linkage / cross-graph reference。
- 依据：
  - [design_docs/project-progress-research-compass-topic-projection-slice1-draft.md](design_docs/project-progress-research-compass-topic-projection-slice1-draft.md)
  - [review/research-compass.md](review/research-compass.md)
  - [design_docs/project-progress-richer-candidate-doc-linkage-slice1-draft.md](design_docs/project-progress-richer-candidate-doc-linkage-slice1-draft.md)
- 风险：中。
- 当前判断：值得保留，但默认优先级低于候选 A。因为目前更大的价值缺口已经从 host refresh 转到 graph breadth。

### C. preview freshness signaling / auto-refresh watcher

- 做什么：继续围绕 standalone preview，评估是否需要在 artifacts 变化时提供 dirty-state 提示、自动刷新或 watcher-driven refresh。
- 依据：
  - [design_docs/stages/planning-gate/2026-04-26-project-progress-preview-artifact-refresh-pipeline-integration.md](design_docs/stages/planning-gate/2026-04-26-project-progress-preview-artifact-refresh-pipeline-integration.md)
  - [docs/host-interaction-model.md](docs/host-interaction-model.md)
  - [vscode-extension/src/views/progressGraphPreview.ts](vscode-extension/src/views/progressGraphPreview.ts)
- 风险：中。
- 当前判断：是自然延伸，但默认优先级低于候选 A，因为当前手动 refresh 已经 end-to-end 成立，watcher 不是最直接的价值增量。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. preview consume path 已经从“能看”收口到“能端到端刷新”
2. 当前更稀缺的信息不是 refresh 行为，而是更多真实方向是否能进入图里
3. 把 non-project-progress candidates 纳入 projection，会更直接回应最初“多方向推进历史”的目标