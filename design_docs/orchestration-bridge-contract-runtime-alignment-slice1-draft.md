# Slice 1 Draft — Orchestration Bridge Contract/Runtime Alignment

本文是 [design_docs/stages/planning-gate/2026-04-28-orchestration-bridge-contract-runtime-alignment.md](design_docs/stages/planning-gate/2026-04-28-orchestration-bridge-contract-runtime-alignment.md) 的 Slice 1 设计草案。

## Goal

当前 Slice 1 只解决一个更窄的问题：

1. 哪些现有 runtime file 是这次 alignment 的 authority surface
2. 每个 file 当前承接的是 Slice 1-3 contract 的哪一层
3. 哪些差异应归类为 keep、trim、extend 或 rename
4. 下一步最小 code-touch boundary 应从哪里开始

## Current runtime authority surface

当前最直接的 alignment surface 已经存在于以下 5 个文件：

1. `src/runtime/orchestration/models.py`
   - 承接 bridge primitive 的 runtime model
2. `src/runtime/orchestration/projection.py`
   - 承接 group-item projection 的最小 surface 归一化
3. `src/runtime/orchestration/rollup.py`
   - 承接 work-item roll-up
4. `src/runtime/orchestration/stop_conditions.py`
   - 承接 dominant roll-up 到 boundary judgment 的映射
5. `src/runtime/orchestration/landing.py`
   - 承接 `wait_external_resolution` 之后的 landing artifact 构建

当前判断：这 5 个文件已经足以构成 alignment gate 的最小 authority surface，不需要再把 scope 扩到 broader daemon runtime。

## Contract mapping

当前推荐的 contract 对齐关系是：

1. Slice 1 contract 主要映射到 `models.py`
2. Slice 2 的 group-item projection 主要映射到 `projection.py`，并部分回看 `models.py`
3. Slice 2 的 work-item roll-up 主要映射到 `rollup.py`
4. Slice 3 的 stop-boundary trigger family 与 next runtime entry 主要映射到 `stop_conditions.py` 与 `landing.py`

因此本 Slice 的关键不是发明新对象，而是先确认这五个 surface 是否真的只承接了各自应有的 contract 责任。

## Alignment categories

当前推荐先把观察到的差异压成四类，而不是直接下手改代码：

1. keep：runtime 与 contract 已一致，可直接保留
2. trim：runtime 当前暴露得比 contract 更宽，应先收窄
3. extend：contract 已要求，但 runtime surface 仍缺最小信号
4. rename：语义一致但命名或表述方式会造成 boundary 漂移

## Current inventory

### Keep

当前已经可以直接保留的部分：

1. `models.py` 用 tuple-based collection 与 frozen dataclass 保持 bridge primitive 的稳定观察面，这与 thin contract 的“纯 model / pure helper”方向一致
2. `projection.py`、`rollup.py`、`stop_conditions.py`、`landing.py` 当前都保持 pure helper / pure evaluator 风格，没有把 bridge 推成新的治理对象
3. `tests/test_runtime_orchestration.py` 与 `tests/test_runtime_orchestration_landing.py` 已经覆盖 models / projection / roll-up / stop-boundary / landing artifact 的最小 happy-path 与 guard-path

### Trim

当前需要明确收窄但不一定立刻改代码的部分：

1. `__init__.py` 与更高层 coordinator / adapter 只是调用入口，不应在本 gate 里被误当成 primary contract authority
2. alignment gate 当前不应顺手扩大到 `landing_dispatch.py` 的 consumer wiring 细节；它只在 landing-facing contract 发生变化时作为 secondary validation surface 使用

### Extend

当前最明显、且值得优先处理的缺口有两类：

1. Slice 2 contract 要求 group-item / work-item 至少能观察到 owner-facing delivery signal，但当前 runtime model 主要承载 governance-side projection，dispatch result 还没有回流到 bridge model surface
2. 当前测试已经覆盖 roll-up 与 landing artifact，但还没有一条明确以“contract/runtime conformance”为目标的窄测试，把 Slice 1-3 文档口径与现有 helper 行为绑在一起

### Rename

当前主要的命名漂移点有两类：

1. 文档里使用 `external-resolution clue`、`authority-transfer signal` 这类边界词，而 runtime helper 更偏向 `reason`、`rollup_surface_kind/state`、`boundary_kind`
2. landing artifact 使用 `reviewer_takeover`，consumer payload 使用 `review_intake`，两者语义连续，但在 alignment 文档里需要被明确写成同一条 runtime chain 的不同层名

## Targeted validation entry

当前推荐的最小验证入口是：

1. 主验证面：`tests/test_runtime_orchestration.py`
2. landing / external-resolution 相关补充面：`tests/test_runtime_orchestration_landing.py`
3. 只有当 conformance edit 触及 owner-facing delivery 语义时，才额外扩大到 `tests/test_runtime_orchestration_landing_consumers.py` 与 `tests/test_runtime_orchestration_landing_dispatch.py`

## Current recommendation

当前推荐的最小入口是：

1. 先在这五个文件上建立一张 contract/runtime 对齐清单
2. 当前第一优先级应放在 extend 类差异，尤其是 owner-facing delivery signal 是否需要最小回流到 bridge model surface
3. 把 targeted validation 入口收窄到当前已覆盖 runtime helper 的测试面，例如 `tests/test_runtime_orchestration.py` 与 `tests/test_runtime_orchestration_landing.py`

## Current status

当前已完成：

1. alignment authority surface 盘点
2. keep / trim / extend / rename 四类差异归类
3. targeted validation 入口收窄

当前下一步更适合进入 Slice 2，先选定第一条 conformance edit，而不是重新扩 scope。

## Out of scope

1. broader daemon queue / persistence / replay runtime
2. 新的 bridge lifecycle family
3. 新的 owner-surface adapter 设计
4. 直接实现 full daemon service