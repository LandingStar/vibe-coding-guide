# AGENTS

本项目默认采用基于文档闭环的开发流程。

开始工作前，先读：

1. `docs/README.md`（若项目携带平台权威文档）
2. `design_docs/Project Master Checklist.md`
3. `design_docs/Global Phase Map and Current Position.md`
4. 当前 active planning 或 phase 文档
5. 相关的 `design_docs/tooling/` 长期协议

若 `docs/` 与 `design_docs/` 冲突，以 `docs/` 为准。

执行规则：

- 在没有窄 scope 文档前，不进入大规模实现。
- 代码、测试、帮助和文档更新必须对应同一个当前切片。
- 若发现新问题超出当前切片，先写回 planning-gate，而不是就地扩 scope。
- 只有在安全停点才刷新 `.codex/handoffs/CURRENT.md`。
- 安全停点下，允许 model 主动进入 handoff 分支；handoff 分支内只有 `blocked` 是自动停止信号。

子 agent 规则：

- 主 agent 负责权威文档、集成和最终 write-back。
- 子 agent 只处理被明确写入合同的窄切片。
- 共享状态文档默认不交给子 agent 直接维护。

对话行为约束（始终有效，不因上下文压缩而失效）：

每条回复末尾的正面模板：`[AI 的分析/判断/倾向] → [基于该分析的推进式提问（askQuestions）]`。发送前检查：(1) 末尾有 AI 自身分析？(2) 以推进式提问收尾？(3) 提问推进工作而非等待许可？(4) 方向引用了文档？(5) 提问前是否给出了当前最相关文档的可跳转链接？任一项不满足则重组末尾。

- 禁止的结尾模式：纯 yes/no 确认、被动等待、纯选项列举、无提问的总结。审批/确认节点不构成停止理由——应在审批提问中同时推进下一个具体设计/实施问题。
- 若当前节点需要用户做选择、审批、方向确认或下一步取舍，必须先给出 AI 自身的分析与推荐，再用 askQuestions 或明确提问继续推进；不要把“请用户自己选”包装成收尾。
- 每次提问前，应先给出当前最相关的文档链接，便于用户直接跳转审核；若提问依赖 planning-gate、direction-analysis、review 文档或权威文档，至少链接其中最关键的入口。
- Phase 完成后自动准备下一步分析文档并以 askQuestions 提问，不得停下等待。
- 候选方向必须引用具体文档作为依据。
- 若对项目状态记忆不完整，应先重读 Checklist / Phase Map / CURRENT.md。
