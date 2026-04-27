---
handoff_id: 2026-04-27_1931_global-direction-candidates-section-recency-semantics_stage-close
entry_role: canonical
kind: stage-close
status: active
scope_key: global-direction-candidates-section-recency-semantics
safe_stop_kind: stage-complete
created_at: 2026-04-27T19:31:29+08:00
supersedes: 2026-04-26_0639_project-progress-doc-loop-projection-and-snapshot-persistence_stage-close
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
  - design_docs/direction-candidates-after-phase-35.md
  - design_docs/stages/planning-gate/2026-04-26-global-direction-candidates-section-recency-semantics.md
  - design_docs/project-progress-global-direction-candidates-recency-semantics-followup-direction-analysis.md
conditional_blocks:
  - phase-acceptance-close
  - code-change
  - dirty-worktree
other_count: 0
---

# Summary

本会话完成 `Global Direction-Candidates Section Recency Semantics` 的 stage-close：`tools/progress_graph/doc_projection.py` 已把 `direction-candidates-global` 的 latest numbered section 选择从“最后出现者获胜”改为显式 recency 规则，优先取 section title 日期、在同日或缺失日期时回退到更早文档位置；`tests/test_progress_graph_doc_projection.py` 已补充顶部插入 numbered section 的 targeted probe 并通过，真实 `.codex/progress-graph/latest.json`、`.dot`、`.html` 已刷新。当前仓库已回到无 active planning-gate 的可恢复 safe stop，下一条主线明确转向 `companion prose projection`，且用户已在方向选择上收窄到 A2 完整 prose projection，但当前轮先做 safe stop 收口。

## Boundary

- 完成到哪里：`design_docs/stages/planning-gate/2026-04-26-global-direction-candidates-section-recency-semantics.md` 已完成并关闭；latest section source-of-truth、实现、targeted tests 与真实 artifact refresh 都已成立。
- 为什么这是安全停点：当前 active gate 已关闭，recency 语义的代码、测试、artifact 与 authority state 已收口；后续工作已经明确属于新的 planning-gate，而不是当前 gate 的自然延长。
- 明确不在本次完成范围内的内容：不进入 `companion prose projection` 实现；不进入 `selected-next-step linkage projection`；不做 `global direction-candidates artifact consistency audit`；不扩到 graph UI 或新的 host workflow。

## Authoritative Sources

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `design_docs/stages/planning-gate/2026-04-26-global-direction-candidates-section-recency-semantics.md`
- `design_docs/project-progress-global-direction-candidates-recency-semantics-followup-direction-analysis.md`

## Session Delta

- 本轮新增：`.codex/handoffs/history/2026-04-27_1931_global-direction-candidates-section-recency-semantics_stage-close.md`。
- 本轮修改：`tools/progress_graph/doc_projection.py`、`tests/test_progress_graph_doc_projection.py`、`.codex/progress-graph/latest.json`、`.codex/progress-graph/latest.dot`、`.codex/progress-graph/latest.html`、`design_docs/stages/planning-gate/2026-04-26-global-direction-candidates-section-recency-semantics.md`、`design_docs/project-progress-global-direction-candidates-recency-semantics-followup-direction-analysis.md`，以及 safe-stop pointer footprint 所在状态面。
- 本轮形成的新约束或新结论：`direction-candidates-global` 的 latest/current surface 现在以日期语义为主，而不再受文档物理顺序直接控制；后续任何 prose 或 linkage 语义都应建立在这条稳定 recency contract 之上。

## Verification Snapshot

- 自动化：`pytest tests/test_progress_graph_doc_projection.py -q` 通过（3 passed）。
- 手测：已 spot check 真实 `.codex/progress-graph/latest.json`、`.dot`、`.html`，确认 recency 刷新结果存在，且 authority state 已回到 `no active planning-gate` / `Latest Completed Slice = Global Direction-Candidates Recency Semantics` 的口径。
- 未完成验证：未重跑 progress graph 全量测试；未做 UI consumer 或 host preview 回归；未做 `companion prose projection` 的任何实现验证。
- 仍未验证的结论：`companion prose projection`、`selected-next-step linkage projection` 与 artifact consistency audit 仍需各自独立 gate 验证，不能从当前 recency 通过直接推出。

## Open Items

- 未决项：下一会话应把用户已选定的 A2 收窄成新的 planning-gate；是否先做完整 companion prose projection，还是再把 A2 进一步切成更窄 slice，需要在新 gate 中固定。
- 已知风险：当前 workspace 仍有大量与本次 safe stop 不同轨道的脏改动，尤其是 bridge/runtime、extension、review 与多条历史 design docs；下一会话不能把这些脏状态误读为全部属于 recency gate。
- 不能默认成立的假设：不能默认 recency 语义稳定就等于 prose 决策链也已可投影；不能默认 `direction-candidates-after-phase-35.md` 的所有 legacy entries 已完成一致性审计；不能默认当前 progress artifact 已同步所有 future candidate semantics。

## Next Step Contract

- 下一会话建议只推进：围绕 `design_docs/project-progress-global-direction-candidates-recency-semantics-followup-direction-analysis.md` 起一个新的窄 scope planning-gate，优先落用户已选定的 A2 `companion prose projection`。
- 下一会话明确不做：不要在同一切片里同时做 companion prose、selected-next-step linkage 与 artifact audit；不要把 recency gate 再打开；不要顺手扩到 UI/host integration。
- 为什么当前应在这里停下：当前 gate 已经把“latest section 到底如何判定”这个基础语义完整回答；继续前进就会跨进新语义层，必须先回到新的 planning-gate，而不是在 safe stop 上直接扩 scope。

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Why This Stage Can Close

- 当前大阶段到这里可以结束的原因：`Global Direction-Candidates Section Recency Semantics` 的完成定义已经满足，contract、实现、targeted tests 与真实 artifact refresh 都已成立，且当前仓库已重新回到 `no active planning-gate`。
- 当前不继续把更多内容塞进本阶段的原因：后续 companion prose / selected-next-step / audit 都属于新的控制路径；若在当前 gate 内继续推进，会把已经收口的基础语义 gate 与新的 higher-level projection gate 混在一起。

## Planning-Gate Return

- 应回到的 planning-gate 位置：当前无 active planning-gate；下一次收敛应回到 `design_docs/project-progress-global-direction-candidates-recency-semantics-followup-direction-analysis.md` 与 `design_docs/direction-candidates-after-phase-35.md` 当前推荐的 companion prose 入口。
- 下一阶段候选主线：A `companion prose projection`（推荐，且用户已进一步选到 A2 完整 companion prose projection）、B `selected-next-step linkage projection`、C `global direction-candidates artifact consistency audit`。
- 下一阶段明确不做：不重新打开 recency semantics gate；不把三条候选主线混成同一条 planning-gate；不在没有新 gate 的情况下继续写 companion prose 代码。

## Conditional Blocks

### phase-acceptance-close

Trigger:
本次 safe stop 是对 `Global Direction-Candidates Section Recency Semantics` 的正式 stage-close，当前 gate 已完成并关闭。

Required fields:

- Acceptance Basis: `design_docs/stages/planning-gate/2026-04-26-global-direction-candidates-section-recency-semantics.md` 已达到 stop condition，且 Result 段已明确记录 recency contract、实现、targeted probe 与 artifact refresh 全部成立。
- Automation Status: `pytest tests/test_progress_graph_doc_projection.py -q` 通过（3 passed），覆盖了 recency probe。
- Manual Test Status: 已 spot check 真实 `.codex/progress-graph/latest.json` / `.dot` / `.html` 刷新结果与 authority state 口径。
- Checklist/Board Writeback Status: Checklist、Phase Map、checkpoint 与 current handoff mirror 的 pointer footprint 已准备同步到本次 safe stop。

Verification expectation:
对当前 stage-close，必须同时看到 gate 关闭、targeted pytest 通过、真实 artifact 刷新，以及 safe-stop pointer footprint 写回；当前除了 mirror rotation 尚待执行外，其余验收依据都已具备。

Refs:

- `design_docs/stages/planning-gate/2026-04-26-global-direction-candidates-section-recency-semantics.md`
- `tests/test_progress_graph_doc_projection.py`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`

### code-change

Trigger:
本次 handoff 覆盖了 progress graph projection 代码、针对性测试与真实 artifact 的改动，因此属于 code-change。

Required fields:

- Touched Files: `tools/progress_graph/doc_projection.py`、`tests/test_progress_graph_doc_projection.py`、`.codex/progress-graph/latest.json`、`.codex/progress-graph/latest.dot`、`.codex/progress-graph/latest.html`、`design_docs/stages/planning-gate/2026-04-26-global-direction-candidates-section-recency-semantics.md`、`design_docs/project-progress-global-direction-candidates-recency-semantics-followup-direction-analysis.md`。
- Intent of Change: 稳定 `direction-candidates-global` 的 latest/current 判定，使其不再依赖 numbered section 的物理顺序，而按日期语义与更早位置 tie-break 选择 latest section。
- Tests Run: `pytest tests/test_progress_graph_doc_projection.py -q`。
- Untested Areas: 未覆盖 companion prose / linkage / audit 路径；未重跑 progress graph 全套；未重跑 VS Code extension 或 host preview 验证。

Verification expectation:
本次 code-change 至少需要一组与 recency 控制路径直接对齐的 targeted tests，并且真实 artifact 已刷新；当前这两项已成立，但全仓更宽回归仍留给后续切片。

Refs:

- `tools/progress_graph/doc_projection.py`
- `tests/test_progress_graph_doc_projection.py`
- `.codex/progress-graph/latest.json`
- `design_docs/stages/planning-gate/2026-04-26-global-direction-candidates-section-recency-semantics.md`

### dirty-worktree

Trigger:
生成 handoff 时，workspace 中仍存在大量未提交修改，且其中不少超出当前 recency safe stop 边界。

Required fields:

- Dirty Scope: 当前脏改动覆盖 `.codex/`、`design_docs/`、`tools/progress_graph/`、`src/runtime/orchestration/`、`vscode-extension/`、`review/` 等区域。
- Relevance to Current Handoff: 本次 handoff 直接相关的是 recency gate 对应的 progress graph 文件、真实 artifact 与状态面；bridge/runtime、extension、release 与更早阶段的 design docs 脏改动不应自动归入本次收口。
- Do Not Revert Notes: 下一会话不得把当前大量 dirty worktree 视为本次 gate 可统一回退对象；继续 A2 前应先按 `authoritative_refs` 与 workspace reality 区分 recency 主线相关与无关的脏改。
- Need-to-Inspect Paths: `tools/progress_graph/doc_projection.py`、`tests/test_progress_graph_doc_projection.py`、`.codex/progress-graph/latest.json`、`.codex/progress-graph/latest.dot`、`.codex/progress-graph/latest.html`、`design_docs/stages/planning-gate/2026-04-26-global-direction-candidates-section-recency-semantics.md`、`design_docs/project-progress-global-direction-candidates-recency-semantics-followup-direction-analysis.md`、`design_docs/Project Master Checklist.md`、`design_docs/Global Phase Map and Current Position.md`、`.codex/checkpoints/latest.md`、`.codex/handoffs/`。

Verification expectation:
dirty 状态已由当前 workspace reality 明确成立，且显著超出本次 gate 边界；接手方必须先核对现实工作树，而不能只依赖 handoff 正文判断哪些改动属于当前主线。

Refs:

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/checkpoints/latest.md`
- `.codex/handoffs/CURRENT.md`

## Other

None.
