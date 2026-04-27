# Planning Gate — Zone-Approved Payload Writeback Semantics

> 日期: 2026-04-24
> 状态: COMPLETE
> 关联方向分析: `design_docs/shared-review-zone-approved-payload-writeback-direction-analysis.md`

## 1. Why this gate exists

shared-review zone 的最小 companion / result / summary surface 已完成，但当前 runtime 仍保留一个明显缺口：

- reviewer `approve` 之后，`Executor.apply_review_feedback()` 会进入 writeback
- 但 `WritebackEngine._plan_grouped_review_payloads()` 仍只接受 `grouped_review_outcome.outcome == all_clear`
- 因此 zone-driven `review_required` 即使已经被批准，也不会真正触发 grouped child payload writeback

这意味着 shared-review zone 目前只做到“可审阅”，还没做到“批准后可落地”。

## 2. Scope

本 gate 只处理：

1. review `approve` 后，zone-driven grouped review 是否允许进入 payload writeback
2. approval-driven writeback 需要哪些最小结果面 / summary / audit 语义
3. 现有 `all_clear-only` 自动写回路径如何保持不回归

本 gate 不处理：

1. patch-level merge
2. 新增第二套 resolved bundle / merge artifact object
3. group 内 handoff / escalation terminal semantics

## 3. Working hypothesis

当前最小可行路线应是：

1. 保持 `grouped_review_outcome.outcome == review_required`
2. 仅在 reviewer `approve` 且 `review_driver == shared_review_zone` 时，允许 grouped child payload writeback
3. summary / audit 明确标记这是 approval-driven writeback，而不是 `all_clear` 自动放行

## 4. Slices

### Slice 1 — Approval eligibility contract

- 定义 zone-approved payload writeback 的最小 eligibility 规则
- 让 writeback planning 能区分 `all_clear` 自动路径 与 `shared_review_zone + applied` 审批路径
- 补一条最小红绿测试覆盖这条 eligibility

当前状态：基础实现已落地到 `src/pep/writeback_engine.py` 与 `tests/test_pep_writeback_integration.py`；当前 grouped child payload writeback 已新增 `eligibility_basis`，并支持 `shared-review-zone-approved`。定向回归已通过。

### Slice 2 — Planning and summary alignment

- 让 grouped child payload planning 真正接受 zone-approved path
- 在 grouped child summary / grouped review summary 中保留 approval-driven reason
- 保持现有 `all_clear-only` 自动路径不回归

当前状态：planning / summary 对齐已落地到 `src/pep/writeback_engine.py`；writeback markdown summary 现已保留 grouped child writeback eligibility，既有 `all_clear` 路径回归已通过。

### Slice 3 — Audit / authority write-back

- 若实现中发现 audit detail 仍缺 approval-driven visibility，则补最小结果面
- 同步 authority docs / checklist / checkpoint / phase map

当前状态：当前先以 `grouped_child_writeback_summary.eligibility_basis` 作为 approval-driven visibility surface，并已同步 authority docs；若后续 dogfood 证明审计事件还不够，再单独补 audit 事件。

## 5. Validation gate

- 新增或更新窄测试：
  - shared-review-zone `review_required` 经 `approve` 后可进入 grouped payload writeback
  - 非 shared-review-zone 的 `review_required` 在 `approve` 后仍不会自动进入该路径
- 更广回归：
  - `tests/test_collaboration.py`
  - `tests/test_pep_writeback_integration.py`

## 6. Stop condition

- 当 approval-driven writeback eligibility、summary 对齐、以及最小回归都成立时停止
- 不在本 gate 内扩展到 patch merge 或 group 内 authority transfer