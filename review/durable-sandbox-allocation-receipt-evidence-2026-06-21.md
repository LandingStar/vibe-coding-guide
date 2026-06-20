# Durable Sandbox Allocation Receipt Evidence Review

> Date: 2026-06-21
> Gate: `design_docs/stages/planning-gate/2026-06-21-durable-sandbox-allocation-receipt-evidence.md`
> Status: PASSED

## Scope

This slice made sandbox allocation receipts durable without enabling provider
execution:

- added `sandbox_allocation_receipt_evidence` as a JSON-safe evidence product;
- added default path, writer, reader, summary, and metadata helpers;
- added `SandboxAllocation` JSON round-trip helpers, including lease mount
  authorization and optional git-worktree receipts;
- exported the evidence contract from `src/runtime/orchestration`;
- extended `inspect_scheduler_authorization_snapshot()` with optional
  `sandbox_allocation_evidence_path`;
- merged receipt evidence into readback by task id while preserving read-only
  behavior.

## Evidence

Validation commands:

```powershell
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/sandbox_allocation_evidence.py src/runtime/orchestration/scheduler_authorization_readback.py src/runtime/orchestration/__init__.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "sandbox_allocation_receipt or scheduler_authorization_readback or git_worktree" -q
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -q
```

Results:

- `py_compile`: passed
- focused durable evidence/readback tests: `14 passed, 212 deselected`
- full runtime orchestration test file: `226 passed`

## Boundary

Evidence readers remain read-only. They read persisted allocation metadata and
do not execute `GitWorktreeSandboxProvider`, run live runtime providers, mutate
scheduler state, run cleanup, refresh projections, or mutate Local Work
Trajectory.

## Residual Risk

Host-controlled scheduler runs still need an explicit opt-in wiring slice before
real git-worktree allocation receipts are emitted automatically. Cleanup remains
explicit and receipt-based only; a cleanup runner should consume durable
evidence in a later gate.
