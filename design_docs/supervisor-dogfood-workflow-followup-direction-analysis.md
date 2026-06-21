# Supervisor Dogfood Workflow Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-supervisor-dogfood-workflow.md`
closed with a deterministic fake-runtime workflow that proves:

```text
seed fixture -> exact admission -> lifecycle start -> supervisor step -> final readback
```

Review evidence:

- `review/supervisor-dogfood-workflow-2026-06-21.md`

## Current Position

The backend scheduler/orchestration line now has:

1. explicit task fixture seeding;
2. exact ExchangeArtifact admission;
3. lifecycle control start/readback;
4. policy-controlled bounded harness;
5. host-managed supervisor contract;
6. CLI/MCP supervisor step surface;
7. CLI/MCP supervisor dogfood workflow surface.

The supervisor result now carries stable host/session/run identity and the
workflow proves those identities through a complete fake-runtime sequence.

## Candidate A - Agent Home / Context Session Binding Over Supervisor Runs

### Goal

Bind agent home, temporary scratch, and context-session lifecycle records to
supervisor run identity and harness attempts.

### Why Useful

The user-level multi-agent direction needs each working agent to have
auditable private/persistent home and temporary scratch surfaces. The
supervisor workflow now provides the run identity needed to attach those
records without inventing a separate ownership source.

### Boundary

Start with product contracts and deterministic fake-runtime binding. Do not
start real providers, do not add Host UX, and do not make cleanup implicit.

## Candidate B - Host UX Readback For Supervisor Workflow

### Goal

Expose supervisor dogfood workflow status/result readback in Host UX.

### Why Useful

Operator visibility will matter for daemon management, but adding UI before
storage/session binding risks presenting a workflow that still lacks the
agent-owned storage lifecycle needed by the next orchestration layer.

### Boundary

No new runtime semantics; UI must consume existing result/readback shapes only.

## Candidate C - Supervisor Workflow Evidence Product

### Goal

Write a durable evidence artifact for supervisor dogfood workflow runs.

### Why Useful

Durable evidence would help Host UX and later audit/replay, but it is less
urgent than deciding the storage/session product shape that supervisor runs
should own.

### Boundary

Evidence write must be explicit and separate from Local Work Trajectory.

## Recommendation

My current preference is Candidate A:

```text
Agent Home / Context Session Binding Over Supervisor Runs
```

Reason:

1. the supervisor workflow now proves the run identity sequence;
2. the next multi-agent risk is storage/context ownership, not UI visibility;
3. durable evidence and Host UX can consume the same binding result later;
4. starting with fake-runtime deterministic contracts preserves the current
   safety boundary.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-21-supervisor-agent-home-session-binding.md`

Suggested first slice:

1. define the minimal binding product between supervisor run identity and agent
   home/context session;
2. expose deterministic helper functions for fake-runtime supervisor workflow
   runs;
3. record readback facts without creating hidden cleanup or retention policy;
4. add focused tests over identity mapping, authority split, and non-goals;
5. preserve no Host UX, no live provider, no implicit cleanup, and no Local
   Work Trajectory mutation from scheduler/runtime code.
