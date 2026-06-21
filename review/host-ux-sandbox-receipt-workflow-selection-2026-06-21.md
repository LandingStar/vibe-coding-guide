# Host UX Selection For Sandbox Receipt Workflow Review

> Date: 2026-06-21
> Gate: `design_docs/stages/planning-gate/2026-06-21-host-ux-sandbox-receipt-workflow-selection.md`
> Status: PASSED

## Scope

This slice added the first Host UX operator control for sandbox receipt cleanup:

- rendered a `Sandbox Receipt Cleanup` section in the existing VS Code Progress
  Graph Preview / Scheduler Operator card;
- required manual `sandbox_allocation_receipt_evidence` path entry;
- required an explicit confirmation checkbox before cleanup action dispatch;
- added shared `cleanupReceipts` webview action coercion;
- mapped the action to `doc-based-coding scheduler cleanup-receipts`;
- summarized cleanup result payloads in the existing last-action card;
- left Host Evidence presentation as the readback surface after the panel
  reloads.

## Evidence

Validation commands:

```powershell
npm run build
node --test dist/test/schedulerOperatorContracts.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "cleanup_receipts"
.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "cleanup"
```

Results:

- VS Code extension build: passed
- focused Scheduler Operator / Progress Graph Preview node tests:
  `32 passed`
- CLI cleanup focused pytest: `3 passed, 37 deselected`
- Host Evidence cleanup readback focused pytest: `2 passed, 66 deselected`

Screenshot-style validation:

- `output/playwright/host-ux-sandbox-receipt-workflow/host-ux-cleanup-fixture.png`

The screenshot shows the Scheduler Operator cleanup path input, explicit
confirmation checkbox, `Clean receipts` button, latest cleanup result, and Host
Evidence cleanup card in the same rendered panel.

## Boundary

This slice does not implement automatic evidence discovery/listing, does not
run a default cleanup daemon, does not run live Qoder or real-provider
expansion, does not change scheduler admission/evidence schema, does not
refresh scheduler projection as part of cleanup, and does not mutate
agent-owned Local Work Trajectory from Host UX/CLI/MCP/runtime code.

The UI intentionally calls the existing explicit cleanup CLI surface for a
manually supplied existing evidence path. The broader allocate/read/cleanup/read
workflow still needs a separate Host UX contract because it requires source repo
root, git-worktree sandbox root, allocation evidence id, and mode selection.

## Residual Risk

Manual path entry is functional but operator ergonomics remain limited. The next
slice should add evidence discovery/selection and, separately, full workflow
mode selection rather than overloading this cleanup-only control.
