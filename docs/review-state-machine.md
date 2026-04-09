# Review State Machine

## 文档定位

本文件定义平台中的最小 `Review State Machine`。

它的目标是把高影响动作从“口头上说要 review”推进为：

- 有状态
- 有事件
- 有迁移规则
- 可追溯

本文件当前只定义状态机语义，不绑定具体实现方式。

## 解决什么问题

如果没有统一 review 状态机：

- `inform / review / approve` 很容易退化成模糊标签
- proposal、revision、approval、apply 的边界会混乱
- handoff、subagent output、write-back 很难共享同一套审批语言

## 不解决什么问题

本文件不定义：

- 谁来担任 reviewer
- 某个实例具体需要哪些文档审批
- UI 如何展示状态
- 具体数据库或事件总线实现

## 最小状态

当前平台固定以下最小状态：

- `proposed`
- `waiting_review`
- `approved`
- `rejected`
- `revised`
- `applied`

## 状态语义

### `proposed`

已经形成动作提案，但还未提交最终审查。

### `waiting_review`

提案已经进入 review 阶段，等待 reviewer 或 approver 决定。

### `approved`

提案已经被授权执行，但尚未真正落地。

### `rejected`

当前提案被拒绝，默认视为本轮提案的终止状态。

### `revised`

当前提案收到了 revision feedback，且已经形成一个修订中的新版本语境。

这里保留 `revised` 为显式状态，而不是仅作为事件，是为了保留审计清晰度。

### `applied`

提案已经执行并完成 write-back。

## 最小事件

当前建议最小事件集合为：

- `propose`
- `submit_for_review`
- `approve`
- `reject`
- `request_revision`
- `revise`
- `apply`

## 事件语义

### `propose`

生成一个新的提案，使对象进入 `proposed`。

### `submit_for_review`

将 `proposed` 的提案提交审查，进入 `waiting_review`。

### `approve`

将 `waiting_review` 的提案推进到 `approved`。

### `reject`

将 `waiting_review` 的提案推进到 `rejected`。

### `request_revision`

将 `waiting_review` 的提案推进到 `revised`，表示需要改后再提。

### `revise`

对 `revised` 中的提案进行修订，并重新生成一个 `proposed` 版本。

### `apply`

将被允许执行的提案真正落地，并进入 `applied`。

## 最小迁移规则

当前建议允许的核心迁移为：

- `propose` -> `proposed`
- `proposed` + `submit_for_review` -> `waiting_review`
- `waiting_review` + `approve` -> `approved`
- `waiting_review` + `reject` -> `rejected`
- `waiting_review` + `request_revision` -> `revised`
- `revised` + `revise` -> `proposed`
- `approved` + `apply` -> `applied`

对于 `inform` 级动作，允许快速路径：

- `proposed` + `apply` -> `applied`

## 不变量

- `approved` 之前，除 `inform` 快速路径外，不得进入 `applied`。
- `rejected` 默认不是可直接恢复状态；若要继续，通常应生成新的 `proposed`。
- `revised` 不是终态，它必须能重新流回 `proposed`。
- 每次迁移都应可被 tracing / audit 记录。

## 与 Gate 的关系

`inform / review / approve` 不是状态，而是 PDP 输出的 gate 级别。

它们与状态机的关系是：

- `inform`
  - 允许快速应用
- `review`
  - 必须进入 `waiting_review`
- `approve`
  - 必须显式经过 `approved` 才能 `apply`

## 与子 agent 的关系

以下对象都可能进入 review 状态机：

- 主 agent 的 write-back proposal
- `Subagent Report` 的整合结果
- `Handoff`
- 高影响模板应用

换句话说，review 状态机不是某一类 artifact 私有的，而是平台级流转语义。

## 与 Tracing 的关系

每次状态迁移至少应记录：

- 当前对象
- 迁移前状态
- 事件
- 迁移后状态
- 触发原因
- 关联 gate
- 关联 reviewer / authority

## 当前边界

本文件已经固定：

- 最小状态
- 最小事件
- 最小迁移规则
- `revised` 为显式状态

本文件尚未固定：

- 是否加入 `cancelled`
- 是否加入 `superseded`
- 是否需要按 artifact 类型细化迁移约束

## 开放问题

- `revised` 是否应保留历史版本链
- `rejected` 后是否允许某些轻量对象原地重开
- `inform` 快速路径是否仍需要最小 reviewer 可见性
