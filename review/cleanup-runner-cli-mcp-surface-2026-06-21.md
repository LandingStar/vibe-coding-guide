# Cleanup Runner CLI/MCP Surface Review

> Date: 2026-06-21
> Gate: `design_docs/stages/planning-gate/2026-06-21-cleanup-runner-cli-mcp-surface.md`
> Status: PASSED

## Scope

This slice exposed the completed sandbox allocation cleanup runner through
explicit operator-facing surfaces:

- added CLI command `doc-based-coding scheduler cleanup-receipts`;
- added MCP tool `schedulerCleanupReceipts`;
- required an explicit input `sandbox_allocation_receipt_evidence` path;
- accepted optional output evidence path/id, timestamp, and git executable;
- reused `run_sandbox_allocation_cleanup_over_receipts()` directly;
- returned the JSON-safe `SandboxCleanupRunnerResult` shape;
- kept scheduler state, host-run, daemon, projection, readback, and Local Work
  Trajectory runtime paths out of the cleanup side-effect boundary.

## Evidence

Validation commands:

```powershell
.\.venv\Scripts\python.exe -m py_compile src/__main__.py src/mcp/tools.py src/mcp/server.py tests/test_cli.py tests/test_mcp_admission.py
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k cleanup_receipts -q
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k cleanup_receipts -q
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "sandbox_allocation_cleanup or sandbox_allocation_receipt or git_worktree or host_scheduler_runner_git_worktree" -q
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_tools.py -q
```

Results:

- `py_compile`: passed
- CLI cleanup focused tests: `3 passed, 34 deselected`
- MCP cleanup focused tests: `2 passed, 6 deselected`
- runtime cleanup/evidence/git focused tests: `16 passed, 215 deselected`
- full CLI tests: `37 passed`
- full tracked MCP admission tests: `8 passed`
- full runtime orchestration tests: `231 passed`
- full MCP tools tests: `86 passed`

## Boundary

Cleanup remains an explicit host/operator/agent action over one named durable
receipt evidence artifact. This slice does not add default evidence discovery,
does not start a cleanup daemon, does not add Host UX controls, does not run
cleanup during host scheduler runs, does not change scheduler admission schema,
does not run live Qoder/runtime, and does not mutate Local Work Trajectory from
runtime, CLI, or MCP code.

## Residual Risk

The cleanup action now has stable CLI/MCP entry points, but operator visibility
is still thin: existing readback and Host UX surfaces do not yet make cleanup
evidence paths, cleanup states, or post-cleanup receipt transitions easy to
inspect from the normal workflow panel.
