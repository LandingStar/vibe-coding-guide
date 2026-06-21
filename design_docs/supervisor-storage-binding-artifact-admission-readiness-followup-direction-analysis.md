# Supervisor Storage Binding Artifact Admission Readiness Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-supervisor-storage-binding-artifact-admission-readiness.md`
closed with exact-version validation for scheduler submissions that reference
projected supervisor storage binding artifacts.

Review evidence:

- `review/supervisor-storage-binding-artifact-admission-readiness-2026-06-21.md`

## Current Position

The backend scheduler/orchestration line now has:

1. durable supervisor storage binding evidence;
2. compact supervisor storage binding `ExchangeArtifact` projection;
3. a stable binding artifact `ExchangeReference` convention;
4. read-only validation against `JsonArtifactVersionStore`;
5. optional exact-version admission preflight before scheduler snapshot
   mutation.

The validator is usable from code, but operators and tool callers do not yet
have a non-mutating inspection surface to see whether a stored scheduler
submission has valid binding artifact references before admission.

## Candidate A - Read-Only Binding Reference Inspection Surface

### Goal

Expose a non-mutating inspection helper, then CLI/MCP surface, that checks
binding artifact references in a stored scheduler submission artifact.

### Why Useful

This lets Codex, operators, and automation verify exact binding inputs before
choosing to admit the scheduler submission.

### Boundary

Read-only inspection only. Do not submit scheduler tasks, write snapshots,
mark artifacts consumed, read raw evidence JSON, or add Host UX controls.

## Candidate B - Admission Ledger Binding Ref Summary

### Goal

Record binding-reference validation counts and errors in admission ledger
payloads when admission preflight is enabled.

### Why Useful

It would make later readback clearer after a successful or failed admission.

### Boundary

Do not change scheduler task execution or artifact consumption state.

## Candidate C - Host UX Binding Reference Visibility

### Goal

Show binding artifact references and validation status in the operator UI.

### Why Useful

Operators eventually need to understand which supervisor storage binding a task
will consume.

### Boundary

Requires screenshot validation and should consume a backend inspection product
instead of reimplementing validation in the UI.

## Recommendation

My current preference is Candidate A:

```text
Read-Only Binding Reference Inspection Surface
```

Reason:

1. the validation helper already exists and is read-only;
2. exact admission should remain an explicit operator action;
3. a read-only inspection product gives Codex and other hosts a safe preflight
   before mutating scheduler state;
4. Host UX should remain downstream of that backend readback contract.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-21-supervisor-storage-binding-reference-inspection-surface.md`

Suggested first slice:

1. define a compact inspection product for a stored scheduler submission
   artifact's supervisor storage binding refs;
2. expose a runtime helper that returns ok/errors/checked refs without
   mutation;
3. add CLI/MCP read-only surfaces only after the runtime helper is stable;
4. add focused tests for valid/missing/wrong-product/ambiguous cases;
5. do not add Host UX, scheduler admission, artifact consumption, evidence JSON
   reads, storage directory creation, cleanup, or Local Work Trajectory
   mutation.
