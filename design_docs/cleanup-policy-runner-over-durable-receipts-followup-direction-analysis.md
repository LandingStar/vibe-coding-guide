# Cleanup Policy Runner Over Durable Receipts Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-cleanup-policy-runner-over-durable-receipts.md`
closed with an explicit backend cleanup runner over durable
`sandbox_allocation_receipt_evidence`.

Review evidence:

- `review/cleanup-policy-runner-over-durable-receipts-2026-06-21.md`

## Current Position

The git-worktree sandbox line now has:

1. acquired edit lease lifecycle authorization;
2. git-worktree allocation and cleanup command receipts;
3. read-only scheduler authorization readback with receipt projection;
4. durable sandbox allocation receipt evidence;
5. host-run opt-in that writes durable allocation evidence;
6. explicit cleanup runner that consumes durable evidence and writes cleanup
   receipts.

The remaining gap is an operator-facing invocation surface. The backend helper
is usable from tests and Python imports, but normal host or agent workflows need
a standard CLI/MCP command to run cleanup with explicit evidence paths.

## Candidate A - Cleanup Runner CLI/MCP Surface

### Goal

Expose `run_sandbox_allocation_cleanup_over_receipts()` through a narrow
operator surface, likely under the existing scheduler tool family.

### Narrow Scope

1. Add a CLI command that accepts input evidence path, optional output evidence
   path/id, timestamp, and git executable.
2. Add an MCP tool with the same explicit arguments and JSON result.
3. Keep cleanup explicit; do not infer or search evidence paths unless a caller
   asks for the default path by id.
4. Add focused CLI/MCP tests around a temp git repo receipt.

### Non-Goals

1. No background cleanup daemon.
2. No Host UX button.
3. No host-run implicit cleanup.
4. No scheduler admission schema change.

### Why Now

The backend cleanup runner is complete, but direct Python imports are not the
right operational boundary for users or host adapters.

## Candidate B - Host UX Readback Linkage For Cleanup Evidence

### Goal

Show cleanup evidence paths and cleanup state transitions in the existing
authorization readback Host UX.

### Why Lower Priority

Visibility is useful, but it should consume a standard cleanup invocation
surface rather than inventing UI-only cleanup behavior.

## Candidate C - Daemon Loop Git-Worktree Opt-In

### Goal

Mirror one-shot host-run git-worktree opt-in semantics into bounded host daemon
loop requests.

### Why Lower Priority

Daemon work should wait until cleanup can be invoked through a stable operator
surface. Otherwise repeated daemon runs can produce receipts without an equally
standard cleanup entry point.

## Recommendation

Choose Candidate A next:

```text
Cleanup Runner CLI/MCP Surface
```

Reason:

1. it turns the backend cleanup helper into a controlled operator action;
2. it preserves explicit cleanup ownership;
3. it gives Host UX and daemon-loop work a stable surface to consume later;
4. it keeps the next slice backend-only and testable without screenshots.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-21-cleanup-runner-cli-mcp-surface.md`

Suggested first slice:

1. add a CLI command over `run_sandbox_allocation_cleanup_over_receipts()`;
2. add a matching MCP tool;
3. add focused tests for CLI/MCP cleanup over temp git-worktree evidence;
4. keep Host UX and daemon integration deferred.
