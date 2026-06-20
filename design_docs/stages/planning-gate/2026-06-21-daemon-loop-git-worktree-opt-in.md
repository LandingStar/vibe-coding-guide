# Daemon Loop Git-Worktree Opt-In

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/host-ux-cleanup-evidence-readback-linkage-followup-direction-analysis.md`
recommends extending bounded host daemon loop requests with explicit
git-worktree sandbox opt-in now that cleanup receipt visibility exists.

Current chain:

```text
HostSchedulerDaemonLoopRequest
-> host-owned runtime and sandbox wiring
-> run_scheduler_daemon_loop()
-> durable sandbox_allocation_receipt_evidence
-> Host Evidence readback visibility
```

## Goal

Allow host-owned bounded daemon-loop runs to opt into `GitWorktreeSandboxProvider`
with explicit source repository root, sandbox root, and allocation evidence
id/path, then write durable `sandbox_allocation_receipt_evidence` from daemon
loop preflight allocation attempts.

The first slice should prove:

1. daemon loop git-worktree sandbox use is explicit and fail-closed;
2. default fake/shared-process daemon loop behavior is unchanged;
3. daemon loop writes durable sandbox allocation receipt evidence when an
   evidence id is supplied;
4. cleanup remains explicit and outside daemon loop;
5. Host Evidence readback can see the produced allocation evidence.

## Scope

1. Add explicit git-worktree opt-in fields to `HostSchedulerDaemonLoopRequest`.
2. Register `GitWorktreeSandboxProvider` only when opt-in is complete.
3. Preserve caller-supplied sandbox registry behavior.
4. Write durable `sandbox_allocation_receipt_evidence` from loop preflight
   sandbox allocations when evidence id is supplied.
5. Expose compact opt-in/evidence facts in `HostSchedulerDaemonLoopResult`.
6. Add focused runtime tests using a real temporary git repository and
   Host Evidence readback smoke.
7. Update status docs and review evidence on close.

## Non-Goals

1. No Host UX cleanup button.
2. No automatic cleanup in daemon loop.
3. No background daemon service behavior change.
4. No CLI `scheduler daemon-loop` git-worktree opt-in in this slice.
5. No broad evidence discovery.
6. No scheduler admission schema changes.
7. No live Qoder/runtime expansion.
8. No Local Work Trajectory mutation from runtime/CLI/MCP/Host UX code.

## Validation

Minimum validation:

1. `python -m py_compile` over touched runtime/test modules.
2. Focused runtime tests for daemon-loop git-worktree opt-in validation and
   durable allocation evidence writeback.
3. Focused Host Evidence readback smoke over the produced evidence.
4. Focused regression that default daemon-loop result remains fake/shared-process
   and JSON-safe.

## Write-Back Targets

On close, update:

1. `design_docs/Project Master Checklist.md`
2. `design_docs/Global Phase Map and Current Position.md`
3. `.codex/checkpoints/latest.md`
4. `review/daemon-loop-git-worktree-opt-in-2026-06-21.md`

## Completion Criteria

This gate is complete when host-owned daemon loop git-worktree opt-in can
allocate a real temporary git worktree, write durable sandbox allocation receipt
evidence, expose the evidence through Host Evidence readback, and still keep
cleanup explicit and out of daemon loop execution.

## Close Summary

Completed on 2026-06-21.

`HostSchedulerDaemonLoopRequest` now supports explicit git-worktree sandbox
opt-in through `git_worktree_sandbox_root`, `sandbox_allocation_evidence_id`,
and optional `sandbox_allocation_evidence_path`. The host daemon adapter
registers `GitWorktreeSandboxProvider` only when opt-in is complete, writes
durable `sandbox_allocation_receipt_evidence` from loop preflight allocation
attempts, and exposes compact opt-in/evidence fields plus authority facts in
`HostSchedulerDaemonLoopResult`.

Cleanup remains explicit and outside daemon-loop execution. Focused tests cover
fail-closed opt-in validation, real temporary git worktree allocation, durable
receipt writeback, Host Evidence presentation readback, and default daemon-loop
fake/shared-process regression.
