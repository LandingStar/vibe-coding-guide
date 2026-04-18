---
handoff_id: 2026-04-16_1057_llmworker-live-payload-contract-hardening-gate-draft_stage-close
entry_role: canonical
kind: stage-close
status: superseded
scope_key: llmworker-live-payload-contract-hardening-gate-draft
safe_stop_kind: stage-complete
created_at: 2026-04-16T10:57:43+08:00
supersedes: 2026-04-16_1044_llm-live-payload-contract-hardening-direction-analysis_stage-close
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
  - design_docs/stages/planning-gate/2026-04-16-llmworker-live-payload-contract-hardening.md
  - design_docs/llm-live-payload-contract-hardening-direction-analysis.md
  - design_docs/direction-candidates-after-phase-35.md
  - review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md
  - docs/subagent-schemas.md
conditional_blocks:
  - dirty-worktree
other_count: 0
---

# Summary

在 `LLMWorker live payload contract hardening` 方向分析与 status policy 细化完成后，本轮继续把它收敛成了一个可审核的 planning-gate 草案：`design_docs/stages/planning-gate/2026-04-16-llmworker-live-payload-contract-hardening.md`。当前推荐边界已经固定为三项：收紧 prompt 枚举合同、只对低歧义 `content_type` 别名做 narrow normalization、以及在“LLM 主动尝试 payload 但所有 candidate 都被 output guard 拒绝”时把 report 从 `completed` 下调到 `partial`。当前 safe stop 已经从“方向分析完成”前推到“gate draft ready for review”，下一会话可以直接基于 gate 文本进入审核或实现前微调。

## Boundary

- 完成到哪里：已完成 `LLMWorker live payload contract hardening` 的 planning-gate 草案，并同步回高层状态面与 checkpoint。
- 为什么这是安全停点：当前已经有可审核 gate 文本，继续推进将进入 gate review 后的实现阶段；边界清晰且 authority docs 已同步。
- 明确不在本次完成范围内的内容：不实现 `src/workers/llm_worker.py` 代码修改，不修改 schema，不处理 `HTTPWorker`，不再扩大 dogfood。

## Authoritative Sources

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/stages/planning-gate/2026-04-16-llmworker-live-payload-contract-hardening.md`
- `design_docs/llm-live-payload-contract-hardening-direction-analysis.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md`
- `docs/subagent-schemas.md`

## Session Delta

- 本轮新增：
  - `design_docs/stages/planning-gate/2026-04-16-llmworker-live-payload-contract-hardening.md`
  - `.codex/handoffs/history/2026-04-16_1057_llmworker-live-payload-contract-hardening-gate-draft_stage-close.md`
- 本轮修改：
  - `design_docs/Project Master Checklist.md`
  - `design_docs/Global Phase Map and Current Position.md`
  - `design_docs/llm-live-payload-contract-hardening-direction-analysis.md`
  - `.codex/checkpoints/latest.md`
  - `.codex/handoffs/CURRENT.md`
- 本轮形成的新约束或新结论：
  - `allowed_artifacts` 只表达写回权限边界，不单独等于“必须产出 payload”。
  - 若 LLM 主动尝试 payload 且所有 candidate 被 output guard 拒绝，report 应降为 `partial`。
  - `content_type` 可做固定映射的无损别名收敛；`operation` 不对 `upsert` 做自动猜测。
  - 下一步实现范围已被 planning-gate 明确压缩为 prompt strengthening + narrow normalization + status downgrade。

## Verification Snapshot

- 自动化：无新增 pytest；本轮是 gate draft 与状态面同步，代码基线仍沿用上一切片的 942 passed, 2 skipped。
- 手测：已核对 direction analysis、planning-gate 草案、Checklist、Phase Map、checkpoint 与 CURRENT 的边界一致性。
- 未完成验证：尚未实现 gate 内代码改动，因此没有新的 worker-level 或 integration-level 回归。
- 仍未验证的结论：gate 中定义的 prompt strengthening、固定别名收敛与 status downgrade 组合落地后，live rerun 是否能稳定触发 artifact writeback。

## Open Items

- 未决项：对 `design_docs/stages/planning-gate/2026-04-16-llmworker-live-payload-contract-hardening.md` 做最终 review，并决定是否进入实现。
- 已知风险：当前 live `LLMWorker` 仍可能产生 payload drift；在 gate 未实施前，真实 writeback 仍可能只停留在 summary writeback。
- 不能默认成立的假设：不能默认 fixed alias normalization 就足以解决所有 live drift，也不能默认 `operation` semantic drift 可以安全自动纠正。

## Next Step Contract

- 下一会话建议只推进：审核并激活 `design_docs/stages/planning-gate/2026-04-16-llmworker-live-payload-contract-hardening.md`，随后只按 gate 实施 `src/workers/llm_worker.py` 与对应 tests 的窄改动。
- 下一会话明确不做：不要在 gate review 前直接进入 wider redesign，不要顺手改 `HTTPWorker`，也不要放宽 schema。
- 为什么当前应在这里停下：当前已到用户 review / approval 边界；再继续将直接越过 planning-gate 审核进入实现，不应混在同一 closeout 里。

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Why This Stage Can Close

- 当前大阶段到这里可以结束的原因：下一条主线已经从 analysis 收口为具体 gate draft，后续工作不再缺设计入口。
- 当前不继续把更多内容塞进本阶段的原因：实现工作必须在 gate review 之后按窄边界推进，否则容易把 policy / gate / code 改动混成一个未审核的大切片。

## Planning-Gate Return

- 应回到的 planning-gate 位置：`design_docs/stages/planning-gate/2026-04-16-llmworker-live-payload-contract-hardening.md`
- 下一阶段候选主线：`LLMWorker live payload contract hardening`（已起草 gate，默认推荐）；备选仍是 `HTTPWorker failure fallback schema alignment`。
- 下一阶段明确不做：不要跳过 gate review；不要把本轮 gate draft 直接视为已经进入实现。

## Conditional Blocks

### dirty-worktree

Trigger:
workspace 仍处于 dirty 状态，且当前 gate draft 文档/状态面与仓库中其他 pre-existing dirty changes 混在一起；下一会话若依赖 git diff，需要先区分当前 gate draft 相关文件与无关改动。

Required fields:

- Dirty Scope:
- Relevance to Current Handoff:
- Do Not Revert Notes:
- Need-to-Inspect Paths:
- Dirty Scope: 当前阶段新增/修改集中在 planning-gate 草案、方向分析、高层状态面、checkpoint 与 handoff；仓库中还存在大量本轮之外的 dirty changes。
- Relevance to Current Handoff: 当前 gate draft 是下一会话的主入口，其相关文件必须优先识别；其他 dirty paths 不能被误当作本轮 planning-gate 的实现内容。
- Do Not Revert Notes: 不要为了清树而回退 unrelated dirty changes，也不要覆盖当前 gate draft 与 handoff 相关的 `design_docs/`、`.codex/` 文件。
- Need-to-Inspect Paths: `design_docs/stages/planning-gate/2026-04-16-llmworker-live-payload-contract-hardening.md`、`design_docs/llm-live-payload-contract-hardening-direction-analysis.md`、`.codex/checkpoints/latest.md`、`.codex/handoffs/CURRENT.md`。

Verification expectation:
下一会话在进入实现前，应确认 gate draft 相关文件是当前边界，且其他 dirty paths 不是这条切片的一部分。

Refs:

- `design_docs/stages/planning-gate/2026-04-16-llmworker-live-payload-contract-hardening.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`

## Other

None.
