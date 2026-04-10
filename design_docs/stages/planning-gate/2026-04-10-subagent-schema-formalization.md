# Planning Gate — Subagent Schema 规格化

- Status: **CLOSED**
- Phase: 5
- Date: 2026-04-10

## 问题陈述

平台已在 `docs/subagent-schemas.md` 中定义了 3 个核心子 agent 对象（Contract、Report、Handoff）的字段和不变量，并在 `.codex/contracts/` 中提供了模板。但目前：

1. 缺少正式的 JSON Schema（`docs/specs/` 下无对应 `.schema.json`）。
2. 模板只是占位样板，无法用于机器校验。
3. 字段语义（类型、枚举值、必需性、条件约束）未精确定义。
4. 与 Phase 4 已完成的 PDP Decision Envelope 系列 schema 不对齐（格式、draft 版本、命名规范）。

## 目标

将 3 个子 agent 对象升级为 JSON Schema (draft-2020-12) 可验证格式，对齐 Phase 4 schema 标准。

## 切片计划

### Slice A — Subagent Contract + Report Schema

**范围：**
- 创建 `docs/specs/subagent-contract.schema.json`（10 字段，contract_id / task / mode / scope / allowed_artifacts / required_refs / acceptance / verification / out_of_scope / report_schema）
- 创建 `docs/specs/subagent-report.schema.json`（8 字段，report_id / contract_id / status / changed_artifacts / verification_results / unresolved_items / assumptions / escalation_recommendation）
- Contract 和 Report 通过 `contract_id` 强关联，一起处理可确保 ID 格式对齐
- 更新 `docs/subagent-schemas.md` 添加 schema 引用
- 注册到 `pack.json` on_demand
- 验证通过

**不做：**
- 不修改 Handoff 模板或文档（留给 Slice B）
- 不修改 PDP Decision Envelope 结构
- 不创建新的 narrative 文档（现有 `subagent-schemas.md` 已足够，只补充 schema 引用）

### Slice B — Handoff Schema

**范围：**
- 创建 `docs/specs/handoff.schema.json`（10 字段，handoff_id / from_role / to_role / reason / active_scope / authoritative_refs / carried_constraints / open_items / current_gate_state / intake_requirements）
- `current_gate_state` 应与 `review-state-machine.md` 对齐，使用枚举值
- 更新 `docs/subagent-schemas.md` 添加 Handoff schema 引用
- 注册到 `pack.json` on_demand
- 全量验证通过
- write-back：状态板、阶段文档、handoff

**不做：**
- 不修改 Contract / Report schema
- 不修改 Delegation Decision schema

## 验证门

- [ ] 3 个 JSON Schema 均为 valid draft-2020-12
- [ ] 现有 example JSON（`doc-loop-vibe-coding/examples/`）能通过对应 schema 校验
- [ ] `validate_doc_loop.py --target .` 通过
- [ ] `docs/subagent-schemas.md` 引用了全部 3 个 schema
- [ ] `pack.json` on_demand 包含全部 3 个 schema 路径

## 依赖

- `docs/subagent-schemas.md`（字段定义与不变量来源）
- `docs/subagent-management.md`（模式与角色来源）
- `docs/review-state-machine.md`（gate_state 枚举来源）
- `.codex/contracts/*.template.json`（现有模板，schema 应覆盖其结构）
- Phase 4 schema 命名规范（draft-2020-12, `$id`, `additionalProperties: false`）

## 风险

- `report_schema` 字段当前为自由字符串（"subagent-report-minimal"），需决定是否改为枚举或 URI 引用。建议：保持字符串但加 pattern 约束。
- 模板文件（`.codex/contracts/`）当前只是样板，不一定需要同步更新为带 `$schema` 引用的实例。建议：本阶段不改模板，只创建 schema。
