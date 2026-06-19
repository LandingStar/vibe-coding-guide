# Planning Gate: Scheduler Operator Extension-Host Click Sequence Smoke

> Date: 2026-06-19
> Status: COMPLETED

## Context

The completed Scheduler Operator Host UX binding gate converged the VS Code
operator buttons onto the shared CLI surface:

- `doc-based-coding scheduler operator-workflow --admit`
- `doc-based-coding scheduler operator-workflow --run-loop`
- `doc-based-coding scheduler operator-workflow --refresh-projection`

The remaining release-grade risk is no longer command choreography drift, but
whether the Host UX click/message path stays aligned with that shared workflow
contract.

## Scope

Create a narrow, repeatable smoke around the scheduler operator click sequence:

1. Interpret the webview `schedulerOperatorAction` messages emitted by the
   Scheduler Operator buttons.
2. Convert the admitted candidate, bounded-loop, and projection-refresh messages
   into the same shared `scheduler operator-workflow` CLI argument contract.
3. Keep the smoke deterministic without requiring live VS Code Electron,
   credentialed provider execution, or a background scheduler daemon.

This is a validation-surface slice. It may introduce small host-contract helper
code only where needed to make the click/message contract testable.

## Acceptance

1. The click sequence `Admit -> Run bounded loop -> Refresh projection` is
   covered by an executable VS Code extension test.
2. The tested sequence starts from webview-shaped messages, not only from
   already-coerced internal actions.
3. Each sequence step produces `scheduler operator-workflow` arguments with
   exactly the intended explicit action flag:
   - admit: `--admit`
   - bounded loop: `--run-loop`
   - projection refresh: `--refresh-projection`
4. The bounded-loop step remains fake-runtime-only and carries deterministic
   evidence id/path in the smoke.
5. The Host UX still rejects incomplete admission messages before mutation.
6. Existing Scheduler Operator panel and HTML tests continue to pass.
7. UI/image validation includes a screenshot-style artifact before close.

## Non-Goals

- Do not add live Qoder or other credentialed provider execution.
- Do not start a background daemon.
- Do not mutate agent-owned Local Work Trajectory from UI or scheduler workflow
  code.
- Do not change backend scheduler/admission/evidence schemas.
- Do not redesign Scheduler Operator UI visuals.
- Do not introduce a full Electron extension-host runner in this slice unless
  the existing test harness already makes it cheap.

## Validation Plan

```powershell
npm run build --prefix vscode-extension
node --test vscode-extension/dist/test/schedulerOperatorContracts.test.js
node --test vscode-extension/dist/test/progressGraphPreviewPanel.test.js
node --test vscode-extension/dist/test/progressGraphPreviewHtml.test.js
```

Refresh or rerun the existing Scheduler Operator screenshot harness to satisfy
the UI validation rule.

## Completion Notes

Completed on 2026-06-19.

Implementation:

- Added a host-contract helper for Scheduler Operator webview messages and
  shared workflow CLI arguments.
- The Progress Graph Preview panel now reuses that helper when handling
  `schedulerOperatorAction` webview messages.
- The workflow runner now reuses the same helper when building
  `doc-based-coding scheduler operator-workflow` arguments.
- Added an executable click-sequence smoke that starts from webview-shaped
  `schedulerOperatorAction` messages and verifies the three explicit workflow
  flags.

Validation:

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

Screenshot-style validation:

```text
output/playwright/scheduler-operator-ui/scheduler-operator-panel.png
```

Boundary:

This slice validates the Host UX click/message contract and shared CLI argument
mapping. It does not add a full Electron extension-host runner, run live
providers, start a background daemon, or mutate Local Work Trajectory from UI
or scheduler workflow code.
