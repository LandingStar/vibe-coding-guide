# Host-Injected Scheduler Daemon Loop Follow-Up Direction Analysis

> Date: 2026-06-19
> Status: direction analysis

## Context

The host-injected scheduler daemon loop slice added:

- `HostSchedulerDaemonLoopRequest`
- `HostSchedulerDaemonLoopResult`
- `run_host_authorized_scheduler_daemon_loop()`
- fake host-loop validation
- mock-Qoder host-loop validation
- explicit host-loop `scheduler_loop_evidence` writing
- prompt guidance that CLI/MCP daemon loop remains fake-only

Latest implementation review:

- `review/host-injected-scheduler-daemon-loop-2026-06-19.md`

## Current Position

The scheduler now has:

1. durable task submission and ExchangeArtifact admission;
2. admission ledger and admission-state projection;
3. one bounded scheduler tick;
4. bounded repeated scheduler daemon loop;
5. explicit scheduler-loop evidence;
6. read-only evidence bundle/presentation inspection;
7. host-owned injected runtime daemon-loop execution for fake and mock-Qoder.

The remaining gap is not raw provider execution. The immediate gap is operator
workflow composition: after a host daemon loop writes evidence, projection
refresh and readback are still separate steps.

## Candidate A - Host Loop Projection Workflow Polish

### Shape

Add a narrow host-owned helper that composes:

```text
run_host_authorized_scheduler_daemon_loop()
scheduler projection refresh
optional scheduler_loop_evidence write
compact readback summary
```

The helper should keep projection refresh explicit in its name/result and should
not become a background daemon.

### Pros

1. Completes the host loop operator workflow without touching CLI/MCP provider
   boundaries.
2. Reuses the evidence product and scheduler projection surfaces already built.
3. Produces a clearer end-to-end artifact set for UI or release inspection.

### Risks

1. Can blur execution and projection authority if not named and documented
   carefully.
2. Could drift toward UI binding if the result shape is over-designed.

### Fit

High. This is the strongest next backend slice.

## Candidate B - Scheduler Loop Evidence Presentation Polish

### Shape

Refine `dbc://host-evidence/presentation` cards for host-loop evidence,
including host invocation id, runtime host surface, and provider clues.

### Pros

1. Improves operator and future UI readability.
2. Small, read-only surface.

### Risks

1. Lower leverage before projection workflow is composed.
2. Can be handled after richer host-loop evidence exists.

### Fit

Medium.

## Candidate C - Live Credentialed Provider Smoke

### Shape

Run live Qoder through the host-injected daemon loop when credentials and SDK
are available.

### Pros

1. Produces real-provider evidence.

### Risks

1. Environment dependent.
2. Not needed to validate the orchestration contract.
3. Can leak scope into provisioning and credential handling.

### Fit

Low for the immediate next slice.

## Candidate D - UI Binding

### Shape

Bind host-loop evidence/presentation into the VS Code UI.

### Pros

1. Makes host-loop evidence visible.

### Risks

1. Requires screenshot validation.
2. Current worktree has unrelated UI dirt.
3. Better after projection workflow polish.

### Fit

Later, separate gate.

## Recommendation

Choose Candidate A:

> Host Loop Projection Workflow Polish

Reasoning:

1. Runtime authority is now in the right place: host-owned Python injection.
2. Evidence writing exists, but projection readback still requires manual
   composition.
3. A narrow host-owned compose helper can improve workflow without exposing real
   providers through CLI/MCP or starting a daemon service.

## Proposed Next Planning Gate

```text
2026-06-19-host-loop-projection-workflow-polish.md
```

Recommended acceptance:

1. Define host loop + projection request/result before implementation.
2. Reuse `run_host_authorized_scheduler_daemon_loop()` internally.
3. Explicitly refresh scheduler projection only because the helper name/result
   says so.
4. Preserve scheduler-loop evidence write/readback.
5. Validate fake and mock-Qoder injected runtime paths.
6. Do not expose real providers through CLI/MCP, add UI binding, mutate
   ExchangeArtifact lifecycle, mutate admission ledger, or mutate Local Work
   Trajectory from scheduler code.

## Deferred Candidates

1. Scheduler Loop Evidence Presentation Polish.
2. Live credentialed provider smoke.
3. UI Binding.
4. Background daemon/service lifecycle protocol.

