# Platform Positioning

## 文档定位

本文件定义当前仓库在升维后的目标下到底是什么。

它回答的是：

- 这个项目现在的本体是什么
- 为什么它不应再被理解成单一 skill
- `doc-driven vibe coding` 在这个项目里处于什么位置

## 当前定位

本项目当前应被理解为一个**协议/治理驱动工作流平台**。

平台本体不是某条具体 workflow，而是负责承载以下内容的核心驱动层：

- 规则
- 限制
- 标准
- 权限边界
- gate
- 文档对象
- 输入意图分类
- 决策与执行分层
- 插件加载与覆盖
- review / approval 流转
- 子 agent 协作与委派
- tracing / 审计

## 为什么要升维

仅仅把目标定义为“做一个 doc-driven vibe coding skill”会把太多东西过早写死，包括：

- 文档类型
- review 机制
- approval 机制
- handoff 形态
- 子 agent 边界
- write-back 规则

而真实需求已经明确显示：

- 输入意图需要由 AI 在规则约束下判断
- 人通常不直接改文档，而是通过审阅 AI 来治理文档
- 项目开发过程中会持续出现定制化规则
- 规则、模板、提示词、校验器和脚本都需要可扩展

因此项目本体应上升为平台，具体 workflow 作为实例或插件落在平台上。

## 平台与实例的关系

平台本体负责：

- 定义核心对象模型
- 定义权威优先级
- 定义输入意图分类机制
- 定义规则与 gate 的执行框架
- 定义插件如何提供扩展

具体实例负责：

- 提供领域内的文档类型
- 提供实例特有的规则与模板
- 提供实例特有的提示词、校验器与脚本
- 提供实例特有的 trigger、validator 与 scaffold
- 约束主 agent、子 agent 与 write-back 的实例行为

`doc-driven vibe coding` 现在应被视为这个平台上的**官方实例**，而不是平台本身。

## 当前设计吸收的外部经验

当前平台文档已明确吸收以下方向的经验，但不直接照搬其整体产品形态：

- OPA
  - 决策与执行分层
- Continue
  - repo 内规则与 checks 分层
- OpenHands
  - always-on context 与 on-demand pack content
- LangGraph / AutoGen / CrewAI / OpenAI Agents SDK / Semantic Kernel
  - 子 agent、handoff、review、orchestration pattern
- Guardrails AI
  - validator 作为独立扩展件
- Backstage
  - platform / plugin 边界与 docs-like-code
- Dify
  - trigger 与事件输入

这些吸收后的正式结论，应以 `docs/` 下的权威文档为准，而不是直接以外部产品原话为准。

## 非目标

本平台当前不试图：

- 直接替代项目管理工具
- 提供完整通用 rule engine 运行时
- 一次性穷尽所有 workflow 类型
- 先定义完美插件市场再开始实例化

当前阶段的重点是先把平台级文档与核心模型说清。

## 当前工作边界

当前仓库里已经存在的 `doc-loop-vibe-coding/` 资产，属于一版先行原型。

在平台文档定型之前：

- 它保留
- 它可被参考
- 但它不是最高权威来源

当前最高权威来源是根目录 `docs/` 下的平台文档。
