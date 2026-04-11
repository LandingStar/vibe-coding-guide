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

- 未经用户显式许可，禁止主动终止对话。每条回复必须以推进式提问结尾——带有 AI 自身分析和倾向判断的提问，而不是列选项等用户选。只有当用户明确表示允许结束、暂停，或明确要求本轮不要继续追问时，才可不以推进式提问结尾。
- 若当前节点需要用户做选择、审批、方向确认或下一步取舍，必须先给出 AI 自身的分析与推荐，再用 askQuestions 或明确提问继续推进；不要把“请用户自己选”包装成收尾。
- Phase 完成后自动准备下一步分析文档并以 askQuestions 提问，不得停下等待。
- 候选方向必须引用具体文档作为依据。
- 若对项目状态记忆不完整，应先重读 Checklist / Phase Map / CURRENT.md。
