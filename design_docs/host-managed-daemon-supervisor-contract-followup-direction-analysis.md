# Host-Managed Daemon Supervisor Contract Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-host-managed-daemon-supervisor-contract.md`
closed with a runtime-only supervisor contract over the policy-controlled
scheduler daemon harness.

Review evidence:

- `review/host-managed-daemon-supervisor-contract-2026-06-21.md`

## Current Position

The backend scheduler/orchestration line now has:

1. lifecycle control file and lifecycle-gated run-once;
2. bounded host-managed harness;
3. deterministic retry/deadline/cancellation policy over harness attempts;
4. CLI and MCP surfaces for the policy-controlled harness;
5. runtime-only supervisor contract with host/session/run identity,
   cancellation-source metadata, and lifecycle status readback.

The supervisor contract is not yet exposed through CLI or MCP. Codex can invoke
the policy harness directly, but cannot yet invoke the supervisor step that
adds host-owned identity and status readback.

## Candidate A - CLI/MCP Surface For Daemon Supervisor Step

### Goal

Expose `run_scheduler_daemon_supervisor_step()` through explicit CLI and MCP
operator surfaces.

### Why Useful

The runtime contract has value only after Codex/host workflows can call it.
CLI/MCP exposure would let the mainline use the supervisor identity and status
readback layer without introducing Host UX or real background services.

### Boundary

Keep fake-runtime-only, explicit paths, bounded harness controls, no projection
refresh, no cleanup, no live provider, and no Local Work Trajectory mutation
from scheduler code.

## Candidate B - Agent Home / Context Session Binding Over Supervisor Runs

### Goal

Bind agent home, temporary scratch, and context-session lifecycle to supervisor
run identity and harness attempts.

### Why Useful

Larger agent orchestration needs persistent/private agent storage and temporary
scratch ownership. The supervisor run id and status readback now provide a
concrete lifecycle anchor.

### Boundary

Do not combine storage binding with CLI/MCP supervisor exposure unless the
surface is already stable enough to carry the new fields.

## Candidate C - Supervisor Dogfood Workflow

### Goal

Create a deterministic dogfood workflow that uses lifecycle control,
supervisor step execution, and status/evidence readback end to end.

### Why Useful

This would prove the supervisor contract in the actual Codex-style workflow
before Host UX or real provider integration.

### Boundary

Keep fake runtime, explicit paths, no Host UX, and no projection refresh unless
called as a separate explicit workflow step.

## Recommendation

My current preference is Candidate A:

```text
CLI/MCP Surface For Daemon Supervisor Step
```

Reason:

1. the runtime supervisor contract is implemented but not directly invocable by
   Codex or operator tooling;
2. CLI/MCP exposure keeps the next slice bounded and testable;
3. agent-home/session binding needs a stable invocation surface to carry
   supervisor identity consistently;
4. dogfood workflow is more useful after the invocation surface exists.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-21-daemon-supervisor-cli-mcp-surface.md`

Suggested first slice:

1. add CLI command over `run_scheduler_daemon_supervisor_step()`;
2. add MCP tool over the same runtime helper;
3. include supervisor id/session/run/cancellation/status readback fields;
4. preserve fake-runtime-only and explicit path inputs;
5. add focused CLI/MCP tests;
6. do not add Host UX, real provider, projection refresh, cleanup, or Local
   Work Trajectory mutation from scheduler code.
