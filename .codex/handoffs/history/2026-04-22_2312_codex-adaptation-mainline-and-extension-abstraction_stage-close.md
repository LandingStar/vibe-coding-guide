---
handoff_id: 2026-04-22_2312_codex-adaptation-mainline-and-extension-abstraction_stage-close
entry_role: canonical
kind: stage-close
status: superseded
scope_key: codex-adaptation-mainline-and-extension-abstraction
safe_stop_kind: stage-complete
created_at: 2026-04-22T23:12:10+08:00
supersedes: 2026-04-21_0213_dogfood-mcp-feedback-s1-s3-s5-fix_stage-close
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
  - docs/installation-guide.md
  - design_docs/stages/planning-gate/2026-04-22-vscode-extension-llm-provider-abstraction.md
conditional_blocks:
  - phase-acceptance-close
  - code-change
  - cli-change
  - authoring-surface-change
  - dirty-worktree
other_count: 0
---

# Summary

完成 Codex 主链适配与 VS Code extension 内部 LLM provider 抽象：CLI / instructions 生成链现可直接面向 Codex 输出 `AGENTS.md`，extension 命令层不再直接依赖 `CopilotLLMProvider`，同时保留 GitHub Copilot 作为默认实现。已完成针对 Python 主链与 extension 构建面的验证，当前处于无 active planning-gate 的可恢复安全停点。

## Boundary

- 完成到哪里：`generate-instructions` 已支持 `generic|codex|copilot` 目标与按文件名推断 `AGENTS.md` / `AGENTS.override.md`；`README.md` 与 `docs/installation-guide.md` 已补齐 Codex 安装/使用主链；VS Code extension 中 classify / pack generation / governance explanation / model-family discovery 已改为依赖抽象 provider 契约，Copilot 继续作为默认 provider。
- 为什么这是安全停点：本轮目标中的两条窄主线均已收口，planning-gate `2026-04-22-vscode-extension-llm-provider-abstraction.md` 已关闭，自动化与构建验证已完成，仓库当前返回无 active gate。
- 明确不在本次完成范围内的内容：未把 VS Code Chat Participant 改写为独立于 VS Code Chat 的 Codex 运行面；未实现新的 Codex extension provider；未做 extension UI/E2E 或真实 Copilot/Codex 双端到端复验。

## Authoritative Sources

- `design_docs/Project Master Checklist.md` — 当前状态板与 safe-stop 入口
- `design_docs/Global Phase Map and Current Position.md` — 当前阶段口径与 handoff footprint
- `docs/installation-guide.md` — Codex / Copilot 安装与接入主链
- `design_docs/stages/planning-gate/2026-04-22-vscode-extension-llm-provider-abstraction.md` — 本轮 extension 抽象边界与验收门

## Session Delta

- 本轮新增：`design_docs/stages/planning-gate/2026-04-22-vscode-extension-llm-provider-abstraction.md`、`vscode-extension/src/llm/providerFactory.ts`
- 本轮修改：`src/__main__.py`、`src/workflow/instructions_generator.py`、`README.md`、`docs/installation-guide.md`、`vscode-extension/src/llm/types.ts`、`vscode-extension/src/llm/copilot.ts`、`vscode-extension/src/llm/packGenerator.ts`、`vscode-extension/src/governance/interceptor.ts`、`vscode-extension/src/views/configPanel.ts`、`vscode-extension/src/extension.ts`、`vscode-extension/README.md`、`vscode-extension/package.json`
- 本轮形成的新约束或新结论：extension 内可安全复用的 LLM 调用面应先抽象到 provider 契约；VS Code Chat Participant 的 `request.model` 语义暂不应强并入该抽象，否则回归面过大；若需要 Codex 拥有与 extension 等价的交互面，应优先走独立 Codex 系统/入口而非复用 Chat Participant 语义。

## Verification Snapshot

- 自动化：`$env:PYTHONPATH=(Get-Location).Path; pytest tests/test_instructions_generator.py tests/test_cli.py` → `35 passed`；`npm run build`（`vscode-extension/`）→ `build complete`
- 手测：`$env:PYTHONPATH=(Get-Location).Path; python -m src generate-instructions --target codex` 手动确认输出为 Codex/`AGENTS.md` 口径；代码审查确认 extension 命令层已切到 `ManagedLLMProvider`
- 未完成验证：真实 VS Code Extension F5 / VSIX 运行复验；真实 GitHub Copilot provider 在当前抽象后的交互复验；Codex 消费端端到端验证
- 仍未验证的结论：抽象后的 provider 层在真实 Copilot 环境中的 UI 行为保持零回归，尚未通过交互级验证完成闭环

## Open Items

- 未决项：是否进入“Codex 独立系统/入口 contract”方向分析；是否需要在 extension 内继续扩第二 provider
- 已知风险：当前 Python 环境里存在 `site-packages/src` 阴影，需要显式 `PYTHONPATH` 才能稳定命中工作区源码；Chat Participant 仍保持 VS Code/Copilot 原生路径，不能被误当成已完成的 Codex 运行面
- 不能默认成立的假设：不能默认认为“provider 调用层已抽象”就等于“整个 VS Code extension 已适配 Codex”；不能默认认为未复验的 Copilot 真实交互面一定零回归

## Next Step Contract

- 下一会话建议只推进：围绕 Codex 适配进入一条新的方向分析，优先比较“Codex 独立系统/入口 contract”与“extension 内继续扩第二 provider”的回归面、收益与实现边界
- 下一会话明确不做：不直接改写 Chat Participant 运行语义；不在没有新 planning-gate 的情况下继续扩 extension 架构；不回滚或整理与本次 handoff 无关的 dirty worktree
- 为什么当前应在这里停下：当前实现层切片已收口，继续推进将进入新的架构分叉判断，属于下一条窄主线而不是本轮 safe-stop 的一部分

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Why This Stage Can Close

- 当前大阶段到这里可以结束的原因：Codex 主链适配与 extension provider 抽象这两条直接响应用户需求的窄切片均已完成，验证门已覆盖 Python 主链与 extension 编译面，且当前无 active planning-gate
- 当前不继续把更多内容塞进本阶段的原因：后续是否走“独立 Codex 系统/入口”还是“extension 第二 provider”是新的设计分叉，继续实现会越过本轮已确认的无回归边界

## Planning-Gate Return

- 应回到的 planning-gate 位置：`2026-04-22-vscode-extension-llm-provider-abstraction` 已关闭；仓库回到 Checklist 驱动的无 active gate 状态
- 下一阶段候选主线：`Codex 独立系统/入口 contract` 方向分析；`extension 第二 provider 是否值得扩展` 的回归面比较
- 下一阶段明确不做：不把当前已关闭的 provider abstraction planning-gate 重新扩成 Chat Participant 改造或全量 Codex extension 迁移

## Conditional Blocks

### phase-acceptance-close

Trigger:
本次 safe stop 是对“Codex 主链适配 + extension provider abstraction”完成边界的正式 stage-close。

Required fields:

- Acceptance Basis:
- Acceptance Basis: Python 主链 Codex 入口已可生成 `AGENTS.md`，extension 命令层 provider 抽象已完成且 Copilot 默认实现保留，planning-gate 已关闭
- Automation Status: targeted `pytest` 35 passed；`vscode-extension` esbuild 构建通过
- Manual Test Status: `generate-instructions --target codex` 手动验证通过；extension provider 调用面完成代码审查
- Checklist/Board Writeback Status: 本 handoff 生成后将同步 Checklist / Phase Map / direction candidates / checkpoint / CURRENT

Verification expectation:
目标切片必须能被明确描述为“已完成且可停”，并且自动化/构建面无当前 blocker；未完成的仅允许落在下一阶段方向选择或未做的交互复验。

Refs:

- `design_docs/stages/planning-gate/2026-04-22-vscode-extension-llm-provider-abstraction.md`
- `docs/installation-guide.md`

### code-change

Trigger:
本轮覆盖 Python CLI / instructions 生成链与 VS Code extension 内部 provider 调用层的真实代码修改。

Required fields:

- Touched Files:
- Touched Files: `src/__main__.py`, `src/workflow/instructions_generator.py`, `README.md`, `docs/installation-guide.md`, `vscode-extension/src/llm/types.ts`, `vscode-extension/src/llm/copilot.ts`, `vscode-extension/src/llm/providerFactory.ts`, `vscode-extension/src/llm/packGenerator.ts`, `vscode-extension/src/governance/interceptor.ts`, `vscode-extension/src/views/configPanel.ts`, `vscode-extension/src/extension.ts`, `vscode-extension/README.md`, `vscode-extension/package.json`, `design_docs/stages/planning-gate/2026-04-22-vscode-extension-llm-provider-abstraction.md`
- Intent of Change: 为项目补齐 Codex 主链适配，并把 extension 命令层从具体 Copilot provider 解耦为抽象 provider 契约，同时保留 Copilot 默认行为
- Tests Run: targeted `pytest tests/test_instructions_generator.py tests/test_cli.py`；`npm run build`
- Untested Areas: 真实 VS Code/Copilot 交互面、Codex 端到端消费链、extension UI/E2E

Verification expectation:
Python 主链改动需经 targeted pytest 和手动命令验证；extension 改动至少需经 TypeScript/esbuild 构建通过并明确列出未做的交互复验。

Refs:

- `src/workflow/instructions_generator.py`
- `vscode-extension/src/extension.ts`
- `vscode-extension/src/llm/types.ts`

### cli-change

Trigger:
本轮修改了 `generate-instructions` 的 target 语义与输出文件推断规则，属于 CLI 行为面变化。

Required fields:

- Changed Commands:
- Changed Commands: `python -m src generate-instructions --target generic|codex|copilot`；按输出文件名推断 `AGENTS.md` / `AGENTS.override.md` / `copilot-instructions.md`
- Help Sync Status: CLI 帮助文本与 `src/__main__.py` 同步完成
- Command Reference Sync Status: `README.md` 与 `docs/installation-guide.md` 已同步 Codex 入口和命令示例
- CLI Regression Status: targeted CLI pytest 通过；手动生成 Codex instructions 通过

Verification expectation:
新 CLI target 不应破坏原 Copilot/generic 入口口径；至少应通过 targeted CLI 测试并手动验证 Codex 目标输出。

Refs:

- `src/__main__.py`
- `README.md`
- `docs/installation-guide.md`

### authoring-surface-change

Trigger:
本轮改变了 instructions 生成面与 extension 内部模型 provider 发现/选择面，涉及 authoring/discovery surface。

Required fields:

- Changed Authoring Surface:
- Changed Authoring Surface: `AGENTS.md` / `AGENTS.override.md` 目标推断；extension `ManagedLLMProvider` 调用层、model family 列表读取与 provider factory
- Usage Guide Sync Status: `docs/installation-guide.md`、`vscode-extension/README.md`、`vscode-extension/package.json` 命令标题/说明已同步
- Discovery Surface Status: extension 命令层已不直接依赖 `CopilotLLMProvider`；当前默认 provider 仍是 GitHub Copilot
- Authoring Boundary Notes: Chat Participant 保留 VS Code Chat 原生 `request.model` 路径，不纳入本轮共享 provider 抽象

Verification expectation:
作者入口与发现面改动必须同步权威说明，并清楚写出“已抽象的层”与“仍保留原生路径的层”之间的边界。

Refs:

- `docs/installation-guide.md`
- `vscode-extension/README.md`
- `design_docs/stages/planning-gate/2026-04-22-vscode-extension-llm-provider-abstraction.md`

### dirty-worktree

Trigger:
当前仓库存在大量未提交/未跟踪改动，其中包含与本次 safe stop 边界直接相关的 Python、文档、handoff 与 extension 文件。

Required fields:

- Dirty Scope:
- Dirty Scope: 仓库当前包含 `.codex/`、`src/`、`docs/`、`vscode-extension/`、`release/` 等多处已修改与未跟踪文件
- Relevance to Current Handoff: 本次 handoff 覆盖的 Codex 适配与 provider abstraction 文件均处于未提交状态，下一会话必须基于当前工作树现实而不是假设“只存在 handoff 中列出的改动”
- Do Not Revert Notes: 不得回滚与当前 handoff 无关的既有脏改动；继续工作前应先区分“本次 safe stop 覆盖的文件”和“仓库原有其他变更”
- Need-to-Inspect Paths: `src/__main__.py`, `src/workflow/instructions_generator.py`, `docs/installation-guide.md`, `README.md`, `vscode-extension/`, `.codex/handoffs/`, `.codex/checkpoints/latest.md`, `design_docs/Project Master Checklist.md`, `design_docs/Global Phase Map and Current Position.md`

Verification expectation:
下次 intake 应允许 dirty-worktree 警告消失或降为已声明状态；至少要让下一会话明确知道哪些 dirty 路径与本次 safe stop 直接相关。

Refs:

- `design_docs/tooling/Document-Driven Workflow Standard.md`
- `design_docs/Project Master Checklist.md`

## Other

None.
