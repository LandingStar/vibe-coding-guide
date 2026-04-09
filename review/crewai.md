# CrewAI Research

## 产品定位

CrewAI 把 multi-agent collaboration 和 event-driven flow 编排结合得比较紧。它对我们最重要的是：

- manager / crew / flow 分层
- hierarchical process
- human feedback 节点

## 关键机制

- Crews 用于组织 agents 协作。
- Flows 是事件驱动、有状态、可持久化的工作流。
- hierarchical process 提供 manager 统筹任务分配与验证。
- manager 可以是 `manager_llm` 或自定义 `manager_agent`。
- manager agent 支持 `allow_delegation=True`。
- `@human_feedback` 允许在 flow 中等待人的反馈。
- human feedback 可以用 `emit` + LLM 把自由反馈归并为结构化 outcome。

## 对我们最有价值的点

- 子 agent 管理不是只有 delegation，还包括 manager 的 review 责任。
- human feedback 最好产出结构化 outcome，而不是只保留原始自然语言。
- flow state persistence 对长流程治理很重要。

## 与我们目标的差异

- CrewAI 更偏执行编排与自动化，不偏 policy / precedence / doc governance。
- 它没有像 OPA 那样把决策和执行彻底解耦。

## 对子 agent 管理的启发

这是另一条强参照：

- 默认采用 manager-worker，而不是 peer chat
- manager 负责 task assignment、validation、progression
- 人类反馈可以被压缩成 approve / reject / revise 结果

## 我们可吸收的设计点

- Review State Machine 的结果类型化
- manager 责任模型
- stateful flow
- delegation 和 review 并存，而不是只管分工不管验收

## 当前不应直接照搬的点

- 不应先把整个平台建成 execution-first 框架
- 不应把所有自然语言反馈都自动压扁成 outcome，必须保留人工纠偏入口

## 主要来源

- https://docs.crewai.com/en/concepts/flows
- https://docs.crewai.com/en/learn/hierarchical-process
- https://docs.crewai.com/en/learn/human-feedback-in-flows
- https://github.com/crewAIInc/crewAI
