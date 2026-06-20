# Git Worktree Receipt Readback And Cleanup Policy

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/git-worktree-sandbox-provider-spike-followup-direction-analysis.md`
recommends making the new git-worktree provider receipts inspectable before
using the provider in live or host-controlled execution paths.

Current chain:

```text
edit lease lifecycle
-> sandbox mount authorization
-> git-worktree provider allocation receipt
-> explicit cleanup helper receipt
```

The remaining gap is read-only operational visibility and cleanup ownership.

## Goal

Extend scheduler authorization readback with an optional git-worktree receipt
projection and document the minimal cleanup responsibility boundary.

The first slice should prove:

1. allocated, rejected, and cleanup-completed `GitWorktreeSandboxReceipt`
   metadata can be summarized in a JSON-safe readback product;
2. readback remains read-only and never executes a real provider;
3. cleanup ownership states are explicit enough for later host/daemon policy;
4. focused tests cover synthetic allocation receipts without creating live
   worktrees in the readback path.

## Scope

1. Add a JSON-safe summary for optional git-worktree receipt metadata.
2. Add optional receipt input to scheduler authorization readback so callers can
   pass existing allocation evidence.
3. Record cleanup owner/policy metadata in the readback product without starting
   cleanup work.
4. Add focused tests for allocated, rejected, cleanup-completed, and missing
   receipt cases.

## Non-Goals

1. No default registration of `GitWorktreeSandboxProvider`.
2. No automatic cleanup daemon.
3. No live Qoder/runtime execution through git-worktree.
4. No Host UX mutation controls.
5. No scheduler admission schema redesign.
6. No provider execution from readback helpers.
7. No Local Work Trajectory mutation from runtime/readback code.

## Validation

Minimum validation:

1. `python -m py_compile` over touched runtime modules.
2. Focused runtime orchestration tests for git-worktree receipt readback.
3. Existing scheduler authorization readback tests remain green.

## Write-Back Targets

On close, update:

1. `design_docs/Project Master Checklist.md`
2. `design_docs/Global Phase Map and Current Position.md`
3. `.codex/checkpoints/latest.md`
4. `review/git-worktree-receipt-readback-and-cleanup-policy-2026-06-21.md`

## Completion Criteria

This gate is complete when scheduler authorization readback can summarize
optional git-worktree allocation/cleanup receipts without executing providers,
cleanup ownership is explicit in the product, focused tests pass, and status
documents record the result.

## Close Evidence

Completed on 2026-06-21.

Review evidence:

- `review/git-worktree-receipt-readback-and-cleanup-policy-2026-06-21.md`

Validation:

- `.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/scheduler_authorization_readback.py src/runtime/orchestration/sandbox.py src/runtime/orchestration/__init__.py`
- `.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_authorization_readback or git_worktree" -q`
  - `12 passed, 211 deselected`
- `.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -q`
  - `223 passed`
