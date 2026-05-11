# Draft — Orchestration Bridge MVP Boundary

## Purpose

本文只回答一个问题：

在当前 orchestration bridge 主线已经完成 landing dispatch integration、daemon contract-first docs-only 收口，以及 contract/runtime alignment 最小 conformance edit 之后，什么才算 bridge 的 MVP 已完成，从而可以合理切回 `progress_graph` 主线并讨论 graph 的用户交互部分。

本文是 boundary draft，不直接激活新的 planning-gate，也不替代当前 active gate。

## Why this draft is needed now

当前用户已经明确新的顺序：

1. 先继续 orchestration bridge 主线
2. 先把 bridge 的 MVP 阶段完成
3. bridge MVP 完成后，再回到 graph，并优先讨论 graph 的用户交互部分

但当前仓库里还没有一份文档明确写清：

1. 哪些 bridge 能力已经足以算入 MVP
2. 当前 active gate 在 MVP 里处于什么位置
3. 哪些 bridge 能力应明确留到 post-MVP，而不是继续被顺手带进当前主线

## Current completed boundary that already counts toward MVP

基于现有文档，当前已经完成、且应计入 bridge MVP 的部分至少包括以下四层。

### 1. Landing artifact to real owner-surface delivery

`design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-landing-dispatch-integration.md` 已完成并关闭。

这意味着当前已经具备：

1. `build_landing_consumer_payload()` 作为 owner-facing payload normalizer
2. `src/runtime/orchestration/landing_dispatch.py` 作为统一 dispatch helper
3. `handoff` -> `FileHandoffConsumer`
4. `review_intake` -> `FeedbackAPIReviewIntakeConsumer`
5. `escalation` -> `EscalationNotifier.notify()`

因此，bridge 最小链路里“landing artifact 能否进入真实 owner surface”这一层已经不是空洞。

### 2. Thin bridge / daemon contract boundary

`design_docs/stages/planning-gate/2026-04-28-orchestration-bridge-daemon-contract-first.md` 已按 docs-only boundary 完成并关闭。

这意味着当前已经写清：

1. `BridgeWorkItem` / `BridgeGroupItem` 的最小职责边界
2. bridge 与治理内核、landing dispatch surface 的 ownership matrix
3. group-item projection -> work-item roll-up -> stop-boundary 的 contract-first 口径
4. bridge 不是第二套治理内核，也不是第二套 owner-delivery adapter

因此，bridge MVP 当前不再需要重新回答“bridge 是什么层”，而是只需要把这层最小 contract 接到现有 runtime surface。

### 3. Runtime authority surface alignment

`design_docs/stages/planning-gate/2026-04-28-orchestration-bridge-contract-runtime-alignment.md` 已完成并关闭。

这意味着当前已经做完：

1. `models.py` / `projection.py` / `rollup.py` / `stop_conditions.py` / `landing.py` 的 authority surface inventory
2. 最小 compact delivery clue 的 isolated conformance edit
3. `tests/test_runtime_orchestration.py` 的 targeted validation（10 passed）

因此，bridge MVP 当前不再需要重新盘点“现有 runtime helper 是否存在”，而是进入“如何把最小 live hook 接上现有 surface”。

### 4. 当前已明确的 next narrow problem

当前 active gate `design_docs/stages/planning-gate/2026-04-29-orchestration-bridge-delivery-signal-integration-hook.md` 已把新的最小缺口收窄为：

1. delivery dispatch result 应在什么 runtime entry 回写到 `BridgeGroupItem`
2. hook 应落在 `executor_adapter` 邻侧，还是 `coordinator / landing` 边界邻侧
3. 如何在不重写 roll-up / stop-condition family 的前提下，完成最小 live integration

这说明当前离 MVP 最近的剩余问题，已经不是更宽的 daemon/runtime，而是 delivery signal live hook 的最小落点与最小 code-touch。

## What MVP must prove

当前 bridge MVP 不应该被理解为“完整 daemon runtime 可用了”，而应被理解为：

1. 现有治理内核之上，已经存在一条最小可闭环的 thin orchestration bridge
2. 这条 bridge 已经拥有 work-item / group-item 的最小 contract
3. 这条 bridge 已经能把 external-resolution landing 送到真实 owner surface
4. 这条 bridge 已经能把最小 owner-facing delivery signal 回写到 bridge 自己的 compact model surface
5. 整条链不需要把 bridge 扩成新的治理层、owner-delivery 层或 full daemon runtime

换句话说，MVP 的证明目标不是“bridge 功能很多”，而是“bridge 作为薄桥接层已经真的闭环成立”。

## What still remains before MVP can be called complete

当前最小剩余工作应被拆成两段，而不是混成一句“把当前 gate 做完”。

### A. Finish the current docs-first active gate

当前 active gate 还没有完成：

1. Slice 1 只完成了 hook entry recommendation
2. Slice 2 的最小 integration contract 尚未写实
3. Slice 3 的 targeted validation entry 尚未固定

因此，当前 gate 结束前至少还需要：

1. 固定 hook owner matrix
2. 固定 post-dispatch overlay step 的输入 / 输出 contract
3. 固定最小测试入口

这一步完成后，当前 gate 才能关闭；但这一步本身仍只是 MVP 的设计前置，不等于 MVP 已完成。

### B. Land the minimal live integration implementation

即使当前 docs-first gate 关闭，bridge MVP 仍不能立刻判定为完成。

原因是：

1. 当前 active gate 只是在定义 live hook，不是在落实现
2. bridge MVP 至少需要证明最小 live hook 在 runtime 里真的成立

因此，在当前 gate 之后，至少还需要一条最小实现动作，去证明：

1. normalized dispatch result 能通过最小 post-dispatch overlay step 回写 `BridgeGroupItem`
2. 回写只触及 `delivery_surface_kind`、`delivery_state`、`delivery_record_id`、`delivery_failure_detail`
3. 现有 governance projection、roll-up 与 stop-condition family 不被重写
4. 有一条窄验证能证明这条 live hook 成立

当前更合理的默认实现入口，仍应来自 `design_docs/orchestration-bridge-delivery-signal-integration-hook-slice1-draft.md` 中已经写清的 `coordinator / landing boundary` 邻侧 post-dispatch overlay 路线。

## What is explicitly not required for MVP

以下事项当前不应被算入 bridge MVP 前置，否则 bridge 主线会再次膨胀：

1. broader daemon queue / persistence / replay runtime
2. full daemon service 或外部 worker orchestration
3. richer landing history / retry / replay semantics
4. external-resolution landing conformance 的更宽 traceability 收口
5. `landing_dispatch.py` 成为新的 bridge-state owner
6. 新的 bridge lifecycle family
7. 将 graph 的 ready/frontier 信号接入 bridge runtime

这些方向都在文档里被长期保留过，但当前都属于 post-MVP 层。

## MVP completion signals

当前更稳的做法，是把 bridge MVP 完成信号收窄为以下四条。

### Signal 1 — Thin bridge boundary remains intact

以下边界没有被后续实现破坏：

1. bridge 仍只拥有调度、恢复与 compact footprint
2. governance kernel 仍拥有 gate / review / writeback / audit judgment
3. landing dispatch / owner surfaces 仍拥有真实 delivery 细节与 source of truth

### Signal 2 — Live delivery-signal hook is real, not only documented

以下行为已经在 runtime 中成立：

1. delivery dispatch result 已能最小回写到 `BridgeGroupItem`
2. 回写发生在 post-dispatch path，而不是被塞回 `executor_adapter`
3. compact delivery clue 已在 bridge surface 上可见

### Signal 3 — No-change boundary still holds

以下 contract 没被顺手扩大：

1. `project_group_item_surface(...)` 仍只承接 governance-side projection
2. `roll_up_work_item(...)` 的 dominant aggregation rules 未被 delivery signal 改写
3. `evaluate_stop_condition(...)` 的 boundary family 未被重新设计
4. `dispatch_landing_consumer_payload(...)` 仍保持 owner-facing source-of-truth return shape

### Signal 4 — Narrow executable validation exists and passes

至少应存在一条 focused validation，证明最小闭环成立。当前更合理的默认验证入口是：

1. `tests/test_runtime_orchestration_landing_dispatch.py`
2. 必要时补一条新的 orchestration-focused helper test
3. 若实现最终触及更宽 helper chain，再回看 `tests/test_runtime_orchestration.py`

## Proposed judgment rule

当前我建议采用以下判断规则：

1. 当前 active gate 关闭，不等于 bridge MVP 完成
2. 当前 active gate 关闭之后，还需要至少一条最小 live integration implementation + targeted validation
3. 只有当上面的四个 MVP signals 同时成立时，才可以把 bridge 当前 MVP 阶段判定为完成
4. 到那时，再切回 graph，并优先讨论 graph 的用户交互 / preview productization 部分，才不会再次因为 MVP 边界不清而漂移

## Current recommendation

基于现有文档，我当前推荐把 bridge MVP 理解为：

1. 以 thin bridge 为边界
2. 以当前 delivery-signal integration hook 为最后一块最小 live gap
3. 以“最小 live hook 已实现且验证通过”作为 MVP 是否完成的最终判据

这比把 MVP 理解成 full daemon runtime 更稳，也比把当前 docs-only gate 的关闭误当成 MVP 完成更准确。

## Suggested next step

如果沿当前主线继续，下一步最合适的不是直接讨论 post-MVP，而是：

1. 先完成 `design_docs/stages/planning-gate/2026-04-29-orchestration-bridge-delivery-signal-integration-hook.md` 的 Slice 2 与 Slice 3
2. 再起一条最小实现动作，把 post-dispatch overlay hook 落到 runtime helper 与 targeted tests

只有这样，bridge MVP 边界才真正有机会被执行性地关闭。

## Current acceptance snapshot

基于当前 workspace 结果，上述最小执行条件现已成立：

1. Slice 2 / Slice 3 文档已补齐：
	- `design_docs/orchestration-bridge-delivery-signal-integration-hook-slice2-draft.md`
	- `design_docs/orchestration-bridge-delivery-signal-integration-hook-slice3-draft.md`
2. `src/runtime/orchestration/landing.py` 已新增 `overlay_delivery_dispatch_result(...)`，把 normalized dispatch result 最小回写到 `BridgeGroupItem`
3. 当前实现继续保持 no-change boundary：
	- 不改 `project_group_item_surface(...)` 的 governance projection contract
	- 不改 `roll_up_work_item(...)` 的 dominant aggregation rules
	- 不改 `evaluate_stop_condition(...)` 的 boundary family
	- 不改 `dispatch_landing_consumer_payload(...)` 的 source-of-truth return shape
4. focused validation 已通过：
	- `pytest tests/test_runtime_orchestration_landing_dispatch.py -q` -> `9 passed`

因此，若按本文定义的四个 MVP signals 判断，当前 bridge 的 MVP 技术验收条件已经满足。

当前 formal close writeback 现也已完成：

1. `design_docs/stages/planning-gate/2026-04-29-orchestration-bridge-delivery-signal-integration-hook.md` 已正式关闭
2. canonical handoff `2026-04-30_1818_orchestration-bridge-delivery-signal-integration-hook_stage-close` 已生成、校验并轮转为 `CURRENT.md` mirror source
3. Checklist、Phase Map、checkpoint 与 `design_docs/direction-candidates-after-phase-35.md` 已统一到同一 safe-stop 口径

因此，当前剩余工作不再是“bridge MVP 是否成立”或“是否现在执行 close writeback”，而是：

1. 在 bridge MVP 之后，graph 应优先从哪条用户交互 / preview 方向重新启动
2. 用户选定下一条 graph 用户交互候选后，应如何起新的窄 planning-gate

这也是本文在当前仓库状态下更合适的停止点。