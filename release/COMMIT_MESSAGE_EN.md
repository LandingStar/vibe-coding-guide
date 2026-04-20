# Commit Message (English)

```
feat: v0.9.4 architecture compliance closure + Worker schema alignment

Module dependency direction enforcement + all cross-layer violations eliminated +
HTTPWorker report format aligned. B-REF series fully completed.
Multica architecture borrowing (4 items) all landed.
Release: doc-based-coding-v0.9.4.zip (192.4 KB)

## Added

- Module Dependency Direction Standard (6-layer architecture + direction rules doc)
- scripts/lint_imports.py: AST-based cross-package import direction linter
- src/pack/pack_discovery.py: pack discovery logic extracted (demoted from workflow)
- PLATFORM_INTENTS / IMPACT_TABLE / KEYWORD_MAP promoted to src/interfaces.py
- src/runtime/bridge.py: RuntimeBridge unified 3-entry init + WorkerHealth
- src/pack/pack_integrity.py: pack-lock.json + compute_pack_hash()
- src/pack/user_config.py: user-global config layer
- src/workflow/reply_progression.py + check_reply_progression MCP tool
- PackManifest consumes field + check_consumes() capability dependency check
- Conditional always_on loading (scope_path filtering)
- VS Code Extension Config UI (configExplorer / configPanel)
- MCP pack_lock / pack_unlock / pack_verify tools

## Fixed

- 3/3 cross-layer dependency violations eliminated (pack→workflow / pack→pdp types / pack→pdp constants)
- HTTPWorker._error_report() schema alignment (status: blocked + escalation: review_by_supervisor + unresolved_items)
- pack-lock hash mismatch regression (re-locked after consumes field addition)

## Improved

- B-REF-1~7 fully completed (progressive loading / description quality / pack organization / permission policy / workflow interrupt / context isolation / tool surface audit)
- VS Code Extension full feature set (P0-P7 + install wizard + git push guard + Chat Participant)
- Global memory/docs/rules support (user-global pack + config.json)
- Multica architecture borrowing landed (hash locking / conditional loading / RuntimeBridge / consumes)

## Verified

- pytest: 1257 passed, 2 skipped
- lint_imports.py: zero violations, zero known exceptions
- pack_verify: 2/2 packs ok
- VS Code Extension esbuild: zero errors
- MCP full toolchain dogfood passed

## Stats

- 36 files changed, +1159 -555
```
# Commit Message (English)

```
feat: v1.0.0 stable release + post-release verification

Phase 22-35 completed, v1.0.0 stable released.
Post-v1.0 direction candidates A-J all completed.
Release packaging passed full verification chain (build → install → empty-project adoption e2e).

## Core Milestones

- v0.1 dogfood release: Pipeline + MCP Server + Instructions Generator
- PackContext downstream wiring + deep dogfood verification
- MCP Prompts/Resources + Extension Bridging + on_demand lazy loading
- Dogfood feedback remediation (round 1 & 2)
- Stable release boundary confirmation + error recovery + structured error format unification
- v1.0.0 stable release confirmation

## Post-v1.0 Direction Candidates

- A: dual-package implementation (runtime + instance wheel)
- B: validator/check contract closure
- C: compatibility metadata & version declaration
- D: MCP pack info refresh consistency
- E: strict doc-loop runtime enforcement
- F: handoff model-initiated invocation
- H: external skill interaction interface
- I: safe-stop writeback bundle
- J: conversation progression contract stability

## Release Packaging Verification

- Dual-package build: runtime 83KB wheel + instance 48KB wheel
- Clean venv installation: all 5 CLI entry points functional
- Empty-project adoption: bootstrap → validate → MCP startup
- Distributable package: release/doc-based-coding-v1.0.0.zip (with AI-oriented install guide)

## Key New Files

- pyproject.toml (runtime + instance)
- src/mcp/ (MCP server + governance tools)
- src/workflow/ (pipeline, instructions, external skill, safe-stop writeback)
- doc-loop-vibe-coding/pyproject.toml + MANIFEST.in
- release/ (README, INSTALL_GUIDE, zip)
- .codex/handoff-system/ + .codex/handoffs/ + .github/skills/
- docs/first-stable-release-boundary.md
- docs/external-skill-interaction.md
- docs/installation-guide.md
- CHANGELOG.md
```
