# Planning Gate — Plugin-Side Codex Host Support Gap

> 日期: 2026-05-12
> 状态: PROPOSED
> 来源: 2026-05-12 Codex 支持性检查 + scope interrupt `int-6855ef8e0603`
> 当前不改变 active gate: `design_docs/stages/planning-gate/2026-05-27-knowledge-graph-engine-progress-preview-integration.md`
> 关联实现面: `vscode-extension/src/chat/participant.ts`, `vscode-extension/src/llm/providerFactory.ts`, `vscode-extension/package.json`, `src/workflow/instructions_generator.py`, `src/mcp/server.py`

## Why this exists

2026-05-12 的支持性检查已经给出一个足够稳定的判断：

1. Codex 主链当前已经通过 `AGENTS.md` + MCP + CLI/validation 成立
2. VS Code extension 当前可以消费同一条 runtime，但它仍然只是 `Host UX Layer` 的 VS Code 宿主实现，而不是 Codex 的一等交互宿主
3. authority docs 已明确“Codex 不等于 extension 第二 provider”，但仓库里还没有一份独立 future slice 来登记这个插件侧缺口与后续激活条件
4. 当前 active implementation gate 仍然是 `design_docs/stages/planning-gate/2026-05-27-knowledge-graph-engine-progress-preview-integration.md`，因此任何 Codex 插件侧工作都不应直接混入当前 Knowledge Graph Engine 图面切片

因此，本 gate 只负责把“插件侧 Codex 支持缺口”登记成一个独立 future slice，并固定它的边界与激活条件。

## Scope

本 gate 只处理：

1. 把插件侧 Codex 支持缺口登记成独立 planning-gate
2. 明确 `Portable Runtime Layer` 与 `Host UX Layer` 上“支持 Codex”的含义差异
3. 固定任何后续 Codex 宿主工作应从什么最小激活条件开始
4. 若本 gate 后续被激活，收口相应 authority wording 与 backlog 登记

本 gate 不处理：

1. 不在 extension 内实现新的 Codex provider
2. 不改写当前 Knowledge Graph Engine graph-view active gate
3. 不增加第二编辑器宿主实现
4. 不修改现有 CLI / MCP core contract
5. 不直接发布 Codex 专用 extension/runtime 变体

## Working hypothesis

当前假设是：

1. 现在真正缺的不是 `docBasedCoding.llm.provider` 里少一个 `codex` 枚举，而是缺少一份“如果未来要补 Codex 宿主层支持，应如何独立建模”的 planning contract
2. `2026-04-22-vscode-extension-llm-provider-abstraction` 只解决 extension 内部命令层 provider 解耦，不定义 Codex 的产品边界
3. 如果后续需要更短的 Codex 使用面，合理路径应是 `Interaction Adapter Layer` 上的薄 companion / helper surface，而不是把 VS Code Chat participant 语义硬迁过去
4. 因为 authority docs 已经把边界说清，所以第一条 future slice 更适合保持 docs-first / smoke-test-first，而不是直接进入 code-first 实现

## Required inputs

当前必须复用的权威输入：

1. `docs/codex-entry-contract.md`
2. `docs/host-interaction-model.md`
3. `docs/installation-guide.md`
4. `design_docs/stages/planning-gate/2026-04-22-vscode-extension-llm-provider-abstraction.md`
5. `design_docs/host-interaction-surface-isolation-direction-analysis.md`

当前必须复核的实现锚点：

1. `vscode-extension/src/chat/participant.ts`
2. `vscode-extension/src/llm/providerFactory.ts`
3. `vscode-extension/package.json`
4. `src/workflow/instructions_generator.py`
5. `src/mcp/server.py`

## First slice suggestion

若后续激活本 gate，第一刀建议只做：

1. 补一份明确的支持矩阵，区分 `Codex mainline supported` 与 `plugin-side Codex host parity not provided`
2. 在 authority docs 中把“VS Code extension 不是 Codex 第一等宿主支持”写成更显式的 future-gap 口径
3. 固定下一条真正实现线的触发条件：
   - `real Codex host smoke test`
   - 或 `thin Codex helper entry / companion surface`
4. 不在第一刀里引入任何新的 extension/runtime 代码实现

## Success bar

本 gate 的最小成功标准应是：

1. future slice 明确写清 Codex 主链已经通过 `AGENTS.md` + MCP + CLI/validation 成立
2. future slice 明确写清 VS Code extension 当前不等于 Codex 的一等宿主支持
3. `extension second provider` 被固定为本 gate 的显式非目标
4. 后续若要进入真实实现，激活条件已经被写清
5. 当前 `design_docs/stages/planning-gate/2026-05-27-knowledge-graph-engine-progress-preview-integration.md` 的 active 状态不受影响

## Focused validation

若后续激活本 gate，focused validation 至少应复用以下最小闭环：

1. `doc-based-coding generate-instructions --target codex --output <tmp>`
2. `doc-based-coding-mcp --help`
3. `doc-based-coding info`
4. `doc-based-coding validate`
5. `npm run build`（`vscode-extension/`）

## Activation precondition

本 gate 应保持 `PROPOSED`，直到以下任一条件成立：

1. 当前 `design_docs/stages/planning-gate/2026-05-27-knowledge-graph-engine-progress-preview-integration.md` 已 formal close 或被显式暂停
2. 用户明确把 Codex 宿主支持优先级提升到当前 graph-view 主线之前
3. 真实 Codex dogfood 暴露出不能由现有 `AGENTS.md` + MCP + CLI surface 解决的宿主层缺口

## Stop condition

本 gate 作为 future slice draft，做到以下程度就应停下：

1. 插件侧 Codex 缺口已被独立登记，而不是继续停留在口头结论
2. 当前 active Knowledge Graph Engine gate 未被误扩 scope
3. 后续真实实现的激活条件已经固定
4. 没有把 `provider abstraction` 错误升级成“现在就该做 extension 第二 provider”
