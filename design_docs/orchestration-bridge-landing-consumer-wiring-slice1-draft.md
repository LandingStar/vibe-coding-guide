# 设计草案 — Orchestration Bridge Landing Consumer Wiring Slice 1

本文是 `design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-landing-consumer-wiring.md` 的 Slice 1 设计草案。

## 目标

当前只固定 landing artifact 到现有 consumer surface 的映射：

1. `handoff` -> 正式 Handoff payload
2. `escalation` -> escalation notifier payload
3. `reviewer_takeover` -> waiting_review 对齐的最小 review intake payload

## 当前推荐

当前推荐固定以下 contract：

1. `handoff` payload 必须能通过现有 handoff validator
2. `escalation` payload 先落到 `EscalationNotifier.notify()` 可消费的 notification dict
3. `reviewer_takeover` payload 先提供 `review_state = waiting_review`、`gate_level = review`、`allowed_feedback` 等最小字段，供现有 review surface 消费

## 当前判断

我当前判断这条 slice 值得优先，因为它最直接回答 landing artifact 是否能接到真实 consumer surface，而不需要提前进入 daemon/runtime。