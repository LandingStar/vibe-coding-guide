# Planning Gate — Orchestration Bridge Executor Result Adapter

> 日期: 2026-04-26
> 状态: COMPLETE
> 关联方向分析: `design_docs/orchestration-bridge-executor-result-integration-direction-analysis.md`

## 1. Why this gate exists

`design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-models-helpers-implementation.md` 已完成。

这意味着当前已经存在：

1. bridge runtime models
2. group-item projection / work-item roll-up / stop-condition helper
3. 独立的 targeted tests

因此当前最明显的空洞不再是 helper 自身，而是：

- executor 的 execution result 如何被稳定地适配为 bridge helper 的输入

## 2. Scope

本 gate 只处理：

1. 从 `Executor.execute()` 的 execution result 到 `BridgeGroupItem` / `BridgeWorkItem` 输入的 adapter contract
2. adapter helper 的最小实现与 targeted tests
3. serialized dict surface 与 runtime models 的耦合边界

本 gate 不处理：

1. landing integration
2. daemon queue / persistence / replay runtime
3. executor 内部重构

## 3. Working hypothesis

当前最小可行路线应是：

1. adapter 先消费 executor 已对外暴露的 dict execution result
2. adapter 先只负责 result normalization，不修改 executor 主执行流程
3. helper 稳定后，再讨论是否需要更深的 runtime orchestration glue

## 4. Slices

### Slice 1 — Serialized execution-result adapter contract

- 固定 adapter 输入面：`grouped_review_outcome` / `group_terminal_outcome` / `grouped_review_state`
- 固定 adapter 输出给 `project_group_item_surface()` 的 normalized fields
- 明确为什么当前不直接绑定 dataclass object surface

当前状态：Slice 1 设计草案已创建为 `design_docs/orchestration-bridge-executor-result-adapter-slice1-draft.md`；当前推荐先把 serialized dict surface 写成唯一输入面，再进入代码实现。

### Slice 2 — Adapter helper implementation

- 新增 executor-result adapter helper
- 接 `project_group_item_surface()` / `roll_up_work_item()`
- 固定最小异常/空值处理

当前状态：未开始；依赖 Slice 1 先固定 contract。

### Slice 3 — Targeted tests completion

- 新增 adapter targeted tests
- 覆盖 grouped_review、group_terminal、blocked、empty result 四类输入

当前状态：未开始；依赖 Slice 2 先落 helper。

## 5. Validation gate

- 代码验证：
  - adapter 能消费 executor result dict surface 而不改 executor 主流程
  - adapter tests 能和 `tests/test_runtime_orchestration.py` 一起通过

## 6. Stop condition

- 当 adapter contract、helper 实现与 targeted tests 都已落地并通过窄验证后停止
- 不在本 gate 内进入 landing integration / daemon runtime

## 7. Close note

当前 gate 已按边界完成：serialized execution-result contract、adapter helper 与 targeted tests 均已落地，并与现有 runtime bridge 联合回归通过。下一步不再继续扩写本 gate，而是转入 `design_docs/orchestration-bridge-post-adapter-direction-analysis.md` 讨论后续主线。