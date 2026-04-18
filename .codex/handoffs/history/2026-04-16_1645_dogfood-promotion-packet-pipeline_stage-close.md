---
handoff_id: 2026-04-16_1645_dogfood-promotion-packet-pipeline_stage-close
entry_role: canonical
kind: stage-close
status: superseded
scope_key: dogfood-promotion-packet-pipeline
safe_stop_kind: stage-complete
created_at: 2026-04-16T16:45:00+08:00
supersedes: 2026-04-16_1421_controlled-real-worker-payload-evidence-accumulation_stage-close
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
  - design_docs/dogfood-evidence-issue-feedback-boundary.md
  - design_docs/dogfood-promotion-packet-interface-draft.md
  - design_docs/stages/planning-gate/2026-04-16-dogfood-issue-promotion-feedback-packet-contract.md
  - design_docs/stages/planning-gate/2026-04-16-dogfood-promotion-packet-interface-draft.md
  - review/contract-dry-run/2026-04-16-promotion-packet-contract-dry-run.md
  - review/github-issue-quality/2026-04-16-dogfood-issue-standard-benchmark.md
  - design_docs/direction-candidates-after-phase-35.md
  - docs/first-stable-release-boundary.md
conditional_blocks:
  - phase-acceptance-close
  - dirty-worktree
other_count: 0
---

# Summary

`Dogfood Issue Promotion + Feedback Packet Pipeline` 已完成从 docs-only contract 到实现 + e2e 验证的完整链路。本切片沿 3 层递进执行：

1. **Boundary + Contract**：在 `dogfood-evidence-issue-feedback-boundary.md` 中定义了 issue promotion threshold（T1-T4 触发、S1-S3 抑制）、issue candidate 最小字段集（12 字段）、feedback packet minimum field set（9 必选 + 3 可选）、消费者边界矩阵（6 消费者 × 允许/禁止）和 3 条消费原则。外部 GitHub issue 质量 benchmark 和 contract dry-run 均已完成。
2. **Interface Draft**：在 `dogfood-promotion-packet-interface-draft.md` 中定义了 5 个数据结构（EvidenceRef、PromotionDecision、IssueCandidate、FeedbackPacket、ConsumerPayload）和 4 个函数签名（evaluate_promotion、build_issue_candidate、assemble_feedback_packet、dispatch_to_consumers），附完整数据流图。
3. **实现 + 测试**：在 `src/dogfood/` 下实现了 4 个模块（models.py、evaluator.py、builder.py、dispatcher.py），18 个测试全部通过（含 2 个真实 evidence e2e 测试），全量基线 964 passed, 2 skipped。

## Boundary

- 完成到哪里：完成了从 evidence 到 feedback packet 的完整 pipeline 实现和测试。所有 docs-only gate（boundary consolidation、contract definition、interface draft）已关闭。3 个 planning-gate 全部 DONE。
- 为什么这是安全停点：pipeline 的 4 个核心组件已实现并通过 e2e 测试。后续推进（如 pipeline 接入 workflow、持久化、CLI 集成）属于新的实现型 gate，不影响当前已完成的 contract + 实现闭环。
- 明确不在本次完成范围内：不接入现有 workflow（safe_stop_writeback.py、checkpoint 更新流程等）；不实现持久化（文件/DB/API）；不修改 runtime/schema/validator/workflow protocol；不处理 HTTPWorker live rerun；不扩大 adoption wording。

## Authoritative Sources

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/dogfood-evidence-issue-feedback-boundary.md`
- `design_docs/dogfood-promotion-packet-interface-draft.md`
- `design_docs/stages/planning-gate/2026-04-16-dogfood-issue-promotion-feedback-packet-contract.md`
- `design_docs/stages/planning-gate/2026-04-16-dogfood-promotion-packet-interface-draft.md`
- `review/contract-dry-run/2026-04-16-promotion-packet-contract-dry-run.md`
- `review/github-issue-quality/2026-04-16-dogfood-issue-standard-benchmark.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `docs/first-stable-release-boundary.md`

## Test Baseline

964 passed, 2 skipped (previously 946 passed, 2 skipped; +18 new tests)

## Next Directions

1. **Pipeline 接入 workflow**：将 dispatch_to_consumers 的输出接入 safe_stop_writeback.py 或 checkpoint 更新流程
2. **持久化层**：决定 IssueCandidate 和 FeedbackPacket 是否需要文件/DB 持久化
3. **HTTPWorker 独立受控 live rerun**：direction B 的前提条件
4. **更宽泛 dogfood repeatability evidence**：direction C 的继续积累

## Backlog Items Discovered

- B1: `environment` 字段对纯 wording/contract 类 issue 的填写已简化（回写完成）
- B2: `packet_id` 格式中 `{seq}` 计数器在无持久化时需人工管理（留后续组件化）
- B3: IssueCandidate 缺少 `status` 字段（留进入 issues/ 持久面后补充）
- O1-O4: interface draft 中的 4 个开放问题（持久化形态、LLM 辅助、写入控制、seq 计数器）

## Session Delta

- 本轮新增：`src/dogfood/__init__.py`、`src/dogfood/models.py`、`src/dogfood/evaluator.py`、`src/dogfood/builder.py`、`src/dogfood/dispatcher.py`、`tests/test_dogfood_pipeline.py`、`tests/test_dogfood_e2e.py`、`design_docs/dogfood-promotion-packet-interface-draft.md`、`review/contract-dry-run/2026-04-16-promotion-packet-contract-dry-run.md`、`review/github-issue-quality/2026-04-16-dogfood-issue-standard-benchmark.md`、`design_docs/stages/planning-gate/2026-04-16-dogfood-issue-promotion-feedback-packet-contract.md`、`design_docs/stages/planning-gate/2026-04-16-dogfood-promotion-packet-interface-draft.md`、本 canonical handoff。
- 本轮修改：`design_docs/dogfood-evidence-issue-feedback-boundary.md`（新增 4 个 contract 章节）、`design_docs/Project Master Checklist.md`、`design_docs/Global Phase Map and Current Position.md`、`design_docs/direction-candidates-after-phase-35.md`、`.codex/checkpoints/latest.md`、`.codex/handoffs/CURRENT.md`。
- 本轮形成的新约束或新结论：dogfood pipeline 的 promotion threshold（T1-T4 / S1-S3）、issue candidate 最小 12 字段、feedback packet 9+3 字段集与 6 消费者边界矩阵已写入权威 boundary doc 并通过实现验证。

## Verification Snapshot

- 自动化：18 项新增测试（16 单元 + 2 E2E）全部通过；全量回归基线 964 passed, 2 skipped；`design_docs/stages/planning-gate/2026-04-16-dogfood-issue-promotion-feedback-packet-contract.md` 6/6 验证门通过；`design_docs/stages/planning-gate/2026-04-16-dogfood-promotion-packet-interface-draft.md` 8/8 验证门通过。
- 手测：contract dry-run 在 3 条真实 evidence 上验证了 promote（2 条）和 suppress（1 条）路径，产出 `review/contract-dry-run/2026-04-16-promotion-packet-contract-dry-run.md`。
- 未完成验证：未接入 workflow（checkpoint / safe_stop_writeback.py 自动化）；未验证持久化层；未验证 CLI 集成。
- 仍未验证的结论：pipeline 当前是 in-memory 纯函数实现，未验证在真实 workflow 循环中的端到端行为。

## Open Items

- 未决项：下一条主线应在 `Pipeline 接入 workflow`、`持久化层`、`HTTPWorker 独立受控 live rerun` 与 `更宽泛 dogfood repeatability evidence` 之间收口。
- 已知风险：当前仓库仍是大范围 dirty worktree；pipeline 实现为纯函数 + frozen dataclass，暂无状态持久化。
- 不能默认成立的假设：不能默认 pipeline 已接入 workflow 自动循环；不能默认 IssueCandidate / FeedbackPacket 可直接持久化为文件；不能默认当前消费者边界矩阵在 runtime 集成后仍无需调整。

## Next Step Contract

- 下一会话建议只推进：在 `design_docs/direction-candidates-after-phase-35.md` 中选择下一方向并起草窄 scope planning-gate。
- 下一会话明确不做：不要直接修改 `src/workflow/`、`src/mcp/`、`src/pep/` 等已有 runtime 模块与 pipeline 的集成；不要在没有新 gate 的情况下扩展 `src/dogfood/` 的功能。
- 为什么当前应在这里停下：当前 slice 的核心交付（contract → implementation → test）已经完成，继续推进属于新的切片方向。

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Why This Stage Can Close

本 stage 可以关闭，因为 `Dogfood Issue Promotion / Feedback Packet Pipeline` 的完整交付链路已全部完成：

1. **Boundary + Contract 定义**：issue promotion threshold（T1-T4 / S1-S3）、issue candidate 12 字段、feedback packet 9+3 字段、消费者边界 6×矩阵和 3 条消费原则，全部写入权威 boundary doc 并通过 dry-run 验证。
2. **Interface Draft**：5 数据结构 + 4 函数签名 + 完整数据流图，gate 8/8 通过。
3. **实现 + 测试**：`src/dogfood/` 4 模块实现，18 项新测试（16 单元 + 2 E2E）全部通过，全量基线 964 passed, 2 skipped。

剩余工作（pipeline 接入 workflow、持久化、CLI 集成）属于新的方向选择，不影响当前交付的完整性。

## Planning-Gate Return

当前无活跃 planning-gate。上一个 gate `design_docs/stages/planning-gate/2026-04-16-dogfood-promotion-packet-interface-draft.md` 已 DONE。

## Conditional Blocks

### phase-acceptance-close

Trigger:
当前 handoff 对应的是 `Dogfood Issue Promotion / Feedback Packet Pipeline` 全链路完成后的 stage-close，该 slice 从 docs-only contract 出发，经过 dry-run 验证、interface draft、implementation、unit test 和 e2e test，最终进入 safe-stop writeback。

Required fields:

- Acceptance Basis: 3 个 planning-gate 全部 DONE（boundary consolidation 6/6、contract definition 6/6、interface draft 8/8）；`src/dogfood/` 4 模块实现完成；18 项新测试全部通过；全量基线 964 passed, 2 skipped。
- Automation Status: 全量 pytest 回归通过；contract dry-run 在 3 条真实 evidence 上验证了 promote 和 suppress 路径。
- Manual Test Status: E2E 测试使用真实 evidence ref（live-payload-rerun、evidence-accumulation、adoption-judgment）验证了完整 evaluate → build → assemble → dispatch 链路。
- Checklist/Board Writeback Status: `design_docs/Project Master Checklist.md`、`design_docs/Global Phase Map and Current Position.md`、`design_docs/direction-candidates-after-phase-35.md`、`.codex/checkpoints/latest.md` 与 `.codex/handoffs/CURRENT.md` 已同步到 completed-pipeline / no-active-planning-gate 的 safe-stop 状态。

Verification expectation:
接手方应把本 handoff 视为 pipeline 交付完成的正式收口，后续推进属于新方向选择，而不是当前 slice 的延续。

Refs:

- `design_docs/stages/planning-gate/2026-04-16-dogfood-issue-promotion-feedback-packet-contract.md`
- `design_docs/stages/planning-gate/2026-04-16-dogfood-promotion-packet-interface-draft.md`
- `design_docs/dogfood-evidence-issue-feedback-boundary.md`
- `design_docs/dogfood-promotion-packet-interface-draft.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/direction-candidates-after-phase-35.md`

### dirty-worktree

Trigger:
当前仓库仍存在大范围 dirty worktree，且其中只有一部分属于本 completed slice 与 safe-stop 轮换直接相关。

Required fields:

- Dirty Scope: 当前 dirty 范围覆盖 `.codex/`、`design_docs/`、`docs/`、`review/`、`src/`、`tests/` 等多处既有修改与新增文件；本 handoff 直接相关的主要是 `src/dogfood/`、`tests/test_dogfood_*.py`、design docs、review docs、gates、Checklist、Phase Map、direction-candidates、checkpoint 与 handoff 文件。
- Relevance to Current Handoff: 当前 handoff 只对 `Dogfood Issue Promotion / Feedback Packet Pipeline` 的完成态收口和 safe-stop 轮换负责。
- Do Not Revert Notes: 不要为了清理 worktree 回滚与本 slice 无关的预存改动。
- Need-to-Inspect Paths: `src/dogfood/`、`tests/test_dogfood_pipeline.py`、`tests/test_dogfood_e2e.py`、`.codex/handoffs/history/2026-04-16_1645_dogfood-promotion-packet-pipeline_stage-close.md`、`.codex/handoffs/CURRENT.md`、`.codex/checkpoints/latest.md`。

Verification expectation:
下一会话开始前，应先核对哪些改动属于当前 safe-stop 入口，哪些只是并存的仓库脏状态。

Refs:

- `.codex/handoffs/history/2026-04-16_1645_dogfood-promotion-packet-pipeline_stage-close.md`
- `.codex/handoffs/CURRENT.md`
- `.codex/checkpoints/latest.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`

## Other

None.
