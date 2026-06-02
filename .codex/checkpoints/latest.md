# Checkpoint — 2026-06-02T10:09:03+08:00
## Current Phase
Post-v1.0 — Knowledge Graph Engine progress preview integration, release packaging, and G6 residue audit
## Active Planning Gate
design_docs/stages/planning-gate/2026-05-27-knowledge-graph-engine-progress-preview-integration.md
## Current Handoff
- handoff_id: 2026-06-02_1016_knowledge-graph-engine-progress-preview-integration_stage-close
- source_path: .codex/handoffs/history/2026-06-02_1016_knowledge-graph-engine-progress-preview-integration_stage-close.md
- scope_key: knowledge-graph-engine-progress-preview-integration
- created_at: 2026-06-02T10:16:21+08:00
## Current Todo
- [x] Confirm active source and build entries no longer import `@antv/g6` or use `progressGraphV2G6` as a current renderer.
- [x] Keep the old G6 renderer, motion-control, and tests only under `vscode-extension/archive/g6-v2-graph-view-poc/`, excluded from VSIX.
- [x] Remove misleading active-source test fixture text that mentioned `G6 work`.
- [x] Record the 2026-06-02 G6 residue audit in the active Knowledge Graph Engine planning gate.
- [x] Refresh this checkpoint so progress graph generation no longer projects the old Sigma/G6 route as the current active line.
- [x] Refresh `.codex/progress-graph/latest.json`, `.dot`, `.html`, and `control-snapshot.json` from the current doc-loop state.
- [x] Run focused extension build/tests plus release version consistency validation.
- [x] Rebuild the v0.9.7 release zip and VSIX after the residue cleanup.
- [x] Verify packaged VSIX and release zip do not ship `node_modules/`, `vendor/`, `archive/`, `progressGraphV2G6`, or `@antv/g6`.
- [x] Generate and rotate a new safe-stop handoff only after validation and packaging are complete.
## Pending User Decision
(none)
## Direction Candidates
- Selected Line: Knowledge Graph Engine Progress Preview Integration — source: design_docs/stages/planning-gate/2026-05-27-knowledge-graph-engine-progress-preview-integration.md
- Packaging Rule: Component-independent SemVer plus host-pinned tarball and self-contained VSIX runtime — source: design_docs/tooling/Semantic Versioning and Packaging Standard.md
- Distribution Rule: Release zip carries wheels, VSIX, and graph engine tarball build input — source: design_docs/tooling/Dual-Package Distribution Standard.md
## Key Context Files
- design_docs/Project Master Checklist.md
- design_docs/Global Phase Map and Current Position.md
- .codex/handoffs/CURRENT.md
- .codex/handoffs/history/2026-06-02_1016_knowledge-graph-engine-progress-preview-integration_stage-close.md
- design_docs/stages/planning-gate/2026-05-27-knowledge-graph-engine-progress-preview-integration.md
- design_docs/tooling/Semantic Versioning and Packaging Standard.md
- design_docs/tooling/Dual-Package Distribution Standard.md
- CHANGELOG.md
- release/RELEASE_NOTE.md
- release/INSTALL_GUIDE.md
- release/README.md
- vscode-extension/src/webviews/progressGraphV2Engine.ts
- vscode-extension/src/views/progressGraphPreviewHtml.ts
- vscode-extension/src/test/progressGraphColorGroups.test.ts
- vscode-extension/esbuild.config.mjs
- vscode-extension/.vscodeignore
- vscode-extension/package.json
- vscode-extension/package-lock.json
- scripts/release.py
- release/verify_version_consistency.py
