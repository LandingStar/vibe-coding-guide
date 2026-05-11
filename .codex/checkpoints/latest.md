# Checkpoint — 2026-05-07T22:12:50.4475544+08:00
## Current Phase
Post-v1.0 — 全部依赖违规消除 + HTTPWorker schema alignment + Multica 借鉴全部完成 + Codex 主链适配与 VS Code extension provider abstraction + 2026-04-23 docs-only 宿主交互/入口面收口 + 2026-04-24 scratch 轻量恢复协议（docs-only 收口完成） + 2026-05-03 project-progress richer interactive preview stage-close
## Active Planning Gate
design_docs/stages/planning-gate/2026-05-07-sigma-graphology-v2-graph-view-poc.md
## Current Handoff
- handoff_id: 2026-05-03_1210_project-progress-richer-interactive-preview-over-current-export-surface_stage-close
- source_path: .codex/handoffs/history/2026-05-03_1210_project-progress-richer-interactive-preview-over-current-export-surface_stage-close.md
- scope_key: project-progress-richer-interactive-preview-over-current-export-surface
- created_at: 2026-05-03T12:10:19+08:00
## Current Todo
- [x] 已完成当前基础设施评估：现阶段更适合表述为 explorer hardening + control snapshot groundwork，而不是 full control panel pivot
- [x] 已完成 `project-progress-preview-freshness-signaling-and-workflow-polishing` close writeback，并确认 `missing` / `stale` / `failed` helper-level spot check 通过
- [x] 已创建并激活 design_docs/stages/planning-gate/2026-05-06-project-progress-graph-interactive-control-surface.md
- [x] 已创建 Slice 1 草案：design_docs/project-progress-graph-interactive-control-surface-slice1-draft.md
- [x] 已固定当前新主线的第一刀边界：read-only control overlay + orchestration compact snapshot contract
- [x] 已补当前优先入口草案：design_docs/project-progress-graph-interactive-control-surface-snapshot-schema-draft.md
- [x] 已创建 Slice 2 草案：design_docs/project-progress-graph-interactive-control-surface-slice2-projection-helper-contract-draft.md
- [x] 已创建 Slice 2 草案：design_docs/project-progress-graph-interactive-control-surface-slice2-graph-binding-contract-draft.md
- [x] 已创建 Slice 3 草案：design_docs/project-progress-graph-interactive-control-surface-slice3-overlay-consumer-surface-draft.md
- [x] 已按 scope interrupt 记录后续 protocol 清理 gate：design_docs/stages/planning-gate/2026-05-06-rule-protocol-askquestions-wording-cleanup.md
- [x] 已记录保留需求 gate：design_docs/stages/planning-gate/2026-05-05-progress-graph-recursive-work-log-attachment.md
- [x] 已将 snapshot schema draft 翻译为 projection helper 的最小输入/输出 contract
- [x] 已固定 graph binding 的 canonical fields、raw target / scoped key 语义与最小校验边界
- [x] 已定义最小 read-only host overlay 消费面，当前固定为 freshness shell + control summary rail + bound target detail companion + unbound runtime panel
- [x] 已落地 `tools/progress_graph/control_snapshot.py` 最小 pure helper 骨架，并导出 `build_control_snapshot(...)`
- [x] 已落地 `tools/progress_graph/control_binding.py` 最小 binding normalizer 骨架，并导出 `normalize_control_bindings(...)`
- [x] 已新增 focused tests：tests/test_progress_graph_control_snapshot.py
- [x] 已完成 progress_graph 窄范围回归验证：`pytest tests/test_progress_graph_control_snapshot.py tests/test_progress_graph_export.py tests/test_progress_graph_html_preview.py -q` 通过
- [x] 已在 `vscode-extension/src/views/progressGraphPreview.ts` 落最小 read-only overlay consumer skeleton：summary rail + bound target detail companion + unbound runtime panel
- [x] overlay skeleton 已接入 graph payload readiness / raw-target companion wiring 占位，并保持 direct-action boundary 不变
- [x] 已把 `write_control_snapshot(...)` 接入 `vscode-extension/src/views/progressGraphArtifacts.ts` 的真实 regenerate pipeline，并把 `control-snapshot.json` 纳入同一条 artifact 输出链
- [x] 已把 `write_control_snapshot(...)` 的默认 source 接到 `.codex/checkpoints/latest.md` + active planning-gate；当前重新生成的 `.codex/progress-graph/control-snapshot.json` 已成为非空 doc-loop-backed snapshot
- [x] 已完成 `npm run build`（workspace task: `npm: build - vscode-extension`）验证 overlay consumer 改动可编译
- [ ] 保持 no-change boundary：当前不进入 direct mutation controls、daemon persistence / replay 或新的 renderer 重写
- [x] 已将旧的增量宿主增强线暂停在 stable baseline，当前 planning line 已切到 `design_docs/stages/planning-gate/2026-05-07-parallel-v2-graph-renderer-and-library-selection.md`
- [x] 已把真实 doc-loop-backed `BridgeWorkItem` / `BridgeGroupItem` / bindings 输入接到 `write_control_snapshot(...)`，不再继续停留在空 snapshot 入口
- [x] 已完成 focused host spot check：`vscode-extension/src/views/progressGraphPreviewHtml.ts` + `vscode-extension/src/test/progressGraphPreviewHtml.test.ts` 已固定非空 snapshot overlay 与 failed fallback 两条宿主输出路径（2 passed）
- [x] 已完成最小 source coverage 补强第一刀：persisted current handoff mirror `.codex/handoffs/CURRENT.md` 已接入 `write_control_snapshot(...)`，并作为 completed handoff row 进入 unbound runtime panel
- [x] 已完成 escalation source 调研：当前 `review_intake` 仍只落到 in-memory `FeedbackAPI`；escalation 当前没有默认 file sink、默认 output path 或现成 persisted artifact，因此不在本切片内继续扩成新的 persistence contract
- [ ] 若未来仍需要 escalation source coverage，先回到 `design_docs/stages/planning-gate/2026-05-06-escalation-notification-persisted-surface-contract.md`，而不是在当前 gate 内顺手发明新的 file sink contract
- [ ] 后续进入节点呈现增强时，当前第一目标应先复刻更完整的 Obsidian graph view 视觉与浏览语言：低 chrome 关系网络观感、邻接聚焦、cluster/cloud 图感、自由力导式浏览体验与大图可探索性；仍先基于现有 preview / host overlay 推进，不把它立即误扩成新的 renderer 重写
- [ ] 节点团折叠、network control panel 扩展、非线性工作流组件与潜在独立资产化都放在“先复刻 Obsidian graph view 样式”之后的 follow-up slice
- [ ] 当“复刻 Obsidian graph view”达到初步可用时，进入任何 control panel / control surface 深化前都必须先检查 graph 与实际工作对接接口是否已经支持目标状态/动作；若接口未完善，则工作应回到接口处理切片
- [ ] 若决定保留现有 graph 作为稳定 baseline，并并行规划更适合 Obsidian-like graph view 的 V2 展示层，先回到 `design_docs/stages/planning-gate/2026-05-07-parallel-v2-graph-renderer-and-library-selection.md`，不要在当前 slice 内直接把展示架构重做
- [x] 已补 V2 第一刀比较文档：`design_docs/project-progress-v2-graph-library-selection-comparison.md`
- [x] 已补 V2 最小资产边界草案：`design_docs/project-progress-v2-graph-asset-boundary-draft.md`
- [x] 已决定 V2 第一轮 PoC 优先验证 `Sigma.js + Graphology`，并保留 `Cytoscape.js` 作为 folding / control panel 更强的 fallback
- [x] 已创建并激活新的窄 gate：`design_docs/stages/planning-gate/2026-05-07-sigma-graphology-v2-graph-view-poc.md`
- [x] 已创建 adapter shape 草案：`design_docs/project-progress-v2-graph-adapter-shape-draft.md`
- [x] 已创建 focused validation 草案：`design_docs/project-progress-v2-graph-focused-validation-draft.md`
- [x] 已把 `Sigma.js + Graphology` 依赖接入 `vscode-extension/package.json`，并把 `vscode-extension/esbuild.config.mjs` 改为 extension host + webview browser bundle 双构建
- [x] 已把 V2 PoC 接进现有 preview：`vscode-extension/src/views/progressGraphPreview.ts` 现从 `.codex/progress-graph/latest.json` 选图并注入 V2 payload / script URI，`vscode-extension/src/views/progressGraphPreviewHtml.ts` 已注入并行 V2 section，`vscode-extension/src/webviews/progressGraphV2PoC.ts` 已实现 Sigma.js + Graphology + ForceAtlas2 graph-view
- [x] 已完成当前 PoC 的 focused validation：`npm run build` 通过、`vscode-extension/src/test/progressGraphPreviewHtml.test.ts` 已补 V2 shell 注入断言并通过、关键入口 diagnostics clean
- [ ] 继续保持 no-change boundary：当前 V2 PoC 不进入 control panel action semantics，不绕过 graph-to-work 接口检查
- [x] 已完成真实 VS Code 宿主视觉 spot check；此前暴露的 edge=0、Sigma `x/y` 初始化错误与 `project-checklist-current` 零边问题已修复，当前用户验证已确认边可见且无 `x/y` 报错
- [x] 已把当前 PoC 的图感微调推进到可见实现态：`vscode-extension/src/webviews/progressGraphV2PoC.ts` 现已接入 idle label anchors、click-to-focus camera follow，以及 semantic-band seed + ForceAtlas2 cloud tuning；`npm run build` 与关键 diagnostics 持续通过
- [x] 已接入最小 Graph Config：`vscode-extension/src/views/progressGraphPreviewHtml.ts` 现已注入外观 / 力度 / 颜色组配置面，`vscode-extension/src/webviews/progressGraphV2PoC.ts` 已将其接到 renderer 设置、ForceAtlas2 重排与 query-based color groups，并通过 webview state 保留配置
- [x] 已完成当前配置面的 focused validation：`npm run build` 通过、自定义 in-memory helper validation 通过、相关 diagnostics clean
- [x] 已按 Obsidian 官方 Graph/Search 口径收紧颜色组语义：当前颜色组复用 Search 风格核心语法，支持空格 AND、`OR`、`-`、括号、引号、regex 与 `file:`/`path:`/`content:`/`tag:`/`match-case:`/`ignore-case:`，并按列表顺序执行首个命中优先；对应 query semantics validation 已通过
- [ ] 下一刀继续只在当前 PoC slice 内调配置手感与图面读感，不进入 control panel action semantics
## Pending User Decision
(none)
## Direction Candidates
- Selected Line: Sigma Graphology V2 Graph View PoC — source: design_docs/stages/planning-gate/2026-05-07-sigma-graphology-v2-graph-view-poc.md
- Candidate B: Cytoscape.js fallback for stronger folding / control-panel carry — source: design_docs/project-progress-v2-graph-library-selection-comparison.md
- Candidate C: Return to interface handling before panel deepening if graph-to-work contract is insufficient — source: design_docs/project-progress-v2-graph-focused-validation-draft.md
## Key Context Files
- design_docs/Project Master Checklist.md
- design_docs/Global Phase Map and Current Position.md
- .codex/handoffs/CURRENT.md
- .codex/handoffs/history/2026-05-03_1210_project-progress-richer-interactive-preview-over-current-export-surface_stage-close.md
- design_docs/project-progress-graph-interactive-control-surface-direction-analysis.md
- design_docs/stages/planning-gate/2026-05-06-project-progress-graph-interactive-control-surface.md
- design_docs/project-progress-graph-interactive-control-surface-slice1-draft.md
- design_docs/project-progress-graph-interactive-control-surface-snapshot-schema-draft.md
- design_docs/project-progress-graph-interactive-control-surface-slice2-projection-helper-contract-draft.md
- design_docs/project-progress-graph-interactive-control-surface-slice2-graph-binding-contract-draft.md
- design_docs/project-progress-graph-interactive-control-surface-slice3-overlay-consumer-surface-draft.md
- design_docs/stages/planning-gate/2026-04-30-project-progress-richer-interactive-preview-over-current-export-surface.md
- design_docs/project-progress-graph-component-planning.md
- design_docs/project-progress-graph-open-work-breakdown.md
- design_docs/stages/planning-gate/2026-05-06-escalation-notification-persisted-surface-contract.md
- design_docs/stages/planning-gate/2026-05-07-parallel-v2-graph-renderer-and-library-selection.md
- design_docs/stages/planning-gate/2026-05-07-sigma-graphology-v2-graph-view-poc.md
- design_docs/project-progress-v2-graph-library-selection-comparison.md
- design_docs/project-progress-v2-graph-asset-boundary-draft.md
- design_docs/project-progress-v2-graph-adapter-shape-draft.md
- design_docs/project-progress-v2-graph-focused-validation-draft.md
- vscode-extension/esbuild.config.mjs
- vscode-extension/package.json
- vscode-extension/src/views/progressGraphPreviewHtml.ts
- vscode-extension/src/webviews/progressGraphV2PoC.ts
- vscode-extension/src/test/progressGraphPreviewHtml.test.ts
- design_docs/direction-candidates-after-phase-35.md
- src/runtime/orchestration/models.py
- src/runtime/orchestration/rollup.py
- tools/progress_graph/control_snapshot.py
- tests/test_progress_graph_control_snapshot.py
- vscode-extension/src/views/progressGraphPreview.ts
