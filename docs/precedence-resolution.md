# Precedence Resolution

## 文档定位

本文件定义平台级 `Precedence Resolution` 的规格。

它固化以下内容：

- precedence resolution result 的完整字段定义
- 优先级解析的输入与输出语义
- 与三层 adoption 模型的关系

关联权威文档：

- [core-model.md](core-model.md) — Rule 定义与优先级概念
- [governance-flow.md](governance-flow.md) — PDP precedence resolution 职责
- [pdp-decision-envelope.md](pdp-decision-envelope.md) — Decision Envelope 中的 `precedence_resolution` 子结构
- [project-adoption.md](project-adoption.md) — 三层 adoption 模型

## 设计原则

1. **显式胜出**：当多条规则可能冲突时，PDP 必须选出一条胜出规则并记录理由。
2. **可审计**：所有被评估的规则和最终选择都可被追溯。
3. **与 adoption 层次对齐**：优先级解析应考虑平台文档 > 实例 pack > 项目本地 pack 的层次。

## 何时需要 Precedence Resolution

- 当多条规则可能同时适用于当前输入时
- 当实例 pack 规则与平台规则存在冲突时
- 当项目本地 pack 包含 override 规则时

当只有一条规则适用时，此字段可省略。

## Precedence Resolution Result 字段

### 必选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `evaluated_rules` | array of string | 被评估的规则标识列表。至少含一项。 |
| `winning_rule` | string | 最终胜出的规则标识。 |

### 可选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `resolution_strategy` | string | 采用的优先级解析策略描述（如 "project-local override"、"most-specific-match"、"explicit-priority"）。 |
| `conflicts` | array of object | 检测到的规则冲突列表。见下方 `conflict` 结构。 |
| `adoption_layer` | string | 胜出规则所在的 adoption 层。推荐取值：`platform`、`instance`、`project-local`。 |

### `conflict` 子结构

| 字段 | 类型 | 必选 | 说明 |
|------|------|------|------|
| `rule_a` | string | 是 | 冲突规则 A 的标识。 |
| `rule_b` | string | 是 | 冲突规则 B 的标识。 |
| `resolution` | string | 否 | 冲突解决方式描述。 |

## 默认优先级层次

当未指定其他策略时，平台默认的规则优先级（从高到低）：

1. 用户在当前对话中的明确决定
2. 项目本地 pack 的 override 规则
3. 实例 pack 规则
4. 平台文档定义的默认规则

此层次与 `Project Master Checklist` 中的优先级声明一致。

## 可机器校验的 Schema

- [specs/precedence-resolution-result.schema.json](specs/precedence-resolution-result.schema.json)
