# doc-based-coding v0.9.9 Preview Release (2026-07-12)

`v0.9.9` is the patch release that closes the installed-layout Subagent Report
contract defect found during the Spirebound full-workspace test. It also packages
the current readback, orchestration, workspace relay, and `.dbc` runtime-artifact
baseline before the project begins host-lifecycle inversion work.

This release does not implement Managed Mode or invert scheduler/orchestration
ownership around Codex. Direct Assistant Mode remains the active product path.
The Direct/Managed facility matrix is recorded as follow-up design work.

## Package Contents

| Artifact | Version | Notes |
|---|---:|---|
| `doc_based_coding_runtime-0.9.9-py3-none-any.whl` | 0.9.9 | Platform runtime, CLI, MCP server, orchestration and readback surfaces |
| `doc_loop_vibe_coding-0.9.9-py3-none-any.whl` | 0.9.9 | Official doc-loop instance and bootstrap contracts |
| `doc-based-coding-0.2.1.vsix` | 0.2.1 | Independently versioned Direct Assistant Host UX |
| `vscode-extension/vendor/note-web-knowledge-graph-engine-0.1.0.tgz` | 0.1.0 | Pinned graph engine build input |
| `doc-based-coding-v0.9.9.zip` | 0.9.9 batch | Release bundle with both wheels, VSIX, graph input, and installation docs |

## Highlights

### 1. Installed Worker Report Contract

- `consumeWorkerTrajectoryReport` now resolves
  `docs/specs/subagent-report.schema.json` from the target workspace supplied by
  `project_root`, not from the runtime module checkout or `site-packages/docs`.
- Schema loading is workspace-local on every consumption, so one long-lived
  process cannot reuse another workspace's schema.
- Missing or invalid workspace schema failures now identify the exact expected
  path and point operators back to the worker-report procedure.
- Official instance bootstrap now carries both
  `docs/worker-trajectory-update-reporting.md` and the Subagent Report schema.

### 2. Packaging And Installed-Layout Gate

- Instance wheel verification requires both worker-report bootstrap assets.
- The build installs both wheels into an isolated target, proves imports come
  from that target rather than the source checkout, bootstraps a temporary
  workspace, and consumes a valid worker report through the installed CLI.
- Any missing wheel member or failed installed-layout smoke now fails the build
  instead of producing a warning-only package.
- Pack integrity ignores root `build/` and `dist/` outputs so a wheel build does
  not invalidate the source pack lock; nested pack-owned content and source
  changes remain hash inputs.

### 3. Collaboration Evidence Semantics

- Multi-lane Local Work guidance now distinguishes logical lane decomposition,
  runtime worker dispatch, and retained auditable collaboration evidence.
- A lane count alone is no longer treated as proof of leader-worker execution or
  provider-level concurrency.
- Multi-lane leader-worker work must retain worker reports, ExchangeArtifact
  history, scheduler events, runtime invocation evidence, or an explicit
  orchestration blocker.

### 4. Current Runtime Baseline

- Includes unified readback inspection and explicit-source timeline projection,
  with CLI and MCP surfaces.
- Retains Codex and OpenCode worker runtime adapters, scheduler/daemon lifecycle,
  ExchangeArtifact admission/history, continuous worker bindings, sandbox and
  receipt evidence, workspace command relay, and `.dbc` runtime artifact roots.
- Worker trajectory mutation remains leader-owned; bounded workers report
  suggestions through `Subagent Report.trajectory_update`.

## Explicit Boundary

- Host inversion is not part of `0.9.9`.
- Managed Mode may later make DBC own the lifecycle below user-facing Codex CLI
  sessions and may omit VS Code support; that mode is not enabled here.
- OpenCode and additional CLI hosts remain adapter candidates for the later
  managed orchestration path.

## Verification

- `python release/verify_version_consistency.py`: passed
- `python scripts/scan_secrets.py --scope worktree`: passed
- focused worker-report consumer, bootstrap parity, lane guidance, and release
  version tests: passed
- `python scripts/release.py --no-isolation`: passed
  - built and verified both `0.9.9` wheels
  - passed the isolated installed-layout worker-report smoke
  - passed the full Python test suite: `2371 passed, 3 skipped`
  - packaged unchanged VSIX `doc-based-coding-0.2.1.vsix`
  - passed the pre-provisioned VS Code 1.93.1 Electron smoke gate
  - generated `release/doc-based-coding-v0.9.9.zip`

## Install Order

```bash
pip install --force-reinstall doc_based_coding_runtime-0.9.9-py3-none-any.whl
pip install --force-reinstall --no-deps doc_loop_vibe_coding-0.9.9-py3-none-any.whl
```

The VSIX already embeds the graph runtime. The graph engine tarball is included
for release provenance and reproducible extension builds, not as a separate user
installation step.
