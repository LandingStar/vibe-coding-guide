# Planning Gate — Phase 4 Slice D: Delegation Decision Schema

**Status: CLOSED** (executed 2026-04-09)

## 执行结果

- `docs/delegation-decision.md` 已创建（5 个关键问题固化、10 个字段、条件必选逻辑、拒绝/保护条件、Contract 关联）
- `docs/specs/delegation-decision-result.schema.json` 已创建（10 个属性，条件必选 via if/then）
- Envelope 中 `delegation_decision` 已替换为 `$ref`
- 所有文档和 write-back 已完成

## 文档定位

本文件是 Phase 4 Slice D 的窄 scope planning contract。

## 当前问题

PDP Decision Envelope 中的 `delegation_decision` 当前只有 4 个字段（`delegate`、`mode`、`scope_summary`、`requires_review`），没有覆盖 `core-model.md` 和 `subagent-management.md` 中定义的关键决策维度：

- 是否允许 handoff（控制权转移）
- 子 agent 角色约束（worker-only 或允许其他模式）
- 与 Subagent Contract 的关联（delegation decision 如何驱动 contract 生成）
- 升级条件（在什么情况下 delegation 应被拒绝或需要额外保护）

## 权威输入

- `docs/core-model.md`（Delegation Decision、Subagent Core Objects、Default Collaboration Mode）
- `docs/subagent-management.md`（子 agent 管理的完整模型）
- `docs/subagent-schemas.md`（Contract/Report/Handoff schema）
- `docs/governance-flow.md`（PDP delegation decision 职责）
- `docs/pdp-decision-envelope.md`（现有 delegation_decision 子结构）
- `docs/specs/pdp-decision-envelope.schema.json`（现有 schema）

## 本轮只做什么

1. 在 `docs/` 下新建 `delegation-decision.md`
   - 定义 delegation decision result 的完整字段
   - 固化 `core-model.md` 中 Delegation Decision 的 5 个关键问题为可校验规则
   - 定义 delegation decision 与 Subagent Contract 的关联
   - 定义 delegation 拒绝/保护条件
   - 明确实例/pack 可定制的边界

2. 在 `docs/specs/` 下新建 `delegation-decision-result.schema.json`
   - 将 delegation decision result 固化为独立 JSON Schema

3. 更新 `docs/specs/pdp-decision-envelope.schema.json`
   - 将 envelope 中 `delegation_decision` 替换为 `$ref` 引用新 schema

4. 更新 `docs/pdp-decision-envelope.md`
   - 反映 `delegation_decision` 子结构的扩展

5. 更新 `docs/README.md`

## 本轮明确不做什么

- 不细化 escalation_decision、precedence_resolution 的严格 schema
- 不修改现有权威文档正文
- 不实现 runtime 代码
- 不修改 `doc-loop-vibe-coding/` prototype 资产
- 不引入子 agent

## 验收与验证门

- `docs/delegation-decision.md` 存在且包含完整字段定义
- `docs/specs/delegation-decision-result.schema.json` 是合法 JSON Schema
- `docs/specs/pdp-decision-envelope.schema.json` 使用 `$ref` 引用新 schema
- `docs/pdp-decision-envelope.md` 已更新
- `docs/README.md` 已更新
- `python doc-loop-vibe-coding/scripts/validate_doc_loop.py --target .` 通过
- 状态文档同步

## 收口判断

- **为什么可以单独成立**：delegation decision 是 PDP 的核心输出之一，连接治理层和子 agent 管理。在 Envelope 中独立为严格 schema 后，后续 Subagent Contract 和 Report 的 schema 可以引用它。
- **做到哪里停**：说明文档 + JSON Schema + envelope 引用更新 + write-back 即停。
- **下一条候选**：`Phase 4 Slice E: Escalation Decision Schema`，或评估是否需要一个综合收口切片。
