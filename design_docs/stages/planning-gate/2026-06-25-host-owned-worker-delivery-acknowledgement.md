# Host-Owned Worker Delivery Acknowledgement

> Date: 2026-06-25
> Status: IMPLEMENTED

## Trigger

`LeaderWorkerDispatcherTickRecord` now provides recoverable dispatch decisions,
but a host restart still lacks a durable record of which decisions were handed
to a runtime owner, acknowledged by a worker/session, or failed before worker
execution could proceed. Re-running the dispatcher can suppress duplicate
decisions, but that does not prove host delivery.

## Goal

Add a narrow host-owned delivery acknowledgement layer over leader-worker
dispatcher decisions. The layer should persist per-dispatch delivery state and
an append-only audit log so a future runtime supervisor can recover which
dispatch decisions are still pending, already delivered, acknowledged, or
failed.

## Scope

This gate includes:

1. a `LeaderWorkerDeliveryState` JSON contract with one record per dispatcher
   decision source key;
2. a JSONL `LeaderWorkerDeliveryEventRecord` audit log;
3. a deterministic sync helper that reads the dispatcher event log and creates
   missing pending delivery records without duplicating existing records;
4. an acknowledgement helper that marks one known delivery as delivered,
   acknowledged, or failed with compact host/runtime identifiers;
5. a readback helper for delivery counts and latest records;
6. CLI surfaces for sync, ack, and inspect operations;
7. focused tracked tests for sync idempotence, ack recovery, and CLI readback.

## Non-goals

This gate does not:

1. start Codex/Qoder/opencode providers;
2. implement process/session resume;
3. mutate scheduler snapshot/event log;
4. mutate ExchangeArtifact store or admission ledger;
5. mutate dispatcher state/event log;
6. allocate agent homes, sandboxes, or OS processes;
7. implement a background daemon or Web UI;
8. mutate agent-owned Local Work Trajectory from runtime code.

## Contract

Authority remains split:

- scheduler snapshot/event log remains task lifecycle authority;
- ExchangeArtifact store remains message/history authority;
- dispatcher state/log remains activation decision authority;
- delivery state owns host delivery acknowledgement status;
- delivery JSONL log owns delivery audit history;
- provider execution and process recovery remain outside this slice.

The delivery state is keyed by dispatcher decision `source_key`. A dispatcher
decision can therefore be synced repeatedly after host restart without creating
duplicate delivery records. Delivery acknowledgement may be repeated safely:
the state update is deterministic, and the audit log records whether the
request changed state.

## Validation Plan

- Focused runtime tests for dispatcher-log sync and repeated sync de-dup.
- Focused runtime tests for delivery acknowledgement and readback.
- Focused CLI test for sync/ack/inspect.
- `py_compile` for touched runtime/CLI/tests.
- Focused pytest selection for leader-worker delivery surfaces.
- `doc-loop` validator and `git diff --check`.
- Compact Checklist writeback after close.

## Closure Criteria

This gate closes when dispatcher decisions can be durably synced into a
host-owned delivery acknowledgement state and acknowledged through tested
runtime/CLI surfaces without claiming provider execution or background
supervision.

## Implemented Surface

Runtime:

- Added `src/runtime/orchestration/leader_worker_delivery.py`.
- New durable state:
  - `LeaderWorkerDeliveryState`
  - `LeaderWorkerDeliveryRecord`
  - default path `.codex/scheduler/leader-worker-delivery-state.json`
- New compact event log:
  - `LeaderWorkerDeliveryEventRecord`
  - `JsonlLeaderWorkerDeliveryEventLog`
  - default path `.codex/scheduler/leader-worker-delivery-events.jsonl`
- New sync/read/write helpers:
  - `sync_leader_worker_delivery_from_dispatch_log()`
  - `acknowledge_leader_worker_delivery()`
  - `inspect_leader_worker_delivery_state()`
  - `read_leader_worker_delivery_state()`
  - `write_leader_worker_delivery_state()`

CLI:

- Added `doc-based-coding scheduler leader-worker-delivery-sync`.
- Added `doc-based-coding scheduler leader-worker-delivery-ack`.
- Added `doc-based-coding scheduler inspect-leader-worker-delivery`.

Behavior:

- `sync` reads the existing dispatcher JSONL event log and creates one pending
  delivery record per not-yet-known dispatcher decision source key.
- repeated sync is idempotent over the same dispatcher log;
- `ack` updates one known delivery record by source key or delivery record id
  to `delivered`, `acknowledged`, or `failed`;
- `inspect` reports compact counts and latest delivery records without
  mutation.

The authority split explicitly reports:

- provider execution: false;
- scheduler state mutation: false;
- ExchangeArtifact store mutation: false;
- dispatcher state mutation: false;
- Local Work Trajectory mutation from runtime code: false.

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src\runtime\orchestration\leader_worker_delivery.py src\runtime\orchestration\leader_worker_dispatcher.py src\runtime\orchestration\__init__.py src\__main__.py tests\test_runtime_orchestration.py tests\test_cli.py
.\.venv\Scripts\python.exe -m pytest tests\test_runtime_orchestration.py -k "leader_worker_delivery" -q
.\.venv\Scripts\python.exe -m pytest tests\test_runtime_orchestration.py -k "leader_worker_activation or leader_worker_dispatcher or leader_worker_delivery or runtime_invocation" -q
.\.venv\Scripts\python.exe -m pytest tests\test_cli.py -k "leader_worker_dispatcher or leader_worker_delivery or runtime_invocation or scheduler_help_includes_exchange_artifact_admission" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding\scripts\validate_doc_loop.py
git diff --check
```

Observed focused results:

```text
2 passed, 318 deselected
12 passed, 308 deselected
5 passed, 90 deselected
```

`git diff --check` reported only Windows line-ending warnings.

## Residual Risk After Close

This is a host delivery acknowledgement layer, not a live runtime supervisor.
It does not start worker processes, resume interrupted CLI sessions, watch
heartbeats, or compact runtime transcripts. Those belong to later host-owned
runtime supervisor and monitoring gates built on top of delivery state plus
runtime invocation audit.
