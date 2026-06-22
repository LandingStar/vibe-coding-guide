# Supervisor Storage Binding Consumer Fixture Follow-Up Direction Analysis

> Date: 2026-06-22
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-22-supervisor-storage-binding-consumer-fixture.md`
closed with a deterministic `binding-consumer` dogfood fixture.

Review evidence:

- `review/supervisor-storage-binding-consumer-fixture-2026-06-22.md`

## Current Position

The backend now has a repeatable dogfood path:

```text
seed binding-consumer fixture
-> schedulerOperatorWorkflow(inspectBindingRefs=true, admit=true)
-> inspect-admissions binding_reference_summary readback
```

This path verifies exact-version binding artifact consumption without
hand-building fixture payloads and without writing raw supervisor storage
binding evidence JSON.

## Candidate A - Admission Summary Projection Into Exchange Store Bundle

### Goal

Expose latest compact binding readiness/admission summary in the existing
ExchangeArtifact store inspection bundle.

### Why Useful

Operators and Host UX could see candidate readiness and last admission binding
summary from one readback surface before opening the admission ledger directly.

### Boundary

Do not duplicate raw ledger records or raw binding payloads. Keep projection
compact and derived from existing store + ledger products.

## Candidate B - Host UX Binding Reference Visibility

### Goal

Render `binding_reference_inspection` and `binding_reference_summary` in the
Scheduler Operator Host UX.

### Why Useful

The backend path is now stable enough for UI binding. The new fixture gives UI
tests a deterministic input.

### Boundary

Requires screenshot validation. Host UX should consume backend products, not
reimplement binding validation.

## Candidate C - MCP Seed Surface For Dogfood Fixtures

### Goal

Add a dedicated MCP seed tool for deterministic scheduler dogfood fixtures,
including `binding-consumer`.

### Why Useful

MCP-only hosts could create fixtures without shelling out to CLI.

### Boundary

This is lower priority while CLI seed and MCP operator workflow are both
available. Adding a seed tool expands the mutable MCP surface and needs clear
authority wording.

## Recommendation

My current preference is Candidate A:

```text
Admission Summary Projection Into Exchange Store Bundle
```

Reason:

1. it improves readback ergonomics without entering UI scope;
2. it gives Host UX a cleaner backend product to consume later;
3. it stays contract-first and avoids adding another MCP mutation tool before
   the readback model is settled.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-22-exchange-store-binding-admission-summary-projection.md`

Suggested first slice:

1. derive latest compact binding summary per admission candidate from the
   admission ledger during `inspect_exchange_artifact_store()`;
2. include only compact readiness/admission clues, not raw ledger arrays or raw
   binding payloads;
3. add runtime/CLI/MCP resource tests using the `binding-consumer` fixture;
4. keep Host UX and new MCP seed tools as non-goals.
