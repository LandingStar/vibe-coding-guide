# Git Worktree Receipt Readback Cleanup Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-git-worktree-receipt-readback-and-cleanup-policy.md`
closed with read-only git-worktree receipt projection in scheduler authorization
readback.

Review evidence:

- `review/git-worktree-receipt-readback-and-cleanup-policy-2026-06-21.md`

## Current Position

The git-worktree provider line now has:

1. explicit provider allocation and cleanup receipts;
2. fail-closed acquired lease authorization;
3. read-only receipt projection when allocation evidence is supplied by a
   caller;
4. cleanup owner/policy metadata in the readback product.

The remaining gap is durability. Snapshot/MCP readback cannot yet recover real
git-worktree receipts unless a host or runner stores allocation evidence in a
known artifact.

## Candidate A - Durable Sandbox Allocation Receipt Evidence

### Goal

Define and persist a minimal sandbox allocation receipt evidence artifact that
can carry git-worktree allocation/cleanup receipts from controlled host runs to
readback/CLI/MCP consumers.

### Narrow Scope

1. Define a JSON-safe evidence artifact for sandbox allocations.
2. Add writer/reader helpers for local `.codex/scheduler/evidence/` files.
3. Allow authorization readback snapshot helpers to merge optional receipt
   evidence by task id.
4. Keep provider execution explicit and external to the evidence reader.

### Non-Goals

1. No default git-worktree provider registration.
2. No live Qoder/runtime execution.
3. No cleanup daemon.
4. No Host UX mutation controls.
5. No scheduler admission schema redesign.

### Why Now

Receipt readback exists, but only for caller-supplied in-memory allocations.
Durable evidence is the smallest next step that makes provider receipts useful
to CLI/MCP/Host UX without enabling live execution.

## Candidate B - Controlled Host Run Opt-In Provider Wiring

### Goal

Allow a host-controlled scheduler run to opt into a provided
`GitWorktreeSandboxProvider` and emit receipt evidence.

### Why Lower Priority

This should consume the durable evidence artifact rather than inventing receipt
persistence inside host-run wiring.

## Candidate C - Cleanup Policy Runner

### Goal

Add an explicit cleanup runner over durable receipts.

### Why Lower Priority

Cleanup execution should follow durable evidence and host-run opt-in wiring so
there is a real allocation history to clean.

## Recommendation

Choose Candidate A next:

```text
Durable Sandbox Allocation Receipt Evidence
```

Reason:

1. it connects the current readback product to persisted operator evidence;
2. it does not prematurely enable live provider execution;
3. it gives later host-run wiring and cleanup runner slices a shared artifact;
4. it preserves the contract-first rhythm of the sandbox/provider line.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-21-durable-sandbox-allocation-receipt-evidence.md`

Suggested first slice:

1. define the receipt evidence JSON contract;
2. add read/write helpers and tests;
3. let readback snapshot helpers merge optional evidence files;
4. defer provider execution and cleanup runner behavior.
