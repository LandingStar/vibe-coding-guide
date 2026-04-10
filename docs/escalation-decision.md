# Escalation Decision

## 文档定位

本文件定义平台级 `Escalation Decision` 的规格。

它固化以下内容：

- escalation decision result 的完整字段定义
- 平台层的升级触发条件
- 升级目标类型
- 与 delegation 和 gate 的联动

关联权威文档：

- [core-model.md](core-model.md) — Handoff And Escalation 定义
- [subagent-management.md](subagent-management.md) — Escalation 触发条件与目标
- [governance-flow.md](governance-flow.md) — PDP escalation decision 职责
- [pdp-decision-envelope.md](pdp-decision-envelope.md) — Decision Envelope 中的 `escalation_decision` 子结构
- [delegation-decision.md](delegation-decision.md) — delegation 与 escalation 的关系

## 设计原则

1. **升级是正式决策**：escalation 不是异常处理的副产品，而是 PDP 的正式决策输出。
2. **明确目标**：每次升级必须指明目标 authority。
3. **可审计**：升级原因和目标可被 tracing 系统追溯。

## 平台层升级触发条件

以下条件应触发 escalation（从 `subagent-management.md` 固化）：

| 条件 | 说明 |
|------|------|
| scope 不清晰 | 无法明确界定当前工作范围 |
| 需要改权威文档 | 变更超出当前 actor 的默认权限 |
| 跨多个 write scope 集成 | 需要主 agent 或更高 authority 协调 |
| 分类结果低置信度 | `intent_result.confidence` 为 `low` 或 `unknown` |
| 命中高影响 gate | `gate_decision.gate_level` 为 `approve` 或 `intent_result.high_impact` 为 `true` |

## 升级目标类型

| 目标 | 说明 |
|------|------|
| `main_agent` | 升级给主 agent（通常由子 agent 触发） |
| `human_reviewer` | 升级给人类审核者 |

实例可以声明额外的升级目标类型。

## Escalation Decision Result 字段

### 必选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `escalate` | boolean | 是否需要升级。为 `false` 时其他字段可省略。 |

### 条件必选字段（当 `escalate` 为 `true` 时）

| 字段 | 类型 | 说明 |
|------|------|------|
| `reason` | string | 升级原因。应对应上述触发条件之一或自定义原因。 |
| `target_authority` | string | 升级目标。推荐取值：`main_agent`、`human_reviewer`。 |

### 可选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `triggering_condition` | string | 触发升级的具体条件标识。 |
| `context_summary` | string | 传递给升级目标的上下文摘要。 |
| `suggested_action` | string | 建议升级目标采取的动作。 |

## 与其他决策的联动

- 当 `delegation_decision.delegate` 为 `true` 时，子 agent 可能在执行过程中触发 escalation
- escalation 可导致 gate level 提升（如从 `review` 提升到 `approve`）
- escalation 到 `human_reviewer` 时，通常对应 review state machine 进入 `waiting_review`

## 可机器校验的 Schema

- [specs/escalation-decision-result.schema.json](specs/escalation-decision-result.schema.json)
