# 设计草案 — Group Internal Handoff / Escalation Slice 1 Contract

本文是 `design_docs/stages/planning-gate/2026-04-24-group-internal-handoff-escalation-terminal-bundle.md` 的 Slice 1 设计草案。

## 目标

当前目标不是马上让 group 内 child 自由触发 handoff / escalation 并贯通整个 runtime，而是先引入一条**显式、默认收紧、可审计**的 group terminal bundle 路径：

1. child 仍可提供 handoff / escalation 证据
2. 这类证据一旦被 parent 认可，不再继续走普通 grouped review / grouped writeback
3. 整个 group 收口成一个单独的 terminal outcome，作为后续 authority transfer 的唯一入口

## 设计原则

1. 不重写现有 `Subagent Report` / `Handoff` 主 schema 家族
2. 不把 authority transfer 伪装成普通 child success 或普通 grouped review outcome
3. 优先把 group terminal 语义放在现有 companion objects / executor result surface 上
4. Slice 1 先解决“谁触发 terminal bundle、触发后哪些路径必须停止”，不直接扩到 handoff persistence 或更深层调度

## 当前输入证据面

当前最接近 group terminal 语义的输入证据已经存在：

1. `Subagent Report.escalation_recommendation`
2. `handoff` mode 产生的显式 `Handoff` 对象
3. child 执行结果的 `status` / `unresolved_items` / `assumptions`

因此 Slice 1 不建议新开一套 child 输入 schema。更窄的做法是：

1. 继续允许 child 报告 escalation recommendation
2. 继续把显式 `Handoff` 视为 authority transfer 的正式对象
3. 由 parent/executor 把这些证据归一成 group terminal bundle

## 推荐的最小 companion/result surface

### 1. 新 companion object：`GroupTerminalOutcome`

推荐新增：

- `task_group_id: str`
- `terminal_kind: str`
  - `handoff`
  - `escalation`
- `source_child_ids: list[str]`
- `trigger_evidence: list[dict]`
- `authoritative_refs: list[str]`
- `open_items: list[str]`
- `current_gate_state: str`
- `blocked_reason: str = ""`

用途：

1. 表达整个 group 已经不再处于普通 merge/review/writeback 路径
2. 保留 authority transfer 需要带走的最小上下文
3. 让 audit / tracing / checkpoint 有单点可引用的 terminal surface

当前不推荐在 Slice 1 就把完整 `Handoff` 对象直接嵌进 `GroupTerminalOutcome`。更稳的做法是先保留 terminal bundle 与 `Handoff` 的边界，再在后续 slice 决定如何落地 persistence。

### 2. execution result surface

当前 `subgraph` multi-child result 已经有：

- `task_group`
- `child_execution_records`
- `merge_barrier_outcome`
- `grouped_review_outcome`

Slice 1 推荐最小扩展为：

- `group_terminal_outcome`

并定义一条 stop/turn 规则：

1. 若 `group_terminal_outcome` 存在，则当前执行结果不继续承诺普通 grouped review / grouped writeback convergence
2. outer `review_state` 仍然存在，因为 authority transfer 自身也可能受 review gate 约束
3. `grouped_review_outcome` / `grouped_child_writeback_summary` 在该路径下要么缺席，要么明确标记为 `suppressed_by_group_terminal`

Slice 1 不建议直接复用 `GroupedReviewOutcome` 表达 group terminal，因为 grouped review 与 authority transfer 不是一回事。

## 推荐的 terminal 归一规则

### 1. escalation 优先于 handoff

若同一 group 内同时出现：

1. child escalation recommendation
2. child handoff evidence

则 Slice 1 推荐先收口为 `terminal_kind = escalation`。

原因：

1. escalation 代表更高 authority / human reviewer 已经被拉入语境
2. 它比普通 authority transfer 更应优先停止当前 group merge path

### 2. 仅在显式 terminal 证据成立时创建 bundle

以下情况之一成立时，可触发 `GroupTerminalOutcome`：

1. child 结果携带显式 `Handoff`
2. child 报告中的 `escalation_recommendation` 不是 `none`，且 parent 规则允许升级

仅有 `unresolved_items` 或 `partial` 状态，不足以自动创建 group terminal bundle。

### 3. first version 默认停止 merge / grouped review / writeback

一旦 `GroupTerminalOutcome` 形成：

1. 不继续做普通 merge barrier classification
2. 不进入普通 grouped review driver
3. 不进入 grouped child payload writeback planning

这条规则的意义是：

1. authority transfer 先被显式看见
2. 不让普通 review/writeback surface 混进混合终态

## 当前不做的设计

Slice 1 明确不做：

1. 在 group terminal bundle 内直接持久化完整 `Handoff`
2. 多层 chained handoff / escalation
3. child-local handoff 后其它 child 继续 merge 的混合终态
4. orchestration bridge / daemon 层调度

## 当前仍保持 forbidden 的路径

1. child 触发 handoff / escalation 后，parent 继续把该 child 当普通 success 参与 grouped review
2. 在同一轮 group 执行里，同时出现 group terminal bundle 与 grouped child payload writeback
3. 自动把 `partial` / `blocked` 普通结果提升为 handoff

## 当前推荐

我当前推荐：

1. 引入独立 companion object `GroupTerminalOutcome`
2. 继续复用现有 `Handoff` 与 `escalation_recommendation` 作为输入证据，而不是再开新的 child schema
3. terminal bundle 一旦形成，就停止普通 grouped review / grouped writeback 路径
4. Slice 1 先只处理 single-group terminal semantics，不扩到更深层 runtime

这条路线最符合当前权威边界：

1. `Handoff` 仍只表达 authority transfer
2. `Report` 仍只表达执行结果
3. group terminal bundle 只是 parent orchestration 的 companion/result surface