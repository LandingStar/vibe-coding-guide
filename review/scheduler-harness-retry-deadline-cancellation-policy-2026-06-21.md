# Review - Scheduler Harness Retry Deadline Cancellation Policy

> Date: 2026-06-21
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-21-scheduler-harness-retry-deadline-cancellation-policy.md`

## Scope Reviewed

This slice added a deterministic host-owned policy wrapper over the existing
bounded scheduler daemon harness.

Implemented:

1. `SchedulerDaemonHarnessPolicy`
2. `SchedulerDaemonHarnessPolicyAttempt`
3. `SchedulerDaemonHarnessPolicyResult`
4. `SchedulerDaemonHarnessPolicyStopReason`
5. `run_scheduler_daemon_harness_with_policy()`
6. Runtime exports in `src/runtime/orchestration/__init__.py`
7. CLI policy fields on `doc-based-coding scheduler lifecycle harness`
8. Focused runtime and CLI tests.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/scheduler_daemon_harness.py src/runtime/orchestration/__init__.py src/__main__.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_daemon_harness or scheduler_daemon_lifecycle"
15 passed, 230 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "scheduler_lifecycle_cli"
4 passed, 38 deselected
```

Wider related validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_daemon or scheduler_lifecycle or scheduler_loop_evidence"
32 passed, 213 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "scheduler_lifecycle or scheduler_daemon_loop or scheduler_help"
8 passed, 34 deselected
```

`git diff --check` passed for the touched files except expected CRLF warnings.

## Behavioral Notes

The policy wrapper:

1. returns `cancelled` before reading or mutating scheduler state when
   `cancelled=true`;
2. returns `deadline_exceeded` before execution when
   `now_epoch_seconds >= deadline_epoch_seconds`;
3. requires `deadline_epoch_seconds` to be paired with `now_epoch_seconds`;
4. retries only when the harness stop reason is explicitly listed in
   `retry_stop_reasons`;
5. stops with `max_attempts_reached` when a retryable stop reason persists
   through all allowed attempts;
6. otherwise stops with `harness_completed` and preserves the harness result in
   `attempts[].harness`.

CLI `scheduler lifecycle harness` now returns policy result JSON. The previous
direct harness result fields are available under `attempts[0].harness` for
executed attempts.

## Authority Boundary

The authority split remains explicit:

1. Policy authority is host-owned harness policy.
2. Harness authority remains the bounded host-managed process harness.
3. Lifecycle authority remains the scheduler daemon lifecycle control file.
4. Scheduler state authority remains scheduler snapshot and event log.
5. The wrapper does not start an OS service.
6. Scheduler projection refresh remains explicit and separate.
7. Local Work Trajectory remains agent-owned and is not mutated by scheduler
   runtime or CLI code.
8. ExchangeArtifact store and admission ledger are not touched.

## Explicit Non-Goals Preserved

This slice did not:

1. change `run_scheduler_daemon_harness()` semantics;
2. add sleeps, timers, filesystem watching, or real background behavior;
3. run live Qoder or any real provider;
4. add MCP surface;
5. add Host UX binding;
6. refresh scheduler projection automatically;
7. run or hide sandbox cleanup;
8. mutate ExchangeArtifact lifecycle or admission ledger state;
9. mutate Local Work Trajectory from scheduler runtime or CLI code;
10. define a broad production retry policy for every scheduler task state.

## Follow-Up

The backend harness now has bounded lifecycle execution and first-version
host-owned policy semantics. The next slice should either expose this policy
through MCP for Codex/operator use, bind the policy result into a host-managed
daemon supervisor contract, or return to agent home/context session binding.
