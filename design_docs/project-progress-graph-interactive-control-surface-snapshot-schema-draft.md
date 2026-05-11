# Project Progress Graph Interactive Control Surface Snapshot Schema Draft

## 目标

为 `project-progress graph interactive control surface` 的第一版只读观察面固定一份 graph-facing snapshot schema，使后续 projection helper、graph binding 与 host overlay 都消费同一份 authority shape。

## Root object

第一版建议统一输出 `control_snapshot`：

1. `snapshot_version`
   - 当前建议固定为显式版本号，例如 `v1alpha1`
2. `snapshot_kind`
   - 当前建议固定为 `orchestration-bridge-compact`
3. `generated_at`
   - snapshot 生成时间，用于 host/control surface 判断当前观察面的时间戳
4. `work_items`
   - `work_item_surface[]`
5. `group_items`
   - `group_item_surface[]`
6. `bindings`
   - `graph_binding[]`
7. `summary`
   - graph 顶部 control rail 所需的聚合计数与摘要

## Summary surface

第一版 `summary` 只保留 graph-level 观察面需要的最小统计：

1. `open_work_item_count`
2. `blocked_work_item_count`
3. `waiting_external_resolution_count`
4. `active_group_item_count`
5. `unbound_group_item_count`

这些值必须能从 `work_items` / `group_items` 自身推导出来；`summary` 只是消费友好的聚合缓存，不是第二份 source-of-truth。

## Work-item surface

每个 `work_item_surface` 当前建议固定以下字段：

1. `work_item_id`
2. `lifecycle_state`
3. `rollup_surface_kind`
4. `rollup_surface_state`
5. `rollup_blocked_reason`
6. `rollup_writeback_disposition`
7. `dominant_group_item_ids`
8. `open_group_item_count`
9. `source_trace_id`

字段约束：

1. `work_item_id` 必填，且在 snapshot 内唯一
2. `dominant_group_item_ids` 可为空数组，但不允许为 `null`
3. `rollup_blocked_reason` 在非 blocked surface 下允许为 `null`
4. `source_trace_id` 允许为空，用于表示当前 runtime 尚未提供稳定 trace 线索

## Group-item surface

每个 `group_item_surface` 当前建议固定以下字段：

1. `group_item_id`
2. `work_item_id`
3. `task_group_id`
4. `child_task_ids`
5. `lifecycle_state`
6. `governance_surface_kind`
7. `governance_surface_state`
8. `current_gate_state`
9. `writeback_disposition`
10. `delivery_surface_kind`
11. `delivery_state`
12. `blocked_reason`
13. `open_items`
14. `authoritative_refs`
15. `latest_trace_id`
16. `latest_envelope_id`
17. `actor_label`

字段约束：

1. `group_item_id` 必填，且在 snapshot 内唯一
2. `work_item_id` 必须指向现有 `work_item_surface.work_item_id`
3. `child_task_ids`、`open_items`、`authoritative_refs` 必须是数组，允许为空数组
4. `actor_label` 默认允许为空；第一版不能因为 UI 需要而做推断补值

## Graph binding surface

第一版 `graph_binding` 只解决“runtime surface 与 graph 落点怎么对应”，不解决 UI 表现细节。

建议字段：

1. `binding_id`
2. `binding_kind`
   - 建议值：`node`、`cluster`、`graph-section`、`unbound-runtime-panel`
3. `graph_id`
4. `graph_target_id`
5. `graph_target_key`
6. `work_item_ids`
7. `group_item_ids`
8. `binding_reason`

字段约束：

1. 第一版只允许显式 binding
2. `graph_target_id` 必须是 raw graph target 的 local id，而不是 display proxy id
3. 当 `binding_kind != "unbound-runtime-panel"` 时，`graph_id` / `graph_target_id` / `graph_target_key` 必填，且 `graph_target_key` 必须等于 `graph_id::graph_target_id`
4. 当 `binding_kind == "unbound-runtime-panel"` 时，`graph_id` / `graph_target_id` / `graph_target_key` 必须为空
5. 一个 `group_item_id` 可以暂时只出现在 `unbound-runtime-panel`
6. `binding_reason` 用于解释为什么它绑定到某个 graph target，例如 `explicit-node-ref`、`dominant-group-anchor`、`unbound-no-stable-target`

进一步约束：

1. 第一版 binding anchor 只锚定 raw target；display proxy 解析继续留给后续 overlay consumer surface
2. `graph-section` 当前保留，但不作为第一实现入口

## Source mapping

当前字段应优先来自以下已存在 surface：

1. `src/runtime/orchestration/models.py`
   - `BridgeWorkItem`
   - `BridgeGroupItem`
2. `src/runtime/orchestration/rollup.py`
   - work-item roll-up 相关 surface
3. `src/runtime/orchestration/projection.py`
   - governance / delivery compact surface
4. `tools/progress_graph/export.py`
   - `_scoped_key(graph_id, local_id)` 的 consumer-facing key 语义

若某个 UI 想要的字段当前不在这些 surface 中稳定存在，第一版应把它记为缺口，而不是让 projection helper 自行发明语义。

## Refresh boundary

1. 第一版 snapshot 只跟随显式 refresh / regenerate 流程刷新
2. 第一版不要求 watcher-driven auto refresh
3. snapshot producer 与 graph consumer 必须可分离：producer 负责输出稳定 schema，consumer 负责展示

## No-change boundary

1. 不在 schema 内加入 direct action payload
2. 不把 live process internal handle 暴露为 graph consumer contract
3. 不让 snapshot schema 改写现有 doc-loop projection graph 的拓扑定义

## 当前判断

先固定这份 schema，有两个直接收益：

1. Slice 2 的 projection helper 可以按字段表实现，而不是一边写一边补 contract
2. Slice 3 的 host overlay 可以围绕 `summary` / `bindings` / `group_items` 落 UI，而不是再重新定义状态面