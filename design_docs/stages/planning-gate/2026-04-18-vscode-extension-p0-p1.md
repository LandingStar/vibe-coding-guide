# Planning Gate — VS Code Extension P0+P1

> 创建时间: 2026-04-18
> 状态: ACTIVE

## 目标

创建 VS Code Extension 骨架（P0）+ Constraint Dashboard TreeView（P1）。

## Scope

### P0: Extension 骨架 + MCP Client ✅
- [x] `vscode-extension/package.json` — Extension manifest
- [x] `vscode-extension/tsconfig.json` — TypeScript 配置
- [x] `vscode-extension/esbuild.config.mjs` — 打包
- [x] `vscode-extension/src/extension.ts` — activate/deactivate
- [x] `vscode-extension/src/mcp/client.ts` — MCP stdio client（spawn Python server）
- [x] `vscode-extension/src/mcp/types.ts` — MCP tool TypeScript 类型
- [x] `vscode-extension/src/governance/types.ts` — GovernanceInterceptor 接口
- [x] `vscode-extension/src/governance/passthrough.ts` — MVP pass-through
- [x] `vscode-extension/src/llm/types.ts` — LLMProvider 接口
- [x] `vscode-extension/src/llm/copilot.ts` — vscode.lm 实现骨架

### P1: Constraint Dashboard TreeView ✅
- [x] `vscode-extension/src/views/constraintDashboard.ts` — TreeDataProvider
- [x] Activity Bar icon + View Container
- [x] 调用 MCP `check_constraints` 展示 C1-C8 状态

### 设计预留（不实现但定义接口）
- [x] GovernanceInterceptor.beforeFileWrite/beforeTerminalCommand/beforeAgentAction
- [x] ReviewPanel.requestReview
- [x] LLMProvider.classify/generate
- [x] 多 agent 并行可视化数据模型 (`AgentSession` 递归结构)
- [ ] 递归治理流程图渲染接口（需 WebView，下一阶段）

## 不做
- B-REF-4/5/6
- Python runtime 改动
- 完整的治理拦截实现
- Review UI WebView
- Pack Explorer TreeView（P2）

## 验证标准
- F5 启动 Extension，Activity Bar 出现图标
- Constraint Dashboard 显示 C1-C8 状态
- MCP Server 进程被正确启动和管理

## 依据
- `.codex/agent-output/latest.md` — Extension 架构设计
- `design_docs/stages/planning-gate/copilot-integration-runtime-simulation.md` — enforcement gap 分析
- `docs/platform-positioning.md` — 平台定位
- [VS Code Language Model API](https://code.visualstudio.com/api/extension-guides/language-model) — vscode.lm 文档
