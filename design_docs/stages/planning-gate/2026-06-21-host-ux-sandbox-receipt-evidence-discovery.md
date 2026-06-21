# Host UX Evidence Discovery For Sandbox Receipts

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

The completed `Host UX Selection For Sandbox Receipt Workflow` gate added a
manual cleanup control for durable `sandbox_allocation_receipt_evidence` paths.
The follow-up direction analysis recommends making receipt selection safer by
deriving candidates from the already loaded Host Evidence presentation.

Sources:

- `design_docs/stages/planning-gate/2026-06-21-host-ux-sandbox-receipt-workflow-selection.md`
- `review/host-ux-sandbox-receipt-workflow-selection-2026-06-21.md`
- `design_docs/host-ux-sandbox-receipt-workflow-selection-followup-direction-analysis.md`

## Goal

Add a read-only receipt evidence discovery path to the VS Code Scheduler
Operator Host UX:

1. inspect existing Host Evidence presentation cards;
2. derive selectable sandbox receipt evidence path candidates;
3. populate the existing cleanup evidence path input from a selected candidate;
4. retain manual path override and explicit cleanup confirmation;
5. continue invoking the existing `doc-based-coding scheduler cleanup-receipts`
   surface only after explicit operator action.

## In Scope

- Frontend-only candidate extraction from `hostEvidencePresentation.cards`.
- Candidate rows for refs attached to
  `sandbox_allocation_receipt_evidence` cards.
- Clear labels for source evidence vs current/cleanup evidence.
- A select/fill interaction that writes the chosen path into the existing input.
- Focused TypeScript tests for rendering and script contract.
- Screenshot-style validation of the resulting Host UX.

## Out of Scope

- Backend evidence directory scanning.
- Full `scheduler sandbox-receipt-workflow` allocate/read/cleanup/read UI mode.
- New cleanup authority or automatic cleanup.
- Background cleanup daemon behavior.
- Scheduler schema, Host Evidence presentation schema, or MCP tool contract
  changes.
- Local Work Trajectory mutation from Host UX/runtime code.

## Completion Criteria

- Candidate discovery is deterministic and only derived from loaded presentation
  data.
- Manual cleanup input and confirmation remain available.
- Candidate selection does not auto-confirm cleanup.
- Focused extension build/tests pass.
- UI work has a screenshot artifact under `output/playwright/`.
- Checklist, phase map, checkpoint, review evidence, and follow-up direction are
  updated before commit.

## Result

Completed.

The Scheduler Operator cleanup card now derives receipt evidence candidates from
the already loaded Host Evidence presentation. Candidate extraction is limited to
`sandbox_allocation_receipt_evidence` cards and path refs that point into
`.codex/scheduler/evidence/*.json`; worktree refs and other path refs are not
eligible. Each candidate is labeled as current/source/cleanup receipt and carries
cleanup state metadata when available.

Selecting a candidate only fills the existing manual evidence path input. It does
not check the explicit cleanup confirmation box and does not dispatch cleanup by
itself.

## Validation

- `npm run build` from `vscode-extension/` passed.
- `node --test dist/test/schedulerOperatorContracts.test.js dist/test/progressGraphPreviewHtml.test.js dist/test/progressGraphPreviewPanel.test.js`
  passed: `33 passed`.
- `.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "cleanup_receipts"`
  passed: `3 passed, 37 deselected`.
- `.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "cleanup"`
  passed: `2 passed, 66 deselected`.
- Screenshot artifact:
  `output/playwright/host-ux-sandbox-receipt-evidence-discovery/receipt-evidence-discovery.png`.

## Follow-Up

The next product slice should remain separate. The strongest candidates are:

1. full Host UX binding for `scheduler sandbox-receipt-workflow`
   allocate/read/cleanup/read mode;
2. cleanup outcome diff view over before/after receipt evidence.
