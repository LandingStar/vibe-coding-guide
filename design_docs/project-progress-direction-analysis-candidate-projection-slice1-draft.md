# Project Progress Direction Analysis Candidate Projection Slice 1 Draft

## 目标

把当前 active 的 follow-up direction-analysis 文档投影进 `ProgressMultiGraphHistory`，让 progress graph 除了显示“已发生的推进事实”，还能够显示“当前推荐的下一步候选分支”。

## 当前建议的 graph contract

1. graph id：`direction-analysis-current`
2. source path：读取 `design_docs/Project Master Checklist.md` 中最新的 `project-progress-*-followup-direction-analysis.md` 记录
3. 根节点：当前分析文档本身，表达当前 direction-analysis 入口
4. candidate 节点：按 `### A/B/C` 生成，kind 先统一为 `decision`

## 当前建议的 candidate status contract

1. 当前 AI 推荐候选：`in_progress`
2. 其他候选：`pending`
3. 推荐标记同时保留在 node metadata 中，避免后续 consumer 只能依赖 status 猜测

## 当前建议的 parser boundary

1. 只解析 `## 候选路线` 下的 `### A/B/C` 结构
2. 只抽取最小字段：标题、做什么、依据、当前判断
3. 只解析 `## 当前 AI 倾向判断` 中的推荐候选字母
4. 第一刀不支持全仓库自动发现；只解析 Checklist 当前记录的单篇 `project-progress` follow-up analysis 文档

## 当前判断

这条 slice 足够窄，因为它只覆盖 Checklist 当前记录的单篇 `project-progress` follow-up direction-analysis 文档，并把候选项投影成 graph，不会一开始就卷入全局 candidate backlog 聚合与 ranking。