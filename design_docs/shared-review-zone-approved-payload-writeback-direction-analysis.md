# 方向分析 — Zone-Approved Payload Writeback After Shared-Review Zone Approval

## 背景

`design_docs/stages/planning-gate/2026-04-24-shared-review-zone-contract-and-preflight.md` 已完成，当前平台已经具备：

1. shared-review zone companion metadata
2. zone-driven preflight overlap 例外
3. merge/grouped review 的 `review_driver` 与 `shared_review_zone_ids`
4. grouped review writeback summary 对 zone driver 的可见性

这使下一条真正未决的语义问题变得具体：

- 当前 `WritebackEngine` 仍只允许 `grouped_review_outcome.outcome == all_clear` 时进入 grouped child payload writeback
- zone-driven child group 即使经过 reviewer `approve`，其 `grouped_review_outcome.outcome` 仍然是 `review_required`
- 因此“review 已批准的 shared-review zone”当前仍不会真正触发 payload writeback

如果 shared-review zone 不是只想停在“可审阅但不可落地”，那么这一点迟早要被明确。

## 当前判断

当前最重要的新事实不是 writeback engine 不稳定，而是：

1. shared-review zone 已经把 conflict-bearing path 重新接回 runtime
2. 但 approved terminal semantics 还停留在 `all_clear-only` 假设下
3. 因此下一步不是继续扩 contract/preflight，而是先收口“approved review 是否足以解锁 zone-driven writeback”

## 候选方向

### A. Reviewer approval unlocks zone-driven payload writeback（推荐）

做什么：

1. 保持 `grouped_review_outcome.outcome == review_required`
2. 但在 reviewer `approve` 之后，允许 zone-driven child payload 进入 writeback planning
3. writeback summary 需要明确记录：这是“review-approved zone writeback”，不是 `all_clear` 自动放行

优点：

1. 最符合 shared-review zone 的直觉用途
2. 不需要伪造 `all_clear`
3. 可以保留“自动放行”和“人工审批放行”两条清晰路径

风险：

1. 需要补一层 review terminal semantics
2. 需要明确 approved writeback 的审计口径与结果面字段

### B. Approval produces a second-stage resolved outcome object

做什么：

1. shared-review zone 的 `review_required` 经过 reviewer `approve` 后，不直接触发 writeback
2. 而是生成一份独立的 resolved bundle / approved merge artifact
3. writeback 只消费这个二阶段对象

优点：

1. 语义最清楚
2. 适合以后扩到更复杂的人工合并结果

风险：

1. 会显著增加对象和状态复杂度
2. 对当前平台来说偏早

### C. Keep all_clear-only forever

做什么：

1. 即使 reviewer approve，zone-driven path 也不进入 payload writeback
2. shared-review zone 只提供观察与审计，不提供落地能力

优点：

1. 最保守
2. 不需要改 writeback 语义

风险：

1. shared-review zone 的实用价值会非常有限
2. 人工批准却不能落地，用户心智会很拧巴

## 当前推荐

我当前倾向于优先走 **A. Reviewer approval unlocks zone-driven payload writeback**。

原因：

1. 这条路径最贴合当前 shared-review zone 已经建立起来的 contract/preflight/result surface。
2. 它不要求把 `review_required` 伪装成 `all_clear`，语义更干净。
3. 它能把当前平台从“可审阅”推进到“可在人工批准后真正落地”，这是 shared-review zone 成为真实能力的最小闭环。

## 当前建议的下一步

若继续推进，我建议下一步起一条新的 planning-gate，主题聚焦：

- `Zone-Approved Payload Writeback Semantics`

建议只覆盖：

1. review approve 后如何解锁 zone-driven payload writeback
2. 结果面 / 审计面如何表达 approval-driven writeback
3. 现有 `all_clear-only` 路径如何保持不回归

明确不做：

1. patch-level merge
2. 二阶段 resolved bundle 大对象
3. group 内 handoff / escalation