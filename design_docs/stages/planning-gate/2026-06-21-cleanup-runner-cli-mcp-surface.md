# Cleanup Runner CLI/MCP Surface

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/cleanup-policy-runner-over-durable-receipts-followup-direction-analysis.md`
recommends exposing the completed backend cleanup runner through a narrow
operator-facing surface.

Current chain:

```text
sandbox_allocation_receipt_evidence
-> run_sandbox_allocation_cleanup_over_receipts()
-> CLI/MCP explicit cleanup invocation (this gate)
```

## Goal

Add explicit CLI and MCP surfaces for
`run_sandbox_allocation_cleanup_over_receipts()` so a host, operator, or agent
can run git-worktree cleanup using durable receipt evidence without importing
Python internals.

The first slice should prove:

1. cleanup requires an explicit input evidence path;
2. optional output evidence path/id, timestamp, and git executable are caller
   controlled;
3. CLI and MCP return the same JSON-safe cleanup runner result;
4. cleanup remains explicit and is not invoked by host-run, readback, scheduler
   admission, or daemon paths;
5. focused tests cover CLI/MCP cleanup over temp git-worktree evidence.

## Scope

1. Add a CLI command under the existing scheduler command family.
2. Add a matching MCP tool with explicit arguments.
3. Reuse `run_sandbox_allocation_cleanup_over_receipts()` directly.
4. Add focused CLI/MCP tests around successful cleanup and JSON result shape.
5. Update status docs and review evidence on close.

## Non-Goals

1. No background cleanup daemon.
2. No Host UX button or visual binding.
3. No host-run implicit cleanup.
4. No scheduler admission schema changes.
5. No live Qoder/runtime expansion.
6. No default evidence discovery or broad filesystem search.
7. No Local Work Trajectory mutation from runtime/CLI/MCP code.

## Validation

Minimum validation:

1. `python -m py_compile` over touched CLI/MCP/runtime modules.
2. Focused CLI/MCP tests for cleanup runner surface.
3. Existing runtime cleanup runner tests remain green.
4. Relevant scheduler/MCP focused regression remains green.

## Write-Back Targets

On close, update:

1. `design_docs/Project Master Checklist.md`
2. `design_docs/Global Phase Map and Current Position.md`
3. `.codex/checkpoints/latest.md`
4. `review/cleanup-runner-cli-mcp-surface-2026-06-21.md`

## Completion Criteria

This gate is complete when CLI and MCP can explicitly invoke cleanup over
durable sandbox allocation receipt evidence, write updated evidence, return a
stable JSON result, and preserve all non-cleanup paths as side-effect-free.

## Close Summary

Completed on 2026-06-21.

Implemented surfaces:

1. CLI command:
   `doc-based-coding scheduler cleanup-receipts`
2. MCP tool:
   `schedulerCleanupReceipts`

Both surfaces require an explicit input evidence path, accept optional output
evidence path/id, timestamp, and git executable, and return the JSON-safe
`SandboxCleanupRunnerResult` shape.

The cleanup path remains explicit. It does not run during host-run, scheduler
admission, readback, projection refresh, daemon loop, or Local Work Trajectory
runtime code.

Validation results:

1. `py_compile`: passed for touched CLI/MCP/test modules.
2. CLI cleanup focused tests: `3 passed, 34 deselected`.
3. MCP cleanup focused tests: `2 passed, 6 deselected`.
4. Runtime cleanup/evidence/git focused tests: `16 passed, 215 deselected`.
5. Full CLI tests: `37 passed`.
6. Full tracked MCP admission tests: `8 passed`.
7. Full runtime orchestration tests: `231 passed`.
8. Full MCP tools tests: `86 passed`.

Review evidence:

- `review/cleanup-runner-cli-mcp-surface-2026-06-21.md`

Follow-up direction:

- `design_docs/cleanup-runner-cli-mcp-surface-followup-direction-analysis.md`
