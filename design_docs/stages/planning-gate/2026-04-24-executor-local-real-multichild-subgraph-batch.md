# Planning Gate — Executor-local Real Multi-Child Subgraph Batch

> 创建时间: 2026-04-24
> 状态: COMPLETE

## 文档定位

本文件把 post-Slice3 direction analysis 收敛为下一条可执行的窄 scope planning contract。

本候选直接承接：

- `design_docs/stages/planning-gate/2026-04-24-parallel-safe-subgraph-fanout-fanin.md`
- `design_docs/parallel-safe-subgraph-post-slice3-direction-analysis.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `docs/subagent-management.md`
- `docs/subagent-schemas.md`

当前只锁定**executor 内的真实 multi-child subgraph batch**，不提前进入 orchestration bridge / daemon、group 内 handoff、group 内 escalation、或 `team/swarm` runtime。

这里的“真实 multi-child”当前采用最小定义：

1. 一个 parent delegation 在同一个 `TaskGroup` 中显式携带多个 child contracts
2. runtime 真实执行多个 child，并产出多个 `child_execution_records`
3. merge barrier / grouped review / write-back 真实消费多个 child result

当前**不要求**第一轮就进入线程级并发或异步 fan-out；第一轮允许 executor 内部先用确定性 dispatch loop 验证 runtime 语义。

当前已批准的第一版边界：

- strict preflight 继续要求 child `allowed_artifacts` 可证明不重叠
- real multi-child runtime 第一版默认只承诺 `all_clear-only`
- conflict-bearing `review_required` grouped review 作为后续显式扩展候选保留，不在本 gate 内继续扩 scope

## 当前实现进展

- 已完成 Slice 1：`src/pep/executor.py` 已支持 parent-provided `parallel_children` child batch hints，并可在同一个 `TaskGroup` 中真实运行多个 child，产出多个 `child_execution_records` / `subgraph_contexts`
- 已证明 real multi-child `all_clear` 闭环：现有 `MergeBarrierOutcome` / `GroupedReviewOutcome` / grouped child payload write-back 已能消费真实 multi-child result
- 已完成针对性验证：`tests/test_collaboration.py tests/test_pep_writeback_integration.py` 当前合计通过 63 项回归
- 实施中发现新的语义边界：在当前 strict preflight 仍要求 `allowed_artifacts` 不重叠的前提下，真实 multi-child batch 可以稳定证明 `all_clear` 路径，但会让 conflict-bearing `review_required` merge 在正常输入上变得难以到达；详见 `design_docs/parallel-safe-subgraph-conflict-bearing-grouped-review-direction-analysis.md`

## 当前问题

- 当前 real multi-child `all_clear` 路径已经成立，并已被批准为第一版权威边界
- conflict-bearing `review_required` grouped review 已被明确下放到后续方向，不再在本 gate 内继续扩 scope
- 若此时放开 group 内 handoff / escalation，复杂度会立即扩展到第二套终态语义与更深 lineage

## 权威输入

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/stages/planning-gate/2026-04-24-parallel-safe-subgraph-fanout-fanin.md`
- `design_docs/parallel-safe-subgraph-post-slice3-direction-analysis.md`
- `design_docs/workspace-parallel-task-orchestration-direction-analysis.md`
- `docs/subagent-management.md`
- `docs/core-model.md`
- `docs/subagent-schemas.md`
- `src/pep/executor.py`
- `src/pep/writeback_engine.py`
- `tests/test_collaboration.py`
- `tests/test_pep_writeback_integration.py`

## 候选阶段名称

- `Executor-local Real Multi-Child Subgraph Batch`

## 本轮只做什么

- 固定 parent-built child contract batch 的最小输入面
- 在 executor 的 subgraph 路径中，真实 dispatch 多个 child contract
- 真实产出多个 `child_execution_records`
- 让 `MergeBarrierOutcome` / `GroupedReviewOutcome` / grouped review write-back summary 在真实 multi-child 输入上成立
- 保持 `grouped_review_state` 继续镜像到现有 `ReviewStateMachine`

## 本轮明确不做什么

- 不做线程级并发调度器
- 不做 orchestration bridge / daemon
- 不允许 group 内 child 再触发 handoff
- 不允许 group 内 child 再触发 escalation
- 不引入第二套 grouped review 状态机
- 不进入 `team/swarm` runtime

## 当前推荐的运行规则

### 1. Child batch input rule

- parent 必须显式提供 child contract batch，不做 runtime 内的动态 child 发现
- 每个 child 仍复用现有 `Subagent Contract` 边界
- group 内 child 仍必须满足现有 namespace / `allowed_artifacts` / `required_refs` 约束

### 2. Dispatch rule

- 第一轮允许 executor 内部使用确定性 dispatch loop
- “真实 multi-child”在本轮的判定标准不是线程数，而是 runtime 是否真正消费并返回多个 child result
- dispatch 前继续执行现有 preflight，并补 group 内禁止 handoff / escalation 的 guard

### 3. Merge and review rule

- merge barrier 必须真实汇总多个 child result 后再分类
- grouped review outcome 必须保留 child 粒度的 changed artifacts / unresolved items / assumptions
- grouped review 仍通过 `grouped_review_state` 镜像到现有 review state，而不是独立状态机

### 4. Write-back rule

- 只有 `all_clear` 且 review state `applied` 时，才允许 child payload write-back
- 第一轮的目标不是重新设计 write-back，而是证明现有 grouped child payload planning 能消费真实 multi-child result

## 当前推荐的实施顺序

### Slice 1 — Parent-built child batch + executor dispatch loop

- 补 parent delegation 到 child contract batch 的最小输入面
- 让 executor 在单个 `TaskGroup` 内真实运行多个 child
- 真实产出多个 `child_execution_records`

当前状态：已实现，并由 `tests/test_collaboration.py::TestExecutorSubgraphMode::test_subgraph_mode_dispatches_real_multi_child_batch` 覆盖

### Slice 2 — Real multi-child merge barrier + grouped review outcome

- 让 `MergeBarrierOutcome` 与 `GroupedReviewOutcome` 基于多个真实 child result 生成
- 保持 `blocked` / `review_required` / `all_clear` 的现有语义不变

当前状态：helper 层已可消费真实 multi-child result；相关边界已通过 `design_docs/parallel-safe-subgraph-conflict-bearing-grouped-review-direction-analysis.md` 收口，并批准为 strict preflight 下的 `all_clear-only` 第一版语义

### Slice 3 — Real multi-child write-back convergence

- 证明 grouped review write-back summary 与 grouped child payload write-back 可消费真实 multi-child result
- 只验证当前 `all_clear` 路径，不扩到 group 内 handoff / escalation

当前状态：`all_clear` real multi-child child payload write-back 已由 `tests/test_pep_writeback_integration.py::TestGroupedReviewWriteback::test_subgraph_multi_child_batch_applied_executes_grouped_payload_writeback` 覆盖

## 验收与验证门

- 针对性测试：
  - parent-built child batch 的最小输入校验
  - executor 在一个 `TaskGroup` 中产出多个 `child_execution_records`
  - 多 child 的 merge barrier / grouped review 分类测试
  - `all_clear` 多 child payload write-back 测试
- 更广回归：
  - 现有单 child `worker` / `handoff` / `subgraph` 路径不回归
  - 现有 grouped review state 镜像与 write-back integration 不回归
- 手测入口：
  - 两个 child 写不同文档，预期 `all_clear`
  - 两个 child 写同一文档重叠区域，预期 `review_required` 或 `blocked`
  - 任一 child 请求 group 内 handoff / escalation，预期被 preflight guard 拒绝

## 需要同步的文档

- `docs/subagent-management.md`
- `docs/core-model.md`
- `docs/subagent-schemas.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/checkpoints/latest.md`
- `.codex/handoffs/CURRENT.md`（仅当本候选完成并进入 safe stop 时）

## 子 agent 切分草案

- 若需要只读盘点，可让 investigator 汇总 `executor.py` 与当前测试面里最接近“child batch input / multi-result aggregation”的复用点
- child batch contract 命名、group 内禁止 handoff / escalation 的规则、以及 planning-gate write-back 仍由主 agent 负责

## 收口判断

- 为什么这条切片可以单独成立：它只验证“当前 executor 能否承载真实 multi-child runtime 语义”，不提前跳到更大 orchestration 层
- 做到哪里就应该停：当真实 multi-child dispatch、grouped review、和 `all_clear` write-back 都在当前 executor 路径上成立，并且第一版边界被明确写成 strict preflight 下的 `all_clear-only` 后就应停
- 下一条候选主线是什么：
  - 若未来要支持冲突路径，再单独起 `shared-review zone` planning-gate
  - 若上述方向完成，再单独分析 group 内 handoff / escalation terminal semantics
  - 若在实现时发现 executor 耦合过深，再回到 orchestration bridge / daemon 方向