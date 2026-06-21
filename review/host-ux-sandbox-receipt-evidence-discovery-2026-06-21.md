# Host UX Sandbox Receipt Evidence Discovery Review

> Date: 2026-06-21
> Scope: `design_docs/stages/planning-gate/2026-06-21-host-ux-sandbox-receipt-evidence-discovery.md`

## Summary

The VS Code Scheduler Operator cleanup card now exposes read-only receipt
evidence candidates derived from Host Evidence presentation cards.

The implementation keeps cleanup authority unchanged:

- candidates come from loaded `hostEvidencePresentation.cards`;
- eligible cards must represent `sandbox_allocation_receipt_evidence`;
- eligible refs must be evidence JSON paths under `.codex/scheduler/evidence/`;
- selecting a candidate only fills the existing evidence path input;
- explicit confirmation is still required before `cleanupReceipts` is posted.

## Files Reviewed

- `vscode-extension/src/views/progressGraphPreviewHtml.ts`
- `vscode-extension/src/test/progressGraphPreviewHtml.test.ts`
- `vscode-extension/src/test/progressGraphPreviewPanel.test.ts`
- `vscode-extension/src/test/schedulerOperatorContracts.test.ts`
- `tests/test_cli.py`
- `tests/test_progress_graph_trajectory.py`

## Validation

- `npm run build` from `vscode-extension/` passed.
- `node --test dist/test/schedulerOperatorContracts.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js`
  passed: `33 passed`.
- `.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "cleanup_receipts"`
  passed: `3 passed, 37 deselected`.
- `.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "cleanup"`
  passed: `2 passed, 66 deselected`.
- Screenshot-style validation passed with:
  `output/playwright/host-ux-sandbox-receipt-evidence-discovery/receipt-evidence-discovery.png`.

## Screenshot Observation

The Scheduler Operator section displays two receipt evidence candidates, one
current receipt and one source receipt. The worktree path ref is not shown as a
candidate. The manual input remains visible and the cleanup confirmation checkbox
is unchecked.

## Residual Risk

This slice does not discover evidence files from disk. If no Host Evidence
presentation card has been loaded, the UI correctly falls back to manual entry.
Full workflow setup and before/after cleanup diff remain separate product work.
