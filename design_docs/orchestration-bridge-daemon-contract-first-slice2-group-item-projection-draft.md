# Slice 2 Draft — Orchestration Bridge Daemon Contract-First Group-Item Projection

本文是 `design_docs/stages/planning-gate/2026-04-28-orchestration-bridge-daemon-contract-first.md` 的 Slice 2 设计草案。

## Goal

Slice 1 已经固定了 bridge primitive 的 ownership boundary、最小字段建议与 lifecycle 边界。

Slice 2 当前只解决一个更窄的问题：

1. governance kernel 产出的 grouped review / group terminal / blocked 结果，最小如何投影到 `BridgeGroupItem`
2. `dispatch_landing_consumer_payload(...)` 产出的 delivery result，最小如何补充到同一个 `BridgeGroupItem` compact footprint
3. 哪些内容仍然必须保留在 governance-owned 或 owner-surface-owned source of truth，而不是复制到 bridge

本文不定义：

1. `BridgeWorkItem` 如何据此 roll-up
2. `waiting_external_resolution` 的完整 trigger matrix
3. terminal landing artifact 或 external resolution 完成后的恢复机制

## Current input surfaces

当前已经存在、且足以支撑投影的 source surface 包括：

1. `GroupedReviewOutcome` / `grouped_review_state`
2. `GroupTerminalOutcome`
3. grouped child writeback summary / eligibility basis
4. blocked merge / preflight / validator path 产生的 blocked reason
5. `dispatch_landing_consumer_payload(...)` 的稳定返回面：
   - `delivered`
   - `consumer_kind`
   - `target_surface`
   - `record_id`
   - `detail`
   - `consumer_result`

因此当前不建议再创造 bridge-only 的第四套结果对象。更稳的做法是把 bridge 需要的内容压成一个 compact projection。

## Projection boundary

当前 Slice 2 需要固定的不是一长串 schema 字段，而是 `BridgeGroupItem` 至少必须能看见的四类信息：

1. governance surface family：当前 group 是普通 grouped review、group terminal、blocked，还是尚无可消费结果
2. landing surface family：当前 group 是否已经进入 handoff / review intake / escalation notification 这类 owner-facing delivery
3. writeback observation：当前 child writeback 对 bridge 来说是可继续观察、被 suppressed，还是已经 blocked
4. external-resolution clue：bridge 是否已经得到足够信号，知道这个 group 需要等待 reviewer / handoff / escalation / delivery repair

当前 gate 只需要钉住这四类观察面必须存在；至于它们最终落成几个具体字段、字段名是什么、是否与现有 runtime model 完全同名，不应在这份 planning 文档里先锁死。

## Required normalization rules

当前更关键的是固定归一化规则，而不是扩字段表：

1. grouped review、group terminal、blocked 必须继续保持为 governance-owned source family，bridge 只能观察其 compact family 与最小子状态
2. handoff、review intake、escalation notification 必须继续保持为 owner-facing delivery family，bridge 只能观察“未开始 / 已发起 / 已成功 / 已失败”这一层 delivery signal
3. delivery failure 可以提升为 bridge-facing 的等待或修复信号，但不能把 bridge 变成新的 owner-delivery adapter
4. blocked reason 或 delivery detail 只作为最后可见原因的镜像，不应成为新的 source of truth

## Minimal scenario coverage

当前只需要保证以下几类场景能被 `group item` projection 区分：

1. review-required 已产生，但 reviewer takeover 还未真正送到 review surface
2. handoff 或 escalation terminal 已产生，但 owner-facing delivery 还未完成
3. owner-facing delivery 已成功，bridge 只需要保留最小回跳线索
4. blocked 或 delivery failure 已发生，bridge 能区分这是等待外部处理，还是当前 group 本身已阻塞

## Structural boundary

当前推荐继续保持三条边界：

1. `lifecycle_state` 只表达 bridge 调度阶段，不与投影字段混用
2. governance-facing signal、landing-facing signal 与 blocked / delivery detail 只表达 compact result footprint
3. `BridgeGroupItem` 只作为 bridge 与 governance / landing surface 之间的最小 adapter，不复制 raw payload 或 owner artifact

换句话说，Slice 2 的目标不是教 bridge “怎么行动”，而是先固定 bridge “最少看见什么”。

## Current recommendation

我当前推荐：

1. 先把 `BridgeGroupItem` 的 upward projection 固定成上面的四类观察面与归一化规则
2. 保持 external-resolution signal 只表达归一化等待原因，不直接编码 stop / resume 策略
3. 下一步优先进入 `work item` roll-up，而不是跳过 group-item 直接定义桥接停机规则

这样能保证后续 roll-up 只消费已经稳定的 group-level projection，而不是同时处理 raw governance object 与 raw dispatch result。