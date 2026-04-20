# Release 工作目录

## 目的

本目录用于存放 `doc-based-coding-platform` 双发行包的构建、验证与发布相关工作产物。

## 双发行包结构

根据 `design_docs/tooling/Dual-Package Distribution Standard.md`，本项目分为两个发行包：

| # | 名称 | pyproject.toml | 职责 |
|---|------|----------------|------|
| A | `doc-based-coding-runtime` | `./pyproject.toml` | 平台 runtime / CLI / MCP server |
| B | `doc-loop-vibe-coding` | `./doc-loop-vibe-coding/pyproject.toml` | 官方实例 pack 资产 |

依赖方向：B → A（官方实例依赖 runtime，runtime 不依赖实例）。

## 当前状态

- [x] pyproject.toml metadata 已定义（包名 / 版本 / 入口 / 依赖）
- [x] 双发行包标准已固化
- [x] v1.0.0 版本号已在两包中标记
- [x] 构建验证通过（双包均可成功构建 wheel / sdist，内容物完整）
- [x] clean environment 安装验证通过（干净 venv 安装 → CLI 入口可用 → 资产可发现）
- [x] adoption 端到端验证通过（空项目 bootstrap → validate → runtime info → MCP 启动）
- [x] 可分发安装包已打包（`doc-based-coding-v1.0.0.zip`，含 AI 安装指南）
- [ ] 发布流程 / CI 配置

## 构建验证结果（2026-04-12）

| # | Wheel | 大小 | 文件完整性 | 入口点 |
|---|-------|------|-----------|--------|
| A: doc-based-coding-runtime | OK | 83KB | 62 .py 全部收入 | `doc-based-coding`, `doc-based-coding-mcp` |
| B: doc-loop-vibe-coding | OK | 48KB | 39 源文件全部收入 | `doc-loop-bootstrap`, `doc-loop-validate-doc`, `doc-loop-validate-instance` |

### 已修复问题

- 构建产出的 `*.egg-info` 残留在项目根目录会导致 clean venv 中 pip 误判包已安装、跳过 entry point 生成。已通过清理 egg-info 解决。`*.egg-info/` 已在 `.gitignore`。

### 已知观察

- Runtime 包顶层包名为 `src`（`top_level.txt: src`），功能可用但与其他使用 `src` 命名的包存在潜在命名空间冲突。这是已有架构决定，不在当前切片内修改。

## Clean Environment 安装验证结果（2026-04-12）

验证环境：Python 3.12, 干净 venv (`.venv-release-test`)

| 步骤 | 结果 |
|------|------|
| 仅安装 runtime wheel | OK 正常安装，依赖 (jsonschema, mcp 等) 自动拉取 |
| `doc-based-coding --help` | OK 显示 5 条子命令 |
| `doc-based-coding info` | OK 正确输出 pack 信息 |
| `doc-based-coding validate` | OK 返回约束检查结果 |
| 追加安装 instance wheel | OK 正常安装，runtime 依赖复用 |
| `doc-loop-bootstrap --help` | OK 显示 bootstrap 参数 |
| `doc-loop-validate-instance` | OK 所有检查项通过（manifest keys / path refs / schema examples） |
| 安装态资产加载 | OK pack-manifest.json / bootstrap / references 均可从 site-packages 中读取 |

## 版本映射

本项目有三个独立版本化的组件：

| 组件 | 当前版本 | 说明 |
|------|---------|------|
| VS Code Extension (`.vsix`) | `0.1.2` | 前端插件，独立版本线 |
| Runtime (`.whl`) | `0.9.4` | 平台 runtime / CLI / MCP server |
| Instance Pack (`.whl`) | `0.9.4` | 官方 doc-loop 实例资产 |

**兼容性规则**：
- Extension `0.1.x` 兼容 Runtime `0.9.x`
- Instance Pack `0.9.x` 版本需 ≥ Runtime 版本（如 Pack 0.9.4 需要 Runtime ≥ 0.9.4）
- 同一 release 批次的三个文件可组合使用
- **重要**：内容变更时版本号会递增，使用 `pip install <file>` 即可正常升级

## 目录结构

```
release/
├── README.md                          # 本文件
├── INSTALL_GUIDE.md                   # AI 安装指南（面向 Copilot/Codex）
├── RELEASE_NOTE.md                    # 当前版本发布说明
├── COMMIT_MESSAGE_CN.md               # 中文 commit message 模板
├── COMMIT_MESSAGE_EN.md               # 英文 commit message 模板
├── verify_version_consistency.py      # 版本一致性校验脚本
├── doc_based_coding_runtime-*.whl     # runtime wheel
├── doc_loop_vibe_coding-*.whl         # instance wheel
├── doc-based-coding-*.vsix            # VS Code 扩展
└── doc-based-coding-v*.zip            # 可分发安装包（双 wheel + 安装指南）
```

## 最小验证门（来源：Dual-Package Distribution Standard）

### A. Clean Environment 安装验证

1. 只装 runtime → CLI 入口可发现、MCP 可启动、不依赖实例资产
2. 装 runtime + 实例 → 实例入口可发现、资产可读取、runtime 识别实例

### B. Adoption 验证

1. bootstrap 入口生成最小 scaffold
2. 校验入口验证 scaffold 和 project-local pack
3. 平台 runtime 在目标仓库内能恢复上下文

### C. Runtime Smoke

1. CLI: process / check / validate / info / generate-instructions
2. MCP: check_constraints / governance_decide
3. 无硬编码路径依赖

## Adoption 端到端验证结果（2026-04-12）

验证场景：空临时目录（无任何预置文件），从 zip 解压安装到完成 adoption 路径。

| 步骤 | 结果 |
|------|------|
| 解压 `doc-based-coding-v1.0.0.zip` | OK 3 个文件正确解压 |
| 在干净 venv 中安装双包 | OK runtime + 实例安装成功 |
| `doc-loop-bootstrap --target ./my-project --project-name "My New Project"` | OK 21 个文件生成，项目名自动注入 |
| `doc-based-coding info`（从新项目目录） | OK 正确发现 project-local pack（名称 "My New Project-local-pack"） |
| `doc-based-coding validate`（从新项目目录） | OK C5 正确报告"缺 planning-gate"阻塞（预期行为） |
| `doc-based-coding generate-instructions` | OK 完整 instructions 输出（含 C1-C8、conversation progression、external skill interaction） |
| MCP GovernanceTools 初始化 | OK 正确返回 pack info |
| MCP server 进程启动 | OK stdio 模式正常等待 JSON-RPC 输入 |
# Release 工作目录

## 目的

本目录用于存�?`doc-based-coding-platform` 双发行包的构建、验证与发布相关工作产物�?

## 双发行包结构

根据 `design_docs/tooling/Dual-Package Distribution Standard.md`，本项目分为两个发行包：

| �?| 名称 | pyproject.toml | 职责 |
|---|------|----------------|------|
| A | `doc-based-coding-runtime` | `./pyproject.toml` | 平台 runtime / CLI / MCP server |
| B | `doc-loop-vibe-coding` | `./doc-loop-vibe-coding/pyproject.toml` | 官方实例 pack 资产 |

依赖方向：B �?A（官方实例依�?runtime，runtime 不依赖实例）�?

## 当前状�?

- [x] pyproject.toml metadata 已定义（包名 / 版本 / 入口 / 依赖�?
- [x] 双发行包标准已固�?
- [x] v1.0.0 版本号已在两包中标记
- [x] 构建验证通过（双包均可成功构�?wheel / sdist，内容物完整�?
- [x] clean environment 安装验证通过（干净 venv 安装 �?CLI 入口可用 �?资产可发现）
- [x] adoption 端到端验证通过（空项目 bootstrap �?validate �?runtime info �?MCP 启动�?
- [x] 可分发安装包已打包（`doc-based-coding-v1.0.0.zip`，含 AI 安装指南�?
- [ ] 发布流程 / CI 配置

## 构建验证结果�?026-04-12�?

| �?| Wheel | 大小 | 文件完整�?| 入口�?|
|---|-------|------|-----------|--------|
| A: doc-based-coding-runtime | �?| 83KB | 62 .py 全部收入 | `doc-based-coding`, `doc-based-coding-mcp` |
| B: doc-loop-vibe-coding | �?| 48KB | 39 源文件全部收�?| `doc-loop-bootstrap`, `doc-loop-validate-doc`, `doc-loop-validate-instance` |

### 已修复问�?

- 构建产出�?`*.egg-info` 残留在项目根目录会导�?clean venv �?pip 误判包已安装、跳�?entry point 生成。已通过清理 egg-info 解决。`*.egg-info/` 已在 `.gitignore`�?

### 已知观察

- Runtime 包顶层包名为 `src`（`top_level.txt: src`），功能可用但与其他使用 `src` 命名的包存在潜在命名空间冲突。这是已有架构决定，不在当前切片内修改�?

## Clean Environment 安装验证结果�?026-04-12�?

验证环境：Python 3.12, 干净 venv (`.venv-release-test`)

| 步骤 | 结果 |
|------|------|
| 仅安�?runtime wheel | �?正常安装，依�?(jsonschema, mcp �? 自动拉取 |
| `doc-based-coding --help` | �?显示 5 条子命令 |
| `doc-based-coding info` | �?正确输出 pack 信息 |
| `doc-based-coding validate` | �?返回约束检查结�?|
| 追加安装 instance wheel | �?正常安装，runtime 依赖复用 |
| `doc-loop-bootstrap --help` | �?显示 bootstrap 参数 |
| `doc-loop-validate-instance` | �?所有检查项通过（manifest keys / path refs / schema examples�?|
| 安装态资产加�?| �?pack-manifest.json / bootstrap / references 均可�?site-packages 中读�?|

## 版本映射

本项目有三个独立版本化的组件�?

| 组件 | 当前版本 | 说明 |
|------|---------|------|
| VS Code Extension (`.vsix`) | `0.1.1` | 前端插件，独立版本线 |
| Runtime (`.whl`) | `0.9.4` | 平台 runtime / CLI / MCP server |
| Instance Pack (`.whl`) | `0.9.4` | 官方 doc-loop 实例资产 |

**兼容性规�?*�?
- Extension `0.1.x` 兼容 Runtime `0.9.x`
- Instance Pack `0.9.x` 版本需 �?Runtime 版本（如 Pack 0.9.4 需�?Runtime �?0.9.3�?
- 同一 release 批次的三个文件可组合使用
- **重要**：内容变更时版本号会递增，使�?`pip install <file>` 即可正常升级

## 目录结构

```
release/
├── README.md                          # 本文�?
├── INSTALL_GUIDE.md                   # AI 安装指南（面�?Copilot/Codex�?
└── doc-based-coding-v1.0.0.zip        # 可分发安装包（双 wheel + 安装指南�?
```

## 最小验证门（来源：Dual-Package Distribution Standard�?

### A. Clean Environment 安装验证

1. 只装 runtime �?�?CLI 入口可发现、MCP 可启动、不依赖实例资产
2. �?runtime + 实例 �?实例入口可发现、资产可读取、runtime 识别实例

### B. Adoption 验证

1. bootstrap 入口生成最�?scaffold
2. 校验入口验证 scaffold �?project-local pack
3. 平台 runtime 在目标仓库内能恢复上下文

### C. Runtime Smoke

1. CLI: process / check / validate / info / generate-instructions
2. MCP: check_constraints / governance_decide
3. 无硬编码路径依赖

## Adoption 端到端验证结果（2026-04-12�?

验证场景：空临时目录（无任何预置文件），�?zip 解压安装到完�?adoption 路径�?

| 步骤 | 结果 |
|------|------|
| 解压 `doc-based-coding-v1.0.0.zip` | �?3 个文件正确解�?|
| 在干净 venv 中安装双�?| �?runtime + 实例安装成功 |
| `doc-loop-bootstrap --target ./my-project --project-name "My New Project"` | �?21 个文件生成，项目名自动注�?|
| `doc-based-coding info`（从新项目目录） | �?正确发现 project-local pack（名�?"My New Project-local-pack"�?|
| `doc-based-coding validate`（从新项目目录） | �?C5 正确报告"�?planning-gate"阻塞（预期行为） |
| `doc-based-coding generate-instructions` | �?完整 instructions 输出（含 C1-C8、conversation progression、external skill interaction�?|
| MCP GovernanceTools 初始�?| �?正确返回 pack info |
| MCP server 进程启动 | �?stdio 模式正常等待 JSON-RPC 输入 |
