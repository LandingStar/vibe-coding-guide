# Host UX Cleanup Outcome Diff For Sandbox Receipt Workflow

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-host-ux-daemon-loop-sandbox-receipt-workflow-mode.md`
closed with both `run-once` and bounded `daemon-loop` Host UX bindings for
`scheduler sandbox-receipt-workflow`.

Sources:

- `design_docs/host-ux-daemon-loop-sandbox-receipt-workflow-mode-followup-direction-analysis.md`
- `review/host-ux-daemon-loop-sandbox-receipt-workflow-mode-2026-06-21.md`
- `vscode-extension/src/views/progressGraphPreviewHtml.ts`
- `tools/progress_graph/host_evidence.py`

## Goal

Add a read-only Host UX cleanup outcome diff surface for sandbox receipt
evidence so an operator can see how cleanup changed allocation receipt state
without reading raw JSON.

## In Scope

- Derive diff rows only from the already loaded Host Evidence presentation.
- Pair cleanup receipt cards with source/current allocation receipt refs when
  those refs are visible in the card.
- Show workflow-level cleanup state changes:
  - required count;
  - completed count;
  - failed count.
- Show receipt links used for the comparison.
- Keep the surface read-only.
- Add focused TypeScript tests for HTML rendering and candidate derivation.
- Use screenshot-style validation for the updated UI.

## Out of Scope

- Backend evidence directory scanning.
- Reading evidence JSON files directly from the webview.
- New CLI/MCP tools.
- Running cleanup or workflow actions from the diff surface.
- Scheduler projection refresh integration.
- Runtime schema changes.
- Local Work Trajectory mutation from Host UX/runtime code.

## Completion Criteria

- Scheduler Operator Host UX renders a cleanup outcome diff section when visible
  Host Evidence sandbox receipt cards contain source/current/cleanup refs.
- Diff rows are absent or show a clear empty state when no comparable receipt
  pair is visible.
- Diff surface does not post new scheduler actions.
- Focused extension build/tests pass.
- Screenshot artifact shows the diff section without occlusion.
- Checklist, phase map, checkpoint, review evidence, and follow-up direction are
  updated before commit.
