# Planning Gate — Extension 安装/配置向导 Slice 1

> 创建时间: 2026-04-18
> 状态: ACTIVE
> 前置: 2026-04-18-vscode-extension-f5-e2e-verification.md (CLOSED)

## 目标

Extension 首次激活时提供安装配置向导：检测 Python Runtime 状态、引导从 release.zip 安装、自动配置路径。

## Scope

### 必做
- [ ] `vscode-extension/src/setup/wizard.ts` — 安装向导核心逻辑
  - 检测 Python 是否可用（复用 resolvePythonPath + 验证 MCP server module 可加载）
  - 检测 Runtime 版本（`python -m src.mcp.server --version` 或 `doc-based-coding --version`）
  - 如未安装：引导用户选择 release.zip → 解压 → pip install wheels
  - 安装后自动写入 `docBasedCoding.pythonPath` 设置
- [ ] `vscode-extension/src/setup/pythonDetector.ts` — Python 环境检测
  - 检查 workspace venv、系统 Python、ms-python 扩展 Python
  - 验证 Python 版本 >= 3.10
  - 验证 doc-based-coding-runtime 是否已安装
- [ ] `vscode-extension/src/setup/runtimeInstaller.ts` — Runtime 安装器
  - 解压 release.zip 到临时目录
  - 执行 `pip install *.whl`（按正确顺序：runtime 先，instance 后）
  - 安装结果验证
- [ ] Extension activate 中集成：首次激活 → 检测 → 未就绪则触发向导
- [ ] `docBasedCoding.setupWizard` command — 手动触发入口

### 不做（下一 slice）
- 版本兼容性矩阵校验（Extension v ↔ Runtime v）
- 自动更新/卸载
- venv 自动创建
- WebView 向导 UI（本 slice 用 QuickPick + Progress 实现）

## 验证标准
1. 全新环境 F5 → 提示 Python Runtime 未安装 → 引导安装
2. 选择 release.zip → 自动安装两个 wheel → `docBasedCoding.pythonPath` 自动配置
3. 安装后 MCP server 自动启动 → Constraint Dashboard 显示数据
4. 已安装环境 F5 → 跳过向导，直接启动

## 依据
- `design_docs/direction-candidates-after-phase-35.md` 候选 F
- `release/doc-based-coding-v0.9.3.zip` — 安装产物
- `release/INSTALL_GUIDE.md` — 安装步骤参考
