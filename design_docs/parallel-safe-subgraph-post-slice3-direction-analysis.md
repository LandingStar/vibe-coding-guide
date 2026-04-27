# 方向分析 — Parallel-Safe Subgraph After Slice 3 Deep Foundation

## 背景

`design_docs/stages/planning-gate/2026-04-24-parallel-safe-subgraph-fanout-fanin.md` 当前已经完成三层基础收口：

1. Slice 1 foundation：`TaskGroup` / `ParallelChildTask` / `ChildExecutionRecord`、parent-issued lineage / namespace、dispatch preflight
2. Slice 2 foundation：`MergeBarrierOutcome` 与 parent-side conflict classification
3. Slice 3 deep foundation：`GroupedReviewOutcome`、`grouped_review_state` 镜像、grouped review audit events、grouped review write-back summary、以及 `all_clear` 下的 child payload write-back

这意味着平台已经不再停留在 docs-only contract 假设，而是已经在现有 `subgraph` / `executor` / `writeback` 表面上，证明了 parallel-safe contract 的单 child 镜像路径可以成立。

当前真正剩下的问题也因此收缩了：

- 不是“要不要 grouped review”
- 不是“要不要 merge barrier”
- 而是“真实 multi-child dispatch 应该在哪一层出现，以及它如何与 grouped review / handoff / escalation 收口”

本文只回答这个下一阶段的方向选择，**不进入实现**。

## 当前判断

当前最重要的新事实有三条：

1. 现有 executor 已经足够承载 parent-managed companion objects 与 grouped review 镜像，不需要立刻引入新的 daemon / bridge 才能继续前进。
2. 当前 write-back 已经可以在 `all_clear` 下消费 child payload，但真实运行路径仍只会产出单个 `child_execution_record`。
3. 若下一步直接做“真实 multi-child fan-out”，最先需要回答的不是线程并发，而是：
   - child batch 是谁生成
   - child 内是否允许 handoff / escalation
   - grouped review 的终态如何反映到 parent review / write-back

因此，下一阶段不再是单纯实现问题，而是一个 runtime boundary 选择问题。

## 候选方向

### A. Executor-local real multi-child subgraph batch

做什么：

1. 在当前 executor 内允许一个 parent delegation 显式携带多个 child contracts
2. 真实产出多个 `child_execution_records`
3. 继续复用现有 `TaskGroup` / `MergeBarrierOutcome` / `GroupedReviewOutcome` / `grouped_review_state`
4. 第一轮只允许 group 内 child 作为 `subgraph` worker，不允许 group 内再触发 handoff / escalation

推荐的第一版收口顺序：

1. parent-built child contract batch
2. executor 内部的 multi-child dispatch loop
3. multi-child merge barrier + grouped review outcome
4. `all_clear` 下的 multi-child payload write-back

优点：

1. 与当前实现连续性最高
2. 可以最早得到“真实 multi-child path”这个关键信号
3. 不需要同时引入新的 orchestration layer

风险：

1. executor 会继续变厚
2. 若 group 内 handoff / escalation 语义不先禁掉，复杂度会立刻失控

### B. Group terminal semantics before real multi-child dispatch

做什么：

1. 暂不进入真实 multi-child dispatch
2. 先固定 grouped review / handoff / escalation 的终态边界
3. 明确：
   - 哪些 child result 允许直接进入 grouped review
   - 哪些 child blocked 应整体升级为 parent escalation
   - group 内 handoff 是禁止、延迟，还是 bundle 到 parent terminal outcome

优点：

1. 语义风险最低
2. 能先把治理边界说清楚，再做 runtime

风险：

1. 会重新回到 docs-first
2. 对“真实 multi-child runtime 是否成立”的信息增益较低

### C. Pivot to orchestration bridge now

做什么：

1. 不再让 executor 继续承载真实 multi-child dispatch
2. 新起 orchestration bridge / daemon layer
3. 把当前 runtime 作为每个 child task 的治理内核

优点：

1. 长期架构更整洁
2. 更贴近未来 `team/swarm` 演进

风险：

1. 当前过早
2. 会把这轮已经证明可行的 executor-local contract 连续性打断

## 当前推荐

我当前倾向于优先走 **A. Executor-local real multi-child subgraph batch**，但要带两条强硬边界：

1. group 内 child 第一轮只允许 `subgraph` worker，不允许 handoff / escalation 嵌套
2. grouped review 仍继续镜像到现有 `ReviewStateMachine`，不新增第二套 grouped review 状态机

原因：

1. 当前最缺的新信息不是更高层的语义讨论，而是“真实 multi-child path 在当前 runtime 里是否还能保持 contract 连续性”。
2. 这条路线能在不引入 bridge / daemon 的前提下，直接验证 `TaskGroup` 这套 companion objects 是否真能承载多个 child。
3. handoff / escalation 一旦进入 group 内部，scope 会陡增；先把它们显式排除，能把下一条 planning-gate 保持在可实现大小。

## 当前建议的下一条 planning-gate

若继续实现，下一条 planning-gate 建议聚焦：

- `Executor-local Real Multi-Child Subgraph Batch`

建议本轮只覆盖：

1. parent-built child contract batch input
2. executor 内 multi-child dispatch loop
3. 多个 `child_execution_records` 的真实产出
4. 真实 multi-child merge barrier / grouped review / `all_clear` child payload write-back

明确不做：

1. group 内 handoff
2. group 内 escalation
3. orchestration bridge / daemon
4. `team/swarm` runtime