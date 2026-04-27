# 设计草案 — Orchestration Bridge Runtime Primitives Slice 2 Model / Helper Contract

本文是 `design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-runtime-primitives.md` 的 Slice 2 设计草案，建立在 `design_docs/orchestration-bridge-runtime-primitives-slice1-surface-isolation-draft.md` 已固定的 `src/runtime/orchestration/` 模块边界之上。

## 目标

当前目标不是立即实现 daemon runtime，而是把 orchestration bridge 的 runtime model 与 pure helper contract 写成可直接落代码的最小面：

1. `models.py` 里 `BridgeWorkItem` / `BridgeGroupItem` 应长什么样
2. `projection.py` 和 `rollup.py` 各自只负责什么，函数签名如何固定
3. 哪些字段在 runtime 中必须是 optional，哪些必须始终存在

本文不定义：

1. `stop_conditions.py` 的具体 evaluator contract
2. queue / persistence / replay runtime
3. landing integration

## 当前输入证据面

当前 contract 已经提供了足够的结构前提：

1. 上一条 docs-only gate 已固定 `BridgeWorkItem` / `BridgeGroupItem` 的字段与生命周期语义
2. Slice 1 已固定模块布局为 `src/runtime/orchestration/`
3. `src/runtime/bridge.py` 继续保留给 host-entry `RuntimeBridge`

因此 Slice 2 的最小职责不是再发明新对象，而是把已确定的字段压成 runtime model，并把 projection / roll-up helper 写成纯函数边界。

## 当前推荐的 representation rule

当前推荐在 `src/runtime/orchestration/models.py` 中采用：

1. dataclass-based model
2. 以 tuple 表达 `dependency_ids`、`group_item_ids`、`child_task_ids`、`dominant_group_item_ids` 这类稳定集合
3. 统一在 `models.py` 定义 lifecycle / surface / disposition 的 literal-like type alias，避免 helper 间重复散落字符串集合

选择 tuple 的原因是：

1. 它天然避免 mutable default 问题
2. 它与 pure helper 的“返回新对象”语义更一致
3. 它能把 deterministic ordering 约束直接落实到 runtime model

## `models.py` Contract

### 共享类型别名

当前推荐至少定义以下别名：

- `BridgeWorkLifecycle`
- `BridgeGroupLifecycle`
- `GovernanceSurfaceKind`
- `GovernanceSurfaceState`
- `WritebackDisposition`

用途是把 Slice 1 / Slice 2 文档里已经固定的状态集合收束到一个统一来源。

### `BridgeGroupItem`

当前推荐字段：

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `group_item_id` | `str` | 无 | bridge 层 group identity |
| `work_item_id` | `str` | 无 | 归属的 work item |
| `task_group_id` | `str | None` | `None` | 只有真正绑定到 executor-local `TaskGroup` 后才应存在 |
| `child_task_ids` | `tuple[str, ...]` | `()` | 调度前允许为空 |
| `latest_envelope_id` | `str | None` | `None` | 调度/结算前允许为空 |
| `latest_trace_id` | `str | None` | `None` | 可选 lineage pointer |
| `lifecycle_state` | `BridgeGroupLifecycle` | `prepared` | 仍沿用上一条 gate 固定的 3 态 |
| `governance_surface_kind` | `GovernanceSurfaceKind` | `none` | compact result family |
| `governance_surface_state` | `GovernanceSurfaceState | str` | `""` | compact sub-state |
| `blocked_reason` | `str` | `""` | 仅缓存最后可见 reason |
| `writeback_disposition` | `WritebackDisposition` | `pending` | compact writeback disposition |

这里最关键的 runtime 决定是：

1. `task_group_id` 和 `latest_envelope_id` 在 runtime model 中必须是 optional
2. 否则 `prepared -> dispatched` 之前的 group item 无法保持结构合法

### `BridgeWorkItem`

当前推荐字段：

| 字段 | 类型 | 默认值 | 说明 |
|---|---|---|---|
| `work_item_id` | `str` | 无 | bridge 层 work identity |
| `source_envelope_id` | `str` | 无 | 上游 envelope 引用 |
| `source_trace_id` | `str | None` | `None` | 上游 trace 引用 |
| `scope_summary` | `str` | 无 | work-level scope 描述 |
| `dependency_ids` | `tuple[str, ...]` | `()` | 稳定依赖集合 |
| `group_item_ids` | `tuple[str, ...]` | `()` | 稳定 group 集合 |
| `lifecycle_state` | `BridgeWorkLifecycle` | `queued` | 沿用上一条 gate 固定的 6 态 |
| `blocked_reason` | `str` | `""` | 只有 stop evaluator 决定 blocked 时才应写入 |
| `rollup_surface_kind` | `GovernanceSurfaceKind` | `none` | dominant roll-up family |
| `rollup_surface_state` | `GovernanceSurfaceState | str` | `""` | dominant roll-up sub-state |
| `rollup_blocked_reason` | `str` | `""` | dominant reason 镜像 |
| `rollup_writeback_disposition` | `WritebackDisposition` | `pending` | roll-up 后的 writeback 观察口径 |
| `dominant_group_item_ids` | `tuple[str, ...]` | `()` | 按稳定顺序排序的 dominant group 集 |
| `open_group_item_count` | `int` | `0` | 尚未 settled 的 group-item 数量 |

这里最关键的 runtime 决定是：

1. `blocked_reason` 与 `rollup_blocked_reason` 同时保留
2. 前者属于 lifecycle-facing field，后者属于 result-facing field
3. Slice 2 不允许 roll-up helper 直接覆盖 `blocked_reason`；这一步留给 Slice 3 的 stop evaluator

## `projection.py` Contract

当前推荐只暴露一个最小 pure helper：

```python
def project_group_item_surface(
    group_item: BridgeGroupItem,
    *,
    governance_surface_kind: GovernanceSurfaceKind,
    governance_surface_state: GovernanceSurfaceState | str = "",
    blocked_reason: str = "",
    writeback_disposition: WritebackDisposition = "pending",
) -> BridgeGroupItem: ...
```

语义边界：

1. helper 只负责把 compact governance footprint 投影回 `BridgeGroupItem`
2. helper 返回新的 `BridgeGroupItem`，不做 in-place mutate
3. helper 会把 `lifecycle_state` 统一收口到 `settled`
4. helper 不负责把 `prepared` / `dispatched` 绑定到实际 `TaskGroup`；那部分由后续 runtime 调度层自行使用 dataclass replace 或等价方式完成

## `rollup.py` Contract

当前推荐只暴露一个最小 pure helper：

```python
def roll_up_work_item(
    work_item: BridgeWorkItem,
    group_items: tuple[BridgeGroupItem, ...],
) -> BridgeWorkItem: ...
```

语义边界：

1. helper 只消费 `BridgeGroupItem` 上已有的 compact result footprint
2. helper 返回新的 `BridgeWorkItem`，只更新 `rollup_*`、`dominant_group_item_ids`、`open_group_item_count`
3. helper 不直接写 `blocked_reason`
4. helper 要求传入的 `group_items` 全部满足 `group_item.work_item_id == work_item.work_item_id`；不满足时属于 runtime contract violation

## `stop_conditions.py` 在 Slice 2 的边界

当前只保留一个依赖约束，不进入具体 evaluator contract：

1. `stop_conditions.py` 只消费 `BridgeWorkItem`
2. 它的具体返回类型、boundary kinds 和 targeted tests 仍留到 Slice 3

这样可以避免 Slice 2 抢占 Slice 3 的职责，同时保证 `models.py` / `projection.py` / `rollup.py` 的 contract 足够稳定。

## 当前不做的设计

当前不做：

1. `projection.py` 直接消费 `GroupedReviewOutcome` / `GroupTerminalOutcome` 原始对象
2. `rollup.py` 直接返回 stop-condition judgment
3. 专门的 `GroupItemSurface` / `WorkItemRollup` 中间对象
4. `OrchestrationBridgeRuntime` facade

## 当前推荐

我当前推荐：

1. Slice 2 只固定 `models.py` + `projection.py` + `rollup.py` 的 contract
2. 保持 `stop_conditions.py` 继续留给 Slice 3 收口
3. 后续代码实现优先采用 pure helper + return-new-instance 语义，避免 helper 隐式改写 bridge runtime state

这样做能把 runtime primitive 落成最小可测的模型层，而不会提前把调度器或 daemon facade 混进来。