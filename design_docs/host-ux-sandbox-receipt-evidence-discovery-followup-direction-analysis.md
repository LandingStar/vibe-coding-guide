# Host UX Sandbox Receipt Evidence Discovery Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-host-ux-sandbox-receipt-evidence-discovery.md`
closed with read-only receipt candidate discovery and selection for the
Scheduler Operator cleanup card.

Review evidence:

- `review/host-ux-sandbox-receipt-evidence-discovery-2026-06-21.md`

## Current Position

The Host UX now supports this cleanup path:

1. Host Evidence presentation renders durable sandbox receipt evidence cards.
2. Scheduler Operator derives selectable receipt candidates from those cards.
3. Selecting a candidate fills the cleanup evidence path input.
4. The operator must still explicitly confirm cleanup.
5. Cleanup continues to call `doc-based-coding scheduler cleanup-receipts`.

This closes the main safety gap in the manual cleanup-only control: choosing the
right receipt path no longer depends primarily on raw typing when relevant
evidence is visible.

## Candidate A - Full Workflow Mode Host UX

### Goal

Expose `doc-based-coding scheduler sandbox-receipt-workflow` from Host UX with
explicit allocate/read/cleanup/read controls.

### Narrow Scope

1. Let the operator choose `run-once` or `daemon-loop`.
2. Require explicit source repo root and git-worktree sandbox root.
3. Require explicit allocation evidence id/path.
4. Keep cleanup opt-in separate and fail closed when cleanup output is provided
   without cleanup.
5. Show pre-cleanup and post-cleanup Host Evidence readback.

### Why Next

The backend CLI/MCP surface already exists. The Host UX now has evidence
selection and cleanup controls, so a separate full workflow mode can reuse those
pieces without mixing them into the cleanup-only card.

## Candidate B - Cleanup Outcome Diff View

### Goal

Show before/after differences between source receipt evidence and cleanup output
evidence.

### Narrow Scope

1. Compare cleanup required/completed/failed allocation ids.
2. Highlight changed cleanup state per allocation.
3. Link source and cleanup receipt refs.
4. Keep the view read-only.

### Why Lower Priority

It improves operator clarity, but it depends on having both source and cleanup
evidence available. Full workflow mode would more consistently produce those
pairs.

## Recommendation

Choose Candidate A next if continuing Host UX sandbox work:

```text
Host UX Full Sandbox Receipt Workflow Mode
```

Reason:

1. backend workflow contract already exists;
2. discovery/selection makes the cleanup part safer;
3. workflow mode can create the source/readback/cleanup/readback pair needed by
   a later diff view;
4. it remains a clear separate gate from cleanup-only evidence selection.

If the next larger project direction switches back to agent orchestration, keep
Candidate A as a near-term Host UX backlog item rather than expanding the
current completed slice.
