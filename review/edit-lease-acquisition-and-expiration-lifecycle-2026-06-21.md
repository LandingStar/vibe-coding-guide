# Review - Edit Lease Acquisition And Expiration Lifecycle

> Date: 2026-06-21
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-20-edit-lease-acquisition-and-expiration-lifecycle.md`

## Scope Reviewed

This slice introduced scheduler-owned edit lease lifecycle evidence after the
classifier and write-back evidence slices.

Implemented:

1. `EditLeaseLifecycleState` and `EditLeaseLifecycleRecord`.
2. `SchedulerState.edit_lease_lifecycle`.
3. Admission-derived lifecycle transitions for acquired, waiting,
   review-required, and blocked leases.
4. Submission-time requested lifecycle records for declared edit leases.
5. Release on task completion and permission approval.
6. Revoke on runtime failure and permission rejection.
7. Explicit-time expiry through `expire_edit_leases(now=...)`.
8. Scheduler event lifecycle snapshots through `lease_id` and
   `edit_lease_lifecycle`.
9. Scheduler event replay and state snapshot round-trip for lifecycle records.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/scheduler.py src/runtime/orchestration/scheduler_store.py src/runtime/orchestration/scheduler_submission.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "edit_lease_lifecycle or edit_lease_classifier or conflicting_write_leases or scheduler_state_snapshot_round_trips_edit_lease_lifecycle or replay_scheduler_events_recovers_edit_lease_lifecycle"
17 passed
```

Wider relevant regression:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py
207 passed
```

## Behavioral Notes

Lifecycle records are scheduler-owned evidence, not a replacement for the
`EditScopeLease` declaration on `ScheduledTask`.

Admission remains sourced from `classify_edit_lease_conflict()`. Lifecycle
records preserve that conflict decision instead of introducing a second
classifier.

Expiry is deliberately explicit. Calling `expire_edit_leases()` without `now`
does nothing, so replay-sensitive paths do not read ambient wall-clock time.

`SchedulerEvent` can carry lifecycle snapshots. Replay restores those records,
and `lease_*` events update lifecycle state without mutating task state.

## Authority Boundary

This slice does not add real filesystem/process sandbox enforcement, sandbox
mount binding, Host UX/MCP readback, write-back live scheduler queries,
ExchangeArtifact semantic changes, Local Work Trajectory mutation from
scheduler code, or daemon expiry sweeping.

## Follow-Up

The next backend slice should be `Sandbox Mount Binding Over Acquired Leases`.
It should consume `SchedulerState.edit_lease_lifecycle` rather than treating
static `EditScopeLease` declarations as acquired authority.
