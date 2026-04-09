# Dify Research

## 产品定位

Dify 更偏 agentic workflow application platform。对我们最相关的是：

- trigger plugin
- event-driven workflow
- subscription / webhook 模型

## 关键机制

- workflow 应用可以通过 plugin trigger 被外部事件自动触发。
- 触发插件可以订阅 GitHub 的 `Pull Request`、`Push`、`Issue` 等事件。
- 一个 workflow 可以包含多个并行 plugin triggers。
- trigger 输出变量由 trigger plugin 定义，不允许随意修改。
- subscription 基于 webhook，可自动创建或手动创建。
- 没有合适 trigger plugin 时，可以请求社区、自己开发，或退回 webhook trigger。

## 对我们最有价值的点

- 平台后续应支持“事件输入”，不只是聊天输入。
- trigger 是 pack 的重要扩展点之一。
- 外部事件订阅与 workflow 解耦是合理的。

## 与我们目标的差异

- Dify 更偏应用编排与低代码工作流。
- 平台级 policy precedence、doc governance、subagent contract 不是它的中心。

## 对子 agent 管理的启发

直接启发不强，但给出一个重要外部输入视角：

- 子 agent 任务不一定来自主对话，也可能来自 PR、issue、CI failure、schedule 等事件

## 我们可吸收的设计点

- trigger plugin 作为 pack 槽位
- webhook/subscription 设计
- 多 trigger 并行输入
- event source 和 workflow logic 解耦

## 当前不应直接照搬的点

- 不应把平台重心转成 low-code canvas
- 不应让 trigger 成为唯一入口，聊天输入仍然需要保留

## 主要来源

- https://docs.dify.ai/en/use-dify/nodes/trigger/plugin-trigger
- https://github.com/langgenius/dify
