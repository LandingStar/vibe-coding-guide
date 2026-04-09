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

推荐分层如下：

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
