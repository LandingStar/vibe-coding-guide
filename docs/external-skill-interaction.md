# External Skill Interaction

## 文档定位

本文件定义平台级的 `external skill interaction` 最小 contract。

它回答的不是“某个具体 skill 怎么写”，而是：

- 主 agent 何时可以触发外部 skill
- 外部 skill 的结果如何控制后续流转
- 哪些 authority / write scope 边界绝不能被普通 skill 隐式扩大
- 当这些语义被复制到 skill 文本、官方实例 reference 或其他 shipped copies 时，应如何保持与权威来源一致

## 为什么单独成文

当前仓库已经在 handoff family 上证明了几条可用经验，但这些经验此前主要散落在 handoff 特化协议与 shipped copies 中。

如果没有一份独立的权威 contract，平台后续新增其他 external skill 时，仍会重复“先在某个 skill 里跑通，再回头补抽象”的路径。

因此，本文件的目标是把那些已经被证明有效的交互语义，提升为项目无关、skill 家族无关的最小平台 contract。

## Core Contract

- model-initiated entry is allowed when the governing workflow says this skill is the next required step.
- explicit slash routing is valid but is not the only invocation surface.
- blocked is the only automatic stop signal.
- if the result is not blocked, the model may continue to the next directly relevant step.
- this skill does not widen authority, write scope, or control ownership on its own.

## Invocation Boundary

外部 skill 的触发必须同时满足：

- 当前 workflow / rules 明确允许进入该 skill 分支
- 该 skill 的本地前置条件已经满足
- 当前入口没有命中更高优先级的 review / approve / blocked 边界

显式 slash 或客户端路由提示仍然是合法入口，但它只是显式路由方式，不应被写成唯一入口。

## Continuation Boundary

平台要求所有 external skill 至少暴露稳定的顶层 continuation semantics：

- `blocked` 会中止当前 skill 分支并要求上抛原因
- 非 `blocked` 结果允许继续到下一条直接相关的步骤

skill 自己仍可以保留领域化 payload、状态枚举或详细报告，但主 agent 不应依赖某个 skill 的私有字段去重写平台级 continuation 规则。

## Authority Boundary

普通 external skill 可以：

- 提供结果
- 提供 warning / blocking issue / next-step hint
- 在已授权范围内生成或更新局部 artifact

普通 external skill 不可以：

- 隐式扩大权威文档写权限
- 隐式扩大全局状态板 owner 范围
- 隐式带走 active handoff owner
- 用普通结果直接表达 authority transfer

如果确实需要 authority 转移，必须通过平台已定义的显式原语完成，例如：

- `handoff`
- `escalation`

## Reference Implementation Boundary

当前仓库的首个 reference implementation family 是：

- `.github/skills/project-handoff-*`

这组 skill 继续保留各自的领域语义，但应共享本文件定义的顶层交互 contract。

这意味着：

- handoff family 是 proof point，而不是平台 contract 的唯一适用对象
- 后续新增 external skill 时，应优先复用本文件，而不是复制 handoff 特化表述

## Authority -> Shipped Copies

当本 contract 被复制到 skill 文本、官方实例 reference、bootstrap 资产或其他 shipped copies 时，应把本文件视为 authority source。

对应规则是：

- 先稳定 authority contract，再做复制或分发
- shipped copies 不得反向定义 authority semantics
- 对本轮触达的 shipped copies，应通过 companion drift-check / distribution rule 校验核心语义没有漂移

这就是为什么 `authority -> shipped copies` 属于本 contract 的 companion mechanism，而不是独立主切片。

## 消费方 Contract

本文件定义的是 skill 提供方的 contract。消费方（driver）的职责边界、输入来源和结果分发路径定义在 [`driver-responsibilities.md`](driver-responsibilities.md)。

两者形成对称：
- 本文件回答"skill 应如何暴露结果"
- `driver-responsibilities.md` 回答"driver 应如何消费这些结果"

## 当前边界

本文件只固定最小 external skill interaction contract。

它不定义：

- 完整 driver / adapter / 转接层长期架构
- 全部 external skill 家族的一次性适配
- registry / marketplace / 远端分发协议
- 所有 shipped copies 的全自动 code generation