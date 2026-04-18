# Planning Gate — 硬编码禁止远程 git 操作

> 创建时间: 2026-04-19
> 状态: CLOSED
> 关闭时间: 2026-04-19
> 前置: 2026-04-18-extension-install-wizard-slice1.md (CLOSED)

## 目标

Terminal Monitor 层增加 pre-execution guard，在 governance interceptor 之前硬拦截 `git push`（唯一修改远程的操作），不可配置、不可 override。读取类远程操作（pull/fetch/clone）允许通过。

## Scope

### 必做
- [x] `vscode-extension/src/governance/gitRemoteGuard.ts` — 硬编码拦截规则
  - 正则匹配：`git push`、`git pull`、`git fetch`、`git remote`、`git clone`
  - 考虑子命令变体（如 `git remote add`、`git push --force`）
  - 考虑管道/引号/多命令组合（`git push; echo done` / `git push && ...`）
  - 返回 block + 固定拒绝消息（不依赖 MCP）
- [x] `TerminalGovernanceMonitor` 集成
  - 在 `onDidStartTerminalShellExecution` 回调中，先调 guard，再调 interceptor
  - Guard 命中时：立即 sendText Ctrl+C 终止 + 弹 error message（非 warning）
  - Guard 不命中时：继续原有 interceptor 逻辑
- [x] 不可绕过保证
  - 不检查任何配置项
  - 不调用 MCP server
  - 不接受 "Save Anyway" 或其他 override 机制
  - Guard 逻辑位于 Extension 进程内，不依赖外部服务
- [x] MCP `governance_decide` 同步拦截（bonus）
  - Python 侧 `src/mcp/tools.py` pre-check：`terminal-command: git push/pull/fetch/remote/clone` 返回 BLOCK
  - 双层防御 + 可观测性
- [x] VS Code SCM UI 拦截
  - `gitRemoteGuardScm.ts`：生成 git wrapper 脚本（.cmd/.sh），设置 workspace `git.path`
  - Wrapper 拦截 push/pull/fetch/remote/clone（exit 128）、放行其余操作
  - 实测验证：push/fetch → BLOCK, status/log → pass through

### 不做
- git 操作的白名单/豁免机制（如果未来需要，另开切片）
- git 本地操作拦截（commit / add / reset 等不拦截）

## 验证结果
1. ✅ 20/20 regex 单元测试通过（push/pull/fetch/remote/clone blocked; commit/status/add/log/diff/stash/branch/checkout allowed; 引号路径、compound 命令、drive letter）
2. ✅ MCP `governance_decide` 测试：push/pull/fetch → BLOCK; commit/status → ALLOW; non-terminal context → ALLOW
3. ✅ 1133 pytest 全通过，esbuild production build 通过
4. ✅ VSIX 0.1.2 已打包含 guard 代码

## 依据
- `design_docs/Project Master Checklist.md` → "硬编码禁止远程 git 操作"
- 安全约束：AI agent 不应在未经用户明确授权的情况下执行远程 git 操作
