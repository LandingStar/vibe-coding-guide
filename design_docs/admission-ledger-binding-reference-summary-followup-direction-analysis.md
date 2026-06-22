# Admission Ledger Binding Reference Summary Follow-Up Direction Analysis

> Date: 2026-06-22
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-22-admission-ledger-binding-reference-summary.md`
closed with compact `binding_reference_summary` support in admission ledger
records and readback payloads.

Review evidence:

- `review/admission-ledger-binding-reference-summary-2026-06-22.md`

## Current Position

The backend scheduler/operator line now has:

1. exact-version supervisor storage binding artifact refs in scheduler
   submissions;
2. standalone CLI/MCP read-only binding-ref inspection;
3. shared operator workflow binding-ref inspection before explicit admission;
4. fail-closed binding-ref-aware admission preflight;
5. durable admission ledger/readback summaries for binding-aware admissions.

This closes the core inspect -> admit -> durable readback path. The remaining
friction is fixture and dogfood ergonomics: tests and manual sessions currently
hand-build binding artifacts and matching scheduler submissions.

## Candidate A - Supervisor Storage Binding Consumer Fixture

### Goal

Add a deterministic dogfood fixture that seeds:

1. one compact supervisor storage binding artifact;
2. one scheduler task submission that references the binding artifact via
   `supervisor_storage_binding_artifact`;
3. optional fixture metadata that points operators at
   `inspectBindingRefs + admit + inspect-admissions`.

### Why Useful

This would make manual and MCP smoke testing easier and reduce repeated
fixture-building code in tests. It also gives Host UX later a stable candidate
for displaying binding readiness and ledger summaries.

### Boundary

Keep it as deterministic ExchangeArtifact seed data. Do not run providers,
create real agent home/scratch directories, approve persistent homes, or mark
artifacts consumed.

## Candidate B - Host UX Binding Reference Visibility

### Goal

Display workflow `binding_reference_inspection` and ledger
`binding_reference_summary` in Scheduler Operator Host UX.

### Why Useful

Operators eventually need to see binding readiness and durable admission
summary without reading JSON.

### Boundary

Host UX must consume backend products and requires screenshot validation. It
should not reimplement validation.

## Candidate C - Admission Ledger Summary Projection Into Exchange Store Bundle

### Goal

Expose the latest compact binding summary in
`inspect_exchange_artifact_store()` admission state projection.

### Why Useful

The ExchangeArtifact bundle could show candidate readiness and latest admission
binding summary together.

### Boundary

Do not duplicate raw ledger records or raw binding payloads into the store
summary.

## Recommendation

My current preference is Candidate A:

```text
Supervisor Storage Binding Consumer Fixture
```

Reason:

1. the backend path is now complete enough to dogfood end-to-end;
2. a deterministic fixture improves CLI/MCP/manual testing with low risk;
3. Host UX work will be better grounded once there is a stable fixture to
   render;
4. it avoids expanding UI scope before the backend smoke path is ergonomic.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-22-supervisor-storage-binding-consumer-fixture.md`

Suggested first slice:

1. extend scheduler dogfood fixture support with a `binding-consumer` fixture;
2. seed a compact binding artifact and one scheduler submission consuming it;
3. expose it through CLI/MCP fixture seed paths if those already route through
   shared fixture helpers;
4. add focused runtime/CLI/MCP tests that run
   `seed -> operator-workflow inspectBindingRefs+admit -> inspect-admissions`;
5. do not run providers, refresh projection by default, create agent home or
   scratch directories, mark consumed, or mutate Local Work Trajectory from
   runtime/CLI/MCP code.
