# Product Research Index

## 文档定位

本目录收纳对相似产品与相关开源方案的细化研究。

这些文档的用途是：

- 固化原始研究结论，避免后续只留下口头印象
- 为平台与官方实例设计提供可回溯参照
- 让后续新增借鉴点时有稳定落脚处

## 研究方法

当前研究以**官方文档**为主，必要时补充：

- 官方 GitHub 仓库
- 官方产品主页

本目录不负责输出我们的最终设计结论；那些结论单独收纳在 `design_docs/`。

## 首先阅读

如果不是要逐篇细读，而是要先知道“某个问题该去看哪几份报告”，请先读：

- `research-compass.md`

它是本目录的牵头文档，负责：

- 总览当前研究
- 按主题检索
- 按平台层检索
- 按子 agent 相关性检索

## 当前研究清单

- `research-compass.md`
- `continue.md`
- `openhands.md`
- `langgraph-langchain.md`
- `autogen.md`
- `crewai.md`
- `open-policy-agent.md`
- `guardrails-ai.md`
- `backstage.md`
- `dify.md`
- `semantic-kernel.md`
- `openai-agents-sdk.md`

## 关于子 agent 管理

本轮研究特别补充了子 agent / 多 agent 管理相关方案。

原因是此前第一轮相似产品扫描中：

- 规则
- 插件
- 文档
- validator

这些层已经有较多参照，但：

- supervisor / worker
- handoff
- team
- subgraph namespace
- human escalation

这些与子 agent 管理直接相关的模式仍需额外补强。
