# 项目总清单与状态板

## 文档定位

本文件是 `{{PROJECT_NAME}}` 的总入口、状态板与协作恢复入口。

若当前对话、workspace 现实状态与其他文档冲突，优先级应为：

1. 用户在最新对话中的明确决定
2. 当前 workspace 的现实状态
3. 正式设计文档与协议文档
4. 当前 active handoff

## 当前快照

- Snapshot Date: `{{CURRENT_DATE}}`
- Project Name: `{{PROJECT_NAME}}`
- Current Phase: `Planning Gate`
- Active Slice: `TBD`
- Safe Stop Status: `Bootstrap Only`

## 当前文档入口

- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/stages/README.md`
- `design_docs/tooling/README.md`
- `.codex/handoffs/CURRENT.md`

## 已确认决策

- 本项目默认采用“生成/更新 doc 规划 -> 按 doc 实施 -> 结果回写 doc”的工作流。
- 当前还处于 bootstrap 后的规划门，尚未进入第一条正式执行切片。
- handoff 只负责安全停点交接，不替代正式设计文档。

## 当前待办与风险

- `TBD`: 定义第一条窄执行主线并写成 planning-gate 文档。
- `TBD`: 根据项目实际情况细化阶段树和验证门。
- 风险：若先编码再补文档，后续上下文会再次漂移。

## 最近一次写回

- `{{CURRENT_DATE}}`: 初始化 doc-loop 骨架。
