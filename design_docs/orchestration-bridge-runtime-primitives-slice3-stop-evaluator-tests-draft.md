# 设计草案 — Orchestration Bridge Runtime Primitives Slice 3 Stop Evaluator / Tests Boundary

本文是 `design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-runtime-primitives.md` 的 Slice 3 设计草案，直接消费 Slice 2 已固定的 `BridgeWorkItem` runtime model 与 `roll_up_work_item()` 输出。

## 目标

当前目标不是实现 daemon runtime，而是把 `stop_conditions.py` 的 evaluator contract 与 targeted tests boundary 固定下来：

1. `evaluate_stop_condition()` 应返回什么最小结果对象
2. 哪些 `BridgeWorkItem` 组合必须映射为 `continue_waiting`、`wait_external_resolution`、`completed`、`blocked`、`inconsistent`
3. targeted tests 应该落在哪个测试面，而不是误混到现有 `tests/test_runtime_bridge.py`

## 当前输入证据面

当前已有足够输入：

1. `BridgeWorkItem` 已具备 `rollup_surface_kind` / `rollup_surface_state` / `rollup_blocked_reason` / `rollup_writeback_disposition` / `open_group_item_count`
2. 上一条 docs-only gate 已固定 boundary matrix
3. `tests/test_runtime_bridge.py` 当前只覆盖 host-entry `RuntimeBridge`

因此，当前最小 runtime evaluator 不需要再读原始 governance object，只需消费 `BridgeWorkItem`。

## `stop_conditions.py` Contract

当前推荐新增一个最小结果对象：

- `StopConditionDecision`

推荐字段：

| 字段 | 类型 | 说明 |
|---|---|---|
| `boundary_kind` | `Literal["continue_waiting", "wait_external_resolution", "completed", "blocked", "inconsistent"]` | 当前 stop 判断类别 |
| `next_lifecycle_state` | `BridgeWorkLifecycle` | evaluator 建议写回的下一个 lifecycle state |
| `reason` | `str` | 最后可见原因；仅镜像 evaluator 判断 |

当前推荐只暴露一个 pure helper：

```python
def evaluate_stop_condition(work_item: BridgeWorkItem) -> StopConditionDecision: ...
```

语义边界：

1. helper 只消费 `BridgeWorkItem`
2. helper 返回新的判断对象，不直接 in-place mutate work item
3. helper 不负责 resume / retry / replay

## Evaluator Boundary Matrix

当前推荐按以下顺序判断：

| 条件 | `boundary_kind` | `next_lifecycle_state` | `reason` 来源 |
|---|---|---|---|
| `rollup_surface_kind=blocked` | `blocked` | `blocked` | `rollup_blocked_reason` |
| `rollup_surface_kind=group_terminal` | `wait_external_resolution` | `waiting_external_resolution` | `rollup_blocked_reason` 或 `rollup_surface_state` |
| `rollup_surface_kind=grouped_review` 且 `rollup_surface_state=review_required` | `wait_external_resolution` | `waiting_external_resolution` | `review_required` |
| `open_group_item_count > 0` | `continue_waiting` | 保持当前 `lifecycle_state` 或 `waiting_governance_result` | 空字符串 |
| `open_group_item_count = 0` 且 `rollup_writeback_disposition` 属于 `eligible` 或 `none`，且 `rollup_surface_kind` 不属于 `blocked` / `group_terminal` | `completed` | `completed` | 空字符串 |
| 其他组合 | `inconsistent` | 保持当前 `lifecycle_state` | `inconsistent_rollup_state` |

## Guard Rules

当前建议 evaluator 额外显式守护以下组合：

1. `open_group_item_count = 0` 但 `rollup_writeback_disposition = pending` → `inconsistent`
2. `rollup_surface_kind = blocked` 且 `rollup_blocked_reason = ""` → 允许，但 `reason` 仍返回 `blocked` 作为兜底文本
3. `rollup_surface_kind = group_terminal` 且 `rollup_surface_state` 不在 `escalation` / `handoff` → `inconsistent`
4. `rollup_surface_kind = none` 且 `dominant_group_item_ids` 非空 → `inconsistent`

## Targeted Tests Boundary

当前推荐新增独立测试文件：

- `tests/test_runtime_orchestration.py`

而不是把 orchestration helper 测试混进：

- `tests/test_runtime_bridge.py`

理由是：

1. `test_runtime_bridge.py` 当前只覆盖 host-entry `RuntimeBridge`
2. orchestration helper 属于另一个模块面
3. 混在一起会重新模糊两类 bridge 的语义边界

当前推荐的最小测试分组：

1. `TestBridgeModels`
2. `TestProjectionHelper`
3. `TestRollupHelper`
4. `TestStopConditionEvaluator`

## Minimum Test Matrix

当前建议至少覆盖以下用例：

| 测试主题 | 最小用例 |
|---|---|
| model defaults | `BridgeGroupItem` 的 optional dispatch-lineage 字段在 `prepared` 时允许为空 |
| projection | `project_group_item_surface()` 会返回新对象并把 `lifecycle_state` 收口到 `settled` |
| roll-up precedence | blocked > group_terminal > review_required > all_clear 的优先级成立 |
| roll-up openness | 只要有未 settled group-item，`open_group_item_count` 就保持大于 0 且 writeback 不升级为 `eligible` |
| stop evaluator | `group_terminal` 与 `review_required` 都统一映射到 `waiting_external_resolution` |
| inconsistency guard | `open_group_item_count = 0` 且 `rollup_writeback_disposition = pending` 返回 `inconsistent` |

## 当前不做的设计

当前不做：

1. daemon queue / persistence tests
2. landing integration tests
3. 让 `evaluate_stop_condition()` 直接返回修改后的 `BridgeWorkItem`
4. 把 orchestration helper 测试并入 `tests/test_runtime_bridge.py`

## 当前推荐

我当前推荐：

1. `stop_conditions.py` 只暴露 `StopConditionDecision` + `evaluate_stop_condition()`
2. 把 orchestration helper 的全部 targeted tests 收进独立的 `tests/test_runtime_orchestration.py`
3. 当前 gate 在这份草案写清后即可视为 docs-only 收口完成；下一步更适合转入代码实现 gate，而不是继续扩写设计文档

这样能把 runtime primitive 的代码入口、纯 helper contract 与最小测试面一起固定下来。