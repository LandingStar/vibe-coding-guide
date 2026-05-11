# Project Progress Richer Interactive Preview Follow-up Direction Analysis

## Completed boundary

`design_docs/stages/planning-gate/2026-04-30-project-progress-richer-interactive-preview-over-current-export-surface.md` 已完成并关闭。

当前已经具备：

1. 现有 `.codex/progress-graph/latest.html` / host preview 之上的最小交互层已经成立：graph-local search、status filter、selected node detail、focused reveal 可稳定工作
2. 当前交互面同时补上了 zoom controls 与 Ctrl+滚轮缩放，且仍保持在 artifact-side client interaction 边界内
3. `tests/test_progress_graph_html_preview.py` 已通过 focused validation（4 passed），默认 preview artifact 已刷新
4. 当前 gate 仍保持 no-change boundary：未重开 `doc_projection.py` / `export.py` schema、preview freshness signaling、handoff / safe-stop projection 或 renderer 重写
5. “大型项目里将部分节点打包为更大的可展开 compound node”这一需求已被明确记录，但按用户要求仍只停在记录层，不并入当前已完成切片

因此，当前 graph 主线已经不再是“第一版交互能否成立”，而是“在这条第一刀已成立后，下一条最值得进入的窄 follow-up 是什么”。

## Candidate A — Preview Freshness Signaling And Workflow Polishing（推荐）

- 做什么：围绕现有 host preview / artifact refresh workflow，补 stale hint、dirty badge、refresh state 与 artifact freshness 可见性，让当前交互面从“可探索”进一步变成“可稳定使用”
- 依据：
  - `design_docs/project-progress-user-interaction-after-bridge-mvp-direction-analysis.md`
  - `design_docs/project-progress-preview-artifact-refresh-pipeline-integration-followup-direction-analysis.md`
  - `design_docs/project-progress-graph-open-work-breakdown.md`
  - `design_docs/stages/planning-gate/2026-04-30-project-progress-richer-interactive-preview-over-current-export-surface.md`
- 风险：中。
- 当前判断：**推荐**。因为这条线最直接延续当前已完成的 preview 交互面，不需要立刻改写节点 identity / display contract，也最符合“先回到原主线”而不是继续扩新需求的节奏。

## Candidate B — Hierarchical Roll-Up / Expandable Compound Node Over Current Preview

- 做什么：围绕显式 `ProgressCluster` 或等价手工分组，把部分相关节点先打包为更大的 compound node，并提供按需 expand/collapse，用于控制大型项目里 graph 一次性暴露给用户的规模
- 依据：
  - `design_docs/project-progress-user-interaction-after-bridge-mvp-direction-analysis.md`
  - `design_docs/project-progress-graph-open-work-breakdown.md`
  - `design_docs/project-progress-graph-component-planning.md`
  - `design_docs/stages/planning-gate/2026-04-30-project-progress-richer-interactive-preview-over-current-export-surface.md`
- 风险：中。
- 当前判断：这条线已经有明确产品信号，而且技术上也成立；但用户刚刚明确要求“先停在记录”，因此它当前更适合作为已登记的下一候选，而不是默认立刻继续执行的主线。

## Candidate C — Handoff / Safe-Stop Projection Before Further Interaction Expansion

- 做什么：先把 graph 当前仍缺的 handoff / safe-stop family source 补进图面，再继续扩大更重的用户交互层
- 依据：
  - `design_docs/project-progress-graph-open-work-breakdown.md`
  - `design_docs/project-progress-graph-component-planning.md`
  - `design_docs/project-progress-user-interaction-after-bridge-mvp-direction-analysis.md`
- 风险：中。
- 当前判断：这条线在信息覆盖层面依然合理，但它会把主线重新拉回 source coverage，而不是继续沿已经成立的 preview 交互面向前收窄，因此优先级低于 Candidate A。

## Current AI inclination

我当前倾向于先进入 **Candidate A**。

原因是：

1. 当前第一版 richer interactive preview 已经成立，下一条最稳的主线不是再证明“交互能否做”，而是把它补到更可靠的日常使用面
2. Candidate B 虽然已经有明确需求，但用户已明确要求先停在记录层，不要顺势把这条新需求直接并进当前执行主线
3. Candidate C 仍有技术价值，但它会把节奏重新拉回 source coverage，而不是延续当前已建立的 preview / host interaction surface