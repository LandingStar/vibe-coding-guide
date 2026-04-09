# AutoGen Research

## 产品定位

AutoGen 是一个面向 multi-agent collaboration 的编程框架。它在：

- teams
- handoffs
- lifecycle runtime
- human escalation

这些方面给了我们很多可直接借鉴的结构。

## 关键机制

- Teams 被定义为一组共同完成任务的 agents。
- 预置 team 模式包括：
  - `RoundRobinGroupChat`
  - `SelectorGroupChat`
  - `MagenticOneGroupChat`
  - `Swarm`
- handoff 模式里，AI agents 既有 regular tools，也有 delegate tools。
- delegate tool 被调用时，不是在当前 agent 内继续生成，而是把任务转给另一 agent。
- runtime 负责 agent lifecycle，开发者不需要手动实例化所有 agent。
- handoff 场景还内建了 human agent topic，可用于 escalation。

## 对我们最有价值的点

- 把“转交给别的 agent”建模成显式机制，而不是 prompt 幻觉。
- team preset 能帮助区分不同协作模式，不把所有多 agent 都看成同一种。
- runtime lifecycle 和 topic/subscription 让 handoff 更可审计。

## 与我们目标的差异

- AutoGen 更关注 agent collaboration runtime，不是规则/文档治理平台。
- 文档对象、项目级规则覆盖、pack 结构不是它的核心。

## 对子 agent 管理的启发

AutoGen 是当前最直接的补充之一：

- handoff 应是显式动作，不应只是“主 agent 决定换个口吻”
- human escalation 应在系统里有独立位置
- 不同 team 形态应服务不同问题，而不是只保留一种默认编排

## 我们可吸收的设计点

- `handoff` 作为平台一等动作
- `team` / `swarm` / `selector` 等模式分类
- lifecycle 和 event/topic 概念
- human escalation 作为正式节点而非异常分支

## 当前不应直接照搬的点

- 不应先引入过多 runtime 抽象再定义平台协议
- 对 coding governance 而言，group chat 不应成为默认模式

## 主要来源

- https://microsoft.github.io/autogen/stable/user-guide/agentchat-user-guide/tutorial/teams.html
- https://microsoft.github.io/autogen/dev/user-guide/core-user-guide/design-patterns/handoffs.html
- https://github.com/microsoft/autogen
