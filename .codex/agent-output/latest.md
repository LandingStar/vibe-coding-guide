# Session Complete — VS Code Extension P0-P7 + Release v0.1.1

## Commit Message

```
feat(vscode-extension): complete P0-P7 + diagnostics + release v0.1.1

- P0: MCP stdio client for Python governance runtime
- P1: Constraint Dashboard TreeView
- P2: Pack Explorer + Decision Log viewer + Status Bar
- P3: File Save Interception (governance check before save)
- P4: Copilot Intent Classification via vscode.lm API
- P4+: BLOCK Explanation + Pack Generation
- P5: Review Panel WebView
- P6: Terminal Monitor via Shell Integration API (1.93+)
- P6+: File Lifecycle create/delete/rename interception
- P7: Chat Participant @governance with /check /decide /constraints /packs
- Runtime config: serverMode (auto/module/command) + 7-check diagnostics
- Fix ISSUE-001: bootstrap now creates initial planning-gate template
- Fix ISSUE-002: version mapping table + startup version logging
- Fix ISSUE-003: diagnostics warn on stale pythonPath
- Fix ISSUE-004: version bump 0.1.0->0.1.1, pack 0.9.3->0.9.4

Release artifacts:
  - doc-based-coding-0.1.1.vsix (22 KB)
  - doc_based_coding_runtime-0.9.3-py3-none-any.whl (131 KB)
  - doc_loop_vibe_coding-0.9.4-py3-none-any.whl (53 KB)
```

## Handoff

- Path: `.codex/handoffs/history/2026-04-19_0114_vscode-extension-p0-p7-testing-and-release_stage-close.md`
- Status: **active** (CURRENT.md already refreshed)
- Supersedes: `2026-04-18_0435_b-ref-1-slice1-planning-gate-and-code-confirm_stage-close`

## 下一步候选

1. UI 手测（Activity Bar / Review Panel / Terminal / File Lifecycle）
2. 全局记忆/文档/规则支持（跨工作区）
3. Multica 架构研究
4. 子 agent model 管理

## 使用方式

在 Copilot Chat 面板中输入:

- `@governance 这个项目当前有什么约束违规？` — 通用对话（带 governance context）
- `@governance /check` — 检查 C1-C8 约束状态
- `@governance /decide refactor the payment module` — 运行 governance 决策
- `@governance /constraints` — 查看详细约束信息
- `@governance /packs` — 列出已加载的 packs

## 架构

1. 用户在 Chat 中 @governance + 输入
2. Chat Participant handler 分派到子命令
3. 子命令通过 MCP Client 调用 Python governance runtime
4. 结果以 Markdown 流式返回到 Chat 面板
5. 通用对话: governance context 注入 + Copilot model 生成回答

## 前置条件

- MCP Server 需要在运行中（/check /decide /constraints /packs 子命令）
- Copilot 订阅需要有效（通用对话使用 request.model）
- 如果 MCP 未运行，会提示用户启动

## .vsix 状态

已重新打包 (19.55 KB) 并安装到本机。Reload Window 后即可使用 @governance。

## Extension 完整功能

P0 MCP | P1 Constraints | P2 Packs+Logs+StatusBar | P3 File Save | P4 Intent | P4+ AI | P5 Review | P6 Terminal | P6+ Lifecycle | **P7 Chat Participant** <-- NEW
