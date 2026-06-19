# Review - Host Loop Projection Workflow Polish

> Date: 2026-06-19
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-19-host-loop-projection-workflow-polish.md`

## Scope Reviewed

This slice added a host-owned helper that composes bounded host daemon-loop
execution, optional scheduler-loop evidence writing, scheduler projection
refresh, and compact readback.

Implemented:

1. Projection workflow contract:
   - `HostSchedulerDaemonLoopProjectionRefreshResult`
   - `run_host_authorized_scheduler_daemon_loop_and_refresh_projection()`
2. Export from `tools.progress_graph`.
3. Fake host daemon-loop projection validation.
4. Mock-Qoder host daemon-loop projection plus `scheduler_loop_evidence`
   validation.
5. Prompt guidance and bootstrap prompt copy updates.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "host_scheduler_daemon_loop_and_refresh_projection or host_scheduler_daemon_loop_projection"
2 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k scheduler_mcp_smoke_prompt
1 passed

.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "host_scheduler_daemon_loop_and_refresh_projection or host_scheduler_daemon_loop_projection or host_authorized_scheduler_run_and_refresh_projection"
3 passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py tests/test_mcp_admission.py tests/test_doc_loop_prompts.py
285 passed, 1 skipped
```

Change analysis:

```text
impact.direct=[]
impact.transitive=[]
coupling.alerts=[]
```

## Behavioral Notes

`run_host_authorized_scheduler_daemon_loop_and_refresh_projection()` lives in
`tools.progress_graph.scheduler_projection`, matching the earlier one-shot
projection helper. The runtime orchestration package still does not depend on
progress graph projection code.

The helper calls `run_host_authorized_scheduler_daemon_loop()`, then reads the
resulting scheduler snapshot and writes
`.codex/progress-graph/scheduler-work-trajectory.json` unless an explicit
projection output path is supplied.

The compact result keeps the daemon-loop payload available while adding:

1. `scheduler_projection_path`;
2. `projection_summary`;
3. `authority_split.scheduler_projection_refreshed=true`;
4. `authority_split.scheduler_projection_role="read-only-view"`;
5. `authority_split.local_work_trajectory_mutated=false`.

## Authority Boundary

The authority split remains:

1. Scheduler snapshot and event log are scheduler authority.
2. Runtime registry construction is host authority.
3. Scheduler-loop evidence is a review/readback artifact.
4. Scheduler projection is a read-only progress graph view.
5. Local Work Trajectory remains agent-owned.
6. CLI/MCP scheduler loop surfaces remain fake-runtime-only.
7. ExchangeArtifact store and admission ledger are not touched by this
   workflow.

## Explicit Non-Goals Preserved

This slice did not add:

1. CLI or MCP real-provider execution.
2. Live Qoder/provider execution.
3. Background daemon/service lifecycle management.
4. VS Code/UI binding.
5. ExchangeArtifact lifecycle mutation.
6. Admission ledger mutation.
7. Scheduler-owned Local Work Trajectory mutation.
8. Scheduler task submission, queue, daemon-loop, or evidence schema changes.

## Follow-Up

The next backend-oriented polish point is the readback/presentation side of
scheduler-loop evidence. Host execution and projection now have one compact
workflow; the remaining roughness is how `dbc://host-evidence/presentation`
summarizes loop evidence and projection clues for operators or future UI.
