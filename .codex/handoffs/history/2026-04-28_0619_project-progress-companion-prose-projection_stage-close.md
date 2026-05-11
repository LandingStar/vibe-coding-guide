---
handoff_id: 2026-04-28_0619_project-progress-companion-prose-projection_stage-close
entry_role: canonical
kind: stage-close
status: superseded
scope_key: project-progress-companion-prose-projection
safe_stop_kind: stage-complete
created_at: 2026-04-28T06:19:25+08:00
supersedes: 2026-04-28_0548_release-close-handoff-current-refresh-hardening_stage-close
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
  - design_docs/project-progress-companion-prose-projection-followup-direction-analysis.md
  - design_docs/direction-candidates-after-phase-35.md
  - design_docs/project-progress-companion-prose-projection-slice1-draft.md
  - design_docs/stages/planning-gate/2026-04-28-project-progress-companion-prose-projection.md
conditional_blocks:
  - phase-acceptance-close
  - code-change
  - dirty-worktree
other_count: 0
---

# Summary

本会话完成 `Project Progress Companion Prose Projection` 的 stage-close：在 `tools/progress_graph/doc_projection.py` 中把 pure companion prose sections 纳入 `direction-candidates-global`，为 `selected-next-step` / `narrowed-entry` / `actual-next-gate` 建立 section-local 独立 node，并让显式 planning-gate path 建立到 `planning-gates-index` 的最小 linkage；随后补齐 targeted tests、关闭当前 planning-gate、同步 Checklist / Phase Map / checkpoint / direction-candidates / follow-up analysis，并把仓库重新带回无 active planning-gate 的 safe-stop 状态。当前可以安全停下，因为 companion prose 第一刀的 contract、实现、验证与状态面回写已经收口，剩余工作已明确转化为新的方向选择，而不是本 gate 内的未完尾项。

## Boundary

- 完成到哪里：`design_docs/stages/planning-gate/2026-04-28-project-progress-companion-prose-projection.md` 已完成并关闭；`tools/progress_graph/doc_projection.py` 已支持 pure companion prose section 解析、section-local companion nodes 与 explicit actual-next-gate linkage；`tests/test_progress_graph_doc_projection.py` 已补对应 targeted assertions；Checklist、Phase Map、checkpoint、`design_docs/direction-candidates-after-phase-35.md` 与新的 follow-up analysis 已同步到 companion prose 收口后的状态。
- 为什么这是安全停点：当前 gate 的 stop condition 只要求 contract、实现、targeted tests 与真实 artifact refresh 成立；这些条件已经满足，且仓库已重新回到无 active planning-gate 状态，下一步只需从新候选中选择一条窄主线继续。
- 明确不在本次完成范围内的内容：不把本 gate 扩成通用 prose parser；不继续推进 post-release dogfood / install path tightening；不继续 extension runtime/package management follow-up validation；不把 companion prose source boundary 扩到 Checklist、Phase Map 或 release follow-up 之外的更宽 surface。

## Authoritative Sources

- design_docs/Project Master Checklist.md
- design_docs/Global Phase Map and Current Position.md
- design_docs/project-progress-companion-prose-projection-followup-direction-analysis.md
- design_docs/direction-candidates-after-phase-35.md
- design_docs/project-progress-companion-prose-projection-slice1-draft.md
- design_docs/stages/planning-gate/2026-04-28-project-progress-companion-prose-projection.md

## Session Delta

- 本轮新增：新增 `design_docs/project-progress-companion-prose-projection-followup-direction-analysis.md`，把 companion prose 收口后的下一方向候选固定为 `post-release dogfood / install path tightening`、`extension runtime/package management follow-up validation`、`broader companion prose surface expansion`。
- 本轮修改：`tools/progress_graph/doc_projection.py` 现已解析 pure companion prose sections，并输出 `selected-next-step` / `narrowed-entry` / `actual-next-gate` companion nodes；`tests/test_progress_graph_doc_projection.py` 已覆盖 companion node 与 planning-gate linkage；当前 gate、Slice 1 草案、Checklist、Phase Map、checkpoint、`design_docs/v0.9.5-preview-release-followup-direction-analysis.md` 与 `design_docs/direction-candidates-after-phase-35.md` 已全部回写到完成态。
- 本轮形成的新约束或新结论：companion prose 的第一版实现应继续作为 `direction-candidates-global` 的 section-local surface，而不是新 graph 或 metadata-only fallback；显式 planning-gate linkage 只从 `actual-next-gate` prose 提取，不泛化到任意 prose 引用。

## Verification Snapshot

- 自动化：已通过 `python -m pytest tests/test_progress_graph_doc_projection.py -q`（3 passed）；已刷新 `.codex/progress-graph/latest.json` / `.dot` / `.html`，使真实 artifact 反映当前 companion prose 状态面。
- 手测：已人工核对当前 planning-gate、Slice draft、Checklist、Phase Map、checkpoint 与 direction-candidates/follow-up analysis 的边界一致性，确认当前仓库回到无 active planning-gate 且下一方向候选已明确。
- 未完成验证：未跑 Python 全量测试；未对更宽的 `direction-candidates-after-phase-35.md` 历史 section 做额外人工 spot check；未做 post-release install-path dogfood 或 extension runtime/package UI 点击级验证。
- 仍未验证的结论：当前只能确认 companion prose 第一刀在目标 source boundary 上成立，尚不能据此推出更宽 prose surface 也能无改动复用同一 parser/graph contract。

## Open Items

- 未决项：仍需从 `design_docs/project-progress-companion-prose-projection-followup-direction-analysis.md` 选择下一条 post-release 窄主线；若继续 release 路径，当前默认建议是 `post-release dogfood / install path tightening`。
- 已知风险：workspace 仍存在并行未提交的 extension runtime/package management 代码与文档改动；它们不属于当前 companion prose gate 的控制面，但会影响下一会话对 dirty worktree 的判断。
- 不能默认成立的假设：不能把当前 companion prose parser 视为通用 prose parser；不能把 `actual-next-gate` linkage 的成功推广为任意 prose ref 的自动 cross-graph linkage；不能把当前 gate 完成等同于 release 分发路径或 extension 管理面的真实验证已经完成。

## Next Step Contract

- 下一会话建议只推进：从 `design_docs/project-progress-companion-prose-projection-followup-direction-analysis.md` 中重新选择一条窄主线，默认优先进入 `Candidate A. Post-Release Dogfood / Install Path Tightening`。
- 下一会话明确不做：不要重新打开 `design_docs/stages/planning-gate/2026-04-28-project-progress-companion-prose-projection.md`；不要在没有新 planning-gate 的前提下继续扩大 companion prose source boundary；不要把 release install-path dogfood、extension UI validation 与更宽 prose expansion 混成同一切片。
- 为什么当前应在这里停下：当前 gate 已完成其最小 contract，继续推进已经不再是“把本 gate 做完”，而是进入新的方向选择或新的验证/实现切片。

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Why This Stage Can Close

- 当前大阶段到这里可以结束的原因：本 gate 负责的唯一问题是把 `用户选定下一步` / `当前更窄的入口` / `当前实际下一条 planning-gate` 三类 companion prose 变成最小可投影、可验证、可回写的 graph surface；当前 contract、实现、tests 与状态面同步都已完成。
- 当前不继续把更多内容塞进本阶段的原因：剩余工作已经转化为新的候选方向，分别对应 release 分发验证、extension 后续验证或更宽 prose source 扩展；继续追加会直接跨出当前 gate 的 narrow scope。

## Planning-Gate Return

- 应回到的 planning-gate 位置：当前仓库已回到无 active planning-gate 状态；下一次继续时，应先回到 `design_docs/project-progress-companion-prose-projection-followup-direction-analysis.md` 与 `design_docs/direction-candidates-after-phase-35.md` 选择新的窄主线。
- 下一阶段候选主线：`Candidate A. Post-Release Dogfood / Install Path Tightening`、`Candidate B. Extension Runtime/Package Management Follow-up Validation`、`Candidate C. Broader Companion Prose Surface Expansion`。
- 下一阶段明确不做：不重新打开当前 companion prose gate；不在没有新 gate 的前提下继续修改 `tools/progress_graph/doc_projection.py`；不把并行的 extension runtime/package management 脏工作区误当作当前 gate 的待收尾项。

## Conditional Blocks

### phase-acceptance-close

Trigger:
本次 handoff 是 `Project Progress Companion Prose Projection` 的正式 stage-close，用于记录 companion prose 第一版 graph surface 已经完成并回到 safe stop。

Required fields:

- Acceptance Basis:
- Automation Status:
- Manual Test Status:
- Checklist/Board Writeback Status:

Verification expectation:
- Acceptance Basis: `design_docs/stages/planning-gate/2026-04-28-project-progress-companion-prose-projection.md` 的 validation gate 与 stop condition 已满足：selected-next-step / narrowed-entry / actual-next-gate surface 可稳定投影，explicit planning-gate linkage 成立，且 targeted tests 与 artifact refresh 已完成。
- Automation Status: 已通过 `python -m pytest tests/test_progress_graph_doc_projection.py -q`（3 passed），并已刷新 `.codex/progress-graph/latest.json` / `.dot` / `.html`。
- Manual Test Status: 已人工复核 planning-gate、Slice draft、Checklist、Phase Map、checkpoint、direction-candidates 与 follow-up analysis 的边界同步；未做更宽 prose surface 或 release/install-path 手测。
- Checklist/Board Writeback Status: Checklist、Phase Map、checkpoint、`design_docs/v0.9.5-preview-release-followup-direction-analysis.md`、`design_docs/direction-candidates-after-phase-35.md` 与新的 follow-up analysis 已同步到当前 safe-stop 边界。

Verification expectation:
对本次 stage-close，必须同时看到 current gate 关闭、targeted tests 通过、真实 progress graph artifacts 刷新，以及 Checklist / Phase Map / checkpoint / direction-candidates 同步到无 active planning-gate 状态；当前这些条件都已成立。

Refs:

- design_docs/stages/planning-gate/2026-04-28-project-progress-companion-prose-projection.md
- design_docs/Project Master Checklist.md
- design_docs/Global Phase Map and Current Position.md
- .codex/checkpoints/latest.md
- design_docs/direction-candidates-after-phase-35.md

### code-change

Trigger:
本次 handoff 覆盖范围内包含 `tools/progress_graph/doc_projection.py` 与 `tests/test_progress_graph_doc_projection.py` 的实际代码改动，因此需要显式记录实现意图与验证边界。

Required fields:

- Touched Files:
- Intent of Change:
- Tests Run:
- Untested Areas:

Verification expectation:
- Touched Files: `tools/progress_graph/doc_projection.py`、`tests/test_progress_graph_doc_projection.py`。
- Intent of Change: 让 `direction-candidates-global` 能解析 pure companion prose sections，并把 `selected-next-step` / `narrowed-entry` / `actual-next-gate` 作为 section-local companion nodes 投影到 graph，同时只在显式 `actual-next-gate` path 上建立到 `planning-gates-index` 的最小 linkage。
- Tests Run: `python -m pytest tests/test_progress_graph_doc_projection.py -q`（3 passed）。
- Untested Areas: 未跑全量 pytest；未补更宽历史 prose source 的额外 spot checks；未对非当前目标 section 的所有 recency/candidate interaction 进行人工回归。

Verification expectation:
接手方应把当前代码改动理解为“当前 target section 的最小实现已验证”，而不是“更宽 prose parsing 已全量覆盖”；若下一步继续扩大 source boundary，应先新增新的 planning-gate 与针对性测试。

Refs:

- tools/progress_graph/doc_projection.py
- tests/test_progress_graph_doc_projection.py
- design_docs/project-progress-companion-prose-projection-slice1-draft.md
- design_docs/stages/planning-gate/2026-04-28-project-progress-companion-prose-projection.md

### dirty-worktree

Trigger:
生成 handoff 时，workspace 仍存在当前 gate 的未提交代码/文档/graph artifact 以及并行 extension runtime/package management 轨道的未提交改动，这些都会影响下一会话对 repo reality 的判断。

Required fields:

- Dirty Scope:
- Relevance to Current Handoff:
- Do Not Revert Notes:
- Need-to-Inspect Paths:

Verification expectation:
- Dirty Scope: `tools/progress_graph/doc_projection.py`、`tests/test_progress_graph_doc_projection.py`、`.codex/checkpoints/latest.md`、`.codex/progress-graph/latest.json`、`.codex/progress-graph/latest.html`、`design_docs/Project Master Checklist.md`、`design_docs/Global Phase Map and Current Position.md`、`design_docs/v0.9.5-preview-release-followup-direction-analysis.md`、`design_docs/direction-candidates-after-phase-35.md`、`design_docs/project-progress-companion-prose-projection-followup-direction-analysis.md`、`design_docs/project-progress-companion-prose-projection-slice1-draft.md`、`design_docs/stages/planning-gate/2026-04-28-project-progress-companion-prose-projection.md`，以及并行的 `vscode-extension/src/extension.ts`、`vscode-extension/src/setup/runtimeInstaller.ts`、`vscode-extension/src/setup/runtimePackageManager.ts`、`vscode-extension/src/views/configPanel.ts`、`vscode-extension/tsconfig.json` 与对应 extension design docs。
- Relevance to Current Handoff: 前一组文件直接构成当前 companion prose gate 的 safe-stop reality；后一组 extension 文件不属于本 gate 本身，但属于同一 dirty worktree 中已存在的并行已完成轨道，接手方必须区分“当前 gate 收口”与“并行 extension 轨道未提交”。
- Do Not Revert Notes: 不要把 extension runtime/package management 相关改动当成当前 companion prose gate 的可清理噪音；也不要回退 `.codex/progress-graph/latest.*`、checkpoint 或 authority docs 的当前 writeback，因为它们正是本次 safe-stop 的状态面。
- Need-to-Inspect Paths: `tools/progress_graph/doc_projection.py`、`tests/test_progress_graph_doc_projection.py`、`.codex/checkpoints/latest.md`、`design_docs/project-progress-companion-prose-projection-followup-direction-analysis.md`、`design_docs/direction-candidates-after-phase-35.md`、`vscode-extension/src/setup/runtimePackageManager.ts`、`vscode-extension/src/views/configPanel.ts`。

Verification expectation:
接手方必须先区分“当前 companion prose gate 的已完成 writeback”与“并行 extension/runtime 轨道的未提交实现”，再决定下一步是否继续 release 路径、extension follow-up，或更宽 prose expansion。

Refs:

- design_docs/stages/planning-gate/2026-04-28-project-progress-companion-prose-projection.md
- design_docs/stages/planning-gate/2026-04-28-vscode-extension-runtime-package-management.md
- design_docs/vscode-extension-runtime-package-management-slice1-draft.md
- .codex/checkpoints/latest.md

## Other

None.
