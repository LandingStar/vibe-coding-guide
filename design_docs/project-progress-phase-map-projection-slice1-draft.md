# Project Progress Phase Map Projection Slice 1 Draft

## 目标

把 `design_docs/Global Phase Map and Current Position.md` 的 recent history / current position 时间线接入 `ProgressMultiGraphHistory`，让当前 preview 不只显示 checkpoint/checklist/gates，还能显示项目阶段叙事的最近推进链。

## 当前建议的 graph contract

1. graph id：`phase-map-current-position`
2. source path：`design_docs/Global Phase Map and Current Position.md`
3. node kind：recent history entry 先统一投影为 `milestone`
4. node status：第一刀先统一为 `completed`

## 当前建议的 recent-entry boundary

1. 只抓取 date-prefixed 行：`YYYY-MM-DD ...`
2. 只保留最近一小段时间线，而不是把整篇 phase map 全量压进图里
3. 第一刀优先服务展示与历史回看，不追求完整 narrative parser

## 当前建议的 linkage boundary

1. 若 recent-entry 文本里显式出现 `design_docs/stages/planning-gate/*.md`
2. 且该路径存在于 current `planning-gates-index`
3. 则建立 `phase-map-current-position -> planning-gates-index` 的 `linkage`

## 当前判断

这条 slice 足够窄，因为它只补单一权威文档的 recent-history 投影与显式 gate linkage，不进入 direction-analysis 解析或更广的推断逻辑。