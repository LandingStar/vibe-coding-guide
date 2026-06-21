# CLI/MCP Surface For Host Sandbox Receipt Workflow Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-host-sandbox-receipt-workflow-cli-mcp-surface.md`
closed with CLI and MCP surfaces for the shared host sandbox receipt workflow.

Review evidence:

- `review/host-sandbox-receipt-workflow-cli-mcp-surface-2026-06-21.md`

## Current Position

The git-worktree sandbox receipt lifecycle now has:

1. explicit host-run git-worktree opt-in;
2. explicit host daemon-loop git-worktree opt-in;
3. durable allocation receipt evidence;
4. explicit cleanup runner over durable receipts;
5. Host Evidence presentation readback for allocation and cleanup states;
6. a backend helper composing allocate/read/cleanup/read;
7. CLI and MCP invocation surfaces over that helper.

The next gap is operator ergonomics and selection safety. A human-facing Host UX
should not re-implement the workflow; it should call the same CLI/MCP/backend
contract and focus on choosing evidence, confirming cleanup, and rendering the
readback chain.

## Candidate A - Host UX Selection For Sandbox Receipt Workflow

### Goal

Add a Host UX flow that can select or enter sandbox allocation receipt evidence,
invoke the existing workflow or cleanup path explicitly, and refresh Host
Evidence presentation.

### Narrow Scope

1. Show available sandbox allocation/cleanup evidence artifacts from Host
   Evidence presentation or known evidence directory.
2. Require an explicit cleanup confirmation before calling the workflow with
   cleanup enabled.
3. Reuse CLI/MCP/backend workflow rather than duplicating logic in the webview.
4. Render allocation readback and cleanup readback status side by side.
5. Use screenshot validation.

### Why Next

The backend and operator command surfaces are stable. The remaining usability
gap is selecting the right receipt artifact and making cleanup authority visible
to the operator.

## Candidate B - Live Runtime Dogfood Over Sandbox Receipt Workflow

### Goal

Use the workflow around a credentialed live runtime scenario after fake-runtime
workflow invocation is stable.

### Why Lower Priority

The CLI/MCP surface is fake-only by design. Live runtime dogfood needs a
separate host-owned injected runtime permission story and should not be mixed
into the operator surface binding.

## Candidate C - Cleanup Policy Sweep Planning

### Goal

Design a policy-driven sweep over durable sandbox allocation receipt evidence.

### Why Lower Priority

Cleanup remains explicit by current contract. Automatic or semi-automatic sweep
behavior needs a stronger ownership model and should not be introduced until
manual selection and readback are ergonomic.

## Recommendation

Choose Candidate A next:

```text
Host UX Selection For Sandbox Receipt Workflow
```

Reason:

1. the backend/CLI/MCP contract is now stable;
2. Host UX can stay thin and call the same workflow surface;
3. cleanup is potentially destructive and needs a visible confirmation model;
4. screenshot validation can prove the operator readback flow before any live
   runtime expansion.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-21-host-ux-sandbox-receipt-workflow-selection.md`

Suggested first slice:

1. render receipt evidence candidates and current cleanup states;
2. add explicit cleanup action with confirmation;
3. call the existing workflow surface;
4. refresh Host Evidence presentation after completion;
5. validate with focused UI tests and screenshots.
