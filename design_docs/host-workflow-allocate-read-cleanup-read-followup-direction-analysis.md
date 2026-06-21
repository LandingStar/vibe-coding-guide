# Host Workflow For Allocate-Read-Cleanup-Read Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-host-workflow-allocate-read-cleanup-read.md`
closed with a backend helper that sequences host allocation evidence, focused
Host Evidence readback, explicit cleanup, and post-cleanup readback.

Review evidence:

- `review/host-workflow-allocate-read-cleanup-read-2026-06-21.md`

## Current Position

The git-worktree receipt lifecycle now has:

1. explicit host-run git-worktree opt-in;
2. explicit host daemon-loop git-worktree opt-in;
3. durable allocation receipt evidence;
4. explicit cleanup runner over durable receipts;
5. Host Evidence readback for allocation and cleanup states;
6. one backend workflow helper that composes both host-run and daemon-loop
   lifecycle modes.

The next gap is invocation surface. The helper is available to Python callers,
but operators and MCP hosts still need a stable command/tool wrapper if this is
to become a practical scheduler operation.

## Candidate A - CLI/MCP Surface For Host Sandbox Receipt Workflow

### Goal

Expose the backend workflow helper through explicit CLI and MCP surfaces while
preserving cleanup opt-in semantics.

### Narrow Scope

1. Add a CLI command that invokes `run_host_sandbox_receipt_workflow()`.
2. Add a matching MCP tool with the same request shape.
3. Keep Host UX button work deferred.
4. Require explicit `cleanup=true` before cleanup output path/id is accepted.
5. Add focused CLI/MCP tests over fake-runtime temporary git repositories.

### Why Now

The backend contract exists and has test coverage. CLI/MCP exposure is the
lowest-friction way to dogfood it without committing to a Host UX selection
model.

## Candidate B - Host UX Selection And Cleanup Action

### Goal

Add a Host UX flow to select an allocation receipt evidence artifact, invoke
cleanup, and refresh Host Evidence presentation.

### Why Lower Priority

The UI needs a selection and confirmation model. Binding UI before proving the
workflow command surface risks hard-coding interaction details that should stay
thin and replaceable.

## Candidate C - Live Runtime Dogfood Over Workflow Helper

### Goal

Use the helper around a credentialed live runtime scenario after fake-runtime
workflow behavior is stable.

### Why Lower Priority

The current evidence chain is fake-runtime deterministic. Live runtime dogfood
should wait until operators can invoke the helper through a stable CLI/MCP
surface and inspect both allocation and cleanup outputs.

## Recommendation

Choose Candidate A next:

```text
CLI/MCP Surface For Host Sandbox Receipt Workflow
```

Reason:

1. the backend helper is already contract-tested;
2. CLI/MCP gives an operator path without forcing Host UX design choices;
3. it preserves the explicit cleanup authority split;
4. later Host UX can call the same workflow surface instead of duplicating
   allocation/readback/cleanup/readback orchestration.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-21-host-sandbox-receipt-workflow-cli-mcp-surface.md`

Suggested first slice:

1. expose a CLI command for fake-runtime one-shot and daemon-loop workflow
   modes;
2. expose an MCP tool with matching request fields;
3. cover cleanup opt-in validation and successful cleanup readback;
4. keep Host UX binding deferred.
