# doc-based-coding 安装指南

本文档面向 AI 编程助手（Copilot、Codex 等），提供从零安装本平台的精确步骤。

## 概述

本发行包包含两个 Python wheel：

| 文件 | 包名 | 职责 |
|------|------|------|
| `doc_based_coding_runtime-1.0.0-py3-none-any.whl` | doc-based-coding-runtime | 平台 runtime / CLI / MCP server |
| `doc_loop_vibe_coding-1.0.0-py3-none-any.whl` | doc-loop-vibe-coding | 官方实例 pack（文档驱动工作流模板与资产） |

依赖关系：实例包依赖 runtime 包（`doc-based-coding-runtime>=1.0.0,<2.0.0`）。

## 前置要求

- Python >= 3.10
- pip >= 22.0

## 安装步骤

### 1. 创建虚拟环境（推荐）

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

### 2. 安装 runtime 包

```bash
pip install doc_based_coding_runtime-1.0.0-py3-none-any.whl
```

这将同时安装所有依赖（jsonschema、mcp 等）。

### 3. 安装官方实例包

```bash
pip install doc_loop_vibe_coding-1.0.0-py3-none-any.whl
```

由于 runtime 已安装，此步骤不会重复拉取依赖。

### 4. 验证安装

```bash
# 验证 runtime CLI
doc-based-coding --help

# 验证 runtime 能发现 pack
doc-based-coding info

# 验证约束检查
doc-based-coding validate

# 验证实例包 CLI
doc-loop-bootstrap --help
doc-loop-validate-instance --help
```

## 在项目中启用文档驱动工作流

### 方式 A：Bootstrap 新项目

在目标项目根目录中运行：

```bash
doc-loop-bootstrap --target /path/to/your/project --project-name "Your Project Name"
```

这将在目标目录中生成：
- `AGENTS.md` — agent 工作指令
- `design_docs/` — 状态板、阶段文档、工具标准
- `.codex/` — pack 配置、合同模板、提示词、handoff

### 方式 B：手动配置 MCP Server

在你的 VS Code 项目中创建或编辑 `.vscode/mcp.json`：

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
- `check_constraints` — 检查项目约束状态
- `governance_decide` — 对用户输入执行完整治理链
- `get_next_action` — 获取下一步建议行动
- `get_pack_info` — 查看已加载的 pack 信息
- `writeback_notify` — safe-stop 时获取必要写回清单

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
| MCP server 无法启动 | `doc-based-coding-mcp` 不在 PATH 中 | 使用绝对路径或确保 venv 已激活 |
| `pip install` 报 "already installed" | 项目根目录有残留的 `*.egg-info` | 删除 `*.egg-info` 目录后重试 |
