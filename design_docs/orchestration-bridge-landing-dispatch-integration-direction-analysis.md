# Orchestration Bridge Landing Dispatch Integration Direction Analysis

## 背景

`design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-landing-consumer-wiring.md` 已完成：

1. `BridgeLandingArtifact` 已能映射到现有 consumer payload
2. `handoff` 已能复用正式 Handoff schema 并通过 validator
3. `escalation` 与 `reviewer_takeover` 已能落到 notifier / waiting_review 对齐的 payload surface
4. `tests/test_runtime_bridge.py` + 全部 orchestration tests 联合回归已通过（36 passed）

因此当前主线已经不再是“artifact 是否能映射到 consumer payload”，而是“这些 payload 如何进入真正的 dispatch/delivery surface”。

## 候选 A. landing dispatch integration over existing delivery surfaces

- 做什么：定义并实现一个最小 dispatch integration helper，把 handoff payload、escalation notification、review intake payload 接到现有 validator/notifier/review entry surface
- 依据：
  - [src/runtime/orchestration/landing_consumers.py](src/runtime/orchestration/landing_consumers.py)
  - [src/collaboration/handoff_mode.py](src/collaboration/handoff_mode.py)
  - [src/review/feedback_api.py](src/review/feedback_api.py)
  - [src/interfaces.py](src/interfaces.py)
- 风险：中。
- 当前判断：**推荐**。因为当前真正的结构缺口已经不是 payload shape，而是缺统一 dispatch protocol。

## 候选 B. daemon queue / persistence runtime

- 做什么：继续往 queue、persistence、replay runtime 推进
- 依据：
  - [design_docs/orchestration-bridge-daemon-layer-direction-analysis.md](design_docs/orchestration-bridge-daemon-layer-direction-analysis.md)
  - [review/multica/02-direction-and-weaknesses.md](review/multica/02-direction-and-weaknesses.md)
- 风险：高。
- 当前判断：长期成立，但当前优先级低于候选 A。

## 候选 C. richer landing history runtime

- 做什么：继续叠更多 landing artifact 历史、重试与 replay 语义
- 依据：
  - [src/runtime/orchestration/landing.py](src/runtime/orchestration/landing.py)
  - [src/runtime/orchestration/landing_consumers.py](src/runtime/orchestration/landing_consumers.py)
- 风险：中。
- 当前判断：可保留，但默认优先级低于候选 A。

## 当前 AI 倾向判断

我当前倾向于优先进入 **候选 A**。

原因是：

1. payload shape 已经成立，当前最缺的是 delivery contract
2. 不先补 dispatch protocol，就无法判断 bridge landing 这条线能否真正接入现有系统
3. 直接跳 daemon/runtime 会把 delivery 缺口一起放大