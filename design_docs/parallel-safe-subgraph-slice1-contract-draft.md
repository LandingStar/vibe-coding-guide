# 设计草案 — Parallel-Safe Subgraph Slice 1 Contracts And Lineage

## 文档定位

本文是 [design_docs/stages/planning-gate/2026-04-24-parallel-safe-subgraph-fanout-fanin.md](design_docs/stages/planning-gate/2026-04-24-parallel-safe-subgraph-fanout-fanin.md) 的 Slice 1 设计草案。

当前只回答三件事：

1. `TaskGroup` / `ParallelChildTask` / `ChildExecutionRecord` 应该与现有 `Subagent Contract` / `Subagent Report` / `Handoff` 如何分层
2. parent-child lineage 与 namespace 应该如何最小落地
3. dispatch preflight 应该在进入 fan-out 前做哪些硬校验

本文**不进入 merge barrier、grouped review 实现，也不进入代码修改**。

## 现有对象边界不能被打破

当前平台已经固定了三个最小 schema：

- `Subagent Contract`
- `Subagent Report`
- `Handoff`

因此 Slice 1 不应把并行 orchestration 误建模成“再发明一套更大的 contract/report/handoff”。

当前推荐边界是：

1. `TaskGroup` 是 parent orchestration object，不替代 `Subagent Contract`
2. `ParallelChildTask` 是 child dispatch descriptor，内部仍引用一个现有 `Subagent Contract`
3. `ChildExecutionRecord` 是 child runtime execution envelope，不替代 `Subagent Report`
4. `Handoff` 仍只表达 authority transfer，不参与 fan-out 常态路径

换句话说：并行只是把“多个 contract 如何被 parent 协调”显式化，而不是把既有三分法推倒重来。

## 当前推荐对象模型

### 1. TaskGroup

`TaskGroup` 表达一次 parent fan-out / fan-in 的最小 orchestration 单元。

当前推荐最小字段：

- `task_group_id`
- `parent_envelope_id`
- `parent_trace_id`
- `mode`
- `children`
- `join_policy`
- `merge_policy`
- `created_at`

当前推荐约束：

- `mode` 第一轮固定为 `subgraph-fanout`
- `children` 只接受 `ParallelChildTask[]`
- `join_policy` 第一轮固定为 `wait-all`
- `merge_policy` 第一轮只声明 `no_conflict` / `review_required` / `blocked` 三类结果

### 2. ParallelChildTask

`ParallelChildTask` 是“一个 child 如何被纳入 TaskGroup”的最小描述对象。

当前推荐最小字段：

- `child_task_id`
- `contract`
- `namespace`
- `allowed_artifacts`
- `required_refs`
- `priority`

当前推荐约束：

- `contract` 直接使用既有 `Subagent Contract` dict，不单独再造 child contract schema
- `allowed_artifacts` 必须与 `contract.allowed_artifacts` 一致；若不一致，以 child descriptor 显式值为准，但必须通过 preflight 校验
- `priority` 第一轮只作为保留字段，不驱动真实 scheduler

### 3. ChildExecutionRecord

`ChildExecutionRecord` 是 child 执行后的最小运行时证据对象。

当前推荐最小字段：

- `child_task_id`
- `task_group_id`
- `trace_id`
- `namespace`
- `status`
- `report`
- `started_at`
- `finished_at`

当前推荐约束：

- `report` 直接保存既有 `Subagent Report`
- `status` 先与 `report.status` 同步，不新增第二套状态机
- `namespace` 必须与调度前分配值一致，不能由 worker 反向决定

## 当前推荐的命名与 lineage 规则

### TaskGroup ID

当前推荐由 parent 统一生成：

- `tg-<uuid12>`

理由：

- 不把 group identity 绑定到任何单个 child contract
- 与现有 `contract-<uuid>`、`sg-<uuid>` 风格一致

### Child Task ID

当前推荐由 parent 在 group 内顺序生成：

- `child-01`
- `child-02`
- `child-03`

理由：

- group 内唯一即可，不需要全局唯一语义
- 审计与 review 展示比长 UUID 更可读

### Namespace

当前推荐不用 `contract_id` 直接充当 namespace，而是改为：

- `<task_group_id>/<child_task_id>`

例如：

- `tg-a1b2c3d4e5f6/child-01`

理由：

1. 现有 `subgraph_mode.create_context()` 把 `contract_id` 当 namespace，只适合单 child 场景
2. fan-out 后 namespace 需要同时表达 group 归属与 child 身份
3. 这样可以显式保留 parent-child lineage，而不是把 lineage 分散到 trace 推理里

## Dispatch Preflight 当前推荐规则

### 1. Allowed Artifacts Normalization

进入并行前，parent 先把每个 child 的 `allowed_artifacts` 归一化为路径集合：

- 相对路径统一转 project-root 相对语义
- 目录写权限视为“该目录下所有候选文件”的上界
- 文件路径与其父目录路径若同时出现在不同 child 中，视为潜在冲突

第一轮不做更聪明的目录树静态分析，只做保守判定：

- 明确不相交：允许并行
- 任何祖先/后代重叠：进入 `review_required` 或直接拒绝 dispatch

### 2. Namespace Policy Check

第一轮 preflight 必须拒绝以下情形：

- 同一个 `child_task_id` 被重复分配
- namespace 不是 `<task_group_id>/<child_task_id>` 形式
- child 试图声明需要 `per-thread` persistent memory
- 同一 group 内两个 child 复用同一个 namespace

### 3. Contract Consistency Check

第一轮 preflight 必须检查：

- 每个 child 都有合法 `Subagent Contract`
- `contract.mode` 必须为 `subgraph`
- `allowed_artifacts`、`required_refs`、`acceptance` 不能为空泛占位
- child 不得借 fan-out 绕过现有 authoritative docs 写入限制

## 当前推荐的代码触点

第一轮实现最可能涉及以下文件：

- `src/pep/executor.py`
  - 新增 parent fan-out dispatch preflight
  - 生成 `TaskGroup` 与 `ChildExecutionRecord`
- `src/collaboration/subgraph_mode.py`
  - `SubgraphContext` 增加 `task_group_id` / `child_task_id`
  - namespace 生成从 `contract_id` 迁移为 parent-issued value
- `src/subagent/contract_factory.py`
  - 增加从 parent hints 派生多个 child contract 的 helper，或保持由上层先生成 contract 列表后直接传入
- `src/interfaces.py`
  - 若需要 machine-checked 结构，可把 `TaskGroup` / `ChildExecutionRecord` 提升为 dataclass / TypedDict / Protocol 边界

当前不推荐第一轮就改：

- `docs/specs/subagent-contract.schema.json`
- `docs/specs/subagent-report.schema.json`
- `src/collaboration/handoff_mode.py`

因为 Slice 1 的目标是新增 orchestration companion objects，不是重写现有三大 schema。

## 当前推荐的不变量

第一轮至少应固定以下不变量：

1. 一个 `TaskGroup` 只能描述一个 parent 的一次 fan-out
2. 一个 `ParallelChildTask` 必须指向一个合法 `Subagent Contract`
3. 一个 `ChildExecutionRecord` 必须能追溯到 `task_group_id + child_task_id + report.contract_id`
4. namespace 必须由 parent 分配，不由 child runtime 自行决定
5. dispatch preflight 未通过时，不得产生任何 child execution side effect

## 当前刻意保留到后续 Slice 的问题

- `MergeBarrierOutcome` 的最终字段命名
- grouped review 如何映射到现有 `ReviewStateMachine`
- deterministic merge 是否在第一版纳入
- 多 child write-back 是否允许部分 apply

这些问题都重要，但不应反向阻塞 Slice 1 的 contract 与 preflight 设计。

## 当前建议

如果继续沿 A 推进，最稳妥的顺序是：

1. 先按本文把 `TaskGroup` / `ParallelChildTask` / `ChildExecutionRecord` 固定成 companion objects
2. 再在 `Executor + subgraph_mode` 上接入 dispatch preflight 与 lineage
3. 等 parent-child surface 稳定后，再进入 `MergeBarrierOutcome` 与 grouped review

当前不建议一上来把 `TaskGroup` 扩成通用 DAG，也不建议先改 `Subagent Contract` schema 去承载全部 group 语义。