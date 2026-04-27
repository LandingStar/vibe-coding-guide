# Planning Gate — Orchestration Bridge Runtime Primitives

> 日期: 2026-04-26
> 状态: COMPLETE
> 关联方向分析: `design_docs/orchestration-bridge-contract-runtime-followup-direction-analysis.md`

## 1. Why this gate exists

`design_docs/stages/planning-gate/2026-04-25-orchestration-bridge-work-item-group-item-contract.md` 已完成 docs-only 收口。

这意味着当前关于 orchestration bridge 的最小 contract 已经明确：

1. `BridgeWorkItem` / `BridgeGroupItem` 的 primitive 与 ownership boundary 已固定
2. group-item projection、work-item roll-up 与 stop-condition boundary 已写清
3. 当前最值得新增的信息，已经变成“这些 contract 能否下压为最小 runtime primitive”

但当前代码面暴露出一个新的第一顺位结构约束：

- `src/runtime/bridge.py` 已经被 `RuntimeBridge` 占用，并且是 CLI 等入口的宿主桥接 facade

因此，下一条最窄 planning-gate 不能直接跳进 runtime 实现细节，而应先固定：

1. orchestration bridge runtime primitive 应挂在哪个模块面
2. 它如何与现有 `RuntimeBridge` 语义隔离
3. 在模块边界固定后，再进入 pure model / helper 的窄实现

## 2. Scope

本 gate 只处理：

1. orchestration bridge runtime primitive 的模块/命名边界
2. `BridgeWorkItem` / `BridgeGroupItem` runtime model 的最小 contract
3. group-item projection / work-item roll-up / stop-condition evaluation helper 的最小 helper surface 与测试边界

本 gate 不处理：

1. daemon service / queue persistence / replay runtime
2. `waiting_external_resolution` 之后的 landing integration
3. executor 内部重构或现有 `RuntimeBridge` 的宿主入口职责变更

## 3. Working hypothesis

当前最小可行路线应是：

1. 保持 `src/runtime/bridge.py` 继续只承载 host-entry `RuntimeBridge`
2. 为 orchestration bridge runtime primitive 单独开一个隔离的模块面
3. 先落 pure model / pure helper，再考虑更高层的 bridge runtime orchestration

## 4. Slices

### Slice 1 — Runtime surface isolation

- 固定 orchestration bridge runtime primitive 的模块边界与命名边界
- 明确为什么不能把新 primitive 继续塞进 `src/runtime/bridge.py`
- 固定最小 public symbol surface

当前状态：Slice 1 设计草案已创建为 `design_docs/orchestration-bridge-runtime-primitives-slice1-surface-isolation-draft.md`；当前已把 `RuntimeBridge` 与 orchestration bridge primitive 的 module boundary、子包布局与最小 public symbol surface 写清。当前下一窄切口收束为：进入 Slice 2，固定 `models.py` / `projection.py` / `rollup.py` / `stop_conditions.py` 的 runtime contract。

### Slice 2 — Runtime models + projection / roll-up helper contract

- 固定 `BridgeWorkItem` / `BridgeGroupItem` 的 runtime model 形态
- 固定 group-item projection / work-item roll-up helper 的纯函数边界
- 明确 helper 输入输出如何对齐前一条 docs-only gate

当前状态：Slice 2 设计草案已创建为 `design_docs/orchestration-bridge-runtime-primitives-slice2-model-helper-contract-draft.md`；当前已把 `models.py` 的字段合同、optional dispatch-lineage 字段、以及 `projection.py` / `rollup.py` 的 pure helper signature 写清。当前下一窄切口收束为：进入 Slice 3，固定 `stop_conditions.py` evaluator contract 与 targeted tests boundary。

### Slice 3 — Stop-condition evaluator + targeted tests boundary

- 固定 stop-condition evaluator 的 helper surface
- 固定 targeted tests 的最小覆盖面
- 明确这一层仍然不进入 daemon runtime / queue persistence

当前状态：Slice 3 设计草案已创建为 `design_docs/orchestration-bridge-runtime-primitives-slice3-stop-evaluator-tests-draft.md`；当前已把 `evaluate_stop_condition()` 的结果对象、boundary matrix 与 `tests/test_runtime_orchestration.py` 的 targeted tests boundary 写清。当前下一步更适合回看 Slice 1-3 是否足以支撑当前 gate close，而不是继续扩写 runtime 设计。

## 5. Validation gate

- 文档验证：
  - 能清楚回答为什么 orchestration bridge primitive 不能直接落在 `src/runtime/bridge.py`
  - 能清楚回答 `RuntimeBridge` 与 orchestration bridge runtime primitive 各自负责什么
  - 能清楚回答后续代码应先落 pure model / helper，而不是 daemon service
  - 能清楚回答哪些 runtime 字段在 `prepared` / `queued` 阶段必须允许为 `None`
- 未来代码验证：
  - 新增 runtime primitive 后不需要重命名或打破现有 `RuntimeBridge` 入口
  - helper 层可以在不改写现有 governance kernel schema 的前提下被测试

## 6. Stop condition

- 当模块边界、runtime model contract、helper surface 与 targeted tests boundary 已被写清后停止
- 不在本 gate 内直接进入 daemon runtime / landing integration

## 7. Close note

当前 gate 的 Slice 1-3 都已形成独立草案，并已把 module boundary、runtime models、pure helper contract 与 targeted tests boundary 写清。下一步不再继续扩写本 gate，而是更适合转入代码实现 follow-up。