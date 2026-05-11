# Planning Gate — Orchestration Bridge Delivery Signal Integration Hook

> 日期: 2026-04-29
> 状态: COMPLETED
> 来源: `design_docs/orchestration-bridge-contract-runtime-alignment-followup-direction-analysis.md`

## Why this exists

`design_docs/stages/planning-gate/2026-04-28-orchestration-bridge-contract-runtime-alignment.md` 已完成并关闭。

这意味着当前 bridge 主线已经具备：

1. `BridgeGroupItem` 已能承载 compact delivery clue
2. `project_group_item_delivery_signal(...)` 已提供 isolated overlay helper
3. `project_execution_result_to_group_item(...)`、`advance_work_item_from_execution_result(...)`、`build_landing_artifact(...)` 与 `dispatch_landing_consumer_payload(...)` 已形成现有 bridge / landing 基础链路

但当前仍缺一层最小 live hook：

1. delivery dispatch result 还没有真正回写到现有 `BridgeGroupItem` surface
2. executor-side governance projection 与 owner-facing delivery projection 仍停留在两段彼此分离的 helper
3. 当前还没有明确回答这个 hook 应落在 `executor_adapter` 邻侧，还是应该落在 landing dispatch 返回后的 coordinator 邻侧

因此，下一条最窄 planning-gate 应先固定 **delivery signal integration hook over existing bridge surface**，而不是继续停留在 isolated helper，或直接扩大到 broader landing conformance / daemon runtime。

## Current sequencing decision

用户当前已明确：先沿 orchestration bridge 主线继续推进，并在 bridge 的 MVP 阶段完成后，再回到 `progress_graph` 主线讨论 graph 的用户交互部分。

这对当前 gate 的含义是：

1. 当前 gate 仍是 bridge 主线的一部分，而不是切回 graph 前的过渡占位
2. 当前 gate 完成后，下一步应先判断 bridge MVP 还缺哪些最小边界，而不是自动切回 graph backlog
3. graph 相关规划当前只作为后续恢复入口保留，不在本 gate 内激活

## Scope

本 gate 只处理：

1. `BridgeGroupItem` 的 compact delivery clue 应在哪个现有 runtime entry 上被 live 写回
2. 现有 `executor_adapter` / `coordinator` / `landing` / `landing_dispatch` 链路中，哪一层应持有这个最小 integration hook
3. delivery dispatch result 如何被压回 `delivery_surface_kind` / `delivery_state` / `delivery_record_id` / `delivery_failure_detail`
4. 如何在不改变现有 roll-up / stop-condition family 的前提下完成这层 hook
5. 当前 hook 的 targeted validation 入口应从哪组 orchestration tests 开始

本 gate 不处理：

1. external-resolution landing conformance 的更宽 traceability 切片
2. broader daemon queue / persistence / replay runtime
3. owner-surface payload schema 重设计
4. 让 `landing_dispatch.py` 成为新的 bridge-state owner

## Working hypothesis

当前最小可行路线应是：

1. 继续保持 `project_execution_result_to_group_item(...)` 只承接 governance-side projection
2. 把 live integration hook 收窄为一个 **coordinator / landing boundary 邻侧** 的 post-dispatch overlay step，而不是把 owner-facing delivery result 直接塞回 `executor_adapter`
3. 让该 hook 只消费 `BridgeLandingArtifact` / normalized dispatch result / 已有 dominant group identity，回写 group-item delivery clue，但不重开 roll-up / stop decision

## Slices

### Slice 1 — Hook entry selection and neighbor check

- 盘点 `executor_adapter.py`、`coordinator.py`、`landing.py`、`landing_dispatch.py` 的直接控制路径
- 判断 dispatch result 与 `BridgeGroupItem` / dominant group identity 最早在哪一层同时可见
- 固定 hook 的最小 owner matrix

当前状态：Slice 1 设计草案已创建为 `design_docs/orchestration-bridge-delivery-signal-integration-hook-slice1-draft.md`；当前推荐优先验证“coordinator / landing boundary 邻侧的 post-dispatch overlay helper”是否是最小入口，而不是先扩 `executor_adapter` 的输入契约。

### Slice 2 — Minimal integration contract

- 定义 hook 的输入/输出最小面
- 定义 delivery result 到 compact clue 的归一化规则
- 固定 hook 对 group-item / work-item / stop-boundary 的不变项

当前状态：未开始。

当前状态更新：Slice 2 设计草案已创建为 `design_docs/orchestration-bridge-delivery-signal-integration-hook-slice2-draft.md`；当前已把 post-dispatch overlay helper 的最小输入 / 输出 contract、compact delivery clue 归一化规则与 no-change boundary 收窄为 single updated group-item writeback。

### Slice 3 — Targeted validation entry

- 固定最小测试入口
- 明确哪些现有 landing / dispatch tests 可直接扩展，哪些需要新的 focused probe

当前状态：未开始。

当前状态更新：Slice 3 设计草案已创建为 `design_docs/orchestration-bridge-delivery-signal-integration-hook-slice3-draft.md`；当前已固定 `tests/test_runtime_orchestration_landing_dispatch.py` 作为 delivered / failed 两类 compact clue 回写的第一验证入口。

## Current technical result

当前 gate 已完成以下内容：

1. Slice 1 已固定 hook owner 倾向为 `coordinator / landing boundary` 邻侧的 post-dispatch overlay step
2. Slice 2 已把最小 input / output contract 与 compact delivery clue 归一化规则写清
3. Slice 3 已把 `tests/test_runtime_orchestration_landing_dispatch.py` 固定为第一验证入口
4. `src/runtime/orchestration/landing.py` 已新增最小 live helper `overlay_delivery_dispatch_result(...)`
5. `tests/test_runtime_orchestration_landing_dispatch.py` 已新增 delivered / failed 两条 focused tests，并通过 `9 passed`

基于当前结果，这条 gate 的内容面已经满足 stop condition；当前尚未做的，只剩 formal close writeback 与下一条 follow-up 方向选择。

当前状态更新：formal close writeback 已完成；当前 gate 已正式切为 `COMPLETED`，bridge MVP 的 formal close 也已同步到 canonical handoff / `CURRENT.md` / Checklist / Phase Map / checkpoint。

## Validation gate

- 文档验证：
  - 能清楚回答 dispatch result 与 group-item identity 最早在哪一层同时可见
  - 能清楚回答 hook 为什么不应直接塞进 `landing_dispatch.py` 或 `executor_adapter.py`
  - 能清楚回答 compact delivery clue 的 live hook 是否会影响现有 roll-up / stop-condition family
- 后续代码验证：
  - targeted tests 能证明 live hook 成立
  - 当前 hook 不需要重写 owner-surface source-of-truth 或 governance projection contract

## Stop condition

- 当 hook entry、最小 integration contract 与 targeted validation 入口都已写清后停止
- 不在本 gate 内顺手扩大到 broader landing conformance 或 daemon runtime

## Close result

当前 gate-close writeback bundle 已完成，因此本 gate 现已正式切为 `COMPLETED`。

本次收口已完成：

1. `design_docs/orchestration-bridge-mvp-boundary-draft.md` 已确认 bridge MVP 的四个 completion signals 全部成立
2. canonical handoff `2026-04-30_1818_orchestration-bridge-delivery-signal-integration-hook_stage-close` 已生成并校验通过，且已轮转为 `CURRENT.md` 的 mirror source
3. Checklist、Phase Map、checkpoint 与 `design_docs/direction-candidates-after-phase-35.md` 已同步到同一 safe-stop 口径
4. 当前仓库重新回到无 active planning-gate 状态；下一条默认恢复入口切回 `design_docs/project-progress-user-interaction-after-bridge-mvp-direction-analysis.md`

因此，后续不再继续修改本 gate；下一步应回到 post-bridge graph 用户交互候选面，而不是在本 gate 内继续扩大 bridge runtime scope。