# Planning Gate — Handoff Validator 独立化

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-15-handoff-validator-independent-guard |
| Scope | 为 explicit handoff 路径补独立 validator、executor 接线与最小审计事件 |
| Status | DONE |
| 来源 | design_docs/subagent-research-synthesis.md P2 |
| 前置 | 2026-04-15-handoff-recovery-hardening 已完成 |
| 测试基线 | 905 passed, 2 skipped |

## 文档定位

本文件用于把 P2 `Handoff Validator 独立化` 收敛成一个可审核、可执行的窄 scope planning contract。

## 当前问题

当前 handoff 相关代码已经具备：

- `Handoff` schema
- `handoff_builder.build()` / `handoff_mode.execute()`
- Executor 中的 handoff 模式分支
- review state machine 接入

但仍缺一层**独立的 handoff-specific validator / guard**：

1. `Handoff` 目前只有“生成 schema-conforming dict”的能力，没有运行时独立验证器。
2. `docs/subagent-management.md` 与 `design_docs/subagent-management-design.md` 都明确要求：handoff 不应只被视为普通 tool call，且需要独立 tracing、review、validator。
3. 当前 `_execute_handoff_mode()` 在拿到 handoff 结果后直接进入 review 路径，没有 handoff validation failure 的单独处理分支。
4. 这导致 handoff 只能依赖通用 review，而不能在进入 review 前做 fail-fast guard。

## 权威输入

- `docs/subagent-management.md`
- `docs/subagent-schemas.md`
- `docs/delegation-decision.md`
- `docs/specs/handoff.schema.json`
- `design_docs/subagent-management-design.md`
- `design_docs/subagent-research-synthesis.md`
- `src/collaboration/handoff_mode.py`
- `src/subagent/handoff_builder.py`
- `src/pep/executor.py`

## 候选阶段名称

- `P2: Handoff Validator 独立化`

## 本轮只做什么

1. 新增独立 `HandoffValidator` 协议与默认实现
   - 与 `ReportValidator` 分离，不复用通用 report 校验路径
   - 第一版使用平台内建固定逻辑，不做 pack 可插拔

2. 固定第一版 handoff validation 范围
   - schema 校验：基于 `docs/specs/handoff.schema.json`
   - 语义 guard：收口 `docs/subagent-schemas.md` 已明确的不变量
     - `active_scope` 非空
     - `authoritative_refs` 非空
     - `intake_requirements` 非空
     - `current_gate_state` 不丢失 handoff 时的审批语境

3. 接入 Executor handoff 路径
   - `Executor.__init__` 接受可选 `handoff_validator`
   - `_execute_handoff_mode()` 在 handoff 生成后、结果返回前执行独立 validation
   - validation 失败时：
     - 不持久化 invalid handoff
     - 返回显式 `handoff_validation` 结果
     - 进入 review 路径，而不是当作成功 handoff 继续流转

4. 增补最小审计事件
   - `handoff_validated`
   - `handoff_validation_failed`

5. 补测试
   - valid handoff 通过 validator
   - schema invalid handoff 被拒绝
   - semantic invalid handoff 被拒绝
   - invalid handoff 不落盘
   - valid handoff 的既有行为不回归

## 本轮明确不做什么

- 不做 pack 级可插拔 handoff validator
- 不改 `delegation_decision` schema
- 不补 `Handoff` tracing 扩展字段
- 不做 `Report -> Writeback Plans` 自动映射
- 不做 handoff 写回权威文档痕迹
- 不扩展 team / swarm / subgraph 模式

## 关键实现落点

- `src/interfaces.py`
  - 新增 `HandoffValidator` protocol
- `src/subagent/handoff_validator.py`
  - 新增默认 validator 实现
- `src/pep/executor.py`
  - 注入并消费 `handoff_validator`
- `tests/test_handoff.py`
  - 扩展 handoff validator 与 executor integration 测试
- 如有必要：`src/collaboration/handoff_mode.py`
  - 仅做最小配合，不重构协作模式主体

## 验收与验证门

- 针对性检查：
  - [x] handoff validator 独立存在，不复用 report validator
  - [x] `_execute_handoff_mode()` 在返回前执行 handoff validation
  - [x] invalid handoff 不持久化
  - [x] `handoff_validated` / `handoff_validation_failed` 审计事件可观察
- 自动化验证：
  - [x] handoff 相关 targeted tests 新增 ≥ 6（新增 7 个）
  - [x] 全量回归继续通过（905 passed, 2 skipped）
- 文档同步：
  - [x] 本 planning-gate 回写为 done
  - [x] `Project Master Checklist.md` 状态同步
  - [x] `Global Phase Map and Current Position.md` 阶段同步

## 需要同步的文档

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- 本 planning-gate 文档自身

## 子 agent 切分草案

- 本轮不引入子 agent。
- 理由：P2 需要同时把握权威文档语义、executor 路径和 handoff 运行时行为，主 agent 直接收口更稳妥。

## 收口判断

- **为什么这条切片可以单独成立**：P2 只补 handoff-specific validator/guard，不涉及 PDP 决策模型扩张，也不涉及 writeback / tracing 的下一层扩展。
- **做到哪里就应该停**：独立 validator 接入 handoff 路径、 targeted tests 通过、全量回归通过，即停。
- **下一条候选主线**：若 P2 完成，优先看 `Report -> Writeback Plans` 自动映射（P3）或 `Handoff` 审计痕迹（P4）。

## 执行结果

- 状态：DONE
- 完成日期：2026-04-15
- 改动文件：
  - src/interfaces.py
  - src/pep/executor.py
  - src/subagent/handoff_validator.py
  - tests/test_handoff_validator.py
- 验证：
  - handoff targeted tests：27 passed
  - full regression：905 passed, 2 skipped
