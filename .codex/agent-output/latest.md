# Extension P0+P1 Build Report

## 状态: ✅ 全部完成 + VSIX 已打包

---

## 一、Extension 与 Python Runtime 的关系

Extension 是一个 **MCP Client**，它通过 stdio 连接到 **Python MCP Server**（即 `src.mcp.server`）。两者的分发是独立的：

| 组件 | 分发形式 | 当前版本 |
|------|----------|----------|
| VS Code Extension | `.vsix` 文件 | 0.1.0 |
| Python Runtime | pip wheel / release zip | 0.9.3 |

**Extension 不内嵌 Python Runtime**——它 spawn 一个 Python 子进程来运行 MCP Server。因此：

- Python Runtime **不需要为了 Extension 而重新发布**——Extension 直接使用项目本地的 Python 代码
- 如果你想在其他项目中使用 Extension，需要先 `pip install doc-based-coding-runtime` 或确保 `src/mcp/server.py` 可访问

---

## 二、安装步骤

### 前置条件
- VS Code ≥ 1.90.0
- Python 3.10+ 已安装
- 当前项目已有 `.codex/platform.json`（激活条件）

### 安装 Extension

1. 打开 VS Code
2. `Ctrl+Shift+P` → 输入 "Extensions: Install from VSIX..."
3. 选择 `release/doc-based-coding-0.1.0.vsix`
4. 等待安装完成
5. `Ctrl+Shift+P` → "Developer: Reload Window"

### 验证安装
- Activity Bar（左侧边栏）应出现 "Doc-Based Coding" 图标（文档+盾牌）
- 点击图标，侧栏显示两个面板：
  - **Constraints (C1-C8)** — 约束状态
  - **Pack Explorer** — Pack 拓扑

---

## 三、配置

Extension 的配置在 VS Code Settings 中（`Ctrl+,` → 搜索 "Doc-Based Coding"）：

| 设置 | 说明 | 默认值 |
|------|------|--------|
| `docBasedCoding.pythonPath` | Python 可执行文件路径 | 自动检测 |
| `docBasedCoding.autoStart` | 激活时自动启动 MCP Server | `true` |
| `docBasedCoding.serverArgs` | 额外 MCP Server 参数 | `[]` |

### Python 路径自动检测顺序

Extension 会按以下顺序查找 Python：

1. `docBasedCoding.pythonPath` 用户设置
2. `<项目>/.venv/Scripts/python.exe`（Windows）
3. `<项目>/.venv/bin/python`（Linux/Mac）
4. `<项目>/.venv-release-test/Scripts/python.exe`
5. `<项目>/venv/Scripts/python.exe`
6. 系统 `python` 命令

### 推荐配置（当前项目）

由于当前项目使用 `.venv-release-test`，Extension 应该能自动检测到。如果不行，手动设置：

```json
{
  "docBasedCoding.pythonPath": "e:\\workspace\\tool develop\\vibe coding facilities\\doc based coding\\.venv-release-test\\Scripts\\python.exe"
}
```

---

## 四、使用

### 自动行为（autoStart=true 时）

1. 打开含 `.codex/platform.json` 的工作区 → Extension 自动激活
2. Extension 自动 spawn Python MCP Server 子进程
3. Constraint Dashboard 自动加载 C1-C8 约束状态

### 手动命令

| 命令 | 快捷方式 | 说明 |
|------|----------|------|
| Doc-Based Coding: Refresh Constraints | TreeView 标题栏刷新图标 | 重新调用 `check_constraints` |
| Doc-Based Coding: Start MCP Server | Command Palette | 手动启动 MCP Server |
| Doc-Based Coding: Stop MCP Server | Command Palette | 停止 MCP Server |

### 日志输出

- Output Channel: "Doc-Based Coding"（`Ctrl+Shift+U` → 选择 "Doc-Based Coding"）
- 显示 MCP Server 启动/停止、请求/响应、错误信息

### Constraint Dashboard 说明

- 每个 C1-C8 约束显示为 TreeView 节点
- 图标颜色：
  - 🟢 绿色（pass）— 约束满足
  - 🟡 黄色（warning）— 警告
  - 🔴 红色（error）— 约束违反
- 点击可查看详细信息

---

## 五、关于 Python Runtime Release 的判断

当前 Python Runtime v0.9.3 **不需要更新**，原因：

1. Extension 不改变 Python Runtime 的任何代码
2. Extension 通过 `python -m src.mcp.server` 直接使用项目本地代码
3. `analyze_changes` 工具合并已包含在当前代码中（但尚未发布新 release）

如果后续希望：
- 在 **其他项目** 中使用 Extension → 需要发布新的 Python Runtime release
- 让 Extension **内嵌 MCP Server** → 需要重新设计分发策略

---

## 六、已知限制

1. **Pack Explorer 为占位符** — 当前只显示提示文字，P2 阶段实现真实 pack 拓扑
2. **GovernanceInterceptor 为 passthrough** — 所有操作都被 allow，真实拦截在后续实现
3. **CopilotLLMProvider 未连线** — 骨架已写，但尚未在 Extension 主流程中调用
4. **MCP 初始化可能较慢** — 首次 spawn Python 进程 + pack 加载需要几秒

---

# (以下为历史：Extension 架构设计要点 — 治理严格性 + Copilot 集成)

## 用户关键约束

1. **设计时支持严格治理规则**（审查打回、强制拦截），即使 MVP 不全部实现
2. **接入 Copilot 模型服务**（`vscode.lm` Language Model API）

## 一、MCP 的 enforcement gap 与 Extension 的解决路径

来源：[design_docs/stages/planning-gate/copilot-integration-runtime-simulation.md](design_docs/stages/planning-gate/copilot-integration-runtime-simulation.md) 第 395 行的核心结论：

> 本项目的约束（C1-C8）要求"agent 的行为空间必须被外部限制"，而不是"agent 内部自己决定遵守"。

### 当前 MCP 模式的局限

| 层次 | 能力 | 局限 |
|------|------|------|
| MCP BLOCK/ALLOW | 结构性建议 | Agent 仍可选择忽略 BLOCK |
| Instructions | 行为规范 | 上下文压缩后可能丢失 |
| pack-manifest | 规则声明 | 无运行时拦截能力 |

### Extension 可实现的严格治理层

```
                ┌─ Extension Enforcement Layer ─┐
                │                               │
  Agent 请求 ───┤  ① 拦截层 (Interceptor)       │
                │     ↓ governance_decide()      │
                │  ② 决策层 (PDP via MCP)        │
                │     ↓ ALLOW / BLOCK            │
                │  ③ 执行层 (PEP)                │
                │     ↓ 文件写入/命令执行         │
                │  ④ 审计层 (Audit Trail)        │
                │     ↓ decision_logs            │
                │  ⑤ 审查层 (Human Review UI)    │
                │     ↓ approve / reject         │
                └───────────────────────────────┘
```

关键设计点：

1. **Interceptor Pattern**：Extension 注册为文件写入/终端命令的 watcher，在 agent 执行前拦截
   - VS Code API: `workspace.onWillSaveTextDocument`, `workspace.onDidChangeTextDocument`
   - Terminal API: 监控 terminal 输出和命令
   - 用 MCP `governance_decide()` 判断是否放行

2. **Review UI**：当 PDP 返回需要人类审查时，Extension 弹出审查面板
   - WebView 展示决策详情 + approve/reject 按钮
   - 审查结果写回 MCP（通过新的 review tool 或现有的 writeback_notify）

3. **Gate Visualization**：planning-gate 状态在 TreeView 中可视化
   - 红/黄/绿状态指示器
   - 点击可跳转到对应的 gate 文档

### MVP 中需要预留的接口（即使不实现）

```typescript
// src/governance/types.ts — MVP 就定义好
interface GovernanceInterceptor {
  beforeFileWrite(uri: Uri, content: string): Promise<GovernanceDecision>;
  beforeTerminalCommand(command: string): Promise<GovernanceDecision>;
  beforeAgentAction(action: AgentAction): Promise<GovernanceDecision>;
}

interface ReviewPanel {
  requestReview(decision: GovernanceDecision): Promise<ReviewResult>;
}

// MVP 实现：只做 pass-through，但接口先占位
class PassthroughInterceptor implements GovernanceInterceptor {
  async beforeFileWrite() { return { allow: true }; }
  async beforeTerminalCommand() { return { allow: true }; }
  async beforeAgentAction() { return { allow: true }; }
}
```

## 二、Copilot 模型集成

VS Code 提供 `vscode.lm` API，允许 Extension 直接使用 Copilot 的模型：

```typescript
// 使用 Copilot 模型做 intent classification
const [model] = await vscode.lm.selectChatModels({
  vendor: 'copilot',
  family: 'gpt-4o'   // 或其他可用模型
});

const messages = [
  vscode.LanguageModelChatMessage.User(
    `Classify this intent: "${userInput}"`
  )
];
const response = await model.sendRequest(messages);
```

### 集成方案

| 场景 | 当前方案 (Python) | Extension 方案 |
|------|-------------------|----------------|
| Intent Classification | LLM Worker (需 API key) | `vscode.lm` (免费，用 Copilot 订阅) |
| Governance Decide | MCP tool | MCP tool + `vscode.lm` 做 pre-check |
| Pack 文档生成 | 手动 | `vscode.lm` 辅助生成 |

**关键优势**：用户不需要单独配置 LLM API key，直接复用 Copilot 订阅。

### 架构预留

```typescript
// src/llm/types.ts — 抽象 LLM 接口
interface LLMProvider {
  classify(input: string, schema: object): Promise<ClassificationResult>;
  generate(prompt: string): Promise<string>;
}

// 两个实现：
class CopilotLLMProvider implements LLMProvider { /* vscode.lm API */ }
class MCPWorkerProvider implements LLMProvider { /* 通过 MCP 调现有 Python worker */ }
```

## 三、Extension 目录结构（方案 1 确认版）

```
vscode-extension/
├── package.json          # Extension manifest + contributes
├── tsconfig.json
├── esbuild.config.mjs    # 打包配置
├── src/
│   ├── extension.ts      # activate / deactivate
│   ├── mcp/
│   │   ├── client.ts     # MCP stdio client — spawn Python server
│   │   └── types.ts      # MCP tool input/output TypeScript 类型
│   ├── governance/
│   │   ├── types.ts      # GovernanceInterceptor, ReviewPanel 接口
│   │   └── passthrough.ts # MVP pass-through 实现
│   ├── views/
│   │   ├── constraintDashboard.ts  # P1: C1-C8 TreeView
│   │   └── packExplorer.ts         # P2: Pack TreeView (留空)
│   ├── llm/
│   │   ├── types.ts      # LLMProvider 接口
│   │   └── copilot.ts    # vscode.lm 实现
│   └── utils/
│       └── logger.ts
├── test/
│   └── suite/
└── .vscodeignore
```

## 四、package.json 核心 contributes（MVP）

```json
{
  "contributes": {
    "viewsContainers": {
      "activitybar": [{
        "id": "doc-based-coding",
        "title": "Doc-Based Coding",
        "icon": "resources/icon.svg"
      }]
    },
    "views": {
      "doc-based-coding": [
        { "id": "constraintDashboard", "name": "Constraints (C1-C8)" },
        { "id": "packExplorer", "name": "Pack Explorer" }
      ]
    },
    "commands": [
      { "command": "docBasedCoding.refreshConstraints", "title": "Refresh Constraints" },
      { "command": "docBasedCoding.checkConstraints", "title": "Check All Constraints" }
    ]
  }
}
```

## 总结

**设计时就支持严格治理**的关键是：
1. `GovernanceInterceptor` 接口从 MVP 就定义好
2. MCP Client 层是核心连接通道
3. `vscode.lm` 解决 LLM 依赖问题（免 API key）
4. Review UI 接口预留，但 MVP 可用 pass-through

**MVP 可交付物**：Extension 骨架 + MCP Client + Constraint Dashboard + 预留的 Interceptor/LLM 接口
# 仓库结构深度分析 — Extension + Python Runtime 共存方案

## 三种候选方案

### 方案 1: 同仓库顶层目录 `vscode-extension/`

```
doc-based-coding/          ← 当前仓库根目录不变
├── src/                   ← Python runtime (不动)
├── tests/                 ← Python tests (不动)
├── pyproject.toml         ← Python 包配置 (不动)
├── docs/                  ← 权威文档 (不动)
├── design_docs/           ← 设计文档 (不动)
├── doc-loop-vibe-coding/  ← 官方实例 (不动)
├── vscode-extension/      ← ★ 新增
│   ├── package.json
│   ├── tsconfig.json
│   ├── src/
│   │   ├── extension.ts
│   │   ├── mcpClient.ts
│   │   └── views/
│   ├── .vscodeignore
│   └── README.md
└── ...
```

**优势**：
- 零改动现有结构，新增一个目录即可
- Extension 和 MCP Server 同步演进，改 tool 定义时能同时更新 UI
- 共享 docs/ 和 design_docs/
- 单次 checkout 开发完整系统

**劣势**：
- 根目录混合 Python + Node.js 工具链（但通过 `.vscodeignore` 和 `.npmignore` 可隔离）
- CI 需要两套环境（Python + Node）

**MCP Server 连接方式**：Extension 启动时 spawn `python -m src.mcp.server --project <path>`，通过 stdio 通信。Extension 知道 MCP server 在同目录的 Python 包里。

### 方案 2: 独立仓库

```
doc-based-coding/          ← Python runtime 仓库
doc-based-coding-vscode/   ← Extension 仓库（独立）
```

**优势**：
- 工具链完全隔离
- 独立发布节奏

**劣势**：
- MCP tool surface 变更需要跨仓库同步（高风险）
- 开发时需要两个 checkout
- 文档不共享，容易分叉

### 方案 3: 真 monorepo（packages/ 重构）

```
doc-based-coding/
├── packages/
│   ├── runtime/    ← 现有 src/ 迁入
│   └── extension/  ← VS Code Extension
```

**优势**：最干净的 monorepo 结构
**劣势**：需要大规模重构现有路径（所有 import、test 路径、CI、打包配置）

## 我的倾向

**方案 1（同仓库顶层目录）**是最优解：
- 风险最低：现有 1133 项测试、所有 import 路径零变动
- 协作最紧密：改 MCP tool 时 Extension UI 就在旁边
- 启动最快：新增一个目录就可以开始写 Extension

方案 3 虽然更"正确"，但重构成本太高，不值得在 MVP 阶段做。
方案 2 的跨仓同步问题在当前开发节奏下是致命缺陷。

## Extension 与 MCP Server 的连接设计

```
Extension (TypeScript)
  │
  ├─ spawn: python -m src.mcp.server --project ${workspaceFolder}
  │         (或 bundled wheel 中的入口点)
  │
  └─ stdio MCP protocol
       │
       ├── check_constraints → Constraint Dashboard TreeView
       ├── get_pack_info     → Pack Explorer TreeView (P2)
       ├── governance_decide → Command (P4)
       └── query_decision_logs → Output Channel (P3)
```

Extension bundling 策略：
1. **开发期**：Extension spawn 本地 Python 环境中已安装的 MCP server
2. **分发期**：Extension 内嵌 Python wheel + 自带 venv（类似 Pylance 模式）

## 下一步行动（如果确认方案 1）

1. 创建 `vscode-extension/` 骨架（package.json + tsconfig + esbuild）
2. 实现 MCP Client 连接层
3. 实现 Constraint Dashboard TreeView（P1）
4. 本地 F5 测试验证
# 插件化方向分析 — 从 MCP runtime 到 VS Code Extension

## 用户诉求

> "目前项目的深入，对很多内容效果和合理性的感受已经不准确了，需要插件化以及图形化才便于提出更进一步的关于核心思路或结构的建议。另外，未插件化也不便于分发和收集问题。"

核心需要：
1. **可视化** — 看到治理流程的实际运行效果
2. **可交互** — 对规则/Pack/决策有直观操作界面
3. **可分发** — 其他人能安装使用并反馈

## 当前架构位置

```
当前存在的层：
┌─────────────────────────────────┐
│  MCP Server (stdio)             │ ← 已实现，11 个 tools
│  GovernanceTools (Python)       │ ← 已实现，完整治理链
│  Pipeline + Pack System         │ ← 已实现，discovery/loading/tree
│  PDP/PEP Runtime                │ ← 已实现，intent→gate→execution
│  Audit/Decision Logs            │ ← 已实现
└─────────────────────────────────┘

需要新增的层：
┌─────────────────────────────────┐
│  VS Code Extension (TypeScript) │ ← 需要新建
│  ├── TreeView: Pack 浏览器      │
│  ├── WebView: 决策流可视化      │
│  ├── Status Bar: 约束状态       │
│  ├── Output Channel: 审计日志   │
│  └── MCP Client → 连接现有 server│
└─────────────────────────────────┘
```

## 两条路径分析

### 路径 A：MCP-first Extension（推荐）

**思路**：VS Code Extension 作为 MCP Client，通过现有 MCP Server 接口消费全部治理能力。

优势：
- Python runtime 零改动，已有 1133 项测试保护
- TypeScript Extension 只做 UI 层
- MCP 协议是天然的进程隔离边界
- 其他 MCP 客户端（Copilot、Codex）仍可并行使用

需要做的：
- `package.json` + Extension 骨架 (TypeScript)
- MCP Client SDK 集成 (启动/管理 MCP server 子进程)
- TreeView: Pack Explorer（调用 `get_pack_info`）
- TreeView: Constraint Dashboard（调用 `check_constraints`）
- WebView: Decision Flow Viewer（调用 `governance_decide` + `query_decision_logs`）
- Status Bar item: 当前治理状态
- Output Channel: 实时审计日志流
- Commands: 常用操作的 Command Palette 入口

### 路径 B：嵌入式 Python Extension

**思路**：用 Python Extension API 直接加载 runtime。

劣势：
- 与 VS Code extension 生态不兼容（VS Code extension = TypeScript/JS）
- 无法上架 Marketplace
- 不利于分发

**结论：不推荐**

## 我的倾向：路径 A + MVP 分层

### MVP 切片建议（从最有价值到最低）

| 优先级 | 切片 | 提供的价值 | 预估 scope |
|--------|------|-----------|-----------|
| P0 | Extension 骨架 + MCP Client | 基础连接 | 小 |
| P1 | Constraint Dashboard TreeView | 看到 C1-C8 实时状态 | 小 |
| P2 | Pack Explorer TreeView | 浏览已加载 Pack 结构 | 中 |
| P3 | Decision Log 面板 | 审计可视化 | 中 |
| P4 | Governance Decide 交互 | 在 UI 中试验治理决策 | 中 |
| P5 | WebView: 决策流图 | 完整的可视化治理流 | 大 |

**P0+P1 就够 MVP**：安装后能看到约束状态 + Pack 列表，这已经比纯 MCP stdio 强很多。

## 需要讨论的关键问题

1. **语言选择**：Extension 必须 TypeScript，但 runtime 保持 Python。这意味着两个仓库还是 monorepo？
2. **分发策略**：VS Code Marketplace + Python runtime wheel 双轨？还是 Extension 自带 Python runtime bundling？
3. **MVP 范围**：先做到什么程度能让你开始获得有效反馈？
# analyze_changes 合并完成 — 下一步方向

> 生成时间: 2026-04-18

## 刚完成的切片

**analyze_changes 统一入口**：
- `impact_analysis` + `coupling_check` 合并为 `analyze_changes`
- 旧工具名保留为向后兼容别名
- 6 个新测试，全量 1133 passed
- 审计文档已更新

## 本次会话总成绩

| 统计 | 数值 |
|------|------|
| 切片数 | **9** |
| 测试增长 | 992 → 1133 (+141) |
| 新模块 | agent_output.py |
| 新工具 | analyze_changes |
| 标准文档 | Pack Organization Standard, MCP Audit |

## 下一步分析

本次会话 9 个切片已经很充实。我的倾向：

**做 safe-stop handoff** — 理由：
1. 9 切片已远超正常会话量
2. 剩余 B-REF (4/5/6) 都是中到大 scope，适合新会话全局规划
3. 当前无活跃 planning-gate，是天然安全停点

如果想继续，最小风险选项是 B-REF-5（中断原语），因为 scope 中等且与当前 workflow 引擎直接相关。
# 本次会话完成 8 个切片 — 下一步方向

> 生成时间: 2026-04-18

## 完成清单

| # | 切片 | 领域 | 基线 |
|---|------|------|------|
| 1 | Reserved Interfaces | Pack Manager | 992→1058 |
| 2 | B-REF-1 S1 LoadLevel | Pack 加载 | →1082 |
| 3 | B-REF-1 S2 Pipeline 降级 | Pipeline | →1087 |
| 4 | B-REF-1 S3 MCP level/scope | MCP | →1095 |
| 5 | B-REF-2 description 标准 | Pack 质量 | →1104 |
| 6 | B-REF-3 组织规范 | Pack 组织 | →1117 |
| 7 | B-REF-7 tool surface 审计 | MCP 接口 | 不变 |
| 8 | Agent Output 可见性 | 基础设施 | →1127 |

## B-REF 状态

- [x] B-REF-1, 2, 3, 7
- [ ] B-REF-4 (Permission policy, scope 大)
- [ ] B-REF-5 (中断原语, scope 中)
- [ ] B-REF-6 (子 agent 隔离, scope 中)

## 下一步候选

本次会话已非常充实 (+135 tests)。建议方向：

1. **Safe-stop handoff** — 最稳妥，保存所有进度
2. **B-REF-4/5/6 中选一个** — 都是中到大 scope，适合新会话
3. **合并 analyze_changes** — B-REF-7 审计建议的实施，scope 小
4. **其他方向** — HTTPWorker fallback 等

我的倾向是做 safe-stop handoff，因为 8 个切片已经非常充实。
# 当前状态快照

> 生成时间: 2026-04-18 (子 agent 输出可见性临时方案测试)

## 本次会话已完成 8 个切片

| # | 切片 | 基线变化 |
|---|------|---------|
| 1 | Reserved Interfaces | 992→1058 |
| 2 | B-REF-1 Slice 1 (LoadLevel) | →1082 |
| 3 | B-REF-1 Slice 2 (Pipeline 降级) | →1087 |
| 4 | B-REF-1 Slice 3 (MCP level/scope) | →1095 |
| 5 | B-REF-2 (description 质量) | →1104 |
| 6 | B-REF-3 (内部组织) | →1117 |
| 7 | B-REF-7 (tool surface 审计) | 不变 |
| 8 | Agent Output 可见性 | →1127 |

## 新增模块

- `src/workflow/agent_output.py` — OutputSink Protocol + FileSink 实现 + write_agent_output() 全局入口
- GovernanceTools.write_output() 已集成到 MCP tools 层
- 10 个新测试全部通过

## 设计要点

- `OutputSink` Protocol 定义了 `write(content, title) -> str` 接口
- 当前实现 `FileSink` 写入 `.codex/agent-output/latest.md`
- 插件化时可替换为 UIPanelSink（输出到 VS Code WebView）或 ChatStreamSink
- GovernanceTools 已集成 FileSink 实例

## 如何使用

你（用户）现在可以打开 `.codex/agent-output/latest.md` 查看 AI 的分析输出。

后续每次 AI 需要向你展示重要的分析结果（表格、对比、审计等），会先写入这个文件，然后在 askQuestions 中提示你去查看。
