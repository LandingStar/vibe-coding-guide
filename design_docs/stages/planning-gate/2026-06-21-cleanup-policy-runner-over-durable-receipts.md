# Cleanup Policy Runner Over Durable Receipts

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/controlled-host-run-opt-in-provider-wiring-followup-direction-analysis.md`
recommends closing the operational safety gap left after one-shot host runs can
explicitly create git-worktree sandboxes and persist durable allocation
receipts.

Current chain:

```text
HostSchedulerRunRequest git-worktree opt-in
-> GitWorktreeSandboxProvider allocation
-> sandbox_allocation_receipt_evidence
-> explicit cleanup runner over durable receipts (this gate)
```

## Goal

Add an explicit cleanup runner that reads one durable
`sandbox_allocation_receipt_evidence` artifact, cleans git-worktree allocations
whose receipts still require cleanup, and writes updated durable receipt
evidence with cleanup command receipts.

The first slice should prove:

1. cleanup is driven only by an explicit runner call;
2. only git-worktree allocations with `cleanup_required=True` are selected;
3. cleanup uses the existing `GitWorktreeSandboxProvider.cleanup()` receipt
   semantics;
4. updated receipt evidence preserves all allocation facts and records cleanup
   results;
5. readback, host-run, scheduler admission, and daemon paths remain unchanged.

## Scope

1. Add a cleanup runner helper under the runtime orchestration layer.
2. Read a caller-provided durable sandbox allocation receipt evidence artifact.
3. Select cleanup-required git-worktree allocations and call cleanup explicitly.
4. Write updated durable receipt evidence to a caller-provided or default output
   path.
5. Add focused tests for successful git-worktree cleanup and no-op behavior.

## Non-Goals

1. No background cleanup daemon.
2. No implicit cleanup during host runs.
3. No Host UX controls.
4. No scheduler admission schema changes.
5. No live Qoder/runtime expansion.
6. No readback helper side effects.
7. No Local Work Trajectory mutation from runtime code.

## Validation

Minimum validation:

1. `python -m py_compile` over touched runtime modules.
2. Focused runtime orchestration tests for durable receipt cleanup.
3. Existing git-worktree provider, durable receipt, readback, and host-run tests
   remain green.
4. Full `tests/test_runtime_orchestration.py` remains green.

## Write-Back Targets

On close, update:

1. `design_docs/Project Master Checklist.md`
2. `design_docs/Global Phase Map and Current Position.md`
3. `.codex/checkpoints/latest.md`
4. `review/cleanup-policy-runner-over-durable-receipts-2026-06-21.md`

## Completion Criteria

This gate is complete when durable sandbox allocation receipt evidence can be
explicitly cleaned up and rewritten with cleanup receipts, while all normal
readback and host-run paths stay side-effect-free and focused/full runtime
validation passes.

## Close Summary

Completed on 2026-06-21.

Implemented:

1. Added `src/runtime/orchestration/sandbox_cleanup_runner.py`.
2. Added `SandboxCleanupRunnerResult` and
   `run_sandbox_allocation_cleanup_over_receipts()`.
3. Cleanup runner reads one durable `sandbox_allocation_receipt_evidence`,
   selects cleanup-required allocated git-worktree receipts, calls
   `GitWorktreeSandboxProvider.cleanup()`, and writes updated durable receipt
   evidence.
4. `SandboxAllocationReceiptEvidence` now supports explicit authority split
   overrides while preserving the previous default.
5. Runtime public exports now include the cleanup runner helper and result.
6. Focused tests cover real temp git-worktree cleanup and no-op behavior when
   no cleanup-required allocations exist.

Validation:

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

Review evidence:

- `review/cleanup-policy-runner-over-durable-receipts-2026-06-21.md`

Follow-up direction:

- `design_docs/cleanup-policy-runner-over-durable-receipts-followup-direction-analysis.md`
