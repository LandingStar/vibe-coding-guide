# Host UX Cleanup Outcome Diff For Sandbox Receipt Workflow Review

> Date: 2026-06-21
> Scope: `design_docs/stages/planning-gate/2026-06-21-host-ux-cleanup-outcome-diff-sandbox-receipt-workflow.md`

## Summary

Scheduler Operator Host UX now renders a read-only cleanup outcome diff section
inside `Sandbox Receipt Cleanup` when visible Host Evidence sandbox receipt
cards include comparable source and cleanup receipt refs.

The implementation only derives information from the already loaded Host
Evidence presentation. It does not scan evidence directories, read evidence JSON
from the webview, invoke cleanup, change scheduler state, or mutate Local Work
Trajectory.

## Contract Checks

- Diff surface id: `pgHostSchedulerCleanupOutcomeDiff`.
- Diff rows are derived from visible `sandbox_allocation_receipt_evidence` cards.
- A comparable row requires a visible source receipt ref and cleanup receipt ref.
- Rows display:
  - before cleanup required count;
  - after cleanup required/completed/failed counts;
  - changed allocation ids when listed;
  - source receipt path;
  - cleanup receipt path.
- Empty state is explicit when no visible source/cleanup pair is available.
- No new scheduler action button or `postMessage` action is introduced.

## Files Reviewed

- `vscode-extension/src/views/progressGraphPreviewHtml.ts`
- `vscode-extension/src/test/progressGraphPreviewHtml.test.ts`
- `vscode-extension/src/test/progressGraphPreviewPanel.test.ts`
- `vscode-extension/src/test/schedulerOperatorContracts.test.ts`
- `tools/progress_graph/host_evidence.py`

## Validation

- `npm run build` from `vscode-extension/` passed.
- `node --test dist/test/schedulerOperatorContracts.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js`
  passed: `39 passed`.
- Screenshot-style validation passed with:
  `output/playwright/host-ux-cleanup-outcome-diff-sandbox-receipt-workflow/cleanup-outcome-diff.png`.

## Screenshot Observation

The `Cleanup outcome diff` section appears inside the Scheduler Operator cleanup
card. It shows receipt evidence candidates, a read-only diff row with before /
after / changed allocation / source receipt / cleanup receipt facts, manual
cleanup input, confirmation checkbox, and latest action summary without visible
overlap or clipping.

## Residual Risk

The diff is intentionally presentation-derived. If a backend Host Evidence card
does not expose both source and cleanup refs or does not include cleanup state
metadata, the UI will show the empty state rather than reading raw evidence
files. Evidence-aware defaults and backend-enriched diff payloads remain
separate slices.
