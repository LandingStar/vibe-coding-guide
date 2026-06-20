# Git Worktree Sandbox Provider Spike Over Acquired Leases

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/host-ux-authorization-readback-binding-followup-direction-analysis.md`
recommends moving from metadata-only authorization visibility to the first
real filesystem isolation spike.

Current authority chain:

```text
edit lease conflict evidence
-> scheduler-owned edit lease lifecycle
-> metadata-only sandbox mount authorization
-> schedulerAuthorizationReadback
-> Host UX readback
```

The remaining gap is enforcement.

## Goal

Introduce a minimal `git-worktree` sandbox provider spike that consumes acquired
edit lease lifecycle authority and produces inspectable allocation receipts.

The first slice should prove:

1. deterministic per-task worktree allocation under an explicit sandbox root;
2. fail-closed behavior when edit lease lifecycle is missing or non-acquired;
3. a provider receipt that records workspace source, worktree path, branch name,
   authorized writable paths, denied paths, cleanup state, and command output;
4. focused runtime tests using temporary git repositories;
5. compatibility with existing shared-process metadata-only provider behavior.

## Scope

1. Add contract fields to represent worktree allocation receipts without
   changing scheduler admission semantics.
2. Implement a `GitWorktreeSandboxProvider` in the orchestration sandbox layer.
3. Use `git worktree add` over a caller-provided repository root and sandbox
   root.
4. Authorize only lease-scoped writable mounts when lifecycle state is
   `acquired`.
5. Provide explicit cleanup helper behavior for the allocated worktree.
6. Add focused tests for successful allocation, missing lifecycle rejection,
   non-acquired lifecycle rejection, and cleanup receipt behavior.

## Non-Goals

1. No Docker, VM, remote, or OS-level process isolation provider.
2. No Host UX binding or mutation controls.
3. No automatic background cleanup daemon.
4. No scheduler admission schema expansion unless a narrow receipt field is
   required.
5. No provider-driven Local Work Trajectory mutation.
6. No live Qoder/runtime provider execution.
7. No broad write-back planning changes.

## Validation

Minimum validation:

1. `python -m py_compile` over touched runtime modules.
2. Focused runtime orchestration tests for worktree provider behavior.
3. Existing sandbox/preflight focused tests remain green.

## Write-Back Targets

On close, update:

1. `design_docs/Project Master Checklist.md`
2. `design_docs/Global Phase Map and Current Position.md`
3. `.codex/checkpoints/latest.md`
4. `review/git-worktree-sandbox-provider-spike-over-acquired-leases-2026-06-21.md`

## Completion Criteria

This gate is complete when a minimal `GitWorktreeSandboxProvider` can allocate
and clean up deterministic worktrees in tests, refuses missing/non-acquired
lease lifecycle authority, and records enough receipt metadata for later Host
UX or CLI inspection.

## Close Evidence

Completed on 2026-06-21.

Review evidence:

- `review/git-worktree-sandbox-provider-spike-over-acquired-leases-2026-06-21.md`

Validation:

- `.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/sandbox.py src/runtime/orchestration/preflight.py src/runtime/orchestration/__init__.py`
- `.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "git_worktree or shared_process_sandbox or orchestration_preflight_bundle" -q`
  - `13 passed, 206 deselected`
- `.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -q`
  - `219 passed`
