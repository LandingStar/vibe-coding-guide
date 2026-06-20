# Daemon Loop Git-Worktree Opt-In Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-daemon-loop-git-worktree-opt-in.md`
closed with bounded host daemon-loop support for explicit git-worktree sandbox
opt-in and durable allocation receipt evidence writeback.

Review evidence:

- `review/daemon-loop-git-worktree-opt-in-2026-06-21.md`

## Current Position

The git-worktree sandbox lifecycle now has:

1. acquired edit lease lifecycle authorization;
2. real `GitWorktreeSandboxProvider` allocation and cleanup receipts;
3. durable `sandbox_allocation_receipt_evidence`;
4. one-shot host-run opt-in receipt writeback;
5. explicit cleanup runner CLI/MCP surface;
6. Host Evidence readback for allocation/cleanup receipt state;
7. bounded host daemon-loop opt-in receipt writeback.

The remaining operational gap is workflow coherence. The pieces exist, but an
operator or Host UX caller still has to coordinate allocation evidence, cleanup
invocation, and post-cleanup readback manually.

## Candidate A - Host Workflow For Allocate-Read-Cleanup-Read

### Goal

Define a host/operator workflow helper that explicitly sequences:

```text
daemon-loop or one-shot host run
-> durable allocation receipt evidence
-> Host Evidence readback
-> explicit cleanup runner
-> updated Host Evidence readback
```

### Narrow Scope

1. Keep cleanup explicit and opt-in.
2. Consume existing receipt evidence contracts without changing scheduler
   admission schema.
3. Produce one compact workflow result with paths to allocation and cleanup
   evidence artifacts.
4. Reuse existing CLI/MCP cleanup runner and Host Evidence presentation
   products.
5. Add focused runtime/CLI tests; UI binding remains optional unless a later
   gate chooses it.

### Why Now

Daemon-loop work can now create durable worktree receipts. The safest next
step is making the complete lifecycle easy to run and inspect without turning
cleanup into an implicit daemon side effect.

## Candidate B - CLI Daemon-Loop Git-Worktree Opt-In Surface

### Goal

Expose the new daemon-loop opt-in fields directly on CLI command surfaces.

### Why Lower Priority

The backend contract is ready, but exposing raw flags before a workflow helper
risks encouraging partial operation: allocate receipts without a matching
cleanup/readback routine.

## Candidate C - Host UX Cleanup Action

### Goal

Add a Host UX button that invokes cleanup for a selected durable receipt
artifact and refreshes Host Evidence readback.

### Why Lower Priority

The UX action needs a selection/confirmation model. A backend workflow helper
can define that contract first and keep the UI thin.

## Recommendation

Choose Candidate A next:

```text
Host Workflow For Allocate-Read-Cleanup-Read
```

Reason:

1. all required backend products already exist;
2. it keeps cleanup explicit while reducing operator error;
3. it gives later CLI/Host UX surfaces one stable workflow contract to call;
4. it avoids hiding cleanup inside the daemon loop, preserving the authority
   split established by the current cleanup evidence line.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-21-host-workflow-allocate-read-cleanup-read.md`

Suggested first slice:

1. define a compact workflow request/result contract around existing host-run or
   daemon-loop result plus cleanup runner result;
2. implement the helper with explicit cleanup opt-in and evidence paths;
3. validate with a temporary git repo and Host Evidence readback before/after
   cleanup;
4. keep CLI/Host UX binding deferred unless the workflow contract proves stable.
