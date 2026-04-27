# 设计草案 — Orchestration Bridge Landing Integration Slice 1

本文是 `design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-landing-integration.md` 的 Slice 1 设计草案。

## 目标

当前只固定 external-resolution landing contract：

1. 输入来自 coordinator step result / stop decision
2. 当前只覆盖 `group_terminal` 与 `review_required` 两类边界
3. 输出是最小 landing artifact，供 handoff / reviewer takeover 消费

## 当前推荐

当前推荐按以下优先级映射：

1. `group_terminal` + `handoff` -> handoff landing artifact
2. `group_terminal` + `escalation` -> escalation landing artifact
3. `grouped_review` + `review_required` -> reviewer takeover landing artifact
4. `blocked` 与 `completed` 当前不生成 landing artifact

## 已固定的最小 artifact 字段

当前 contract 已固定 `BridgeLandingArtifact` 最小字段：

1. `landing_kind`
2. `work_item_id`
3. `active_scope`
4. `task_group_id`
5. `dominant_group_item_ids`
6. `reason`
7. `authoritative_refs`
8. `open_items`
9. `current_gate_state`
10. `intake_requirements`

## 已固定的 metadata 来源

当前 contract 已固定：

1. `group_terminal` 的 `authoritative_refs` / `open_items` / `current_gate_state` 先经 executor-result adapter 保留到 `BridgeGroupItem`
2. `review_required` 路径用 grouped review 的 `unresolved_items` 作为 `open_items`
3. `review_required` 当前默认落到 `current_gate_state = waiting_review` 与 `authoritative_refs = [AGENTS.md]`

## 当前判断

我当前判断这条 slice 值得优先，因为它最直接回答 coordinator 之后 bridge 是否能真正接出治理落点，而不需要提前引入 daemon runtime。