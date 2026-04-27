# 方向分析 — Group Internal Handoff / Escalation Terminal Semantics

## 背景

Workspace Parallel Task Orchestration 的 Route A 已连续收口完成：

1. parallel-safe subgraph fan-out / fan-in foundation
2. executor-local real multi-child subgraph batch
3. shared-review zone contract / preflight
4. zone-approved payload writeback semantics

当前 parallel runtime 已经拥有一条最小闭环：

- parent-issued lineage / namespace
- strict preflight + shared-review zone 显式例外
- grouped review driver / summary
- reviewer `approve` 后的 approval-driven grouped payload writeback

因此下一条真正还没被 runtime 正式吃下来的缺口，不再是 overlap / review / writeback，而是 **group 内 child 若触发 handoff 或 escalation，整个 group 的 terminal semantics 应如何收口**。

这条问题其实在更早文档里已经被反复延后：

- `design_docs/parallel-safe-subgraph-post-slice3-direction-analysis.md`
- `design_docs/stages/planning-gate/2026-04-24-executor-local-real-multichild-subgraph-batch.md`
- `design_docs/stages/planning-gate/2026-04-24-shared-review-zone-contract-and-preflight.md`

它现在值得重新拿出来，因为其它更底层闭环已经完成。

## 关键未决问题

当某个 child 在 group 内部要求 `handoff` 或 `escalation` 时，当前 runtime 至少有四个语义空洞：

1. 这是 child 自身的 terminal outcome，还是整个 group 的 terminal outcome
2. parent 是否还能继续消费其它 child 的结果，还是必须整体暂停
3. grouped review / grouped writeback summary 如何表示这种 authority transfer
4. audit / tracing 上应把 authority 转移归到 child、group，还是 parent terminal envelope

## 外部借鉴

基于 `review/research-compass.md`，当前最相关的借鉴不是 patch merge，而是 handoff / lifecycle：

1. AutoGen：teams / handoff / human escalation
2. OpenAI Agents SDK：handoff 作为一等原语 + guardrail / tracing

这些借鉴说明 handoff 不应被偷偷塞进普通 child result；它更像一个显式 terminal boundary。

## 候选方向

### A. Group-level terminal bundle（推荐）

做什么：

1. child 可产生 handoff / escalation 请求
2. parent 不把它当普通 child success 继续 merge
3. 而是把 group 收口成一个明确的 terminal bundle，交给 parent / reviewer 决定后续 authority transfer

优点：

1. 与现有 handoff 原语更一致
2. 不会把 authority transfer 偷渡进普通 grouped review path
3. audit / tracing 比较容易保持清楚

风险：

1. 需要新增 group terminal surface
2. 可能影响 grouped review / writeback / checkpoint 总结口径

### B. Child-local handoff, parent keeps merging

做什么：

1. 某个 child 的 handoff / escalation 只记在 child record
2. parent 继续处理其它 child，并照常进入 grouped review / writeback

优点：

1. 改动看起来更小

风险：

1. authority transfer 容易与普通 child result 混淆
2. grouped terminal state 会变得很难解释

### C. Continue forbidding group-internal handoff / escalation

做什么：

1. 保持当前 guard，不让 group 内 child 进入 handoff / escalation
2. 把这块继续留到更高层 orchestration bridge / daemon 再处理

优点：

1. 风险最低

风险：

1. Route A 的 runtime 语义会长期缺一块明显边界
2. 一旦用户真的在 group 内部撞到 authority transfer，当前语义会显得生硬

## 当前推荐

我当前倾向于 **A. Group-level terminal bundle**。

原因：

1. handoff / escalation 本质上是 authority transfer，不适合伪装成普通 child success。
2. 这条路最符合 `review/research-compass.md` 里对 handoff 原语和 tracing 的借鉴。
3. 它可以让 Route A 继续沿“显式 companion/result surface”推进，而不用突然跳到 orchestration bridge / daemon 层。

## 建议的下一步

若继续推进，我建议下一条 planning-gate 聚焦：

- `Group Internal Handoff / Escalation Terminal Bundle`

建议只覆盖：

1. child handoff / escalation 如何升级成 group terminal outcome
2. grouped review / grouped writeback 在该终态下如何停止或转向
3. audit / checkpoint / summary 的最小 companion/result surface

明确不做：

1. orchestration bridge / daemon runtime
2. team/swarm scheduler
3. 更深层跨 group 调度