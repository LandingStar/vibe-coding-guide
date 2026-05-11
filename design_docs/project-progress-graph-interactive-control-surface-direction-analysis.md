# Project Progress Graph Interactive Control Surface Direction Analysis

## Background

当前 `progress_graph` 已经具备：

1. doc-loop progress history 的 authority graph surface
2. HTML preview + VS Code host preview
3. graph-local search / detail / focused reveal / freshness workflow

但用户现在提出的新目标，已经不是“让 preview 更稳定”或“再补一点交互”，而是：

1. 让 graph 变成可以直接交互的 control page
2. 可以直接从 graph 查看节点状态
3. 可以看到各个 agent / worker 当前工作节点
4. 进一步演进到 graph 上的控制入口

这里最关键的现状判断是：

1. 当前 `tools/progress_graph/doc_projection.py` 还没有投影任何 orchestration runtime / bridge state family
2. 当前 bridge runtime 虽然已经有 `BridgeGroupItem` / `BridgeWorkItem` 等 compact primitive，但它们仍主要停留在 helper / runtime contract 层，而不是稳定持久化、可被 graph consumer 直接读取的 control-plane source
3. 因此，当前最大缺口不是 renderer，而是“graph control surface 应消费哪一份最小 runtime 状态快照”

## Current relevant surfaces

当前最接近控制面需求的现有 surface 有两组。

### A. graph side

1. `tools/progress_graph/model.py`
2. `tools/progress_graph/doc_projection.py`
3. `tools/progress_graph/export.py`
4. `tools/progress_graph/html_preview.py`
5. `vscode-extension/src/views/progressGraphPreview.ts`

这组 surface 已能稳定表达：

1. 节点 / 边 / cluster / cross-graph linkage
2. ready nodes / topological layers
3. artifact preview 与 host-side inspection

但它目前主要消费的是文档推进事实，而不是运行中的 bridge / agent state。

### B. orchestration side

1. `src/runtime/orchestration/models.py`
2. `src/runtime/orchestration/projection.py`
3. `src/runtime/orchestration/rollup.py`
4. `src/runtime/orchestration/coordinator.py`

这组 surface 已有最小 compact state：

1. `BridgeGroupItem.lifecycle_state`
2. `BridgeGroupItem.governance_surface_kind` / `governance_surface_state`
3. `BridgeGroupItem.delivery_surface_kind` / `delivery_state`
4. `BridgeGroupItem.current_gate_state` / `open_items` / `blocked_reason`
5. `BridgeWorkItem.lifecycle_state`
6. `BridgeWorkItem.rollup_surface_kind` / `rollup_surface_state`
7. `BridgeWorkItem.dominant_group_item_ids`
8. `BridgeWorkItem.open_group_item_count`

但当前仍缺：

1. 这组状态的稳定 projection / snapshot owner
2. 它与 `progress_graph` node identity 的明确映射 contract
3. 可直接进入 preview / host surface 的统一读取入口

## Candidate A — Read-Only Graph Control Overlay Over Current Preview Surface（推荐）

- 做什么：
  - 先把 graph 提升为只读 control surface，而不是一开始就做可变控制台
  - 新增最小 orchestration control snapshot，把 `BridgeWorkItem` / `BridgeGroupItem` 的 compact state 映射到 graph 可消费的数据面
  - 在现有 preview / host surface 上补一层 control overlay，使用户能直接看到：节点状态、当前 work-item/group-item、dominant lineage、delivery/governance state，以及“谁正在处理这一步”
- 依据：
  - `design_docs/project-progress-graph-component-planning.md`
  - `design_docs/project-progress-graph-open-work-breakdown.md`
  - `design_docs/project-progress-user-interaction-after-bridge-mvp-direction-analysis.md`
  - `src/runtime/orchestration/models.py`
  - `src/runtime/orchestration/rollup.py`
- 风险：中。
- 当前判断：**推荐**。因为它最直接回应“从 graph 查看状态 / agent 当前工作节点”的诉求，同时不要求当前仓库先解决 action ownership、daemon persistence 与 live process control 的重问题。

## Candidate B — Orchestration State Projection First, UI Second

- 做什么：
  - 先不碰 host control UI，而是先把 orchestration runtime state 纳入 `progress_graph` source family
  - 新增独立 graph 或 metadata projection，用于表达 `BridgeWorkItem` / `BridgeGroupItem` 当前状态，再让后续 preview 消费它
- 依据：
  - `design_docs/project-progress-graph-open-work-breakdown.md`
  - `design_docs/project-progress-graph-component-planning.md`
  - `design_docs/orchestration-bridge-delivery-signal-integration-hook-slice2-draft.md`
  - `design_docs/orchestration-bridge-daemon-contract-first-slice2-group-item-projection-draft.md`
- 风险：中。
- 当前判断：技术上更干净，但用户可见价值到达更慢；若当前目标是“尽快把 graph 变成控制页入口”，它不是最合适的第一刀。

## Candidate C — Full Interactive Control Console With Direct Actions

- 做什么：
  - 让 graph 不只是看状态，还能直接触发动作，例如 refresh / reveal 之外的 retry、handoff、review intake、owner-facing controls
  - 将 node/card 直接变成命令入口
- 依据：
  - `design_docs/project-progress-graph-component-planning.md`
  - `design_docs/project-progress-graph-open-work-breakdown.md`
  - `docs/host-interaction-model.md`
  - `src/runtime/orchestration/landing.py`
- 风险：高。
- 当前判断：这条线最终成立，但不应该作为第一刀。因为当前 action ownership、权限边界、失败恢复与 live runtime source-of-truth 都还没有为 graph 直控模式收口。

## Current AI inclination

我当前倾向于优先进入 **Candidate A**。

原因是：

1. 用户要的是“graph 成为控制页面”，第一版不需要立刻等于“graph 直接控制 runtime”
2. 当前仓库已经有足够的 preview/host 基础，也有足够的 bridge compact runtime primitive，可以先做只读 control overlay
3. 当前真正缺的是 orchestration control snapshot 与 graph identity mapping；先补这层，后续无论继续做 richer interaction，还是进入 direct actions，都有稳定落点

## 2026-05-06 assessment update

基于当前代码与文档面，我不建议把下一阶段表述成“现在就从 explorer 转成 control panel”。

更准确的判断是：

1. 当前基础设施已经足够支撑 **control-panel groundwork**，但还不足以支撑真正的 control-panel pivot
2. 当前更像是“explorer hardening + runtime projection groundwork”阶段，而不是“graph 已准备好承接控制面”阶段
3. 当前最大的 blocker 不在 renderer，而在三件事仍未形成稳定 owner：
  - control snapshot producer
  - graph node / cluster / graph section 与 runtime item 的 binding contract
  - actor / worker clue 的显式 authority source

因此，当前推荐不是退回纯 explorer polish，也不是继续把目标写成 full control panel，而是维持当前 active gate、但把实施优先级明确收窄为：

1. 先固定 snapshot authority shape
2. 再固定 graph binding contract
3. 最后才进入 read-only host overlay

## User-selected sequencing

当前用户已进一步明确顺序：

1. 先收口当前 active gate `design_docs/stages/planning-gate/2026-05-03-project-progress-preview-freshness-signaling-and-workflow-polishing.md`
2. 该 gate 收口后，再激活当前 interactive control surface 主线

因此，这份文档当前的作用不是立刻切 active slice，而是固定 close 之后的下一条 graph 主线入口。

## Recommended first slice boundary

若进入 Candidate A，第一刀建议固定为：

1. 先固定 compact orchestration snapshot 的 authority shape，不抓 live process 内部状态
2. 先固定 graph node / cluster / graph section 与 runtime item 的 explicit binding contract
3. 在前两者成立后，再进入 read-only control surface overlay
4. 全程不做 direct mutation controls，并继续复用当前 preview / host surface，不重写成第二套 renderer 或完整前端应用

## Why this is not the current active gate

当前 active gate `design_docs/stages/planning-gate/2026-05-03-project-progress-preview-freshness-signaling-and-workflow-polishing.md` 只覆盖：

1. freshness / dirty-state contract
2. artifact refresh workflow polish
3. 最小 host-side state signaling

而“interactive control surface”会额外引入：

1. orchestration runtime source family
2. graph node -> bridge state mapping contract
3. 更重的 preview/host control information architecture

因此它必须作为新 gate 单独处理，不能直接并进当前 freshness gate。