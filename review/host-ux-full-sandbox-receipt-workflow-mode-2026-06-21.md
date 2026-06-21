# Host UX Full Sandbox Receipt Workflow Mode Review

> Date: 2026-06-21
> Scope: `design_docs/stages/planning-gate/2026-06-21-host-ux-full-sandbox-receipt-workflow-mode.md`

## Summary

Scheduler Operator Host UX now exposes a run-once sandbox receipt workflow
control over the existing backend CLI:

```text
doc-based-coding scheduler sandbox-receipt-workflow --mode run-once
```

The implementation is a thin Host UX binding. It does not alter backend workflow
schema or runtime behavior.

## Contract Checks

- Webview action: `runSandboxReceiptWorkflow`.
- Supported mode in this slice: `run-once`.
- Required before dispatch:
  - `workspaceRoot`;
  - `gitWorktreeSandboxRoot`;
  - `allocationEvidenceId`.
- Optional:
  - `allocationEvidencePath`.
- Cleanup:
  - `--cleanup`, `--cleanup-evidence-id`, and `--cleanup-evidence-path` are
    sent only when the cleanup checkbox is checked.

## Files Reviewed

- `vscode-extension/src/views/schedulerOperatorContracts.ts`
- `vscode-extension/src/views/schedulerOperatorWorkflow.ts`
- `vscode-extension/src/views/progressGraphPreviewHtml.ts`
- `vscode-extension/src/test/schedulerOperatorContracts.test.ts`
- `vscode-extension/src/test/progressGraphPreviewHtml.test.ts`
- `vscode-extension/src/test/progressGraphPreviewPanel.test.ts`
- `src/__main__.py`
- `tools/progress_graph/host_sandbox_receipt_workflow.py`
- `tests/test_cli.py`
- `tests/test_runtime_orchestration.py`

## Validation

- `npm run build` from `vscode-extension/` passed.
- `node --test dist/test/schedulerOperatorContracts.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js`
  passed: `36 passed`.
- `.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "sandbox_receipt_workflow"`
  passed: `3 passed, 37 deselected`.
- `.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "host_sandbox_receipt_workflow"`
  passed: `3 passed, 233 deselected`.
- Screenshot-style validation passed with:
  `output/playwright/host-ux-full-sandbox-receipt-workflow-mode/workflow-mode.png`.

## Screenshot Observation

The new `Sandbox Receipt Workflow` card is visible inside Scheduler Operator.
Required run-once inputs, cleanup opt-in, collapsed cleanup evidence output
settings, and the `Run receipt workflow` button are visible and not occluded by
the graph panel.

## Residual Risk

This slice intentionally does not expose daemon-loop mode. It also does not
pre-fill workflow paths from selected Host Evidence candidates. Those remain
separate Host UX product slices.
