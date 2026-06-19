# Planning Gate - Scheduler Daemon Durable Queue Readiness

> Date: 2026-06-19
> Status: COMPLETED

## Trigger

`design_docs/exchange-artifact-admission-state-projection-followup-direction-analysis.md`
recommends moving beyond stored-artifact admission mechanics into bounded
scheduler advancement.

## Problem

The scheduler line already has:

1. scheduler task submission into durable snapshot / event-log state;
2. explicit scheduler projection refresh;
3. one bounded fake-runtime run path through existing runtime / MCP smoke
   surfaces;
4. host-authorized runner seams for future injected runtime work.

However, the product contract is still framed mostly as smoke helpers. Before
larger multi-agent scheduling, the platform needs a daemon-ready read/write
contract that answers:

```text
Can one bounded scheduler tick advance queued work, report durable queue state,
and preserve host/provider authority boundaries?
```

This first slice should not start a real daemon process. It should define and
implement the minimal tick/readback product shape that a future daemon can
reuse.

## Scope

### Slice 1 - Contract

Define a small daemon-readiness contract around existing scheduler authority:

```text
SchedulerDaemonTickRequest
SchedulerDaemonTickResult
SchedulerDaemonQueueSummary
run_scheduler_daemon_tick()
```

The names may change if the existing runtime has a clearer local naming
pattern, but the semantics should remain:

1. Recover scheduler state from `snapshot_path` plus optional event logs.
2. Run at most one bounded scheduler drain using existing fake/injected runtime
   seams.
3. Write scheduler snapshot and append scheduler events only through existing
   scheduler persistence functions.
4. Return queue/readback clues:
   - task counts by state;
   - ready / blocked / running / completed / failed task ids;
   - dependency count;
   - scheduler event count when event log is provided;
   - run count;
   - stop reason;
   - whether state was written;
   - authority split.

### Slice 2 - Runtime Implementation

Prefer a thin wrapper over existing scheduler primitives:

1. Reuse `run_persisted_scheduler_once()` or
   `run_persisted_scheduler_once_with_wiring()`.
2. Reuse `SchedulerRunPolicy` for bounded tick knobs.
3. Keep default validation on `fake` runtime only unless a host-owned injected
   runtime registry is explicitly passed by Python code.
4. Do not duplicate scheduler recovery, event-log append, or projection logic.

### Slice 3 - Operator / Prompt Surface

This gate may add a CLI read/write surface only if it stays narrow and testable:

```text
doc-based-coding scheduler tick
```

Minimum CLI behavior, if added:

1. Require explicit `--snapshot-path` and `--event-log-path`.
2. Accept `--max-runs`, `--runtime-provider fake`, and `--timestamp`.
3. Print `SchedulerDaemonTickResult` JSON.
4. Reject non-fake runtime providers.
5. Do not refresh scheduler projection automatically.

Prompt guidance should distinguish:

1. `schedulerRunOnceAndProject`: MCP smoke that runs and refreshes projection.
2. `scheduler tick`: daemon-ready bounded advancement without automatic
   projection refresh.
3. Host-owned runners: future injected runtime path, still not a real-provider
   MCP surface.

## Non-Goals

This gate does not:

1. Start a long-running daemon process.
2. Add background scheduling loops.
3. Add retry/cancellation policy beyond placeholder/readback fields.
4. Run real Qoder or other external providers.
5. Broaden MCP provider execution beyond fake runtime.
6. Add UI binding.
7. Mutate ExchangeArtifact lifecycle or admission ledger state.
8. Refresh scheduler projection automatically from the daemon tick.
9. Mutate `.codex/progress-graph/local-work-trajectory.json` from scheduler
   code.

## Acceptance Criteria

The gate may close when:

1. A daemon-ready scheduler tick contract is documented and implemented.
2. The implementation reuses existing scheduler persistence/runtime primitives.
3. Bounded fake-runtime tick advances ready tasks and reports queue summary.
4. No-ready / blocked-task states return useful stop/readback clues.
5. Non-fake runtime execution is rejected unless the call path is explicitly
   host-owned and injected.
6. Tests cover runtime behavior, CLI or prompt surface if added, and authority
   boundaries.
7. Review/status docs record that real daemon loops, provider execution, UI
   binding, retry/cancellation policy, automatic projection refresh, and Local
   Work Trajectory mutation remain deferred.

## Implementation Summary

Completed on 2026-06-19.

This slice added a daemon-ready bounded scheduler tick contract without
starting a long-running daemon process.

Implemented:

1. Runtime contract:
   - `SchedulerDaemonTickRequest`
   - `SchedulerDaemonTickResult`
   - `SchedulerDaemonQueueSummary`
   - `summarize_scheduler_queue()`
   - `run_scheduler_daemon_tick()`
2. Thin runtime implementation:
   - reuses `run_persisted_scheduler_once()`;
   - reuses `SchedulerRunPolicy`;
   - reuses scheduler snapshot and event-log persistence;
   - defaults to fake runtime with shared-process sandbox;
   - rejects non-fake providers unless an explicit host-owned runtime registry
     is injected through Python.
3. CLI operator surface:
   - `doc-based-coding scheduler tick`
   - requires `--snapshot-path` and `--event-log-path`;
   - accepts `--max-runs`, `--runtime-provider fake`, and `--timestamp`;
   - prints `SchedulerDaemonTickResult` JSON;
   - rejects non-fake providers.
4. Prompt guidance:
   - `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
   - bootstrap copy under `doc-loop-vibe-coding/assets/bootstrap/`.

## Validation

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_daemon_tick or summarize_scheduler_queue"
4 passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "scheduler_tick or scheduler_operator_workflow or scheduler_help"
4 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py
19 passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_mcp_admission.py tests/test_doc_loop_prompts.py
207 passed
```

## Non-Goals Preserved

This slice did not add:

1. Long-running daemon process.
2. Background loop scheduling.
3. Retry/cancellation policy beyond current readback fields.
4. Real Qoder or other external provider execution.
5. Broader MCP provider execution.
6. UI binding.
7. ExchangeArtifact lifecycle or admission ledger mutation.
8. Automatic scheduler projection refresh from `scheduler tick`.
9. Local Work Trajectory mutation from scheduler code.
