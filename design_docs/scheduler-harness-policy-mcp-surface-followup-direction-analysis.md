# Scheduler Harness Policy MCP Surface Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-scheduler-harness-policy-mcp-surface.md`
closed with MCP exposure for the policy-controlled scheduler lifecycle harness.

Review evidence:

- `review/scheduler-harness-policy-mcp-surface-2026-06-21.md`

## Current Position

The backend scheduler/orchestration line now has:

1. scheduler snapshot and event-log persistence;
2. bounded scheduler daemon tick / loop;
3. lifecycle control file plus CLI/MCP lifecycle control;
4. lifecycle-gated run-once through CLI/MCP;
5. bounded host-managed scheduler daemon harness through CLI;
6. deterministic harness policy through runtime/CLI;
7. policy-controlled harness execution through MCP;
8. durable sandbox receipt workflow and cleanup evidence products.

The remaining gap is no longer "can Codex invoke the harness"; it can. The next
question is what product should consume or supervise this capability.

## Candidate A - Host-Managed Daemon Supervisor Contract

### Goal

Define the first contract for a host-owned supervisor around repeated
policy-controlled harness invocations.

### Why Useful

The current harness is bounded and immediate. A supervisor contract can define
status readback, cancellation source, cadence ownership, process/session
identity, and lifecycle event shape before any real background service exists.

### Boundary

Do not install an OS service, add filesystem watching, or run an unbounded
daemon in the first slice.

## Candidate B - Agent Home / Context Session Binding Over Harness Attempts

### Goal

Bind agent home / temporary scratch / context session lifecycle to scheduler
harness attempts.

### Why Useful

Larger agent orchestration will need persistent and temporary storage that has
visible ownership and cleanup semantics. Harness attempts now provide concrete
boundaries for such sessions.

### Boundary

Do not combine storage lifecycle with supervisor process semantics in the
first slice unless a minimal shared contract is necessary.

## Candidate C - Harness Policy Dogfood Workflow

### Goal

Create a deterministic dogfood workflow that uses MCP lifecycle control and
`schedulerLifecycleHarness` to seed, start, run policy-controlled harness, and
read back scheduler state/evidence.

### Why Useful

This would prove the MCP surface in the actual Codex-style workflow without
moving directly into daemon supervision or agent-home storage.

### Boundary

Keep fake runtime, explicit paths, and no Host UX. Do not add projection
refresh unless it is an explicit separate step.

## Recommendation

My current preference is Candidate A:

```text
Host-Managed Daemon Supervisor Contract
```

Reason:

1. MCP exposure has closed the immediate Codex invocation gap;
2. the next missing product is host ownership of repeated policy-controlled
   harness invocations, not another one-shot execution path;
3. supervisor contract work can remain deterministic and bounded while
   preparing later real background process integration;
4. agent-home binding needs lifecycle anchors, and a supervisor contract will
   make those anchors clearer.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-21-host-managed-daemon-supervisor-contract.md`

Suggested first slice:

1. define supervisor request/status/result objects over policy-controlled
   harness invocations;
2. include cancellation/deadline source fields and status readback facts;
3. add deterministic tests with fake runtime and no sleeps/watchers;
4. preserve no OS service, no Host UX, no live provider, no projection refresh,
   no cleanup, and no Local Work Trajectory mutation from scheduler code.
