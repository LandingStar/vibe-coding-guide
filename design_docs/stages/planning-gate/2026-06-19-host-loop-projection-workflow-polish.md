# Planning Gate - Host Loop Projection Workflow Polish

> Date: 2026-06-19
> Status: COMPLETED

## Trigger

`design_docs/host-injected-scheduler-daemon-loop-followup-direction-analysis.md`
recommends composing host-injected daemon-loop execution, optional
`scheduler_loop_evidence`, and scheduler projection refresh into one explicit
host workflow.

## Problem

The scheduler backend now has:

```text
HostSchedulerDaemonLoopRequest
run_host_authorized_scheduler_daemon_loop()
scheduler_loop_evidence
write_scheduler_work_trajectory_artifact()
dbc://host-evidence/bundle
dbc://host-evidence/presentation
```

However, a host caller still needs to manually run the daemon loop, remember
whether evidence was written, refresh the scheduler-derived trajectory
projection, and then read back a compact machine result. That is awkward for
operator dogfood and future UI binding.

The missing piece is not a new runtime surface. It is a host-owned workflow
helper with an explicit name and result shape that says projection refresh is
part of this helper, not implicit scheduler behavior.

## Scope

### Slice 1 - Host Workflow Contract

Add a host-facing projection workflow result around the existing daemon loop:

```text
HostSchedulerDaemonLoopProjectionRefreshResult
run_host_authorized_scheduler_daemon_loop_and_refresh_projection()
```

The result should expose:

1. the existing host daemon-loop result;
2. the scheduler projection path;
3. the loaded scheduler-derived `LocalWorkTrajectory`;
4. a compact JSON/machine summary;
5. authority clues for provider execution, evidence writing, projection
   refresh, and Local Work Trajectory non-mutation.

### Slice 2 - Composition Behavior

The helper should:

1. call `run_host_authorized_scheduler_daemon_loop()` internally;
2. read scheduler state after the loop;
3. write the scheduler-derived trajectory projection through
   `write_scheduler_work_trajectory_artifact()`;
4. preserve optional `scheduler_loop_evidence` behavior from the request;
5. report projection refresh explicitly in the host result.

### Slice 3 - Validation

Cover:

1. fake host daemon-loop path with projection refresh;
2. mock-Qoder host daemon-loop path with projection refresh and
   `scheduler_loop_evidence`;
3. Local Work Trajectory preservation;
4. compact JSON result shape;
5. prompt guidance that the workflow helper is host-owned and not CLI/MCP
   real-provider exposure.

## Non-Goals

This gate does not:

1. Add CLI or MCP real-provider execution.
2. Start a background daemon/service.
3. Run live Qoder or require credentials.
4. Add VS Code/UI binding.
5. Mutate ExchangeArtifact lifecycle or admission ledger state.
6. Mutate `.codex/progress-graph/local-work-trajectory.json` from scheduler
   code.
7. Change scheduler task submission, queue, daemon-loop, or evidence schemas.

## Acceptance Criteria

The gate may close when:

1. The host daemon-loop projection workflow contract is implemented and
   documented.
2. Fake and mock-Qoder injected runtime paths refresh scheduler projection
   after loop execution.
3. Optional `scheduler_loop_evidence` writing is preserved and visible in the
   compact result.
4. The result reports `scheduler_projection_refreshed=true` while
   `local_work_trajectory_mutated=false`.
5. Focused tests cover runtime/projection behavior and prompt guidance.
6. Review/status docs record that CLI/MCP real-provider surfaces, live
   provider execution, background daemon lifecycle, UI binding,
   ExchangeArtifact/admission mutation, and scheduler-owned Local Work
   Trajectory mutation remain deferred.

## Implementation Summary

Completed on 2026-06-19.

This slice added a host-owned workflow helper that composes the existing
host-injected scheduler daemon loop with explicit scheduler-derived trajectory
projection refresh.

Implemented:

1. Host workflow contract:
   - `HostSchedulerDaemonLoopProjectionRefreshResult`
   - `run_host_authorized_scheduler_daemon_loop_and_refresh_projection()`
2. Composition behavior:
   - calls `run_host_authorized_scheduler_daemon_loop()` internally;
   - preserves fake and mock-Qoder host runtime wiring;
   - preserves optional `scheduler_loop_evidence` writing from
     `HostSchedulerDaemonLoopRequest`;
   - reads scheduler state after loop execution and writes the read-only
     scheduler projection artifact.
3. Compact result readback:
   - includes `scheduler_projection_path`;
   - includes `projection_summary`;
   - reports `scheduler_projection_refreshed=true`;
   - reports `local_work_trajectory_mutated=false`.
4. Prompt guidance:
   - `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`;
   - bootstrap copy under `doc-loop-vibe-coding/assets/bootstrap/`.

## Validation

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

## Non-Goals Preserved

This slice did not add:

1. CLI or MCP real-provider execution.
2. Live Qoder/provider execution.
3. Background daemon/service lifecycle management.
4. VS Code/UI binding.
5. ExchangeArtifact lifecycle mutation.
6. Admission ledger mutation.
7. Scheduler-owned Local Work Trajectory mutation.
8. Scheduler task submission, queue, daemon-loop, or evidence schema changes.
