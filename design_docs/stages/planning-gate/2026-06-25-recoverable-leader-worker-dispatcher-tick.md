# Recoverable Leader Worker Dispatcher Tick

> Date: 2026-06-25
> Status: IMPLEMENTED

## Trigger

`LeaderWorkerActivationResult` can project runnable/waiting/blocked leader and
worker state, but it is currently read-only. A restarted host can inspect the
same scheduler and ExchangeArtifact inputs, yet there is no durable activation
cursor, no dispatcher-level event log, and no bounded tick/loop surface that
can decide which agent should be activated next without running providers.

## Goal

Add a narrow, recoverable dispatcher layer over leader-worker activation. The
dispatcher should persist activation cursors and compact dispatch decisions so
leader/worker coordination can survive host restart and avoid re-emitting the
same scheduling signal repeatedly.

## Scope

This gate includes:

1. a `LeaderWorkerDispatcherState` JSON contract containing the embedded
   activation state, emitted decision source keys, tick counters, and compact
   last-result summary;
2. a JSONL `LeaderWorkerDispatcherTickRecord` audit log;
3. a deterministic `run_leader_worker_dispatcher_tick()` that reads scheduler
   snapshot + ExchangeArtifact store, runs activation projection, emits new
   dispatch decisions, writes dispatcher state, and appends a tick record;
4. a bounded `run_leader_worker_dispatcher_loop()` that repeats ticks until
   `max_ticks` or no new dispatch decisions;
5. CLI surfaces for tick and loop read/write operations;
6. focused tests for first tick persistence, restart/dedup behavior, loop stop
   behavior, and CLI readback.

## Non-goals

This gate does not:

1. run Codex/Qoder/opencode providers;
2. mutate scheduler snapshot/event log;
3. mutate ExchangeArtifact store or admission ledger;
4. implement a background daemon or web UI;
5. allocate agent homes, sandboxes, or processes;
6. guarantee delivery acknowledgements from live workers;
7. mutate agent-owned Local Work Trajectory from runtime code.

## Contract

Authority remains split:

- scheduler snapshot/event log is task lifecycle authority;
- ExchangeArtifact store is message/history authority;
- dispatcher state file is activation cursor and dispatch de-dup authority;
- dispatcher event log is compact audit history;
- provider execution remains outside this slice.

Dispatch decisions are idempotent within the state file. A decision source key
is derived from event kind, agent, lane/task/message source, and next action.
If a host restarts and runs another tick with unchanged inputs, already emitted
decisions are suppressed while lifecycles are still projected for status
readback.

## Validation Plan

- Focused runtime tests for dispatcher tick persistence and loop stop behavior.
- Focused CLI tests for tick/loop commands.
- `py_compile` for touched runtime/CLI/tests.
- `doc-loop` validator and `git diff --check`.
- Compact Checklist writeback after close.

## Closure Criteria

This gate closes when leader-worker activation has a tested persistent
dispatcher tick/loop surface that can recover from local files and emit compact
dispatch decisions without claiming provider execution or a background daemon.

## Implemented Surface

Runtime:

- Added `src/runtime/orchestration/leader_worker_dispatcher.py`.
- New durable state:
  - `LeaderWorkerDispatcherState`
  - `LEADER_WORKER_DISPATCHER_STATE_SCHEMA_VERSION`
  - default path `.codex/scheduler/leader-worker-dispatcher-state.json`
- New compact event log:
  - `LeaderWorkerDispatcherTickRecord`
  - `JsonlLeaderWorkerDispatcherEventLog`
  - default path `.codex/scheduler/leader-worker-dispatcher-events.jsonl`
- New decision model:
  - `LeaderWorkerDispatchDecision`
- New execution helpers:
  - `run_leader_worker_dispatcher_tick()`
  - `run_leader_worker_dispatcher_loop()`
  - `read_leader_worker_dispatcher_state()`
  - `write_leader_worker_dispatcher_state()`

CLI:

- Added `doc-based-coding scheduler leader-worker-dispatcher-tick`.
- Added `doc-based-coding scheduler leader-worker-dispatcher-loop`.

Behavior:

- `tick` recovers scheduler state from snapshot + event log, reads
  ExchangeArtifact records, runs the activation pass, emits only not-yet-emitted
  dispatch decisions, persists dispatcher state, and appends one JSONL tick
  record.
- `loop` repeats bounded ticks until `max_ticks` or no new dispatch decisions.
- Message duplication is handled by the embedded activation mailbox cursor;
  task/policy decision duplication is handled by dispatcher source keys.

The authority split explicitly reports:

- provider execution: false;
- scheduler state mutation: false;
- ExchangeArtifact store mutation: false;
- Local Work Trajectory mutation from runtime code: false.

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src\runtime\orchestration\leader_worker_dispatcher.py src\runtime\orchestration\__init__.py src\__main__.py tests\test_runtime_orchestration.py tests\test_cli.py
.\.venv\Scripts\python.exe -m pytest tests\test_runtime_orchestration.py -k "leader_worker_dispatcher" -q
.\.venv\Scripts\python.exe -m pytest tests\test_runtime_orchestration.py tests\test_cli.py -k "leader_worker_activation or leader_worker_dispatcher or scheduler_help_includes_exchange_artifact_admission" -q
```

Observed focused results:

```text
3 passed, 315 deselected
15 passed, 397 deselected
```

## Residual Risk After Close

This is still a dispatcher decision layer, not a live worker runtime manager.
It does not start processes, track process health, acknowledge worker delivery,
or recover interrupted provider sessions. Those belong to a later host-owned
runtime supervisor gate built on top of this dispatcher state/log contract.
