# Release 工作目录

## 目的

本目录用于存放 `doc-based-coding-platform` 双发行包、VS Code extension、发布验证与一体分发相关工作产物。

## 发行包结构

根据 `design_docs/tooling/Dual-Package Distribution Standard.md`，本项目的 Python 安装态分为两个发行包：

| # | 名称 | pyproject.toml | 职责 |
|---|------|----------------|------|
| A | `doc-based-coding-runtime` | `./pyproject.toml` | 平台 runtime / CLI / MCP server |
| B | `doc-loop-vibe-coding` | `./doc-loop-vibe-coding/pyproject.toml` | 官方实例 pack 资产 |

VS Code extension 是独立版本线；当前 release zip 会携带 VSIX 作为一体包成员，但 VSIX 版本不要求与 runtime 批次号一致。

## 当前状态

- [x] pyproject.toml metadata 已定义（包名 / 版本 / 入口 / 依赖）
- [x] 双发行包标准已固化
- [x] 当前 preview 版本号已在 runtime / instance / release 文档中同步到 `0.9.7`
- [x] VS Code extension 版本已推进到 `0.2.0`
- [x] graph engine 发布态依赖已固定为 `vscode-extension/vendor/note-web-knowledge-graph-engine-0.1.0.tgz`
- [x] 构建验证通过（双包均可成功构建 wheel，VSIX 可成功构建）
- [x] 可分发安装包已打包（`doc-based-coding-v0.9.7.zip`，含双 wheel、VSIX、graph engine 构建输入和安装指南）
- [ ] 发布流程 / CI 配置

## 版本映射

本项目当前有四个独立版本化的组件：

| 组件 | 当前版本 | 说明 |
|------|---------|------|
| Runtime (`.whl`) | `0.9.7` | 平台 runtime / CLI / MCP server |
| Instance Pack (`.whl`) | `0.9.7` | 官方 doc-loop 实例资产 |
| VS Code Extension (`.vsix`) | `0.2.0` | 前端插件，独立版本线 |
| Knowledge Graph Engine (`.tgz`) | `0.1.0` | 图谱组件，作为固定构建输入进入 release zip |

兼容性规则：

- Instance Pack `0.9.x` 版本需声明兼容 Runtime 范围
- Extension 可独立 bump，但 release note 必须显式记录 VSIX 版本
- Knowledge Graph Engine 独立 SemVer；VSIX 运行时必须自包含，不要求用户单独安装 npm 包
- 内容变更时版本号必须递增，不能复用已发布版本号

## 目录结构

```text
release/
├── README.md
├── INSTALL_GUIDE.md
├── RELEASE_NOTE.md
├── COMMIT_MESSAGE_CN.md
├── COMMIT_MESSAGE_EN.md
├── verify_version_consistency.py
├── doc_based_coding_runtime-*.whl
├── doc_loop_vibe_coding-*.whl
├── doc-based-coding-*.vsix
└── doc-based-coding-v*.zip
```

当前 `doc-based-coding-v0.9.7.zip` 内包含：

- `doc_based_coding_runtime-0.9.7-py3-none-any.whl`
- `doc_loop_vibe_coding-0.9.7-py3-none-any.whl`
- `doc-based-coding-0.2.0.vsix`
- `vscode-extension/vendor/note-web-knowledge-graph-engine-0.1.0.tgz`
- `INSTALL_GUIDE.md`
- `RELEASE_NOTE.md`
- `README.md`

## 最小验证门

### A. Clean Environment 安装验证

1. 只装 runtime → CLI 入口可发现、MCP 可启动、不依赖实例资产
2. 装 runtime + 实例 → 实例入口可发现、资产可读取、runtime 识别实例
3. 安装 VSIX → extension 可启动，progress graph preview 可打开

### B. Adoption 验证

1. bootstrap 入口生成最小 scaffold
2. 校验入口验证 scaffold 和 project-local pack
3. 平台 runtime 在目标仓库内能恢复上下文

### C. Runtime Smoke

1. CLI: process / check / validate / info / generate-instructions
2. MCP: check_constraints / governance_decide
3. 任一入口都不应依赖发布者源码工作区里的硬编码路径

### D. Graph Runtime Smoke

1. VSIX 包内应包含 `dist/webviews/progressGraphV2Engine.js`
2. VSIX 包内应包含 `dist/webviews/knowledgeGraphForceWorker.js`
3. VSIX 不应包含 `node_modules/` 或 `vendor/`
4. release zip 应包含 graph engine tarball 作为固定构建输入
