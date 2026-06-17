# Agent Runtime Adapter And Scheduler Follow-up Direction Analysis

## Completed Boundary

`design_docs/stages/planning-gate/2026-06-16-agent-runtime-adapter-and-scheduler-skeleton.md`
has reached `READY-FOR-CLOSE-REVIEW`.

The current skeleton now proves:

1. A project-owned `AgentRuntimeAdapter` contract can select fake and mockable
   Qoder runtimes without moving scheduling authority into an SDK.
2. `SchedulerState` can own task graph state, dependencies, context scope,
   edit leases, sandbox profiles, merge gates, run records, and event history.
3. Fake runtime execution can pass through the adapter boundary and persisted
   one-shot runner.
4. Qoder remains host-authorized and mock-backed only; MCP smoke execution is
   still fake-only.
5. Scheduler-derived Local Work Trajectory is projection-only and separate from
   the agent-owned lifecycle trajectory.

Evidence review:

- `review/agent-runtime-adapter-and-scheduler-skeleton-2026-06-17.md`

The next question is no longer whether the core objects can exist. It is which
thin execution surface should make the scheduler practically dogfoodable while
preserving the ownership boundary.

## Candidate A — Host-Authorized Scheduler Runner Adapter（推荐）

Do what:

1. Add a thin host adapter surface that can construct a
   `RuntimeRegistryWiringResult` and call
   `run_persisted_scheduler_once_with_wiring()`.
2. Keep MCP `schedulerRunOnceAndProject` fake-only.
3. Support two validation modes:
   - fake runtime path for deterministic smoke
   - injected mock Qoder client path for host-authorized registry wiring
4. Return an auditable run summary with snapshot path, event log path, runtime
   providers, host invocation surface, run count, stop reason, permission review
   counts, produced artifact refs, and projection path.
5. Document the prompt / maintenance flow for agents that need to submit,
   project, run once, and inspect scheduler state.

Why first:

1. It directly follows the just-completed host wiring contract.
2. It produces dogfoodable behavior without importing the real Qoder SDK.
3. It keeps real provider execution out of MCP until host permission and UX
   routing are explicit.
4. It gives later daemon / sandbox work a concrete one-shot runner to wrap.

Main risk:

The adapter may accidentally become a second scheduler command layer. Keep it
thin: it should assemble host authorization, call the persisted runner, and
report evidence only.

## Candidate B — Real Qoder SDK Wrapper Slice

Do what:

1. Implement a real `QoderQueryClient` wrapper behind the existing protocol.
2. Map SDK responses into `QoderQueryResult`.
3. Surface permission requests instead of approving them.
4. Keep transcript refs outside scheduler authority.

Why not first:

The current project still benefits from a host-authorized runner shell before a
real SDK client is introduced. Without that shell, real SDK work risks mixing
credential / process / host UX decisions into the scheduler core.

Use after Candidate A has a clear host seam.

## Candidate C — Scheduler Daemon And Queue Runtime

Do what:

1. Add a long-running scheduler loop.
2. Handle periodic recovery, queue drain, cancellation, timeout, retry, and log
   compaction policy.

Why not first:

The one-shot runner has not yet been dogfooded through a host-authorized seam.
Daemon behavior would multiply lifecycle complexity before the execution
surface is stable.

Use after one-shot host execution is observable and repeatable.

## Candidate D — Real Sandbox Provider

Do what:

1. Implement a concrete `git-worktree`, Docker, or remote-VM sandbox provider.
2. Bind edit leases to actual filesystem / process isolation.

Why not first:

`SandboxProfile` and provider contracts are in place, but runtime execution is
still single-shot and fake/mock oriented. Real sandboxing should follow a stable
host execution seam and explicit provider selection policy.

## Current Recommendation

Choose Candidate A as the next planning gate:

```text
Host-Authorized Scheduler Runner Adapter
```

Suggested first slice:

1. Define a host adapter function / CLI-like local entry over
   `run_persisted_scheduler_once_with_wiring()`.
2. Add prompt guidance for fake smoke and mock-Qoder host wiring smoke.
3. Keep MCP fake-only and explicitly test rejection / non-exposure of real
   provider execution through MCP.
4. Project the post-run scheduler state and return compact evidence for UI or
   agent inspection.

Explicit non-goals:

1. Real Qoder SDK import.
2. Scheduler daemon.
3. Real sandbox isolation.
4. Automatic Local Work Trajectory mutation from scheduler state.
5. Runtime subagents becoming project-level lanes.
