# Pi Agent Adapter Research Notes

> Date: 2026-06-28
> Status: research notes for later adapter planning

## Purpose

This note preserves the Pi Agent research conclusion so a later Pi adapter
gate can start from a stable position instead of repeating the same comparison.

It is not an active implementation gate. The current implementation focus after
this note is OpenCode runtime provider adapter work.

## Product Positioning

Pi Agent is best treated as a candidate **agent runtime / harness**, not as the
core doc-based-coding scheduler.

The useful surfaces for this project are:

1. CLI one-shot or JSON mode for bounded worker execution;
2. RPC JSONL mode for host-controlled session interaction;
3. SDK-level session/context/control APIs for future continuous lane workers;
4. external sandbox integration points for stronger isolation.

The project should not make Pi Agent the central orchestration authority. The
doc-based-coding scheduler, leader-worker lifecycle, Local Work Trajectory
ownership, exchange artifacts, runtime invocation audit, and sandbox/writeback
policy should remain project-owned.

## Why Pi Is Different From OpenCode

Pi appears more useful when the project wants a controllable agent harness with
longer-lived session behavior.

Compared with a simple CLI worker adapter, Pi's interesting traits are:

1. session and context concepts are closer to the planned "continuous worker on
   one lane" model;
2. RPC mode could support a host-owned adapter that steers a worker across
   multiple related tasks;
3. SDK usage may expose richer control than a plain process wrapper;
4. because the surface is more harness-like, it overlaps more with project
   orchestration design and should be adopted carefully.

OpenCode is a better first adapter target for proving provider extensibility
because it can be added as a narrower CLI/process-backed worker runtime without
pressure to redesign the scheduler.

## Main Risks

### Authority Overlap

Pi has enough agent/session semantics that a careless integration could blur
the boundary between:

1. doc-based-coding scheduler authority;
2. host-owned runtime invocation authority;
3. Pi session/context authority.

The adapter must keep Pi behind `AgentRuntimeAdapter` and project-owned
products. Pi should return compact results, permission/review signals, and
artifact deltas; it should not become the source of truth for task lifecycle or
Local Work Trajectory mutation.

### Isolation

Pi should be assumed to run with the permissions of its host process unless a
separate sandbox is configured. A future adapter must therefore require the same
host-owned sandbox/writeback review boundary used for Codex/OpenCode workers:

1. no silent source workspace mutation;
2. git-worktree or equivalent sandbox opt-in for editing workers;
3. review-only patch artifacts for writeback;
4. compact audit, no raw transcript or secret persistence.

### Premature Continuous Worker Binding

Pi is attractive for continuous lane workers, but that is a later capability.
The first Pi gate should avoid solving all of:

1. worker memory continuity;
2. cross-node lane context reuse;
3. worker reactivation;
4. mailbox/history replay;
5. persistent agent home promotion.

Those concerns need their own contract-first gate.

## Recommended Future Gate

Suggested gate name:

```text
Pi Agent Runtime Provider Adapter Smoke
```

Suggested first scope:

1. add `runtime_provider="pi-agent"` or another stable provider key;
2. implement credential-safe readiness for the selected Pi executable/package;
3. support one bounded worker task through CLI JSON mode or RPC JSONL mode;
4. normalize success, failure, timeout, permission/review, stdout/stderr byte
   counts, and compact metadata into existing runtime products;
5. register Pi only through host-authorized runtime wiring;
6. prove the adapter with mock process/RPC tests and a readiness-negative CLI
   test;
7. keep MCP real-provider execution closed.

Suggested non-goals:

1. no replacement of the scheduler;
2. no persistent Pi session reuse across lane nodes;
3. no daemon/service lifecycle;
4. no raw transcript persistence;
5. no direct Local Work Trajectory mutation by Pi workers;
6. no automatic patch merge.

## Later Pi-Specific Direction

After the first smoke passes, Pi may become the better candidate for:

1. continuous same-lane worker sessions;
2. grouping a small set of strongly-coupled lanes under one worker context;
3. explicit worker reactivation through mailbox/history products;
4. host-owned session compaction;
5. agent home or private folder promotion after workspace-agent audit.

Those should be planned as orchestration features first, then mapped onto Pi.

## Current Recommendation

Do not start with Pi for the next adapter slice. Start with OpenCode to prove
that the provider seam accepts another independent worker runtime. Return to Pi
after OpenCode confirms the adapter shape and after the continuous-lane-worker
contract is better specified.
