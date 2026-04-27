# Subagent Schemas

## 文档定位

本文件定义平台中与子 agent 直接相关的 3 个最小 schema：

- `Subagent Contract`
- `Subagent Report`
- `Handoff`

本文件的重点是把这三个对象分清，不让它们在语义上互相吞并。

当前只定义对象、字段和不变量，不绑定最终文件格式。

## 为什么要拆成 3 个对象

这三个对象解决的是不同问题：

- `Subagent Contract`
  - 输入边界
- `Subagent Report`
  - 输出证据
- `Handoff`
  - 控制权转移

如果把它们合并成一个大对象，会混淆：

- 执行委派
- 结果汇报
- authority 转移

因此当前平台明确采用三分法。

## Parallel-Safe Subgraph Companion Objects

为了承接 `subgraph` 的并行安全收口，当前实现允许在 parent orchestration 侧额外出现一组 companion objects：

- `TaskGroup`
- `ParallelChildTask`
- `ChildExecutionRecord`
- `MergeBarrierOutcome`
- `GroupedReviewOutcome`

它们的作用分别是：

- `TaskGroup`
  - 表达一个 parent delegation 派生出的 child 集合
- `ParallelChildTask`
  - 包装单个 child 的 `Subagent Contract`、lineage 与 namespace boundary
- `ChildExecutionRecord`
  - 包装单个 child 的 `Subagent Report` 与执行证据
- `MergeBarrierOutcome`
  - 包装 parent 在 merge barrier 上对多 child 结果的冲突分类与下一步 review 倾向
- `GroupedReviewOutcome`
  - 包装 child 粒度证据在 grouped review / write-back 流程中的聚合视图

这里的关键边界是：

- 这 3 个对象当前只是 companion objects，不是替代 `Subagent Contract` / `Subagent Report` / `Handoff` 的新 schema
- `TaskGroup` 不替代 `Delegation Decision`
- `ParallelChildTask` 不替代 `Subagent Contract`
- `ChildExecutionRecord` 不替代 `Subagent Report`
- `MergeBarrierOutcome` 不替代 grouped review result 或最终 writeback result
- `GroupedReviewOutcome` 不替代现有 `ReviewStateMachine`，也不直接等于最终 writeback result
- `Handoff` 仍只表达 authority transfer，而不是 child orchestration

当前实现态还固定了两条并行安全 guard：

- child lineage 由 parent-issued `task_group_id` / `child_task_id` / `namespace` 表达
- dispatch preflight 会校验 namespace、unsafe path、`per-thread` persistence 与 disjoint write set overlap；当前还会返回 machine-readable `overlap_decisions`，用于区分普通 blocked overlap 与 shared-review-zone-driven allowed overlap
- merge barrier classification 当前只覆盖 `no_conflict` / `review_required` / `blocked`
- grouped review outcome 当前作为现有 review / write-back 流程的 companion surface，并通过 `grouped_review_state` 镜像接入现有 `ReviewStateMachine`，但不引入第二套 grouped review 状态机；当前已可通过 `review_driver` 与 `shared_review_zone_ids` 区分普通 conflict-driven review 与 shared-review-zone-driven review。对应 grouped child payload writeback 也新增最小 eligibility surface：`grouped_child_writeback_summary.eligibility_basis` 可区分 `all_clear` 自动写回与 `shared-review-zone-approved` 审批后写回。

当前 authority 还允许一条更具体的实现态口径：executor 可以在一个 `TaskGroup` 中真实消费多个 child contracts，并产出多个 `child_execution_records`；`all_clear` 下的 grouped child payload write-back 也已可消费真实 multi-child result。当前第一版 real multi-child 权威边界固定为 strict preflight 下的 `all_clear-only` 自动写回，即默认不承诺 conflict-bearing `review_required` 是真实 batch runtime 的常见自动写回路径。作为下一条显式例外路径，`ParallelChildTask` 现已支持可选 `shared_review_zone_id`；在同 zone 且 same-artifact 的前提下，preflight 可放行 overlap 并留下 zone-driven decision evidence，同时 merge/grouped review 与 grouped review writeback summary 都能保留这一 driver。进一步地，当 reviewer 对该 zone-driven `review_required` 给出 `approve` 时，grouped child payload writeback 现在可以通过 `shared-review-zone-approved` eligibility 继续进入 planning，但这不改变原始 grouped review outcome 仍是 `review_required` 的事实。对于 group 内 authority transfer 语义，当前还新增了一个更窄的 companion/result 起点：`GroupTerminalOutcome`。它现在已经同时承载显式 `escalation_recommendation` 与显式 child `Handoff` 证据下的 group terminal bundle，并通过 `suppressed_surfaces` 把被暂停的 `merge_barrier` / `grouped_review` / `grouped_child_writeback` 结果面显式化；在 writeback summary 与 `group_terminal_prepared` audit detail 中，这层 suppression 也已被统一镜像。为避免 invalid handoff 混入普通 success，subgraph child 路径现在会用 `handoff_validator` 校验 nested handoff evidence；失败时会降级为 blocked child result。

但这仍不等于完整 fan-out runtime：当前尚未把 thread-level fan-out scheduler、group 内 handoff / escalation terminal semantics、或独立 grouped review 状态迁移固定进权威 schema。

## 1. Subagent Contract

### 文档定位

`Subagent Contract` 是对子 agent 的输入约束。

它回答：

- 要做什么
- 能碰什么
- 必须读什么
- 什么算完成
- 什么明确不做
- 最后要按什么结构回报

### 最小字段

- `contract_id`
  - 当前合同的唯一标识
- `task`
  - 任务陈述
- `mode`
  - 当前建议默认值为 `worker`
- `scope`
  - 当前委派边界
- `allowed_artifacts`
  - 允许修改或读取的 artifact
- `required_refs`
  - 必须重读的 refs
- `acceptance`
  - 验收标准
- `verification`
  - 需要执行的验证
- `out_of_scope`
  - 明确不做的内容
- `report_schema`
  - 子 agent 回报所应遵循的结构

### 不变量

- 合同必须明确边界，不能只写宽泛目标。
- 若没有 `allowed_artifacts`，默认不允许写权威文档。
- 若没有 `out_of_scope`，默认说明不充分。
- 合同默认不转移 authority，只转移工作切片。

### JSON Schema

机器可验证的 schema 定义见 [`docs/specs/subagent-contract.schema.json`](specs/subagent-contract.schema.json)。

## 2. Subagent Report

### 文档定位

`Subagent Report` 是子 agent 的结构化输出。

它回答：

- 实际做了什么
- 改了什么
- 若后续需要 writeback，可提供什么结构化内容载荷
- 跑了哪些验证
- 哪些问题还没解决
- 是否建议升级

### 最小字段

- `report_id`
  - 当前报告的唯一标识
- `contract_id`
  - 对应的合同标识
- `status`
  - 例如：
    - `completed`
    - `partial`
    - `blocked`
- `changed_artifacts`
  - 实际改动的 artifact
- `artifact_payloads`
  - 可选的结构化内容载荷，供后续 writeback plan 映射消费
- `verification_results`
  - 运行过的验证及结果
- `unresolved_items`
  - 未解决问题
- `assumptions`
  - 执行中做出的假设
- `escalation_recommendation`
  - 是否建议升级，以及为什么

### 不变量

- 报告必须能回溯到某个合同。
- 报告应优先提供证据，不应只是自由总结。
- 若 `status=completed`，不代表系统已经完成，只代表子 agent 任务已收口。
- `changed_artifacts` 与 `verification_results` 不应为空泛描述。
- `changed_artifacts` 仍是执行后证据列表；`artifact_payloads` 不替代执行证据。
- `artifact_payloads` 若存在，只表达“供后续 writeback 消费的结构化内容候选”，不等于“真实文件已被成功写回”。

### `artifact_payloads` 第一版边界

若 `artifact_payloads` 出现，第一版每项固定包含：

- `path`
- `content`
- `operation`
- `content_type`

其中：

- `operation` 只允许：`create` / `update` / `append`
- `content_type` 只允许：`markdown` / `json` / `yaml` / `text`

当前不把 directive 级更新（如 `section_replace` / `line_insert`）直接塞进 `Subagent Report`。这层 schema 只负责提供后续 writeback 可消费的结构化候选内容，不负责声明真实文件已经被更新。

### JSON Schema

机器可验证的 schema 定义见 [`docs/specs/subagent-report.schema.json`](specs/subagent-report.schema.json)。

## 3. Handoff

### 文档定位

`Handoff` 用于表达控制权的显式转移。

它不是“再派一个活”，而是“从一个 authority 角色转交给另一个 authority 角色”。

### 最小字段

- `handoff_id`
  - 当前 handoff 的唯一标识
- `from_role`
  - 当前交出控制权的一方
- `to_role`
  - 当前接收控制权的一方
- `reason`
  - 为什么需要 handoff
- `active_scope`
  - 当前正在承接的范围
- `authoritative_refs`
  - 接手前必须重读的正式文档
- `carried_constraints`
  - 必须带过去的约束条件
- `open_items`
  - 尚未解决但随 handoff 转移的内容
- `current_gate_state`
  - 当前 review / approve 语境
- `intake_requirements`
  - 接手前的最小核验动作

### 不变量

- handoff 默认意味着 authority 转移，不只是执行分工。
- handoff 不应替代正式文档本身。
- 若没有 `authoritative_refs` 与 `intake_requirements`，handoff 不完整。
- handoff 应带着当前 gate 状态一起转移，而不是把审批语境丢失。

### JSON Schema

机器可验证的 schema 定义见 [`docs/specs/handoff.schema.json`](specs/handoff.schema.json)。

## Contract 与 Handoff 的边界

当前平台明确区分：

- `Subagent Contract`
  - 工作切片输入
- `Handoff`
  - 控制权转移输入

即使二者都可能带 refs 和边界，它们也不应合并成同一 schema。

## Report 与 Handoff 的边界

`Subagent Report` 是执行结果。  
`Handoff` 是控制权转移。

一个结果可以引发 handoff，但 report 本身不等于 handoff。

## 与平台对象的关系

### 与 `Delegation Decision`

- PDP 决定是否产生 `Subagent Contract`
- 并决定是否允许进入 `Handoff`

### 与 `Policy Enforcement Point`

- PEP 负责把合同交给子 agent
- PEP 负责收集报告
- PEP 负责在规则允许时落地 handoff

### 与 `Review State Machine`

- 合同的结果可能进入 review
- handoff 本身也可能受 gate 约束

## 当前边界

本文件已经固定：

- 为什么要三分
- 每个对象的最小字段
- 每个对象的基本不变量

本文件尚未固定：

- 是否需要 `Worker Task` 与 `Subgraph Task` 进一步拆分
- 是否需要为 `Handoff` 补专门的 tracing 字段
- companion objects 是否需要在未来升级为正式可序列化 schema

## 开放问题

- `Handoff` 是否需要显式记录 `supersedes`
- `Subagent Report` 是否需要进一步升级为 directive 级 writeback payload
- `MergeBarrierOutcome` 是否应在后续切片进入正式 schema，还是继续保持 parent-side companion object
- `GroupedReviewOutcome` 是否应在后续切片进入正式 schema，还是继续保持 parent-side companion object
