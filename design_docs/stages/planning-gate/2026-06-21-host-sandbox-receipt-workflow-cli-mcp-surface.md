# CLI/MCP Surface For Host Sandbox Receipt Workflow

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/host-workflow-allocate-read-cleanup-read-followup-direction-analysis.md`
recommends exposing the backend host sandbox receipt workflow through operator
surfaces before binding Host UX.

The backend helper already exists:

- `tools.progress_graph.host_sandbox_receipt_workflow.HostSandboxReceiptWorkflowRequest`
- `tools.progress_graph.host_sandbox_receipt_workflow.run_host_sandbox_receipt_workflow()`

## Goal

Expose the existing host sandbox receipt workflow through explicit CLI and MCP
surfaces so operators and MCP hosts can run the same allocate/read/cleanup/read
contract without re-implementing the lifecycle.

## Scope

1. Add CLI command:
   `doc-based-coding scheduler sandbox-receipt-workflow`.
2. Add MCP tool:
   `schedulerSandboxReceiptWorkflow`.
3. Support `run_once` and `daemon_loop` modes over fake runtime wiring.
4. Require explicit git-worktree opt-in fields:
   scheduler snapshot path, event log path, workspace/source repo root,
   git-worktree sandbox root, and allocation evidence id.
5. Preserve cleanup authority:
   cleanup runs only when `--cleanup` / `cleanup=true` is supplied, and cleanup
   output path/id are rejected otherwise by the shared backend helper.
6. Add focused CLI and MCP tests over temporary git repositories.
7. Update status docs and review evidence on close.

## Non-Goals

1. No Host UX button, selector, or confirmation model.
2. No live Qoder or real-provider CLI/MCP expansion.
3. No default git-worktree provider discovery.
4. No background cleanup daemon.
5. No scheduler admission schema changes.
6. No automatic projection refresh.
7. No Local Work Trajectory mutation from CLI/MCP/runtime code.

## Validation

Minimum validation:

1. `python -m py_compile` over touched CLI/MCP/test modules.
2. Focused CLI test proving successful run-once workflow cleanup/readback.
3. Focused MCP test proving successful daemon-loop workflow cleanup/readback.
4. Focused CLI/MCP validation that cleanup output requires cleanup opt-in.
5. Focused tool-list/help assertions for the new surface.

## Write-Back Targets

On close, update:

1. `design_docs/Project Master Checklist.md`
2. `design_docs/Global Phase Map and Current Position.md`
3. `.codex/checkpoints/latest.md`
4. `review/host-sandbox-receipt-workflow-cli-mcp-surface-2026-06-21.md`

## Completion Criteria

This gate is complete when CLI and MCP callers can invoke the shared backend
workflow for both host run modes through one stable operator contract while
cleanup remains explicit and opt-in.

## Close Summary

Completed on 2026-06-21.

The existing backend workflow is now exposed through:

1. CLI `doc-based-coding scheduler sandbox-receipt-workflow`;
2. MCP `schedulerSandboxReceiptWorkflow`.

Both surfaces support `run-once` / `daemon-loop` modes, require explicit
git-worktree opt-in inputs, keep `runtimeProvider=fake` as the only CLI/MCP
runtime, and call `run_host_sandbox_receipt_workflow()` instead of duplicating
allocation/readback/cleanup/readback logic. Cleanup remains opt-in through
`--cleanup` / `cleanup=true`; cleanup evidence output without cleanup is
rejected by the shared backend validation.
