# Orchestration Bridge Post-Landing Direction Analysis

## 背景

`design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-landing-integration.md` 已完成：

1. external-resolution landing contract 已固定
2. landing helper 已落地到 `src/runtime/orchestration/landing.py`
3. `tests/test_runtime_bridge.py` + `tests/test_runtime_orchestration.py` + `tests/test_runtime_orchestration_adapter.py` + `tests/test_runtime_orchestration_coordinator.py` + `tests/test_runtime_orchestration_landing.py` 联合回归已通过（33 passed）

因此当前主线已经不再是“boundary 是否能产出 landing artifact”，而是“这些 artifact 下一步最值得先接到哪种真实 consumer”。

## 候选 A. landing consumer wiring over existing handoff/review surfaces

- 做什么：把 `BridgeLandingArtifact` 接到现有 handoff / reviewer takeover consumer surface，先形成最小可消费闭环，而不是只停在 artifact
- 依据：
  - [src/runtime/orchestration/landing.py](src/runtime/orchestration/landing.py)
  - [src/collaboration/handoff_mode.py](src/collaboration/handoff_mode.py)
  - [docs/specs/handoff.schema.json](docs/specs/handoff.schema.json)
- 风险：中。
- 当前判断：**推荐**。因为当前最直接的真实价值空洞，是 landing artifact 还没有被实际 consumer 接住。

## 候选 B. daemon queue / persistence runtime

- 做什么：继续往 queue、persistence、replay runtime 推进
- 依据：
  - [design_docs/orchestration-bridge-daemon-layer-direction-analysis.md](design_docs/orchestration-bridge-daemon-layer-direction-analysis.md)
  - [review/multica/02-direction-and-weaknesses.md](review/multica/02-direction-and-weaknesses.md)
- 风险：高。
- 当前判断：长期成立，但当前优先级低于候选 A。

## 候选 C. richer coordinator / landing history runtime

- 做什么：继续在 coordinator / landing 之间叠更多状态历史、artifact 跟踪与重试语义
- 依据：
  - [src/runtime/orchestration/coordinator.py](src/runtime/orchestration/coordinator.py)
  - [src/runtime/orchestration/landing.py](src/runtime/orchestration/landing.py)
- 风险：中。
- 当前判断：可以保留，但默认优先级低于候选 A。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. models、adapter、coordinator、landing artifact 都已经成立
2. 当前最关键的未知数已经不再是 artifact shape，而是 artifact 能否被现有 handoff / reviewer surface 真正消费
3. 先接 consumer 的信息增益，高于直接进入 daemon runtime 或继续堆 bridge-only state