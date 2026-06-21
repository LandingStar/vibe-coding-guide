# Review - Daemon Supervisor CLI/MCP Surface

> Date: 2026-06-21
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-21-daemon-supervisor-cli-mcp-surface.md`

## Scope Reviewed

This slice exposed the host-managed daemon supervisor step through explicit
operator invocation surfaces.

Implemented:

1. CLI action:
   - `doc-based-coding scheduler lifecycle supervisor-step`
2. GovernanceTools method:
   - `scheduler_daemon_supervisor_step()`
3. MCP tool registration and routing:
   - `schedulerDaemonSupervisorStep`
4. Prompt/audit guidance:
   - `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
   - `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
   - `design_docs/tooling/MCP Tool Surface Audit.md`
5. Focused CLI/MCP/server/prompt tests.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/__main__.py src/mcp/tools.py src/mcp/server.py src/runtime/orchestration/scheduler_daemon_supervisor.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "scheduler_lifecycle_cli"
5 passed, 38 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "scheduler_lifecycle or scheduler_daemon_supervisor"
5 passed, 8 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler"
2 passed, 18 deselected
```

Wider related validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py
13 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_tools.py
86 passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "scheduler_daemon_supervisor or scheduler_daemon_harness or scheduler_daemon_lifecycle"
19 passed, 230 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py
43 passed
```

## Behavioral Notes

`doc-based-coding scheduler lifecycle supervisor-step` and
`schedulerDaemonSupervisorStep`:

1. require explicit supervisor identity and lifecycle control path;
2. remain fake-runtime-only;
3. accept supervisor/session/run/host/requester identity fields;
4. accept cancellation-source and cancellation-reason fields;
5. accept the same bounded harness and policy controls as lifecycle harness;
6. return supervisor result JSON with status readback and
   `harness_policy_result`;
7. expose authority facts showing no OS service, background process, timers,
   watchers, projection refresh, cleanup, ExchangeArtifact mutation, admission
   ledger mutation, or Local Work Trajectory mutation.

## Explicit Non-Goals Preserved

This slice did not:

1. change `run_scheduler_daemon_supervisor_step()` semantics;
2. change harness or policy semantics;
3. add Host UX binding;
4. run live Qoder or any real provider;
5. start an OS service, watcher, timer, or unbounded daemon;
6. refresh scheduler projection automatically;
7. execute or hide cleanup;
8. mutate ExchangeArtifact lifecycle or admission ledger state;
9. mutate Local Work Trajectory from scheduler runtime, CLI, or MCP code;
10. bind agent home, scratch retention, or context-session storage lifecycle.

## Follow-Up

The supervisor step is now reachable from Codex/MCP and CLI operator paths.
The next narrow slice should dogfood the supervisor surface through a
deterministic lifecycle workflow before adding agent-home/context-session
storage binding.
