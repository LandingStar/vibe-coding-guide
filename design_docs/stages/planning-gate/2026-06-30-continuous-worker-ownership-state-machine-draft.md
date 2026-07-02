# Planning Gate Draft - Continuous Worker Ownership State Machines

Date: 2026-06-30

Status: DRAFT

## Context

The OpenCode direct server/API adapter stage is closed. The next recommended
work is continuous worker session/lane ownership policy for long-lived OpenCode
worker contexts.

The repository already has a provider-neutral continuous worker binding layer:

- durable binding ledger;
- compact binding event log;
- lane, lane-group, agent, and task scopes;
- OpenCode delivery-time lookup;
- continuous-worker-first session selector precedence;
- same-binding concurrency exclusion inside one delivery batch;
- compact context bundle references.

That layer is not yet a full ownership policy. The missing design is the
state-machine contract that decides who owns a lane or lane group, when a
worker/session may continue across trajectory nodes, how runtime leases are
serialized, and when a session must be compacted, forked, marked stale,
released, or promoted from a server/API-created session.

## Goal

Define the state-machine contract for continuous worker session/lane ownership
before implementing further schema, CLI, scheduler, runtime, or UI changes.

This draft is meant to be split into smaller `/goal` slices after review. It is
not itself an implementation gate.

## Non-Goals

This draft does not:

1. change runtime code;
2. change the existing binding ledger schema;
3. create or promote provider sessions;
4. implement a worker daemon or long-lived worker pool;
5. expose live provider execution through MCP;
6. give workers Local Work Trajectory mutation authority;
7. store raw transcript text or secret values;
8. replace the scheduler as the source of truth.

## Design Principle

Use three linked state machines instead of one overloaded worker state:

1. Lane Ownership State Machine:
   answers which worker owns a lane or lane group.
2. Worker Binding State Machine:
   answers whether the continuous worker binding is reusable and trustworthy.
3. Delivery Lease State Machine:
   answers whether the scheduler may currently deliver a task through that
   worker without violating serialization.

The machines are connected by `binding_id`, but each machine owns a different
decision boundary.

## State Machine 1: Lane Ownership

Lane ownership is a scheduler/project policy. It maps a lane or lane group to a
continuous worker binding.

### States

```text
unowned
  -> claimed
  -> active
  -> suspended
  -> transferred
  -> released
```

### State Semantics

- `unowned`: the lane or lane group has no continuous worker owner. Tasks use
  one-shot delivery or normal provider selection.
- `claimed`: an ownership record exists, but the worker has not yet completed a
  valid first delivery for this scope.
- `active`: subsequent eligible nodes in this lane or lane group default to the
  same continuous worker binding.
- `suspended`: ownership remains valid, but the scheduler should not deliver new
  work through it until resumed. Typical causes are dependency waits, review
  waits, or manual pauses.
- `transferred`: ownership moved to another binding. The old ownership record is
  kept for audit and should no longer be selected.
- `released`: ownership ended intentionally. Future work must claim a new owner
  or run without continuity.

### Allowed Actions

```text
claimLane(scope, worker_id, binding_id)
activateOwnership(binding_id)
suspendOwnership(binding_id, reason)
resumeOwnership(binding_id)
transferOwnership(binding_id, new_binding_id, reason)
releaseOwnership(binding_id, reason)
```

### Required Invariants

1. One lane may have at most one active lane-scope owner.
2. One lane may be covered by at most one active lane-group owner unless a
   future explicit priority rule resolves the conflict.
3. A task-level binding may override lane ownership only for that task.
4. An agent-level binding may override lane ownership only when the task agent
   matches.
5. `suspended` ownership is not `stale` binding; suspension is a scheduler wait
   condition, not a provider/session trust failure.
6. `transferred` must reference the replacement binding and must be auditable.

## State Machine 2: Worker Binding

Worker binding is the durable continuity record. It describes the worker
identity, provider, scope, session selector, compact context reference, and
lifecycle facts. For a continuous worker, private storage ownership is a
derived invariant of the binding, not an optional boolean capability.

### States

```text
proposed
  -> claimed
  -> ready
  -> idle
  -> compacting
  -> stale
  -> released
  -> archived

ready/idle
  -> forked
```

`running` is intentionally not a durable binding state in this draft. Runtime
execution is represented by Delivery Lease instead, so the binding ledger stays
focused on long-lived lifecycle rather than high-frequency locks.

### State Semantics

- `proposed`: a leader/scheduler decision says continuity should exist, but no
  durable binding/session selector is claimed yet.
- `claimed`: the binding exists and has scope, worker id, runtime provider, and
  optional session selector.
- `ready`: the binding is eligible for delivery.
- `idle`: the binding remains eligible but has no active delivery lease.
- `compacting`: the project is building or attaching a compact context bundle;
  no new delivery should start through this binding until compaction completes.
- `forked`: a new binding was derived from this one. The old binding may stay
  usable, be released, or be archived according to ownership policy.
- `stale`: the binding or provider session is not trustworthy. It must be
  recovered, forked, released, or archived before normal reuse.
- `released`: intentional end of active continuity.
- `archived`: historical record only.

### Allowed Actions

```text
proposeBinding(scope, worker_id)
claimBinding(scope, worker_id, runtime_provider, session_selector)
markReady(binding_id)
markIdle(binding_id)
requestCompact(binding_id, reason)
finishCompact(binding_id, compact_context_ref)
forkBinding(binding_id, target_scope, reason)
markStale(binding_id, reason)
recoverStale(binding_id, strategy)
releaseBinding(binding_id, reason)
archiveBinding(binding_id, reason)
```

### Required Invariants

1. A binding must not be selected for delivery while `compacting`, `stale`,
   `released`, or `archived`.
2. A server/API-created session does not become a continuous worker binding
   unless an explicit host-owned promotion/claim action occurs.
3. Binding records must not store raw transcript text or secret values.
4. Compact context bundles are project-owned summaries and references; they are
   not provider transcript storage.
5. A binding session selector must match the binding runtime provider.
6. Retryable runtime failure may mark the binding `stale`; it should not
   silently release or archive it without an explicit policy action.
7. Forking must create or reference a distinct binding generation.
8. A continuous worker binding implies a private/specialized storage location
   by default. Do not model this as `has_private_storage: true|false`; model
   the location and governance as references such as `private_storage_ref` and
   `private_storage_policy_ref`.
9. The default private storage retention policy is retain-after-owned-lanes-
   merge so the material can support later analysis and framework improvement.
10. Non-continuous workers still use the explicit request/approval path defined
    by the agent home and scratch-space design record.

### Private Storage Reference

The default private storage reference should be deterministic or registry
backed, for example:

```text
dbc://agent-home/continuous-worker/{binding_id}
```

The reference identifies where private notes, rules, documents, and capability
material are governed. It is not permission to store raw transcripts, secrets,
unreviewed patches, hidden scheduler state, or unauthorized project copies.
Policy details such as retention, visibility, promotion review, and secret
scanning belong in `private_storage_policy_ref` or the referenced storage
manifest, not in a worker-binding boolean.

## State Machine 3: Delivery Lease

Delivery lease is a short-lived runtime serialization record. It prevents two
tasks from consuming the same continuous worker/session at the same time.

### States

```text
available
  -> reserved
  -> running
  -> completed

reserved/running
  -> failed_retryable
  -> failed_terminal
  -> expired
```

### State Semantics

- `available`: no active lease blocks this binding.
- `reserved`: the scheduler selected this binding for a task, but runtime
  invocation has not started.
- `running`: runtime invocation has started.
- `completed`: the task delivery finished successfully.
- `failed_retryable`: delivery failed in a way that may be retried; the binding
  may need stale recovery.
- `failed_terminal`: delivery failed in a non-retryable way.
- `expired`: the reservation or run exceeded its lease timeout or the host
  recovered after an interrupted process.

### Allowed Actions

```text
reserveLease(binding_id, task_id, delivery_id)
beginLeaseRun(lease_id)
completeLease(lease_id, result_ref)
failLeaseRetryable(lease_id, reason)
failLeaseTerminal(lease_id, reason)
expireLease(lease_id, reason)
releaseLease(lease_id)
```

### Required Invariants

1. A binding may have at most one active `reserved` or `running` lease.
2. Delivery selection must exclude any task whose resolved binding already has
   an active lease.
3. Lease completion is the only point where delivery may update
   `last_used_at`, reuse audit refs, or compact-needed hints on the binding.
4. Retryable failure should emit both lease failure evidence and a binding
   stale/recovery decision.
5. Lease records must be compact and secret-safe.

## Cross-Machine Flow

### Normal Same-Lane Continuity

```text
LaneOwnership: unowned -> claimed -> active
WorkerBinding: proposed -> claimed -> ready
DeliveryLease: available -> reserved -> running -> completed
WorkerBinding: ready -> idle
```

The next node on the same lane resolves the active ownership, selects the same
binding, and opens a new delivery lease.

### Lane Wait Without Worker Failure

```text
LaneOwnership: active -> suspended
WorkerBinding: idle
DeliveryLease: available
```

No stale marker is emitted because the worker/session is still trustworthy. The
scheduler simply has no deliverable work for that owner.

### Retryable Runtime Failure

```text
DeliveryLease: running -> failed_retryable
WorkerBinding: ready/idle -> stale
LaneOwnership: active remains active unless policy releases/transfers it
```

The next decision is recovery policy: reuse, fork, transfer ownership, release,
or fall back to one-shot delivery.

### Compact Context

```text
WorkerBinding: idle -> compacting -> ready/idle
```

Compaction attaches a project-owned compact context bundle reference. It does
not imply provider transcript persistence.

### Fork New Context

```text
WorkerBinding: ready/idle -> forked
WorkerBinding(new): claimed -> ready
LaneOwnership: active -> transferred, or a new lane/lane-group claims the new binding
```

Forking is used for experiments, new lanes, divergent approaches, or replacing
a stale session while preserving audit lineage.

## Selection Precedence Draft

Delivery-time continuous worker selection should remain deterministic:

1. explicit task/session override;
2. active task-scope binding;
3. active agent-scope binding;
4. active lane-scope ownership/binding;
5. active lane-group ownership/binding;
6. older OpenCode session ledger;
7. no continuity, provider may create a one-shot or server/API session.

Open question: lane-group may need to precede lane in some workflows. The
default above preserves narrow scope before broad scope, but a later gate may
register a scope-priority policy.

## Error Message Requirements

Future implementation gates should use explicit errors that tell the operator
which state machine rejected the action:

- `lane ownership conflict: lane already has active owner ...`
- `worker binding not selectable: binding is stale ...`
- `delivery lease conflict: binding already has active lease ...`
- `server-api-created session cannot be reused as continuous worker until promoted ...`
- `compact context rejected: raw transcript or secret-like field is not allowed ...`

Each error should include the relevant id (`lane_id`, `lane_group_id`,
`binding_id`, `lease_id`, `task_id`) and the allowed next actions.

## UI / Monitoring Implications

The monitoring UI should eventually expose:

1. lane owner badge: none, active, suspended, transferred, released;
2. binding lifecycle badge: ready, idle, compacting, stale, released, archived;
3. active lease indicator: reserved/running task and timeout;
4. compact context ref and last compact time;
5. fork/transfer lineage;
6. stale recovery action hints;
7. conflicts that block concurrent delivery.

This draft does not implement UI. It only defines a read model target.

## Suggested Follow-Up `/goal` Slices

### Slice A: Contract And Transition Table

Write the final contract document with explicit allowed/forbidden transition
tables and examples. No runtime changes.

### Slice B: Schema Alignment

Extend or add data contracts for lane ownership, binding generation, lease
policy, compact policy, and continuous-worker private storage refs/policy refs.
Do not add a boolean field for whether a continuous worker has private storage;
default ownership is a binding invariant. Add validation and focused tests only.

### Slice C: Delivery Lease Minimum

Implement a short-lived lease ledger or in-memory-plus-audit mechanism so one
binding cannot be selected by two concurrent deliveries. Keep runtime behavior
otherwise unchanged.

### Slice D: Lane Ownership Tooling

Add host/leader-owned claim, inspect, suspend, resume, transfer, and release
surfaces. Do not invoke providers.

### Slice E: Server/API Session Promotion

Add explicit host-owned promotion from `server_api_created` session metadata to
a continuous worker binding. Do not auto-promote during delivery.

### Slice F: Monitoring Read Model

Expose a read-only state projection for lane ownership, binding lifecycle,
leases, stale/recovery hints, and compact context refs.

## Recommended Defaults

1. Scope priority defaults to narrow-before-broad:
   `task > agent > lane > lane_group > session_ledger > none`.
2. `claimed` ownership becomes `active` only after the first successful
   delivery through the binding.
3. Delivery leases should be persisted durably, but as compact short-lived
   records rather than full runtime logs.
4. Compact policy default is `auto`. Manual compact remains an explicit option,
   but there must be an automatic fallback so a continuous worker cannot avoid
   compaction until it harms worker execution.
5. `llm-auto` compact policy is future work. In that mode, a smaller model reads
   worker outputs plus sent/received exchange products and decides compact
   timing. A hard threshold must still force compaction even when the model
   declines, and the system must log that forced override.
6. For `llm-auto`, retain the worker outputs and exchange records between the
   last model-approved compact and the next model-approved compact for policy
   improvement. This retention window must handle multiple forced compacts
   between two model-approved compacts, and also the case where forced compacts
   occur after a model-approved compact but no later model-approved compact has
   happened yet.
7. A stale binding should keep lane ownership but automatically suspend delivery
   until recovery, transfer, fork, release, or fallback is explicit.

## Remaining Open Questions

1. What exact thresholds should `auto` use first: event count, estimated token
   budget, elapsed time, output volume, exchange-product count, or a combined
   score?
2. Should forced compact retention for future `llm-auto` keep full exchange
   product references only, or also normalized summaries of each product?
3. How long should forced-compact improvement material be retained after the
   next model-approved compact closes the window?

## Acceptance Criteria For This Draft

This draft is acceptable when it gives enough structure for the next `/goal` to
produce a final transition-table contract without touching runtime code.
