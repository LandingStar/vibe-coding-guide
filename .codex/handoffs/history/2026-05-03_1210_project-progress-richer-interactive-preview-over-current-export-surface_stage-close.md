---
handoff_id: 2026-05-03_1210_project-progress-richer-interactive-preview-over-current-export-surface_stage-close
entry_role: canonical
kind: stage-close
status: superseded
scope_key: project-progress-richer-interactive-preview-over-current-export-surface
safe_stop_kind: stage-complete
created_at: 2026-05-03T12:10:19+08:00
supersedes: 2026-04-30_1818_orchestration-bridge-delivery-signal-integration-hook_stage-close
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
  - design_docs/project-progress-richer-interactive-preview-followup-direction-analysis.md
  - design_docs/direction-candidates-after-phase-35.md
  - design_docs/project-progress-richer-interactive-preview-slice1-draft.md
  - design_docs/stages/planning-gate/2026-04-30-project-progress-richer-interactive-preview-over-current-export-surface.md
conditional_blocks:
  - phase-acceptance-close
  - code-change
  - dirty-worktree
other_count: 0
---

# Summary

本会话完成 `Project Progress Richer Interactive Preview Over Current Export Surface` 的 stage-close：把现有 HTML / host preview 的第一版交互层稳定在 graph-local search、status filter、selected node detail、focused reveal 与 zoom surface 上，同时保持 `doc_projection`、`export` schema 与 host wiring 不变；随后通过 `tests/test_progress_graph_html_preview.py` 的 focused validation（4 passed）、补齐 follow-up direction analysis，并将 Checklist / Phase Map / checkpoint / direction candidates / progress-graph artifacts / `CURRENT.md` 收口到同一 safe-stop 口径。当前可以安全停下，因为这条 gate 的 stop condition 已满足，仓库重新回到无 active planning-gate 状态，下一会话只需从已固定的 graph follow-up 候选中选一条新的窄主线继续。

## Boundary

- 完成到哪里：`design_docs/stages/planning-gate/2026-04-30-project-progress-richer-interactive-preview-over-current-export-surface.md` 已正式关闭；当前 HTML / host preview 已稳定具备 graph-local search、status filter、selected node detail、focused reveal、zoom controls 与 Ctrl+滚轮缩放；`design_docs/project-progress-richer-interactive-preview-followup-direction-analysis.md` 与 `design_docs/direction-candidates-after-phase-35.md` 已固定 close 后的下一步候选；Checklist / Phase Map / checkpoint / `CURRENT.md` 与 `.codex/progress-graph/latest.json` / `.dot` / `.html` 已同步到同一 safe-stop 口径。
- 为什么这是安全停点：当前 gate 的 stop condition 只要求交互 contract、最小 artifact-side interaction 与 focused validation 成立；这些条件已满足，且当前仓库重新回到无 active planning-gate 状态，后续工作已转化为新的方向选择，而不是本 gate 内的未完尾项。
- 明确不在本次完成范围内的内容：不在本轮进入 preview freshness signaling / dirty badge / watcher；不把已记录的 compound node / expandable roll-up 需求直接并入当前 gate；不回到 handoff / safe-stop projection 扩面；不重写 renderer 或重新打开 `doc_projection.py` / `export.py` schema。

## Authoritative Sources

- design_docs/Project Master Checklist.md
- design_docs/Global Phase Map and Current Position.md
- design_docs/project-progress-richer-interactive-preview-followup-direction-analysis.md
- design_docs/direction-candidates-after-phase-35.md
- design_docs/project-progress-richer-interactive-preview-slice1-draft.md
- design_docs/stages/planning-gate/2026-04-30-project-progress-richer-interactive-preview-over-current-export-surface.md

## Session Delta

- 本轮新增：新增 `design_docs/project-progress-richer-interactive-preview-followup-direction-analysis.md`，把当前 gate 收口后的下一步重新压窄为 preview freshness / workflow polish、compound node 可展开 roll-up，以及 handoff / safe-stop projection 三条候选；新增 canonical handoff `.codex/handoffs/history/2026-05-03_1210_project-progress-richer-interactive-preview-over-current-export-surface_stage-close.md`。
- 本轮修改：当前 planning-gate 已切为 `COMPLETED`；`design_docs/direction-candidates-after-phase-35.md`、Checklist、Phase Map、checkpoint、`.codex/progress-graph/latest.json` / `.dot` / `.html` 与 `CURRENT.md` 已同步到同一 graph safe-stop 口径。
- 本轮形成的新约束或新结论：当前 richer interactive preview 的第一刀已足够收口为独立 stage-close；“大型项目 graph 规模控制”需求保留为单独候选，不应顺势并入当前已完成切片；当前更稳的默认恢复线应先回到 preview freshness / workflow polish，而不是直接继续实现 compound node。

## Verification Snapshot

- 自动化：`& ".venv-release-test/Scripts/python.exe" -m pytest tests/test_progress_graph_html_preview.py -q` 已通过（4 passed）；真实 `.codex/progress-graph/latest.json` / `.dot` / `.html` 已按最新 authority state 重新写出；本次 canonical handoff 已通过 `validate_handoff.py` 校验，且 `refresh_current.py` 已完成 `CURRENT.md` 轮转。
- 手测：此前已对 repo artifact 与外部测试工作区中的 preview 交互（尺寸修复、zoom controls、Ctrl+滚轮缩放）做过行为 spot check；本轮额外复核了 planning-gate、follow-up direction analysis、direction candidates、Checklist、Phase Map 与 checkpoint 的边界一致性。
- 未完成验证：未重跑 Python 全量测试；未在本轮 close bundle 后追加新的 VS Code host 点击级回归；未对 follow-up 候选 A/B/C 做实现级验证。
- 仍未验证的结论：当前只能确认 richer interactive preview 的第一版交互层与 close bundle 成立，尚不能据此推出 preview freshness、compound node expand/collapse 或 handoff / safe-stop projection 已经具备实现边界。

## Open Items

- 未决项：仍需从 `design_docs/project-progress-richer-interactive-preview-followup-direction-analysis.md` 中选定下一条 graph 窄主线；当前尚未创建新的 planning-gate。
- 已知风险：workspace 仍是 dirty worktree，除当前 graph close bundle 外，还并行存在 bridge/runtime、extension runtime/package management 与若干 earlier safe-stop 文档轨道；若下一会话不先区分这些路径，容易误把并行轨道当成当前 graph handoff 的待收尾项。
- 不能默认成立的假设：不能把当前第一版交互层视为 preview freshness 已完成；不能把 compound node 需求已记录等同于已进入执行；不能把当前 graph safe stop 视为 handoff / safe-stop family source coverage 已经补齐。

## Next Step Contract

- 下一会话建议只推进：从 `design_docs/project-progress-richer-interactive-preview-followup-direction-analysis.md` 中重新选择一条 graph follow-up 窄主线；默认优先进入 `Candidate A. Preview Freshness Signaling And Workflow Polishing`。
- 下一会话明确不做：不要重新打开 `design_docs/stages/planning-gate/2026-04-30-project-progress-richer-interactive-preview-over-current-export-surface.md`；不要把 freshness、compound node 与 handoff / safe-stop projection 混进同一切片；不要在没有新 planning-gate 的前提下继续修改当前 gate 的 contract 文本。
- 为什么当前应在这里停下：当前 gate 已经回答了“现有 HTML / host preview 上的第一版更强交互能否成立”这个问题；继续前进已经不再是收尾，而是进入新的候选方向与新的 planning-gate 激活阶段。

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Why This Stage Can Close

- 当前大阶段到这里可以结束的原因：当前 `project-progress` 用户交互主线的第一刀已经完成了其最小 contract、实现、focused validation 与状态面 writeback；当前仓库也重新回到无 active planning-gate 状态，因此已经具备稳定可交接的 safe-stop。
- 当前不继续把更多内容塞进本阶段的原因：preview freshness、compound node 规模控制与 handoff / safe-stop projection 都会引入新的控制面、数据边界或 host workflow 语义；继续追加会直接跨出当前 gate 的 narrow scope，而不是“把它做完”。

## Planning-Gate Return

- 应回到的 planning-gate 位置：当前仓库已回到无 active planning-gate 状态；下一次继续时，应先回到 `design_docs/project-progress-richer-interactive-preview-followup-direction-analysis.md` 与 `design_docs/direction-candidates-after-phase-35.md` 顶部最新 section，从中选择新的 graph 窄主线并创建新的 planning-gate。
- 下一阶段候选主线：A `preview freshness signaling and workflow polishing`（推荐）、B `hierarchical roll-up / expandable compound node over current preview`、C `handoff / safe-stop projection before further interaction expansion`。
- 下一阶段明确不做：不重新打开当前 richer interactive preview gate；不在没有新 gate 的前提下继续往 `html_preview.py` 里叠新的交互需求；不把 graph source coverage 与当前 preview polish 混成同一刀。

## Conditional Blocks

### phase-acceptance-close

Trigger:
本次 handoff 是 `Project Progress Richer Interactive Preview Over Current Export Surface` 的正式 stage-close，需要为当前 graph 交互切片的完成边界、验证依据与状态板 writeback 提供最小验收信息。

Required fields:

- Acceptance Basis: 当前 planning-gate 的 stop condition 已满足：graph-local interaction contract、最小 artifact-side interaction 与 focused validation 均已成立，且 no-change boundary 仍保持完整。
- Automation Status: `tests/test_progress_graph_html_preview.py` 已通过（4 passed）；真实 `.codex/progress-graph/latest.json` / `.dot` / `.html` 已按最新 authority state 刷新；canonical handoff 已通过 `validate_handoff.py`，`refresh_current.py` 已完成 mirror 轮转。
- Manual Test Status: 当前 gate 边界内的 preview 交互此前已完成 repo artifact 与外部测试工作区的行为 spot check；本轮额外复核了 planning-gate / follow-up direction analysis / direction candidates / Checklist / Phase Map / checkpoint 的状态面一致性。
- Checklist/Board Writeback Status: Checklist、Phase Map、checkpoint、`design_docs/direction-candidates-after-phase-35.md` 与 `design_docs/project-progress-richer-interactive-preview-followup-direction-analysis.md` 已同步到当前 safe-stop 口径。

Verification expectation:
对本次 stage-close，必须同时看到当前 gate 关闭、focused validation 通过、follow-up direction surface 明确，以及 Checklist / Phase Map / checkpoint / `CURRENT.md` 对齐到同一 canonical handoff；当前这些条件都已成立。

Refs:

- design_docs/stages/planning-gate/2026-04-30-project-progress-richer-interactive-preview-over-current-export-surface.md
- design_docs/project-progress-richer-interactive-preview-followup-direction-analysis.md
- design_docs/Project Master Checklist.md
- design_docs/Global Phase Map and Current Position.md
- .codex/checkpoints/latest.md
- .codex/handoffs/CURRENT.md

### code-change

Trigger:
本次 handoff 覆盖范围内包含当前 graph 交互切片的真实实现与测试改动，因此需要显式记录代码边界、验证面与仍未覆盖的区域。

Required fields:

- Touched Files: `tools/progress_graph/html_preview.py`、`tests/test_progress_graph_html_preview.py`、`vscode-extension/src/views/progressGraphPreview.ts`、`vscode-extension/src/views/progressGraphArtifacts.ts`、`vscode-extension/src/extension.ts`、`vscode-extension/package.json`、`design_docs/project-progress-richer-interactive-preview-slice1-draft.md`、`design_docs/project-progress-user-interaction-after-bridge-mvp-direction-analysis.md`、`design_docs/stages/planning-gate/2026-04-30-project-progress-richer-interactive-preview-over-current-export-surface.md`。
- Intent of Change: 在保持现有 export / host contract 不变的前提下，把当前 preview 提升为可直接探索项目推进状态的最小交互面，补齐 graph-local filter、detail、focused reveal 与 zoom，并让 host preview 继续直接承载 raw `latest.html`。
- Tests Run: `& ".venv-release-test/Scripts/python.exe" -m pytest tests/test_progress_graph_html_preview.py -q`（4 passed）。
- Untested Areas: 未重跑 Python 全量测试；未在本轮 close bundle 后补新的 VS Code host 点击级回归；未进入 freshness、compound node 或 handoff / safe-stop projection 的实现级验证。

Verification expectation:
接手方应把当前代码改动理解为“现有 preview 上的第一版交互层已稳定成立”，而不是“更宽的 graph interaction / source coverage 已全部完成”；若下一步继续扩大交互面，必须通过新的 planning-gate 与新的 focused validation 进入。

Refs:

- tools/progress_graph/html_preview.py
- tests/test_progress_graph_html_preview.py
- vscode-extension/src/views/progressGraphPreview.ts
- vscode-extension/src/views/progressGraphArtifacts.ts
- design_docs/project-progress-richer-interactive-preview-slice1-draft.md
- design_docs/stages/planning-gate/2026-04-30-project-progress-richer-interactive-preview-over-current-export-surface.md

### dirty-worktree

Trigger:
生成 handoff 时，workspace 仍保留当前 graph safe-stop bundle、本轮 progress-graph artifact 刷新以及并行 bridge/runtime、extension runtime/package management 等轨道的未提交改动，因此必须显式区分“当前收口结果”与“并行 dirty tracks”。

Required fields:

- Dirty Scope: 直接属于当前 graph close bundle 的路径包括 `.codex/checkpoints/latest.md`、`.codex/handoffs/CURRENT.md`、`.codex/handoffs/history/2026-05-03_1210_project-progress-richer-interactive-preview-over-current-export-surface_stage-close.md`、`.codex/progress-graph/latest.json`、`.codex/progress-graph/latest.dot`、`.codex/progress-graph/latest.html`、`design_docs/Project Master Checklist.md`、`design_docs/Global Phase Map and Current Position.md`、`design_docs/direction-candidates-after-phase-35.md`、`design_docs/project-progress-richer-interactive-preview-followup-direction-analysis.md`、`design_docs/project-progress-richer-interactive-preview-slice1-draft.md`、`design_docs/project-progress-user-interaction-after-bridge-mvp-direction-analysis.md`、`design_docs/stages/planning-gate/2026-04-30-project-progress-richer-interactive-preview-over-current-export-surface.md`、`tools/progress_graph/html_preview.py`；并行仍未提交的轨道还包括 `src/runtime/orchestration/*.py`、`src/pep/executor.py`、`vscode-extension/src/extension.ts`、`vscode-extension/src/setup/runtimeInstaller.ts`、`vscode-extension/src/views/configPanel.ts`、`vscode-extension/tsconfig.json`、`design_docs/stages/planning-gate/2026-04-26-orchestration-bridge-landing-dispatch-integration.md`、`design_docs/orchestration-bridge-landing-dispatch-integration-slice1-draft.md`、`design_docs/v0.9.5-preview-release-followup-direction-analysis.md` 以及 earlier canonical handoff / decision-log 路径。
- Relevance to Current Handoff: 第一组路径直接构成当前 graph gate close 的 safe-stop reality；第二组 bridge / extension / earlier safe-stop 轨道不属于本 handoff 本身，但会影响下一会话对 workspace reality 的判断，必须与当前 graph close bundle 显式区分。
- Do Not Revert Notes: 不要回退当前 graph close bundle 对 gate / Checklist / Phase Map / checkpoint / `CURRENT.md` / canonical handoff / `.codex/progress-graph/latest.*` 的同步结果；也不要把并行的 bridge/runtime 或 extension runtime/package management 改动误当成当前 handoff 的噪音清理掉，它们是工作区真实存在的并行轨道。
- Need-to-Inspect Paths: `design_docs/stages/planning-gate/2026-04-30-project-progress-richer-interactive-preview-over-current-export-surface.md`、`design_docs/project-progress-richer-interactive-preview-followup-direction-analysis.md`、`design_docs/Project Master Checklist.md`、`design_docs/Global Phase Map and Current Position.md`、`.codex/checkpoints/latest.md`、`.codex/handoffs/CURRENT.md`、`.codex/handoffs/history/2026-05-03_1210_project-progress-richer-interactive-preview-over-current-export-surface_stage-close.md`、`tools/progress_graph/html_preview.py`、`vscode-extension/src/views/progressGraphPreview.ts`。

Verification expectation:
dirty worktree 已按当前 `git status --short --untracked-files=all` 的现实状态核对；接手方必须先区分“当前 graph close bundle”与“并行 bridge / extension / earlier safe-stop 轨道”，再决定下一条 graph planning-gate 的真实落点。

Refs:

- design_docs/stages/planning-gate/2026-04-30-project-progress-richer-interactive-preview-over-current-export-surface.md
- design_docs/project-progress-richer-interactive-preview-followup-direction-analysis.md
- .codex/checkpoints/latest.md
- .codex/handoffs/CURRENT.md
- tools/progress_graph/html_preview.py

## Other

None.
