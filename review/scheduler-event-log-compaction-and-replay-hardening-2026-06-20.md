# Review - Scheduler Event-Log Compaction And Replay Hardening

> Date: 2026-06-20
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-20-scheduler-event-log-compaction-and-replay-hardening.md`

## Scope Reviewed

This slice hardened scheduler snapshot / JSONL event-log compaction and replay
boundaries.

Implemented:

1. `SchedulerCompactionResult` replay-boundary fields:
   - `archived_event_log_path`
   - `archive_requested`
   - `reset_event_log_requested`
   - `archived_event_count`
   - `active_event_count_after_compaction`
   - `replay_boundary_summary`
2. `JsonlSchedulerEventLog.write_all()` and `JsonlSchedulerEventLog.clear()`.
3. Optional archive/reset behavior in `write_compacted_scheduler_snapshot()`.
4. Readable strict replay errors for events that reference task IDs outside
   the baseline snapshot authority boundary.
5. Focused tests covering:
   - default non-destructive compaction compatibility;
   - archive/reset compaction;
   - empty post-compaction active log;
   - compacted snapshot plus post-compaction event recovery;
   - missing source event-log idempotence;
   - reset-without-archive rejection;
   - boundary-oriented unknown-task replay errors.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_event_log or replay_scheduler_events or recover_scheduler_state or write_compacted_scheduler_snapshot"
17 passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py
185 passed
```

## Behavioral Notes

`write_compacted_scheduler_snapshot()` remains backward compatible by default:
it writes the recovered compacted snapshot and leaves the active event log
untouched.

Archive/reset behavior is explicit:

```text
write_compacted_scheduler_snapshot(
    snapshot_path,
    event_log_path,
    compacted_snapshot_path,
    archive_event_log_path=archive_path,
    reset_event_log=True,
)
```

When enabled, the helper writes all events represented by the compacted snapshot
to the archive JSONL file, writes the compacted snapshot, and then resets the
active event log to an empty post-compaction replay boundary. Recovery from the
compacted snapshot then replays only new post-compaction events.

## Authority Boundary

The authority split remains:

1. Scheduler snapshots remain task-contract authority.
2. Scheduler event logs remain replay / audit material.
3. Event logs do not create missing scheduler task contracts.
4. Archive/reset compaction preserves pre-compaction history outside the active
   log.
5. Local Work Trajectory remains agent-owned and is not mutated by scheduler
   code.

## Explicit Non-Goals Preserved

This slice did not add:

1. Background scheduler daemon service.
2. Retry, cancellation, timeout execution, heartbeat, pause, or resume.
3. Real Qoder or other external provider execution.
4. UI binding.
5. Real sandbox providers.
6. ExchangeArtifact lifecycle mutation.
7. Admission ledger mutation.
8. Event-log-driven task contract creation.
9. Remote log retention, redaction, compression, or database storage.

## Follow-Up

The scheduler now has a safer persistence boundary for long-running
orchestration. The next likely backend candidate is `Background Scheduler Daemon
Lifecycle Protocol`, but it should remain a separate planning gate because it
introduces service lifecycle, heartbeat, cancellation, and operator-control
semantics.
