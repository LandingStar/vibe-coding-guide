# Review - Host-Managed Scheduler Daemon Process Harness

> Date: 2026-06-21
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-21-host-managed-scheduler-daemon-process-harness.md`

## Scope Reviewed

This slice added a bounded host-managed scheduler daemon process harness over
the existing lifecycle control file and lifecycle-gated run-once helper.

Implemented:

1. `src/runtime/orchestration/scheduler_daemon_harness.py`
2. Runtime objects:
   - `SchedulerDaemonHarnessRequest`
   - `SchedulerDaemonHarnessCycle`
   - `SchedulerDaemonHarnessResult`
   - `SchedulerDaemonHarnessStopReason`
3. `run_scheduler_daemon_harness()`
4. CLI action:
   - `doc-based-coding scheduler lifecycle harness`
5. Focused runtime and CLI tests.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/scheduler_daemon_harness.py src/runtime/orchestration/__init__.py src/__main__.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_daemon_harness or scheduler_daemon_lifecycle"
11 passed, 230 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "scheduler_lifecycle_cli"
3 passed, 38 deselected
```

## Behavioral Notes

The harness:

1. requires a lifecycle control path;
2. runs bounded cycles only;
3. inspects lifecycle state before each cycle;
4. calls `run_scheduler_daemon_lifecycle_once()` for scheduler execution;
5. consumes `cancelling` lifecycle state through the existing run-once cancel
   path;
6. returns compact cycle summaries, total run count, stop reason, and authority
   split.

CLI `scheduler lifecycle harness` accepts existing run-once stop policy fields
plus `--max-cycles` and `--max-loop-failures`. It rejects non-fake runtime
providers at the generic CLI surface.

## Authority Boundary

The authority split remains:

1. Lifecycle authority is still the scheduler daemon lifecycle control file.
2. Scheduler state authority remains scheduler snapshot and event log.
3. The harness does not start an OS service.
4. Scheduler projection refresh remains explicit and separate.
5. Local Work Trajectory remains agent-owned and is not mutated by scheduler
   runtime or CLI code.
6. ExchangeArtifact store and admission ledger are not touched.

## Explicit Non-Goals Preserved

This slice did not add:

1. OS service / install-time daemon registration.
2. Sleep, filesystem watch, auto-start, or unbounded background behavior.
3. Live Qoder or real provider execution.
4. MCP surface.
5. Host UX binding.
6. Automatic scheduler projection refresh.
7. Hidden sandbox cleanup.
8. Retry/deadline/cancellation policy redesign.

## Follow-Up

The backend now has lifecycle control, CLI/MCP lifecycle operations, and a
bounded host-managed harness. The next backend slice should decide whether to
add an MCP surface for the harness, add scheduler retry/deadline policy over
the harness result, or bind agent home/session storage to harness-driven
runtime cycles.
