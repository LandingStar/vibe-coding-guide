# Planning Gate — Phase 4 Slice C: Gate Decision Schema

**Status: CLOSED** (executed 2026-04-09)

## 执行结果

- `docs/gate-decision.md` 已创建（gate level 语义、review state machine 映射规则、输入约束、override 机制、实例定制边界）
- `docs/specs/gate-decision-result.schema.json` 已创建（6 个属性，3 个必选）
- `docs/specs/pdp-decision-envelope.schema.json` 已重构：gate_level + review_state_entry 合并为 gate_decision ($ref)
- `docs/pdp-decision-envelope.md` 已更新字段定义和子结构说明
- `docs/README.md` 已更新
- `validate_doc_loop.py --target .` 通过
- 所有 write-back 已完成

## 文档定位

本文件是 Phase 4 Slice C 的窄 scope planning contract。

## 当前问题

PDP Decision Envelope 中的 `gate_level` 字段当前只是一个 `enum`（`inform / review / approve`），没有定义：

- 做出 gate 决策时需要哪些输入
- gate 决策的结构化输出除了 `gate_level` 本身还应包含什么
- gate level 与 review state machine 入口的精确映射规则
- 实例和 pack 如何定义自定义的 gate 规则

`governance-flow.md` 和 `review-state-machine.md` 已各自从不同角度描述了这些关系，但目前没有统一的可校验规格。

## 权威输入

- `docs/governance-flow.md`（gate 级别定义、PDP gate decision 职责）
- `docs/review-state-machine.md`（gate 与状态机的关系、迁移规则）
- `docs/core-model.md`（Gate 定义、Rule 定义）
- `docs/pdp-decision-envelope.md`（现有 gate_level 和 review_state_entry 字段）
- `docs/specs/pdp-decision-envelope.schema.json`（现有 schema）

## 本轮只做什么

1. 在 `docs/` 下新建 `gate-decision.md`
   - 定义 Gate Decision 的完整语义
   - 定义 gate decision result 的完整字段（扩展现有 `gate_level` + `review_state_entry`）
   - 固化 gate level 与 review state machine 入口的精确映射规则
   - 定义 gate decision 的输入约束（需要 intent_result、precedence、workspace context）
   - 明确实例/pack 可定制的 gate 规则边界

2. 在 `docs/specs/` 下新建 `gate-decision-result.schema.json`
   - 将 gate decision result 固化为独立 JSON Schema

3. 更新 `docs/specs/pdp-decision-envelope.schema.json`
   - 将 envelope 中 `gate_level` 和 `review_state_entry` 合并为 `gate_decision` 子结构，使用 `$ref` 引用新 schema

4. 更新 `docs/pdp-decision-envelope.md`
   - 反映 `gate_decision` 子结构替代原有的 `gate_level` + `review_state_entry` 字段

5. 更新 `docs/README.md`
   - 在文档地图中加入新文档

## 本轮明确不做什么

- 不细化 delegation_decision、escalation_decision、precedence_resolution 的严格 schema
- 不修改 `governance-flow.md`、`review-state-machine.md`、`core-model.md` 的正文
- 不实现 runtime 代码
- 不修改 `doc-loop-vibe-coding/` prototype 资产
- 不引入子 agent

## 验收与验证门

- 针对性检查：
  - `docs/gate-decision.md` 存在且包含完整字段定义和映射规则
  - `docs/specs/gate-decision-result.schema.json` 存在且是合法 JSON Schema
  - `docs/specs/pdp-decision-envelope.schema.json` 使用 `$ref` 引用新 schema
  - `docs/pdp-decision-envelope.md` 已更新
  - `docs/README.md` 已更新文档地图
- 更广回归：
  - `python doc-loop-vibe-coding/scripts/validate_doc_loop.py --target .` 仍通过
- 文档同步：
  - 本 planning-gate 回写为 closed
  - `Project Master Checklist.md` 状态同步
  - `Global Phase Map and Current Position.md` 阶段同步
  - `.codex/handoffs/CURRENT.md` 刷新

## 需要同步的文档

- `docs/README.md`
- `docs/pdp-decision-envelope.md`
- `docs/specs/pdp-decision-envelope.schema.json`
- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/handoffs/CURRENT.md`
- `.codex/packs/project-local.pack.json`
- 本 planning-gate 文档自身

## 子 agent 切分草案

- 本轮不引入子 agent。

## 收口判断

- **为什么这条切片可以单独成立**：Gate Decision 是 PDP 最核心的决策输出之一。它连接 intent classification 和 review state machine，是治理流转的关键枢纽。
- **做到哪里就应该停**：说明文档 + JSON Schema + envelope 引用更新 + 文档地图更新 + write-back 完成即停。
- **下一条候选主线**：`Phase 4 Slice D: Delegation Decision Schema`。
