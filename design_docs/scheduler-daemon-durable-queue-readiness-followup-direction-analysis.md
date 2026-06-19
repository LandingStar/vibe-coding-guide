# Scheduler Daemon Durable Queue Readiness Follow-Up Direction Analysis

> Date: 2026-06-19
> Status: direction analysis

## Context

The daemon-readiness slice added a bounded one-tick scheduler contract:

- `SchedulerDaemonTickRequest`
- `SchedulerDaemonTickResult`
- `SchedulerDaemonQueueSummary`
- `run_scheduler_daemon_tick()`
- `doc-based-coding scheduler tick`

Latest implementation review:

- `review/scheduler-daemon-durable-queue-readiness-2026-06-19.md`

Current operator flow can now be:

1. `doc-based-coding resources read dbc://exchange-artifacts/bundle`
2. `admitExchangeArtifact` or
   `doc-based-coding scheduler admit-exchange-artifact`
3. `doc-based-coding scheduler tick --max-runs 1`
4. `doc-based-coding scheduler inspect-state`
5. `doc-based-coding scheduler project`

## Current Position

The scheduler now has:

1. Durable task submission.
2. Exact-version stored-artifact admission through CLI and MCP.
3. Admission ledger and admission-state projection.
4. One bounded scheduler tick with fake-runtime guard.
5. Explicit projection refresh after tick.
6. Host-owned runner seams for future injected runtime work.

This is not yet a daemon. It is a daemon-ready tick/readback contract.

## Candidate A - Durable Daemon Loop Policy

### Shape

Define the first real repeated-tick daemon policy without adding real-provider
execution.

Minimum expected behavior:

1. Define daemon run request/result objects around repeated
   `run_scheduler_daemon_tick()` calls.
2. Add stop policy:
   - max ticks;
   - no ready tasks;
   - blocked tasks;
   - max runtime failures;
   - explicit cancellation placeholder.
3. Return aggregate queue/readback clues across ticks.
4. Keep fake runtime only for CLI/MCP surfaces.
5. Keep automatic projection refresh optional or separate.

### Pros

1. Moves from daemon-ready tick to actual bounded daemon loop.
2. Exercises recovery and repeated event-log replay.
3. Gives future multi-agent orchestration a durable control loop contract.

### Risks

1. Needs crisp stop-policy naming.
2. Can grow into retry/cancellation/runtime-provider policy if not scoped.

### Fit

High, if the next goal is backend scheduler progress.

## Candidate B - Host Evidence Binding For Scheduler Tick

### Shape

Create evidence JSON or presentation support for tick results, similar to
host-run evidence surfaces.

### Pros

1. Makes scheduler progress easier to inspect.
2. UI can consume evidence without binding directly to raw tick internals.

### Risks

1. Evidence schema can distract from daemon loop semantics.
2. UI work should remain separate and requires screenshot validation.

### Fit

Medium. Useful after or alongside daemon-loop policy, but not the core backend
loop.

## Candidate C - Host-Injected Runtime Tick

### Shape

Expose a host-owned path that calls `run_scheduler_daemon_tick()` with an
injected runtime registry, including mock-Qoder validation.

### Pros

1. Connects daemon tick to the host runtime layer.
2. Reuses current host authorization seams.

### Risks

1. Can blur fake-only CLI/MCP policy.
2. Live provider readiness is still environment-dependent.

### Fit

Medium. Keep separate from daemon-loop control policy.

## Candidate D - UI Binding

### Shape

Bind queue summary, tick results, scheduler state, and projection refresh into
the host UI.

### Pros

1. Gives operators a clearer progress view.
2. Existing read models are becoming UI-ready.

### Risks

1. Requires screenshot validation.
2. Current worktree has unrelated UI dirt; avoid mixing with backend loop work.

### Fit

Useful later, separate gate.

## Recommendation

Choose Candidate A:

> Durable Daemon Loop Policy

Reasoning:

1. The current slice deliberately stopped at one tick.
2. The next backend bottleneck is repeated bounded advancement with durable
   stop policy and recovery semantics.
3. This can stay fake-runtime-only and avoid provider/UI scope creep.

## Proposed Next Planning Gate

```text
2026-06-19-scheduler-durable-daemon-loop-policy.md
```

Recommended acceptance:

1. Define daemon loop request/result and stop policy before implementation.
2. Reuse `run_scheduler_daemon_tick()` internally.
3. Cover max-tick, no-ready, blocked, and failure stop reasons.
4. Keep CLI/MCP fake-runtime-only.
5. Do not add real provider execution, UI binding, exchange artifact mutation,
   or automatic Local Work Trajectory mutation.

## Deferred Candidates

1. Host Evidence Binding For Scheduler Tick.
2. Host-Injected Runtime Tick.
3. UI Binding.
4. Retry/cancellation policy beyond placeholders.
