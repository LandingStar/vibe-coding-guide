# Review - Sandbox Mount Binding Over Acquired Leases

> Date: 2026-06-21
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-21-sandbox-mount-binding-over-acquired-leases.md`

## Scope Reviewed

This slice connected metadata-only sandbox allocation to scheduler-owned
acquired edit lease lifecycle records.

Implemented:

1. `SandboxRequest.edit_lease_lifecycle`.
2. `SandboxLeaseMountAuthorization`.
3. `SandboxAllocation.lease_authorized_mounts`.
4. `SandboxAllocation.lease_authorization_state`.
5. `SandboxAllocation.lease_authorization_reason`.
6. Fail-closed lease-scoped allocation for missing or non-acquired lifecycle.
7. Preflight wiring from `SchedulerState.edit_lease_lifecycle` into
   `SandboxRequest`.
8. Focused tests for acquired authorization, missing lifecycle rejection,
   non-acquired lifecycle rejection, and preserved no-edit-lease behavior.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/sandbox.py src/runtime/orchestration/preflight.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "sandbox_provider or orchestration_preflight_bundle or preflighted_task or preflighted_ready_tasks"
16 passed
```

Wider relevant regression:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py
210 passed
```

## Behavioral Notes

`SharedProcessSandboxProvider` remains metadata-only. The allocation evidence
does not claim real process or filesystem isolation.

Required mounts from task context and input refs remain visible. Lease allowed
artifacts are added only when the sandbox request includes a matching acquired
`EditLeaseLifecycleRecord`.

Static `EditScopeLease.allowed_artifacts` no longer authorizes lease-scoped
mounts by itself. Missing, mismatched, released, revoked, expired, blocked, or
review-required lifecycle records reject allocation with readable reasons.

`build_orchestration_preflight_bundle()` now accepts an optional
`scheduler_state`. When present, it passes the task's lifecycle record to the
sandbox provider. `drain_preflighted_ready_tasks()` passes the current
scheduler state after `mark_ready_tasks()`, so acquired lifecycle records
created by admission participate in preflight.

## Authority Boundary

This slice does not implement real filesystem/process sandbox enforcement,
Docker/git-worktree/remote-VM providers, Host UX/MCP readback, write-back
planning, daemon expiry sweeping, or Local Work Trajectory mutation from
sandbox/preflight code.

## Follow-Up

The next backend/product slice should choose between:

1. Host UX/MCP lease and sandbox authorization readback; or
2. a real sandbox provider spike consuming the same authorization metadata.

My recommendation is readback first if operator diagnosis is the priority, and
real provider spike first if actual isolation is now the highest risk.
