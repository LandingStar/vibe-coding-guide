---
handoff_id: 2026-05-12_0900_plugin-side-codex-host-support-gap_phase-close
entry_role: canonical
kind: phase-close
status: superseded
scope_key: plugin-side-codex-host-support-gap
safe_stop_kind: phase-complete
created_at: 2026-05-12T09:00:58+08:00
supersedes: 2026-05-03_1210_project-progress-richer-interactive-preview-over-current-export-surface_stage-close
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
  - docs/codex-entry-contract.md
  - design_docs/stages/planning-gate/2026-05-12-plugin-side-codex-host-support-gap.md
  - design_docs/stages/planning-gate/2026-05-08-g6-v2-graph-view-poc.md
conditional_blocks:
  - phase-acceptance-close
  - dirty-worktree
other_count: 0
---

# Summary

本会话完成一条独立的 docs-only phase-close：先基于 authority docs、runtime/CLI/MCP 实现面和 extension 实现面对“当前插件以及 MCP 包对 Codex 的支持性”做了证据化检查，再把超出当前 active G6 图面主线的插件侧 Codex 宿主缺口登记为 `PROPOSED` future slice。当前可以安全停下，因为本轮目标只要求把支持边界判断收口为稳定结论，并把 out-of-scope gap 固定进 planning surface；用户也已明确选择“保持当前只到 proposed gate”，因此当前停点不属于半完成实现态。

## Boundary

- 完成到哪里：已确认 Codex 主链当前通过 `AGENTS.md` + MCP + CLI/validation 成立；已确认 VS Code extension 当前仍属于 `Host UX Layer`，不等于 Codex 的一等宿主支持；已新增 `design_docs/stages/planning-gate/2026-05-12-plugin-side-codex-host-support-gap.md` 并在 Checklist 中登记对应 backlog 项，且保持 `PROPOSED`，不改变当前 `design_docs/stages/planning-gate/2026-05-08-g6-v2-graph-view-poc.md` 的 active 状态。
- 为什么这是安全停点：当前小切片的完成边界可以稳定描述为“支持性检查 + scope interrupt + proposed gate 登记”，已完成项与未完成项分离清楚，且后续无论是继续当前 G6 主线，还是未来显式激活 Codex 宿主缺口，都不需要依赖本次对话中的隐性上下文才能恢复。
- 明确不在本次完成范围内的内容：未在 extension 内实现新的 Codex provider；未把 Chat Participant 改造成 Codex 运行面；未激活 `2026-05-12-plugin-side-codex-host-support-gap`；未改写当前 G6 图面 active gate；未做真实 Codex client 端到端宿主 smoke test。

## Authoritative Sources

- `design_docs/Project Master Checklist.md` — 当前 active slice、safe-stop footprint 与新登记 backlog 的总入口
- `design_docs/Global Phase Map and Current Position.md` — 当前 Post-v1.0 阶段口径与 handoff footprint 对齐入口
- `docs/codex-entry-contract.md` — Codex 主链闭环、宿主分层边界与“Codex 不等于 extension 第二 provider”的权威口径
- `design_docs/stages/planning-gate/2026-05-12-plugin-side-codex-host-support-gap.md` — 本轮新登记的 future slice contract
- `design_docs/stages/planning-gate/2026-05-08-g6-v2-graph-view-poc.md` — 当前仍在推进中的主实现线，后续不得被本切片误扩 scope

## Session Delta

- 本轮新增：`design_docs/stages/planning-gate/2026-05-12-plugin-side-codex-host-support-gap.md`；当前 canonical handoff `.codex/handoffs/history/2026-05-12_0900_plugin-side-codex-host-support-gap_phase-close.md`。
- 本轮修改：`design_docs/Project Master Checklist.md` 新增 2026-05-12 backlog 项，把插件侧 Codex 宿主缺口固定为 `PROPOSED` future slice；随后将当前 handoff footprint 同步到 `CURRENT.md` / Checklist / Phase Map / checkpoint。
- 本轮形成的新约束或新结论：当前“支持 Codex”应继续理解为 `AGENTS.md` + MCP + CLI/validation 的主链支持，而不是 extension 第二 provider；插件侧 Codex 宿主缺口若后续要进入实现，必须从独立 planning-gate 激活，而不是混入当前 G6 图面切片。

## Verification Snapshot

- 自动化：`npm run build`（`vscode-extension/`）通过；`doc-based-coding generate-instructions --target codex --output tmp/codex-support-check.md` 生成成功；`doc-based-coding-mcp --help` 可用；`doc-based-coding info` 与 `doc-based-coding validate` 均通过；新增 proposed gate 与 Checklist 改动的 diagnostics 检查无当前错误。
- 手测：复核了 `docs/codex-entry-contract.md`、`docs/installation-guide.md`、`src/workflow/instructions_generator.py`、`src/mcp/server.py`、`vscode-extension/src/chat/participant.ts`、`vscode-extension/src/llm/providerFactory.ts` 与 `vscode-extension/package.json` 的边界一致性；确认临时生成的 `tmp/codex-support-check.md` 内容符合 Codex 指令面后已删除；确认新 gate 保持 `PROPOSED`，且当前 G6 gate 仍为 `ACTIVE`。
- 未完成验证：未做真实 Codex client 宿主侧 smoke test；未做 extension 内任何新的 Codex 宿主实现验证；未重跑与本切片无直接关系的全量测试。
- 仍未验证的结论：未来是否需要 `thin Codex helper entry / companion surface` 仍未验证；当前只确认主链支持成立，并确认插件侧 parity 尚未提供。

## Open Items

- 未决项：是否在当前 G6 主线 formal close 后激活 `2026-05-12-plugin-side-codex-host-support-gap`；若激活，第一刀应走 docs-first / smoke-test-first 还是 companion/helper surface 方向。
- 已知风险：当前 workspace 是重度 dirty worktree，存在并行 extension/UI、本地配置、progress-graph artifact 与临时文件轨道；若下一会话不先区分这些轨道，容易把本次 docs-only phase-close 误读为“插件侧 Codex 支持已经进入实现”。
- 不能默认成立的假设：不能把 `provider abstraction` 等同于 Codex 宿主支持；不能把 Codex 主链支持成立等同于 VS Code extension 已具备 Codex parity；不能把新建 `PROPOSED` gate 误当成已激活实现线。

## Next Step Contract

- 下一会话建议只推进：默认回到当前 active 主线 `design_docs/stages/planning-gate/2026-05-08-g6-v2-graph-view-poc.md` 继续其窄范围图面调校；若用户显式提升 Codex 宿主支持优先级，才从 `design_docs/stages/planning-gate/2026-05-12-plugin-side-codex-host-support-gap.md` 的 activation precondition 重新进入。
- 下一会话明确不做：不要在没有激活 `2026-05-12-plugin-side-codex-host-support-gap` 的前提下继续实现插件侧 Codex 支持；不要把 `extension second provider` 作为当前默认方向；不要把当前 G6 gate 与 Codex gap gate 混成同一切片。
- 为什么当前应在这里停下：本轮已经回答了“当前插件与 MCP 包对 Codex 的支持边界是什么，以及插件侧缺口应如何被登记”这个问题；继续推进将直接跨入新的优先级判断或新的实现切片，而不再属于当前 phase-close 的收口范围。

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Phase Completion Check

- 当前小 phase 的完成定义：完成一次证据化 Codex 支持性检查；把检查结论固定为稳定边界口径；对超出当前 active G6 主线的插件侧 Codex 宿主缺口执行 scope interrupt 并登记为独立 `PROPOSED` planning-gate；同步 Checklist backlog，但不激活新 gate。
- 当前小 phase 是否已满足完成定义：是。支持性检查、scope interrupt、proposed gate 登记与 Checklist 回写都已完成，且用户已明确选择“保持当前只到 proposed gate”。
- 当前停点为何不属于半完成状态：当前切片并不承诺任何插件实现或宿主适配代码；它只承诺“形成稳定结论并登记 future slice”。这条边界已完整收口，没有残留在“马上还要补一半实现”的中间态。

## Parent Stage Status

- 所属大阶段当前状态：项目仍处于 Post-v1.0 持续演进阶段；当前主实现线仍是 graph 方向的 `G6 V2 Graph View PoC`，而本次 handoff 关闭的是一条独立的 side-phase docs slice。
- 所属大阶段是否接近尾声：否。当前主线仍有 active G6 gate 和后续图面调校工作；本次 phase-close 只是在该大阶段中额外收口了一条并行的文档判断/登记切片。
- 下一步继续哪条窄主线：默认继续 `design_docs/stages/planning-gate/2026-05-08-g6-v2-graph-view-poc.md`；只有在当前 gate 收口、被显式暂停，或用户显式改优先级时，才回到 `design_docs/stages/planning-gate/2026-05-12-plugin-side-codex-host-support-gap.md`。

## Conditional Blocks

### phase-acceptance-close

Trigger:
本次 safe stop 是一次正式的 docs-only `phase-close`：它收口的是“Codex 支持性检查 + 插件侧宿主缺口登记”这一条独立小切片，而不是当前 G6 主实现线的 stage-close。

Required fields:

- Acceptance Basis: 已通过 authority docs + code/runtime evidence 确认 Codex 主链支持成立、VS Code extension 当前不等于 Codex 一等宿主支持；已新增 `design_docs/stages/planning-gate/2026-05-12-plugin-side-codex-host-support-gap.md` 并明确保持 `PROPOSED`；Checklist 已登记对应 backlog，且 active G6 gate 未被改写。
- Automation Status: `npm run build`（`vscode-extension/`）通过；`doc-based-coding generate-instructions --target codex --output tmp/codex-support-check.md` 成功；`doc-based-coding-mcp --help`、`doc-based-coding info`、`doc-based-coding validate` 成功；目标文档 diagnostics clean。
- Manual Test Status: 已复核 Codex 主链与 extension 边界相关的 authority docs、CLI/MCP 实现面和 extension 实现锚点；已人工确认临时 Codex 指令面输出合理且随后删除；已人工确认 proposed gate 未误激活、G6 gate 未被误扩 scope。
- Checklist/Board Writeback Status: proposed gate 与 Checklist backlog 已完成；当前 canonical handoff、`CURRENT.md`、Checklist 顶部 handoff footprint、Phase Map handoff footprint 与 checkpoint current handoff footprint 已统一到本次 phase-close。

Verification expectation:
接手方应把本次 phase-close 理解为“边界判断与 future-slice 登记已经完成”，而不是“插件侧 Codex 支持已实现”。若后续继续推进 Codex 宿主能力，必须重新检查 activation precondition，而不是直接基于本 handoff 进入实现。

Refs:

- `docs/codex-entry-contract.md`
- `design_docs/stages/planning-gate/2026-05-12-plugin-side-codex-host-support-gap.md`
- `design_docs/Project Master Checklist.md`

### dirty-worktree

Trigger:
生成 handoff 时，workspace 中存在大量未提交改动与未跟踪文件，其中只有少数文档/footprint 路径直接属于本次 docs-only phase-close，其余属于并行 extension、progress-graph、本地配置与临时文件轨道。

Required fields:

- Dirty Scope: 直接属于本次 handoff 的路径主要包括 `design_docs/stages/planning-gate/2026-05-12-plugin-side-codex-host-support-gap.md`、`design_docs/Project Master Checklist.md`、`.codex/handoffs/history/2026-05-12_0900_plugin-side-codex-host-support-gap_phase-close.md`、`.codex/handoffs/CURRENT.md`、`.codex/checkpoints/latest.md`、`design_docs/Global Phase Map and Current Position.md`；并行 dirty 轨道还包括 `.codex/pack-lock.json`、`.codex/progress-graph/*`、`.codex/config.toml`、`.codex/decision-logs/*`、`.bashrc`、`tmp/*`、`vscode-extension/*`、`design_docs/stages/planning-gate/2026-05-11-ai-chat-vibe-coding-readonly-tool-loop.md` 等。
- Relevance to Current Handoff: 本 handoff 只直接覆盖 Codex 支持性检查、proposed gate 登记与 handoff footprint writeback；其它 dirty 路径不是本次 phase-close 的完成边界，但它们会影响下一会话对 workspace 现实状态的判断。
- Do Not Revert Notes: 不要回退与本次 handoff 无关的并行 dirty 改动；也不要把当前 `PROPOSED` gate 误升级为 active 实现面；若后续需要清理本地配置或临时文件，应在独立切片中处理，而不是在恢复本 handoff 时顺手回退。
- Need-to-Inspect Paths: `design_docs/stages/planning-gate/2026-05-12-plugin-side-codex-host-support-gap.md`、`design_docs/Project Master Checklist.md`、`design_docs/Global Phase Map and Current Position.md`、`.codex/checkpoints/latest.md`、`.codex/handoffs/CURRENT.md`、`docs/codex-entry-contract.md`、`design_docs/stages/planning-gate/2026-05-08-g6-v2-graph-view-poc.md`。

Verification expectation:
下次 intake 应先确认上述 handoff-specific 路径与并行 dirty 轨道是否仍保持当前区分；若 dirty 范围进一步扩大，也不应把本 handoff 当成那些并行轨道的总说明文档。

Refs:

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/checkpoints/latest.md`

## Other

None.
