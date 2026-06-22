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
4. `dbc://exchange-artifacts/bundle` inspects stored coordination products and
   reports scheduler-admission candidates. It does not submit tasks.
5. `admit_exchange_artifact_version_to_scheduler()` is the controlled Python
   helper for exact-version store admission. It writes scheduler snapshot/event
   log state, but does not run providers, refresh projection, or mutate
   Local Work Trajectory.
6. `doc-based-coding scheduler admit-exchange-artifact` is the CLI operator
   surface over exact-version store admission. It writes scheduler snapshot and
   event-log state only; it does not run providers, refresh projection, mark
   exchange artifacts consumed, or mutate Local Work Trajectory. It also writes
   an admission ledger record by default.
7. `admitExchangeArtifact` is the MCP exact-version admission tool. It reuses
   the same admission ledger policy as the CLI, writes scheduler snapshot and
   event-log state only, and does not run providers, refresh projection, mark
   exchange artifacts consumed, or mutate Local Work Trajectory.
8. `schedulerBindingReferenceInspect` and
   `doc-based-coding scheduler inspect-binding-refs` are read-only binding-ref
   inspection surfaces for one exact stored scheduler submission artifact. Use
   them before admission when a task references
   `supervisor_storage_binding_artifact` inputs. They read the ExchangeArtifact
   store, validate exact binding refs, and do not admit tasks, mutate scheduler
   state, write admission ledgers, read raw evidence JSON, refresh projection,
   or mutate Local Work Trajectory.
9. `doc-based-coding scheduler inspect-admissions` is the CLI readback surface
   for the local ExchangeArtifact admission ledger. It does not write scheduler
   state, exchange artifacts, projection artifacts, or Local Work Trajectory.
10. `doc-based-coding scheduler inspect-state` is the CLI readback surface for
   scheduler snapshot/event-log clues. It does not write state or projection.
11. `doc-based-coding scheduler tick` is the daemon-ready bounded advancement
   surface. It runs one fake-runtime tick over scheduler snapshot/event-log
   state and does not refresh scheduler projection automatically.
12. `doc-based-coding scheduler daemon-loop` is the bounded repeated daemon
   loop policy surface. It repeatedly calls the fake-runtime tick contract
   until max ticks, no-ready, blocked-task, or runtime-failure stop policy
   fires. It does not refresh scheduler projection automatically.
13. `doc-based-coding scheduler project` is the CLI projection refresh surface
   for `.codex/progress-graph/scheduler-work-trajectory.json`. It does not run
   providers or mutate Local Work Trajectory.
14. Host-authorized runners use Python/host wiring through
   `HostSchedulerRunRequest` plus
   `run_host_authorized_scheduler_once_and_refresh_projection()`. This is the
   path for mock-Qoder or future real-provider dogfood. It is not exposed as a
   real-provider MCP tool.
15. Host-injected daemon loops use Python/host wiring through
   `HostSchedulerDaemonLoopRequest` plus
   `run_host_authorized_scheduler_daemon_loop()`. This is the path for
   repeated bounded mock-Qoder or future real-provider daemon-loop dogfood. It
   is not exposed as a real-provider CLI or MCP tool.
16. Host loop projection workflow uses
   `run_host_authorized_scheduler_daemon_loop_and_refresh_projection()` when a
   host-owned Python caller needs one compact workflow that runs the bounded
   daemon loop, preserves optional `scheduler_loop_evidence`, refreshes
   `.codex/progress-graph/scheduler-work-trajectory.json`, and reads back a
   scheduler-derived trajectory summary. This is explicit host workflow
   composition, not scheduler-owned Local Work Trajectory mutation and not
   CLI/MCP real-provider exposure.
17. Shared scheduler operator workflow uses `schedulerOperatorWorkflow`,
   `doc-based-coding scheduler operator-workflow`, or
   `run_scheduler_operator_workflow()` when a Codex/MCP/Host UX caller needs
   one explicit contract over candidate inspection, exact admission, bounded
   fake loop evidence, scheduler projection refresh, and Host Evidence
   presentation readback. Mutating steps remain opt-in through
   `admit` / `runLoop` / `refreshProjection`.
18. Scheduler daemon lifecycle control uses
   `doc-based-coding scheduler lifecycle <action>` or
   `schedulerLifecycleControl` for deterministic control-file operations:
   inspect, start, heartbeat, pause, resume, cancel, and shutdown. The MCP
   control tool also accepts deterministic `mark_stale`. These actions write
   only the lifecycle control file and do not run providers or refresh
   projection.
19. Scheduler lifecycle run-once uses
   `doc-based-coding scheduler lifecycle run-once` or
   `schedulerLifecycleRunOnce` to run one lifecycle-gated bounded fake-runtime
   loop. It may mutate scheduler snapshot/event-log state only through the
   bounded scheduler loop; paused/cancelled/stopped/stale controls skip
   scheduler mutation, and cancellation is consumed before provider execution.
20. Scheduler lifecycle harness uses
   `doc-based-coding scheduler lifecycle harness` or
   `schedulerLifecycleHarness` to run the bounded host-managed harness with
   explicit cancelled/deadline preflight and retry over listed harness stop
   reasons. It remains fake-runtime-only in MCP, does not refresh projection,
   and does not mutate agent-owned Local Work Trajectory.
21. Scheduler daemon supervisor step uses
   `doc-based-coding scheduler lifecycle supervisor-step` or
   `schedulerDaemonSupervisorStep` to run one host-managed supervisor step over
   the policy-controlled bounded harness. It adds supervisor/session/run
   identity, cancellation-source metadata, and lifecycle status readback while
   remaining fake-runtime-only in CLI/MCP. It does not start a service, refresh
   projection, execute cleanup, or mutate agent-owned Local Work Trajectory.
22. Supervisor dogfood workflow uses
   `doc-based-coding scheduler supervisor-dogfood-workflow` or
   `schedulerSupervisorDogfoodWorkflow` when the current gate needs the complete
   deterministic sequence: seed a scheduler dogfood fixture, admit the exact
   version, start lifecycle control, run one supervisor step, and read back final
   scheduler/supervisor facts. It is fake-runtime-only, does not refresh
   scheduler projection, execute cleanup, start a service, or mutate
   agent-owned Local Work Trajectory.
23. Controlled host-runtime dogfood uses
   `run_host_runtime_dogfood_harness()` to run the host-authorized scheduler
   pass, refresh scheduler projection, and write compact evidence JSON.

These tools must not mutate `.codex/progress-graph/local-work-trajectory.json`.

## Minimal Paths

Prefer explicit paths under `.codex/scheduler/` or a test temp directory:

```text
.codex/scheduler/scheduler-state.json
.codex/scheduler/scheduler-events.jsonl
.codex/scheduler/scheduler-daemon-control.json
.codex/scheduler/evidence/<evidence-id>.json
.codex/orchestration/exchange-artifacts.json
.codex/orchestration/exchange-artifact-admissions.json
.codex/progress-graph/scheduler-work-trajectory.json
```

Do not invent a default scheduler state path inside a tool call unless the
current planning-gate has fixed that path.

## Exchange Artifact Store Inspection

Use the read-only exchange artifact bundle when the current gate asks to
inspect stored coordination products or prepare an admission decision:

```text
dbc://exchange-artifacts/bundle
doc-based-coding resources read dbc://exchange-artifacts/bundle
inspect_exchange_artifact_store()
default_exchange_artifact_store_path()
```

Expected inspection behavior:

1. Read `.codex/orchestration/exchange-artifacts.json` by default.
2. Return exact artifact IDs, versions, latest flags, kind / intent /
   lifecycle / producer, scope, payload part types, and visibility clues.
3. Detect scheduler task submission and batch submission candidates through
   advisory `admission_candidates[]` metadata.
4. Include ledger-derived `admission_state` for each exact artifact version
   when `.codex/orchestration/exchange-artifact-admissions.json` is available.
   Missing ledgers produce `admission_state.status=not_admitted`.
5. Keep `admission_state` read-only: it is not exchange artifact lifecycle
   mutation, consumed marking, scheduler projection refresh, or a scheduler
   admission action.
6. Return an empty bundle when the store file is missing.
7. Isolate malformed store or admission ledger JSON into `errors[]` /
   `error_count` without hiding valid store summaries.
8. Report `authority_split.admission_state_source` as
   `exchange_artifact_admission_ledger`.
9. Do not submit tasks, mark artifacts consumed, execute providers, refresh
   scheduler projection, mutate scheduler snapshots, or mutate Local Work
   Trajectory.

The exchange artifact store is a coordination product store. Scheduler
snapshots remain the scheduling authority. A later admission gate may consume
an exact artifact version, but this inspection resource is not that admission
action.

## Exact-Version Store Admission

Use the exact-version admission helper when the current gate asks to consume a
stored scheduler submission artifact from Python/runtime code:

```text
admit_exchange_artifact_version_to_scheduler()
PersistedExchangeArtifactAdmissionResult
submit_scheduler_task_with_persistence()
submit_scheduler_task_batch_with_persistence()
```

Required inputs:

```text
artifact_store_path
artifact_id
version
snapshot_path
event_log_path
replace_existing
timestamp
```

Expected admission behavior:

1. Read the exact `(artifact_id, version)` from `JsonArtifactVersionStore`.
2. Require exactly one scheduler submission product payload:
   `scheduler_task_submission` or `scheduler_task_batch_submission`.
3. Submit through existing scheduler submission adapters.
4. Append `task_submitted` audit events and write the scheduler snapshot.
5. Return submitted task IDs, dependency IDs, source artifact identity,
   submission event IDs, and authority clues.
6. Reject missing exact versions, malformed stores, non-submission artifacts,
   and ambiguous multiple scheduler submission payloads with readable errors.
7. Do not run providers, mark exchange artifacts consumed, refresh scheduler
   projection, or mutate `.codex/progress-graph/local-work-trajectory.json`.

For agent/host-facing MCP exact admission, use the `admitExchangeArtifact`
tool below. For operator-triggered admission outside Python or MCP, use the CLI
surface below.

### MCP Exact-Version Admission

Use the MCP tool when an agent or MCP host needs to admit one exact stored
scheduler submission artifact through the structured tool surface:

```text
admitExchangeArtifact
```

Required inputs:

```text
artifactId
version
snapshotPath
eventLogPath
```

Optional inputs:

```text
artifactStorePath
admissionLedgerPath
allowDuplicateAdmission
replaceExisting
actor
timestamp
```

Expected MCP behavior:

1. Resolve relative paths under the MCP project root.
2. Default `artifactStorePath` to
   `.codex/orchestration/exchange-artifacts.json`.
3. Default `admissionLedgerPath` to
   `.codex/orchestration/exchange-artifact-admissions.json`.
4. Reuse the same ledger duplicate policy as the CLI: reject duplicate exact
   artifact/version admission before scheduler mutation unless
   `allowDuplicateAdmission=true`.
5. Keep `allowDuplicateAdmission` distinct from `replaceExisting`: duplicate
   admission controls ledger replay policy, while replace-existing controls
   scheduler task replacement semantics.
6. Return snake_case JSON fields including `ok`, `artifact_store_path`,
   `admission_ledger_path`, `admission_ledger_record_id`,
   `submitted_task_ids`, `submission_event_ids`, `dependency_ids`,
   `task_count`, `dependency_count`, `ran_tasks=false`,
   `refreshed_projection=false`, and `authority_split`.
7. On duplicate rejection, return a non-throwing `ok=false` payload with
   `status=rejected_duplicate`, `duplicate_of`, `scheduler_state_mutated=false`,
   and `event_log_mutated=false`.
8. Do not run providers, mark exchange artifacts consumed, refresh scheduler
   projection, or mutate `.codex/progress-graph/local-work-trajectory.json`.

### Binding Reference Inspection

Use the read-only inspection surface before admission when a stored scheduler
submission declares exact supervisor storage binding artifact inputs:

```text
schedulerBindingReferenceInspect

doc-based-coding scheduler inspect-binding-refs \
  --artifact-id <artifact-id> \
  --version <version>
```

Optional inputs:

```text
artifactStorePath
--artifact-store-path .codex/orchestration/exchange-artifacts.json
```

Expected inspection behavior:

1. Read the exact scheduler submission artifact from `JsonArtifactVersionStore`.
2. Accept `scheduler_task_submission` and `scheduler_task_batch_submission`.
3. Reuse `validate_supervisor_storage_binding_artifact_refs()` for each task.
4. Report `product_type="supervisor_storage_binding_reference_inspection"`,
   source artifact id/version, submission product type, task count, binding ref
   count, checked ref count, `errors[]`, `error_count`, and per-task entries.
5. Use `ref_kind="supervisor_storage_binding_artifact"` with exact `ref_id`
   and `version`.
6. Return `ok=false` for missing artifact versions, wrong source product,
   missing binding artifacts, wrong binding product, or ambiguous binding
   payloads without mutating scheduler state.
7. CLI exits non-zero for inspection errors while still printing the JSON
   product. MCP returns the same JSON product.
8. Do not admit tasks, submit tasks, write scheduler snapshots or event logs,
   mutate ExchangeArtifact stores, write admission ledgers, mark artifacts
   consumed, read raw supervisor binding evidence JSON, run providers, refresh
   scheduler projection, or mutate
   `.codex/progress-graph/local-work-trajectory.json`.

### CLI Operator Admission

Use the CLI operator surface when an operator or host script needs to admit one
exact stored scheduler submission artifact without opening an MCP write tool:

```text
doc-based-coding scheduler admit-exchange-artifact \
  --artifact-id <artifact-id> \
  --version <version> \
  --snapshot-path .codex/scheduler/scheduler-state.json \
  --event-log-path .codex/scheduler/scheduler-events.jsonl
```

Optional inputs:

```text
--artifact-store-path .codex/orchestration/exchange-artifacts.json
--admission-ledger-path .codex/orchestration/exchange-artifact-admissions.json
--allow-duplicate-admission
--actor <actor-id>
--replace-existing
--timestamp <timestamp>
```

Expected CLI behavior:

1. Resolve relative paths under the detected project root.
2. Default `--artifact-store-path` to
   `.codex/orchestration/exchange-artifacts.json`.
3. Require explicit scheduler snapshot and event-log paths.
4. Default `--admission-ledger-path` to
   `.codex/orchestration/exchange-artifact-admissions.json`.
5. Before scheduler mutation, reject duplicate exact artifact/version admission
   when a previous `admitted` ledger record exists and
   `--allow-duplicate-admission` is absent.
6. Keep `--allow-duplicate-admission` distinct from `--replace-existing`:
   duplicate admission controls ledger replay policy, while replace-existing
   controls scheduler task replacement semantics.
7. Print JSON with `ok=true`, `submitted_task_ids`,
   `submission_event_ids`, count fields, `admission_ledger_path`,
   `admission_ledger_record_id`, and `authority_split`.
8. Reject missing arguments, duplicate admission, and non-submission stored
   artifacts without scheduler mutation.
9. Do not run providers, mark exchange artifacts consumed, refresh scheduler
   projection, or mutate
   `.codex/progress-graph/local-work-trajectory.json`.

### CLI Admission Ledger Readback

Use the CLI admission-ledger readback surface when an operator or host script
needs to verify exact stored-artifact admission history without mutating
scheduler state:

```text
doc-based-coding scheduler inspect-admissions \
  --admission-ledger-path .codex/orchestration/exchange-artifact-admissions.json \
  --artifact-id <artifact-id> \
  --version <version>
```

Expected ledger behavior:

1. Read `.codex/orchestration/exchange-artifact-admissions.json` by default.
2. Report compact `status_counts`, `records[]`, `artifact_ids`, filters, and
   authority clues.
3. Include `admitted`, `rejected_duplicate`, and `failed` records.
4. Return an empty readback when the ledger file is missing.
5. Do not mutate scheduler state, exchange artifacts, scheduler projection, or
   `.codex/progress-graph/local-work-trajectory.json`.

### CLI Operator Readback And Projection

Use the CLI readback, bounded tick, and projection surfaces when an operator or
script needs to verify admission results without an MCP host:

```text
doc-based-coding scheduler inspect-state \
  --snapshot-path .codex/scheduler/scheduler-state.json \
  --event-log-path .codex/scheduler/scheduler-events.jsonl

doc-based-coding scheduler tick \
  --snapshot-path .codex/scheduler/scheduler-state.json \
  --event-log-path .codex/scheduler/scheduler-events.jsonl \
  --max-runs 1

doc-based-coding scheduler daemon-loop \
  --snapshot-path .codex/scheduler/scheduler-state.json \
  --event-log-path .codex/scheduler/scheduler-events.jsonl \
  --max-ticks 3 \
  --max-runs-per-tick 1 \
  --max-runtime-failures 1 \
  --evidence-id scheduler-loop-smoke

doc-based-coding scheduler project \
  --snapshot-path .codex/scheduler/scheduler-state.json \
  --event-log-path .codex/scheduler/scheduler-events.jsonl
```

Optional projection inputs:

```text
--output-path .codex/progress-graph/scheduler-work-trajectory.json
--trajectory-id local-work:scheduler-projection
--title "Scheduler Local Work Trajectory"
--guide-context <planning-or-review-doc>
--source-graph-id <graph-id>
--source-node-id <node-id>
```

Expected readback behavior:

1. Read scheduler snapshot and optional scheduler / merge-gate JSONL logs.
2. Print task, dependency, run-record, merge-gate, task-state, and event-log
   summary clues.
3. Do not write scheduler state, exchange artifacts, projection artifacts, run
   providers, or mutate `.codex/progress-graph/local-work-trajectory.json`.

Expected tick behavior:

1. Recover scheduler state from explicit snapshot and event-log paths.
2. Run at most the requested `--max-runs` fake-runtime tasks.
3. Return `run_count`, `stop_reason`, `queue_summary`, scheduler event count,
   and `authority_split`.
4. Write scheduler snapshot/event-log state through scheduler primitives.
5. Do not run real providers, refresh scheduler projection, mutate exchange
   artifacts, mutate admission ledger, or mutate
   `.codex/progress-graph/local-work-trajectory.json`.
6. Evidence writing is explicit: `--evidence-id <id>` writes
   `product_type="scheduler_loop_evidence"` under
   `.codex/scheduler/evidence/<safe-id>.json`; without `--evidence-id`, no
   evidence artifact is written.

Expected daemon-loop behavior:

1. Repeatedly call the bounded tick contract over explicit scheduler snapshot
   and event-log paths.
2. Stop on `max_ticks_reached`, `no_ready_tasks`, `blocked_tasks`,
   `runtime_failure_limit_reached`, or `cancelled`.
3. Return `tick_count`, `total_run_count`, `stop_reason`,
   `final_queue_summary`, per-iteration summaries, scheduler event count, and
   `authority_split`.
4. Write scheduler snapshot/event-log state only through tick/scheduler
   primitives.
5. Do not run real providers, refresh scheduler projection, mutate exchange
   artifacts, mutate admission ledger, or mutate
   `.codex/progress-graph/local-work-trajectory.json`.

Expected projection CLI behavior:

1. Read scheduler snapshot and optional scheduler / merge-gate JSONL logs.
2. Write `.codex/progress-graph/scheduler-work-trajectory.json` by default, or
   the explicit `--output-path`.
3. Print trajectory identity, projection path, event/lane/relation counts, and
   authority clues.
4. Do not run providers, mutate scheduler state, mark exchange artifacts
   consumed, or mutate
   `.codex/progress-graph/local-work-trajectory.json`.

Recommended operator workflow:

```text
schedulerOperatorWorkflow
doc-based-coding scheduler operator-workflow ...
schedulerSupervisorDogfoodWorkflow
doc-based-coding scheduler supervisor-dogfood-workflow ...
doc-based-coding resources read dbc://exchange-artifacts/bundle
schedulerBindingReferenceInspect
doc-based-coding scheduler inspect-binding-refs ...
admitExchangeArtifact
doc-based-coding scheduler admit-exchange-artifact ...
doc-based-coding scheduler inspect-admissions ...
doc-based-coding scheduler inspect-state ...
doc-based-coding scheduler tick ...
doc-based-coding scheduler daemon-loop ...
doc-based-coding scheduler project ...
```

Prefer `schedulerOperatorWorkflow` or `doc-based-coding scheduler
operator-workflow` when the current gate wants the complete operator sequence
through one shared contract. Prefer the lower-level commands/tools when the
gate is specifically validating an individual lifecycle step.
Prefer `schedulerSupervisorDogfoodWorkflow` or `doc-based-coding scheduler
supervisor-dogfood-workflow` when the current gate wants the complete
supervisor sequence through seed, exact admission, lifecycle start, supervisor
step, and final readback.
Prefer `schedulerBindingReferenceInspect` or `doc-based-coding scheduler
inspect-binding-refs` before admission when the candidate task consumes
`supervisor_storage_binding_artifact` refs.

Expected shared workflow behavior:

1. Default mode is read-only: inspect candidates and read Host Evidence
   presentation.
2. `admit=true` / `--admit` admits one exact artifact/version and writes the
   admission ledger.
3. `runLoop=true` / `--run-loop` runs only the bounded fake scheduler loop and
   writes scheduler-loop evidence.
4. `refreshProjection=true` / `--refresh-projection` refreshes only the
   scheduler-derived projection artifact.
5. Per-step status is returned in `steps[]`; failed admission skips dependent
   loop/projection steps.
6. The shared workflow does not run live providers, start a background daemon,
   mark ExchangeArtifacts consumed, or mutate
   `.codex/progress-graph/local-work-trajectory.json`.

Expected supervisor dogfood workflow behavior:

1. Seed one deterministic scheduler dogfood fixture (`simple` or `multilane`).
2. Admit the exact fixture artifact/version into scheduler snapshot/event-log
   state.
3. Start lifecycle control explicitly.
4. Run one fake-runtime host-managed supervisor step.
5. Read final lifecycle and scheduler queue facts.
6. Do not refresh scheduler projection, run cleanup, start a service, or mutate
   `.codex/progress-graph/local-work-trajectory.json`.

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
HostSchedulerDaemonLoopRequest
run_host_authorized_scheduler_daemon_loop()
run_host_authorized_scheduler_daemon_loop_and_refresh_projection()
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

Expected host-injected daemon-loop behavior:

- `HostSchedulerDaemonLoopResult.to_json_dict()` is JSON-serializable
- `runtime_registry_providers` records the registered providers
- `runtime_host_surface` is `host-authorized-adapter` for mock-Qoder or later
  real-provider runs
- `tick_count`, `total_run_count`, `stop_reason`, and
  `final_queue_summary` are visible
- explicit `evidence_id` writes `product_type="scheduler_loop_evidence"`
  through the same read-only host evidence bundle/presentation path
- `authority_split.runtime_registry_authority="host_runtime_wiring"`
- `authority_split.scheduler_projection_refreshed=false`
- `authority_split.local_work_trajectory_mutated=false`

Do not add a CLI/MCP real-provider daemon loop. The CLI `doc-based-coding scheduler daemon-loop` remains fake-runtime-only.

Expected host loop projection workflow behavior:

- `run_host_authorized_scheduler_daemon_loop_and_refresh_projection()` calls the
  host daemon-loop helper, then writes the read-only scheduler projection
- `scheduler_projection_path` points at
  `.codex/progress-graph/scheduler-work-trajectory.json` unless an explicit
  projection path was supplied
- `projection_summary` gives compact machine readback for the
  scheduler-derived trajectory
- explicit `evidence_id` still writes `scheduler_loop_evidence`
- when explicit `evidence_id` is used, the composed host workflow enriches the
  just-written evidence metadata after projection refresh with:
  `workflow_surface="host-loop-projection-workflow"`,
  `scheduler_projection_path`, `scheduler_projection_role`,
  `scheduler_projection_refreshed=true`, and compact
  `scheduler_projection_summary`
- `authority_split.scheduler_projection_refreshed=true`
- `authority_split.local_work_trajectory_mutated=false`

This helper is for host-owned workflow polish. It must not be treated as a
background daemon, a scheduler state mutation beyond the bounded loop, or a
CLI/MCP real-provider surface. The evidence metadata must remain compact and
must not embed full trajectory JSON.

Expected scheduler-loop evidence presentation behavior:

- `dbc://host-evidence/presentation` remains read-only and must not execute
  providers, refresh projection, or mutate scheduler/trajectory state
- scheduler-loop cards surface runtime provider, host surface, host invocation,
  tick/run/event counts, and final queue counts as `key_facts`
- when evidence metadata or authority split includes projection clues,
  scheduler projection path/role/refreshed state are surfaced through
  `key_facts`, `refs`, `authority_clues`, and card `metadata`
- legacy scheduler-loop evidence without projection metadata must still render
  cleanly without a scheduler projection ref
- malformed evidence remains isolated into `errors[]` / `error_rows`

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
surface existing scheduler evidence:

```text
dbc://host-evidence/bundle
dbc://host-evidence/presentation
read_host_scheduler_run_evidence_summary()
read_host_scheduler_run_evidence_summaries()
read_scheduler_loop_evidence_summary()
read_host_evidence_bundle()
build_host_evidence_presentation()
host_scheduler_evidence_dir()
```

Expected consumer behavior:

1. Read existing `host_scheduler_run_evidence` and `scheduler_loop_evidence`
   JSON under `.codex/scheduler/evidence/`.
2. Validate `product_type` and `schema_version`.
3. Return compact summaries for UI, MCP resources, review docs, or release
   tooling.
4. Exclude embedded `host_result` / `loop_result` from the summary payload;
   downstream consumers should not bind to the raw writer artifact.
5. Return an empty bundle when the evidence directory is missing.
6. Do not execute providers, initialize scheduler snapshots, refresh scheduler
   projections, mutate Local Work Trajectory, or synthesize evidence.
7. Isolate malformed local evidence files into `errors[]` / `error_count`
   without hiding valid `summaries[]`; strict runtime readers may still fail.

When MCP resources are available, prefer reading
`dbc://host-evidence/bundle`. It returns the same compact bundle JSON through
the standard read-only resource surface.

For host/UI/operator-facing inspection, prefer
`dbc://host-evidence/presentation`. It returns `HostEvidencePresentation`
JSON with `status`, `cards[]`, `error_rows[]`, count fields, output refs, and
authority clues. It is also read-only and must not execute providers or mutate
scheduler/local trajectory artifacts.

When an MCP resource reader is not available, use the CLI fallback:

```text
doc-based-coding resources list
doc-based-coding resources read dbc://host-evidence/bundle
doc-based-coding resources read dbc://host-evidence/presentation
doc-based-coding resources read dbc://exchange-artifacts/bundle
```

Readiness-negative live smoke outcomes remain review-doc evidence unless an
actual evidence JSON artifact exists. Do not create fake evidence JSON merely to
make a UI or summary look populated.

## Controlled Real Qoder Wrapper Spike

Use the real Qoder wrapper only from a host-owned Python surface, never through
`schedulerRunOnceAndProject`.

The current wrapper seam is:

```text
doc-based-coding qoder readiness
QoderSDKQueryClientConfig
QoderSDKQueryClient
QoderSDKHostReadinessReport
QoderQueryClient
QoderAgentRuntimeAdapter
run_host_runtime_dogfood_harness()
```

Expected host construction:

1. Read `docs/qoder-host-provisioning-check-guide.md`.
2. Run `doc-based-coding qoder readiness` before any live Qoder smoke attempt.
3. Install the optional `qoder-agent-sdk` package in the host runtime
   environment. It is not a hard dependency of the doc-based-coding runtime.
4. Provide `QODER_PERSONAL_ACCESS_TOKEN` or an explicitly supported SDK auth
   mode in the host environment. Do not write token values into files,
   scheduler state, evidence JSON, decision logs, review docs, or Local Work
   Trajectory.
5. Construct `QoderSDKQueryClient(QoderSDKQueryClientConfig(...))` in the
   host-authorized adapter layer.
6. Build `RuntimeRegistryWiringConfig(providers=("qoder",), ...)` with
   `RuntimeHostInvocation(surface="host-authorized-adapter", ...)` and
   `RuntimeProviderPermissionGrant(provider="qoder", allow_sdk_client=True)`.
7. Pass the wrapper as `qoder_query_client` to
   `run_host_runtime_dogfood_harness()`.

Expected readiness command behavior:

- It reports `sdk_importable`, `auth_mode`, `auth_env_var`,
  `token_present`, `ready`, `error_kind`, `raw_error_type`, and a redacted
  `summary`.
- It never prints token values.
- It does not run a Qoder query, initialize scheduler snapshots, write host
  evidence JSON, refresh scheduler projection, or mutate Local Work Trajectory.
- `doc-based-coding qoder readiness --auth-mode qodercli` may report
  `token_present=false`; that is acceptable when the SDK is importable and
  exposes `qodercli_auth`.

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
- admission ledger path and record IDs
- whether duplicate admission was rejected or explicitly allowed
- whether projection was refreshed before run
- run count and stop reason
- scheduler projection artifact path
- host dogfood evidence JSON path when `run_host_runtime_dogfood_harness()` was used
- host-runner result JSON when a host-authorized adapter was used
- any real-provider rejection if intentionally tested
- validation commands or MCP responses used as evidence
