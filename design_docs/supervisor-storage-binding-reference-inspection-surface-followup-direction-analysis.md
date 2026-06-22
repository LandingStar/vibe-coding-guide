# Supervisor Storage Binding Reference Inspection Surface Follow-Up Direction Analysis

> Date: 2026-06-22
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-supervisor-storage-binding-reference-inspection-surface.md`
closed with a read-only runtime/CLI/MCP inspection surface for supervisor
storage binding refs in stored scheduler submissions.

Review evidence:

- `review/supervisor-storage-binding-reference-inspection-surface-2026-06-22.md`

## Current Position

The backend scheduler/orchestration line now has:

1. durable supervisor storage binding evidence;
2. compact supervisor storage binding `ExchangeArtifact` projection;
3. exact-version binding artifact reference validation;
4. opt-in fail-closed admission preflight;
5. read-only CLI/MCP inspection for binding refs before admission.

The inspection product is now available to Codex/MCP and CLI operators, but it
is not yet part of higher-level operator workflows or durable admission
readback summaries.

## Candidate A - Operator Workflow Binding Ref Inspection Step

### Goal

Thread the read-only binding-ref inspection product into the existing shared
operator workflow before exact admission.

### Why Useful

`schedulerOperatorWorkflow` is already the main contract for candidate
inspection, optional admission, bounded loop execution, projection refresh, and
Host Evidence readback. Adding an optional/read-only binding-ref inspection
step would let callers see binding readiness in the same workflow payload before
requesting mutation.

### Boundary

Inspection must remain read-only. Admission remains an explicit `admit=true`
step. Do not auto-admit, do not mark artifacts consumed, and do not run
providers.

## Candidate B - Admission Ledger Binding Ref Summary

### Goal

Record compact binding-reference validation counts/errors in admission ledger
records when admission preflight is explicitly enabled.

### Why Useful

After an admission decision, operators would be able to inspect why a binding
preflight passed or failed without rerunning the exact inspection.

### Boundary

Do not store raw evidence JSON or raw binding payloads. Do not change scheduler
execution semantics.

## Candidate C - Host UX Binding Reference Visibility

### Goal

Display binding artifact refs and validation status in the Scheduler Operator
Host UX.

### Why Useful

Operators eventually need to see whether a scheduler task consumes supervisor
storage binding artifacts before admission.

### Boundary

Host UX should consume the backend inspection product; it should not reimplement
binding-ref validation. This requires screenshot validation and should remain a
separate UI slice.

## Recommendation

My current preference is Candidate A:

```text
Operator Workflow Binding Ref Inspection Step
```

Reason:

1. `schedulerOperatorWorkflow` is already the safest high-level operator entry;
2. binding-ref inspection should be visible before explicit admission;
3. the inspection helper is stable and read-only;
4. Host UX can later bind to the shared workflow product instead of calling a
   second bespoke validator.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-22-operator-workflow-binding-reference-inspection-step.md`

Suggested first slice:

1. add an optional binding-ref inspection step to `schedulerOperatorWorkflow`;
2. expose the inspection result in CLI/MCP workflow payloads;
3. keep admission opt-in and separate from inspection;
4. add focused runtime/CLI/MCP tests for inspect-only, inspect+admit success,
   and inspect failure before admission;
5. do not add Host UX, scheduler runtime execution changes, consumed marking,
   raw evidence JSON reads, or Local Work Trajectory mutation.
