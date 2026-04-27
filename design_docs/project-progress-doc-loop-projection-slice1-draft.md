# 设计草案 — Project Progress Doc-Loop Projection Slice 1

本文是 `design_docs/stages/planning-gate/2026-04-26-project-progress-doc-loop-projection-and-snapshot-persistence.md` 的 Slice 1 设计草案。

## 目标

当前只固定最小 projection contract：

1. 哪些文档来源进入 progress graph
2. 每类来源如何映射为 graph / node / edge / metadata
3. snapshot 持久化放在哪里

## 当前推荐 graph ids

当前推荐先固定 3 个 graph：

1. `checkpoint-current`
2. `planning-gates-index`
3. `project-checklist-current`

## 当前推荐 source mapping

### 1. checkpoint-current

- 来源：`.codex/checkpoints/latest.md`
- 节点：current todo items
- 边：todo list 顺序上的 `workflow` edge
- metadata：phase、planning_gate、pending_decision、timestamp

### 2. planning-gates-index

- 来源：`design_docs/stages/planning-gate/*.md`
- 节点：每个 planning-gate 文档
- 边：首版不推断 workflow/dependency，仅保留文档索引与状态
- metadata：gate path、status、related analysis、date

### 3. project-checklist-current

- 来源：`design_docs/Project Master Checklist.md`
- 节点：Active Slice、Latest Completed Slice、活跃待办 items
- 边：活跃待办顺序上的 `workflow` edge；其余关系先用 `linkage`
- metadata：snapshot date、current phase、safe stop status

## 当前推荐 status mapping

当前推荐先固定：

1. `done` / `x` / `complete` / `completed` / `closed` -> `completed`
2. `active` / `in-progress` / `in progress` -> `in_progress`
3. `paused` / `blocked` -> `blocked`
4. 其余未完成项 -> `pending`

## 当前推荐 persistence path

当前推荐先固定到：

1. `.codex/progress-graph/latest.json`

该文件存整份 `ProgressMultiGraphHistory`，每次投影时追加新 snapshot 并刷新当前图指针。

## 当前判断

我当前判断这条 slice 足够窄，因为它只把真实 doc-loop 来源接到已有 graph foundation 上，不进入 UI、调度或通用 markdown 解析框架。