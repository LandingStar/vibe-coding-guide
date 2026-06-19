# Planning Gate - Scheduler Loop Evidence Presentation Polish

> Date: 2026-06-19
> Status: COMPLETED

## Trigger

`design_docs/host-loop-projection-workflow-polish-followup-direction-analysis.md`
recommends improving the read-only presentation surface for
`scheduler_loop_evidence` before moving to UI binding or live provider smoke.

## Problem

The backend can now run a host-injected bounded daemon loop, optionally write
`scheduler_loop_evidence`, refresh scheduler-derived projection through an
explicit host workflow, and return compact workflow readback.

The remaining operator gap is that `dbc://host-evidence/presentation`
summarizes scheduler-loop evidence too generically. It shows core loop counts,
but host/runtime authority, host invocation clues, and projection-related
metadata are not surfaced clearly enough for future UI or manual inspection.

## Scope

### Slice 1 - Scheduler Loop Card Facts

Improve `SchedulerLoopEvidenceSummary` presentation cards by surfacing:

1. runtime provider;
2. runtime host surface when present in evidence metadata;
3. host invocation id when present in evidence metadata;
4. tick/run/event counts;
5. completed/ready/blocked/failed queue counts;
6. stop reason/detail.

### Slice 2 - Projection And Authority Clues

When evidence metadata or authority split contains projection clues, the card
should expose them as stable facts/refs:

1. `scheduler_projection_path`;
2. `scheduler_projection_refreshed`;
3. `scheduler_projection_role`;
4. `local_work_trajectory_mutated`;
5. provider execution and scheduler state mutation clues.

Old evidence that lacks projection metadata must still render without errors.

### Slice 3 - Validation And Prompt Guidance

Cover:

1. scheduler-loop evidence presentation with host/projection metadata;
2. scheduler-loop evidence presentation without projection metadata;
3. malformed evidence isolation remains unchanged;
4. prompt guidance explains the read-only presentation role.

## Non-Goals

This gate does not:

1. Change `scheduler_loop_evidence` schema.
2. Add provider execution or real-provider CLI/MCP surfaces.
3. Refresh scheduler projection.
4. Mutate scheduler state, ExchangeArtifact store, admission ledger, or Local
   Work Trajectory.
5. Add VS Code/UI binding.
6. Start or manage a background daemon service.

## Acceptance Criteria

The gate may close when:

1. Scheduler-loop evidence presentation cards expose host/runtime/queue clues
   as stable JSON.
2. Projection clues are surfaced when available and omitted cleanly when absent.
3. Existing evidence bundle/presentation read-only behavior and malformed
   evidence isolation are preserved.
4. Focused tests cover the new presentation shape.
5. Scheduler smoke prompt guidance and bootstrap prompt copy describe the
   read-only presentation role.
6. Review/status docs record that UI binding, live provider execution,
   scheduler mutation, projection refresh, ExchangeArtifact/admission mutation,
   and Local Work Trajectory mutation remain deferred.

## Implementation Summary

Completed on 2026-06-19.

This slice improved the read-only `dbc://host-evidence/presentation` contract
for `scheduler_loop_evidence`.

Implemented:

1. Scheduler-loop card facts:
   - runtime provider;
   - host surface;
   - host invocation id;
   - tick/run/event counts;
   - completed/ready/blocked/failed queue counts.
2. Projection and authority clues:
   - scheduler projection path when present;
   - scheduler projection role when present;
   - scheduler projection refreshed state;
   - scheduler state/provider/local trajectory authority clues.
3. Compatibility:
   - old scheduler-loop evidence without projection metadata still renders;
   - `metadata.surface` remains evidence generation metadata and does not
     override the card host surface;
   - malformed evidence remains isolated into errors.
4. Prompt guidance:
   - `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`;
   - bootstrap copy under `doc-loop-vibe-coding/assets/bootstrap/`.

## Validation

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "scheduler_loop_evidence_presentation or host_evidence_presentation or host_evidence_bundle_isolates"
6 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "scheduler_mcp_smoke_prompt or host_evidence_resources_read_scheduler_loop_evidence"
2 passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py tests/test_mcp_admission.py tests/test_doc_loop_prompts.py
287 passed, 1 skipped
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
3. Scheduler projection refresh.
4. Scheduler state, ExchangeArtifact store, admission ledger, or Local Work
   Trajectory mutation.
5. VS Code/UI binding.
6. Background daemon service lifecycle.
