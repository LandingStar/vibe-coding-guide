# Project Master Checklist

## Purpose

This file is the short recovery/status entry for the current repository. It is
intended to stay small enough for agents to read after context compression.

The full historical checklist was archived on 2026-06-22:

- `design_docs/history/Project Master Checklist Archive 2026-06-22.md`

Use that archive only when historical traceability is needed. Do not re-expand
this file into a full project timeline.

## Authority And Conflict Order

If repository documents disagree, use this order:

1. The user's latest explicit decision
2. Current workspace reality
3. Formal docs and protocol documents under `docs/` and `design_docs/tooling/`
4. Active planning gate / active direction analysis
5. Current checkpoint and handoff
6. This checklist as a compact status index
7. Archived historical records

## Current Snapshot

- Snapshot Date: `2026-06-27`
- Project Name: `doc-based-coding-platform`
- Version: `0.9.8` (preview)
- Current Phase: `Post-v1.0 - Agent orchestration / Codex stable worker runtime`
- Current Focus: `C7 Codex runtime status readback completed`
- Latest Completed Planning Gate:
  `design_docs/stages/planning-gate/2026-06-27-codex-runtime-status-readback.md`
- Latest Completed Slice: `Codex Runtime Status Readback`
- Latest Completion Evidence:
  `design_docs/stages/planning-gate/2026-06-27-codex-runtime-status-readback.md`,
  `design_docs/codex-cli-stable-worker-runtime-continuous-use-target.md`,
  `design_docs/stages/planning-gate/2026-06-27-codex-multilane-continuous-progress-fixture.md`,
  `design_docs/stages/planning-gate/2026-06-27-codex-delivery-sandbox-patch-review-closure.md`,
  `design_docs/stages/planning-gate/2026-06-27-codex-interruption-recovery-and-retry-policy.md`,
  `design_docs/stages/planning-gate/2026-06-27-codex-permission-review-outcome-consumer.md`,
  `design_docs/stages/planning-gate/2026-06-26-bounded-codex-supervisor-loop-binding.md`,
  `design_docs/stages/planning-gate/2026-06-26-credentialed-codex-cli-e2e-smoke.md`,
  `design_docs/stages/planning-gate/2026-06-26-codex-result-consumer-contract.md`,
  `design_docs/stages/planning-gate/2026-06-26-codex-delivery-supervisor-loop.md`,
  `design_docs/stages/planning-gate/2026-06-25-host-owned-worker-delivery-acknowledgement.md`,
  `design_docs/stages/planning-gate/2026-06-25-recoverable-leader-worker-dispatcher-tick.md`,
  `design_docs/stages/planning-gate/2026-06-25-runtime-invocation-recovery-and-audit-trail.md`
  and `design_docs/stages/planning-gate/2026-06-25-leader-worker-activation-loop-contract.md`
- Last Checkpoint: `.codex/checkpoints/latest.md`
  (may point to parked work; do not treat it as newer than this checklist)
- Current Target Definition:
  `design_docs/codex-cli-stable-worker-runtime-continuous-use-target.md`

## Current Recovery Read Order

Start with these files, in order:

1. `design_docs/Project Master Checklist.md`
1. `design_docs/stages/planning-gate/2026-06-27-codex-runtime-status-readback.md`
1. `design_docs/codex-cli-stable-worker-runtime-continuous-use-target.md`
1. `design_docs/stages/planning-gate/2026-06-27-codex-multilane-continuous-progress-fixture.md`
1. `design_docs/stages/planning-gate/2026-06-27-codex-delivery-sandbox-patch-review-closure.md`
1. `design_docs/stages/planning-gate/2026-06-27-codex-interruption-recovery-and-retry-policy.md`
1. `design_docs/stages/planning-gate/2026-06-27-codex-permission-review-outcome-consumer.md`
1. `design_docs/stages/planning-gate/2026-06-26-bounded-codex-supervisor-loop-binding.md`
1. `design_docs/stages/planning-gate/2026-06-26-credentialed-codex-cli-e2e-smoke.md`
1. `design_docs/stages/planning-gate/2026-06-26-codex-result-consumer-contract.md`
1. `design_docs/stages/planning-gate/2026-06-26-codex-delivery-supervisor-loop.md`
1. `design_docs/stages/planning-gate/2026-06-25-host-owned-worker-delivery-acknowledgement.md`
1. `design_docs/stages/planning-gate/2026-06-25-recoverable-leader-worker-dispatcher-tick.md`
1. `design_docs/stages/planning-gate/2026-06-25-runtime-invocation-recovery-and-audit-trail.md`
1. `design_docs/stages/planning-gate/2026-06-25-leader-worker-activation-loop-contract.md`
1. `design_docs/stages/planning-gate/2026-06-25-host-ux-worker-patch-review-binding.md`
1. `design_docs/worker-patch-composition-preflight-followup-direction-analysis.md`
1. `design_docs/stages/planning-gate/2026-06-24-worker-patch-composition-preflight.md`
1. `design_docs/stages/planning-gate/2026-06-24-worker-patch-apply-reject-policy.md`
1. `design_docs/stages/planning-gate/2026-06-24-worker-patch-review-integration.md`
1. `design_docs/stages/planning-gate/2026-06-24-codex-worker-sandbox-writeback-policy.md`
1. `design_docs/stages/planning-gate/2026-06-24-codex-cli-worker-runtime-provider.md`
1. `design_docs/stages/planning-gate/2026-06-24-guide-worker-planned-execution-closure.md`
1. `design_docs/stages/planning-gate/2026-06-24-autonomous-guide-instruction-planner.md`
1. `design_docs/stages/planning-gate/2026-06-24-host-owned-guide-worker-provider-execution-wrapper.md`
1. `design_docs/stages/planning-gate/2026-06-24-guide-worker-provider-runtime-mapping.md`
1. `design_docs/stages/planning-gate/2026-06-24-guide-worker-lane-wave-executor-contract.md`
1. `design_docs/stages/planning-gate/2026-06-24-guide-worker-local-orchestration-mcp-surface.md`
1. `design_docs/stages/planning-gate/2026-06-23-guide-worker-local-trajectory-orchestration-mvp.md`
1. `review/agent-communication-product-closure-2026-06-22.md`
1. `design_docs/Global Phase Map and Current Position.md`
1. Directly relevant `docs/` and `design_docs/tooling/` protocol documents

Historical recovery beyond this list should use:

- `design_docs/history/Project Master Checklist Archive 2026-06-22.md`

## Active Work

### Codex Runtime Status Readback

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-27-codex-runtime-status-readback.md`

Current implementation surface:

- Runtime helper/module:
  `src/runtime/orchestration/codex_runtime_status.py`
- CLI:
  `doc-based-coding scheduler inspect-codex-runtime-status`

Behavior:

- Provides compact read-only status for scheduler state, delivery records,
  runtime invocation audit, output/review/worker-patch artifact refs, and safe
  `next_action` clues.
- Does not run Codex, mutate scheduler/delivery/artifact/runtime logs, mutate
  Local Work Trajectory, or expose raw transcripts.

Validation:

- `py_compile` passed for touched runtime/CLI/tests.
- Focused C7 runtime and CLI tests passed.
- Adjacent Codex delivery supervisor runtime and CLI tests passed.
- Doc-loop validator passed.

### Codex Multi-Lane Continuous Progress Fixture

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-27-codex-multilane-continuous-progress-fixture.md`

Current implementation surface:

- Runtime helper/module:
  `src/runtime/orchestration/codex_delivery_smoke.py`
- CLI:
  `doc-based-coding scheduler codex-delivery-e2e-smoke --fixture multilane`,
  `doc-based-coding scheduler codex-delivery-supervisor-loop --fixture multilane`

Behavior:

- Adds an opt-in multi-lane fixture with two independent lane-distinct Codex
  workers and one dependent Codex follow-up task.
- Lets the existing bounded Codex supervisor loop complete multiple lane
  workers over bounded ticks while preserving serial execution semantics.
- Exposes target task state and task state counts for the fixture readback.

Validation:

- `py_compile` passed for touched runtime/CLI/tests.
- Focused bounded Codex loop tests passed: `4 passed, 333 deselected`.
- Focused Codex loop CLI tests passed: `2 passed, 100 deselected`.
- Adjacent Codex delivery/runtime tests passed: `14 passed, 323 deselected`.
- Doc-loop validator passed.

### Codex Delivery Sandbox Patch Review Closure

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-27-codex-delivery-sandbox-patch-review-closure.md`

Current implementation surface:

- Runtime helper/module:
  `src/runtime/orchestration/leader_worker_codex_delivery.py`
- Bounded loop binding:
  `src/runtime/orchestration/codex_delivery_smoke.py`
- CLI:
  `doc-based-coding scheduler codex-delivery-supervisor-once`,
  `doc-based-coding scheduler codex-delivery-supervisor-loop`

Behavior:

- Allows host opt-in sandbox preflight for Codex delivery, including
  git-worktree allocation when an explicit sandbox root is provided.
- Passes preflight runtime workspace metadata to Codex CLI.
- Publishes git-worktree edits as review-only
  `worker_patch_review_proposal` artifacts before consuming successful
  results.
- Keeps result completion, patch review, patch apply, and sandbox cleanup as
  separate operator decisions.

Validation:

- `py_compile` passed for touched runtime/CLI/tests.
- Focused Codex delivery supervisor runtime tests passed:
  `13 passed, 323 deselected`.
- Focused Codex delivery supervisor CLI tests passed:
  `5 passed, 97 deselected`.
- Adjacent Codex result/permission/worker patch review runtime tests passed:
  `23 passed, 313 deselected`.
- Adjacent Codex delivery / worker patch CLI tests passed:
  `9 passed, 93 deselected`.
- Doc-loop validator passed.

### Codex Interruption Recovery And Retry Policy

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-27-codex-interruption-recovery-and-retry-policy.md`

Current implementation surface:

- Runtime helper/module:
  `src/runtime/orchestration/leader_worker_codex_delivery.py`
- Bounded loop binding:
  `src/runtime/orchestration/codex_delivery_smoke.py`
- CLI:
  `doc-based-coding scheduler codex-delivery-supervisor-once`,
  `doc-based-coding scheduler codex-delivery-supervisor-loop`

Behavior:

- Allows host-authorized retry of eligible transient failed Codex delivery
  records after restart.
- Keeps non-retryable failures failed.
- Skips already completed scheduler tasks rather than duplicating completion.
- Preserves compact runtime invocation audit and no raw transcript persistence.
- Does not resume a live Codex process mid-turn and does not mutate
  agent-owned Local Work Trajectory.

Validation:

- `py_compile` passed.
- Focused C4 runtime retry tests passed:
  `2 passed, 331 deselected` and `1 passed, 333 deselected`.
- Focused C4 CLI help tests passed: `2 passed, 99 deselected`.
- Adjacent Codex delivery/result-consumer/permission/runtime invocation tests
  passed: `25 passed, 309 deselected`.
- Adjacent Codex delivery CLI tests passed: `9 passed, 92 deselected`.

### Codex Permission Review Outcome Consumer

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-27-codex-permission-review-outcome-consumer.md`

Current implementation surface:

- Runtime helper/module:
  `src/runtime/orchestration/codex_permission_review_consumer.py`
- Helper: `consume_codex_permission_review_result()`
- Supervisor integration:
  `run_codex_delivery_supervisor_once()` now routes
  `RuntimeRunResult.permission_requests` before successful result consumption.
- Delivery state: `review_required` / `delivery_review_required`

Behavior:

- Stores permission-review output artifacts as durable review evidence.
- Appends scheduler `task_review_required` rather than `task_completed`.
- Marks delivery `review_required`, not `acknowledged` or provider `failed`.
- Keeps downstream dependencies waiting until a scheduler-owned permission
  approval event resolves review.
- Preserves no raw transcript persistence and no runtime-owned Local Work
  Trajectory mutation.

Validation:

- `py_compile` passed.
- Focused Codex permission/result/delivery runtime tests passed:
  `11 passed, 320 deselected`.
- Focused Codex delivery CLI tests passed: `4 passed, 97 deselected`.
- Adjacent Codex delivery/result-consumer/runtime invocation tests passed:
  `20 passed, 311 deselected`.
- Adjacent Codex delivery CLI tests passed: `9 passed, 92 deselected`.

### Bounded Codex Supervisor Loop Binding

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-26-bounded-codex-supervisor-loop-binding.md`

Current implementation surface:

- Runtime helper/module: `src/runtime/orchestration/codex_delivery_smoke.py`
- Helper: `run_bounded_codex_delivery_supervisor_loop()`
- CLI: `doc-based-coding scheduler codex-delivery-supervisor-loop`

Behavior:

- Runs a bounded host/operator loop that recovers scheduler state, marks
  admissible tasks ready, persists dispatcher decisions, syncs delivery records,
  invokes Codex with result consumption, and recovers again.
- Exposes explicit bounds for max ticks, max deliveries, and max runtime
  failures.
- Returns compact stop/readback evidence including stop reason, task state
  counts, target states, delivery counts, runtime invocation count, and
  authority split.
- Does not implement daemonization, interruption resume, permission/review
  outcome consumption, MCP live-provider execution, source patch apply, or
  runtime-owned Local Work Trajectory mutation.

Validation:

- `py_compile` passed.
- Focused C1/C2 runtime tests passed: `4 passed, 326 deselected`.
- Focused C1/C2 CLI tests passed: `4 passed, 97 deselected`.
- Adjacent Codex delivery/result-consumer runtime tests passed:
  `19 passed, 311 deselected`.
- Adjacent Codex delivery CLI tests passed: `9 passed, 92 deselected`.

### Credentialed Codex CLI E2E Smoke

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-26-credentialed-codex-cli-e2e-smoke.md`

Current implementation surface:

- Runtime helper/module: `src/runtime/orchestration/codex_delivery_smoke.py`
- Helper: `run_codex_delivery_e2e_smoke()`
- CLI: `doc-based-coding scheduler codex-delivery-e2e-smoke`

Behavior:

- Optionally initializes a minimal scheduler-owned C1 fixture with one ready
  Codex task and one waiting non-Codex control task.
- Fails closed on negative Codex CLI readiness before dispatcher/delivery/runtime
  mutation.
- Chains dispatcher tick, delivery sync, Codex delivery with result consumption,
  and scheduler recovery for one narrow task.
- Produces compact readback for runtime audit, delivery acknowledgement, output
  artifact ref, and recovered target task state.

Validation:

- `py_compile` passed.
- Focused C1 runtime tests passed: `2 passed, 326 deselected`.
- Focused C1 CLI tests passed: `2 passed, 97 deselected`.
- Adjacent Codex delivery/result-consumer runtime tests passed:
  `17 passed, 311 deselected`.
- Adjacent Codex delivery CLI tests passed: `7 passed, 92 deselected`.

### Codex Result Consumer Contract

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-26-codex-result-consumer-contract.md`

Current implementation surface:

- Runtime helper/module: `src/runtime/orchestration/codex_result_consumer.py`
- Consumer helper:
  `consume_successful_codex_result()`
- Supervisor integration:
  `CodexDeliverySupervisorRequest.consume_success_results`,
  `artifact_store_path`, and `replace_existing_result_artifact`
- CLI:
  `doc-based-coding scheduler codex-delivery-supervisor-once
  --consume-success-results`

Behavior:

- Stores successful Codex `RuntimeRunResult.output_artifact` into the durable
  ExchangeArtifact store.
- Appends `task_completed` to the scheduler event log so existing recovery
  advances the task to `complete`.
- Acknowledges delivery only after result artifact/event persistence succeeds.
- Marks delivery `failed` with `failure_kind=result_consumer_failed` when the
  successful provider result cannot be consumed durably.
- Does not mutate scheduler snapshots, compact event logs, expose MCP live
  provider execution, persist raw transcripts, or mutate runtime-owned Local
  Work Trajectory.

Validation:

- `py_compile` passed.
- Focused Codex result/delivery runtime tests passed:
  `6 passed, 320 deselected`.
- Focused CLI/Codex delivery tests passed: `3 passed, 94 deselected`.

### Codex Delivery Supervisor Loop

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-26-codex-delivery-supervisor-loop.md`

Current implementation surface:

- Runtime helper/module: `src/runtime/orchestration/leader_worker_codex_delivery.py`
- Host-owned pass:
  `run_codex_delivery_supervisor_once()`
- Models:
  `CodexDeliverySupervisorRequest`,
  `CodexDeliverySupervisorRecord`,
  `CodexDeliverySupervisorResult`
- CLI:
  `doc-based-coding scheduler codex-delivery-supervisor-once`

Behavior:

- Consumes pending leader-worker delivery records only when they correspond to
  ready/admissible Codex scheduler tasks.
- Executes Codex through host-authorized adapter wiring and explicit
  process-spawn grant.
- Writes delivery acknowledgement plus compact runtime invocation audit.
- Does not mutate scheduler state/event log, ExchangeArtifact store, MCP live
  provider surfaces, raw transcripts, or runtime-owned Local Work Trajectory.

Validation:

- `py_compile` passed.
- Focused Codex delivery runtime tests passed: `3 passed, 320 deselected`.
- Focused CLI/delivery/runtime tests passed: `4 passed, 92 deselected`.
- Focused adjacent runtime regression passed: `12 passed, 311 deselected`.
- Doc-loop validator passed.
- `git diff --check` passed with Windows line-ending warnings only.

### Host-Owned Worker Delivery Acknowledgement

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-25-host-owned-worker-delivery-acknowledgement.md`

Current implementation surface:

- Runtime helper/module: `src/runtime/orchestration/leader_worker_delivery.py`
- Durable delivery state: `LeaderWorkerDeliveryState`
- JSONL delivery log: `JsonlLeaderWorkerDeliveryEventLog`
- Sync/ack/readback helpers:
  `sync_leader_worker_delivery_from_dispatch_log()`,
  `acknowledge_leader_worker_delivery()`,
  `inspect_leader_worker_delivery_state()`
- CLI:
  `doc-based-coding scheduler leader-worker-delivery-sync`,
  `doc-based-coding scheduler leader-worker-delivery-ack`,
  `doc-based-coding scheduler inspect-leader-worker-delivery`

Validation:

- `py_compile` passed.
- Focused delivery tests in `tests/test_runtime_orchestration.py` passed:
  `2 passed, 318 deselected`.
- Focused leader-worker/runtime regression passed:
  `12 passed, 308 deselected`.
- Focused CLI regression passed:
  `5 passed, 90 deselected`.

### Recoverable Leader Worker Dispatcher Tick

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-25-recoverable-leader-worker-dispatcher-tick.md`

Current implementation surface:

- Runtime helper/module: `src/runtime/orchestration/leader_worker_dispatcher.py`
- Durable dispatcher state: `LeaderWorkerDispatcherState`
- JSONL dispatch log: `JsonlLeaderWorkerDispatcherEventLog`
- Tick/loop helpers:
  `run_leader_worker_dispatcher_tick()`,
  `run_leader_worker_dispatcher_loop()`
- CLI:
  `doc-based-coding scheduler leader-worker-dispatcher-tick`,
  `doc-based-coding scheduler leader-worker-dispatcher-loop`

Validation:

- `py_compile` passed.
- Focused dispatcher tests in `tests/test_runtime_orchestration.py` passed:
  `3 passed, 315 deselected`.
- Focused activation/CLI regression in tracked suites passed:
  `15 passed, 397 deselected`.

### Runtime Invocation Recovery And Audit Trail

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-25-runtime-invocation-recovery-and-audit-trail.md`

Current implementation surface:

- Runtime helper/module: `src/runtime/orchestration/runtime_invocation_audit.py`
- JSONL store: `JsonlRuntimeInvocationLog`
- Retry/audit runner: `run_with_runtime_invocation_audit()`
- CLI readback: `doc-based-coding scheduler inspect-runtime-invocations`
- Host-owned guide-worker wrapper:
  `run_host_owned_guide_worker_provider_execution()` now audits and retries
  Qoder/Codex provider client invocations by default.

Validation:

- `py_compile` passed.
- Focused runtime/CLI tests in tracked suites passed:
  `15 passed, 397 deselected`.
- Focused wrapper/CLI/runtime integration tests passed:
  `3 passed, 76 deselected`; `5 passed, 87 deselected`; `8 passed`.

### Leader Worker Activation Loop Contract

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-25-leader-worker-activation-loop-contract.md`

Current implementation surface:

- Runtime helper/module: `src/runtime/orchestration/leader_worker_activation.py`
- Policy helper: `evaluate_leader_worker_policy()`
- Activation pass: `run_leader_worker_activation_pass()`
- CLI readback: `doc-based-coding scheduler inspect-leader-worker-activation`

Validation:

- `py_compile` passed.
- Focused runtime/CLI tests in tracked suites passed:
  `15 passed, 397 deselected`.

### Checklist Recovery-Surface Optimization

Status: `completed`

Goal:

- Keep this file as a compact recovery/status entry instead of a full history
  log.
- Make the latest user pivot, prepared guide-worker gate, and completed agent
  communication closure visible without requiring agents to scan archived
  history.
- Keep stale checkpoint/handoff data discoverable but not stronger than the
  latest user decision and current workspace reality.

### Guide Worker Exchange Workflow Dogfood

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-23-guide-worker-exchange-workflow-dogfood.md`

Goal:

- Prove guide/worker use of the completed `ExchangeArtifact` communication
  surfaces in one deterministic fake-runtime-safe workflow.

Current implementation surface:

- Runtime helper: `run_guide_worker_exchange_dogfood()`
- CLI: `doc-based-coding scheduler guide-worker-exchange-dogfood`
- First candidate type: `scheduler_submission_candidate`

Validation:

- Runtime helper focused test passed.
- CLI focused test passed.
- Agent communication runtime regression passed.
- Focused adjacent CLI regression passed.
- Scheduler MCP prompt tests passed.
- Doc-loop validator passed.
- `git diff --check` passed with Windows line-ending warnings only.
- `analyze_changes` returned no impact nodes and no coupling alerts.

### Guide Worker Local Trajectory Orchestration MVP

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-23-guide-worker-local-trajectory-orchestration-mvp.md`

Goal:

- Implement the first scheduler-owned guide/worker workflow on one Local Work
  Trajectory slice: guide creates concrete worker instructions, scheduler
  admits worker tasks, and a finite cross-lane wave can run one ready worker
  task per lane.

Current implementation surface:

- Runtime helper: `run_guide_worker_local_trajectory_orchestration()`
- CLI: `doc-based-coding scheduler guide-worker-local-orchestration`
- Parallelism contract: scheduling wave only; fake runtime still executes
  sequentially inside the wave.

Validation:

- `py_compile` for helper/exports/CLI/tests passed.
- Focused runtime/CLI tests passed: `3 passed, 359 deselected`.

### Guide Worker Local Orchestration MCP Surface

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-24-guide-worker-local-orchestration-mcp-surface.md`

Goal:

- Expose the guide-worker local trajectory orchestration helper through Codex
  MCP with structured `workerInstructions`, while keeping runtime execution
  fake-only and preserving the distinction between scheduling waves and true
  process parallelism.

Current implementation surface:

- Runtime parser: `guide_worker_instructions_from_sequence()`
- MCP tool: `schedulerGuideWorkerLocalOrchestration`

Validation:

- `py_compile` for runtime/MCP/tests passed.
- Focused MCP route tests passed: `4 passed, 22 deselected`.

### Guide Worker Lane Wave Executor Contract

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-24-guide-worker-lane-wave-executor-contract.md`

Goal:

- Make guide-worker scheduling waves executable through a bounded, lane-distinct
  wave executor that can invoke runtime adapters as one wave and merge results
  back into scheduler state deterministically.

Current implementation surface:

- Runtime executor: `execute_guide_worker_parallel_wave()`
- Result model: `GuideWorkerWaveExecutionResult`
- MCP option: `waveExecutionMode`

Validation:

- `py_compile` for runtime/MCP/tests passed.
- Focused runtime/MCP/CLI tests passed: `9 passed, 381 deselected`.

### Guide Worker Provider Runtime Mapping

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-24-guide-worker-provider-runtime-mapping.md`

Goal:

- Let guide-worker instructions map worker tasks to a requested runtime
  provider, while keeping live provider execution behind host-authorized
  injected registries and preserving MCP fake-only safeguards.

Current implementation surface:

- Instruction field: `worker_runtime_provider`
- JSON/MCP alias: `workerRuntimeProvider`
- Host-injected mock Qoder execution test over the existing wave executor

Validation:

- `py_compile` for runtime/MCP/tests passed.
- Focused runtime/MCP/CLI tests passed: `11 passed, 381 deselected`.

### Host-Owned Guide Worker Provider Execution Wrapper

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-24-host-owned-guide-worker-provider-execution-wrapper.md`

Goal:

- Provide a host-owned wrapper for provider-backed guide-worker lane waves while
  keeping Codex MCP fake-only.

Current implementation surface:

- Host helper: `run_host_owned_guide_worker_provider_execution()`
- CLI: `doc-based-coding qoder guide-worker-smoke`
- Evidence product: `host_guide_worker_provider_execution_evidence`

Validation:

- `py_compile` for wrapper/runtime/CLI/tests passed.
- Focused wrapper/CLI/runtime tests passed: `6 passed, 433 deselected`.
- Related MCP/CLI/runtime regression passed: `16 passed, 378 deselected`.

### Autonomous Guide Instruction Planner

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-24-autonomous-guide-instruction-planner.md`

Goal:

- Let a single guide/leader schedule multiple lane-bound worker tasks from a
  high-level guide task plus lane specs, while preserving explicit
  `workerInstructions` precedence.

Current implementation surface:

- Runtime request: `GuideWorkerPlanningRequest`
- Lane spec: `GuideWorkerPlannerLaneSpec`
- CLI flags: `--guide-task-title`, `--guide-task-summary`, repeatable
  `--planner-lane`
- MCP payload fields: `guideTask`, `plannerLaneSpecs`

Validation:

- `py_compile` for runtime/CLI/MCP/tests passed.
- Focused runtime/CLI/MCP tests passed: `15 passed, 385 deselected`.
- Scheduler prompt tests passed: `21 passed`.
- Doc-loop validator passed.
- `git diff --check` passed with Windows line-ending warnings only.
- `analyze_changes` returned no impact nodes; MCP registration coupling was
  covered by server schema/routing and route tests.

### Guide Worker Planned Execution Closure

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-24-guide-worker-planned-execution-closure.md`

Goal:

- Let the host-owned guide-worker provider wrapper execute planner-derived
  lane-bound workers and publish per-worker execution receipts.

Current implementation surface:

- Resolver: `resolve_guide_worker_instructions()`
- Config fields: `planning_request`, `planner_worker_runtime_provider`
- CLI planner flags on `qoder guide-worker-smoke`
- Evidence fields: `planning`, `planned_worker_instructions`,
  `worker_execution_receipts`

Validation:

- `py_compile` for wrapper/runtime/CLI/tests passed.
- Focused wrapper/CLI/prompt tests passed: `10 passed, 166 deselected`.
- Related runtime/MCP/CLI regression passed: `17 passed, 383 deselected`.
- Doc-loop validator passed.
- `git diff --check` passed with Windows line-ending warnings only.
- `analyze_changes` returned no impact nodes and no coupling alerts.

### Codex Worker Sandbox Writeback Policy

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-24-codex-worker-sandbox-writeback-policy.md`

Goal:

- Add the first host-owned sandbox/writeback bridge for Codex workers:
  explicit worker sandbox profiles, git-worktree allocation evidence, and
  review-only worker writeback receipts.

Current implementation surface:

- Instruction fields: `sandbox_profile` / JSON-MCP `sandboxProfile`
- Preflight runtime task fields: `runtime_workspace_root`,
  `sandbox_allocation_id`, `sandbox_provider`, `visible_mounts`
- Host wrapper config: `git_worktree_sandbox_root`,
  `sandbox_allocation_evidence_id`, `sandbox_allocation_evidence_path`
- Evidence field: `worker_writeback_receipts`

Validation:

- `py_compile` for runtime/wrapper/CLI/MCP/tests passed.
- Focused runtime/wrapper/CLI/MCP tests passed: `29 passed, 461 deselected`.
- Doc-loop validator passed.

### Worker Patch Review Integration

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-24-worker-patch-review-integration.md`

Goal:

- Export git-worktree worker edits as review-only patch proposal
  `ExchangeArtifact` products and connect them to the existing
  `merge_candidate` readback path without applying patches automatically.

Current implementation surface:

- Runtime helper: `build_worker_patch_review_artifact(s)()`
- Product: `worker_patch_review_proposal`
- Host evidence fields: `worker_patch_artifact_refs` and per-receipt
  `patch_artifact_ref`
- CLI help: `codex guide-worker-smoke` and `qoder guide-worker-smoke`
  describe review-only patch artifacts / merge candidates.

Validation:

- `py_compile` for runtime/wrapper/CLI/tests passed.
- Focused runtime/wrapper/CLI/MCP tests passed: `22 passed, 470 deselected`.

### Worker Patch Apply/Reject Policy

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-24-worker-patch-apply-reject-policy.md`

Goal:

- Consume accepted worker patch review dispositions explicitly through
  check/apply/reject actions while preserving review-only export and separate
  cleanup ownership.

Current implementation surface:

- Runtime helper: `consume_worker_patch_review_decision()`
- Result model: `WorkerPatchReviewConsumerResult`
- CLI: `doc-based-coding scheduler consume-worker-patch-review`
- Action-candidate readback: worker patch proposals remain `merge_candidate`
  but suggest `workerPatchReview`.

Validation:

- `py_compile` for runtime/CLI/tests passed.
- Focused runtime/CLI tests passed: `5 passed, 383 deselected`.
- Adjacent action-candidate/merge/patch tests passed:
  `14 passed, 560 deselected`.

### Worker Patch Composition Preflight

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-24-worker-patch-composition-preflight.md`

Goal:

- Preflight multiple worker patch proposals in caller order using a temporary
  workspace, detecting first conflicts and touched-path collisions without
  mutating source workspace.

Current implementation surface:

- Runtime helper: `preflight_worker_patch_composition()`
- Models: `WorkerPatchCompositionRef`,
  `WorkerPatchCompositionStep`,
  `WorkerPatchCompositionPreflightResult`
- CLI: `doc-based-coding scheduler preflight-worker-patch-composition`

Validation:

- `py_compile` for runtime/CLI/tests passed.
- Focused runtime/CLI tests passed: `4 passed, 388 deselected`.
- Adjacent worker patch/action-candidate regression passed:
  `13 passed, 457 deselected`.
- Doc-loop validator passed.
- `git diff --check` passed with Windows line-ending warnings only.
- `analyze_changes` returned no impact nodes and no coupling alerts.

### Host UX Worker Patch Review Binding

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-25-host-ux-worker-patch-review-binding.md`

Goal:

- Make worker patch review proposals operable from Scheduler Operator Host UX
  with explicit check/reject and non-mutating multi-patch preflight.

Current implementation surface:

- Runtime helper: `review_worker_patch_action_candidate()`
- CLI: `doc-based-coding scheduler review-worker-patch`
- Host UX panel: `Worker Patch Review`
- Actions: single-patch `Check`, single-patch `Reject`, and selected patch
  composition preflight.

Validation:

- `py_compile` for runtime/CLI touched files passed.
- Focused runtime tests passed: `8 passed, 299 deselected`.
- Focused CLI tests passed: `7 passed, 83 deselected`.
- Extension build passed.
- Focused Scheduler Operator contract tests passed: `14 passed`.
- Focused Progress Graph Preview render tests passed: `21 passed`.
- Screenshot verification recorded at
  `output/playwright/host-ux-worker-patch-review-binding/worker-patch-review-fixture.png`.
- Doc-loop validator passed.
- `git diff --check` passed with Windows line-ending warnings only.
- `analyze_changes` returned no impact nodes and no coupling alerts.

### Codex CLI Worker Runtime Provider

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-24-codex-cli-worker-runtime-provider.md`

Goal:

- Add Codex CLI as a host-owned worker runtime provider for guide-worker lane
  waves while keeping MCP live-provider execution fake-only.

Current implementation surface:

- Runtime provider key: `codex`
- Adapter seam: `CodexCliClient`, `CodexCliAgentRuntimeAdapter`
- Process wrapper: `CodexCliProcessClient`
- Host-owned CLI: `doc-based-coding codex readiness`,
  `doc-based-coding codex guide-worker-smoke`

Validation:

- `py_compile` for runtime/wrapper/CLI/MCP/tests passed.
- Focused runtime/wrapper/CLI tests passed: `24 passed, 432 deselected`.
- Focused MCP fake-only/CLI regression passed: `13 passed, 102 deselected`.
- Doc-loop validator passed.
- `git diff --check` passed with Windows line-ending warnings only.
- `analyze_changes` returned no impact nodes; the MCP registration coupling
  alert was reviewed as non-actionable because only schema wording changed and
  focused MCP route tests passed.

### Evidence Publish To Consumer Closure

Status: `completed`

Planning gate:

- `design_docs/stages/planning-gate/2026-06-22-evidence-publish-to-consumer-closure.md`

Goal:

- Prove durable supervisor storage binding evidence can enter a downstream
  scheduler consumer closure through the compact binding artifact publish
  surface.

Current implementation surface:

- Runtime helper: `run_evidence_publish_to_consumer_closure()`
- CLI: `doc-based-coding scheduler evidence-publish-consumer-closure`

Validation:

- Focused runtime/CLI closure tests passed: `4 passed, 363 deselected`.

## Latest Completed Slice

### Agent Communication Product Closure

Status: `completed`

Summary:

- Closed the first artifact-centered agent communication product layer:
  mailbox/history, reply/lifecycle, action candidates, dispositions, and
  accepted-candidate consumers.
- Exposed the surfaces through runtime helpers, CLI, MCP tools/resources, and
  prompt/tool-audit docs.
- Preserved the rule that text alone does not mutate scheduler/review/handoff/
  merge/blocker state.

Key docs:

- `review/agent-communication-product-closure-2026-06-22.md`
- `design_docs/agent-coordination-exchange-artifact-design-record.md`
- `design_docs/agent-runtime-layering-and-orchestration-slice-plan.md`

Validation:

- `py_compile` for agent communication runtime/CLI/MCP/tests passed.
- Focused product validation: `39 passed, 191 deselected`.
- Wider related validation: `230 passed`.
- `git diff --check`: no whitespace errors; Windows line-ending warnings only.
- `analyze_changes`: MCP registration coupling was covered by server
  schema/routing and route tests.

## Current Pending Todo

- [x] Finish this Checklist recovery-surface optimization pass.
- [x] Align AGENTS/bootstrap/tooling guidance with the compact Checklist role.
- [x] Finish focused and adjacent validation for
  `Guide Worker Exchange Workflow Dogfood`.
- [x] Open and complete the next narrow guide-worker orchestration planning
  gate.
- [x] Complete the guide-worker local orchestration MCP wrapper.
- [x] Complete the fake/mock-validated lane wave executor contract.
- [x] Complete provider runtime mapping for host-injected worker adapters.
- [x] Complete host-owned guide-worker provider execution wrapper.
- [x] Complete the deterministic guide instruction planner for high-level task
  plus lane-spec decomposition.
- [x] Complete host-owned planned guide-worker execution receipts.
- [x] Complete `Evidence Publish To Consumer Closure` and remove its parked
  recovery branch from the current hot path.
- [x] Complete Codex worker sandbox writeback receipts.
- [x] Complete worker patch review artifact integration.
- [x] Complete worker patch check/apply/reject consumer.
- [x] Complete multi-worker patch composition preflight.
- [x] Complete Host UX worker patch review binding.
- [x] Complete runtime invocation audit/retry and leader-worker activation
  contracts.
- [x] Complete recoverable leader-worker dispatcher tick/loop.
- [x] Complete host-owned worker delivery acknowledgement.
- [x] Complete Codex delivery supervisor loop over pending delivery records.
- [x] Define stable Codex CLI worker runtime continuous-use target and
  acceptance criteria.
- [x] Complete Codex permission/review outcome consumer.
- [x] Complete Codex interruption recovery and retry policy.
- [x] Complete Codex delivery sandbox patch review closure.
- [x] Complete Codex multi-lane continuous progress fixture.
- [x] Complete Codex runtime status readback and close the first stable
  continuous-use target in
  `design_docs/codex-cli-stable-worker-runtime-continuous-use-target.md`.
- [ ] For later gates, consider persistent monitoring UI, true process-level
  parallelism, distributed worker leases, live Codex process resume, or
  automatic log compaction as separate product slices.

## Write Rules For This File

Keep this file short:

- Update it when current phase, active gate, latest completed slice, recovery
  order, or immediate pending todo changes.
- Do not append long validation streams or full historical phase logs here.
- Put historical detail in `design_docs/history/` or the relevant planning gate
  / review / direction-analysis document.
- Keep new entries linked to their source docs.

## Related Indexes

- Phase/status narrative:
  `design_docs/Global Phase Map and Current Position.md`
- Active checkpoint:
  `.codex/checkpoints/latest.md`
- Active handoff mirror:
  `.codex/handoffs/CURRENT.md`
- Direction candidates:
  `design_docs/direction-candidates-after-phase-35.md`
- Tooling protocols:
  `design_docs/tooling/`
- Platform authority docs:
  `docs/`
