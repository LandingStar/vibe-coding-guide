# Credentialed Codex CLI E2E Smoke

> Date: 2026-06-26
> Status: IMPLEMENTED

## Trigger

The Codex delivery supervisor and result consumer are implemented as separate
host-owned steps. The next gap is an operator-safe proof that these steps can be
run together against one scheduler-owned Codex worker task without manually
threading dispatcher, delivery sync, Codex delivery, result consumption, and
recovery commands.

## Goal

Add one repeatable C1 smoke path for the target in
`design_docs/codex-cli-stable-worker-runtime-continuous-use-target.md`.

The smoke should:

1. optionally initialize a minimal scheduler-owned Codex worker fixture;
2. run one dispatcher tick;
3. sync leader-worker delivery records;
4. run one Codex delivery supervisor pass with successful result consumption;
5. recover scheduler state from snapshot plus event log;
6. report whether the target Codex task is complete.

## Scope

This gate includes:

1. a small runtime helper that composes existing dispatcher, delivery,
   supervisor, result-consumer, and recovery surfaces;
2. a CLI command for a host/operator C1 smoke;
3. fixture initialization for a single ready Codex task plus one waiting
   non-Codex task;
4. injected-client tests that prove durable acknowledgement, runtime audit,
   output artifact storage, and recovered completion;
5. CLI help/readiness-negative coverage.

## Non-goals

This gate does not:

1. implement the continuous bounded supervisor loop from C2;
2. implement interruption resume;
3. implement permission/review outcome consumption;
4. apply Codex patches to the source workspace;
5. expose live Codex execution through MCP;
6. mutate runtime-owned Local Work Trajectory;
7. add true process-level parallelism.

## Contract

The helper is a host/operator smoke, not a new scheduler authority. It preserves
the existing split:

- scheduler snapshot remains the baseline task contract;
- scheduler event log records completion only through the result consumer;
- dispatcher state/log records activation decisions;
- delivery state/log records pending and acknowledged delivery;
- runtime invocation log records compact Codex attempt audit;
- ExchangeArtifact store records successful Codex output artifacts;
- Local Work Trajectory is not mutated by runtime code.

When host readiness is requested and Codex CLI is not ready, the smoke fails
closed before mutating scheduler or delivery state.

## Validation Plan

- Focused runtime test for helper with an injected Codex client.
- Focused runtime test for readiness-negative fail-closed behavior.
- Focused CLI help test.
- Focused CLI readiness-negative smoke test with a missing executable.
- `py_compile` for touched files.
- Focused pytest selections for `codex_delivery_smoke`, existing Codex
  delivery, and CLI Codex smoke paths.
- Doc-loop validator and `git diff --check`.

## Closure Criteria

This gate closes when a single command/helper can run the C1 path end to end
and produce compact evidence that one scheduler-owned Codex task reached
recovered `complete` state with durable runtime audit, delivery acknowledgement,
stored output artifact, and scheduler completion event.

## Implemented Surface

Runtime:

- Added `src/runtime/orchestration/codex_delivery_smoke.py`.
- New request/result models:
  - `CodexDeliveryE2ESmokeRequest`
  - `CodexDeliveryE2ESmokeFixtureResult`
  - `CodexDeliveryE2ESmokeResult`
- New helpers:
  - `run_codex_delivery_e2e_smoke()`
  - `run_codex_delivery_e2e_smoke_with_process_client()`

Behavior:

- Optional fixture initialization writes a minimal scheduler snapshot with one
  ready Codex task and one waiting non-Codex control task.
- With host readiness required, the smoke checks Codex CLI readiness before
  dispatcher/delivery/runtime mutation and fails closed when the CLI is
  unavailable.
- The smoke then runs one dispatcher tick, syncs delivery records, runs one
  Codex delivery supervisor pass with `consume_success_results=True`, and
  recovers scheduler state.
- Successful output is stored in `JsonArtifactVersionStore`; the scheduler
  event log receives `task_completed`; delivery is acknowledged only after
  durable result consumption succeeds.

CLI:

- Added `doc-based-coding scheduler codex-delivery-e2e-smoke`.
- The command supports explicit paths plus `--initialize-fixture`,
  `--replace-existing-fixture`, Codex process options, runtime retry options,
  and result-artifact replacement.

Authority split:

- scheduler snapshot is mutated only for explicit fixture initialization;
- scheduler completion comes only from event-log replay;
- dispatcher, delivery, runtime audit, and ExchangeArtifact mutations remain in
  their existing stores;
- MCP live-provider surface remains absent;
- runtime code does not mutate agent-owned Local Work Trajectory;
- raw transcripts are not persisted.

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src\runtime\orchestration\codex_delivery_smoke.py src\runtime\orchestration\__init__.py src\__main__.py tests\test_runtime_orchestration.py tests\test_cli.py
.\.venv\Scripts\python.exe -m pytest tests\test_runtime_orchestration.py -k "codex_delivery_e2e_smoke" -q
.\.venv\Scripts\python.exe -m pytest tests\test_cli.py -k "codex_delivery_e2e_smoke" -q
.\.venv\Scripts\python.exe -m pytest tests\test_runtime_orchestration.py -k "codex_delivery or codex_result_consumer or leader_worker_delivery or leader_worker_dispatcher or runtime_invocation" -q
.\.venv\Scripts\python.exe -m pytest tests\test_cli.py -k "codex_delivery or leader_worker_delivery or runtime_invocation or scheduler_help_includes_exchange_artifact_admission" -q
```

Observed focused results:

```text
2 passed, 326 deselected
2 passed, 97 deselected
17 passed, 311 deselected
7 passed, 92 deselected
```

## Residual Risk After Close

This closes the C1 single-task smoke only. It still does not implement the C2
bounded repeated supervisor loop, permission/review outcome consumer,
interruption resume, multi-lane fixture acceptance, process-level parallelism,
or source workspace patch review/apply integration.
