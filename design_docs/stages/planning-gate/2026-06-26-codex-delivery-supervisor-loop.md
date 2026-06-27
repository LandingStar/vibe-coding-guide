# Codex Delivery Supervisor Loop

> Date: 2026-06-26
> Status: IMPLEMENTED

## Trigger

The leader-worker dispatcher and host-owned delivery acknowledgement layers now
persist which activation decisions should be delivered to a worker runtime, but
Codex is not yet connected to that recoverable delivery loop. Existing Codex
support is available as a host-owned runtime adapter and CLI process client, and
runtime invocation audit/retry is already available.

## Goal

Add one narrow host-owned Codex delivery supervisor step that can consume
pending `LeaderWorkerDeliveryRecord` entries for ready Codex worker tasks,
invoke Codex through the existing host-authorized runtime adapter seam, and
write delivery acknowledgement plus compact runtime invocation audit.

## Scope

This gate includes:

1. a runtime helper that reads delivery state plus recovered scheduler state;
2. selection of pending delivery records with
   `event_kind=task_ready` and `next_action=run_agent`;
3. Codex-only task filtering using the scheduler task's runtime provider;
4. host-owned Codex runtime registry wiring with an explicit process-spawn
   permission grant;
5. runtime invocation audit/retry around the Codex client seam;
6. delivery acknowledgement to `acknowledged` on successful Codex completion;
7. delivery acknowledgement to `failed` on verified delivery/runtime failure;
8. a CLI command for one bounded supervisor pass;
9. focused tracked runtime and CLI tests with injected/failing Codex clients.

## Non-goals

This gate does not:

1. implement a background daemon;
2. mutate scheduler snapshot/event log or mark scheduler tasks complete;
3. publish result artifacts into the durable ExchangeArtifact store;
4. allocate git worktree sandboxes or agent homes;
5. resume interrupted Codex CLI sessions;
6. watch heartbeats or compact raw transcripts;
7. expose live Codex provider execution through MCP;
8. mutate agent-owned Local Work Trajectory from runtime code.

## Contract

Authority remains split:

- scheduler snapshot/event log remains task lifecycle authority;
- dispatcher state/log remains activation decision authority;
- delivery state/log records host delivery acknowledgement;
- runtime invocation JSONL records compact Codex invocation attempts;
- Codex process construction remains host-owned and requires an explicit
  process-spawn permission grant;
- Local Work Trajectory remains agent-owned and is not mutated by runtime code.

The first implementation intentionally does not call `run_ready_task()`, because
that would mutate scheduler state. It invokes `runtime.start_session()` and
`runtime.run_task()` directly over `task_to_runtime_spec(task)` and writes only
delivery/audit state. A later gate must explicitly decide how Codex runtime
results become scheduler completion, review, or patch products.

## Validation Plan

- Focused runtime tests for successful Codex delivery acknowledgement.
- Focused runtime tests for non-Codex records being skipped without failure.
- Focused runtime tests for failed Codex invocation writing failed delivery and
  failed runtime invocation audit.
- Focused CLI test for missing Codex executable producing structured failure
  JSON and failed delivery state.
- `py_compile` for touched runtime/CLI/tests.
- Focused pytest selections for `codex_delivery`, delivery, and runtime
  invocation surfaces.
- `doc-loop` validator and `git diff --check`.

## Closure Criteria

This gate closes when a host can run one bounded Codex delivery supervisor pass
over existing pending delivery records and obtain durable delivery/audit
evidence without claiming scheduler completion, daemon recovery, MCP live
provider execution, or Local Work Trajectory mutation from runtime code.

## Implemented Surface

Runtime:

- Added `src/runtime/orchestration/leader_worker_codex_delivery.py`.
- New request/result models:
  - `CodexDeliverySupervisorRequest`
  - `CodexDeliverySupervisorRecord`
  - `CodexDeliverySupervisorResult`
- New helper:
  - `run_codex_delivery_supervisor_once()`

Behavior:

- Reads existing leader-worker delivery state.
- Recovers scheduler state from snapshot plus event log.
- Selects pending delivery records where `event_kind=task_ready` and
  `next_action=run_agent`.
- Executes only scheduler tasks whose `agent.runtime_provider` is `codex`.
- Skips non-Codex or non-task delivery records without mutating them.
- Invokes Codex through host-authorized adapter wiring and explicit
  process-spawn grant.
- Wraps the Codex client seam in runtime invocation audit/retry.
- Marks successful Codex delivery records `acknowledged`.
- Marks Codex delivery/runtime failures `failed`.

CLI:

- Added `doc-based-coding scheduler codex-delivery-supervisor-once`.

Authority split:

- provider execution: true only when at least one Codex delivery was attempted;
- delivery state/log mutation: true only for attempted Codex deliveries;
- runtime invocation log mutation: true only for attempted audited invocations;
- scheduler state/event-log mutation: false;
- ExchangeArtifact store mutation: false;
- MCP live provider surface: false;
- runtime code Local Work Trajectory mutation: false;
- raw transcript persistence: false.

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src\runtime\orchestration\leader_worker_codex_delivery.py src\runtime\orchestration\__init__.py src\__main__.py tests\test_runtime_orchestration.py tests\test_cli.py
.\.venv\Scripts\python.exe -m pytest tests\test_runtime_orchestration.py -k "codex_delivery" -q
.\.venv\Scripts\python.exe -m pytest tests\test_cli.py -k "codex_delivery or leader_worker_delivery or runtime_invocation or scheduler_help_includes_exchange_artifact_admission" -q
.\.venv\Scripts\python.exe -m pytest tests\test_runtime_orchestration.py -k "codex_delivery or leader_worker_delivery or leader_worker_dispatcher or runtime_invocation" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding\scripts\validate_doc_loop.py
git diff --check
```

Observed focused results:

```text
3 passed, 320 deselected
4 passed, 92 deselected
12 passed, 311 deselected
```

`git diff --check` reported only existing Windows line-ending warnings.

## Residual Risk After Close

This is still a bounded host-owned supervisor step, not a full runtime daemon.
It does not mutate scheduler task completion, persist result artifacts into the
durable ExchangeArtifact store, resume interrupted Codex sessions, watch
heartbeats, allocate agent homes, or compact long-running runtime transcripts.
Those require later gates.
