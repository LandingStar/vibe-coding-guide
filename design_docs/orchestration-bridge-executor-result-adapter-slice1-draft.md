# 设计草案 — Orchestration Bridge Executor Result Adapter Slice 1

本文是 `design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-executor-result-adapter.md` 的 Slice 1 设计草案。

## 目标

当前只固定 adapter contract：

1. 输入来自 `Executor.execute()` 的 dict execution result
2. 输出是 `project_group_item_surface()` 需要的 normalized fields
3. 当前不直接绑定 `GroupedReviewOutcome` / `GroupTerminalOutcome` dataclass object

## 当前推荐的输入面

当前推荐 adapter 只读取：

- `grouped_review_outcome`
- `group_terminal_outcome`
- `grouped_review_state`

并按以下优先级归一化：

1. 若存在 `group_terminal_outcome`，优先投影为 `group_terminal`
2. 否则若存在 `grouped_review_outcome`，投影为 `grouped_review`
3. 若二者都不存在但 execution result 已 blocked，投影为 `blocked`
4. 否则保持 `none`

## 当前推荐

我当前推荐：

1. Slice 1 先把 serialized dict result 视为唯一输入面
2. Slice 2 再把这个 contract 落成 adapter helper
3. 当前不回退到 executor 内部 dataclass object，避免把 adapter 绑死在内部构造路径上