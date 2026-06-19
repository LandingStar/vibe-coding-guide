# Review - Scheduler Operator Extension-Host Click Sequence Smoke

> Date: 2026-06-19
> Planning Gate: `design_docs/stages/planning-gate/2026-06-19-scheduler-operator-extension-host-click-sequence-smoke.md`

## Summary

Added a deterministic Host UX click/message contract smoke for Scheduler
Operator actions.

The new test starts from webview-shaped messages:

```text
schedulerOperatorAction admit
schedulerOperatorAction runLoop
schedulerOperatorAction project
```

and verifies that each step maps to the shared CLI surface:

```text
doc-based-coding scheduler operator-workflow
```

with exactly one explicit action flag per step.

## Changed Files

- `vscode-extension/src/views/schedulerOperatorContracts.ts`
- `vscode-extension/src/views/progressGraphPreview.ts`
- `vscode-extension/src/views/schedulerOperatorWorkflow.ts`
- `vscode-extension/src/test/schedulerOperatorContracts.test.ts`
- `vscode-extension/src/test/progressGraphPreviewPanel.test.ts`
- `design_docs/stages/planning-gate/2026-06-19-scheduler-operator-extension-host-click-sequence-smoke.md`

## Behavior

- Webview `schedulerOperatorAction` messages are now coerced by a shared helper.
- The panel rejects incomplete admission messages before mutation.
- Scheduler Operator CLI args are built by the same shared helper used in tests.
- Admit emits `--admit` only.
- Run bounded loop emits `--run-loop` only, with fake runtime and deterministic
  evidence id/path support for smoke tests.
- Refresh projection emits `--refresh-projection` only.

## Validation

```text
npm run build --prefix vscode-extension
build complete
```

```text
node --test vscode-extension/dist/test/schedulerOperatorContracts.test.js
3 passed
```

```text
node --test vscode-extension/dist/test/progressGraphPreviewPanel.test.js
10 passed
```

```text
node --test vscode-extension/dist/test/progressGraphPreviewHtml.test.js
13 passed
```

Screenshot validation:

```text
output/playwright/scheduler-operator-ui/scheduler-operator-panel.png
```

## Boundary Checks

- No live Qoder or credentialed provider execution was added.
- No background daemon lifecycle was added.
- No backend scheduler/admission/evidence schema changed.
- No ExchangeArtifact consumed marking was added.
- No UI or scheduler workflow path mutates agent-owned Local Work Trajectory.
- No visual redesign was introduced.

## Residual Risk

This is a deterministic click/message contract smoke, not a full Electron
extension-host automation run. It covers the brittle Host UX contract seam
without adding environment-heavy test infrastructure.
