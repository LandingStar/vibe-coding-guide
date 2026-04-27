# Direction Analysis — Orchestration Bridge / Daemon Layer Follow-up

## 1. 背景

`Group Internal Handoff / Escalation Terminal Bundle` gate 已完成。

当前 executor-local parallel runtime 已经拥有的闭环包括：

1. `TaskGroup` / `ParallelChildTask` / `ChildExecutionRecord` 的最小 companion surface
2. strict preflight + shared-review zone 例外
3. grouped review / grouped payload writeback / zone-approved writeback
4. group terminal bundle：显式 `escalation_recommendation` 与显式 child `Handoff` 都能收口为 `GroupTerminalOutcome`
5. terminal suppression 已在 result / writeback summary / audit detail 三层镜像

因此，下一个问题已经不再是“executor-local fan-out/fan-in 能否成立”，而是：

**当单个 parent-managed group 的治理闭环已经成立后，更高一层的多任务调度面应放在哪里。**

## 2. 现在为什么值得切到 bridge / daemon

来自 `design_docs/workspace-parallel-task-orchestration-direction-analysis.md` 的关键信号已经发生变化：

1. 此前并行的主要阻塞是缺少 parallel-safe governance contract；这条阻塞现在已经被 Route A 的多个 planning-gate 基本拆开。
2. 当前 executor 仍然是 parent-scoped、single group scoped 的治理内核；它并不天然等于更高层 scheduler。
3. `review/multica/02-direction-and-weaknesses.md` 显示，真正的多任务编排需求会很快把问题推向 daemon / dependency / lifecycle / restart 可靠性，而不只是继续堆 executor 内部分支。

因此，如果下一步还继续把更多 orchestration 语义堆进 executor，本项目会开始把两层职责混在一起：

1. **治理内核**：contract / gate / review / writeback / audit / terminal bundle
2. **调度层**：队列、依赖、重试、生命周期、跨 group 资源协调、恢复

## 3. 候选路线

### A. thin orchestration bridge over current governance kernel

- 做什么：把 bridge / daemon 定义为上层调度面，只负责 work-item lifecycle、group scheduling、dependency wake-up、restart/recovery；每个 child group 仍把当前 `Executor` 当作治理内核调用。
- 优点：
  1. 不重写现有 gate / review / writeback / audit 语义
  2. 让 daemon 只新增“调度职责”，避免和治理内核职责纠缠
  3. 最符合 Multica 暴露出的现实教训：daemon 可靠性本身就是独立问题
- 风险：
  1. 需要明确定义 bridge 与 executor 的边界，否则会出现双重状态机
  2. 需要回答 group terminal bundle 向 bridge 回传的 landing contract 是什么
- 判断：**推荐**。

### B. continue expanding executor into a higher-level orchestrator

- 做什么：继续在当前 `Executor` 内直接加入多 group 调度、dependency edges、queue/retry 语义。
- 优点：
  1. 复用现有入口，短期实现表面上更直接
  2. 不必新增 bridge abstraction
- 风险：
  1. executor 会同时承担治理与调度两类职责，边界更难收口
  2. 未来 daemon/recovery/restart 问题会直接污染治理内核
  3. 与 Route A 之前“先固定内核 contract，再讨论 scheduler”的顺序相反
- 判断：不推荐作为下一刀。

### C. jump directly to first-class daemon runtime

- 做什么：直接把 daemon / scheduler / dependency graph / terminal landing 做成更完整的一等 runtime。
- 优点：
  1. 从长期看更接近完整 orchestration 平台
  2. 可以一次性讨论 work queue / dependency graph / lifecycle
- 风险：
  1. scope 过大，会重新打开太多尚未收口的边界
  2. 当前还没有 bridge contract，直接做 full daemon 容易把恢复、terminal landing、治理状态都绑死
- 判断：长期成立，但不适合作为当前 follow-up。

## 4. 我当前推荐的最小下一步

我当前推荐：

1. 采用 **候选 A**，先做 `bridge / daemon contract-first` 方向或 planning-gate
2. 不直接实现 daemon，而是先固定 bridge 和治理内核之间的最小接口

推荐原因：

1. Route A 已经证明 executor-local 治理内核能承接 parallel child 的关键收口
2. 下一步真正未定义的是“谁来调度多个 group，以及 terminal bundle 往上如何交接”
3. 这正是 bridge / daemon 的职责，而不是继续塞进 executor

## 5. 推荐的下一条 planning-gate 问题

若沿候选 A 继续，下一条 planning-gate 应优先回答：

1. bridge / daemon 持有什么最小 work item / group item primitive
2. executor 返回的 `GroupTerminalOutcome`、grouped review state、writeback summary 如何向 bridge 回传
3. bridge 是否只管理调度与恢复，而不直接决定 gate / review 语义
4. terminal bundle 形成后，bridge 应如何停机、转交或等待 human takeover

## 6. 当前明确不做

本方向分析不建议在下一刀里直接进入：

1. full team/swarm runtime
2. 跨 daemon persistence 协议
3. 完整队列系统或外部服务部署
4. 把 bridge 生命周期直接塞进现有 executor

## 7. 结论

当前最合理的判断不是“bridge / daemon 还太早”，而是：

**现在终于到了可以讨论 bridge / daemon 的时候，但前提是把它收窄成对现有治理内核的上层 contract，而不是直接把 scheduler 做成新的核心。**