# Scheduler MCP Smoke Prompt

Use this prompt when the current task explicitly asks to verify the scheduler
MCP lifecycle or to create a minimal scheduler-backed work trajectory smoke.

Read first:

1. `design_docs/stages/planning-gate/2026-06-16-agent-runtime-adapter-and-scheduler-skeleton.md`
2. `design_docs/tooling/MCP Tool Surface Audit.md`
3. The current planning-gate that authorizes scheduler work

Do not use this prompt for ordinary Local Work Trajectory updates.
`localTrajectory` remains the agent-owned lifecycle mutation tool.
Scheduler MCP tools operate on scheduler-owned snapshot/event-log state.

## Authority Boundary

Keep the lifecycle split:

1. `schedulerSubmitTasks` submits task contracts into scheduler-owned
   `snapshotPath` and `eventLogPath`.
2. `schedulerProjection` reads scheduler state/history and writes the
   scheduler-derived trajectory projection artifact.
3. `schedulerRunOnceAndProject` runs one bounded fake-runtime scheduler pass,
   writes the scheduler snapshot, and refreshes the scheduler projection.
4. Host-authorized runners use Python/host wiring through
   `HostSchedulerRunRequest` plus
   `run_host_authorized_scheduler_once_and_refresh_projection()`. This is the
   path for mock-Qoder or future real-provider dogfood. It is not exposed as a
   real-provider MCP tool.
5. Controlled host-runtime dogfood uses
   `run_host_runtime_dogfood_harness()` to run the host-authorized scheduler
   pass, refresh scheduler projection, and write compact evidence JSON.

These tools must not mutate `.codex/progress-graph/local-work-trajectory.json`.

## Minimal Paths

Prefer explicit paths under `.codex/scheduler/` or a test temp directory:

```text
.codex/scheduler/scheduler-state.json
.codex/scheduler/scheduler-events.jsonl
.codex/scheduler/evidence/<evidence-id>.json
.codex/progress-graph/scheduler-work-trajectory.json
```

Do not invent a default scheduler state path inside a tool call unless the
current planning-gate has fixed that path.

## Submit

Call `schedulerSubmitTasks` with a small batch. Use `fake` runtime providers for
the smoke path.

Recommended shape:

```json
{
  "snapshotPath": ".codex/scheduler/scheduler-state.json",
  "eventLogPath": ".codex/scheduler/scheduler-events.jsonl",
  "batchId": "batch-smoke",
  "timestamp": "2026-06-17T00:00:00+08:00",
  "tasks": [
    {
      "taskId": "task-a",
      "title": "Task A",
      "instruction": "Complete the first fake scheduler task.",
      "agent": {"agentId": "agent:a", "runtimeProvider": "fake"},
      "contextScope": {"contextId": "context:a", "laneId": "lane:a"},
      "outputArtifactId": "task-a:result"
    },
    {
      "taskId": "task-b",
      "title": "Task B",
      "instruction": "Complete after Task A.",
      "agent": {"agentId": "agent:b", "runtimeProvider": "fake"},
      "contextScope": {"contextId": "context:b", "laneId": "lane:b"},
      "outputArtifactId": "task-b:result",
      "dependencies": [
        {
          "dependencyId": "dep-a-b",
          "sourceTaskId": "task-a",
          "targetTaskId": "task-b",
          "requiredState": "complete"
        }
      ]
    }
  ]
}
```

Expected submit evidence:

- `ok=true`
- `submitted_task_ids` contains both tasks
- `submission_event_ids` is non-empty
- `ran_tasks=false`
- `refreshed_projection=false`
- `local_trajectory_mutated=false`
- `source_log.timestamp` and `source_log.action` are present

## Project Before Run

Call `schedulerProjection` after submit when you need to inspect the queued task
graph before execution.

Expected projection evidence:

- The scheduler projection artifact path exists.
- It contains scheduler task events.
- Submitted tasks are not completed merely because projection refreshed.

## Run Once And Project

Call `schedulerRunOnceAndProject` only when the smoke should execute ready
`fake` tasks.

Use `runtimeProvider="fake"`. If a real provider such as `qoder` is requested,
the tool should reject it until host permission, sandbox, and adapter registry
wiring are explicit.

Expected run evidence:

- `ok=true`
- `runtime_provider="fake"`
- `run_count` matches the number of executable fake tasks
- `state_written=true`
- scheduler projection exists and shows completed task events
- scheduler event history includes submission and run lifecycle events

## Host-Authorized Runner

Use the host-authorized runner only when the current planning-gate explicitly
asks for host-wired scheduler execution.

The host-facing Python adapter is:

```text
HostSchedulerRunRequest
run_host_authorized_scheduler_once()
run_host_authorized_scheduler_once_and_refresh_projection()
run_host_runtime_dogfood_harness()
```

Expected host-runner evidence:

- `HostSchedulerRunResult.to_json_dict()` is JSON-serializable
- `runtime_registry_providers` records the registered providers
- `runtime_host_surface` is `host-authorized-adapter` for mock-Qoder or later
  real-provider runs
- `state_written=true`
- `stop_reason` and `run_count` are visible
- `output_artifact_refs` is present when tasks produce artifacts
- `history_summary` references scheduler event logs and source log clues
- `authority_split.local_work_trajectory_mutated=false`

Do not route `qoder` through `schedulerRunOnceAndProject`. MCP remains
fake-only; real providers require explicit host permission grants and injected
runtime clients.

## Controlled Host Runtime Dogfood Harness

Use `run_host_runtime_dogfood_harness()` when the current gate asks for repeatable
host-runtime dogfood evidence.

Expected evidence JSON:

- `product_type="host_scheduler_run_evidence"`
- `schema_version="1"`
- `evidence_id` and `timestamp` are present
- `snapshot_path`, `event_log_path`, and `scheduler_projection_path` are present
- `runtime_providers` records `["fake"]` or `["qoder"]`
- `host_invocation.surface` is `host-authorized-adapter`
- `host_invocation.reason` explains the dogfood run
- `run_count`, `stop_reason`, and `stop_detail` are visible
- ready / blocked / failed / permission-review task IDs are visible
- `output_artifact_refs` records produced artifacts
- `history_summary` references scheduler event logs and projection paths
- `authority_split.local_work_trajectory_mutated=false`

The evidence JSON is a review artifact. It is not scheduler state and must not
be used to replay task contracts. Scheduler state remains the snapshot plus
event log.

### Host Evidence Consumer

Use the read-only host evidence consumer when the task asks to inspect or
surface existing host-run evidence:

```text
dbc://host-evidence/bundle
read_host_scheduler_run_evidence_summary()
read_host_scheduler_run_evidence_summaries()
read_host_evidence_bundle()
host_scheduler_evidence_dir()
```

Expected consumer behavior:

1. Read existing `host_scheduler_run_evidence` JSON under
   `.codex/scheduler/evidence/`.
2. Validate `product_type` and `schema_version`.
3. Return compact summaries for UI, MCP resources, review docs, or release
   tooling.
4. Exclude embedded `host_result` from the summary payload; downstream
   consumers should not bind to the raw writer artifact.
5. Return an empty bundle when the evidence directory is missing.
6. Do not execute providers, initialize scheduler snapshots, refresh scheduler
   projections, mutate Local Work Trajectory, or synthesize evidence.
7. Isolate malformed local evidence files into `errors[]` / `error_count`
   without hiding valid `summaries[]`; strict runtime readers may still fail.

When MCP resources are available, prefer reading
`dbc://host-evidence/bundle`. It returns the same compact bundle JSON through
the standard read-only resource surface.

When an MCP resource reader is not available, use the CLI fallback:

```text
doc-based-coding resources list
doc-based-coding resources read dbc://host-evidence/bundle
```

Readiness-negative live smoke outcomes remain review-doc evidence unless an
actual evidence JSON artifact exists. Do not create fake evidence JSON merely to
make a UI or summary look populated.

## Controlled Real Qoder Wrapper Spike

Use the real Qoder wrapper only from a host-owned Python surface, never through
`schedulerRunOnceAndProject`.

The current wrapper seam is:

```text
QoderSDKQueryClientConfig
QoderSDKQueryClient
QoderQueryClient
QoderAgentRuntimeAdapter
run_host_runtime_dogfood_harness()
```

Expected host construction:

1. Install the optional `qoder-agent-sdk` package in the host runtime
   environment. It is not a hard dependency of the doc-based-coding runtime.
2. Provide `QODER_PERSONAL_ACCESS_TOKEN` or an explicitly supported SDK auth
   mode in the host environment. Do not write token values into files,
   scheduler state, evidence JSON, decision logs, review docs, or Local Work
   Trajectory.
3. Construct `QoderSDKQueryClient(QoderSDKQueryClientConfig(...))` in the
   host-authorized adapter layer.
4. Build `RuntimeRegistryWiringConfig(providers=("qoder",), ...)` with
   `RuntimeHostInvocation(surface="host-authorized-adapter", ...)` and
   `RuntimeProviderPermissionGrant(provider="qoder", allow_sdk_client=True)`.
5. Pass the wrapper as `qoder_query_client` to
   `run_host_runtime_dogfood_harness()`.

Expected negative-path behavior:

- missing `qoder-agent-sdk` -> `QoderRuntimeError(error_kind="sdk_unavailable")`
- missing auth token -> `QoderRuntimeError(error_kind="authentication_failed")`
- malformed SDK stream -> `QoderRuntimeError(error_kind="invalid_response")`
- SDK permission callback request -> deny by default with
  `QoderRuntimeError(error_kind="permission_denied")`
- `permission_request_policy="surface"` may surface a compact
  `PermissionRequest`, but the wrapper still returns `False` to the SDK
  permission callback and does not approve the request internally

Before running the scheduler, `run_host_runtime_dogfood_harness()` calls the
wrapper's `validate_host_ready()` when available. This is the fail-closed guard:
missing SDK/auth fails before evidence JSON, scheduler projection, or scheduler
state are written.

The wrapper must keep result material compact. Do not copy raw transcripts,
tokens, or full SDK logs into `QoderQueryResult.metadata`,
`HostSchedulerRunEvidence`, review docs, or Local Work Trajectory.

### Host-Owned Qoder Smoke Runner Helper

Prefer the host-owned smoke helper for repeatable Qoder wrapper checks:

```text
run_host_owned_qoder_smoke()
HostOwnedQoderSmokeRunConfig
QoderSmokeTaskConfig
```

The helper lives under `tools/progress_graph/qoder_smoke.py` because it composes
the host dogfood harness, scheduler projection, and evidence artifacts. It is
not a scheduler daemon and is not an MCP execution surface.

Expected helper behavior:

1. Create or reuse `.codex/scheduler/qoder-smoke-state.json`.
2. Create or reuse `.codex/scheduler/qoder-smoke-events.jsonl`.
3. Build a one-task Qoder smoke scheduler snapshot when requested.
4. Construct host invocation and qoder permission grant.
5. Construct `QoderSDKQueryClient` from host config, unless an injected
   `QoderQueryClient` is supplied for tests.
6. Delegate execution to `run_host_runtime_dogfood_harness()`.
7. Write compact `HostSchedulerRunEvidence` and scheduler-derived trajectory
   projection.

Use injected clients for deterministic tests. Use the real SDK wrapper only
when the host environment intentionally provides `qoder-agent-sdk` and
`QODER_PERSONAL_ACCESS_TOKEN`.

If SDK/auth are missing, the helper should fail before evidence/projection
writes and leave the smoke task in `proposed` state. Treat that as expected
negative-path evidence, not as scheduler corruption.

## Write-Back

Record:

- paths used
- submitted task IDs
- dependency IDs
- whether projection was refreshed before run
- run count and stop reason
- scheduler projection artifact path
- host dogfood evidence JSON path when `run_host_runtime_dogfood_harness()` was used
- host-runner result JSON when a host-authorized adapter was used
- any real-provider rejection if intentionally tested
- validation commands or MCP responses used as evidence
