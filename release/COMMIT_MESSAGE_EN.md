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
