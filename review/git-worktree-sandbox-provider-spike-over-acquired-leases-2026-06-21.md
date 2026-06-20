# Git Worktree Sandbox Provider Spike Over Acquired Leases Review

> Date: 2026-06-21
> Gate: `design_docs/stages/planning-gate/2026-06-21-git-worktree-sandbox-provider-spike-over-acquired-leases.md`
> Status: PASSED

## Scope

This slice implemented the first real filesystem-isolation provider spike for
scheduler tasks:

- added typed `GitWorktreeSandboxReceipt` and `GitWorktreeCommandReceipt`;
- added `GitWorktreeSandboxProvider`;
- allocates deterministic per-task worktrees under caller-provided sandbox root;
- consumes acquired edit lease lifecycle authority before writable mount
  exposure;
- fails closed when lifecycle is missing, mismatched, or non-acquired;
- records allocation and cleanup command receipts;
- preserves existing `SharedProcessSandboxProvider` behavior.

## Evidence

Validation commands:

```powershell
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/sandbox.py src/runtime/orchestration/preflight.py src/runtime/orchestration/__init__.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "git_worktree or shared_process_sandbox or orchestration_preflight_bundle" -q
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -q
```

Results:

- `py_compile`: passed
- focused sandbox/preflight tests: `13 passed, 206 deselected`
- full runtime orchestration test file: `219 passed`

## Boundary

The provider does not register itself as a default daemon/host provider and does
not mutate scheduler admission, write-back planning, Host UX, ExchangeArtifact
stores, or Local Work Trajectory from provider code.

## Residual Risk

Cleanup is explicit and receipt-based only. A later host/daemon slice still
needs a durable cleanup policy before this provider should be used for long-lived
operator workflows.
