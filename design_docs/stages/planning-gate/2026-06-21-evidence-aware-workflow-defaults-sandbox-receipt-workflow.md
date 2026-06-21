# Evidence-Aware Workflow Defaults For Sandbox Receipt Workflow

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-host-ux-cleanup-outcome-diff-sandbox-receipt-workflow.md`
closed with a read-only cleanup outcome diff over visible Host Evidence receipt
refs. The follow-up direction recommends using those already visible receipt
candidates to reduce manual workflow field entry without changing cleanup
authority.

Sources:

- `design_docs/host-ux-cleanup-outcome-diff-sandbox-receipt-workflow-followup-direction-analysis.md`
- `review/host-ux-cleanup-outcome-diff-sandbox-receipt-workflow-2026-06-21.md`
- `vscode-extension/src/views/progressGraphPreviewHtml.ts`

## Goal

Add an explicit Host UX action that pre-fills `Sandbox Receipt Workflow`
allocation evidence defaults from a visible sandbox receipt evidence candidate.

## In Scope

- Add a visible candidate action that fills:
  - `allocation evidence path`;
  - `allocation evidence id`.
- Derive the default evidence id from the selected evidence path filename stem.
- Preserve the existing cleanup candidate `Select` behavior for
  `Sandbox Receipt Cleanup`.
- Preserve manual override: operators can edit fields after prefill.
- Keep cleanup opt-in unchecked by default.
- Keep all scheduler workflow and cleanup actions explicitly button-triggered.
- Add focused TypeScript tests for rendering and script contract.
- Use screenshot-style validation for the updated UI.

## Out of Scope

- Backend evidence directory scanning.
- Raw evidence JSON reads from the webview.
- Backend workflow schema or CLI/MCP changes.
- Auto-running workflow or cleanup actions.
- Auto-checking cleanup opt-in.
- Scheduler projection refresh integration.
- Local Work Trajectory mutation from Host UX/runtime code.

## Completion Criteria

- Visible receipt candidates render an explicit workflow-prefill action.
- Prefill fills only workflow allocation evidence id/path fields.
- Cleanup evidence selection continues to fill only cleanup receipt path.
- Prefill does not check cleanup, disable buttons, or post scheduler actions.
- Focused extension build/tests pass.
- Screenshot artifact shows the workflow prefill affordance without occlusion.
- Checklist, phase map, checkpoint, review evidence, and follow-up direction are
  updated before commit.
