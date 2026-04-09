# Open Policy Agent Research

## 产品定位

OPA 不是 agent 框架，但它是“规则核心 / policy engine”方向最重要的参照之一。

## 关键机制

- OPA 是通用 policy engine。
- 它明确把 policy decision-making 与 policy enforcement 解耦。
- 软件把结构化输入送给 OPA，OPA 返回结构化决策结果。
- 决策不局限于 allow/deny，也可以输出任意结构化数据。
- Decision logs 会记录：
  - queried policy
  - input
  - result
  - bundle metadata
  - traceability fields
- decision logs 支持 masking sensitive data。

## 对我们最有价值的点

- 平台应区分：
  - 谁负责判定
  - 谁负责执行
- 规则系统不应该和变更执行逻辑混在一起。
- 高影响决策应有可审计日志。

## 与我们目标的差异

- OPA 不负责多 agent 编排。
- 它不负责 prompt、模板、文档系统。
- 它是 policy substrate，不是 workflow UX。

## 对子 agent 管理的启发

直接启发不在“如何管子 agent”，而在：

- 子 agent 委派、文档写回、phase-close 这些动作也应先经过 decision layer
- 子 agent 执行器不应自己兼任 policy authority

## 我们可吸收的设计点

- `Policy Decision Point` / `Policy Enforcement Point` 分层
- 结构化 rule input / decision output
- decision logs / trace IDs / masking
- policy bundle 的可分发思路

## 当前不应直接照搬的点

- 不应把平台过早变成纯 Rego 风格 policy engine
- 我们仍需要文档、prompt、pack 与 human review 这些 agent-native 结构

## 主要来源

- https://www.openpolicyagent.org/docs
- https://www.openpolicyagent.org/docs/management-decision-logs
- https://github.com/open-policy-agent/opa
