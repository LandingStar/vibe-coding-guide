# Review - Background Scheduler Daemon Lifecycle Protocol

> Date: 2026-06-20
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-20-background-scheduler-daemon-lifecycle-protocol.md`

## Scope Reviewed

This slice added a local scheduler daemon lifecycle control protocol around the
existing bounded scheduler daemon loop.

Implemented:

1. `src/runtime/orchestration/scheduler_daemon_lifecycle.py`.
2. Lifecycle data contract:
   - `SchedulerDaemonLifecycleState`
   - `SchedulerDaemonLifecycleAction`
   - `SchedulerDaemonLifecycleControl`
   - `SchedulerDaemonLifecycleRequest`
   - `SchedulerDaemonLifecycleResult`
   - `SchedulerDaemonLifecycleRunOnceRequest`
   - `SchedulerDaemonLifecycleRunOnceResult`
3. Local JSON lifecycle control helpers:
   - `read_scheduler_daemon_lifecycle_control()`
   - `write_scheduler_daemon_lifecycle_control()`
   - `apply_scheduler_daemon_lifecycle_action()`
   - `inspect_scheduler_daemon_lifecycle_control()`
   - `lifecycle_queue_snapshot()`
4. Lifecycle-gated run-once helper:
   - `run_scheduler_daemon_lifecycle_once()`
5. Public exports through `src/runtime/orchestration/__init__.py`.
6. Tests covering:
   - start / heartbeat / pause / resume / cancel / shutdown;
   - stale heartbeat detection for epoch-second and ISO-8601 heartbeat values;
   - paused lifecycle skip without scheduler mutation;
   - running lifecycle bounded fake-runtime loop;
   - cancel request consumption without scheduler mutation.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_daemon_lifecycle or scheduler_daemon_loop"
16 passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py
191 passed
```

## Behavioral Notes

The lifecycle control file is local JSON state. It records daemon id, scheduler
snapshot path, event-log path, lifecycle state, run id, heartbeat timestamp,
requested action, last bounded-loop result summary, metadata, and authority
clues. Stale heartbeat detection accepts both epoch-second strings and
ISO-8601 timestamps to match the wider scheduler runtime convention.

`run_scheduler_daemon_lifecycle_once()` is intentionally a bounded call:

1. It runs the scheduler loop only when control state is `running`.
2. It skips scheduler mutation for paused / cancelled / stopped / stale states.
3. It consumes `cancelling` or requested `cancel` into `cancelled` before any
   provider execution.
4. It records compact loop summary back to lifecycle control after a run.
5. It does not create a long-lived process.

## Authority Boundary

The authority split remains:

1. Lifecycle intent lives in the lifecycle control file.
2. Scheduler task state remains in scheduler snapshot / event log.
3. Scheduler projection remains explicit and separate.
4. Local Work Trajectory remains agent-owned.
5. ExchangeArtifact store and admission ledger are not touched.

## Explicit Non-Goals Preserved

This slice did not add:

1. Real background daemon service.
2. Sleep / polling / watch mode.
3. OS service registration or process supervision.
4. Real Qoder or external provider execution.
5. CLI or MCP lifecycle command surface.
6. UI binding.
7. New retry/timeout execution policy.
8. Real sandbox provider implementation.
9. Local Work Trajectory mutation from scheduler code.

## Follow-Up

The scheduler now has a durable local lifecycle-control object. The next
backend candidate should stay narrow: either expose a small operator CLI/MCP
read/write surface for this lifecycle control, or advance edit-lease conflict
policy before enabling higher-concurrency agent writes.
