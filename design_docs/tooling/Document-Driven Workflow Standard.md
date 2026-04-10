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

## Checkpoint 触发时机

在以下节点，应调用 `write_checkpoint()` 或手动维护 `.codex/checkpoints/latest.md`：

1. **Phase 完成后** — 记录当前阶段、候选方向、关键文件
2. **上下文即将耗尽前** — 当 conversation 明显变长时，主动写一次 checkpoint
3. **重要设计决定落地后** — 用户审核通过的设计节点
4. **会话安全停点** — 与 handoff 同步写入

Checkpoint 不替代 handoff，而是补充 conversation 内的快照恢复。格式定义见 `design_docs/context-persistence-design.md`。

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
