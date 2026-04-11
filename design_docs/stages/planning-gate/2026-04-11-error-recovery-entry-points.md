# Planning Gate — Error Recovery for Entry Points

- Status: **COMPLETED**
- Phase: 33
- Date: 2026-04-11

## 问题陈述

Phase 32 已定义首个稳定 release 的边界与收口清单。在考虑升级确认之前，用户选择先补齐入口面的错误处理。

当前调查发现三类问题：

1. **Pipeline 初始化无容错**：任何一个 pack manifest JSON 损坏就导致整个 CLI / MCP 服务崩溃。
2. **MCP 工具初始化无容错**：`GovernanceTools.__init__` 中 `Pipeline.from_project()` 异常直接传播，MCP 服务器无法启动。
3. **沉默失败**：pack 不存在时默认跳过无日志，用户不知道发生了什么。

已有的好模式（不需要改）：
- `PackRegistrar._load_module()` 和 `_register_validators()` 已做优雅降级 + skipped_details 诊断。
- `LLMWorker` / `HTTPWorker` 已有指数退避重试 + 结构化错误报告。
- `WritebackEngine.execute_plan()` 已将异常转为 `WritebackResult`。
- `ReviewStateMachine` 有自定义 `InvalidTransitionError`。

## 权威输入

- `docs/first-stable-release-boundary.md`
- `design_docs/Project Master Checklist.md`
- `src/workflow/pipeline.py`（Pack 发现与加载）
- `src/mcp/tools.py`（MCP 初始化）
- `src/__main__.py`（CLI 入口）
- `review/research-compass.md`

## 本轮只做什么

### Slice A: Pipeline 初始化容错

- `_discover_packs()` 中 `manifest_loader.load()` 加 try/except，损坏的 manifest 跳过并记录警告，不崩溃整个 Pipeline。
- `Pipeline.from_project()` 返回时携带 `warnings` 列表（或通过 logger 输出），告知哪些 pack 被跳过及原因。
- 测试：构造一个损坏 manifest + 一个正常 manifest → Pipeline 仍可初始化，warnings 包含跳过信息。

### Slice B: MCP 初始化容错

- `GovernanceTools.__init__` 中包裹 `Pipeline.from_project()` 异常，初始化失败时进入降级模式（Pipeline 为 None）。
- 降级模式下 `governance_decide` / `check_constraints` 返回结构化错误信息而非崩溃。
- 测试：模拟 Pipeline 构建失败 → MCP 工具返回诊断错误而非 traceback。

### Slice C: CLI `--debug` 模式

- 新增可选 `--debug` 标志，开启后错误输出包含完整 traceback（stderr）。
- 默认行为不变（简洁错误消息 + 退出码 1）。
- 测试：`--debug` 开启时 stderr 包含 traceback；关闭时仅显示错误消息。

## 本轮明确不做什么

- 不给 manifest_loader / Pipeline 加文件读取 retry（Worker 已有重试，入口面暂不需要）
- 不改变 PackRegistrar 的行为（Phase 31 已完善）
- 不改变 WritebackEngine / Worker 的错误处理
- 不引入新的全局异常类层次
- 不做结构化错误响应格式的全面统一（超出当前切片）

## 验收与验证门

- Pipeline 遇到单个损坏 manifest 时不崩溃，仍能加载其余合法 pack
- MCP 服务器在 Pipeline 初始化失败后仍可启动并返回诊断
- CLI `--debug` 模式显示 traceback
- 各 Slice 有对应的 targeted tests
- `pytest tests/` 全量通过无回归

## 需要同步的文档

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/handoffs/CURRENT.md`
- `.codex/checkpoints/latest.md`

## 收口判断

- 该切片只做入口面容错，不做全局错误格式统一
- 做到 Pipeline/MCP/CLI 三个入口不因单点故障崩溃就应收口
