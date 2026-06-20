# Git Worktree Sandbox Provider Spike Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-git-worktree-sandbox-provider-spike-over-acquired-leases.md`
closed with a minimal `GitWorktreeSandboxProvider` that can allocate and clean
up deterministic worktrees in tests.

Review evidence:

- `review/git-worktree-sandbox-provider-spike-over-acquired-leases-2026-06-21.md`

## Current Position

The backend safety chain now reaches the first real filesystem isolation spike:

1. scheduler admission records edit lease conflict evidence;
2. scheduler lifecycle records acquired/released/revoked/expired lease authority;
3. sandbox allocation consumes acquired lifecycle metadata;
4. readback and Host UX expose metadata-only authorization facts;
5. `GitWorktreeSandboxProvider` can allocate explicit worktrees and record
   allocation/cleanup receipts.

The remaining gap is not raw allocation. It is operational lifecycle and
operator visibility around real provider receipts.

## Candidate A - Git Worktree Receipt Readback And Cleanup Policy

### Goal

Make `git-worktree` allocation receipts inspectable through the scheduler
authorization/readback path and define the minimal cleanup responsibility
boundary.

### Narrow Scope

1. Extend read-only authorization diagnostics to summarize optional
   `GitWorktreeSandboxReceipt` data when a caller supplies real allocation
   evidence.
2. Define cleanup receipt states and host/daemon responsibility in one narrow
   contract.
3. Add tests for allocated, rejected, and cleanup-completed receipts.
4. Keep provider registration explicit and opt-in.

### Non-Goals

1. No default daemon registration.
2. No automatic cleanup daemon.
3. No live Qoder/runtime execution through the provider.
4. No Host UX mutation controls.
5. No scheduler admission schema redesign.

### Why Now

The provider can already allocate. Before using it in operator flows, humans and
future host adapters need a reliable way to inspect what was allocated and who
is responsible for cleanup.

## Candidate B - Provider Registry Wiring For Controlled Host Runs

### Goal

Allow controlled host scheduler runs to opt into a caller-provided
`GitWorktreeSandboxProvider`.

### Why Lower Priority

This makes real provider execution easier before receipt visibility and cleanup
responsibility are fully visible. It should follow Candidate A.

## Candidate C - Lease Expiry Sweep Before Provider Preflight

### Goal

Expire stale acquired leases inside bounded scheduler loops before provider
allocation.

### Why Lower Priority

Expiry sweeping changes scheduling behavior. It is safer after provider receipt
readback makes rejected/expired behavior easy to inspect.

## Recommendation

Choose Candidate A next:

```text
Git Worktree Receipt Readback And Cleanup Policy
```

Reason:

1. real worktree allocation now exists but remains mostly visible only in tests;
2. cleanup is explicit and receipt-based, with no durable owner yet;
3. readback is already the established operator diagnostic product;
4. keeping this as a read-only/contract-first slice avoids prematurely enabling
   live provider execution.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-21-git-worktree-receipt-readback-and-cleanup-policy.md`

Suggested first slice:

1. define the receipt readback projection shape;
2. document cleanup ownership states;
3. add focused readback tests over synthetic git-worktree allocations;
4. defer default provider registration and live runtime execution.
