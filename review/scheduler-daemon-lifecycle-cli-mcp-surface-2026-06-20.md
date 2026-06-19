# Review - Scheduler Daemon Lifecycle CLI/MCP Surface

> Date: 2026-06-20
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-20-scheduler-daemon-lifecycle-cli-mcp-surface.md`

## Scope Reviewed

This slice exposed the completed scheduler daemon lifecycle control contract
through explicit local operator and MCP surfaces.

Implemented:

1. CLI scheduler lifecycle namespace:
   - `doc-based-coding scheduler lifecycle inspect`
   - `doc-based-coding scheduler lifecycle start`
   - `doc-based-coding scheduler lifecycle heartbeat`
   - `doc-based-coding scheduler lifecycle pause`
   - `doc-based-coding scheduler lifecycle resume`
   - `doc-based-coding scheduler lifecycle cancel`
   - `doc-based-coding scheduler lifecycle shutdown`
   - `doc-based-coding scheduler lifecycle run-once`
2. MCP lifecycle tools:
   - `schedulerLifecycleControl`
   - `schedulerLifecycleRunOnce`
3. MCP server tool listing, JSON schema, and call routing.
4. Scheduler MCP smoke prompt guidance in repo-local and bootstrap copies.
5. Focused CLI and MCP tests for lifecycle transitions, fake-runtime run-once,
   server exposure, and prompt discoverability.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m py_compile src/__main__.py src/mcp/tools.py src/mcp/server.py
passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py -k "scheduler_lifecycle"
2 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py -k "scheduler_lifecycle"
2 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler_mcp"
1 passed
```

Wider regression:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py
34 passed

.\.venv\Scripts\python.exe -m pytest tests/test_mcp_admission.py
5 passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py
191 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py
20 passed
```

## Behavioral Notes

CLI lifecycle actions require an explicit `--control-path`. `start` also
requires explicit scheduler snapshot path, event-log path, and daemon id.
`run-once` remains fake-runtime only and is lifecycle-gated by the control
file.

The MCP control tool mirrors deterministic lifecycle control-file actions and
adds the runtime-supported `mark_stale` action for explicit stale marking.
Relative MCP paths resolve under the MCP project root.

## Authority Boundary

The authority split remains:

1. Lifecycle control actions write only the scheduler daemon lifecycle control
   file.
2. `run-once` may mutate scheduler snapshot/event-log state only through
   `run_scheduler_daemon_lifecycle_once()`.
3. Scheduler projection refresh remains explicit and separate.
4. Real providers remain outside this generic MCP lifecycle surface.
5. Local Work Trajectory remains agent-owned and is not mutated by scheduler
   code, CLI scheduler lifecycle commands, or MCP scheduler lifecycle tools.
6. ExchangeArtifact store and admission ledger are not touched.

## Explicit Non-Goals Preserved

This slice did not add:

1. Persistent background daemon process.
2. Sleep / polling / filesystem watch / OS service registration / process
   supervision.
3. Real Qoder or other external provider execution through generic MCP.
4. Host UX lifecycle binding.
5. Automatic scheduler projection refresh from lifecycle actions.
6. ExchangeArtifact lifecycle or admission ledger mutation.
7. Scheduler task admission, event-log compaction, or projection semantic
   changes.

## Follow-Up

The lifecycle control contract now has runtime, CLI, and MCP surfaces. The next
slice should either bind lifecycle readback/control into the Host UX over this
stable surface, or defer UI and continue backend orchestration policy work such
as edit-lease conflict expansion.
