# Daemon Loop Git-Worktree Opt-In Review

> Date: 2026-06-21
> Gate: `design_docs/stages/planning-gate/2026-06-21-daemon-loop-git-worktree-opt-in.md`
> Status: PASSED

## Scope

This slice mirrored the one-shot host-run git-worktree opt-in into the bounded
host daemon loop:

- added explicit `HostSchedulerDaemonLoopRequest` fields for
  `git_worktree_sandbox_root`, `sandbox_allocation_evidence_id`, and optional
  `sandbox_allocation_evidence_path`;
- registered `GitWorktreeSandboxProvider` only when opt-in is complete;
- required caller-provided `workspace_root` source repository and allocation
  evidence id before git-worktree provider registration;
- preserved caller-supplied sandbox registry behavior;
- collected daemon-loop preflight sandbox allocations and wrote durable
  `sandbox_allocation_receipt_evidence`;
- exposed opt-in and allocation-evidence write facts in
  `HostSchedulerDaemonLoopResult.to_json_dict()`;
- recorded authority facts showing scheduler/runtime/sandbox execution while
  keeping cleanup explicit and not daemon-owned.

## Evidence

Validation commands:

```powershell
.\.venv\Scripts\python.exe -m py_compile src/runtime/orchestration/scheduler_host_daemon.py tests/test_runtime_orchestration.py tools/progress_graph/host_evidence.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "host_scheduler_daemon_loop and git_worktree" -q
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "host_scheduler_daemon_loop" -q
```

Results:

- `py_compile`: passed
- focused daemon-loop git-worktree tests: `2 passed, 231 deselected`
- focused daemon-loop regression: `7 passed, 226 deselected`

## Boundary

The daemon loop still does not perform cleanup. It only allocates when the host
explicitly opts in and writes durable allocation receipt evidence. This slice
does not add Host UX cleanup buttons, default git-worktree provider discovery,
CLI daemon-loop opt-in flags, live Qoder expansion, scheduler admission schema
changes, or Local Work Trajectory mutation from runtime/CLI/MCP/Host UX code.

## Residual Risk

The cleanup surface is explicit and already available through receipt cleanup
runner paths, but daemon-loop callers now have to manage cleanup as part of
their operator workflow. The next useful slice is not another allocation path;
it is a host/operator workflow that makes the allocate-read-cleanup-read cycle
hard to misuse.
