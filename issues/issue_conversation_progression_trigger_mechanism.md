# Issue: 对话推进规则触发机制设计缺陷 — 需要 runtime 化或末端注入

## 背景

在实际使用中，对话推进规则（conversation progression contract）被反复违反——即使规则已写入 `copilot-instructions.md`、`AGENTS.md`、pack rules、reference 文档四个载体。

## 问题分析

根因并非规则措辞不清，而是**规则放置位置与约束触发时机存在 positional decay 错配**：

1. **位置 vs 时机**：规则在 system prompt 最前端一次性加载，但约束的是每条回复的最后一段——到生成末尾时，规则已被工具调用和中间分析推到 context window 远端
2. **缺少 runtime 触发**：项目状态约束有 `check_constraints` 做机器检查，但对话行为约束是纯 instruction-layer，没有回复边界的触发钩子
3. **负面 vs 正面**：原规则以"禁止 X"为主，缺少"必须做成 Y 的样子"的正面模板引导

## 已实施的短期改进（2026-04-15）

- A+C 路径：将规则从负面禁止改写为**正面模板 + 发送前检查清单**
- 更新了 `.github/copilot-instructions.md`（主载体）、`AGENTS.md`（副本 ×2）、`doc-loop-vibe-coding/references/conversation-progression.md`（reference）

## 长期改进方向（插件化之前考虑）

### B. Runtime 工具化

新增 `check_reply_progression` 工具，在回复发出前对文本做格式检查：
- 检测末尾是否为推进式提问
- 检测是否包含 AI 自身分析
- 作为 machine-checked 约束而非 instruction-layer 约束

### D. 末端位置注入

在 instructions generator 中把关键行为约束同时放在 prompt 尾部（靠近生成区），直接对抗 positional decay。

### 更远期

- 与依赖图谱（FR-1/FR-2）的变更钩子机制统一——对话行为规则也可以被建模为一种"耦合约束"，在特定触发条件下被钩起

## 状态

- 创建日期: 2026-04-15
- 状态: `open`
- 优先级: 中（影响每次对话的行为质量，但已有短期缓解）
- 标签: `conversation-progression`, `rule-enforcement`, `long-term`
