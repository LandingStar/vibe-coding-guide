# Intent Classification

## 文档定位

本文件定义平台级 `Interaction Intent Classification` 的规格。

它固化以下内容：

- 平台最小 intent 枚举集合
- intent classification result 的完整字段定义
- intent classification 的最低要求
- 高影响 intent 的标识与保护规则
- 平台枚举与实例/pack 扩展的边界

关联权威文档：

- [core-model.md](core-model.md) — Interaction Intent 定义与约束
- [governance-flow.md](governance-flow.md) — Intent Classification 最低要求
- [pdp-decision-envelope.md](pdp-decision-envelope.md) — Decision Envelope 中的 `intent_result` 子结构

## 设计原则

1. **AI 分类、人可纠偏**：intent 分类由 AI 负责，但结果必须可见，且人类可以纠正。
2. **允许不确定**：必须允许 `unknown` 和 `ambiguous` 作为合法分类结果。
3. **高影响保护**：属于高影响类别的 intent 不得自动无保护生效。
4. **平台枚举可扩展**：平台定义最小固定集合，实例和 pack 可以声明额外 intent 类型。

## 平台最小 Intent 枚举

以下是平台层固定的最小 intent 集合，所有实例必须识别：

| Intent | 语义 | 影响级别 |
|--------|------|----------|
| `question` | 用户提出问题，不要求改变任何 artifact | 低 |
| `correction` | 用户指出错误并要求修正 | 中 |
| `constraint` | 用户增加一条约束 | 中 |
| `scope-change` | 用户要求改变当前工作范围 | 高 |
| `protocol-change` | 用户要求改变工作协议或流程本身 | 高 |
| `approval` | 用户批准当前提案 | 中 |
| `rejection` | 用户拒绝当前提案 | 中 |
| `request-for-writeback` | 用户要求将结果写回文档 | 中 |
| `issue-report` | 用户报告一个问题 | 中 |
| `unknown` | AI 无法判断 intent 类型 | — |
| `ambiguous` | AI 认为输入可能属于多种 intent | — |

### 影响级别说明

- **低**：通常可以 `inform` gate 处理
- **中**：通常需要 `review` gate 或更高
- **高**：必须在 PDP 层触发额外保护，不得自动无保护生效

影响级别是推荐默认值，实际 gate 决策由 PDP 结合规则、precedence 和 workspace 状态综合决定。

## 实例扩展机制

实例和 project-local pack 可以通过 `intents` 字段声明额外的 intent 类型，例如：

```json
{
  "intents": [
    "question",
    "correction",
    "deploy-request",
    "hotfix-request"
  ]
}
```

扩展规则：

- 实例声明的 intent 不得与平台最小集合中的含义冲突
- 实例可以为自定义 intent 指定影响级别
- 平台最小集合中的 intent 始终有效，即使实例未显式列出

## Intent Classification Result 字段

以下是 intent classification result 的完整字段定义：

### 必选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `intent` | string | 识别出的 interaction intent。必须是平台最小枚举或实例扩展声明中的值。 |
| `confidence` | enum | 分类置信度。取值：`high`、`medium`、`low`、`unknown`。 |

### 可选字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `explanation` | string | 对分类结果的简要解释。推荐在 `confidence` 非 `high` 时提供。 |
| `high_impact` | boolean | 当前 intent 是否属于高影响类别。由 PDP 根据平台影响级别表和实例规则综合判定。 |
| `alternatives` | array of object | 候选 intent 列表。当 `intent` 为 `ambiguous` 或 `confidence` 为 `low` 时推荐提供。每项包含 `intent`（string）和 `confidence`（enum）。 |
| `corrected_by` | string | 若人类纠正了 AI 的分类，此字段记录纠正者标识。 |
| `original_intent` | string | 若发生纠正，此字段记录 AI 的原始分类结果。 |

## Intent Classification 最低要求

以下约束从 `core-model.md` 和 `governance-flow.md` 固化为可校验规则：

1. **可见性**：intent classification result 必须作为 Decision Envelope 的一部分输出，不得隐藏。
2. **可纠偏**：系统必须支持人类通过 `corrected_by` 和 `original_intent` 字段记录纠正。
3. **允许不确定**：`unknown` 和 `ambiguous` 是合法的 `intent` 取值，不得被系统拒绝。
4. **高影响保护**：当 `high_impact` 为 `true` 时，PDP 不得输出 `inform` 作为 gate level，除非有显式的覆盖规则。
5. **confidence 降级触发**：当 `confidence` 为 `low` 或 `unknown` 时，推荐提供 `alternatives` 并触发人工确认。

## 与 PDP Decision Envelope 的关系

本文档定义的 `intent_result` 是 Decision Envelope 中同名子结构的严格版本。

- Envelope 中的 `intent_result` 使用 `$ref` 引用本文档对应的 JSON Schema
- 所有 Envelope 中的 intent 相关字段语义以本文档为准

## 可机器校验的 Schema

本 Intent Classification Result 的 JSON Schema 定义见：

- [specs/intent-classification-result.schema.json](specs/intent-classification-result.schema.json)
