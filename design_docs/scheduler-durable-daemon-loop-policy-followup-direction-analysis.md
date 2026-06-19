# Scheduler Durable Daemon Loop Policy Follow-Up Direction Analysis

> Date: 2026-06-19
> Status: direction analysis

## Context

The scheduler daemon loop policy slice added:

- `SchedulerDaemonLoopStopPolicy`
- `SchedulerDaemonLoopRequest`
- `SchedulerDaemonLoopIteration`
- `SchedulerDaemonLoopResult`
- `run_scheduler_daemon_loop()`
- `doc-based-coding scheduler daemon-loop`

Latest implementation review:

- `review/scheduler-durable-daemon-loop-policy-2026-06-19.md`

Current operator flow can now be:

1. `doc-based-coding resources read dbc://exchange-artifacts/bundle`
2. `admitExchangeArtifact` or
   `doc-based-coding scheduler admit-exchange-artifact`
3. `doc-based-coding scheduler daemon-loop --max-ticks N`
4. `doc-based-coding scheduler inspect-state`
5. `doc-based-coding scheduler project`

## Current Position

The scheduler now has:

1. Durable task submission.
2. Exact-version stored-artifact admission through CLI and MCP.
3. Admission ledger and admission-state projection.
4. One bounded scheduler tick.
5. Repeated bounded daemon loop policy.
6. Explicit projection refresh after tick/loop.
7. Host-owned runtime seams for future injected runtime work.

This is still not a background daemon service. It is a durable scheduler control
contract that can be called by an operator, host, or later daemon process.

## Candidate A - Host Evidence Binding For Scheduler Loop

### Shape

Create a host/operator evidence product for scheduler loop results.

Minimum expected behavior:

1. Define a compact scheduler-loop evidence JSON schema.
2. Record loop request summary, stop reason, tick count, task-run count, final
   queue summary, authority split, and validation clues.
3. Keep evidence writing optional and explicit.
4. Expose read-only resource/CLI inspection after evidence exists.
5. Do not run provider, mutate scheduler state, or refresh projection from the
   read surface.

### Pros

1. Makes daemon-loop results inspectable without UI binding to raw internals.
2. Mirrors the existing host evidence pattern.
3. Creates a good bridge toward later UI/operator dashboards.

### Risks

1. Needs clear evidence path ownership.
2. Can drift into UI binding if not scoped.

### Fit

High. This is the best next step if the goal is operator visibility before real
provider execution.

## Candidate B - Host-Injected Runtime Daemon Loop

### Shape

Allow host-owned Python callers to run `run_scheduler_daemon_loop()` with an
injected runtime registry, including mock-Qoder validation.

### Pros

1. Moves closer to real multi-agent runtime orchestration.
2. Reuses existing injected runtime and host authorization seams.

### Risks

1. Changes provider authority and deserves a separate review boundary.
2. Live provider readiness remains environment-dependent.

### Fit

Medium-high, but should follow evidence binding unless the immediate goal is
runtime dogfood.

## Candidate C - Scheduler Projection After Loop Workflow Polish

### Shape

Improve operator guidance and maybe helper composition for:

```text
daemon-loop -> inspect-state -> project
```

### Pros

1. Makes current manual workflow easier.
2. Avoids provider authority changes.

### Risks

1. Lower leverage than evidence binding.
2. Could accidentally introduce automatic projection refresh, which current
   slices intentionally avoided.

### Fit

Medium. Useful but not the strongest next backend slice.

## Candidate D - UI Binding

### Shape

Bind scheduler loop summaries and projections into host UI.

### Pros

1. Makes scheduler progress visible to users.
2. Uses already structured loop results.

### Risks

1. Requires screenshot validation.
2. Current worktree has unrelated UI dirt; avoid mixing with backend loop
   policy.

### Fit

Useful later, separate gate.

## Recommendation

Choose Candidate A:

> Host Evidence Binding For Scheduler Loop

Reasoning:

1. The scheduler now has a real bounded loop contract but no durable evidence
   product for loop runs.
2. Evidence binding improves observability without changing provider
   authority.
3. It creates a clean bridge for future UI and host orchestration.

## Proposed Next Planning Gate

```text
2026-06-19-scheduler-loop-host-evidence-binding.md
```

Recommended acceptance:

1. Define scheduler-loop evidence product before implementation.
2. Keep evidence writing explicit and separate from read-only resources.
3. Record stop policy/result/authority clues.
4. Add CLI/resource readback if it stays read-only.
5. Do not add real provider execution, UI binding, automatic projection
   refresh, exchange artifact mutation, or Local Work Trajectory mutation.

## Deferred Candidates

1. Host-Injected Runtime Daemon Loop.
2. Scheduler Projection After Loop Workflow Polish.
3. UI Binding.
4. Full retry/cancellation/operator-control protocol.

