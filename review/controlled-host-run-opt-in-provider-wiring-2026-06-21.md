# Controlled Host Run Opt-In Provider Wiring Review

> Date: 2026-06-21
> Gate: `design_docs/stages/planning-gate/2026-06-21-controlled-host-run-opt-in-provider-wiring.md`
> Status: PASSED

## Scope

This slice wired durable sandbox allocation receipts into a host-controlled run
path:

- added explicit one-shot `HostSchedulerRunRequest` git-worktree opt-in fields;
- registered `GitWorktreeSandboxProvider` only when the host request opts in;
- required caller-provided `workspace_root`, `git_worktree_sandbox_root`, and
  `sandbox_allocation_evidence_id`;
- preserved sandbox allocations from preflight attempts in `PreflightDrainResult`;
- wrote durable `sandbox_allocation_receipt_evidence` from host-run allocation
  attempts;
- surfaced receipt evidence path and opt-in metadata in `HostSchedulerRunResult`;
- kept default fake-runtime/shared-process host runs unchanged.

## Evidence

Validation commands:

```powershell
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/preflight.py src/runtime/orchestration/scheduler_host_runner.py src/runtime/orchestration/__init__.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "host_scheduler_runner or sandbox_allocation_receipt or git_worktree" -q
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -q
```

Results:

- `py_compile`: passed
- focused host/git/evidence tests: `15 passed, 213 deselected`
- full runtime orchestration test file: `228 passed`

## Boundary

The provider remains opt-in and host-owned. This slice does not register
git-worktree as a default provider, run live Qoder, start cleanup, bind Host UX,
change scheduler admission schema, mutate ExchangeArtifact/admission ledgers, or
mutate Local Work Trajectory from runtime code.

## Residual Risk

Durable allocation receipts can now be produced by one-shot host runs, but
cleanup remains manual. A later cleanup runner should consume receipt evidence,
execute explicit cleanup, and persist cleanup receipts without making cleanup
implicit or daemon-owned by default.
