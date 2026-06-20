# Review - Lease And Sandbox Authorization Readback

> Date: 2026-06-21
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-21-lease-and-sandbox-authorization-readback.md`

## Scope Reviewed

This slice added read-only scheduler authorization diagnostics over:

1. task edit lease declarations;
2. scheduler-owned edit lease lifecycle records;
3. metadata-only shared-process sandbox mount authorization.

Implemented:

1. `src/runtime/orchestration/scheduler_authorization_readback.py`.
2. `inspect_scheduler_authorization()`.
3. `inspect_scheduler_authorization_snapshot()`.
4. `SchedulerAuthorizationReadback` and task/lifecycle/sandbox summary
   dataclasses.
5. MCP `schedulerAuthorizationReadback`.
6. Focused runtime tests for acquired, missing, and non-acquired lifecycle
   authorization states.
7. Snapshot readback test covering optional event-log recovery.
8. MCP exposure/routing test.

## Evidence

Compilation:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/scheduler_authorization_readback.py src/runtime/orchestration/__init__.py src/mcp/tools.py src/mcp/server.py tests/test_runtime_orchestration.py tests/test_mcp_admission.py
passed
```

Focused runtime validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "authorization_readback or sandbox_provider or orchestration_preflight_bundle"
12 passed
```

Focused MCP validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "authorization_readback or scheduler_lifecycle"
3 passed
```

Wider relevant regression:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py
214 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py
6 passed
```

## Behavioral Notes

The readback helper uses existing scheduler snapshot/recovery functions as the
input authority. When `schedulerEventLogPath` is provided, the helper consumes
`recover_scheduler_state()` rather than creating a second replay model.

Sandbox authorization readback reuses `SharedProcessSandboxProvider` allocation
metadata. This keeps readback aligned with preflight behavior:

1. acquired lifecycle records authorize lease-scoped mounts;
2. missing lifecycle records reject lease-scoped mounts;
3. non-acquired lifecycle records reject lease-scoped mounts;
4. no-edit-lease tasks remain `not_required`.

The MCP tool returns an `authority_split` block showing that the path is
read-only: no scheduler mutation, projection refresh, provider execution,
ExchangeArtifact/admission ledger mutation, or Local Work Trajectory mutation.

## Preserved Non-Goals

This slice did not add Host UX binding, a CLI command, real sandbox provider
behavior, Qoder/runtime execution, scheduler mutation, projection refresh,
ExchangeArtifact/admission ledger mutation, write-back planning changes, or
Local Work Trajectory mutation from scheduler readback code.

## Follow-Up

The next product slice can bind the readback product into Host UX, while the
next isolation slice can start a real sandbox provider spike that consumes the
same authorization metadata.
