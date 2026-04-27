# Planning Gate — Orchestration Bridge Coordinator Glue

> 日期: 2026-04-26
> 状态: COMPLETE
> 关联方向分析: `design_docs/orchestration-bridge-post-adapter-direction-analysis.md`

## 1. Why this gate exists

`design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-executor-result-adapter.md` 已完成。

当前已经存在：

1. bridge runtime models
2. group-item projection / work-item roll-up / stop-condition helper
3. executor-result adapter helper

因此当前主线已经不再是单个 helper 的成立性，而是：

- 能否把这些 helper 串成一个最小 work-item 驱动闭环

## 2. Scope

本 gate 只处理：

1. 单步 coordinator/glue contract
2. 最小 coordinator helper 实现
3. coordinator targeted tests

本 gate 不处理：

1. landing integration
2. daemon queue / persistence / replay runtime
3. executor / worker 主流程改写

## 3. Working hypothesis

当前最小可行路线应是：

1. 一次只处理一个 group item 的 execution result
2. coordinator 只做三步：更新 group item、roll-up work item、判断 stop condition
3. 若这条 pure glue 成立，再决定是否需要更厚的 stateful orchestration runtime

## 4. Slices

### Slice 1 — Coordinator step contract

- 固定单步输入：`BridgeWorkItem`、`group_items`、`group_item_id`、`execution_result`
- 固定单步输出：updated group item、updated group-item tuple、updated work item、stop decision
- 明确为什么当前先不进入 daemon/persistence

当前状态：Slice 1 设计草案已创建为 `design_docs/orchestration-bridge-coordinator-glue-slice1-draft.md`。

### Slice 2 — Coordinator helper implementation

- 新增最小 coordinator helper
- 组合 executor adapter、roll-up、stop evaluator
- 固定最小校验与错误行为

当前状态：进行中。

### Slice 3 — Targeted tests completion

- 新增 coordinator targeted tests
- 覆盖 completed / wait_external_resolution / blocked / invalid target 四类输入

当前状态：进行中。

## 5. Validation gate

- coordinator tests 通过
- coordinator tests 与 `tests/test_runtime_orchestration.py`、`tests/test_runtime_orchestration_adapter.py` 联合通过

## 6. Stop condition

- 当 single-step coordinator contract、helper 与 targeted tests 都已落地并通过窄验证后停止
- 不在本 gate 内进入 landing integration / daemon runtime

## 7. Close note

当前 gate 已按边界完成：single-step coordinator contract、helper 与 targeted tests 已落地，并与现有 runtime bridge/orchestration 测试联合通过。下一步转入 `design_docs/orchestration-bridge-landing-integration-direction-analysis.md` 处理 external-resolution landing surface。