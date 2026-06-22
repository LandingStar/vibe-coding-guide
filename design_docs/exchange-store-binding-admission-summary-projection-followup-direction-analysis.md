# Exchange Store Binding Admission Summary Projection Follow-Up Direction Analysis

> Date: 2026-06-22
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-22-exchange-store-binding-admission-summary-projection.md`
closed with compact binding readiness and latest binding-aware admission
summary projected into the ExchangeArtifact store bundle.

Review evidence:

- `review/exchange-store-binding-admission-summary-projection-2026-06-22.md`

## Current Position

The backend readback path is now:

```text
seed binding-consumer fixture
-> exchange store bundle shows binding_reference_readiness
-> schedulerOperatorWorkflow(inspectBindingRefs=true, admit=true)
-> exchange store bundle shows latest_binding_reference_summary
```

This gives operators and Host UX one compact read model for candidate
readiness plus latest binding-aware admission result.

## Candidate A - Host UX Binding Reference Visibility

### Goal

Render `binding_reference_readiness` and
`latest_binding_reference_summary` in Scheduler Operator Host UX.

### Why Useful

The backend now exposes a stable compact product. Host UX can show readiness
and latest admission result without reimplementing validation or directly
reading admission ledger records.

### Boundary

Requires screenshot validation. Use `binding-consumer` fixture as deterministic
input. Do not add new runtime semantics.

## Candidate B - MCP Seed Surface For Dogfood Fixtures

### Goal

Add a dedicated MCP seed tool for deterministic scheduler dogfood fixtures,
including `binding-consumer`.

### Why Useful

MCP-only hosts could create fixture inputs without CLI shell execution.

### Boundary

This expands mutable MCP surface. It should wait until there is concrete
MCP-only dogfood friction.

## Candidate C - ExchangeArtifact Consumption Lifecycle

### Goal

Introduce an explicit consumed/used state for ExchangeArtifact versions after
admission or scheduler execution.

### Why Useful

Operators may eventually need to distinguish candidate, admitted, consumed,
and superseded states.

### Boundary

This is broader lifecycle semantics and should not be mixed into Host UX
readback.

## Recommendation

My current preference is Candidate A:

```text
Host UX Binding Reference Visibility
```

Reason:

1. the backend product is now intentionally UI-consumable;
2. the deterministic fixture gives screenshot validation a stable input;
3. adding an MCP seed tool or artifact lifecycle mutation is less urgent than
   making the current operator surface readable.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-22-host-ux-binding-reference-visibility.md`

Suggested first slice:

1. seed `binding-consumer` fixture in a Host UX test workspace;
2. render binding readiness on ExchangeArtifact candidates;
3. after operator workflow admission, render latest binding summary;
4. verify with screenshot-style tooling per project UI rule;
5. keep new MCP seed tools and ExchangeArtifact lifecycle mutation as non-goals.
