# Review - Edit Lease Conflict Classifier And Admission Evidence

> Date: 2026-06-20
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-20-edit-lease-conflict-classifier-and-admission-evidence.md`

## Scope Reviewed

This slice implemented the backend edit lease classifier recommended by
`design_docs/edit-lease-conflict-policy-expansion-direction-analysis.md`.

Implemented:

1. `EditLeaseConflictDecision` structured scheduler evidence.
2. `classify_edit_lease_conflict()` as a pure scheduler-owned classifier.
3. Scheduler admission integration through `AdmissionDecision.edit_lease_conflict`.
4. `review-zone` overlap routing to existing `ScheduledTask.state =
   review_required`.
5. Package exports from `src.runtime.orchestration`.
6. Focused runtime tests for exact overlap, directory containment, directory
   overlap, denied artifacts, review-zone, unsupported policies, unsafe paths,
   and read/write compatibility.

## Evidence

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

## Behavioral Notes

The classifier is pure and does not read the filesystem. It normalizes
project-relative lease paths by rejecting empty paths, absolute paths, and
`..` traversal. This matches the scheduler replay/admission requirement that
classification should be deterministic without ambient workspace state.

The first supported conflict policy remains `block-on-overlap`. Unsupported
policies fail closed with `unsupported_policy` evidence.

`review-zone` is deliberately not an automatic run permission. A task with
overlapping review-zone edit authority moves to `review_required`, records
`task_review_required` through the existing scheduler event path, and is
reported through existing queue summaries as review work rather than ready
work.

## Authority Boundary

This slice changes scheduler admission evidence only. It does not change
write-back planning, ExchangeArtifact admission, MCP tool surfaces, Host UX
readback, sandbox provider behavior, or lease lifecycle.

## Follow-Up

The next backend follow-up should be `Write-Back Enforcement Unification`, so
payload planning can consume the same edit lease path/classification semantics
instead of relying only on separate `contract.allowed_artifacts` checks.
