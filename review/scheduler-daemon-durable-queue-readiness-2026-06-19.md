# Review - Scheduler Daemon Durable Queue Readiness

> Date: 2026-06-19
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-19-scheduler-daemon-durable-queue-readiness.md`

## Scope Reviewed

This slice promoted the existing one-shot scheduler runner into a
daemon-ready bounded tick/readback contract while preserving current scheduler
authority boundaries.

Implemented:

1. Runtime module:
   - `src/runtime/orchestration/scheduler_daemon.py`
   - `SchedulerDaemonTickRequest`
   - `SchedulerDaemonTickResult`
   - `SchedulerDaemonQueueSummary`
   - `run_scheduler_daemon_tick()`
   - `summarize_scheduler_queue()`
2. Runtime exports in `src/runtime/orchestration/__init__.py`.
3. CLI surface:
   - `doc-based-coding scheduler tick`
   - explicit snapshot/event-log paths
   - `--max-runs`
   - fake-runtime-only guard
4. Prompt guidance in scheduler smoke prompts.
5. Tests for bounded tick advancement, blocked queue reporting, non-fake
   provider rejection, queue summary grouping, CLI workflow, and prompt
   coverage.

## Evidence

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

## Behavioral Notes

`run_scheduler_daemon_tick()` is not a daemon loop. It is the reusable product
shape for one daemon tick:

1. Recover scheduler state from snapshot plus event log.
2. Run a bounded drain through existing scheduler primitives.
3. Persist scheduler snapshot/event-log changes.
4. Return queue summary and authority clues.

The default path creates a fake runtime registry and shared-process sandbox.
Non-fake provider execution is rejected unless Python callers explicitly pass
a host-owned runtime registry. The CLI intentionally exposes only the fake
runtime path.

`doc-based-coding scheduler tick` does not refresh
`.codex/progress-graph/scheduler-work-trajectory.json`; callers should use
`doc-based-coding scheduler project` when they want an explicit projection
refresh after one or more ticks.

## Authority Boundary

The authority split remains:

1. Scheduler snapshot and event log are scheduler authority.
2. Scheduler projection is a read-only view refreshed by a separate command.
3. Local Work Trajectory remains agent-owned.
4. ExchangeArtifact store and admission ledger are not touched by ticks.

## Explicit Non-Goals Preserved

This slice did not add:

1. Long-running background daemon.
2. Scheduler polling loop.
3. Retry or cancellation policy expansion.
4. Real Qoder/provider execution.
5. MCP real-provider execution.
6. UI binding.
7. ExchangeArtifact lifecycle mutation.
8. Automatic scheduler projection refresh.
9. Local Work Trajectory mutation from scheduler code.

## Follow-Up

The platform now has a stable one-tick contract suitable for future daemon and
multi-agent orchestration work. The strongest next backend candidate is a
durable daemon loop policy slice: lifecycle state, explicit stop policy,
operator readback, and recovery behavior around repeated ticks. Host evidence
binding and UI can use the tick result shape, but should remain separate gates.
