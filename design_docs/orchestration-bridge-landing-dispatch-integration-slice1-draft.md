# 设计草案 — Orchestration Bridge Landing Dispatch Integration Slice 1

本文是 `design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-landing-dispatch-integration.md` 的 Slice 1 设计草案。

## 目标

当前只固定 landing dispatch contract：

1. `handoff` payload -> handoff delivery surface
2. `escalation` payload -> `EscalationNotifier.notify()`
3. `reviewer_takeover` payload -> waiting_review 对齐的 review entry surface

## 当前已确认的 owner surface

1. `src/runtime/orchestration/landing_consumers.py` 已把 `BridgeLandingArtifact` 规范化为 `handoff`、`escalation_notification`、`review_intake` 三类 consumer payload；Slice 1 不再重做 payload shape。
2. `handoff` 路径当前只有“已通过 validator 的 handoff payload”，还没有真正的 delivery protocol；现有 `src/collaboration/handoff_mode.py` 是 worker-owned fire-and-transfer 入口，不应直接复用为 landing dispatch surface。
3. `escalation` 路径已有明确 owner：`src/interfaces.py` 中的 `EscalationNotifier.notify(notification: dict) -> dict`。
4. `reviewer_takeover` 路径最接近的现有 owner 不是新 schema，而是现有 `waiting_review` result / `src/review/feedback_api.py` 的 pending review store；当前 `review_intake` payload 与该 surface 之间仍缺一个很薄的 intake adapter。

## 当前推荐

当前推荐固定以下 contract：

1. dispatch helper 输出统一的 success/failure result，而不是把底层 consumer 结果直接外泄到 bridge 上层
2. handoff 路径当前最小补齐为显式 handoff consumer protocol；不复用 handoff builder 的输入契约
3. reviewer_takeover 路径当前只要求对齐现有 review surface，不另起新 schema

## Slice 1 定稿合同

### 1. Dispatch 输入边界

1. Slice 2 的 dispatch helper 直接消费 `BridgeLandingConsumerPayload`，不再重新读取 `BridgeLandingArtifact`。
2. `build_landing_consumer_payload(...)` 继续作为唯一 payload normalizer；dispatch 层只负责 delivery，不再改写 payload 结构。

### 2. Delivery owner mapping

1. `consumer_kind == "handoff"`
	- 目标 surface：新的显式 handoff consumer callable / protocol
	- 输入：已通过 `handoff_validator` 校验的最终 handoff payload
	- 约束：不调用 `handoff_mode.execute()`，因为该入口会重新执行 worker 并重新生成 handoff，不符合 landing dispatch 的“已产出 payload 再投递”语义
2. `consumer_kind == "escalation_notification"`
	- 目标 surface：`EscalationNotifier.notify(notification)`
	- 输入：现有 escalation notification payload
	- 约束：直接保留 notifier 的现有 owner，不在 bridge 层重新发明 escalation schema
3. `consumer_kind == "review_intake"`
	- 目标 surface：薄的 review-intake adapter，再落到现有 `waiting_review` / `FeedbackAPI` 对齐 surface
	- 输入：现有 review intake payload
	- 约束：不引入新的 review schema；只负责把 bridge payload 变成可登记、可列入 pending review 的最小 review entry

### 3. Unified delivery result

dispatch helper 的统一返回面固定为一个 plain dict，至少包含：

1. `delivered: bool`
2. `consumer_kind: str`
3. `target_surface: str`
4. `record_id: str | None`（例如 `handoff_id` 或 `review_object_id`）
5. `detail: str`
6. `consumer_result: dict`（底层 owner surface 的原始返回）

当前判断：这层 wrapper 已足够支撑 bridge 上层判断 success/failure，而不需要在 Slice 1 先引入 dataclass result。

## Slice 2 入口已固定

进入实现时，当前只需要补三样东西：

1. 显式 handoff consumer protocol
2. review-intake adapter
3. 一个统一调用三类 owner surface 并返回上方 result contract 的最小 dispatch helper

## 当前判断

我当前判断这条 slice 值得优先，因为当前真正的结构缺口是 dispatch contract，而不是 artifact 或 payload shape。