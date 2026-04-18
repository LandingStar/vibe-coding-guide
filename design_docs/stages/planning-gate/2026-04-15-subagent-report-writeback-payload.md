# Planning Gate — Subagent Report Writeback Payload

## 元信息

| 字段 | 值 |
|------|-----|
| Gate ID | 2026-04-15-subagent-report-writeback-payload |
| Scope | 为 Subagent Report 引入可选 artifact_payloads contract，固定 report 与后续 writeback 的边界 |
| Status | DONE |
| 来源 | design_docs/subagent-research-synthesis.md P3 前置约束 |
| 前置 | 2026-04-15-handoff-validator-independent-guard 已完成 |
| 测试基线 | 912 passed, 2 skipped |

## 文档定位

本文件用于把 P3 的前置问题收敛成一个可审核的窄 scope planning contract：先扩展 `Subagent Report` 的 payload 能力，再进入真正的 `Report -> Writeback Plans` 自动映射。

## 当前问题

当前 `Subagent Report` 只有：

- `changed_artifacts: list[str]`

它足以表达“改了哪些 artifact”，但不足以安全表达：

- 每个 artifact 要写入什么内容
- 应该是 `create` / `update` / `append`
- 内容属于哪种类型

因此：

1. 直接按现有 report 去改真实文件不安全。
2. 即使进入 P3，也只能做保守 manifest，无法形成真正的 artifact-level writeback。
3. 如果不先补 payload，后续任何“真实文件自动写回”都只能靠外部约定，而不是机器可校验 contract。

## 权威输入

- `docs/subagent-schemas.md`
- `docs/specs/subagent-report.schema.json`
- `design_docs/subagent-research-synthesis.md`
- `design_docs/subagent-tracing-writeback-direction-analysis.md`
- `src/pep/writeback_engine.py`
- `src/subagent/report_validator.py`
- `src/workers/llm_worker.py`
- `src/workers/http_worker.py`

## 候选阶段名称

- `P3-prep: Richer Subagent Report Payload for Writeback`

## 推荐方案

推荐在 `Subagent Report` 中新增一个**可选**字段：

- `artifact_payloads`

建议第一版结构：

- `path`
- `content`
- `operation`
- `content_type`

其中：

- `operation` 第一版只允许：`create` / `update` / `append`
- `content_type` 与现有 `WritebackPlan` 对齐：`markdown` / `json` / `yaml` / `text`

理由：

1. 比 `changed_artifacts` 更丰富，但仍然保持 report 语义，不直接暴露全部 writeback directive 复杂度。
2. 能支撑后续 P3 把 payload 映射到真实 `WritebackPlan`。
3. 不必在这一轮就把 `section_replace` / `line_insert` 之类 directive 级操作引入 report schema。

## 本轮只做什么

1. 扩展 `docs/specs/subagent-report.schema.json`
   - 新增可选 `artifact_payloads`
   - item 至少包含：
     - `path: string`
     - `content: string`
     - `operation: enum(create, update, append)`
     - `content_type: enum(markdown, json, yaml, text)`

2. 更新 `docs/subagent-schemas.md`
   - 说明 `changed_artifacts` 与 `artifact_payloads` 的边界：
     - 前者是“实际改动了哪些 artifact”的证据列表
     - 后者是“供后续 writeback 消费的结构化内容载荷”

3. 让 schema validator 接受该字段
   - `src/subagent/report_validator.py` 应能通过新的合法 report

4. 最小 worker/runtime 对齐
   - 不要求 LLM/Stub 立刻生成该字段
   - HTTP worker 若收到远端返回的 `artifact_payloads`，应原样保留
   - 现有默认行为保持兼容

5. 补测试
   - schema 接受带 `artifact_payloads` 的 report
   - 缺字段/非法 operation/非法 content_type 的 payload 被拒绝
   - 现有无 payload report 继续通过

## 本轮明确不做什么

- 不在本轮消费 `artifact_payloads` 生成 `WritebackPlan`
- 不改 `WritebackEngine.plan()`
- 不直接改用户真实文件
- 不引入 directive 级 payload（`section_replace` / `line_insert` / `line_replace`）
- 不修改 handoff / escalation / review state 语义

## 关键实现落点

- `docs/specs/subagent-report.schema.json`
- `docs/subagent-schemas.md`
- `src/subagent/report_validator.py`
- `tests/` 下的 report / worker / schema 相关测试

## 验收与验证门

- [x] `artifact_payloads` 进入 report schema 且通过 draft-2020-12 校验
- [x] `report_validator` 接受合法 payload report
- [x] 非法 payload report 被拒绝
- [x] HTTP worker 透传远端 `artifact_payloads`
- [x] targeted tests 新增 >= 6（实际 7 个）
- [x] 全量回归继续通过（912 passed, 2 skipped）

## 需要同步的文档

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- 本 planning-gate 文档自身

## 子 agent 切分草案

- 本轮不引入子 agent。
- 理由：这里是在固定平台 contract，不是局部实现切片。

## 收口判断

- **为什么这条切片可以单独成立**：它只补 report 的能力边界，不进入 writeback 消费路径。
- **做到哪里就应该停**：schema + docs + validator + tests 对齐即停。
- **下一条候选主线**：在该 payload 落地后，再进入真正的 P3，把 `artifact_payloads` 映射为 `WritebackPlan`。

## 执行结果

- 状态：DONE
- 完成日期：2026-04-15
- 改动文件：
   - docs/specs/subagent-report.schema.json
   - docs/subagent-schemas.md
   - tests/test_subagent_modules.py
   - tests/test_workers.py
- 说明：
   - `src/subagent/report_validator.py` 无需代码改动；其 schema-driven validation 路径已自动兼容新的可选字段，并由新增测试锁定。
- 验证：
   - targeted tests：7 passed
   - full regression：912 passed, 2 skipped
