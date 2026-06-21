# Host Workflow For Allocate-Read-Cleanup-Read

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/daemon-loop-git-worktree-opt-in-followup-direction-analysis.md`
recommends turning the existing allocation evidence, Host Evidence readback,
and explicit cleanup runner pieces into one host/operator workflow contract.

Current chain:

```text
one-shot host run or bounded host daemon loop
-> durable sandbox_allocation_receipt_evidence
-> Host Evidence presentation readback
-> explicit cleanup runner
-> updated durable cleanup receipt evidence
-> Host Evidence presentation readback
```

## Goal

Provide a backend workflow helper that explicitly sequences allocation,
readback, cleanup, and post-cleanup readback for git-worktree sandbox receipt
evidence.

The first slice should prove:

1. the workflow can run a one-shot host scheduler pass with explicit
   git-worktree opt-in, read the allocation evidence, run cleanup, and read the
   cleanup evidence;
2. the workflow can run a bounded host daemon loop through the same lifecycle;
3. cleanup remains explicit and opt-in, not an implicit side effect of host run
   or daemon-loop execution;
4. the workflow result is JSON-safe and exposes evidence paths, readback
   presentation statuses, and authority split facts;
5. existing one-shot and daemon-loop behavior remains available outside this
   helper.

## Scope

1. Add a compact backend workflow request/result contract around existing
   `HostSchedulerRunRequest` and `HostSchedulerDaemonLoopRequest`.
2. Support workflow mode for `run_once` and `daemon_loop`.
3. Require an explicit cleanup opt-in flag before invoking cleanup.
4. Reuse `run_host_authorized_scheduler_once()`,
   `run_host_authorized_scheduler_daemon_loop()`,
   `run_sandbox_allocation_cleanup_over_receipts()`, and Host Evidence
   presentation helpers.
5. Add focused runtime tests over temporary git repositories for both workflow
   modes.
6. Update status docs and review evidence on close.

## Non-Goals

1. No CLI binding in this slice.
2. No Host UX button or selection model.
3. No background cleanup daemon.
4. No default git-worktree provider discovery.
5. No scheduler admission schema changes.
6. No live Qoder/runtime expansion.
7. No Local Work Trajectory mutation from runtime/CLI/MCP/Host UX code.

## Validation

Minimum validation:

1. `python -m py_compile` over touched runtime/test modules.
2. Focused tests for one-shot workflow allocate/read/cleanup/read.
3. Focused tests for daemon-loop workflow allocate/read/cleanup/read.
4. Focused regression that cleanup is rejected unless explicitly opted in.
5. Focused JSON serialization checks for workflow results.

## Write-Back Targets

On close, update:

1. `design_docs/Project Master Checklist.md`
2. `design_docs/Global Phase Map and Current Position.md`
3. `.codex/checkpoints/latest.md`
4. `review/host-workflow-allocate-read-cleanup-read-2026-06-21.md`

## Completion Criteria

This gate is complete when backend callers have one explicit helper that can
perform the git-worktree allocation receipt lifecycle end to end for both
one-shot host runs and bounded host daemon loops, while preserving cleanup as a
separate opt-in authority.

## Close Summary

Completed on 2026-06-21.

`tools.progress_graph.host_sandbox_receipt_workflow` now provides
`HostSandboxReceiptWorkflowRequest`, `HostSandboxReceiptWorkflowResult`, and
`run_host_sandbox_receipt_workflow()`. The helper supports `run_once` and
`daemon_loop` modes, composes existing host-run / host-daemon adapters with
focused Host Evidence presentation readback, and invokes
`run_sandbox_allocation_cleanup_over_receipts()` only when `cleanup=True`.

Focused tests cover:

1. one-shot host run allocation evidence, readback, cleanup, and post-cleanup
   readback;
2. bounded host daemon-loop allocation evidence, readback, cleanup, and
   post-cleanup readback;
3. fail-closed cleanup output validation when cleanup is not explicitly opted
   in;
4. JSON-safe workflow result payloads.
