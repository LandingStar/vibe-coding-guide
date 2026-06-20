# Controlled Host Run Opt-In Provider Wiring Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-controlled-host-run-opt-in-provider-wiring.md`
closed with host-controlled one-shot git-worktree opt-in and durable allocation
receipt evidence writeback.

Review evidence:

- `review/controlled-host-run-opt-in-provider-wiring-2026-06-21.md`

## Current Position

The git-worktree sandbox line now has:

1. provider allocation and cleanup receipts;
2. acquired edit lease lifecycle authorization;
3. read-only authorization readback with optional durable receipt merge;
4. file-backed sandbox allocation receipt evidence;
5. one-shot host-run opt-in that emits durable allocation receipts.

The remaining operational gap is cleanup. Host runs can now create git
worktrees and persist receipts, but there is no controlled runner that consumes
those receipts and records cleanup results.

## Candidate A - Cleanup Policy Runner Over Durable Receipts

### Goal

Add an explicit cleanup runner that reads
`sandbox_allocation_receipt_evidence`, runs cleanup for git-worktree allocations
that still require cleanup, and writes a new durable receipt evidence artifact
with cleanup command receipts.

### Narrow Scope

1. Read one durable sandbox allocation receipt evidence artifact.
2. Select git-worktree allocations with `cleanup_required=True`.
3. Run explicit `GitWorktreeSandboxProvider.cleanup()` using caller-provided
   git executable policy.
4. Write updated durable receipt evidence to a caller-provided or default path.
5. Preserve read-only inspection behavior for normal readback paths.

### Non-Goals

1. No background cleanup daemon.
2. No implicit cleanup during host runs.
3. No Host UX controls.
4. No scheduler admission schema changes.
5. No live Qoder/runtime expansion.

### Why Now

The previous slice created real allocation receipts through host opt-in. Cleanup
runner work now has real evidence to consume and can stay explicit.

## Candidate B - Host UX Readback Linkage For Receipt Evidence

### Goal

Expose the new sandbox allocation evidence path in Host UX and readback panels.

### Why Lower Priority

The operator visibility surface is useful, but cleanup is the immediate safety
gap after real worktree creation.

## Candidate C - Daemon Loop Git-Worktree Opt-In

### Goal

Mirror one-shot host opt-in semantics into bounded host daemon loop requests.

### Why Lower Priority

Daemon loop wiring should wait until cleanup is explicit, otherwise repeated
host loop runs can create worktrees without an official cleanup surface.

## Recommendation

Choose Candidate A next:

```text
Cleanup Policy Runner Over Durable Receipts
```

Reason:

1. it closes the operational safety loop introduced by real worktree creation;
2. it consumes the durable receipt product instead of adding a new state shape;
3. it preserves explicit host/operator authority over cleanup;
4. it gives later Host UX and daemon-loop work a clean lifecycle to surface.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-21-cleanup-policy-runner-over-durable-receipts.md`

Suggested first slice:

1. add a receipt cleanup runner helper;
2. add focused tests over a temporary git repo allocation evidence artifact;
3. write updated receipt evidence after cleanup;
4. keep daemon and UI integration deferred.
