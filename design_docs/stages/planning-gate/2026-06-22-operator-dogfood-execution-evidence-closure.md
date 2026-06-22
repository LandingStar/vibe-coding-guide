# Planning Gate - Operator Dogfood Execution Evidence Closure

> Date: 2026-06-22
> Status: PROPOSED

## Trigger

`design_docs/host-ux-consumed-exchange-artifact-operator-flow-followup-direction-analysis.md`
recommends closing the gap between existing Scheduler Operator primitives and a
single reviewable operator-owned dogfood execution product.

Recent completed inputs:

1. deterministic scheduler operator fixtures, including `binding-consumer`;
2. binding-ref inspection and ledger binding summary;
3. ExchangeArtifact consumed lifecycle mutation;
4. Scheduler Operator Host UX lifecycle affordances;
5. bounded fake scheduler loop evidence and Host Evidence readback.

## Problem

The platform currently has strong individual primitives:

```text
seed -> inspect -> admit -> runLoop -> project -> read evidence
```

However, no single product proves that a scheduler operator candidate can move
through the whole bounded fake-runtime execution closure and return compact
facts that are ready for review, later Host UX one-click controls, and later
live-runtime dogfood.

Without this closure, follow-up work risks jumping prematurely either into UI
convenience or live provider execution before the operator evidence contract is
stable.

## Scope

### Slice 1 - Closure Contract

Define a compact request/result over the existing
`SchedulerOperatorWorkflowRequest`.

The result must preserve:

1. source fixture/artifact id/version;
2. admission status and ledger clue;
3. binding readiness/summary clue when applicable;
4. consumed lifecycle state after optional consume;
5. loop evidence id/path and stop reason;
6. scheduler projection path and counts;
7. Host Evidence presentation status/card count;
8. authority split, including no Local Work Trajectory mutation.

### Slice 2 - Deterministic Backend/CLI Product

Implement a deterministic fake-runtime closure that starts from a fixture seed
and calls the shared operator workflow with explicit flags.

The default first fixture should be `binding-consumer` because it exercises
binding refs and ledger summaries. A simple fixture may remain available as a
lower-friction option.

### Slice 3 - Validation

Add focused runtime and CLI tests proving:

1. fixture seed is deterministic;
2. exact admission succeeds;
3. binding inspection is run when requested;
4. bounded fake loop writes evidence;
5. projection refresh writes scheduler trajectory output;
6. optional `markConsumedOnSuccess` marks the exact artifact version consumed;
7. Host Evidence presentation can read the written evidence;
8. authority split remains explicit and no Local Work Trajectory is mutated.

## Non-Goals

This gate does not:

1. run live Qoder or any real provider;
2. add a Host UX one-click closure control;
3. start OS services, timers, watchers, or background daemons;
4. create agent home directories or scratch directories;
5. execute sandbox cleanup;
6. mutate agent-owned Local Work Trajectory from runtime/CLI/MCP code;
7. replace `scheduler operator-workflow`;
8. define a general agent-cluster scheduler.

## Open Design Points

1. Whether this closure should be a thin wrapper around
   `run_scheduler_operator_workflow()` or an added mode on that workflow.
2. Whether the first slice should expose MCP immediately or wait until the CLI
   product boundary stabilizes.
3. Whether closure evidence should stay as scheduler loop evidence plus compact
   closure summary, or introduce a separate evidence product in a later gate.

## Initial Recommendation

Start with a thin wrapper product rather than adding a mode to
`scheduler operator-workflow`.

Reason:

1. existing operator workflow is already a shared primitive used by Host UX;
2. fixture seeding is a dogfood concern and should not be folded into every
   operator workflow invocation;
3. a wrapper can keep the closure deterministic and test-friendly while
   preserving the lower-level workflow as the stable host-neutral building
   block.

## Acceptance Criteria

The gate may close when:

1. a named closure request/result contract exists;
2. runtime helper can execute a full fake-runtime closure from deterministic
   fixture seed through Host Evidence readback;
3. CLI surface can run the closure with explicit project/path inputs;
4. focused runtime and CLI tests pass;
5. adjacent scheduler operator workflow tests still pass;
6. review evidence records command output and authority split;
7. follow-up direction identifies whether to expose the closure in MCP, Host UX,
   or live Qoder dogfood next.
