# Host UX Authorization Readback Binding

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/lease-and-sandbox-authorization-readback-followup-direction-analysis.md`
recommends making the new read-only scheduler authorization readback visible in
Host UX before starting real sandbox-provider enforcement.

The backend/MCP product already exists:

```text
SchedulerState / snapshot / optional event-log recovery
-> schedulerAuthorizationReadback
-> edit lease declaration + lifecycle + sandbox authorization diagnostics
```

## Goal

Add a read-only authorization diagnostics section to the existing VS Code
Scheduler Operator / Progress Graph Preview surface.

Operators should be able to see, without running a scheduler mutation:

1. whether scheduler authorization readback is available;
2. task edit lease declaration counts;
3. lease lifecycle state counts;
4. sandbox authorization state counts;
5. compact per-task lifecycle and sandbox authorization status rows;
6. clear empty/error states when scheduler snapshot inputs are not yet present.

## Scope

1. Add a Host UX readback adapter that calls the existing
   `schedulerAuthorizationReadback` MCP/tool path through the installed runtime
   helper pattern already used by the Scheduler Operator panel.
2. Extend the existing Scheduler Operator workflow state with an optional
   authorization readback payload and read error.
3. Render a compact, read-only Authorization Readback subsection inside the
   Scheduler Operator panel.
4. Cover empty, error, and populated render paths in focused extension tests.
5. Capture screenshot-style evidence for the updated UI.

## Non-Goals

1. No new scheduler mutation buttons.
2. No real sandbox provider or filesystem isolation.
3. No scheduler/admission/readback schema expansion unless rendering is blocked.
4. No ExchangeArtifact store or admission ledger mutation.
5. No scheduler projection refresh beyond existing operator actions.
6. No Local Work Trajectory mutation from UI.
7. No CLI surface for authorization readback.

## Validation

Minimum validation:

1. VS Code extension focused tests covering:
   - scheduler operator workflow readback adapter;
   - progress graph preview HTML populated authorization section;
   - empty/error authorization states;
   - no new Local Work Trajectory mutation surface.
2. TypeScript build or existing extension build gate.
3. Screenshot-style evidence under `output/playwright/`.

## Write-Back Targets

On close, update:

1. `design_docs/Project Master Checklist.md`
2. `design_docs/Global Phase Map and Current Position.md`
3. `.codex/checkpoints/latest.md`
4. `review/host-ux-authorization-readback-binding-2026-06-21.md`

## Completion Criteria

This gate is complete when the Progress Graph Preview panel exposes the
read-only authorization readback product in the Scheduler Operator area, focused
tests pass, and screenshot evidence shows the populated UI state.

## Close Notes

Closed on 2026-06-21.

Review evidence:

- `review/host-ux-authorization-readback-binding-2026-06-21.md`
- Screenshot: `output/playwright/host-ux-authorization-readback/authorization-readback.png`

Validation:

```text
npm run build --prefix vscode-extension
node --test vscode-extension/dist/test/progressGraphPreviewHtml.test.js vscode-extension/dist/test/progressGraphPreviewPanel.test.js
```

Focused tests passed: `26 passed`.
