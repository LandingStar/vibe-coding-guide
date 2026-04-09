# Core Model

## 文档定位

本文件定义平台级核心对象与它们之间的关系。

它只回答“系统里有哪些核心对象，它们如何互动”，不定义某个具体实例的文档模板。

## 核心视角

本平台不是“人和文档直接协作”的模型，而是：

**human-governed, AI-operated, artifact-mediated workflow**

也就是：

- 人通过审阅、质疑、建议、批准来治理流程
- 主 AI 负责实际读取、改写、整合和维护文档
- 文档与其他产物承担外部化工作记忆和行动合同
- 子 agent 只消费被裁剪过的局部合同

## Actors

### Human Reviewer

负责：

- 审核 AI 的判断和提案
- 提出疑点、修正意见和新约束
- 对高影响决策进行批准或否决

默认不直接维护大部分权威文档。

### Main AI

负责：

- 判断当前输入的交互意图
- 读取和比较权威文档
- 按规则决定下一步动作
- 起草、修改、整合和回写文档
- 驱动实现、验证与实例级 write-back

主 AI 是文档系统的默认操作者。

### Subagent

负责：

- 执行被明确写入合同的窄切片
- 返回事实、验证和未决项

默认不直接维护平台级权威文档，也不自行改写高层协议。

## Artifacts

平台中的关键 artifact 包括：

- 平台文档
- 实例文档
- 提示词
- 模板
- 校验器
- 脚本
- 代码与其他实现产物

文档不是唯一 artifact，但它是当前官方实例里最主要的控制面。

## Policy Decision Point

平台应显式区分 `Policy Decision Point` 与执行层。

`Policy Decision Point` 负责：

- interaction intent classification
- rule evaluation
- precedence resolution
- gate decision
- delegation decision
- escalation decision

它的职责是产出结构化决策，而不是直接落地副作用。

## Policy Enforcement Point

`Policy Enforcement Point` 负责执行经过决策层允许的动作，例如：

- 文档起草与改写
- 模板应用
- script / validator / check 调用
- handoff 落地
- write-back
- tracing 记录

这样做的原因是：

- 决策和执行可以独立演化
- 子 agent 执行器不需要兼任 policy authority
- 高影响动作可审计、可 review、可拒绝

## Interaction Intent

人类输入默认是自然语言，不需要手工声明输入类型。

由 AI 在规则约束下判断当前输入更像哪类**interaction intent**，例如：

- `question`
- `correction`
- `constraint`
- `scope-change`
- `protocol-change`
- `approval`
- `rejection`
- `request-for-writeback`
- `issue-report`
- `unknown`

这里的关键点是：

- 分类由 AI 负责
- 分类结果应可见
- 人可以纠正分类
- 高影响分类不能无保护地直接生效
- 必须允许 `unknown` 或 `ambiguous`

## Rule

Rule 是平台上约束行为的基本单元。

一个 rule 可以约束：

- 谁能改什么
- 某类输入触发什么动作
- 某类变更需要什么 gate
- 某类文档如何被读写
- 某类实例需要哪些模板或校验

Rule 不局限于文档规则，也可以覆盖 prompt、脚本与验证行为。

## Gate

Gate 是对高影响动作的控制点。

当前建议至少存在三类决策级别：

- `inform`
  - AI 可先更新，再向人汇报
- `review`
  - AI 先起草，由人审阅后再定稿
- `approve`
  - AI 不得自行落地，必须等待人的显式批准

哪些动作属于哪一级，不由核心模型单独决定，而由实例和项目定制规则共同决定。

## Review State Machine

高影响动作不应只有 gate label，还应进入统一的 review 状态机。

当前最小状态为：

- `proposed`
- `waiting_review`
- `approved`
- `rejected`
- `revised`
- `applied`

其中：

- `inform` 通常可直接进入 `applied`
- `review` 通常要经过 `waiting_review`
- `approve` 通常必须显式进入 `approved` 后才能执行

后续若需要 `cancelled`、`superseded` 等状态，应在不破坏当前最小闭环的前提下扩展。

更具体的状态与迁移规则见：

- `review-state-machine.md`

## Delegation Decision

是否委派给子 agent，不应只是一种执行技巧，而应是决策层正式输出。

一个 `Delegation Decision` 至少应回答：

- 当前是否允许委派
- 推荐的协作模式是什么
- 子 agent 是否只能作为 worker
- 是否允许 handoff
- 是否需要先经过 review / approve

这保证子 agent 管理不会绕开平台规则。

## Subagent Core Objects

平台核心中至少需要以下与子 agent 有关的对象：

- `Supervisor`
- `Worker`
- `Subagent Contract`
- `Subagent Report`
- `Handoff`
- `Escalation`

它们的关系是：

- `Supervisor` 负责委派、review、integration 与 write-back
- `Worker` 负责被合同限定的窄切片
- `Subagent Contract` 负责明确输入边界
- `Subagent Report` 负责结构化返回结果
- `Handoff` 负责显式移交控制权
- `Escalation` 负责把问题升级给更高 authority

相关对象的最小 schema 见：

- `subagent-schemas.md`

## Default Collaboration Mode

当前平台默认协作模式应理解为：

- `supervisor-worker`

而不是：

- `group chat`
- `swarm`
- `peer mesh`

原因是 `supervisor-worker` 最适合：

- coding governance
- 文档控制面
- artifact ownership 约束
- write-back 收口

其他协作模式仍可存在，但应视为扩展模式，而不是默认模式。

## Handoff And Escalation

`Handoff` 不应被视为普通 tool call 的语义变体。

它应是平台里的独立对象，因为它意味着：

- 控制权转移
- 上下文承接
- tracing 与审计链延续
- 独立的 guard / validator / review 规则

`Escalation` 则用于：

- 子 agent 回到主 agent
- 主 agent 回到 human reviewer
- 低置信度或高影响决策升级

## Tracing And Audit

平台应默认支持最小 tracing / audit 能力，以记录：

- 输入是什么
- PDP 做了什么决策
- 触发了哪个 gate
- 是否发生委派
- 是否发生 handoff / escalation
- 哪个 PEP 执行了什么动作
- 最终写回了哪些 artifact

这不是调试附属物，而是治理平台的基础能力。

## Authority And Precedence

当前推荐优先级从高到低为：

1. 用户当前回合中的明确决定
2. 当前 workspace 的现实状态
3. 项目级定制规则
4. 官方实例规则
5. 平台核心默认规则
6. 历史产物与旧摘要

这个顺序的目的，是让平台既能扩展，又不失去现实约束。

## Core Loop

平台级最小运行环如下：

1. 接收自然语言输入
2. `Policy Decision Point` 判断 interaction intent
3. 加载相关规则、pack 与实例上下文
4. 进行 precedence、gate 与 delegation 决策
5. 若进入 review，则走 `Review State Machine`
6. `Policy Enforcement Point` 执行被允许的动作
7. 写回 artifact，并记录 tracing / audit 信息
8. 记录新的状态与未决项

## 当前边界

本文件只定义平台级核心模型。

它不定义：

- 具体官方实例有哪些文档
- 具体模板长什么样
- 某个实例的 write-back 细节
- 某个实例的 handoff schema
- 某个 pack manifest 的最终字段

这些都属于实例文档和插件模型。
