# Durable Sandbox Allocation Receipt Evidence Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-durable-sandbox-allocation-receipt-evidence.md`
closed with a file-backed `sandbox_allocation_receipt_evidence` product and
snapshot readback merge support.

Review evidence:

- `review/durable-sandbox-allocation-receipt-evidence-2026-06-21.md`

## Current Position

The git-worktree sandbox line now has:

1. explicit provider allocation and cleanup receipts;
2. fail-closed acquired edit lease lifecycle authorization;
3. read-only scheduler authorization readback projection;
4. durable receipt evidence read/write helpers;
5. snapshot readback merge by task id without provider or cleanup execution.

The remaining gap is controlled production of receipt evidence. A host or runner
can now persist receipts, but scheduler host-run wiring does not yet opt into a
real sandbox provider or write the durable receipt artifact.

## Candidate A - Controlled Host Run Opt-In Provider Wiring

### Goal

Allow a host-controlled scheduler run to opt into a supplied
`GitWorktreeSandboxProvider`, allocate sandboxes for eligible tasks, and emit
durable `sandbox_allocation_receipt_evidence`.

### Narrow Scope

1. Add an explicit host-run option for git-worktree sandbox allocation.
2. Require caller-provided sandbox root and git repository root.
3. Keep acquired edit lease lifecycle as the authorization source.
4. Write durable receipt evidence after allocation.
5. Keep fake-runtime and existing shared-process default behavior unchanged.

### Non-Goals

1. No default provider registration.
2. No live Qoder/runtime expansion.
3. No cleanup runner.
4. No Host UX mutation controls.
5. No scheduler admission schema redesign.

### Why Now

Durable receipt evidence exists, so host-run wiring can consume the shared
artifact instead of inventing a second persistence shape.

## Candidate B - Cleanup Policy Runner

### Goal

Add an explicit cleanup runner that consumes durable git-worktree allocation
receipts and records cleanup command receipts.

### Why Lower Priority

There is still no normal host-run path that emits durable allocation receipts.
Cleanup should follow real allocation evidence production.

## Candidate C - Scheduler Authorization Readback CLI Surface

### Goal

Expose snapshot readback plus optional receipt evidence path through a CLI
command for operators and tests.

### Why Lower Priority

The readback product already exists in Python/MCP paths. CLI polish is useful,
but it does not advance real receipt production.

## Recommendation

Choose Candidate A next:

```text
Controlled Host Run Opt-In Provider Wiring
```

Reason:

1. it is the smallest step that turns durable receipt evidence into live
   operator data;
2. it keeps real provider execution explicitly host-owned;
3. it preserves acquired lease lifecycle as the authorization authority;
4. it gives later cleanup runner and Host UX readback work real evidence to
   consume.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-21-controlled-host-run-opt-in-provider-wiring.md`

Suggested first slice:

1. add a host-run request option for git-worktree sandbox provider wiring;
2. require explicit sandbox root and source repository root;
3. write durable allocation receipt evidence for allocations attempted in the
   run;
4. keep cleanup and UI binding deferred.
