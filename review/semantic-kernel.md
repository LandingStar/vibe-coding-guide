# Semantic Kernel Research

## 产品定位

Semantic Kernel 同时给我们两类参照：

- plugins 的导入与共享模型
- 多 agent orchestration patterns

## 关键机制

- Plugins 可以来自：
  - native code
  - OpenAPI specification
  - MCP Server
- Plugin function 区分：
  - retrieval functions
  - task automation functions
- 官方明确提到：task automation functions 往往需要 human-in-the-loop approval。
- Agent orchestration 提供统一接口，支持：
  - concurrent
  - sequential
  - handoff
  - group chat
  - magentic

## 对我们最有价值的点

- pack 的扩展来源不应局限于本地脚本，还应预留 OpenAPI / MCP 等来源。
- orchestration patterns 应是可切换的，不应绑死在单一运行模式上。
- task automation 与 retrieval 的治理要求不同。

## 与我们目标的差异

- Semantic Kernel 更偏 SDK 与 orchestration framework。
- 它没有把 docs / write-back / handoff 文档体系作为核心对象。

## 对子 agent 管理的启发

非常直接：

- handoff、group chat、concurrent、sequential 应当被视为不同协作模式
- 主平台要能支持模式切换，而不是只有一种 subagent shape
- task automation 相关子 agent 需要更强的人工批准边界

## 我们可吸收的设计点

- pack 能力来源多样化
- orchestration pattern 抽象
- retrieval vs automation 分类
- HITL approval 与 automation 的联动

## 当前不应直接照搬的点

- 不应把所有 orchestration pattern 都过早实现
- 平台当前仍应先定文档和规则模型，而不是先扩 SDK 表面

## 主要来源

- https://learn.microsoft.com/en-us/semantic-kernel/concepts/plugins/
- https://learn.microsoft.com/en-us/semantic-kernel/frameworks/agent/agent-orchestration/
- https://github.com/microsoft/semantic-kernel
