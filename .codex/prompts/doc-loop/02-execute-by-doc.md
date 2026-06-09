# Execute By Doc Prompt

Local Work Trajectory note: for task-like implementation, validation, review, or write-back work, proactively maintain Local Work Trajectory as agent-owned state. Use `localTrajectory start` when beginning a tracked task with no active trajectory, `append` for meaningful milestones, and `advance` when the active milestone is complete. Use `addLane`, `merge`, and `relate` only for explicit work-context split, fan-in, or relation metadata. If `localTrajectory` is expected but missing, report the MCP/tool exposure problem explicitly and do not ask the user to manually maintain trajectory nodes. Do not record MCP path or host-environment configuration checks into Local Work Trajectory unless the user explicitly asks to track that environment task.

Progression note: when implementation needs user choice, review approval, direction confirmation, or next-step tradeoff, state the current AI analysis/recommendation first, then continue with an explicit forward-driving question.

先读当前 active planning 或 phase 文档，再开始实现。

实施要求：

- 只处理文档声明的当前切片
- 若发现新问题超出当前边界，写回 open items 或 planning-gate
- 代码、测试、帮助、文档同步必须围绕同一个切片
- 优先复用已确认可直接依赖的文档控制面，而不是把它们留到事后补记
- 对 Pipeline / CLI / MCP / Instructions 等 pre-release 运行时入口，只有在 planning doc 明确写入时才作为 dogfood / verification 使用，不要默认把它们当成唯一主路径
- 若 `analyze_changes` 或 `impact_analysis` 报告缺少 `baseline_graph.json`，将其视为依赖传播分析不可用的降级状态；除非当前切片明确要求创建或维护 dependency baseline，否则不要临时伪造或手写 baseline
- 若当前切片确实要求创建、刷新或维护 dependency baseline，先使用 `.codex/prompts/doc-loop/05-dependency-baseline.md` 的专项规则
- 不要把未验证内容写成完成

若实施途中需要用户做选择、审批、方向确认或下一步取舍：

- 先陈述你当前的分析与推荐

完成后请准备 write-back，而不是只给口头总结。
