# Controlled Host Runtime Dogfood Harness Follow-up Direction Analysis

## Completed Boundary

`design_docs/stages/planning-gate/2026-06-17-controlled-host-runtime-dogfood-harness.md`
has reached `READY-FOR-CLOSE-REVIEW`.

The current boundary now proves:

1. A host-run evidence JSON product exists:
   `HostSchedulerRunEvidence`.
2. The evidence writer persists compact review artifacts under a caller-provided
   path or the default `.codex/scheduler/evidence/<evidence-id>.json`.
3. `run_host_runtime_dogfood_harness()` can run fake-runtime dogfood through
   the host-authorized scheduler runner, refresh scheduler projection, and
   write evidence.
4. The same harness can run mock-Qoder through explicit host invocation,
   explicit permission grant, and an injected `QoderQueryClient`.
5. MCP scheduler execution remains fake-only.
6. Scheduler projection remains read-only and separate from agent-owned Local
   Work Trajectory.

Evidence review:

- `review/controlled-host-runtime-dogfood-harness-2026-06-17.md`

## Candidate A — Controlled Real Qoder Wrapper Spike

Do what:

1. Implement the smallest real Qoder SDK wrapper behind the existing
   `QoderQueryClient` protocol.
2. Keep wrapper construction host-owned and outside MCP.
3. Run one bounded scheduled task through the dogfood harness.
4. Persist evidence JSON and scheduler projection.
5. Surface transcript references / runtime metadata without making raw
   transcript scheduler authority.

Why not immediately without another gate:

The wrapper touches external SDK behavior, credentials, host permission, and
possibly process/network policy. It needs explicit gate scope and a rollback
plan.

## Candidate B — Host Evidence Consumer / UX Surface

Do what:

1. Add a read-only consumer for host-run evidence JSON.
2. Surface evidence path, host invocation, providers, stop reason, output refs,
   and authority split in the Progress Graph preview or another host panel.
3. Keep evidence consumption display-only.

Why not first:

Evidence JSON exists, but there is not yet enough real dogfood volume to justify
UI investment. A display surface is useful after at least fake + real/mock
runtime evidence examples accumulate.

## Candidate C — Scheduler Daemon Preparation

Do what:

1. Define daemon loop boundaries over the existing one-shot runner.
2. Decide queue polling, cancellation, timeout, retry, and event-log rotation
   contracts.
3. Keep execution serial / bounded until real sandbox behavior is fixed.

Why not first:

The dogfood harness proves one-shot execution. Daemon behavior would multiply
lifecycle cases before real runtime and sandbox assumptions are tested.

## Candidate D — Real Sandbox Provider Contract Expansion

Do what:

1. Select one real isolation candidate such as git-worktree, Docker, or remote
   VM.
2. Bind sandbox allocation to edit leases and scratch paths.
3. Validate cleanup and artifact recovery behavior.

Why not first:

The harness still uses shared-process metadata. Real sandboxing matters before
large-scale agents, but it should follow a sharper decision on which runtime
will be dogfooded first.

## Current Recommendation

Do not jump directly into daemon or UI.

Recommended next gate:

```text
Controlled Real Qoder Wrapper Spike
```

The first slice should remain narrow:

1. Real SDK wrapper behind `QoderQueryClient`.
2. Host-owned construction and permission grant.
3. One deterministic scheduled task through
   `run_host_runtime_dogfood_harness()`.
4. Evidence JSON inspection.
5. No MCP real-provider exposure.
6. No daemon, parallel execution, real sandbox, or UI redesign.

This keeps the project moving toward real runtime validation while preserving
the scheduler authority split proven by the dogfood harness.
