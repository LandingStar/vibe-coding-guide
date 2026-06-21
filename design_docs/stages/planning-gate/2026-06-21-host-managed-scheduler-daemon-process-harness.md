# Planning Gate - Host-Managed Scheduler Daemon Process Harness

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/backend-orchestration-after-host-ux-sandbox-branch-direction-analysis.md`
recommends pausing the Host UX sandbox receipt branch and returning to the
backend scheduler/orchestration line.

## Problem

The runtime now has:

```text
SchedulerDaemonLifecycleControl
apply_scheduler_daemon_lifecycle_action()
inspect_scheduler_daemon_lifecycle_control()
run_scheduler_daemon_lifecycle_once()
doc-based-coding scheduler lifecycle ...
schedulerLifecycleControl / schedulerLifecycleRunOnce
```

This is enough for caller-driven lifecycle mutations and bounded run-once
invocations. It is not yet a host-owned process harness. A local operator still
has to repeatedly call lifecycle inspection / heartbeat / run-once manually.

This slice should answer:

```text
Can the project add a small bounded host-managed harness around the existing
lifecycle control file without introducing an OS service, Host UX binding, or
real provider execution?
```

## Scope

### Slice 1 - Harness Runtime Contract

Add a new runtime module for the host-managed harness.

Minimum objects:

```text
SchedulerDaemonHarnessRequest
SchedulerDaemonHarnessCycle
SchedulerDaemonHarnessResult
```

The harness should:

1. require a lifecycle control path;
2. run a bounded number of cycles for deterministic tests;
3. inspect lifecycle state at the start of each cycle;
4. heartbeat while lifecycle state is `running`;
5. call `run_scheduler_daemon_lifecycle_once()` with existing stop policy;
6. stop on paused / cancelling / cancelled / stopped / stale / max cycles /
   loop failure threshold;
7. expose compact cycle summaries and authority split.

### Slice 2 - Minimal CLI Smoke

Expose a minimal CLI action:

```text
doc-based-coding scheduler lifecycle harness --control-path PATH ...
```

The command should:

1. stay fake-runtime only;
2. accept bounded harness cycle count and existing run-once stop policy fields;
3. return JSON;
4. not refresh scheduler projection;
5. not mutate Local Work Trajectory.

### Slice 3 - Focused Tests

Add focused tests for:

1. harness drains a small fake-runtime task graph and stops when no ready tasks
   remain;
2. harness stops without scheduler mutation when lifecycle is paused / stopped;
3. harness consumes cancelling state through lifecycle run-once and reports
   cancellation;
4. CLI harness smoke returns JSON and rejects non-fake runtime provider.

## Non-Goals

This gate does not:

1. Start an OS service, Windows service, systemd unit, launch agent, or
   install-time daemon registration.
2. Add sleeps, filesystem watching, auto-start, or long-running unbounded
   background behavior.
3. Run live Qoder or any real provider.
4. Add MCP surface in this slice.
5. Add Host UX binding.
6. Refresh scheduler projection automatically.
7. Run or hide sandbox cleanup.
8. Mutate ExchangeArtifact lifecycle or admission ledger state.
9. Mutate agent-owned Local Work Trajectory from scheduler runtime or CLI code.
10. Redesign retry/deadline/cancellation policy beyond current bounded stop
    policy and lifecycle states.

## Acceptance Criteria

The gate may close when:

1. Harness runtime request/result objects exist and are exported.
2. Harness cycles reuse `run_scheduler_daemon_lifecycle_once()` rather than
   duplicating scheduler execution semantics.
3. Harness stop reasons are visible in JSON output.
4. CLI `scheduler lifecycle harness` exists and remains fake-runtime only.
5. Focused runtime and CLI tests pass.
6. Review/status docs record validation and preserved non-goals.

## Implementation Summary

Completed on 2026-06-21.

This slice added a bounded host-managed scheduler daemon process harness around
the existing lifecycle control file and lifecycle-gated run-once helper.

Implemented:

1. New runtime module:
   - `src/runtime/orchestration/scheduler_daemon_harness.py`
2. Runtime contract:
   - `SchedulerDaemonHarnessRequest`
   - `SchedulerDaemonHarnessCycle`
   - `SchedulerDaemonHarnessResult`
   - `SchedulerDaemonHarnessStopReason`
   - `run_scheduler_daemon_harness()`
3. CLI surface:
   - `doc-based-coding scheduler lifecycle harness`
4. Focused runtime tests for draining fake-runtime work, paused lifecycle
   skip, and cancelling lifecycle consumption.
5. Focused CLI test for harness smoke and non-fake provider rejection.

The harness reuses `run_scheduler_daemon_lifecycle_once()` for scheduler
execution rather than duplicating daemon-loop semantics. It runs a bounded
number of cycles, inspects lifecycle state before each cycle, consumes
cancelling state through the existing lifecycle run-once path, and returns
compact cycle summaries plus authority split.

## Validation

Focused validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/scheduler_daemon_harness.py src/runtime/orchestration/__init__.py src/__main__.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_daemon_harness or scheduler_daemon_lifecycle"
11 passed, 230 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "scheduler_lifecycle_cli"
3 passed, 38 deselected
```

## Non-Goals Preserved

This slice did not add:

1. OS service, Windows service, systemd unit, launch agent, or install-time
   daemon registration.
2. Sleeps, filesystem watching, auto-start, or unbounded long-running process
   behavior.
3. Live Qoder or any real provider execution.
4. MCP surface.
5. Host UX binding.
6. Automatic scheduler projection refresh.
7. Hidden sandbox cleanup.
8. ExchangeArtifact lifecycle or admission ledger mutation.
9. Scheduler-runtime or CLI mutation of agent-owned Local Work Trajectory.
10. Retry/deadline/cancellation policy redesign.
