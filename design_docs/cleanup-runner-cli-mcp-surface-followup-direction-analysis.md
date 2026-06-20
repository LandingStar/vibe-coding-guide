# Cleanup Runner CLI/MCP Surface Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-cleanup-runner-cli-mcp-surface.md`
closed with explicit CLI and MCP cleanup invocation over durable
`sandbox_allocation_receipt_evidence`.

Review evidence:

- `review/cleanup-runner-cli-mcp-surface-2026-06-21.md`

## Current Position

The git-worktree sandbox line now has:

1. acquired edit lease lifecycle authorization;
2. git-worktree allocation and cleanup command receipts;
3. read-only authorization readback with optional receipt projection;
4. durable sandbox allocation receipt evidence;
5. one-shot host-run opt-in that writes allocation receipts;
6. backend cleanup runner over durable receipts;
7. explicit CLI/MCP cleanup surfaces.

The remaining operational gap is visibility and workflow linkage. Operators can
now run cleanup, but the normal readback and Host UX surfaces do not yet make it
easy to see which receipt evidence exists, whether cleanup has already run, or
which updated evidence artifact should be inspected next.

## Candidate A - Host UX Readback Linkage For Cleanup Evidence

### Goal

Expose cleanup evidence facts through existing readback and Host UX surfaces so
operators can inspect allocation evidence, cleanup state, cleanup command
receipts, and updated evidence paths after invoking CLI/MCP cleanup.

### Narrow Scope

1. Extend readback/presentation consumption of existing
   `sandbox_allocation_receipt_evidence` summaries.
2. Surface cleanup state counts and cleanup output evidence path/id.
3. Reuse existing authorization/Host Evidence presentation patterns.
4. Keep cleanup execution in CLI/MCP; Host UX should remain read-only unless a
   later gate explicitly adds a button.

### Non-Goals

1. No Host UX cleanup button in the first readback linkage slice.
2. No daemon cleanup loop.
3. No default evidence discovery across arbitrary filesystem locations.
4. No scheduler admission schema changes.

### Why Now

CLI/MCP cleanup is usable, but operators still need a standard place to confirm
what cleanup did without manually opening raw JSON evidence files.

## Candidate B - Daemon Loop Git-Worktree Opt-In

### Goal

Mirror one-shot host-run git-worktree provider opt-in into bounded host daemon
loop requests.

### Why Lower Priority

Daemon loop work should wait until cleanup evidence visibility is in place.
Otherwise repeated daemon runs can produce more worktree receipt artifacts than
the operator can easily inspect.

## Candidate C - Cleanup Button Host UX Surface

### Goal

Add an explicit Host UX action that invokes the existing CLI/MCP cleanup surface
for a selected evidence artifact.

### Why Lower Priority

This can be useful, but it should come after readback linkage clarifies what
the user is selecting and what evidence transition they should expect.

## Recommendation

Choose Candidate A next:

```text
Host UX Readback Linkage For Cleanup Evidence
```

Reason:

1. cleanup now has an execution surface, so visibility is the next safety gap;
2. read-only linkage keeps the next slice smaller than a button or daemon path;
3. it gives future daemon and Host UX action work a clearer product to consume;
4. it avoids broadening cleanup ownership beyond explicit CLI/MCP invocation.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-21-host-ux-cleanup-evidence-readback-linkage.md`

Suggested first slice:

1. define the readback facts needed for cleanup evidence visibility;
2. bind existing durable receipt summaries into the Host Evidence/readback
   presentation path;
3. add backend/Host UX tests for read-only display state;
4. use screenshot validation if the Host UX panel is touched.
