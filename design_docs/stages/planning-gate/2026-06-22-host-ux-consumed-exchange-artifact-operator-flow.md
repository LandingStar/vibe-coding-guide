# Planning Gate - Host UX Consumed ExchangeArtifact Operator Flow

> Date: 2026-06-22
> Status: COMPLETED

## Trigger

`review/exchange-artifact-consumption-lifecycle-2026-06-22.md` closed the first
runtime lifecycle slice with an explicit exact-version consumption mutation and
an opt-in ledger-backed admission flag.

Host UX currently renders admission candidates but does not expose consumed
state or the new opt-in operator action.

## Problem

Operators need two distinct facts visible at the candidate card:

1. the exact stored artifact version has already been consumed;
2. the current admission action can intentionally consume the exact version
   after successful admission.

Without this, the runtime now has a durable consumed fact, but the operator
surface still behaves as if admission/admitted status is the only lifecycle
signal.

## Product Decision

Consumed candidates should remain visible as historical records.

Default Host UX behavior:

```text
unconsumed candidate -> Admit, Admit + Consume
admitted but unconsumed candidate -> disabled Admitted, no auto-consume
consumed candidate -> disabled Consumed
```

Rationale:

1. hiding consumed candidates would make recent operator actions harder to
   audit;
2. auto-consuming on regular Admit would contradict the runtime contract;
3. a separate `Admit + Consume` button makes the lifecycle mutation explicit.

## Scope

### Slice 1 - Read Model Binding

Thread `summary.lifecycle_state` into each
`SchedulerOperatorExchangeCandidate`.

### Slice 2 - Operator Workflow Routing

Add `markConsumedOnSuccess` to the Scheduler Operator admit action contract and
route it to the shared `scheduler operator-workflow` CLI args.

This requires adding a matching runtime flag to `scheduler operator-workflow`
because Host UX uses that shared workflow rather than direct
`scheduler admit-exchange-artifact`.

### Slice 3 - Candidate Rendering

Render lifecycle state on candidate cards.

For unconsumed candidates, show:

1. regular `Admit`;
2. explicit `Admit + Consume`.

For consumed candidates, show a disabled `Consumed` state and do not expose a
mutating action.

### Slice 4 - Screenshot Validation

Build a deterministic HTML fixture that shows both unconsumed and consumed
candidate states, then validate with a screenshot-style browser artifact.

## Non-Goals

This gate does not:

1. hide or filter consumed candidates;
2. make regular Admit consume by default;
3. add a standalone consume-only Host UX action;
4. mutate input binding artifacts consumed;
5. change scheduler runtime execution semantics;
6. change ExchangeArtifact store schema;
7. add consumed filtering controls.

## Acceptance Criteria

The gate may close when:

1. Host UX candidate read model includes `lifecycleState`;
2. regular Admit does not mark consumed;
3. `Admit + Consume` routes `markConsumedOnSuccess=true` through
   Scheduler Operator contract and CLI workflow;
4. consumed candidates render a visible disabled consumed state;
5. focused extension tests cover rendering and action argument contracts;
6. backend CLI tests cover `scheduler operator-workflow --mark-consumed-on-success`;
7. screenshot validation demonstrates both candidate states.

## Completion

Completed on 2026-06-22.

Outcome:

1. `summary.lifecycle_state` is threaded into
   `SchedulerOperatorExchangeCandidate.lifecycleState`;
2. Scheduler Operator Host UX renders `lifecycle=<state>` on each candidate
   card;
3. unconsumed candidates expose regular `Admit` and explicit
   `Admit + Consume`;
4. regular `Admit` sends `markConsumedOnSuccess=false` and does not consume by
   default;
5. `Admit + Consume` sends `markConsumedOnSuccess=true` through the shared
   Scheduler Operator action contract and CLI workflow;
6. consumed candidates remain visible as historical records and render a
   disabled `Consumed` button;
7. backend CLI/MCP/operator workflow tests, extension contract/rendering tests,
   adjacent regression tests, and screenshot validation passed.

Review evidence:

`review/host-ux-consumed-exchange-artifact-operator-flow-2026-06-22.md`
