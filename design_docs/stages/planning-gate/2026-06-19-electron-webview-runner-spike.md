# Planning Gate: Electron Webview Runner Spike

> Date: 2026-06-19
> Status: COMPLETED

## Context

The completed Extension-Host Scheduler Projection Lifecycle Smoke proved the
host-facing panel lifecycle seam and generated webview HTML evidence:

- `design_docs/stages/planning-gate/2026-06-19-extension-host-scheduler-projection-lifecycle-smoke.md`
- `review/extension-host-scheduler-projection-lifecycle-smoke-2026-06-19.md`
- `design_docs/extension-host-scheduler-projection-lifecycle-smoke-followup-direction-analysis.md`

The remaining question is whether a real VS Code Electron webview runner can be
kept narrow and stable enough to become release-grade validation for the
Progress Graph Preview Host UX.

## Scope

Create or evaluate the narrowest Electron/webview runner for the Progress Graph
Preview:

1. Use the existing `@vscode/test-electron` dependency if it can be wired
   without broad test infrastructure churn.
2. Use a deterministic fake-runtime workspace or prebuilt fixture.
3. Open or exercise the real VS Code Progress Graph Preview Host UX surface.
4. Verify the webview DOM exposes the Scheduler Trajectory Projection mount and
   the deterministic projection counts: `4 lanes / 6 events / 12 relations`.
5. Capture screenshot-style or DOM evidence if the real webview path renders.
6. If a full Electron runner is not viable in this slice, record the exact
   blocker and leave a narrower follow-up contract instead of broadening scope.

## Acceptance

1. The spike proves whether a full Electron runner is viable now.
2. The attempted runner starts from real VS Code extension-host/webview
   mechanics, not only static HTML builder output.
3. The fixture remains fake-runtime-only and deterministic.
4. Success path verifies Scheduler Trajectory Projection DOM contains:
   - `pgHostSchedulerWorkTrajectoryRoot`
   - `pgHostSchedulerWorkTrajectoryPayload`
   - `lanes=4`
   - `events=6`
   - `relations=12`
5. Failure/defer path records a concrete blocker and the next smallest
   actionable seam.
6. Existing focused frontend/backend tests still pass.
7. Planning gate, review evidence, checkpoint/status docs, and Local Work
   Trajectory are updated at close.

## Non-Goals

- Do not add live Qoder or credentialed provider execution.
- Do not start a background scheduler daemon.
- Do not broaden scheduler/admission/evidence schemas.
- Do not mutate agent-owned Local Work Trajectory from scheduler workflow code.
- Do not redesign the Local Work Trajectory visual model.
- Do not replace React Flow or the existing progress graph preview architecture.
- Do not make Electron runner setup a broad CI/platform redesign in this slice.

## Validation Plan

Expected focused validation:

```powershell
npm run build --prefix vscode-extension
node --test vscode-extension/dist/test/progressGraphSchedulerOperatorLifecycle.test.js
node --test vscode-extension/dist/test/progressGraphPreviewHtml.test.js
node --test vscode-extension/dist/test/progressGraphPreviewPanel.test.js
node --test vscode-extension/dist/test/localWorkTrajectory.test.js
```

If a viable Electron runner is introduced:

```powershell
node <focused electron runner entry>
```

Backend projection guard:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py tests/test_runtime_orchestration.py -k "scheduler_operator_multilane_dogfood_fixture or scheduler_projection" -q
```

## Close Summary

The spike implemented a narrow real VS Code Electron runner seam without
broadening scheduler runtime scope.

The runner now:

1. Builds a separate Electron extension-test bundle under
   `vscode-extension/dist/electron-test/suite`.
2. Creates a deterministic fake workspace with a prebuilt scheduler trajectory
   fixture containing `4 lanes / 6 events / 12 relations`.
3. Launches `Code.exe` directly with `shell: false`, isolated user data and
   extension directories, and the extension under development.
4. Opens the real Progress Graph Preview command in extension test mode.
5. Reads the rendered host-side webview HTML through a test-only command,
   `docBasedCoding.test.getProgressGraphPreviewSnapshot`.
6. Requires both summary and rendered HTML evidence files after the Electron
   process exits, preventing false-positive zero-exit runs.

The stable VS Code extension test API does not expose reliable direct DOM
inspection for the inner webview iframe. The accepted narrow seam for this
slice is therefore:

- real VS Code Electron process startup;
- real extension host activation;
- real command and webview panel creation;
- host-side readback of the latest assigned `webview.html` through a command
  registered only when `context.extensionMode === vscode.ExtensionMode.Test`.

## Validation Result

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

Blocked by host environment:

```text
npm run test:electron:smoke --prefix vscode-extension
```

The Electron runner reached real `Code.exe` startup but failed before extension
tests because the local VS Code install is currently holding the
`vscode-updating` Inno Setup mutex:

```text
checkInnoSetupMutex: vscode-updating is held, waiting up to 30s for setup to finish...
checkInnoSetupMutex: vscode-updating still held after 31412ms, giving up
Error: Code is currently being updated. Please wait for the update to complete before launching.
```

No rendered Electron evidence was produced in this run because VS Code exited
before loading the extension tests.

## Close Decision

This planning gate is closed as a completed spike with a concrete rerun
blocker:

- the code-level Electron runner seam is implemented and covered by focused
  build/static tests;
- true rendered Electron evidence is deferred until the local VS Code update
  mutex is released or an isolated VS Code executable is supplied via
  `VSCODE_ELECTRON_SMOKE_EXECUTABLE`;
- the runner is not yet promoted into release-grade validation because the
  real Electron path has not produced evidence in this environment.
