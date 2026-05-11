# Planning Gate — Rule / Protocol askQuestions Wording Cleanup

> 日期: 2026-05-06
> 状态: PAUSED
> 来源: scope interrupt during `design_docs/stages/planning-gate/2026-05-06-project-progress-graph-interactive-control-surface.md`

## Why this exists

当前用户额外提出一条 protocol/rule 文档清理需求：

1. 清理修改 rule 内与 `askQuestions` 有关的表述
2. 避免文档把推进式提问过度绑定到单一工具名
3. 避免当前“应直接推进、减少过度询问”的执行倾向与旧表述产生冲突

这条需求不属于当前 active graph interactive control surface slice：

1. 当前 active gate 正在收口 graph-facing snapshot / binding / overlay contract
2. rule/protocol wording cleanup 属于 workflow/protocol surface
3. 因此需要单独记录，不能混入当前 graph 主线实现

## Scope

本 gate 只处理：

1. 盘点当前仓库中与 `askQuestions` 直接绑定的 rule/protocol 表述
2. 区分哪些表述是“必须结构化提问”，哪些只是“推荐工具实现”
3. 清理会与当前 direct-progression 执行策略冲突的 wording

本 gate 不处理：

1. 当前 graph interactive control surface 的代码实现
2. control snapshot / binding / overlay contract
3. runtime / preview / export surface 代码变更

## Working hypothesis

当前最小可行路线应是：

1. 先盘点 `AGENTS.md`、`.github/copilot-instructions.md`、以及相关 protocol 文档中对 `askQuestions` 的强绑定描述
2. 保留“推进式提问 / 结构化确认”的行为 contract
3. 放松或改写与具体工具名强耦合、且会阻碍直接推进的 wording

## Activation condition

仅当当前 active graph slice 到达安全停点，或用户明确要求切回 workflow/protocol 清理线时再激活。