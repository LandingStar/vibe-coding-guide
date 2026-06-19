# Planning Gate - Host-Injected Scheduler Daemon Loop

> Date: 2026-06-19
> Status: COMPLETED

## Trigger

`design_docs/scheduler-loop-host-evidence-binding-followup-direction-analysis.md`
recommends moving from fake-runtime CLI loop evidence to a host-owned Python
injection seam that can run the bounded scheduler daemon loop with explicit
runtime wiring.

## Problem

The scheduler now has:

```text
run_scheduler_daemon_loop()
SchedulerLoopEvidence
doc-based-coding scheduler daemon-loop --evidence-id
dbc://host-evidence/bundle
dbc://host-evidence/presentation
```

The CLI/MCP surfaces remain fake-runtime-only by design. The missing backend
step is a host-owned Python helper that can run the same bounded loop with an
explicit `RuntimeRegistryWiringConfig`, including mock-Qoder validation, while
preserving the existing authority split.

## Scope

### Slice 1 - Host Loop Contract

Add a host-facing daemon-loop contract:

```text
HostSchedulerDaemonLoopRequest
HostSchedulerDaemonLoopResult
run_host_authorized_scheduler_daemon_loop()
```

Expected fields:

1. scheduler snapshot and event-log paths;
2. `RuntimeRegistryWiringConfig`;
3. `SchedulerDaemonLoopStopPolicy`;
4. optional evidence id/path;
5. host invocation and runtime provider readback;
6. scheduler loop result;
7. optional scheduler-loop evidence write result;
8. authority split.

### Slice 2 - Host Runtime Wiring

The helper should:

1. build a runtime registry with `build_runtime_registry_from_config()`;
2. require `RuntimeHostInvocation(surface="host-authorized-adapter")` for
   non-fake providers through the existing wiring validation;
3. require `RuntimeProviderPermissionGrant` and injected `QoderQueryClient` for
   qoder;
4. pass the built registry into `run_scheduler_daemon_loop()`;
5. preserve CLI/MCP fake-runtime-only behavior.

### Slice 3 - Evidence Write

When `evidence_id` is supplied, the helper writes `scheduler_loop_evidence`
through the existing evidence contract.

Expected behavior:

1. default path uses `.codex/scheduler/evidence/<safe-id>.json`;
2. evidence metadata records the host surface and invocation id;
3. evidence readback continues through existing `dbc://host-evidence/*`;
4. evidence writing does not refresh scheduler projection or mutate Local Work
   Trajectory.

### Slice 4 - Validation

Cover:

1. fake host loop path;
2. mock-Qoder host loop path;
3. qoder rejection without host authorization / grant / injected client;
4. explicit evidence write and readback;
5. unchanged CLI non-fake rejection.

## Non-Goals

This gate does not:

1. Add a CLI or MCP real-provider execution surface.
2. Run live Qoder or require Qoder credentials.
3. Start a background daemon/service.
4. Add UI binding.
5. Automatically refresh scheduler projection.
6. Mutate ExchangeArtifact lifecycle or admission ledger state.
7. Mutate `.codex/progress-graph/local-work-trajectory.json` from scheduler
   code.
8. Change scheduler submission/admission semantics.

## Acceptance Criteria

The gate may close when:

1. The host daemon-loop request/result contract is documented and implemented.
2. Host-owned fake and mock-Qoder loop runs work through injected runtime
   wiring.
3. Non-fake providers are rejected unless the existing host authorization,
   permission grant, and injected client requirements are satisfied.
4. Explicit host-loop evidence writing produces `scheduler_loop_evidence` that
   existing read-only host evidence resources can consume.
5. CLI/MCP real-provider execution remains unavailable.
6. Focused tests cover runtime contract, evidence write/readback, prompt
   guidance, and CLI non-goals.
7. Review/status docs record that UI binding, live provider execution,
   automatic projection refresh, ExchangeArtifact mutation, and scheduler-owned
   Local Work Trajectory mutation remain deferred.

## Implementation Summary

Completed on 2026-06-19.

This slice added a host-owned Python daemon-loop adapter that reuses the
existing bounded scheduler daemon loop while keeping CLI/MCP real-provider
execution unavailable.

Implemented:

1. Host daemon-loop contract:
   - `HostSchedulerDaemonLoopRequest`
   - `HostSchedulerDaemonLoopResult`
   - `run_host_authorized_scheduler_daemon_loop()`
2. Host runtime wiring:
   - reuses `build_runtime_registry_from_config()`;
   - preserves existing `RuntimeHostInvocation(surface="host-authorized-adapter")`
     requirement for non-fake providers;
   - preserves `RuntimeProviderPermissionGrant` and injected `QoderQueryClient`
     requirements for qoder.
3. Evidence write:
   - optional `evidence_id` writes `scheduler_loop_evidence`;
   - default path uses `.codex/scheduler/evidence/<safe-id>.json`;
   - metadata records host daemon-loop surface and invocation id.
4. Prompt guidance:
   - `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`;
   - bootstrap copy under `doc-loop-vibe-coding/assets/bootstrap/`.

## Validation

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

## Non-Goals Preserved

This slice did not add:

1. CLI or MCP real-provider execution.
2. Live Qoder execution or credential requirements.
3. Background daemon/service lifecycle management.
4. UI binding.
5. Automatic scheduler projection refresh.
6. ExchangeArtifact lifecycle or admission ledger mutation.
7. Scheduler-owned Local Work Trajectory mutation.

