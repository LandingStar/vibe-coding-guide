# Copilot Workspace Instructions

本项目是一个**协议/治理驱动工作流平台**（doc-based-coding-platform）。

## 权威文档分层

- `docs/` — 当前仓库关于平台与官方实例定位的最高权威来源
- `design_docs/Project Master Checklist.md` — 状态板与协作恢复入口
- `design_docs/Global Phase Map and Current Position.md` — 当前阶段口径
- `design_docs/stages/` — planning-gate、phase doc
- `design_docs/tooling/` — 长期有效的协议与标准
- `.codex/handoffs/CURRENT.md` — 安全停点交接入口
- `.codex/prompts/doc-loop/` — 可复用提示词

若 `docs/` 与 `design_docs/` 冲突，以 `docs/` 为准。

## 开发闭环

1. 从现有文档恢复上下文
2. 生成或刷新一个窄 scope planning-gate 文档
3. 只按该文档实施当前切片
4. 通过验证门
5. 回写状态板、阶段文档、协议文档与 handoff

## 核心约束

- 在没有窄 scope 文档前，不进入大规模实现
- 代码、测试、帮助和文档更新必须对应同一个当前切片
- 若发现新问题超出当前切片，先写回 planning-gate，而不是就地扩 scope
- 安全停点下，允许 model 主动执行 handoff 构建；handoff 分支内若未返回 `blocked`，不应因缺少额外 slash 或重复授权而停下
- 重要设计节点必须先交用户审核，再进入下一大步
- 主 agent 负责权威文档、集成和最终 write-back
- 子 agent 只处理被明确写入合同的窄切片
- 共享状态文档默认不交给子 agent 直接维护

## 对话行为约束（上下文压缩后仍必须遵守）

以下规则**始终有效**，不因 conversation history 被压缩而失效：

- **未经用户显式许可，禁止主动终止对话**：每条回复必须以推进式提问结尾——即带有 AI 自身分析/推荐/判断的提问，而不是单纯列选项等用户选。"你是否希望 X？""请选择方向" 都算终止。正确做法是 AI 先给出自己的分析和倾向判断，再以 askQuestions 工具向用户确认。Phase 完成后尤其如此——应主动准备下一步分析文档并提问，不得停下等待。只有当用户明确表示允许结束、暂停，或明确要求本轮不要继续追问时，才可不以推进式提问结尾。
- **用户选择/审批必须以提问推进**：如果当前节点需要用户做选择、审批、方向确认或下一步取舍，AI 必须先给出自己的分析、推荐或倾向判断，再用提问继续交流；需要结构化确认时，必须优先使用 askQuestions，而不是把“请你自己选”包装成收尾。
- **方向选择必须文档化**：提供候选方向时，每个候选项必须引用具体的设计文档或权威文档作为依据，不得仅靠口头描述。
- **Phase 完成后自动推进**：当一个 Phase 的 write-back 完成后，应主动准备下一步的分析和候选方向文档，然后以提问方式与用户讨论，而不是停下来等待。
- **上下文恢复优先读文档**：若发现自身对当前项目状态的记忆不完整（如从压缩后的 summary 恢复），应先重新读取关键状态文档（Checklist、Phase Map、CURRENT.md），再继续工作。
- **候选方向的来源**：Phase 完成后的候选方向应从以下来源提取，而非凭空生成：
  - `design_docs/Project Master Checklist.md` 的待办与风险
  - `docs/` 权威文档中标记的未实现能力
  - `review/research-compass.md` 中的借鉴点
  - 当前 Phase 实施过程中发现的新需求
