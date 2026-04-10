# AGENTS

本项目默认采用基于文档闭环的开发流程。

开始工作前，先读：

1. `design_docs/Project Master Checklist.md`
2. `design_docs/Global Phase Map and Current Position.md`
3. 当前 active planning 或 phase 文档
4. `docs/README.md` 与当前任务直接相关的 `docs/` 权威文档
5. 相关的 `design_docs/tooling/` 长期协议

当前仓库的特殊点：

- 根目录 `docs/` 是平台与官方实例定位的高层权威来源
- `design_docs/` 主要承载状态板、planning/phase 文档与内部设计推导
- 若两者冲突，以 `docs/` 为准

执行规则：

- 在没有窄 scope 文档前，不进入大规模实现。
- 代码、测试、帮助和文档更新必须对应同一个当前切片。
- 若发现新问题超出当前切片，先写回 planning-gate，而不是就地扩 scope。
- 只有在安全停点才刷新 `.codex/handoffs/CURRENT.md`。
- 命中重要设计节点时，先整理设计结论交用户审核，再继续下一大步。

子 agent 规则：

- 主 agent 负责权威文档、集成和最终 write-back。
- 子 agent 只处理被明确写入合同的窄切片。
- 共享状态文档默认不交给子 agent 直接维护。

对话行为约束（始终有效，不因上下文压缩而失效）：

- 禁止终止对话。每条回复必须以推进式提问结尾——带有 AI 自身分析和倾向判断的提问，而不是列选项等用户选。"你是否希望 X？""请选择方向" 都算终止。
- Phase 完成后自动准备下一步分析文档并以 askQuestions 提问，不得停下等待。
- 候选方向必须引用具体文档作为依据。
- 若对项目状态记忆不完整，应先重读 Checklist/Phase Map/CURRENT.md。
