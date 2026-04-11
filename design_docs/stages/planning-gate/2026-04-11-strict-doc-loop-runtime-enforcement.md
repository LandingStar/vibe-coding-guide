# Planning Gate Candidate — Strict Doc-Loop Runtime Enforcement

- Status: **COMPLETED**
- Owner: **main agent**
- Date: `2026-04-11`
- Phase Context: `Phase 35 v1.0 Stable Release Confirmation — 完成` 后的 post-v1.0 窄切片
- Upstream Decision Source:
  - [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md)
  - [design_docs/tooling/Document-Driven Workflow Standard.md](design_docs/tooling/Document-Driven Workflow Standard.md)
  - [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)

## 为什么现在做

- 当前 enforcement audit 已确认：runtime 级 `check_constraints()` 主要仍只机器检查 C4/C5，但 MCP tool/server 公开表述仍在暗示“结构化 enforce C1-C8”。
- 这会把“规则存在”与“runtime 已自动化检查”混为一谈，造成能力边界失真。
- 既然用户已经明确质疑“严格 doc-loop 规则是否真的生效”，下一步更合理的不是直接写一个庞大的对话审查器，而是先把 runtime 的真实可审计边界收口成明确 contract。

## 本切片要交付什么

1. 让 runtime constraint 结果显式区分：哪些约束是 machine-checked，哪些仍属于 instruction-layer / advisory-layer。
2. 让 MCP tool/server 的公开描述与真实运行时能力一致，不再笼统声称“结构化 enforce C1-C8”。
3. 为这条边界补齐 targeted tests，避免后续再次出现“文案说全检查，代码只检查部分”的漂移。

## 本切片明确不做什么

- 不实现完整的对话内容审计器。
- 不尝试自动判定每一轮回复是否满足“推进式提问”等纯对话层要求。
- 不把 C1-C8 全部强行塞进同一种 runtime 机制。
- 不顺手处理 MCP pack info 刷新一致性。

## 实施范围

- `src/workflow/pipeline.py`
  - 扩展 constraint result 的结构，使 runtime 能显式报告 machine-checked / instruction-layer boundary。
- `src/mcp/tools.py`
  - 调整 `check_constraints()` / `get_next_action()` 等 tool 输出与文档说明，使其和真实能力对齐。
- `src/mcp/server.py`
  - 调整 MCP tool 描述，避免继续宣称“结构化 enforce C1-C8”。
- `tests/test_pipeline.py`
- `tests/test_mcp_tools.py`
- 必要的文档与状态板回写。

## 验证门

- targeted tests 至少覆盖：
  - constraint result 会显式返回 machine-checked constraints
  - constraint result 会显式返回 instruction-layer / advisory constraints
  - MCP tools/server 对外文案不再误称 runtime 已完整 enforce C1-C8
- 相关修改文件无静态错误。

## 预计 write-back

- [design_docs/Project Master Checklist.md](design_docs/Project Master Checklist.md)
- [design_docs/Global Phase Map and Current Position.md](design_docs/Global Phase Map and Current Position.md)
- [.codex/checkpoints/latest.md](.codex/checkpoints/latest.md)
- 如有必要，刷新 [design_docs/direction-candidates-after-phase-35.md](design_docs/direction-candidates-after-phase-35.md)

## 收口判断

- 当 runtime 结果和 MCP 暴露面都能明确说清“哪些约束已机器检查、哪些仍不是 runtime enforce 范围”，并有 regression coverage 时，本切片即可收口。
- 到这里为止即可，不继续扩成完整 conversational rule engine。

## 执行结果

- `ConstraintResult` 现已显式区分 `machine_checked_constraints` 与 `instruction_layer_constraints`。
- runtime 现在会直接返回一条 `runtime_enforcement_summary`，明确当前只 machine-check C4/C5，C1/C2/C3/C6/C7/C8 仍属于 instruction-layer。
- MCP tools 与 server 的公开表述已改为“报告约束状态与 runtime coverage”，不再笼统声称结构化 enforce 全部 C1-C8。
- targeted tests 已覆盖新的 runtime boundary contract；`tests/test_checkpoint.py`、`tests/test_pipeline.py`、`tests/test_mcp_tools.py` 共 73 项通过。

## 本轮收口后的剩余边界

- 当前切片解决的是“runtime contract 要诚实且可审计”，不是“完整自动化对话规则审查”。
- 因此 runtime 仍不会自动判断每一轮回复是否满足推进式提问等纯对话层要求；这部分仍由上层 agent 指令与流程约束承担。