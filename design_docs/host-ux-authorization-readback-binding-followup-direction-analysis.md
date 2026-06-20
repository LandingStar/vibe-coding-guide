# Host UX Authorization Readback Binding Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-host-ux-authorization-readback-binding.md`
closed with a read-only Host UX diagnostic surface for scheduler authorization
facts.

Review evidence:

- `review/host-ux-authorization-readback-binding-2026-06-21.md`
- Screenshot: `output/playwright/host-ux-authorization-readback/authorization-readback.png`

## Current Position

The metadata-only authorization chain now has both backend and operator
visibility:

1. scheduler admission records edit lease conflict evidence;
2. scheduler lifecycle records requested/acquired/released/revoked/expired
   authority;
3. sandbox allocation consumes acquired lifecycle metadata;
4. MCP/readback exposes the authorization product;
5. Host UX shows the readback product in the Scheduler Operator panel.

The remaining product gap is no longer visibility. It is enforcement.

## Candidate A - Git Worktree Sandbox Provider Spike Over Acquired Leases

### Goal

Introduce the first real sandbox provider spike that consumes acquired edit
lease lifecycle authority.

### Narrow Scope

1. Choose `git-worktree` as the first provider strategy.
2. Allocate deterministic per-task workspace directories.
3. Materialize or expose only lease-authorized writable paths.
4. Preserve required read-only refs when possible.
5. Emit allocation and cleanup receipts.
6. Fail closed when lifecycle authorization is missing or non-acquired.
7. Keep fake-runtime compatibility for tests.

### Non-Goals

1. No Docker/VM/remote provider.
2. No Host UX mutation controls.
3. No scheduler admission schema expansion unless provider receipts require a
   narrow metadata field.
4. No automatic background cleanup daemon.
5. No Local Work Trajectory mutation from provider code.

### Why Now

The readback UI makes authorization failures inspectable. A worktree provider
is the next smallest step from metadata-only isolation toward real filesystem
separation.

## Candidate B - Scheduler Authorization Readback CLI Surface

### Goal

Expose the same readback product through a CLI command.

### Why Lower Priority

Codex/MCP and Host UX now both have readback visibility. CLI can follow once
provider spike output clarifies which receipt fields operators need.

## Candidate C - Lease Expiry Sweep In Daemon Loop

### Goal

Use explicit scheduler loop time inputs to expire leases before provider
preflight.

### Why Lower Priority

Expiry sweeping changes scheduling behavior. It is safer after at least one
provider spike proves how expired/non-acquired leases should fail in practice.

## Recommendation

Choose Candidate A next:

```text
Git Worktree Sandbox Provider Spike Over Acquired Leases
```

Reason:

1. backend authorization and Host UX readback are now both in place;
2. the platform still lacks real filesystem isolation;
3. worktree isolation is narrower and more inspectable than Docker/VM;
4. the existing Host UX readback can diagnose provider authorization failures.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-21-git-worktree-sandbox-provider-spike-over-acquired-leases.md`

Suggested first slice:

1. define provider contract additions for worktree allocation receipts;
2. implement deterministic worktree allocation/cleanup in a test temp repo;
3. wire fail-closed lifecycle authorization checks;
4. add focused runtime tests;
5. defer Host UX and background daemon behavior.
