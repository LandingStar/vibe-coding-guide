# Planning Gate - Write-Back Enforcement Unification

> Date: 2026-06-20
> Status: COMPLETED

## Trigger

`design_docs/edit-lease-conflict-policy-expansion-direction-analysis.md`
recommends using the newly completed scheduler edit lease classifier as the
next coherence point for write-back planning.

The previous slice completed:

- `EditLeaseConflictDecision`
- `classify_edit_lease_conflict()`
- scheduler admission evidence through `AdmissionDecision.edit_lease_conflict`
- `review-zone` overlap routing to `review_required`

## Problem

Write-back planning currently validates payload paths only against
`contract.allowed_artifacts` or child `allowed_artifacts`. That is useful, but
it is not yet aligned with scheduler edit lease policy evidence.

As a result, a task may carry scheduler admission evidence such as
`review_required`, `blocked`, `unsafe_path`, or `denied_artifact_hit`, while
write-back payload planning still reports only generic allowed-artifact results.

This slice should answer:

```text
Can write-back planning consume scheduler edit lease evidence as optional
input and produce planned/skipped/review-routed/blocked payload evidence without
changing write execution or lease lifecycle?
```

## Scope

### Slice 1 - Optional Lease Evidence Input

Extend write-back payload planning to accept optional edit lease evidence in
`execution_result`.

Accepted first shape:

```text
execution_result["edit_lease_conflict"] = {
  "state": "compatible" | "waiting" | "review_required" | "blocked",
  "classification": "...",
  "reason": "...",
  "left_path": "...",
  "right_path": "..."
}
```

The write-back engine should also accept dataclass-like objects if a caller
passes `EditLeaseConflictDecision` directly.

### Slice 2 - Payload Disposition

For payload entries:

1. compatible / absent lease evidence preserves existing behavior;
2. `review_required` evidence does not create write plans and records
   `disposition = review_routed`;
3. `blocked` or `waiting` evidence does not create write plans and records
   `disposition = blocked`;
4. path-local validation continues to reject unsafe/outside-boundary payloads;
5. the existing summary still records planned and skipped payloads.

### Slice 3 - Focused Tests

Add focused tests for:

1. compatible / absent evidence preserves existing payload planning;
2. review-required evidence routes payloads to skipped review evidence;
3. blocked evidence routes payloads to skipped blocked evidence;
4. lease evidence works for grouped child payload planning;
5. existing grouped shared-review-zone approval behavior remains intact.

## Non-Goals

This gate does not:

1. Add lease acquisition / release / renewal lifecycle.
2. Evaluate ambient-time lease expiration.
3. Pull live scheduler state into the write-back engine.
4. Change scheduler admission.
5. Execute review-routed payload writes.
6. Add MCP or Host UX lease readback.
7. Add real sandbox provider enforcement.
8. Change ExchangeArtifact admission semantics.
9. Mutate agent-owned Local Work Trajectory from scheduler or write-back code.

## Acceptance Criteria

The gate may close when:

1. Write-back payload summaries can distinguish `planned`, `review_routed`,
   `blocked`, and existing skipped reasons.
2. Review-required edit lease evidence prevents direct write plans.
3. Blocked edit lease evidence prevents direct write plans.
4. Focused write-back tests pass.
5. Wider relevant regression passes.
6. Review/status docs record validation and preserved non-goals.

## Close Summary

This gate closed after implementing optional edit lease evidence consumption in
`src/pep/writeback_engine.py`.

Implemented behavior:

1. `WritebackEngine` accepts optional `edit_lease_conflict` or
   `edit_lease_decision` evidence from `execution_result`.
2. Evidence can be dict-like or dataclass-like, including direct
   `EditLeaseConflictDecision` objects.
3. Report payload planning and grouped child payload planning share the same
   payload disposition logic.
4. `review_required` evidence prevents direct payload write plans and records
   skipped payload evidence with `disposition = review_routed`.
5. `blocked` and `waiting` evidence prevent direct payload write plans and
   record skipped payload evidence with `disposition = blocked`.
6. Unsafe path and allowed-artifact boundary validation remain local to the
   write-back engine and still run before lease evidence disposition.
7. Write-back markdown summaries now count review-routed and blocked payloads
   for report payloads and grouped child payloads.

Validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/pep/writeback_engine.py tests/test_pep_writeback_lease_evidence.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_pep_writeback_lease_evidence.py
5 passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py
198 passed
```

Review evidence:

`review/write-back-enforcement-unification-2026-06-20.md`
