# Host UX Operator Dogfood Closure Control Follow-Up Direction Analysis

> Date: 2026-06-22
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-22-host-ux-operator-dogfood-closure-control.md`
closed with the shared deterministic closure product available through Host UX.

Review evidence:

- `review/host-ux-operator-dogfood-closure-control-2026-06-22.md`

## Current Position

The operator closure is now reachable through all intended fake-runtime
surfaces:

```text
runtime: run_scheduler_operator_dogfood_closure()
CLI:     doc-based-coding scheduler operator-dogfood-closure
MCP:     schedulerOperatorDogfoodClosure
Host UX: Run dogfood closure
```

The completed UI slice did not extend backend authority. It only invokes the
shared CLI product and displays compact readback.

## Candidate A - Live Qoder Runtime Provider Dogfood

### Goal

Run one controlled scheduler task through a real Qoder-backed runtime provider
under explicit host permission and isolation policy.

### Why Useful

The deterministic fake-runtime closure is now fully productized. The remaining
backend risk is live runtime execution: host authorization, runtime provider
adapter behavior, evidence readback, failure isolation, and authority split.

### Boundary

This needs a separate live-runtime gate. Do not retrofit the fake-only closure
control to execute live providers directly.

## Candidate B - Host UX Closure Result Polish

### Goal

Polish compact presentation only if repeated dogfood shows ambiguity in
closure summary, evidence links, or projection readback.

### Why Useful

The current summary is functional and screenshot-validated. Further UI polish
should be driven by operator feedback, not speculation.

## Candidate C - Release Packaging Refresh

### Goal

Package a new preview build after the Host UX closure control if distribution
is the immediate goal.

### Why Useful

The closure is now visible from the extension UI, so a release may be useful
for manual dogfood outside the development host.

## Recommendation

My current preference is Candidate A:

```text
Live Qoder Runtime Provider Dogfood
```

Reason:

1. fake-runtime runtime/CLI/MCP/Host UX surfaces are now aligned;
2. additional UI work has lower risk-reduction value without new dogfood
   findings;
3. live runtime execution is the next unproven authority and isolation surface;
4. it should remain a separate gate with explicit provider/runtime boundaries.

## Proposed Next Planning Gate

```text
design_docs/stages/planning-gate/2026-06-22-live-qoder-runtime-provider-dogfood.md
```
