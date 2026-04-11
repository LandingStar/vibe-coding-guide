# Planning Gate — Dogfood Feedback Remediation

- Status: **CLOSED**
- Phase: 28
- Date: 2026-04-10

## 问题陈述

Phase 27 的 dogfood 反馈表明，当前平台的 blocking 级问题已修复，但仍有两个中优先级问题直接影响真实使用：

1. `issue-report` 输入的分类准确率不足。
2. `current_phase` 与 checkpoint / planning-gate 状态同步不一致。

这两个问题都会直接影响治理链的可信度，比继续扩功能更值得优先收敛。

## 权威输入

- `design_docs/dogfood-feedback-phase-27.md`
- `design_docs/direction-candidates-after-phase-27.md`
- `design_docs/context-persistence-design.md`
- `review/research-compass.md`

## 本轮只做什么

### Slice A: issue-report 分类修正

修改 `src/pdp/intent_classifier.py`：
- 为 `issue-report` 扩充关键词：`bug`、`错误`、`异常`、`崩溃`、`error`
- 补测试，覆盖中文/英文 bug report 输入
- 目标：让典型 bug report 不再落到 `ambiguous` 或错误归类到 `correction`

### Slice B: current_phase / checkpoint 同步

修改 checkpoint/write-back 相关流程：
- 确保 Phase write-back 完成后，`.codex/checkpoints/latest.md` 同步更新当前 phase
- 保证 `check_constraints()`、`get_next_action()` 读取到的 phase 与 Checklist/Phase Map 一致
- 补测试，覆盖 write-back 后状态恢复场景

## 本轮明确不做什么

- 不处理 `PackRegistrar` 路径解析（F4）
- 不改 `CLI check` 输出结构（F8）
- 不进入错误恢复/重试策略
- 不做 CI/CD

## 验收与验证门

- `issue-report` 中文/英文场景有测试覆盖并通过
- checkpoint 同步场景有测试覆盖并通过
- 全量回归 559+ 测试通过
- dogfood 反馈文档更新状态

## 需要同步的文档

- `design_docs/dogfood-feedback-phase-27.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/handoffs/CURRENT.md`

## 子 agent 切分草案

- 当前不需要子 agent；主 agent 直接完成即可

## 收口判断

- 这条切片可以单独成立，因为它只处理 Phase 27 已经实测暴露的两个高价值问题
- 做到分类修正 + phase/checkpoint 同步 + 测试通过就应停
- 下一条候选主线：F4/F8 的次级 dogfood 修复，或错误恢复策略