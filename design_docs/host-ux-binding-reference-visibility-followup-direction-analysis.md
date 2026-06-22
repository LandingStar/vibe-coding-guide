# Host UX Binding Reference Visibility Follow-Up Direction Analysis

> Date: 2026-06-22
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-22-host-ux-binding-reference-visibility.md`
closed with Scheduler Operator Host UX rendering compact binding readiness and
latest binding-aware admission summaries.

Review evidence:

- `review/host-ux-binding-reference-visibility-2026-06-22.md`

## Current Position

The operator readback chain is now visible end to end:

```text
seed binding-consumer fixture
-> ExchangeArtifact bundle projects binding readiness
-> Host UX candidate card shows readiness
-> Host UX Admit sends inspectBindingRefs=true
-> shared operator workflow records binding summary
-> ExchangeArtifact bundle projects latest binding admission summary
-> Host UX candidate card shows latest binding admission summary
```

This completes the immediate UI binding for the supervisor storage binding
artifact consumption path.

## Candidate A - ExchangeArtifact Consumption Lifecycle

### Goal

Introduce an explicit consumed/used state for exact ExchangeArtifact versions
after admission or execution.

### Why Useful

The operator can now see candidate readiness and latest admission result, but
the artifact lifecycle still does not distinguish "available for admission",
"admitted", and "consumed by scheduler execution". A lifecycle state would make
repeated operator decisions clearer.

### Boundary

This is runtime lifecycle semantics. It should not be mixed with UI rendering.
It must define exact mutation authority, duplicate-admission behavior, and
readback projection before code changes.

## Candidate B - MCP Seed Surface For Dogfood Fixtures

### Goal

Add a dedicated MCP seed tool for deterministic scheduler dogfood fixtures,
including `binding-consumer`.

### Why Useful

MCP-only hosts could create fixture inputs without shell execution.

### Boundary

This expands mutable MCP surface. It should wait for concrete MCP-only dogfood
friction because CLI seed already exists and Host UX can consume the resulting
readback.

## Candidate C - Host UX Operator Flow Polish

### Goal

Improve the Scheduler Operator card flow around repeated admissions, disabled
states, and post-admission refresh hints.

### Why Useful

The current binding readback is visible, but richer lifecycle semantics would
make polishing more meaningful. Without lifecycle, UI can only infer from
admission status and latest summary.

### Boundary

Keep this behind Candidate A unless the user reports immediate Host UX friction.

## Recommendation

My current preference is Candidate A:

```text
ExchangeArtifact Consumption Lifecycle
```

Reason:

1. UI readback is now sufficient for dogfood;
2. the next missing operator concept is lifecycle state, not another display
   card;
3. lifecycle should be contract-first before adding more Host UX affordances.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-22-exchange-artifact-consumption-lifecycle.md`

Suggested first slice:

1. define exact lifecycle states and mutation authority for stored
   ExchangeArtifact versions;
2. decide whether admission, scheduler run completion, or explicit operator
   action marks a version consumed;
3. add readback projection only after the contract is explicit;
4. keep Host UX changes and MCP seed tools as non-goals for the first lifecycle
   slice.
