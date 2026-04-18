# Planning Gate Candidate

## 文档定位

本文件用于把 P3 `Report -> Writeback Plans 自动映射` 收敛成一个安全、可审核的窄 scope planning contract。

## 当前问题

当前 `WritebackEngine.plan()` 只从 envelope / execution result 推导默认 writeback summary，不检视 `execution_result.report.changed_artifacts`。

这造成两个直接问题：

1. 子 agent 报告里声明的实际改动 artifact 不会自动进入 writeback 规划。
2. reviewer / admin 在 `.codex/writebacks/` 侧看不到结构化的 report-derived artifact 列表。

但当前 report schema 只有：

- `changed_artifacts: list[str]`

并**没有**任何内容载荷、patch、diff 或新内容字段。因此：

- 直接依据 report 去改用户真实文件 **不安全**
- 把 P3 直接做成“按 report 自动 update 源文件”会超出当前 schema 能承载的信息量

此外，当前 3 个 worker 实现默认都返回空的 `changed_artifacts`，说明第一版 P3 更适合先把“writeback 管道可消费 report artifact 列表”打通，而不是直接承诺真实文件写回。

## 权威输入

- `design_docs/subagent-research-synthesis.md`
- `design_docs/subagent-tracing-writeback-direction-analysis.md`
- `docs/subagent-schemas.md`
- `docs/specs/subagent-report.schema.json`
- `src/pep/writeback_engine.py`
- `src/pep/executor.py`
- `tests/test_pep_writeback_integration.py`

## 候选阶段名称

- `P3a: Report -> Writeback Mapping（Conservative）`

## 本轮只做什么

1. **归一化 report.changed_artifacts**
   - 仅接受字符串路径
   - 统一为 project-root 相对路径
   - 去重
   - 记录并跳过：绝对路径越界、空字符串、glob/模糊模式

2. **让 report artifact 进入 writeback 规划**
   - 在 `review_state=applied` 且存在 `report.changed_artifacts` 时
   - 除默认 summary plan 外，额外生成一个 report-derived manifest writeback plan

3. **新增受控 manifest 输出**
   - 输出路径：`.codex/writebacks/reported-artifacts/{envelope_id}.json`
   - 内容至少包含：
     - `envelope_id`
     - `contract_id`
     - `report_id`
     - `status`
     - `normalized_changed_artifacts`
     - `skipped_changed_artifacts`
   - 目的：把 report 声明的 artifact 变更正式纳入 writeback 可追踪面

4. **扩展默认 summary writeback 内容**
   - 在 `.codex/writebacks/{envelope_id}.md` 中追加：
     - report changed_artifacts 数量
     - manifest 文件路径
     - skipped 条目摘要

5. **补测试**
   - report 无 changed_artifacts 时不生成 manifest plan
   - report 有合法 artifact 时生成 manifest plan
   - 非法 / 越界 / glob artifact 被跳过并记录
   - dry-run / non-dry-run 行为一致

## 本轮明确不做什么

- 不直接按 report 改用户源文件
- 不扩展 `subagent-report.schema.json` 新增 diff/content 字段
- 不引入 `touch` / `noop` 之外的新 writeback operation
- 不改 handoff / tracing / audit 的下一层问题
- 不要求现有 worker 立刻填充非空 `changed_artifacts`

## 关键实现落点

- `src/pep/writeback_engine.py`
  - 归一化 + manifest plan 生成
- `src/pep/executor.py`
  - 若需要，透传 report-derived planning metadata
- `tests/test_pep_writeback_integration.py`
  - 扩展 writeback integration 测试
- 可能新增：
  - `tests/test_writeback_engine.py`

## 验收与验证门

- `report.changed_artifacts` 合法时生成额外 manifest writeback plan
- summary writeback 中能看到 report artifact 摘要
- 越界 / glob / 空值 artifact 不进入 plan，但会被记录
- dry-run 下只返回 plan，不创建文件
- non-dry-run 下会写入 manifest 文件
- targeted tests 新增 >= 6
- 全量回归继续通过

## 需要同步的文档

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- 本 planning-gate 文档自身

## 子 agent 切分草案

- 本轮不引入子 agent。
- 理由：P3a 需要同时约束 report schema 边界与 writeback 安全边界，主 agent 直接收口更稳妥。

## 收口判断

- **为什么这条切片可以单独成立**：它只解决“report artifact 列表如何进入 writeback 管道”的最小闭环，不碰真实文件内容写回。
- **做到哪里就应该停**：manifest plan + summary 扩展 + tests 通过即停。
- **下一条候选主线**：若未来要支持真实文件自动写回，应先扩展 report payload（例如 diff / content / patch），那会是单独切片。
