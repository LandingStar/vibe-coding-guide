---
handoff_id: 2026-04-16_1111_llmworker-live-payload-contract-hardening_stage-close
entry_role: canonical
kind: stage-close
status: superseded
scope_key: llmworker-live-payload-contract-hardening
safe_stop_kind: stage-complete
created_at: 2026-04-16T11:11:56+08:00
supersedes: 2026-04-16_1057_llmworker-live-payload-contract-hardening-gate-draft_stage-close
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
  - design_docs/stages/planning-gate/2026-04-16-llmworker-live-payload-contract-hardening.md
  - design_docs/llm-live-payload-contract-hardening-direction-analysis.md
  - design_docs/live-payload-rerun-verification-direction-analysis.md
  - design_docs/direction-candidates-after-phase-35.md
  - review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md
  - docs/subagent-schemas.md
conditional_blocks:
  - phase-acceptance-close
  - code-change
  - dirty-worktree
other_count: 0
---

# Summary

完成了 `LLMWorker Live Payload Contract Hardening`。本轮已经把 planning-gate 里的三条窄边界全部落成代码与测试：`LLMWorker` prompt 现在显式约束允许的 `operation` / `content_type` 枚举并加入禁止示例；output guard 现在只对 `text/markdown`、`text/plain`、`application/json` 这类低歧义 `content_type` 做固定 alias normalization；若 LLM 主动尝试输出 payload 但所有 candidate 都被 guard 拒绝，最终 `report.status` 会从 `completed` 下调为 `partial`。相关 targeted regression `55 passed, 1 skipped`，全量回归 `946 passed, 2 skipped`，且高层状态面与 checkpoint 已同步回“无 active planning-gate”的 safe stop。下一会话的自然主线不再是继续补实现，而是一轮更小的 live rerun 验证。

## Boundary

- 完成到哪里：`design_docs/stages/planning-gate/2026-04-16-llmworker-live-payload-contract-hardening.md` 已 DONE；`src/workers/llm_worker.py` 与对应 worker / integration tests 已按 gate 落地；Checklist、Phase Map、direction-candidates 与 checkpoint 已同步到实现完成边界。
- 为什么这是安全停点：当前切片的实现、targeted regression 与全量回归都已完成，且下一步已经从“实现 hardening”切换为“复核真实模型 signal”；已完成项与未完成项可以稳定分离。
- 明确不在本次完成范围内的内容：不包含新的 live DashScope rerun，不修改 `HTTPWorker`，不改 schema，不扩多 payload，也不对 `operation` 做语义猜测映射。

## Authoritative Sources

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/stages/planning-gate/2026-04-16-llmworker-live-payload-contract-hardening.md`
- `design_docs/llm-live-payload-contract-hardening-direction-analysis.md`
- `design_docs/live-payload-rerun-verification-direction-analysis.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `review/payload-handoff-footprint-controlled-dogfood-2026-04-16.md`
- `docs/subagent-schemas.md`

## Session Delta

- 本轮新增：`design_docs/live-payload-rerun-verification-direction-analysis.md`、`.codex/handoffs/history/2026-04-16_1111_llmworker-live-payload-contract-hardening_stage-close.md`。
- 本轮修改：`src/workers/llm_worker.py`、`tests/test_workers.py`、`tests/test_pep_writeback_integration.py`、`design_docs/stages/planning-gate/2026-04-16-llmworker-live-payload-contract-hardening.md`、`design_docs/Project Master Checklist.md`、`design_docs/Global Phase Map and Current Position.md`、`design_docs/direction-candidates-after-phase-35.md`、`.codex/checkpoints/latest.md`。
- 本轮形成的新约束或新结论：
  - live prompt contract 必须显式列出允许枚举，并明确禁止 `upsert`、`text/markdown` 这类已观察到的漂移值。
  - `content_type` 只允许做固定、无损、低歧义 alias normalization；`operation` 继续保持保守拒绝边界。
  - `allowed_artifacts` 仍只表达写回权限边界；只有在 LLM 主动尝试 payload 且所有 candidate 都被 guard 拒绝时，`status` 才从 `completed` 下调为 `partial`。
  - 当前自动化基线已提升到 `946 passed, 2 skipped`。

## Verification Snapshot

- 自动化：targeted regression `55 passed, 1 skipped`；全量回归 `946 passed, 2 skipped`。
- 手测：已核对 planning-gate、Checklist、Phase Map、direction-candidates、checkpoint 与 handoff 边界一致；未执行新的 live real-model rerun。
- 未完成验证：新的 prompt + normalization + status policy 组合尚未在 live DashScope 路径上重新实跑。
- 仍未验证的结论：当前 hardening 是否足以提升真实 `artifact_payloads` 命中率，或是否只会更准确地把失败表征为 `partial`。

## Open Items

- 未决项：是否立刻进入一轮更小的 live rerun 验证，还是暂时转向 `HTTPWorker failure fallback schema alignment`。
- 已知风险：真实模型仍可能继续输出 schema 不接受的 `operation` 值；当前仓库仍存在大量与本切片无关的 dirty changes，下一会话若看 diff 需要先分流。
- 不能默认成立的假设：不能默认 `content_type` alias normalization 已足以修复真实 writeback 命中率，也不能默认 `HTTPWorker` 与本轮 `LLMWorker` hardening 可以合并处理。

## Next Step Contract

- 下一会话建议只推进：优先做一轮更小的 live payload rerun verification，复跑受控 `LLMWorker` real-model path，观察新的 prompt + normalization + status policy 会把真实结果推到哪里。
- 下一会话明确不做：不要在没有新 live signal 的情况下继续加宽 normalization，不要改 schema，不要顺手并入 `HTTPWorker` 或其他 real-worker 路线，也不要清理或回退 unrelated dirty changes。
- 为什么当前应在这里停下：当前实现切片已经闭环，再继续写代码只会增加猜测；下一步最有价值的信息必须来自新的 live run，而不是继续本地扩实现。

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Why This Stage Can Close

- 当前大阶段到这里可以结束的原因：`LLMWorker live payload contract hardening` 这条窄切片的 gate、实现、自动化验证与状态面回写都已经完成，且无 active planning-gate 残留。
- 当前不继续把更多内容塞进本阶段的原因：继续推进会跨入新的 live rerun / real-worker follow-up 范围，不再属于本轮 hardening 的实现收口。

## Planning-Gate Return

- 应回到的 planning-gate 位置：当前无 active planning-gate；从 `design_docs/direction-candidates-after-phase-35.md` 的 `After LLMWorker Live Payload Contract Hardening` 增量更新重新进入下一方向选择。
- 下一阶段候选主线：`live payload rerun verification`（推荐）；备选仍是 `HTTPWorker failure fallback schema alignment`。
- 下一阶段明确不做：不要把新的 live rerun 或 `HTTPWorker` follow-up 混进当前已关闭的 hardening 切片里。

## Conditional Blocks

### phase-acceptance-close

Trigger:
当前 handoff 覆盖的是 `LLMWorker Live Payload Contract Hardening` 的正式 stage-close：planning-gate 已 DONE、代码与测试已落地，且仓库状态面已经回到无 active planning-gate 的 safe stop。

Required fields:

- Acceptance Basis:
- Automation Status:
- Manual Test Status:
- Checklist/Board Writeback Status:
- Acceptance Basis: planning-gate 的三条目标已经全部落地，包括 prompt strengthening、窄 `content_type` alias normalization、以及 attempted-payload rejection -> `partial` 的 status policy。
- Automation Status: targeted regression `55 passed, 1 skipped`；全量回归 `946 passed, 2 skipped`。
- Manual Test Status: 已核对 gate、Checklist、Phase Map、direction-candidates、checkpoint 与 handoff 边界一致；未执行新的 live rerun。
- Checklist/Board Writeback Status: `design_docs/Project Master Checklist.md`、`design_docs/Global Phase Map and Current Position.md`、`design_docs/direction-candidates-after-phase-35.md` 与 `.codex/checkpoints/latest.md` 已同步到当前 closeout。

Verification expectation:
接手方应把本 handoff 视为“实现 closeout 已完成，但 live real-model 验证仍待下一切片”的正式收口，而不是把 live rerun 误读成已完成项。

Refs:

- `design_docs/stages/planning-gate/2026-04-16-llmworker-live-payload-contract-hardening.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`

### code-change

Trigger:
本轮直接修改了 `LLMWorker` 运行时代码与对应测试，且这些改动共同构成当前 safe stop 的完成边界。

Required fields:

- Touched Files:
- Intent of Change:
- Tests Run:
- Untested Areas:
- Touched Files: `src/workers/llm_worker.py`、`tests/test_workers.py`、`tests/test_pep_writeback_integration.py`。
- Intent of Change: 收紧 live payload contract，使真实模型输出更稳定落入当前 schema 允许边界，并把 attempted-but-rejected payload 更准确地表征为 `partial`。
- Tests Run: `pytest tests/test_workers.py tests/test_pep_writeback_integration.py -q` -> `55 passed, 1 skipped`；`pytest tests -q` -> `946 passed, 2 skipped`。
- Untested Areas: 未执行新的 live DashScope rerun；因此真实模型在新 prompt contract 下的最终 payload writeback 命中率仍待验证。

Verification expectation:
接手方若继续沿这条主线推进，应默认代码面已经过 targeted + full regression，而不是重新猜测本地语义；真正需要补的是 live signal，而不是更多本地自动化。

Refs:

- `src/workers/llm_worker.py`
- `tests/test_workers.py`
- `tests/test_pep_writeback_integration.py`
- `design_docs/stages/planning-gate/2026-04-16-llmworker-live-payload-contract-hardening.md`

### dirty-worktree

Trigger:
生成 handoff 时 workspace 仍有大量未提交修改；其中只有一小部分属于当前 hardening closeout，其余是当前 safe stop 之外的 pre-existing dirty surfaces。

Required fields:

- Dirty Scope:
- Relevance to Current Handoff:
- Do Not Revert Notes:
- Need-to-Inspect Paths:
- Dirty Scope: 当前切片相关改动集中在 `src/workers/llm_worker.py`、对应 tests、planning-gate、Checklist、Phase Map、direction-candidates、checkpoint 与 handoff；此外仓库还存在 `.codex/handoff-system/`、`.github/skills/`、`doc-loop-vibe-coding/`、`release/`、`src/pack/`、`src/workflow/` 等 broader dirty surfaces。
- Relevance to Current Handoff: 当前切片文件构成下一会话做 live rerun verification 的真实起点；其他 dirty paths 不能被误当作这条 hardening 主线的一部分。
- Do Not Revert Notes: 不要为清理当前 closeout 而回退 unrelated dirty changes；尤其不要覆盖当前切片触达的 `src/workers/llm_worker.py`、tests、`design_docs/` 与 `.codex/` 状态文件。
- Need-to-Inspect Paths: `src/workers/llm_worker.py`、`tests/test_workers.py`、`tests/test_pep_writeback_integration.py`、`design_docs/stages/planning-gate/2026-04-16-llmworker-live-payload-contract-hardening.md`、`design_docs/direction-candidates-after-phase-35.md`、`.codex/checkpoints/latest.md`。

Verification expectation:
接手方在使用 git diff 或准备新切片前，应先确认哪些改动属于当前 hardening closeout，哪些只是并存的仓库脏状态；当前 handoff 不把“整个 repo 都脏”误写成“全部都与本切片相关”。

Refs:

- `design_docs/Project Master Checklist.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `src/workers/llm_worker.py`

## Other

None.
