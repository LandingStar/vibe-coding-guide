# 项目总清单与状态板

## 文档定位

本文件是 `doc-based-coding-platform` 的总入口、状态板与协作恢复入口。

若当前对话、workspace 现实状态与其他文档冲突，优先级应为：

1. 用户在最新对话中的明确决定
2. 当前 workspace 的现实状态
3. 正式设计文档与协议文档
4. 当前 active handoff

## 当前快照

- Snapshot Date: `2026-04-08`
- Project Name: `doc-based-coding-platform`
- Current Phase: `Phase 2 Review Checkpoint`
- Active Slice: `design_docs/doc-loop-prototype-authority-rereview.md`
- Safe Stop Status: `Waiting User Review`

## 当前文档入口

- `docs/README.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/stages/planning-gate/2026-04-08-doc-loop-prototype-authority-rereview.md`
- `design_docs/doc-loop-prototype-authority-rereview.md`
- `design_docs/stages/README.md`
- `design_docs/tooling/README.md`
- `.codex/handoffs/CURRENT.md`

## 已确认决策

- 本项目默认采用“生成/更新 doc 规划 -> 按 doc 实施 -> 结果回写 doc”的工作流。
- 根目录 `docs/` 是当前仓库里关于平台与官方实例定位的最高权威来源。
- `design_docs/` 现在主要承载状态板、planning/phase 文档与内部设计推导。
- 当前已完成第一条仓库级执行切片：把 repo-local adoption 入口对齐到当前仓库现实。
- 当前已开启下一条 planning gate：`doc-loop-vibe-coding` prototype authority rereview。
- 重要设计节点默认必须先交用户审核，再进入下一大步。
- 当前已形成 prototype authority rereview 结论，正在等待用户审核。
- handoff 只负责安全停点交接，不替代正式设计文档。

## 当前待办与风险

- 当前主线：等待用户审核 `design_docs/doc-loop-prototype-authority-rereview.md`。
- 后续候选主线：根据审核结果决定优先补 prototype cleanup 还是 runtime/spec formalization。
- 风险：若 `docs/`、`design_docs/` 与 project-local pack 的入口再次漂移，后续 agent 仍可能按过时入口恢复上下文。

## 最近一次写回

- `2026-04-08`: 初始化 doc-loop 骨架。
- `2026-04-08`: 对齐当前仓库的 repo-local adoption 入口，使 `docs/` 成为 project-local pack 的正式权威输入之一。
- `2026-04-08`: 起草 `doc-loop-vibe-coding` prototype authority rereview 的 planning-gate。
- `2026-04-08`: 形成 `doc-loop-vibe-coding` prototype authority rereview 结论并进入用户审核节点。
