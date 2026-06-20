# Planning Gate - Lease And Sandbox Authorization Readback

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-sandbox-mount-binding-over-acquired-leases.md`
closed with metadata-only sandbox allocation bound to acquired edit lease
lifecycle records.

The review in
`review/sandbox-mount-binding-over-acquired-leases-2026-06-21.md` recommends
readback first when operator diagnosis is the priority.

## Problem

The scheduler now owns three related authorization facts:

1. static task edit lease declarations;
2. dynamic edit lease lifecycle records;
3. sandbox allocation metadata derived from acquired lifecycle records.

Those facts are currently available only by reading low-level scheduler state or
preflight allocation details. Operators and MCP hosts need a read-only summary
that answers:

```text
For this scheduler snapshot, which tasks have edit leases, what lifecycle state
are those leases in, and would lease-scoped sandbox mounts be authorized?
```

## Scope

### Slice 1 - Runtime Readback Contract

Add a runtime helper that consumes an in-memory `SchedulerState` or a scheduler
state snapshot path and returns a JSON-safe readback product.

The summary should include:

1. task count and edit-lease task count;
2. lifecycle record count and lifecycle state counts;
3. per-task edit lease declaration facts;
4. per-task lifecycle facts, including missing lifecycle records;
5. per-task sandbox authorization facts for metadata-only shared-process
   allocation;
6. readable reasons for missing or non-acquired lifecycle rejection.

The helper must not mutate scheduler state, write files, refresh projections, or
run an agent runtime.

### Slice 2 - Snapshot / Replay Input

The snapshot helper should accept a required scheduler state snapshot path and
may accept an optional scheduler event log path for replay-based recovery.

If an event log is provided, reuse the existing scheduler recovery path so the
readback can inspect post-snapshot lifecycle events without inventing a second
replay model.

### Slice 3 - MCP Tool Surface

Expose the readback via MCP as `schedulerAuthorizationReadback`.

Required input:

```text
snapshotPath
```

Optional inputs:

```text
schedulerEventLogPath
strict
workspaceRoot
scratchRoot
```

Relative paths resolve under the MCP project root.

### Slice 4 - Focused Tests

Add tests for:

1. acquired lifecycle records reporting authorized lease-scoped mounts;
2. missing lifecycle records reporting rejected lease-scoped mounts;
3. non-acquired lifecycle records reporting rejected lease-scoped mounts;
4. snapshot helper preserving read-only behavior;
5. MCP tool exposure and routing.

## Non-Goals

This gate does not:

1. Add Host UX or VS Code panel binding.
2. Add a CLI command.
3. Implement real filesystem or process isolation.
4. Add Docker, git-worktree, remote-VM, or real sandbox provider behavior.
5. Run Qoder or any other agent runtime.
6. Mutate scheduler state, ExchangeArtifact store, admission ledger, scheduler
   projection, Host Evidence, or agent-owned Local Work Trajectory from the
   readback helper/tool.
7. Change edit lease conflict classification or admission semantics.
8. Change write-back planning or execution.

## Acceptance Criteria

The gate may close when:

1. Runtime readback reports task, lease lifecycle, and sandbox authorization
   facts from scheduler state.
2. Snapshot readback can inspect a stored scheduler state snapshot.
3. Optional event-log replay uses the existing recovery helper when provided.
4. MCP `schedulerAuthorizationReadback` returns the same summary shape.
5. Focused runtime and MCP tests pass.
6. Wider relevant runtime orchestration regression passes.
7. Review/status docs record validation and preserved non-goals.

## Close Summary

Completed on 2026-06-21.

This gate added a read-only scheduler authorization diagnostic surface over
edit lease declarations, scheduler-owned edit lease lifecycle records, and
metadata-only sandbox mount authorization.

Implemented behavior:

1. `inspect_scheduler_authorization()` builds an in-memory readback product from
   `SchedulerState`.
2. `inspect_scheduler_authorization_snapshot()` reads a scheduler snapshot and,
   when a scheduler event log is provided, reuses existing
   `recover_scheduler_state()` replay before inspection.
3. `SchedulerAuthorizationReadback` reports task counts, edit-lease task counts,
   lifecycle state counts, sandbox authorization state counts, per-task lease
   facts, lifecycle missing/non-missing facts, per-task sandbox allocation
   authorization, and orphan lifecycle records.
4. Sandbox authorization readback reuses `SharedProcessSandboxProvider`
   metadata allocation so acquired/missing/non-acquired decisions share the same
   contract as preflight.
5. MCP `schedulerAuthorizationReadback` exposes the readback product with
   required `snapshotPath` and optional `schedulerEventLogPath`, `strict`,
   `workspaceRoot`, and `scratchRoot`.
6. The readback surface reports `authority_split` showing no scheduler
   mutation, runtime execution, projection refresh, ExchangeArtifact/admission
   ledger mutation, or Local Work Trajectory mutation.

Validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/scheduler_authorization_readback.py src/runtime/orchestration/__init__.py src/mcp/tools.py src/mcp/server.py tests/test_runtime_orchestration.py tests/test_mcp_admission.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "authorization_readback or sandbox_provider or orchestration_preflight_bundle"
12 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "authorization_readback or scheduler_lifecycle"
3 passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py
214 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py
6 passed
```

Review evidence:

`review/lease-and-sandbox-authorization-readback-2026-06-21.md`

## Implementation Notes

Prefer a new small module rather than adding readback concerns directly into
the scheduler, sandbox, or MCP server files.

Likely implementation files:

- `src/runtime/orchestration/scheduler_authorization_readback.py`
- `src/runtime/orchestration/__init__.py`
- `src/mcp/tools.py`
- `src/mcp/server.py`
- `tests/test_runtime_orchestration.py`
- `tests/test_mcp_admission.py`

## Follow-Up

If this gate closes cleanly, the next choices remain:

1. Host UX binding over the readback product; or
2. real sandbox provider spike consuming the same authorization metadata.
