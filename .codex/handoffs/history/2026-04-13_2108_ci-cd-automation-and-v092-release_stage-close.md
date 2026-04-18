---
handoff_id: 2026-04-13_2108_ci-cd-automation-and-v092-release_stage-close
entry_role: canonical
kind: stage-close
status: superseded
scope_key: ci-cd-automation-and-v092-release
safe_stop_kind: stage-complete
created_at: 2026-04-13T21:08:03+08:00
supersedes: 2026-04-13_1139_hierarchical-pack-overrides-boundary-protocol_stage-close
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
  - design_docs/direction-candidates-after-phase-35.md
  - design_docs/tooling/Backlog and Reserve Management Standard.md
  - design_docs/stages/planning-gate/2026-04-13-ci-cd-build-release-automation.md
  - .codex/checkpoints/latest.md
  - CHANGELOG.md
  - issues/issue_doc_loop_v091_release_and_pack_discovery.md
conditional_blocks:
  - code-change
  - dirty-worktree
other_count: 0
---

# Summary

v0.9.1 issue 修复 + CI/CD 本地自动化脚本 + v0.9.2 release 完成。本轮从 dogfood 发现的 4 类问题出发，实现了 site-packages pack 自动发现的测试隔离、版本一致性检查、双包一键构建与打包脚本，并通过真实 version bump 验证了整套工具链的端到端可用性。

## Boundary

- 完成到哪里：v0.9.2 release 已产出（`release/doc-based-coding-v0.9.2.zip`，141.3 KB），CI/CD planning-gate COMPLETED，4 个 dogfood 发现全部修复
- 为什么这是安全停点：所有 planning-gate 验证项已通过（7/7），全量回归 803 passed / 2 skipped / 0 failures，release zip 内容验证完整
- 明确不在本次完成范围内的内容：远程 CI/CD（GitHub Actions）、PyPI 发布、自动 git tag、干净 venv 安装验证（下一步）

## Authoritative Sources

- `design_docs/Project Master Checklist.md` — 总状态板，已更新 dogfood #3/#4 和 CI/CD 条目
- `design_docs/stages/planning-gate/2026-04-13-ci-cd-build-release-automation.md` — CI/CD planning-gate (COMPLETED)
- `issues/issue_doc_loop_v091_release_and_pack_discovery.md` — v0.9.1 issue tracker（4/4 已关闭）
- `.codex/checkpoints/latest.md` — 最新 checkpoint
- `CHANGELOG.md` — v0.9.2 + v0.9.1+ci 条目

## Session Delta

- 本轮新增：`scripts/build.py`、`scripts/release.py`、`release/verify_version_consistency.py`、`design_docs/stages/planning-gate/2026-04-13-ci-cd-build-release-automation.md`、`release/doc-based-coding-v0.9.2.zip`
- 本轮修改：`src/workflow/pipeline.py`（`include_site_packages` 参数）、`src/mcp/tools.py`（同）、`tests/test_mcp_prompts_resources.py`（测试隔离）、`tests/test_mcp_tools.py`（同）、`tests/test_dual_package_distribution.py`（版本动态化）、`tests/test_official_instance_e2e.py`（同）、`pyproject.toml`（v0.9.2）、`doc-loop-vibe-coding/pyproject.toml`（同）、`doc-loop-vibe-coding/pack-manifest.json`（同）、`release/RELEASE_NOTE.md`（v0.9.2）、`release/INSTALL_GUIDE.md`（同）、`CHANGELOG.md`
- 本轮形成的新约束或新结论：(1) 测试中版本号应动态读取而非硬编码——已通过 `_read_canonical_version()` 修复。(2) `python -m build` 在隔离模式下受 PyPI 网络影响——`--no-isolation` 选项已加入 build/release 脚本。(3) `_discover_packs()` 的 site-packages 扫描在测试中需要显式关闭。

## Verification Snapshot

- 自动化：803 passed, 2 skipped, 0 failures（release.py 内置 pytest）
- 手测：build.py dry-run / full build / release.py dry-run / full release / version consistency check / wheel content verification — 全部通过
- 未完成验证：干净 venv 中 v0.9.2 wheel 安装验证（下一步执行）
- 仍未验证的结论：无

## Open Items

- 未决项：干净 venv 安装验证
- 已知风险：无
- 不能默认成立的假设：无

## Next Step Contract

- 下一会话建议只推进：干净 venv 中安装 v0.9.2 并验证 CLI 入口和资产可发现性
- 下一会话明确不做：不起新的能力实现 planning-gate（除非 dogfood 中出现新信号）
- 为什么当前应在这里停下：CI/CD 自动化与 v0.9.2 release 已完成，剩余是安装验证行为

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Why This Stage Can Close

- 当前大阶段到这里可以结束的原因：CI/CD planning-gate 全部 7 项验证门已通过，v0.9.2 release zip 已产出，dogfood 发现 #3 和 #4 已修复。
- 当前不继续把更多内容塞进本阶段的原因：安装验证是独立行为，不属于构建/打包自动化的 scope。

## Planning-Gate Return

- 应回到的 planning-gate 位置：无 active gate（继续 dogfood-only 节奏）
- 下一阶段候选主线：干净 venv 安装验证 → 继续受控 dogfood
- 下一阶段明确不做：不激活任何 BL 或 R 条目（除非 dogfood 命中触发条件）

## Conditional Blocks

### code-change

Trigger:
本轮涉及多文件代码变更：新增 CI/CD 脚本、修改 pipeline 和 tools 层、修改测试文件、version bump。

Required fields:

- Touched Files: `scripts/build.py` (NEW), `scripts/release.py` (NEW), `release/verify_version_consistency.py` (NEW), `src/workflow/pipeline.py` (modified), `src/mcp/tools.py` (modified), `tests/test_mcp_prompts_resources.py` (modified), `tests/test_mcp_tools.py` (modified), `tests/test_dual_package_distribution.py` (modified), `tests/test_official_instance_e2e.py` (modified), `pyproject.toml` (version bump), `doc-loop-vibe-coding/pyproject.toml` (version bump), `doc-loop-vibe-coding/pack-manifest.json` (version bump), `release/RELEASE_NOTE.md` (version bump), `release/INSTALL_GUIDE.md` (version bump)
- Intent of Change: (1) 解决 site-packages pack 自动发现在测试中的隔离问题。(2) 提供一键构建和打包的 CI/CD 脚本。(3) 把硬编码版本号改为动态读取。(4) 从 v0.9.1 bump 到 v0.9.2。
- Tests Run: 803 passed, 2 skipped, 0 failures（release.py 内含 pytest）
- Untested Areas: 干净 venv 安装验证

Verification expectation:
下一会话应在干净 venv 中安装 v0.9.2 wheel 并验证 CLI 入口。

Refs:

- `design_docs/stages/planning-gate/2026-04-13-ci-cd-build-release-automation.md`
- `issues/issue_doc_loop_v091_release_and_pack_discovery.md`

### dirty-worktree

Trigger:
version bump、新脚本、修改文件均未 commit。

Required fields:

- Dirty Scope: 上述所有 touched files + `release/doc-based-coding-v0.9.2.zip` + `dist/*.whl` + build 产物
- Relevance to Current Handoff: 全部与本轮变更直接相关
- Do Not Revert Notes: 不要丢弃 `scripts/build.py`、`scripts/release.py`、`release/verify_version_consistency.py`——这些是本轮的核心交付物
- Need-to-Inspect Paths: `dist/` 和 `release/` 下的 wheel 和 zip（应为 v0.9.2）

Verification expectation:
下一会话 intake 时应确认 wheel 文件名包含 `0.9.2`，release zip 同。

Refs:

- `pyproject.toml`（version = "0.9.2"）
- `doc-loop-vibe-coding/pack-manifest.json`（version: "0.9.2"）

## Other

None.
