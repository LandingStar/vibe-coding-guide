# Planning Gate — Review 完整流程 + 真实通知系统

- Status: **CLOSED**
- Phase: 13
- Date: 2026-04-10

## 问题陈述

Phase 11 实现了 Review 状态机（6 状态/7 事件/8 迁移规则），但 PEP executor 中仅驱动 `proposed → waiting_review` 和 `proposed → applied` 路径。`rejected`（拒绝）和 `revised`（修订重提）路径完全没有 PEP 驱动逻辑。此外，升级通知仍为 StubNotifier（内存记录），无法在真实团队中工作。

**当前缺口：**
- PEP 无法处理 reviewer 返回的 approve/reject/request_revision 反馈
- rejected 后无降级/重新路由逻辑
- revised 后无重新提交循环
- 通知只有 StubNotifier，无 webhook/console/file 通道

## 切片计划

### Slice A — 通知适配器系统

**范围：**
- 创建 `src/pep/notifiers/` 包
  - `__init__.py`
  - `console_notifier.py`：打印到 stdout（开发/调试用）
  - `webhook_notifier.py`：通用 HTTP POST 通知（含 URL + headers 配置）
  - `file_notifier.py`：写通知到 JSON 文件（用于 CI/集成测试）
- 每个 notifier 实现 `EscalationNotifier` Protocol（`notify(notification) -> dict`）
- webhook_notifier 使用 `urllib.request`（标准库，不引入外部依赖）
- 测试：各 notifier 单元测试、Protocol 兼容性测试

**不做：**
- 不实现 Email/Slack（留给后续，可按同模式扩展）
- 不涉及 PEP 集成变更

### Slice B — Review Orchestrator（Rejected/Revised 流程驱动）

**范围：**
- 创建 `src/pep/review_orchestrator.py`
  - `ReviewOrchestrator` 类
  - `submit_feedback(rsm, feedback_event, reason) -> dict`：接收 reviewer 反馈并驱动状态机
  - 当 `feedback_event=approve` → `rsm.transition(APPROVE)` → 若 apply 条件满足则 `rsm.transition(APPLY)`
  - 当 `feedback_event=reject` → `rsm.transition(REJECT)` → 返回 rejected 结果
  - 当 `feedback_event=request_revision` → `rsm.transition(REQUEST_REVISION)` → 返回 revised 结果，含"需要修改并重新提交"指令
  - 当 revised 后 `revise` → `rsm.transition(REVISE)` 回到 proposed → 可再次 submit_for_review
- 更新 `src/pep/executor.py`
  - `execute()` 返回的结果附带 `review_machine` 引用（供后续 feedback 使用）
  - 新增 `submit_review_feedback(result, feedback, reason)` 方法：使用保存的 rsm 驱动后续状态
- 端到端测试：
  - approve 后 apply + 触发 writeback
  - reject 后 terminal state
  - request_revision → revise → 重新 submit_for_review
  - 通知在 rejection 和 revision 时被发送
- write-back

**不做：**
- 不实现外部 reviewer UI 或 CLI
- 不实现自动 revision 内容生成

## 验证门

- [ ] `pytest tests/` 全部通过
- [ ] 3 个 notifier 通过单元测试
- [ ] ReviewOrchestrator approve/reject/revision 路径测试
- [ ] reject 后状态为 terminal
- [ ] revision 循环可重新提交

## 依赖

- `src/review/state_machine.py`（Phase 11 产出）
- `src/interfaces.py` — EscalationNotifier Protocol
- `src/pep/executor.py`（Phase 12 产出）

## 风险

- webhook_notifier 测试需要 mock HTTP（可用 unittest.mock.patch）
- Executor 暴露 rsm 引用可能需要调整现有测试的 assert
