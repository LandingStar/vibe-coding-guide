# Project Progress Host Preview Integration Follow-up Direction Analysis

## 当前已完成边界

`design_docs/stages/planning-gate/2026-04-26-project-progress-host-preview-integration.md` 已完成并关闭。

当前已经具备：

1. `vscode-extension` 已新增 `docBasedCoding.openProgressGraphPreview` 命令
2. 该命令会直接读取 `.codex/progress-graph/latest.html`，并在 VS Code WebView panel 中打开现有 preview artifact
3. 若 preview artifact 缺失，宿主内会显示明确 fallback，而不是静默失败
4. `vscode-extension` 的 `npm run build` 已通过

因此，当前最重要的问题已经不再是“宿主内有没有 progress graph 入口”，而是“下一步更值得继续补 graph 语义深度，还是继续把宿主预览工作流做得更顺滑”。

## 候选路线

### A. richer research-compass topic projection（推荐）

- 做什么：继续把 `review/research-compass.md` 的“按问题检索”或更细的 topic surface 投影到 progress graph，而不只停留在研究入口条目层。
- 依据：
  - [review/research-compass.md](review/research-compass.md)
  - [design_docs/project-progress-external-reference-projection-followup-direction-analysis.md](design_docs/project-progress-external-reference-projection-followup-direction-analysis.md)
  - [design_docs/project-progress-host-preview-integration-slice1-draft.md](design_docs/project-progress-host-preview-integration-slice1-draft.md)
- 风险：中。
- 当前判断：**推荐**。因为宿主内入口现在已经成立，下一步最值得新增的信息重新变回 graph 本身的语义密度。

### B. preview workflow integration

- 做什么：继续把 progress graph preview 的刷新/再打开/入口组织做成更顺滑的宿主工作流，而不只停留在单个打开命令。
- 依据：
  - [docs/host-interaction-model.md](docs/host-interaction-model.md)
  - [vscode-extension/src/extension.ts](vscode-extension/src/extension.ts)
  - [design_docs/stages/planning-gate/2026-04-26-project-progress-host-preview-integration.md](design_docs/stages/planning-gate/2026-04-26-project-progress-host-preview-integration.md)
- 风险：中。
- 当前判断：值得做，但默认优先级低于候选 A。因为在预览入口已经可用后，继续打磨工作流的收益暂时低于补 graph 内容本身。

### C. non-project-progress candidate aggregation

- 做什么：继续把 `design_docs/direction-candidates-after-phase-35.md` 中非 `project progress` 主线的候选块也纳入 projection。
- 依据：
  - [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
  - [design_docs/project-progress-global-direction-candidates-aggregation-slice1-draft.md](design_docs/project-progress-global-direction-candidates-aggregation-slice1-draft.md)
- 风险：中到高。
- 当前判断：可保留，但默认优先级低于候选 A/B。因为这会明显扩大当前 scope。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. 现在宿主内已经能直接打开 progress graph preview，最小消费入口成立
2. 继续做宿主工作流打磨的边际收益，暂时低于把 graph 的 external-reference 语义做得更细
3. 若先补 richer research topics，后续无论继续做 preview workflow 还是扩更宽的 candidate aggregation，宿主内验证都会更有内容