# Planning Gate — VS Code Extension Runtime / Package Management Surface

> 日期: 2026-04-28
> 状态: COMPLETED
> 来源: 用户要求“插件中加入功能，能查看当前包的版本信息并选择卸载、重装、更新或禁用”

## Why this exists

当前 VS Code extension 已经具备：

1. setup wizard，可在缺少 runtime 时从 workspace `release/` 安装 wheel 或 release zip
2. MCP start / stop 命令与 `autoStart` 配置
3. Config Explorer / Config Panel / Pack Explorer 等侧边栏入口

但当前仍有一个明显缺口：

1. 插件里没有统一的“已安装运行时/实例包状态”视图
2. 用户无法直接看到当前 Python 环境里安装的是哪个 runtime / instance 版本
3. 已有安装流程偏向首次 setup，不适合高频执行“重装/更新/卸载”
4. “禁用”当前仍只能靠手工停服务或改配置，缺少明确的一键语义

因此，这条需求不应直接塞进当前 release-close 主线，而应单独收窄成新的 extension planning-gate。

## Scope

本 gate 只处理：

1. 在 VS Code extension 中提供一个最小 runtime / instance package management surface
2. 展示当前 extension 版本、Python 环境、runtime 版本、instance pack 版本、MCP server 运行状态与本地 `release/` 可用批次
3. 为当前 Python 环境提供最小操作：`reinstall`、`update`、`uninstall`、`disable`
4. 尽量复用现有 `setup/` 安装链路与配置/命令入口，而不是新建第二套安装系统

本 gate 不处理：

1. VS Code extension 自身的 VSIX 升级/卸载自动化
2. PyPI / 远程 registry 更新源管理
3. 多 Python 环境选择器或全局环境管理器
4. 通用包管理 UI 框架
5. 修改当前 active release-close handoff 状态面

## Working hypothesis

当前最小可行路线应是：

1. 复用现有 `Config Panel` webview，而不是新增一个新的长期侧边栏容器
2. 复用 `setup/pythonDetector.ts` 读取当前 Python + runtime 安装态，再补一层 instance pack 版本读取
3. `reinstall` / `update` 优先复用当前 `runtimeInstaller.ts`，只从 workspace `release/` 中的 wheel / zip 执行本地批次安装
4. `uninstall` 通过当前 Python 环境执行 `pip uninstall`，先移除 `doc-loop-vibe-coding`，再移除 `doc-based-coding-runtime`
5. `disable` 第一版只做 extension-local soft disable：停止当前 MCP server，并把 `docBasedCoding.autoStart` 设为 `false`，不等于卸载包

## Slices

### Slice 1 — Status surface and action semantics

- 固定需要展示的版本/状态字段
- 固定 `reinstall` / `update` / `uninstall` / `disable` 分别作用到哪一层
- 明确第一版是否需要改写 `.vscode/mcp.json`

当前状态：已完成；最小版 status surface 已接入现有 `Config Panel`，并固定第一版 `disable = stop server + autoStart=false`，未改写 `.vscode/mcp.json`。

### Slice 2 — Installer / uninstaller helper alignment

- 在现有 `setup/` 路径上补最小 helper，支持 installed-state refresh 与 uninstall
- 保持 release-local install source，不引入远程升级源

当前状态：已完成；现有 `setup/runtimeInstaller.ts` 已补 `force-reinstall` 支持，并新增 installed-state `runtimePackageManager` helper 与 `pip uninstall` 路径。

### Slice 3 — Config Panel integration and narrow validation

- 将 status + actions 接入现有 `Config Panel`
- 运行 `vscode-extension` 构建验证，并补最小交互级验证

当前状态：已完成；`Config Panel` 已展示 extension / Python / runtime / instance / server / local release batch 信息，并接入 `update` / `reinstall` / `uninstall` / `disable` 按钮；`npm run build` 已通过。

## Validation gate

- extension 可以在当前 workspace Python 环境中显示 runtime / instance / extension 三类版本信息
- `reinstall` / `update` / `uninstall` / `disable` 各自只作用于约定层面，不互相混淆
- `npm run build` 通过
- 若触及安装 helper，至少保留当前控制路径的最小可执行验证

## Stop condition

- 当状态面、动作语义、helper 对齐与 UI 接入都成立后停止
- 不在本 gate 内扩大到 VSIX 自升级、远程源更新或多环境管理