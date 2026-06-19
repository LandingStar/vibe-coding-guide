# Review - Scheduler Durable Daemon Loop Policy

> Date: 2026-06-19
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-19-scheduler-durable-daemon-loop-policy.md`

## Scope Reviewed

This slice promoted the daemon-ready one-tick scheduler contract into a bounded
repeated loop policy while preserving current provider and projection authority
boundaries.

Implemented:

1. Runtime contract:
   - `SchedulerDaemonLoopStopPolicy`
   - `SchedulerDaemonLoopRequest`
   - `SchedulerDaemonLoopIteration`
   - `SchedulerDaemonLoopResult`
   - `run_scheduler_daemon_loop()`
2. Runtime exports in `src/runtime/orchestration/__init__.py`.
3. CLI surface:
   - `doc-based-coding scheduler daemon-loop`
   - explicit scheduler snapshot/event-log paths
   - `--max-ticks`
   - `--max-runs-per-tick`
   - `--max-runtime-failures`
   - fake-runtime-only guard
4. Prompt guidance in scheduler smoke prompts.
5. Tests for repeated dependent advancement, max-tick stop, blocked-task stop,
   runtime-failure-limit stop, zero-tick read-only behavior, CLI workflow, and
   prompt coverage.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_daemon_loop or scheduler_daemon_tick or summarize_scheduler_queue" tests/test_cli.py -k "scheduler_daemon_loop or scheduler_operator_workflow or scheduler_help"
9 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py
19 passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_mcp_admission.py tests/test_doc_loop_prompts.py
214 passed
```

## Behavioral Notes

`run_scheduler_daemon_loop()` is still not a background daemon. It is the first
bounded repeated-loop product contract:

1. Apply an explicit outer stop policy.
2. Call `run_scheduler_daemon_tick()` for each iteration.
3. Reuse tick-level durable recovery, snapshot write, event-log append, and
   fake-runtime guard.
4. Return aggregate `tick_count`, `total_run_count`, `stop_reason`,
   per-iteration summaries, final queue summary, scheduler event count, and
   authority clues.

The zero-tick and cancelled pre-stop paths recover scheduler state read-only and
do not mark proposed tasks ready or write event logs.

## Authority Boundary

The authority split remains:

1. Scheduler snapshot and scheduler event log are scheduler authority.
2. Scheduler projection remains explicitly refreshed by
   `doc-based-coding scheduler project`.
3. CLI loop execution remains fake-runtime-only.
4. Non-fake runtime providers remain Python-only through explicit host-owned
   runtime registry injection.
5. Local Work Trajectory remains agent-owned.
6. ExchangeArtifact store and admission ledger are not touched by loop runs.

## Explicit Non-Goals Preserved

This slice did not add:

1. Long-running daemon service.
2. Scheduler polling/watch mode.
3. Real Qoder/provider execution.
4. MCP execution tool for the loop.
5. UI binding.
6. Automatic scheduler projection refresh.
7. ExchangeArtifact lifecycle mutation.
8. Admission ledger mutation.
9. Local Work Trajectory mutation from scheduler code.
10. Full retry/cancellation/operator-control protocol.

## Follow-Up

The scheduler now has a bounded repeated loop suitable for host/operator
integration. The strongest next backend candidate is host evidence binding for
scheduler loop results, so operators and future UI surfaces can inspect durable
loop runs without binding to raw scheduler internals. Host-injected runtime loop
execution should stay separate because it changes provider authority.

