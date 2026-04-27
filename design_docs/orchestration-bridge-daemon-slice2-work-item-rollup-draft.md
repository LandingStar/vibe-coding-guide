# 设计草案 — Orchestration Bridge Slice 2 Work Item Roll-Up

本文是 `design_docs/stages/planning-gate/2026-04-25-orchestration-bridge-work-item-group-item-contract.md` 的 Slice 2 设计草案补充，建立在 `design_docs/orchestration-bridge-daemon-slice2-governance-result-projection-draft.md` 已固定的 `BridgeGroupItem` compact result projection 之上。

## 目标

当前只解决一个更窄的问题：

1. 多个 `BridgeGroupItem` 的 compact result footprint，最小应该如何汇总到 `BridgeWorkItem`
2. work-item 需要缓存哪些聚合字段，才能表达“当前最强治理结果”而不复制全部 group-item payload
3. roll-up 如何保持 deterministic，而不把 bridge 推成第二套治理内核

本文不定义：

1. work-item 何时进入 `waiting_external_resolution` / `completed` / `blocked`
2. terminal landing artifact
3. external resolution 完成后的 resume / retry / restart 语义

## 当前输入面

roll-up 只消费现有 `BridgeGroupItem` 上已经固定的字段：

- `group_item_id`
- `lifecycle_state`
- `governance_surface_kind`
- `governance_surface_state`
- `blocked_reason`
- `writeback_disposition`

因此当前推荐仍然是 projection-over-projection，而不是把 `GroupedReviewOutcome` / `GroupTerminalOutcome` 重新搬到 work-item。

## 当前推荐的最小 roll-up 字段

当前推荐 `BridgeWorkItem` 至少补齐以下聚合 footprint：

- `rollup_surface_kind: str`
- `rollup_surface_state: str = ""`
- `rollup_blocked_reason: str = ""`
- `rollup_writeback_disposition: str = "pending"`
- `dominant_group_item_ids: list[str]`
- `open_group_item_count: int = 0`

字段解释：

1. `rollup_surface_kind`：当前最强 group-item 治理结果属于哪一类 surface family
2. `rollup_surface_state`：该 family 的最小子状态
3. `rollup_blocked_reason`：dominant group-item 暴露出的最后可见原因；仅镜像，不成为新权威来源
4. `rollup_writeback_disposition`：从 group-item 的 writeback footprint 聚合得到的 work-item 级观察口径
5. `dominant_group_item_ids`：哪些 group-item 共同决定了当前 dominant roll-up
6. `open_group_item_count`：当前还未 `settled` 的 group-item 数量；只表示开放数量，不复制完整进度清单

## Deterministic Roll-Up Rules

1. 只有 `lifecycle_state=settled` 的 group-item 可以参与 `rollup_surface_*` 的 dominant 计算
2. 未 `settled` 的 group-item 只增加 `open_group_item_count`，不单独创造新的 roll-up surface family
3. `dominant_group_item_ids` 必须按稳定顺序排序；当前建议按 `group_item_id` 字典序
4. 如果没有任何 `settled` group-item，则 work-item roll-up 固定为：
   - `rollup_surface_kind=none`
   - `rollup_surface_state=""`
   - `rollup_blocked_reason=""`
   - `rollup_writeback_disposition=pending`
   - `dominant_group_item_ids=[]`
5. `rollup_blocked_reason` 只从 `dominant_group_item_ids` 里取第一个非空 reason；若 dominant set 内都为空，则保持空字符串

## Surface Precedence Matrix

`rollup_surface_kind` 与 `rollup_surface_state` 当前推荐按以下优先级聚合：

| settled group-item 条件 | `rollup_surface_kind` | `rollup_surface_state` | `dominant_group_item_ids` | 说明 |
|---|---|---|---|---|
| 任一 `governance_surface_kind=blocked` | `blocked` | `blocked` | 所有 blocked group-item | blocked 始终优先于其他 surface family |
| 否则，任一 `group_terminal/escalation` | `group_terminal` | `escalation` | 所有 escalation group-item | escalation 在 terminal family 内高于 handoff |
| 否则，任一 `group_terminal/handoff` | `group_terminal` | `handoff` | 所有 handoff group-item | 仍属于 authority-transfer footprint |
| 否则，任一 `grouped_review/review_required` | `grouped_review` | `review_required` | 所有 review_required group-item | review gate 高于 all_clear |
| 否则，任一 `grouped_review/all_clear` | `grouped_review` | `all_clear` | 所有 all_clear group-item | 表示当前最强 settled 结果是可放行 grouped review |
| 否则 | `none` | `""` | `[]` | 当前没有 settled governance footprint |

当前矩阵只回答“当前最强 settled 结果是什么”，不回答 work-item 应不应该停机或完成。

## Writeback Roll-Up Matrix

`rollup_writeback_disposition` 当前推荐按更保守的聚合规则计算：

| 条件 | `rollup_writeback_disposition` | 说明 |
|---|---|---|
| 任一 settled group-item 为 `blocked` | `blocked` | blocked 直接压过其他 writeback disposition |
| 否则，任一 settled group-item 为 `suppressed` | `suppressed` | terminal suppression 直接主导 work-item 观察口径 |
| 否则，`open_group_item_count > 0` | `pending` | 只要仍有未结算 group-item，就不把 work-item 宣布为 `eligible` |
| 否则，任一 settled group-item 为 `pending` | `pending` | 已 settled 的结果仍未给出可执行 writeback |
| 否则，任一 settled group-item 为 `eligible` | `eligible` | 仅在没有更高优先级且所有 group-item 已 settled 时出现 |
| 否则 | `none` | 当前没有 child writeback payload 可做 |

## 结构性边界

当前推荐继续保持三条边界：

1. `BridgeGroupItem` 继续作为 bridge 与 governance kernel 之间的最小 result adapter
2. `BridgeWorkItem` 只保留 dominant roll-up 与开放数量，不复制所有 group-item payload
3. stop-condition、external resolution、resume/retry 语义继续留给下一条 Slice 3 draft

换句话说，roll-up 只把多个 group-item 压成一个 deterministic 观察面，不负责把观察面解释成行动策略。

## 当前不做的设计

当前不做：

1. work-item 级终态机
2. `dominant_group_item_ids` 之外的完整 group-item 进度镜像
3. terminal landing artifact schema
4. bridge 级别的恢复/重试策略

## 当前推荐

我当前推荐：

1. 在 `BridgeWorkItem` 上使用 `rollup_` 前缀字段，而不是复用 group-item 原字段名
2. 用 `open_group_item_count` 保留最小进度信号，避免为了 stop-condition 提前复制完整进度表
3. 在下一条 Slice 3 draft 中，直接消费这里的 roll-up 结果与现有 `work_item.lifecycle_state`，定义 stop-condition boundary

这样能保证 bridge 的结构仍然保持为：group-item 负责接治理结果，work-item 负责看聚合结果，而不是让两层对象互相复制。