---
handoff_id: 2026-04-16_0936_payload-handoff-footprint-controlled-dogfood_stage-close
entry_role: canonical
kind: stage-close
status: superseded
scope_key: payload-handoff-footprint-controlled-dogfood
safe_stop_kind: stage-complete
created_at: 2026-04-16T09:36:47+08:00
supersedes: 2026-04-16_0915_llmworker-structured-payload-producer-alignment_stage-close
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
  - design_docs/stages/planning-gate/2026-04-16-payload-handoff-footprint-controlled-dogfood.md
  - review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md
  - design_docs/direction-candidates-after-phase-35.md
  - docs/subagent-schemas.md
conditional_blocks:
  - phase-acceptance-close
  - dirty-worktree
other_count: 0
---

# Summary

完成了 `Payload + Handoff Footprint Controlled Dogfood`。本轮没有继续扩大 producer 语义，而是围绕当前已经打通的 `StubWorker` payload path、`LLMWorker` schema-valid report baseline 与 latest handoff footprint 做了一轮受控 dogfood。baseline `StubWorker` 路径在临时目录里稳定触发了 payload-derived writeback，且 `CURRENT.md` / checkpoint 的 handoff footprint 一致。live DashScope `LLMWorker` 路径成功返回 schema-valid `completed` report，但真实 payload candidate 使用了 schema 不接受的枚举值（如 `upsert`、`text/markdown`），因此被保守归一化层丢弃，没有触发 artifact writeback。当前无 active planning-gate，结果面、状态面与方向文档已同步，因此这是一个真实 safe stop。

## Boundary

- 完成到哪里：`design_docs/stages/planning-gate/2026-04-16-payload-handoff-footprint-controlled-dogfood.md` 已 DONE；baseline runtime 证明、live DashScope run 与结果归档已完成，下一方向已重新收口到更窄的 live payload contract hardening / real-worker consistency follow-up。
- 为什么这是安全停点：本轮 dogfood 的职责是拿到真实 signal，而不是继续扩实现；该 signal 已明确落到当前结果文档与方向文档中，继续推进会跨入新的 planning-gate 范围。
- 明确不在本次完成范围内的内容：不修 `LLMWorker` / `HTTPWorker` 代码、不扩多 payload、不改 schema、不做新的 tracing/ledger 设计，也不继续做更宽的 dogfood 扩展。

## Authoritative Sources

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/stages/planning-gate/2026-04-16-payload-handoff-footprint-controlled-dogfood.md`
- `review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `docs/subagent-schemas.md`

## Session Delta

- 本轮新增：`review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md`、`.codex/handoffs/history/2026-04-16_0936_payload-handoff-footprint-controlled-dogfood_stage-close.md`（canonical handoff）。
- 本轮修改：`design_docs/stages/planning-gate/2026-04-16-payload-handoff-footprint-controlled-dogfood.md`、`design_docs/Project Master Checklist.md`、`design_docs/Global Phase Map and Current Position.md`、`design_docs/direction-candidates-after-phase-35.md`、`.codex/checkpoints/latest.md`、`.codex/handoffs/CURRENT.md`。
- 本轮形成的新约束或新结论：
  - baseline `StubWorker` payload path 与 latest handoff footprint 恢复面可以一起成立。
  - live `LLMWorker` 已能稳定返回 schema-valid report，但当前 prompt / response contract 还不足以稳定约束 payload `operation` / `content_type` 落入 schema 允许集合。
  - 当前 real-worker 缺口已经从“路径是否可用”收敛为“live payload contract consistency 是否足够强”。

## Verification Snapshot

- 自动化：通过 `Executor + StubWorkerBackend + WritebackEngine` 执行 baseline runtime dogfood，成功触发 payload-derived writeback；通过 `Executor + LLMWorker + WritebackEngine` 执行 live DashScope run，成功获得 schema-valid `completed` report；后续直接抓取 raw response 诊断 live payload candidate 漂移原因。
- 手测：重读 `CURRENT.md`、checkpoint、Checklist、Phase Map、direction-candidates 与 dogfood 结果文档，确认 latest handoff footprint 恢复入口一致，且 live signal 已回写到状态面。
- 未完成验证：本轮没有新增 pytest 回归；沿用上一切片留下的全量基线 `942 passed, 2 skipped` 作为当前代码面基线。
- 仍未验证的结论：在不同任务文本与更复杂上下文下，live `LLMWorker` 是否仍会稳定把 payload 枚举压回当前 schema 允许集合。

## Open Items

- 未决项：下一条窄切片尚未选择；当前推荐转入 `LLMWorker live payload contract hardening`，备选为 `HTTPWorker failure fallback schema alignment`。
- 已知风险：当前 live `LLMWorker` 虽然不会再产生 invalid report，但仍可能因 payload 枚举漂移而只留下 summary writeback，不触发 artifact writeback。
- 不能默认成立的假设：不能因为 baseline dogfood 与 mocked integration 都成立，就默认 live payload producer 语义已经稳定。

## Next Step Contract

- 下一会话建议只推进：优先起一条 `LLMWorker live payload contract hardening` 的窄 gate，针对真实模型的 `operation` / `content_type` 枚举漂移做 contract-strengthening 或保守 normalization 评估。
- 下一会话明确不做：不要在没有新 gate 的情况下继续泛化 dogfood、直接扩多 payload / schema、顺手改 `HTTPWorker` 成功态语义，或继续宽扩 tracing/ledger。
- 为什么当前应在这里停下：dogfood 的目标已经达到，继续推进会从“收集真实 signal”跨到“修复新的具体缺口”，那已经是下一条实现切片。

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Why This Stage Can Close

- 当前大阶段到这里可以结束的原因：baseline runtime 与 live runtime 都已经执行，且结果已经收口为一个具体、可复现的 live payload contract 缺口；当前 gate 的观察职责已完成。
- 当前不继续把更多内容塞进本阶段的原因：继续推进就会进入新的实现决策，例如 prompt hardening、同义值 normalization 或 `HTTPWorker` consistency follow-up，不再属于 controlled dogfood 收口边界。

## Planning-Gate Return

- 应回到的 planning-gate 位置：无 active gate；从 `design_docs/direction-candidates-after-phase-35.md` 的 `After Payload + Handoff Footprint Controlled Dogfood` 增量更新重新进入方向选择。
- 下一阶段候选主线：`LLMWorker live payload contract hardening`（推荐）；备选为 `HTTPWorker failure fallback schema alignment` 或更窄的 `driver / adapter backlog-recording only`。
- 下一阶段明确不做：不要把新的 live signal 直接混入当前 dogfood closeout，也不要在没有新 gate 的情况下继续改 producer 语义。

## Conditional Blocks

### phase-acceptance-close

Trigger:
当前 handoff 覆盖的是 `Payload + Handoff Footprint Controlled Dogfood` 的正式收口边界，planning-gate 已 DONE，且仓库重新回到无 active planning-gate 的 safe stop。

Required fields:

- Acceptance Basis:
- Automation Status:
- Manual Test Status:
- Checklist/Board Writeback Status:
- Acceptance Basis: baseline `StubWorker` payload path 与 latest handoff footprint 恢复面已在 controlled dogfood 中成立，live DashScope `LLMWorker` 也已给出明确的 real payload signal 与具体缺口。
- Automation Status: baseline runtime dogfood 执行成功；live DashScope run 执行成功；无新增 pytest，沿用上一切片全量基线 `942 passed, 2 skipped`。
- Manual Test Status: 重读 `CURRENT.md`、checkpoint、Checklist、Phase Map、direction-candidates 与结果文档，确认状态面与恢复入口一致。
- Checklist/Board Writeback Status: planning-gate、Checklist、Phase Map、direction-candidates、checkpoint 与 handoff/CURRENT mirror 已对齐到本 canonical handoff。

Verification expectation:
验收依据以 runtime dogfood 观察与状态面回写为主；当前 handoff 不把 live payload contract hardening 伪装成已完成事项。

Refs:

- `design_docs/stages/planning-gate/2026-04-16-payload-handoff-footprint-controlled-dogfood.md`
- `review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md`
- `design_docs/Project Master Checklist.md`

### dirty-worktree

Trigger:
生成 handoff 时，workspace 仍存在当前切片的未提交改动，并且仓库中还有与本切片无关的其他脏状态；下一会话若直接依赖 git diff 需要先区分两者。

Required fields:

- Dirty Scope:
- Relevance to Current Handoff:
- Do Not Revert Notes:
- Need-to-Inspect Paths:
- Dirty Scope: 当前切片涉及 dogfood 结果文档、planning-gate、Checklist、Phase Map、direction-candidates、checkpoint 与 handoff 状态面；此外 workspace 中还存在本切片之外的 pre-existing dirty paths。
- Relevance to Current Handoff: 当前切片文件构成本 handoff 的真实边界；其余 dirty paths 意味着下一会话不能把“工作树不干净”误读成全部都属于 controlled dogfood slice。
- Do Not Revert Notes: 不要为清理当前 handoff 边界而重置 unrelated dirty changes；尤其不要覆盖当前切片触达的 `review/`、`design_docs/` 与 `.codex/` 文件。
- Need-to-Inspect Paths: `review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md`、`design_docs/stages/planning-gate/2026-04-16-payload-handoff-footprint-controlled-dogfood.md`、`design_docs/direction-candidates-after-phase-35.md`、`.codex/checkpoints/latest.md`。

Verification expectation:
handoff 生成前已重新检查 workspace reality，并把“当前切片文件”和“其他已有 dirty paths”分开表述；未尝试通过 reset/checkout 强行清树。

Refs:

- `design_docs/Project Master Checklist.md`
- `review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md`
- `design_docs/stages/planning-gate/2026-04-16-payload-handoff-footprint-controlled-dogfood.md`

## Other

None.
