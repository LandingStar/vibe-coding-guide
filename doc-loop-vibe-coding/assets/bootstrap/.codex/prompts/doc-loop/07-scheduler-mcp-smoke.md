# Scheduler MCP Smoke Prompt

Use this prompt when the current task explicitly asks to verify the scheduler
MCP lifecycle or to create a minimal scheduler-backed work trajectory smoke.

Read first:

1. `design_docs/stages/planning-gate/2026-06-16-agent-runtime-adapter-and-scheduler-skeleton.md`
2. `design_docs/tooling/MCP Tool Surface Audit.md`
3. The current planning-gate that authorizes scheduler work

Do not use this prompt for ordinary Local Work Trajectory updates.
`localTrajectory` remains the leader/main/supervisor-owned lifecycle mutation
tool. Bounded workers/subagents must not call it directly; worker progress,
blocked state, completion, or suggested trajectory actions belong in
`Subagent Report.trajectory_update` for the leader to consume. Worker report
procedure: `docs/worker-trajectory-update-reporting.md`.
Scheduler MCP tools operate on scheduler-owned snapshot/event-log state.

CLI notation in this prompt is a DBC argv shorthand. When MCP exposes
`workspaceDbcCommand`, run CLI-equivalent DBC checks or operator surfaces
through that per-agent workspace relay instead of resolving a bare
`doc-based-coding` executable from PATH. Prefer dedicated structured MCP tools
when they exist.

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
9. `schedulerStorageBindingArtifactPublish` and
   `doc-based-coding scheduler publish-storage-binding-artifact` publish one
   durable `supervisor_storage_binding_evidence` summary as a compact exact
   version ExchangeArtifact. They mutate only the local ExchangeArtifact store;
   they do not admit tasks, run providers, create agent home or scratch
   directories, write scratch manifests, read raw binding payloads into
   exchange artifacts, refresh projection, or mutate Local Work Trajectory.
10. `agentExchangeMailbox` and
   `doc-based-coding scheduler inspect-agent-mailbox` build a per-agent
   ExchangeArtifact mailbox with `inbox`, `outbox`, `related`, and actionable
   readback. They read only the local ExchangeArtifact store, redact sensitive
   preview payloads, and do not mutate scheduler state, ExchangeArtifact
   lifecycle, admission ledgers, projection artifacts, providers, or Local Work
   Trajectory.
11. `agentExchangeHistory`,
   `doc-based-coding scheduler inspect-agent-history`, and
   `dbc://agent-exchange/history` build a compact ExchangeArtifact
   communication history summary with participant/lifecycle counts, causality
   edges, and compact log entries. They read only the local ExchangeArtifact
   store, do not expose raw sensitive text/structured payload content, and do
   not mutate scheduler state, ExchangeArtifact lifecycle, admission ledgers,
   projection artifacts, providers, or Local Work Trajectory.
12. `agentExchangeActionCandidates`,
   `doc-based-coding scheduler inspect-agent-action-candidates`, and
   `dbc://agent-exchange/action-candidates` classify stored ExchangeArtifacts
   into scheduler submission, review, handoff, blocker, and merge candidates
   with structured reasons. They read only the local ExchangeArtifact store and
   optional admission ledger, do not expose raw sensitive payload content, and
   do not admit tasks, open reviews, write handoffs, mutate exchange artifacts,
   write admission ledgers, run providers, refresh projections, or mutate
   Local Work Trajectory.
13. `agentExchangeActionCandidateDecide` and
   `doc-based-coding scheduler decide-agent-action-candidate` write one
   standard disposition ExchangeArtifact for an existing action candidate. They
   may mutate only the local ExchangeArtifact store by adding/replacing the
   disposition artifact; they do not admit tasks, open reviews, write handoffs,
   resolve merge gates, mutate the source artifact, write admission ledgers,
   run providers, refresh projections, or mutate Local Work Trajectory.
14. `agentExchangeAcceptedSchedulerCandidateConsume` and
   `doc-based-coding scheduler consume-accepted-scheduler-candidate` consume
   one accepted `scheduler_submission_candidate` disposition by calling the
   existing exact-version admission helper. They may write scheduler
   snapshot/event-log state and admission ledger records; they do not create
   dispositions, consume non-scheduler candidates, open reviews, write
   handoffs, resolve merge gates, run providers, refresh projections, or
   mutate Local Work Trajectory.
15. `agentExchangeAcceptedReviewCandidateConsume` and
   `doc-based-coding scheduler consume-accepted-review-candidate` consume one
   accepted `review_candidate` disposition by dispatching a review intake
   payload to the existing review intake adapter. They do not create
   dispositions, admit scheduler tasks, write handoffs, resolve merge gates,
   run providers, refresh projections, or mutate Local Work Trajectory.
16. `agentExchangeAcceptedHandoffCandidateConsume` and
   `doc-based-coding scheduler consume-accepted-handoff-candidate` consume one
   accepted `handoff_candidate` disposition by dispatching a schema-valid
   Handoff payload to the existing handoff delivery adapter. They require an
   explicit handoff directory and do not create dispositions, admit scheduler
   tasks, open reviews, resolve merge gates, run providers, refresh
   projections, or mutate Local Work Trajectory.
17. `agentExchangeAcceptedMergeCandidateConsume` and
   `doc-based-coding scheduler consume-accepted-merge-candidate` consume one
   accepted `merge_candidate` disposition by resolving an explicit scheduler
   merge gate. They require an explicit `gateId` and `approved` decision, may
   write scheduler snapshot and merge-gate event-log state, and do not infer
   a gate from ExchangeArtifact relations, admit scheduler tasks, open reviews,
   write handoffs, run providers, refresh projections, or mutate Local Work
   Trajectory.
18. `agentExchangeAcceptedBlockerCandidateConsume` and
   `doc-based-coding scheduler consume-accepted-blocker-candidate` consume one
   accepted `blocker_candidate` disposition by blocking an explicit scheduler
   task. They require an explicit `taskId` and non-empty reason, may write
   scheduler snapshot and event-log state, and do not infer a task from
   ExchangeArtifact relations, admit scheduler tasks, open reviews, write
   handoffs, resolve merge gates, run providers, refresh projections, or
   mutate Local Work Trajectory.
19. `doc-based-coding scheduler guide-worker-exchange-dogfood` runs the
   deterministic fake-runtime guide/worker exchange dogfood scenario. It
   composes the existing mailbox, reply, history, action-candidate,
   disposition, and accepted scheduler-candidate consumer helpers. It writes
   only the owned ExchangeArtifact products, scheduler snapshot/event-log
   state, and admission ledger needed for the proof; it does not add a new MCP
   tool, run live providers, refresh projection, persist raw transcripts, or
   mutate Local Work Trajectory.
20. `schedulerGuideWorkerLocalOrchestration` and
   `doc-based-coding scheduler guide-worker-local-orchestration` run the first
   scheduler-owned guide/worker local trajectory orchestration MVP. They create
   a structured guide instruction ExchangeArtifact, admit a scheduler worker
   task batch, and execute bounded fake-runtime worker waves with at most one
    ready task per lane. The MCP tool accepts structured `workerInstructions`
    for custom lane-bound worker tasks, or `guideTask` + `plannerLaneSpecs` for
    the deterministic guide planner to generate concrete lane instructions.
    It also accepts `sandboxProfile` on worker instructions/planner lane specs
    and `waveExecutionMode=serial|threaded` for the fake/mock wave executor.
    `sandboxProfile` defaults to `shared-process`; host-owned wrappers may opt
    into `git-worktree` and durable allocation receipt evidence. This defines
    bounded lane-distinct wave execution; `threaded` may
    invoke fake/mock runtime calls concurrently and then merges scheduler state
    deterministically, but it does not make live providers available. Runtime
    code can map host-injected worker adapters via `workerRuntimeProvider`, but
    this MCP surface rejects non-fake
   `workerRuntimeProvider` values. It does not run Qoder/opencode/Codex
   providers, refresh projection, persist raw transcripts, create agent
   home/scratch directories, or mutate agent-owned Local Work Trajectory.
21. `doc-based-coding qoder guide-worker-smoke`,
   `doc-based-coding codex guide-worker-smoke`, and
   `run_host_owned_guide_worker_provider_execution()` are the host-owned
   provider execution wrapper for guide-worker lane waves. They may run Qoder
   worker tasks only through explicit host runtime wiring, a Qoder permission
   grant, and either an injected `QoderQueryClient` or host-constructed
   `QoderSDKQueryClient`; they may run Codex CLI worker tasks only through
   explicit host runtime wiring, a Codex process-spawn grant, and either an
   injected `CodexCliClient` or host-constructed `CodexCliProcessClient`. They
   write compact guide-worker provider execution evidence after readiness
   succeeds. When configured with `git_worktree_sandbox_root` and
   `sandbox_allocation_evidence_id`, they also write durable sandbox allocation
   receipt evidence and review-only worker writeback receipts. They do not
   auto-merge worker worktrees into the source workspace. They are not MCP
   real-provider surfaces, do not accept raw token values, do not refresh
   scheduler projection, do not create persistent agent home directories, do
   not persist raw transcripts, and do not mutate agent-owned Local Work
   Trajectory.
   In multi-lane Local Work, leader-worker coordination is required rather
   than optional. Treat worker/leader inactive periods as lifecycle state
   waiting for messages, dependencies, or review; use compact runtime invocation audit
   for provider-backed execution and do not persist raw transcripts.
12. `agentExchangeReply` and
   `doc-based-coding scheduler reply-exchange-artifact` create one
   exact-version reply ExchangeArtifact with `causality.replies_to`,
   `caused_by`, and a compact `log` part. They mutate only the local
   ExchangeArtifact store; they do not admit scheduler tasks, run providers,
   write admission ledgers, refresh projections, or mutate Local Work
   Trajectory.
13. `agentExchangeTransition` and
   `doc-based-coding scheduler transition-exchange-artifact` transition one
   exact stored ExchangeArtifact version to `accepted`, `rejected`,
   `consumed`, `superseded`, or `archived` and append a compact `log` part.
   They are idempotent when the exact version is already in the target state
   and do not admit scheduler tasks, run providers, write admission ledgers,
   refresh projections, or mutate Local Work Trajectory.
14. `doc-based-coding scheduler inspect-admissions` is the CLI readback surface
   for the local ExchangeArtifact admission ledger. It does not write scheduler
   state, exchange artifacts, projection artifacts, or Local Work Trajectory.
   When explicit binding-ref preflight was enabled during admission, ledger
   records include compact `binding_reference_summary` counts/errors without
   raw supervisor storage binding evidence JSON.
15. `doc-based-coding scheduler inspect-state` is the CLI readback surface for
   scheduler snapshot/event-log clues. It does not write state or projection.
16. `doc-based-coding scheduler tick` is the daemon-ready bounded advancement
   surface. It runs one fake-runtime tick over scheduler snapshot/event-log
   state and does not refresh scheduler projection automatically.
17. `doc-based-coding scheduler daemon-loop` is the bounded repeated daemon
   loop policy surface. It repeatedly calls the fake-runtime tick contract
   until max ticks, no-ready, blocked-task, or runtime-failure stop policy
   fires. It does not refresh scheduler projection automatically.
18. `doc-based-coding scheduler project` is the CLI projection refresh surface
   for `.dbc/progress-graph/scheduler-work-trajectory.json`. It does not run
   providers or mutate Local Work Trajectory.
19. Host-authorized runners use Python/host wiring through
   `HostSchedulerRunRequest` plus
   `run_host_authorized_scheduler_once_and_refresh_projection()`. This is the
   path for mock-Qoder or future real-provider dogfood. It is not exposed as a
   real-provider MCP tool.
20. Host-injected daemon loops use Python/host wiring through
   `HostSchedulerDaemonLoopRequest` plus
   `run_host_authorized_scheduler_daemon_loop()`. This is the path for
   repeated bounded mock-Qoder or future real-provider daemon-loop dogfood. It
   is not exposed as a real-provider CLI or MCP tool.
21. Host loop projection workflow uses
   `run_host_authorized_scheduler_daemon_loop_and_refresh_projection()` when a
   host-owned Python caller needs one compact workflow that runs the bounded
   daemon loop, preserves optional `scheduler_loop_evidence`, refreshes
   `.dbc/progress-graph/scheduler-work-trajectory.json`, and reads back a
   scheduler-derived trajectory summary. This is explicit host workflow
   composition, not scheduler-owned Local Work Trajectory mutation and not
   CLI/MCP real-provider exposure.
22. Shared scheduler operator workflow uses `schedulerOperatorWorkflow`,
   `doc-based-coding scheduler operator-workflow`, or
   `run_scheduler_operator_workflow()` when a Codex/MCP/Host UX caller needs
   one explicit contract over candidate inspection, exact admission, bounded
   fake loop evidence, scheduler projection refresh, and Host Evidence
   presentation readback. Use `inspectBindingRefs=true` /
   `--inspect-binding-refs` to include read-only supervisor storage binding
   reference inspection before admission. Mutating steps remain opt-in through
   `admit` / `runLoop` / `refreshProjection`.
23. Operator dogfood closure uses `schedulerOperatorDogfoodClosure`,
   `doc-based-coding scheduler operator-dogfood-closure`, or
   `run_scheduler_operator_dogfood_closure()` when the current gate needs the
   complete deterministic operator evidence closure in one call: seed fixture,
   inspect binding refs when applicable, admit the exact artifact/version, mark
   it consumed after successful admission by default, run a bounded fake loop,
   refresh scheduler projection, and read Host Evidence presentation. It is
   fake-runtime-only and does not start services, execute cleanup, create agent
   home/scratch directories, or mutate agent-owned Local Work Trajectory.
   Use `doc-based-coding scheduler evidence-publish-consumer-closure` or
   `run_evidence_publish_to_consumer_closure()` when the current gate must
   prove the durable evidence publish path itself: write compact supervisor
   storage binding evidence, publish it through the compact binding artifact
   surface, create a consuming scheduler submission that references that
   exact published artifact id/version, then run the same fake-runtime
   operator closure steps through Host Evidence readback. This is a CLI/backend
   composition surface, not a new MCP tool. It does not create real agent
   home/scratch directories, write scratch manifests, execute cleanup, run live
   providers, or mutate agent-owned Local Work Trajectory.
21. Scheduler daemon lifecycle control uses
   `doc-based-coding scheduler lifecycle <action>` or
   `schedulerLifecycleControl` for deterministic control-file operations:
   inspect, start, heartbeat, pause, resume, cancel, and shutdown. The MCP
   control tool also accepts deterministic `mark_stale`. These actions write
   only the lifecycle control file and do not run providers or refresh
   projection.
22. Scheduler lifecycle run-once uses
   `doc-based-coding scheduler lifecycle run-once` or
   `schedulerLifecycleRunOnce` to run one lifecycle-gated bounded fake-runtime
   loop. It may mutate scheduler snapshot/event-log state only through the
   bounded scheduler loop; paused/cancelled/stopped/stale controls skip
   scheduler mutation, and cancellation is consumed before provider execution.
23. Scheduler lifecycle harness uses
   `doc-based-coding scheduler lifecycle harness` or
   `schedulerLifecycleHarness` to run the bounded host-managed harness with
   explicit cancelled/deadline preflight and retry over listed harness stop
   reasons. It remains fake-runtime-only in MCP, does not refresh projection,
   and does not mutate agent-owned Local Work Trajectory.
24. Scheduler daemon supervisor step uses
   `doc-based-coding scheduler lifecycle supervisor-step` or
   `schedulerDaemonSupervisorStep` to run one host-managed supervisor step over
   the policy-controlled bounded harness. It adds supervisor/session/run
   identity, cancellation-source metadata, and lifecycle status readback while
   remaining fake-runtime-only in CLI/MCP. It does not start a service, refresh
   projection, execute cleanup, or mutate agent-owned Local Work Trajectory.
25. Supervisor dogfood workflow uses
   `doc-based-coding scheduler supervisor-dogfood-workflow` or
   `schedulerSupervisorDogfoodWorkflow` when the current gate needs the complete
   deterministic sequence: seed a scheduler dogfood fixture, admit the exact
   version, start lifecycle control, run one supervisor step, and read back final
   scheduler/supervisor facts. It is fake-runtime-only, does not refresh
   scheduler projection, execute cleanup, start a service, or mutate
   agent-owned Local Work Trajectory.
26. Controlled host-runtime dogfood uses
   `run_host_runtime_dogfood_harness()` to run the host-authorized scheduler
   pass, refresh scheduler projection, and write compact evidence JSON.

These tools must not mutate `.dbc/progress-graph/local-work-trajectory.json`.

## Minimal Paths

Prefer explicit paths under `.dbc/scheduler/` or a test temp directory:

```text
.dbc/scheduler/scheduler-state.json
.dbc/scheduler/scheduler-events.jsonl
.dbc/scheduler/scheduler-daemon-control.json
.dbc/scheduler/evidence/<evidence-id>.json
.dbc/orchestration/exchange-artifacts.json
.dbc/orchestration/exchange-artifact-admissions.json
.dbc/progress-graph/scheduler-work-trajectory.json
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

1. Read `.dbc/orchestration/exchange-artifacts.json` by default.
2. Return exact artifact IDs, versions, latest flags, kind / intent /
   lifecycle / producer, scope, payload part types, and visibility clues.
3. Detect scheduler task submission and batch submission candidates through
   advisory `admission_candidates[]` metadata.
4. Include ledger-derived `admission_state` for each exact artifact version
   when `.dbc/orchestration/exchange-artifact-admissions.json` is available.
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
   projection, or mutate `.dbc/progress-graph/local-work-trajectory.json`.

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
   `.dbc/orchestration/exchange-artifacts.json`.
3. Default `admissionLedgerPath` to
   `.dbc/orchestration/exchange-artifact-admissions.json`.
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
   projection, or mutate `.dbc/progress-graph/local-work-trajectory.json`.

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
--artifact-store-path .dbc/orchestration/exchange-artifacts.json
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
   `.dbc/progress-graph/local-work-trajectory.json`.

### CLI Operator Admission

Use the CLI operator surface when an operator or host script needs to admit one
exact stored scheduler submission artifact without opening an MCP write tool:

```text
doc-based-coding scheduler admit-exchange-artifact \
  --artifact-id <artifact-id> \
  --version <version> \
  --snapshot-path .dbc/scheduler/scheduler-state.json \
  --event-log-path .dbc/scheduler/scheduler-events.jsonl
```

Optional inputs:

```text
--artifact-store-path .dbc/orchestration/exchange-artifacts.json
--admission-ledger-path .dbc/orchestration/exchange-artifact-admissions.json
--allow-duplicate-admission
--actor <actor-id>
--replace-existing
--timestamp <timestamp>
```

Expected CLI behavior:

1. Resolve relative paths under the detected project root.
2. Default `--artifact-store-path` to
   `.dbc/orchestration/exchange-artifacts.json`.
3. Require explicit scheduler snapshot and event-log paths.
4. Default `--admission-ledger-path` to
   `.dbc/orchestration/exchange-artifact-admissions.json`.
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
   `.dbc/progress-graph/local-work-trajectory.json`.

### CLI Admission Ledger Readback

Use the CLI admission-ledger readback surface when an operator or host script
needs to verify exact stored-artifact admission history without mutating
scheduler state:

```text
doc-based-coding scheduler inspect-admissions \
  --admission-ledger-path .dbc/orchestration/exchange-artifact-admissions.json \
  --artifact-id <artifact-id> \
  --version <version>
```

Expected ledger behavior:

1. Read `.dbc/orchestration/exchange-artifact-admissions.json` by default.
2. Report compact `status_counts`, `records[]`, `artifact_ids`, filters, and
   authority clues.
3. Include `admitted`, `rejected_duplicate`, and `failed` records.
4. Return an empty readback when the ledger file is missing.
5. Do not mutate scheduler state, exchange artifacts, scheduler projection, or
   `.dbc/progress-graph/local-work-trajectory.json`.

### CLI Operator Readback And Projection

Use the CLI readback, bounded tick, and projection surfaces when an operator or
script needs to verify admission results without an MCP host:

```text
doc-based-coding scheduler inspect-state \
  --snapshot-path .dbc/scheduler/scheduler-state.json \
  --event-log-path .dbc/scheduler/scheduler-events.jsonl

doc-based-coding scheduler tick \
  --snapshot-path .dbc/scheduler/scheduler-state.json \
  --event-log-path .dbc/scheduler/scheduler-events.jsonl \
  --max-runs 1

doc-based-coding scheduler daemon-loop \
  --snapshot-path .dbc/scheduler/scheduler-state.json \
  --event-log-path .dbc/scheduler/scheduler-events.jsonl \
  --max-ticks 3 \
  --max-runs-per-tick 1 \
  --max-runtime-failures 1 \
  --evidence-id scheduler-loop-smoke

doc-based-coding scheduler project \
  --snapshot-path .dbc/scheduler/scheduler-state.json \
  --event-log-path .dbc/scheduler/scheduler-events.jsonl
```

Optional projection inputs:

```text
--output-path .dbc/progress-graph/scheduler-work-trajectory.json
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
   providers, or mutate `.dbc/progress-graph/local-work-trajectory.json`.

Expected tick behavior:

1. Recover scheduler state from explicit snapshot and event-log paths.
2. Run at most the requested `--max-runs` fake-runtime tasks.
3. Return `run_count`, `stop_reason`, `queue_summary`, scheduler event count,
   and `authority_split`.
4. Write scheduler snapshot/event-log state through scheduler primitives.
5. Do not run real providers, refresh scheduler projection, mutate exchange
   artifacts, mutate admission ledger, or mutate
   `.dbc/progress-graph/local-work-trajectory.json`.
6. Evidence writing is explicit: `--evidence-id <id>` writes
   `product_type="scheduler_loop_evidence"` under
   `.dbc/scheduler/evidence/<safe-id>.json`; without `--evidence-id`, no
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
   `.dbc/progress-graph/local-work-trajectory.json`.

Expected projection CLI behavior:

1. Read scheduler snapshot and optional scheduler / merge-gate JSONL logs.
2. Write `.dbc/progress-graph/scheduler-work-trajectory.json` by default, or
   the explicit `--output-path`.
3. Print trajectory identity, projection path, event/lane/relation counts, and
   authority clues.
4. Do not run providers, mutate scheduler state, mark exchange artifacts
   consumed, or mutate
   `.dbc/progress-graph/local-work-trajectory.json`.

Recommended operator workflow:

```text
schedulerOperatorDogfoodClosure
doc-based-coding scheduler operator-dogfood-closure ...
schedulerOperatorWorkflow
doc-based-coding scheduler operator-workflow ...
schedulerSupervisorDogfoodWorkflow
doc-based-coding scheduler supervisor-dogfood-workflow ...
schedulerStorageBindingArtifactPublish
doc-based-coding scheduler publish-storage-binding-artifact ...
doc-based-coding scheduler evidence-publish-consumer-closure ...
doc-based-coding resources read dbc://exchange-artifacts/bundle
agentExchangeMailbox
doc-based-coding scheduler inspect-agent-mailbox --agent-id <agent-id>
agentExchangeHistory
doc-based-coding scheduler inspect-agent-history ...
doc-based-coding resources read dbc://agent-exchange/history
agentExchangeActionCandidates
doc-based-coding scheduler inspect-agent-action-candidates ...
doc-based-coding resources read dbc://agent-exchange/action-candidates
agentExchangeActionCandidateDecide
doc-based-coding scheduler decide-agent-action-candidate ...
agentExchangeAcceptedSchedulerCandidateConsume
doc-based-coding scheduler consume-accepted-scheduler-candidate ...
agentExchangeAcceptedReviewCandidateConsume
doc-based-coding scheduler consume-accepted-review-candidate ...
agentExchangeAcceptedHandoffCandidateConsume
doc-based-coding scheduler consume-accepted-handoff-candidate ...
agentExchangeAcceptedMergeCandidateConsume
doc-based-coding scheduler consume-accepted-merge-candidate ...
agentExchangeAcceptedBlockerCandidateConsume
doc-based-coding scheduler consume-accepted-blocker-candidate ...
agentExchangeReply
doc-based-coding scheduler reply-exchange-artifact ...
agentExchangeTransition
doc-based-coding scheduler transition-exchange-artifact ...
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

Prefer `schedulerOperatorDogfoodClosure` or `doc-based-coding scheduler
operator-dogfood-closure` when the current gate wants the complete deterministic
operator evidence closure through one shared product. The default
`binding-consumer` fixture covers fixture seed, binding-ref inspection, exact
admission, consumed lifecycle marking, bounded fake loop evidence, projection
refresh, and Host Evidence readback.
Prefer `schedulerOperatorWorkflow` or `doc-based-coding scheduler
operator-workflow` when the current gate wants opt-in control over individual
operator steps rather than the whole closure. Include `inspectBindingRefs=true`
or `--inspect-binding-refs` when the same workflow payload should show
supervisor storage binding readiness before explicit admission.
Prefer `schedulerSupervisorDogfoodWorkflow` or `doc-based-coding scheduler
supervisor-dogfood-workflow` when the current gate wants the complete
supervisor sequence through seed, exact admission, lifecycle start, supervisor
step, and final readback.
Prefer `schedulerStorageBindingArtifactPublish` or `doc-based-coding scheduler
publish-storage-binding-artifact` when a gate has a durable supervisor storage
binding evidence file and needs to make its compact summary available as an
exact-version ExchangeArtifact for downstream scheduler submissions.
Prefer `doc-based-coding scheduler evidence-publish-consumer-closure` when a
gate must prove the whole path from durable supervisor storage binding evidence
through published exact-version binding artifact into a consuming scheduler
submission and fake-runtime operator closure. This supersedes the
`binding-consumer` fixture for that specific proof because the consumer must
reference the artifact produced by the publish step, not a directly seeded
fixture artifact.
The consuming scheduler submission references the artifact produced by the publish step.
Prefer `schedulerBindingReferenceInspect` or `doc-based-coding scheduler
inspect-binding-refs` before admission when the candidate task consumes
`supervisor_storage_binding_artifact` refs and the inspection is intentionally
separate from the shared operator workflow.
Prefer `agentExchangeMailbox` or `doc-based-coding scheduler
inspect-agent-mailbox --agent-id <agent-id>` when a scheduled or runtime agent
needs its own ExchangeArtifact communication view. Use it for per-agent
inbox/outbox/related/actionable readback, not for store-wide admission
candidate inspection.
Prefer `agentExchangeHistory`, `doc-based-coding scheduler
inspect-agent-history`, or `doc-based-coding resources read
dbc://agent-exchange/history` when a guide agent needs a compact
communication-history readback over ExchangeArtifact causality and `log` parts.
Use it for participant/lifecycle counts, causality edges, and compact timeline
entries, not for raw transcript replay.
Prefer `agentExchangeActionCandidates`, `doc-based-coding scheduler
inspect-agent-action-candidates`, or `doc-based-coding resources read
dbc://agent-exchange/action-candidates` when a guide or scheduler-facing agent
needs to see which communication products are candidates for scheduler
admission, review, handoff, blocker, or merge follow-up. Treat it as read-only
candidate discovery; use explicit downstream surfaces for any mutation.
Prefer `agentExchangeActionCandidateDecide` or `doc-based-coding scheduler
decide-agent-action-candidate` when a guide/operator needs to record an
accept/reject/defer/supersede decision for one candidate as a durable
ExchangeArtifact. Treat it as a decision product only; use explicit downstream
surfaces for scheduler admission, review intake, handoff persistence, blocker
state, or merge resolution.
Prefer `agentExchangeAcceptedSchedulerCandidateConsume` or `doc-based-coding
scheduler consume-accepted-scheduler-candidate` when an accepted
`scheduler_submission_candidate` disposition should be turned into real
scheduler admission through the existing exact-version ledger-backed admission
path. Do not use it for review, handoff, blocker, or merge candidates.
Prefer `agentExchangeAcceptedReviewCandidateConsume` or `doc-based-coding
scheduler consume-accepted-review-candidate` when an accepted
`review_candidate` disposition should be turned into review intake through the
existing review adapter. Do not use it for scheduler, handoff, blocker, or
merge candidates.
Prefer `agentExchangeAcceptedHandoffCandidateConsume` or `doc-based-coding
scheduler consume-accepted-handoff-candidate` when an accepted
`handoff_candidate` disposition should be turned into a schema-valid Handoff
payload through the existing handoff delivery adapter. Always provide an
explicit handoff directory. Do not use it for scheduler, review, blocker, or
merge candidates.
Prefer `agentExchangeAcceptedMergeCandidateConsume` or `doc-based-coding
scheduler consume-accepted-merge-candidate` when an accepted `merge_candidate`
disposition should resolve an existing scheduler merge gate. Always provide an
explicit `gateId` and `approved` decision; do not infer a gate from
ExchangeArtifact relations. Do not use it for scheduler, review, handoff, or
blocker candidates.
Prefer `agentExchangeAcceptedBlockerCandidateConsume` or `doc-based-coding
scheduler consume-accepted-blocker-candidate` when an accepted
`blocker_candidate` disposition should block an existing scheduler task. Always
provide an explicit `taskId` and non-empty reason; do not infer a task from
ExchangeArtifact relations. Do not use it for scheduler, review, handoff, or
merge candidates.
Use `doc-based-coding scheduler guide-worker-exchange-dogfood` when the current
gate needs to prove the whole guide/worker communication sequence locally:
worker-addressed coordination product, worker mailbox readback, worker reply,
scheduler submission candidate, guide disposition, and explicit accepted
scheduler-candidate consumption. This is a CLI/runtime dogfood surface, not a
new MCP tool.
Prefer `agentExchangeReply` or `doc-based-coding scheduler
reply-exchange-artifact` when an agent needs to answer one exact
ExchangeArtifact version while preserving `causality.replies_to` and compact
coordination logs.
Prefer `agentExchangeTransition` or `doc-based-coding scheduler
transition-exchange-artifact` when an agent or guide needs to mark one exact
ExchangeArtifact version `accepted`, `rejected`, `consumed`, `superseded`, or
`archived` without triggering scheduler admission or provider execution.
Use `doc-based-coding scheduler seed-dogfood-fixture --fixture binding-consumer`
when a gate needs a deterministic compact supervisor storage binding artifact
plus a scheduler submission that consumes it. Then run
`schedulerOperatorWorkflow` with `inspectBindingRefs=true` and `admit=true`.
Prefer the lower-level commands/tools when the gate is specifically validating
an individual lifecycle step.

Expected shared workflow behavior:

1. Default mode is read-only: inspect candidates and read Host Evidence
   presentation.
2. `inspectBindingRefs=true` / `--inspect-binding-refs` reads the same exact
   artifact/version and returns binding-ref readiness without mutation.
3. `admit=true` / `--admit` admits one exact artifact/version and writes the
   admission ledger. When `inspectBindingRefs=true` /
   `--inspect-binding-refs` is also enabled, the admission record includes a
   compact `binding_reference_summary`.
4. `runLoop=true` / `--run-loop` runs only the bounded fake scheduler loop and
   writes scheduler-loop evidence.
5. `refreshProjection=true` / `--refresh-projection` refreshes only the
   scheduler-derived projection artifact.
6. Per-step status is returned in `steps[]`; failed inspection or admission
   skips dependent admission/loop/projection steps.
7. The shared workflow does not run live providers, start a background daemon,
   mark ExchangeArtifacts consumed, or mutate
   `.dbc/progress-graph/local-work-trajectory.json`.

Expected supervisor dogfood workflow behavior:

1. Seed one deterministic scheduler dogfood fixture (`simple` or `multilane`).
2. Admit the exact fixture artifact/version into scheduler snapshot/event-log
   state.
3. Start lifecycle control explicitly.
4. Run one fake-runtime host-managed supervisor step.
5. Read final lifecycle and scheduler queue facts.
6. Do not refresh scheduler projection, run cleanup, start a service, or mutate
   `.dbc/progress-graph/local-work-trajectory.json`.

## Submit

Call `schedulerSubmitTasks` with a small batch. Use `fake` runtime providers for
the smoke path.

Recommended shape:

```json
{
  "snapshotPath": ".dbc/scheduler/scheduler-state.json",
  "eventLogPath": ".dbc/scheduler/scheduler-events.jsonl",
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
  `.dbc/progress-graph/scheduler-work-trajectory.json` unless an explicit
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
   JSON under `.dbc/scheduler/evidence/`.
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
doc-based-coding qoder smoke
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
8. When a CLI smoke is needed, run `doc-based-coding qoder smoke` instead of
   hand-assembling the Python helper, but keep it host-owned and outside MCP.

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
doc-based-coding qoder smoke
run_host_owned_qoder_smoke()
HostOwnedQoderSmokeRunConfig
QoderSmokeTaskConfig
```

The helper lives under `tools/progress_graph/qoder_smoke.py` because it composes
the host dogfood harness, scheduler projection, and evidence artifacts. It is
not a scheduler daemon and is not an MCP execution surface.

Expected CLI smoke options:

```text
--auth-mode env|qodercli
--auth-env-var NAME
--sdk-module NAME
--cwd PATH
--model NAME
--max-turns N
--permission-request-policy deny|surface
--snapshot-path .dbc/scheduler/qoder-smoke-state.json
--event-log-path .dbc/scheduler/qoder-smoke-events.jsonl
--evidence-id qoder-smoke
--evidence-path .dbc/scheduler/evidence/qoder-smoke.json
--projection-output-path .dbc/progress-graph/scheduler-work-trajectory.json
--host-invocation-id host-owned-qoder-smoke-cli
--reason "bounded host-owned Qoder smoke"
--reset-snapshot
--no-initialize-snapshot
--timestamp 2026-06-22T00:00:00+08:00
```

Expected helper behavior:

1. Create or reuse `.dbc/scheduler/qoder-smoke-state.json`.
2. Create or reuse `.dbc/scheduler/qoder-smoke-events.jsonl`.
3. Build a one-task Qoder smoke scheduler snapshot when requested.
4. Construct host invocation and qoder permission grant.
5. Construct `QoderSDKQueryClient` from host config, unless an injected
   `QoderQueryClient` is supplied for tests.
6. Delegate execution to `run_host_runtime_dogfood_harness()`.
7. Write compact `HostSchedulerRunEvidence` and scheduler-derived trajectory
   projection.
8. The CLI command must never accept a raw token value; credentials stay in the
   host environment or supported SDK auth mode.

Use injected clients for deterministic tests. Use the real SDK wrapper only
when the host environment intentionally provides `qoder-agent-sdk` and
`QODER_PERSONAL_ACCESS_TOKEN`.

If SDK/auth are missing, the helper should fail before evidence/projection
writes and leave the smoke task in `proposed` state. Treat that as expected
negative-path evidence, not as scheduler corruption.

With `doc-based-coding qoder smoke --no-initialize-snapshot`, readiness-negative
hosts should fail without creating the smoke scheduler snapshot.

### Host-Owned Guide Worker Provider Execution

Use the host-owned guide-worker wrapper when the current gate asks to exercise
provider-backed worker agents on different Local Work Trajectory lanes:

```text
doc-based-coding qoder guide-worker-smoke
run_host_owned_guide_worker_provider_execution()
HostOwnedGuideWorkerProviderExecutionConfig
```

Expected CLI options:

```text
--auth-mode env|qodercli
--auth-env-var NAME
--sdk-module NAME
--cwd PATH
--model NAME
--max-turns N
--permission-request-policy deny|surface
--artifact-store-path .dbc/orchestration/exchange-artifacts.json
--admission-ledger-path .dbc/orchestration/exchange-artifact-admissions.json
--snapshot-path .dbc/scheduler/guide-worker-provider-execution-state.json
--event-log-path .dbc/scheduler/guide-worker-provider-execution-events.jsonl
--evidence-id guide-worker-provider-execution
--evidence-path .dbc/scheduler/evidence/guide-worker-provider-execution.json
--host-invocation-id host-owned-guide-worker-provider-execution-cli
--reason "bounded host-owned guide-worker provider execution"
--guide-task-title "Build maze game"
--guide-task-summary "Split browser client and server API work."
--planner-lane lane:client=Client UI:browser controls and test hooks:client,web
--planner-lane lane:server=Server API:state API and port boundary:server,api
--max-parallel-lanes 2
--max-waves 1
--wave-execution-mode serial|threaded
--timestamp 2026-06-24T00:00:00+08:00
```

Expected helper behavior:

1. Validate Qoder SDK/auth readiness before writing ExchangeArtifact store,
   scheduler state, event logs, or evidence.
2. Create a guide instruction artifact and scheduler worker task batch.
3. When `--planner-lane` is supplied, derive worker tasks from the deterministic
   guide planner and default those planned workers to Qoder in this host-owned
   wrapper. Explicit worker instructions still take precedence at the helper
   layer.
4. Emit worker tasks with `AgentSpec.runtime_provider` from
   `workerRuntimeProvider`.
5. Execute at most one ready worker task per lane per wave through the
   host-authorized runtime registry.
6. Merge wave results deterministically by task id.
7. Write compact `host_guide_worker_provider_execution_evidence` with
   planner metadata, generated instructions, per-worker execution receipts,
   provider, lane, wave, task state, output artifact, path, and authority facts.
8. Keep MCP `schedulerGuideWorkerLocalOrchestration` fake-only.

If SDK/auth are missing, the wrapper should fail before evidence, scheduler
state, or exchange-store writes. Treat that as expected negative-path evidence.

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
- durable supervisor storage binding evidence path and published binding
  artifact id/version when `evidence-publish-consumer-closure` was used
- consuming scheduler submission artifact id/version and whether it references
  the published binding artifact instead of a fixture artifact
- host-runner result JSON when a host-authorized adapter was used
- any real-provider rejection if intentionally tested
- validation commands or MCP responses used as evidence
