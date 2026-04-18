---
handoff_id: 2026-04-19_0128_extension-install-wizard-slice1_stage-close
entry_role: canonical
kind: stage-close
status: active
scope_key: extension-install-wizard-slice1
safe_stop_kind: stage-complete
created_at: 2026-04-19T01:28:00+08:00
supersedes: 2026-04-19_0114_vscode-extension-p0-p7-testing-and-release_stage-close
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
conditional_blocks:
  - phase-acceptance-close
  - code-change
  - dirty-worktree
other_count: 0
---

# Summary

Extension 安装/配置向导（Slice 1）全功能完成并通过 F5 双场景测试。wizard 在首次激活时自动检测 Python 环境，runtime 未安装时弹模态对话框引导从 release/ 目录 wheel 或 zip 安装，安装后自动启动 MCP 并生成 `.vscode/mcp.json` 使 VS Code 原生 MCP 集成可发现。

## Boundary

- 完成到哪里：planning-gate `2026-04-18-extension-install-wizard-slice1.md` 全部 scope 完成并关闭，含两处增强（release/ 自动检测 + mcp.json 生成）
- 为什么这是安全停点：wizard 全流程（检测→安装→启动→原生集成）均已 F5 测试通过，无编译错误，无待修 bug
- 明确不在本次完成范围内的内容：版本兼容性矩阵、自动更新/卸载、venv 自动创建、WebView 向导 UI

## Authoritative Sources

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/stages/planning-gate/2026-04-18-extension-install-wizard-slice1.md`
- `vscode-extension/src/setup/wizard.ts`
- `vscode-extension/src/extension.ts`

## Session Delta

- 本轮新增：`wizard.ts`、`pythonDetector.ts`、`runtimeInstaller.ts`
- 本轮修改：`extension.ts`（autoStart try-catch + mcp.json 生成）、`constraintDashboard.ts`（updateClient 方法）、`package.json`（setupWizard command + pythonPath/autoStart/serverArgs 配置）
- 本轮形成的新约束或新结论：pip install 必须批量执行避免本地 wheel 互相依赖解析失败；mcp.json 读取需 strip BOM

## Verification Snapshot

- 自动化：TypeScript `tsc --noEmit` 0 errors，esbuild production build 通过
- 手测：F5 验证两场景 — (1) 已安装环境自动启动 MCP 并写 mcp.json ✓ (2) clean venv 未安装环境弹模态向导 + zip 安装 ✓
- 未完成验证：Copilot Chat 调用原生 MCP 工具（用户确认列表显示"已停止"状态，按需启动正常）
- 仍未验证的结论：无

## Open Items

- 未决项：VS Code 原生 MCP 与 Extension 自有 MCPClient 双实例并存是否需要长期统一
- 已知风险：`python -m src.mcp.server` 依赖 wheel 打包含 `src` 包，路径改动会影响
- 不能默认成立的假设：无

## Next Step Contract

- 下一会话建议只推进：Checklist 中待办项（全局记忆/子 agent model 管理/硬编码 git 拦截）或新方向候选
- 下一会话明确不做：wizard 二期功能（版本兼容性矩阵、WebView UI）
- 为什么当前应在这里停下：planning-gate 已关闭，所有验证标准满足，用户确认可以继续推进其他方向

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Why This Stage Can Close

- 当前大阶段到这里可以结束的原因：planning-gate 中 5 项必做全部完成，4 项验证标准全部通过（全新环境向导弹出、zip 安装成功、MCP 自动启动、已安装环境跳过向导）
- 当前不继续把更多内容塞进本阶段的原因：向导二期（版本矩阵、WebView UI、自动更新）属于独立切片，不应与本 slice 合并

## Planning-Gate Return

- 应回到的 planning-gate 位置：无 active planning-gate（本 gate 已关闭）
- 下一阶段候选主线：Checklist 待办（全局记忆机制 / 硬编码 git 拦截 / 子 agent model 管理）或新方向候选
- 下一阶段明确不做：wizard slice 2

## Conditional Blocks

### phase-acceptance-close

Trigger:
planning-gate `2026-04-18-extension-install-wizard-slice1.md` 状态从 ACTIVE 改为 CLOSED

Required fields:

- Acceptance Basis: 4 项验证标准全部满足（全新环境向导弹出、zip 安装 + wheel batch install 通过、MCP 自动启动、已安装环境跳过向导直接启动）
- Automation Status: TypeScript 编译 0 error + esbuild production build 通过
- Manual Test Status: F5 双场景测试通过（已配置 + 未配置环境）
- Checklist/Board Writeback Status: Checklist 新增条目 + Phase Map 新增条目 + planning-gate 标记 CLOSED

Verification expectation:
下次 session 核对 Checklist VS Code Extension 区块末尾应有安装向导条目

Refs:

- `design_docs/stages/planning-gate/2026-04-18-extension-install-wizard-slice1.md`
- `design_docs/Project Master Checklist.md`

### code-change

Trigger:
新增 3 个 TypeScript 文件 + 修改 3 个已有文件

Required fields:

- Touched Files: `vscode-extension/src/setup/wizard.ts` (new), `vscode-extension/src/setup/pythonDetector.ts` (new), `vscode-extension/src/setup/runtimeInstaller.ts` (new), `vscode-extension/src/extension.ts` (modified), `vscode-extension/src/views/constraintDashboard.ts` (modified), `vscode-extension/package.json` (modified)
- Intent of Change: 实现首次激活安装向导 + 修复 autoStart 静默失败 + 添加 mcp.json 自动生成
- Tests Run: TypeScript `tsc --noEmit` 0 errors, esbuild build 通过, F5 手动双场景验证
- Untested Areas: 无自动化 TS 测试（Extension E2E 测试框架未搭建）

Verification expectation:
下次 session 运行 `npm run build` 应零错误

Refs:

- `vscode-extension/src/setup/`
- `vscode-extension/src/extension.ts`

### dirty-worktree

Trigger:
本轮所有代码变更尚未 git commit

Required fields:

- Dirty Scope: `vscode-extension/src/setup/` (3 new files), `vscode-extension/src/extension.ts`, `vscode-extension/src/views/constraintDashboard.ts`, `vscode-extension/package.json`, `design_docs/` (3 writeback)
- Relevance to Current Handoff: 全部是本切片的一手产出
- Do Not Revert Notes: 无需 revert，全部为有意变更
- Need-to-Inspect Paths: 无特殊关注

Verification expectation:
用户 commit 后此 block 自动失效

Refs:

- 本 handoff 所列 Touched Files

## Other

None.
