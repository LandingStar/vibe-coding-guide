# Plugin Model

## 文档定位

本文件定义平台如何承载扩展。

这里的“插件”不一定只是一份 skill，它更像一个可加载的 workflow pack，可以携带规则、模板、提示词、校验器、脚本与实例文档。

## 为什么需要插件模型

如果规则和流程都写死在平台本体里，项目很快会遇到两个问题：

- 官方实例会反过来绑死平台
- 项目级定制无法优雅叠加，只能不断打补丁

因此平台必须把“可扩展”作为核心能力，而不是后补特性。

## Pack 应包含什么

一个 pack 可以按需提供以下内容：

- 术语定义
- 实例文档类型
- interaction intent 扩展
- 规则与限制
- gate 映射
- 提示词
- 模板
- 校验器
- 脚本
- trigger
- checks
- 示例资产

不是每个 pack 都必须包含全部内容，但它至少应清楚说明自己覆盖了哪些扩展点。

## Pack Manifest

每个 pack 都应有一个清晰的 `Pack Manifest`，用于说明这个 pack 到底提供了什么。

详细规范见：

- `pack-manifest.md`

当前建议最小字段包括：

- `name`
- `version`
- `kind`
- `scope`
- `provides`
- `always_on`
- `on_demand`
- `depends_on`
- `overrides`
- `triggers`
- `validators`
- `scripts`

其中：

- `provides` 用于列出该 pack 提供了哪些能力槽位
- `always_on` / `on_demand` 用于声明上下文加载策略
- `overrides` 用于描述它打算覆盖谁
- `kind` 可用于区分平台默认 pack、官方实例 pack、项目定制 pack

当前文档先固定对象与目的，不固定最终文件格式。

## Pack 的职责边界

Pack 负责实例化平台，不负责重定义平台核心对象。

换句话说：

- pack 可以扩展 rule
- pack 可以扩展 document type
- pack 可以扩展 validator
- pack 可以扩展 prompt 和 script
- pack 可以扩展 trigger 与 checks
- pack 不应随意改写核心优先级语义和 actor 基本角色

若确实需要动到平台本体，应先回到平台文档层面，而不是在某个 pack 内偷偷重写。

## 覆盖与优先级

当前推荐覆盖顺序为：

1. 项目级本地 pack 或定制规则
2. 官方实例 pack
3. 平台核心默认规则

若多个 pack 同时命中，应遵循：

- 先看是否有显式覆盖关系
- 再看项目级定制是否声明优先
- 若仍冲突，则回退到人工 review，而不是让 AI 自行硬判

## Pack Origins

当前平台最低限度必须支持：

- 平台核心默认 pack
- 官方实例 pack
- 项目级本地 pack

同时应预留未来扩展来源，例如：

- 用户级 pack
- 组织级 pack
- 远端 registry pack

这样做是为了吸收已有技能平台对“来源分层”的经验，同时不在当前阶段把分发体系一次性做满。

## Pack Sources

pack 的能力来源不应被局限为本地 markdown 或脚本。

当前平台应预留以下来源：

- 本地文件
- native code
- OpenAPI specification
- MCP server
- 未来可能的远端 registry

这能避免 pack 抽象一开始就被某种单一载体绑死。

## Always-On And On-Demand

pack 内容应显式分成两类：

- `Always-On Context`
  - 会直接参与高层行为塑形
  - 例如平台核心规则、项目级总规则、当前实例的高层边界
- `On-Demand Pack Content`
  - 按需展开
  - 例如模板、参考说明、局部 script、局部 validator、局部文档

这样可以避免：

- 高层规则被遗漏
- 局部细节过早挤占上下文

## Pack And Quality Layers

pack 可以提供多种与质量控制相关的能力，但应区分：

- `tests`
  - 程序性验证
- `checks`
  - AI 审查任务
- `validators`
  - 对输入/输出/合同等对象的结构和约束检查

这三者不应在 pack 中混成同一个抽象。

## Pack And Triggers

pack 可以提供 trigger，用于声明：

- 这个实例是否接受聊天输入之外的事件输入
- 哪些事件可以触发 workflow
- 事件 payload 由谁定义和校验

当前建议至少预留：

- chat
- issue
- PR
- CI failure
- webhook
- schedule

## 与 Skill 的关系

Skill 可以被视为一种 pack 载体，但 pack 的范围应比 skill 更宽。

pack 除了可以像 skill 一样包含提示词和说明，还可以承载：

- 更强的规则集合
- 更稳定的模板体系
- 校验脚本
- 领域化文档模型
- 分发与版本化信息

因此，平台层建议使用 `pack` 作为抽象名词，而把 `skill` 视为可兼容的一种落地形式。

## 官方实例

当前第一个官方实例是：

- `doc-driven vibe coding`

它的目标不是定义平台，而是证明：

- 文档可以作为实例的主要控制面
- 人通过 AI 而不是直接维护文档也能形成稳定治理
- 子 agent 可以通过窄合同接入
- write-back 可以成为长期记忆机制

## 当前边界

本文件只定义插件模型的抽象边界。

它暂不定义：

- 最终 manifest 文件格式
- 插件安装协议
- 插件远程分发与市场协议
- 版本兼容与迁移策略

这些可以在后续平台实现阶段再单独展开。
