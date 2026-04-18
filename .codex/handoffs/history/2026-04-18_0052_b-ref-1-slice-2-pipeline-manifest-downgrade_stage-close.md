---
handoff_id: 2026-04-18_0052_b-ref-1-slice-2-pipeline-manifest-downgrade_stage-close
entry_role: canonical
kind: stage-close
status: superseded
scope_key: b-ref-1-slice-2-pipeline-manifest-downgrade
safe_stop_kind: stage-complete
created_at: 2026-04-18T00:52:25+08:00
supersedes: 2026-04-17_2203_pack-reserved-interfaces-and-progressive-load-tests_stage-close
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
  - design_docs/stages/planning-gate/2026-04-17-b-ref-1-slice-2-pipeline-manifest-downgrade.md
  - design_docs/b-ref-1-pack-progressive-loading-direction-analysis.md
  - src/workflow/pipeline.py
  - src/pack/context_builder.py
  - src/pack/manifest_loader.py
  - tests/test_pack_progressive_load.py
conditional_blocks:
  - phase-acceptance-close
  - code-change
  - dirty-worktree
other_count: 0
---

# Summary

完成 B-REF-1 Slice 2：Pipeline MANIFEST 降级。`Pipeline._load_packs()` 从 `LoadLevel.FULL` 降级为 `LoadLevel.MANIFEST`，`pack_context` 属性按需 lazy-upgrade 到 FULL，`process_scoped()` 和 `info()` 均使用 MANIFEST 级别。新增 5 个 Pipeline 级别测试，全量基线 1087 passed, 2 skipped。本次会话累计完成：reserved interfaces 实现 + B-REF-1 Slice 1 测试覆盖（24 tests）+ B-REF-1 Slice 2 Pipeline 降级（5 tests）。

## Boundary

- 完成到哪里：B-REF-1 Slice 2（Pipeline MANIFEST downgrade）全部验收条件 6/6 已勾选
- 为什么这是安全停点：Pipeline 降级已生效且向后兼容（1087 passed），Slice 2 planning-gate 完整关闭，下一步 Slice 3（MCP Pack 选择）是独立可启动的新切片
- 明确不在本次完成范围内的内容：B-REF-1 Slice 3（MCP `get_pack_info` 分级返回 + description 驱动）、B-REF-2（description 质量标准）

## Authoritative Sources

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/stages/planning-gate/2026-04-17-b-ref-1-slice-2-pipeline-manifest-downgrade.md`
- `design_docs/b-ref-1-pack-progressive-loading-direction-analysis.md`
- `src/workflow/pipeline.py`
- `src/pack/context_builder.py`
- `src/pack/manifest_loader.py`
- `tests/test_pack_progressive_load.py`

## Session Delta

- 本轮新增：`TestPipelineManifestDowngrade` 类（5 个测试）、`LoadLevel` import 在 pipeline.py
- 本轮修改：`pipeline.py`（`_load_packs()` 降级 MANIFEST、`pack_context` lazy upgrade、`process_scoped()`/`info()` 使用 MANIFEST）、`test_pack_progressive_load.py`（新增 TestPipelineManifestDowngrade fixture + 5 tests）
- 本轮形成的新约束或新结论：Pipeline 初始化阶段不再需要 FULL load，规则合并只需 MANIFEST 级别数据；`pack_context` 属性是唯一触发 FULL upgrade 的入口

## Verification Snapshot

- 自动化：pytest 1087 passed, 2 skipped（全量回归零退化）
- 手测：无
- 未完成验证：MCP 工具层未测试（不在 Slice 2 scope）
- 仍未验证的结论：大规模 pack 场景下 MANIFEST-first 的 token 节省量（需要 Slice 3+ 实测）

## Open Items

- 未决项：B-REF-1 Slice 3（MCP Pack 选择 + description 驱动）、B-REF-2（description 质量标准）
- 已知风险：无
- 不能默认成立的假设：无

## Next Step Contract

- 下一会话建议只推进：B-REF-1 Slice 3 planning-gate 起草与实施，或从 direction-candidates-after-phase-35.md 选择其他方向
- 下一会话明确不做：回退 Pipeline 降级行为、修改 Slice 1/2 已通过的测试
- 为什么当前应在这里停下：Slice 2 是自然的功能边界——Pipeline 降级已完整生效，后续 MCP 层改动是独立 surface

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Why This Stage Can Close

- 当前大阶段到这里可以结束的原因：B-REF-1 Slice 2 所有 6 项验收条件已满足，Pipeline 降级实现 + 测试 + 全量回归全部通过
- 当前不继续把更多内容塞进本阶段的原因：Slice 3 涉及 MCP 工具层（不同 surface area）且依赖 B-REF-2 description 标准，应作为独立切片启动

## Planning-Gate Return

- 应回到的 planning-gate 位置：`design_docs/b-ref-1-pack-progressive-loading-direction-analysis.md` → Slice 3
- 下一阶段候选主线：B-REF-1 Slice 3（MCP `get_pack_info` 分级返回 + description 驱动选择）
- 下一阶段明确不做：回退 MANIFEST 降级、重构 Slice 1/2 已稳定的 API

## Conditional Blocks

### phase-acceptance-close

Trigger:
B-REF-1 Slice 2 planning-gate 验收条件 6/6 全部勾选完成

Required fields:

- Acceptance Basis: `design_docs/stages/planning-gate/2026-04-17-b-ref-1-slice-2-pipeline-manifest-downgrade.md` 6/6 checked
- Automation Status: pytest 1087 passed, 2 skipped
- Manual Test Status: 无手测需求
- Checklist/Board Writeback Status: Project Master Checklist 基线已更新为 1087; Phase Map 已追加 Slice 2 条目

Verification expectation:
全量回归通过，planning-gate 文档所有 checkbox 已勾选

Refs:

- `design_docs/stages/planning-gate/2026-04-17-b-ref-1-slice-2-pipeline-manifest-downgrade.md`
- `design_docs/Project Master Checklist.md`

### code-change

Trigger:
Pipeline.py 降级为 MANIFEST 加载 + pack_context lazy upgrade + 新测试

Required fields:

- Touched Files: `src/workflow/pipeline.py`, `tests/test_pack_progressive_load.py`
- Intent of Change: Pipeline 初始化从 FULL 降级为 MANIFEST，pack_context 属性按需升级到 FULL
- Tests Run: pytest 1087 passed, 2 skipped（含 5 个新 Pipeline 降级测试）
- Untested Areas: MCP 工具层的分级返回（Slice 3 scope）

Verification expectation:
全量回归通过，TestPipelineManifestDowngrade 5/5 通过

Refs:

- `src/workflow/pipeline.py`
- `tests/test_pack_progressive_load.py`

### dirty-worktree

Trigger:
本会话多个文件已修改但未 commit

Required fields:

- Dirty Scope: `src/workflow/pipeline.py`, `src/pack/pack_manager.py`, `tests/test_pack_progressive_load.py`, `tests/test_pack_manager_boundary.py`, planning-gate 文档, Checklist, Phase Map
- Relevance to Current Handoff: 全部与当前 handoff scope 直接相关
- Do Not Revert Notes: 所有改动均已通过全量回归，不应回退
- Need-to-Inspect Paths: 无需额外检查

Verification expectation:
下次会话 intake 时应确认 workspace 文件与 handoff 描述一致

Refs:

- `design_docs/Project Master Checklist.md`

## Other

None.
