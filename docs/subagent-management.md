# Subagent Management

## 文档定位

本文件定义平台中的子 agent 管理模型。

它的目标不是穷举所有多 agent runtime，而是先固定平台默认立场：

- 默认如何委派
- 默认如何限制子 agent
- 默认如何 review 子 agent 结果

## 默认模式

平台当前默认协作模式为：

- `supervisor-worker`

这里的默认角色关系是：

- 主 agent = `Supervisor`
- 子 agent = `Bounded Worker`

原因：

- 最适合 coding governance
- 最适合文档控制面
- 最容易约束 artifact ownership
- 最容易做 write-back 收口

## 非默认模式

平台承认其他协作模式存在价值，但它们不是默认主路径：

- `handoff`
- `team`
- `swarm`
- `subgraph`

这些模式可用于：

- 长流程
- 多方案竞争
- 专业化承接
- 状态隔离

但应作为扩展模式而不是基础模式。

## Core Objects

平台中的子 agent 管理至少涉及：

- `Delegation Decision`
- `Supervisor`
- `Worker`
- `Subagent Contract`
- `Subagent Report`
- `Handoff`
- `Escalation`

对应最小 schema 见：

- `subagent-schemas.md`

## Delegation Decision

是否委派、委派给谁、以什么模式委派，应由 `Policy Decision Point` 正式决定。

最低决策内容包括：

- 当前是否允许委派
- 允许哪种协作模式
- 是否需要人工 review / approve
- 是否允许 handoff
- 是否必须保留主 agent 集成权

## Subagent Contract

每次委派至少应有一份 `Subagent Contract`。

最小字段建议：

- `task`
- `scope`
- `allowed_artifacts`
- `required_refs`
- `acceptance`
- `verification`
- `out_of_scope`
- `report_schema`

## Artifact Ownership

默认情况下，子 agent 不应直接维护：

- 平台权威文档
- 项目全局状态板
- active handoff

除非合同显式授权。

## Context Loading

主 agent 与子 agent 的上下文装载应区分：

- 主 agent 装载 `Always-On Context`
- 子 agent 只装载必要规则片段、合同 refs 与当前 scope 相关 artifact

平台当前明确反对把全量项目文档直接灌给子 agent。

## Subagent Report

子 agent 返回内容应优先结构化，而不是自由总结。

最低报告内容包括：

- 实际改动了什么
- 跑了哪些验证
- 哪些问题未解决
- 做了哪些假设
- 是否建议升级

## Handoff

`Handoff` 是一等原语，不应被视为普通 tool call 的变体。

当发生 handoff 时，平台需要独立处理：

- 控制权转移
- 上下文承接
- tracing
- review / approve
- validator / guard

## Escalation

`Escalation` 用于把问题提升给更高 authority。

常见触发条件：

- scope 不清晰
- 需要改权威文档
- 需要跨多个 write scope 集成
- 分类结果低置信度
- 命中高影响 gate

升级目标通常是：

- 主 agent
- human reviewer

## Review Of Subagent Output

子 agent 的完成不等于系统完成。

默认流程应为：

1. 子 agent 产出 candidate result
2. 主 agent review 结果
3. 主 agent 决定 integration / rejection / revision
4. 必要时进入 human review / approve
5. 由主 agent 完成最终 write-back

## Tracing And Audit

每次子 agent 参与都应至少可追溯：

- 为什么委派
- 按什么合同委派
- 子 agent 做了什么
- 跑了哪些验证
- 为什么合并或拒绝结果
- 是否发生 handoff / escalation

## 当前边界

本文件定义平台默认的子 agent 管理立场。

它不定义：

- 某个实例内部的具体合同模板
- 某个 runtime 的具体 API
- team / swarm / subgraph 的最终执行协议
