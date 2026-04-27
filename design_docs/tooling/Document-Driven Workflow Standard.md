# Document-Driven Workflow Standard

## 文档定位

本文件定义 `doc-based-coding-platform` 的默认开发闭环：先生成或更新 doc 形成 planning contract，再按 doc 实施，最后把结果与验证回写到 doc 系统。

## 核心闭环

默认流程如下：

1. 从现有文档恢复上下文
2. 生成或刷新一个窄 scope planning doc
3. 只按该 doc 实施当前切片
4. 通过验证门
5. 回写状态板、阶段文档、协议文档与 handoff

## 权威文档分层

推荐分层如下：

- `docs/`
  - 当前仓库的高层平台/实例权威文档
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

对当前仓库应特别强调：

- 若 `docs/` 与 `design_docs/` 中的内部推导或旧设计笔记冲突，以 `docs/` 为准
- `design_docs/` 主要承载状态板、planning/phase 文档与设计推导，而不是反向定义平台本体

对第一次进入仓库的使用者，默认应先由 `docs/starter-surface.md` 提供首跳路由，而不是让 README、安装文档和实例文档分别承担完整入门说明。

`docs/starter-surface.md` 只负责入口分流，不构成第二 authority source。

对临时调查物与稳定文档面的分流，见 `design_docs/tooling/Temporary Scratch and Stable Docs Standard.md`。

当某个 scratch artifact 在当前交互之后仍需要作为恢复入口时，必须按 `Temporary Scratch and Stable Docs Standard` 中定义的 recovery contract 显式报告状态；不满足这一条件的短暂 scratch，不应被强制纳入恢复协议。

## 规划规则

在进入实现前，当前 planning doc 必须说明：

- 本轮要证明或交付什么
- 本轮明确不做什么
- 通过什么验证来宣布完成
- 哪些文档和提示词需要同步更新

## 实施规则

实施时必须遵守：

- 不先编码、后补边界
- 不在当前切片里偷偷吸收邻近 backlog
- 新问题优先写回 planning-gate，而不是就地扩 scope
- 文档事实变化时，要同步更新文档，而不是只更新代码

## Temporary Scratch vs Stable Docs

对当前仓库，默认应把“一次性调查 / 待确认草稿”和“稳定可复用文档资产”分开：

- `.codex/tmp/`（推荐）用于临时 scratch
- `review/` 用于结构化研究与可复用报告
- `design_docs/` 用于方向分析、planning-gate 与长期设计推导
- `docs/` 用于 authority 结论
- Checklist / Phase Map / checkpoint / handoff 永远不视为 scratch

具体 promotion 规则与案例映射，见 `design_docs/tooling/Temporary Scratch and Stable Docs Standard.md`。

若 scratch artifact 满足“当前交互结束后仍需恢复入口”的条件，则还应同时遵守该标准中的四状态 recovery contract；promotion 与 recovery 状态彼此独立，不得互相替代。

## 当前仓库的自用边界

对当前仓库，应区分两类“使用本项目结果”的方式：

- 文档型成果现在就应作为默认控制面：`design_docs/Project Master Checklist.md`、`design_docs/Global Phase Map and Current Position.md`、active planning-gate、`design_docs/tooling/Document-Driven Workflow Standard.md`、handoff、checkpoint、方向分析文档
- 这些文档型成果应直接参与 planning、执行、write-back，而不是只在 Phase 结束后补记

对当前仓库已产出的 Pipeline / CLI / MCP / Instructions / project-local pack 等运行时入口：

- 在首个稳定 release 前，应视为 pre-release dogfood / verification 入口
- 可以用于受控验证、反馈收集和 release 前收敛
- 不应默认成为所有切片的唯一主路径
- 若要提升为默认 self-hosting 主路径，应先完成稳定版收口并得到用户确认

## 人工审核节点

当前仓库额外约束如下：

- 重要设计节点默认不得由 AI 单方面收口，必须先交由用户审核
- 在用户明确审核前，相关设计结论只应视为 `proposed` 或 `waiting_review`

当前默认视为重要设计节点的内容包括：

- 权威文档结构调整
- 核心对象语义变更
- prototype rereview 结论收口
- 是否引入子 agent 以及如何切分
- 会显著影响后续主线选择的设计分叉

若某次工作命中这些节点，应先汇总设计结论，再等待用户审核，而不是直接把设计结论当成既成事实推进到下一大步。

## 对话推进规则

对当前仓库的主 agent 行为，还必须额外遵守以下对话推进约束：

- 未经用户显式许可，不得主动终止对话。
- 默认每条回复都应以推进式提问收尾，且该提问必须包含 AI 自身的分析、推荐或倾向判断，而不是把选择责任完全丢给用户。
- 每次推进式提问前，应先给出当前最相关的文档链接，便于用户直接跳转审核；若提问依赖 planning-gate、direction-analysis、review 文档或权威文档，至少链接最关键的入口。
- 若当前节点需要用户做选择、审批、方向确认或下一步取舍，agent 必须先给出自己的分析与推荐，再通过提问继续交流；需要结构化确认时，应使用 `askQuestions`，而不是把“请用户自己选”当成收尾。
- 对不改变权威边界、阶段顺序、主 consumer/runtime 架构的实现细节，agent 默认应自行判断并继续推进；不得为了满足“以提问结尾”而把细粒度实现选择包装成用户确认节点。
- 只有当实现路径遇到真正困难、局部信息不足且无法通过附近取证消除，或该选择会显著影响结构边界、phase/gate 顺序、主 consumer/runtime 接线方向时，才应升级为用户确认问题。
- 如果一个 Phase 或 planning-gate 已完成，agent 应先准备下一步方向分析或下一份窄 scope planning-gate，再通过提问与用户确认，而不是停下等待。
- 只有在用户明确表示允许结束、暂停，或明确要求本轮不要继续追问时，才可不以推进式提问结尾。
- **完成边界强制规则**：当所有当前任务已完成且不存在活跃 planning-gate 时，agent 必须先调用 `get_next_action` 获取下一步推荐，再基于该推荐组装包含自身判断的 forward question。这是对话推进规则中发现的最高风险违规场景（完成边界失忆），此条规则有最高优先级。

## Checkpoint 触发时机

在以下节点，应调用 `write_checkpoint()` 或手动维护 `.codex/checkpoints/latest.md`：

1. **Phase 完成后** — 记录当前阶段、候选方向、关键文件
2. **上下文即将耗尽前** — 当 conversation 明显变长时，主动写一次 checkpoint
3. **重要设计决定落地后** — 用户审核通过的设计节点
4. **会话安全停点** — 与 handoff 同步写入

Checkpoint 不替代 handoff，而是补充 conversation 内的快照恢复。格式定义见 `design_docs/context-persistence-design.md`。

## Handoff 执行规则

对当前仓库，handoff 分支还必须遵守以下执行语义：

- 一旦当前状态已经满足安全停点，model 可以主动进入 handoff 分支，不需要额外等待显式 slash 指令。
- handoff 分支内的 `generate / accept / refresh current / rebuild` 仍必须满足各自前置条件；主动执行不等于可以越过安全停点、目标解析或结构校验。
- handoff 分支中，`blocked` 是必须上抛的停止信号；若结果不是 `blocked`，model 可以继续执行下一条与当前交接目标直接相关的 handoff 指令。
- 若当前目标是把仓库停在可恢复的 active handoff 状态，则 `generate` 成功后，model 可以继续执行 `refresh current`，而不需要再等待一次重复授权。

## External Skill Interaction Contract

对当前仓库，普通 external skill 与 handoff family 还必须遵守统一的顶层交互 contract：

- 以 `docs/external-skill-interaction.md` 作为 authority source。
- 当 governing workflow 认定这是下一条所需分支时，model 可以主动进入 external skill，不需要把显式 slash 指令当作唯一入口。
- `blocked` 是 external skill 分支中的唯一自动停止信号；若结果不是 `blocked`，model 可以继续执行下一条直接相关的步骤。
- external skill 可以返回 skill-specific payload，但不得借此隐式扩大 authority、write scope 或控制权 owner。
- 若需要 authority 转移，必须走 `handoff` 或 `escalation` 等显式原语。
- 若这些规则被复制到 skill 文本或其他 shipped copies，本轮触达的副本必须通过 companion drift-check / distribution rule 与 authority source 保持一致。

## 临时规则突破

对话过程中，用户可能口头临时授权突破某条 instruction-layer 约束（例如"这轮不用以提问结尾"或"允许本次扩大 scope"）。此类临时授权必须遵守以下规则：

- **可突破约束**（overridable）：C1、C2、C3、C6、C7。这些是 instruction-layer 层的行为约束，用户可临时授权豁免。
- **不可突破约束**（non-overridable）：C4、C5、C8。Machine-checked 约束和 subagent 边界不允许临时绕过。
- **注册**：获得用户口头授权后，model 应通过 `governance_override` MCP tool 将临时 override 注册到 `.codex/temporary-overrides.json`，记录约束标识、授权理由和生效范围。
- **生效范围**：`turn`（单轮生效）、`session`（本次对话）、`until-next-safe-stop`（到下一个安全停点）。
- **自动过期**：session 和 until-next-safe-stop scoped 的 override 在 safe-stop writeback 时自动过期。
- **审计**：所有 override 的注册、撤销与过期记录保留在持久化存储中，`check_constraints` 输出会展示当前活跃的临时 override。
- **禁止**：不得在无用户授权的情况下自行注册 override。

## Safe-Stop Writeback Bundle

当当前切片在安全停点收口时，write-back 不应只理解为“更新一两份状态文档”，而应视为一组 bundle 化动作。

默认必做项至少包括：

- 生成 canonical handoff（写入 `.codex/handoffs/history/*.md`）
- 刷新 `.codex/handoffs/CURRENT.md`
- 同步 `design_docs/Project Master Checklist.md`
- 同步 `design_docs/Global Phase Map and Current Position.md`
- 同步当前方向候选文档
- 同步 `.codex/checkpoints/latest.md`

条件项至少包括：

- 若当前 safe-stop 会把仓库带回无 active slice，则清除 active planning-gate 标记
- 若已有其他 active canonical handoff，则将其 supersede
- 若本轮改变了 safe-stop 或 handoff workflow 语义，则同步 `design_docs/tooling/Document-Driven Workflow Standard.md` 与 `design_docs/tooling/Session Handoff Standard.md`

这些项不应再依赖 main agent 临场回忆。若使用 runtime / tool helper，helper 返回的 `files_to_update` 与 bundle contract 应至少覆盖以上固定收口面。

## 方向模板

Phase 完成后的候选方向应使用 `design_docs/stages/_templates/Direction Candidates Template.md` 模板，确保每条候选方向引用具体权威文档。

## 验证与写回

在宣布当前切片完成前，至少应回写：

- 当前切片做了什么
- 跑了哪些自动化
- 做了哪些手测
- 哪些项仍未验证
- 为什么现在可以收口
- 下一条候选主线是什么

## Prompt Pack 联动

若流程规则、delegation 规则或 write-back 方式发生变化，应同步检查：

- `.codex/prompts/doc-loop/01-planning-gate.md`
- `.codex/prompts/doc-loop/02-execute-by-doc.md`
- `.codex/prompts/doc-loop/03-writeback.md`
- `.codex/prompts/doc-loop/04-subagent-contract.md`

## 当前边界

本标准只定义文档闭环、文档分层与 write-back 规则。

它不替代：

- 具体业务设计
- 代码架构说明
- 单个阶段的功能边界
