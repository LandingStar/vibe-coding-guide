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

子 agent 规则：

- 主 agent 负责权威文档、集成和最终 write-back。
- 子 agent 只处理被明确写入合同的窄切片。
- 共享状态文档默认不交给子 agent 直接维护。
