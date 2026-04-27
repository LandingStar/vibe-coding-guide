# 设计草案 — Orchestration Bridge Models Implementation Slice 1

本文是 `design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-models-helpers-implementation.md` 的 Slice 1 设计草案。

## 目标

当前只实现最小 runtime models：

1. `BridgeWorkItem`
2. `BridgeGroupItem`
3. 共享 type alias

当前不进入 helper 实现。

## 当前推荐

当前推荐新增：

- `src/runtime/orchestration/models.py`
- `src/runtime/orchestration/__init__.py`

`models.py` 应包含：

1. `BridgeWorkLifecycle`
2. `BridgeGroupLifecycle`
3. `GovernanceSurfaceKind`
4. `GovernanceSurfaceState`
5. `WritebackDisposition`
6. `BridgeGroupItem`
7. `BridgeWorkItem`

## 实现边界

1. 使用 dataclass
2. 稳定集合统一使用 tuple
3. `task_group_id` / `latest_envelope_id` / `latest_trace_id` 保持 optional
4. 不在本 slice 内加入任何 evaluator 或 projection/roll-up helper

## 当前推荐的验证

当前推荐在后续测试中至少验证：

1. 默认值正确
2. optional dispatch-lineage 字段在初始态可为空
3. tuple-based collection 默认不共享可变状态