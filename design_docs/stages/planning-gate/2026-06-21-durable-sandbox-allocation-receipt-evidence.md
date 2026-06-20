# Durable Sandbox Allocation Receipt Evidence

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/git-worktree-receipt-readback-cleanup-followup-direction-analysis.md`
recommends making sandbox allocation receipts durable before wiring real
git-worktree provider execution into host-controlled runs.

Current chain:

```text
GitWorktreeSandboxProvider allocation
-> SandboxAllocation.git_worktree_receipt
-> scheduler authorization readback projection
-> durable receipt evidence artifact (this gate)
```

The remaining gap is a file-backed receipt evidence product that can be read by
snapshot/CLI/MCP/Host UX paths without executing a provider.

## Goal

Define and persist a minimal sandbox allocation receipt evidence artifact, then
allow authorization readback snapshot helpers to merge that evidence by task id.

The first slice should prove:

1. a JSON-safe evidence artifact can store one or more `SandboxAllocation`
   records with optional git-worktree receipts;
2. read/write helpers preserve allocation state, lease authorization facts, and
   git-worktree receipt command output;
3. snapshot readback can merge optional receipt evidence by task id;
4. evidence readers do not execute providers, mutate scheduler state, or run
   cleanup.

## Scope

1. Add a `sandbox_allocation_receipt_evidence` runtime contract.
2. Add default path, writer, and reader helpers under
   `.codex/scheduler/evidence/`.
3. Add conversion helpers between `SandboxAllocation` and JSON-safe evidence
   payloads.
4. Extend `inspect_scheduler_authorization_snapshot()` with an optional receipt
   evidence path.
5. Add focused tests for round-trip persistence and readback merge behavior.

## Non-Goals

1. No default git-worktree provider registration.
2. No live Qoder/runtime execution.
3. No cleanup daemon or cleanup runner.
4. No Host UX mutation controls.
5. No scheduler admission schema redesign.
6. No Local Work Trajectory mutation from runtime/readback code.

## Validation

Minimum validation:

1. `python -m py_compile` over touched runtime modules.
2. Focused runtime orchestration tests for durable receipt evidence and readback
   merge behavior.
3. Existing git-worktree receipt readback tests remain green.

## Write-Back Targets

On close, update:

1. `design_docs/Project Master Checklist.md`
2. `design_docs/Global Phase Map and Current Position.md`
3. `.codex/checkpoints/latest.md`
4. `review/durable-sandbox-allocation-receipt-evidence-2026-06-21.md`

## Completion Criteria

This gate is complete when sandbox allocation receipt evidence can be written,
read, and merged into scheduler authorization snapshot readback without
executing providers or cleanup, and focused/full runtime validation passes.

## Close Summary

Completed on 2026-06-21.

Implemented:

1. Added `src/runtime/orchestration/sandbox_allocation_evidence.py` with the
   `sandbox_allocation_receipt_evidence` JSON contract.
2. Added default evidence path, writer, reader, summary, and
   `SandboxAllocation` JSON round-trip helpers.
3. Exported the evidence helpers from `src/runtime/orchestration/__init__.py`.
4. Extended `inspect_scheduler_authorization_snapshot()` with optional
   `sandbox_allocation_evidence_path` merge support keyed by task id.
5. Added focused tests for durable receipt round-trip, contract rejection, and
   scheduler authorization snapshot readback merge.

Validation:

```powershell
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/sandbox_allocation_evidence.py src/runtime/orchestration/scheduler_authorization_readback.py src/runtime/orchestration/__init__.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "sandbox_allocation_receipt or scheduler_authorization_readback or git_worktree" -q
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -q
```

Results:

- `py_compile`: passed
- focused durable evidence/readback tests: `14 passed, 212 deselected`
- full runtime orchestration test file: `226 passed`

Review evidence:

- `review/durable-sandbox-allocation-receipt-evidence-2026-06-21.md`
