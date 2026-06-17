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
