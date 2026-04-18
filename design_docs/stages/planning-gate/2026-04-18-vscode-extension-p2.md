# Planning Gate — VS Code Extension P2

> 创建时间: 2026-04-18
> 状态: COMPLETE

## 目标

在 P0+P1 骨架上实现三项展示层功能：Pack Explorer 实化、Decision Log Viewer、Governance Status Bar。

## Scope

### 1. Pack Explorer 实化
- [x] `vscode-extension/src/views/packExplorer.ts` — 替换 placeholder 为真实 TreeDataProvider
- [x] 调用 MCP `get_pack_info` (level=manifest)，展示 pack name/kind/scope/provides/description
- [x] 子节点：provides capabilities + scope_paths
- [x] 刷新命令：`docBasedCoding.refreshPacks`

### 2. Decision Log Viewer
- [x] `vscode-extension/src/views/decisionLogViewer.ts` — 新增 TreeDataProvider
- [x] 调用 MCP `query_decision_logs` (limit=50)
- [x] 展示 timestamp / intent / decision(ALLOW|BLOCK) / trace_id
- [x] 刷新命令：`docBasedCoding.refreshDecisionLogs`
- [x] View 注册到 Activity Bar viewContainer

### 3. Governance Status Bar
- [x] `vscode-extension/src/views/statusBar.ts` — StatusBarItem
- [x] 显示 violation count（从 Constraint Dashboard 共享数据）
- [x] 点击跳转 Constraint Dashboard view

### 辅助修改
- [x] `package.json` — 新增 view、commands
- [x] `extension.ts` — 注册新 providers + status bar

## 不做
- WebView 详情面板（P3）
- Governance Interceptor 实施（P3+）
- Python runtime 改动

## 验证标准
- F5 启动后 Pack Explorer 展示真实 pack 列表（从 MCP 返回）
- Decision Log View 展示最近决策记录
- Status Bar 显示 constraint violation 数量
- `npm run build` 零错误

## 依据
- `design_docs/stages/planning-gate/2026-04-18-vscode-extension-p0-p1.md` — P1 scope 中预留的 P2 items
- `vscode-extension/src/mcp/types.ts` — 已定义 PackInfo / DecisionLogEntry 类型
