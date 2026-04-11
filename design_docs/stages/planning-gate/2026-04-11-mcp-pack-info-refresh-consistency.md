# Planning Gate Candidate — MCP Pack Info Refresh Consistency

- Status: **COMPLETED**
- Owner: **main agent**
- Date: `2026-04-11`
- Phase Context: `Phase 35 v1.0 Stable Release Confirmation — 完成` 后的 post-v1.0 窄切片
- Upstream Decision Source:
  - [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)

## 为什么现在做

- 当前 post-v1.0 的方向候选里，剩下的最小实现缺口主要就是 MCP 长生命周期进程对 pack state 的刷新一致性。
- 之前已观察到：fresh `Pipeline.from_project(...).info()` 能反映最新 manifest，但长生命周期 `GovernanceTools` 可能仍保留旧的 pack context。
- 这会让 `get_info()`，以及其他依赖 pack context 的 prompts/resources 视图，与磁盘现实脱节。

## 本切片要交付什么

1. 修复长生命周期 `GovernanceTools` 对 pack state 的刷新一致性，使同一个 MCP server 进程能在后续调用中看到最新 manifest / pack context。
2. 用 targeted tests 证明：同一 `GovernanceTools` 实例在磁盘上的 pack manifest 或 prompts 发生变化后，后续调用能读取到新状态。
3. 明确这个修复的边界：它解决的是 pack state 刷新，不解决源码变更后的 server 热重载。

## 本切片明确不做什么

- 不实现源码级热重载。
- 不改变 `.vscode/mcp.json` 的开发态模式。
- 不扩成通用文件监听器或后台 watch 机制。

## 实施范围

- `src/mcp/tools.py`
  - 修复或重构 `GovernanceTools` 的 pipeline 刷新策略。
- `tests/test_mcp_tools.py`
- `tests/test_mcp_prompts_resources.py`
- 相关状态文档 write-back。

## 验证门

- 同一 `GovernanceTools` 实例在 manifest 更新后，`get_info()` 可见新 state。
- 同一 `GovernanceTools` 实例在 prompts / resources 相关 manifest 更新后，可见新 state。
- targeted tests 通过，且相关文件无静态错误。

## 收口判断

- 当 pack state 刷新一致性在长生命周期 MCP tools 层被验证修复，并明确“源码改动仍需重启 host”后，本切片即可收口。

## 执行结果

- `GovernanceTools` 现已在每次 public tool 调用前刷新 Pipeline，因此长生命周期 MCP 进程里的 pack manifests / prompts / resources 视图会随磁盘状态更新。
- 这次修复解决的是 pack state refresh consistency，不是源码级热重载；源码改动仍需重启 MCP host。
- 已补充同一 `GovernanceTools` 实例在 manifest 更新后读取新 state 的回归测试。
- 已补充同一 `GovernanceTools` 实例在 prompts manifest 更新后读取新 prompt 列表的回归测试。
- 直接相关窄测试 4 项通过；相关代码文件无静态错误。