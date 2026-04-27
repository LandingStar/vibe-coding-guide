# Planning Gate — Codex Independent Entry Contract

> 创建时间: 2026-04-23
> 状态: CLOSED

## 文档定位

本文件把“Codex 独立系统 / 入口 contract”收敛为下一条可执行的窄 scope planning contract。

本候选直接承接：

- `design_docs/codex-independent-entry-contract-direction-analysis.md`
- `design_docs/host-interaction-surface-isolation-direction-analysis.md`
- `docs/host-interaction-model.md`
- `docs/starter-surface.md`

当前只锁定**Codex 最短入口路由 + 与 extension/Copilot 面的职责边界**，不提前进入 helper surface、第二 provider 或宿主实现。

## 当前问题

- Codex 主链已经可用，但其最短入口 contract 仍分散在安装说明、AGENTS 生成链和方向分析里
- 当前需要把 Codex 入口单独写成一条清晰的 product boundary，而不是继续与 extension provider 话题混用
- `docs/host-interaction-model.md` 已把 Codex 归入 Interaction Adapter Layer，但仍缺少一个针对 Codex 的独立入口 contract 文档化切片
- 若不先收口这条 contract，后续 helper entry / companion surface 很容易提前长成第二套解释

## 权威输入

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/codex-independent-entry-contract-direction-analysis.md`
- `design_docs/host-interaction-surface-isolation-direction-analysis.md`
- `docs/host-interaction-model.md`
- `docs/starter-surface.md`
- `docs/installation-guide.md`
- `design_docs/stages/planning-gate/2026-04-22-vscode-extension-llm-provider-abstraction.md`

## 候选阶段名称

- `Codex Independent Entry Contract`

## 本轮只做什么

- 定义 Codex 使用面的最短入口闭环：instructions → MCP 注册 → validation / authority docs 跳转
- 明确 Codex 与 VS Code/Copilot extension 的职责边界
- 明确为什么 Codex 不等于 extension 第二 provider
- 明确未来若出现 Codex helper surface，哪些内容可以薄层化，哪些仍必须保留在 authority docs
- 产出一个可被后续 companion/onboarding 复用的 Codex 独立入口 contract

## 本轮明确不做什么

- 不实现新的 extension provider
- 不重写 Chat Participant
- 不实现 Codex helper entry 或 companion packaging
- 不修改 Python runtime / MCP contract
- 不同时推进第二编辑器宿主适配

## 验收与验证门

- 针对性测试：文档层一致性检查，确认 starter surface、installation guide、Codex contract 之间的首跳描述一致
- 更广回归：无代码回归；仅检查本轮文档未与 host interaction model、provider abstraction planning-gate 冲突
- 手测入口：用“首次在 Codex 中接入”“已在仓库内工作、只想知道 Codex 最短入口”“比较 Codex 与 VS Code/Copilot 职责边界”三种样例手工走读
- 文档同步：若候选被激活并完成，需同步 starter surface、installation guide、Checklist / Phase Map / checkpoint 口径

## 需要同步的文档

- `docs/starter-surface.md`
- `docs/installation-guide.md`
- `docs/host-interaction-model.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/checkpoints/latest.md`
- `.codex/handoffs/CURRENT.md`（仅当本候选进入并完成实际切片时）

## 子 agent 切分草案

- 若需要只读梳理当前 Codex 入口散点，可让 investigator 统计 AGENTS / install / MCP 注册 / validation 的首跳差异
- 最终 contract、边界结论与 write-back 仍由主 agent 负责

## 收口判断

- 为什么这条切片可以单独成立：它在宿主 taxonomy 已经明确后，专门收口 Codex 这一条 Interaction Adapter 子案例，不触碰宿主 UI 或 provider 实现
- 做到哪里就应该停：当 Codex 最短入口闭环、与 extension 的职责边界、helper 非目标和同步面都清晰后就应停，不继续扩到 helper 或 provider
- 下一条候选主线是什么：
  - 若本切片完成，可继续进入 helper entry / companion surface 方向
  - 若用户更关心恢复体验，则回到 scratch 轻量恢复协议方向