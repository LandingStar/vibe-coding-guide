# Project Progress User Interaction After Bridge MVP Direction Analysis

## Background

当前 bridge 主线已经把 MVP 技术边界收窄到最小 live delivery hook，并已满足以下条件：

1. thin bridge / governance kernel / owner-surface 三层边界仍保持分离
2. normalized dispatch result 已能最小回写到 `BridgeGroupItem`
3. focused validation 已通过

用户此前已明确顺序：

1. 先完成 orchestration bridge 的 MVP 阶段
2. bridge MVP 完成后，再回到 `progress_graph`
3. 回到 graph 时，优先考虑用户交互部分

因此，当前 graph 主线的判断标准不再是“先补哪一层 graph foundation”，而是：

1. 哪一条 graph 用户交互线最能直接消化当前已存在的 export / HTML / host preview 基础
2. 哪一条线能在不重新打开整个 graph backlog 的前提下，先把用户价值做出来
3. 哪一条线仍需要先补 coverage / semantics 前置，不能直接进入交互实现

## Current graph interaction baseline

当前已经存在、可直接作为用户交互起点的 graph 基线包括：

1. `.codex/progress-graph/latest.json`
2. `.codex/progress-graph/latest.dot`
3. `.codex/progress-graph/latest.html`
4. VS Code host preview panel
5. regenerate + reload refresh workflow

因此，当前 graph 的用户交互起点并不是“从零开始做第一版 preview”，而是“在现有 preview / host surface 上继续增强”。

## Candidate A — Richer Interactive Preview Over Current Export Surface（推荐）

- 做什么：
  - 在现有 HTML / host preview 基础上，补最小交互层，例如 graph filter、node detail、cluster expand/collapse、focused reveal
- 依据：
  - `design_docs/project-progress-graph-component-planning.md`
  - `design_docs/project-progress-graph-open-work-breakdown.md`
  - `design_docs/project-progress-html-preview-followup-direction-analysis.md`
  - `design_docs/project-progress-host-preview-integration-followup-direction-analysis.md`
- 风险：中。
- 当前判断：**推荐**。因为当前 preview 已经不是空壳，最直接的用户价值正好落在“让现有 preview 更像真正的交互面”，而不是再次回到基础展示证明。

当前还应把 Candidate A 下的一条保留需求单独看待：

1. 大型项目里的部分相关节点，需要能先打包为更大的 compound node，并在图中作为可展开节点控制一次性暴露给用户的 graph 规模；仅靠滚动、缩放或筛选，不足以稳定解决图面过大问题
2. 这条需求属于 Candidate A 的后续交互切片，而不是当前 active gate 已完成的第一刀；当前第一刀只覆盖 graph-local filter、detail 与 focused reveal
3. 第一版应优先复用显式 `ProgressCluster` 或等价的手工分组，并保留稳定 member mapping、原始节点 identity 与显式边界，而不是直接引入自动聚类或新的 renderer 重写

## Candidate B — Preview Freshness Signaling And Workflow Polishing

- 做什么：
  - 围绕现有 host preview，补 stale hint、dirty badge、refresh state、artifact freshness 可见性
- 依据：
  - `design_docs/project-progress-preview-artifact-refresh-pipeline-integration-followup-direction-analysis.md`
  - `design_docs/project-progress-graph-open-work-breakdown.md`
- 风险：中。
- 当前判断：合理，但优先级低于候选 A。因为它更像 workflow polish，而不是更强的 graph interaction 本身。

## Candidate C — Handoff / Safe-Stop Projection Before Interaction Expansion

- 做什么：
  - 先把 graph 当前最缺的 handoff / safe-stop family source 补进图面，再进入更重的 interaction layer
- 依据：
  - `design_docs/project-progress-graph-open-work-breakdown.md`
  - `design_docs/project-progress-graph-component-planning.md`
- 风险：中。
- 当前判断：仍有技术合理性，但优先级低于候选 A。因为用户已经明确希望 bridge MVP 之后先考虑 graph 用户交互；若先回到 coverage 扩展，会再次把当前节奏拉回基础层。

## Current AI inclination

我当前倾向于优先进入 **Candidate A**。

原因是：

1. 当前 graph preview / host surface 已具备最小闭环
2. 继续补 richer interaction，最能直接回应“回到 graph 时优先考虑用户交互”的要求
3. Candidate B 虽然也属于用户交互相关，但更偏 workflow polish；Candidate C 则会明显把主线重新拉回 source coverage