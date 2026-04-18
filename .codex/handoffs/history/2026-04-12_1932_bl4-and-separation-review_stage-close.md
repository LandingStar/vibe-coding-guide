---
handoff_id: 2026-04-12_1932_bl4-and-separation-review_stage-close
entry_role: canonical
kind: stage-close
status: superseded
scope_key: bl4-and-separation-review
safe_stop_kind: stage-complete
created_at: 2026-04-12T19:32:43+08:00
supersedes: 2026-04-11_2348_handoff-model-initiated-invocation_stage-close
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
  - design_docs/stages/planning-gate/2026-04-12-temporary-rule-override.md
  - design_docs/stages/planning-gate/2026-04-13-driver-instance-separation-review.md
  - design_docs/direction-candidates-after-phase-35.md
  - docs/governance-flow.md
  - design_docs/tooling/Document-Driven Workflow Standard.md
conditional_blocks:
  - code-change
  - authoring-surface-change
  - dirty-worktree
other_count: 0
---

# Summary

两个 post-v1.0 切片已完成：BL-4（临时规则突破能力，3 个实施切片）和 driver/实例包分离审查（审查 + 1 个修复切片 + 1 个设计决策）。Checklist 中已无中/高优先级待办。

## Boundary

- 完成到哪里：BL-4 全部实施完毕（数据模型 + MCP tool + safe-stop 集成 + 权威文档）；driver/实例包分离审查完毕，唯一违规（runtime 硬编码实例路径）已修复。
- 为什么这是安全停点：Checklist 中所有中/高优先级 post-v1.0 项均已完成；剩余全为低优先级 gap analysis 或背景性 dogfood 项。
- 明确不在本次完成范围内的内容：Slice B 的 reference doc 放置策略讨论已决（保持现状）但未涉及实际迁移；低优先级 gap analysis 项（depends_on / provides / checks / overrides）未启动。

## Authoritative Sources

- `design_docs/Project Master Checklist.md` — Checklist 状态已更新，BL-4 和分离审查均标记完成
- `design_docs/Global Phase Map and Current Position.md` — 仍为 Phase 35 completed / v1.0 released
- `design_docs/direction-candidates-after-phase-35.md` — BL-4 已标记完成，已完成方向列表已更新
- `design_docs/stages/planning-gate/2026-04-12-temporary-rule-override.md` — COMPLETED
- `design_docs/stages/planning-gate/2026-04-13-driver-instance-separation-review.md` — COMPLETED

## Session Delta

- 本轮新增：`src/workflow/temporary_override.py`、`doc-loop-vibe-coding/references/temporary-override.md`、`tests/test_temporary_override.py`、`design_docs/stages/planning-gate/2026-04-12-temporary-rule-override.md`、`design_docs/stages/planning-gate/2026-04-13-driver-instance-separation-review.md`
- 本轮修改：`src/workflow/pipeline.py`（ConstraintResult.active_overrides）、`src/mcp/tools.py`（governance_override）、`src/mcp/server.py`（governance_override 注册）、`src/workflow/instructions_generator.py`（_temporary_override_section）、`src/workflow/safe_stop_writeback.py`（expire-temporary-overrides）、`src/workflow/external_skill_interaction.py`（移除硬编码实例路径，改为 pack-declared shipped_copies）、`.codex/packs/project-local.pack.json`（temporary_override rules + shipped_copies）、`doc-loop-vibe-coding/assets/bootstrap/.codex/packs/project-local.pack.json`（shipped_copies）、`docs/governance-flow.md`（Temporary Rule Override section）、`design_docs/tooling/Document-Driven Workflow Standard.md`（临时规则突破 section）、`tests/test_mcp_tools.py`（TestGovernanceOverride）、`tests/test_instructions_generator.py`（temporary override tests）、`tests/test_external_skill_interaction.py`（shipped_copies via rules）、`tests/test_external_skill_interaction_contract_surfaces.py`（load pack rules for drift-check）、`design_docs/Project Master Checklist.md`（BL-4 和分离审查标记完成）、`design_docs/direction-candidates-after-phase-35.md`（BL-4 完成状态）
- 本轮形成的新约束或新结论：C4/C5/C8 不可突破（non-overridable）；reference docs 保留在实例包作为面向消费者的 always_on 参考；runtime 中不应包含任何实例特定路径（shipped copies 通过 pack rules 声明）

## Verification Snapshot

- 自动化：651 passed, 2 skipped, 1 pre-existing failure (`test_error_recovery.py::TestMCPErrorInfoFormat::test_mcp_require_pipeline_uses_error_info` — GovernanceTools.__new__ 绕过 __init__ 导致 _project_root 缺失，与本轮变更无关)
- 手测：planning-gate 验证项逐条核对通过
- 未完成验证：无
- 仍未验证的结论：无

## Open Items

- 未决项：无
- 已知风险：pre-existing test failure 应在后续修复
- 不能默认成立的假设：无

## Next Step Contract

- 下一会话建议只推进：持续 pre-release dogfood（G）；若 dogfood 命中新信号则起新 planning-gate
- 下一会话明确不做：不应在无新信号的情况下启动低优先级 gap analysis 项
- 为什么当前应在这里停下：Checklist 中所有中/高优先级项已完成，当前无 active gate

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Why This Stage Can Close

- 当前大阶段到这里可以结束的原因：BL-4 和分离审查是 Checklist 中最后两个中/高优先级 post-v1.0 项，均已完成。
- 当前不继续把更多内容塞进本阶段的原因：剩余项全为低优先级或背景性，不构成同一阶段的必要延续。

## Planning-Gate Return

- 应回到的 planning-gate 位置：无 active planning-gate
- 下一阶段候选主线：G（持续 dogfood），仅在出现新信号时起新 gate
- 下一阶段明确不做：不启动低优先级 gap analysis 项（depends_on / provides / checks / overrides），除非 dogfood 中出现相关回归

## Conditional Blocks

### code-change

Trigger:
BL-4 新增了 `temporary_override.py` 模块和 `governance_override` MCP tool；分离审查修改了 `external_skill_interaction.py` 的 shipped copies 发现机制。

Required fields:

- Touched Files: `src/workflow/temporary_override.py` (NEW), `src/workflow/pipeline.py`, `src/mcp/tools.py`, `src/mcp/server.py`, `src/workflow/instructions_generator.py`, `src/workflow/safe_stop_writeback.py`, `src/workflow/external_skill_interaction.py`, `tests/test_temporary_override.py` (NEW), `tests/test_mcp_tools.py`, `tests/test_instructions_generator.py`, `tests/test_external_skill_interaction.py`, `tests/test_external_skill_interaction_contract_surfaces.py`
- Intent of Change: (1) 为对话中临时规则突破提供可追溯、可审计、可撤销的 runtime contract；(2) 消除 runtime 对实例包路径的硬编码依赖
- Tests Run: 651 passed, 2 skipped, 1 pre-existing failure
- Untested Areas: 无新增未测试区域

Verification expectation:
全量 pytest 通过（除 pre-existing failure）。BL-4 planning-gate 8 项验证均已检查。分离审查确认 `src/` 不再包含 `doc-loop-vibe-coding` 字面路径。

Refs:

- `design_docs/stages/planning-gate/2026-04-12-temporary-rule-override.md`
- `design_docs/stages/planning-gate/2026-04-13-driver-instance-separation-review.md`

### authoring-surface-change

Trigger:
新增 `governance_override` MCP tool，instructions generator 新增 `_temporary_override_section()`。

Required fields:

- Changed Authoring Surface: `governance_override` MCP tool (register / revoke / list)；instructions generator 输出新增 Temporary Rule Override section
- Usage Guide Sync Status: `docs/governance-flow.md` 已新增 Temporary Rule Override section；`design_docs/tooling/Document-Driven Workflow Standard.md` 已新增临时规则突破 section
- Discovery Surface Status: MCP tool 已在 `src/mcp/server.py` 注册，inputSchema 完整；pack rules 已声明 `temporary_override` 配置
- Authoring Boundary Notes: `governance_override` 仅操作 `.codex/temporary-overrides.json`，不修改 pack rules 或权威文档

Verification expectation:
MCP tool 测试（7 tests in TestGovernanceOverride）和 instructions generator 测试（2 temporary override tests）均已通过。

Refs:

- `src/mcp/server.py` — tool registration
- `src/mcp/tools.py` — GovernanceTools.governance_override()
- `docs/governance-flow.md` — Temporary Rule Override section

### dirty-worktree

Trigger:
本轮所有变更均未提交到 git。

Required fields:

- Dirty Scope: 上述 Session Delta 中列出的所有新增和修改文件
- Relevance to Current Handoff: 所有脏文件都是本轮工作产物，直接相关
- Do Not Revert Notes: 所有文件均为有意变更，不应回滚
- Need-to-Inspect Paths: 无需额外检查的路径

Verification expectation:
下一会话 intake 时应确认这些文件存在且内容与 handoff 描述一致。

Refs:

- 见 Session Delta 列表

## Other

None.
