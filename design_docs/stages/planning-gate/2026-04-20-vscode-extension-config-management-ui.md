# Planning Gate — VS Code Extension Config Management UI

> 创建时间: 2026-04-20
> 状态: COMPLETE
> 前置: P2 Pack Explorer (COMPLETE), User-Global Config Layer P1 (DONE)
> 研究基础: extension.ts / packExplorer.ts / reviewPanel.ts / mcp/client.ts 架构调研

## 目标

在 VS Code Extension 侧提供用户级全局配置（`~/.doc-based-coding/config.json`）的可视化管理能力，分两层实现：

- **Slice A**：TreeView 展示当前配置 + inline 编辑能力
- **Slice B**：Webview 表单面板，支持 pack-level / project-level 配置批量编辑

## 架构决策

1. **Slice A 复用 PackExplorerProvider 模式**：新增 `ConfigExplorerProvider` 实现 `TreeDataProvider`，通过 MCP `get_pack_info(level='full')` + `Pipeline.info()` 的 `user_config` 节获取数据
2. **Slice B 使用 WebviewViewProvider（侧边栏嵌入）**：非独立 WebviewPanel，复用 ReviewPanelProvider 的 CSP/nonce/escapeHtml 模式，但注册为 `WebviewViewProvider` 嵌入 Activity Bar
3. **配置写入路径**：Extension 通过新增 MCP tool (`update_user_config`) 写回 config.json，不直接操作文件系统
4. **热切换 MCP client**：与现有 provider 一致，实现 `updateClient(client)` 方法

## Scope

### Slice A — Config TreeView Explorer

- [x] `vscode-extension/src/views/configExplorer.ts` — 新增 TreeDataProvider
  - 顶层节点：Extension Settings / User-Global Config / Active Pack Config
  - Extension Settings 子节点：读取 `docBasedCoding.*` 配置项，显示 key=value
  - User-Global Config 子节点：从 MCP 获取 `user_config` 数据，显示 extra_pack_dirs / default_model / default_llm_params
  - Active Pack Config 子节点：从 `get_pack_info(level='full')` 获取 pack 列表及其 config
  - 刷新命令：`docBasedCoding.refreshConfig`

- [x] `vscode-extension/src/extension.ts` — 注册
  - `createTreeView('configExplorer', { treeDataProvider })` 
  - 注册 `docBasedCoding.refreshConfig` 命令
  - 注册 `docBasedCoding.editConfigItem` 命令（inline 编辑单项，通过 `showInputBox`）

- [x] `vscode-extension/package.json` — contributes 扩展
  - `views.doc-based-coding` 新增 `configExplorer` 条目
  - `commands` 新增 refreshConfig / editConfigItem
  - `menus.view/title` 新增 configExplorer 的 refresh 按钮
  - `menus.view/item/context` 新增 configExplorer 的 edit 按钮（contextValue='configEditable'）

- [x] Python 侧：新增 MCP tool `update_user_config`
  - 接受 `{ field: string, value: any }` 参数
  - 写入 `~/.doc-based-coding/config.json`
  - 返回更新后的完整 config

- [x] 测试
  - TreeView 刷新后显示三个顶层分组
  - editConfigItem 通过 MCP 写回后 TreeView 自动刷新
  - MCP tool `update_user_config` 的 Python 单元测试（6 cases）

### Slice B — Config Webview 表单面板

- [x] `vscode-extension/src/views/configPanel.ts` — WebviewViewProvider
  - 注册为 `vscode.window.registerWebviewViewProvider('configPanel', provider)`
  - HTML 表单：extra_pack_dirs（列表编辑）、default_model（输入框）、default_llm_params（JSON 编辑器）
  - postMessage 双向通信：load / save / saveResult / config
  - CSP: nonce-based，复用 reviewPanel.ts 的安全模式
  - 保存后自动触发 `docBasedCoding.refreshConfig` 同步 TreeView

- [x] `vscode-extension/package.json` — contributes 扩展
  - `views.doc-based-coding` 新增 `configPanel` 条目 (type: webview)

- [x] 测试
  - npm run build 零错误
  - Webview 加载后显示当前配置
  - 保存后 config.json 更新且 TreeView 同步刷新
  - 无效 JSON 输入在客户端侧被 validate 拦截

### 不做（后续）

- user_memory_dir / user_templates_dir 的 UI 管理
- default_rules_overlay 编辑
- config.json hot-reload / file watcher（由后续 slice 处理）
- 多 workspace 配置对比视图

## 验证标准

### Slice A
1. F5 启动后 Activity Bar 的 Doc-Based Coding 容器出现 Config Explorer view
2. 展示三个顶层分组，子节点正确反映当前配置
3. editConfigItem 命令可修改 extra_pack_dirs，修改后 TreeView 自动更新
4. `npm run build` 零错误

### Slice B
1. Activity Bar 中 configPanel 可见
2. 表单正确加载当前 config.json 内容
3. 保存操作通过 MCP tool 写回 config.json
4. `npm run build` 零错误

## 依据

- [2026-04-18-vscode-extension-p2.md](2026-04-18-vscode-extension-p2.md) — P2 TreeView 模式参考（COMPLETE）
- [2026-04-20-user-global-config-layer.md](2026-04-20-user-global-config-layer.md) — Python runtime config 层（DONE），其"不做"区列出本 gate
- `vscode-extension/src/views/packExplorer.ts` — TreeDataProvider 参考实现
- `vscode-extension/src/governance/reviewPanel.ts` — Webview CSP/通信 参考实现
- `vscode-extension/src/mcp/client.ts` — callTool 接口
