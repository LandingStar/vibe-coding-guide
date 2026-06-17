# Planning Gate — Host-Authorized Scheduler Runner Adapter

> Date: 2026-06-17
> Status: COMPLETED

## Trigger

`design_docs/stages/planning-gate/2026-06-16-agent-runtime-adapter-and-scheduler-skeleton.md`
has reached `READY-FOR-CLOSE-REVIEW`.

The skeleton now has:

1. `run_persisted_scheduler_once_with_wiring()`.
2. `RuntimeHostInvocation`.
3. `RuntimeProviderPermissionGrant`.
4. Fake-only MCP `schedulerRunOnceAndProject`.
5. Mockable Qoder runtime wiring tests.
6. Scheduler projection artifacts separated from agent-owned Local Work
   Trajectory.

The next step is to make this host-wired one-shot runner dogfoodable without
turning MCP into a real-provider execution surface and without importing the
real Qoder SDK.

## Authority Inputs

- `design_docs/agent-runtime-adapter-and-scheduler-followup-direction-analysis.md`
- `review/agent-runtime-adapter-and-scheduler-skeleton-2026-06-17.md`
- `review/host-authorized-scheduler-runner-adapter-2026-06-17.md`
- `design_docs/stages/planning-gate/2026-06-16-agent-runtime-adapter-and-scheduler-skeleton.md`
- `design_docs/qoder-runtime-adapter-requirements.md`
- `design_docs/agent-runtime-layering-and-orchestration-slice-plan.md`
- `design_docs/tooling/MCP Tool Surface Audit.md`
- `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`

## Problem

The scheduler can now recover, drain, write back snapshot state, and refresh a
scheduler-derived projection. However, the host-authorized execution seam is
still only a low-level Python helper plus tests.

Without a narrow host adapter product:

1. Host UX code would need to assemble runtime wiring details ad hoc.
2. Fake smoke and mock-Qoder smoke would not share one auditable result shape.
3. It would be too easy to expose `qoder` through MCP by mistake.
4. Later daemon, real SDK, or sandbox work would lack a stable one-shot runner
   boundary to wrap.

## Scope

This gate creates a thin host adapter over existing scheduler runner facilities.

### Slice 1 — Host Runner Request / Result Contract

Define project-owned request and result objects for one host-authorized
scheduler run.

The request should contain:

1. Snapshot path.
2. Scheduler event log path.
3. Optional merge-gate event log path.
4. Optional projection output path.
5. Runtime providers.
6. Host invocation metadata.
7. Optional qoder permission grant.
8. Optional policy knobs such as max runs and timestamp.

The result should contain:

1. Snapshot path and event log path.
2. Runtime providers actually registered.
3. Host invocation surface.
4. Run count.
5. Stop reason.
6. Remaining ready / blocked / failed task IDs.
7. Permission review count or task IDs.
8. Produced output artifact refs.
9. Scheduler projection path.
10. Compact history/log summary references for the run, including scheduler
    event-log path, optional merge-gate event-log path, and any
    `ExchangeArtifact` source-log clues returned by intake tools.
11. Authority split flags showing Local Work Trajectory was not mutated.

`ExchangeArtifact` already carries the historical communication `log` payload
part. That log is the place for timestamp, actor, action, channel, summary,
related artifact IDs, related event IDs, related run IDs, sequence, and clock.
The host runner result should reference or summarize those compact log clues
for history management, but it must not duplicate raw runtime transcripts or
turn scheduler JSONL events into the communication product authority.

### Slice 2 — Thin Host Adapter Function

Implement a local Python entry that:

1. Builds runtime registry wiring from the request.
2. Allocates the existing shared-process sandbox provider for this gate.
3. Calls `run_persisted_scheduler_once_with_wiring()`.
4. Refreshes the scheduler-derived projection.
5. Returns the compact result contract.

The adapter must be thin. It must not:

1. Decide task readiness itself.
2. Mutate scheduler state outside the existing persisted runner.
3. Reconstruct task contracts from event logs.
4. Mutate `.codex/progress-graph/local-work-trajectory.json`.
5. Import, construct, or execute the real Qoder SDK.

### Slice 3 — Fake And Mock-Qoder Validation

Prove two paths:

1. Fake runtime path: deterministic local smoke with projection refresh.
2. Mock-Qoder path: host-authorized `RuntimeRegistryWiringResult` with injected
   mock `QoderQueryClient`.

The mock-Qoder path must prove that:

1. `RuntimeHostInvocation(surface="host-authorized-adapter")` is required.
2. `RuntimeProviderPermissionGrant` is required.
3. The result records provider and host surface metadata.
4. MCP remains fake-only and rejects `runtimeProvider="qoder"`.

### Slice 4 — Prompt / Maintenance Guidance

Update or add prompt guidance for agents that need to exercise scheduler state:

1. Submit scheduler task contracts.
2. Project queued scheduler state.
3. Run one host-authorized scheduler pass.
4. Inspect projection and event logs.
5. Preserve the authority split between scheduler projection and agent-owned
   Local Work Trajectory.

## Non-Goals

This gate does not:

1. Import or execute the real Qoder SDK.
2. Add real opencode execution.
3. Start a scheduler daemon.
4. Implement real process parallelism.
5. Implement Docker, remote VM, or git-worktree sandbox isolation.
6. Add retry, timeout, cancellation, or event-log rotation policy.
7. Expose qoder through MCP.
8. Let scheduler tools mutate agent-owned Local Work Trajectory.
9. Let runtime subagents become project-level lanes.

## Required Design Decisions

Before implementation, the gate must fix:

1. Whether the host adapter lives under `src/runtime/orchestration/` or a
   separate host-facing module.
2. Whether the result contract should be a dataclass only or also a
   JSON-serializable helper.
3. How to report permission review tasks compactly without approving them.
4. Which prompt should be updated: extend `07-scheduler-mcp-smoke.md` or add a
   new host-runner prompt.
5. Whether projection refresh is mandatory or optional for the host adapter.
6. Which compact history fields from scheduler events and exchange `log` parts
   are exposed on the host-runner result, without treating raw transcripts as
   authoritative coordination history.

## Acceptance Criteria

The gate may close only when:

1. A host runner request/result contract exists and is JSON-serializable.
2. A fake runtime scheduler run can complete through the host adapter and write
   a scheduler projection.
3. A mock-Qoder scheduler run can complete only through
   `host-authorized-adapter` with explicit grant and injected client.
4. MCP `schedulerRunOnceAndProject` still rejects `qoder` and remains fake-only.
5. The result contract exposes runtime providers, host surface, stop reason,
   run count, output artifact refs, compact history/log references, and
   authority split flags.
6. Focused tests cover fake success, mock-Qoder success, missing host
   invocation or grant rejection, and MCP fake-only behavior.
7. Prompt / maintenance guidance explains the submit -> project -> host-run ->
   inspect loop without replacing `localTrajectory`.

## Implementation Notes

### 2026-06-17 — Slice 1-3 Runtime And Projection Adapter

Implemented:

1. `src/runtime/orchestration/scheduler_host_runner.py`
   - `HostSchedulerRunRequest`
   - `HostSchedulerRunResult`
   - `run_host_authorized_scheduler_once()`
2. `HostSchedulerRunResult.to_json_dict()` now exposes:
   - snapshot and event-log paths
   - optional merge-gate event-log path
   - optional scheduler projection path
   - registered runtime providers
   - host invocation surface / invocation ID / requester
   - run count and stop reason
   - ready / blocked / failed task IDs
   - permission-review task IDs and count
   - output artifact refs
   - compact history summary
   - authority split flags proving agent-owned Local Work Trajectory was not
     mutated
3. `tools/progress_graph/scheduler_projection.py`
   - `HostSchedulerRunProjectionRefreshResult`
   - `run_host_authorized_scheduler_once_and_refresh_projection()`
4. Exports updated in:
   - `src/runtime/orchestration/__init__.py`
   - `tools/progress_graph/__init__.py`
5. Scheduler prompt guidance updated in:
   - `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
   - `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`

Boundary kept:

1. `src/runtime/orchestration` still does not import `tools.progress_graph`.
2. MCP `schedulerRunOnceAndProject` remains fake-only.
3. No real Qoder SDK is imported or constructed.
4. No scheduler tool mutates `.codex/progress-graph/local-work-trajectory.json`.

Focused validation:

```text
pytest tests/test_runtime_orchestration.py -k "host_scheduler_runner or run_persisted_scheduler_once_with"
5 passed

pytest tests/test_progress_graph_trajectory.py -k "host_authorized_scheduler_run_and_refresh_projection or run_persisted_scheduler_once_and_refresh_projection"
2 passed

pytest tests/test_mcp_tools.py -k "scheduler_run_once_and_project"
3 passed

pytest tests/test_mcp_tools.py -k "scheduler_submit_tasks"
4 passed

pytest tests/test_doc_loop_prompts.py -k "scheduler_mcp"
1 passed

pytest tests/test_mcp_prompts_resources.py
21 passed

pytest tests/test_runtime_orchestration.py tests/test_mcp_tools.py tests/test_progress_graph_trajectory.py tests/test_doc_loop_prompts.py tests/test_mcp_prompts_resources.py
280 passed, 1 skipped
```

Close-review evidence:

- `review/host-authorized-scheduler-runner-adapter-2026-06-17.md`

### 2026-06-17 — Close Writeback

Closed after close-review evidence confirmed all acceptance criteria:

1. Host runner request/result contract is JSON-serializable.
2. Fake and mock-Qoder host-authorized paths are covered by focused tests.
3. MCP scheduler execution remains fake-only.
4. Scheduler projection refresh remains separate from agent-owned Local Work
   Trajectory.
5. Prompt / maintenance guidance covers the submit -> project -> host-run ->
   inspect loop.

Selected follow-up gate:

- `design_docs/stages/planning-gate/2026-06-17-controlled-host-runtime-dogfood-harness.md`

## Recommended First Implementation Bias

Prefer a small Python module near the existing orchestration runner.

Do not introduce a new daemon, CLI installer, VS Code UI binding, or real SDK
wrapper in this gate.
