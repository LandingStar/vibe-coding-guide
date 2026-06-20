# Planning Gate - Edit Lease Conflict Classifier And Admission Evidence

> Date: 2026-06-20
> Status: COMPLETED

## Trigger

`design_docs/edit-lease-conflict-policy-expansion-direction-analysis.md`
recommends turning scheduler edit lease overlap checks into a structured,
testable classifier before adding lease lifecycle, write-back unification,
sandbox mount binding, or Host UX readback.

## Problem

`EditScopeLease` is already scheduler-owned metadata, but scheduler admission
currently uses a coarse helper that only blocks write/write exact path
intersection against ready/running tasks.

That misses:

1. project-relative path normalization;
2. directory/file containment;
3. denied artifact evidence;
4. unsupported conflict policy evidence;
5. explicit review-zone routing;
6. a reusable decision object for future UI/MCP/write-back consumers.

## Scope

### Slice 1 - Scheduler-Owned Classifier

Add a pure scheduler classifier that compares a proposed task lease with active
ready/running task leases and returns structured evidence.

The first decision shape should include:

```text
EditLeaseConflictDecision
- state: compatible | waiting | review_required | blocked
- classification:
  - no_overlap
  - exact_path_overlap
  - directory_contains_file
  - directory_overlap
  - denied_artifact_hit
  - unsupported_policy
  - unsafe_path
  - review_zone_overlap
- left_task_id / right_task_id
- left_lease_id / right_lease_id
- left_path / right_path
- reason
```

### Slice 2 - Admission Integration Only

Integrate the classifier into `evaluate_task_admission()` only.

Default semantics:

1. read/read and read/write remain compatible;
2. write/write overlap remains blocked by default;
3. `review-zone` overlap becomes `review_required`, not automatic execution;
4. unsupported `conflict_policy` becomes blocked with readable evidence;
5. unsafe lease paths become blocked with readable evidence;
6. exact overlap preserves the existing simple blocking behavior.

### Slice 3 - Focused Tests

Add tests for:

1. exact path overlap;
2. directory containment;
3. denied artifact hit;
4. review-zone overlap admission state;
5. unsupported conflict policy;
6. unsafe path normalization;
7. read/write compatibility.

## Non-Goals

This gate does not:

1. Add persistent lease acquisition / release / renewal lifecycle.
2. Implement ambient-time lease expiration.
3. Change write-back execution semantics.
4. Bind real sandbox providers or filesystem enforcement.
5. Add Host UX or MCP readback for lease decisions.
6. Change ExchangeArtifact admission semantics.
7. Mutate agent-owned Local Work Trajectory from scheduler code.

## Acceptance Criteria

The gate may close when:

1. The classifier and decision dataclass are available from the orchestration
   runtime package.
2. Scheduler admission uses the classifier and exposes structured decision
   evidence.
3. `review-zone` overlap lands tasks in `review_required`.
4. Focused scheduler tests pass.
5. Review/status docs record validation and preserved non-goals.

## Implementation Summary

Completed on 2026-06-20.

This slice replaced the scheduler's coarse edit lease exact-overlap helper with
a structured scheduler-owned classifier:

```text
EditLeaseConflictDecision
classify_edit_lease_conflict()
```

Implemented behavior:

1. scheduler admission now carries `edit_lease_conflict` structured evidence;
2. project-relative lease paths are normalized without filesystem access;
3. unsafe paths are blocked;
4. unsupported conflict policies are blocked;
5. exact path overlap remains blocked with the prior readable reason shape;
6. directory/file containment and directory/directory overlap are classified;
7. denied artifact hits are classified before ordinary overlap;
8. read/write overlap remains compatible;
9. `review-zone` overlap lands in `review_required` and records a
   `task_review_required` event through existing scheduler history.

The new classifier is exported from `src.runtime.orchestration` for future
write-back, MCP, Host UX, and sandbox-policy consumers.

## Validation

Focused validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/scheduler.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "edit_lease_classifier or conflicting_write_leases or drain_ready_tasks_reports_blocked_admission"
9 passed
```

Wider regression:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py
198 passed
```

## Non-Goals Preserved

This slice did not add:

1. persistent lease acquisition / release / renewal lifecycle;
2. ambient-time lease expiration;
3. write-back execution changes;
4. real sandbox provider binding or filesystem enforcement;
5. Host UX or MCP readback for lease decisions;
6. ExchangeArtifact admission semantic changes;
7. scheduler-code mutation of agent-owned Local Work Trajectory.

## Follow-Up

The next backend slice should be `Write-Back Enforcement Unification`: make
write-back planning consume the same classifier/path semantics without changing
lease lifecycle or real sandbox enforcement yet.
