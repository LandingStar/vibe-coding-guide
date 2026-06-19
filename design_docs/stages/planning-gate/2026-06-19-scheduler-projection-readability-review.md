# Planning Gate: Scheduler Projection Readability Review

> Date: 2026-06-19
> Status: COMPLETED

## Context

The completed Scheduler Operator click-sequence smoke proved that Host UX
messages map to the shared `doc-based-coding scheduler operator-workflow`
surface with explicit `--admit`, `--run-loop`, and `--refresh-projection`
flags.

The next product risk is readability: the deterministic multi-lane scheduler
fixture can now produce a scheduler-derived Local Work Trajectory projection,
but the projection still needs to be inspected as a user-facing operator view.

## Scope

Use the existing deterministic multi-lane scheduler operator fixture to review
the scheduler-derived trajectory projection:

1. Generate or reuse a deterministic multi-lane fixture through the shared
   scheduler operator workflow.
2. Inspect the resulting `.codex/progress-graph/scheduler-work-trajectory.json`
   structure.
3. Render the projected Local Work Trajectory with the current React Flow
   webview bundle.
4. Decide whether any unreadability belongs to scheduler projection semantics,
   Local Work Trajectory mapping, or frontend layout.
5. Apply only narrow fixes when the evidence points to one clear defect.

## Acceptance

1. A deterministic multi-lane scheduler projection is generated from the
   existing fake-runtime operator workflow.
2. The generated projection has clear lane, event, and relation counts recorded
   in review evidence.
3. A screenshot-style artifact captures the rendered scheduler-derived
   trajectory projection.
4. The review explicitly classifies any observed readability issue as backend
   projection, Local Work Trajectory mapping, frontend layout, or no immediate
   fix.
5. Focused backend and frontend tests relevant to any touched files pass.
6. Status docs, checkpoint, review evidence, and Local Work Trajectory are
   updated at close.

## Non-Goals

- Do not add live Qoder or other credentialed provider execution.
- Do not start a background daemon.
- Do not add a full Electron extension-host runner.
- Do not redesign the Local Work Trajectory visual model.
- Do not change scheduler/admission/evidence schemas.
- Do not mutate agent-owned Local Work Trajectory from scheduler workflow code.
- Do not replace the current React Flow renderer in this slice.

## Validation Plan

Backend projection validation:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py -k "scheduler_operator_multilane_dogfood_fixture or scheduler_projection"
```

Frontend validation, if the renderer is touched:

```powershell
npm run build --prefix vscode-extension
node --test vscode-extension/dist/test/localWorkTrajectory.test.js
node --test vscode-extension/dist/test/progressGraphPreviewHtml.test.js
```

Screenshot validation:

```powershell
npx --yes --cache output/playwright/.npm-cache playwright screenshot <harness-url> output/playwright/scheduler-trajectory-preview/readability-review.png --viewport-size "1440,1200"
```

## Closeout

The deterministic multi-lane scheduler fixture was projected and rendered as a
scheduler-derived Local Work Trajectory:

- projection source root:
  `output/playwright/scheduler-trajectory-preview/project-readability-review-fixed`
- projection artifact:
  `output/playwright/scheduler-trajectory-preview/project-readability-review-fixed/.codex/progress-graph/scheduler-work-trajectory.json`
- rendered screenshot artifact:
  `output/playwright/scheduler-trajectory-preview/readability-review.png`

Recorded projection counts:

- lanes: `4`
- events: `6`
- relations: `12`
- scheduler history lines: `19`

Observed readability issues and classification:

- Backend projection semantics: fan-in merge events were originally ordered
  after their target task events, creating a lane-order `target -> merge`
  sequence that contradicted the `merge -> target` relation. This was fixed by
  spacing scheduler task event order values and placing merge events immediately
  before their target task order.
- Local Work Trajectory mapping: no schema or recursive trajectory mapping
  change was required. The projection remains a read-only scheduler-state view.
- Frontend layout: scheduler-state projections now use lane order by earliest
  projected scheduler task event order and full-fit mode. Full-fit rendering
  now has a distinct height budget, initial default viewport binding, and
  non-animated viewport application so screenshot/user first paint does not
  capture a clipped intermediate state.

Validation:

```text
npm run build --prefix vscode-extension
build complete
```

```text
node --test vscode-extension/dist/test/localWorkTrajectory.test.js
2 passed
```

```text
node --test vscode-extension/dist/test/progressGraphPreviewHtml.test.js
13 passed
```

```text
.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py tests/test_runtime_orchestration.py -k "scheduler_operator_multilane_dogfood_fixture or scheduler_projection or fan_in_dependencies or scheduler_owned_merge_gate or persisted_scheduler_runner_result" -q
4 passed, 243 deselected
```

Change impact / coupling check:

```text
analyze_changes: direct=[], transitive=[], coupling.alerts=[]
```
