# Planning Gate - Sandbox Mount Binding Over Acquired Leases

> Date: 2026-06-21
> Status: ACTIVE

## Trigger

`design_docs/stages/planning-gate/2026-06-20-edit-lease-acquisition-and-expiration-lifecycle.md`
closed with scheduler-owned edit lease lifecycle records. The direction
analysis in `design_docs/edit-lease-lifecycle-after-writeback-unification-direction-analysis.md`
recommends sandbox mount binding as the next backend slice after lifecycle
authority exists.

## Problem

`SharedProcessSandboxProvider` currently derives `visible_mounts` from
`SandboxRequest.required_mounts` plus the static `EditScopeLease.allowed_artifacts`.
That keeps the provider metadata useful, but it cannot distinguish a declared
lease from an acquired lease.

This is now the wrong authority boundary. After lifecycle support, sandbox
allocation should consume scheduler-owned lifecycle evidence:

```text
static EditScopeLease declaration -> not enough to authorize writable mounts
EditLeaseLifecycleRecord(state="acquired") -> metadata authority for lease-scoped mounts
```

This slice should answer:

```text
Can metadata-only sandbox allocation bind lease-scoped visible mounts to an
acquired edit lease lifecycle record without implementing real filesystem
enforcement?
```

## Scope

### Slice 1 - Sandbox Request / Allocation Contract

Extend sandbox metadata contracts so callers can pass acquired lifecycle
evidence and allocations can report mount authorization:

```text
SandboxRequest
- edit_lease_lifecycle: EditLeaseLifecycleRecord | None

SandboxLeaseMountAuthorization
- lease_id
- task_id
- lifecycle_state
- authorized_mounts
- denied_mounts
- reason

SandboxAllocation
- lease_authorized_mounts
- lease_authorization_state
- lease_authorization_reason
```

The exact field names may differ if implementation finds a cleaner shape, but
the allocation must make it inspectable whether lease mounts came from acquired
lifecycle evidence.

### Slice 2 - Preflight Binding

`build_orchestration_preflight_bundle()` should read
`SchedulerState.edit_lease_lifecycle` for the task's lease and pass that record
to `SandboxRequest`.

If the task has an edit lease and `mount_policy == "lease-scoped"`:

1. acquired lifecycle record authorizes lease allowed artifacts as visible
   mounts;
2. missing lifecycle record rejects allocation or preflight with a readable
   reason;
3. non-acquired lifecycle state rejects allocation or preflight with a readable
   reason;
4. static `EditScopeLease.allowed_artifacts` alone no longer authorizes
   lease-scoped mounts.

### Slice 3 - Shared Process Provider Metadata

`SharedProcessSandboxProvider` remains metadata-only. It should not claim
filesystem/process isolation.

It should:

1. keep required context/input mounts visible;
2. add lease mounts only when the lifecycle record is `acquired`;
3. expose which mounts were authorized by which lease;
4. reject non-acquired lease-scoped requests clearly.

### Slice 4 - Focused Tests

Add tests for:

1. acquired lifecycle record authorizes lease-scoped visible mounts;
2. static edit lease without acquired lifecycle does not authorize lease mounts;
3. missing lifecycle record for a lease-scoped edit task rejects preflight;
4. released/blocked/revoked/expired lifecycle record rejects preflight;
5. allocation reports authorization metadata for acquired mounts;
6. existing no-edit-lease and required-mount behavior stays compatible.

## Non-Goals

This gate does not:

1. Implement real filesystem mount enforcement.
2. Add Docker, git-worktree, or remote-VM providers.
3. Create directories, worktrees, containers, or cleanup jobs.
4. Add Host UX or MCP readback.
5. Change edit lease conflict classification.
6. Change write-back planning or execution.
7. Add daemon expiry sweeping.
8. Mutate agent-owned Local Work Trajectory from sandbox/preflight code.

## Acceptance Criteria

The gate may close when:

1. Sandbox request/allocation metadata can express acquired-lease mount
   authorization.
2. Preflight passes acquired lifecycle records into sandbox allocation.
3. Lease-scoped edit mounts are not authorized from static declarations alone.
4. Non-acquired lifecycle states fail closed with readable reasons.
5. Focused sandbox/preflight tests pass.
6. Wider relevant runtime orchestration regression passes.
7. Review/status docs record validation and preserved non-goals.

## Implementation Notes

Prefer extending the existing metadata-only sandbox contract over adding a new
provider. The next real-provider slice should consume the same authorization
metadata rather than inventing a second mount policy.

Likely implementation files:

- `src/runtime/orchestration/sandbox.py`
- `src/runtime/orchestration/preflight.py`
- `src/runtime/orchestration/__init__.py`
- `tests/test_runtime_orchestration.py`

## Follow-Up

If this gate closes cleanly, the next likely backend slice is Host UX/MCP lease
readback or a real sandbox provider spike. Real provider work should wait until
this metadata boundary is stable.
