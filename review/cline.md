# Cline (cline/cline) 分析

## 来源

- 仓库/URL：https://github.com/cline/cline
- 发现日期：2026-04-21
- 状态：**详细分析完成**

## 项目概述

Cline 是目前社区最活跃的 AI 编程助手 VS Code 扩展之一。核心定位是"自主编码代理"——用户用自然语言描述任务，Cline 通过工具链（文件读写、终端命令、浏览器操作、MCP 服务器调用）自主完成实现。

关键特性：

- **VS Code 扩展 + CLI 双端运行**：VS Code 侧为 Webview（React）+ gRPC/Protobus 通信；CLI 侧为 React Ink TUI，复用核心逻辑
- **Plan / Act 双模式**：Plan 模式只读探索，Act 模式执行变更；支持按模式配置不同 LLM
- **多层规则体系**：`.clinerules/`（workspace）+ 全局 Rules + `.cursorrules` / `.windsurfrules` / `AGENTS.md` 自动检测 + Enterprise Remote Rules
- **Skills**：按需加载的领域专家指令集，通过 `use_skill` 工具触发
- **Workflows**：可复用的多步骤自动化流程，通过 `/workflow.md` 调用
- **Hooks**：可编程生命周期钩子（PreToolUse / PostToolUse / TaskStart / TaskResume / Notification）
- **Auto-Approve 体系**：按操作类型细粒度审批（读文件 / 编辑文件 / 安全命令 / 所有命令 / 浏览器 / MCP）+ YOLO 全自动模式
- **MCP 集成**：McpHub 管理连接、MCP Marketplace 一键安装、Per-tool auto-approve
- **Checkpoints**：文件快照 + 回滚能力
- **Memory Bank**：基于 `.clinerules` 的自定义上下文持久化模式（custom instructions pattern，非内建功能）

## 结构化对比

| 维度 | Cline | 本平台 (doc-based-coding) |
|------|-------|--------------------------|
| **角色划分** | 单一 AI Agent + 人类用户；无显式子 Agent 治理协议（有 subagent 工具但无 supervisor/worker 协议） | 主 Agent + 子 Agent 分层；主 Agent 负责权威文档/集成/write-back，子 Agent 只处理窄切片 |
| **文档职责** | `.clinerules/` = 规则注入；Memory Bank = 手动上下文恢复；无显式的"权威文档分层"概念 | 多层权威文档：`docs/` > `design_docs/` > planning-gate > phase doc；文档是状态真相来源 |
| **执行机制** | 工具流水线（ToolExecutor → Handler）+ 直接 LLM 控制；规则层是 system prompt 注入 | Governance Pipeline（PDP → PEP）+ Pack 系统；规则层既有 instruction-layer 也有 machine-checked 层 |
| **治理验证** | Hooks 可编程验证（脚本级）+ Auto-Approve 操作粒度控制；无显式 constraint 检查机器 | C1-C8 约束体系，machine-checked constraints + planning-gate 必须存在才能执行 |
| **防漂移机制** | 规则通过 system prompt 注入（instruction-layer only）；Hooks 可做运行时强制；无 pack-lock | pack-lock.json 哈希锁定 + manifest_version 版本感知 + merge_conflicts 检测 + decision logs 审计 |
| **持续推进机制** | Plan/Act 双模式切换（YOLO 自动切换）；无显式的"对话推进规则"或"forward-driving question"协议 | 显式对话推进协议：每条回复必须以 AI 分析 + askQuestions 结尾；Phase 完成后自动推进下一步 |
| **复杂度定位** | 重量级完整产品（VS Code 扩展 + CLI + Webview + gRPC + 测试平台 + Evals 框架） | 中等复杂度平台（Python MCP server + VS Code 扩展 + 文档治理协议） |

## 借鉴点

### BP-1: 条件规则（Conditional Rules）

- **外部实现**：YAML frontmatter 中 `paths:` glob 数组，当文件上下文匹配时自动激活
- **本平台现状**：Pack 通过 `scope_path` 做目录级选择，但无基于 glob 的条件激活
- **差异**：Cline 的条件粒度更细（文件级 glob），且 fail-open（frontmatter 解析失败仍加载）
- **可操作性**：⚠ 需适配
- **采纳建议**：可在 Pack manifest 中增加可选的 `conditional_paths` 字段，实现 pack 内规则的条件激活。与现有 `scope_path` 互补而非替代

### BP-2: 多源规则自动检测与合并

- **外部实现**：自动检测 `.clinerules/`、`.cursorrules`、`.windsurfrules`、`AGENTS.md`，统一展示在 Rules 面板，用户可逐条 toggle
- **本平台现状**：Pack 系统是唯一的规则来源；不检测外部规则文件
- **差异**：Cline 对已有生态文件的兼容性远超本平台
- **可操作性**：📋 记录为 future direction
- **采纳建议**：Post-v1.0 考虑支持读取 `.cursorrules` / `AGENTS.md` 作为 "compat pack"，以降低新用户迁移成本

### BP-3: Hooks（可编程生命周期钩子）

- **外部实现**：PreToolUse / PostToolUse / TaskStart / TaskResume / Notification 五种钩子，支持 shell 脚本，可阻断操作或注入上下文
- **本平台现状**：governance pipeline 的 PEP 层有工具权限检查（`tool_permissions`），但无用户可编程钩子
- **差异**：Cline 的 Hooks 给了用户"可编程的策略执行点"，本平台的 PEP 是"声明式策略"
- **可操作性**：📋 记录为 future direction
- **采纳建议**：Hooks 与本平台的 Pack `tool_permissions` 可互补——声明式权限 + 可编程验证。但优先级低于核心治理功能

### BP-4: 细粒度 Auto-Approve 体系

- **外部实现**：按操作类型（readFiles / editFiles / executeSafeCommands / executeAllCommands / useBrowser / useMcp）分别控制，区分 local / external，支持 YOLO 全自动
- **本平台现状**：Pack 的 `tool_permissions` 做 allow/deny/ask，但无用户可配置的全局审批策略
- **差异**：Cline 的审批是 UI 级别的用户配置；本平台的权限是 pack 级别的声明
- **可操作性**：⚠ 需适配
- **采纳建议**：VS Code 扩展可参考 Cline 的 Auto-Approve UI 设计，在 Settings 面板添加操作级审批开关。但核心区别是本平台的权限来自 pack 声明而非用户设置

### BP-5: 规则 Toggle UI

- **外部实现**：所有规则（global / workspace / cursor / windsurf / agents / remote）在同一面板中展示，每条可独立 toggle on/off
- **本平台现状**：VS Code 扩展的 Decision Log Viewer 有 filter，但无 Pack/规则的 toggle 面板
- **差异**：Cline 的 toggle 体验远超本平台
- **可操作性**：⚠ 需适配
- **采纳建议**：VS Code 扩展中增加 "Pack Rules" 面板，列出所有 loaded packs 及其 always_on/on_demand 规则，支持临时 toggle。这是 UX 层改进，不影响核心协议

### BP-6: Skills vs Pack on-demand

- **外部实现**：Skills 是独立的 `.md` 文件，通过 `use_skill` 工具按需加载；与 Rules（always-on）明确分离
- **本平台现状**：Pack 有 `always_on` vs `on_demand` 分区，但两者都在同一 pack manifest 内
- **差异**：Cline 的 Skills 作为顶层概念，与 Rules 完全分离；本平台将两者统一在 Pack 内
- **可操作性**：❌ 不采纳
- **采纳建议**：本平台的 Pack 统一模型更优——同一个 pack 既能声明 always_on 规则也能声明 on_demand 内容，避免文件散落。Cline 的分离模型增加了管理碎片

### BP-7: Memory Bank 与 Checkpoints 分离

- **外部实现**：Memory Bank（Markdown 文件）= 知识持久化；Checkpoints（文件快照）= 代码状态快照。两者互补但独立
- **本平台现状**：`design_docs/` + planning-gate + handoff 系统 = 知识持久化；无文件级快照
- **差异**：Cline 的 Checkpoint 提供了原子级回滚能力，本平台没有
- **可操作性**：📋 记录为 future direction
- **采纳建议**：文件级 checkpoint/snapshot 超出当前平台范围，但其"知识 vs 状态分离"的设计思路值得参考。本平台的 handoff 系统已部分实现知识持久化

## 差异分析

### Cline 缺失清单（本平台有、Cline 没有）

| # | 能力 | 说明 |
|---|------|------|
| 1 | 文档权威分层 | 本平台有 `docs/` > `design_docs/` > planning-gate 层级；Cline 的规则是平面结构 |
| 2 | Machine-checked 约束 | 本平台 C4/C5/C8 不可覆盖；Cline 的规则全是 instruction-layer |
| 3 | Planning-gate 守门 | 本平台要求"窄 scope 文档先于实现"；Cline 的 Plan 模式是建议性的 |
| 4 | Decision logs 审计 | 本平台有结构化 decision log + merge conflicts；Cline 无显式审计日志 |
| 5 | Pack 锁定与版本控制 | pack-lock.json + manifest_version；Cline 的规则无版本/完整性校验 |
| 6 | 显式对话推进协议 | "每条回复必须以 AI 分析 + askQuestions 结尾"；Cline 无此约束 |
| 7 | 子 Agent 治理协议 | 主/子 agent 职责分离 + 共享状态保护；Cline 的 subagent 工具无类似协议 |
| 8 | Dependency graph + 影响分析 | `analyze_changes` / `impact_analysis`；Cline 无依赖图 |
| 9 | Dogfood 反馈管道 | `promote_dogfood_evidence` 结构化反馈；Cline 无自我评估管道 |

### 本平台缺失清单（Cline 有、本平台没有）

| # | 能力 | 说明 |
|---|------|------|
| 1 | 文件级 Checkpoint/回滚 | Cline 可快照文件状态并回滚；本平台无此能力 |
| 2 | 条件规则 (glob-based) | Cline 的 `paths:` frontmatter；本平台只有目录级 scope |
| 3 | 外部规则文件兼容 | `.cursorrules` / `.windsurfrules` / `AGENTS.md` 自动检测 |
| 4 | 可编程 Hooks | PreToolUse / PostToolUse 等用户脚本钩子 |
| 5 | 细粒度 Auto-Approve UI | 按操作类型的审批开关 + YOLO 模式 |
| 6 | MCP Marketplace | 一键安装 MCP 服务器的生态 |
| 7 | CLI 模式 | 终端下独立运行 AI agent |
| 8 | 规则 Toggle 面板 | 统一展示/切换所有规则来源 |
| 9 | 浏览器操作工具 | 内置浏览器自动化 |
| 10 | Plan/Act 分离模型 | 双模式 + 按模式配 LLM |

### 交叉验证结论

两个项目在**定位上有根本差异**：

- **Cline**：Agent-first，用户给任务，AI 自主执行。治理是"安全网"（Auto-Approve + Hooks + Checkpoints）
- **本平台**：Governance-first，文档是源头，AI 在治理框架内执行。治理是"骨架"（Planning-gate + Constraints + Decision logs）

这意味着：
1. Cline 的 UX 模式（Rules toggle / Auto-Approve / Hooks）可借鉴到本平台 VS Code 扩展的 UI 层
2. Cline 的核心治理模型（instruction-layer only）**不应**影响本平台的 machine-checked 约束方向
3. Cline 的 Conditional Rules 和多源兼容是本平台 Pack 系统可吸收的低成本增强

## 行动项决策

| # | 建议 | 决策 | 理由 | 优先级 |
|---|------|------|------|--------|
| A1 | Pack manifest 增加 `conditional_paths` glob 条件 | 📋 记录 | 有价值但需设计 pack 内条件激活与 scope_path 的交互 | 未来 |
| A2 | VS Code 扩展增加 Rules/Pack Toggle 面板 | ⚠ 需适配后采纳 | UX 改进，提升用户对 loaded packs 的可见性 | 中 |
| A3 | 外部规则文件兼容（.cursorrules / AGENTS.md 读取） | 📋 记录 | 降低新用户迁移成本，但需要设计"compat pack"语义 | 未来 |
| A4 | Hooks 可编程生命周期钩子 | 📋 记录 | 与 tool_permissions 互补，但优先级低于核心治理 | 未来 |
| A5 | Auto-Approve UI（按操作类型审批开关） | 📋 记录 | VS Code 扩展可参考设计；但本平台审批来自 pack 声明 | 未来 |
| A6 | 文件级 Checkpoint/回滚 | ❌ 不采纳 | 超出平台定位，属于 IDE 级功能 | — |
| A7 | CLI 模式 / MCP Marketplace | ❌ 不采纳 | 超出当前平台范围 | — |
| A8 | Memory Bank 参考设计纳入 handoff 演进 | 📋 记录 | Cline 的"每次 session 读取所有 memory 文件"模式可验证 handoff 系统设计 | 低 |
