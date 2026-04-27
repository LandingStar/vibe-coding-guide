---
handoff_id: 2026-04-26_0639_project-progress-doc-loop-projection-and-snapshot-persistence_stage-close
entry_role: canonical
kind: stage-close
status: superseded
scope_key: project-progress-doc-loop-projection-and-snapshot-persistence
safe_stop_kind: stage-complete
created_at: 2026-04-26T06:39:43+08:00
supersedes: 2026-04-24_1013_scratch-lightweight-recovery-protocol_stage-close
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
  - design_docs/direction-candidates-after-phase-35.md
  - design_docs/stages/planning-gate/2026-04-26-project-progress-doc-loop-projection-and-snapshot-persistence.md
  - design_docs/project-progress-doc-loop-projection-followup-direction-analysis.md
conditional_blocks:
  - phase-acceptance-close
  - code-change
  - dirty-worktree
other_count: 0
---

# Summary

本会话完成 `Project Progress Doc-Loop Projection And Snapshot Persistence` 的 stage-close：新增 `tools/progress_graph/doc_projection.py`，把 checkpoint / planning-gate / checklist 投影成真实 progress snapshots，写出 `.codex/progress-graph/latest.json`，补齐 targeted tests，并把 gate、Checklist、Phase Map、checkpoint 与方向候选同步到 `gate complete + 无 active planning-gate + 下一推荐为 user-facing graph export surface` 的口径。当前仓库处于可恢复 safe stop。

## Boundary

- 完成到哪里：`Project Progress Doc-Loop Projection And Snapshot Persistence` 已完成最小 projection contract、实现与窄验证；当前三类真实来源 `checkpoint-current`、`planning-gates-index`、`project-checklist-current` 已可生成并追加到 `.codex/progress-graph/latest.json`；相关状态面已同步到当前 gate 关闭后的口径，且 `design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-landing-dispatch-integration.md` 继续保持 `PAUSED`。
- 为什么这是安全停点：当前 active gate 已关闭，当前切片内的代码、targeted tests、真实 workspace artifact 写出与状态面回写都已完成；下一步已经明显切换为新的 consumer 选择，而不是继续扩写当前 projection slice。
- 明确不在本次完成范围内的内容：不进入 Graphviz / React Flow export schema；不扩 direction-analysis / phase map projection 与 richer linkage inference；不让 scheduler / daemon / orchestration bridge runtime 直接消费当前 history；不恢复暂停中的 landing dispatch integration 主线。

## Authoritative Sources

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `design_docs/stages/planning-gate/2026-04-26-project-progress-doc-loop-projection-and-snapshot-persistence.md`
- `design_docs/project-progress-doc-loop-projection-followup-direction-analysis.md`

## Session Delta

- 本轮新增：`.codex/handoffs/history/2026-04-26_0639_project-progress-doc-loop-projection-and-snapshot-persistence_stage-close.md`、`tools/progress_graph/doc_projection.py`、`tests/test_progress_graph_doc_projection.py`、`design_docs/project-progress-doc-loop-projection-slice1-draft.md`、`design_docs/project-progress-doc-loop-projection-followup-direction-analysis.md`、`.codex/progress-graph/latest.json`。
- 本轮修改：`tools/progress_graph/__init__.py`、`design_docs/stages/planning-gate/2026-04-26-project-progress-doc-loop-projection-and-snapshot-persistence.md`、`design_docs/Project Master Checklist.md`、`design_docs/Global Phase Map and Current Position.md`、`design_docs/direction-candidates-after-phase-35.md`、`.codex/checkpoints/latest.md`。
- 本轮形成的新约束或新结论：progress graph 的第一批真实 consumer 只需 checkpoint / planning-gate / checklist 三类薄 parser，即可形成可追加的 snapshot history；当前下一条窄主线默认应先固定 `user-facing graph export surface`，而不是继续把 projection 直接拉回 runtime 调度主线。

## Verification Snapshot

- 自动化：`pytest tests/test_progress_graph_doc_projection.py` 通过（2 passed）；`pytest tests/test_progress_graph.py tests/test_progress_graph_doc_projection.py` 联合通过（8 passed）；`tools/progress_graph/doc_projection.py`、`tests/test_progress_graph_doc_projection.py`、`tools/progress_graph/__init__.py` 与相关状态文档均已通过错误检查。
- 手测：在真实 workspace 中调用 `write_doc_progress_history(Path.cwd())`，确认 `.codex/progress-graph/latest.json` 成功写出且存在性为真，并可作为当前 snapshot history 入口读取。
- 未完成验证：未做 user-facing export / UI consumer 验证；未做 scheduler-facing integration 验证；未重跑与本切片无直接关系的全仓大回归。
- 仍未验证的结论：direction-analysis / phase map projection、richer linkage inference、以及面向展示或调度的最终导出 schema 仍需后续独立切片验证。

## Open Items

- 未决项：是否立即进入 `user-facing graph export surface`；后续是否补 `doc source enrichment and linkage refinement`；以及何时才让 runtime/scheduler 消费 `global_ready_nodes()`。
- 已知风险：当前工作树仍然很脏，且包含与本次 handoff 边界无关的 bridge/runtime、release、extension 与 review 改动；当前 progress graph 只覆盖三类 doc sources，若不先说明边界，后续容易把当前 snapshot 误读为“全项目推进图”。
- 不能默认成立的假设：不能默认 `.codex/progress-graph/latest.json` 已经等于最终用户展示 schema；不能默认 paused 的 landing dispatch integration 应在 export surface 之前恢复；不能默认当前薄 parser 已覆盖全部高价值 doc-loop 来源。

## Next Step Contract

- 下一会话建议只推进：优先起一个窄 scope planning-gate，收口 `user-facing graph export surface`，把当前 `.codex/progress-graph/latest.json` 变成稳定的 Graphviz / React Flow / compound-graph-friendly 展示输入。
- 下一会话明确不做：不在同一切片里同时补更多 doc sources、调度集成与完整 UI；不恢复 `design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-landing-dispatch-integration.md`；不把当前 export surface 问题扩成 scheduler/runtime 主线。
- 为什么当前应在这里停下：当前切片已经把“progress graph 是否有真实 doc-loop 数据源与持久化快照”这个问题完整回答；继续往下做的内容已经属于新的 consumer contract，而不是本次 projection stage 的自然延伸。

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Why This Stage Can Close

- 当前大阶段到这里可以结束的原因：`Project Progress Doc-Loop Projection And Snapshot Persistence` 的完成定义已经满足，projection contract、实现、真实 workspace snapshot 写出、targeted tests 与状态面回写都已经成立；当前仓库重新回到无 active planning-gate 的稳定口径。
- 当前不继续把更多内容塞进本阶段的原因：剩余工作已经明显转向“谁消费这份 snapshot history”这一新阶段问题；继续推进会跨出当前 stage 的 `projection + persistence` 边界，直接进入 export、source enrichment 或 runtime integration 的新切片。

## Planning-Gate Return

- 应回到的 planning-gate 位置：当前无 active planning-gate；下一次收敛应回到 `design_docs/project-progress-doc-loop-projection-followup-direction-analysis.md` 与 `design_docs/direction-candidates-after-phase-35.md` 的最新候选位置。
- 下一阶段候选主线：`user-facing graph export surface`（推荐）、`doc source enrichment and linkage refinement`、`scheduler-facing ready frontier integration`；`orchestration bridge landing dispatch integration` 继续保持 `PAUSED`。
- 下一阶段明确不做：不在未起新 gate 的情况下继续扩当前 projection gate；不把 export、source enrichment、runtime integration 三条线混成同一切片；不默认恢复暂停中的 bridge landing dispatch 主线。

## Conditional Blocks

### phase-acceptance-close

Trigger:
本次 safe stop 是对 `Project Progress Doc-Loop Projection And Snapshot Persistence` 的正式 stage-close，当前 gate 已完成并关闭。

Required fields:

- Acceptance Basis: `design_docs/stages/planning-gate/2026-04-26-project-progress-doc-loop-projection-and-snapshot-persistence.md` 已完成 projection contract、实现、targeted tests 与 `.codex/progress-graph/latest.json` 写出，stop condition 已满足。
- Automation Status: `pytest tests/test_progress_graph_doc_projection.py` 通过（2 passed），联合 `pytest tests/test_progress_graph.py tests/test_progress_graph_doc_projection.py` 通过（8 passed）；相关 Python 文件与状态文档已完成错误检查，canonical handoff 也会纳入结构校验。
- Manual Test Status: 已在真实 workspace 中执行 `write_doc_progress_history(Path.cwd())`，确认 `latest.json` 写出成功并可作为当前 snapshot history 入口。
- Checklist/Board Writeback Status: Checklist、Phase Map、direction candidates 与 checkpoint 已同步到 `gate complete + 无 active planning-gate + 下一推荐为 export surface` 的口径；safe-stop handoff footprint 由同一 bundle 继续刷新。

Verification expectation:
对当前 stage-close，至少需要同时看到 gate 关闭、窄测试通过、真实 artifact 写出、以及状态板回写四项证据；本次四项都已具备，缺口仅剩下一阶段 consumer 选择而非本阶段验收。

Refs:

- `design_docs/stages/planning-gate/2026-04-26-project-progress-doc-loop-projection-and-snapshot-persistence.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/direction-candidates-after-phase-35.md`

### code-change

Trigger:
本次 handoff 覆盖了新的 Python projection 代码、导出 surface 更新、targeted tests 与真实 generated artifact，因此属于 code-change。

Required fields:

- Touched Files: `tools/progress_graph/doc_projection.py`、`tools/progress_graph/__init__.py`、`tests/test_progress_graph_doc_projection.py`、`.codex/progress-graph/latest.json`，以及与其同步的 planning-gate / follow-up / Checklist / Phase Map / checkpoint 文档。
- Intent of Change: 把 progress graph foundation 从空模型推进到真实 doc-loop consumer，让 checkpoint / planning-gate / checklist 能被投影为当前 snapshot history，并以单文件 JSON 持久化，而不引入通用 markdown parser 或 runtime/scheduler 耦合。
- Tests Run: `pytest tests/test_progress_graph_doc_projection.py`；`pytest tests/test_progress_graph.py tests/test_progress_graph_doc_projection.py`；真实 workspace 中执行 `write_doc_progress_history(Path.cwd())` 并确认 `latest.json` 写出。
- Untested Areas: 未覆盖 export surface / UI consumer；未覆盖 scheduler-facing integration；未覆盖更丰富 doc sources 与大规模历史数据性能。

Verification expectation:
本次 code-change 需要至少有一组 targeted tests 和一组真实 workspace 写出验证，且未验证范围必须明确保留在后续切片；当前验证满足这一要求，但没有把全仓回归或展示层消费混入本次 slice。

Refs:

- `tools/progress_graph/doc_projection.py`
- `tests/test_progress_graph_doc_projection.py`
- `.codex/progress-graph/latest.json`
- `design_docs/stages/planning-gate/2026-04-26-project-progress-doc-loop-projection-and-snapshot-persistence.md`

### dirty-worktree

Trigger:
生成 handoff 时，workspace 中仍存在大量未提交与未跟踪改动，且其中不少不属于本次 progress graph projection stage 的直接边界。

Required fields:

- Dirty Scope: 当前脏改动覆盖 `.codex/`、`design_docs/`、`tools/progress_graph/`、`src/runtime/orchestration/`、`vscode-extension/`、`review/`、`release/` 等区域。
- Relevance to Current Handoff: 本次 handoff 直接覆盖 `tools/progress_graph/`、`tests/test_progress_graph_doc_projection.py`、`.codex/progress-graph/latest.json`、当前 planning-gate 与状态面文档；其余 bridge/runtime、extension、release 等脏改动属于并行或既有轨道，不能自动归入本次 stage-close。
- Do Not Revert Notes: 下一会话不得把当前 dirty worktree 一概视为本次切片可回滚对象；若继续 export surface 或 handoff writeback，应先区分 progress graph 主线与 bridge/runtime/release/extension 轨道。
- Need-to-Inspect Paths: `tools/progress_graph/doc_projection.py`、`tests/test_progress_graph_doc_projection.py`、`.codex/progress-graph/latest.json`、`design_docs/stages/planning-gate/2026-04-26-project-progress-doc-loop-projection-and-snapshot-persistence.md`、`design_docs/project-progress-doc-loop-projection-followup-direction-analysis.md`、`design_docs/Project Master Checklist.md`、`design_docs/Global Phase Map and Current Position.md`、`.codex/checkpoints/latest.md`、`.codex/handoffs/`，以及仍然 dirty 的 `src/runtime/orchestration/` 与 `vscode-extension/` 区域。

Verification expectation:
dirty 状态已通过当前 workspace 变更摘要确认存在，且明显超出本次 stage 边界；下一会话 intake 必须继续以 workspace 现实状态优先，而不能假设 handoff 中文件清单等于全部相关差异。

Refs:

- `design_docs/Project Master Checklist.md`
- `.codex/checkpoints/latest.md`
- `.codex/handoffs/CURRENT.md`

## Other

None.
