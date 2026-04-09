# Subagent Management Design

## 文档定位

本文件专门记录基于研究结论整理出的**子 agent 管理设计方向**。

之所以单列，是因为这一层在第一轮设计里明显不足，不能继续作为官方实例的附属细节处理。

## 输入材料

当前主要依据：

- [LangGraph / LangChain Research](../review/langgraph-langchain.md)
- [AutoGen Research](../review/autogen.md)
- [CrewAI Research](../review/crewai.md)
- [Semantic Kernel Research](../review/semantic-kernel.md)
- [OpenAI Agents SDK Research](../review/openai-agents-sdk.md)
- [OpenHands Research](../review/openhands.md)

## 当前总判断

外部方案表明，“子 agent 管理”至少不是一个单一问题。它实际上包含以下子问题：

- 谁来决定是否委派
- 委派给谁
- 委派的粒度和合同怎么定义
- 子 agent 拥有什么上下文
- 子 agent 产生的结果如何验证
- 何时需要升级给主 agent 或人类
- 如何恢复、审计和回放委派链

## 1. 推荐默认模式

### 1.1 默认采用 supervisor-worker

借鉴来源：

- [LangGraph / LangChain Research](../review/langgraph-langchain.md)
- [CrewAI Research](../review/crewai.md)

当前建议：

- 主 agent 默认担任 supervisor
- 子 agent 默认担任 bounded worker

原因：

- 最符合 coding / doc governance 的控制需求
- 最容易把权威文档维护权留在主 agent
- 最容易做 scope 和 artifact ownership 限制

### 1.2 不以 group chat 作为默认模式

借鉴来源：

- [AutoGen Research](../review/autogen.md)
- [Semantic Kernel Research](../review/semantic-kernel.md)

group chat / team / swarm 仍有价值，但更适合：

- 头脑风暴
- 方案比较
- 探索性分析

不适合作为默认 coding governance 主路径。

## 2. 子 agent 的几种协作模式

### 2.1 Worker 模式

适用：

- 文件修改
- 定向调研
- 局部脚本
- 局部 validator

要求：

- 明确 write scope
- 明确输入材料
- 明确交付格式

### 2.2 Handoff 模式

借鉴来源：

- [AutoGen Research](../review/autogen.md)
- [OpenAI Agents SDK Research](../review/openai-agents-sdk.md)
- [Semantic Kernel Research](../review/semantic-kernel.md)

适用：

- 当前会话控制权真的需要移交
- 需要切换到另一专业化 agent 持续承接

要求：

- handoff 是显式原语
- handoff 不应只被视为普通 tool call
- handoff 需要独立 tracing、review 和 validator

### 2.3 Team / Swarm 模式

借鉴来源：

- [AutoGen Research](../review/autogen.md)

适用：

- 多方案竞争
- 并行角色辩论
- 需要 selector/manager 二次判断的复杂场景

限制：

- 不作为默认 coding 主路径
- 必须有主 agent 做最终收口

### 2.4 Subgraph 模式

借鉴来源：

- [LangGraph / LangChain Research](../review/langgraph-langchain.md)

适用：

- 长流程
- 独立状态空间
- 可恢复、可重入的子流程

要求：

- namespace
- persistence
- side effect 管理

## 3. 子 agent 合同模型

### 3.1 合同最小字段

当前建议每个子 agent 合同至少包含：

- `task`
- `scope`
- `allowed_artifacts`
- `required_refs`
- `acceptance`
- `verification`
- `out_of_scope`
- `report_schema`

### 3.2 报告格式

建议子 agent 输出不是自由总结，而是结构化报告：

- 改了什么
- 跑了什么验证
- 什么没解决
- 假设是什么
- 是否建议升级

### 3.3 Artifact ownership

当前建议默认禁止子 agent 直接维护：

- 平台权威文档
- 项目全局状态板
- 当前 active handoff

除非主 agent 的合同显式授权。

## 4. 上下文装载策略

### 4.1 主 agent 与子 agent 区分上下文装载

借鉴来源：

- [OpenHands Research](../review/openhands.md)

当前建议：

- 主 agent 装载 always-on context
- 子 agent 只装载：
  - 项目总规则中的必要片段
  - 当前合同相关 refs
  - 当前 write scope 相关 artifact

### 4.2 Progressive disclosure

避免把全量项目文档都灌给子 agent。

原因：

- 容易漂移
- 容易越界
- 会削弱合同边界

## 5. Review 与升级机制

### 5.1 子 agent 完成不等于系统完成

借鉴来源：

- [CrewAI Research](../review/crewai.md)
- [OpenAI Agents SDK Research](../review/openai-agents-sdk.md)

当前建议：

- 子 agent 只提交 candidate result
- 主 agent 负责 review、integration、write-back
- 高影响结果仍需 human review / approve

### 5.2 升级条件

若出现以下情况，应升级回主 agent 或人类：

- scope 不再清晰
- 需要改动权威文档
- 需要跨多个 write scope 集成
- 分类结果低置信度
- 触发高影响 gate

## 6. Tracing 与审计

借鉴来源：

- [Open Policy Agent Research](../review/open-policy-agent.md)
- [OpenAI Agents SDK Research](../review/openai-agents-sdk.md)

当前建议：

子 agent 管理应默认记录：

- 委派来源
- 合同摘要
- 关键决策
- 验证结果
- 升级链

也就是要能回答：

- 为什么委派
- 按什么合同委派
- 子 agent 做了什么
- 为什么允许或拒绝合并其结果

## 7. 当前建议写入平台核心的对象

我建议后续把以下对象写进平台核心模型：

- `Delegation Decision`
- `Subagent Contract`
- `Subagent Report`
- `Handoff`
- `Escalation`
- `Supervisor`
- `Worker`
- `Review State`

## 8. 当前不应先做的事

- 不应先做复杂 swarm runtime
- 不应先把所有协作模式都实现
- 不应让子 agent 直接接管权威文档
- 不应把 handoff 和普通 tool call 混为一谈

## 当前开放问题

- `Handoff` 与 `Worker Task` 是否需要两套不同 schema
- 是否要在平台核心里正式支持 `team`，还是只在部分 pack 中开放
- 子 agent tracing 是平台内建，还是 pack 可选
- 子 agent validator 应挂在输入侧、输出侧，还是都需要
