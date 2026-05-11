# Planning Gate — Progress Graph Recursive Work-Log Attachment

> 日期: 2026-05-05
> 状态: PAUSED
> 来源: `mcp_doc-based-cod2_workflow_interrupt` during `design_docs/stages/planning-gate/2026-05-03-project-progress-preview-freshness-signaling-and-workflow-polishing.md`

## Why this exists

在处理 host preview 渲染回归时，新增了一条明确但超出当前切片的新需求：

1. 需要一套标准化、可递归查询的工作日志 / 处理记录结构
2. 这些记录应可依附于 progress graph，作为经验积累与后续参考数据

这条需求明显不是当前 freshness / workflow polish gate 的一部分，因为它会把当前工作从“宿主渲染与状态信号”扩到新的数据结构、查询面、投影与展示 contract。

## Scope

本 gate 只处理：

1. work-log / handling-record 在 progress graph 侧的最小 authority contract
2. “可递归查询” 的边界定义：按节点、按图、按处理链还是按经验主题查询
3. 记录面与现有 checkpoint / planning-gate / graph artifact 之间的最小依附关系
4. 是否需要新的 projection / export / preview surface

本 gate 不处理：

1. 当前 host preview 渲染回归修复
2. 当前 freshness signaling gate 的 close-ready 验证
3. compound node / hierarchy expansion
4. watcher / auto-refresh

## Working hypothesis

当前最小可行路线应是：

1. 先把 work-log 视为依附于现有 progress graph node / graph 的 companion data，而不是立刻扩成第二套独立 graph
2. 查询面优先固定为“从 graph 节点或 graph section 递归追到相关处理记录”，而不是先做通用知识库
3. 第一刀应先固定 authority path、record schema 与 query contract，再决定是否投影到 current preview

## Activation condition

仅当以下条件满足时再激活本 gate：

1. `design_docs/stages/planning-gate/2026-05-03-project-progress-preview-freshness-signaling-and-workflow-polishing.md` 已完成或安全停点
2. 当前 graph preview 的宿主承载与行为验证不再阻塞日常使用
3. 用户明确要求把经验记录依附到 progress graph，并进入 schema / query contract 设计

## Stop condition

当前状态只做需求登记，不进入实现。