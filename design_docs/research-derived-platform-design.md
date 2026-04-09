# Research-Derived Platform Design

## 文档定位

本文件用于把 `review/` 中的研究结论收束成当前平台设计方向。

它回答的是：

- 我们准备吸收哪些外部模式
- 它们应该落在平台哪一层
- 哪些模式当前应刻意避免过早实现

本文件是设计推导层，不替代 `docs/` 中的平台权威定义。

## 输入材料

当前主要依据：

- [Continue Research](../review/continue.md)
- [OpenHands Research](../review/openhands.md)
- [LangGraph / LangChain Research](../review/langgraph-langchain.md)
- [AutoGen Research](../review/autogen.md)
- [CrewAI Research](../review/crewai.md)
- [Open Policy Agent Research](../review/open-policy-agent.md)
- [Guardrails AI Research](../review/guardrails-ai.md)
- [Backstage Research](../review/backstage.md)
- [Dify Research](../review/dify.md)
- [Semantic Kernel Research](../review/semantic-kernel.md)
- [OpenAI Agents SDK Research](../review/openai-agents-sdk.md)

## 当前总判断

外部方案没有任何一个可以被直接当成我们的平台本体，但它们已经足够支持我们把平台抽成下列层次：

1. 核心治理层
2. pack 扩展层
3. review / approval 流转层
4. validator / checks 层
5. 文档与模板层
6. 触发器与事件输入层
7. 实例层

## 1. 核心治理层

### 1.1 引入 PDP / PEP 分层

借鉴来源：

- [Open Policy Agent Research](../review/open-policy-agent.md)

建议引入：

- `Policy Decision Point`
  - 负责 intent classification、rule evaluation、gate decision
- `Policy Enforcement Point`
  - 负责文档改写、脚本执行、validator 调用、handoff 落地

设计理由：

- 决策和执行分离后，规则才可能可扩展、可替换、可审计
- 子 agent 执行器不再兼任 policy authority

### 1.2 明确 precedence

借鉴来源：

- [Continue Research](../review/continue.md)
- [OpenHands Research](../review/openhands.md)

当前建议固定：

1. 用户当前回合中的明确决定
2. 当前 workspace 的现实状态
3. 项目级 pack 或本地定制规则
4. 官方实例 pack
5. 平台核心默认规则
6. 历史产物

## 2. Pack 扩展层

### 2.1 把 plugin 正式收束成 pack

借鉴来源：

- [OpenHands Research](../review/openhands.md)
- [Continue Research](../review/continue.md)
- [Guardrails AI Research](../review/guardrails-ai.md)
- [Semantic Kernel Research](../review/semantic-kernel.md)

建议 pack 至少支持以下槽位：

- `rules`
- `intents`
- `gates`
- `document_types`
- `prompts`
- `validators`
- `scripts`
- `templates`
- `triggers`

### 2.2 区分 always-on 与 on-demand

借鉴来源：

- [OpenHands Research](../review/openhands.md)

建议 pack 内容二分：

- `always-on context`
  - 平台核心规则
  - 项目级总规则
  - 当前实例的高层边界
- `on-demand content`
  - 模板
  - 参考说明
  - 局部 validator
  - 局部脚本
  - 实例细节

## 3. Review / Approval 流转层

### 3.1 Human review 作为一等 gate

借鉴来源：

- [LangGraph / LangChain Research](../review/langgraph-langchain.md)
- [AutoGen Research](../review/autogen.md)
- [CrewAI Research](../review/crewai.md)
- [OpenAI Agents SDK Research](../review/openai-agents-sdk.md)

建议 review 不再只是规则说明，而应是正式状态机。

最小状态建议：

- `proposed`
- `waiting_review`
- `approved`
- `rejected`
- `revised`
- `applied`

### 3.2 决策级别

当前仍保留三类 gate：

- `inform`
- `review`
- `approve`

但现在应把它们视为：

- policy decision 的输出
- review state machine 的入口条件

而不是单纯文字标签。

## 4. Validator / Checks 层

### 4.1 明确 checks / validators / tests 分层

借鉴来源：

- [Continue Research](../review/continue.md)
- [Guardrails AI Research](../review/guardrails-ai.md)

建议区分：

- `tests`
  - 程序性、确定性的代码验证
- `checks`
  - 与上下文相关的 AI 审查任务
- `validators`
  - 输入/输出、合同、报告、handoff 等对象的结构和约束检查

### 4.2 validator 作为独立扩展件

建议 validator 可以：

- 由 pack 附带
- 被多个实例复用
- 应用于输入、输出、handoff、write-back、subagent report

## 5. 文档与模板层

### 5.1 docs-like-code 进入平台核心

借鉴来源：

- [Backstage Research](../review/backstage.md)
- [OpenHands Research](../review/openhands.md)

建议将：

- 文档
- 模板
- scaffold

都视为正式 artifact，而不是说明性附属物。

### 5.2 模板应保留 review step

借鉴来源：

- [Backstage Research](../review/backstage.md)

建议模板不只是“复制文件”，还要支持：

- 起草
- review
- 再应用

## 6. 触发器与事件输入层

### 6.1 不把输入限制为聊天

借鉴来源：

- [Continue Research](../review/continue.md)
- [Dify Research](../review/dify.md)

建议平台预留多类输入源：

- chat input
- issue
- PR
- CI failure
- webhook
- schedule

### 6.2 interaction intent 仍由 AI 判断

但现在要明确：

- 这是 PDP 的职责
- 分类结果必须可见
- 人可以纠偏
- 高影响类型不能自动无保护生效

## 7. 官方实例层

### 7.1 `doc-driven vibe coding` 的平台位置

借鉴来源：

- 全部研究共同支持

当前结论：

- `doc-driven vibe coding` 只是官方实例
- 它主要验证文档是否能承担控制面
- 它不应再反向定义平台本体

## 需要避免的方向

当前研究也明确告诉我们，下面这些事情现在不应先做：

- 不应先做重量级 runtime 再补协议
- 不应先做 marketplace 再定义 pack
- 不应把平台收缩成 PR/issue 自动化系统
- 不应把单个 skill 或模板包误认成平台本体
- 不应把 validator 系统误认成完整治理系统

## 当前建议写入后续权威文档的对象

我建议下一步把以下对象正式提升进 `docs/`：

- `Policy Decision Point`
- `Policy Enforcement Point`
- `Pack Manifest`
- `Review State Machine`
- `Always-On Context`
- `On-Demand Pack Content`
- `Trigger`

## 当前开放问题

- pack manifest 的最小字段是什么
- review state machine 是否需要 `superseded` / `cancelled`
- trigger 是否属于 pack 可选能力还是平台保留接口
- validator 和 checks 是否需要不同 registry
- 项目级 pack 的目录规范是否现在就要固定
