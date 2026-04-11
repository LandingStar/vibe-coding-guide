# Planning Gate — Self-Hosting Workflow Rule Formalization

- Status: **CLOSED**
- Phase: 29
- Date: 2026-04-11

## 问题陈述

当前仓库实际上已经进入 self-hosting / dogfood 状态，但这个事实主要散落在阶段记录里，还没有被提升为长期规则：

1. Phase 22 已交付 Pipeline + CLI、MCP Server + GovernanceTools、Instructions Generator、project-local pack 约束，并完成 MCP dogfood 验证。
2. Phase 27 使用平台自身的 CLI / MCP 工具执行了 3 个真实治理场景，形成 `design_docs/dogfood-feedback-phase-27.md`。
3. Phase 28 继续根据 dogfood 反馈修复 `issue-report` 分类与 checkpoint phase 同步问题。

如果这个要求不被写入长期规则，后续开发仍可能退回到“先堆功能、最后再 dogfood”的路径，导致平台结果没有持续反哺平台本身。

## 审核后边界

结合用户审核，本轮采用以下边界：

1. 文档型成果现在就作为默认自用控制面：Checklist、Phase Map、planning-gate、Workflow Standard、handoff、checkpoint、方向分析文档。
2. Pipeline / CLI / MCP / Instructions / project-local pack 等运行时入口虽然已经可用，但在首个稳定 release 前只作为受控 dogfood / verification 入口，不作为所有切片的强制默认依赖。
3. 只有在稳定版收口并经用户确认后，运行时链路才考虑升级为默认 self-hosting 主路径。

## 本轮只做什么

1. 把“文档型成果立即自用、运行时入口在稳定版前仅受控 dogfood”写入长期工作流文档。
2. 在权威文档中明确官方实例不只是示例，也是当前仓库的文档型 dogfood 路径。
3. 在状态板中记录“已经开始自用”的当前状态，并把运行时链路的 pre-release 边界写清楚。
4. 同步更新 doc-loop prompts，使后续 agent 在 planning / execute 阶段显式区分默认控制面与 pre-release 运行时入口。
5. 向用户报告当前已经在使用的范围与证据。

## 本轮明确不做什么

- 不修改 runtime / CLI / MCP 功能代码
- 不处理 F4 / F8
- 不扩展为所有目标仓库的通用平台强制规则
- 不进入 CI/CD 或 bootstrap 变更

## 验收与验证门

- 至少 1 份 `docs/` 权威文档明确 self-hosting / dogfood 的定位
- `design_docs/tooling/Document-Driven Workflow Standard.md` 明确本仓库开发时的自用规则
- `design_docs/Project Master Checklist.md` 记录当前已开始自用，并将其提升为持续要求
- 若 prompt pack 被改动，其表述与 Workflow Standard 一致
- 通过 reread 相关文档确认口径一致；本轮不要求新增自动化测试

## 需要同步的文档

- `docs/official-instance-doc-loop.md`
- `design_docs/tooling/Document-Driven Workflow Standard.md`
- `design_docs/Project Master Checklist.md`
- `.codex/prompts/doc-loop/01-planning-gate.md`
- `.codex/prompts/doc-loop/02-execute-by-doc.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/handoffs/CURRENT.md`
- `.codex/checkpoints/latest.md`

## 收口判断

- 该切片只 formalize 已存在的 repo-local 工作方式，不引入新的平台能力
- 文档与 prompt 口径对齐后即可收口
- 完成后再回到功能主线，继续决定 Phase 29 是否转入 F4 / F8 或其他方向