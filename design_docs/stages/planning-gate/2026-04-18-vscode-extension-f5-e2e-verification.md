# Planning Gate — VS Code Extension F5 端到端验证

> 创建时间: 2026-04-18
> 状态: CLOSED ✅
> 前置: 2026-04-18-vscode-extension-p0-p1.md (CLOSED)

## 目标

在 Extension Development Host 中真实运行 Extension，验证 MCP 连接、Dashboard 显示和 Activity Bar，修复运行时发现的问题。

## Scope

### 必做
- [x] `.vscode/launch.json` — Extension Host 调试配置（两个配置：Run Extension / Watch）
- [x] `.vscode/tasks.json` — watch task 添加 background problem matcher
- [x] F5 启动验证 — Extension 激活、Activity Bar 图标、MCP Server spawn
- [x] MCP 连接验证 — stdio JSON-RPC handshake 成功（initialize + tools/call + check_constraints）
- [x] Constraint Dashboard 验证 — TreeView 显示 C1-C8 状态
- [x] Pack Explorer 占位符确认 — P2 scope，显示 "Start MCP server to view packs" 符合预期

### 不做
- Pack Explorer TreeView 实现（P2）
- GovernanceInterceptor 实现（P2）
- 安装向导 / release 包装（下一 slice）
- Python runtime 代码改动
- 新增 MCP tool

## 验证标准
1. F5 启动 → Extension Development Host 窗口打开
2. Activity Bar 出现 doc-based-coding 图标
3. 点击图标 → 侧边栏显示 Constraint Dashboard 和 Pack Explorer 两个视图
4. Constraint Dashboard 调用 MCP `check_constraints` 并显示结果（或显示 server 未连接的合理状态）
5. Output Channel 显示 MCP 启动日志
6. 无 console error / 无 activation failure

## 依据
- `design_docs/direction-candidates-after-phase-35.md` §2026-04-18 候选 A
- `design_docs/stages/planning-gate/2026-04-18-vscode-extension-p0-p1.md` — P0+P1 已完成
- `vscode-extension/package.json` — Extension manifest
