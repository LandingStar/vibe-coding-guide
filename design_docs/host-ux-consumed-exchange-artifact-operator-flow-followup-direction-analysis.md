# Host UX Consumed ExchangeArtifact Operator Flow Follow-Up Direction Analysis

> Date: 2026-06-22
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-22-host-ux-consumed-exchange-artifact-operator-flow.md`
closed with Scheduler Operator Host UX rendering `ExchangeArtifact`
`lifecycle_state`, preserving consumed candidates as disabled historical
records, and routing explicit `Admit + Consume` through the shared operator
workflow.

Review evidence:

- `review/host-ux-consumed-exchange-artifact-operator-flow-2026-06-22.md`

## Current Position

The scheduler/operator line now has the following usable chain:

```text
seed deterministic scheduler candidate
-> inspect ExchangeArtifact candidate bundle
-> inspect supervisor storage binding refs when needed
-> admit exact version with ledger-backed readback
-> optionally mark exact version consumed after successful admission
-> run bounded fake scheduler loop
-> optionally refresh scheduler-derived trajectory projection
-> read Host Evidence presentation
-> show candidate lifecycle / binding / admission facts in Host UX
```

The Host UX lifecycle work closed the immediate operator affordance gap: an
operator can now distinguish regular admission from admission that consumes the
exact artifact version.

The remaining gap is not another card-level UI state. It is the lack of one
reviewable dogfood execution product that proves the operator flow can take a
candidate through bounded execution and come back with evidence, projection,
and lifecycle readback in one contract.

## Candidate A - Operator Dogfood Execution Evidence Closure

### Goal

Define and implement a narrow deterministic operator dogfood closure over the
existing shared scheduler operator workflow:

```text
seed fixture
-> admit exact candidate
-> run bounded fake loop
-> refresh scheduler projection
-> mark consumed only when admission succeeds and explicitly requested
-> read Host Evidence presentation
-> return compact closure summary
```

### Why Useful

This is the smallest next slice that proves the current products work together
as an operator-owned execution loop rather than isolated primitives.

It would connect recent completed work without jumping to live providers:

1. `binding-consumer` fixture and binding readiness;
2. ledger-backed exact admission and binding summary;
3. consumed lifecycle mutation;
4. bounded fake scheduler loop evidence;
5. scheduler-derived trajectory projection;
6. Host Evidence readback.

### Boundary

Keep it deterministic, fake-runtime-only, explicit, and bounded.

Do not add live Qoder/real provider execution. Do not create agent home or
scratch directories. Do not run cleanup. Do not mutate agent-owned Local Work
Trajectory. Do not add new Host UX controls in the first slice.

## Candidate B - Host UX Operator Dogfood Closure Control

### Goal

Add a Host UX control that performs the complete operator dogfood closure from
one candidate card.

### Why Useful

This would make the workflow convenient for manual dogfood. However, the
backend closure contract should be stable first. Otherwise the UI would encode
workflow sequencing that may still change.

### Boundary

Presentation and invocation only. It must consume the same backend closure
product and must be screenshot-validated.

## Candidate C - Live Qoder Runtime Provider Dogfood

### Goal

Run one controlled scheduler task through a real Qoder-backed runtime provider.

### Why Useful

This is directionally important for the orchestration layer, but it should not
be the immediate next slice. The current fake-runtime operator closure still
needs a reviewable product boundary before a credentialed provider is involved.

### Boundary

Requires explicit credential/runtime readiness checks, isolation policy, and
failure evidence. It should be its own planning gate.

## Recommendation

My current preference is Candidate A:

```text
Operator Dogfood Execution Evidence Closure
```

Reason:

1. Host UX now has enough lifecycle affordance to drive the operator flow;
2. backend primitives already exist, but no single product proves the full
   closure;
3. a deterministic fake-runtime closure gives a stable target for later Host UX
   one-click controls;
4. it keeps the next slice contract-first and avoids prematurely involving live
   Qoder or broader agent cluster scheduling.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-22-operator-dogfood-execution-evidence-closure.md`

Suggested first slice:

1. define a compact closure request/result over the existing
   `SchedulerOperatorWorkflowRequest`;
2. seed one deterministic fixture, preferably starting with `binding-consumer`
   because it exercises binding refs and ledger summaries;
3. call shared operator workflow with explicit `inspectBindingRefs`, `admit`,
   `runLoop`, `refreshProjection`, and optional
   `markConsumedOnSuccess`;
4. return compact closure facts:
   - artifact id/version/lifecycle;
   - admission ledger status;
   - binding summary status;
   - loop evidence id/path;
   - projection path and event/lane/relation counts;
   - Host Evidence card count/status;
   - authority split;
5. add runtime and CLI tests first; add MCP only if the CLI product boundary is
   stable in the same slice;
6. preserve fake-runtime-only, no live provider, no Host UX, no cleanup, no
   agent home/scratch directory creation, and no Local Work Trajectory mutation
   from runtime/CLI/MCP code.

## Notes On Recovery Surfaces

`design_docs/Project Master Checklist.md` and
`design_docs/Global Phase Map and Current Position.md` are newer than
`.codex/checkpoints/latest.md` for this direction. The checkpoint still points
to an earlier supervisor storage binding boundary and should be treated as a
recovery artifact, not the active direction source for this decision.
