# Slice 1 Draft — VS Code Extension Runtime / Package Management Surface

## Contract focus

本 Slice 只固定插件里“查看版本信息 + 执行动作”的最小合同，不进入 helper 实现。

## Current status

当前最小版合同已按推荐边界落地：

1. 现有 `Config Panel` 已新增 runtime / package status 区块
2. 当前已展示 extension version、Python path/version、runtime version、instance pack version、server running state、`autoStart`、`serverMode` 与 workspace `release/` artifacts
3. `update` / `reinstall` 当前都走 workspace-local release 安装批次，并通过 `force-reinstall` 覆盖同版本重装
4. `uninstall` 当前会对选中 Python 环境执行 `pip uninstall -y doc-loop-vibe-coding doc-based-coding-runtime`
5. `disable` 当前只做 soft disable：stop current MCP server + `docBasedCoding.autoStart = false`
6. 当前仍不改写 `.vscode/mcp.json`

验证：`vscode-extension` 的 `npm run build` 已通过。

## Recommended UI owner

当前推荐把这一面挂在现有 `Config Panel` webview 中，而不是新增新的 Activity Bar view。

理由：

1. 当前 extension 已有 setup wizard 负责首次安装，`Config Panel` 更适合承接安装后的日常管理
2. 现有侧边栏里没有其他更直接的运行时控制面
3. 这样可以把 `autoStart`、server 运行状态与包版本信息放在同一个操作上下文里

## Status fields

当前推荐至少展示：

1. extension version
2. selected Python path
3. Python version
4. runtime installed? / runtime version
5. instance pack installed? / instance version
6. MCP server running? / stopped?
7. detected local release artifacts（wheel / zip / VSIX）

## Action semantics

### Reinstall

- 含义：从当前 workspace `release/` 的本地批次重新安装 runtime + instance 包
- 作用层：当前选中的 Python 环境
- 当前推荐：复用现有 `runtimeInstaller` 本地安装链，不新建远程源逻辑

### Update

- 含义：若 workspace `release/` 中存在较新批次，则按当前本地批次重新安装；若没有更高版本，则退化为同版本 reinstall
- 作用层：当前选中的 Python 环境
- 当前推荐：第一版不接 PyPI；只做 workspace-local release update

### Uninstall

- 含义：从当前选中的 Python 环境移除 instance + runtime 包
- 作用层：当前 Python 环境
- 当前推荐顺序：先卸载 `doc-loop-vibe-coding`，再卸载 `doc-based-coding-runtime`

### Disable

- 含义：禁用 extension 对当前环境的自动接入，而不是卸载包
- 当前推荐语义：
  1. stop current MCP server
  2. set `docBasedCoding.autoStart = false`
- 当前不等于：
  1. pip uninstall
  2. 删除 wheel 文件
  3. 自动移除 `.vscode/mcp.json` entry

## Decision fork

### A. Soft disable only

- 做什么：停止 server + 关闭 `autoStart`
- 优点：最可逆，也最不容易破坏用户已有 MCP 注册面
- 当前判断：推荐

### B. Disable plus rewrite `.vscode/mcp.json`

- 做什么：除 stop + `autoStart=false` 外，再移除或改写 native MCP entry
- 风险：会直接修改用户的 workspace 配置文件，第一版过重
- 当前判断：不推荐作为第一刀

## Out of scope

1. VSIX 自更新或卸载
2. 多环境选择器
3. 远程版本源发现
4. 通用 package manager 抽象