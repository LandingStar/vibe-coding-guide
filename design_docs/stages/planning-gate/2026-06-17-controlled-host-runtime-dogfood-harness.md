# Planning Gate — Controlled Host Runtime Dogfood Harness

> Date: 2026-06-17
> Status: COMPLETED

## Trigger

`design_docs/stages/planning-gate/2026-06-17-host-authorized-scheduler-runner-adapter.md`
has reached `READY-FOR-CLOSE-REVIEW`.

The follow-up direction analysis recommends this next narrow slice:

- `design_docs/host-authorized-scheduler-runner-followup-direction-analysis.md`

This gate became active after the host-authorized scheduler runner adapter gate
was accepted for close. It fixes the next narrow dogfood boundary over the
existing host runner without expanding into real SDK execution, daemon behavior,
or UI redesign.

## Problem

The project now has a host-authorized one-shot runner:

```text
HostSchedulerRunRequest
HostSchedulerRunResult
run_host_authorized_scheduler_once()
run_host_authorized_scheduler_once_and_refresh_projection()
```

However, the project still lacks a repeatable dogfood harness that can:

1. Construct an explicit host-run request from stable inputs.
2. Run fake and mock-Qoder scheduler smoke paths through the same host seam.
3. Persist compact evidence for review and later host UX consumption.
4. Keep MCP fake-only while proving host-authorized runtime wiring outside MCP.

Without this harness, the next real-runtime work would have to mix host
permission, runtime client construction, evidence capture, and scheduler
execution in one large slice.

## Authority Inputs

- `design_docs/host-authorized-scheduler-runner-followup-direction-analysis.md`
- `review/host-authorized-scheduler-runner-adapter-2026-06-17.md`
- `design_docs/stages/planning-gate/2026-06-17-host-authorized-scheduler-runner-adapter.md`
- `design_docs/qoder-runtime-adapter-requirements.md`
- `design_docs/agent-runtime-layering-and-orchestration-slice-plan.md`
- `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`

## Scope

This gate creates a narrow host-runtime dogfood harness over the existing host
runner.

### Slice 1 — Evidence JSON Contract

Define a compact host-run evidence artifact.

The evidence JSON should contain:

1. Schema / product type and version.
2. Evidence ID and timestamp.
3. Snapshot path.
4. Scheduler event-log path.
5. Optional merge-gate event-log path.
6. Scheduler projection path.
7. Runtime providers.
8. Host invocation surface, invocation ID, requester, and reason.
9. Run count.
10. Stop reason and stop detail.
11. Ready / blocked / failed task IDs.
12. Permission-review task IDs and count.
13. Output artifact refs.
14. Compact history summary.
15. Authority split flags:
    - scheduler state authority
    - scheduler projection role
    - local work trajectory role
    - local work trajectory mutated flag

The evidence JSON is a review artifact. It is not scheduler state and must not
be used as a source from which tasks are replayed.

### Slice 2 — Fake Runtime Dogfood Harness

Add a local Python entry/helper that:

1. Accepts explicit scheduler snapshot / event-log paths.
2. Builds a `HostSchedulerRunRequest` with fake runtime config.
3. Calls `run_host_authorized_scheduler_once_and_refresh_projection()`.
4. Writes the compact evidence JSON.
5. Returns the evidence path and compact run result.

This path should be deterministic and suitable for tests.

### Slice 3 — Mock-Qoder Host-Authorized Dogfood Harness

Add a mock-Qoder mode that:

1. Requires `RuntimeHostInvocation(surface="host-authorized-adapter")`.
2. Requires `RuntimeProviderPermissionGrant`.
3. Requires an injected `QoderQueryClient`.
4. Writes the same evidence JSON shape as fake mode.
5. Does not import, construct, or execute the real Qoder SDK.

### Slice 4 — Prompt / Maintenance Guidance

Update or add guidance for agents that need to:

1. Create or reuse a scheduler snapshot and event log.
2. Run the host dogfood harness.
3. Inspect evidence JSON and scheduler projection.
4. Preserve the authority split:
   - scheduler state remains scheduler-owned
   - scheduler projection remains read-only
   - Local Work Trajectory remains agent-owned
5. Avoid using MCP as a real-provider execution surface.

## Non-Goals

This gate does not:

1. Import or execute the real Qoder SDK.
2. Add a real opencode runtime.
3. Add a scheduler daemon.
4. Implement real process, Docker, remote VM, or git-worktree isolation.
5. Add retry, timeout, cancellation, or event-log rotation policy.
6. Expose qoder through MCP.
7. Mutate `.codex/progress-graph/local-work-trajectory.json`.
8. Promote runtime subagents to project-level scheduler tasks or trajectory
   lanes.
9. Redesign the VS Code UI.

## Required Design Decisions

Before implementation, this gate must fix:

1. Where the harness lives:
   - `src/runtime/orchestration/`
   - `tools/`
   - or a host-facing helper module
2. Whether the evidence writer returns only a path or a structured result.
3. Whether evidence output path is required or defaults under `.codex/scheduler/`.
4. How fake and mock-Qoder modes select or inject runtime config.
5. Which prompt should own ongoing maintenance guidance.

## Acceptance Criteria

The gate may close only when:

1. A host-run evidence JSON contract exists and is documented.
2. A fake-runtime dogfood run can write that evidence JSON and refresh scheduler
   projection.
3. A mock-Qoder host-authorized dogfood run can write the same evidence shape.
4. Evidence includes provider, host invocation, run count, stop reason, output
   artifact refs, permission-review tasks, history summary, and authority split
   flags.
5. MCP fake-only rejection remains covered.
6. Prompt / maintenance guidance explains how to run, inspect, and write back
   dogfood evidence without using `localTrajectory` as scheduler state.
7. Focused tests cover fake evidence write, mock-Qoder evidence write, missing
   host authorization / grant rejection, and MCP fake-only behavior.

## Recommended First Implementation Bias

Prefer a small helper near the host-runner adapter and a pure evidence JSON
writer. Keep the harness as a caller of existing scheduler runner facilities,
not a second scheduler.

Do not add a daemon, real SDK wrapper, GUI binding, installer behavior, or
sandbox implementation in this gate.

## Implementation Notes

### 2026-06-17 — Slice 1-3 Evidence Contract And Harness

Implemented:

1. `src/runtime/orchestration/scheduler_dogfood.py`
   - `HOST_SCHEDULER_RUN_EVIDENCE_PRODUCT_TYPE`
   - `HOST_SCHEDULER_RUN_EVIDENCE_SCHEMA_VERSION`
   - `HostSchedulerRunEvidence`
   - `HostSchedulerRunEvidenceWriteResult`
   - `build_host_scheduler_run_evidence()`
   - `write_host_scheduler_run_evidence()`
   - `default_host_scheduler_run_evidence_path()`
2. `tools/progress_graph/scheduler_dogfood.py`
   - `HostRuntimeDogfoodHarnessResult`
   - `run_host_runtime_dogfood_harness()`
3. Exports updated in:
   - `src/runtime/orchestration/__init__.py`
   - `tools/progress_graph/__init__.py`

Boundary kept:

1. Runtime layer owns only evidence product construction / writing.
2. The harness that refreshes scheduler projection lives under
   `tools/progress_graph`, so `src/runtime/orchestration` still does not import
   progress graph code.
3. The harness calls existing host runner and projection helpers; it does not
   schedule tasks itself.
4. Mock-Qoder mode still requires `RuntimeHostInvocation`,
   `RuntimeProviderPermissionGrant`, and an injected `QoderQueryClient`.
5. No real Qoder SDK is imported or constructed.
6. MCP `schedulerRunOnceAndProject` remains fake-only.
7. `.codex/progress-graph/local-work-trajectory.json` remains agent-owned.

Focused validation:

```text
pytest tests/test_runtime_orchestration.py -k "host_scheduler_runner or host_scheduler_run_evidence"
3 passed

pytest tests/test_progress_graph_trajectory.py -k "host_runtime_dogfood_harness or host_authorized_scheduler_run"
4 passed

pytest tests/test_mcp_tools.py -k "scheduler_run_once_and_project"
3 passed

pytest tests/test_doc_loop_prompts.py -k "scheduler_mcp"
1 passed

pytest tests/test_runtime_orchestration.py tests/test_mcp_tools.py tests/test_progress_graph_trajectory.py tests/test_doc_loop_prompts.py tests/test_mcp_prompts_resources.py
284 passed, 1 skipped
```

Evidence JSON fields now include:

1. `product_type` / `schema_version`.
2. `evidence_id` / `timestamp`.
3. Scheduler snapshot, event-log, optional merge-gate log, and projection paths.
4. Runtime providers.
5. Host invocation surface, invocation id, requester, and reason.
6. Run count, stop reason, stop detail, ready / blocked / failed task IDs.
7. Permission-review task IDs / count.
8. Output artifact refs.
9. Compact history summary.
10. Authority split flags.

The evidence JSON is a review artifact only. It is not scheduler state and must
not be replayed into task contracts.

Close-review evidence:

- `review/controlled-host-runtime-dogfood-harness-2026-06-17.md`
