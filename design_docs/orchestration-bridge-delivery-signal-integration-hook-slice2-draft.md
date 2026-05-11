# Slice 2 Draft — Orchestration Bridge Delivery Signal Integration Hook Minimal Contract

本文是 [design_docs/stages/planning-gate/2026-04-29-orchestration-bridge-delivery-signal-integration-hook.md](design_docs/stages/planning-gate/2026-04-29-orchestration-bridge-delivery-signal-integration-hook.md) 的 Slice 2 设计草案，直接承接 [design_docs/orchestration-bridge-delivery-signal-integration-hook-slice1-draft.md](design_docs/orchestration-bridge-delivery-signal-integration-hook-slice1-draft.md) 已收窄出的 hook owner 结论。

## Goal

当前 Slice 2 只解决一个更窄的问题：

1. post-dispatch overlay step 的最小输入面是什么
2. 这一步最小输出面是什么
3. compact delivery clue 的写回规则应如何保持与现有 governance projection、roll-up 与 stop-boundary 解耦

本文不定义：

1. 更宽的 external-resolution traceability contract
2. owner-surface payload / artifact schema 重设计
3. queue / persistence / replay / daemon runtime
4. graph-ready signal 或 graph user-interaction 回流

## Current contract anchor

当前已经稳定存在、且应继续复用的 surface 包括：

1. `CoordinatorAdvanceResult`
2. `BridgeLandingArtifact`
3. `dispatch_landing_consumer_payload(...)` 的 normalized dispatch result
4. `BridgeGroupItem` 上已存在的 compact delivery clue 字段：
   - `delivery_surface_kind`
   - `delivery_state`
   - `delivery_record_id`
   - `delivery_failure_detail`

因此，当前最小 contract 问题不是“是否需要新 bridge state object”，而是：

1. 哪个 helper 同时消费上面三层输入
2. 哪个 helper 负责把 dispatch result 归一化为现有 `BridgeGroupItem` clue
3. 这个 helper 是否需要重算 work-item roll-up 或 stop decision

## Chosen helper boundary

当前推荐把 live hook 收窄为一个新的 post-dispatch overlay helper，它应满足以下边界：

1. helper 发生在 `build_landing_artifact(...)` 之后、`dispatch_landing_consumer_payload(...)` 之后
2. helper 消费 bridge 已有 group/work context，而不是重新读取 raw executor result
3. helper 只回写 group-item compact delivery clue，不承担新的 owner-surface dispatch 职责
4. helper 默认不重算 roll-up / stop decision

换句话说，这一步是“把 owner-facing delivery result 最小镜像回 bridge observation surface”，而不是“让 bridge 接管 owner-facing state”。

## Minimal input surface

当前最小输入面应固定为：

1. `advance_result: CoordinatorAdvanceResult`
   - 用于提供当前 `group_items`、`updated_group_item`、`work_item` 与 dominant lineage 观察面
2. `artifact: BridgeLandingArtifact`
   - 用于提供当前 landing family 与 dominant group identity
3. `dispatch_result: Mapping[str, object]`
   - 只消费 normalized dispatch result 的稳定字段：
     - `delivered`
     - `consumer_kind`
     - `record_id`
     - `detail`

当前不应要求 helper 再接收：

1. raw owner payload
2. `consumer_result` 的全量细节
3. 新的 stop-state override 参数
4. 新的 work-item lifecycle override 参数

## Minimal output surface

当前最小输出面应固定为：

1. 更新后的 `group_items`
2. 更新后的 `updated_group_item`

当前默认不要求 helper 返回：

1. 新的 `BridgeWorkItem`
2. 新的 `StopConditionDecision`
3. 新的 wrapper dataclass result

原因是：

1. 当前 gate 的目标只是把 compact delivery clue 接回 live path
2. 若一开始就把 work-item / decision 一并重算，会过早扩大到行为改动

## Normalization rules

当前 compact delivery clue 的归一化规则应固定如下：

### 1. delivery family mapping

`dispatch_result["consumer_kind"]` 应只被归一化为现有 `BridgeGroupItem.delivery_surface_kind` 可接受的 family：

1. `handoff` -> `handoff`
2. `review_intake` -> `review_intake`
3. `escalation_notification` -> `escalation_notification`
4. 其他值 -> `none`

### 2. delivery state mapping

当前状态只保留最小 bridge-facing 观察面：

1. 未进入 overlay 前保持既有值
2. `delivered == True` -> `delivered`
3. `delivered == False` -> `failed`

当前不新增 `in_progress`、`retrying`、`unknown` 一类更细 lifecycle。

### 3. record clue mapping

1. `record_id` 为非空字符串时，写入 `delivery_record_id`
2. 若当前 dispatch 未给出 `record_id`，保持既有值

### 4. failure clue mapping

1. `delivered == False` 时，`detail` 写入 `delivery_failure_detail`
2. `delivered == True` 时，清空 `delivery_failure_detail`

## Dominant-group writeback rule

当前 helper 的写回边界应保持 conservative：

1. 只允许回写当前 `advance_result.updated_group_item`
2. 只允许用该 group-item 的 `group_item_id` 在 `group_items` 中做同位替换
3. 当前不扩大到同时更新多个 dominant groups

原因是：

1. 当前 active chain 仍是 single-step advance over one group item
2. 先锁定单 group-item 回写，可以最大限度避免误把 bridge 推成 multi-owner state merger

## No-change boundary

当前 Slice 2 明确不应改变以下 contract：

1. `project_execution_result_to_group_item(...)` 的输入契约
2. `project_group_item_surface(...)` 的 governance projection contract
3. `roll_up_work_item(...)` 的 dominant aggregation rules
4. `evaluate_stop_condition(...)` 的 boundary family
5. `dispatch_landing_consumer_payload(...)` 的 normalized source-of-truth shape

## Suggested runtime landing point

若进入代码实现，当前最自然的最小落点是：

1. 在 `src/runtime/orchestration/projection.py` 中新增一个独立 delivery overlay helper
2. 保持 `landing_dispatch.py` 只做 dispatch
3. 在更高一层由一个 bridge-facing orchestration helper 调用该 overlay helper，把 clue 写回现有 group-item

这样可以继续保持：

1. projection 负责 clue normalization
2. orchestration helper 负责 bridge-state writeback
3. dispatch 层继续保留 owner-facing source-of-truth

## Current recommendation

我当前推荐：

1. Slice 2 只把 post-dispatch overlay helper 的输入 / 输出 contract 与归一化规则写清
2. 默认先只支持 single updated group-item writeback
3. 下一步进入 Slice 3 时，直接围绕这个最小 contract 固定 focused validation matrix，而不是再扩 helper family