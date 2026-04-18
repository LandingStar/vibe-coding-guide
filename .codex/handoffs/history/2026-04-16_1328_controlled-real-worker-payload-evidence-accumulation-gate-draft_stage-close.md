---
handoff_id: 2026-04-16_1328_controlled-real-worker-payload-evidence-accumulation-gate-draft_stage-close
entry_role: canonical
kind: stage-close
status: superseded
scope_key: controlled-real-worker-payload-evidence-accumulation-gate-draft
safe_stop_kind: stage-complete
created_at: 2026-04-16T13:28:00+08:00
supersedes: 2026-04-16_1315_real-worker-payload-adoption-judgment_stage-close
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
  - design_docs/stages/planning-gate/2026-04-16-controlled-real-worker-payload-evidence-accumulation.md
  - design_docs/controlled-real-worker-payload-evidence-accumulation-direction-analysis.md
  - review/real-worker-payload-adoption-judgment-2026-04-16.md
  - docs/first-stable-release-boundary.md
  - design_docs/direction-candidates-after-phase-35.md
conditional_blocks:
  - phase-acceptance-close
  - dirty-worktree
other_count: 0
---

# Summary

在完成 `Real-Worker Payload Adoption Judgment` 之后，当前已根据用户选择把下一主线 A 收敛成新的 planning-gate 草案：`design_docs/stages/planning-gate/2026-04-16-controlled-real-worker-payload-evidence-accumulation.md`。这条 gate 现在已经同时收紧了三条关键边界：失败时只记录 signal、不回到 runtime hardening；artifact 目标固定为临时目录中的单一预置 markdown 文件更新；即使第二条 success 到手，wording ceiling 也只允许提升到“受控 real-worker payload path 已具备最小可重复 dogfood 能力”。当前剩余的主要 review 点，已经收口到“这个 ceiling 是否足够保守且可执行”。本次 safe stop 的边界仍是“gate draft ready for review”。

## Boundary

- 完成到哪里：已完成下一方向 A 的 direction confirmation、planning-gate 草案写作，以及 Checklist / Phase Map / direction candidates 的 gate review 边界同步。
- 为什么这是安全停点：下一步尚未进入执行态，而是明确停在 gate review；当前不会出现“半条 rerun 已开始但证据未归档”的中间态。
- 明确不在本次完成范围内的内容：不执行 rerun；不修改 runtime code、schema 或 `HTTPWorker`；不实现 dogfood evidence / issue / feedback integration 组件或 skill。

## Authoritative Sources

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/stages/planning-gate/2026-04-16-controlled-real-worker-payload-evidence-accumulation.md`
- `design_docs/controlled-real-worker-payload-evidence-accumulation-direction-analysis.md`
- `review/real-worker-payload-adoption-judgment-2026-04-16.md`
- `docs/first-stable-release-boundary.md`
- `design_docs/direction-candidates-after-phase-35.md`

## Session Delta

- 本轮新增：`design_docs/stages/planning-gate/2026-04-16-controlled-real-worker-payload-evidence-accumulation.md`，以及本 canonical handoff 草案。
- 本轮修改：`design_docs/Project Master Checklist.md`、`design_docs/Global Phase Map and Current Position.md`、`design_docs/direction-candidates-after-phase-35.md`。
- 本轮形成的新约束或新结论：下一条主线已被严格限定为“1 次额外且独立的受控 rerun”；若失败，本轮只记录 signal，不在同一切片里追加实现修复；artifact 目标固定为 `allowed_artifacts=["docs/controlled-dogfood-llm.md"]`，且语义限定为临时目录中的现有 markdown 文件更新；若再次成功，wording ceiling 最多只提升到“受控 real-worker payload path 已具备最小可重复 dogfood 能力”。

## Verification Snapshot

- 自动化：新 gate 文档与状态面文档无错误；`mcp_doc-based-cod_coupling_check` 对本轮变更返回 `alerts=[]`。
- 手测：无；当前停点仍处于 gate review 边界，尚未进入 rerun 执行。
- 未完成验证：本 gate 的核心验证动作，也就是额外 1 条独立受控 live rerun，尚未执行。
- 仍未验证的结论：当前仍未验证正向 signal 的最小可重复性。

## Open Items

- 未决项：在失败态边界、artifact 边界与 success 后 wording ceiling 都已写入 gate 后，继续 review 该 ceiling 是否足够保守且可执行。
- 已知风险：当前仓库 dirty worktree 很大；若下一会话不按 gate 文本行事，容易把本轮 rerun 验证重新扩成 runtime hardening。
- 不能默认成立的假设：不能默认第二条 signal 会成功；不能默认一旦成功就等于默认稳定面；不能默认 dogfood 组件/skill 已进入实施优先级。

## Next Step Contract

- 下一会话建议只推进：继续 review 并确认这条 planning-gate 草案，优先确认 success 后 wording ceiling 是否接受；若确认，则按 gate 执行 1 条额外且独立的受控 live rerun。
- 下一会话明确不做：不要提前运行第二条或更多 rerun；不要在 review 阶段直接改 runtime；不要把 dogfood 组件/skill backlog 混入同一切片。
- 为什么当前应在这里停下：当前最合适的停点就是 gate review，本轮已经把执行边界写清楚，再往前走就会越过审核节点。

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Why This Stage Can Close

- 当前大阶段到这里可以结束的原因：下一主线已经从方向选择收口到具体 planning-gate，恢复入口足够明确。
- 当前不继续把更多内容塞进本阶段的原因：再往前就是新的执行切片，而不是当前 gate 起草阶段的工作。

## Planning-Gate Return

- 应回到的 planning-gate 位置：`design_docs/stages/planning-gate/2026-04-16-controlled-real-worker-payload-evidence-accumulation.md`
- 下一阶段候选主线：优先执行 `controlled real-worker payload evidence accumulation`；正交备选仍是 `HTTPWorker failure fallback schema alignment`。
- 下一阶段明确不做：不重新打开 adoption judgment 文档重写；不直接扩大 stable wording；不在无新证据时追加实现改动。

## Conditional Blocks

### phase-acceptance-close

Trigger:
当前 handoff 表示新的 planning-gate 草案已经起好并切回 review 边界，因此必须确认 gate 文本与状态板已经同步，避免下一会话从错误入口恢复。

Required fields:

- Acceptance Basis: `design_docs/stages/planning-gate/2026-04-16-controlled-real-worker-payload-evidence-accumulation.md` 已明确写出范围、非目标、验证门与收口判断。
- Automation Status: gate 文档与状态面文档均无错误；`mcp_doc-based-cod_coupling_check` 返回无 alerts。
- Manual Test Status: 当前仍为 gate review 边界，无新增手测。
- Checklist/Board Writeback Status: `Project Master Checklist`、`Global Phase Map`、`direction-candidates-after-phase-35` 已同步到新的 gate review 边界。

Verification expectation:
当前需要的只剩用户对 gate 边界的 review 或收紧；这不阻塞本 handoff 作为 review safe stop 成立。

Refs:

- `design_docs/stages/planning-gate/2026-04-16-controlled-real-worker-payload-evidence-accumulation.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/direction-candidates-after-phase-35.md`

### dirty-worktree

Trigger:
当前仓库仍存在大范围 dirty worktree，且本轮只新增了 gate 草案与状态面同步；若不显式标注，下一会话容易把预存脏改误当作本 gate 的执行范围。

Required fields:

- Dirty Scope: 涵盖 `.codex/`、`.github/skills/`、`design_docs/`、`docs/`、`src/`、`release/` 等多处既有修改；本轮直接相关的是新 planning-gate 草案、状态面文档与新的 gate-draft handoff。
- Relevance to Current Handoff: 当前 handoff 只描述下一主线 A 的 gate review 边界，不承担其他既有代码或 release 改动的归并。
- Do Not Revert Notes: 不要回滚与本 gate 无关的预存改动；尤其不要覆盖刚生成的 completed-slice handoff、CURRENT 或 checkpoint。
- Need-to-Inspect Paths: `.codex/handoffs/history/2026-04-16_1315_real-worker-payload-adoption-judgment_stage-close.md`、`.codex/handoffs/CURRENT.md`、`.codex/checkpoints/latest.md`、`design_docs/stages/planning-gate/2026-04-16-controlled-real-worker-payload-evidence-accumulation.md`、`design_docs/Project Master Checklist.md`、`design_docs/Global Phase Map and Current Position.md`。

Verification expectation:
已通过 `git status --short` 确认 dirty worktree 仍很大；下一会话进入执行前，应再次只读取当前 gate 直接相关文件，避免作用域漂移。

Refs:

- `.codex/handoffs/history/2026-04-16_1328_controlled-real-worker-payload-evidence-accumulation-gate-draft_stage-close.md`
- `.codex/handoffs/CURRENT.md`
- `.codex/checkpoints/latest.md`
- `design_docs/stages/planning-gate/2026-04-16-controlled-real-worker-payload-evidence-accumulation.md`

## Other

None.
