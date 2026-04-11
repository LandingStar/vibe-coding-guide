# Planning Gate — Post-v1.0 Doc-Loop Enforcement And MCP Client Neutrality

- Status: **COMPLETED**
- Date: 2026-04-11

## 当前问题

用户明确质疑当前仓库没有严格遵循 doc-loop 规则，这个判断有现实依据：

1. `check_constraints()` / `get_next_action()` 当前把 checkpoint 中的 `—` 当成了一个真实 active planning gate 字面值，导致无 planning gate 状态被误读。
2. project-local pack 的 C1 仍是旧文案，只写“禁止终止对话”，未同步到“未经用户显式许可才可例外”的最新正式规则。
3. MCP 运行时与安装文档中仍存在“偏向 Copilot”的叙述，尚未明确声明它应服务于任意支持 stdio MCP 的客户端，例如 Codex。

## 权威输入

- `design_docs/Project Master Checklist.md`
- `design_docs/tooling/Document-Driven Workflow Standard.md`
- `AGENTS.md`
- `.github/copilot-instructions.md`
- `.codex/packs/project-local.pack.json`
- `src/workflow/checkpoint.py`
- `src/workflow/pipeline.py`
- `src/mcp/tools.py`
- `src/mcp/server.py`
- `docs/installation-guide.md`

## 本轮只做什么

- 修正 active planning gate 空哨兵值 `—` 的读取与 next-action 判断。
- 同步 project-local pack 中的 C1 约束文案，使其与正式规则载体一致。
- 把 MCP 运行时与安装文档改成面向通用 MCP 客户端，而不是只暗示 Copilot。
- 为上述行为补 targeted tests。

## 本轮明确不做什么

- 不进入 MCP `get_pack_info` 的缓存刷新一致性切片
- 不扩展为完整对话级规则自动审计系统
- 不修改双发行包安装骨架或发布流程
- 不生成 handoff

## 验收与验证门

- 针对性测试：checkpoint / pipeline / MCP tool 层新增或更新的 targeted tests 通过
- 更广回归：现有 `tests/test_mcp_tools.py`、`tests/test_pipeline.py`、`tests/test_checkpoint.py` 不回归
- 手测入口：`check_constraints` 与 `get_next_action` 在无 active planning gate 时不再把 `—` 当作真实路径
- 文档同步：安装文档与 MCP 运行时说明明确支持通用 MCP 客户端

## 需要同步的文档

- `design_docs/Project Master Checklist.md`
- `.codex/checkpoints/latest.md`
- `docs/installation-guide.md`
- 如有需要，更新 `design_docs/Global Phase Map and Current Position.md`

## 子 agent 切分草案

- 当前不需要子 agent；这是一个紧耦合的小修复切片。

## 收口判断

- 当 `—` 哨兵值误判修复、C1 文案对齐、MCP 客户端中立表述落地且测试通过时，本切片即可收口。
- 做到这里就应停，不顺手扩成 MCP 缓存一致性或更大的规则引擎切片。

## 执行结果

- 已修复 checkpoint / pipeline / MCP tool 对 `—` active planning gate 哨兵值的误判。
- 已修复 `_check_constraints()` 对 checkpoint 的读取路径，使其不再错误地对项目根目录调用 `read_checkpoint()` 并退回异常分支。
- 已同步 `.codex/packs/project-local.pack.json` 中的 C1 文案，使其与当前正式规则载体一致。
- 已将 MCP 运行时与安装文档改成面向通用 MCP 客户端，而不是只暗示 Copilot。
- 已补充开发态说明：源码模式下修改 MCP 相关代码后，需要重启 MCP host 才能看到新行为。
- `tests/test_checkpoint.py`、`tests/test_pipeline.py`、`tests/test_mcp_tools.py` 的 targeted tests 共 71 项通过。

## 本轮发现但未在本轮继续扩做的缺口

- 当前 runtime 级 `check_constraints()` 仍然主要只机器检查 C4/C5；C1-C3、C6-C8 仍主要停留在规则/提示词层，而不是完整的运行时审计层。
- 这说明“严格 doc-loop 规则”目前属于“部分生效”：关键状态约束与 planning-gate 约束可检查，但对话级推进规则尚未被完整自动化强制。