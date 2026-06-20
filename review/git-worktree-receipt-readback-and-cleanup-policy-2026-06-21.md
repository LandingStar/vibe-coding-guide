# Git Worktree Receipt Readback And Cleanup Policy Review

> Date: 2026-06-21
> Gate: `design_docs/stages/planning-gate/2026-06-21-git-worktree-receipt-readback-and-cleanup-policy.md`
> Status: PASSED

## Scope

This slice added read-only git-worktree receipt visibility to scheduler
authorization readback:

- added `GitWorktreeCommandReceiptSummary`;
- added `GitWorktreeReceiptSummary`;
- extended `SandboxAuthorizationSummary` with optional `git_worktree_receipt`;
- allowed `inspect_scheduler_authorization()` callers to provide existing
  `SandboxAllocation` evidence by task id;
- recorded cleanup owner/policy metadata without executing provider or cleanup
  work;
- preserved existing shared-process metadata-only readback behavior.

## Evidence

Validation commands:

```powershell
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/scheduler_authorization_readback.py src/runtime/orchestration/sandbox.py src/runtime/orchestration/__init__.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_authorization_readback or git_worktree" -q
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -q
```

Results:

- `py_compile`: passed
- focused readback/worktree tests: `12 passed, 211 deselected`
- full runtime orchestration test file: `223 passed`

## Boundary

Readback remains read-only. It only summarizes caller-provided allocation
evidence and does not register or execute `GitWorktreeSandboxProvider`, run live
runtime providers, mutate scheduler state, start cleanup, or alter scheduler
admission.

## Residual Risk

Receipt evidence is currently an in-memory caller-supplied input to
`inspect_scheduler_authorization()`. A later slice still needs a durable store or
host-run evidence bridge before CLI/MCP/snapshot readback can recover real
git-worktree allocation receipts from persisted scheduler artifacts.
