# Planning Gate — VS Code Extension P3 (Governance Interceptor)

> 创建时间: 2026-04-18
> 状态: COMPLETE

## 目标

将 PassthroughInterceptor 升级为真实 MCP-backed Governance Interceptor，实现文件保存前的自动治理检查。

## Scope

- [x] `vscode-extension/src/governance/interceptor.ts` — MCPGovernanceInterceptor 实现
  - 调用 MCP `governance_decide` 判断 ALLOW/BLOCK
  - MCP 不可用时 fallback 为 allow + warning log
  - Error 时 fallback 为 allow（不阻塞用户正常工作）
- [x] `registerGovernanceListeners()` — 注册 `onWillSaveTextDocument` 监听
  - BLOCK 时弹出 modal warning，用户可选 "Save Anyway" 或 "Cancel"
  - "Save Anyway" 记录用户 override 到 output channel
  - 只拦截 `file` scheme 文档（跳过 untitled/output 等）
- [x] `extension.ts` — 用 MCPGovernanceInterceptor 替换 PassthroughInterceptor
  - startMCPServer 时自动更新 interceptor 的 MCP client
- [x] esbuild 零错误

## 不做
- Terminal command 拦截（VS Code API 限制，需后续研究 shell integration）
- Review UI WebView（P4+）
- Override 记录写回 MCP decision logs（可在后续 slice 加入）

## 验证标准
- `npm run build` 零错误 ✅
- F5 启动后保存文件时，Output Channel 显示 governance_decide 调用日志
- 如果 governance_decide 返回 BLOCK，弹窗出现

## 依据
- `vscode-extension/src/governance/types.ts` — GovernanceInterceptor 接口
- P1 planning gate 中 "设计预留" 段已定义接口
