# Planning Gate - Host Loop Workflow Evidence Metadata

> Date: 2026-06-19
> Status: COMPLETED

## Trigger

`design_docs/scheduler-loop-evidence-presentation-polish-followup-direction-analysis.md`
recommends making the host loop projection workflow write compact projection
clues into `scheduler_loop_evidence` metadata, because the presentation surface
can already display those clues when evidence provides them.

## Problem

`run_host_authorized_scheduler_daemon_loop_and_refresh_projection()` composes:

1. host-authorized bounded daemon loop execution;
2. optional `scheduler_loop_evidence` writing;
3. scheduler-derived trajectory projection refresh;
4. compact workflow result readback.

The workflow result has `scheduler_projection_path` and `projection_summary`,
but evidence is currently written by the lower host daemon loop helper before
the projection refresh occurs. As a result, `dbc://host-evidence/presentation`
can show projection clues only for hand-authored or externally enriched
evidence, not reliably for evidence produced by the composed host workflow.

## Scope

### Slice 1 - Compact Projection Metadata

When `run_host_authorized_scheduler_daemon_loop_and_refresh_projection()` writes
`scheduler_loop_evidence`, enrich that evidence with compact workflow metadata
after projection refresh:

1. `scheduler_projection_path`;
2. `scheduler_projection_role="read-only-view"`;
3. `scheduler_projection_refreshed=true`;
4. compact `projection_summary` fields already returned by
   `LocalWorkTrajectory.summary()`;
5. a workflow surface marker that distinguishes composed workflow evidence from
   lower-level daemon-loop evidence.

### Slice 2 - Authority Boundary

Preserve the authority split:

1. scheduler runtime code must not import progress graph projection code;
2. the composed workflow may update its own just-written evidence artifact;
3. evidence schema version remains unchanged;
4. metadata must stay compact and must not embed full trajectory JSON;
5. Local Work Trajectory remains untouched.

### Slice 3 - Validation And Prompt Guidance

Cover:

1. fake host workflow writes evidence with projection metadata;
2. mock-Qoder host workflow writes evidence with projection metadata and
   presentation can display it;
3. no-evidence workflow still refreshes projection without writing evidence;
4. scheduler smoke prompt explains the enriched metadata contract.

## Non-Goals

This gate does not:

1. Change `scheduler_loop_evidence` schema version.
2. Add provider execution or real-provider CLI/MCP surfaces.
3. Add VS Code/UI binding.
4. Start or manage a background daemon service.
5. Change scheduler task execution policy.
6. Mutate ExchangeArtifact store or admission ledger state.
7. Mutate agent-owned Local Work Trajectory.
8. Store full trajectory JSON inside evidence metadata.

## Acceptance Criteria

The gate may close when:

1. Host loop projection workflow evidence durably includes compact projection
   metadata after projection refresh.
2. Existing lower-level host daemon loop evidence remains compatible.
3. Host evidence presentation can surface the enriched workflow metadata through
   existing scheduler-loop presentation fields.
4. Focused tests cover fake and mock-Qoder workflow evidence paths.
5. Scheduler smoke prompt guidance and bootstrap prompt copy document the
   metadata contract.
6. Review/status docs record that UI binding, live provider execution,
   background daemon lifecycle, ExchangeArtifact/admission mutation, and Local
   Work Trajectory mutation remain deferred.

## Implementation Summary

Completed on 2026-06-19.

Implemented:

1. `run_host_authorized_scheduler_daemon_loop_and_refresh_projection()` now
   enriches just-written `scheduler_loop_evidence` after projection refresh.
2. Enriched metadata includes:
   - `workflow_surface="host-loop-projection-workflow"`;
   - `scheduler_projection_path`;
   - `scheduler_projection_role="read-only-view"`;
   - `scheduler_projection_refreshed=true`;
   - compact `scheduler_projection_summary`.
3. Host evidence presentation now prefers explicit workflow metadata when
   displaying scheduler projection refreshed state.
4. Lower-level host daemon loop evidence remains compatible and keeps its
   lower-level surface metadata.
5. Scheduler smoke prompt guidance and bootstrap prompt copy describe the
   metadata contract.

## Validation

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "host_scheduler_daemon_loop_projection or scheduler_loop_evidence_presentation"
4 passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py tests/test_mcp_admission.py tests/test_doc_loop_prompts.py
288 passed, 1 skipped
```

Change analysis:

```text
impact.direct=[]
impact.transitive=[]
coupling.alerts=[]
```

## Non-Goals Preserved

This slice did not add:

1. `scheduler_loop_evidence` schema changes.
2. Provider execution or real-provider CLI/MCP surfaces.
3. VS Code/UI binding.
4. Background daemon service lifecycle.
5. Scheduler task execution policy changes.
6. ExchangeArtifact store or admission ledger mutation.
7. Agent-owned Local Work Trajectory mutation.
8. Full trajectory JSON inside evidence metadata.
