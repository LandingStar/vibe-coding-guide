# Planning Gate — Structured Error Format Unification

- Status: **COMPLETED**
- Phase: 34
- Date: 2026-04-11

## 问题陈述

Phase 33 补齐了入口面容错，但各入口面返回的错误格式不一致：

| 入口面 | 当前错误格式 | 问题 |
|--------|-------------|------|
| CLI | `"Error ...: {exc}"` 文本 → stderr | 纯文本，不可解析 |
| MCP `_require_pipeline()` | `{"error": "...", "message": "...", "suggestion": "..."}` | 有结构但字段名是 ad-hoc |
| Pipeline `init_warnings` | `list[str]` | 只有警告无错误分类 |
| Worker `_error_report()` | `{"status": "failed", "verification_results": [...]}` | 嵌套在 report schema 中 |
| WritebackEngine | `WritebackResult(success=False, error="...")` | dataclass，非 dict |
| ReviewStateMachine | `InvalidTransitionError` 异常 | 正确行为，不需统一 |

目标是给 Pipeline / CLI / MCP 三个入口面定义一个统一的 `ErrorInfo` 结构，使调用方（AI agent 或人）可以用相同的字段来判断错误类型和恢复建议。

## 权威输入

- `docs/first-stable-release-boundary.md`
- `design_docs/stages/planning-gate/2026-04-11-error-recovery-entry-points.md`
- `src/workflow/pipeline.py`
- `src/mcp/tools.py`
- `src/__main__.py`

## 本轮只做什么

### Slice A: ErrorInfo 数据结构

- 在 `src/workflow/pipeline.py`（或适当位置）新增 `ErrorInfo` dataclass：
  - `category`: str — 错误类别（`init_failed`, `manifest_invalid`, `constraint_violated`, `process_failed`, `unknown`）
  - `message`: str — 人可读的错误描述
  - `source`: str — 发生错误的组件（`pipeline`, `mcp`, `cli`, `pack_loader`）
  - `suggestion`: str — 恢复建议
  - `detail`: str — 可选的技术细节（默认空）
- `ErrorInfo.to_dict()` 输出标准化 JSON 格式。

### Slice B: Pipeline 集成

- `Pipeline._init_warnings` 改为 `Pipeline._init_errors: list[ErrorInfo]`（把字符串升级为结构化对象）。
- `Pipeline.info()` 输出 `init_errors` 列表（dict 形式）。
- 保持向后兼容：`init_warnings` property 仍返回 `list[str]`（从 `ErrorInfo.message` 提取）。

### Slice C: MCP / CLI 对齐

- MCP `_require_pipeline()` 改为返回 `ErrorInfo.to_dict()` 格式。
- CLI `_handle_error()` 的 stderr 输出保持不变（人可读文本），但如果 `--debug` 开启，额外输出 JSON 格式 ErrorInfo 到 stderr。

## 本轮明确不做什么

- 不改变 Worker / WritebackEngine / ReviewStateMachine 的错误格式（它们各自有合理的领域格式）
- 不引入全局异常类层次（ErrorInfo 是数据结构不是异常）
- 不改变 CLI 默认输出格式（保持简洁文本）
- 不添加 ErrorInfo JSON Schema（过早规格化）

## 验收与验证门

- `ErrorInfo` dataclass 可构造并序列化为 dict
- Pipeline `init_errors` 包含结构化错误信息
- MCP 降级模式返回 `ErrorInfo.to_dict()` 格式
- 向后兼容：`init_warnings` 仍可用
- 各 Slice 有 targeted tests
- 现有测试无回归

## 需要同步的文档

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `.codex/handoffs/CURRENT.md`
- `.codex/checkpoints/latest.md`

## 收口判断

- 做到三个入口面的错误输出共享相同字段名就应收口
- 不追求所有子系统错误格式统一
