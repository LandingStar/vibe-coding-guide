# Edit Lease Lifecycle After Write-Back Unification Direction Analysis

> Date: 2026-06-20
> Status: direction analysis

## Context

The edit lease policy line has now completed two narrow backend slices:

1. `design_docs/stages/planning-gate/2026-06-20-edit-lease-conflict-classifier-and-admission-evidence.md`
2. `design_docs/stages/planning-gate/2026-06-20-write-back-enforcement-unification.md`

The current state is stronger than the earlier skeleton:

1. `EditScopeLease` is a scheduler-owned task object.
2. `classify_edit_lease_conflict()` emits structured
   `EditLeaseConflictDecision` evidence.
3. Scheduler admission can route conflicts to `waiting`, `review_required`, or
   `blocked`.
4. Write-back planning can consume explicit edit lease evidence and turn
   payloads into `planned`, `review_routed`, or `blocked` evidence.
5. `SharedProcessSandboxProvider` can expose lease-scoped `visible_mounts`, but
   remains metadata-only.
6. Scheduler daemon lifecycle control exists for the daemon owner, but not for
   individual edit leases.

Relevant baselines:

- `design_docs/edit-lease-conflict-policy-expansion-direction-analysis.md`
- `review/write-back-enforcement-unification-2026-06-20.md`
- `design_docs/agent-runtime-layering-and-orchestration-slice-plan.md`
- `design_docs/agent-cluster-scheduling-and-isolation-investigation.md`
- `review/background-scheduler-daemon-lifecycle-protocol-2026-06-20.md`
- `review/scheduler-daemon-lifecycle-cli-mcp-surface-2026-06-20.md`

## Problem

The project now has a stable conflict decision and a write-back consumer, but
leases are still static task metadata. That leaves several gaps:

1. There is no scheduler-owned record that a lease was requested, acquired,
   renewed, released, expired, or revoked.
2. `EditScopeLease.expires_at` is a string field, but no deterministic policy
   interprets it.
3. Cancellation, shutdown, task failure, and stale scheduler recovery do not
   yet have a lease cleanup target.
4. Sandbox mount binding cannot distinguish a lease that is merely declared
   from one that was actually acquired.
5. Host UX / MCP readback would currently show declared task lease data and
   conflict evidence, but not lifecycle ownership.
6. A real sandbox provider would need lifecycle-backed mount authority before
   it can safely treat lease paths as enforceable filesystem boundaries.

The next slice should therefore decide whether the project should first define
lease lifecycle semantics, jump to sandbox binding, or expose readback.

## Candidate A - Edit Lease Acquisition And Expiration Lifecycle

### Shape

Introduce scheduler-owned lease lifecycle evidence without changing real
filesystem enforcement.

First-version objects could include:

```text
EditLeaseLifecycleRecord
- lease_id
- task_id
- state: requested | acquired | waiting | review_required | released | expired | revoked | blocked
- mode
- allowed_artifacts
- denied_artifacts
- conflict_policy
- acquired_at
- expires_at
- released_at
- reason
- conflict_decision

SchedulerLeaseEvent
- lease_requested
- lease_acquired
- lease_waiting
- lease_review_required
- lease_released
- lease_expired
- lease_revoked
- lease_blocked
```

Recommended first behavior:

1. Keep `EditScopeLease` as the task declaration.
2. Add scheduler-owned helper(s) that derive lifecycle records from admission
   and explicit lifecycle operations.
3. Require deterministic time input for expiry checks; do not read ambient
   current time in replay-sensitive code.
4. Treat task completion, cancellation, rejection, and failure as explicit
   release/revoke opportunities.
5. Record lifecycle evidence in scheduler history or a narrow lease event log.
6. Keep write-back as a consumer of explicit evidence, not a live scheduler
   state reader.

### Pros

1. Fills the missing authority layer between conflict classification and real
   sandbox enforcement.
2. Gives cancellation / shutdown / stale recovery a concrete cleanup target.
3. Makes `expires_at` meaningful without introducing ambient-time
   nondeterminism.
4. Gives Host UX / MCP readback stable lifecycle facts later.
5. Can be validated locally with scheduler tests and no external provider.

### Risks

1. If the slice tries to implement daemon expiry sweeping, cleanup, Host UX,
   and sandbox mount enforcement together, it will grow too large.
2. Expiry policy can become nondeterministic if it uses wall-clock time inside
   replay paths.
3. Lifecycle records must not become a second source of task contract truth.

### Fit

High. This is the recommended next planning gate.

## Candidate B - Sandbox Mount Binding Over Acquired Leases

### Shape

Bind acquired edit leases to `SandboxRequest.required_mounts` /
`SandboxAllocation.visible_mounts` and make allocation evidence explicitly say
which lease authorized which mount.

Possible first behavior:

1. preflight requires an acquired lease record for write-capable sandbox mounts;
2. sandbox allocation emits `lease_authorized_mounts`;
3. `SharedProcessSandboxProvider` remains metadata-only but reports the same
   contract shape expected from real providers.

### Pros

1. Moves toward enforceable execution isolation.
2. Aligns sandbox mount policy with scheduler edit authority.
3. Gives future Docker / worktree / remote VM providers a clearer contract.

### Risks

1. Premature if there is no acquired/released/expired lifecycle record.
2. Metadata-only shared-process allocation can look stronger than it is unless
   warnings remain explicit.
3. Real provider enforcement is still separate and security-heavy.

### Fit

Second. It should consume Candidate A rather than invent lifecycle status
inside sandbox allocation.

## Candidate C - Host UX / MCP Lease Readback

### Shape

Expose lease declarations, lifecycle records, conflict decisions, and current
blocking reasons through MCP resources or Host UX panels.

Possible first behavior:

1. a read-only MCP resource for scheduler lease summaries;
2. CLI inspection over snapshot / event-log paths;
3. Host UX later reads the same summary.

### Pros

1. Improves operator diagnosis for blocked or review-routed tasks.
2. Helps users see why graph/scheduler progress stopped.
3. Low execution risk if read-only.

### Risks

1. Premature before lifecycle records exist.
2. Can become noisy if it only shows declared leases and conflict strings.
3. UI work requires screenshot validation and should not be mixed into backend
   lifecycle semantics.

### Fit

Third. It should follow the lifecycle record shape.

## Candidate D - Lifecycle Host UX Readback / Control Binding

### Shape

Bind the already completed scheduler daemon lifecycle CLI/MCP surface to Host
UX readback and controls.

### Pros

1. The daemon lifecycle control contract already exists.
2. It improves operator ergonomics for start/pause/resume/cancel/run-once.
3. It is adjacent to existing Scheduler Operator Host UX work.

### Risks

1. It advances daemon operation, not edit authority safety.
2. It is UI work and requires screenshot validation.
3. It does not solve lease lifecycle or sandbox readiness.

### Fit

Viable as a product polish line, but not the strongest next backend slice for
multi-agent safety.

## Candidate E - Real Sandbox Provider Spike

### Shape

Implement a first real provider behind `SandboxProvider`, likely `git-worktree`
or `docker`, and validate one scheduled task with stronger filesystem/process
separation.

### Pros

1. Converts metadata-only sandboxing into real operational isolation.
2. Directly supports future high-risk agents.
3. Lets provider feasibility be measured with concrete tests.

### Risks

1. Environment-heavy and security-sensitive.
2. Provider choice is not only an implementation detail; it affects cleanup,
   secrets, network, and mount policy.
3. Without lease lifecycle, it lacks a durable authority source for mount
   ownership and cleanup.

### Fit

Later. It should follow lease lifecycle and mount binding.

## Recommendation

Choose Candidate A next:

> Edit Lease Acquisition And Expiration Lifecycle

Reasoning:

1. Conflict classification and write-back evidence are already in place.
2. The next missing invariant is not more UI or a stronger provider; it is a
   scheduler-owned lifecycle record for who currently holds edit authority.
3. Sandbox mount binding and Host UX readback both need lifecycle facts to avoid
   presenting declarations as acquired authority.
4. A narrow lifecycle slice is deterministic, local, and testable without real
   providers or UI.

## Proposed Next Planning Gate

```text
2026-06-20-edit-lease-acquisition-and-expiration-lifecycle.md
```

Recommended scope:

1. Define scheduler-owned lease lifecycle record and event shape.
2. Add explicit acquire / release / expire / revoke helpers.
3. Use `classify_edit_lease_conflict()` as the admission evidence source.
4. Require explicit `now` / `timestamp` input for expiry decisions.
5. Release or revoke leases on task completion, cancellation, rejection, and
   failure where existing scheduler state already exposes those transitions.
6. Persist lifecycle evidence through existing scheduler history or a narrow
   lease event log.
7. Add focused runtime orchestration tests over acquire, blocked acquire,
   review-required acquire, deterministic expiry, release, and replay/readback
   expectations.

Recommended non-goals:

1. Do not implement real filesystem or process sandbox enforcement.
2. Do not add a real Docker / worktree / remote VM provider.
3. Do not add Host UX binding.
4. Do not add MCP readback unless needed for focused validation.
5. Do not make write-back query live scheduler state.
6. Do not mutate ExchangeArtifact admission semantics.
7. Do not mutate agent-owned Local Work Trajectory from scheduler code.
8. Do not use ambient wall-clock time inside replay-sensitive logic.

## Deferred Direction Order

Recommended order after Candidate A:

1. `Sandbox Mount Binding Over Acquired Leases`
2. `Host UX / MCP Lease Readback`
3. `Lifecycle Host UX Readback / Control Binding`
4. `Real Sandbox Provider Spike`
5. `Real Background Daemon Host`
