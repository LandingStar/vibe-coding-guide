# 设计草案 — Orchestration Bridge Slice 3 Stop-Condition Boundary

本文是 `design_docs/stages/planning-gate/2026-04-25-orchestration-bridge-work-item-group-item-contract.md` 的 Slice 3 设计草案，直接消费 Slice 1 已固定的 `BridgeWorkItem.lifecycle_state` 与 Slice 2 已固定的 group-item projection / work-item roll-up。

## 目标

当前只解决一个更窄的问题：

1. bridge 何时继续等待治理结果，何时进入 `waiting_external_resolution`
2. bridge 何时可以把 work-item 视为 `completed` 或 `blocked`
3. stop-condition boundary 如何只消费现有 footprint，而不再新增第三套 bridge-only state family

本文不定义：

1. `waiting_external_resolution` 之后如何 resume
2. terminal landing artifact
3. queue / retry / restart runtime

## 当前输入面

Slice 3 只使用已经固定的输入：

- `BridgeWorkItem.lifecycle_state`
- `BridgeWorkItem.rollup_surface_kind`
- `BridgeWorkItem.rollup_surface_state`
- `BridgeWorkItem.rollup_blocked_reason`
- `BridgeWorkItem.rollup_writeback_disposition`
- `BridgeWorkItem.open_group_item_count`
- `BridgeWorkItem.dominant_group_item_ids`

因此当前推荐是“基于现有 footprint 的 boundary mapping”，而不是再加新的 `stop_state` 主对象。

## 当前推荐的 boundary kinds

为了表达 stop-condition，而不引入新对象，当前推荐只定义一组派生判断：

- `continue_waiting`
- `wait_external_resolution`
- `completed`
- `blocked`
- `inconsistent`

其中：

1. `continue_waiting` 表示 bridge 应继续维持现有调度/等待过程，不是终态
2. `wait_external_resolution` 表示 bridge 必须等待 review gate、handoff 或 escalation 之外部接管
3. `completed` 表示从 bridge 观察面看，本轮 work-item 已无待决 group-item 且无更高优先级阻断
4. `blocked` 表示 bridge 已收到确定的 blocked footprint
5. `inconsistent` 不是用户可见终态，而是 runtime 后续应显式校验的 contract guard

## Boundary Matrix

当前推荐按照以下顺序判断 stop-condition：

| 条件 | boundary kind | target `BridgeWorkItem.lifecycle_state` | 说明 |
|---|---|---|---|
| `rollup_surface_kind=blocked` | `blocked` | `blocked` | blocked 优先于其他所有 boundary |
| `rollup_surface_kind=group_terminal` | `wait_external_resolution` | `waiting_external_resolution` | escalation / handoff 都属于 authority-transfer |
| `rollup_surface_kind=grouped_review` 且 `rollup_surface_state=review_required` | `wait_external_resolution` | `waiting_external_resolution` | review gate 也属于外部接管等待 |
| `open_group_item_count > 0` | `continue_waiting` | 保持当前 `lifecycle_state` 或 `waiting_governance_result` | 只要还有未 settled group-item，就不宣布完成 |
| `open_group_item_count = 0` 且 `rollup_writeback_disposition` 属于 `eligible` 或 `none`，且 `rollup_surface_kind` 不属于 `blocked` / `group_terminal` | `completed` | `completed` | bridge 观察面已无待决阻断 |
| 其他组合 | `inconsistent` | 保持当前 `lifecycle_state`，交由 runtime validator 处理 | 不静默推断为 completed 或 blocked |

## Boundary Notes

当前边界有三个关键判断：

1. `review_required` 不需要新的 lifecycle state，直接落到 `waiting_external_resolution`
2. `completed` 必须同时满足“没有 open group-item”与“没有更高优先级的 blocked / terminal footprint”
3. `rollup_writeback_disposition=pending` 在 `open_group_item_count=0` 时不应被自动解释成 continue；这类组合应视为 `inconsistent`

## Inconsistency Guard Examples

以下组合当前建议明确视为 inconsistent，而不是由 bridge 默默吞掉：

1. `open_group_item_count=0`，但 `rollup_surface_kind=none` 且 `dominant_group_item_ids` 非空
2. `rollup_surface_kind=blocked`，但 `dominant_group_item_ids` 为空
3. `open_group_item_count=0`，`rollup_writeback_disposition=pending`，且 `rollup_surface_kind` 不是 `grouped_review/review_required`
4. `rollup_surface_kind=group_terminal`，但 `rollup_surface_state` 不是 `escalation` 或 `handoff`

这些 guard 的目的不是在本文里定义 validator 实现，而是为后续 runtime gate 保留明确约束。

## 结构性边界

当前推荐继续保持三条边界：

1. Slice 1 负责 primitive identity / lifecycle
2. Slice 2 负责 group-item projection 与 work-item roll-up
3. Slice 3 只负责把这些既有 footprint 映射到 boundary judgment，不新增新的状态家族

这意味着 bridge 的 stop-condition 仍然只是现有 contract 的消费者，而不是新的治理层。

## 当前不做的设计

当前不做：

1. `waiting_external_resolution -> dispatching` 的恢复协议
2. external resolution 的持久化 / replay 机制
3. terminal landing artifact schema
4. runtime validator 的具体代码实现

## 当前推荐

我当前推荐：

1. 在 bridge runtime 真正落地前，先把这里的 boundary matrix 作为唯一 stop-condition authority
2. 让 `review_required`、`escalation`、`handoff` 全部统一落到 `waiting_external_resolution`，避免再发明 `wait_review` 之类的细分 lifecycle
3. 下一步不要立刻写 runtime，而是先回看 Slice 1-3 三份草案是否已经足够支持 gate close

这样能保持 bridge 的 contract 面仍然很薄，同时把未来 runtime 的 stop/continue 规则提前压成 deterministic doc surface。