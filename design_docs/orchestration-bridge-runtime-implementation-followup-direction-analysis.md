# Orchestration Bridge Runtime Implementation Follow-Up Direction Analysis

## 背景

`design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-runtime-primitives.md` 已完成 docs-only 收口：

1. `src/runtime/orchestration/` 的模块边界已固定
2. `BridgeWorkItem` / `BridgeGroupItem` 的 runtime model contract 已固定
3. `project_group_item_surface()` / `roll_up_work_item()` / `evaluate_stop_condition()` 的 helper surface 与 targeted tests boundary 已固定

因此当前主线已经不再是“runtime primitive 还缺哪块设计”，而是“应该先落哪一层代码”。

## 候选 A. models + pure helpers 先落地

- 做什么：先实现 `models.py`、`projection.py`、`rollup.py`、`stop_conditions.py` 与 `tests/test_runtime_orchestration.py`，全部保持 pure model / pure helper 边界
- 依据：
  - [design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-runtime-primitives.md](design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-runtime-primitives.md)
  - [design_docs/orchestration-bridge-runtime-primitives-slice2-model-helper-contract-draft.md](design_docs/orchestration-bridge-runtime-primitives-slice2-model-helper-contract-draft.md)
  - [design_docs/orchestration-bridge-runtime-primitives-slice3-stop-evaluator-tests-draft.md](design_docs/orchestration-bridge-runtime-primitives-slice3-stop-evaluator-tests-draft.md)
- 风险：中低。
- 当前判断：**推荐**。因为它最贴近当前 contract，同时不要求立刻绑定 queue/persistence/landing integration。

## 候选 B. 先做 landing integration adapter

- 做什么：围绕 `waiting_external_resolution` 先做 handoff / reviewer takeover 的落地 adapter
- 依据：
  - [design_docs/orchestration-bridge-runtime-primitives-slice3-stop-evaluator-tests-draft.md](design_docs/orchestration-bridge-runtime-primitives-slice3-stop-evaluator-tests-draft.md)
  - [docs/specs/handoff.schema.json](docs/specs/handoff.schema.json)
- 风险：中。
- 当前判断：有价值，但优先级低于候选 A，因为当前 helper 层还未落代码，先接 landing adapter 会让依赖方向倒过来。

## 候选 C. 先做 daemon queue/persistence skeleton

- 做什么：直接把 orchestration bridge 推到 daemon service、queue persistence、recovery skeleton
- 依据：
  - [design_docs/orchestration-bridge-daemon-layer-direction-analysis.md](design_docs/orchestration-bridge-daemon-layer-direction-analysis.md)
  - [review/multica/02-direction-and-weaknesses.md](review/multica/02-direction-and-weaknesses.md)
- 风险：高。
- 当前判断：长期仍成立，但现在进入会把尚未证明的 helper contract 一起绑进持久化语义，时机过早。

## 当前 AI 倾向判断

我当前倾向于直接进入 **候选 A**。

原因是：

1. 当前 docs gate 已经把最小 helper contract 压成了可落代码状态
2. 最值得新增的信息，已经变成这些 pure models/helpers 能否通过 targeted tests 稳定成立
3. 如果 helper 层都还没落地，就继续向 landing/daemon 扩展会放大回退成本

因此，下一条 planning-gate 更适合聚焦：

1. 在 `src/runtime/orchestration/` 中新增 runtime models
2. 新增 projection / roll-up / stop-condition helper
3. 新增 `tests/test_runtime_orchestration.py` 做 targeted validation