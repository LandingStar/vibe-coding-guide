# Codex Result Consumer Contract

> Date: 2026-06-26
> Status: IMPLEMENTED

## Trigger

`Codex Delivery Supervisor Loop` now invokes Codex for pending
leader-worker delivery records and writes durable delivery acknowledgement plus
runtime invocation audit. The remaining gap is immediately after a successful
`RuntimeRunResult`: the result is visible to the supervisor response, but it is
not yet stored as a durable `ExchangeArtifact` product and the scheduler event
log is not advanced to `task_completed`.

## Goal

Add one narrow result-consumer step that converts a successful Codex
`RuntimeRunResult` into durable scheduler-owned completion evidence:

1. store the returned `output_artifact` in the JSON-backed ExchangeArtifact
   store;
2. append one `task_completed` scheduler event referencing the exact artifact
   version;
3. let existing scheduler recovery replay advance the task to `complete`;
4. acknowledge delivery only after the result consumer succeeds.

## Scope

This gate includes:

1. a small runtime helper for successful Codex result consumption;
2. explicit artifact store path input;
3. append-only scheduler event log mutation;
4. supervisor integration that can opt into result consumption;
5. delivery failure marking when successful provider execution cannot be
   consumed durably;
6. CLI flags for enabling consumption and selecting the artifact store;
7. focused tests for successful consumption, replayed scheduler completion,
   and failed consumer acknowledgement.

## Non-goals

This gate does not:

1. implement a daemon or long-running supervisor;
2. write scheduler snapshots directly;
3. compact scheduler event logs;
4. handle permission-review result branches;
5. extract or apply patches from Codex output;
6. persist raw Codex transcripts;
7. resume interrupted Codex CLI sessions;
8. expose live provider execution through MCP;
9. mutate agent-owned Local Work Trajectory from runtime code.

## Contract

Authority remains split:

- delivery state/log records whether host delivery succeeded, failed, or was
  acknowledged;
- runtime invocation JSONL records provider attempt audit;
- ExchangeArtifact store records exact durable output artifacts;
- scheduler event log records task lifecycle advancement;
- scheduler snapshot remains the baseline contract authority and is not mutated
  by this consumer;
- scheduler recovery is the read boundary that combines snapshot plus event log
  into current task state.

The consumer is all-or-failed for the scheduler-facing result: if the artifact
cannot be stored or the scheduler completion event cannot be appended, the
delivery record is marked `failed` with `failure_kind=result_consumer_failed`
instead of being acknowledged. The provider run may have succeeded in that
case, but task completion is not claimed.

The supervisor's default behavior remains backward-compatible unless result
consumption is explicitly requested. When enabled, the ExchangeArtifact store
is required and delivery acknowledgement happens only after successful
artifact/event persistence.

## Validation Plan

- Focused runtime test for result consumer storing the output artifact and
  appending `task_completed`.
- Focused supervisor test for successful Codex delivery with result
  consumption and recovered scheduler task state `complete`.
- Focused supervisor test for durable consumer failure marking delivery
  `failed` without appending completion.
- Focused CLI help/argument test for the new consumption flags.
- `py_compile` for touched runtime/CLI/tests.
- Focused pytest selections covering Codex delivery and result consumer.
- Doc-loop validator and `git diff --check`.

## Closure Criteria

This gate closes when a bounded Codex delivery supervisor pass can optionally
turn a successful Codex run into durable ExchangeArtifact storage plus a
recoverable scheduler completion event, while preserving explicit authority
boundaries and failing closed when result persistence fails.

## Implemented Surface

Runtime:

- Added `src/runtime/orchestration/codex_result_consumer.py`.
- New request/result models:
  - `CodexResultConsumerRequest`
  - `CodexResultConsumerResult`
- New helper:
  - `consume_successful_codex_result()`

Supervisor integration:

- `CodexDeliverySupervisorRequest` now supports:
  - `artifact_store_path`
  - `consume_success_results`
  - `replace_existing_result_artifact`
- `run_codex_delivery_supervisor_once()` keeps old behavior by default.
- When `consume_success_results=True`, successful Codex output is stored in
  `JsonArtifactVersionStore`, a `task_completed` event is appended to
  `JsonlSchedulerEventLog`, and delivery acknowledgement is written only after
  both mutations succeed.
- If result consumption fails, the delivery record is marked `failed` with
  `failure_kind=result_consumer_failed`; scheduler completion is not claimed.

CLI:

- `doc-based-coding scheduler codex-delivery-supervisor-once` now exposes:
  - `--consume-success-results`
  - `--artifact-store-path PATH`
  - `--replace-existing-result-artifact`

Authority split:

- provider execution remains host-owned and audited;
- delivery state/log remains delivery authority;
- ExchangeArtifact store is mutated only when result consumption is enabled and
  succeeds;
- scheduler event log is mutated only when result consumption is enabled and
  succeeds;
- scheduler snapshot remains unmutated;
- MCP live-provider surface remains absent;
- runtime code still does not mutate agent-owned Local Work Trajectory.

## Validation

Passed:

```text
.\.venv\Scripts\python.exe -m py_compile src\runtime\orchestration\codex_result_consumer.py src\runtime\orchestration\leader_worker_codex_delivery.py src\runtime\orchestration\__init__.py src\__main__.py
.\.venv\Scripts\python.exe -m pytest tests\test_runtime_orchestration.py -k "codex_delivery_supervisor or codex_result_consumer" -q
.\.venv\Scripts\python.exe -m pytest tests\test_cli.py -k "codex_delivery_supervisor or scheduler_help_includes_exchange_artifact_admission" -q
.\.venv\Scripts\python.exe -m py_compile src\runtime\orchestration\codex_result_consumer.py src\runtime\orchestration\leader_worker_codex_delivery.py src\runtime\orchestration\__init__.py src\__main__.py tests\test_runtime_orchestration.py tests\test_cli.py
.\.venv\Scripts\python.exe -m pytest tests\test_runtime_orchestration.py -k "codex_delivery_supervisor or codex_result_consumer or leader_worker_delivery or leader_worker_dispatcher or runtime_invocation" -q
.\.venv\Scripts\python.exe -m pytest tests\test_cli.py -k "codex_delivery_supervisor or leader_worker_delivery or runtime_invocation or scheduler_help_includes_exchange_artifact_admission" -q
.\.venv\Scripts\python.exe doc-loop-vibe-coding\scripts\validate_doc_loop.py
git diff --check
```

Observed focused results:

```text
6 passed, 320 deselected
3 passed, 94 deselected
15 passed, 311 deselected
5 passed, 92 deselected
```

`validate_doc_loop.py` passed. `git diff --check` reported only existing
Windows line-ending warnings.

## Residual Risk After Close

This closes successful result consumption only. Permission-review branches,
runtime session resume, transcript compaction, daemon scheduling, patch
extraction/apply, scheduler snapshot compaction, and MCP live-provider
execution still require separate contract gates.
