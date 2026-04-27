---
handoff_id: 2026-04-23_2238_llmdoc-derived-doc-surface-and-host-boundaries_stage-close
entry_role: canonical
kind: stage-close
status: superseded
scope_key: llmdoc-derived-doc-surface-and-host-boundaries
safe_stop_kind: stage-complete
created_at: 2026-04-23T22:38:35+08:00
supersedes: 2026-04-22_2312_codex-adaptation-mainline-and-extension-abstraction_stage-close
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
  - design_docs/direction-candidates-after-phase-35.md
  - docs/starter-surface.md
  - docs/host-interaction-model.md
  - docs/codex-entry-contract.md
  - design_docs/tooling/Temporary Scratch and Stable Docs Standard.md
conditional_blocks:
  - phase-acceptance-close
  - authoring-surface-change
  - dirty-worktree
other_count: 0
---

# Summary

本会话完成 llmdoc 借鉴触发的 docs-only 收口：新增宿主交互四层模型、temporary scratch / stable docs 分流标准、starter surface 首跳路由与 Codex 独立入口 contract，并关闭 4 个 `2026-04-23` planning-gate。相关权威文档、状态板、方向文档与 checkpoint 已同步到同一口径，当前仓库回到无 active planning-gate 的可恢复 safe stop。

## Boundary

- 完成到哪里：`review/llmdoc.md` 的借鉴结论已沉淀为 `design_docs/` 方向分析、4 个已关闭的 docs-only planning-gate、以及 `docs/host-interaction-model.md`、`docs/starter-surface.md`、`docs/codex-entry-contract.md`、`design_docs/tooling/Temporary Scratch and Stable Docs Standard.md` 四个长期文档面；README / AGENTS / 安装与官方实例入口也已统一到新边界。
- 为什么这是安全停点：4 个 docs-only 切片都已关闭，当前无 active gate；关键 Markdown 与状态面已完成一致性检查；下一步工作已经收敛为新的窄方向选择，而不再属于当前文档收口本身。
- 明确不在本次完成范围内的内容：不实现 scratch 轻量恢复协议；不实现 helper entry / companion surface；不实现 extension 第二 provider；不修改 Python runtime、MCP contract 或 VS Code extension 运行时行为。

## Authoritative Sources

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `docs/starter-surface.md`
- `docs/host-interaction-model.md`
- `docs/codex-entry-contract.md`
- `design_docs/tooling/Temporary Scratch and Stable Docs Standard.md`

## Session Delta

- 本轮新增：`review/llmdoc.md`、`design_docs/llmdoc-public-surface-direction-analysis.md`、`design_docs/llmdoc-temporary-scratch-stable-docs-direction-analysis.md`、`design_docs/host-interaction-surface-isolation-direction-analysis.md`、`design_docs/codex-independent-entry-contract-direction-analysis.md`、`design_docs/direction-candidates-after-llmdoc-planning-gates.md`、4 个 `2026-04-23` planning-gate、`docs/host-interaction-model.md`、`docs/starter-surface.md`、`docs/codex-entry-contract.md`、`design_docs/tooling/Temporary Scratch and Stable Docs Standard.md`。
- 本轮修改：`README.md`、`docs/README.md`、`AGENTS.md`、`docs/installation-guide.md`、`docs/official-instance-doc-loop.md`、`docs/driver-responsibilities.md`、`docs/external-skill-interaction.md`、`design_docs/tooling/Document-Driven Workflow Standard.md`、`design_docs/tooling/External Project Review Standard.md`、`design_docs/Project Master Checklist.md`、`design_docs/Global Phase Map and Current Position.md`、`design_docs/direction-candidates-after-phase-35.md`、`.codex/checkpoints/latest.md`。
- 本轮形成的新约束或新结论：starter surface 成为第一次进入仓库的首跳路由，而不是第二 authority source；`.codex/tmp/` 被固定为推荐 scratch 面；Codex 被固定为 Interaction Adapter Layer 子案例，而不是 extension 第二 provider；VS Code extension 被固定为 Host UX Layer 实现。

## Verification Snapshot

- 自动化：对 `docs/codex-entry-contract.md`、`docs/starter-surface.md`、`docs/README.md`、`docs/installation-guide.md`、`docs/host-interaction-model.md`、`design_docs/stages/planning-gate/2026-04-23-codex-independent-entry-contract.md` 以及本次 safe-stop 回写的 Checklist / Phase Map / checkpoint 执行文档错误检查，均为 `No errors found`。
- 手测：按“第一次进入仓库”“在 Codex 中接入”“比较 Codex 与 VS Code/Copilot 职责边界”三条入口路径做文档走读，确认 starter surface、host interaction model 与 Codex entry contract 之间的首跳关系一致。
- 未完成验证：未重跑 Python / extension / release 自动化，因为本轮没有新增代码变更。
- 仍未验证的结论：helper entry / companion surface 是否必要、scratch 轻量恢复协议应采取何种最小恢复 contract，仍需后续独立切片判断。

## Open Items

- 未决项：`scratch 轻量恢复协议`、`helper entry / companion surface`、`extension 第二 provider 扩展比较分析` 仍是下一阶段候选；当前只完成了它们的前置边界整理。
- 已知风险：当前工作树仍是 dirty，且同时包含前一阶段的代码 / release 变更与本阶段的 docs-only 变更；下次 intake 必须按 workspace 现实状态分辨“本次 handoff 覆盖面”和“已存在但不属于本次 docs-only 收口的脏改动”。
- 不能默认成立的假设：不能默认认为 starter surface 已经等价于 helper entry；不能默认认为 Codex 独立入口 contract 已经回答了 extension 第二 provider 的实现价值；不能默认认为 scratch 分流标准已经自动带来恢复协议。

## Next Step Contract

- 下一会话建议只推进：默认先开一条 `scratch 轻量恢复协议` 的窄 planning-gate，把当前已固定的 scratch / stable 分流继续推进到最小恢复 contract；若用户优先关心入口体验，再改走 `helper entry / companion surface`。
- 下一会话明确不做：不重新打开已经关闭的 4 个 `2026-04-23` docs-only planning-gate；不把 helper、recovery protocol、extension 第二 provider 混成同一条切片；不在没有新 planning-gate 的情况下继续扩大实现面。
- 为什么当前应在这里停下：当前阶段已经把 llmdoc 借鉴对应的文档边界与 authority surface 收口完成，再往下就是新的方向选择或协议深化，而不是当前 safe stop 的延伸动作。

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Why This Stage Can Close

- 当前大阶段到这里可以结束的原因：llmdoc 借鉴触发的四条 docs-only 主线已经全部形成稳定文档资产并关闭 planning-gate，且状态面、方向文档与 checkpoint 已回到无 active gate 的一致口径。
- 当前不继续把更多内容塞进本阶段的原因：剩余候选已经转成新的窄协议或产品面问题，继续推进会跨出“docs-only 边界收口”并重新进入 planning-gate 选择。

## Planning-Gate Return

- 应回到的 planning-gate 位置：当前无 active planning-gate；方向选择应回到 `design_docs/direction-candidates-after-phase-35.md` 的最新补充段落。
- 下一阶段候选主线：`scratch 轻量恢复协议`、`helper entry / companion surface`、`extension 第二 provider 扩展比较分析`。
- 下一阶段明确不做：不直接把 `docs/host-interaction-model.md`、`docs/starter-surface.md` 或 `docs/codex-entry-contract.md` 扩成新的实现切片；不在未起新 gate 的情况下进入 runtime / provider / UI 代码改造。

## Conditional Blocks

### phase-acceptance-close

Trigger:
本次 safe stop 是对 `2026-04-23` llmdoc-derived docs-only 建设块的正式 stage-close。

Required fields:

- Acceptance Basis: `host interaction surface isolation`、`temporary scratch / stable docs split`、`public surface convergence`、`Codex independent entry contract` 四条 planning-gate 均已关闭，且对应 authority / tooling docs 已落地。
- Automation Status: 本轮涉及的关键 Markdown 与 safe-stop 状态面检查均通过，无文档错误。
- Manual Test Status: 已按 starter surface、Codex entry、host boundary 三条场景做文档走读。
- Checklist/Board Writeback Status: Checklist、Phase Map、当前方向候选文档与 checkpoint 已同步到新的 safe-stop footprint 和无 active gate 口径。

Verification expectation:
docs-only 收口至少需要满足三点：planning-gate 已关闭、权威入口彼此不冲突、状态面回写与 safe-stop footprint 一致；本次三者均已满足。

Refs:

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/direction-candidates-after-phase-35.md`

### authoring-surface-change

Trigger:
本轮直接改动了仓库的首跳入口、Codex 入口说明和宿主分层说明，属于 authoring/discovery surface 变化。

Required fields:

- Changed Authoring Surface: `docs/starter-surface.md`、`docs/codex-entry-contract.md`、`docs/host-interaction-model.md`，以及与之同步的 `README.md`、`docs/README.md`、`AGENTS.md`、`docs/installation-guide.md`、`docs/official-instance-doc-loop.md`。
- Usage Guide Sync Status: 根 README、文档地图、AGENTS、安装文档与官方实例文档都已同步到新的首跳路由与 Codex 入口边界。
- Discovery Surface Status: 仓库第一次进入的默认路线现指向 starter surface；Codex 入口现指向 `AGENTS.md` + MCP + validation；宿主差异被固定为四层模型中的 adapter / host UX 区分。
- Authoring Boundary Notes: 本轮没有实现 helper entry、companion packaging、第二 provider 或第二宿主 UI；这些仍留在后续 planning-gate 决策面。

Verification expectation:
作者入口变化必须同时满足“入口更短”和“authority 不分叉”；本轮通过交叉文档检查和入口走读确认上述条件成立。

Refs:

- `docs/starter-surface.md`
- `docs/installation-guide.md`
- `docs/codex-entry-contract.md`
- `docs/host-interaction-model.md`

### dirty-worktree

Trigger:
生成 handoff 时，仓库仍存在大量未提交改动，且这些改动同时覆盖前一阶段的代码 / release 变更与本阶段的 docs-only 收口。

Required fields:

- Dirty Scope: 当前 dirty 路径覆盖 `.codex/`、`design_docs/`、`docs/`、`review/`、`release/`、`src/`、`vscode-extension/` 等区域。
- Relevance to Current Handoff: 本次 handoff 直接覆盖 `design_docs/`、`docs/`、`review/` 和状态面文件；同时工作树里还保留前一阶段的 Python / extension / release 改动，下一会话必须明确区分它们与本次 docs-only 收口的边界。
- Do Not Revert Notes: 不得把当前工作树脏状态一概视为本次 handoff 的可回滚对象；继续工作前应先确认哪些改动属于前一阶段的 Codex/provider/release 结果，哪些属于本次 llmdoc-derived docs-only 收口。
- Need-to-Inspect Paths: `docs/starter-surface.md`、`docs/codex-entry-contract.md`、`docs/host-interaction-model.md`、`design_docs/tooling/Temporary Scratch and Stable Docs Standard.md`、`design_docs/direction-candidates-after-phase-35.md`、`.codex/checkpoints/latest.md`、`.codex/handoffs/`，以及仍然 dirty 的 `src/`、`vscode-extension/`、`release/` 区域。

Verification expectation:
已基于当前工作树变更摘要确认 dirty 状态真实存在，且不止覆盖本次 docs-only 范围；因此下次 intake 必须以 workspace 现实状态优先，而不是假设 handoff 列表等于全部差异。

Refs:

- `design_docs/Project Master Checklist.md`
- `.codex/checkpoints/latest.md`
- `.codex/handoffs/CURRENT.md`

## Other

None.
