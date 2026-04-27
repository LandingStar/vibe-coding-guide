# 设计草案 — Orchestration Bridge Landing Dispatch Integration Slice 1

本文是 `design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-landing-dispatch-integration.md` 的 Slice 1 设计草案。

## 目标

当前只固定 landing dispatch contract：

1. `handoff` payload -> handoff delivery surface
2. `escalation` payload -> `EscalationNotifier.notify()`
3. `reviewer_takeover` payload -> waiting_review 对齐的 review entry surface

## 当前推荐

当前推荐固定以下 contract：

1. dispatch helper 输出统一的 success/failure result，而不是把底层 consumer 结果直接外泄到 bridge 上层
2. handoff 路径当前最小补齐为显式 handoff consumer protocol；不复用 handoff builder 的输入契约
3. reviewer_takeover 路径当前只要求对齐现有 review surface，不另起新 schema

## 当前判断

我当前判断这条 slice 值得优先，因为当前真正的结构缺口是 dispatch contract，而不是 artifact 或 payload shape。