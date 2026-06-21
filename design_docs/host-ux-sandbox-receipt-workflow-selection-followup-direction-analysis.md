# Host UX Sandbox Receipt Workflow Selection Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-host-ux-sandbox-receipt-workflow-selection.md`
closed with a first manual Host UX cleanup control over existing durable
sandbox allocation receipt evidence.

Review evidence:

- `review/host-ux-sandbox-receipt-workflow-selection-2026-06-21.md`

## Current Position

The Host UX now has a minimal cleanup path:

1. the operator manually enters a receipt evidence path;
2. the operator explicitly confirms cleanup;
3. the webview dispatches a shared `cleanupReceipts` action;
4. the extension invokes `doc-based-coding scheduler cleanup-receipts`;
5. the panel reloads and Host Evidence presentation can show cleanup readback.

This is intentionally cleanup-only. It does not yet provide evidence listing,
selection from cards, or full allocate/read/cleanup/read workflow setup.

## Candidate A - Evidence Discovery And Selection UX

### Goal

Replace raw path typing as the main operator path with a read-only evidence
candidate list sourced from Host Evidence presentation and/or the known evidence
directory.

### Narrow Scope

1. List durable sandbox allocation/cleanup receipt evidence candidates.
2. Show cleanup state per candidate before action.
3. Populate the existing manual path input from selection.
4. Keep explicit confirmation before cleanup.
5. Keep cleanup invocation on the existing CLI/MCP/backend surface.

### Why Next

This improves operator safety without expanding runtime authority. The current
control proves the action path; the next risk is selecting the correct receipt.

## Candidate B - Full Workflow Mode Host UX

### Goal

Expose the existing `sandbox-receipt-workflow` allocate/read/cleanup/read
surface from Host UX with explicit mode and path inputs.

### Why Lower Priority

It needs more inputs than the current cleanup-only flow: source repo root,
git-worktree sandbox root, scheduler snapshot/event log, allocation evidence
id, workflow mode, and cleanup output policy. That should be a separate
contracted UI slice.

## Candidate C - Cleanup Outcome Diff View

### Goal

Show before/after evidence deltas for a cleanup action.

### Why Lower Priority

The Host Evidence card already shows cleanup settled/failed/required counts.
Diff view is useful, but evidence discovery is a clearer next safety gain.

## Recommendation

Choose Candidate A next:

```text
Host UX Evidence Discovery For Sandbox Receipts
```

Reason:

1. current manual cleanup action is already wired and validated;
2. selecting the correct receipt is now the main operator safety gap;
3. discovery can remain read-only until the operator explicitly confirms
   cleanup;
4. it avoids mixing full allocation workflow setup into this cleanup-only
   control.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-21-host-ux-sandbox-receipt-evidence-discovery.md`

Suggested first slice:

1. read existing Host Evidence presentation cards and known evidence refs;
2. render selectable sandbox receipt evidence candidates;
3. populate the existing cleanup evidence path input from selection;
4. retain manual override and explicit confirmation;
5. validate with focused UI tests and screenshot-style tooling.
