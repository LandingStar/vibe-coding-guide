# Review - Host-Managed Daemon Supervisor Contract

> Date: 2026-06-21
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-21-host-managed-daemon-supervisor-contract.md`

## Scope Reviewed

This slice added the first runtime-only host-managed supervisor contract over
the policy-controlled scheduler daemon harness.

Implemented:

1. `src/runtime/orchestration/scheduler_daemon_supervisor.py`
2. Supervisor request/status/result contract:
   - `SchedulerDaemonSupervisorRequest`
   - `SchedulerDaemonSupervisorStatus`
   - `SchedulerDaemonSupervisorResult`
   - `SchedulerDaemonSupervisorStopReason`
3. Runtime entry point:
   - `run_scheduler_daemon_supervisor_step()`
4. Orchestration exports.
5. Focused tests in `tests/test_runtime_orchestration.py`.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/scheduler_daemon_supervisor.py src/runtime/orchestration/__init__.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_daemon_supervisor"
4 passed, 245 deselected
```

Wider related validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_daemon_supervisor or scheduler_daemon_harness or scheduler_daemon_lifecycle"
19 passed, 230 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py
249 passed
```

## Behavioral Notes

The supervisor step:

1. requires `supervisor_id`;
2. carries host/session/run/requester/cancellation metadata;
3. performs cancelled/deadline preflight before lifecycle control readback;
4. delegates execution to `run_scheduler_daemon_harness_with_policy()`;
5. reads lifecycle status before and after attempted harness execution;
6. reports queue summary when scheduler snapshot recovery is available;
7. reports readback errors without hiding the supervisor result;
8. exposes authority facts showing no OS service, background process, timers,
   watchers, projection refresh, cleanup, ExchangeArtifact mutation, admission
   ledger mutation, or Local Work Trajectory mutation.

## Authority Boundary

The new authority split is:

1. Supervisor authority is host-owned daemon supervisor contract.
2. Policy authority remains host-owned harness policy.
3. Harness authority remains bounded process harness.
4. Lifecycle authority remains scheduler daemon lifecycle control file.
5. Scheduler state authority remains scheduler snapshot and event log.

## Explicit Non-Goals Preserved

This slice did not:

1. add CLI, MCP, or Host UX surface;
2. run live Qoder or any real provider;
3. start an OS service, watcher, timer, or unbounded daemon;
4. change harness or policy semantics;
5. refresh scheduler projection automatically;
6. execute or hide cleanup;
7. mutate ExchangeArtifact lifecycle or admission ledger state;
8. mutate Local Work Trajectory from scheduler runtime code;
9. bind agent home, scratch retention, or context-session storage lifecycle.

## Follow-Up

The runtime contract is now stable enough to expose through operator surfaces.
The next narrow backend slice should either add a CLI/MCP invocation surface for
the supervisor step, bind agent home/context sessions over supervisor runs, or
dogfood the supervisor through deterministic scheduler lifecycle workflow.
