# Pack Manifest

## 文档定位

本文件定义平台中 `Pack Manifest` 的最小规范。

它的作用是让一个 pack 能够声明：

- 自己是谁
- 属于哪一层
- 提供哪些能力
- 哪些内容是 always-on
- 哪些内容是 on-demand
- 它依赖谁、覆盖谁

本文件当前只定义对象、字段和不变量，不绑定最终文件格式。

## 解决什么问题

如果没有统一的 manifest：

- pack 提供了什么很难快速判断
- precedence 与 override 关系容易只停留在口头说明
- 平台无法稳定知道该装载哪些上下文与扩展件

因此，manifest 是 pack 的**能力声明面**，不是运行时状态记录。

## 不解决什么问题

本文件当前不解决：

- 远端分发协议
- 安装与发布流程
- 签名、校验和安全模型
- 最终使用 YAML、JSON 还是其他格式

## 核心定位

`Pack Manifest` 应被理解为：

- pack 的身份证
- pack 的能力目录
- pack 的装载与覆盖声明

它不应被理解为：

- pack 内部规则正文
- 运行时状态快照
- 市场元数据中心

## 最小字段

### 身份字段

- `name`
  - pack 的稳定名称
- `version`
  - pack 的版本标识
- `kind`
  - pack 类型
  - 当前建议至少支持：
    - `platform-default`
    - `official-instance`
    - `project-local`
- `scope`
  - 适用范围说明

### 能力声明字段

- `provides`
  - 声明该 pack 提供了哪些能力槽位
- `document_types`
  - 该 pack 引入或定义的文档类型
- `intents`
  - 该 pack 扩展或细化的 interaction intent
- `gates`
  - 该 pack 额外使用或约束的 gate 语义

### 上下文装载字段

- `always_on`
  - 默认常驻上下文
- `on_demand`
  - 按需加载内容

### 依赖与覆盖字段

- `depends_on`
  - 依赖哪些 pack 或能力
- `overrides`
  - 显式声明覆盖哪些 pack 或规则来源

### 扩展件字段

- `prompts`
  - 该 pack 暴露的提示词面
- `templates`
  - 模板与 scaffold
- `validators`
  - validator 列表
- `checks`
  - AI 审查任务
- `scripts`
  - 执行脚本
- `triggers`
  - 事件输入入口

## 字段设计原则

### `provides`

`provides` 用于回答“这个 pack 具备哪些能力面”，而不是直接塞入完整内容。

例如它可以声明：

- `rules`
- `document_types`
- `prompts`
- `validators`
- `triggers`

### `always_on` 与 `on_demand`

这两个字段不是简单的文件列表，而是上下文装载声明。

它们的区别是：

- `always_on`
  - 会直接参与高层行为塑形
- `on_demand`
  - 只在需要时展开

### `depends_on`

用于声明：

- 此 pack 依赖哪些基础能力
- 若缺少这些能力，pack 是否仍可部分工作

当前阶段先只要求表达依赖关系，不要求定义复杂求解算法。

### `overrides`

用于声明：

- 该 pack 准备覆盖谁
- 覆盖是否显式

它不应绕开平台的 precedence 规则。

## 不变量

`Pack Manifest` 至少应满足以下不变量：

- 一个 manifest 只能描述一个 pack。
- manifest 声明的是能力与关系，不是运行时状态。
- manifest 不应内联大段规则正文。
- `always_on` 与 `on_demand` 应只引用该 pack 可装载的内容。
- `overrides` 不得假定自己能绕过平台核心 precedence。
- 未声明的能力不应被默认视为该 pack 提供。

## 与平台核心的关系

`Pack Manifest` 服务于：

- `Policy Decision Point`
  - 用于知道当前有哪些可用能力与覆盖关系
- `Policy Enforcement Point`
  - 用于知道有哪些 prompts、templates、validators、scripts 可被调用

它同时也是：

- `Always-On Context`
- `On-Demand Pack Content`

这两个抽象的入口声明面。

## 与实例的关系

官方实例和项目级实例都应能通过 manifest 暴露自己的能力。

例如 `doc-driven vibe coding` 未来应能通过 manifest 声明：

- 文档类型
- write-back 规则
- handoff 规则
- 子 agent 合同模板
- 相关 prompts / validators / scripts

## 当前边界

本文件已经固定了：

- `Pack Manifest` 的职责
- 最小字段集合
- 基本不变量

本文件尚未固定：

- 目录布局
- 字段最终类型系统
- 最终序列化格式
- 版本兼容策略

## 开放问题

- `scope` 是否需要进一步拆成 `audience` 与 `workspace_scope`
- `provides` 是否需要固定枚举
- `depends_on` 是否需要区分强依赖与软依赖
- `overrides` 是否需要携带覆盖理由或条件
