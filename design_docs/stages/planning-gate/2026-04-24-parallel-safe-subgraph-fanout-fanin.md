# Planning Gate — Parallel-Safe Subgraph Fan-Out / Fan-In

> 创建时间: 2026-04-24
> 状态: COMPLETE

## 文档定位

本文件把“同工作区任务并行编排”候选 A 收敛为下一条可执行的窄 scope planning contract。

本候选直接承接：

- `design_docs/workspace-parallel-task-orchestration-direction-analysis.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `docs/subagent-management.md`
- `docs/core-model.md`
- `design_docs/stages/planning-gate/2026-04-24-executor-local-real-multichild-subgraph-batch.md`

当前只锁定**parallel-safe subgraph orchestration 的最小 contract**，不提前进入 full task-graph runtime、team/swarm lifecycle、或外部 orchestration daemon 实现。

下一阶段方向分析见：

- `design_docs/parallel-safe-subgraph-post-slice3-direction-analysis.md`

当前 active planning-gate 已切换到：

- `design_docs/stages/planning-gate/2026-04-24-executor-local-real-multichild-subgraph-batch.md`

## 当前实现进展

- 已完成 Slice 1 foundation：`TaskGroup` / `ParallelChildTask` / `ChildExecutionRecord` 已落在 `src/interfaces.py`
- 已完成 parent-issued lineage / namespace surface：`src/collaboration/subgraph_mode.py` 与 `src/pep/executor.py` 已支持 `task_group_id` / `child_task_id` / parent-issued `namespace`
- 已完成 dispatch preflight foundation：`src/pep/executor.py` 已实现 namespace、unsafe path、`per-thread` persistence、disjoint write set overlap 校验；显式 lineage hints 的 subgraph 路径会先过 preflight 再执行
- 已完成 Slice 2 foundation：`src/interfaces.py` / `src/pep/executor.py` 已新增 `MergeBarrierOutcome` 与 parent-side merge barrier conflict classification helper，当前覆盖 `no_conflict` / `review_required` / `blocked`
- 已完成 Slice 3 foundation：`src/interfaces.py` / `src/pep/executor.py` / `src/pep/writeback_engine.py` 已新增 `GroupedReviewOutcome`、grouped review audit events、grouped review write-back summary interface、`grouped_review_state` 到现有 `ReviewStateMachine` 的镜像、以及 `all_clear` 下的 child payload write-back；当前 grouped review 仍复用现有 `ReviewStateMachine`
- 已完成针对性验证：`tests/test_collaboration.py`、`tests/test_pep_delegation.py` 已覆盖并通过相关回归
- 尚未完成 Slice 3 收口：当前仍没有独立 grouped review 状态迁移、真实 multi-child fan-out dispatch、或真实 multi-child payload write-back 汇合

## 当前问题

- 当前平台的 delegation 仍按 `single-contract / single-worker / single-report / single-review` 建模
- `subgraph` 已具备 namespace 隔离与 delta merge 雏形，但还没有 fan-out、barrier、multi-child merge、grouped review 的 contract
- `team/swarm` 目前只存在于文档与 schema 允许值层，不是可执行 runtime primitive
- 若在没有并行安全 contract 的前提下直接“支持并行”，最先失控的不是线程，而是 `allowed_artifacts`、namespace、merge、review 与 tracing 的边界
- LangGraph、AutoGen、Multica、CrewAI 的共同信号都指向同一结论：并行前必须先固定 task interface、persistence policy、termination/review lifecycle

## 权威输入

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/workspace-parallel-task-orchestration-direction-analysis.md`
- `design_docs/parallel-safe-subgraph-slice1-contract-draft.md`
- `design_docs/subagent-management-design.md`
- `design_docs/subagent-context-isolation-evaluation.md`
- `design_docs/subagent-tracing-writeback-direction-analysis.md`
- `docs/subagent-management.md`
- `docs/core-model.md`
- `docs/subagent-schemas.md`
- `src/collaboration/subgraph_mode.py`
- `src/pep/executor.py`
- `src/subagent/contract_factory.py`
- `review/langgraph-langchain.md`
- `review/autogen.md`
- `review/multica/02-direction-and-weaknesses.md`
- `review/crewai.md`

## 候选阶段名称

- `Parallel-Safe Subgraph Fan-Out / Fan-In`

## 本轮只做什么

- 固定 parent 可派生多个 child subgraph 的最小 contract 边界，但仍保持 `supervisor-managed` 模式
- 固定 child task identity、parent-child lineage 与最小 trace surface
- 固定 `per-invocation` child namespace policy，明确本轮禁止 `per-thread` persistent child 并行重入
- 固定 `allowed_artifacts` 的并行硬约束，要求 dispatch 前先做 disjoint write set 校验
- 固定 barrier merge 的最小语义：所有 child result 回齐后，按冲突分类进入 auto-merge、review、blocked 三路之一
- 固定 grouped review outcome 的最小结果面，避免并行 child 结果重新坍缩成单 report 假设
- 给出 3 个首批实现小切片的推荐顺序；当前已完成 Slice 1 foundation，后续是否继续推进 Slice 2 仍需单独收口

## 当前推荐的最小对象集合

当前默认不直接引入完整 `TaskGraph`。第一轮只固定以下 4 个最小 contract object：

| 对象 | 作用 | 当前推荐最小字段 |
|---|---|---|
| `TaskGroup` | 表达一个 parent delegation 派生出的并行 child 集合 | `task_group_id`、`parent_trace_id`、`mode=subgraph-fanout`、`children[]`、`join_policy`、`merge_policy` |
| `ParallelChildTask` | 表达单个 child subgraph 的输入边界 | `child_task_id`、`contract_ref|contract_payload`、`namespace`、`allowed_artifacts`、`required_refs`、`acceptance` |
| `ChildExecutionRecord` | 表达 child 的执行证据与 lineage | `child_task_id`、`status`、`trace_id`、`namespace`、`changed_artifacts`、`verification_results`、`unresolved_items` |
| `MergeBarrierOutcome` | 表达 parent 对所有 child 结果的 join/merge 判定 | `task_group_id`、`child_statuses`、`conflict_classification`、`review_outcome`、`merged_delta|blocked_reason` |

当前推荐遵循两条约束：

1. `TaskGroup` 是对“一个 parent 如何等待并汇合多个 child”的最小建模，不等于通用 DAG。
2. `ParallelChildTask` 仍沿用现有 `Subagent Contract` 边界，不在本轮把 child task 扩成第二套独立 contract 体系。

## 当前推荐的运行规则

### 1. Child persistence policy

- 默认只允许 `per-invocation` child namespace
- child 调用结束后，namespace 只保留本次执行所需的 trace / delta 证据，不累积跨调用共享记忆
- 当前显式禁止需要 `per-thread` memory 的 child 并行重入

### 2. Dispatch preflight

- parent 在 fan-out 前必须先校验全部 child 的 `allowed_artifacts`
- 若两个 child 的写集无法证明不相交，则不得直接并行 dispatch
- dispatch preflight 的失败应优先表现为 planning/runtime guard，而不是事后 merge 惊喜

### 3. Barrier merge policy

- parent 只有在 child 全部进入 terminal state（`completed` / `partial` / `blocked` / `cancelled`）后才进入 merge barrier
- merge barrier 不直接等于 write-back；它先产出 `MergeBarrierOutcome`
- `MergeBarrierOutcome` 再决定：自动合并、送 review、或整体阻塞

### 4. Review aggregation policy

- 不再把多个 child result 压扁成“一个 child report”
- grouped review 至少要能表达：
  - `all_clear`
  - `review_required`
  - `blocked`
- grouped review outcome 需要保留 child 粒度的 unresolved / assumptions / changed_artifacts 证据

## 当前推荐的冲突分类

| 冲突类 | 语义 | 默认处理 |
|---|---|---|
| `no_conflict` | child 写集不相交，或 merge 结果可直接拼接 | 自动合并 |
| `deterministic_merge` | 写同一高层对象但能按明确规则合并 | 自动合并，并留下 merge evidence |
| `review_required` | 无法安全自动合并，但冲突仍可由人审决定 | 进入 grouped review |
| `blocked` | 写集、namespace 或 parent-child 语义冲突已超出当前 slice | 阻塞并升级，不继续 write-back |

当前第一轮实现只应覆盖 `no_conflict` 与 `review_required` 为主线；`deterministic_merge` 只在规则极清楚时纳入；`blocked` 必须始终可达。

## 当前推荐的实施顺序

### Slice 1 — Contracts + Lineage + Dispatch Preflight

- 详细设计草案见：`design_docs/parallel-safe-subgraph-slice1-contract-draft.md`
- 为 `TaskGroup` / `ParallelChildTask` / `ChildExecutionRecord` 固定最小 schema 或等价数据结构
- 在 executor 路径上补 parent-child lineage 与 trace surface
- 加入 dispatch preflight，先做 child namespace 与 disjoint write set 校验

当前状态：foundation 已实现并通过针对性回归；真正的 multi-child fan-out dispatch 与 barrier merge 仍留在后续切片

### Slice 2 — Barrier Merge + Conflict Classification

- 定义 `MergeBarrierOutcome`
- 实现 child result 汇合与 `no_conflict` / `review_required` / `blocked` 分类
- 保持 write-back 仍在 parent 侧集中进行

当前状态：foundation 已实现并通过针对性回归；grouped review aggregation 与集中 write-back 汇合仍留在后续切片

### Slice 3 — Grouped Review + Audit / Write-Back Integration

- 把 grouped review outcome 接到现有 review state machine
- 把 merge barrier / grouped review 事件接入 audit trace
- 明确多 child write-back 与 handoff/escalation 的关系

当前状态：foundation 已实现并通过针对性回归；grouped review 结果已进入 executor result surface、review feedback 后的 write-back summary 与 audit trace，并可在 `all_clear` 下驱动 child payload write-back；独立 grouped review 状态迁移与真实 multi-child dispatch 仍留在后续收口

## 本轮明确不做什么

- 不实现完整 `TaskGraph` / `Scheduler` / `Agent Team` / `Swarm` runtime
- 不允许长期共享记忆 child 的并行重入
- 不把 orchestration layer / daemon bridge 一并实现
- 不扩到跨工作区分布式调度
- 不同时改 VS Code extension、Chat Participant、或 host UX 交互面
- 不在本轮重新设计 `Subagent Contract` / `Subagent Report` / `Handoff` 的全部 schema

## 验收与验证门

- 针对性测试：
  - `TaskGroup` / child contract 最小 schema 校验
  - dispatch preflight 对 disjoint write set / namespace policy 的校验测试
  - barrier merge 对 `no_conflict` / `review_required` / `blocked` 的分类测试
  - grouped review outcome 保留 child 粒度证据的测试
- 更广回归：
  - 现有 `supervisor-worker`、`handoff`、`subgraph` 单 child 路径行为不回归
  - 现有 write-back、audit、decision log 行为不被并行 contract 误伤
- 手测入口：
  - 两个 child 写不同文档，预期自动合并
  - 两个 child 写同一文档不同区块，预期进入 review_required
  - 一个 child 要求 `per-thread` 持久上下文，另一个 child 并行重入同子图，预期 blocked
- 文档同步：若本候选进入实现并完成至少 Slice 1，需要同步 authority docs、状态面与 checkpoint

当前状态：checkpoint、active planning-gate 与 authority docs 已同步到当前实现口径

## 需要同步的文档

- `docs/subagent-management.md`
- `docs/core-model.md`
- `docs/subagent-schemas.md`
- `design_docs/workspace-parallel-task-orchestration-direction-analysis.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/checkpoints/latest.md`
- `.codex/handoffs/CURRENT.md`（仅当本候选完成并回到 safe stop 时）

## 子 agent 切分草案

- 若需要只读盘点，可让 investigator 汇总当前 `subgraph_mode`、`Executor`、`contract_factory` 与相关测试面里最接近 fan-out/fan-in 的可复用点
- contract 命名、冲突分类、grouped review 语义与 planning-gate write-back 仍由主 agent 负责

## 收口判断

- 为什么这条切片可以单独成立：它先解决 parallel-safe contract，而不是一次性重写整个多 agent runtime
- 做到哪里就应该停：当最小对象集合、dispatch preflight、namespace policy、barrier merge、grouped review outcome 与 3 个实现小切片顺序都清楚后就应停，不继续扩到 full team/swarm runtime
- 下一条候选主线是什么：
  - 默认进入 Slice 1：`Contracts + Lineage + Dispatch Preflight`
  - 若在 Slice 1 中发现 parent orchestration 与 current executor 耦合过深，再回到候选 C，单独起 `orchestration bridge / daemon layer` 方向分析
  - 若用户要求更强协作模式，再另起 `first-class task-graph / team / swarm runtime` 的高阶设计文档
