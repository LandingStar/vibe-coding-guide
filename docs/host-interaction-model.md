# Host Interaction Model

## 文档定位

本文件定义平台如何把**宿主无关核心**与**具体宿主交互面**分开。

它回答的是：

- 平台哪些能力应保持宿主无关
- 哪些差异只属于宿主交互薄层
- Copilot / Codex / generic 与 VS Code / Windsurf / Antigravity 等差异应如何落在同一模型下

它不定义第二编辑器实现、第二 provider 实现或统一 adapter framework。

## 核心结论

当前平台应按四层理解：

1. **Core Contract Layer**
2. **Portable Runtime Layer**
3. **Interaction Adapter Layer**
4. **Host UX Layer**

真正需要被隔离出来的是第 3、4 层，而不是重写第 1、2 层。

## 四层模型

| 层次 | 定义 | 当前代表资产 |
|---|---|---|
| Core Contract Layer | 平台权威语义、状态面与工作流边界 | `docs/`、`design_docs/`、planning-gate、handoff、checkpoint、workflow standard |
| Portable Runtime Layer | 可跨宿主复用的执行内核 | CLI、MCP server、Pipeline、GovernanceTools、InstructionsGenerator |
| Interaction Adapter Layer | 将目标宿主/助手的调用方式翻译为同一条核心 contract 的薄层 | `generate-instructions` 目标分支、`AGENTS.md` / Copilot instructions 输出、`mcp.json`、`.codex/config.toml`、`codex mcp add` |
| Host UX Layer | 面向具体宿主的交互展示与宿主 API 对接 | VS Code extension 的 TreeView / WebView / notification / interception / chat participant |

## 允许依赖方向

### 基本规则

1. **Core Contract Layer 是真相源**：其语义可被上层消费，但不应被上层重新定义。
2. **Portable Runtime Layer 实现核心 contract**：它可以消费 Core Contract，但不应依赖某个具体宿主 UX。
3. **Interaction Adapter Layer 只翻译，不改写**：它可以消费 Core Contract 与 Portable Runtime，但不得引入新的治理语义、第二份 authority 或宿主私有规则。
4. **Host UX Layer 只负责体验与呈现**：它可以通过 Interaction Adapter 或 Portable Runtime 消费能力，但不得回写新的平台语义定义。

### 明确禁止

- 不允许由某个编辑器插件重新定义 planning-gate、handoff、safe-stop、authority priority
- 不允许把某个宿主的 chat / UI 语义提升为平台默认 contract
- 不允许让宿主专用文档替代 `docs/` / `design_docs/` 的正式口径

## 两类宿主差异必须分开

### 1. 指令/助手目标差异

这类差异体现为：

- `generic`
- `copilot`
- `codex`

它们主要影响：

- 指令文件格式
- 最短入口描述
- MCP 注册/调用方式提示

这类差异应落在 **Interaction Adapter Layer**。

### 2. 编辑器/UI 宿主差异

这类差异体现为：

- VS Code
- Windsurf
- Antigravity
- 其他带 UI 扩展面的宿主

它们主要影响：

- TreeView / WebView / Notification / Settings / Interceptor / Chat integration 等宿主 API

这类差异应落在 **Host UX Layer**。

两类差异都叫“宿主相关”，但不应被混成一个统一接口。

## 当前仓库资产映射

| 资产 | 所属层次 | 说明 |
|---|---|---|
| `docs/platform-positioning.md` | Core Contract | 平台本体定位 |
| `docs/official-instance-doc-loop.md` | Core Contract | 官方实例定位 |
| `design_docs/tooling/Document-Driven Workflow Standard.md` | Core Contract | 工作流规则 |
| `design_docs/Project Master Checklist.md` / `Global Phase Map...` | Core Contract | 状态面 |
| `src/workflow/` / `src/runtime/` / `src/mcp/` / CLI | Portable Runtime | 可移植执行内核 |
| `generate-instructions` / `AGENTS.md` / Copilot instructions 输出 | Interaction Adapter | 指令目标适配 |
| `.codex/config.toml` / `codex mcp add` / `.vscode/mcp.json` | Interaction Adapter | 宿主注册适配 |
| `vscode-extension/` | Host UX | 当前唯一真实 UI 宿主实现 |

## 首批子案例

### Codex 独立入口 contract

Codex 当前应被视为 **Interaction Adapter Layer** 的首个重点子案例：

- 它主要关心 `AGENTS.md`、MCP 注册、CLI/验证链如何构成最短入口
- 它不是 VS Code extension 第二 provider 的同义词

详见：`docs/codex-entry-contract.md` 与 `design_docs/codex-independent-entry-contract-direction-analysis.md`

### VS Code extension

VS Code extension 当前应被视为 **Host UX Layer** 的第一个实现：

- provider abstraction 只解决该层内部的一部分调用解耦
- 它不等于跨宿主模型本身

### 未来 Windsurf / Antigravity

在没有真实接入需求前，未来第二宿主应先被视为 **Host UX Layer 候选**，而不是直接进入实现。

## 与相关权威文档的关系

- `installation-guide.md`：说明“如何接入”，本文件说明“接入差异属于哪一层”
- `driver-responsibilities.md`：driver 属于 Portable Runtime，不属于宿主交互层
- `external-skill-interaction.md`：external skill contract 属于核心/运行时边界，不属于宿主 UI 适配
- `design_docs/stages/planning-gate/2026-04-22-vscode-extension-llm-provider-abstraction.md`：该 gate 只处理 VS Code extension 内部 provider 解耦，不构成宿主隔离总纲

## 当前边界

本文件当前固定的是：

- 四层模型
- 允许依赖方向
- 当前资产映射
- 首批子案例归类

本文件当前不固定：

- 统一 adapter framework 的代码骨架
- 第二编辑器实现
- 第二 provider 实现
- 特定宿主的 packaging / marketplace 分发方案
