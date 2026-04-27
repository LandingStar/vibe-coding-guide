# 设计草案 — Orchestration Bridge Slice 2 Governance Result Projection

本文是 `design_docs/stages/planning-gate/2026-04-25-orchestration-bridge-work-item-group-item-contract.md` 的 Slice 2 设计草案。

## 目标

Slice 1 已经固定了 bridge primitive 的 identity、ownership boundary 与最小 lifecycle transition table。

Slice 2 当前只解决一个更窄的问题：

1. executor-local governance kernel 产出的结果，最小应该如何投影到 `BridgeGroupItem`
2. bridge 需要缓存哪些 compact footprint 字段，才能驱动后续调度判断
3. 哪些内容仍然必须保留在 governance-owned source of truth，而不是复制到 bridge

本文不定义：

1. `BridgeWorkItem` 如何据此进入 stop / wait / resume
2. terminal landing artifact
3. external resolution 完成后的恢复机制

## 当前输入面

当前已经存在、且足以支撑投影的治理结果面包括：

1. `GroupedReviewOutcome` / `grouped_review_state`
2. `GroupTerminalOutcome`
3. grouped child writeback summary / eligibility basis
4. blocked merge / preflight / validator 路径产生的 blocked reason

因此当前不建议再创造 bridge-only 的第四套结果对象。更稳的做法是把 bridge 需要的内容压成一个 compact projection。

## 当前推荐的 compact projection 字段

当前推荐 `BridgeGroupItem` 至少补齐或固定以下结果 footprint：

- `governance_surface_kind: str`
- `governance_surface_state: str = ""`
- `blocked_reason: str = ""`
- `writeback_disposition: str = "pending"`

字段解释：

1. `governance_surface_kind`：说明当前看到的是哪一类治理面，例如 `grouped_review`、`group_terminal`、`blocked`、`none`
2. `governance_surface_state`：仅保存该治理面的最小子状态，例如 `all_clear`、`review_required`、`escalation`、`handoff`
3. `blocked_reason`：仅缓存最后可见的阻塞原因，不成为新权威来源
4. `writeback_disposition`：只表达 bridge 可观察到的 writeback 处置口径，而不是重做 writeback planning

当前建议的 `writeback_disposition` 最小集合：

- `pending`
- `eligible`
- `suppressed`
- `blocked`
- `none`

## Field Contract Matrix

| 字段 | 允许值 | 来源 | 归一化规则 | 当前边界 |
|---|---|---|---|---|
| `governance_surface_kind` | `none`, `grouped_review`, `group_terminal`, `blocked` | executor-local result family | 必须只按 source surface family 归类，不能从 lifecycle 反推 | 不新增 bridge-only result family |
| `governance_surface_state` | `""`, `all_clear`, `review_required`, `escalation`, `handoff`, `blocked` | source surface 的最小子状态 | 当 kind=`none` 时必须为空字符串；其余值必须与 `governance_surface_kind` 一致 | 只保留最小 label，不复制完整 payload |
| `blocked_reason` | 空字符串或 source blocked reason 文本 | blocked path / terminal bundle / validator guard | 只能镜像最后可见原因，不能凭 bridge 调度状态自行合成 | 不是新权威来源 |
| `writeback_disposition` | `pending`, `eligible`, `suppressed`, `blocked`, `none` | grouped child writeback summary / terminal suppression / blocked path | 必须表达 bridge 可观察到的处置口径，而不是新的 writeback planner 决策 | 只做 projection，不做 planning |

进一步的按列规则：

1. `governance_surface_kind=grouped_review` 时，`governance_surface_state` 只允许 `all_clear` 或 `review_required`
2. `governance_surface_kind=group_terminal` 时，`governance_surface_state` 只允许 `escalation` 或 `handoff`
3. `governance_surface_kind=blocked` 时，`governance_surface_state` 固定为 `blocked`
4. `governance_surface_kind=none` 时，`governance_surface_state` 必须为空，`blocked_reason` 也必须为空
5. `writeback_disposition=suppressed` 只在 terminal suppression 路径出现，不用来表达普通 review wait
6. `writeback_disposition=none` 只表示当前没有 child writeback payload 可做，不表示 bridge 可以跳过治理决策

## Projection Matrix

| executor-local source surface | `governance_surface_kind` | `governance_surface_state` | `blocked_reason` | `writeback_disposition` | bridge boundary |
|---|---|---|---|---|---|
| 尚无可消费治理结果 | `none` | `` | `` | `pending` | bridge 只知道仍在等待 footprint，不推导更多语义 |
| `GroupedReviewOutcome` with `grouped_review_state=all_clear` | `grouped_review` | `all_clear` | `` | `eligible` or `none` | 是否真的执行 writeback 仍由 governance kernel 决定 |
| `GroupedReviewOutcome` with `grouped_review_state=review_required` | `grouped_review` | `review_required` | `` | `pending` | bridge 只知道结果仍未完全放行，不在此定义 stop rule |
| `GroupTerminalOutcome` with `terminal_kind=escalation` | `group_terminal` | `escalation` | source blocked reason if any | `suppressed` | bridge 看见 authority-transfer footprint，但不在此定义 landing artifact |
| `GroupTerminalOutcome` with `terminal_kind=handoff` | `group_terminal` | `handoff` | source blocked reason if any | `suppressed` | bridge 只缓存最小 terminal kind 与原因 |
| blocked merge / preflight / validator path | `blocked` | `blocked` | source blocked reason | `blocked` | blocked 的 source of truth 仍留在 governance-owned object |

## 结构性边界

当前推荐继续保持三条边界：

1. `lifecycle_state` 只表达 bridge 调度阶段
2. `governance_surface_kind` / `governance_surface_state` / `blocked_reason` / `writeback_disposition` 只表达 compact result footprint
3. stop-condition、resume、external takeover 后的回流语义全部留到 Slice 3

换句话说，Slice 2 的目标不是教 bridge “怎么行动”，而是先固定 bridge “最少看见什么”。

## 当前不做的设计

当前不做：

1. work-item 级别的 roll-up algorithm
2. `waiting_external_resolution` 的恢复入口
3. terminal landing artifact schema
4. bridge 对 grouped review / group terminal 详细 payload 的本地镜像

## 当前推荐

我当前推荐：

1. 把 `BridgeGroupItem` 的 compact result projection 固定成上面的 4 个字段
2. 保持 `writeback_disposition` 只表达可观察处置，不重做 writeback 规划
3. 先不要把 stop-condition 和 work-item roll-up 混进 Slice 2

这样能保证下一步进入 Slice 3 时，bridge 的“状态轴”和“治理结果轴”仍然是分开的。