# Review - Scheduler Operator Host UX Unified Workflow Binding

> Date: 2026-06-19
> Planning Gate: `design_docs/stages/planning-gate/2026-06-19-scheduler-operator-host-ux-unified-workflow-binding.md`

## Summary

Bound the VS Code Scheduler Operator action buttons to the shared scheduler
operator workflow CLI surface.

The Host UX no longer duplicates the old three-command choreography:

```text
scheduler admit-exchange-artifact
scheduler daemon-loop
scheduler project
```

Instead, it invokes:

```text
doc-based-coding scheduler operator-workflow
```

with one explicit mutation flag per button.

## Changed Files

- `vscode-extension/src/views/schedulerOperatorWorkflow.ts`
- `vscode-extension/src/test/progressGraphPreviewPanel.test.ts`
- `design_docs/stages/planning-gate/2026-06-19-scheduler-operator-host-ux-unified-workflow-binding.md`

## Behavior

- `Admit` calls `scheduler operator-workflow --admit --artifact-id ... --version ...`.
- `Run bounded loop` calls `scheduler operator-workflow --run-loop` with fake
  runtime, bounded loop limits, explicit evidence id/path, and actor.
- `Refresh projection` calls `scheduler operator-workflow --refresh-projection`
  with explicit projection path and guide context.
- Artifact store, admission ledger, scheduler snapshot/event log, and scheduler
  projection paths remain explicit.
- Last-action summaries read nested shared workflow results:
  `admission_result`, `loop_result`, and `projection_result`.
- The summary reader still accepts the old direct-command payload shape.

## Validation

```text
npm run build --prefix vscode-extension
build complete
```

```text
node --test vscode-extension/dist/test/progressGraphPreviewPanel.test.js
10 passed
```

```text
node --test vscode-extension/dist/test/progressGraphPreviewHtml.test.js
13 passed
```

```text
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_mcp_admission.py -k "scheduler_operator_multilane_dogfood_fixture or scheduler_operator_workflow"
10 passed
```

Screenshot validation:

```text
output/playwright/scheduler-operator-ui/scheduler-operator-panel.png
```

The screenshot shows the Scheduler Operator panel rendering one admission
candidate, the explicit `Admit`, `Run bounded loop`, and `Refresh projection`
controls, last-action feedback, and Host Evidence readback.

## Boundary Checks

- No visual redesign was introduced.
- Existing read-only resource behavior remains unchanged.
- No backend scheduler/admission/evidence schema changed.
- No live Qoder or real provider execution was added.
- No background daemon lifecycle was added.
- No ExchangeArtifact consumed marking was added.
- No UI or scheduler workflow path mutates agent-owned Local Work Trajectory.

## Residual Risk

This is a Host UX plumbing convergence slice. It verifies the shared workflow
surface is wired into the panel and that the panel still renders correctly, but
it does not test a live VS Code extension-host click sequence against a real
workspace.
