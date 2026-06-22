# Operator Dogfood Execution Evidence Closure Follow-Up Direction Analysis

> Date: 2026-06-22
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-22-operator-dogfood-execution-evidence-closure.md`
closed with a deterministic fake-runtime closure:

```text
seed binding-consumer fixture
-> inspect binding refs
-> admit exact artifact/version
-> mark consumed on successful admission
-> run bounded fake loop
-> refresh scheduler projection
-> read Host Evidence presentation
-> return compact closure summary
```

Review evidence:

- `review/operator-dogfood-execution-evidence-closure-2026-06-22.md`

## Current Position

The scheduler/operator line now has both lower-level primitives and one
reviewable backend closure product.

The closure remains CLI/runtime only. It deliberately did not add MCP exposure,
Host UX one-click controls, live providers, cleanup, or agent-owned trajectory
mutation.

## Candidate A - MCP Surface For Operator Dogfood Closure

### Goal

Expose the existing closure result through a Codex-oriented MCP tool, likely
`schedulerOperatorDogfoodClosure`.

### Why Useful

Codex is the current primary supported host. MCP exposure would let an agent run
the deterministic closure directly without shelling through CLI, while keeping
the same backend contract and fake-runtime-only boundary.

### Boundary

No new runtime semantics, no Host UX, no live provider, and no Local Work
Trajectory mutation from the tool. The MCP tool should map camelCase request
fields to `SchedulerOperatorDogfoodClosureRequest`.

## Candidate B - Host UX Operator Dogfood Closure Control

### Goal

Add one Host UX control that runs the complete operator closure and presents the
compact closure summary.

### Why Useful

This would make manual dogfood easier now that the backend closure product is
stable. It should consume the closure product rather than re-encoding the
sequence in frontend code.

### Boundary

Presentation and invocation only. Screenshot validation is required because
this changes UI.

## Candidate C - Live Qoder Runtime Provider Dogfood

### Goal

Run one controlled scheduler task through a real Qoder-backed runtime provider.

### Why Useful

This is important for proving the agent runtime path, but it should remain
behind a separate planning gate with credential/runtime readiness checks and
explicit isolation policy.

### Boundary

No credentialed live execution should be introduced through the deterministic
fake-runtime closure gate.

## Recommendation

My current preference is Candidate A:

```text
MCP Surface For Operator Dogfood Closure
```

Reason:

1. Codex is the primary supported host path;
2. the backend closure product is already stable and CLI-tested;
3. MCP exposure is a thinner integration step than Host UX;
4. Host UX can later reuse the same product once the agent-facing surface is
   fixed;
5. live Qoder dogfood should wait until fake-runtime operator closure is
   directly callable from the primary agent surface.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-22-operator-dogfood-closure-mcp-surface.md`

Suggested first slice:

1. add GovernanceTools/MCP method and tool registration;
2. map camelCase request fields to `SchedulerOperatorDogfoodClosureRequest`;
3. return the same closure JSON shape as CLI/runtime;
4. update scheduler MCP prompt and tool surface audit;
5. add focused MCP tests for registration, routing, fake-runtime rejection, and
   binding-consumer success;
6. preserve no Host UX, no live provider, no cleanup, no agent home/scratch
   creation, and no Local Work Trajectory mutation.
