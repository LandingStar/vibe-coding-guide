# Host UX Daemon-Loop Sandbox Receipt Workflow Mode Review

> Date: 2026-06-21
> Scope: `design_docs/stages/planning-gate/2026-06-21-host-ux-daemon-loop-sandbox-receipt-workflow-mode.md`

## Summary

Scheduler Operator Host UX now exposes both sandbox receipt workflow modes over
the existing backend CLI:

```text
doc-based-coding scheduler sandbox-receipt-workflow --mode run-once
doc-based-coding scheduler sandbox-receipt-workflow --mode daemon-loop
```

The implementation stays a thin Host UX binding. It does not alter backend
workflow schema, scheduler admission schema, runtime behavior, or Local Work
Trajectory ownership.

## Contract Checks

- Webview action remains `runSandboxReceiptWorkflow`.
- Supported modes are `run-once` and `daemon-loop`.
- Run-once keeps `--max-runs 1` and sends no daemon-loop bound flags.
- Daemon-loop requires positive integer text for:
  - `maxTicks`;
  - `maxRunsPerTick`;
  - `maxRuntimeFailures`.
- Daemon-loop maps to:
  - `--mode daemon-loop`;
  - `--max-ticks`;
  - `--max-runs-per-tick`;
  - `--max-runtime-failures`.
- Cleanup remains explicit opt-in; cleanup output flags are sent only when the
  cleanup checkbox is checked.

## Files Reviewed

- `vscode-extension/src/views/schedulerOperatorContracts.ts`
- `vscode-extension/src/views/progressGraphPreviewHtml.ts`
- `vscode-extension/src/views/schedulerOperatorWorkflow.ts`
- `vscode-extension/src/test/schedulerOperatorContracts.test.ts`
- `vscode-extension/src/test/progressGraphPreviewHtml.test.ts`
- `vscode-extension/src/test/progressGraphPreviewPanel.test.ts`
- `src/__main__.py`
- `tools/progress_graph/host_sandbox_receipt_workflow.py`
- `tests/test_cli.py`
- `tests/test_runtime_orchestration.py`
- `tests/test_mcp_admission.py`

## Validation

- `npm run build` from `vscode-extension/` passed.
- `node --test dist/test/schedulerOperatorContracts.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js`
  passed: `38 passed`.
- `.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "sandbox_receipt_workflow"`
  passed: `3 passed, 37 deselected`.
- `.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "host_sandbox_receipt_workflow"`
  passed: `3 passed, 233 deselected`.
- `.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "scheduler_sandbox_receipt_workflow"`
  passed: `2 passed, 8 deselected`.
- Screenshot-style validation passed with:
  `output/playwright/host-ux-daemon-loop-sandbox-receipt-workflow-mode/daemon-loop-workflow-mode.png`.

## Screenshot Observation

The `Sandbox Receipt Workflow` card shows the workflow mode selector, the
daemon-loop bounded fake-runtime inputs, existing workspace/sandbox/allocation
fields, cleanup opt-in, collapsed cleanup evidence output settings, and the
`Run receipt workflow` button. The controls fit inside the Scheduler Operator
panel without visible overlap or occlusion at the validation viewport.

## Residual Risk

This slice intentionally does not add evidence-aware defaults, cleanup outcome
diffing, scheduler projection refresh, or real provider / Qoder execution.
Those remain separate product slices.
