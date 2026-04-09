# OpenAI Agents SDK Research

## 为什么补充这一项

这一项是本轮新增补充，原因很明确：

此前相似产品中，真正把**subagent delegation / handoff / guardrails / tracing** 作为一组最小原语清楚写出来的方案还不够。

OpenAI Agents SDK 正好补上这一层。

## 产品定位

OpenAI Agents SDK 是一个多 agent workflow 框架，强调少量核心原语：

- agents
- handoffs
- guardrails

同时提供 tracing、sessions 和 HITL 支持。

## 关键机制

- 官方把 handoffs 直接定义成 agent 可委派给其他 agent 的机制。
- handoffs 在模型看来是 tool-like 的，但走独立 handoff pipeline。
- Agents SDK 的核心原语非常少，强调“少而够用”。
- SDK 内建 tracing，可观察 handoff、guardrail、tool call 等事件。
- Guardrails 分 input、output、tool 三类。
- 文档明确指出：tool guardrails 不适用于 handoff call 本身。
- tripwire 触发后可直接中断执行。

## 对我们最有价值的点

- 子 agent 委派应当是平台里的正式原语，而不是普通 tool 的变体说明。
- guardrails 不能想当然套用到 handoff，handoff 需要独立治理。
- tracing 应作为平台内置能力，而不是调试附属品。

## 与我们目标的差异

- 这是 SDK 层框架，不是平台级治理文档系统。
- 它没有项目级 pack 覆盖、docs taxonomy、write-back protocol 这些内容。

## 对子 agent 管理的启发

这是当前最直接的补充之一：

- handoff 需要独立 schema
- handoff 需要独立 guard / validator / review 处理
- tracing 必须覆盖 handoff 事件
- sessions / state 对多轮 subagent orchestration 是必要能力

## 我们可吸收的设计点

- handoff 作为一等原语
- agent / handoff / guardrail 三元基础
- tracing 先天内建
- tripwire / fail-fast 机制

## 当前不应直接照搬的点

- 不应把平台绑定到某一家模型或 SDK 语义
- 不应因为原语少，就忽略我们的文档治理层

## 主要来源

- https://openai.github.io/openai-agents-python/
- https://openai.github.io/openai-agents-python/handoffs/
- https://openai.github.io/openai-agents-python/guardrails/
- https://github.com/openai/openai-agents-python
