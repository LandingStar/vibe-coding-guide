# Planning Gate - Host-Managed Daemon Supervisor Contract

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/scheduler-harness-policy-mcp-surface-followup-direction-analysis.md`
recommends adding the first host-owned supervisor contract over repeated
policy-controlled scheduler daemon harness invocations.

## Problem

The backend scheduler/orchestration line now has:

```text
SchedulerDaemonLifecycleControl
run_scheduler_daemon_lifecycle_once()
run_scheduler_daemon_harness()
run_scheduler_daemon_harness_with_policy()
doc-based-coding scheduler lifecycle harness
schedulerLifecycleHarness
```

These surfaces support bounded, explicit, caller-driven execution. They do not
yet define the product contract for a host-managed supervisor that owns repeated
policy-controlled harness invocations, status readback, cancellation source, and
session identity.

This slice should answer:

```text
Can the project define a deterministic supervisor contract over the existing
policy-controlled harness without adding a real background service?
```

## Scope

### Slice 1 - Supervisor Runtime Contract

Add runtime request/status/result objects around
`run_scheduler_daemon_harness_with_policy()`.

Minimum objects:

```text
SchedulerDaemonSupervisorRequest
SchedulerDaemonSupervisorStatus
SchedulerDaemonSupervisorResult
```

Required behavior:

1. require an explicit supervisor id and lifecycle control path;
2. carry host-owned session/run identity fields;
3. carry explicit cancellation source fields;
4. carry deadline/readback timestamp fields;
5. invoke the policy-controlled harness at most once per supervisor call;
6. return status readback facts derived from lifecycle control when available;
7. expose authority split and mutation flags in JSON output.

### Slice 2 - Deterministic Tests

Add focused tests covering:

1. cancelled supervisor preflight returns before control-file read or mutation;
2. deadline preflight returns supervisor status without scheduler mutation;
3. running supervisor delegates to the policy-controlled harness and reports
   harness attempts;
4. status readback reports lifecycle state, queue summary where available, and
   readback errors where unavailable.

## Non-Goals

This gate does not:

1. Start or install an OS service, Windows service, systemd unit, launch agent,
   or install-time daemon registration.
2. Add sleeps, timers, filesystem watchers, auto-start, or unbounded daemon
   behavior.
3. Add CLI, MCP, or Host UX surface in this first contract slice.
4. Run live Qoder or any real provider.
5. Change existing harness or policy semantics.
6. Refresh scheduler projection automatically.
7. Run or hide sandbox cleanup.
8. Mutate ExchangeArtifact lifecycle or admission ledger state.
9. Mutate Local Work Trajectory from scheduler runtime code.
10. Bind agent home, scratch retention, or context-session storage lifecycle.

## Acceptance Criteria

The gate may close when:

1. Supervisor request/status/result objects exist and are exported.
2. Supervisor execution reuses `run_scheduler_daemon_harness_with_policy()`
   rather than duplicating harness semantics.
3. Cancellation/deadline preflight can return without reading or mutating the
   lifecycle control file.
4. Status readback facts are visible in result JSON.
5. Focused runtime tests pass.
6. Review/status docs record validation and preserved non-goals.

## Completion Summary

Completed on 2026-06-21.

Implemented:

1. New runtime module:
   - `src/runtime/orchestration/scheduler_daemon_supervisor.py`
2. Runtime contract:
   - `SchedulerDaemonSupervisorRequest`
   - `SchedulerDaemonSupervisorStatus`
   - `SchedulerDaemonSupervisorResult`
   - `SchedulerDaemonSupervisorStopReason`
   - `run_scheduler_daemon_supervisor_step()`
3. Orchestration exports for the supervisor contract.
4. Focused runtime tests for:
   - cancelled supervisor preflight without control-file read;
   - deadline preflight without scheduler mutation;
   - policy harness delegation with status readback;
   - status readback queue errors.

The supervisor step reuses `run_scheduler_daemon_harness_with_policy()` and
adds host-owned identity, cancellation-source, status-readback, and authority
split facts around it. Cancellation and deadline preflight can return before
reading or mutating lifecycle control.

## Validation

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

## Review Evidence

- `review/host-managed-daemon-supervisor-contract-2026-06-21.md`
- `design_docs/host-managed-daemon-supervisor-contract-followup-direction-analysis.md`
