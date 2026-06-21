# Host Workflow For Allocate-Read-Cleanup-Read Review

> Date: 2026-06-21
> Gate: `design_docs/stages/planning-gate/2026-06-21-host-workflow-allocate-read-cleanup-read.md`
> Status: PASSED

## Scope

This slice added a backend host/operator workflow helper for the explicit
git-worktree receipt lifecycle:

- added `tools.progress_graph.host_sandbox_receipt_workflow`;
- introduced `HostSandboxReceiptWorkflowRequest`,
  `HostSandboxReceiptWorkflowResult`, and workflow step summaries;
- supported both `run_once` and `daemon_loop` modes;
- reused existing host-run, host-daemon, cleanup runner, and Host Evidence
  presentation products;
- required `cleanup=True` before cleanup evidence output can be requested or
  cleanup can execute;
- returned JSON-safe payloads with allocation/cleanup evidence paths,
  readback presentation payloads, step status, and authority facts;
- kept CLI, MCP, Host UX, scheduler admission schema, and default provider
  behavior unchanged.

## Evidence

Validation commands:

```powershell
.\.venv\Scripts\python.exe -m py_compile tools/progress_graph/host_sandbox_receipt_workflow.py tools/progress_graph/__init__.py tests/test_runtime_orchestration.py
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "host_sandbox_receipt_workflow" -q
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "host_scheduler_runner_git_worktree or host_scheduler_daemon_loop_git_worktree or host_sandbox_receipt_workflow" -q
.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "host_evidence_bundle_reads_sandbox_allocation_cleanup_evidence or host_evidence_cleanup_evidence_failed_state_takes_precedence" -q
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -q
```

Results:

- `py_compile`: passed
- focused workflow tests: `3 passed, 233 deselected`
- adjacent host/git/workflow regression: `7 passed, 229 deselected`
- focused Host Evidence cleanup readback regression: `2 passed, 66 deselected`
- full runtime orchestration file: `236 passed`

## Boundary

The workflow helper does not create a new cleanup policy. It composes existing
explicit cleanup authority and refuses cleanup output parameters unless cleanup
is explicitly requested. This slice does not expose CLI/MCP commands, add Host
UX buttons, start a background cleanup daemon, register a default git-worktree
provider, change scheduler admission schemas, or mutate agent-owned Local Work
Trajectory from runtime/CLI/MCP/Host UX code.

## Residual Risk

The backend helper is now usable by callers, but there is no operator command
surface yet. A later CLI/MCP binding should call this helper instead of
re-implementing the lifecycle, preserving one contract for future Host UX.
