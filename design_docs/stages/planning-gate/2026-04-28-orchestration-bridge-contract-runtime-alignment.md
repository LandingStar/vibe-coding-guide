# Planning Gate — Orchestration Bridge Contract/Runtime Alignment

> 日期: 2026-04-28
> 状态: COMPLETED
> 来源: `design_docs/orchestration-bridge-daemon-contract-first-followup-direction-analysis.md`

## Why this exists

`design_docs/stages/planning-gate/2026-04-28-orchestration-bridge-daemon-contract-first.md` 已按 docs-only boundary 完成并关闭。

这意味着当前 bridge 主线已经具备：

1. ownership boundary、group-item projection、work-item roll-up 与 stop-boundary trigger family 的完整 contract 面
2. 下一条 runtime 入口应沿现有 `models` / `rollup` / `stop_conditions` / `landing` surface 对齐，而不是直接进入 queue / persistence / replay
3. 当前仓库已经存在最小 runtime helper，因此最值得新增的信息不再是“应该设计什么”，而是“现有 helper 与这份 contract 是否真正一致”

因此，下一条最窄 planning-gate 应先固定 **contract/runtime alignment surface**，而不是继续写更高层 daemon 设计。

## Scope

本 gate 只处理：

1. `src/runtime/orchestration/models.py` 与 Slice 1 contract 的对齐边界
2. `src/runtime/orchestration/projection.py` 与 Slice 2 group-item projection contract 的对齐边界
3. `src/runtime/orchestration/rollup.py`、`stop_conditions.py`、`landing.py` 与 Slice 2-3 contract 的对齐边界
4. 哪些现有 runtime helper 可以原样保留，哪些需要 trim、rename、补最小字段或补 targeted tests
5. 如何在不改写 governance kernel schema 的前提下完成这层 alignment

本 gate 不处理：

1. broader daemon queue / persistence / replay runtime
2. 新的 bridge lifecycle family
3. owner-facing landing surface 的新 adapter 设计
4. broader companion prose 或 dogfood backlog

## Working hypothesis

当前最小可行路线应是：

1. 先以 contract 为 authority，对现有 runtime surface 做一轮 alignment inventory
2. 优先修补“contract 已明确、runtime helper 已存在但口径不完全一致”的窄缺口
3. 不把 alignment gate 误扩成新的 daemon runtime 设计或新的 owner-surface 集成设计

## Slices

### Slice 1 — Alignment inventory and ownership map

- 盘点 `models.py`、`projection.py`、`rollup.py`、`stop_conditions.py`、`landing.py` 与 Slice 1-3 contract 的对应关系
- 标出 keep / trim / extend / rename 四类差异
- 固定本 gate 的最小 code-touch boundary 与 targeted validation 入口

当前状态：Slice 1 设计草案已创建为 `design_docs/orchestration-bridge-contract-runtime-alignment-slice1-draft.md`；当前已补出 alignment authority surface、keep / trim / extend / rename 四类差异与 targeted validation 入口。当前下一窄切口收束为：选定第一条 conformance edit，而不是直接扩大到 broader daemon runtime。

### Slice 2 — Minimal runtime conformance edits

- 只对 Slice 1 已确认的差异做最小 runtime edit
- 保持 `models` / `rollup` / `stop_conditions` / `landing` 的职责不再发散
- 补足最小 targeted tests

当前状态：Slice 2 草案已创建为 `design_docs/orchestration-bridge-contract-runtime-alignment-slice2-delivery-signal-backflow-draft.md`；当前已决定最小 delivery signal 采用 group-item-first 落点，由 `models.py` 承载 compact signal、`projection.py` 负责纯归一化、`landing_dispatch.py` 保持 source-of-truth，并已把最小 clue 收窄为 delivery family / delivery state / record clue / failure clue。当前还已决定最小代码接入方式为“`models.py` 增字段 + `projection.py` 独立 delivery projector”，而不是把 delivery kwargs 混入现有治理 projector，且本刀暂不接 integration hook；独立 delivery projector 的最小 contract 现已写清，并已完成最小代码实现与 targeted tests，`tests/test_runtime_orchestration.py` 结果为 `10 passed`。当前下一窄切口收束为：判断这条 isolated conformance edit 是否已满足本 gate 的最小 close 条件，或是否需要新的窄 follow-up slice。
当前状态：Slice 2 草案已创建为 `design_docs/orchestration-bridge-contract-runtime-alignment-slice2-delivery-signal-backflow-draft.md`；当前已决定最小 delivery signal 采用 group-item-first 落点，由 `models.py` 承载 compact signal、`projection.py` 负责纯归一化、`landing_dispatch.py` 保持 source-of-truth，并已把最小 clue 收窄为 delivery family / delivery state / record clue / failure clue。当前还已决定最小代码接入方式为“`models.py` 增字段 + `projection.py` 独立 delivery projector”，而不是把 delivery kwargs 混入现有治理 projector，且本刀暂不接 integration hook；独立 delivery projector 的最小 contract 现已写清，并已完成最小代码实现与 targeted tests，`tests/test_runtime_orchestration.py` 结果为 `10 passed`。当前 gate-close writeback bundle 已完成，当前 gate 已正式切为 `COMPLETED`；后续主线改由 `design_docs/orchestration-bridge-contract-runtime-alignment-followup-direction-analysis.md` 承接。

## Validation gate

- 文档验证：
  - 能清楚回答哪几个 runtime 文件是当前 alignment authority surface
  - 能清楚回答每个 surface 对应 Slice 1-3 的哪一层 contract
  - 能清楚回答哪些差异属于 keep、哪些属于 trim / extend / rename
- 后续代码验证：
  - targeted tests 能覆盖当前 alignment slice
  - alignment edit 不迫使 governance kernel schema 返工

## Stop condition

- 当 alignment inventory、最小 code-touch boundary 与 targeted validation 入口都已写清后停止
- 不在本 gate 内直接进入 broader daemon runtime 设计

## Close result

当前 gate-close writeback bundle 已完成，因此本 gate 现已正式切为 `COMPLETED`。

本次收口已完成：

1. current-gate follow-up direction analysis 已写入 `design_docs/orchestration-bridge-contract-runtime-alignment-followup-direction-analysis.md`
2. `design_docs/direction-candidates-after-phase-35.md` 已同步 close 后的下一步候选面
3. canonical handoff `2026-04-29_1925_orchestration-bridge-contract-runtime-alignment_stage-close` 已生成、校验通过，并已轮转为 `CURRENT.md` 的 mirror source
4. Checklist、Phase Map 与 checkpoint 已统一到同一 handoff footprint，当前仓库重新回到无 active planning-gate 状态

此前 close 规则差点执行不精确的原因保留如下：

1. 当前 planning-gate 本地 `Stop condition` 只编码了切片内部的 implementation readiness，没有把 safe-stop writeback bundle 明写成 close 前置条件
2. `/memories/repo/project-state.md` 曾停留在“无 active planning gate”的过期状态，因此 repo memory 不能被当作 close judgment 的权威来源
3. 当本地 gate 文本与高层 workflow 标准分离时，模型容易在“内容已完成”处过早停下，而不是继续执行 close bundle

因此后续不再继续修改本 gate；下一步应从 `design_docs/orchestration-bridge-contract-runtime-alignment-followup-direction-analysis.md` 起新的窄 planning-gate。