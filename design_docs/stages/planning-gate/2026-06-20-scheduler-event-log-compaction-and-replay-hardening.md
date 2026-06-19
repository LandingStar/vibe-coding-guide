# Planning Gate - Scheduler Event-Log Compaction And Replay Hardening

> Date: 2026-06-20
> Status: COMPLETED

## Trigger

`design_docs/agent-orchestration-after-release-evidence-direction-analysis.md`
recommends returning to orchestration core after the full release evidence line
and selecting `Scheduler Event-Log Compaction And Replay Hardening` as the next
backend slice.

## Problem

The scheduler already has:

```text
recover_scheduler_state()
replay_scheduler_events()
write_compacted_scheduler_snapshot()
JsonlSchedulerEventLog
```

The current compaction primitive writes a recovered state into a compacted
snapshot, but it deliberately leaves the source JSONL event log untouched. That
was the right first primitive. It is not enough for longer-running orchestration:
there is still no explicit post-compaction replay boundary, no archive path for
events represented by the compacted snapshot, and no readable failure contract
when recovery sees events that no longer match the snapshot authority boundary.

This slice should answer:

```text
Can scheduler compaction safely preserve pre-compaction event history, reset the
active event log for future events, and recover from compacted snapshot +
post-compaction log without treating event logs as task-contract authority?
```

## Scope

### Slice 1 - Contract

Extend the existing compaction contract without breaking the current
non-destructive default.

The contract should distinguish:

1. source snapshot path;
2. source event log path;
3. compacted snapshot path;
4. optional archived event log path;
5. whether active event log reset was requested;
6. whether active event log reset happened;
7. replay boundary summary:
   - compacted event count;
   - archived event count;
   - post-compaction active event count;
   - strict / non-strict recovery mode.

### Slice 2 - Runtime Implementation

Implement an explicit archive/reset path.

Minimum behavior:

1. default call remains non-destructive and preserves current behavior;
2. when archive/reset is requested, write all compacted events to an archive
   JSONL file;
3. after successful archive write and compacted snapshot write, reset the
   active event log to empty;
4. if source log does not exist, reset should still leave an empty active log
   and report zero archived events;
5. recover from a compacted snapshot plus the reset active event log should
   replay only post-compaction events;
6. error messages for unknown task events should name the replay boundary and
   the fact that event logs do not create task contracts.

### Slice 3 - Focused Tests

Add focused tests for:

1. default non-destructive compaction remains unchanged;
2. archive/reset compaction writes compacted snapshot and archived JSONL events;
3. active event log is empty after archive/reset;
4. compacted snapshot plus new post-compaction event recovers correctly;
5. missing source event log archive/reset is idempotent;
6. strict unknown-event replay error is readable and boundary-oriented.

## Non-Goals

This gate does not:

1. Start or define a background scheduler daemon service.
2. Add retry, cancellation, timeout execution, heartbeat, pause, or resume.
3. Run real Qoder or any external provider.
4. Add UI binding or screenshot validation.
5. Add real sandbox providers.
6. Change ExchangeArtifact lifecycle or admission ledger behavior.
7. Make event logs create scheduler task contracts.
8. Mutate `.codex/progress-graph/local-work-trajectory.json` from scheduler
   code.
9. Define remote log retention, redaction, compression, or database storage.

## Acceptance Criteria

The gate may close when:

1. The compaction result contract exposes archive/reset and replay-boundary
   fields.
2. Non-destructive compaction remains backward compatible.
3. Archive/reset compaction preserves pre-compaction history outside the active
   log and creates an empty post-compaction active log.
4. Recovery from compacted snapshot plus post-compaction log is covered by
   tests.
5. Strict replay errors explain that unknown event task IDs are outside the
   snapshot authority boundary.
6. Review/status docs record validation and preserved non-goals.

## Implementation Summary

Completed on 2026-06-20.

This slice hardened scheduler event-log compaction and replay without changing
the existing default behavior.

Implemented:

1. `SchedulerCompactionResult` now exposes replay-boundary metadata:
   - `archived_event_log_path`
   - `archive_requested`
   - `reset_event_log_requested`
   - `archived_event_count`
   - `active_event_count_after_compaction`
   - `replay_boundary_summary`
2. `JsonlSchedulerEventLog` now supports:
   - `write_all(events)`
   - `clear()`
3. `write_compacted_scheduler_snapshot()` now remains non-destructive by
   default, but can explicitly:
   - archive the represented scheduler events to a JSONL file;
   - reset the active event log after successful archive + compacted snapshot
     write;
   - reject active-log reset without an archive path.
4. Strict replay errors now explain that unknown task IDs are outside the
   baseline snapshot task-contract boundary and that event logs are replay /
   audit material, not task-contract creation authority.

## Validation

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_event_log or replay_scheduler_events or recover_scheduler_state or write_compacted_scheduler_snapshot"
17 passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py
185 passed
```

## Non-Goals Preserved

This slice did not add:

1. Background scheduler daemon service.
2. Retry, cancellation, timeout execution, heartbeat, pause, or resume.
3. Real Qoder or other external provider execution.
4. UI binding or screenshot validation.
5. Real sandbox providers.
6. ExchangeArtifact lifecycle or admission ledger changes.
7. Event-log-driven task contract creation.
8. Scheduler-code mutation of agent-owned Local Work Trajectory.
9. Remote log retention, redaction, compression, or database storage.
