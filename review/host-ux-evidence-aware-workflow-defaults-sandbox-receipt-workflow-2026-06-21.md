# Host UX Evidence-Aware Workflow Defaults For Sandbox Receipt Workflow Review

> Date: 2026-06-21
> Scope: `design_docs/stages/planning-gate/2026-06-21-evidence-aware-workflow-defaults-sandbox-receipt-workflow.md`

## Summary

Scheduler Operator Host UX now renders an explicit `Use for workflow` action on
visible sandbox receipt evidence candidates. The action pre-fills the
`Sandbox Receipt Workflow` allocation evidence id/path fields from the selected
receipt evidence path while preserving the existing cleanup selection behavior.

The implementation is UI-only. It does not scan backend evidence directories,
read raw evidence JSON, invoke workflow/cleanup actions, change scheduler
schema, or mutate Local Work Trajectory.

## Contract Checks

- Existing cleanup `Select` still fills only `pgHostCleanupEvidencePath`.
- New `Use for workflow` fills only:
  - `pgHostSandboxWorkflowAllocationEvidenceId`;
  - `pgHostSandboxWorkflowAllocationEvidencePath`.
- Evidence id is derived from the selected evidence path filename stem.
- Workflow prefill does not call `vscode.postMessage`.
- Workflow prefill does not check cleanup opt-in.
- Workflow prefill does not fill cleanup evidence output fields.
- Operators can still manually edit the fields after prefill.

## Files Reviewed

- `vscode-extension/src/views/progressGraphPreviewHtml.ts`
- `vscode-extension/src/test/progressGraphPreviewHtml.test.ts`
- `design_docs/stages/planning-gate/2026-06-21-evidence-aware-workflow-defaults-sandbox-receipt-workflow.md`

## Validation

- `npm run build` from `vscode-extension/` passed.
- `node --test dist/test/schedulerOperatorContracts.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js`
  passed: `39 passed`.
- Screenshot-style validation passed with:
  `output/playwright/host-ux-evidence-aware-workflow-defaults-sandbox-receipt-workflow/workflow-defaults.png`.
- Focused candidate screenshot:
  `output/playwright/host-ux-evidence-aware-workflow-defaults-sandbox-receipt-workflow/workflow-defaults-candidate.png`.

## Screenshot Observation

The candidate card shows `Select` and `Use for workflow` as separate actions
without visible overlap. Browser validation confirmed two workflow prefill
buttons, two cleanup select buttons, no horizontal overflow, and clicking
`Use for workflow` filled `allocation-receipts` plus
`.codex/scheduler/evidence/allocation-receipts.json` while leaving cleanup
unchecked and cleanup evidence path empty.

## Residual Risk

The prefill action is intentionally based on visible presentation refs. If Host
Evidence does not expose a receipt path ref, no prefill action is available for
that evidence. Backend-enriched cleanup diff payloads and projection refresh
follow-up remain separate candidates.
