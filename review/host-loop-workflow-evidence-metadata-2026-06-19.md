# Review - Host Loop Workflow Evidence Metadata

> Date: 2026-06-19
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-19-host-loop-workflow-evidence-metadata.md`

## Scope Reviewed

This slice made the composed host loop projection workflow write compact
projection clues back into its own `scheduler_loop_evidence` metadata.

Implemented:

1. `run_host_authorized_scheduler_daemon_loop_and_refresh_projection()` now
   enriches just-written evidence after scheduler projection refresh.
2. Enriched metadata includes:
   - `workflow_surface="host-loop-projection-workflow"`;
   - `scheduler_projection_path`;
   - `scheduler_projection_role="read-only-view"`;
   - `scheduler_projection_refreshed=true`;
   - compact `scheduler_projection_summary`.
3. Existing lower-level host daemon loop evidence remains compatible and keeps
   its lower-level surface metadata.
4. Host evidence presentation now prefers explicit workflow metadata for
   scheduler projection refreshed display when present.
5. Scheduler smoke prompt guidance and bootstrap prompt copy were updated.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "host_scheduler_daemon_loop_projection or scheduler_loop_evidence_presentation"
4 passed
```

Full tracked validation will be recorded in the gate after final run.

Full tracked validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py tests/test_mcp_admission.py tests/test_doc_loop_prompts.py
288 passed, 1 skipped
```

Change analysis:

```text
impact.direct=[]
impact.transitive=[]
coupling.alerts=[]
```

## Behavioral Notes

The lower host daemon loop writes evidence before projection refresh. The
composed `tools.progress_graph` workflow therefore enriches only the evidence it
just wrote, after the projection artifact has been created and read back.

This keeps the direction of dependencies clean:

1. scheduler runtime does not import progress graph projection code;
2. progress graph workflow composes runtime execution, projection refresh, and
   evidence metadata enrichment;
3. evidence schema version stays unchanged;
4. evidence metadata remains compact and does not embed full trajectory JSON.

## Authority Boundary

The enriched metadata is a host-workflow readback clue. It does not make the
evidence artifact a scheduler state authority.

This slice did not:

1. add provider execution surfaces;
2. add CLI/MCP real-provider daemon-loop execution;
3. bind VS Code/UI;
4. start a background daemon service;
5. mutate ExchangeArtifact store or admission ledger state;
6. mutate agent-owned Local Work Trajectory.

## Follow-Up

The backend readback chain is now tighter: host workflow execution, projection
refresh, durable evidence, and read-only presentation can carry the same compact
projection clues.

The next decision point is whether to move these completed backend products into
UI binding, or first add more live-provider smoke coverage when credentials are
available.
