# PDP Decision Envelope

## 文档定位

本文件定义平台 `Policy Decision Point` 输出的最小结构化格式——**Decision Envelope**。

Envelope 封装一次 PDP 评估的全部决策产出。它不定义下游如何执行，也不定义各子决策类型的完整内部 schema；下游执行由 `Policy Enforcement Point` 负责，各子决策类型的细化由后续规格文档展开。

关联权威文档：

- [core-model.md](core-model.md) — PDP/PEP 定义与 interaction intent 枚举
- [governance-flow.md](governance-flow.md) — 最小治理流与 gate 级别
- [review-state-machine.md](review-state-machine.md) — 状态、事件与迁移规则

## 设计原则

1. **决策与执行分离**：Envelope 只携带决策结果，不产生副作用。
2. **最小可用**：只包含当前平台已定义的核心决策维度，不预设未来子类型。
3. **可审计**：每个 Envelope 有唯一标识和时间戳，可被 tracing 和审批系统引用。
4. **可扩展**：子决策类型的内部结构当前使用开放对象，可在后续切片中替换为严格 schema。

## 字段定义

### 必选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `decision_id` | string | 当前决策的唯一标识符。推荐格式：UUID 或等价全局唯一字符串。 |
| `timestamp` | string (date-time) | 决策生成时间，ISO 8601 格式。 |
| `input_summary` | string | 触发本次决策的输入摘要。应足够简短但可追溯到原始输入。 |
| `intent_result` | object | interaction intent 分类结果。见下方 `intent_result` 结构。 |
| `gate_decision` | object | gate 决策结果，包含 gate level、review 状态入口和理由。见下方 `gate_decision` 结构。完整规格见 [gate-decision.md](gate-decision.md)。 |
| `rationale` | string | 人类可读的决策理由。应解释为什么选择了当前 gate level 和其他决策。 |

### 可选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `precedence_resolution` | object | 规则优先级解析结果。见下方 `precedence_resolution` 结构。当存在多条可能冲突的规则时应填写。 |
| `delegation_decision` | object | 是否委派给子 agent。见下方 `delegation_decision` 结构。不委派时可省略。 |
| `escalation_decision` | object | 是否需要升级给更高 authority。见下方 `escalation_decision` 结构。不升级时可省略。 |

## 子结构

### `intent_result`

完整规格见 [intent-classification.md](intent-classification.md)。

以下为概要：

| 字段 | 类型 | 必选 | 说明 |
|------|------|------|------|
| `intent` | string | 是 | 识别出的 interaction intent。取值见 [intent-classification.md](intent-classification.md) 的平台最小枚举。 |
| `confidence` | enum | 是 | 分类置信度。取值：`high`、`medium`、`low`、`unknown`。 |
| `explanation` | string | 否 | 对分类结果的简要解释。 |
| `high_impact` | boolean | 否 | 当前 intent 是否属于高影响类别。 |
| `alternatives` | array | 否 | 候选 intent 列表。详见 [intent-classification.md](intent-classification.md)。 |
| `corrected_by` | string | 否 | 纠正者标识（仅在人工纠正后出现）。 |
| `original_intent` | string | 否 | AI 原始分类（仅在人工纠正后出现）。 |

### `gate_decision`

完整规格见 [gate-decision.md](gate-decision.md)。

以下为概要：

| 字段 | 类型 | 必选 | 说明 |
|------|------|------|------|
| `gate_level` | enum | 是 | PDP 判定的 gate 级别。取值：`inform`、`review`、`approve`。 |
| `review_state_entry` | enum | 是 | 推荐进入的 review 状态。取值：`proposed`、`waiting_review`。 |
| `rationale` | string | 是 | gate 决策的理由。 |
| `triggering_rules` | array of string | 否 | 影响本次决策的规则标识。 |
| `override` | object | 否 | 覆盖记录。详见 [gate-decision.md](gate-decision.md)。 |
| `fast_path_eligible` | boolean | 否 | 是否满足 inform 快速路径条件。 |

### `precedence_resolution`

完整规格见 [precedence-resolution.md](precedence-resolution.md)。

以下为概要：

| 字段 | 类型 | 必选 | 说明 |
|------|------|------|------|
| `evaluated_rules` | array of string | 是 | 被评估的规则标识列表。 |
| `winning_rule` | string | 是 | 最终胜出的规则标识。 |
| `resolution_strategy` | string | 否 | 采用的优先级解析策略描述。 |
| `conflicts` | array of object | 否 | 检测到的冲突列表。详见 [precedence-resolution.md](precedence-resolution.md)。 |
| `adoption_layer` | enum | 否 | 获胜规则所属 adoption 层级。取值：`platform`、`instance`、`project-local`。 |

### `delegation_decision`

完整规格见 [delegation-decision.md](delegation-decision.md)。

以下为概要：

| 字段 | 类型 | 必选 | 说明 |
|------|------|------|------|
| `delegate` | boolean | 是 | 是否委派给子 agent。 |
| `mode` | string | 条件 | 推荐的协作模式。`delegate` 为 `true` 时必选。 |
| `scope_summary` | string | 条件 | 委派范围描述。`delegate` 为 `true` 时必选。 |
| `worker_only` | boolean | 条件 | 是否限定为 bounded worker。`delegate` 为 `true` 时必选。 |
| `requires_review` | boolean | 条件 | 子 agent 输出是否需要 review。`delegate` 为 `true` 时必选。 |
| `allow_handoff` | boolean | 否 | 是否允许 handoff。默认 `false`。 |
| `rationale` | string | 否 | 决策理由。 |
| `contract_hints` | object | 否 | Contract 生成提示。详见 [delegation-decision.md](delegation-decision.md)。 |
| `rejection_reason` | string | 否 | 拒绝委派原因（`delegate` 为 `false` 时）。 |
| `review_gate_level` | enum | 否 | 子 agent 输出的 review gate level。取值：`review`、`approve`。 |

### `escalation_decision`

完整规格见 [escalation-decision.md](escalation-decision.md)。

以下为概要：

| 字段 | 类型 | 必选 | 说明 |
|------|------|------|------|
| `escalate` | boolean | 是 | 是否需要升级。 |
| `reason` | string | 条件 | 升级原因。`escalate` 为 `true` 时必选。 |
| `target_authority` | string | 条件 | 升级目标（如 `main_agent`、`human_reviewer`）。`escalate` 为 `true` 时必选。 |
| `triggering_condition` | string | 否 | 触发升级的平台级条件标识。 |
| `context_summary` | string | 否 | 升级上下文摘要。 |
| `suggested_action` | string | 否 | 建议的后续动作。 |

## 与其他平台对象的关系

- **PEP** 接收 Decision Envelope，仅执行 envelope 中允许的动作。
- **Review State Machine** 由 `gate_decision` 子结构驱动入口，精确映射规则见 [gate-decision.md](gate-decision.md)：
  - `inform` → 允许快速路径进入 `applied`
  - `review` → 必须进入 `waiting_review`
  - `approve` → 必须显式经过 `approved` 才能 `apply`
- **Subagent Contract** 可由 `delegation_decision` 触发生成，但 contract 本身的 schema 不在本文件定义。
- **Tracing / Audit** 应以 `decision_id` 作为关联键。

## 可机器校验的 Schema

本 Envelope 的 JSON Schema 定义见：

- [specs/pdp-decision-envelope.schema.json](specs/pdp-decision-envelope.schema.json)

## 后续演进方向

- 所有 6 个子决策类型（`intent_result`、`gate_decision`、`delegation_decision`、`escalation_decision`、`precedence_resolution`）均已独立为严格 JSON Schema
- 可增加 `cancelled`、`superseded` 等扩展 review 状态的联动字段
- runtime 实现（parser、validator、serializer）待平台进入实现阶段后单独规划
