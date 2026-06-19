# Planning Gate: Extension-Host Scheduler Projection Lifecycle Smoke

> Date: 2026-06-19
> Status: COMPLETED

## Context

The completed Scheduler Projection Readability Review proved that the
deterministic multi-lane fake-runtime scheduler projection is readable in the
static React Flow harness:

- `design_docs/stages/planning-gate/2026-06-19-scheduler-projection-readability-review.md`
- `review/scheduler-projection-readability-review-2026-06-19.md`
- `design_docs/scheduler-projection-readability-review-followup-direction-analysis.md`

The remaining product-confidence gap is lifecycle: the actual VS Code extension
host and webview refresh/display loop should prove it can surface the same
scheduler projection path, not only a static HTML fixture.

## Scope

Build the narrowest extension-host lifecycle smoke that validates scheduler
projection refresh/display through the Host UX surface:

1. Use a deterministic seeded workspace or fixture root.
2. Keep runtime fake-only.
3. Exercise the extension/host-facing path that refreshes scheduler projection
   and displays the Scheduler Local Work Trajectory payload.
4. Verify the rendered or generated webview surface contains scheduler
   projection counts and a scheduler trajectory mount/payload.
5. Capture screenshot-style or webview HTML evidence when the touched UI path
   renders visual output.

## Acceptance

1. The smoke uses a deterministic multi-lane scheduler candidate or fixture.
2. The smoke invokes the extension-host-facing scheduler projection refresh or
   display path, not only the backend projection helper.
3. The smoke verifies the webview surface exposes scheduler projection counts:
   `4 lanes / 6 events / 12 relations` for the current fixture.
4. The smoke verifies a scheduler Local Work Trajectory payload/mount is present
   in the generated or rendered Host UX surface.
5. Any screenshot or HTML artifact used as evidence is recorded in review
   evidence.
6. Existing focused backend/frontend tests still pass.
7. Status docs, checkpoint, review evidence, and Local Work Trajectory are
   updated at close.

## Non-Goals

- Do not add live Qoder or credentialed provider execution.
- Do not start a background daemon.
- Do not broaden scheduler/admission/evidence schemas.
- Do not mutate agent-owned Local Work Trajectory from scheduler workflow code.
- Do not redesign the Local Work Trajectory visual model.
- Do not replace React Flow or the existing progress graph preview architecture.
- Do not solve large-graph scheduler readability in this slice.

## Validation Plan

Expected focused validation, to be narrowed after inspecting existing extension
test facilities:

```powershell
npm run build --prefix vscode-extension
node --test vscode-extension/dist/test/progressGraphPreviewHtml.test.js
node --test vscode-extension/dist/test/localWorkTrajectory.test.js
```

If an executable extension-host test seam already exists or can be introduced
narrowly:

```powershell
node --test <focused extension-host scheduler projection smoke>
```

Backend projection guard:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py tests/test_runtime_orchestration.py -k "scheduler_operator_multilane_dogfood_fixture or scheduler_projection" -q
```

## Completion Notes

Completed on 2026-06-19.

Implementation:

- Added `progressGraphSchedulerOperatorLifecycle.ts` as a narrow Host UX
  lifecycle seam for `schedulerOperatorAction`: set running state, render the
  preserved shell, resolve runtime, call the shared workflow action, notify the
  operator, then reload from disk.
- Updated `ProgressGraphPreviewPanel` to use that lifecycle helper while
  keeping the VS Code-specific progress/window/runtime adapter in the panel.
- Extended the Scheduler Trajectory Projection toolbar metadata to show
  `lanes`, `events`, and `relations`, so the Host UX surface exposes the
  deterministic multi-lane projection counts directly.
- Added an executable Node smoke for lifecycle ordering, invalid-message
  rejection, and post-failure reload behavior.
- Strengthened the generated webview HTML test fixture to assert
  `4 lanes / 6 events / 12 relations` and the scheduler trajectory payload
  mount.

Evidence:

```text
output/playwright/scheduler-projection-lifecycle-smoke/index.html
output/playwright/scheduler-projection-lifecycle-smoke/lifecycle-smoke.png
output/playwright/scheduler-projection-lifecycle-smoke/lifecycle-smoke-trajectory-panel.png
```

Validation:

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

Boundary:

This slice did not add live Qoder/provider execution, did not start a
background daemon, did not broaden scheduler/admission/evidence schemas, did
not mutate agent-owned Local Work Trajectory from scheduler workflow code, did
not redesign the trajectory visual model, and did not introduce a full Electron
extension-host runner.
