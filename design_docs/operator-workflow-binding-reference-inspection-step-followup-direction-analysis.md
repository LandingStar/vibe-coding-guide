# Operator Workflow Binding Reference Inspection Step Follow-Up Direction Analysis

> Date: 2026-06-22
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-22-operator-workflow-binding-reference-inspection-step.md`
closed with optional read-only supervisor storage binding reference inspection
inside the shared `schedulerOperatorWorkflow`.

Review evidence:

- `review/operator-workflow-binding-reference-inspection-step-2026-06-22.md`

## Current Position

The backend scheduler/operator line now has:

1. exact-version supervisor storage binding artifact refs in scheduler
   submissions;
2. fail-closed admission preflight support when validation is explicitly
   enabled;
3. standalone CLI/MCP read-only binding-ref inspection;
4. shared operator workflow binding-ref inspection before explicit admission;
5. default-compatible operator workflow behavior when inspection is not enabled.

The remaining gap is durable post-decision readback: after admission succeeds
or fails, the admission ledger can show status and error summary, but it does
not yet carry compact binding-reference validation counts or per-task failure
clues.

## Candidate A - Admission Ledger Binding Ref Summary

### Goal

Record compact binding-reference validation summary fields in admission ledger
records when binding-ref preflight is explicitly enabled.

### Why Useful

Operators can inspect why a binding-ref-aware admission passed or failed
without rerunning the exact workflow inspection. This makes the mutating
admission decision auditable while keeping raw supervisor storage binding
evidence out of the ledger.

### Boundary

Do not store raw evidence JSON or raw binding payloads. Store only compact
counts, task ids, ref ids/versions, and readable validation errors.

## Candidate B - Host UX Binding Reference Visibility

### Goal

Display workflow `binding_reference_inspection` in Scheduler Operator Host UX.

### Why Useful

Operators eventually need to see binding readiness in the UI before clicking
admission actions.

### Boundary

Host UX must consume the backend workflow product and should not reimplement
validation. This requires screenshot validation and should remain a separate UI
slice.

## Candidate C - Supervisor Storage Binding Consumer Fixture

### Goal

Add a deterministic dogfood fixture whose scheduler task consumes a supervisor
storage binding artifact and exercises `inspectBindingRefs + admit`.

### Why Useful

The current tests cover the path, but a named fixture would make manual and MCP
smoke testing easier.

### Boundary

Do not run providers or create real agent home/scratch directories. Keep it as
a deterministic ExchangeArtifact fixture.

## Recommendation

My current preference is Candidate A:

```text
Admission Ledger Binding Ref Summary
```

Reason:

1. the workflow already exposes pre-admission readiness;
2. admission ledger is the durable readback surface for actual admission
   decisions;
3. compact validation metadata improves auditability without adding UI scope;
4. Host UX can later display either workflow inspection or ledger summaries
   from stable backend products.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-22-admission-ledger-binding-reference-summary.md`

Suggested first slice:

1. extend admission ledger records or adjacent readback payload with compact
   binding-ref validation summary when explicit validation is enabled;
2. include summary on both admitted and failed preflight paths;
3. keep raw evidence JSON and raw binding payloads out of the ledger;
4. add focused runtime/CLI/MCP readback tests;
5. do not add Host UX, scheduler execution changes, consumed marking, provider
   execution, or Local Work Trajectory mutation.
