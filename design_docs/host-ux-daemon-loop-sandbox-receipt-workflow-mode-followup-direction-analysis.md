# Host UX Daemon-Loop Sandbox Receipt Workflow Mode Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-host-ux-daemon-loop-sandbox-receipt-workflow-mode.md`
closed with both `run-once` and `daemon-loop` Host UX bindings for
`scheduler sandbox-receipt-workflow`.

Review evidence:

- `review/host-ux-daemon-loop-sandbox-receipt-workflow-mode-2026-06-21.md`

## Current Position

The Scheduler Operator Host UX now has the complete first workflow-mode surface
for sandbox receipts:

1. read-only Host Evidence presentation;
2. cleanup-only receipt selection and explicit cleanup invocation;
3. full sandbox receipt workflow invocation in `run-once` mode;
4. full sandbox receipt workflow invocation in bounded `daemon-loop` mode.

The Host UX remains fake-runtime-only and does not refresh scheduler projection
or mutate Local Work Trajectory.

## Candidate A - Cleanup Outcome Diff View

### Goal

Compare allocation evidence and cleanup evidence after workflow execution.

### Narrow Scope

1. Show cleanup required/completed/failed id changes.
2. Highlight per-allocation cleanup state transitions.
3. Link allocation and cleanup evidence refs.
4. Keep the view read-only.

### Why Next

Both workflow modes can now produce allocation evidence and optional cleanup
evidence. A diff view would make the evidence pair easier to inspect without
changing scheduler/runtime behavior.

## Candidate B - Evidence-Aware Workflow Defaults

### Goal

Use selected Host Evidence receipt candidates to prefill workflow input fields.

### Narrow Scope

1. Prefill only visible path/id fields.
2. Keep cleanup opt-in unchecked by default.
3. Do not auto-run cleanup or workflow actions.
4. Preserve manual input override.

### Why Lower Priority

This improves operator ergonomics, but can blur cleanup-only evidence selection
and new workflow allocation output. It is better after the evidence readback
story is clearer.

## Candidate C - Scheduler Projection Refresh Integration

### Goal

Offer a follow-up refresh after workflow execution so scheduler-derived
trajectory projection can be inspected from the same Host UX flow.

### Why Lower Priority

Projection refresh is already available as a separate explicit Scheduler
Operator action. Folding it into workflow mode should wait until the evidence
inspection surface is easier to read.

## Recommendation

Choose Candidate A next if continuing the Host UX sandbox branch:

```text
Host UX Cleanup Outcome Diff For Sandbox Receipt Workflow
```

Reason:

1. the workflow can now create the evidence pair in both modes;
2. diffing is read-only and does not broaden runtime authority;
3. it reduces operator ambiguity around whether cleanup actually changed the
   receipt state;
4. it can be tested with deterministic presentation fixtures and screenshot
   validation.
