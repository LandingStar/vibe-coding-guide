# Orchestration Bridge Landing Integration Direction Analysis

## 背景

`design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-coordinator-glue.md` 已完成：

1. minimal coordinator step contract 已固定
2. coordinator helper 已落地到 `src/runtime/orchestration/coordinator.py`
3. `tests/test_runtime_bridge.py` + `tests/test_runtime_orchestration.py` + `tests/test_runtime_orchestration_adapter.py` + `tests/test_runtime_orchestration_coordinator.py` 联合回归已通过（29 passed）

因此当前主线已经不再是“helper 链能否闭环”，而是“`waiting_external_resolution` 如何接到真正的 landing surface”。

## 候选 A. landing integration over external-resolution boundary

- 做什么：围绕 `waiting_external_resolution`，把 `group_terminal` / `review_required` stop boundary 接到 handoff / reviewer takeover 的 landing artifact contract
- 依据：
  - [src/runtime/orchestration/coordinator.py](src/runtime/orchestration/coordinator.py)
  - [src/runtime/orchestration/stop_conditions.py](src/runtime/orchestration/stop_conditions.py)
  - [docs/specs/handoff.schema.json](docs/specs/handoff.schema.json)
- 风险：中。
- 当前判断：**推荐**。因为 coordinator 已证明最小闭环成立，下一步最接近真实价值的是把 external-resolution boundary 接到真实治理落点。

## 候选 B. daemon queue / persistence runtime

- 做什么：继续往 queue、persistence、replay runtime 推进
- 依据：
  - [design_docs/orchestration-bridge-daemon-layer-direction-analysis.md](design_docs/orchestration-bridge-daemon-layer-direction-analysis.md)
  - [review/multica/02-direction-and-weaknesses.md](review/multica/02-direction-and-weaknesses.md)
- 风险：高。
- 当前判断：长期成立，但当前优先级低于候选 A。

## 候选 C. richer multi-step coordinator runtime

- 做什么：继续在当前 pure coordinator 之上叠更多状态推进与历史追踪
- 依据：
  - [src/runtime/orchestration/coordinator.py](src/runtime/orchestration/coordinator.py)
  - [src/runtime/orchestration/models.py](src/runtime/orchestration/models.py)
- 风险：中。
- 当前判断：可以保留，但当前信息增益不如直接接 landing surface。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. models、helpers、adapter、coordinator 都已经成立
2. 当前最接近真实治理价值的空洞，是 external-resolution boundary 还没有 landing surface
3. 直接把 `waiting_external_resolution` 接到 handoff / reviewer takeover，能比继续堆 runtime state 更快证明 bridge 这条线是否真正可用