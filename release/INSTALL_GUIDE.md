# doc-based-coding 安装指南

本文档面向 AI 编程助手（Copilot、Codex 等），提供从零安装或升级本平台的精确步骤。

## 概述

本发行包包含两个 Python wheel、一个 VS Code VSIX，以及一个用于可复现构建的 graph engine npm tarball。

| 文件 | 包名 | 职责 |
|------|------|------|
| `doc_based_coding_runtime-0.9.8-py3-none-any.whl` | doc-based-coding-runtime | 平台 runtime / CLI / MCP server |
| `doc_loop_vibe_coding-0.9.8-py3-none-any.whl` | doc-loop-vibe-coding | 官方实例 pack（文档驱动工作流模板与资产） |
| `doc-based-coding-0.2.1.vsix` | doc-based-coding VS Code extension | VS Code 扩展，内含已构建的 graph webview runtime |
| `vscode-extension/vendor/note-web-knowledge-graph-engine-0.1.0.tgz` | @note-web/knowledge-graph-engine | 固定构建输入，用户安装时无需单独安装 |

依赖关系：实例包依赖 runtime 包（`doc-based-coding-runtime>=0.9.8,<1.0.0`）。

## 前置要求

- Python >= 3.10
- pip >= 22.0
- VS Code >= 1.93.0（如需安装 VSIX）

## 安装步骤

### 1. 解压 release zip

将 `doc-based-coding-v0.9.8.zip` 解压到一个临时目录。后续命令默认在该目录下执行。

### 2. 创建虚拟环境（推荐）

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 3. 安装 runtime 包

```bash
pip install --force-reinstall doc_based_coding_runtime-0.9.8-py3-none-any.whl
```

这将同时安装所有依赖（jsonschema、mcp 等）。

### 4. 安装官方实例包

```bash
pip install --force-reinstall --no-deps doc_loop_vibe_coding-0.9.8-py3-none-any.whl
```

由于 runtime 已安装，此步骤不需要重复解析 runtime 依赖。

> 本地离线安装提示：如果你希望让 pip 从当前目录自动查找依赖，也可以使用：
>
> ```bash
> pip install --force-reinstall --no-index --find-links . doc_loop_vibe_coding-0.9.8-py3-none-any.whl
> ```

### 5. 安装 VS Code 扩展

在 VS Code 中执行：

1. 打开 Extensions 视图
2. 选择 `...`
3. 选择 `Install from VSIX...`
4. 选择 `doc-based-coding-0.2.1.vsix`

也可以使用命令行：

```bash
code --install-extension doc-based-coding-0.2.1.vsix --force
```

Graph engine 已内嵌在 VSIX 的 `dist/webviews` 构建产物中。用户不需要安装 `@note-web/knowledge-graph-engine`，也不需要准备外部 graph engine 工作区。

## 验证安装

```bash
# 验证 runtime CLI
doc-based-coding --help

# 验证 runtime 能发现 pack（包括 pip 安装的官方实例 pack）
doc-based-coding info

# 验证约束检查
doc-based-coding validate

# 验证实例包 CLI
doc-loop-bootstrap --help
doc-loop-validate-instance --help
```

VS Code 侧验证：

1. 打开已采用 doc-loop 的工作区
2. 执行 `Doc-Based Coding: Open Progress Graph Preview`
3. 确认 `Knowledge Graph Engine` 图谱可见
4. 点击 `Refresh Graph`
5. 确认 refresh 后图谱会自动执行一次 `Shake Layout`

## 在项目中启用文档驱动工作流

### 方式 A：Bootstrap 新项目

在目标项目根目录中运行：

```bash
doc-loop-bootstrap --target /path/to/your/project --project-name "Your Project Name"
```

这将在目标目录中生成：

- `AGENTS.md`
- `design_docs/`
- `.codex/`

### 方式 B：手动配置 MCP Server

如果目标宿主是 Codex，应优先把 MCP server 注册到目标工作区自己的 `.codex/config.toml`，而不是依赖用户级 `~/.codex/config.toml` 中固定到某个项目的全局配置。用户级配置只适合个人通用默认值；项目采用 doc-based-coding 时，MCP 指向应随项目一起落在工作区配置中。

Windows / Codex 工作区级 `.codex/config.toml` 示例：

```toml
[mcp_servers.doc_based_coding_governance]
command = ".venv\\Scripts\\doc-based-coding-mcp.exe"
args = ["--project", "."]
cwd = "."
```

macOS / Linux 可写为：

```toml
[mcp_servers.doc_based_coding_governance]
command = ".venv/bin/doc-based-coding-mcp"
args = ["--project", "."]
cwd = "."
```

如果目标宿主是 VS Code / Copilot Chat，则在你的 VS Code 项目中创建或编辑 `.vscode/mcp.json`：

```json
{
  "servers": {
    "doc-based-coding-governance": {
      "type": "stdio",
      "command": "doc-based-coding-mcp",
      "args": ["--project", "${workspaceFolder}"]
    }
  }
}
```

MCP server 启动后，在 Copilot Chat 中可以调用以下治理工具：

- `check_constraints`
- `governance_decide`
- `get_next_action`
- `get_pack_info`
- `writeback_notify`

## 可用 CLI 命令一览

### Runtime（doc-based-coding）

| 命令 | 说明 |
|------|------|
| `doc-based-coding process <text>` | 对输入执行完整治理链（dry-run） |
| `doc-based-coding info` | 显示已加载的 pack 信息 |
| `doc-based-coding validate` | 检查项目约束状态 |
| `doc-based-coding check [text]` | 仅执行约束/状态检查 |
| `doc-based-coding generate-instructions` | 生成 copilot-instructions 片段 |

### 实例包（doc-loop-vibe-coding）

| 命令 | 说明 |
|------|------|
| `doc-loop-bootstrap` | 将文档驱动工作流脚手架复制到目标仓库 |
| `doc-loop-validate-doc` | 验证文档结构符合工作流标准 |
| `doc-loop-validate-instance` | 验证实例 pack manifest 与资产一致性 |

## 故障排查

| 问题 | 原因 | 解决 |
|------|------|------|
| `doc-based-coding` 命令不可用 | 虚拟环境未激活 | 运行 `activate` 脚本 |
| `doc-based-coding info` 无 pack 输出 | 未安装实例包，或项目中缺少 `.codex/packs/` | 安装实例包或运行 `doc-loop-bootstrap` |
| MCP server 无法启动 | `doc-based-coding-mcp` 不在 PATH 中 | 使用绝对路径或确认 venv 已激活 |
| VSIX 安装后图谱不可见 | 扩展未刷新或旧 VSIX 仍在运行 | 重新加载 VS Code 窗口，并确认扩展版本为 `0.2.1` |
| `pip install` 报 "already installed" | 项目根目录有残留的 `*.egg-info` | 删除 `*.egg-info` 目录后重试 |
