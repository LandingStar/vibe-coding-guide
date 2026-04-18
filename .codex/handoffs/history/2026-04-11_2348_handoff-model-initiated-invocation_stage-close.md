---
handoff_id: 2026-04-11_2348_handoff-model-initiated-invocation_stage-close
entry_role: canonical
kind: stage-close
status: superseded
scope_key: handoff-model-initiated-invocation
safe_stop_kind: stage-complete
created_at: 2026-04-11T23:48:20+08:00
supersedes: 2026-04-11_1929_phase-35-v1-stable-release-confirmation_phase-close
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
  - design_docs/stages/planning-gate/2026-04-11-handoff-model-initiated-invocation.md
  - design_docs/direction-candidates-after-phase-35.md
  - design_docs/tooling/Session Handoff Standard.md
  - design_docs/tooling/Document-Driven Workflow Standard.md
conditional_blocks:
  - phase-acceptance-close
  - authoring-surface-change
  - dirty-worktree
other_count: 0
---

# Summary

已完成 post-v1.0 窄切片 `handoff-model-initiated-invocation`：权威协议、workflow 文档、handoff skill contract 与 bootstrap/example 副本已经统一到“安全停点下 model 可主动进入 handoff 分支，且只有 `blocked` 是停止信号”的语义。状态板已回写到 safe stop，portable handoff kit 的定向测试通过，因此这是一个可以无隐性上下文交接的 stage-close 停点。

## Boundary

- 完成到哪里：`design_docs/stages/planning-gate/2026-04-11-handoff-model-initiated-invocation.md` 已标记为 `COMPLETED`，`Project Master Checklist`、`Global Phase Map` 与 `.codex/checkpoints/latest.md` 已恢复到 `Active Slice: —` 的 safe stop 口径。
- 为什么这是安全停点：本切片只涉及 handoff 协议、skill invocation contract 与 shipped 文档副本的一致性收口；完成项与未完成项已经稳定分离，下一会话不需要依赖本对话隐性上下文即可继续。
- 明确不在本次完成范围内的内容：不改 handoff Python 结果结构，不扩展到非 handoff skill 的通用自动执行框架，不继续推进新的 post-v1.0 实现切片。

## Authoritative Sources

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/stages/planning-gate/2026-04-11-handoff-model-initiated-invocation.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `design_docs/tooling/Session Handoff Standard.md`
- `design_docs/tooling/Document-Driven Workflow Standard.md`

## Session Delta

- 本轮新增：`design_docs/stages/planning-gate/2026-04-11-handoff-model-initiated-invocation.md`；handoff skill / handoff-system shipped 副本在 `.github/skills/` 与 `.codex/handoff-system/` 下被纳入当前工作树 reality。
- 本轮修改：`design_docs/tooling/Session Handoff Standard.md`、`design_docs/tooling/Document-Driven Workflow Standard.md`、`AGENTS.md`、`.github/copilot-instructions.md`、`.codex/handoff-system/docs/Skill Workflow.md`、`.codex/handoff-system/docs/Overview.md`、handoff skill 文本、bootstrap/example 副本，以及 `Project Master Checklist` / `Global Phase Map` / `.codex/checkpoints/latest.md` 等状态文档。
- 本轮形成的新约束或新结论：安全停点下 model 可以主动发起 handoff；handoff 分支中只有 `blocked` 是停止信号；显式 slash 入口仍保留为示例，但不再是唯一触发条件。

## Verification Snapshot

- 自动化：`pytest .codex/handoff-system/tests/test_install_portable_handoff_kit.py -q` 通过（1 passed）；代表性协议与 skill 文本诊断检查无新增错误。
- 手测：文档级复核已确认当前不再存在 active rule 层的“必须显式 slash 才能执行”约束；未新增单独 runtime 手测需求。
- 未完成验证：未运行全量 pytest；本切片未触及 Python runtime 结果结构，因此未做更大范围回归。
- 仍未验证的结论：无额外运行时语义变化；当前变更限定在协议、skill 与 shipped 副本的一致性收口。

## Open Items

- 未决项：当前无阻塞；safe stop 已建立，可从本 handoff 继续恢复。
- 已知风险：工作区仍包含大量累计未提交改动与 `.venv-mcp/` / `.vscode/` 环境噪音；后续若清理工作树，必须逐项甄别，不能按目录名直接回退。
- 不能默认成立的假设：未运行全量测试套件；下一会话不应假设所有历史脏文件都与本切片无关。

## Next Step Contract

- 下一会话建议只推进：从 `design_docs/direction-candidates-after-phase-35.md` 继续确认下一个 post-v1.0 窄切片；若没有新的用户方向，优先延续 checklist 中的持续 dogfood / gap 跟踪线。
- 下一会话明确不做：不回退 handoff model 主动调用与 blocked-only stop 语义，不把 handoff 分支重新收窄成 slash-only 入口，不在本 safe stop 上临时扩 scope 修补无关问题。
- 为什么当前应在这里停下：当前 slice 已闭环，状态板与 shipped 副本已同步，safe stop 与下一条 planning/direction 入口都已明确，下一会话可以不依赖本对话隐性上下文继续。

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。
- 读 `design_docs/direction-candidates-after-phase-35.md` 确认下一个 post-v1.0 方向是否已变化。

## Why This Stage Can Close

- 当前大阶段到这里可以结束的原因：当前连续建设块只负责收口 handoff 执行语义；协议、workflow、skill contract 与 shipped 副本同步均已完成，并已恢复到 `Active Slice: —` 的 safe stop。
- 当前不继续把更多内容塞进本阶段的原因：再往前推进已经不是“收口 handoff 语义”而是新的 post-v1.0 方向选择；继续扩 scope 会违反本 planning-gate 的窄边界。

## Planning-Gate Return

- 应回到的 planning-gate 位置：`design_docs/direction-candidates-after-phase-35.md`
- 下一阶段候选主线：持续 pre-release dogfood / gap 跟踪，或从该方向文档中再选新的 post-v1.0 窄切片。
- 下一阶段明确不做：不继续在当前 `handoff-model-initiated-invocation` slice 中混入新的 runtime、packaging 或 validator 实现工作。

## Conditional Blocks

### phase-acceptance-close

Trigger:
当前 handoff 是对 `design_docs/stages/planning-gate/2026-04-11-handoff-model-initiated-invocation.md` 的正式 stage-close 交接。

Required fields:

- Acceptance Basis: planning gate 的 Target Outcome / Exit Condition 全部满足；权威协议、workflow、skills 与 bootstrap/example 副本已统一到 model 主动调用 + blocked-only stop 口径。
- Automation Status: `pytest .codex/handoff-system/tests/test_install_portable_handoff_kit.py -q` 1 passed；代表性协议与 skill 文本诊断无错误。
- Manual Test Status: 文档级复核已确认当前不再存在 active rule 层的显式 slash-only 约束；未新增单独 runtime 手测需求。
- Checklist/Board Writeback Status: `Project Master Checklist`、`Global Phase Map` 与 `.codex/checkpoints/latest.md` 已回写到 safe stop；本 handoff 作为当前最新 canonical 交接边界。

Verification expectation:
接手方只需复核 planning-gate 的 execution / validation 结果与状态板 safe stop 口径是否一致，无需再假设存在未落盘的语义改动。

Refs:

- `design_docs/stages/planning-gate/2026-04-11-handoff-model-initiated-invocation.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/checkpoints/latest.md`

### authoring-surface-change

Trigger:
本切片直接修改 handoff 协议文案、skill invocation contract、bootstrap/example authoring surfaces，以及显式 slash 入口的发现性文案。

Required fields:

- Changed Authoring Surface: `design_docs/tooling/Session Handoff Standard.md`、`design_docs/tooling/Document-Driven Workflow Standard.md`、`AGENTS.md`、`.github/copilot-instructions.md`、`.codex/handoff-system/docs/`、`.github/skills/`、`.codex/handoff-system/skill/` 与 bootstrap/example 副本。
- Usage Guide Sync Status: 权威协议与 shipped 副本已同步，方向文档与 planning gate 也已回写到同一口径。
- Discovery Surface Status: `/project-handoff-*` 仍保留为显式调用示例；portable handoff kit 定向测试确认 sample skill 复制后仍可发现。
- Authoring Boundary Notes: 变更限定在 handoff 分支的入口 / 续行语义与 authoring-facing 文案，不涉及 handoff Python 结果结构或非 handoff skill 通用自动执行框架。

Verification expectation:
接手方应同时读 authority 层与 shipped copy 层，确认口径没有再次漂移；不要只抽查其中一侧。

Refs:

- `design_docs/tooling/Session Handoff Standard.md`
- `design_docs/tooling/Document-Driven Workflow Standard.md`
- `AGENTS.md`
- `.github/copilot-instructions.md`
- `.codex/handoff-system/docs/Skill Workflow.md`

### dirty-worktree

Trigger:
当前工作树仍含大量累计未提交改动，包含本切片相关文档 / skill 改动以及更早的 post-v1.0 累积产物，另有 `.venv-mcp/` 与 `.vscode/` 等环境级变化。

Required fields:

- Dirty Scope: `git status --short` 显示 `design_docs/`、`docs/`、`.codex/`、`.github/skills/`、`src/`、`tests/`、`doc-loop-vibe-coding/` 等路径均处于脏状态，并有 `.venv-mcp/` / `.vscode/` 等未跟踪目录。
- Relevance to Current Handoff: 本 handoff 直接依赖当前 workspace reality；接手方必须在读取 handoff 后先核对 dirty worktree，而不是把旧 handoff 或 state docs 当成唯一真相。
- Do Not Revert Notes: 不要批量回退 `.codex/`、`.github/skills/`、`design_docs/`、bootstrap/example docs 与累计 post-v1.0 runtime/test 变更；环境目录在清理前也要先确认是否只是本机噪音。
- Need-to-Inspect Paths: `.codex/handoff-system/`、`.github/skills/`、`design_docs/tooling/`、`design_docs/stages/planning-gate/2026-04-11-handoff-model-initiated-invocation.md`、`.venv-mcp/`、`.vscode/`。

Verification expectation:
接手方应先跑一次 `git status --short` 并以当前工作树 reality 为准，再决定哪些文件属于正式工作产出、哪些只是本机环境噪音。

Refs:

- `git status --short`
- `design_docs/Project Master Checklist.md`

## Other

None.
