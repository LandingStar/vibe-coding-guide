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
3. **与 adoption 层次和作用域链对齐**：优先级解析既要考虑平台文档 > 实例 pack > 项目本地 pack 的来源层次，也要考虑显式 `scope_path` 下的 pack 链顺序。

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
| `resolution_strategy` | string | 采用的优先级解析策略描述（如 "project-local override"、"most-specific-match"、"explicit-priority"、"explicit-override adoption-layer-priority"）。 |
| `conflicts` | array of object | 检测到的规则冲突列表。见下方 `conflict` 结构。 |
| `adoption_layer` | string | 胜出规则所在的 adoption 层。推荐取值：`platform`、`instance`、`project-local`。 |
| `explicit_override` | boolean | 当胜出 pack 的 `overrides` 列表包含被覆盖的 pack 名称时为 `true`。缺失表示未检测到显式覆盖声明。 |

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

## Scoped Pack Chain

当调用方显式提供 `scope_path` 时，平台不再把所有已加载 pack 视为同等参与者，而是先做一次作用域路由：

1. 根据 pack tree 找到与 `scope_path` 最匹配的 pack 节点
2. 取该节点从 root 到 leaf 的完整 pack 链
3. 仅用这条链参与后续规则合并

当前语义约束为：

- pack tree 是单继承树，而不是 DAG
- 所有 kind 都可以参与树
- 链中的 precedence 由顺序决定：越靠后的 pack 越具体，优先级越高
- 若未提供 `scope_path`，或没有任何 pack 命中该路径，则回退到全局合并

因此，在 scoped 模式下，precedence 的关键不再只是“来自哪一层”，而是“位于哪条已解析链上的哪个位置”。

### 配置错误 vs 运行时冲突

同一个 parent 下若多个子 pack 的 `scope_paths` 互相重叠，这不是 runtime 需要通过 review 或 precedence result 解决的业务冲突，而是 pack 配置错误，应在加载阶段直接拒绝。

### 推荐 `resolution_strategy`

在 scoped 模式下，`resolution_strategy` 推荐使用类似：

- `scope-chain`
- `scope-chain most-specific-match`
- `project-local scope-chain override`

以显式体现“先做 scope 路由，再做 precedence 选择”的两段式语义。

## 可机器校验的 Schema

- [specs/precedence-resolution-result.schema.json](specs/precedence-resolution-result.schema.json)
