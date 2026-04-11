# Installation Guide

## 文档定位

本文件说明当前 `doc-based-coding-platform` 的**可执行安装流程**。

它回答的是：

- 如何安装平台 runtime 包
- 如何安装官方实例 `doc-loop-vibe-coding`
- 安装后如何做最小验证
- 如何把 MCP 以“安装态”方式接入 VS Code、Codex 等兼容客户端

它不定义远程 registry、发布自动化和 marketplace；当前仓库尚未固定这些分发层协议。

## 当前结论

截至当前仓库状态，平台已经具备双发行包的最小安装骨架：

- runtime 包：`doc-based-coding-runtime`
- 官方实例包：`doc-loop-vibe-coding`

当前最稳定的安装方式有两种：

1. 从源码 checkout 直接安装本地路径
2. 先构建 wheel，再把 wheel 分发给目标项目安装

当前**还没有**固定 PyPI / 私有源发布流程，因此本指南先只覆盖这两种本地/离线友好的安装方式。

## 安装前提

- Python `>=3.10`
- 目标项目应有独立虚拟环境
- pip 可以解析本仓库声明的第三方依赖

Windows PowerShell 示例：

```powershell
py -3.11 -m venv .venv
. .\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

macOS / Linux 示例：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

## 方式 A：从源码路径直接安装

如果你当前就持有本仓库 checkout，这是最直接的安装方式。

在仓库根目录运行：

```powershell
python -m pip install .
python -m pip install .\doc-loop-vibe-coding
```

这两步分别会安装：

- `doc-based-coding-runtime`
- `doc-loop-vibe-coding`

安装后应能获得以下命令入口：

- `doc-based-coding`
- `doc-based-coding-mcp`
- `doc-loop-bootstrap`
- `doc-loop-validate-doc`
- `doc-loop-validate-instance`

## 方式 B：先构建 wheel 再安装

如果你希望把安装源和使用环境分开，建议先构建 wheel。

在仓库根目录运行：

```powershell
python -m pip wheel . -w .\dist
python -m pip wheel .\doc-loop-vibe-coding -w .\dist
```

然后在目标环境安装：

```powershell
python -m pip install .\dist\doc_based_coding_runtime-1.0.0-py3-none-any.whl
python -m pip install .\dist\doc_loop_vibe_coding-1.0.0-py3-none-any.whl
```

这种方式适合：

- 团队内部分发
- 离线或半离线环境
- 在多个目标仓库重复安装同一组版本

## 最小安装验证

安装完成后，建议至少做 3 组验证。

### 1. 官方实例自检

```powershell
doc-loop-validate-instance
```

这会检查官方实例包的 manifest、示例和 bootstrap 资产是否自洽。

### 2. bootstrap + 项目接入验证

为某个目标仓库生成最小 scaffold：

```powershell
doc-loop-bootstrap --target <target-repo> --force
doc-loop-validate-doc --target <target-repo>
```

这两步会验证：

- 目标仓库是否成功生成最小 doc-loop scaffold
- project-local pack、合同模板、prompt 和长期文档是否齐全

### 3. runtime 命令可用性验证

进入已经 bootstrap 的目标仓库根目录后，运行：

```powershell
doc-based-coding info
doc-based-coding validate
```

如果目标仓库结构完整，这两条命令应能读取当前项目文档与 pack 信息，而不是依赖发布者源码工作区路径。

## MCP 安装态接入

### 当前 MCP 运行情况

当前 workspace 中的 MCP 工具是可用的：

- `check_constraints` 可正常返回当前 phase 与 active planning gate 状态
- `get_pack_info` 可正常返回已加载 pack 与触发器信息
- 当前工作区没有 MCP 约束阻塞

但要注意：本仓库中的 [../.vscode/mcp.json](../.vscode/mcp.json) 仍是**开发态配置**，它当前直接引用：

- workspace 内的 `.venv-mcp`
- 源码模块入口 `-m src.mcp.server`

这适合本仓库 dogfood，不应原样复制到安装态项目。

还要注意：如果你在这种开发态配置下直接修改了 `src.mcp.server`、`src.mcp.tools`、`src.workflow.pipeline` 等 MCP 相关源码，已连接的 MCP host 进程通常不会自动热重载。要验证最新行为，应先重启当前 MCP client / host，再重新发起工具调用，否则编辑器里看到的仍可能是旧进程结果。

但这条限制只针对源码热更新；对于 pack manifest、prompts、resources 等 workspace 内容变更，当前 MCP tools 已改为在每次调用前刷新 Pipeline，因此长生命周期进程中的后续调用应能看到最新磁盘状态。

### 安装态推荐方式

安装态项目应优先引用已经安装好的 `doc-based-coding-mcp` 入口。

这个入口并不依赖 Copilot 专有协议；凡是支持 stdio MCP server 的客户端，都应能复用同一条 server 启动命令。当前至少应按以下方式理解：

- VS Code / Copilot Chat：使用 workspace 级 `mcp.json` 指向安装后的 `doc-based-coding-mcp`
- Codex 或其他 MCP host：只要能配置 stdio server，同样应指向安装后的 `doc-based-coding-mcp` 与目标项目根目录
- 不应把 server 绑定成“只能由 Copilot 使用”的实现

Windows PowerShell / VS Code `mcp.json` 示例：

```json
{
  "servers": {
    "doc-based-coding-governance": {
      "type": "stdio",
      "command": "${workspaceFolder}/.venv/Scripts/doc-based-coding-mcp.exe",
      "args": [],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

macOS / Linux 示例：

```json
{
  "servers": {
    "doc-based-coding-governance": {
      "type": "stdio",
      "command": "${workspaceFolder}/.venv/bin/doc-based-coding-mcp",
      "args": [],
      "cwd": "${workspaceFolder}"
    }
  }
}
```

安装态配置应满足：

- 使用目标项目自己的虚拟环境
- 直接调用安装后的 `doc-based-coding-mcp`
- `cwd` 指向目标项目根目录
- 不再依赖发布者工作区中的 `src.mcp.server` 或固定 `.venv-mcp`
- 不依赖某个特定 MCP 客户端专有的源码路径约定

## 与 adoption 文档的关系

如果你的目标不是“在当前仓库里体验命令”，而是“把这套机制接到另一个真实项目”，请继续阅读：

- [project-adoption.md](project-adoption.md)
- [official-instance-doc-loop.md](official-instance-doc-loop.md)

其中：

- 本文解决“如何安装与启动入口”
- adoption 文档解决“安装后如何让一个真实仓库挂上来”

## 当前边界

本文件当前固定的是：

- 双发行包的实际安装方式
- 当前可用的命令入口
- 最小安装验证步骤
- MCP 安装态接入示例

本文件当前不固定：

- 远程包源地址
- 发布自动化流程
- 完整离线依赖镜像方案
- 多官方实例并存时的安装冲突求解