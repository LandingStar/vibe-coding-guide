# Document-Driven Workflow Standard

## 文档定位

本文件定义 `{{PROJECT_NAME}}` 的默认开发闭环：先生成或更新 doc 形成 planning contract，再按 doc 实施，最后把结果与验证回写到 doc 系统。

## 核心闭环

默认流程如下：

1. 从现有文档恢复上下文
2. 生成或刷新一个窄 scope planning doc
3. 只按该 doc 实施当前切片
4. 通过验证门
5. 回写状态板、阶段文档、协议文档与 handoff

## 权威文档分层

推荐分层如下。此分层对应平台的三层 adoption 模型：平台权威文档（`docs/`）、官方实例 pack、项目级本地 pack。

- `docs/`
  - 平台级权威文档（若本项目携带平台 docs）。定义核心对象、gate 语义、review state machine、project adoption、插件模型。若与项目内部文档冲突，以 `docs/` 为准。
- `Project Master Checklist.md`
  - 状态板与协作入口
- `Global Phase Map and Current Position.md`
  - 当前阶段口径与阅读顺序
- `design_docs/stages/`
  - planning-gate、phase doc、manual test guide
- `design_docs/tooling/`
  - 长期有效的协议与标准
- `.codex/handoffs/CURRENT.md`
  - 安全停点交接入口
- `.codex/prompts/doc-loop/`
  - 可复用提示词面

## 规划规则

在进入实现前，当前 planning doc 必须说明：

- 本轮要证明或交付什么
- 本轮明确不做什么
- 通过什么验证来宣布完成
- 哪些文档和提示词需要同步更新
- 本轮预期产出物需要哪个 gate 层级（`inform`、`review` 或 `approve`）

若本轮切片涉及重要设计节点，规划文档应明确注明：产出物必须经过用户审核（通过 review state machine 进入 `proposed → waiting_review → approved`）才能应用。

## 实施规则

实施时必须遵守：

- 不先编码、后补边界
- 不在当前切片里偷偷吸收邻近 backlog
- 新问题优先写回 planning-gate，而不是就地扩 scope
- 文档事实变化时，要同步更新文档，而不是只更新代码

## 验证与写回

在宣布当前切片完成前，至少应回写：

- 当前切片做了什么
- 跑了哪些自动化
- 做了哪些手测
- 哪些项仍未验证
- 为什么现在可以收口
- 下一条候选主线是什么

## 对话推进规则

对采用本 workflow 的主 agent，还必须额外遵守以下约束：

- 未经用户显式许可，不得主动终止对话。
- 默认每条回复都应以推进式提问收尾，且该提问必须包含 AI 自身的分析、推荐或倾向判断。
- 每次推进式提问前，应先给出当前最相关的文档链接，便于用户直接跳转审核；若提问依赖 planning-gate、direction-analysis、review 文档或权威文档，至少链接最关键的入口。
- 若当前节点需要用户做选择、审批、方向确认或下一步取舍，agent 必须先给出自己的分析与推荐，再通过 askQuestions 或明确提问继续交流。
- 若一个 Phase 或 planning-gate 已完成，agent 应先准备下一步方向分析或下一份窄 scope planning-gate，再通过提问与用户确认，而不是停下等待。
- 只有在用户明确表示允许结束、暂停，或明确要求本轮不要继续追问时，才可不以推进式提问结尾。
- **完成边界强制规则**：当所有当前任务已完成且不存在活跃 planning-gate 时，agent 必须先调用 `get_next_action` 获取下一步推荐，再基于该推荐组装包含自身判断的 forward question。这是对话推进规则中发现的最高风险违规场景（完成边界失忆），此条规则有最高优先级。

## Prompt Pack 联动

若流程规则、delegation 规则或 write-back 方式发生变化，应同步检查：

- `.codex/prompts/doc-loop/01-planning-gate.md`
- `.codex/prompts/doc-loop/02-execute-by-doc.md`
- `.codex/prompts/doc-loop/03-writeback.md`
- `.codex/prompts/doc-loop/04-subagent-contract.md`

## Handoff 执行规则

对采用本 workflow 的项目，handoff 分支还应遵守以下执行语义：

- 一旦当前状态已经满足安全停点，model 可以主动进入 handoff 分支，不需要额外等待显式 slash 指令。
- handoff 分支内的 `generate / accept / refresh current / rebuild` 仍必须满足各自前置条件。
- `blocked` 是 handoff 分支中的停止信号；若结果不是 `blocked`，model 可以继续执行下一条与当前交接目标直接相关的 handoff 指令。

## External Skill Interaction Contract

对采用本 workflow 的项目，external skill 的顶层交互语义应保持统一：

- 当 governing workflow 认定这是下一条所需分支时，model 可以主动进入 external skill，不需要把显式 slash 指令当作唯一入口。
- `blocked` 是 external skill 分支中的唯一自动停止信号；若结果不是 `blocked`，model 可以继续执行下一条直接相关的步骤。
- external skill 可以返回 skill-specific payload，但不得借此隐式扩大 authority、write scope 或控制权 owner。
- 若需要 authority 转移，必须走 `handoff` 或 `escalation` 等显式原语。
- 若这些规则被复制到 skill 文本或其他 shipped copies，应为本轮触达的副本补 companion drift-check / distribution rule。

## Safe-Stop Writeback Bundle

当当前切片在安全停点收口时，write-back 应按 bundle 处理，而不是只零散更新少量文档。

默认必做项至少包括：

- 生成 canonical handoff
- 刷新 `.codex/handoffs/CURRENT.md`
- 同步 `Project Master Checklist.md`
- 同步 `Global Phase Map and Current Position.md`
- 同步当前方向候选文档
- 同步 `.codex/checkpoints/latest.md`

条件项至少包括：

- 若 safe-stop 会带回无 active slice，则清除 active planning-gate 标记
- 若已有其他 active canonical handoff，则将其 supersede
- 若本轮改变了 safe-stop / handoff workflow 语义，则同步相应协议文档

## 当前边界

本标准只定义文档闭环、文档分层与 write-back 规则。

它不替代：

- 具体业务设计
- 代码架构说明
- 单个阶段的功能边界
