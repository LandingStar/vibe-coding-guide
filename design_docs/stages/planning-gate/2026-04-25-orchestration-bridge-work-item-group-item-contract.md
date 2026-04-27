# Planning Gate — Orchestration Bridge Work Item / Group Item Contract

> 日期: 2026-04-25
> 状态: COMPLETE
> 关联方向分析: `design_docs/orchestration-bridge-daemon-layer-direction-analysis.md`

## 1. Why this gate exists

`Group Internal Handoff / Escalation Terminal Bundle` gate 已完成。

这意味着当前 executor-local parallel runtime 已经能在单个 parent-managed group 内完成：

1. strict preflight
2. grouped review / grouped child writeback
3. shared-review zone 例外
4. group terminal bundle（显式 escalation 与显式 child handoff）

因此当前最明显的空洞已经不再是 group 内治理语义，而是：

- 如果要进入 bridge / daemon 分叉，bridge 到底持有什么最小调度 primitive
- 哪些字段归 bridge 所有，哪些字段仍必须保持在现有 governance kernel 内

如果在这个节点继续直接把更高层调度语义叠进 `Executor`，会重新混淆两层职责：

1. `Executor` / `TaskGroup` / `GroupTerminalOutcome` 负责治理内核
2. bridge / daemon 负责更高层的 work-item lifecycle、group scheduling、recovery

因此，下一条最窄 planning-gate 应先固定 **bridge-owned work item / group item primitive**，而不是先跳到 landing artifact 或 full daemon runtime。

## 2. Scope

本 gate 只处理：

1. bridge / daemon 层应持有的最小 `work item` / `group item` primitive
2. bridge primitive 与现有 `Decision Envelope` / `TaskGroup` / `GroupTerminalOutcome` 的 ownership boundary
3. bridge 在不重写治理内核的前提下，至少需要哪些 lifecycle / result footprint 字段

本 gate 不处理：

1. terminal bundle 之后的 landing artifact / canonical handoff 落地
2. full daemon runtime / queue system / service deployment
3. dependency wake-up 自动执行
4. executor 内部实现或 scheduler runtime 代码

## 3. Working hypothesis

当前最小可行路线应是：

1. bridge 只新增 scheduler-facing primitive，而不是重写现有 governance object
2. `work item` 负责承载更高层调度身份与生命周期
3. `group item` 负责引用一个 executor-local group 的治理结果 footprint，而不是嵌入完整 child result surface
4. bridge 通过 compact projection 消费 grouped review / group terminal / writeback summary，而不直接决定 gate / review 语义

## 4. Slices

### Slice 1 — Work item / group item primitive contract

- 固定 bridge-owned `work item` / `group item` 的最小字段
- 明确哪些字段归 bridge 所有，哪些字段只允许引用现有 governance kernel
- 明确这两个 primitive 与 `Decision Envelope`、`TaskGroup`、`GroupTerminalOutcome` 的关系

当前状态：Slice 1 设计草案已创建为 `design_docs/orchestration-bridge-daemon-slice1-work-item-group-item-contract-draft.md`；当前已补出 bridge / executor / governance kernel 的 ownership matrix 与最小 lifecycle transition table。当前推荐把 bridge primitive 继续收窄成 scheduler-facing identity / lifecycle / governance-footprint wrapper，而不是让 bridge 复制完整 grouped review / terminal 对象。下一窄切口收束为：进入 Slice 2，定义 governance result footprint 如何投影到 `group item`。

### Slice 2 — Governance result projection into bridge state

- 定义 grouped review / group terminal / grouped child writeback summary 如何投影到 `group item`
- 定义 bridge 是否需要额外的 compact result kind / stop reason 字段
- 明确 bridge 只持有 result footprint，不重写内核对象

当前状态：Slice 2 设计草案已创建为 `design_docs/orchestration-bridge-daemon-slice2-governance-result-projection-draft.md`；当前已补出 `BridgeGroupItem` 的 compact result projection field matrix，并把 `governance_surface_kind` / `governance_surface_state` / `blocked_reason` / `writeback_disposition` 的允许值与归一化规则写清。当前已新增 `design_docs/orchestration-bridge-daemon-slice2-work-item-rollup-draft.md`，把 `BridgeWorkItem` 的 roll-up 字段、surface precedence 和 writeback precedence 固定下来。当前下一窄切口收束为：进入 Slice 3，定义 stop-condition boundary。

### Slice 3 — Bridge lifecycle / stop-condition boundary

- 定义 bridge primitive 至少需要哪些 lifecycle state
- 定义 `group terminal`、`waiting_review`、`blocked` 如何推动 bridge 停机、挂起或等待外部接管
- 为后续 runtime gate 准备 stop condition

当前状态：Slice 3 设计草案已创建为 `design_docs/orchestration-bridge-daemon-slice3-stop-condition-boundary-draft.md`；当前已把 `BridgeWorkItem.lifecycle_state` 与 Slice 2 roll-up 之间的 boundary matrix 写清，并明确 `review_required`、`escalation`、`handoff` 统一落到 `waiting_external_resolution`。当前下一步更适合回看 Slice 1-3 是否足以支撑 gate close，而不是立刻进入 runtime 实现。

## 5. Validation gate

- 文档验证：
  - 能清楚回答 `work item` / `group item` 分别属于哪一层
  - 能清楚回答 bridge 与 `Executor` 哪一层拥有 gate / review / writeback 决策权
  - 能清楚回答 bridge primitive 是否只是 compact wrapper，而不是第二套治理对象
  - 能清楚回答多个 `group item` 如何 deterministic 地汇总为一个 `work item` 观察面
  - 能清楚回答 `review_required`、`group_terminal`、`blocked` 何时推动 bridge 进入哪个 boundary judgment
- 未来代码验证：
  - bridge runtime 落地时不需要改写现有 grouped review / group terminal schema 才能接入
  - executor-local 路径在没有 bridge 时仍可独立工作

## 6. Stop condition

- 当 `work item` / `group item` primitive、ownership boundary、最小 lifecycle footprint、group-item result projection、以及 work-item roll-up 都已写清，并且 stop-condition boundary 已被单独收口后停止
- 不在本 gate 内直接进入 daemon runtime 实现或 terminal landing artifact 设计

## 7. Close note

当前 gate 已按 docs-only 边界完成：Slice 1-3 均已形成独立草案，且 validation gate 所要求的结构问题已能被回答。下一步不再继续扩写本 gate，而是转入 `design_docs/orchestration-bridge-contract-runtime-followup-direction-analysis.md` 讨论后续方向。