# Agent Runtime Layering And Orchestration Slice Plan

> Date: 2026-06-16
> Status: design record / planning recommendation

## Context

This document records the discussion after the initial agent-cluster and SDK feasibility research:

1. The project still needs a project-owned orchestration layer before entering real multi-agent execution.
2. Qoder SDK should be used as an early agent runtime backend for implementation and testing support.
3. Qoder SDK should not become the core scheduler.
4. Bare model calls remain a separate lower-level option and should not be confused with agent runtime execution.

Related documents:

- `design_docs/agent-cluster-scheduling-and-isolation-investigation.md`
- `design_docs/agent-sdk-adoption-feasibility.md`
- `design_docs/qoder-runtime-adapter-requirements.md`
- `design_docs/agent-coordination-exchange-artifact-design-record.md`
- `design_docs/agent-home-and-scratch-space-design-record.md`
- `design_docs/scheduler-native-merge-gate-design-record.md`
- `docs/subagent-management.md`
- `design_docs/workspace-parallel-task-orchestration-direction-analysis.md`
- `design_docs/orchestration-bridge-mvp-boundary-draft.md`

## Confirmed Three-Layer Structure

### 1. Orchestration Layer

This is the project-owned authority layer.

It owns:

1. Task graph and task lifecycle.
2. Lane / context stream decisions.
3. Dependency readiness and wake-up.
4. Context scope.
5. Edit scope lease and conflict classification.
6. Sandbox profile selection.
7. Resource limits, cancellation, retry, pause, resume, and timeout policy.
8. Merge gate, grouped review, write-back, and authority-doc protection.
9. Audit events and Local Work Trajectory projection.

It must not be delegated to Qoder, opencode, OpenAI Agents SDK, AutoGen, LangGraph, or any other external SDK.

The orchestration layer can call those runtimes, but it should remain the source of truth for scheduling state.

### 2. Agent Runtime Layer

This layer executes a bounded task that the orchestration layer has already admitted.

An agent runtime may provide:

1. Agent loop.
2. Tool use.
3. MCP access.
4. Session management.
5. Subagent delegation inside that runtime.
6. Event stream or hooks.
7. Permission callbacks.
8. Transcript inspection.

Qoder SDK currently belongs here.

The runtime receives a narrowed task contract and returns normalized events, report data, artifact deltas, and trace references. It does not decide the global task graph, write authority, merge policy, or project phase.

### 3. Bare Model Layer

This layer is direct inference.

It is useful when the project only needs:

1. Text generation.
2. Classification.
3. Summarization.
4. Structured extraction.
5. Small deterministic helper reasoning.

Bare model calls should not be used to run a coding worker that edits files or invokes tools unless the project wraps them in an agent runtime or worker adapter.

## Qoder SDK Position

The current judgment is:

> Qoder SDK is an agent runtime backend candidate, not the project scheduler and not a bare model API.

This is because the SDK exposes a Qoder agent execution surface rather than only a model inference endpoint. The documented surface includes:

1. `query()` as the main async execution entry.
2. File read/write, code search, command execution, and related tool use.
3. Custom subagents through `options.agents`.
4. Independent subagent context from the parent session.
5. Session control, including new sessions, resume, and fork.
6. Subagent transcript inspection.
7. Hooks / permission surfaces suitable for runtime observation and guardrails.
8. MCP server configuration for tool extension.

Therefore, during orchestration-layer development, Qoder should be used as an early `AgentRuntimeAdapter` implementation:

```text
TaskGraphScheduler
  -> AgentRuntimeAdapter(qoder)
       -> Qoder SDK query(...)
       -> normalized RunEvent / SubagentReport / ArtifactDelta
  -> merge gate / review / write-back
```

Qoder should not receive authority to:

1. Replan the whole project task graph.
2. Move Local Work Trajectory anchors directly.
3. Decide merge / write-back acceptance.
4. Edit authority docs unless the orchestration layer explicitly grants an edit lease.
5. Bypass project governance or review state.

## Agent Home And Scratch Space Position

Agent-private storage is a first-class orchestration resource, but it is not the same as runtime, task context, or edit authority.

The project now distinguishes:

1. `AgentRuntime`: execution session, tools, model, events.
2. `AgentHome`: audited persistent private folder for a registered agent.
3. `AgentScratchSpace`: temporary private folder for a run, task, or lane.
4. `ContextBundle`: current task visibility surface.
5. `EditScopeLease`: project artifact write authority.

An agent may request a persistent home from a workspace-registration authority. After audit approval, that home may store private capability material such as notes, checklists, safe templates, and de-identified experience. It must not store secrets, unauthorized project copies, hidden scheduler state, or unreviewed patches.

Temporary scratch space can exist without registration, but it must be archived or deleted when the agent is merged, retired, or reclaimed. Promotion from scratch into persistent home requires review.

Detailed boundary: `design_docs/agent-home-and-scratch-space-design-record.md`.

## Coordination Exchange Artifact Position

Agent communication should be artifact-centered rather than unrestricted chat-history centered.

The first-pass coordination product is `ExchangeArtifact`:

1. A common shell for query, proposal, blocker, result, review, contract, handoff, retention, and cleanup products.
2. A multi-part payload that can carry text, structured data, references, artifact deltas, contracts, evidence, relations, storage manifests, and logs.
3. A versioned and scoped product that can be referenced by scheduler state, Local Work Trajectory projection, review packets, and context bundles.

The `log` part is included in the first version for historical communication management. It stores compact timestamped coordination history and should not be confused with raw runtime transcript.

Detailed boundary: `design_docs/agent-coordination-exchange-artifact-design-record.md`.

## opencode Position

opencode remains a useful runtime candidate, but its shape is different.

The current reading is:

1. `opencode serve` exposes a headless HTTP / OpenAPI server.
2. The JS/TS SDK is primarily a type-safe client for controlling that server.
3. Its useful surfaces are sessions, messages, SSE events, agent listing, MCP registration, plugin hooks, and custom tools.

This makes opencode attractive as a session/server-first runtime backend, especially for programmatic control and event observation. It should still be adapted behind the same runtime contract instead of becoming the scheduler.

## Why No SDK Should Become The Core Scheduler

The scheduler must encode project-specific authority:

1. Which documents are authoritative.
2. Which task may run now.
3. Which context stream a task belongs to.
4. Which files may be edited.
5. Which sandbox profile is required.
6. Which dependencies block execution.
7. Which results require review.
8. Which write-back is accepted.
9. Which events project into Local Work Trajectory.

External SDKs usually solve a different problem: agent loop, tool invocation, sessions, tracing, workflow patterns, or sandbox execution. They can be excellent providers, but none of them should own this project's scheduling truth.

## Current Orchestration-Layer Baseline

The project is not starting from zero.

Already available:

1. PDP / PEP governance runtime.
2. Subagent contract, report, and handoff schemas.
3. Worker backend abstraction with stub / LLM / HTTP foundations.
4. Supervisor-worker as the default collaboration model.
5. Handoff and subgraph collaboration modes.
6. Parent-managed parallel-safe foundation with `TaskGroup`, `ParallelChildTask`, `ChildExecutionRecord`, `MergeBarrierOutcome`, and `GroupedReviewOutcome`.
7. Shared-review zone contract and approval-driven grouped write-back eligibility.
8. Thin orchestration bridge MVP: work item / group item boundary, landing dispatch, and delivery-signal overlay.
9. Local Work Trajectory as a visual projection of local work lines, dependencies, merge, compound nodes, anchors, and graph navigation.

Still missing:

1. A standalone scheduler lifecycle.
2. Durable scheduler state and event history.
3. Dependency readiness / wake-up loop.
4. Admission control across edit leases, sandbox availability, and resource limits.
5. Runtime adapter contract for Qoder / opencode / Codex / other providers.
6. A fake-run scheduler test harness independent from UI.
7. A first Qoder-backed bounded task execution spike.
8. Clear policy for when runtime subagents may be used inside a scheduled task.
9. End-to-end guide/worker use of the coordination exchange surfaces inside a
   scheduler-owned workflow.

No longer missing:

1. Coordination `ExchangeArtifact` schema and local durable store foundation.
2. Per-agent mailbox and compact exchange-history read models.
3. Reply and exact-version lifecycle transition helpers.
4. Action-candidate detection and disposition products.
5. Accepted-candidate consumers for scheduler admission, review intake,
   handoff delivery, explicit merge-gate resolution, and explicit task
   blocking.

Closure evidence:

- `review/agent-communication-product-closure-2026-06-22.md`

## Proposed Orchestration Slices

### Slice O1 — Runtime Adapter Contract

Goal: define the boundary between the project scheduler and external agent runtimes.

Deliverables:

1. `AgentRuntimeAdapter` contract.
2. `RuntimeCapabilities`.
3. `AgentSpec`.
4. `TaskSpec`.
5. `SessionHandle`.
6. `RunHandle`.
7. `RunEvent`.
8. `PermissionRequest`.
9. `ArtifactDelta`.
10. Fake runtime mapping for contract validation.
11. Qoder runtime mapping for later dogfood validation.

Current implementation:

`src/runtime/orchestration/runtime_adapter.py` now provides the first adapter contract, fake runtime, and provider-keyed `AgentRuntimeAdapterRegistry`. Qoder is represented only as a capability mapping through `qoder_runtime_capabilities()`, not as a real SDK dependency.
`src/runtime/orchestration/scheduler.py` now also includes `run_scheduled_task_with_registry()`, a narrow helper that resolves the task runtime from `task.agent.runtime_provider` through an instance-scoped registry before delegating to `run_ready_task()`.
`QoderAgentRuntimeAdapter` now exists as a mockable seam backed by a project-owned `QoderQueryClient` protocol and stable `QoderQueryRequest` object. It proves result normalization, permission request surfacing, and registry/scheduler execution without importing the real Qoder SDK.
The scheduler-side permission gate now turns runtime-surfaced permission requests into `review_required` task state and `task_review_required` history instead of treating the task as complete. `resolve_task_permission_review()` provides the first review resolution loop: approval completes the paused task and wakes direct dependents, while rejection blocks the task without waking dependents.

Non-goals:

1. No real Qoder execution yet.
2. No scheduler queue.
3. No UI binding.
4. No opencode adapter validation in this first slice.

### Slice O2 — Local Scheduler Skeleton

Goal: make orchestration state real before any external runtime is trusted.

Deliverables:

1. `ScheduledTask`.
2. `TaskDependency`.
3. `SchedulerState`.
4. `TaskRunRecord`.
5. `ContextScope`.
6. `EditScopeLease`.
7. `SandboxProfile`.
8. Local JSON or equivalent event-history persistence.
9. Fake worker execution tests.

Current implementation:

`src/runtime/orchestration/scheduler.py` now provides the first local skeleton for scheduler-owned task state, dependencies, context scope, edit lease, sandbox profile, admission decisions, readiness promotion, direct dependency wake-up, and one ready-task execution path through fake runtime. `src/runtime/orchestration/scheduler_store.py` adds a versioned JSON snapshot round-trip for `SchedulerState`.
`SchedulerEvent` plus `JsonlSchedulerEventLog` now provide the first append-only scheduler history. `mark_ready_tasks()` and `run_ready_task()` can optionally record readiness, waiting, running, completion, and failure events while preserving the existing no-log call path.
Runtime-surfaced permission requests now record `task_review_required`, keep the task in `review_required`, and avoid waking downstream dependencies that require completion. Permission approval / rejection is now explicit scheduler-owned state transition history through `task_permission_approved` / `task_permission_rejected`, and replay can recover both outcomes from the scheduler event log.
`replay_scheduler_events()` now provides baseline-based recovery from scheduler events. It updates existing baseline tasks and run records, including permission-review states, but does not create task contracts from event history. `recover_scheduler_state()` is the narrow file-based entrypoint that combines a scheduler snapshot path with a JSONL event log path and returns `SchedulerRecoveryResult` for callers that need explicit recovery evidence. `write_compacted_scheduler_snapshot()` adds the first non-destructive compaction primitive: it writes the recovered state to a caller-provided compacted snapshot path while leaving the source event log untouched.
`src/runtime/orchestration/preflight.py` now provides `OrchestrationPreflightBundle`,
`build_orchestration_preflight_bundle()`, `PreflightedTaskRunResult`, and
`run_preflighted_task()`. The builder is a non-executing assembly helper that
connects a ready `ScheduledTask` to `TaskSpec`, `SandboxAllocation`, and
`AgentScratchSpace`. `run_preflighted_task()` is the first controlled execution
entrypoint over that bundle: it verifies the bundle still matches the current
`SchedulerState`, resolves the runtime through `AgentRuntimeAdapterRegistry`,
and delegates state mutation to the scheduler-owned `run_ready_task()` path. It
does not introduce a daemon, bypass admission, or create scratch directories.
`PreflightDrainResult` and `drain_preflighted_ready_tasks()` now provide the
preflight-aware bounded drain path. It serially combines `mark_ready_tasks()`,
`build_orchestration_preflight_bundle()`, and `run_preflighted_task()` while
preserving the same bounded policy and failure semantics as scheduler
`drain_ready_tasks()`: failed runtime tasks are marked `blocked`, fail-fast is
the default, and `continue_on_failure=true` only continues independent ready
branches.
`src/runtime/orchestration/scheduler_submission.py` now provides the first
intake adapter from artifact-centered coordination products to scheduler-owned
state. `SchedulerTaskSubmission` can be encoded as an
`ExchangeArtifact(kind="request", intent="propose")` with a structured
`product_type="scheduler_task_submission"` payload, parsed back, and submitted
through `submit_scheduler_task()` into a `SchedulerState` as a `ScheduledTask`
plus optional `TaskDependency` edges.
`SchedulerTaskBatchSubmission` extends the same intake surface to a multi-task
artifact with `product_type="scheduler_task_batch_submission"`. It lets a guide
or planning agent submit a small task graph in one artifact, including
cross-task dependency edges, while still leaving readiness, execution, and
failure handling to the scheduler. These submission products are only
translation/admission inputs; they do not run tasks, bypass scheduler readiness,
or make ExchangeArtifact the scheduling authority.
`submit_scheduler_task_batch_with_persistence()` now adds the first persistence
smoke over this intake path: it submits the batch, appends `task_submitted`
audit events, writes the resulting `SchedulerState` snapshot, and leaves
recovery to `recover_scheduler_state()`. The snapshot remains the task-contract
authority; submission events are breadcrumbs for audit/projection, not a source
from which replay invents task contracts.
`submit_scheduler_task_with_persistence()` and
`admit_exchange_artifact_version_to_scheduler()` now add the exact-version
store admission path. The helper reads a stored `ExchangeArtifact` version from
`JsonArtifactVersionStore`, requires exactly one scheduler submission payload,
and writes scheduler snapshot/event-log state through the existing submission
adapters. The exchange store remains the exact coordination-product source, not
the scheduler authority; this path does not run providers, refresh scheduler
projection, expose a stored-artifact MCP write tool, or mutate Local Work
Trajectory.
`src/runtime/orchestration/scheduler_runner.py` adds
`run_persisted_scheduler_once()`, the first command-style persisted run entry:
recover from scheduler snapshot + event log, run a bounded preflight drain
through explicit sandbox/runtime registries, and write the resulting state back
to the snapshot. This is the current "make it run once" surface, not a daemon,
watcher, retry supervisor, or parallel worker launcher.
`tools/progress_graph/scheduler_projection.py` now provides the first pure view projection from `SchedulerState` to `LocalWorkTrajectory`. This projection maps `ContextScope.lane_id` to lanes, scheduler tasks to trajectory events, task dependencies to trajectory relations, and run/output artifact references to event metadata. It returns a view object only and intentionally does not write the workspace-local trajectory artifact.
`SchedulerRunPolicy` and `drain_ready_tasks()` now provide the first bounded queue-drain primitive: it performs an explicit readiness scan, runs ready tasks in deterministic order through the supplied runtime adapter, uses completion-triggered direct wake-up, and stops with a visible reason when the queue is empty, `max_runs` is reached, a runtime task fails, or admission leaves only blocked tasks. The default policy remains fail-fast. `continue_on_failure=true` keeps the failed task blocked while allowing independent ready tasks to continue, then reports `completed_with_failures` once the queue drains.

Still pending:

1. Event-log truncation / rotation policy after compacted snapshots are verified.
2. Daemon-style queue loop plus active retry, cancellation, and timeout execution beyond the bounded local drain primitives.
3. Richer edit lease conflict policy.
4. Real sandbox providers.
5. Runtime event-log projection beyond the snapshot-derived trajectory view.

Non-goals:

1. No parallel process execution.
2. No Qoder adapter.
3. No sandbox provider implementation.

### Slice O3 — Readiness And Admission Control

Goal: decide which tasks are ready and runnable.

Deliverables:

1. Dependency readiness evaluation.
2. Edit lease conflict detection.
3. Sandbox profile availability check.
4. Resource limit placeholder.
5. Clear blocked / waiting / ready reasons.

Non-goals:

1. No automatic retries.
2. No distributed scheduling.
3. No UI control surface.

### Slice O4 — Qoder Runtime Adapter Spike

Goal: prove that one bounded scheduled task can be executed through Qoder and normalized back into project objects.

Deliverables:

1. Qoder adapter behind `AgentRuntimeAdapter`.
2. One bounded task execution path.
3. Session creation and event capture.
4. Permission / hook mapping where available.
5. Output normalized into `SubagentReport` / `ArtifactDelta`.
6. Adapter-level tests using a mockable seam first, then a controlled local dogfood path.

Non-goals:

1. Qoder does not schedule tasks.
2. Qoder does not update authority docs directly.
3. Qoder subagents are not exposed as project-level lanes yet.

Current implementation:

`QoderQueryClient`, `QoderQueryRequest`, `QoderQueryResult`, and
`QoderAgentRuntimeAdapter` now define the mockable adapter seam. Mocked tests
validate a `qoder` task through `AgentRuntimeAdapterRegistry` and
`run_scheduled_task_with_registry()`. The request object is the intended input
contract for a later real SDK wrapper, so the wrapper does not depend directly
on scheduler internals. `RuntimeRunResult.permission_requests` and
`QoderQueryResult.permission_requests` now surface runtime permission requests
without approving them inside the adapter. Scheduler handling now records
`task_review_required` and avoids waking downstream dependencies until review
resolves the permission request. The real Qoder SDK wrapper and controlled
dogfood execution are still pending. Requirements for that wrapper are captured
in `design_docs/qoder-runtime-adapter-requirements.md`.

### Slice O5 — Scheduler Projection To Local Work Trajectory

Goal: make scheduler events visible without making Local Work Trajectory the authority.

Current implementation:

`tools/progress_graph/scheduler_projection.py` implements the first snapshot-derived projection through `build_scheduler_work_trajectory()`. It is intentionally read-only and does not expose any trajectory-driven scheduler mutation.

Deliverables:

1. Scheduler task start / ready / running / blocked / merge events projected into Local Work Trajectory.
2. Lane mapping policy from `ContextScope`.
3. Merge / dependency relation projection.
4. Audit references connecting scheduler run records and trajectory events.

Current coverage:

1. Lane mapping from `ContextScope.lane_id`.
2. Task lifecycle state mapping into trajectory event status.
3. Dependency relation projection for `depends_on` / `waits_for`.
4. Run records and output artifact references surfaced as event metadata.
5. Direct downstream dependency wake-up after a completed task.
6. Persisted one-shot runner results can be observed by rebuilding the
   scheduler-derived trajectory from the post-run `SchedulerState`; the
   projection shows completed tasks, dependency relations, run IDs, session IDs,
   and output artifact IDs / versions without mutating the workspace-local
   trajectory artifact.
7. Optional scheduler event-log clues can be attached to projected task events
   as metadata (`scheduler_event_ids`, kinds, timestamps, and sequences). These
   clues support historical traceability only; they do not create tasks or
   replace snapshot/replay authority.
8. Multi-dependency fan-in targets are now visible as projection-only merge
   events. The projector preserves original dependency edges, adds fan-in source
   edges into the synthetic merge event, and adds one `merges_into` relation
   from that merge event to the target task. The merge event is a visual summary
   of scheduler dependencies, not a new scheduler task contract.
9. Scheduler-owned merge gate skeleton is now available for join points that
   require real scheduler work. `SchedulerMergeGate` lives in
   `SchedulerState.merge_gates`, round-trips through scheduler snapshots, and
   projects as a real merge event with `scheduler-owned-merge-gate` metadata.
   Target task admission now waits for associated merge gates to reach
   `complete`. `resolve_scheduler_merge_gate()` provides the first external
   decision loop: approval completes the gate and re-evaluates the target task;
   rejection blocks the gate and keeps the target waiting.
10. Merge-gate-specific history is now separated from task scheduler events.
    `SchedulerMergeGateEvent` and `JsonlSchedulerMergeGateEventLog` can record
    merge gate completed / blocked decisions. This log is history-only and is
    not replayed into scheduler contracts.
11. Scheduler-owned merge gate projection can now receive merge-gate history
    events and expose them as metadata on the projected merge event. The
    metadata includes event IDs, kinds, timestamps, sequences, decision artifact
    references, and a compact `scheduler_merge_gate_event_log` field intended
    for historical communication management. This remains projection-only:
    orphan history events are ignored and event history does not create or
    replay scheduler contracts.
12. `build_scheduler_work_trajectory_from_history()` is now the convenience
    entry for persisted JSONL history. It reads optional scheduler task event
    logs and merge-gate event logs, injects them into the scheduler-derived
    trajectory projection, and records source paths / event counts on trajectory
    metadata. It deliberately does not recover scheduler state or compact event
    logs.
13. `write_scheduler_work_trajectory_artifact()` now provides the stable
    projection artifact writer. Its default path is
    `.codex/progress-graph/scheduler-work-trajectory.json`, deliberately
    separate from `.codex/progress-graph/local-work-trajectory.json` so
    scheduler visualization refreshes do not overwrite agent-owned Local Work
    Trajectory lifecycle state.
14. MCP now exposes `schedulerProjection` as the first host/agent callable
    refresh surface for this scheduler-derived artifact. It takes a scheduler
    snapshot path plus optional scheduler and merge-gate JSONL history paths,
    writes the projection artifact, and returns the path, counts, and metadata.
    It is intentionally separate from `localTrajectory`.
15. `read_trajectory_artifacts_bundle()` defines the preview consumption bundle
    for trajectory artifacts. It reads the agent-owned local trajectory and the
    scheduler-derived trajectory independently, preserving per-artifact role,
    path, exists flag, parse error, payload, and compact summary. This gives UI
    adapters a stable contract before visual binding.
16. VS Code Progress Graph Preview now consumes
    `.codex/progress-graph/scheduler-work-trajectory.json` as a second,
    read-only trajectory section labeled `Scheduler Trajectory Projection`.
    It keeps the scheduler-derived payload separate from
    `.codex/progress-graph/local-work-trajectory.json`, reuses the existing
    trajectory renderer through a second mount point, and does not expose
    scheduler mutation controls.

Still pending:

1. Rich event-replay visualization from scheduler JSONL event logs.
2. Scheduler-native merge gate execution semantics: gate readiness,
   artifact merge output, runtime execution, and merge-gate event replay /
   compaction policy remain future slices.
3. Richer UI affordances for scheduler-derived trajectory history, such as
   compact event-log timelines or scheduler-run detail overlays.

Non-goals:

1. No UI redesign.
2. No user-driven scheduler mutation from trajectory UI.

### Slice O6 — Sandbox Provider Contract

Goal: separate execution isolation from context isolation before high-risk agents are enabled.

Deliverables:

1. `SandboxProvider` contract.
2. `shared-process` metadata implementation.
3. `git-worktree` / `docker` / `remote-vm` placeholder capability shape.
4. Secret, network, and mount policy fields.

Current implementation:

`src/runtime/orchestration/sandbox.py` now provides the first sandbox provider
contract surface:

```text
SandboxCapability
SandboxRequest
SandboxAllocation
SandboxProvider
SandboxProviderRegistry
SharedProcessSandboxProvider
sandbox_capability_placeholder()
```

`SharedProcessSandboxProvider` is deliberately metadata-only. It can allocate a
`shared-process` profile and echo workspace root, scratch path, visible mounts,
network policy, and secret policy for scheduler / audit surfaces, but it does
not claim process or filesystem isolation. `sandbox_capability_placeholder()`
records the capability shape for `none`, `git-worktree`, `docker`, and
`remote-vm` without registering them as available providers. Real sandbox
execution, cleanup, and process supervision remain separate implementation
slices.

Non-goals:

1. No remote sandbox provider yet.
2. No Docker implementation unless a later gate explicitly selects it.
3. No process launch, filesystem mount, network enforcement, or cleanup action
   in the shared-process metadata provider.

### Slice O7 — Agent Home And Scratch Governance

Goal: define private persistent and temporary storage as orchestration resources.

Deliverables:

1. `AgentHomeRegistration`.
2. `AgentScratchSpace`.
3. Home registration request / decision flow.
4. Scratch manifest, archival, cleanup, and promotion review flow.
5. Secret / sensitive-content policy hooks.
6. Relationship to `ContextBundle`, `EditScopeLease`, and Local Work Trajectory projection.

Current implementation:

`src/runtime/orchestration/agent_storage.py` now provides the first governance
product objects and exchange-artifact mapping helpers:

```text
AgentHomeRegistration
AgentScratchSpace
ScratchManifestEntry
ScratchManifest
CleanupReceipt
agent_home_registration_to_artifact()
scratch_manifest_to_artifact()
cleanup_receipt_to_artifact()
```

Home registration requests / decisions map to `ExchangeArtifact(kind="retention",
intent="request_registration")` with `structured`, `storage_manifest`, and
`log` parts. Scratch manifests map to retention review artifacts with redaction
flags derived from manifest entries. Cleanup receipts map to
`ExchangeArtifact(kind="cleanup")` and satisfy the existing `cleanup` rule that
requires both `storage_manifest` and `log`. This makes agent-private storage
visible to the artifact-centered coordination layer without making Local Work
Trajectory or prose transcript the storage authority.

`src/runtime/orchestration/exchange_store.py` now also provides
`JsonArtifactVersionStore` and exchange artifact JSON serialization helpers.
This gives agent storage products and scheduler submission products a durable,
version-addressable coordination store while preserving the existing rule that
scheduler-relevant state must be machine-readable and validated before
persistence.

The store now also has a read-only inspection/admission-prep surface through
`ExchangeArtifactInspectionBundle` and `dbc://exchange-artifacts/bundle`. The
default inspected path is `.codex/orchestration/exchange-artifacts.json`. This
is a coordination product store convention, not a persistent agent-home
implementation and not scheduler state authority.
Stored scheduler submission artifacts can be admitted by exact version through
`admit_exchange_artifact_version_to_scheduler()`, which writes scheduler
snapshot/event-log state while preserving the exchange store as source material
only. It does not create agent-home directories, run providers, refresh
projection, or mutate Local Work Trajectory.

Non-goals:

1. No persistent home implementation yet.
2. No default agent-home storage path commitment until workspace-registration authority is fixed.
3. No automatic promotion from scratch to home.
4. No directory creation, deletion, archive, or file persistence in this slice.

### Slice O8 — Coordination Exchange Artifact Contract

Goal: define the intermediate products through which agents communicate.

Deliverables:

1. `ExchangeArtifact` shell.
2. Core payload part schemas for text, structured data, references, artifact deltas, contracts, evidence, relations, storage manifests, and logs.
3. Scheduler-relevant rule: state-changing content must not exist only in prose.
4. Mapping to RawTranscript, CoordinationEventLog, and ArtifactVersionStore.

Current implementation:

`src/runtime/orchestration/exchange.py` defines the first `ExchangeArtifact`
shell, payload parts, relation / contract / log products, and validation rule
that scheduler-relevant content must not exist only in text.
`src/runtime/orchestration/exchange_store.py` provides
`InMemoryArtifactVersionStore`, `JsonArtifactVersionStore`,
`JsonlCoordinationEventLog`, serialization helpers for current payload part
types, and a read-only `ExchangeArtifactInspectionBundle` over the local durable
store. `dbc://exchange-artifacts/bundle` exposes this inspection bundle through
the existing resource surface so operators and agents can see exact stored
versions and scheduler submission candidates before a later admission action.
`admit_exchange_artifact_version_to_scheduler()` is the first runtime helper for
that later admission action: it consumes one exact stored scheduler submission
artifact and persists the resulting scheduler task contracts. The JSON store is
durable and local, but it remains a coordination artifact store rather than
scheduler state authority.

### 2026-06-22 Agent Communication Product Closure

The first agent communication product layer is now implemented on top of the
`ExchangeArtifact` store:

1. `agent_communication.py` builds per-agent mailbox views.
2. `agent_exchange_history.py` builds compact causality/log history summaries.
3. `agent_exchange_actions.py` provides exact-version reply and lifecycle
   transition helpers.
4. `agent_exchange_action_candidates.py` identifies scheduler submission,
   review, handoff, blocker, and merge action candidates.
5. `agent_exchange_action_disposition.py` records candidate dispositions as
   machine-readable coordination products.
6. `agent_exchange_action_consumers.py` consumes accepted dispositions through
   explicit owner surfaces.

The surfaces are exposed through CLI, MCP tools, and where appropriate
read-only resources. Acceptance evidence is summarized in
`review/agent-communication-product-closure-2026-06-22.md`.

Non-goals:

1. No raw transcript persistence implementation yet.
2. No UI rendering implementation yet.
3. No full product-type enum freeze beyond the first contract.
4. No real multi-agent scheduling workflow or runtime-provider execution
   policy over these communication products yet.

## Recommended Next Step

The next planning-gate should be narrow:

> Agent Runtime Adapter Contract And Scheduler Skeleton

Recommended scope:

1. Complete Slice O1.
2. Start Slice O2 only far enough to prove fake-run state transitions.
3. Keep Qoder as a named target mapping, but do not run real Qoder until O4.

This keeps the project contract-first while still steering directly toward the later Qoder-backed test path.

## Acceptance Criteria For The Next Gate

The next gate should not close until:

1. The adapter boundary can express Qoder and a fake runtime without changing scheduler objects.
2. The scheduler can create a small task graph and persist its state.
3. At least one fake task can move through proposed -> ready -> running -> review_required or complete.
4. Context scope, edit lease, and sandbox profile are present as first-class objects.
5. Local Work Trajectory remains explicitly documented as projection, not authority.
