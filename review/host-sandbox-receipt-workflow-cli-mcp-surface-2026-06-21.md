# CLI/MCP Surface For Host Sandbox Receipt Workflow Review

> Date: 2026-06-21
> Gate: `design_docs/stages/planning-gate/2026-06-21-host-sandbox-receipt-workflow-cli-mcp-surface.md`
> Status: PASSED

## Scope

This slice exposed the existing host sandbox receipt workflow through operator
surfaces:

- added CLI `doc-based-coding scheduler sandbox-receipt-workflow`;
- added MCP `schedulerSandboxReceiptWorkflow`;
- supported `run-once` and `daemon-loop` modes;
- required explicit scheduler snapshot, event log, source git repo,
  git-worktree sandbox root, and allocation evidence id inputs;
- preserved fake-only CLI/MCP runtime wiring;
- preserved explicit cleanup via `--cleanup` / `cleanup=true`;
- reused `run_host_sandbox_receipt_workflow()` as the only lifecycle
  implementation.

## Evidence

Validation commands:

```powershell
.\.venv\Scripts\python.exe -m py_compile src/__main__.py src/mcp/tools.py src/mcp/server.py tests/test_cli.py tests/test_mcp_admission.py
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "sandbox_receipt_workflow" -q
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "sandbox_receipt_workflow" -q
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "scheduler" -q
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -q
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_tools.py -q
```

Results:

- `py_compile`: passed
- focused CLI workflow tests: `3 passed, 37 deselected`
- focused MCP workflow tests: `2 passed, 8 deselected`
- scheduler CLI focused regression: `33 passed, 7 deselected`
- full MCP admission tests: `10 passed`
- full MCP tools tests: `86 passed`

## Boundary

This slice does not add a Host UX button, selector, or confirmation model. It
does not run live Qoder or real-provider CLI/MCP execution, does not register a
default git-worktree provider, does not start a cleanup daemon, does not change
scheduler admission schema, does not refresh scheduler projection, and does not
mutate agent-owned Local Work Trajectory from CLI/MCP/runtime code.

## Residual Risk

The operator surface is now available, but Host UX still has no guided flow for
selecting allocation evidence, invoking cleanup, and presenting the readback
chain. That should be a separate UI/interaction planning gate because it needs a
confirmation and artifact-selection model.
