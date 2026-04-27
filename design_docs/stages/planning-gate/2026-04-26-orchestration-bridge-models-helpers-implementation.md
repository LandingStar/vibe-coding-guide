# Planning Gate — Orchestration Bridge Models / Helpers Implementation

> 日期: 2026-04-26
> 状态: COMPLETE
> 关联方向分析: `design_docs/orchestration-bridge-runtime-implementation-followup-direction-analysis.md`

## 1. Why this gate exists

`design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-runtime-primitives.md` 已完成 docs-only 收口。

这意味着当前关于 orchestration bridge runtime primitive 的最小 contract 已经明确：

1. 模块边界已经固定到 `src/runtime/orchestration/`
2. runtime model 与 pure helper surface 已写清
3. targeted tests boundary 已明确与现有 `RuntimeBridge` 测试隔离

因此当前最窄的下一条 gate 不再是继续写文档，而是先把这些 contract 落成最小代码实现。

## 2. Scope

本 gate 只处理：

1. `src/runtime/orchestration/models.py` 的 runtime models
2. `src/runtime/orchestration/projection.py`、`rollup.py`、`stop_conditions.py` 的 pure helper 实现
3. `tests/test_runtime_orchestration.py` 的 targeted tests

本 gate 不处理：

1. landing integration
2. queue / persistence / replay runtime
3. `RuntimeBridge` 宿主入口职责变更

## 3. Working hypothesis

当前最小可行路线应是：

1. 先用 pure dataclass model + pure helper 实现 contract
2. 先让 targeted tests 在不触碰现有 governance kernel schema 的前提下成立
3. 在 helper 层稳定后，再讨论 landing integration 与 daemon skeleton

## 4. Slices

### Slice 1 — Models implementation

- 新增 `BridgeWorkItem` / `BridgeGroupItem`
- 新增共享类型别名
- 保持 optional dispatch-lineage 字段与 tuple-based stable collections

当前状态：Slice 1 设计草案已创建为 `design_docs/orchestration-bridge-models-implementation-slice1-draft.md`；当前推荐先只落 `models.py`，并用最小测试验证默认值与 optional 字段语义。

### Slice 2 — Projection / roll-up / stop helper implementation

- 实现 `project_group_item_surface()`
- 实现 `roll_up_work_item()`
- 实现 `evaluate_stop_condition()`

当前状态：未开始；依赖 Slice 1 先固定 models。

### Slice 3 — Targeted tests completion

- 新增 `tests/test_runtime_orchestration.py`
- 覆盖 model defaults、projection、roll-up precedence、stop evaluator、inconsistency guards

当前状态：未开始；依赖 Slice 2 先落 helper 实现。

## 5. Validation gate

- 代码验证：
  - `tests/test_runtime_orchestration.py` 能独立验证新 helper 层
  - 现有 `tests/test_runtime_bridge.py` 不需要改名或重写语义
  - 新 helper 层不要求修改现有 governance kernel schema

## 6. Stop condition

- 当 models、pure helpers 与 targeted tests 都已落地并通过窄验证后停止
- 不在本 gate 内继续进入 landing integration / daemon runtime

## 7. Close note

当前 gate 已按实现边界完成：`src/runtime/orchestration/` 中的 models 与 pure helpers 已落地，`tests/test_runtime_bridge.py` + `tests/test_runtime_orchestration.py` 联合回归已通过。下一步不再继续扩写本 gate，而是转入 executor-result adapter follow-up。