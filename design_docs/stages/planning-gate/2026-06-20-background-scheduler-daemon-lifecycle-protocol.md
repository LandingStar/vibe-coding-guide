# Planning Gate - Background Scheduler Daemon Lifecycle Protocol

> Date: 2026-06-20
> Status: COMPLETED

## Trigger

`design_docs/agent-orchestration-after-release-evidence-direction-analysis.md`
and the completed scheduler event-log compaction slice both recommend moving
toward a background scheduler lifecycle only after scheduler persistence has a
clear compaction / replay boundary.

## Problem

The scheduler now has a bounded repeated loop:

```text
SchedulerDaemonLoopRequest
SchedulerDaemonLoopResult
SchedulerDaemonLoopStopPolicy
run_scheduler_daemon_loop()
```

This is enough for explicit operator commands and host-injected bounded runs. It
is not yet a lifecycle protocol. There is no durable control file that records
whether a daemon owner intends the scheduler to run, pause, cancel, heartbeat,
resume, shut down, or be considered stale.

This slice should answer:

```text
Can the project define a local, durable scheduler daemon lifecycle control
contract around the existing bounded loop without starting an OS background
service?
```

## Scope

### Slice 1 - Lifecycle Contract

Define first-version lifecycle objects:

```text
SchedulerDaemonLifecycleState
SchedulerDaemonLifecycleControl
SchedulerDaemonLifecycleRequest
SchedulerDaemonLifecycleResult
SchedulerDaemonLifecycleRunOnceRequest
SchedulerDaemonLifecycleRunOnceResult
```

The first lifecycle states should cover:

1. `idle`
2. `running`
3. `paused`
4. `cancelling`
5. `cancelled`
6. `stopped`
7. `stale`

The control file should record:

1. daemon id;
2. scheduler snapshot path;
3. scheduler event-log path;
4. status;
5. run id;
6. heartbeat timestamp;
7. requested action;
8. last result summary;
9. authority clues.

### Slice 2 - Local Store And Transitions

Implement a JSON lifecycle control store.

Minimum operations:

1. start / register lifecycle control;
2. heartbeat;
3. pause;
4. resume;
5. cancel request;
6. shutdown;
7. mark stale when heartbeat age exceeds caller-provided threshold;
8. readback / inspection.

The store must be deterministic and local. It should not spawn a process,
sleep, poll, watch the filesystem, or run providers on its own.

### Slice 3 - Bounded Run-Once Wrapper

Add one helper that checks lifecycle state and then delegates to
`run_scheduler_daemon_loop()`.

Minimum behavior:

1. `paused`, `cancelling`, `cancelled`, `stopped`, and `stale` controls do not
   run the loop;
2. `running` controls may run one bounded loop and then write compact result
   summary into the lifecycle control file;
3. an explicit cancel request maps to a cancelled stop policy before running;
4. the helper returns authority clues showing scheduler state may mutate only
   through the bounded loop and lifecycle state mutates only through the control
   file.

### Slice 4 - Focused Tests

Add focused tests for:

1. start / heartbeat / pause / resume / cancel / shutdown transitions;
2. stale detection;
3. paused lifecycle skips scheduler loop mutation;
4. running lifecycle can invoke the bounded fake-runtime loop once;
5. run-once result records last loop summary and authority split.

## Non-Goals

This gate does not:

1. Start a real background daemon process.
2. Add sleeps, polling, filesystem watch, OS service registration, or process
   supervision.
3. Run real Qoder or other external providers.
4. Add CLI or MCP lifecycle commands unless needed for minimal validation.
5. Add UI binding.
6. Add retry/timeout execution policy beyond existing bounded loop fields.
7. Add real sandbox providers.
8. Mutate ExchangeArtifact lifecycle or admission ledger state.
9. Mutate `.codex/progress-graph/local-work-trajectory.json` from scheduler
   code.

## Acceptance Criteria

The gate may close when:

1. Lifecycle control objects and JSON store are implemented.
2. Lifecycle transitions are deterministic and tested.
3. Stale heartbeat detection is deterministic and tested.
4. Run-once wrapper respects pause/cancel/stopped/stale lifecycle states.
5. Running lifecycle delegates to `run_scheduler_daemon_loop()` without
   introducing a background service.
6. Review/status docs record validation and preserved non-goals.

## Implementation Summary

Completed on 2026-06-20.

This slice added a local scheduler daemon lifecycle protocol without starting
an OS background service.

Implemented:

1. New runtime module:
   - `src/runtime/orchestration/scheduler_daemon_lifecycle.py`
2. Lifecycle contract:
   - `SchedulerDaemonLifecycleState`
   - `SchedulerDaemonLifecycleAction`
   - `SchedulerDaemonLifecycleControl`
   - `SchedulerDaemonLifecycleRequest`
   - `SchedulerDaemonLifecycleResult`
   - `SchedulerDaemonLifecycleRunOnceRequest`
   - `SchedulerDaemonLifecycleRunOnceResult`
3. Local JSON control helpers:
   - `read_scheduler_daemon_lifecycle_control()`
   - `write_scheduler_daemon_lifecycle_control()`
   - `apply_scheduler_daemon_lifecycle_action()`
   - `inspect_scheduler_daemon_lifecycle_control()`
   - `lifecycle_queue_snapshot()`
4. Lifecycle-gated run-once helper:
   - `run_scheduler_daemon_lifecycle_once()`
5. Public exports from `src/runtime/orchestration/__init__.py`.

The first implementation supports deterministic start, heartbeat, pause,
resume, cancel, shutdown, mark-stale, and inspect transitions. Stale heartbeat
detection accepts both epoch-second strings and ISO-8601 timestamps so the
control file remains compatible with existing scheduler timestamp conventions.
The run-once helper runs `run_scheduler_daemon_loop()` only while lifecycle
state is `running`; paused / cancelled / stopped / stale controls skip
scheduler mutation, and cancelling controls are consumed into `cancelled`
without running providers.

## Validation

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_daemon_lifecycle or scheduler_daemon_loop"
16 passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py
191 passed
```

## Non-Goals Preserved

This slice did not add:

1. A real background daemon process.
2. Sleeps, polling, filesystem watch, OS service registration, or process
   supervision.
3. Real Qoder or other external provider execution.
4. CLI or MCP lifecycle commands.
5. UI binding.
6. New retry/timeout execution policy beyond existing bounded loop fields.
7. Real sandbox providers.
8. ExchangeArtifact lifecycle or admission ledger mutation.
9. Scheduler-code mutation of agent-owned Local Work Trajectory.
