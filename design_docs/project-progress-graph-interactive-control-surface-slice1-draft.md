# Project Progress Graph Interactive Control Surface Slice 1 Draft

## 目标

让当前 progress graph 在不引入 direct mutation controls、也不依赖 daemon queue / persistence runtime 的前提下，先成为一个 **只读 control surface**：

1. 用户可以直接从 graph 查看当前节点状态
2. 用户可以看到当前 work-item / group-item 的 bridge 观察面
3. 当 runtime 已提供足够线索时，graph 可以显示“当前谁在处理这一步”或“当前处理线索是什么”

## 当前建议的 control snapshot contract

第一刀不直接把 live runtime state 塞进 graph node，而是先固定一份只读 snapshot。

### 1. work-item surface

最小建议字段：

1. `work_item_id`
2. `lifecycle_state`
3. `rollup_surface_kind`
4. `rollup_surface_state`
5. `rollup_blocked_reason`
6. `rollup_writeback_disposition`
7. `dominant_group_item_ids`
8. `open_group_item_count`
9. `source_trace_id`

### 2. group-item surface

最小建议字段：

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

### 3. actor / worker clue surface

当前不应伪造“agent identity”。第一版只允许显示 runtime 当前已经稳定暴露的处理线索，例如：

1. `latest_trace_id`
2. `latest_envelope_id`
3. 来自 group/work item 的 owner-facing delivery clue
4. 显式 actor label（仅当运行态后续明确提供时）

如果当前 runtime 没有稳定 actor 标识，则 UI 应显示“当前处理线索未知 / 未显式暴露”，而不是做推断式命名。

## 当前建议的 source-of-truth

1. `src/runtime/orchestration/models.py` 中的 `BridgeWorkItem` / `BridgeGroupItem` 是第一版 control snapshot 的字段来源
2. 第一版应新增独立的 graph-facing projection / snapshot helper，而不是让 `doc_projection.py` 直接读取 live runtime internals
3. preview / host surface 只消费 snapshot，不拥有 runtime state

## 当前优先级判断

结合当前代码面，下一阶段不宜被表述成“直接从 explorer 切到 control panel”。

更准确的推进顺序应是：

1. 先固定 snapshot authority shape
2. 再固定 graph binding contract
3. 然后才让 host overlay 消费这两层结果

也就是说，当前仓库仍应先停留在 explorer-hardening-compatible 的基础设施补强期，而不是先做 UI 侧的 control-panel 感知。

## 当前建议的 graph binding contract

1. 第一版优先使用显式 binding，而不是自动 topic matching 或模糊映射
2. binding 应允许三种落点：
   - graph-level status card
   - node-level status chip / detail companion
   - unresolved runtime items side panel
3. 当某个 work-item / group-item 还没有稳定 node binding 时，允许它先停留在 graph 旁侧的 control panel，而不是强行挂到错误节点

## 当前建议的后续 UI bundle

1. graph 顶部新增 control summary
   - 当前 open work items
   - waiting / blocked / completed roll-up
2. node detail 中新增 control section
   - 关联 work-item / group-item
   - governance / delivery state
   - blocked reason / open items / authoritative refs
3. 图侧栏新增 unresolved runtime panel
   - 尚未绑定到具体 graph node 的 work/group item

这组 UI bundle 当前应被视为 Slice 1/2 之后的消费层，而不是当前第一实现入口。

## 当前建议的边界

1. 第一刀只做 read-only control overlay
2. 不允许 graph 直接触发 retry / handoff / review intake / escalation 等动作
3. 不引入 daemon queue / persistence / replay runtime
4. 不重写当前 preview renderer
5. 不让 control snapshot 改写现有 `ready_nodes()` / topological layers 语义

## 当前明确不做

1. direct mutation controls
2. live process introspection
3. 自动 agent identity 推断
4. graph 与 bridge runtime 的强耦合 owner 反转

## 当前判断

这条 slice 足够窄，因为它先只回答一个问题：

“现有 progress graph，怎样在不变成第二套调度器的前提下，稳定显示 bridge / agent 当前处理状态？”

先把这层 contract 固定，后续无论是把 control snapshot 正式投影进 graph，还是继续做 direct actions，都会有稳定落点。