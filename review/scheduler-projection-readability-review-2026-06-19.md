# Review - Scheduler Projection Readability Review

> Date: 2026-06-19
> Planning Gate: `design_docs/stages/planning-gate/2026-06-19-scheduler-projection-readability-review.md`

## Summary

Reviewed the scheduler-derived Local Work Trajectory projection produced from
the deterministic multi-lane Scheduler Operator fixture.

The review found two narrow readability defects:

1. Backend projection ordered fan-in merge events after their target task
   events, which created a contradictory lane-order sequence.
2. Frontend full-fit rendering for scheduler-state projections could show a
   clipped first paint or screenshot capture.

Both defects were fixed without changing scheduler/admission/evidence schemas,
without live provider execution, and without changing Local Work Trajectory
ownership semantics.

## Projection Evidence

Projection fixture root:

```text
output/playwright/scheduler-trajectory-preview/project-readability-review-fixed
```

Projection artifact:

```text
output/playwright/scheduler-trajectory-preview/project-readability-review-fixed/.codex/progress-graph/scheduler-work-trajectory.json
```

Rendered screenshot:

```text
output/playwright/scheduler-trajectory-preview/readability-review.png
```

Recorded counts:

```text
lanes=4
events=6
relations=12
scheduler_history=19
```

The two extra events are scheduler fan-in merge projection events.

## Changed Files

- `tools/progress_graph/scheduler_projection.py`
- `tests/test_progress_graph_trajectory.py`
- `vscode-extension/src/webviews/localWorkTrajectory.tsx`
- `vscode-extension/src/test/localWorkTrajectory.test.ts`
- `design_docs/stages/planning-gate/2026-06-19-scheduler-projection-readability-review.md`

## Behavior

- Scheduler task projection order now leaves gaps with `_task_event_order()`.
- Fan-in and scheduler-owned merge events are ordered immediately before their
  target scheduler task.
- Tests assert no reverse lane-order `target -> merge` sequence is emitted.
- Scheduler-state projections use lane order by earliest projected task event
  order.
- Scheduler-state projections use full-fit mode.
- Full-fit mode uses separate width/height budgets.
- Full-fit mode supplies the initial `defaultViewport` and applies subsequent
  viewport correction with duration `0`, avoiding clipped first-frame
  screenshots.

## Validation

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

Screenshot validation:

```text
npx --yes --cache output/playwright/.npm-cache playwright screenshot <local-file-url-for-output/playwright/scheduler-trajectory-preview/readability-review.html> "output/playwright/scheduler-trajectory-preview/readability-review.png" --viewport-size "1440,1200"
```

Visual result:

```text
output/playwright/scheduler-trajectory-preview/readability-review.png
```

Change impact:

```text
analyze_changes: direct=[], transitive=[], coupling.alerts=[]
```

## Boundary Checks

- No live Qoder or credentialed provider execution was added.
- No background daemon lifecycle was added.
- No full Electron extension-host runner was added.
- No scheduler/admission/evidence schema was changed.
- No scheduler workflow path mutates agent-owned Local Work Trajectory.
- No Local Work Trajectory visual model redesign was introduced.
- No React Flow renderer replacement was introduced.

## Residual Risk

This review used a deterministic four-lane fixture. It improves the first
operator-readable scheduler projection, but it does not prove large scheduler
graphs, live-provider timing, or full VS Code extension-host lifecycle behavior.
