# Review - Extension-Host Scheduler Projection Lifecycle Smoke

> Date: 2026-06-19
> Planning Gate: `design_docs/stages/planning-gate/2026-06-19-extension-host-scheduler-projection-lifecycle-smoke.md`

## Summary

Reviewed the Host UX lifecycle path for refreshing and displaying the
scheduler-derived Local Work Trajectory projection.

The smoke keeps runtime fake-only and uses the existing VS Code Progress Graph
Preview panel seam rather than introducing a full Electron runner. It validates
the `schedulerOperatorAction` lifecycle from the host-facing message/action
boundary through running-state render, shared workflow invocation, notification,
and disk reload. The generated webview surface now also exposes the scheduler
projection counts directly in the Scheduler Trajectory Projection toolbar.

## Evidence

HTML evidence:

```text
output/playwright/scheduler-projection-lifecycle-smoke/index.html
```

Screenshot evidence:

```text
output/playwright/scheduler-projection-lifecycle-smoke/lifecycle-smoke.png
output/playwright/scheduler-projection-lifecycle-smoke/lifecycle-smoke-trajectory-panel.png
```

Recorded scheduler trajectory shape:

```text
lanes=4
events=6
relations=12
```

The trajectory panel screenshot directly shows the Scheduler Trajectory
Projection mount metadata:

```text
Scheduler projection · artifact=.codex/progress-graph/scheduler-work-trajectory.json · lanes=4 · events=6 · relations=12
```

## Changed Files

- `vscode-extension/src/views/progressGraphSchedulerOperatorLifecycle.ts`
- `vscode-extension/src/views/progressGraphPreview.ts`
- `vscode-extension/src/views/progressGraphPreviewHtml.ts`
- `vscode-extension/src/test/progressGraphSchedulerOperatorLifecycle.test.ts`
- `vscode-extension/src/test/progressGraphPreviewHtml.test.ts`
- `design_docs/stages/planning-gate/2026-06-19-extension-host-scheduler-projection-lifecycle-smoke.md`

## Behavior

- Invalid scheduler operator messages are rejected before mutation.
- Valid scheduler operator actions set a running last-action state and render
  the preserved shell before execution.
- The panel resolves the runtime and calls the shared
  `doc-based-coding scheduler operator-workflow` path through the existing
  workflow runner.
- Success and failure both update the last-action state and then reload the
  preview from disk.
- Scheduler trajectory mount metadata now includes lane, event, and relation
  counts.

## Validation

```text
npm run build --prefix vscode-extension
build complete
```

```text
node --test vscode-extension/dist/test/progressGraphSchedulerOperatorLifecycle.test.js
3 passed
```

```text
node --test vscode-extension/dist/test/progressGraphPreviewHtml.test.js
13 passed
```

```text
node --test vscode-extension/dist/test/progressGraphPreviewPanel.test.js
10 passed
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
.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py tests/test_runtime_orchestration.py -k "scheduler_operator_multilane_dogfood_fixture or scheduler_projection or fan_in_dependencies or scheduler_owned_merge_gate or persisted_scheduler_runner_result" -q
4 passed, 243 deselected
```

Screenshot validation used the local `playwright` package because the
`playwright-cli` wrapper attempted to use the user npm cache and failed with an
EPERM cache-write error in this environment.

## Boundary Checks

- No live Qoder or credentialed provider execution was added.
- No background daemon lifecycle was added.
- No scheduler/admission/evidence schema was changed.
- No scheduler workflow path mutates agent-owned Local Work Trajectory.
- No Local Work Trajectory visual model redesign was introduced.
- No React Flow renderer replacement was introduced.
- No full Electron extension-host runner was introduced.

## Residual Risk

This is a host-facing lifecycle seam smoke, not a full VS Code Electron
extension-host run. It proves the panel lifecycle contract and generated
webview evidence, but not the complete VS Code command/webview process under
Electron. A later Electron runner spike should decide whether the added
environment cost is justified before broadening release validation.
