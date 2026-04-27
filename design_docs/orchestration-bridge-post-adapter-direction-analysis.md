# Orchestration Bridge Post-Adapter Direction Analysis

## 背景

`design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-executor-result-adapter.md` 已完成：

1. executor-result adapter contract 已固定
2. adapter helper 已落地到 `src/runtime/orchestration/executor_adapter.py`
3. `tests/test_runtime_bridge.py` + `tests/test_runtime_orchestration.py` + `tests/test_runtime_orchestration_adapter.py` 联合回归已通过（25 passed）

因此当前主线已经不再是“executor result 怎么进 bridge helper”，而是“这些 helper 之上，下一层最值得先落哪块 glue”。

## 候选 A. orchestration coordinator glue over current helpers

- 做什么：新增一个最小 coordinator/glue 层，把 `project_execution_result_to_group_item()`、`roll_up_work_item()` 与 `evaluate_stop_condition()` 串成一个 work-item 驱动闭环，但仍不进入 daemon/persistence
- 依据：
  - [src/runtime/orchestration/executor_adapter.py](src/runtime/orchestration/executor_adapter.py)
  - [src/runtime/orchestration/rollup.py](src/runtime/orchestration/rollup.py)
  - [src/runtime/orchestration/stop_conditions.py](src/runtime/orchestration/stop_conditions.py)
- 风险：中。
- 当前判断：**推荐**。因为当前 helper 已经各自成立，最值得新增的信息是“这些 helper 串起来后，work-item 驱动闭环能否最小成立”。

## 候选 B. external-resolution landing integration

- 做什么：围绕 `waiting_external_resolution` 直接接入 handoff / reviewer takeover / landing artifact
- 依据：
  - [src/runtime/orchestration/stop_conditions.py](src/runtime/orchestration/stop_conditions.py)
  - [docs/specs/handoff.schema.json](docs/specs/handoff.schema.json)
- 风险：中。
- 当前判断：值得保留，但默认优先级低于候选 A，因为还没有 coordinator glue 就直接接 landing，会让输入闭环不完整。

## 候选 C. daemon queue / persistence runtime

- 做什么：继续往 daemon service、queue persistence、recovery runtime 推进
- 依据：
  - [design_docs/orchestration-bridge-daemon-layer-direction-analysis.md](design_docs/orchestration-bridge-daemon-layer-direction-analysis.md)
  - [review/multica/02-direction-and-weaknesses.md](review/multica/02-direction-and-weaknesses.md)
- 风险：高。
- 当前判断：长期成立，但当前时机仍偏早。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. models、helpers、adapter 都已经落地并过窄回归
2. 当前最关键的不确定性已经不是单个 helper，而是这些 helper 串成 work-item 驱动闭环后是否还保持稳定
3. 先做 coordinator glue 的信息增益，明显高于直接接 landing 或 persistence