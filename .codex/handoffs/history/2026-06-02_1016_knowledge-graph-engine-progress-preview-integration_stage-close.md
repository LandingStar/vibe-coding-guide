---
handoff_id: 2026-06-02_1016_knowledge-graph-engine-progress-preview-integration_stage-close
entry_role: canonical
kind: stage-close
status: active
scope_key: knowledge-graph-engine-progress-preview-integration
safe_stop_kind: stage-complete
created_at: 2026-06-02T10:16:21+08:00
supersedes: 2026-05-12_0900_plugin-side-codex-host-support-gap_phase-close
authoritative_refs:
  - design_docs/Project Master Checklist.md
  - design_docs/Global Phase Map and Current Position.md
  - design_docs/stages/planning-gate/2026-05-27-knowledge-graph-engine-progress-preview-integration.md
  - design_docs/tooling/Semantic Versioning and Packaging Standard.md
  - design_docs/tooling/Dual-Package Distribution Standard.md
  - CHANGELOG.md
  - release/RELEASE_NOTE.md
conditional_blocks:
  - phase-acceptance-close
  - code-change
  - authoring-surface-change
  - dirty-worktree
other_count: 0
---

# Summary

本次 safe stop 收口 `Knowledge Graph Engine Progress Preview Integration` 的发布前清理和打包边界：VS Code progress graph preview 已以外部 `@note-web/knowledge-graph-engine` 为当前实现线，旧 G6 路线仅作为归档参考保留；本轮进一步清理了 active source/test 中的误导性 G6 残留、修正 progress graph 对 `SUPERSEDED / ARCHIVED REFERENCE` planning gate 的状态投影，并重建 `v0.9.7` release zip 与 `0.2.0` VSIX。当前可以安全停下，因为当前源码、dist、VSIX 和 release zip 都已验证不再携带 G6 运行链路。

## Boundary

- 完成到哪里：`vscode-extension` 当前 renderer 入口为 `progressGraphV2Engine`，VSIX 只包含 `extension/dist/extension.js`、`extension/dist/webviews/progressGraphV2Engine.js` 与 `knowledgeGraphForceWorker.js`；release zip 包含两个 `0.9.7` wheel、`doc-based-coding-0.2.0.vsix`、三份 release 文档和固定 graph engine tarball。
- 为什么这是安全停点：G6 残留已按运行链路、构建链路、当前生成物和发布包四层验证；旧 G6 gate 在 progress graph 中已投影为 `archived`，当前 active gate 指向 `2026-05-27-knowledge-graph-engine-progress-preview-integration.md`。
- 明确不在本次完成范围内的内容：没有继续修改外部 `knowledge-graph-engine` 源码；没有删除历史/记录性 G6 文档；没有激活插件侧 Codex host support proposed gate。

## Authoritative Sources

- `design_docs/stages/planning-gate/2026-05-27-knowledge-graph-engine-progress-preview-integration.md`
- `design_docs/tooling/Semantic Versioning and Packaging Standard.md`
- `design_docs/tooling/Dual-Package Distribution Standard.md`
- `CHANGELOG.md`
- `release/RELEASE_NOTE.md`
- `release/INSTALL_GUIDE.md`
- `release/README.md`

## Session Delta

- 本轮新增：active gate 末尾新增 `2026-06-02 G6 残留审计`；`.codex/checkpoints/latest.md` 更新为当前 KGE 发布与残留审计恢复点。
- 本轮修改：`vscode-extension/src/test/progressGraphColorGroups.test.ts` 去除 `"G6 work"` 测试夹具；`tools/progress_graph/doc_projection.py` 将 archived/superseded gate 映射为 `archived`；`tools/progress_graph/html_preview.py` 输出前去除 HTML 行尾空白；`.codex/progress-graph/latest.{json,dot,html}` 和 `control-snapshot.json` 已刷新。
- 本轮形成的新约束或新结论：G6 字样允许存在于历史/归档/替代路线记录中，但不得出现在 active source、dist、VSIX 运行内容或当前 active gate 投影中。

## Verification Snapshot

- 自动化：`python -m pytest tests/test_progress_graph_doc_projection.py tests/test_progress_graph_html_preview.py -q` 通过（8 passed）；`npm run build` 通过；`node --test dist/test/progressGraphPreviewHtml.test.js` 通过（3 passed）；`node --test dist/test/progressGraphColorGroups.test.js` 通过（1 file passed）；`node --test dist/test/aiChatToolLoop.test.js` 通过（4 passed）；`python release/verify_version_consistency.py` 通过。
- 手测：用 zipfile 检查 `release/doc-based-coding-v0.9.7.zip` 正好 7 个条目，包含 graph engine tarball；检查 `release/doc-based-coding-0.2.0.vsix` 无 `node_modules/`、`vendor/`、`archive/`、`progressGraphV2G6`、`progressGraphV2PoC` 条目，且无 `@antv/g6`、`progressGraphV2G6`、`progressGraphV2G6Config`、`progressGraphMotionControl` 字节命中。
- 未完成验证：未重新运行完整 pytest 大套件；release 脚本本轮使用 `--skip-tests --no-isolation`，只跑了本次切片相关 focused tests。
- 仍未验证的结论：未在真实 VS Code UI 里重复安装本轮重建后的 VSIX 做人工 smoke；包内容与构建结果已经验证。

## Open Items

- 未决项：是否在安装验证后正式分发/tag 当前 `v0.9.7` preview release。
- 已知风险：`.codex/handoffs/history/`、Phase Map、CHANGELOG `v0.9.6`、历史 requirements 中仍有 G6 文字，这是归档记录而非当前运行依赖；后续扫描时需继续按历史/active 边界区分。
- 不能默认成立的假设：不能假设外部 graph engine 的未来版本会自动兼容当前宿主；跨组件更新仍需通过需求文档、tarball 固定和 release consistency check。

## Next Step Contract

- 下一会话建议只推进：从安装验收或 release 分发/tag 开始，优先验证 `release/doc-based-coding-v0.9.7.zip` 与 `release/doc-based-coding-0.2.0.vsix` 的安装流程。
- 下一会话明确不做：不要回到 G6 renderer、G6 motion-control 或 `@antv/g6` 依赖上继续修补；不要把历史文档中的 G6 记录误删为“清理”。
- 为什么当前应在这里停下：当前发布批次已经重建并通过包边界检查；继续工作会进入安装验收/分发阶段，属于下一条窄线。

## Intake Checklist

- 核对 `authoritative_refs` 是否仍是当前有效入口。
- 核对当前 workspace 现实状态是否与 handoff 一致。
- 核对 `conditional_blocks` 是否与当前任务仍相关。
- 若存在 `Other`，逐条复核其归类理由。

## Why This Stage Can Close

- 当前大阶段到这里可以结束的原因：用户要求的新包已生成；G6 当前链路残留已审计并清理；KGE 作为当前图谱实现线的发布边界已固定。
- 当前不继续把更多内容塞进本阶段的原因：安装验收、tag/distribution、插件侧 Codex host support 都是独立后续线，继续混入会扩大当前发布清理切片。

## Planning-Gate Return

- 应回到的 planning-gate 位置：`design_docs/stages/planning-gate/2026-05-27-knowledge-graph-engine-progress-preview-integration.md`
- 下一阶段候选主线：安装验收与 release 分发/tag；或在用户改变优先级时回到 `2026-05-12-plugin-side-codex-host-support-gap.md` proposed gate。
- 下一阶段明确不做：不恢复 G6 当前实现路线，不把外部 graph engine 源码复制成长线 fork。

## Conditional Blocks

### phase-acceptance-close

Trigger:

当前为 KGE progress preview integration 的发布前 stage-close。

Required fields:

- Acceptance Basis: active source/dist/package 无 G6 运行链路；release zip/VSIX 已重建；SemVer 与 dual-package 发布规则已写入 tooling docs。
- Automation Status: focused Python/Node tests、extension build、version consistency、release packaging 均通过。
- Manual Test Status: 包内容与 VSIX 字节扫描通过；未做真实 VS Code UI 重装 smoke。
- Checklist/Board Writeback Status: active gate、checkpoint、progress graph artifacts 已同步；`CURRENT.md` 将由 refresh-current 轮转到本 handoff。

Verification expectation:

下一会话先复核 release 包路径和 CURRENT mirror，再进入安装验收。

Refs:

- `design_docs/stages/planning-gate/2026-05-27-knowledge-graph-engine-progress-preview-integration.md`
- `.codex/checkpoints/latest.md`
- `.codex/progress-graph/latest.dot`
- `release/doc-based-coding-v0.9.7.zip`

### code-change

Trigger:

本轮修改了测试夹具、progress graph 投影器和 HTML artifact writer。

Required fields:

- Touched Files: `vscode-extension/src/test/progressGraphColorGroups.test.ts`、`tools/progress_graph/doc_projection.py`、`tools/progress_graph/html_preview.py`、`tests/test_progress_graph_doc_projection.py`。
- Intent of Change: 清除 active test G6 误导文本；让 superseded/archived planning gate 正确投影为 `archived`；避免生成 HTML 带行尾空白。
- Tests Run: `pytest tests/test_progress_graph_doc_projection.py tests/test_progress_graph_html_preview.py -q`、`npm run build`、focused Node tests。
- Untested Areas: 未跑完整 pytest 大套件，未做 VS Code UI 重装 smoke。

Verification expectation:

若后续改动 progress graph 投影或 HTML writer，至少重跑上述 focused Python tests 并刷新 `.codex/progress-graph/latest.*`。

Refs:

- `tools/progress_graph/doc_projection.py`
- `tools/progress_graph/html_preview.py`
- `tests/test_progress_graph_doc_projection.py`

### authoring-surface-change

Trigger:

本轮更新了 release docs、CHANGELOG、tooling packaging standard、checkpoint 和 handoff 恢复入口。

Required fields:

- Changed Authoring Surface: `CHANGELOG.md`、`release/RELEASE_NOTE.md`、`release/INSTALL_GUIDE.md`、`release/README.md`、`design_docs/tooling/Semantic Versioning and Packaging Standard.md`、`design_docs/tooling/Dual-Package Distribution Standard.md`。
- Usage Guide Sync Status: release note 和 install guide 已说明 VSIX 自包含 graph runtime，用户不需要外部 graph engine 工作区。
- Discovery Surface Status: checkpoint 与 progress graph artifacts 已指向 KGE active gate；旧 G6 gate 在 current graph 中为 archived。
- Authoring Boundary Notes: 历史/归档 G6 表述保留，active 实现和发布包不得依赖 G6。

Verification expectation:

下一次发布前继续运行 `release/verify_version_consistency.py`，并检查 VSIX/release zip 内容边界。

Refs:

- `design_docs/tooling/Semantic Versioning and Packaging Standard.md`
- `design_docs/tooling/Dual-Package Distribution Standard.md`
- `release/RELEASE_NOTE.md`

### dirty-worktree

Trigger:

当前仓库有大量既有未提交/未跟踪变更；本 handoff 只覆盖 KGE 发布、G6 残留审计和相关生成物。

Required fields:

- Dirty Scope: 直接相关包括 `.codex/checkpoints/latest.md`、`.codex/progress-graph/*`、`.codex/handoffs/*`、`CHANGELOG.md`、`design_docs/stages/planning-gate/2026-05-27-knowledge-graph-engine-progress-preview-integration.md`、`tools/progress_graph/doc_projection.py`、`tools/progress_graph/html_preview.py`、`tests/test_progress_graph_doc_projection.py`、`vscode-extension/src/test/progressGraphColorGroups.test.ts`、release 包与 release docs。
- Relevance to Current Handoff: 这些路径构成本轮发布包和 G6 残留审计的真实状态面。
- Do Not Revert Notes: 不要回退外部图谱组件接入、vendor tarball、VSIX 包边界、release versioning 或历史 G6 归档文件；不要把无关 dirty 文件当成本 handoff 必须解决的问题。
- Need-to-Inspect Paths: `design_docs/stages/planning-gate/2026-05-27-knowledge-graph-engine-progress-preview-integration.md`、`.codex/checkpoints/latest.md`、`.codex/handoffs/CURRENT.md`、`release/doc-based-coding-v0.9.7.zip`、`release/doc-based-coding-0.2.0.vsix`、`vscode-extension/src/webviews/progressGraphV2Engine.ts`。

Verification expectation:

下一会话先用 `git status --short` 区分本 handoff 覆盖的 dirty scope 与其他并行工作，不要做 blanket revert。

Refs:

- `.codex/checkpoints/latest.md`
- `.codex/progress-graph/latest.dot`
- `release/doc-based-coding-v0.9.7.zip`

## Other

None.
