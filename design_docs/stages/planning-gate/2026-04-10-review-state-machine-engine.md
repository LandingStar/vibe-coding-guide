# Planning Gate — Review 状态机引擎

- Status: **CLOSED**
- Phase: 11
- Date: 2026-04-10

## 问题陈述

`review-state-machine.md` 定义了完整的 6 状态/7 事件/8 条迁移规则，但当前代码中没有状态机实现。PEP 只输出 `waiting_review` 字符串，无法跟踪一个提案从 proposed → waiting_review → approved/rejected/revised → applied 的完整生命周期。

## 切片计划

### Slice A — 状态机核心引擎

**范围：**
- 创建 `src/review/state_machine.py`
  - 6 个状态、7 个事件（枚举或常量）
  - 迁移表：8 条核心迁移规则 + inform 快速路径
  - `ReviewStateMachine` 类
    - `transition(event) -> new_state`
    - 非法迁移抛出 `InvalidTransitionError`
    - 每次迁移记录审计条目（对象、前状态、事件、后状态、原因、关联 gate）
  - `current_state`、`history` 属性
- 测试：所有合法迁移 + 所有非法迁移 + 审计记录

**不做：**
- 不涉及持久化
- 不涉及 PEP 集成

### Slice B — PEP 集成

**范围：**
- 更新 `src/pep/executor.py`
  - 每次 execute 创建或接收 ReviewStateMachine 实例
  - inform gate → 快速路径（proposed → applied）
  - review/approve gate → submit_for_review（proposed → waiting_review）
  - delegation 完成后若 report.status=completed → approve + apply
  - escalation 触发时保持 waiting_review
- 执行结果中包含 `review_state` 和 `review_history`
- 端到端测试
- write-back

**不做：**
- 不实现外部持久化（文件/DB）
- 不实现 revision 流程的自动触发（留给后续 Phase）

## 验证门

- [x] `pytest tests/` 全部通过（129 passed, 1 skipped）
- [x] 所有 8 条迁移规则测试覆盖
- [x] 非法迁移正确抛出异常
- [x] PEP 端到端测试包含状态机状态
- [ ] `validate_doc_loop.py --target .` 通过

## 依赖

- `docs/review-state-machine.md`（权威来源）
- `src/pep/executor.py`（Phase 10 产出）

## 风险

- Slice B 的 PEP 集成可能需要调整现有测试的 assert（因为执行结果会包含新的 review_state 字段）。
