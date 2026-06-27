# Bounded Codex Supervisor Loop Binding

> Date: 2026-06-26
> Status: IMPLEMENTED

## Trigger

C1 proved that a single host/operator command can run one scheduler-owned Codex
task through dispatcher, delivery sync, Codex delivery, result consumption, and
recovery. The remaining normal-progress gap is that the operator still has only
a one-delivery smoke, not a bounded repeated loop that can keep activating and
delivering ready Codex work until a clear stop condition.

## Goal

Implement Gate C2 from
`design_docs/codex-cli-stable-worker-runtime-continuous-use-target.md`: one
host-owned helper/command that repeatedly chains:

```text
recover scheduler state
-> dispatcher tick
-> delivery sync
-> Codex delivery with result consumption
-> recover scheduler state
-> repeat until bounded stop
```

## Scope

This gate includes:

1. a runtime helper for bounded repeated Codex progress;
2. explicit bounds for ticks, Codex deliveries, and runtime failures;
3. compact stop reasons and count summaries;
4. support for existing scheduler/delivery/artifact state paths;
5. optional fixture initialization for a small multi-task Codex chain;
6. a scheduler CLI command for host/operator use;
7. focused tests using injected Codex clients.

## Non-goals

This gate does not:

1. implement a background daemon;
2. implement live session resume after interruption;
3. implement permission/review outcome consumption;
4. run true process-level parallelism;
5. expose live Codex execution through MCP;
6. apply worker patches to the source workspace;
7. mutate agent-owned Local Work Trajectory from runtime code.

## Contract

The loop is bounded and host-owned. It does not replace scheduler authority:

- scheduler snapshot remains the baseline task contract;
- scheduler event log records task completion via result consumption;
- dispatcher state/log records activation decisions and de-duplication;
- delivery state/log records pending/acknowledged/failed delivery;
- runtime invocation log records compact Codex attempts and retries;
- ExchangeArtifact store records durable output artifacts;
- final state is read by scheduler recovery.

The helper must return a compact JSON-compatible summary including:

1. stop reason and stop detail;
2. tick count, attempted/completed/failed/skipped counts;
3. pending delivery counts;
4. recovered task state counts;
5. authority split.

## Validation Plan

- Focused runtime test for a two-task Codex chain completing over repeated
  loop iterations.
- Focused runtime test for max-deliveries stop.
- Focused CLI help/readiness-negative coverage.
- Existing C1/Codex delivery/result-consumer regression.
- `py_compile`, doc-loop validator, and `git diff --check`.

## Closure Criteria

This gate closes when one bounded host/operator command can make repeated
Codex progress across more than one ready-after-recovery task without manual
step-by-step dispatcher/delivery/supervisor commands, while preserving all
existing authority boundaries and returning explicit stop/readback evidence.

## Implemented Surface

Runtime:

- Extended `src/runtime/orchestration/codex_delivery_smoke.py`.
- New request/result models:
  - `CodexDeliveryBoundedLoopRequest`
  - `CodexDeliveryBoundedLoopIteration`
  - `CodexDeliveryBoundedLoopResult`
- New helpers:
  - `run_bounded_codex_delivery_supervisor_loop()`
  - `run_bounded_codex_delivery_supervisor_loop_with_process_client()`

Behavior:

- Performs credential-safe Codex readiness before fixture or scheduler/delivery
  mutation when readiness is required.
- Optionally initializes a small fixture containing a ready Codex task, a
  dependent Codex follow-up task, and a waiting non-Codex control task.
- Each iteration recovers scheduler state, calls `mark_ready_tasks()` to append
  readiness/waiting events for newly admissible work, persists dispatcher
  decisions, syncs delivery records, runs Codex delivery with result
  consumption, and recovers again.
- Stops with explicit reasons including `all_targets_complete`,
  `max_ticks_reached`, `max_deliveries_reached`,
  `max_runtime_failures_reached`, `no_progress`, and `codex_not_ready`.

CLI:

- Added `doc-based-coding scheduler codex-delivery-supervisor-loop`.
- The command exposes explicit bounds:
  - `--max-ticks`
  - `--max-deliveries`
  - `--max-runtime-failures`
- It reuses the C1 path arguments for state paths, fixture initialization, Codex
  process options, runtime retry options, and result-artifact replacement.

Authority split:

- scheduler snapshot is mutated only for explicit fixture initialization;
- scheduler lifecycle advancement is append-only event-log based;
- dispatcher, delivery, runtime audit, and ExchangeArtifact stores keep their
  existing authority boundaries;
- MCP live-provider surface remains absent;
- runtime code does not mutate agent-owned Local Work Trajectory;
- raw transcripts are not persisted.

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src\__main__.py src\runtime\orchestration\codex_delivery_smoke.py src\runtime\orchestration\__init__.py tests\test_runtime_orchestration.py tests\test_cli.py
.\.venv\Scripts\python.exe -m pytest tests\test_runtime_orchestration.py -k "codex_delivery_e2e_smoke or bounded_codex_delivery_supervisor_loop" -q
.\.venv\Scripts\python.exe -m pytest tests\test_cli.py -k "codex_delivery_e2e_smoke or codex_delivery_supervisor_loop" -q
.\.venv\Scripts\python.exe -m pytest tests\test_runtime_orchestration.py -k "codex_delivery or codex_result_consumer or leader_worker_delivery or leader_worker_dispatcher or runtime_invocation" -q
.\.venv\Scripts\python.exe -m pytest tests\test_cli.py -k "codex_delivery or leader_worker_delivery or runtime_invocation or scheduler_help_includes_exchange_artifact_admission" -q
```

Observed focused results:

```text
4 passed, 326 deselected
4 passed, 97 deselected
19 passed, 311 deselected
9 passed, 92 deselected
```

## Residual Risk After Close

This closes bounded normal progress only. It does not yet implement
permission/review outcome consumption, interruption/in-progress resume,
runtime invocation log compaction policy binding for the loop, source workspace
patch review/apply integration, MCP live-provider execution, or true
process-level parallelism.
