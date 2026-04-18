---
handoff_id: 2026-04-12_2053_manifest-versioning-and-validate-fix_stage-close
entry_role: canonical
kind: stage-close
status: superseded
scope_key: manifest-versioning-and-validate-fix
safe_stop_kind: stage-complete
created_at: 2026-04-12T20:53:19+08:00
supersedes: 2026-04-12_1932_bl4-and-separation-review_stage-close
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
  - design_docs/stages/planning-gate/2026-04-13-pack-manifest-versioning.md
  - design_docs/stages/planning-gate/2026-04-13-validate-governance-vs-runtime-disambiguation.md
  - design_docs/direction-candidates-after-phase-35.md
  - docs/pack-manifest.md
  - release/INSTALL_GUIDE.md
conditional_blocks:
  - code-change
  - cli-change
  - authoring-surface-change
  - dirty-worktree
other_count: 0
---

# Summary

本轮完成 4 项工作切片：pack manifest schema 版本化、pre-existing test failure 修复、validate 命令治理阻塞 vs 运行失败语义区分、release zip 重打包。所有 planning-gate 已验证并标为 COMPLETED。全套测试 675 passed, 2 skipped, 0 failures。

## Boundary

- 完成到哪里：manifest_version 字段 + 版本感知 loader + 文档化；test failure 修复（refresh=False）；validate/check 退出码三级（0/1/2）+ JSON 新字段（command_status/governance_status/blocking_constraints）+ C5 初始状态降级为 warn + 终端文案改进；INSTALL_GUIDE.md 更新；release zip 重打包
- 为什么这是安全停点：所有 planning-gate 已 COMPLETED，全套 675 passed，无 in-progress 工作，release zip 已生成
- 明确不在本次完成范围内的内容：depends_on 依赖校验（低优先级 backlog）、provides/checks/overrides 字段消费、BL-1/BL-2/BL-3

## Authoritative Sources

- `design_docs/Project Master Checklist.md` — 已更新，含本轮所有完成项
- `design_docs/direction-candidates-after-phase-35.md` — 已更新 AI 倾向判断与已完成方向列表
- `design_docs/stages/planning-gate/2026-04-13-pack-manifest-versioning.md` — COMPLETED
- `design_docs/stages/planning-gate/2026-04-13-validate-governance-vs-runtime-disambiguation.md` — COMPLETED
- `docs/pack-manifest.md` — 已增加 Schema Versioning 节
- `release/INSTALL_GUIDE.md` — 已增加 validate 输出/退出码语义说明
- `review/research-compass.md` — "版本化 pack manifest 规范" 已标记为已填充

## Session Delta

- 本轮新增：`tests/test_manifest_versioning.py`（17 tests）、`manifest_version` 字段与版本感知 loader、validate 退出码 2 + JSON 新字段 + C5 初始状态降级
- 本轮修改：`src/pack/manifest_loader.py`、`src/workflow/pipeline.py`（ConstraintResult.to_dict + C5 降级）、`src/__main__.py`（validate/check 退出码 + 文案）、4 个 pack manifest JSON 文件、`docs/pack-manifest.md`、`release/INSTALL_GUIDE.md`、`tests/test_pipeline.py`、`tests/test_mcp_tools.py`（新增 6 个测试 + 更新 2 个）、`tests/test_cli.py`（新增 2 个）、`tests/test_error_recovery.py`（refresh=False fix）
- 本轮形成的新约束或新结论：(1) manifest_version major 不匹配→拒绝加载，minor 不匹配→警告继续；(2) CLI 退出码 0=通过/1=运行错误/2=治理阻塞；(3) C5 在初始状态（无 checkpoint/phase）降为 warn

## Verification Snapshot

- 自动化：675 passed, 2 skipped, 0 failures（pytest 全量）
- 手测：`python -m src validate` 在当前项目验证输出正确，退出码 0
- 未完成验证：未在独立干净 venv 中验证新 zip 安装态
- 仍未验证的结论：无

## Open Items

- 未决项：无
- 已知风险：初始状态下 JSON violations 列表仍含 C5 warn 条目，部分用户/agent 可能困惑为什么有 violation 但退出码 0（已在 INSTALL_GUIDE.md 说明）
- 不能默认成立的假设：无

## Next Step Contract

- 下一会话建议只推进：持续 dogfood / 视反馈起新 planning-gate；或从 Checklist 低优先级 backlog 中选择下一项（depends_on 依赖校验最推荐）
- 下一会话明确不做：不扩展 C5 降级到更多场景、不改 manifest_version 兼容策略
- 为什么当前应在这里停下：所有本轮切片已收口，planning-gate 已 COMPLETED，test baseline 已建立

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Why This Stage Can Close

- 当前大阶段到这里可以结束的原因：4 项工作切片全部通过验证门，无残留 in-progress 工作
- 当前不继续把更多内容塞进本阶段的原因：剩余 backlog 均为低优先级独立条目，与本轮切片无直接耦合

## Planning-Gate Return

- 应回到的 planning-gate 位置：当前无 active gate，进入 dogfood 背景模式
- 下一阶段候选主线：depends_on 依赖校验（Checklist gap #11）、其他 dogfood 反馈驱动的窄 gate
- 下一阶段明确不做：BL-1/BL-2/BL-3（均为"等触发条件"状态）

## Conditional Blocks

### code-change

Trigger:
manifest_version 字段 + 版本感知 loader + C5 初始状态降级 + validate/check 退出码三级 + ConstraintResult.to_dict() 新字段 + test fix

Required fields:

- Touched Files: `src/pack/manifest_loader.py`, `src/workflow/pipeline.py`, `src/__main__.py`, `tests/test_manifest_versioning.py`, `tests/test_pipeline.py`, `tests/test_mcp_tools.py`, `tests/test_cli.py`, `tests/test_error_recovery.py`, `.codex/packs/project-local.pack.json`, `doc-loop-vibe-coding/pack-manifest.json`, `doc-loop-vibe-coding/assets/bootstrap/.codex/packs/project-local.pack.json`, `doc-loop-vibe-coding/examples/project-local.pack.json`
- Intent of Change: (1) manifest schema 版本化使 loader 能检测不兼容格式变更 (2) validate 输出语义区分使 agent/用户不再把治理阻塞误判为运行失败 (3) C5 初始状态降级使新项目不被不必要阻塞
- Tests Run: 675 passed, 2 skipped, 0 failures（pytest 全量）
- Untested Areas: 安装态干净 venv 验证（已打包但未在本轮执行）

Verification expectation:
全套 pytest 通过，手动验证 validate 输出。

Refs:

- `design_docs/stages/planning-gate/2026-04-13-pack-manifest-versioning.md`
- `design_docs/stages/planning-gate/2026-04-13-validate-governance-vs-runtime-disambiguation.md`

### cli-change

Trigger:
validate/check 命令退出码从 1 改为 2（治理阻塞）、终端文案改进、help 文本增加退出码语义说明

Required fields:

- Changed Commands: `validate`、`check`、`--help`
- Help Sync Status: 已同步，增加了 Exit codes 三行说明
- Command Reference Sync Status: `INSTALL_GUIDE.md` 已更新，增加退出码语义表和 validate 输出说明
- CLI Regression Status: 5 个 CLI 测试通过（含 2 个新增）

Verification expectation:
`pytest tests/test_cli.py` 5 passed。手动 `python -m src validate` 退出码 0 确认。

Refs:

- `src/__main__.py`
- `release/INSTALL_GUIDE.md`
- `tests/test_cli.py`

### authoring-surface-change

Trigger:
`docs/pack-manifest.md` 增加 Schema Versioning 节；`release/INSTALL_GUIDE.md` 增加 validate 输出/退出码语义说明

Required fields:

- Changed Authoring Surface: `docs/pack-manifest.md`（manifest_version 字段 + Schema Versioning 节）、`release/INSTALL_GUIDE.md`（validate 输出/退出码表）
- Usage Guide Sync Status: 已同步
- Discovery Surface Status: 无新发现面变更
- Authoring Boundary Notes: manifest_version 仅影响 loader 行为，不影响 pack 语义能力声明

Verification expectation:
文档内容与代码实现一致，验证门已通过。

Refs:

- `docs/pack-manifest.md`
- `release/INSTALL_GUIDE.md`

### dirty-worktree

Trigger:
本轮所有变更均处于 uncommitted 状态

Required fields:

- Dirty Scope: 上述所有 touched files + planning-gate + Checklist + direction-candidates + release zip
- Relevance to Current Handoff: 全部为本轮有效变更，均在 handoff 覆盖范围内
- Do Not Revert Notes: 不可回滚任何 src/ 或 tests/ 变更
- Need-to-Inspect Paths: `release/doc-based-coding-v1.0.0.zip`（需确认打包内容完整）

Verification expectation:
下一会话 intake 时核查 workspace 现实与 handoff 一致。

Refs:

- 本 handoff 的 Session Delta 节

## Other

None.
