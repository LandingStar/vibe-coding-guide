# Codex CLI Stable Worker Runtime Continuous Use Target

> Date: 2026-06-26
> Status: first stable continuous-use target completed / slice guidance

## Purpose

This document turns the informal goal "stable Codex CLI worker runtime
continuous use" into a goal-ready target with explicit acceptance criteria and
bounded implementation slices.

It refines the gap left after:

- `design_docs/stages/planning-gate/2026-06-24-codex-cli-worker-runtime-provider.md`
- `design_docs/stages/planning-gate/2026-06-24-codex-worker-sandbox-writeback-policy.md`
- `design_docs/stages/planning-gate/2026-06-25-runtime-invocation-recovery-and-audit-trail.md`
- `design_docs/stages/planning-gate/2026-06-25-leader-worker-activation-loop-contract.md`
- `design_docs/stages/planning-gate/2026-06-25-recoverable-leader-worker-dispatcher-tick.md`
- `design_docs/stages/planning-gate/2026-06-25-host-owned-worker-delivery-acknowledgement.md`
- `design_docs/stages/planning-gate/2026-06-26-codex-delivery-supervisor-loop.md`
- `design_docs/stages/planning-gate/2026-06-26-codex-result-consumer-contract.md`

## Goal-Ready Target Statement

Use this as the target text for a future goal instruction:

```text
Make Codex CLI usable as a stable, recoverable scheduler-owned worker runtime.

Acceptance means that, in a test workspace with scheduler-owned tasks and at
least two lane-distinct worker contexts, one host/operator command can start a
bounded supervisor loop that continuously activates ready Codex worker tasks,
dispatches them through leader-worker delivery, invokes Codex CLI with compact
audit/retry, handles success/failure/permission outcomes without manual
step-by-step intervention, persists successful output artifacts, advances
scheduler task state through recoverable event logs, preserves sandbox and
writeback review boundaries, survives a simulated interruption with auditable
resume behavior, and exposes enough status readback for an operator or guide
agent to understand what ran, what is waiting, what failed, and what requires
review. Detailed info can be found in `design_docs/codex-cli-stable-worker-runtime-continuous-use-target.md`.
```

## Meaning Of "Stable Continuous Use"

This target is stronger than "Codex CLI can be invoked once".

It means Codex CLI is a dependable `AgentRuntimeAdapter` backend inside the
project-owned orchestration layer:

1. The scheduler remains the lifecycle authority.
2. Codex CLI runs only admitted, bounded worker tasks.
3. The host supervisor can keep making progress across multiple ready tasks.
4. Runtime attempts are retryable, auditable, and recoverable.
5. Results are durable products, not only command output.
6. Permission requests, failures, and interrupted runs produce explicit states.
7. Sandboxes and review-only writeback policy are preserved.
8. Operator and guide-agent readback is sufficient to decide the next action.

## Explicit Acceptance Criteria

### A. Host Readiness

The system must provide a credential-safe readiness check for Codex CLI:

1. Reports executable path/version or equivalent availability evidence.
2. Fails closed when Codex CLI is missing or unusable.
3. Does not print tokens, auth material, or raw credentials.
4. Can be run independently from scheduler mutation.

Existing partial surface: `doc-based-coding codex readiness`.

### B. Bounded Supervisor Loop

One command or host-owned helper must run the minimal continuous loop:

```text
recover scheduler state
-> evaluate leader-worker activation
-> write dispatch decisions
-> sync delivery records
-> deliver ready Codex tasks
-> consume successful results
-> repeat until bounded stop condition
```

Acceptance details:

1. The loop has explicit bounds: max ticks, max deliveries, max runtime
   failures, and stop reason.
2. It does not require the user to manually run activation, dispatcher,
   delivery sync, Codex delivery, and result consumption as separate commands.
3. It can skip non-Codex tasks without failing the Codex path.
4. It preserves deterministic read/write paths for state, logs, delivery, and
   artifacts.
5. It returns a compact JSON summary with attempted, completed, failed,
   waiting, skipped, and review-required counts.

### C. Durable Success Path

For every successful Codex worker task:

1. Runtime invocation audit contains the Codex attempt record.
2. Delivery state is acknowledged only after result consumption succeeds.
3. Output artifact is stored in `JsonArtifactVersionStore`.
4. Scheduler event log gets a `task_completed` event with exact artifact id and
   version.
5. `recover_scheduler_state(snapshot, event_log)` reconstructs the completed
   task, run record, and output artifact reference.

Existing partial surface: Codex result consumer contract.

### D. Failure Path

For a failed Codex invocation or failed result consumer:

1. Delivery state is marked `failed` with a stable `failure_kind`.
2. Failure detail is compact and credential-redacted.
3. Runtime invocation audit records retry attempts where applicable.
4. Scheduler completion is not claimed.
5. Operator readback can distinguish provider failure from durable result
   consumer failure.

### E. Permission / Review Path

If Codex runtime surfaces permission requests or cannot safely complete without
host review:

1. The task must not be marked complete.
2. Scheduler state should become `review_required` or another explicit
   waiting/review state.
3. The permission request must be durable enough for operator/guide review.
4. Approval/rejection must be handled by a scheduler-owned transition.
5. Downstream dependencies that require completion must not wake until review
   resolves.

Implemented in
`design_docs/stages/planning-gate/2026-06-27-codex-permission-review-outcome-consumer.md`.

Remaining gap: approval/rejection still uses the existing scheduler-owned
permission review resolver; no dedicated UI approval panel is included in this
target slice.

### F. Interruption And Resume

The loop must survive an interrupted Codex CLI run or host process stop:

1. Runtime invocation logs preserve the last known attempt state.
2. Delivery records remain pending, failed, or in-progress with enough metadata
   to decide resume/retry/abandon.
3. Restarting the supervisor does not duplicate completed tasks.
4. Restarting can quickly retry eligible pending/failed-transient work under
   explicit policy.
5. Old invocation logs can be compacted or archived without losing audit facts.

Implemented in
`design_docs/stages/planning-gate/2026-06-27-codex-interruption-recovery-and-retry-policy.md`
for durable retry of eligible transient failed delivery after restart.

Remaining gap: live Codex process resume, distributed leases, and heartbeat
supervision remain out of scope for this target slice.

### G. Sandbox And Writeback Boundary

Codex worker execution must remain compatible with sandbox/writeback policy:

1. Worker tasks can run in the configured runtime workspace or git-worktree
   sandbox.
2. Source workspace changes are not silently applied.
3. Worker edits are exported as review-only patch artifacts or equivalent
   review products.
4. Cleanup is explicit and auditable.
5. Result consumption and patch review remain separate concepts.

Current partial surface: Codex worker sandbox writeback policy and worker patch
review integration.

### H. Multi-Lane Limited Parallelism

For at least two lane-distinct worker contexts:

1. The scheduler can select independent ready Codex tasks from different lanes.
2. The loop can make progress across lanes without conflating context scopes.
3. Lane dependencies and merge/review gates block only the appropriate work.
4. The first stable target may run tasks serially while preserving scheduling
   parallelism metadata.
5. Process-level concurrent runtime execution for lane-distinct Codex delivery
   is implemented as the follow-up C8 gate:
   `design_docs/stages/planning-gate/2026-06-28-codex-concurrent-delivery-gate.md`.

### I. Operator / Guide-Agent Readback

The host must provide readback for:

1. Current scheduler queue and stop reason.
2. Pending/acknowledged/failed delivery records.
3. Runtime invocation attempts and retry status.
4. Output artifact refs for completed tasks.
5. Review-required and permission-required work.
6. Failed result-consumer records.
7. Projection into scheduler-derived work trajectory, without mutating the
   agent-owned Local Work Trajectory artifact.

### J. End-To-End Test Fixture

The target is not accepted until there is a repeatable fixture that proves:

1. At least three worker tasks.
2. At least two lane-distinct contexts.
3. At least one dependency edge.
4. At least one successful Codex completion.
5. At least one skipped non-Codex or waiting task, or one review/failure branch
   if live Codex behavior allows deterministic simulation.
6. Recovery from snapshot plus event log after the loop.
7. No raw secrets in logs.

## Suggested Slice Breakdown

### Gate C1 — Credentialed Codex CLI E2E Smoke

Status: implemented in
`design_docs/stages/planning-gate/2026-06-26-credentialed-codex-cli-e2e-smoke.md`.

Purpose: prove that the already-built Codex delivery and result-consumer path
works with a real Codex CLI in a controlled test workspace.

Acceptance:

1. Uses real Codex CLI when host readiness is positive.
2. Runs one narrow scheduler-owned task.
3. Writes runtime audit, delivery acknowledgement, output artifact, and
   `task_completed`.
4. Recovers scheduler state as `complete`.
5. Leaves source workspace writeback under review-only policy.

Non-goals:

1. No continuous loop.
2. No interruption recovery.
3. No permission branch closure.
4. No process-level parallelism.

### Gate C2 — Bounded Codex Supervisor Loop Binding

Status: implemented in
`design_docs/stages/planning-gate/2026-06-26-bounded-codex-supervisor-loop-binding.md`.

Purpose: remove manual step-by-step operation for normal progress.

Acceptance:

1. One command/helper chains activation, dispatch, delivery sync, Codex
   delivery, and result consumption.
2. Supports bounded repeated ticks.
3. Reports stable stop reasons.
4. Keeps authority split visible in JSON output.

Non-goals:

1. No daemon.
2. No live session resume.
3. No permission branch implementation unless already available.

### Gate C3 — Codex Permission / Review Outcome Consumer

Status: implemented in
`design_docs/stages/planning-gate/2026-06-27-codex-permission-review-outcome-consumer.md`.

Purpose: handle Codex permission requests and review-required outcomes without
incorrectly marking tasks complete.

Acceptance:

1. Permission request is persisted as scheduler/review state.
2. Delivery is not acknowledged as completed work until review resolves.
3. Approval and rejection produce scheduler-owned events.
4. Downstream dependencies respect the review state.

Non-goals:

1. No UI approval panel unless separately scoped.
2. No broad permission policy redesign.

### Gate C4 — Interruption Recovery And Retry Policy

Status: implemented in
`design_docs/stages/planning-gate/2026-06-27-codex-interruption-recovery-and-retry-policy.md`.

Purpose: make interrupted or transient failed Codex executions recoverable.

Acceptance:

1. In-progress or failed-transient delivery can be inspected after restart.
2. Retry policy decides retry/abandon without duplicating completed tasks.
3. Runtime invocation logs are compactly preserved.
4. Old invocation logs can be archived/compacted under explicit policy.

Non-goals:

1. No distributed worker lease.
2. No remote process supervisor.

### Gate C5 — Sandbox / Patch Review Integration Closure

Status: implemented in
`design_docs/stages/planning-gate/2026-06-27-codex-delivery-sandbox-patch-review-closure.md`.

Purpose: connect Codex continuous execution to the existing sandbox and
review-only writeback products.

Acceptance:

1. Codex task execution can run in a configured worker sandbox.
2. Detected file changes are exported as review-only patch artifacts.
3. Result completion and patch apply remain separate operator decisions.
4. Cleanup remains explicit and auditable.

Non-goals:

1. No automatic patch application.
2. No conflict resolution automation beyond existing review/preflight surfaces.

### Gate C6 — Multi-Lane Continuous Progress Fixture

Status: implemented in
`design_docs/stages/planning-gate/2026-06-27-codex-multilane-continuous-progress-fixture.md`.

Purpose: prove limited lane-aware continuous use.

Acceptance:

1. Fixture has at least two lanes and at least three tasks.
2. Independent lane tasks can both be selected over bounded loop ticks.
3. Dependency and merge/review gating are visible.
4. Scheduler-derived trajectory projection shows the resulting state.

Non-goals:

1. True simultaneous Codex processes may remain deferred.
2. No new Local Work Trajectory mutation from runtime code.

### Gate C7 — Operator / Guide-Agent Runtime Status Readback

Status: implemented in
`design_docs/stages/planning-gate/2026-06-27-codex-runtime-status-readback.md`.

Purpose: make the loop usable without opening raw files manually.

Acceptance:

1. One readback command summarizes scheduler, delivery, runtime invocation,
   result artifacts, and review-required items.
2. Output is compact enough for a guide agent to use as context.
3. It reports what action is safe next.
4. It does not mutate scheduler or Local Work Trajectory.

Non-goals:

1. No full web UI unless separately scoped.
2. No long transcript viewer.

### Gate C8 — Codex Concurrent Delivery Gate

Status: implemented in
`design_docs/stages/planning-gate/2026-06-28-codex-concurrent-delivery-gate.md`.

Purpose: add explicit bounded process-level concurrency for independent
lane-distinct Codex worker delivery while retaining serialized writeback.

Provider scope: C8 is Codex-only. It does not adapt Qoder, opencode, generic
provider runtimes, or the guide-worker wave executor to process-level
concurrency.

Acceptance:

1. `CodexDeliverySupervisorRequest` and bounded loop request expose an
   explicit concurrency limit with serial defaults.
2. One supervisor pass can run at least two lane-distinct Codex runtime
   invocations concurrently when the limit is greater than one.
3. A concurrent runtime batch never includes two records from the same lane.
4. Runtime invocation audit remains durable and redacted.
5. Result consumption, permission review, worker patch review, delivery
   acknowledgement, scheduler event-log writes, and exchange-store writes
   remain serialized after runtime completion.
6. Loop / CLI JSON reports requested concurrency, observed batch size,
   process-level parallelism, and serialized writeback.

Non-goals:

1. No daemon or long-lived worker pool.
2. No distributed leases.
3. No live Codex process resume.
4. No automatic patch application or conflict resolution.

## Recommended Order

Recommended immediate order:

1. C1: Credentialed Codex CLI E2E Smoke.
2. C2: Bounded Codex Supervisor Loop Binding.
3. C3: Permission / Review Outcome Consumer.
4. C4: Interruption Recovery And Retry Policy.
5. C5: Sandbox / Patch Review Integration Closure.
6. C6: Multi-Lane Continuous Progress Fixture.
7. C7: Operator / Guide-Agent Runtime Status Readback.
8. C8: Codex Concurrent Delivery Gate.

Reasoning:

- C1 proves the live runtime before more orchestration is built around it.
- C2 removes manual command chaining and makes normal use possible.
- C3 prevents unsafe false completion when Codex asks for permission.
- C4 addresses the user's explicit concern about service/network interruption.
- C5 keeps real code edits behind review-only writeback.
- C6 proves lane-aware continuous use after the single-provider loop is stable.
- C7 turns the machinery into an inspectable operator product.
- C8 upgrades lane-aware scheduling into opt-in true process-level Codex
  runtime concurrency while keeping writeback serialized.

## Completion Audit

As of 2026-06-27, this target's first stable continuous-use pass is accepted:

- A Host Readiness: covered by the Codex readiness surface and C1 fail-closed
  smoke behavior.
- B Bounded Supervisor Loop: covered by C2 and the
  `codex-delivery-supervisor-loop` command.
- C Durable Success Path: covered by C2 and the Codex result consumer contract.
- D Failure Path: covered by delivery failure state, compact runtime invocation
  audit, and C4 retry policy.
- E Permission / Review Path: covered by C3 permission/review outcome
  consumption and scheduler-owned review state.
- F Interruption And Resume: covered by C4 restart retry over eligible
  transient failed delivery records. Live process resume remains out of scope.
- G Sandbox And Writeback Boundary: covered by C5 sandbox preflight and
  review-only worker patch publication.
- H Multi-Lane Limited Parallelism: covered by C6 multi-lane fixture. Execution
  remains serial while preserving lane-distinct scheduling metadata.
- I Operator / Guide-Agent Readback: covered by C7 compact status readback.
  The scheduler-derived trajectory projection part is covered by the existing
  `doc-based-coding scheduler project` projection surface, not by C7; both
  surfaces preserve that runtime code does not mutate agent-owned Local Work
  Trajectory.
- J End-To-End Test Fixture: covered by C6/C7 fake-client multi-lane fixture
  tests and adjacent supervisor regression tests.

Acceptance evidence is recorded in:

- `design_docs/stages/planning-gate/2026-06-27-codex-runtime-status-readback.md`
- `design_docs/stages/planning-gate/2026-06-27-codex-multilane-continuous-progress-fixture.md`
- `design_docs/stages/planning-gate/2026-06-27-codex-delivery-sandbox-patch-review-closure.md`
- `design_docs/stages/planning-gate/2026-06-27-codex-interruption-recovery-and-retry-policy.md`
- `design_docs/stages/planning-gate/2026-06-27-codex-permission-review-outcome-consumer.md`
- `design_docs/stages/planning-gate/2026-06-26-bounded-codex-supervisor-loop-binding.md`
- `design_docs/stages/planning-gate/2026-06-26-credentialed-codex-cli-e2e-smoke.md`
- `design_docs/stages/planning-gate/2026-06-26-codex-result-consumer-contract.md`
- `design_docs/stages/planning-gate/2026-06-26-codex-delivery-supervisor-loop.md`

As of 2026-06-28, the follow-up C8 gate also closes the previously deferred
process-level concurrency gap for independent lane-distinct Codex delivery:

- `design_docs/stages/planning-gate/2026-06-28-codex-concurrent-delivery-gate.md`

## Current Distance Estimate

From the current repository state:

1. Minimal live single-worker Codex CLI loop: C1 + C2.
2. Stable recoverable single-provider continuous use: C1 + C2 + C4 + C3.
3. Review-safe real coding worker use: C1 through C5.
4. Multi-lane usable worker runtime: C1 through C6.
5. Operator-friendly routine use: C1 through C7.
6. Opt-in process-concurrent lane-distinct Codex delivery: C1 through C8.

The project now has the C1 through C8 foundation for review-safe, recoverable,
multi-lane Codex worker delivery with compact operator / guide-agent status
readback and explicit opt-in process-level runtime concurrency for independent
lane-distinct delivery records. It satisfies this document's first stable
continuous-use target and the follow-up C8 concurrency gate while leaving
daemonization, persistent monitoring UI, distributed worker leases, live Codex
process resume, live-provider throughput validation, and automatic patch
application as explicit later product work.

## Explicit Non-Goals For The Target

This target does not require:

1. Codex CLI becoming the scheduler.
2. MCP live provider execution.
3. Runtime code mutating agent-owned Local Work Trajectory.
4. Automatic patch application to the source workspace.
5. True distributed workers.
6. True process-level parallelism in the first C1-C7 acceptance pass.
7. Raw transcript retention as the primary audit mechanism.

## Readiness Checklist For Future `/goal`

Before starting a goal against this target, read:

1. `design_docs/Project Master Checklist.md`
2. This document
3. `design_docs/stages/planning-gate/2026-06-26-codex-result-consumer-contract.md`
4. `design_docs/stages/planning-gate/2026-06-26-codex-delivery-supervisor-loop.md`
5. `design_docs/stages/planning-gate/2026-06-25-runtime-invocation-recovery-and-audit-trail.md`
6. `design_docs/stages/planning-gate/2026-06-24-codex-worker-sandbox-writeback-policy.md`
7. `design_docs/agent-runtime-layering-and-orchestration-slice-plan.md`

Then open only the next narrow gate. Do not implement all gates in one slice.
