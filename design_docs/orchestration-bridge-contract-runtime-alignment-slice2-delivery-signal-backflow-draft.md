# Slice 2 Draft — Orchestration Bridge Contract/Runtime Alignment Delivery Signal Backflow

本文是 [design_docs/stages/planning-gate/2026-04-28-orchestration-bridge-contract-runtime-alignment.md](design_docs/stages/planning-gate/2026-04-28-orchestration-bridge-contract-runtime-alignment.md) 的 Slice 2 设计草案，直接承接 Slice 1 已归类出的第一条 extend gap。

## Goal

当前只解决一个更窄的问题：

1. owner-facing delivery signal 是否需要最小回流到 bridge model surface
2. 如果需要，应该回流到 group-item、work-item，还是只停留在 dispatch result 外层
3. 哪些 delivery 信息属于 compact signal，哪些仍必须留在 `dispatch_landing_consumer_payload(...)` 的原始结果里

本文不定义：

1. full owner artifact mirror
2. broader landing consumer redesign
3. queue / persistence / replay runtime

## Current mismatch

当前 runtime 已经拥有两层稳定面：

1. `landing.py` 能在 `wait_external_resolution` boundary 上构造最小 landing artifact
2. `landing_dispatch.py` 能把 artifact 投递到真实 owner surface，并返回 delivery result

但当前 bridge model surface 主要承接 governance-side projection，delivery result 还没有以 compact signal 回流到 group-item / work-item。

因此当前最小 conformance 问题不是“要不要重做 dispatch”，而是：

1. bridge runtime 是否至少需要知道 landing 是否已成功送达
2. bridge runtime 是否至少需要知道 delivery failure 已发生
3. bridge runtime 是否需要保留最小 record clue，便于回跳而不是重新拉 full consumer result

## Recommended boundary

当前推荐只允许最小 delivery signal 回流，而不是把 dispatch result 整体并回 bridge model：

1. bridge model 最多只观察 owner-facing delivery family
2. bridge model 最多只观察 delivery 当前是未开始、成功、失败，还是仍需后续处理
3. bridge model 最多只观察最小 record clue 与 failure clue
4. `consumer_result`、owner artifact path、pending-review payload 等原始细节继续留在 dispatch result / owner surface，不成为 bridge model 的新 source of truth

## Chosen minimal compact clue set

当前已决定最小 compact delivery clue 只保留以下四类：

1. delivery family：当前对应的是 handoff、review-intake、escalation notification 中的哪一类 owner-facing landing
2. delivery state：当前是尚未发起、已成功，还是已失败
3. record clue：当前是否已经拿到最小 record id，足够后续回跳
4. failure clue：当前是否已经出现 delivery failure，以及 bridge 可见的最后一条 failure reason

当前不进入最小集合的内容包括：

1. `consumer_result` 全量内容
2. owner artifact path
3. pending review payload 细节
4. dispatch target surface 的完整诊断信息

这条边界的核心是：只保留 bridge 后续 conformance 真正需要的最小 clue，而不把 dispatch result 重新包装成第二套 owner-delivery 状态对象。

## Preferred landing point

当前更合理的判断是：

1. delivery signal 应先回流到 group-item，因为它本质上仍然对应单个 dominant group 的 owner-facing landing
2. work-item 只在确有必要时观察聚合后的 delivery clue，而不直接复制所有 group-level delivery detail
3. 如果当前 stop-boundary 只依赖 dominant governance roll-up，那么 delivery signal 应主要作为后续 conformance / traceability clue，而不是立即扩大为新的 stop-state family

## Chosen minimal landing layer

当前已决定采用以下最小落点：

1. `models.py` 负责承载 group-item 级别的 compact delivery signal，但不承载 raw dispatch result 或 owner artifact
2. `projection.py` 负责作为纯归一化入口，把 owner-facing delivery signal 写回 `BridgeGroupItem`
3. `landing_dispatch.py` 继续只负责 dispatch 与返回 source-of-truth 的 delivery result，不承担新的 bridge-state 聚合职责

这条边界的核心是：

1. model 层只持有最小 signal
2. projection 层负责把 signal 变成 bridge 可观察面
3. dispatch 层继续保留真实 delivery 细节与 failure detail 的权威来源

因此当前第一条 conformance edit 的最小 code-touch boundary 已经收窄为：

1. `src/runtime/orchestration/models.py`
2. `src/runtime/orchestration/projection.py`

而不是把 `src/runtime/orchestration/landing_dispatch.py` 一起拖进状态聚合逻辑。

## Chosen minimal code-touch approach

当前已决定采用以下最小代码接入方式：

1. `models.py` 只为 `BridgeGroupItem` 增加 compact delivery clue 所需的最小字段
2. `projection.py` 新增独立的 delivery projector，用来把 dispatch result 归一化为 group-item 可观察 signal
3. 现有 `project_group_item_surface(...)` 继续只承接 governance-side projection，不混入 owner-facing delivery kwargs
4. `landing_dispatch.py` 继续返回 source-of-truth 的 dispatch result，不改造成 bridge-state writer

当前这样收窄的原因是：

1. `project_group_item_surface(...)` 目前只被 `executor_adapter.py` 调用，职责已经明确偏向治理结果投影
2. 如果把 delivery signal 直接混入现有 projector，会重新模糊 governance projection 与 owner-facing delivery projection 的边界
3. 独立 delivery projector 可以把 code-touch 边界稳定留在 `models.py` / `projection.py`，同时保留后续最小 integration hook

因此当前最合理的下一步不是再讨论层次，而是决定这个独立 delivery projector 的输入/输出最小 contract。

## Integration-hook decision

当前已决定：这一刀先不接 integration hook。

原因是：

1. 当前 stop-boundary 仍然只消费 governance-side dominant roll-up，并不依赖 delivery signal 才能继续工作
2. 如果现在把 delivery signal 直接接进 coordinator、dispatch flow 或更高层 roll-up，会把 alignment gate 从最小 conformance 过早扩大成行为改动
3. 先把 `models.py` + `projection.py` 的 isolated conformance surface 固定下来，后续是否真正接入 flow，应该由下一条更窄的 integration decision 再决定

因此当前 Slice 2 的最小范围应保持为：

1. 定义 compact delivery clue
2. 定义 group-item-first 落点
3. 定义 `models.py` + `projection.py` 的独立 delivery projector
4. 暂不把这个 projector 接到更高层 flow

## Minimal delivery projector contract

当前已把独立 delivery projector 的最小 contract 收窄为：

1. 它是 pure helper：输入一个现有 `BridgeGroupItem` 与最小 delivery clue，输出一个新的 `BridgeGroupItem`
2. 它只覆写 delivery family / delivery state / record clue / failure clue 相关字段
3. 它不改变 `lifecycle_state`
4. 它不改变 governance-side surface、writeback posture、authoritative refs、open items 或 current gate state
5. 它不持有 raw `consumer_result`，也不接管 dispatch source-of-truth

当前 contract 更偏向“overlay”而不是“re-project”：

1. governance projection 先发生
2. delivery projector 只在需要时叠加 owner-facing delivery clue
3. work-item 是否观察这些 clue，留给后续更窄的 integration decision

因此当前最小实现目标已经足够明确：

1. `models.py` 需要能承载这四类 compact clue
2. `projection.py` 需要一个独立的 pure overlay helper
3. 本刀不需要改 `executor_adapter.py`、`rollup.py`、`stop_conditions.py` 或 `landing_dispatch.py` 的既有行为

## Implementation status

当前这条最小 conformance edit 已按上述 contract 落地：

1. `src/runtime/orchestration/models.py` 已为 `BridgeGroupItem` 增加 compact delivery clue 所需的最小字段
2. `src/runtime/orchestration/projection.py` 已新增独立的 `project_group_item_delivery_signal(...)` overlay helper
3. `src/runtime/orchestration/__init__.py` 已导出新增类型与 helper，保持 orchestration runtime surface 可见
4. `tests/test_runtime_orchestration.py` 已补充默认值与 delivery overlay targeted tests

当前验证结果：

1. `tests/test_runtime_orchestration.py` 已通过，结果为 `10 passed`

## Current recommendation

我当前推荐：

1. 先把 delivery signal backflow 固定成 compact signal boundary，而不是字段明细
2. 当前已把回流落点收窄为 group-item-first，且决定由 `models.py` 承载 signal、`projection.py` 负责归一化、`landing_dispatch.py` 保持 source-of-truth
3. 当前已把最小 delivery signal 固定成 delivery family / delivery state / record clue / failure clue 四类 compact clue，并通过“`models.py` 增字段 + `projection.py` 独立 delivery projector”的方式落地，且本刀未引入 integration hook；当前下一步应转向判断这条 isolated conformance edit 是否已满足本 gate 的最小 close 条件，或是否需要新的窄 follow-up slice

这样可以把当前 conformance edit 继续保持在窄 scope 内，而不是重新放大到 owner-surface redesign。