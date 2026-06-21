# Host UX Full Sandbox Receipt Workflow Mode Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-host-ux-full-sandbox-receipt-workflow-mode.md`
closed with the first Host UX binding for `scheduler sandbox-receipt-workflow`
in `run-once` mode.

Review evidence:

- `review/host-ux-full-sandbox-receipt-workflow-mode-2026-06-21.md`

## Current Position

The Scheduler Operator Host UX now has three sandbox receipt surfaces:

1. Host Evidence readback cards for durable receipt evidence;
2. cleanup-only receipt selection and explicit cleanup invocation;
3. run-once full sandbox receipt workflow invocation.

The run-once workflow can create allocation evidence and optionally cleanup
evidence through the existing backend CLI. It remains fake-runtime-only and does
not refresh scheduler projection or mutate Local Work Trajectory.

## Candidate A - Daemon-Loop Workflow Mode

### Goal

Extend the Host UX workflow card to support backend
`scheduler sandbox-receipt-workflow --mode daemon-loop`.

### Narrow Scope

1. Add an explicit mode selector.
2. Require daemon-loop bounds:
   - max ticks;
   - max runs per tick;
   - max runtime failures.
3. Keep fake-runtime-only behavior.
4. Keep cleanup opt-in semantics unchanged.
5. Validate with contract tests and screenshot.

### Why Next

The backend already supports daemon-loop mode. The UI now has the right workflow
shape, so adding a mode selector is a natural incremental extension.

## Candidate B - Cleanup Outcome Diff View

### Goal

Compare allocation evidence and cleanup evidence after workflow execution.

### Narrow Scope

1. Show cleanup required/completed/failed id changes.
2. Highlight per-allocation cleanup state transitions.
3. Link allocation and cleanup evidence refs.
4. Keep the view read-only.

### Why Lower Priority

The current Host UX can now create the evidence pair, but the first readback
view can still rely on Host Evidence cards. Diff view is useful after both
workflow modes are available.

## Candidate C - Evidence-Aware Workflow Defaults

### Goal

Use selected Host Evidence candidates to fill workflow allocation/cleanup
evidence fields.

### Why Lower Priority

It improves ergonomics, but can blur the distinction between cleanup-only
receipts and new workflow allocation outputs. It should follow the clearer mode
contract.

## Recommendation

Choose Candidate A next if continuing Host UX sandbox work:

```text
Host UX Daemon-Loop Sandbox Receipt Workflow Mode
```

Reason:

1. backend CLI/MCP mode already exists;
2. run-once UI has established the action contract and validation path;
3. keeping daemon-loop separate limits risk and preserves test clarity;
4. diff/readback improvements become more valuable once both execution modes are
   reachable from Host UX.
