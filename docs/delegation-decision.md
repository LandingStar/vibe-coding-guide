# Delegation Decision

## 文档定位

本文件定义平台级 `Delegation Decision` 的规格。

它固化以下内容：

- delegation decision result 的完整字段定义
- `core-model.md` 中 Delegation Decision 5 个关键问题的可校验规则
- delegation decision 与 Subagent Contract 的关联
- delegation 拒绝/保护条件
- 实例/pack 可定制的边界

关联权威文档：

- [core-model.md](core-model.md) — Delegation Decision 定义与 Default Collaboration Mode
- [subagent-management.md](subagent-management.md) — 子 agent 管理完整模型
- [subagent-schemas.md](subagent-schemas.md) — Contract/Report/Handoff schema
- [governance-flow.md](governance-flow.md) — PDP delegation decision 职责
- [pdp-decision-envelope.md](pdp-decision-envelope.md) — Decision Envelope 中的 `delegation_decision` 子结构
- [gate-decision.md](gate-decision.md) — delegation 与 gate 的联动

## 设计原则

1. **委派是决策，不是技巧**：是否委派给子 agent 是 PDP 的正式决策输出，不应被视为执行层的优化手段。
2. **默认最严格**：未显式声明的权限默认不授予子 agent。
3. **合同驱动**：每次委派必须生成 Subagent Contract；delegation decision 是 contract 的前驱。
4. **可审计**：每次 delegation 决策可被 tracing 系统追溯。

## 5 个关键问题

`core-model.md` 要求一个 Delegation Decision 至少回答以下 5 个问题。本文件将其固化为结构化字段：

| # | 问题 | 对应字段 |
|---|------|---------|
| 1 | 当前是否允许委派？ | `delegate` |
| 2 | 推荐的协作模式是什么？ | `mode` |
| 3 | 子 agent 是否只能作为 worker？ | `worker_only` |
| 4 | 是否允许 handoff？ | `allow_handoff` |
| 5 | 是否需要先经过 review / approve？ | `requires_review` |

## Delegation Decision Result 字段

### 必选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `delegate` | boolean | 是否委派给子 agent。为 `false` 时，其他字段可省略。 |

### 条件必选字段（当 `delegate` 为 `true` 时）

| 字段 | 类型 | 说明 |
|------|------|------|
| `mode` | string | 推荐的协作模式。平台默认为 `supervisor-worker`。其他可选值：`handoff`、`team`、`swarm`、`subgraph`。 |
| `scope_summary` | string | 委派范围的简要描述。应与后续生成的 Subagent Contract 的 `scope` 字段一致。 |
| `worker_only` | boolean | 子 agent 是否限定为 bounded worker。为 `true` 时，子 agent 不得修改权威文档、全局状态板或 active handoff。 |
| `requires_review` | boolean | 子 agent 输出是否需要经过 review / approve。 |

### 可选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `allow_handoff` | boolean | 是否允许发生 handoff（控制权转移）。默认 `false`。 |
| `rationale` | string | delegation 决策的理由。 |
| `contract_hints` | object | 传递给 Subagent Contract 生成器的提示信息。见下方 `contract_hints` 结构。 |
| `rejection_reason` | string | 当 `delegate` 为 `false` 时，记录拒绝委派的原因。 |
| `review_gate_level` | enum | 子 agent 输出进入 review 时建议的 gate level。取值：`review`、`approve`。 |
| `capability_warnings` | array of string | advisory warning。表示当前 merged provides 不覆盖该 intent 常见所需能力，因此需要额外 review。 |

### `contract_hints` 子结构

| 字段 | 类型 | 必选 | 说明 |
|------|------|------|------|
| `suggested_task` | string | 否 | 推荐的 contract task 描述。 |
| `allowed_artifacts` | array of string | 否 | 推荐的 contract 允许改动的 artifact 列表。 |
| `required_refs` | array of string | 否 | 推荐的 contract 必须读取的参考文档列表。 |
| `out_of_scope` | array of string | 否 | 推荐的 contract 明确排除的范围。 |

## Delegation 拒绝/保护条件

以下条件应触发 `delegate: false` 或额外保护：

1. **scope 不清晰**：无法明确界定子 agent 的工作范围时，不应委派。
2. **需要修改权威文档**：子 agent 默认不得修改平台权威文档（`docs/`）。
3. **需要跨多个 write scope 集成**：集成工作应由主 agent 负责。
4. **高影响 intent**：当 `intent_result.high_impact` 为 `true` 时，委派需要额外保护（`requires_review` 应为 `true`）。
5. **低置信度分类**：当 `intent_result.confidence` 为 `low` 或 `unknown` 时，推荐不委派，或要求 approve 级 review。
6. **能力面不完整**：若 `RuleConfig.available_capabilities` 未覆盖该 intent 常见所需能力，可继续委派，但应附带 `capability_warnings`，并至少要求 `review` 级复核。

## 与 Subagent Contract 的关联

Delegation Decision 是 Subagent Contract 的前驱：

- `delegate: true` 时，PEP 应根据 delegation decision 生成 Subagent Contract
- `scope_summary` 应与 contract 的 `scope` 字段一致
- `contract_hints` 中的建议可直接填充 contract 模板
- `worker_only` 约束应传递到 contract 的 `allowed_artifacts` 和 `out_of_scope`

## 与 Gate Decision 的联动

- 当 `requires_review` 为 `true` 时，子 agent 输出应进入 review state machine
- `review_gate_level` 指定进入 review 时的 gate level
- 若 delegation decision 未指定 `review_gate_level`，默认使用当前请求的 gate_decision 中的 gate_level

### Capability Check

平台当前对部分 delegatable intent 做轻量 capability check：

- `constraint` 通常需要 `rules`
- `correction` 与 `request-for-writeback` 通常需要 `document_types`
- `issue-report` 当前不要求特定能力

这些需求默认由 runtime 内置映射给出，也可由 pack rules 中的 `capability_requirements` 覆盖。

该检查是 advisory，而不是 hard block：缺失能力时仍可委派，但结果必须带上 `capability_warnings`，并进入 `review` 或更高 gate。

## 实例/Pack 可定制的边界

实例和 project-local pack 可以定制：

- 哪些 intent 类型允许/禁止委派
- worker_only 的默认值
- allow_handoff 的默认值
- 额外的委派保护条件

不可定制的部分：

- 委派必须生成 Subagent Contract（平台固定）
- 子 agent 默认不得修改权威文档（平台固定，只能通过显式 contract 授权）
- delegation decision 必须是 PDP 的正式输出（平台固定）

## 可机器校验的 Schema

本 Delegation Decision Result 的 JSON Schema 定义见：

- [specs/delegation-decision-result.schema.json](specs/delegation-decision-result.schema.json)
