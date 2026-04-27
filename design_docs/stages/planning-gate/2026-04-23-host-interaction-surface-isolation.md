# Planning Gate — Host Interaction Surface Isolation

> 创建时间: 2026-04-23
> 状态: CLOSED

## 文档定位

本文件把“宿主交互面隔离”收敛为下一条可执行的窄 scope planning contract。

本候选直接承接：

- `design_docs/host-interaction-surface-isolation-direction-analysis.md`
- `design_docs/codex-independent-entry-contract-direction-analysis.md`
- `design_docs/direction-candidates-after-llmdoc-planning-gates.md`

当前只锁定**taxonomy + 资产映射 + 允许依赖方向**，不提前进入第二宿主实现、第二 provider、或统一 adapter framework 骨架。

## 当前问题

- 当前平台已经同时存在 CLI、MCP、instructions target、VS Code extension、Codex 接入等多种交互面，但尚未显式分层
- `generate-instructions` 已出现 `generic|codex|copilot` 目标差异，说明 interaction adapter 层真实存在，但边界未固定
- VS Code extension provider abstraction 只解决 extension 内部调用层解耦，不等于跨宿主模型
- 若不先收口宿主交互面隔离，后续 Copilot / Codex / Windsurf / Antigravity 等会持续被当作平行产品线处理

## 权威输入

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/host-interaction-surface-isolation-direction-analysis.md`
- `design_docs/codex-independent-entry-contract-direction-analysis.md`
- `design_docs/stages/planning-gate/2026-04-22-vscode-extension-llm-provider-abstraction.md`
- `docs/installation-guide.md`
- `docs/driver-responsibilities.md`
- `docs/external-skill-interaction.md`
- `docs/official-instance-doc-loop.md`

## 候选阶段名称

- `Host Interaction Surface Isolation`

## 本轮只做什么

- 定义四层模型：Core Contract / Portable Runtime / Interaction Adapter / Host UX
- 把当前仓库已有资产映射到四层，明确哪些面已经是 host-neutral，哪些仍是宿主相关
- 区分两类宿主差异：
  - 指令/助手目标差异（Copilot / Codex / generic）
  - 编辑器/UI 宿主差异（VS Code / Windsurf / Antigravity / 其他）
- 明确未来宿主适配的允许依赖方向，防止 host-specific 语义反向侵入核心 contract
- 产出 2-4 个首批子案例映射，其中 Codex 独立入口 contract 作为第一子案例

## 本轮明确不做什么

- 不实现第二编辑器适配
- 不实现第二 provider
- 不设计统一 adapter registry / framework 骨架
- 不重构现有 VS Code extension 代码
- 不同时推进 public surface convergence 或 scratch/stable docs split 的实际实施

## 验收与验证门

- 针对性测试：文档层一致性检查，确认四层模型与现有 authority docs、driver / external-skill contract 不冲突
- 更广回归：无代码回归；仅检查本轮文档未与安装指南、provider abstraction planning-gate、official instance 定位相冲突
- 手测入口：用“Codex 主链接入”“VS Code extension 交互”“未来第二编辑器占位”三种样例手工走一遍分层映射
- 文档同步：若候选被激活并完成，需同步 Workflow / 安装 / 方向候选类文档与状态面口径

## 需要同步的文档

- `docs/installation-guide.md`
- `docs/driver-responsibilities.md`
- `docs/external-skill-interaction.md`
- `design_docs/direction-candidates-after-llmdoc-planning-gates.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/checkpoints/latest.md`
- `.codex/handoffs/CURRENT.md`（仅当本候选进入并完成实际切片时）

## 子 agent 切分草案

- 若需要做只读资产盘点，可让 investigator 统计当前 CLI / MCP / instructions / extension 文档与代码面的宿主差异点
- taxonomy 结论、允许依赖方向与 planning-gate write-back 仍由主 agent 负责

## 收口判断

- 为什么这条切片可以单独成立：它先解决“哪些属于平台核心、哪些只是宿主交互薄层”的边界问题，为后续任何单一宿主扩展建立统一前提
- 做到哪里就应该停：当四层模型、资产映射、允许依赖方向和首批子案例都清晰后就应停，不继续扩到 adapter framework 或具体宿主实现
- 下一条候选主线是什么：
  - 若本切片完成，可把 `Codex 独立系统/入口 contract` 作为首个子案例继续收窄
  - 若用户更关心文档沉淀语义，则回到 `2026-04-23-temporary-scratch-stable-docs-split.md`
  - 若用户更关心入口体验，则回到 `2026-04-23-public-surface-convergence.md`