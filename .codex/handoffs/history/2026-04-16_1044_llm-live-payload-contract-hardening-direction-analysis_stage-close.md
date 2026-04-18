---
handoff_id: 2026-04-16_1044_llm-live-payload-contract-hardening-direction-analysis_stage-close
entry_role: canonical
kind: stage-close
status: superseded
scope_key: llm-live-payload-contract-hardening-direction-analysis
safe_stop_kind: stage-complete
created_at: 2026-04-16T10:44:21+08:00
supersedes: 2026-04-16_0936_payload-handoff-footprint-controlled-dogfood_stage-close
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
  - design_docs/llm-live-payload-contract-hardening-direction-analysis.md
  - design_docs/direction-candidates-after-phase-35.md
  - review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md
  - docs/subagent-schemas.md
conditional_blocks:
  - dirty-worktree
other_count: 0
---

# Summary

在 `Payload + Handoff Footprint Controlled Dogfood` 之后，本轮继续完成了一条窄 scope 的方向分析收口：针对 live `LLMWorker` payload candidate 的枚举漂移问题，重读了 `OpenAI Agents SDK` 与 `Guardrails AI` 两份最相关研究，并新增 `design_docs/llm-live-payload-contract-hardening-direction-analysis.md`。结论已经明确收敛到下一条推荐主线：`LLMWorker live payload contract hardening`。关键判断现已进一步固定为两条：`content_type` 可以接受极窄的无损别名收敛，而 `operation` 不应对 `upsert` 这类跨语义值做自动猜测；若 LLM 主动尝试产出 payload 但所有 candidate 都被 output guard 拒绝，report 应从 `completed` 下调为 `partial`。当前无 active planning-gate，下一会话可以直接从该分析文档进入新 gate 设计，因此这是一个真实 safe stop。

## Boundary

- 完成到哪里：已完成针对 `LLMWorker live payload contract hardening` 的定向重研，并把结果写入 `design_docs/llm-live-payload-contract-hardening-direction-analysis.md` 与 `design_docs/direction-candidates-after-phase-35.md`。
- 为什么这是安全停点：当前没有 active planning-gate，且下一方向已从“是否继续 dogfood”收口为一个具体、可开 gate 的 hardening 主线；继续推进将跨入新的 planning-gate。
- 明确不在本次完成范围内的内容：不改 `LLMWorker` / `HTTPWorker` 实现、不调整 schema、不再继续 wider dogfood，也不在本轮里直接实现 hardening。

## Authoritative Sources

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/llm-live-payload-contract-hardening-direction-analysis.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md`
- `docs/subagent-schemas.md`

## Session Delta

- 本轮新增：`design_docs/llm-live-payload-contract-hardening-direction-analysis.md`、`.codex/handoffs/history/2026-04-16_1044_llm-live-payload-contract-hardening-direction-analysis_stage-close.md`（canonical handoff）。
- 本轮修改：`design_docs/direction-candidates-after-phase-35.md`、`.codex/checkpoints/latest.md`、`.codex/handoffs/CURRENT.md`。
- 本轮形成的新约束或新结论：
  - `artifact_payloads` 漂移应被视为 output guard / validator 问题，而不是 handoff 或 writeback 问题。
  - `content_type` 可以接受极窄、固定映射的无损别名收敛。
  - `operation` 不应对 `upsert` 这类跨语义值做自动猜测。
  - status policy 已进一步收敛：不能把 `allowed_artifacts` 单独解释成“必须产出 payload”，但若 LLM 主动尝试 payload 且所有 candidate 被 output guard 拒绝，report 应降为 `partial`。

## Verification Snapshot

- 自动化：无新增 pytest；本轮工作以定向重研与文档分析为主，代码面仍沿用上一切片留下的全量基线 `942 passed, 2 skipped`。
- 手测：重读 `review/openai-agents-sdk.md`、`review/guardrails-ai.md`、`docs/subagent-schemas.md` 与 dogfood 结果文档，确认新分析文档给出的 hardening 边界与当前 live signal 一致。
- 未完成验证：未实现新的 hardening 逻辑，因此也未对别名 normalization 或 status downgrade 行为做新回归。
- 仍未验证的结论：在引入 prompt strengthening 与 narrow normalization 之后，live `LLMWorker` 是否能稳定触发 artifact writeback。

## Open Items

- 未决项：是否按已经细化好的 status policy 与 output-guard 边界，直接起 `LLMWorker live payload contract hardening` gate。
- 已知风险：当前 live `LLMWorker` 仍可能产生 schema-valid 但 payload 不可消费的 `completed` report；若不尽快进入 hardening，这个缺口会继续存在。
- 不能默认成立的假设：不能因为已经完成定向重研，就默认别名收敛策略已经被代码验证，也不能默认 `upsert` 之类值可以安全映射。

## Next Step Contract

- 下一会话建议只推进：把 `design_docs/llm-live-payload-contract-hardening-direction-analysis.md` 收敛为一条新的 planning-gate，并围绕 prompt strengthening、narrow output normalization 与已细化的 status policy 实施。
- 下一会话明确不做：不要继续扩大 dogfood，不要顺手去修 `HTTPWorker` 成功态，也不要直接放宽 `Subagent Report` schema。
- 为什么当前应在这里停下：当前最有价值的分析已经完成，继续推进就从“方向分析”进入“新 gate 实施”，不应混在同一 safe stop 里。

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Why This Stage Can Close

- 当前大阶段到这里可以结束的原因：dogfood 结果已经被进一步收敛成一条明确的 next-step analysis，下一方向不再模糊。
- 当前不继续把更多内容塞进本阶段的原因：继续推进将直接跨入新的 gate 设计与实现，超出本轮方向分析 closeout 的边界。

## Planning-Gate Return

- 应回到的 planning-gate 位置：无 active gate；从 `design_docs/llm-live-payload-contract-hardening-direction-analysis.md` 与 `design_docs/direction-candidates-after-phase-35.md` 进入下一条 gate 设计。
- 下一阶段候选主线：`LLMWorker live payload contract hardening`（推荐）；备选为 `HTTPWorker failure fallback schema alignment`。
- 下一阶段明确不做：不要把当前方向分析误当成代码收口，也不要在没有新 gate 的情况下继续扩 wider dogfood。

## Conditional Blocks

### dirty-worktree

Trigger:
生成 handoff 时，workspace 仍存在当前分析步骤的未提交改动，并且仓库中还有与本步骤无关的其他脏状态；下一会话若直接依赖 git diff 需要先区分两者。

Required fields:

- Dirty Scope:
- Relevance to Current Handoff:
- Do Not Revert Notes:
- Need-to-Inspect Paths:
- Dirty Scope: 当前步骤涉及方向分析文档、direction-candidates、checkpoint 与 handoff 状态面；此外 workspace 中还存在本步骤之外的 pre-existing dirty paths。
- Relevance to Current Handoff: 当前步骤文件构成本 handoff 的真实边界；其余 dirty paths 意味着下一会话不能把“工作树不干净”误读成全部都属于 live payload contract hardening analysis。
- Do Not Revert Notes: 不要为清理当前 handoff 边界而重置 unrelated dirty changes；尤其不要覆盖当前步骤触达的 `design_docs/` 与 `.codex/` 文件。
- Need-to-Inspect Paths: `design_docs/llm-live-payload-contract-hardening-direction-analysis.md`、`design_docs/direction-candidates-after-phase-35.md`、`.codex/checkpoints/latest.md`。

Verification expectation:
handoff 生成前已重新检查 workspace reality，并把“当前步骤文件”和“其他已有 dirty paths”分开表述；未尝试通过 reset/checkout 强行清树。

Refs:

- `design_docs/llm-live-payload-contract-hardening-direction-analysis.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `design_docs/Project Master Checklist.md`

## Other

None.
