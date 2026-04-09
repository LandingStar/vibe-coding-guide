# LangGraph / LangChain Research

## 产品定位

LangGraph 代表的是一种**状态图 + durable execution + interrupt + subgraph** 的 agent runtime 思路。配合 LangChain 的 subagents 文档，它在子 agent 管理上比第一轮扫描时看到的更强。

## 关键机制

- `interrupt()` 可以暂停 graph，等待外部输入后恢复。
- interrupt 依赖 checkpoint persistence，支持 human-in-the-loop approval / review。
- subgraph 是 graph 里的 node，可用于：
  - multi-agent systems
  - reusable graph fragments
  - distributed development with stable interfaces
- subgraph 有 namespace 与 persistence 语义，需要处理重复调用和状态隔离。
- LangChain 的 `subagents` 模式明确区分：
  - supervisor
  - router
- supervisor 是保持对话上下文并动态决定调用哪个 subagent 的完整 agent。

## 对我们最有价值的点

- 子 agent 不只是“被调用一次的工具”，还需要 namespace、state 和 resume 语义。
- human review 最好不是口头约定，而是 runtime 可暂停节点。
- supervisor / router 必须明确区分，不然分类器会被误当成管理者。
- side effects 在可中断流程中必须 idempotent，或被放到 interrupt 之后。

## 与我们目标的差异

- LangGraph 偏 runtime 编排，不偏规则治理。
- 文档、模板、pack registry 不是它的中心。
- 它要求较强的状态机思维，平台复杂度会上升。

## 对子 agent 管理的启发

这是当前最强参照之一：

- 用 supervisor-worker 作为默认子 agent 模式
- 用 subgraph/namespace 处理独立状态
- 用 interrupt / resume 处理 review / approve
- 把 side effects 和 state persistence 单独考虑

## 我们可吸收的设计点

- Review State Machine 需要支持暂停与恢复
- 子 agent 需要明确 namespace / scope / state ownership
- manager/supervisor 与 simple router 不能混用
- 长流程执行应有 durable state 概念

## 当前不应直接照搬的点

- 现在不应先实现重量级 runtime
- 平台文档阶段不应被 graph API 细节绑架

## 主要来源

- https://docs.langchain.com/oss/python/langgraph/interrupts
- https://docs.langchain.com/oss/python/langgraph/use-subgraphs
- https://docs.langchain.com/oss/python/langchain/multi-agent/subagents
- https://github.com/langchain-ai/langgraph
