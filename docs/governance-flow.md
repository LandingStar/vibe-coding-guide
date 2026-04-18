# Governance Flow

## 文档定位

本文件定义平台中的高层治理流转。

它关注的是：

- 一个输入如何被判断
- 何时进入 review / approve
- 何时允许执行
- 何时允许 write-back

它不定义某个实例内部的具体文档模板。

## 最小流转

当前平台最小治理流如下：

1. 接收输入
2. 判定 interaction intent
3. 加载相关规则、pack 与上下文
4. 进行 gate 与 delegation 决策
5. 若需要 review，则进入 review 状态机
6. 执行被允许的动作
7. 写回 artifact
8. 记录 tracing / audit 信息

## 输入层

当前平台默认允许的输入类型至少包括：

- 自然语言聊天输入
- issue
- PR
- CI failure
- webhook
- schedule

输入来源不要求人手工声明输入类型；AI 负责判断 interaction intent。

## Intent Classification

interaction intent 判断属于 `Policy Decision Point` 的职责。

最低要求：

- 结果可见
- 可被人工纠偏
- 允许 `unknown` / `ambiguous`
- 高影响 intent 不得自动无保护生效

## Gate Decision

当前 gate 级别为：

- `inform`
- `review`
- `approve`

PDP 的任务是结合：

- 当前 intent
- precedence
- active pack rules
- workspace 现实状态

决定当前动作需要哪个 gate。

## Review State Machine

当前统一 review 状态为：

- `proposed`
- `waiting_review`
- `approved`
- `rejected`
- `revised`
- `applied`

推荐理解：

- `proposed`
  - 已形成动作提案，但尚未进入最终审查
- `waiting_review`
  - 等待人或更高 authority 审核
- `approved`
  - 已授权执行
- `rejected`
  - 明确不允许执行
- `revised`
  - 根据反馈重写后重新进入提案
- `applied`
  - 已执行并完成 write-back

更具体的状态、事件与迁移规则见：

- `review-state-machine.md`

## Policy Decision Point

PDP 至少负责：

- intent classification
- precedence resolution
- gate decision
- delegation decision
- escalation decision

它输出的是结构化决策，而不是直接执行副作用。

## Policy Enforcement Point

PEP 至少负责：

- 文档改写
- 模板应用
- checks / validators / scripts 触发
- handoff 落地
- write-back
- tracing 记录

PEP 不负责自行重解释规则优先级。

## Human Review

人类在平台中默认不是文档直接操作者，而是：

- reviewer
- approver
- corrector

也就是：

- 人通过审阅 AI 来治理文档与动作
- AI 通过文档与其他 artifact 来治理执行

## Delegation In Flow

若当前任务需要子 agent 参与：

- 是否委派由 PDP 决定
- 委派后的实际执行由 PEP 触发
- 子 agent 结果先返回给主 agent
- 主 agent 负责 integration 与 write-back

高影响委派仍可进入 `review` 或 `approve`。

子 agent 相关对象的最小 schema 见：

- `subagent-schemas.md`

## Escalation In Flow

若出现以下情况，应进入 escalation：

- intent 分类低置信度
- scope 不清晰
- 需要修改权威文档
- 需要跨多个 write scope 集成
- 触发高影响 gate

escalation 的目标可以是：

- 主 agent
- human reviewer

## Tracing And Audit

每次治理流转至少应能追溯：

- 输入是什么
- intent 如何被判断
- 命中了哪些规则
- 触发了哪个 gate
- 是否发生 delegation / handoff / escalation
- 执行了哪些动作
- 写回了哪些 artifact
- 是否存在临时规则 override（含约束标识、授权理由与有效范围）

## Temporary Rule Override

对话过程中用户可临时授权豁免 instruction-layer 约束。此类 override 有以下治理属性：

- 仅限可突破约束（C1/C2/C3/C6/C7）；machine-checked 约束（C4/C5）与 subagent 边界（C8）不可突破
- 必须有显式用户授权才能注册
- 通过 `governance_override` MCP tool 注册到 `.codex/temporary-overrides.json`
- 在 safe-stop writeback bundle 中自动过期
- 审计记录保留 override 的完整生命周期（注册、撤销、过期）

## 当前边界

本文件只定义平台级治理流转。

它不定义：

- 某个实例的具体 write-back 文档列表
- 某个实例的具体 handoff 模板
- 某个 pack 的 manifest 文件格式
