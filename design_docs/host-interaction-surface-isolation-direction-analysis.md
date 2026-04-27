# 方向分析 — 宿主交互面隔离（Host Interaction Surface Isolation）

## 背景

当前仓库已经有几条看起来分散、实则相关的宿主接入线索：

1. Python runtime、CLI、MCP server 已经天然具备较强的 host-neutral 属性。
2. `generate-instructions` 已支持 `generic|codex|copilot`，说明“指令面”已经开始出现目标宿主差异。
3. VS Code extension 已形成较完整的 UI/交互面，但 `2026-04-22-vscode-extension-llm-provider-abstraction` 也明确把 Chat Participant 和新 provider 排除在当前抽象之外。
4. `direction-candidates-after-phase-35.md` 已记录“跨编辑器 / 跨 CLI 适配层”是用户明确提出的长期需求。
5. 最新用户诉求进一步把问题说得更清楚：我们希望把与具体插件/CLI（Copilot、Codex）以及具体编辑器/宿主（VS Code、Windsurf、Antigravity 等）相关的交互部分隔离出来，让平台核心可以更便捷地跨宿主复用。

这说明当前最缺的，不是某一个具体宿主的支持，而是一个更高层的边界回答：

- 平台核心 contract 到底是什么
- 哪些是宿主无关的核心
- 哪些只是宿主交互薄层
- Codex/Copilot/Windsurf/Antigravity 应该以什么抽象落在同一模型下

本文仅做方向分析，**不进入实现**。

## 现状摘要

| 层次 | 当前现状 | 问题 |
|---|---|---|
| 核心治理/文档 contract | `docs/` + `design_docs/` + planning-gate + handoff + checkpoint | 语义稳定，但尚未显式标成“宿主无关核心” |
| Runtime kernel | CLI + MCP server + Pipeline + InstructionsGenerator | 已较接近可复用内核，但宿主边界未被单独命名 |
| 指令目标面 | `generic|codex|copilot` + `AGENTS.md` / Copilot instructions 输出 | 已出现 target-specific 分支，但缺少统一的 interaction taxonomy |
| 编辑器/插件 UI 面 | VS Code extension（TreeView / WebView / Notification / Chat Participant / Interceptor） | 目前只有 VS Code 实现，且 UI 语义天然宿主相关 |
| 安装/注册面 | `mcp.json`、`.codex/config.toml`、`codex mcp add` | 这些入口已经体现宿主差异，但尚未归入统一 adapter 视图 |

## 架构约束（设计必须遵守）

1. **核心 contract 必须宿主无关**：治理链、文档分层、planning-gate、safe-stop、MCP 工具语义不能因为宿主不同而分叉
2. **宿主交互层只能翻译，不得重写规则**：宿主适配层负责把交互习惯映射到同一条 authority contract，而不是长出各自版本的平台规则
3. **MCP / CLI 应视为首个可移植内核**：它们是当前最接近跨宿主复用的能力，不应被 UI 宿主面反向绑死
4. **编辑器 UI 适配与 AI 助手入口适配要分开**：VS Code/Windsurf/Antigravity 属于宿主 UI 轴，Copilot/Codex 属于助手/指令轴，这两类差异不应混在一个接口里
5. **分析先于骨架实现**：当前只回答边界与候选路径，不直接引入统一 adapter framework 或第二宿主实现

## 一个更清晰的分层模型

建议把当前平台按下面四层理解：

1. **Core Contract Layer**
   - `docs/` authority
   - `design_docs/` 状态/推导
   - planning-gate / handoff / checkpoint / workflow standard
2. **Portable Runtime Layer**
   - CLI
   - MCP server
   - Pipeline / GovernanceTools / InstructionsGenerator
3. **Interaction Adapter Layer**
   - 指令目标适配：Copilot / Codex / generic
   - 宿主注册适配：`mcp.json` / `.codex/config.toml` / 其他 host config
4. **Host UX Layer**
   - VS Code extension 的 TreeView / WebView / notification / interception / chat participant
   - 未来 Windsurf / Antigravity / 其他编辑器的 UI 宿主适配

当前真正需要被隔离出来的，是第 3、4 层，而不是再去改写第 1、2 层。

## 候选方案

### 方案 A — Doc-first Host Interaction Taxonomy（推荐）

**思路**：先把“核心 contract / 可移植内核 / 交互适配层 / 宿主 UX 层”的边界文档化，形成统一 taxonomy，再决定具体宿主如何接入。

**内容**：

- 定义平台哪些面是宿主无关核心
- 定义哪些文件、命令、配置属于 interaction adapter 层
- 明确 Codex / Copilot / generic 属于“指令目标适配”
- 明确 VS Code / Windsurf / Antigravity 属于“宿主 UI 适配”
- 说明为什么 extension 第二 provider 不能替代宿主隔离设计

**优点**：

- 能一次性把当前分散的宿主问题收拢到同一张结构图里
- Codex 独立入口 contract 会自然变成该方向下的首个子案例，而不是孤立文档
- 后续如果真要支持第二编辑器或第二 CLI/插件，不需要重新定义核心边界

**缺点**：

- 不能直接提升任何单一宿主的体验
- 会引出后续至少一条 planning-gate，短期看属于“边界建设”而非功能新增

### 方案 B — 先按具体宿主逐个扩（Codex、再 Windsurf、再 Antigravity）

**思路**：不先做统一 taxonomy，直接按宿主逐个出独立入口 contract 或 helper surface。

**优点**：

- 对单一宿主的响应更快
- 如果只有一个近程目标，短期感知收益更强

**缺点**：

- 容易让每个宿主文档各自长出一套局部约定
- 会重复讨论“核心 vs 宿主差异”问题
- 多做两个宿主后，必然还要回头补统一模型

### 方案 C — 直接上统一 adapter framework 骨架（不推荐）

**思路**：直接设计并实现 `EditorAdapter` / `AssistantAdapter` / `HostAdapterRegistry` 等统一框架。

**优点**：

- 形式上最完整

**缺点**：

- 当前还没有对宿主差异做完边界分析，直接写骨架容易抽象过早
- 会把 runtime、extension、packaging、instructions 同时卷入
- 风险和 scope 都明显过大

## 推荐

| 阶段 | 方案 | 触发条件 |
|---|---|---|
| 当前 | **方案 A — Doc-first Host Interaction Taxonomy** | 当我们要把 Copilot/Codex/Windsurf/Antigravity 等差异统一上浮到同一个宿主隔离模型时 |
| 下一阶段候选 | **方案 B — 某个具体宿主的独立入口 contract** | 当 taxonomy 已清楚，且某个宿主的真实接入需求最先浮现时 |
| 不建议 | **方案 C — 统一 adapter framework 先实现** | 在没有先定义 taxonomy 前，不建议进入 |

## 与当前已有方向的关系

- `design_docs/codex-independent-entry-contract-direction-analysis.md`：应视为本方向下的**首个具体子案例**，而不是更高层总纲
- `design_docs/stages/planning-gate/2026-04-23-public-surface-convergence.md`：它关注“入口变短”，而本方向关注“宿主差异如何被隔离”；两者相关，但不等价
- `design_docs/stages/planning-gate/2026-04-23-temporary-scratch-stable-docs-split.md`：它处理文档对象分类，是另一条正交但仍更前置的语义线
- `design_docs/stages/planning-gate/2026-04-22-vscode-extension-llm-provider-abstraction.md`：它只解决 extension 命令层 provider 抽象，不构成跨宿主模型
- `design_docs/direction-candidates-after-phase-35.md` §跨编辑器/跨 CLI 适配层：本文件可视为对那条长期待办的收窄与具体化

## 当前判断

我当前倾向于把后续顺序调整为：

1. 继续保留 `Temporary Scratch / Stable Docs Split` 作为最前置的文档语义切片候选
2. 在宿主扩展问题上，优先进入 **Host Interaction Taxonomy**，而不是直接继续做 Codex / provider / 第二编辑器其中任何一条实现线
3. Codex 独立入口 contract 作为该 taxonomy 的首个子案例保留
4. extension 第二 provider 比较分析继续后移

原因是：

1. 你刚刚提出的诉求已经明显高于 Codex 单线，应被建模为更高层宿主隔离问题
2. 若不先做这层 taxonomy，后续 Copilot/Codex/Windsurf/Antigravity 会各自产生一份局部解释
3. 只有 taxonomy 清晰后，我们才能判断哪些能力应该停留在 MCP/CLI 核心，哪些才值得做宿主 UI 适配

## 若进入下一条 planning-gate，建议边界

若你认可当前方向，下一条 planning-gate 建议只做：

1. 定义四层模型（Core Contract / Portable Runtime / Interaction Adapter / Host UX）
2. 映射当前仓库已有资产到四层
3. 明确 Codex、Copilot、VS Code、Windsurf、Antigravity 分别属于哪类宿主差异
4. 明确未来宿主适配的允许依赖方向与明确非目标

下一条 planning-gate 明确不做：

1. 不实现第二编辑器适配
2. 不实现第二 provider
3. 不重构 extension 代码
4. 不同时推进 public surface convergence 与 helper packaging

## 参考来源

- `design_docs/direction-candidates-after-phase-35.md`
- `design_docs/codex-independent-entry-contract-direction-analysis.md`
- `design_docs/stages/planning-gate/2026-04-22-vscode-extension-llm-provider-abstraction.md`
- `docs/installation-guide.md`
- `docs/driver-responsibilities.md`
- `docs/external-skill-interaction.md`
- `docs/official-instance-doc-loop.md`
