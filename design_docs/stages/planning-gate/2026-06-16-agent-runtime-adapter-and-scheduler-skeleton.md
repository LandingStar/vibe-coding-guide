# Planning Gate — Agent Runtime Adapter And Scheduler Skeleton

> Date: 2026-06-16
> Status: READY-FOR-CLOSE-REVIEW

## Trigger

The project has confirmed a three-layer structure:

1. Project-owned orchestration layer.
2. Agent runtime layer.
3. Bare model layer.

Qoder SDK is now positioned as an early agent runtime backend for implementation and testing support, not as the core scheduler and not as a bare model API.

## Authority Inputs

- `design_docs/agent-runtime-layering-and-orchestration-slice-plan.md`
- `design_docs/agent-coordination-exchange-artifact-design-record.md`
- `design_docs/agent-home-and-scratch-space-design-record.md`
- `design_docs/scheduler-native-merge-gate-design-record.md`
- `design_docs/qoder-runtime-adapter-requirements.md`
- `design_docs/agent-cluster-scheduling-and-isolation-investigation.md`
- `design_docs/agent-sdk-adoption-feasibility.md`
- `docs/subagent-management.md`
- `design_docs/workspace-parallel-task-orchestration-direction-analysis.md`
- `design_docs/orchestration-bridge-mvp-boundary-draft.md`

## Problem

The project already has governance, subagent contracts, worker adapters, subgraph foundations, grouped review, orchestration bridge MVP, and Local Work Trajectory projection.

However, it still lacks a standalone orchestration-layer scheduler that can:

1. Own task graph state.
2. Decide readiness.
3. Enforce context scope and edit lease admission.
4. Select sandbox profile.
5. Call external agent runtimes through a replaceable adapter.
6. Normalize runtime events and results back into project-owned objects.
7. Preserve coordination artifacts as scoped and versioned intermediate products.

Without this layer, directly using Qoder / opencode / OpenAI Agents SDK would risk giving an external runtime authority over scheduling and write-back decisions that should remain project-owned.

For this first gate, opencode remains a research reference and later adapter candidate. It is not part of the required adapter validation surface.

## Scope

This gate is intentionally narrow.

### Slice 1 — Agent Runtime Adapter Contract

Define the project-owned adapter boundary:

1. `AgentRuntimeAdapter`.
2. `RuntimeCapabilities`.
3. `AgentSpec`.
4. `TaskSpec`.
5. `SessionHandle`.
6. `RunHandle`.
7. `RunEvent`.
8. `PermissionRequest`.
9. `ArtifactDelta`.
10. Mapping notes for Qoder and fake runtime.

Current implementation note:

```text
src/runtime/orchestration/runtime_adapter.py
- AgentRuntimeAdapter Protocol
- RuntimeCapabilities
- AgentSpec
- TaskSpec
- SessionHandle
- RunHandle
- RunEvent
- PermissionRequest
- ArtifactDelta
- RuntimeRunResult
- QoderQueryClient
- QoderQueryRequest
- QoderQueryResult
- QoderRuntimeErrorKind
- QoderRuntimeError
- qoder_query_result_from_response()
- FakeAgentRuntimeAdapter
- QoderAgentRuntimeAdapter
- AgentRuntimeAdapterRegistry
- qoder_runtime_capabilities()

src/runtime/orchestration/runtime_wiring.py
- RuntimeHostSurfaceKind
- RuntimeHostInvocation
- RuntimeProviderPermissionGrant
- RuntimeRegistryWiringConfig
- RuntimeRegistryWiringResult
- build_runtime_registry_from_config()
```

The fake runtime validates the contract without invoking any external SDK. It consumes versioned `ExchangeArtifact` references through `InMemoryArtifactVersionStore`, produces a result `ExchangeArtifact`, and records compact coordination events through `JsonlCoordinationEventLog`.

`AgentRuntimeAdapterRegistry` is the first provider-keyed runtime selection
facility. It registers concrete adapter instances by their declared capability
provider and lets scheduler / host code resolve an adapter for a task's
`AgentSpec.runtime_provider` without making the scheduler depend on a global
runtime singleton. The registry is instance-scoped so workspaces, tests, and
host surfaces can own their wiring independently.

`run_scheduled_task_with_registry()` is the narrow scheduler-side seam over the
registry. It resolves the task runtime from `task.agent.runtime_provider` and
then delegates to `run_ready_task()`. It does not drain queues, own sessions
beyond the optional session argument, or introduce daemon behavior.

`runtime_wiring.py` is now the first host-facing registry construction seam. It
builds an instance-scoped `AgentRuntimeAdapterRegistry` from explicit host
configuration instead of letting scheduler state construct adapters. The default
wiring registers only `fake`. Registering `qoder` requires both
an explicit `RuntimeProviderPermissionGrant` and an injected `QoderQueryClient`;
otherwise it fails with a clear configuration error. The grant must identify the
provider, approver, approval timestamp, and `allow_sdk_client=true`. This keeps
real runtime permission and SDK client construction in the Host UX /
Interaction Adapter layer, while preserving the scheduler as a consumer of an
already-authorized registry.

The host-level permission grant does not approve per-run runtime permission
requests. Shell, network, file read/write, and tool requests surfaced through
`QoderQueryResult.permission_requests` still flow into the scheduler-side review
gate.

`RuntimeHostInvocation` now records which host surface is asking to build a
runtime registry for one scheduler invocation. Current surfaces are:

```text
mcp-scheduler-run-once
cli-scheduler-run-once
host-authorized-adapter
```

The first two surfaces are fake-only in this gate. A qoder-capable registry can
only be built through `host-authorized-adapter` and still requires
`RuntimeProviderPermissionGrant` plus an injected `QoderQueryClient`. This keeps
`schedulerRunOnceAndProject` as a fake smoke path while leaving a precise host
adapter seam for future real runtime execution.

`QoderAgentRuntimeAdapter` is now present only as a mockable adapter skeleton. It
depends on a project-owned `QoderQueryClient` protocol and does not import or
require the real Qoder SDK. The client receives a stable `QoderQueryRequest`
containing the agent, task, session, instruction, acceptance, input artifact
references, and output artifact ID. This prevents a later real SDK wrapper from
directly coupling itself to scheduler internals. Mocked tests prove the registry
/ scheduler path can execute a `qoder` task and normalize the result into
`RuntimeRunResult`, `ExchangeArtifact`, `ArtifactDelta`, and compact run events.
`RuntimeRunResult.permission_requests` and
`QoderQueryResult.permission_requests` now carry surfaced runtime permission
requests without approving them inside the adapter.
`QoderRuntimeError` now provides the first stable adapter-side error
normalization surface for `sdk_unavailable`, `authentication_failed`,
`permission_denied`, `timeout`, `tool_execution_failed`, `invalid_response`,
`policy_cancelled`, and `unknown`. `QoderAgentRuntimeAdapter` fills task,
session, and run context before re-raising known qoder errors and wraps
unexpected query-client exceptions as `unknown` with `raw_error_type`.
`qoder_query_result_from_response()` now provides the first response-shape
normalization helper for future SDK wrappers: it converts response-like mappings
into `QoderQueryResult`, normalizes artifact deltas and permission requests, and
raises `QoderRuntimeError(error_kind="invalid_response")` for malformed
responses.
Real SDK wiring remains outside this gate's required implementation surface.
The real wrapper requirements are captured in
`design_docs/qoder-runtime-adapter-requirements.md`.

### Slice 2 — Scheduler Skeleton With Fake Runtime

Define and minimally implement local scheduler objects:

1. `ScheduledTask`.
2. `TaskDependency`.
3. `SchedulerState`.
4. `TaskRunRecord`.
5. `ContextScope`.
6. `EditScopeLease`.
7. `SandboxProfile`.
8. Local event-history persistence or equivalent testable state log.
9. Fake runtime execution path for one bounded task.

Current implementation note:

```text
src/runtime/orchestration/scheduler.py
- ScheduledTask
- TaskDependency
- SchedulerState
- TaskRunRecord
- ContextScope
- EditScopeLease
- SandboxProfile
- AdmissionDecision
- evaluate_task_admission()
- mark_ready_tasks()
- wake_dependent_tasks()
- run_ready_task()
- run_scheduled_task_with_registry()
- resolve_task_permission_review()
- SchedulerRunPolicy
- drain_ready_tasks()

src/runtime/orchestration/scheduler_store.py
- write_scheduler_state_snapshot()
- read_scheduler_state_snapshot()
- SchedulerEvent
- JsonlSchedulerEventLog
- SchedulerRecoveryResult
- SchedulerCompactionResult
- replay_scheduler_events()
- recover_scheduler_state()
- write_compacted_scheduler_snapshot()

src/runtime/orchestration/scheduler_submission.py
- SchedulerTaskSubmission
- SchedulerTaskSubmissionResult
- SchedulerTaskBatchSubmission
- SchedulerTaskBatchSubmissionResult
- scheduler_task_submission_to_artifact()
- scheduler_task_submission_from_artifact()
- submit_scheduler_task()
- scheduler_task_batch_submission_to_artifact()
- scheduler_task_batch_submission_from_artifact()
- submit_scheduler_task_batch()
- submit_scheduler_task_batch_with_persistence()

src/runtime/orchestration/scheduler_runner.py
- PersistedSchedulerRunOnceResult
- run_persisted_scheduler_once()
- run_persisted_scheduler_once_with_wiring()
```

The first scheduler skeleton can mark dependency-free tasks ready, keep dependency-blocked tasks waiting, block conflicting write leases against ready/running tasks, run one ready task through the fake runtime, wake direct downstream dependents after completion, round-trip scheduler state through a versioned JSON snapshot, and optionally append scheduler-owned lifecycle events to a JSONL log.

`SchedulerEvent` records scheduler decisions such as `task_ready`, `task_waiting`, `task_blocked`, `task_running`, `task_completed`, `task_run_failed`, `task_review_required`, `task_permission_approved`, and `task_permission_rejected`. It is not an `ExchangeArtifact` and does not store agent prose transcripts. It may carry run IDs, session IDs, dependency IDs, and output artifact IDs so later projection, review, or replay code can correlate scheduler state with runtime and artifact history.

`replay_scheduler_events()` now applies scheduler events to a baseline
`SchedulerState`. Replay can recover task lifecycle state, blocked / waiting
reasons, output artifact references, and completed run records. It deliberately
does not create tasks from event history; task contracts, context scope, edit
leases, and sandbox profiles must come from the scheduler-owned baseline state.

`recover_scheduler_state()` is the first narrow recovery entrypoint over the
snapshot plus JSONL history pair. It reads the scheduler-owned baseline JSON
snapshot, reads the scheduler event log, applies replay, and returns
`SchedulerRecoveryResult` with the baseline, events, recovered state, paths, and
strict-mode flag. It intentionally does not compact snapshots, create task
contracts from events, or start a daemon recovery loop.

`write_compacted_scheduler_snapshot()` is the first non-destructive snapshot
compaction primitive. It recovers scheduler state from the source snapshot and
event log, writes that recovered state to a caller-provided compacted snapshot
path, and returns `SchedulerCompactionResult`. This API deliberately does not
truncate, rotate, or rewrite the source event log; event-log rotation remains a
later policy slice.

`wake_dependent_tasks()` re-evaluates only direct dependents of a completed
source task. `run_ready_task()` uses that narrower wake-up path after completion
instead of globally scanning unrelated waiting tasks. This keeps wake-up behavior
local to the dependency edge that changed while preserving `mark_ready_tasks()`
as the explicit whole-queue readiness scan.

When a `RuntimeRunResult` carries `permission_requests`, the scheduler-side
permission gate stores the output artifact reference but marks the task
`review_required`, records `task_review_required`, and does not wake downstream
dependencies that require the task to be `complete`.

`resolve_task_permission_review()` now closes that first permission gate loop.
Approval turns the paused task into `complete`, updates its run record, records
`task_permission_approved`, and wakes direct downstream dependents. Rejection
turns the task into `blocked`, updates its run record, and records
`task_permission_rejected` without waking dependents. The same two event kinds
are replayable from scheduler JSONL history.

`drain_ready_tasks()` is the first bounded queue-drain primitive. It performs an
initial explicit readiness scan, runs ready tasks in deterministic task-id order
through the supplied runtime adapter, lets each completed task wake direct
dependents, and repeats until no ready task remains or `max_runs` is reached.
It returns a `SchedulerDrainResult` with the final state, run results, stop
reason, and remaining ready task IDs. This is deliberately a local primitive,
not a daemon, retry loop, or parallel process scheduler.

The first drain failure policy is intentionally conservative: a runtime
exception marks the failed task `blocked`, records `task_run_failed`, and stops
the current drain with `stop_reason=task_failed`. If readiness/admission leaves
only blocked tasks and no ready task, the drain returns `stop_reason=blocked_tasks`.
`SchedulerRunPolicy` now carries the bounded run knobs. Its default preserves the
conservative behavior. When `continue_on_failure=true`, the failed task remains
blocked and is not retried, but the drain may continue other currently ready
independent tasks. If the queue drains after one or more such failures, the
result uses `stop_reason=completed_with_failures` and reports all failed task
IDs. Retry, timeout, and cancellation remain policy fields / future behavior,
not active retry or kill mechanisms yet.

Current sandbox provider note:

```text
src/runtime/orchestration/sandbox.py
- SandboxCapability
- SandboxRequest
- SandboxAllocation
- SandboxProvider
- SandboxProviderRegistry
- SharedProcessSandboxProvider
- sandbox_capability_placeholder()
```

The scheduler already carries `SandboxProfile` as a task-owned isolation
request. The first provider contract now separates that request shape from
provider allocation metadata. `SharedProcessSandboxProvider` is intentionally
metadata-only and does not claim process or filesystem isolation. `git-worktree`,
`docker`, and `remote-vm` are represented only as placeholder capability shapes
until a later gate explicitly implements one of them.

Current preflight assembly note:

```text
src/runtime/orchestration/preflight.py
- OrchestrationPreflightBundle
- PreflightedTaskRunResult
- PreflightDrainResult
- build_orchestration_preflight_bundle()
- run_preflighted_task()
- drain_preflighted_ready_tasks()
```

The first preflight helper connects a ready `ScheduledTask` to its runtime
`TaskSpec`, metadata-only `SandboxAllocation`, and temporary
`AgentScratchSpace`. It does not run the task, create directories, or mutate
scheduler state; it only assembles the project-owned inputs a later executor can
consume. `run_preflighted_task()` is the first controlled execution seam over
that bundle: it checks that the bundle still matches the current
`SchedulerState`, resolves the runtime adapter from `AgentRuntimeAdapterRegistry`,
and delegates lifecycle mutation to `run_ready_task()`.

`drain_preflighted_ready_tasks()` is the preflight-aware bounded drain helper.
It serially performs readiness scanning, preflight assembly, runtime registry
selection, and scheduler-owned task execution. It preserves the same first
failure policy as `drain_ready_tasks()`: failed runtime tasks are marked
`blocked`, fail-fast is the default, and `continue_on_failure=true` only lets
independent ready branches continue after the failed task has been removed from
the ready queue. It returns `PreflightDrainResult`, including preflight bundles,
runtime results, stop reason, remaining ready IDs, blocked IDs, and failed IDs.

This is still a local skeleton, not a full durable event-replay backend with
snapshot compaction, retry policy, process supervision, or parallel execution.

Current task submission note:

`scheduler_submission.py` is the first artifact-centered intake surface for
scheduler-owned task state. It accepts structured exchange artifacts with
`product_type="scheduler_task_submission"` for one task and
`product_type="scheduler_task_batch_submission"` for a small task graph.
Single-task submission translates into one `ScheduledTask` plus optional
`TaskDependency` edges. Batch submission translates into multiple
`ScheduledTask` objects and their declared dependency edges in one state update
flow. These submission artifacts are input products, not running tasks, daemon
commands, or Local Work Trajectory mutations.

The first accepted fields mirror the existing scheduler contract: task ID,
title, instruction, `AgentSpec`, `ContextScope`, optional `EditScopeLease`,
`SandboxProfile`, input artifact references, acceptance criteria, output
artifact ID, and dependencies. The batch product adds batch ID, title, summary,
and a non-empty task list. The parser deliberately raises readable errors for
missing product type, missing required fields, duplicate task IDs inside a
batch, unsupported runtime providers, unsupported sandbox kinds, and malformed
reference/dependency lists.

The submission artifact encoders now attach a compact `log` payload part beside
the structured submission payload. This log records timestamp, actor, action,
channel, summary, and related artifact IDs so later communication-history
inspection can order and attribute the task submission without reading a raw
runtime transcript. The log is part of the exchange artifact; it does not
replace scheduler-owned `task_submitted` events.

`submit_scheduler_task_batch_with_persistence()` adds the current persistence
smoke. It submits a batch into `SchedulerState`, appends one `task_submitted`
audit event per task, writes the scheduler snapshot, and verifies that normal
`recover_scheduler_state()` can reload the snapshot/event pair before bounded
drain continues. The event log remains audit/projection material only; task
contracts are still recovered from the snapshot, not reconstructed from
`task_submitted` events.

MCP now exposes the same intake through `schedulerSubmitTasks`. The tool accepts
explicit `snapshotPath` and `eventLogPath`, plus either an existing batch-shaped
payload or `batchId` + `tasks` convenience fields. CamelCase MCP keys are
normalized into the scheduler submission payload shape before parsing. If the
snapshot does not exist, the tool starts from an empty `SchedulerState`; it then
uses the existing `scheduler_task_batch_submission` exchange-artifact parser and
`submit_scheduler_task_batch_with_persistence()` path. It submits task
contracts, appends `task_submitted` events, and writes the scheduler snapshot,
but it does not run tasks, refresh scheduler projection artifacts, or mutate
agent-owned Local Work Trajectory.

`scheduler_runner.py` provides the current one-shot command surface:
`run_persisted_scheduler_once()`. It recovers scheduler state from snapshot plus
event log, drains ready tasks through `drain_preflighted_ready_tasks()` using
explicit sandbox/runtime registries, appends normal scheduler lifecycle events
to the same JSONL log, and writes the post-run state back to the snapshot. This
is intentionally a bounded local run helper, not a daemon, process supervisor,
retry engine, or parallel execution runtime.

`run_persisted_scheduler_once_with_wiring()` is the host-only seam over the same
runner. It accepts a pre-built `RuntimeRegistryWiringResult` instead of a bare
runtime registry. Fake-only wiring can come from fake-only host surfaces such as
`mcp-scheduler-run-once`. If the runtime registry contains any non-fake provider,
the helper requires `RuntimeHostInvocation(surface="host-authorized-adapter")`;
otherwise it rejects the run before recovery/drain. The result records
`runtime_registry_providers` and `runtime_host_surface` for host-side audit.
This helper is not exposed as an MCP real-provider tool in this gate.

Current projection note:

```text
tools/progress_graph/scheduler_projection.py
- build_scheduler_work_trajectory()
- build_scheduler_work_trajectory_from_history()
- scheduler_work_trajectory_json_path()
- write_scheduler_work_trajectory_artifact()
- run_persisted_scheduler_once_and_refresh_projection()
```

This helper projects `SchedulerState` into a `LocalWorkTrajectory` view without
writing `.codex/progress-graph/local-work-trajectory.json`. It maps scheduler
context scopes to lanes, tasks to trajectory events, dependencies to explicit
trajectory relations, and run/output artifact references to event metadata.
The direction remains one-way: scheduler state is authority, while Local Work
Trajectory is a read-only visualization surface for this path.

The persisted one-shot runner path is now covered by projection validation:
after `submit_scheduler_task_batch_with_persistence()` and
`run_persisted_scheduler_once()`, rebuilding the scheduler-derived trajectory
from the post-run `SchedulerState` exposes completed task events, dependency
relations, run record IDs, session IDs, and output artifact IDs / versions. This
keeps runner visibility in the projection layer and still avoids writing or
mutating the workspace-local trajectory artifact.

`run_persisted_scheduler_once_and_refresh_projection()` is the first local
Python API that closes the persisted-run plus projection-refresh loop. It lives
in `tools.progress_graph`, not in the orchestration runtime, so runtime code
does not depend on progress graph exports. The helper:

1. Recovers and drains one bounded scheduler run through
   `run_persisted_scheduler_once()`.
2. Re-reads the post-run scheduler snapshot.
3. Writes `.codex/progress-graph/scheduler-work-trajectory.json` using the same
   scheduler JSONL event log as history input.
4. Returns both the run result and the loaded scheduler-derived trajectory.

This remains a local API / host-adapter seam. It does not create a daemon, does
not mutate `.codex/progress-graph/local-work-trajectory.json`, and does not add
a new MCP tool yet. A future MCP entry should wrap this helper after the host
permission and invocation contract is fixed.

MCP now exposes that first wrapper as `schedulerRunOnceAndProject`. The initial
contract deliberately requires explicit `snapshotPath` and `eventLogPath`
instead of inventing a default scheduler state location. It uses the built-in
fake runtime adapter and shared-process sandbox provider, runs one bounded
persisted scheduler pass, writes the updated scheduler snapshot, and refreshes
the scheduler-derived trajectory projection. It remains a thin host-facing
entry over the local Python helper:

```text
schedulerRunOnceAndProject
- required: snapshotPath
- required: eventLogPath
- optional: mergeGateEventLogPath
- optional: outputPath
- optional: maxRuns
- optional: timestamp
- optional: runtimeProvider (defaults to fake; currently fake-only)
- optional: guideContext
- optional: sourceGraphId / sourceNodeId
```

This MCP tool is not yet the real Qoder or multi-runtime execution surface. The
`runtimeProvider` parameter is present only to make the boundary explicit and to
avoid silent misuse: omitted / empty / `fake` values use the built-in fake
runtime smoke path, while `qoder` or any unknown provider returns a clear
fake-only error. Real provider selection should be introduced only after host
permission, sandbox, and adapter registration contracts are explicit.

The MCP implementation now uses `build_runtime_registry_from_config()` even for
the fake-only smoke path. It reports `runtime_registry_providers=["fake"]` on a
successful run so callers can inspect which registry was actually wired. This is
not a qoder execution surface yet: the tool still rejects `runtimeProvider=qoder`
before building the registry, and qoder wiring remains limited to mocked,
host-authorized tests until a later host permission / real SDK adapter slice.
The tool also supplies `RuntimeHostInvocation(surface="mcp-scheduler-run-once")`
to the wiring layer, making the fake-only boundary machine-checkable.

`build_scheduler_work_trajectory()` can also receive optional scheduler events
and attach compact history clues to matching task events. The metadata records
event IDs, kinds, timestamps, and sequences for already-known scheduler tasks
only. Orphan event-log entries are ignored by projection, and task contracts
still come from `SchedulerState` / snapshot recovery rather than trajectory or
event-log display data.

The scheduler-derived projection now also summarizes multi-dependency fan-in.
When more than one dependency targets the same scheduled task, the projector
adds a synthetic `merge` event on the target lane, adds fan-in source relations
from each upstream task into that merge event, and adds one `merges_into`
relation from the merge event to the target task. The original dependency edges
remain present for compatibility and exact inspection. This is a display
summary only; the scheduler does not gain a new task or lifecycle state from the
synthetic merge event.

The scheduler-native merge gate boundary is now documented separately in
`design_docs/scheduler-native-merge-gate-design-record.md`. The current
decision is to keep ordinary multi-dependency fan-in dependency-only and use
projection summaries for readability. A scheduler-owned merge gate should be
introduced only when the join point has real scheduler work, such as review,
artifact merge, branch choice, compatibility checking, conflict resolution, or
an explicit fan-in decision.

The first scheduler-owned merge gate skeleton is now implemented:
`SchedulerMergeGate` is a snapshot-owned product on
`SchedulerState.merge_gates`, round-trips through scheduler snapshot JSON, and
projects as a real `merge` event with `scheduler-owned-merge-gate` metadata.
The projector suppresses the synthetic fan-in summary for a target that already
has a real merge gate, while still preserving exact dependency edges. Runtime
target admission also waits for associated merge gates to reach `complete`
after ordinary task dependencies are satisfied.

`resolve_scheduler_merge_gate()` is the first explicit external decision loop:
approval marks a non-terminal gate `complete`, can store a decision artifact
reference, and re-evaluates the target task; rejection marks the gate `blocked`
and keeps the target waiting on that gate. Runtime execution and automatic
artifact merge output are intentionally left for later slices.

Merge-gate-specific event schema is now separated from task scheduler events:
`SchedulerMergeGateEvent` plus `JsonlSchedulerMergeGateEventLog` can persist
append-only merge gate history such as `merge_gate_completed` and
`merge_gate_blocked`. `resolve_scheduler_merge_gate()` can write to this sink
when provided. These events are not consumed by scheduler replay yet; snapshot
state remains the merge gate contract authority.

`build_scheduler_work_trajectory()` can optionally receive the merge-gate event
history and attach it to scheduler-owned merge gate events as metadata. The
projection keeps both machine-friendly columns (`scheduler_merge_gate_event_ids`,
kinds, timestamps, sequences, and decision artifact references) and a compact
human-readable `scheduler_merge_gate_event_log` line list. The log list is for
historical communication management and inspection only; orphan gate events are
ignored, and the projected log does not create, replay, or resolve merge gate
contracts.

`build_scheduler_work_trajectory_from_history()` is the first convenience entry
over persisted JSONL history. It reads optional `JsonlSchedulerEventLog` and
`JsonlSchedulerMergeGateEventLog` files, forwards their records into
`build_scheduler_work_trajectory()`, and records the source paths / event counts
on trajectory metadata. It is still a projection helper, not scheduler recovery,
snapshot compaction, or log replay.

The scheduler-derived trajectory now also carries a compact history timeline on
trajectory metadata. This timeline merges scheduler task events and scheduler
merge-gate events into stable, timestamped line entries for inspection and later
UI consumption:

```text
scheduler_history_timeline
scheduler_history_timeline_count
scheduler_history_timeline_limit
scheduler_history_timeline_truncated
```

The compact timeline is intentionally projection-only. It may include orphan
history events so humans can inspect them, but it does not create trajectory
nodes, replay scheduler contracts, repair snapshots, or resolve merge gates.
Node-level metadata remains narrower and only attaches history clues to known
tasks or known merge gates.

`write_scheduler_work_trajectory_artifact()` is the first stable artifact
writer for this projection. Its default output is
`.codex/progress-graph/scheduler-work-trajectory.json`, intentionally separate
from agent-owned `.codex/progress-graph/local-work-trajectory.json`. The writer
can consume the optional JSONL history paths above and records
`projection_artifact_path` in metadata, but it must not mutate Local Work
Trajectory lifecycle state.

MCP now exposes the same writer through `schedulerProjection`. The tool accepts
`snapshotPath` plus optional `schedulerEventLogPath`,
`mergeGateEventLogPath`, `outputPath`, `trajectoryId`, `title`,
`guideContext`, `sourceGraphId`, and `sourceNodeId`. It reads a scheduler
snapshot, writes the scheduler projection artifact, and returns the written
path plus compact trajectory counts. This is the first host/agent callable
surface for scheduler projection refresh and remains separate from
`localTrajectory`, which is still the agent-owned lifecycle mutation tool.

The current MCP smoke path is now explicitly documented and prompt-backed:
`schedulerSubmitTasks -> schedulerProjection -> schedulerRunOnceAndProject`.
The smoke first submits fake-runtime task contracts into scheduler-owned
snapshot/event-log state, optionally projects the queued graph before execution,
then runs a bounded fake-runtime pass and refreshes the scheduler-derived
projection. The accompanying prompt is
`.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md` with a bootstrap copy under
`doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/`. This prompt is
for scheduler lifecycle verification only; it must not be used as a replacement
for agent-owned `localTrajectory` lifecycle updates.

Preview consumption contract:

1. `.codex/progress-graph/local-work-trajectory.json` is the agent-owned Local
   Work Trajectory lifecycle artifact. It may be missing, empty, or temporarily
   invalid without invalidating scheduler state.
2. `.codex/progress-graph/scheduler-work-trajectory.json` is the scheduler-
   derived read-only projection artifact. It may be missing when no scheduler
   snapshot has been projected yet.
3. A host preview should read both artifacts independently, preserve per-
   artifact `exists`, `path`, `error`, `trajectory`, and compact `summary`
   fields, and avoid treating either artifact's parse failure as a failure of
   the other artifact.
4. The two trajectory payloads must not be merged into one lifecycle object.
   UI may display them as tabs, sections, overlays, or detail panels, but the
   authority labels remain separate: `agent` for local trajectory and
   `scheduler` for scheduler projection.
5. Refresh behavior remains split: `localTrajectory` mutates only the agent
   lifecycle artifact; `schedulerProjection` refreshes only the scheduler
   projection artifact.

### Slice 3 — Readiness And Admission Smoke Test

Prove the scheduler can:

1. Mark a dependency-free task ready.
2. Keep a dependency-blocked task waiting.
3. Reject conflicting edit leases with a readable reason.
4. Move one fake task through proposed -> ready -> running -> review_required or complete.

## Non-Goals

This gate does not:

1. Execute real Qoder.
2. Execute real opencode.
3. Implement real process parallelism.
4. Implement Docker, remote VM, or git-worktree sandbox.
5. Redesign Local Work Trajectory UI.
6. Let Local Work Trajectory become scheduler authority.
7. Add full team / swarm runtime.
8. Allow runtime subagents to become project-level lanes automatically.
9. Validate opencode adapter behavior.
10. Implement persistent Agent Home storage.
11. Implement full ExchangeArtifact persistence or UI rendering.

## Required Design Decisions

Before implementation, the gate must fix:

1. Whether adapter contracts live under existing worker abstractions or a new orchestration runtime namespace.
2. Whether scheduler state persists as JSON first or an in-memory object with explicit event-log export first.
3. How `SubagentReport` and `ArtifactDelta` relate in the first fake runtime path.
4. How Local Work Trajectory projection is deferred without losing traceability.
5. How the fake runtime path references `ExchangeArtifact` without requiring the full artifact store.

## Acceptance Criteria

The gate may close only when:

1. The adapter contract can map to Qoder and fake runtime without changing scheduler objects.
2. Scheduler state can represent at least a three-task graph with dependencies.
3. A fake runtime task can complete through the adapter boundary.
4. Edit lease conflict detection has focused tests.
5. Context scope, edit lease, and sandbox profile are present as first-class data objects.
6. Documentation explicitly preserves the rule: orchestration state is authority; Local Work Trajectory is projection.
7. The scheduler skeleton can reference exchange artifact IDs or placeholders without treating prose transcript as authority.

## Completion Evidence

Current review artifact:

- `review/agent-runtime-adapter-and-scheduler-skeleton-2026-06-17.md`

Follow-up direction analysis:

- `design_docs/agent-runtime-adapter-and-scheduler-followup-direction-analysis.md`

Current verdict: the implementation evidence satisfies all seven acceptance
criteria for this gate, so the gate is ready for close review.

This is not a formal stage close. The remaining close work is the normal
writeback bundle: accept or revise the immediate follow-up direction and
synchronize the relevant project status surfaces only after close is accepted.

Residual work remains outside this gate by design: real Qoder SDK execution,
opencode adapter behavior, real sandbox isolation, daemon scheduling, retry /
timeout execution policy, full ExchangeArtifact persistence, UI rendering, and
persistent Agent Home storage.

## Recommended First Implementation Bias

Prefer a small Python implementation near the existing runtime/orchestration surface if it avoids duplicating the older PEP executor model.

Do not place the scheduler inside VS Code extension code or graph UI code.

Do not make Qoder a required dependency for the first implementation slice.
