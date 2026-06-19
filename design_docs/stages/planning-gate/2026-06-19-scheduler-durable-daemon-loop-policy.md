# Planning Gate - Scheduler Durable Daemon Loop Policy

> Date: 2026-06-19
> Status: COMPLETED

## Trigger

`design_docs/scheduler-daemon-durable-queue-readiness-followup-direction-analysis.md`
recommends moving from the one-tick scheduler daemon-readiness contract to a
bounded repeated daemon loop policy.

## Problem

The scheduler now has a durable one-tick advancement contract:

```text
SchedulerDaemonTickRequest
SchedulerDaemonTickResult
SchedulerDaemonQueueSummary
run_scheduler_daemon_tick()
doc-based-coding scheduler tick
```

This proves that a single bounded fake-runtime scheduler tick can recover
durable state, advance ready work, persist scheduler state, and report queue
status. It does not yet define the repeated loop policy needed by a future
daemon or multi-agent orchestration controller.

The next slice should answer:

```text
Can a bounded scheduler daemon loop repeatedly call the one-tick contract,
stop for explicit durable policy reasons, and report enough aggregate state for
operators and future hosts?
```

## Scope

### Slice 1 - Contract

Define a small repeated-loop contract around the existing tick contract:

```text
SchedulerDaemonLoopRequest
SchedulerDaemonLoopResult
SchedulerDaemonLoopStopPolicy
SchedulerDaemonLoopIteration
run_scheduler_daemon_loop()
```

The contract should include:

1. explicit scheduler snapshot and event-log paths;
2. `max_ticks` as the outer loop bound;
3. per-tick `max_runs_per_tick`;
4. fake-runtime-only default behavior;
5. stop reasons:
   - `max_ticks_reached`;
   - `no_ready_tasks`;
   - `blocked_tasks`;
   - `runtime_failure_limit_reached`;
   - `cancelled`;
6. aggregate queue/readback clues:
   - total tick count;
   - total task-run count;
   - final queue summary;
   - per-iteration summaries;
   - scheduler event count;
   - authority split.

### Slice 2 - Runtime Implementation

Implement the loop as a thin wrapper over `run_scheduler_daemon_tick()`.

The implementation must:

1. call `run_scheduler_daemon_tick()` for each iteration;
2. reuse the tick-level scheduler recovery and persistence path;
3. stop before running when `max_ticks` is zero;
4. stop after a tick when no ready tasks remain;
5. stop after a tick when ready work is blocked;
6. stop when failed/blocked runtime-failure tasks reach the configured limit;
7. preserve the fake-runtime guard unless a Python caller injects a host-owned
   runtime registry.

### Slice 3 - CLI / Prompt Surface

Add a narrow CLI operator command:

```text
doc-based-coding scheduler daemon-loop
```

Minimum behavior:

1. require `--snapshot-path` and `--event-log-path`;
2. accept `--max-ticks`, `--max-runs-per-tick`,
   `--max-runtime-failures`, `--runtime-provider fake`, and `--timestamp`;
3. print `SchedulerDaemonLoopResult` JSON;
4. reject non-fake providers from CLI;
5. do not refresh scheduler projection automatically.

Prompt guidance should distinguish:

1. `scheduler tick`: one bounded tick;
2. `scheduler daemon-loop`: repeated bounded fake-runtime loop;
3. `scheduler project`: explicit projection refresh;
4. host-owned runners: future injected runtime path, still not a real-provider
   MCP surface.

## Non-Goals

This gate does not:

1. Start a background daemon process.
2. Add sleeps, polling, watch mode, or service lifecycle management.
3. Run real Qoder or other external providers.
4. Add MCP execution surface for the loop.
5. Add UI binding.
6. Add automatic scheduler projection refresh.
7. Mutate ExchangeArtifact lifecycle or admission ledger state.
8. Mutate `.codex/progress-graph/local-work-trajectory.json` from scheduler
   code.
9. Implement full retry, cancellation, or operator-control protocol beyond
   named stop reasons and readback fields.

## Acceptance Criteria

The gate may close when:

1. The daemon loop request/result/stop policy contract is documented and
   implemented.
2. The loop reuses `run_scheduler_daemon_tick()` internally.
3. Tests cover:
   - repeated advancement across dependent tasks;
   - max-tick stop;
   - no-ready stop;
   - blocked-task stop;
   - runtime-failure-limit stop or placeholder behavior;
   - CLI fake-runtime-only rejection.
4. CLI and prompt guidance distinguish tick, daemon-loop, and projection
   refresh.
5. Review/status docs record the preserved non-goals.

## Implementation Summary

Completed on 2026-06-19.

This slice added a bounded repeated scheduler daemon loop policy without
starting a background daemon process.

Implemented:

1. Runtime contract:
   - `SchedulerDaemonLoopStopPolicy`
   - `SchedulerDaemonLoopRequest`
   - `SchedulerDaemonLoopIteration`
   - `SchedulerDaemonLoopResult`
   - `run_scheduler_daemon_loop()`
2. Thin runtime implementation:
   - reuses `run_scheduler_daemon_tick()` for each iteration;
   - keeps zero-tick / cancelled pre-stop paths read-only;
   - stops on `max_ticks_reached`, `no_ready_tasks`, `blocked_tasks`, and
     `runtime_failure_limit_reached`;
   - preserves fake-runtime default behavior and Python-only injected runtime
     registry seams.
3. CLI operator surface:
   - `doc-based-coding scheduler daemon-loop`;
   - explicit `--snapshot-path` and `--event-log-path`;
   - `--max-ticks`, `--max-runs-per-tick`, `--max-runtime-failures`,
     `--runtime-provider fake`, and `--timestamp`;
   - JSON output with iteration summaries, final queue summary, stop reason,
     scheduler event count, and authority split.
4. Prompt guidance:
   - `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`;
   - bootstrap copy under `doc-loop-vibe-coding/assets/bootstrap/`.

## Validation

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_daemon_loop or scheduler_daemon_tick or summarize_scheduler_queue" tests/test_cli.py -k "scheduler_daemon_loop or scheduler_operator_workflow or scheduler_help"
9 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py
19 passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_mcp_admission.py tests/test_doc_loop_prompts.py
214 passed
```

## Non-Goals Preserved

This slice did not add:

1. Background daemon service.
2. Sleeps, polling, watch mode, or service lifecycle management.
3. Real Qoder or other external provider execution.
4. MCP execution surface for the loop.
5. UI binding.
6. Automatic scheduler projection refresh.
7. ExchangeArtifact lifecycle or admission ledger mutation.
8. Local Work Trajectory mutation from scheduler code.
9. Full retry/cancellation/operator-control protocol beyond named stop reasons
   and readback fields.
