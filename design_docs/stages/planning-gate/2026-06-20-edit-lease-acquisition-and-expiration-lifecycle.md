# Planning Gate - Edit Lease Acquisition And Expiration Lifecycle

> Date: 2026-06-20
> Status: COMPLETED

## Trigger

`design_docs/edit-lease-lifecycle-after-writeback-unification-direction-analysis.md`
recommends making edit lease lifecycle a scheduler-owned authority layer before
sandbox mount binding, Host UX/MCP readback, or real sandbox provider work.

The previous slices completed:

- `EditLeaseConflictDecision`
- `classify_edit_lease_conflict()`
- scheduler admission evidence through `AdmissionDecision.edit_lease_conflict`
- write-back planning consumption of optional edit lease evidence

## Problem

`EditScopeLease` is currently task declaration metadata. The scheduler can
classify conflicts and write-back can consume that evidence, but there is no
scheduler-owned lifecycle record that proves whether an edit lease was
requested, acquired, released, expired, revoked, or blocked.

This leaves several unsafe ambiguities:

1. `expires_at` exists on `EditScopeLease`, but no deterministic helper
   interprets it.
2. Ready/running task state is doing double duty as the only proxy for active
   edit authority.
3. Task completion, cancellation, rejection, failure, and stale recovery do not
   have an explicit lease cleanup target.
4. Future sandbox mount binding cannot distinguish a declared lease from an
   acquired lease.
5. Future Host UX/MCP readback would otherwise have to present static lease
   declarations as if they were current authority.

This slice should answer:

```text
Can scheduler code create and update deterministic edit lease lifecycle records
without adding real filesystem enforcement or Host UX/MCP readback?
```

## Scope

### Slice 1 - Lifecycle Record Shape

Add scheduler-owned lifecycle data structures:

```text
EditLeaseLifecycleState
- requested
- acquired
- waiting
- review_required
- released
- expired
- revoked
- blocked

EditLeaseLifecycleRecord
- lease_id
- task_id
- state
- mode
- allowed_artifacts
- denied_artifacts
- conflict_policy
- acquired_at
- expires_at
- released_at
- reason
- conflict_decision

EditLeaseLifecycleEvent
- lease_requested
- lease_acquired
- lease_waiting
- lease_review_required
- lease_released
- lease_expired
- lease_revoked
- lease_blocked
```

The first implementation may keep lifecycle records inside `SchedulerState`.
The record is derived from and linked to `EditScopeLease`, but it must not
replace the task contract declaration.

### Slice 2 - Deterministic Lifecycle Helpers

Add explicit scheduler helpers for:

1. request/acquire from an admitted task lease;
2. waiting/review-required/blocked from `classify_edit_lease_conflict()`;
3. release on successful task completion or approved permission review;
4. revoke on task failure, cancellation, permission rejection, or explicit
   terminal block;
5. expire from `expires_at` using caller-provided `now` or `timestamp`.

Expiry checks must not read ambient wall-clock time inside replay-sensitive
paths. If no timestamp is provided, expiry is not evaluated.

### Slice 3 - Event And Replay Evidence

Lifecycle changes should be inspectable through scheduler-owned evidence.

First acceptable shape:

1. extend `SchedulerEventKind` and `SchedulerEvent` with lease lifecycle events;
2. record lease id / lifecycle fields in scheduler events;
3. teach scheduler replay to recover lifecycle records from events;
4. teach scheduler state snapshot JSON to round-trip lifecycle records.

If a narrower dedicated lease event log proves cleaner during implementation,
record that decision in this gate before changing course.

### Slice 4 - Focused Tests

Add focused runtime orchestration tests for:

1. compatible write lease becomes acquired when a task becomes ready/running;
2. blocked conflict creates blocked lifecycle evidence;
3. review-zone conflict creates review-required lifecycle evidence;
4. completed task releases its acquired lease;
5. permission rejection or runtime failure revokes its acquired lease;
6. deterministic expiry uses explicit `now` and never ambient time;
7. snapshot round-trip preserves lifecycle records;
8. replay from scheduler events recovers lifecycle records.

## Non-Goals

This gate does not:

1. Add real filesystem or process sandbox enforcement.
2. Bind sandbox mounts to acquired lease records.
3. Implement a Docker, git-worktree, or remote-VM provider.
4. Add Host UX or MCP lease readback.
5. Make write-back planning query live scheduler state.
6. Change ExchangeArtifact admission semantics.
7. Change Local Work Trajectory ownership or mutate it from scheduler code.
8. Introduce background daemon expiry sweeping.
9. Use ambient wall-clock time for lifecycle expiry decisions.

## Acceptance Criteria

The gate may close when:

1. Scheduler exports lifecycle record/state/event shapes.
2. Scheduler helpers can acquire, release, revoke, block, review-route, and
   expire edit leases deterministically.
3. Existing admission conflict classification remains the source of blocked or
   review-required lifecycle evidence.
4. Task terminal transitions update lifecycle records where an edit lease was
   acquired.
5. Scheduler event replay and state snapshots preserve lifecycle evidence.
6. Focused runtime orchestration lifecycle tests pass.
7. Wider relevant runtime orchestration regression passes.
8. Review/status docs record validation and preserved non-goals.

## Close Summary

Completed on 2026-06-21.

This gate added scheduler-owned edit lease lifecycle evidence without adding
real sandbox enforcement or Host UX/MCP readback.

Implemented behavior:

1. `EditLeaseLifecycleState` and `EditLeaseLifecycleRecord` are exported from
   orchestration runtime.
2. `SchedulerState` now carries `edit_lease_lifecycle` records keyed by
   `lease_id`.
3. Scheduler admission derives lifecycle records from existing
   `classify_edit_lease_conflict()` evidence:
   - admissible edit leases become `acquired`;
   - waiting decisions become `waiting`;
   - review-zone conflicts become `review_required`;
   - blocked conflicts become `blocked`.
4. Task submission records declared edit leases as `requested`.
5. Task completion and permission approval release acquired leases.
6. Runtime failure and permission rejection revoke acquired leases.
7. `expire_edit_leases()` expires active leases only when the caller provides
   explicit `now`; no ambient time is read for expiry.
8. `SchedulerEvent` can carry `lease_id` and an optional lifecycle snapshot;
   replay restores lifecycle records and treats `lease_*` events as lifecycle
   evidence rather than task state transitions.
9. Scheduler state snapshots round-trip lifecycle records and conflict
   decisions.

Validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/scheduler.py src/runtime/orchestration/scheduler_store.py src/runtime/orchestration/scheduler_submission.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "edit_lease_lifecycle or edit_lease_classifier or conflicting_write_leases or scheduler_state_snapshot_round_trips_edit_lease_lifecycle or replay_scheduler_events_recovers_edit_lease_lifecycle"
17 passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py
207 passed
```

Review evidence:

`review/edit-lease-acquisition-and-expiration-lifecycle-2026-06-21.md`

## Implementation Notes

Prefer extending the existing scheduler/state/replay path before creating a new
storage subsystem. The purpose of this slice is to make lease authority visible
and deterministic, not to make it externally enforceable yet.

The most likely implementation files are:

- `src/runtime/orchestration/scheduler.py`
- `src/runtime/orchestration/scheduler_store.py`
- `src/runtime/orchestration/__init__.py`
- `tests/test_runtime_orchestration.py`

## Follow-Up

If this gate closes cleanly, the next backend slice should be:

```text
Sandbox Mount Binding Over Acquired Leases
```

That follow-up should consume lifecycle records rather than re-classifying
static `EditScopeLease` declarations.
