# Review - Electron Webview Runner Spike

> Date: 2026-06-19
> Planning Gate: `design_docs/stages/planning-gate/2026-06-19-electron-webview-runner-spike.md`

## Summary

Reviewed the narrow Electron runner spike for the VS Code Progress Graph
Preview Host UX.

The implementation adds a real VS Code Electron extension-test runner that
creates a deterministic fake workspace, opens the Progress Graph Preview
command, and probes the latest rendered webview HTML through a test-only
extension command. The runner is intentionally fake-runtime-only and does not
expand scheduler provider execution, daemon behavior, or trajectory mutation.

The current local Electron smoke did not produce rendered evidence because the
installed VS Code is blocked by its update mutex before extension tests start.

## Implemented Runner

- `vscode-extension/src/electron-test/suite/index.ts`
  - Activates the extension under test.
  - Executes `docBasedCoding.openProgressGraphPreview`.
  - Polls `docBasedCoding.test.getProgressGraphPreviewSnapshot`.
  - Asserts the Scheduler Trajectory Projection mount and deterministic counts:
    `lanes=4`, `events=6`, `relations=12`.
  - Writes rendered HTML and a compact JSON summary when
    `DBC_ELECTRON_SMOKE_EVIDENCE_DIR` is set.

- `vscode-extension/scripts/run-electron-webview-smoke.mjs`
  - Builds an isolated fake workspace under `output/electron/webview-runner-smoke`.
  - Writes deterministic `.codex/progress-graph/latest.html` and
    `.codex/progress-graph/scheduler-work-trajectory.json`.
  - Launches `Code.exe` directly with `shell: false`.
  - Removes inherited `ELECTRON_RUN_AS_NODE` and `VSCODE_DEV`.
  - Requires both summary and rendered HTML evidence files after process exit.

- `vscode-extension/esbuild.config.mjs`
  - Builds Electron extension tests separately into
    `dist/electron-test/suite`.

- `vscode-extension/src/views/progressGraphPreview.ts`
  - Adds `getTestSnapshot()` for host-side webview HTML readback.

- `vscode-extension/src/extension.ts`
  - Registers the snapshot command only in
    `vscode.ExtensionMode.Test`.

## Probe Boundary

Stable VS Code extension tests do not expose direct DOM access to the inner
webview iframe. This spike therefore uses the narrowest available host seam:

```text
real VS Code Electron process
real extension host activation
real command + webview panel creation
test-mode-only host-side readback of assigned webview.html
```

The command is not contributed in `package.json` and is guarded by extension
test mode.

## Validation

Passed:

```text
npm run build --prefix vscode-extension
build complete
```

```text
node --test vscode-extension/dist/test/progressGraphPreviewPanel.test.js
11 passed
```

```text
node --test vscode-extension/dist/test/extensionManifest.test.js
1 passed
```

```text
node --test vscode-extension/dist/test/progressGraphPreviewHtml.test.js
13 passed
```

```text
node --test vscode-extension/dist/test/progressGraphSchedulerOperatorLifecycle.test.js
3 passed
```

```text
node --test vscode-extension/dist/test/localWorkTrajectory.test.js
2 passed
```

```text
node --test vscode-extension/dist/test/schedulerOperatorContracts.test.js
3 passed
```

```text
.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py tests/test_runtime_orchestration.py -k "scheduler_operator_multilane_dogfood_fixture or scheduler_projection" -q
2 passed, 245 deselected
```

Blocked:

```text
npm run test:electron:smoke --prefix vscode-extension
```

The runner reached real VS Code startup, then failed before extension tests:

```text
checkInnoSetupMutex: vscode-updating is held, waiting up to 30s for setup to finish...
checkInnoSetupMutex: vscode-updating still held after 31412ms, giving up
Error: Code is currently being updated. Please wait for the update to complete before launching.
```

No `output/electron/webview-runner-smoke/electron-webview-smoke-summary.json`
evidence was produced because VS Code exited before loading the extension test
entry.

## Boundary Checks

- No live Qoder or credentialed provider execution was added.
- No background scheduler daemon was added.
- No scheduler/admission/evidence schema was changed.
- No scheduler workflow path mutates agent-owned Local Work Trajectory.
- No Local Work Trajectory visual model redesign was introduced.
- No React Flow renderer replacement was introduced.
- The test snapshot command is hidden from the manifest and only registered in
  extension test mode.
- The Electron runner rejects false positives by requiring evidence files after
  the Electron process exits.

## Residual Risk

The code-level runner seam is implemented, but it is not yet release-grade
evidence. A successful real Electron run is still required after the local VS
Code update lock clears, or by supplying an isolated VS Code executable via
`VSCODE_ELECTRON_SMOKE_EXECUTABLE`.
