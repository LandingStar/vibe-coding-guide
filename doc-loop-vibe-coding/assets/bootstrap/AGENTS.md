# AGENTS

## Local Work Trajectory

- Task-like implementation, validation, review, and write-back work must be reflected in Local Work Trajectory by the agent, not by the user.
- Before substantial task work begins, judge whether the task is large enough or split-worthy enough to need distinct Local Work lanes. If yes or uncertain, follow `design_docs/tooling/local-work-lane-splitting/README.md`; keep detailed lane split criteria there, not in this file.
- Direct `localTrajectory` mutation is leader/main/supervisor authority. Bounded workers/subagents must not call `localTrajectory` directly; they must put trajectory/status suggestions in their `Subagent Report.trajectory_update`, and the leader/main agent consumes the report before mutating Local Work Trajectory. Worker report procedure: `docs/worker-trajectory-update-reporting.md`.
- When MCP exposes `localTrajectory` to a leader/main/supervisor, use it proactively: `start` when beginning a tracked task with no active trajectory, `append` for meaningful milestones, `advance` when the active milestone is complete, `addLane` only for a distinct work context, `merge` only for explicit fan-in, and `relate` only for visible relation metadata.
- Do not wait for a user instruction such as "start trajectory"; do not ask the user to manually create trajectory nodes.
- If `localTrajectory` is expected but unavailable, report the MCP/tool exposure problem explicitly. Use the repository-local trajectory API only when the current project rules allow local file mutation.
- MCP path or host-environment configuration checks are not project work and must not be recorded into Local Work Trajectory unless the user explicitly says to track that environment task.

本项目默认采用基于文档闭环的开发流程。

开始工作前，先读：

1. `docs/README.md`（若项目携带平台权威文档）
2. `design_docs/Project Master Checklist.md`（短热状态入口）
3. Checklist 的 `Current Recovery Read Order` 指向的最新 closure/gate/review 文档
4. `design_docs/Global Phase Map and Current Position.md`
5. 当前 active planning 或 phase 文档
6. 相关的 `design_docs/tooling/` 长期协议

`.codex/checkpoints/latest.md` 与 `.codex/handoffs/CURRENT.md` 是恢复安全停点或停放分支的辅助入口；只有当 Checklist 指向它们、用户要求恢复对应分支，或需要核对 safe-stop/handoff footprint 时才默认读取。不要让旧 checkpoint/handoff 覆盖 Checklist 中更新的当前焦点。

若 `docs/` 与 `design_docs/` 冲突，以 `docs/` 为准。

执行规则：

- 在没有窄 scope 文档前，不进入大规模实现。
- 代码、测试、帮助和文档更新必须对应同一个当前切片。
- 若发现新问题超出当前切片，先写回 planning-gate，而不是就地扩 scope。
- 只有在安全停点才刷新 `.codex/handoffs/CURRENT.md`。
- 安全停点下，允许 model 主动进入 handoff 分支；handoff 分支内只有 `blocked` 是自动停止信号。

Dependency baseline 规则：

- `tools/dependency_graph/baseline_graph.json` 是可选的工作区本地依赖传播快照；初始化工作区时默认不创建它。
- 若 `analyze_changes` / `impact_analysis` 报告 baseline 缺失，按“影响传播不可用、耦合检查仍可继续”的降级状态处理。
- 普通实现任务中不要为了消除提示而手写或伪造 baseline。
- 只有当前切片明确要求创建、刷新或维护 dependency baseline 时，才使用 `.codex/prompts/doc-loop/05-dependency-baseline.md` 的专项提示词；若目标工作区没有可复现生成器，应先写 planning-gate 或需求说明。

子 agent 规则：

- 主 agent 负责权威文档、集成和最终 write-back。
- 子 agent 只处理被明确写入合同的窄切片。
- 共享状态文档默认不交给子 agent 直接维护。
- 子 agent / worker 不直接维护 Local Work Trajectory；其进度、阻塞、完成和建议推进动作必须写入 `Subagent Report.trajectory_update`，由主 agent / leader 审核后执行 `localTrajectory`。固定流程文档：`docs/worker-trajectory-update-reporting.md`。

对话行为约束（始终有效，不因上下文压缩而失效）：

每条回复末尾的正面模板：`[AI 的分析/判断/倾向] → [基于该分析的推进式提问]`。发送前检查：(1) 末尾有 AI 自身分析？(2) 以推进式提问收尾？(3) 提问推进工作而非等待许可？(4) 方向引用了文档？(5) 提问前是否给出了当前最相关文档的可跳转链接？任一项不满足则重组末尾。

- 禁止的结尾模式：纯 yes/no 确认、被动等待、纯选项列举、无提问的总结。审批/确认节点不构成停止理由——应在审批提问中同时推进下一个具体设计/实施问题。
- 若当前节点需要用户做选择、审批、方向确认或下一步取舍，必须先给出 AI 自身的分析与推荐，再用明确的推进式提问继续推进；不要把“请用户自己选”包装成收尾。
- 每次提问前，应先给出当前最相关的文档链接，便于用户直接跳转审核；若提问依赖 planning-gate、direction-analysis、review 文档或权威文档，至少链接其中最关键的入口。
- Phase 完成后自动准备下一步分析文档并以推进式提问继续交流，不得停下等待。
- 候选方向必须引用具体文档作为依据。
- 若对项目状态记忆不完整，应先重读 Checklist 及其 `Current Recovery Read Order` 指向的文档；只有在 Checklist 指向 handoff/checkpoint 或需要恢复安全停点时才读 CURRENT.md / checkpoint。
