# doc-based-coding v0.9.8 Preview Release (2026-06-07)

This `v0.9.8` preview release closes the current Local Work Trajectory and host
coordination slice: the VS Code extension now packages the React Flow / ELK
local trajectory view, the MCP surface exposes the trajectory lifecycle, Codex is
restored as the primary supported host chain, and release builds now include
secret hygiene checks.

## Package Contents

| Artifact | Version | Notes |
|---|---:|---|
| `doc_based_coding_runtime-0.9.8-py3-none-any.whl` | 0.9.8 | Platform runtime, CLI, MCP server, PDP/PEP, workflow, pack runtime |
| `doc_loop_vibe_coding-0.9.8-py3-none-any.whl` | 0.9.8 | Official doc-loop instance pack |
| `doc-based-coding-0.2.1.vsix` | 0.2.1 | VS Code extension with built graph and Local Work Trajectory webview runtime |
| `vscode-extension/vendor/note-web-knowledge-graph-engine-0.1.0.tgz` | 0.1.0 | Pinned graph engine build input for audit and reproducible extension builds |
| `doc-based-coding-v0.9.8.zip` | 0.9.8 batch | Local release bundle containing the wheels, VSIX, graph engine tarball, and install docs |

## Highlights

### 1. Local Work Trajectory MVP

- Added the `localTrajectory` MCP lifecycle surface for starting, appending,
  advancing, opening lanes, merging lanes, and recording explicit relations.
- Added the VS Code Local Work Trajectory webview using React Flow + ELK.
- Added multi-line visual mapping for lane opening, merge/fan-in, dependencies,
  wait/sync/handoff style auxiliary relations, and lane labels.
- Kept Local Work Trajectory as a projection artifact, not the scheduler
  authority or a claim that lanes always equal real parallel agents.

### 2. Host Coordination And Codex Mainline

- Re-aligned durable rules so Codex remains the primary supported target chain:
  `AGENTS.md` + MCP + CLI/validation.
- Kept VS Code / Copilot as a Host UX Layer over the same backend rather than a
  replacement for Codex support.
- Extended host-side AI chat/tool loop integration and tests around tool result
  handling and progress graph panel behavior.

### 3. Secret Hygiene And Release Guardrails

- Added `scripts/scan_secrets.py` and release/build integration for worktree
  secret scanning.
- Added the Secret Hygiene and Log Redaction standard.
- Added scanner tests so high-confidence secrets are reported by detector and
  location without printing matched values.
- Refreshed `pack-lock.json` for the current official instance content.

### 4. Graph Runtime Packaging Boundary

- Preserved the pinned external `@note-web/knowledge-graph-engine` release-local
  tarball boundary from the previous graph integration work.
- The VSIX remains self-contained for graph webview renderer / worker runtime;
  users do not need a separate graph engine workspace or npm install.

## Verification

- `python release/verify_version_consistency.py`: passed
- `python scripts/scan_secrets.py --scope worktree`: passed
- `python -m pytest tests/test_doc_loop_prompts.py tests/test_error_recovery.py::TestPipelineInitResilience::test_no_warnings_when_all_packs_valid -q`: `3 passed`
- `python scripts/release.py --no-isolation`: passed
  - built both wheels
  - ran full Python test suite: `1432 passed, 3 skipped`
  - packaged VSIX `doc-based-coding-0.2.1.vsix`
  - generated `release/doc-based-coding-v0.9.8.zip`

## Install Order

```bash
pip install --force-reinstall doc_based_coding_runtime-0.9.8-py3-none-any.whl
pip install --force-reinstall --no-deps doc_loop_vibe_coding-0.9.8-py3-none-any.whl
```

Install the VS Code extension with "Install from VSIX" and select
`doc-based-coding-0.2.1.vsix`. The graph engine is already embedded in the VSIX
webview build output.
