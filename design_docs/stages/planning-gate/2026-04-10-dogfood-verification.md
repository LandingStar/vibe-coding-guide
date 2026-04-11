# Planning Gate — Dogfood 深度验证

- Status: **CLOSED**
- Phase: 27
- Date: 2026-04-10

## 问题陈述

平台已到 Phase 26（555 tests），功能覆盖相当完整。但所有验证都是 unit/integration 级别——没有在真实开发流程中使用自身工具链处理过一个完整的治理场景。

参考 `review/research-compass.md` 中 OpenHands、Continue 等项目的 dogfood-first 策略：功能堆叠的边际收益在降低，真实使用反馈才能产出可靠的优先级信号。

## 验证目标

用平台自身的 MCP 工具和 CLI 处理 **3 种真实治理场景**，记录每个场景中的：
- 工具产出是否符合预期
- 哪些步骤需要人工干预/补充
- UX 摩擦点（参数不直观、输出不够用、缺少关键信息等）
- 需要修复或改进的具体问题

### 场景 1: governance_decide 处理 issue-report

输入一段真实的 issue-report 文本（如 "checkpoint.py 的 todos 参数不支持字符串列表，需要 dict，但文档没说明"），观察：
- intent 分类是否正确（应为 issue-report）
- gate 判定是否合理（应为 review）
- delegation 决策是否产出可执行 contract
- 约束检查是否有效

### 场景 2: check_constraints 状态恢复

模拟上下文压缩后的恢复场景：
- 调用 check_constraints，验证返回的 files_to_reread 列表是否完整
- 调用 get_next_action，验证推荐的下一步是否准确
- 检查 checkpoint 文件是否被正确引用

### 场景 3: writeback_notify phase 推进

模拟 Phase 完成后的自动推进：
- 调用 writeback_notify("Phase 27: Dogfood Verification")
- 验证返回的 pending_gates 检测是否正确
- 验证 files_to_update 列表是否完整

## 本轮只做什么

1. 在终端执行 3 个 CLI 场景，记录输出
2. 分析输出，识别问题和改进点
3. 将发现写入 dogfood 反馈文档
4. 修复发现的 **blocking 级别** 问题（如果有）
5. 非 blocking 问题记录为 backlog

## 本轮明确不做

- 不做大规模重构
- 不新增功能（除非是 blocking 修复）
- 不修改 MCP server 协议层
- 不做 CI/CD

## 验收与验证门

- 3 个场景全部执行并记录
- 发现的 blocking 问题已修复
- dogfood 反馈文档已创建
- 全量回归 555+ 测试通过

## 同步更新

- 创建 `design_docs/dogfood-feedback-phase-27.md`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/handoffs/CURRENT.md`

## 收口判断

- 3 个场景的执行是 pass/fail 二元判断：要么工具链产出了合理结果，要么暴露了具体问题
- 做到 blocking 问题修复 + 反馈文档就应该停
- 下一条候选主线：根据 dogfood 反馈确定
