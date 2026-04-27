# Project Progress Global Direction Candidates Aggregation Slice 1 Draft

## 目标

把 `design_docs/direction-candidates-after-phase-35.md` 中与 `project progress` 主线直接相关的候选块投影进 `ProgressMultiGraphHistory`，让 progress graph 同时可见当前一跳方向与更长跨度的候选分支面。

## 当前建议的 graph contract

1. graph id：`direction-candidates-global`
2. source path：`design_docs/direction-candidates-after-phase-35.md`
3. section 节点：每个 `project progress` 相关 section 生成一个 `milestone` 节点
4. candidate 节点：按 `- 候选 1/2/3` 生成，kind 先统一为 `decision`

## 当前建议的 selection boundary

1. 只选标题含 `project progress` 的 `##` section
2. 当前不解析其他主线 section
3. 只抽取最小字段：section 标题、已完成边界、候选标题、做什么、依据、当前倾向

## 当前建议的 recommended surface

1. 若 section 中出现 `- 当前倾向：默认先进入候选 N`，则对应 candidate 标记为 recommended
2. recommended candidate 先用 `in_progress` 表示
3. 其余 candidate 先统一为 `pending`

## 当前判断

这条 slice 足够窄，因为它只覆盖 `direction-candidates-after-phase-35.md` 中的 `project progress` 相关 section，不会一开始就卷进整篇 backlog 的泛化 relevance 问题。