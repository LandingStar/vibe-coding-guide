# Planning Gate - Scheduler Harness Retry Deadline Cancellation Policy

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/host-managed-scheduler-daemon-process-harness-followup-direction-analysis.md`
recommends adding retry / deadline / cancellation policy over the newly
completed host-managed scheduler daemon harness.

## Problem

The harness now exposes bounded cycle results and stop reasons, but callers do
not yet have a policy object that explains:

1. when a harness run should be cancelled before execution;
2. when a deadline should prevent execution;
3. when retry is permitted over retryable stop reasons;
4. why the policy stopped.

This slice should answer:

```text
Can the project add a deterministic policy wrapper over existing harness
results without changing harness execution semantics or adding MCP/Host UX?
```

## Scope

### Slice 1 - Runtime Policy Contract

Add first-version policy objects to the harness runtime module:

```text
SchedulerDaemonHarnessPolicy
SchedulerDaemonHarnessPolicyAttempt
SchedulerDaemonHarnessPolicyResult
```

The first policy should support:

1. explicit `cancelled` preflight stop;
2. `deadline_epoch_seconds` compared with caller-provided
   `now_epoch_seconds`;
3. `max_attempts`;
4. explicit `retry_stop_reasons`;
5. JSON result shape with attempts, final stop reason, policy stop reason, and
   authority split.

### Slice 2 - CLI Policy Fields

Extend the existing CLI action:

```text
doc-based-coding scheduler lifecycle harness
```

with policy fields:

```text
--policy-cancelled
--deadline-epoch-seconds N
--now-epoch-seconds N
--max-attempts N
--retry-stop-reasons REASON[,REASON...]
```

The CLI should remain fake-runtime only, return JSON, and not add MCP/Host UX.

### Slice 3 - Focused Tests

Add focused tests for:

1. cancelled preflight returns without reading/mutating scheduler state;
2. deadline preflight returns without scheduler mutation;
3. retry stops after `max_attempts` for a retryable stop reason;
4. non-retryable success-like stop reason does not retry;
5. CLI policy fields route to the same policy result shape.

## Non-Goals

This gate does not:

1. Change existing `run_scheduler_daemon_harness()` semantics.
2. Add sleeps, timers, filesystem watching, or real background behavior.
3. Run live Qoder or any real provider.
4. Add MCP surface.
5. Add Host UX binding.
6. Refresh scheduler projection automatically.
7. Run or hide sandbox cleanup.
8. Mutate ExchangeArtifact lifecycle or admission ledger state.
9. Mutate Local Work Trajectory from scheduler runtime or CLI code.
10. Define broad production retry policy for every scheduler task state.

## Acceptance Criteria

The gate may close when:

1. Policy request/result objects exist and are exported.
2. Policy preflight handles cancel and deadline deterministically.
3. Retry behavior is driven by explicit stop reasons and max attempts.
4. CLI `scheduler lifecycle harness` can return policy result JSON.
5. Focused runtime and CLI tests pass.
6. Review/status docs record validation and preserved non-goals.

## Completion Summary

Completed on 2026-06-21.

Implemented:

1. `SchedulerDaemonHarnessPolicy`
2. `SchedulerDaemonHarnessPolicyAttempt`
3. `SchedulerDaemonHarnessPolicyResult`
4. `SchedulerDaemonHarnessPolicyStopReason`
5. `run_scheduler_daemon_harness_with_policy()`
6. CLI policy fields on `doc-based-coding scheduler lifecycle harness`

The policy wrapper preserves existing `run_scheduler_daemon_harness()`
execution semantics and adds deterministic host-owned preflight / retry
coordination around harness attempts.

## Validation

Focused validation passed:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/scheduler_daemon_harness.py src/runtime/orchestration/__init__.py src/__main__.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_daemon_harness or scheduler_daemon_lifecycle"
15 passed, 230 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "scheduler_lifecycle_cli"
4 passed, 38 deselected
```

Wider related validation passed:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_daemon or scheduler_lifecycle or scheduler_loop_evidence"
32 passed, 213 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "scheduler_lifecycle or scheduler_daemon_loop or scheduler_help"
8 passed, 34 deselected
```

`git diff --check` passed for the touched files except expected CRLF warnings.

## Review Evidence

- `review/scheduler-harness-retry-deadline-cancellation-policy-2026-06-21.md`
- `design_docs/scheduler-harness-retry-deadline-cancellation-policy-followup-direction-analysis.md`
