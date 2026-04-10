# Gate Decision

## 文档定位

本文件定义平台级 `Gate Decision` 的规格。

它固化以下内容：

- gate level 的完整语义
- gate decision result 的完整字段定义
- gate level 与 review state machine 入口的精确映射规则
- gate decision 的输入约束
- 实例/pack 可定制的 gate 规则边界

关联权威文档：

- [core-model.md](core-model.md) — Gate 定义与 Rule 定义
- [governance-flow.md](governance-flow.md) — Gate Decision 职责与 gate 级别
- [review-state-machine.md](review-state-machine.md) — 状态机迁移规则与 gate 关系
- [pdp-decision-envelope.md](pdp-decision-envelope.md) — Decision Envelope 中的 gate_decision 子结构
- [intent-classification.md](intent-classification.md) — 影响级别与 gate 联动

## 设计原则

1. **Gate 是决策输出，不是标签**：gate level 不是静态标注，而是 PDP 根据输入综合判定的决策结果。
2. **与 Review State Machine 精确联动**：每个 gate level 对应 review state machine 的明确入口，不允许模糊对应。
3. **可被覆盖但可审计**：实例和 pack 可以定制 gate 规则，但覆盖必须显式声明且可追溯。
4. **高影响保护**：高影响 intent 不得被降级到 `inform`，除非有显式覆盖规则。

## Gate Level 语义

### `inform`

- AI 可先执行，再向人汇报。
- 对应 review state machine：允许快速路径 `proposed → applied`，跳过 `waiting_review`。
- 适用场景：低影响、低风险、可逆操作。

### `review`

- AI 先起草，由人审阅后再定稿。
- 对应 review state machine：必须进入 `waiting_review`，等待 reviewer 决定。
- 适用场景：中等影响操作、文档变更、策略调整。

### `approve`

- AI 不得自行落地，必须等待人的显式批准。
- 对应 review state machine：必须显式经过 `approved` 才能进入 `applied`。
- 适用场景：高影响操作、不可逆变更、安全敏感操作。

## Gate Level 与 Review State Machine 映射

| Gate Level | 允许的状态路径 | 必须经过的状态 | 快速路径 |
|------------|---------------|---------------|---------|
| `inform` | `proposed → applied` | 无 | 是 |
| `review` | `proposed → waiting_review → approved/rejected → applied` | `waiting_review` | 否 |
| `approve` | `proposed → waiting_review → approved → applied` | `waiting_review` + `approved` | 否 |

### 映射不变量

- `inform` 快速路径仅在 `high_impact` 为 `false` 或未设置时有效。
- `review` 必须进入 `waiting_review`，但 reviewer 可以一步 `approve`。
- `approve` 必须显式经过 `approved` 状态，不允许 reviewer 跳过该状态直接 `apply`。
- 不得绕过 review state machine 进行 `apply`（`inform` 快速路径除外）。

## Gate Decision Result 字段

### 必选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `gate_level` | enum | PDP 判定的 gate 级别。取值：`inform`、`review`、`approve`。 |
| `review_state_entry` | enum | 基于 gate level 推荐进入的 review 状态。取值：`proposed`（尚未提交）或 `waiting_review`（已提交审查）。当 gate_level 为 `inform` 时，可为 `proposed`（将走快速路径）。 |
| `rationale` | string | gate 决策的理由。应解释为什么选择了当前 gate level。 |

### 可选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `triggering_rules` | array of string | 影响本次 gate 决策的规则标识列表。 |
| `override` | object | 若本次决策覆盖了默认 gate level，记录覆盖信息。见下方 `override` 结构。 |
| `fast_path_eligible` | boolean | 是否满足 `inform` 快速路径的条件。当 gate_level 为 `inform` 时应为 `true`。 |

### `override` 子结构

| 字段 | 类型 | 必选 | 说明 |
|------|------|------|------|
| `original_gate_level` | enum | 是 | 被覆盖的默认 gate level。取值：`inform`、`review`、`approve`。 |
| `override_source` | string | 是 | 覆盖来源（如 pack 规则名、用户指令等）。 |
| `reason` | string | 否 | 覆盖理由。 |

## Gate Decision 的输入约束

PDP 做出 gate decision 时应考虑以下输入：

1. **intent_result**：interaction intent 分类及其影响级别。
2. **precedence_resolution**：规则优先级解析结果（若存在冲突规则）。
3. **active pack rules**：当前生效的 pack 中声明的 gate 规则。
4. **workspace context**：当前 workspace 的现实状态（如是否有未完成的 review、当前 phase 等）。

### 高影响保护规则

- 当 `intent_result.high_impact` 为 `true` 时，gate_level 不得为 `inform`，除非存在显式 `override`。
- 当 `intent_result.confidence` 为 `low` 或 `unknown` 时，推荐将 gate_level 提升到至少 `review`。

## 实例/Pack 可定制的边界

实例和 project-local pack 可以通过 `gates` 字段定制 gate 行为：

- 声明哪些 intent 类型默认使用哪个 gate level
- 声明额外的 gate 触发条件
- 声明 gate level 覆盖规则

不可定制的部分：

- gate level 与 review state machine 的映射关系（平台固定）
- 高影响保护规则（平台固定，只能通过显式 override 绕过）
- gate level 的三级枚举（`inform / review / approve`）

## 可机器校验的 Schema

本 Gate Decision Result 的 JSON Schema 定义见：

- [specs/gate-decision-result.schema.json](specs/gate-decision-result.schema.json)
