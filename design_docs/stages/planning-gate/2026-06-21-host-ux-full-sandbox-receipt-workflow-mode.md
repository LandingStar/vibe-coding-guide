# Host UX Full Sandbox Receipt Workflow Mode

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-host-ux-sandbox-receipt-evidence-discovery.md`
closed with read-only sandbox receipt evidence discovery in Scheduler Operator
Host UX. The follow-up direction analysis recommends exposing the existing
`scheduler sandbox-receipt-workflow` backend surface as a separate workflow mode.

Sources:

- `design_docs/host-ux-sandbox-receipt-evidence-discovery-followup-direction-analysis.md`
- `review/host-ux-sandbox-receipt-evidence-discovery-2026-06-21.md`
- `design_docs/stages/planning-gate/2026-06-21-host-sandbox-receipt-workflow-cli-mcp-surface.md`

## Goal

Add the first Host UX binding for the full sandbox receipt workflow by wiring
`run-once` mode through explicit operator controls.

This should let the operator run:

```text
doc-based-coding scheduler sandbox-receipt-workflow --mode run-once ...
```

from Scheduler Operator Host UX with explicit source repo, git-worktree sandbox
root, allocation evidence id/path, and optional cleanup output settings.

## In Scope

- Add a `runSandboxReceiptWorkflow` Host UX action contract.
- Support only `mode=run-once` in this slice.
- Collect required inputs:
  - workspace/source repo root;
  - git-worktree sandbox root;
  - allocation evidence id;
  - optional allocation evidence path.
- Keep cleanup as an explicit checkbox:
  - when checked, provide cleanup evidence id/path;
  - when unchecked, do not send cleanup output flags.
- Reuse the existing CLI backend surface.
- Summarize workflow steps and evidence paths in last-action status.
- Add focused TypeScript tests for message coercion and CLI args.
- Use screenshot-style validation for the Host UX.

## Out of Scope

- `daemon-loop` workflow mode.
- Real provider / Qoder execution.
- Backend workflow schema changes.
- Background cleanup daemon behavior.
- Cleanup outcome diff view.
- Scheduler projection refresh as part of this workflow.
- Local Work Trajectory mutation from Host UX/runtime code.

## Completion Criteria

- The Host UX exposes a distinct run-once sandbox receipt workflow control.
- Missing required fields are rejected before dispatch.
- Cleanup output flags are only sent when cleanup is explicitly checked.
- Existing cleanup-only receipt action remains unchanged.
- Focused extension build/tests pass.
- Screenshot artifact shows the new workflow control in Scheduler Operator.
- Checklist, phase map, checkpoint, review evidence, and follow-up direction are
  updated before commit.

## Result

Completed.

The VS Code Scheduler Operator Host UX now includes a distinct `Sandbox Receipt
Workflow` control. It is scoped to `run-once` mode and maps to the existing
backend CLI surface:

```text
doc-based-coding scheduler sandbox-receipt-workflow --mode run-once ...
```

The action contract requires explicit workspace/source repo root,
git-worktree sandbox root, and allocation evidence id before dispatch. Optional
allocation evidence path is passed only when filled. Cleanup remains explicit:
cleanup output id/path are sent only when the operator checks the cleanup option.

The workflow control is independent from the prior cleanup-only receipt card.

## Validation

- `npm run build` from `vscode-extension/` passed.
- `node --test dist/test/schedulerOperatorContracts.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js`
  passed: `36 passed`.
- `.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "sandbox_receipt_workflow"`
  passed: `3 passed, 37 deselected`.
- `.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "host_sandbox_receipt_workflow"`
  passed: `3 passed, 233 deselected`.
- Screenshot artifact:
  `output/playwright/host-ux-full-sandbox-receipt-workflow-mode/workflow-mode.png`.

## Follow-Up

Remaining Host UX sandbox workflow work should stay in separate gates:

1. add `daemon-loop` workflow mode;
2. add cleanup outcome diff/readback comparison;
3. optionally improve evidence path defaults from selected Host Evidence cards.
