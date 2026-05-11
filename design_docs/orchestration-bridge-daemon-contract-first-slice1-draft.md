# Slice 1 Draft — Orchestration Bridge Daemon Contract-First

## Contract focus

本 Slice 只固定 landing-dispatch gate 关闭之后，bridge / daemon 与现有治理内核之间的最小 ownership matrix，不进入 runtime helper 或 daemon queue 实现。

## Design principles

1. 不重写现有 `Decision Envelope` / `TaskGroup` / `GroupTerminalOutcome` / grouped review 主对象家族
2. bridge 只拥有调度身份、生命周期、recovery judgment 与 compact footprint，不拥有 gate / review / writeback 决策权
3. landing dispatch 已经是 owner-facing delivery surface，bridge 不再重写 handoff / review / escalation payload shape
4. 如果 bridge 需要更多细节，优先新增 compact projection 字段或引用，而不是复制治理对象本体

## Current lower surfaces

当前已经稳定存在的下游 surface：

1. governance kernel 继续拥有 `Decision Envelope`、`TaskGroup`、`GroupTerminalOutcome`、grouped review / writeback / audit judgment
2. `src/runtime/orchestration/landing_dispatch.py` 已把 `handoff`、`escalation`、`review_intake` 三类 payload 统一落到真实 owner surface
3. landing dispatch gate 已证明 owner-facing payload 不需要再由 bridge 重写 shape

因此，当前下一刀不再是补 owner surface，而是回答 bridge / daemon 上层到底拥有哪一层 identity、lifecycle、recovery 与等待外部接管语义。

## Minimum primitive boundary

当前 Slice 1 只需要把两个 bridge primitive 的职责边界钉住，不需要在这里锁具体 schema：

### 1. `BridgeWorkItem`

当前判断：它只需要承接更高层的调度身份、依赖关系、bridge-facing lifecycle，以及“是否必须等待外部接管”的观察面。

当前不应让它直接承接：

1. 完整 grouped review / terminal payload
2. 完整 owner-facing landing artifact
3. 详细 review / writeback 历史

### 2. `BridgeGroupItem`

当前判断：它只需要引用一个 executor-local group，并暴露最小的 compact governance / landing footprint，供 bridge 后续聚合。

当前不应让它直接承接：

1. `TaskGroup` / child record 的完整镜像
2. 原始 handoff / review_intake / escalation payload
3. 第二套与 governance kernel 竞争的 review / writeback 状态对象

## Recommended ownership matrix

当前推荐先固定以下边界：

1. bridge / daemon 拥有：`work item` / `group item` identity、dependency / scheduling state、retry / recovery intent、external-resolution waiting boundary
2. governance kernel 拥有：gate / review / writeback / audit judgment，以及 `GroupTerminalOutcome`、grouped review state 等 raw result object
3. landing dispatch / owner surfaces 拥有：真实 handoff document 持久化、pending review 登记、escalation notification delivery
4. bridge 只消费 compact projection，不直接拥有 raw handoff payload、FeedbackAPI entry 或 owner-surface document schema

## Ownership matrix

当前推荐把 bridge / governance kernel / landing dispatch surface 的 ownership boundary 压成三条规则：

1. bridge / daemon 只拥有调度身份、bridge-facing lifecycle、依赖关系，以及 compact recovery / external-resolution judgment
2. governance kernel 继续拥有 grouped review、group terminal、writeback、audit 与 raw result object 的 source of truth
3. landing dispatch / owner surface 继续拥有 handoff 持久化、review intake 登记、escalation delivery 以及这些 delivery result 的原始细节

当前矩阵的核心判断是：

1. bridge 可以拥有新的调度 identity、lifecycle 与 external-resolution boundary judgment
2. bridge 可以缓存 compact governance / landing footprint
3. 但 grouped review / terminal / writeback / owner delivery 的 source of truth 仍然必须留在现有治理内核与 landing dispatch surface

这意味着后续如果发现 bridge 需要更多字段，优先应先问：

1. 是否只需要再加一个 compact footprint 字段
2. 还是其实在错误地把 bridge 推成第二套治理内核或第二套 owner-delivery adapter

只有前者才应进入当前 gate。

## Lifecycle boundary

当前 Slice 1 只需要固定生命周期的边界层口径，不需要在这里写死完整迁移表：

1. `BridgeWorkItem` 需要能表达“待调度 / 调度中 / 等待治理结果 / 等待外部接管 / 完成 / 阻塞”这一层调度观察面
2. `BridgeGroupItem` 需要能表达“尚未派发 / 已派发 / 已结算”这一层 group-level 调度观察面
3. governance result 与 owner delivery result 仍应作为与 lifecycle 分离的第二条轴，不应直接编码成新的 lifecycle family

这已经足够支撑当前 gate 回答 ownership boundary；更细的迁移规则应留给后续 runtime 或 stop-boundary 文档，而不是在 Slice 1 里提前锁死。

## Current recommendation

当前推荐把 bridge 继续收窄为 scheduler-facing lifecycle / recovery wrapper：

1. `group item` 负责引用一个 executor-local group 的 compact governance + landing footprint
2. `work item` 负责汇总多个 `group item` 的调度观察面与恢复判断
3. bridge 只决定“继续调度 / 等待外部接管 / 可恢复 / 停机边界”，不直接决定 gate / review 语义

## Slice 2 questions to settle

进入 Slice 2 前，当前需要进一步收束：

1. `GroupTerminalOutcome`、grouped review state、writeback summary、landing dispatch result 分别先投影到 `group item` 还是 `work item`
2. `waiting_external_resolution` 的触发证据应来自哪些已有 surface
3. bridge-facing stop reason / recovery intent 是否需要单独 compact 字段，还是可由现有 projection 组合推出

## Current status

当前已完成：

1. bridge / governance kernel / landing dispatch surface 的 ownership boundary
2. `BridgeWorkItem` / `BridgeGroupItem` 的最小职责划分
3. scheduler-facing lifecycle 与 result surface 分离的边界口径

当前下一步更适合进入 Slice 2，固定 upward terminal / landing projection contract，而不是提前进入 runtime helper。

## Decision fork

### A. Wrapper-first ownership matrix（推荐）

- 做什么：先把 bridge 收窄成 work-item / group-item wrapper，并固定 compact projection contract
- 优点：最符合当前 landing dispatch 已收口后的边界，不会重新污染 governance kernel 或 owner surface

当前判断：推荐。

### B. Runtime-first daemon skeleton

- 做什么：先做 daemon lifecycle / queue skeleton，再回头补 ownership matrix
- 风险：会把 queue / persistence / replay 语义提前混入，打破当前 gate 的 docs-first 收窄边界

当前判断：不推荐作为第一刀。

## Out of scope

1. full daemon runtime / queue / persistence / replay 实现
2. direct runtime helper coding
3. broader companion prose surface expansion
4. dogfood evidence / issue / feedback backlog