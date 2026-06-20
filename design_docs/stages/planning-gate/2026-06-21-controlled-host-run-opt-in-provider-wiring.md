# Controlled Host Run Opt-In Provider Wiring

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/durable-sandbox-allocation-receipt-evidence-followup-direction-analysis.md`
recommends wiring controlled host runs to explicitly opt into real
git-worktree sandbox allocation now that durable
`sandbox_allocation_receipt_evidence` exists.

Current chain:

```text
GitWorktreeSandboxProvider allocation
-> SandboxAllocation.git_worktree_receipt
-> sandbox_allocation_receipt_evidence
-> scheduler authorization readback merge
```

The remaining gap is controlled production of durable receipt evidence from a
host-owned run path.

## Goal

Allow a host-controlled scheduler run to opt into a provided
`GitWorktreeSandboxProvider`, allocate eligible task sandboxes using acquired
edit lease lifecycle authority, and write durable sandbox allocation receipt
evidence.

The first slice should prove:

1. existing fake-runtime/shared-process host runs remain unchanged by default;
2. git-worktree sandbox allocation is only enabled by explicit host-run input;
3. git-worktree opt-in requires caller-provided sandbox root and source repo
   root;
4. allocation uses acquired edit lease lifecycle and fail-closed sandbox
   provider behavior already defined by the sandbox layer;
5. attempted allocations are persisted as
   `sandbox_allocation_receipt_evidence` without running cleanup.

## Scope

1. Add explicit host-run request fields for git-worktree sandbox opt-in.
2. Build and register a `GitWorktreeSandboxProvider` only when the opt-in is
   present.
3. Thread caller-provided source repository root / sandbox root into the
   preflight run path.
4. Write durable sandbox allocation receipt evidence after host-run allocation
   attempts.
5. Add focused tests covering default behavior, successful opt-in evidence, and
   missing required opt-in paths.

## Non-Goals

1. No default git-worktree provider registration.
2. No live Qoder/runtime expansion.
3. No cleanup runner or cleanup daemon.
4. No Host UX mutation controls.
5. No scheduler admission schema redesign.
6. No ExchangeArtifact or admission ledger mutation changes.
7. No Local Work Trajectory mutation from runtime code.

## Validation

Minimum validation:

1. `python -m py_compile` over touched runtime modules.
2. Focused runtime orchestration tests for controlled host-run opt-in evidence.
3. Existing durable receipt evidence and git-worktree provider tests remain
   green.

## Write-Back Targets

On close, update:

1. `design_docs/Project Master Checklist.md`
2. `design_docs/Global Phase Map and Current Position.md`
3. `.codex/checkpoints/latest.md`
4. `review/controlled-host-run-opt-in-provider-wiring-2026-06-21.md`

## Completion Criteria

This gate is complete when host-controlled run code can explicitly opt into
git-worktree sandbox allocation, write durable allocation receipt evidence, and
keep default host-run behavior unchanged, with focused/full runtime validation
passing.

## Close Summary

Completed on 2026-06-21.

Implemented:

1. Added explicit `HostSchedulerRunRequest` fields:
   `git_worktree_sandbox_root`, `sandbox_allocation_evidence_id`, and
   `sandbox_allocation_evidence_path`.
2. `run_host_authorized_scheduler_once()` now registers
   `GitWorktreeSandboxProvider` only when the host request opts in.
3. Git-worktree opt-in fail-fast validates `workspace_root`,
   `git_worktree_sandbox_root`, and `sandbox_allocation_evidence_id`.
4. `PreflightDrainResult` now preserves sandbox allocations from preflighted
   attempts so durable receipt evidence can be written from the host-run path.
5. Host-run opt-in writes durable `sandbox_allocation_receipt_evidence` after
   allocation attempts without running cleanup.
6. Default fake-runtime/shared-process host-run behavior remains unchanged.

Validation:

```powershell
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/preflight.py src/runtime/orchestration/scheduler_host_runner.py src/runtime/orchestration/__init__.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "host_scheduler_runner or sandbox_allocation_receipt or git_worktree" -q
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -q
```

Results:

- `py_compile`: passed
- focused host/git/evidence tests: `15 passed, 213 deselected`
- full runtime orchestration test file: `228 passed`

Review evidence:

- `review/controlled-host-run-opt-in-provider-wiring-2026-06-21.md`
