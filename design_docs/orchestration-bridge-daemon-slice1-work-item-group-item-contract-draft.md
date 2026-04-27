# 设计草案 — Orchestration Bridge Slice 1 Work Item / Group Item Contract

本文是 `design_docs/stages/planning-gate/2026-04-25-orchestration-bridge-work-item-group-item-contract.md` 的 Slice 1 设计草案。

## 目标

当前目标不是直接实现 daemon，也不是先设计 terminal landing artifact，而是先固定 bridge / daemon 层最小的 scheduler-facing primitive：

1. bridge 至少需要一个更高层 `work item`
2. bridge 至少需要一个承接 executor-local group 的 `group item`
3. 这两个对象必须与现有 governance kernel 解耦，而不是复制它的全部状态

## 设计原则

1. 不重写现有 `Decision Envelope` / `TaskGroup` / `GroupTerminalOutcome` 主对象家族
2. bridge 只拥有调度身份、生命周期与 compact governance footprint，不拥有 gate / review / writeback 决策权
3. `group item` 是对 executor-local group 的 wrapper，不替代 `TaskGroup`
4. Slice 1 先固定 identity / ownership / lifecycle 字段，不直接进入 queue、restart、landing contract

## 当前输入证据面

当前最接近 bridge / daemon 语义的输入面已经存在：

1. `Decision Envelope`：仍是当前用户请求与治理入口
2. `TaskGroup`：表达一个 parent-managed child group
3. `GroupedReviewOutcome` / `grouped_review_state`
4. `GroupTerminalOutcome`
5. grouped child writeback summary / eligibility basis

因此 Slice 1 不建议再发明第三套治理结果对象。更窄的做法是：

1. bridge primitive 只引用这些对象的 compact footprint
2. 完整治理对象继续留在 executor-local kernel
3. bridge 只根据 footprint 决定调度层的挂起、推进或等待外部接管

## 推荐的最小 primitive

### 1. `BridgeWorkItem`

推荐字段：

- `work_item_id: str`
- `source_envelope_id: str`
- `source_trace_id: str | None`
- `scope_summary: str`
- `dependency_ids: list[str]`
- `group_item_ids: list[str]`
- `lifecycle_state: str`
- `blocked_reason: str = ""`

用途：

1. 表达一个 bridge-owned orchestration 单位
2. 承载比单个 `TaskGroup` 更高层的调度身份
3. 聚合多个 `group item` 的当前调度状态

当前不建议让 `BridgeWorkItem` 直接携带：

1. `allowed_artifacts`
2. `review_state` 的完整历史
3. 完整 grouped review / terminal payload

这些仍属于现有治理内核对象。

### 2. `BridgeGroupItem`

推荐字段：

- `group_item_id: str`
- `work_item_id: str`
- `task_group_id: str`
- `child_task_ids: list[str]`
- `latest_envelope_id: str`
- `latest_trace_id: str | None`
- `lifecycle_state: str`
- `governance_surface_kind: str`
- `blocked_reason: str = ""`

其中：

- `governance_surface_kind` 当前建议只保留 compact kind，例如：
  - `grouped_review`
  - `group_terminal`
  - `blocked`
  - `none`

用途：

1. bridge 层需要知道某个 group 当前是普通 grouped review、terminal bundle 还是 blocked
2. 但不要求 bridge 持有完整 `GroupedReviewOutcome` / `GroupTerminalOutcome`
3. 后续 Slice 2 再定义这个 compact kind 如何进一步映射到 result footprint

## 推荐的 ownership boundary

### bridge 负责拥有的字段

bridge 应拥有：

1. work item / group item 的 identity
2. dependency / grouping relationship
3. 调度生命周期状态
4. compact governance footprint 的缓存或引用

### executor / governance kernel 继续拥有的字段

executor 继续拥有：

1. `Decision Envelope`
2. `TaskGroup` / `ParallelChildTask` / `ChildExecutionRecord`
3. `GroupedReviewOutcome`
4. `GroupTerminalOutcome`
5. grouped child writeback summary / audit event detail

### 当前推荐的 boundary rule

1. bridge 不复制完整 child report / grouped review / terminal payload
2. bridge 只消费一个 compact projection 或明确引用
3. 若 bridge 需要更多细节，应跳转回 governance-owned artifact，而不是就地扩 primitive

这条规则直接对应 Multica 的教训：不要在 scheduler 层再造一套与治理层竞争的状态对象。

## Ownership Matrix

当前推荐先把 bridge / executor / governance kernel 的 ownership boundary 写成显式矩阵：

| 字段或对象 | bridge / daemon | executor-local governance kernel | 说明 |
|---|---|---|---|
| `work_item_id` / `group_item_id` | owns | no | 纯 bridge 调度身份 |
| `source_envelope_id` / `source_trace_id` | references | owns original envelope/result lineage | bridge 只保留回跳指针 |
| `dependency_ids` / `group_item_ids` | owns | no | 调度层关系，不属于治理对象 |
| `TaskGroup` / `ParallelChildTask` / `ChildExecutionRecord` | no | owns | bridge 不复制 child-level evidence |
| `GroupedReviewOutcome` | footprint only | owns | bridge 只持有 compact kind / ref |
| `GroupTerminalOutcome` | footprint only | owns | bridge 只消费 terminal kind / blocked reason / ref |
| grouped child writeback summary | footprint only | owns | bridge 不重做 writeback 规划 |
| `lifecycle_state` | owns | no | scheduler-facing state，不等于 review state |
| `review_state` / `grouped_review_state` | observes only | owns | bridge 可以观察，但不重写 gate 迁移 |
| `blocked_reason` | shared footprint | owns source of truth | bridge 可缓存最后可见原因，但不成为新权威来源 |

当前矩阵的核心判断是：

1. bridge 可以拥有新的调度 identity 和 lifecycle
2. bridge 可以缓存 compact footprint
3. 但 grouped review / terminal / writeback 的 source of truth 仍然必须留在 executor-local governance kernel

这意味着后续实现如果发现 bridge 需要更多字段，优先应先问：

1. 是不是只需要再加一个 footprint 字段
2. 还是其实在错误地把 bridge 推成第二套治理内核

只有前者才应进入当前 gate。

## 推荐的最小 lifecycle 集

### `BridgeWorkItem.lifecycle_state`

当前建议最小集合为：

- `queued`
- `dispatching`
- `waiting_governance_result`
- `waiting_external_resolution`
- `completed`
- `blocked`

推荐的最小迁移表：

| 当前状态 | 允许下一状态 | 触发条件 | 边界说明 |
|---|---|---|---|
| `queued` | `dispatching` | bridge 选中该 work item，且至少一个 `group item` 已满足调度前提 | 只表示开始调度，不表示已拿到治理结果 |
| `queued` | `blocked` | bridge 在调度前已确认必要引用缺失、依赖图无效或无法形成合法 group 派发 | 这是 contract 级硬停，不引入 retry 语义 |
| `dispatching` | `waiting_governance_result` | 至少一个 `group item` 已成功交给 executor-local kernel | bridge 从此只等待 compact footprint，不扩展治理对象 |
| `dispatching` | `blocked` | 当前派发无法形成合法目标 group，或调度入口立即暴露 blocked footprint | 不在 Slice 1 中定义自动重试 |
| `waiting_governance_result` | `dispatching` | 已派发 group 已结算，且 work item 仍有剩余 `prepared` group 或新解锁的依赖可继续派发 | 这是继续推进其他 group，不等于重跑同一个 group |
| `waiting_governance_result` | `waiting_external_resolution` | 最新治理 footprint 表明 bridge 必须等待外部接管，例如显式 terminal / review gate / handoff 接管 | 这里只定义挂起，不定义 landing artifact 或 resume 细节 |
| `waiting_governance_result` | `completed` | 所有关联 `group item` 都已结算，且没有 blocked / external handoff 条件残留 | 完成依据仍来自 governance-owned source of truth |
| `waiting_governance_result` | `blocked` | 最新治理 footprint 暴露 blocked，或 bridge 丢失继续推进所需的最小引用 | `blocked_reason` 仅镜像最后可见原因 |

当前不定义 `waiting_external_resolution -> dispatching`、`completed -> *`、`blocked -> *` 的返回迁移。它们在 Slice 1 中都视为 terminal-like 状态；真正的恢复、resume、retry 或 restart 语义留给后续 runtime gate。

### `BridgeGroupItem.lifecycle_state`

当前建议最小集合为：

- `prepared`
- `dispatched`
- `settled`

推荐的最小迁移表：

| 当前状态 | 允许下一状态 | 触发条件 | 边界说明 |
|---|---|---|---|
| `prepared` | `dispatched` | bridge 已把该 `group item` 绑定到具体 executor-local `TaskGroup` 并发起派发 | 只表示已送入治理内核 |
| `prepared` | `settled` | 调度前检查已得出最终 footprint，例如 preflight 直接暴露 blocked，因而无需进入实际派发 | 用 `settled` 吸纳快速失败，避免额外引入 `blocked` lifecycle |
| `dispatched` | `settled` | executor-local kernel 已产出可消费的 compact governance footprint | 具体是 grouped review、group terminal 还是 blocked，由 `governance_surface_kind` 表示 |

结构上应保持两个轴分离：

1. `lifecycle_state` 只回答 bridge 调度当前处于哪个阶段
2. `governance_surface_kind` / `blocked_reason` 才回答 executor-local kernel 产出了什么治理结论

因此 Slice 1 不建议更早引入 retry / restart / resumed 等状态，也不建议把 `group terminal` / `waiting_review` 直接编码成新的 lifecycle state；这些都属于后续 result projection 与 stop-condition boundary，而不是 primitive contract 本身。

## 当前不做的设计

Slice 1 明确不做：

1. terminal bundle landing artifact
2. full queue / retry / wake-up engine
3. bridge 跨进程 persistence
4. 把 `BridgeWorkItem` 直接等同于 `Decision Envelope`
5. 把 `BridgeGroupItem` 直接等同于 `TaskGroup`

## 当前推荐

我当前推荐：

1. 先引入 `BridgeWorkItem` 与 `BridgeGroupItem` 两个最小 primitive
2. 让它们只承载 scheduler-facing identity / lifecycle / governance-footprint wrapper
3. 明确 bridge 只管理调度，不重写 gate / review / writeback 决策
4. 把更深层的 result projection 与 stop-condition 留到后续 slices

这条路线的优点是：

1. 不破坏已经完成的 executor-local governance kernel
2. 为 bridge / daemon 分叉提供最小 contract-first 入口
3. 能把下一步实现继续压在窄 scope 内，而不是直接膨胀成 full runtime