# 全候选方向对比表 — 2026-04-18

> 生成时间: B-REF-3 完成后
> 当前基线: 1117 passed, 2 skipped
> 已完成 B-REF: 1 (渐进加载), 2 (描述质量), 3 (内部组织)

## 对比表

| # | 方向 | 领域 | Scope | 类型 | 前置依赖 | 来源 |
|---|------|------|-------|------|---------|------|
| B-REF-4 | Permission policy 分层覆盖 | 权限/安全 | 大 | 实现 | 需新子系统 | Claude permission policies |
| B-REF-5 | 工作流中断原语 | Workflow 引擎 | 中 | 实现 | Pipeline 已稳定 | Claude user.interrupt |
| B-REF-6 | 子 agent 上下文隔离评估 | 多 agent | 中 | 评估/文档 | Subagent delegation 已存在 | Claude multi-agent |
| B-REF-7 | Custom tool surface 合并审计 | MCP 接口 | 小 | 审计/文档 | MCP server 已有 11+ tools | Claude best practices |
| 候选 B | HTTPWorker failure fallback | Worker/Subagent | 小 | 实现 | HTTPWorker + schema 已存在 | direction-candidates |
| 外部 | Plugin distribution/marketplace | 分发/生态 | 大 | 规划/实现 | Dual-Package Standard 已有 | plugin-distribution analysis |
| 外部 | Hierarchical pack topology | Pack 系统 | 中 | 实现 | PackTree 单层已有 | hierarchical-pack analysis |

## 象限分析

### 高价值 + 小 scope（1 切片可完成）
- **B-REF-7**: tool surface 审计 — 审计现有 MCP tools，给出合并建议。跨领域，不再深入 Pack
- **候选 B**: HTTPWorker failure fallback — Worker 领域，schema 对齐，scope 极窄

### 高价值 + 中 scope（需 2+ 切片）
- **B-REF-5**: 中断原语 — 解决 workflow 引擎的核心缺口
- **B-REF-6**: 上下文隔离评估 — 多 agent 架构的关键评审

### 高价值 + 大 scope（需独立规划）
- **B-REF-4**: Permission policy — 安全基础设施，全新子系统

### 中价值 + 大 scope（不紧急）
- Plugin distribution — 生态建设
- Hierarchical topology — Pack 系统继续深入

## AI 倾向

本次会话已连续完成 3 个 Pack 质量 B-REF (1/2/3)。如果继续：
- B-REF-7 或候选 B 是跨领域、scope 最小的选项
- 如果想完全离开 Pack 系统，候选 B (Worker 领域) 是最佳选择
- 如果想做审计型工作（轻量输出），B-REF-7 最合适
- 本次也是很好的 safe-stop 边界（+125 tests, 6 切片）
