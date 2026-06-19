# Host Loop Projection Workflow Polish Follow-Up Direction Analysis

> Date: 2026-06-19
> Status: direction analysis

## Context

The host loop projection workflow polish slice added:

- `HostSchedulerDaemonLoopProjectionRefreshResult`
- `run_host_authorized_scheduler_daemon_loop_and_refresh_projection()`
- fake host-loop projection validation
- mock-Qoder host-loop projection validation
- optional `scheduler_loop_evidence` preservation
- compact readback with `scheduler_projection_path` and `projection_summary`

Latest implementation review:

- `review/host-loop-projection-workflow-polish-2026-06-19.md`

## Current Position

The scheduler orchestration backend now has a bounded path from:

1. stored task admission;
2. scheduler daemon-loop advancement;
3. host-injected fake/mock-Qoder runtime execution;
4. optional scheduler-loop evidence write;
5. scheduler-derived trajectory projection refresh;
6. compact host workflow readback.

The remaining backend roughness is not execution. It is readback quality for
operators and future UI consumers.

## Candidate A - Scheduler Loop Evidence Presentation Polish

### Shape

Refine `dbc://host-evidence/presentation` for scheduler-loop evidence and host
loop projection workflow evidence clues.

Likely fields:

1. host invocation id and runtime host surface;
2. runtime provider;
3. tick count and total run count;
4. stop reason/detail;
5. final queue summary highlights;
6. scheduler projection path when available in metadata or companion readback;
7. authority split facts.

### Pros

1. Improves operator readability without changing scheduler state or runtime
   authority.
2. Builds directly on the new compact host workflow result.
3. Creates a cleaner input for later VS Code/UI binding.

### Risks

1. Presentation can become UI design if over-scoped.
2. Needs careful handling of evidence files that do not carry projection
   metadata.

### Fit

High. This is the strongest next narrow backend/readback slice.

## Candidate B - Host Loop Workflow Evidence Metadata

### Shape

Extend the host loop projection workflow helper to write projection path and
projection summary into `scheduler_loop_evidence.metadata`.

### Pros

1. Makes projection clues durable in the evidence artifact.
2. Simplifies future presentation readback.

### Risks

1. Slightly blurs evidence vs workflow result if not documented carefully.
2. Could require another test matrix over old/new evidence.

### Fit

Medium. Useful, but likely best combined with or after Candidate A if a
presentation gap demands durable projection clues.

## Candidate C - Live Credentialed Provider Smoke

### Shape

Run the host loop projection workflow against live Qoder when host credentials
and SDK are available.

### Pros

1. Produces real-provider evidence over the composed workflow.

### Risks

1. Environment dependent.
2. Not needed to validate the host workflow contract.
3. Can leak into provisioning and credential handling.

### Fit

Low for immediate next work.

## Candidate D - UI Binding

### Shape

Bind host-loop evidence/projection readback into VS Code UI.

### Pros

1. Makes evidence visible to users.

### Risks

1. Requires screenshot validation.
2. Current backend readback can still be improved first.
3. Worktree contains unrelated UI dirt from older slices.

### Fit

Later, separate gate.

## Recommendation

Choose Candidate A:

> Scheduler Loop Evidence Presentation Polish

Reasoning:

1. Host execution and projection refresh now have a compact workflow.
2. Operators still need a clearer read-only presentation surface before UI
   binding.
3. This preserves the current authority split while improving the product
   surface that future UI can consume.

## Proposed Next Planning Gate

```text
2026-06-19-scheduler-loop-evidence-presentation-polish.md
```

Recommended acceptance:

1. Keep the surface read-only.
2. Improve scheduler-loop evidence cards with host/runtime/queue/projection
   clues where available.
3. Preserve malformed evidence isolation.
4. Do not add provider execution, scheduler mutation, projection refresh, UI
   binding, ExchangeArtifact mutation, admission ledger mutation, or Local Work
   Trajectory mutation.

## Deferred Candidates

1. Host loop workflow evidence metadata.
2. Live credentialed provider smoke.
3. UI Binding.
4. Background daemon/service lifecycle protocol.
