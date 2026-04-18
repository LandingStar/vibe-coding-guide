# VibeCoding-Workflow 分析

## 来源

- 仓库：[Sakura1618/VibeCoding-Workflow](https://github.com/Sakura1618/VibeCoding-Workflow)
- 博客：[人类主导的半自动 Vibe-coding 工作流](https://blog.sakurax.top/人类主导的半自动-vibe-coding-工作流/)
- 发现日期：2026-04-15
- 状态：**详细分析完成**

## 项目概述

一套面向 RooCode 的仓库级工作流模板，目标是降低 AI 多切片持续开发时的"做完就停"问题。

### 核心思路

三件事：
1. 让 AI 不因小切片完成就停
2. 让活跃任务池只保留该做的
3. 下次会话从明确恢复点接着跑

### 三个角色

| 角色 | 职责 | 对应我们平台的概念 |
|------|------|-------------------|
| Autonomous Orchestrator | 父调度器：选切片、派发、验收、更新状态、自动继续 | 主 agent + driver |
| Slice Executor | 单切片执行者：最小正确实现、验证、自修复 | 子 agent |
| Milestone Reviewer | 阶段复盘：不做功能、只做重规划 | checkpoint + direction-candidates |

### 五份文档

| 文档 | 职责 | 对应我们平台的概念 |
|------|------|-------------------|
| `AGENTS.md` | 长期规则 | `.github/copilot-instructions.md` + pack 规则 |
| `docs/ROADMAP.md` | 长期里程碑 | `design_docs/Global Phase Map` |
| `docs/WORK_QUEUE.md` | 当前活跃任务池 | `Project Master Checklist` 活跃待办 |
| `docs/SESSION_STATE.md` | 恢复点 | `.codex/handoffs/CURRENT.md` |
| `docs/DONE.md` | 已闭环记录 | `design_docs/phase-0-26-review.md` + 已勾选待办 |

## 初步与本平台的对比

### 共同解决的问题
- "做完一个小切片就停下来等确认"
- 上下文跑偏 / 重复审仓
- Backlog / 状态 / 路线混杂
- 切片间缺少衔接

### 关键差异

| 维度 | VibeCoding-Workflow | 本平台 |
|------|-------|-------|
| 客户端 | RooCode（3 自定义模式） | VS Code Copilot（MCP + AGENTS.md + instructions） |
| 执行层 | 纯提示词/规则层 | 运行时 PDP/PEP + check_constraints + MCP 工具链 |
| 状态管理 | 5 文件扁平结构 | 分层权威文档 + planning-gate + checkpoint + handoff |
| 治理验证 | 无机器可审计层 | C1-C8 约束 + validator/check 框架 + 审计日志 |
| 防漂移 | Anti-Drift Rules（9 条显式规则） | pack 规则 + conversation-progression + completion-boundary |
| 持续推进 | Run Budget（默认连续 3 切片）| get_next_action + 完成边界协议 |
| 复杂度 | 轻量模板（~10 文件） | 完整平台（70+ .py + 30+ docs） |

### 值得借鉴的模式

1. **Run Budget（连续推进预算）**：默认连续推 3 个切片再触发复盘机制。我们的 `get_next_action` 完成了类似功能但没有显式的"预算"概念。
2. **Forbidden Stop Patterns 显式列表**：直接列举 4 种禁止的停止文案模板 — 与我们的正面模板互补。
3. **Milestone Reviewer 独立角色化**：专门用于"不做功能、只做重规划"— 我们用 checkpoint + direction-candidates 实现但没有角色化。
4. **文档职责严格单一**：每份文档只做一件事，交叉引用但不交叉内容。
5. **Anti-Drift 规则的系统性**：9 条规则覆盖了重复审仓、盲补丁、假进展、美化重构等多种漂移场景。

## 详细分析：逐条模式映射

### 1. Run Budget vs get_next_action / completion-boundary

**VibeCoding-Workflow**：Continuous Run Budget — 一次父任务默认连续推进最多 3 个已完成切片，或直到达到里程碑子目标，或触发停止/重规划条件。完成一个切片后默认自动进入下一切片。

**本平台**：
- `completion_boundary_protocol`（C3 + pack rules）：当所有 todo 完成且无活跃 planning-gate 时，强制调用 `get_next_action` MCP 工具获取下一步推荐，再组装 forward question。
- `get_next_action` 返回结果：有活跃 gate → 继续做；无 gate → 读 Checklist/Phase Map 选方向。
- **无显式"预算"概念**：我们只防"停下来等确认"，不控制"连续做几个切片后必须触发复盘"。

**差异分析**：

| 维度 | VibeCoding-Workflow | 本平台 | 评估 |
|------|-------|-------|------|
| 防止做完就停 | ✅ Run Budget + Forbidden Stop | ✅ completion-boundary + C1/C3 | 功能等价 |
| 连续推进上限 | ✅ 3 切片后触发复盘 | ❌ 无上限 | 可借鉴 |
| 复盘触发机制 | ✅ Milestone Replan Triggers（7 条） | ⚠ 只在 phase 完成后才生成 direction-candidates | 可借鉴 |
| 下一切片选择 | ✅ 7 条优先级规则 | ⚠ 委托给 get_next_action + 用户 | 互补 |

**采纳建议**：引入"连续切片计数"概念到 pack rules 中——连续完成 N 个切片后触发一次 mini-review（检查是否漂移、是否需要重规划），N 可配置（默认 3）。不需要运行时实现，只需在 pack rules 中增加一条 `slice_budget` 约束。

### 2. Anti-Drift Rules 覆盖度对比

**VibeCoding-Workflow 的 8 条 Anti-Drift 规则**：

| # | 规则 | 本平台是否覆盖 | 覆盖方式 |
|---|------|------------|---------|
| 1 | 不得在无新证据情况下重复完整审仓 | ⚠ 无显式规则 | 仅靠 C4 上下文恢复优先读文档间接覆盖 |
| 2 | 同一问题连续两次修复未缩小失败面 → 必须切换策略 | ❌ 未覆盖 | — |
| 3 | 同一文件/报错反复改动两轮无改善 → 回到根因分析 | ❌ 未覆盖 | — |
| 4 | 不得把重写计划/总结/todo 当作代码进展替代品 | ❌ 未覆盖 | — |
| 5 | 不得重新打开已闭环切片（除非有新证据） | ✅ gate DONE 后不可回退 | Gate 状态机隐含 |
| 6 | 主链未闭环时不做锦上添花型任务 | ⚠ C5/C6 部分覆盖 | 要求先有 planning-gate，但不禁止在 gate 内做额外美化 |
| 7 | 不得为通过测试删除测试/日志/错误处理 | ❌ 未覆盖 | — |
| 8 | 不得把临时 workaround 叙述为正式完成方案 | ❌ 未覆盖 | — |

**覆盖度**：2/8 直接覆盖，2/8 部分覆盖，4/8 完全缺失。

**采纳建议**：将 #2、#3、#4、#7、#8 作为新的 pack rules 条目（severity: warn）加入 `project-local.pack.json`。建议编号为 AD-1 到 AD-5（Anti-Drift 规则组）。这些规则不需要运行时实现，纯规则/提示词层即可生效。

### 3. Forbidden Stop Patterns vs C1 正面模板

**VibeCoding-Workflow 的 4 条 Forbidden Stop**：
1. "我已经完成当前最小切片，请告诉我下一步"
2. "下面有两个方案，请选择"
3. "是否继续下一阶段？"
4. "我建议先到这里，等你确认后再继续"

**本平台 C1**：仅用正面模板（"每条回复以推进式提问结尾"）+ Pre-Send Checklist 4 项，不显式列出禁止文案。

**差异分析**：正面模板覆盖了所有 4 种禁止模式的语义，但**负面示例更容易被 LLM 精确匹配**。我们曾经在早期使用了负面列表但改为正面模板（因为负面列表导致了更频繁的违规）。

**采纳建议**：**不采纳**。经验证据表明正面模板 + checklist 比负面列表更有效（本轮开发中正面模板的违规率明显更低）。保留现有策略。

### 4. Milestone Reviewer vs checkpoint + direction-candidates

**VibeCoding-Workflow**：独立角色 `Milestone Reviewer`，7 条触发条件，不做功能只做重规划。

**本平台**：
- checkpoint 机制（`tools/checkpoint/`）
- direction-candidates 文档（`design_docs/direction-candidates-after-phase-*.md`）
- Phase Map 更新
- 无独立角色，由主 agent 在 phase 完成后执行

**差异分析**：VibeCoding-Workflow 将复盘**角色化**（独立模式），而我们将其**流程化**（phase 完成后的固定步骤）。角色化的优势是强制上下文切换（防止"既做功能又做设计"时的漂移），但 VS Code Copilot 不原生支持自定义模式切换。

**采纳建议**：不引入独立角色（客户端限制），但可以将 Milestone Replan 的 **7 条触发条件**吸收为 pack rules 中的"复盘触发规则组"，在满足任一条件时强制执行 direction-candidates 生成。

### 5. WORK_QUEUE "唯一活跃入口" vs Checklist

**VibeCoding-Workflow**：`docs/WORK_QUEUE.md` 是唯一任务来源，任何新任务必须先进入此文件。不允许从其他文档直接取任务。

**本平台**：`Project Master Checklist` 是状态板，但任务来源分散在 Checklist 待办、planning-gate、direction-candidates、issues/ 等多处。`get_next_action` 会读多个来源。

**差异分析**：单一入口简洁但不适合我们的分层文档架构。我们的 planning-gate 机制天然要求多层文档。

**采纳建议**：**不采纳**统一为单一入口。但可以增强 `get_next_action` 的来源扫描——确保它覆盖 issues/、direction-candidates、Checklist 三个来源。

### 6. Slice Rules 结构化对比

**VibeCoding-Workflow**：每个切片必须包含 9 项（目标、非目标、主要范围、允许改动、禁止改动、完成标准、验证命令、已知风险、推荐下一片）。

**本平台**：planning-gate 包含问题陈述、目标（做/不做）、验证门、风险、后续切片预览。

| 字段 | VCW | 本平台 | 差异 |
|------|-----|--------|------|
| 目标 | ✅ | ✅ 目标/做 | 等价 |
| 非目标 | ✅ | ✅ 不做 | 等价 |
| 范围 | ✅ | ✅ Gate scope | 等价 |
| 允许改动 | ✅ | ❌ 未显式列出 | 可借鉴 |
| 禁止改动 | ✅ | ❌ 未显式列出 | 可借鉴 |
| 完成标准 | ✅ | ✅ 验证门 | 等价 |
| 验证命令 | ✅ | ⚠ 隐含在测试基线 | 可加显式 |
| 已知风险 | ✅ | ✅ 风险 | 等价 |
| 推荐下一片 | ✅ | ✅ 后续切片预览 | 等价 |

**采纳建议**：在 planning-gate 模板中增加"允许改动"和"禁止改动"两个可选字段。不强制但鼓励在高风险切片中使用。

---

## 详细分析：博客"半自动 Vibe-coding 工作流"

### 背景

这篇博客是 VibeCoding-Workflow 仓库的前置文章，描述了 Sakura1618 在引入结构化工作流模板**之前**的半自动开发方式。

### 工具链

| 工具 | 功能 |
|------|------|
| OpenCode Desktop | 图形化 AI 编码工作台（会话管理、MCP、LSP、多代理并行） |
| OMO (oh-my-openagent) | 多 Agent 编排框架：自动拆解任务、并行执行 |
| RTK (Rust Token Killer) | Token 压缩工具（平均 60-90% 降幅） |

### 工作流程

1. **触发**：`ulw` + 一句话自然语言 → OMO 自动拆解为子任务
2. **执行**：并行 Agent 研究文档/搜索代码/写代码；RTK 压缩输出
3. **人类检查点**：只看 Git Changes 面板，快速扫文件列表 + 核心 Diff
4. **纠正**：在 Diff 视图 revert hunk 或对话提示修正
5. **收尾**：OMO 自我纠错、跑测试、生成 Commit Message

### 作者自评的局限

> "这套工作流还不能很省心（会遇到卡切片、偏离开发路线），这套工作流没有长期约束和任务自驱。"

这正是后续 VibeCoding-Workflow 仓库试图解决的问题——通过结构化文档和规则提供"长期约束和任务自驱"。

### 详细分析：半自动→全自动演进路径

**Sakura1618 的演进轨迹**：
1. **阶段 A（半自动）**：OpenCode + OMO + RTK — 强工具、弱规则。人类通过 Git Changes 做 review，每步都手动确认。
2. **阶段 B（全自动）**：VibeCoding-Workflow — 弱工具（纯 Roo Code）、强规则。通过结构化文档 + 角色 + 规则让 AI 自驱。
3. **关键转折**：作者发现"工具层的并行和压缩不够"——缺的是长期约束和任务自驱。

**本平台的演进轨迹**：
1. **阶段 A**：doc-loop 概念验证 → planning-gate + checkpoint 文档管理
2. **阶段 B**：pack 规则 + C1-C8 约束 + conversation-progression
3. **阶段 C**：PDP/PEP runtime + MCP 工具链 + 可审计治理

**交叉验证**：Sakura1618 从 A→B 的跳跃点正是我们平台在阶段 B 已经解决的问题（结构化规则+自驱），但我们额外走到了阶段 C（运行时可审计），这是 VibeCoding-Workflow 目前缺失的。这验证了我们平台的定位差异是有意义的。

### OMO 并行 Agent 参考价值

OMO 支持多 Agent 并行执行子任务——我们当前的子 agent 是串行的（主 agent 一次只派一个子 agent）。

**评估**：
- 并行价值：读取/搜索类任务天然可并行（Explore agent 已支持），但写入任务并行需要解决文件冲突
- 我们的 `src/pep/executor.py` 支持 `SubgraphMode`（已有骨架），但实际运行仍是串行
- 并行化是 runtime 层面的能力，不是规则层可解决的

**结论**：并行子 agent 是有价值的 future direction，但超出当前 dogfood 阶段。已有 `SubgraphMode` 骨架可在未来扩展。不在当前切片引入。

### RTK Token 压缩借鉴

RTK (Rust Token Killer) 实现 60-90% 的 token 压缩，主要用于命令输出。

**本平台现有**：`_summarize_content()` 做粗糙的内容截断（非压缩），`PackContext` 的 `context_budget` 控制注入量。

**评估**：
- Token 压缩是实用工具方向，但我们的瓶颈不在 token 量（MCP context 构建已有预算控制）
- RTK 是独立二进制工具，不适合直接集成
- 更有价值的是"智能摘要"而非"机械压缩"

**结论**：记录为参考方向，不采纳为当前切片。如果未来 context 预算成为瓶颈，可考虑引入摘要增强。

### Git Changes 人类检查点 vs Review 状态机

**Sakura1618 的做法**：人类在 Git Changes 面板快速扫文件列表，只看关键 Diff。效率极高但完全依赖人类判断。

**本平台**：Review 状态机 → Notifier → FeedbackAPI → 人类异步审核。流程完整但重量级。

**差异**：两者解决的是不同层次的 review 问题。Git Changes 适合"当前切片的代码变更审查"，Review 状态机适合"跨切片的设计审批和治理审查"。两者互补而非冲突。

**结论**：不需要改变现有机制。Git Changes 是 IDE 原生能力，本来就是开发者自然使用的。

---

## 延伸方向：review other's work 标准流程组件

从对这两个资源的分析流程中，可以提炼出一个通用的"外部项目/资源分析"标准流程组件：

1. **快速概览**：README + 仓库结构 → 初步定位
2. **核心对比**：与本平台在角色、文档、执行机制、治理层的结构化对比
3. **借鉴点提取**：每个借鉴点标注"值得引入"/"仅参考"/"不适用"
4. **差异分析**：对方缺失什么、我们缺失什么
5. **行动项生成**：从借鉴点到具体 issue / planning-gate 的转化

这个流程未来可以组件化为一个标准 review 模板或工具，降低分析外部项目时的重复劳动。待后续设计开发。

---

## 综合采纳决策汇总

| # | 建议 | 决策 | 理由 | 优先级 |
|---|------|------|------|--------|
| A1 | 引入 slice_budget 连续切片计数 | ✅ 采纳 | 防止长连续施工漂移 | 低 |
| A2 | Anti-Drift 规则 AD-1~AD-5 加入 pack rules | ✅ 采纳 | 覆盖 4 个完全缺失场景 | 中 |
| A3 | Milestone Replan 7 条触发条件 → pack rules | ✅ 采纳 | 增强复盘触发系统性 | 低 |
| A4 | planning-gate 增加"允许/禁止改动"字段 | ✅ 采纳 | 提升切片边界明确性 | 低 |
| A5 | Forbidden Stop 负面列表 | ❌ 不采纳 | 正面模板已验证更有效 | — |
| A6 | WORK_QUEUE 唯一入口模式 | ❌ 不采纳 | 不适合分层文档架构 | — |
| A7 | 独立 Milestone Reviewer 角色 | ❌ 不采纳 | 客户端不支持模式切换 | — |
| A8 | OMO 并行子 agent | 📋 记录 | 有价值但超出当前阶段 | 未来 |
| A9 | RTK Token 压缩 | 📋 记录 | 当前非瓶颈 | 未来 |

**立即可执行（纯规则层，不需要代码改动）**：A1、A2、A3 → 修改 pack rules JSON
**下次 planning-gate 时纳入**：A4 → 修改 gate 模板
