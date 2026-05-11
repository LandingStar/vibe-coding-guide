# Planning Gate — Orchestration Bridge Daemon Contract-First

> 日期: 2026-04-28
> 状态: COMPLETED
> 来源: `design_docs/orchestration-bridge-landing-dispatch-integration-followup-direction-analysis.md`、`design_docs/orchestration-bridge-daemon-layer-direction-analysis.md`、`design_docs/workspace-parallel-task-orchestration-direction-analysis.md`

## Why this exists

`design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-landing-dispatch-integration.md` 已完成并关闭。

这意味着当前 orchestration bridge 主线已经具备：

1. `build_landing_consumer_payload()` 作为稳定 payload normalizer
2. `src/runtime/orchestration/landing_dispatch.py` 作为统一 dispatch helper
3. `handoff` / `escalation` / `review_intake` 三类 payload 到真实 owner surface 的最小落地路径
4. owner-surface wiring 与 orchestration 窄范围联合验证（30 passed）

因此，当前最明显的空洞已经不再是 landing payload 能否落到真实 owner surface，而是：

1. bridge / daemon 到底持有什么最小调度 contract
2. `work item` / `group item` lifecycle 与 `GroupTerminalOutcome`、landing dispatch result 之间如何向上衔接
3. bridge 是否只承接调度与恢复，而不直接决定 gate / review / writeback 语义

如果在这个节点继续直接把 daemon queue / persistence / replay 叠进 runtime，会再次把两层职责混在一起：

1. `Executor` / grouped review / writeback / landing dispatch 负责治理内核与 owner-surface delivery
2. bridge / daemon 负责更高层的 work-item lifecycle、调度、恢复与等待外部接管边界

因此，下一条最窄 planning-gate 应先固定 **thin bridge / daemon contract**，而不是直接进入 full daemon runtime。

## Scope

本 gate 只处理：

1. bridge / daemon 层应持有的最小 work-item / group-item lifecycle 与 recovery-facing contract
2. bridge 与现有 governance kernel / landing dispatch surface 的 ownership boundary
3. `GroupTerminalOutcome`、grouped review state、writeback summary、landing dispatch result 如何向 bridge state 做 compact projection
4. bridge 在 `waiting_external_resolution` / 停机 / 恢复边界上至少需要哪些判断字段

本 gate 不处理：

1. full daemon runtime / queue system / service deployment
2. queue persistence / replay / external worker orchestration 实现
3. 继续扩 landing history / retry 语义
4. broader companion prose surface expansion
5. dogfood evidence / issue / feedback backlog

## Working hypothesis

当前最小可行路线应是：

1. bridge 只新增 scheduler-facing primitive 与 compact projection，不重写现有 governance object
2. governance kernel 继续拥有 gate / review / writeback / audit / owner-surface delivery 决策权
3. bridge 通过 compact footprint 消费 grouped review / group terminal / landing dispatch result，并把它们折叠成 lifecycle / recovery judgment
4. 当 bridge 需要等待 human takeover 或 owner-surface completion 时，应停在 bridge-facing `waiting_external_resolution` boundary，而不是把新状态家族塞回 executor

## Slices

### Slice 1 — Ownership matrix after landing dispatch close

- 固定 bridge-owned lifecycle / recovery fields
- 明确 governance kernel 与 landing dispatch surface 继续拥有的职责
- 固定 bridge 不直接拥有的 raw owner payload / review object / handoff document boundary

当前状态：Slice 1 设计草案已创建为 `design_docs/orchestration-bridge-daemon-contract-first-slice1-draft.md`；当前已把 bridge / governance kernel / landing dispatch surface 的 ownership boundary、两类 primitive 的最小职责划分，以及 lifecycle 与 result surface 分离的口径收窄到 planning-gate 所需层级。当前推荐继续把 bridge 收窄成 scheduler-facing identity / lifecycle / recovery wrapper，而不是让 bridge 复制完整 grouped review / handoff / feedback surface。

### Slice 2 — Upward terminal / landing projection contract

- 定义 `GroupTerminalOutcome`、grouped review state、writeback summary、landing dispatch result 如何投影到 `group item` / `work item`
- 定义 bridge 是否需要额外的 compact stop reason / recovery intent / external-resolution reason 字段
- 明确 bridge 只持有 projection，不重写 kernel object

当前状态：Slice 2 草案已创建为 `design_docs/orchestration-bridge-daemon-contract-first-slice2-group-item-projection-draft.md` 与 `design_docs/orchestration-bridge-daemon-contract-first-slice2-work-item-rollup-draft.md`；当前已先按 `group-item-first projection` 固定单个 `group item` 必须能观察到的治理面、landing 面、writeback 观察面与 external-resolution clue，再把多个 group 的 deterministic roll-up 收窄为 work-item 必须能看见的 dominant signal、writeback posture、open-group signal 与 lineage clue。当前下一窄切口收束为：进入 `waiting_external_resolution` / stop-boundary 的 trigger matrix，而不是再扩字段级 schema。

### Slice 3 — Stop / recovery boundary and next runtime entry

- 定义 bridge 至少需要哪些 lifecycle state 才能表达等待、恢复、停机与再次调度
- 定义本 docs-first gate 完成后，下一条 runtime gate 应先落哪个最小 helper / model surface
- 为后续 contract runtime gate 准备 stop condition

当前状态：Slice 3 草案已创建为 `design_docs/orchestration-bridge-daemon-contract-first-slice3-stop-boundary-draft.md`；当前已把 dominant roll-up 到 `continue_waiting` / `wait_external_resolution` / `completed` / `blocked` / `inconsistent` 的触发边界，以及下一条 runtime 应沿现有 roll-up / stop / landing surface 接入的口径收窄为 boundary-level 合同。本 slice 仍然不直接实现 daemon queue / persistence / replay。

## Validation gate

- 文档验证：
  - 能清楚回答 bridge / daemon 与 governance kernel / landing dispatch surface 各自拥有的职责
  - 能清楚回答 `GroupTerminalOutcome`、grouped review、writeback summary、landing dispatch result 如何向上回传到 bridge-facing state
  - 能清楚回答 bridge 是否只承接调度与恢复，而不直接决定 gate / review 语义
  - 能清楚回答 `waiting_external_resolution`、停机、恢复边界依赖哪些 compact projection 字段
- 未来代码验证：
  - runtime 落地时不需要改写现有 grouped review / group terminal / landing dispatch schema 才能接入
  - landing dispatch gate 当前实现能作为 bridge 上层的稳定下游 surface 继续复用

## Stop condition

- 当 ownership boundary、group-item projection、work-item roll-up、stop / recovery boundary 与 next runtime entry 都已写清后停止
- 不在本 gate 内直接进入 daemon runtime 实现或 queue / persistence / replay 设计

## Close note

当前 gate 已按 docs-only 边界完成：

1. Slice 1 固定了 bridge / governance kernel / landing dispatch surface 的 ownership boundary 与 primitive responsibility
2. Slice 2 固定了 group-item projection 与 work-item roll-up 的最小观察面
3. Slice 3 固定了 dominant roll-up 到 stop-boundary judgment 的触发边界，以及下一条 runtime entry 应沿现有 helper surface 对齐的口径

因此，下一步不再继续扩写本 gate，而是转入 `design_docs/orchestration-bridge-daemon-contract-first-followup-direction-analysis.md` 讨论 follow-up。