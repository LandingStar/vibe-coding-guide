# Cleanup Policy Runner Over Durable Receipts Review

> Date: 2026-06-21
> Gate: `design_docs/stages/planning-gate/2026-06-21-cleanup-policy-runner-over-durable-receipts.md`
> Status: PASSED

## Scope

This slice closed the explicit cleanup loop for git-worktree sandbox allocation
receipts:

- added `src/runtime/orchestration/sandbox_cleanup_runner.py`;
- added `SandboxCleanupRunnerResult`;
- added `run_sandbox_allocation_cleanup_over_receipts()`;
- selected only allocated git-worktree allocations with
  `cleanup_required=True` and receipt `cleanup_state="required"`;
- reused `GitWorktreeSandboxProvider.cleanup()` for command receipt semantics;
- wrote updated `sandbox_allocation_receipt_evidence` with cleanup authority
  metadata;
- exported the runner through `src/runtime/orchestration/__init__.py`;
- kept host-run, readback, scheduler admission, daemon, and Local Work
  Trajectory runtime mutation paths unchanged.

## Evidence

Validation commands:

```powershell
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/sandbox_allocation_evidence.py src/runtime/orchestration/sandbox_cleanup_runner.py src/runtime/orchestration/__init__.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "sandbox_allocation_cleanup or sandbox_allocation_receipt or git_worktree" -q
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "sandbox_allocation_cleanup or sandbox_allocation_receipt or scheduler_authorization_readback or host_scheduler_runner or git_worktree" -q
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -q
```

Results:

- `py_compile`: passed
- focused cleanup/evidence/git-worktree tests: `16 passed, 215 deselected`
- wider cleanup/evidence/readback/host/git tests: `21 passed, 210 deselected`
- full runtime orchestration test file: `230 passed`

## Boundary

Cleanup remains explicit and host/operator-owned. This slice does not start a
background cleanup daemon, does not run cleanup during host scheduler runs, does
not add Host UX controls, does not change scheduler admission schema, does not
run live Qoder/runtime, and does not mutate Local Work Trajectory from runtime
code.

## Residual Risk

The backend runner can now clean durable receipts, but it is still only a Python
helper. Operators need a narrow CLI/MCP surface before this can be used
consistently outside tests or direct runtime imports.
