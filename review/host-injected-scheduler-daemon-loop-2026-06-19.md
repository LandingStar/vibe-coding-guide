# Review - Host-Injected Scheduler Daemon Loop

> Date: 2026-06-19
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-19-host-injected-scheduler-daemon-loop.md`

## Scope Reviewed

This slice added a host-owned Python adapter for bounded scheduler daemon loops
with explicit runtime injection.

Implemented:

1. Runtime contract:
   - `HostSchedulerDaemonLoopRequest`
   - `HostSchedulerDaemonLoopResult`
   - `run_host_authorized_scheduler_daemon_loop()`
2. Runtime wiring integration:
   - fake host loop path;
   - mock-Qoder host loop path;
   - qoder rejection without host-authorized surface, permission grant, or
     injected client.
3. Optional scheduler-loop evidence writing from host path.
4. Prompt guidance and bootstrap prompt copy updates.
5. Tests covering host loop behavior, evidence write/readback, prompt guidance,
   and unchanged CLI fake-only behavior.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "host_scheduler_daemon_loop"
5 passed

.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "host_scheduler_daemon_loop or scheduler_daemon_loop or scheduler_loop_evidence"
10 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py tests/test_cli.py -k "scheduler_daemon_loop or scheduler_mcp_smoke_prompt"
5 passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py tests/test_mcp_admission.py tests/test_doc_loop_prompts.py
283 passed, 1 skipped
```

## Behavioral Notes

`run_host_authorized_scheduler_daemon_loop()` builds a runtime registry through
`RuntimeRegistryWiringConfig`, then injects that registry into
`run_scheduler_daemon_loop()`. This keeps daemon-loop policy, queue summaries,
and stop reasons centralized in the existing scheduler daemon module.

When `evidence_id` is provided, the helper writes `scheduler_loop_evidence`
through the same evidence product used by the CLI loop. Existing read-only
host evidence resources can consume that artifact without new resource URIs.

## Authority Boundary

The authority split remains:

1. Scheduler snapshot and event log are scheduler authority.
2. Runtime registry construction is host authority.
3. Scheduler-loop evidence is a review/readback artifact, not replay authority.
4. CLI/MCP scheduler loop surfaces remain fake-runtime-only.
5. Scheduler projection remains explicit and is not auto-refreshed.
6. Local Work Trajectory remains agent-owned.
7. ExchangeArtifact store and admission ledger are not touched by host loop
   execution.

## Explicit Non-Goals Preserved

This slice did not add:

1. CLI or MCP real-provider execution.
2. Live Qoder/provider execution.
3. Background daemon/service lifecycle management.
4. UI binding.
5. Automatic scheduler projection refresh.
6. ExchangeArtifact lifecycle mutation.
7. Admission ledger mutation.
8. Local Work Trajectory mutation from scheduler code.

## Follow-Up

The next backend-oriented gap is workflow polish around host-loop evidence and
projection readback: a host caller can now run and write loop evidence, but
projection refresh remains a separate operator action.


