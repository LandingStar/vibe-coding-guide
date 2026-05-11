# Slice 1 Draft — Orchestration Bridge Delivery Signal Integration Hook

本文是 [design_docs/stages/planning-gate/2026-04-29-orchestration-bridge-delivery-signal-integration-hook.md](design_docs/stages/planning-gate/2026-04-29-orchestration-bridge-delivery-signal-integration-hook.md) 的 Slice 1 设计草案。

## Goal

当前 Slice 1 只解决一个更窄的问题：

1. delivery dispatch result 最早在哪个现有 runtime entry 上与 `BridgeGroupItem` 的回写目标同时可见
2. 这个 live hook 应落在 `executor_adapter` 邻侧，还是应落在 landing dispatch 返回后的 coordinator 邻侧
3. 哪条路径能最小化对现有 governance projection、roll-up 与 stop-condition 的扰动

## Current neighboring surfaces

当前最直接相关的现有 surface 只有四层：

1. `src/runtime/orchestration/executor_adapter.py`
   - `project_execution_result_to_group_item(...)` 当前只消费 `execution_result`
   - 它当前只调用 `project_group_item_surface(...)`，不接触 dispatch result
2. `src/runtime/orchestration/coordinator.py`
   - `advance_work_item_from_execution_result(...)` 当前负责 group-item 更新、work-item roll-up 与 stop decision
   - 这层拥有最新 `BridgeGroupItem` / `BridgeWorkItem` / dominant group lineage 的最直接桥接面
3. `src/runtime/orchestration/landing.py`
   - `build_landing_artifact(...)` 当前从 `CoordinatorAdvanceResult` 构造 external-resolution artifact
   - 这层首次把 dominant group identity 与 landing kind 固定下来
4. `src/runtime/orchestration/landing_dispatch.py`
   - `dispatch_landing_consumer_payload(...)` 当前返回 normalized dispatch result：`delivered`、`consumer_kind`、`record_id`、`detail`、`consumer_result`
   - 这层拥有 owner-facing delivery 的 source-of-truth，但不拥有 bridge state

## Discriminating local check

当前最便宜、且最能推翻路径判断的近邻检查已经成立：

1. `project_execution_result_to_group_item(...)` 只看到 `execution_result`，看不到 dispatch result
2. `build_landing_artifact(...)` 与 `dispatch_landing_consumer_payload(...)` 又都发生在 governance roll-up / stop decision 之后

因此，如果 live hook 必须消费真实 dispatch result，那么它默认不应直接落在当前 `executor_adapter.py` 的既有输入契约里。

## Recommended hook owner

基于上述近邻检查，当前更合理的最小入口是：

1. 保持 `executor_adapter.py` 继续只承接 governance-side projection
2. 把 live hook 收窄为一个 **coordinator / landing boundary 邻侧** 的 post-dispatch overlay step
3. 让这一步在拿到 normalized dispatch result 之后，只把 compact delivery clue 回写到既有 `BridgeGroupItem`

这条边界比“直接扩 `project_execution_result_to_group_item(...)` 输入契约”更稳，因为：

1. 它不要求把 owner-facing delivery result 伪装成 executor governance result
2. 它不要求 `landing_dispatch.py` 反向承担 bridge-state owner 角色
3. 它能把当前 hook 限制在一条明显发生于 `wait_external_resolution` 之后的 post-dispatch path

## Minimal contract direction

当前推荐先按以下 contract 继续收窄：

1. hook 的输入至少需要：
   - 现有 `CoordinatorAdvanceResult` 或等价 group/work context
   - `BridgeLandingArtifact`
   - normalized dispatch result
2. hook 的输出应优先保持为：
   - 更新后的 `BridgeGroupItem` 或更新后的 `group_items`
   - 默认不重算 roll-up / stop decision
3. hook 当前只允许写回：
   - `delivery_surface_kind`
   - `delivery_state`
   - `delivery_record_id`
   - `delivery_failure_detail`

## No-change boundary

当前 Slice 1 已明确不应碰以下边界：

1. `project_group_item_surface(...)` 的 governance projection contract
2. `roll_up_work_item(...)` 的 dominant governance aggregation rules
3. `evaluate_stop_condition(...)` 的 boundary family
4. `dispatch_landing_consumer_payload(...)` 的 source-of-truth return shape

换句话说，这条 hook 的目标是把现有 isolated helper 接到 live path，而不是重写当前 orchestration runtime 的判定逻辑。

## First targeted validation entry

当前推荐的最小验证入口是：

1. `tests/test_runtime_orchestration_landing_dispatch.py`
   - 这里已经串起 `advance_work_item_from_execution_result(...)` -> `build_landing_artifact(...)` -> `build_landing_consumer_payload(...)` -> `dispatch_landing_consumer_payload(...)`
2. 必要时补一个新的 orchestration-focused helper test，让 dispatch result 回写后的 group-item compact clue 可见
3. 暂不要求一开始就扩大到更宽的 `tests/test_runtime_orchestration.py` / coordinator 全链路回归

## Current recommendation

我当前推荐：

1. 先把 hook owner 固定为 coordinator / landing boundary 邻侧的 post-dispatch overlay step
2. 先不扩 `executor_adapter.py` 的输入契约，除非下一步发现已有调用面其实已经稳定携带 dispatch result
3. 下一步进入 Slice 2 时，优先把 hook 的输入/输出 contract 写清，再决定是否需要新的 helper 名称或新的 result wrapper

这样可以继续保持最小 live integration hook 的窄 scope，而不是过早把 owner-facing delivery result 重新揉进治理投影路径。