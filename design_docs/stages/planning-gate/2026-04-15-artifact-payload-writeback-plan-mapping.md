# Planning Gate — Artifact Payload WritebackPlan Mapping

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-15-artifact-payload-writeback-plan-mapping |
| Scope | 消费 Subagent Report.artifact_payloads 并映射为真实 WritebackPlan，第一版只支持 create/update/append |
| Status | DONE |
| 来源 | design_docs/subagent-research-synthesis.md §P3，design_docs/subagent-tracing-writeback-direction-analysis.md Gap B |
| 前置 | 2026-04-15-subagent-report-writeback-payload 已完成 |
| 测试基线 | 922 passed, 2 skipped |

## 文档定位

本文件用于把真正的 P3 `artifact_payloads -> WritebackPlan` 自动映射收敛成一个安全、可审核的窄 scope planning contract。

## 当前问题

`Subagent Report` 现在已经具备可选 `artifact_payloads`：

- `path`
- `content`
- `operation`
- `content_type`

但当前运行时仍存在一个明确断点：

1. `WritebackEngine.plan()` 只会生成默认 summary plan，不消费 `report.artifact_payloads`。
2. 即使子 agent 已经返回了结构化 payload，PEP 也不会把它转成真实 `WritebackPlan`。
3. 因而刚完成的 richer payload slice 只解决了 contract 问题，还没有进入真正的 writeback 管道。

与此同时，这一轮不应再次扩 scope：

- 不能回退到只看 `changed_artifacts`
- 不能直接引入 `section_replace` / `line_insert` 这类 directive 级操作
- 不能绕过 contract 的 `allowed_artifacts` 边界

## 权威输入

- `design_docs/subagent-research-synthesis.md`
- `design_docs/subagent-tracing-writeback-direction-analysis.md`
- `design_docs/stages/planning-gate/2026-04-15-subagent-report-writeback-payload.md`
- `docs/subagent-schemas.md`
- `docs/specs/subagent-report.schema.json`
- `src/pep/writeback_engine.py`
- `src/pep/executor.py`
- `src/subagent/contract_factory.py`
- `tests/test_pep_writeback_integration.py`

## 候选阶段名称

- `P3: artifact_payloads -> WritebackPlan Mapping`

## 推荐方案

推荐只消费 `report.artifact_payloads`，不再推导或猜测 `changed_artifacts`。

第一版映射规则：

1. 仅在 `review_state=applied` 时生效。
2. 仅消费 schema 已允许的 `create` / `update` / `append`。
3. `path` 必须是 project-root 内相对路径；绝对路径、越界路径、空路径直接跳过。
4. 若 `contract.allowed_artifacts` 非空，则 payload path 必须命中允许边界；否则跳过。
5. 映射结果直接生成真实 `WritebackPlan`，并与默认 summary plan 一起进入现有 writeback 执行链。

理由：

1. 刚完成的 P3-prep 已经提供了结构化 payload，这一轮应直接消费现成 contract，而不是再做保守中间层。
2. `allowed_artifacts` 已是现有 contract 的 write boundary，直接复用它能避免 report 绕过委派边界。
3. 保持 operation 只到 `create` / `update` / `append`，可以把复杂 directive 级写回继续留在后续切片。

## 本轮只做什么

1. 在 writeback planning 路径中消费 `report.artifact_payloads`
   - 可放在 `WritebackEngine.plan()`，直接读取 `execution_result.report` 与 `execution_result.contract`
   - 不新增第二套独立执行器

2. 增加 payload path 安全归一化
   - 拒绝空路径、绝对路径、越出 project root 的路径
   - 统一成 project-root 相对路径后再进入 plan

3. 把 `allowed_artifacts` 作为 report-derived writeback 的硬边界
   - `allowed_artifacts` 为空时，不生成 report-derived user-file plans
   - 非空时，只允许 exact match 或受控子路径命中

4. 保持现有 summary writeback 行为，同时增加 report-derived 规划摘要
   - summary 中追加 payload-derived plans 数量
   - 追加 skipped payload 数量摘要，便于 reviewer 观察

5. 补 targeted tests
   - 有合法 payload 时会生成真实 `WritebackPlan`
   - `allowed_artifacts` 不命中时被拒绝
   - 绝对路径 / 越界路径被拒绝
   - `allowed_artifacts` 为空时不生成 user-file payload plans
   - `create` / `update` / `append` 三种映射都可达
   - dry-run / non-dry-run 行为一致

## 本轮明确不做什么

- 不再消费 `changed_artifacts` 生成 plan
- 不支持 `section_replace` / `section_append` / `line_insert` / `line_replace`
- 不扩展 `artifact_payloads` schema 字段
- 不让 worker / template / example 在本轮强制产出 payload
- 不修改 handoff / audit / checkpoint 的下一层问题

## 关键实现落点

- `src/pep/writeback_engine.py`
  - `artifact_payloads` 到 `WritebackPlan` 的映射与 path 归一化
- `src/pep/executor.py`
  - 若需要，补充 writeback planning 摘要元数据
- `tests/test_pep_writeback_integration.py`
  - 扩展 delegated report -> writeback integration 覆盖
- 可能新增：
  - `tests/test_writeback_engine.py`

## 验收与验证门

- [x] 合法 `artifact_payloads` 会生成 report-derived `WritebackPlan`
- [x] `allowed_artifacts` 边界被严格执行
- [x] 绝对路径 / 越界路径 / 空路径不会进入 plan
- [x] summary writeback 能反映 payload-derived plans 与 skipped 数量
- [x] targeted tests 新增 >= 8（实际定向回归 36 passed）
- [x] 全量回归继续通过（922 passed, 2 skipped）

## 需要同步的文档

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- 本 planning-gate 文档自身

## 子 agent 切分草案

- 本轮不引入子 agent。
- 理由：P3 需要同时把握 report contract、contract write boundary 与 writeback runtime，主 agent 直接收口更稳妥。

## 收口判断

- **为什么这条切片可以单独成立**：它只解决“结构化 payload 如何进入真实 writeback 管道”的最小闭环，不再扩 schema，也不碰 directive 级更新。
- **做到哪里就应该停**：payload-derived plans 可控进入现有 writeback 链、targeted tests 通过、全量回归通过，即停。
- **下一条候选主线**：若 P3 完成，再决定是补 P4 `handoff` 审计痕迹，还是单独做 payload-producing worker / example 对齐切片。

## 执行结果

- 状态：DONE
- 完成日期：2026-04-15
- 改动文件：
   - src/pep/writeback_engine.py
   - tests/test_writeback_engine.py
   - tests/test_pep_writeback_integration.py
- 说明：
   - `WritebackEngine.plan()` 现在会在默认 summary plan 之外，消费 `execution_result.report.artifact_payloads` 并生成受边界约束的 report-derived `WritebackPlan`。
   - `contract.allowed_artifacts` 被作为真实写回的硬边界；空白、绝对、越界与未授权路径全部跳过，并写入 `report_writeback_summary`。
   - `create` 语义收紧为“不覆盖已有文件”，避免 payload 驱动的真实写回静默覆盖现有内容。
   - `src/pep/executor.py` 本轮无需改动；现有 writeback 执行链已可直接消费新增 plan。
- 验证：
   - targeted tests：36 passed
   - full regression：922 passed, 2 skipped