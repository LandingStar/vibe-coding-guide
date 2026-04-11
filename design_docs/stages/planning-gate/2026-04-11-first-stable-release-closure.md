# Planning Gate — First Stable Release Closure

- Status: **COMPLETED**
- Phase: 32
- Date: 2026-04-11

## 问题陈述

Phase 29 已明确：在首个稳定 release 前，当前仓库的运行时链路只能作为 pre-release dogfood 入口，不能默认提升为 self-hosting 主路径。

Phase 30 和 Phase 31 已先后收掉两类最直接的 dogfood 盲点：

1. F8：CLI `check` 不再把纯约束 / 状态检查和完整治理链混在一起。
2. F4：PackRegistrar skipped validator 的原因现在可直接解释，不再停留在黑箱状态。

在此基础上，下一步最有价值的工作不再是继续零散修 bug，而是把“什么条件下才算首个稳定 release”写成一条可执行的窄 scope 规划切片。

## 审核后边界

用户已确认当前 Phase 32 先只做“稳定版边界 + blocker checklist 定义”，不把版本号、changelog、发布动作并入同一条切片。

## 权威输入

- `design_docs/stages/planning-gate/2026-04-11-self-hosting-workflow-rule.md`
- `design_docs/direction-candidates-after-phase-31.md`
- `design_docs/Project Master Checklist.md`
- `docs/official-instance-doc-loop.md`
- `docs/current-prototype-status.md`

## 本轮只做什么

### Slice A: 稳定版边界定义

- 明确首个稳定 release 要覆盖哪些默认入口
- 明确哪些入口仍然保持实验 / 非阻塞状态
- 定义“允许默认 self-hosting”的最小判断标准

### Slice B: 收口清单

- 列出进入首个稳定 release 前必须处理的 blocker / must-have
- 明确哪些 backlog 不是首个稳定版的阻塞项
- 把当前已知验证门整理成可执行 checklist

## 本轮明确不做什么

- 不直接实现 CI/CD
- 不直接做版本发布自动化
- 不扩展新的运行时能力
- 不把 script-style validator 语义升级并入当前切片

## 验收与验证门

- 稳定版边界有清晰的 in-scope / out-of-scope 定义
- 默认 self-hosting 主路径的前置条件被文档化
- blocker / non-blocker 清单可直接转成后续实现切片

## 需要同步的文档

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/handoffs/CURRENT.md`
- `.codex/checkpoints/latest.md`

## 收口判断

- 该切片只做稳定版边界和收口条件定义，不直接进实现
- 做到边界清晰 + checklist 可执行就应收口
- 完成后再决定是否进入稳定版 blocker 实现、错误恢复或 CI/CD 配套