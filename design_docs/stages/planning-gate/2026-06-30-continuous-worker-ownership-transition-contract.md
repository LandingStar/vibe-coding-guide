# Planning Gate - Continuous Worker Ownership Transition Contract

Date: 2026-06-30

Status: COMPLETED

## Purpose

This document is the Slice A contract for continuous worker session/lane
ownership. It formalizes state machines, transition tables, invariants, errors,
and follow-up slice boundaries.

This is a documentation-only contract. It does not implement runtime, schema,
CLI, MCP, UI, lease ledger, lane ownership tooling, private storage allocation,
auto compact, or `llm-auto`.

## Source Documents

- `design_docs/stages/planning-gate/2026-06-30-continuous-worker-ownership-state-machine-draft.md`
- `design_docs/stages/planning-gate/2026-06-29-continuous-worker-session-policy.md`
- `design_docs/stages/planning-gate/2026-06-30-opencode-server-api-stage-live-smoke-closure.md`
- `design_docs/agent-home-and-scratch-space-design-record.md`

## Boundary

The existing provider-neutral continuous worker binding layer can already bind
OpenCode delivery to a reusable host session selector and avoid selecting two
tasks with the same binding in one delivery batch. It is not yet a complete
ownership policy.

This contract defines the ownership policy surface without changing code:

1. Lane Ownership State Machine.
2. Worker Binding State Machine.
3. Delivery Lease State Machine.

The three machines are linked by `binding_id`, but each has a separate
authority:

- Lane ownership is scheduler/project policy.
- Worker binding is durable continuity identity and lifecycle.
- Delivery lease is short-lived runtime serialization.

## Recommended Defaults

```text
scope_priority = task > agent > lane > lane_group > session_ledger > none
ownership_activation = after_first_successful_delivery
lease_persistence = durable_compact_lease_ledger
compact_policy_default = auto
manual_compact = explicit_option_with_auto_fallback
llm_auto_compact = future_slice_only
stale_ownership_behavior = keep_ownership_but_suspend_delivery
private_storage = derived_invariant_for_continuous_worker_binding
private_storage_retention = retain_after_owned_lanes_merge
```

## Global Invariants

1. The scheduler remains the source of truth for task readiness, lane
   ownership, and delivery eligibility.
2. Worker/subagent processes must not directly maintain Local Work Trajectory.
   They report progress through worker reports; leader/main/supervisor authority
   consumes those reports.
3. A binding can have at most one active delivery lease at a time.
4. A binding in `compacting`, `stale`, `released`, or `archived` is not
   selectable for new delivery.
5. `stale` does not mean `released`.
6. Lane `suspended` does not mean worker binding `stale`.
7. A `server_api_created` session is not automatically a continuous worker.
   Promotion requires explicit host-owned action in a later slice.
8. No state machine, audit event, compact bundle, lease record, or private
   storage manifest may persist raw transcript text or secret values.
9. Private storage for continuous workers is a derived invariant, not an
   optional boolean capability.
10. Compact policy defaults to `auto`; `manual` is an explicit option but must
    not remove automatic fallback.

## Contract Terms

### Active Delivery Lease

An active delivery lease is a lease in `reserved` or `running`.

### Selectable Binding

A selectable binding is an active continuity candidate whose Worker Binding
state is `ready` or `idle`, whose Lane Ownership state allows delivery, and
which has no active delivery lease.

### Explicit Host-Owned Action

An explicit host-owned action is a leader/main/supervisor/operator action that
mutates durable project state. Runtime provider responses alone are not
host-owned actions.

### Audit Event

An audit event is a compact, secret-safe fact about a state transition. It may
reference artifacts, sessions, compact context refs, worker reports, or exchange
product ids, but it must not embed raw provider transcripts or secret values.

## State Machine 1: Lane Ownership

Lane Ownership maps a lane or lane group to a continuous worker binding.

### States

| State | Definition | Selectable? |
| --- | --- | --- |
| `unowned` | No continuous owner exists for the lane or lane group. | No continuity selection. |
| `claimed` | An owner is claimed, but no successful delivery has activated it. | Only for first validation delivery. |
| `active` | Future eligible work defaults to the owned binding. | Yes, if binding and lease allow. |
| `suspended` | Ownership remains, but new delivery is paused. | No. |
| `transferred` | Ownership moved to a replacement binding. | No for old owner. |
| `released` | Ownership intentionally ended. | No. |

### Allowed Transitions

| From | Action | Required Inputs | To | Audit Event |
| --- | --- | --- | --- | --- |
| `unowned` | `claimLane` | `scope_kind`, `scope_id`, `binding_id`, `worker_id`, `requested_by`, `reason` | `claimed` | `lane_ownership_claimed` |
| `claimed` | `activateOwnership` | `binding_id`, successful `delivery_id`, `task_id` | `active` | `lane_ownership_activated` |
| `claimed` | `releaseOwnership` | `binding_id`, `reason` | `released` | `lane_ownership_released` |
| `claimed` | `transferOwnership` | `binding_id`, `new_binding_id`, `reason` | `transferred` | `lane_ownership_transferred` |
| `active` | `suspendOwnership` | `binding_id`, `reason` | `suspended` | `lane_ownership_suspended` |
| `active` | `transferOwnership` | `binding_id`, `new_binding_id`, `reason` | `transferred` | `lane_ownership_transferred` |
| `active` | `releaseOwnership` | `binding_id`, `reason` | `released` | `lane_ownership_released` |
| `suspended` | `resumeOwnership` | `binding_id`, `reason` | `active` | `lane_ownership_resumed` |
| `suspended` | `transferOwnership` | `binding_id`, `new_binding_id`, `reason` | `transferred` | `lane_ownership_transferred` |
| `suspended` | `releaseOwnership` | `binding_id`, `reason` | `released` | `lane_ownership_released` |
| `transferred` | `archiveOwnership` | `binding_id`, `reason` | `released` | `lane_ownership_archived` |

### Forbidden Transitions

| From | Forbidden Action | Error |
| --- | --- | --- |
| `unowned` | `activateOwnership` | `lane ownership activation rejected: no owner is claimed` |
| `unowned` | `suspendOwnership` | `lane ownership suspend rejected: no owner exists` |
| `claimed` | delivery as fully active owner before first success | `lane ownership not active: first successful delivery is required` |
| `active` | second active lane owner for same lane | `lane ownership conflict: lane already has active owner` |
| `suspended` | delivery selection | `lane ownership not selectable: ownership is suspended` |
| `transferred` | resume old owner | `lane ownership not resumable: ownership was transferred` |
| `released` | resume owner | `lane ownership not resumable: ownership was released` |

### Lane Ownership Errors

Errors must include `lane_id` or `lane_group_id`, `binding_id`, current state,
requested action, and allowed next actions.

Examples:

```text
lane ownership conflict: lane already has active owner lane=lane:server binding=continuous-worker:lane:server
lane ownership not selectable: ownership is suspended lane=lane:server binding=continuous-worker:lane:server allowed=resumeOwnership|transferOwnership|releaseOwnership
```

## State Machine 2: Worker Binding

Worker Binding is the durable continuity record. It links worker identity,
runtime provider, scope, session selector, compact context refs, private storage
refs, and lifecycle facts.

### States

| State | Definition | Selectable? |
| --- | --- | --- |
| `proposed` | Continuity is proposed but no durable binding is claimed. | No. |
| `claimed` | Binding exists with scope, worker id, provider, and optional selector. | Not until `ready`. |
| `ready` | Binding is eligible for delivery. | Yes, if ownership and lease allow. |
| `idle` | Binding remains eligible and has no active lease. | Yes, if ownership allows. |
| `compacting` | Compact context work is in progress. | No. |
| `forked` | A descendant binding was derived from this binding. | Policy-dependent; default old binding remains non-selected until explicitly returned to `ready` or `idle`. |
| `stale` | Binding/session trust is impaired. | No. |
| `released` | Continuity intentionally ended. | No. |
| `archived` | Historical record only. | No. |

`running` is not a durable Worker Binding state. Active execution belongs to
Delivery Lease.

### Allowed Transitions

| From | Action | Required Inputs | To | Audit Event |
| --- | --- | --- | --- | --- |
| none | `proposeBinding` | `scope_kind`, `scope_id`, `worker_id`, `requested_by`, `reason` | `proposed` | `worker_binding_proposed` |
| `proposed` | `claimBinding` | `binding_id`, `worker_id`, `runtime_provider`, `scope`, optional `session_selector`, `private_storage_ref`, `private_storage_policy_ref` | `claimed` | `worker_binding_claimed` |
| none | `claimBinding` | same as above | `claimed` | `worker_binding_claimed` |
| `claimed` | `markReady` | `binding_id`, readiness evidence | `ready` | `worker_binding_ready` |
| `ready` | `markIdle` | `binding_id`, completed or no active lease evidence | `idle` | `worker_binding_idle` |
| `idle` | `markReady` | `binding_id`, reason | `ready` | `worker_binding_ready` |
| `ready` | `requestCompact` | `binding_id`, `compact_policy`, `reason`, threshold evidence if auto | `compacting` | `worker_binding_compact_requested` |
| `idle` | `requestCompact` | same as above | `compacting` | `worker_binding_compact_requested` |
| `compacting` | `finishCompact` | `binding_id`, `compact_context_ref`, summary refs, audit refs | `ready` or `idle` | `worker_binding_compacted` |
| `ready` | `forkBinding` | `binding_id`, `target_scope`, `new_binding_id`, `reason` | `forked` | `worker_binding_forked` |
| `idle` | `forkBinding` | same as above | `forked` | `worker_binding_forked` |
| `ready` | `markStale` | `binding_id`, `reason`, failure or expiry evidence | `stale` | `worker_binding_marked_stale` |
| `idle` | `markStale` | same as above | `stale` | `worker_binding_marked_stale` |
| `stale` | `recoverStale` | `binding_id`, `strategy`, evidence | `ready` or `idle` | `worker_binding_recovered` |
| `stale` | `forkBinding` | `binding_id`, `target_scope`, `new_binding_id`, `reason` | `forked` | `worker_binding_forked` |
| `claimed`/`ready`/`idle`/`stale`/`forked` | `releaseBinding` | `binding_id`, `reason` | `released` | `worker_binding_released` |
| `released` | `archiveBinding` | `binding_id`, `reason` | `archived` | `worker_binding_archived` |

### Forbidden Transitions

| From | Forbidden Action | Error |
| --- | --- | --- |
| `proposed` | delivery selection | `worker binding not selectable: binding is only proposed` |
| `claimed` | delivery selection before `markReady` | `worker binding not selectable: binding is claimed but not ready` |
| `ready`/`idle` | second binding for same active task/lane/agent scope without policy override | `worker binding conflict: active binding already exists for scope` |
| `compacting` | delivery selection | `worker binding not selectable: binding is compacting` |
| `compacting` | `requestCompact` again | `worker binding compact rejected: compaction already in progress` |
| `stale` | delivery selection | `worker binding not selectable: binding is stale` |
| `released` | delivery selection or recovery | `worker binding not selectable: binding is released` |
| `archived` | any active lifecycle action | `worker binding immutable: binding is archived` |
| any | store raw transcript or secret | `worker binding rejected: raw transcript or secret value is not allowed` |
| any | `has_private_storage: true|false` as ownership field | `worker binding schema rejected: private storage is a derived invariant, use refs/policy refs` |

### Private Storage Contract

Continuous worker private storage is not optional at the model level.

Required rules:

1. Continuous worker binding implies private/specialized storage by default.
2. Do not model this as `has_private_storage: true|false`.
3. Use `private_storage_ref` and `private_storage_policy_ref`, or a deterministic
   reference such as:

   ```text
   dbc://agent-home/continuous-worker/{binding_id}
   ```

4. Non-continuous workers still use the explicit request/approval path from
   `design_docs/agent-home-and-scratch-space-design-record.md`.
5. Default retention is `retain_after_owned_lanes_merge`.
6. Retention supports later analysis and framework improvement.
7. Private storage must not contain secrets, raw transcripts, hidden scheduler
   state, unreviewed patches, or unauthorized project copies.

### Compact Contract

Compact policy default is `auto`.

Required rules:

1. `manual` compact is an explicit trigger option.
2. `manual` must not disable automatic fallback.
3. `auto` must prevent a continuous worker from avoiding compaction until it
   harms execution.
4. `llm-auto` is a future slice and is not implemented here.
5. Future `llm-auto` must:
   - use a smaller model to read worker outputs and sent/received exchange
     products;
   - let that model decide compact timing;
   - enforce hard threshold forced compact even when the model declines;
   - record forced compact logs;
   - retain the improvement window from the last model-approved compact to the
     next model-approved compact;
   - support multiple forced compacts between two model-approved compacts;
   - support forced compact after a model-approved compact when no later
     model-approved compact exists yet.

### Worker Binding Errors

Errors must include `binding_id`, scope, current state, requested action, and
allowed next actions.

Examples:

```text
worker binding not selectable: binding is stale binding=continuous-worker:lane:server allowed=recoverStale|forkBinding|releaseBinding
worker binding schema rejected: private storage is a derived invariant, use private_storage_ref/private_storage_policy_ref
compact policy rejected: manual compact cannot disable auto fallback binding=continuous-worker:lane:server
```

## State Machine 3: Delivery Lease

Delivery Lease is the short-lived runtime serialization record for one delivery
attempt through one binding.

### States

| State | Definition | Active? |
| --- | --- | --- |
| `available` | No active lease blocks the binding. | No. |
| `reserved` | Scheduler selected the binding, runtime has not started. | Yes. |
| `running` | Runtime invocation has started. | Yes. |
| `completed` | Delivery completed successfully. | No. |
| `failed_retryable` | Delivery failed and may be retried. | No after release. |
| `failed_terminal` | Delivery failed terminally. | No after release. |
| `expired` | Lease exceeded timeout or host recovered interruption. | No after recovery. |

### Allowed Transitions

| From | Action | Required Inputs | To | Audit Event |
| --- | --- | --- | --- | --- |
| `available` | `reserveLease` | `binding_id`, `task_id`, `delivery_id`, `lease_id`, `reserved_at`, `expires_at` | `reserved` | `delivery_lease_reserved` |
| `reserved` | `beginLeaseRun` | `lease_id`, `started_at`, runtime invocation ref | `running` | `delivery_lease_started` |
| `reserved` | `expireLease` | `lease_id`, `reason`, `observed_at` | `expired` | `delivery_lease_expired` |
| `running` | `completeLease` | `lease_id`, `result_ref`, `completed_at` | `completed` | `delivery_lease_completed` |
| `running` | `failLeaseRetryable` | `lease_id`, `reason`, failure ref | `failed_retryable` | `delivery_lease_failed_retryable` |
| `running` | `failLeaseTerminal` | `lease_id`, `reason`, failure ref | `failed_terminal` | `delivery_lease_failed_terminal` |
| `running` | `expireLease` | `lease_id`, `reason`, `observed_at` | `expired` | `delivery_lease_expired` |
| `failed_retryable` | `releaseLease` | `lease_id`, recovery action ref | `available` | `delivery_lease_released` |
| `completed` | `releaseLease` | `lease_id` | `available` | `delivery_lease_released` |
| `failed_terminal` | `releaseLease` | `lease_id`, policy action ref | `available` | `delivery_lease_released` |
| `expired` | `releaseLease` | `lease_id`, recovery action ref | `available` | `delivery_lease_released` |

### Forbidden Transitions

| From | Forbidden Action | Error |
| --- | --- | --- |
| `available` | `beginLeaseRun` without reservation | `delivery lease start rejected: lease is not reserved` |
| `reserved` | second reservation for same `binding_id` | `delivery lease conflict: binding already has active lease` |
| `running` | second reservation for same `binding_id` | `delivery lease conflict: binding already has active lease` |
| `completed` | `beginLeaseRun` | `delivery lease immutable: lease is completed` |
| `failed_retryable` | delivery retry without release/re-reserve | `delivery lease retry rejected: release and reserve a new lease` |
| `failed_terminal` | retry | `delivery lease retry rejected: failure is terminal` |
| `expired` | resume without recovery decision | `delivery lease expired: recovery decision required` |
| any | persist raw transcript or secret | `delivery lease rejected: raw transcript or secret value is not allowed` |

### Delivery Lease Errors

Errors must include `lease_id` if known, `binding_id`, `task_id`, current state,
requested action, and allowed next actions.

Examples:

```text
delivery lease conflict: binding already has active lease binding=continuous-worker:lane:server lease=lease:42 task=task:server
delivery lease expired: recovery decision required lease=lease:42 allowed=releaseLease|markStale|recoverStale
```

## Cross-Machine Rules

### Selection Rule

Delivery selection resolves continuity in this order:

1. explicit task/session override;
2. active task-scope binding;
3. active agent-scope binding;
4. active lane-scope ownership/binding;
5. active lane-group ownership/binding;
6. older OpenCode session ledger;
7. no continuity.

Selection must then reject the candidate if:

- ownership is `suspended`, `transferred`, or `released`;
- binding is not `ready` or `idle`;
- the binding has an active delivery lease;
- the session selector provider mismatches the binding provider;
- required private storage refs/policy refs are invalid once Slice B defines
  their schema.

### First Success Activation

Lane ownership starts as `claimed`. It becomes `active` only after successful
delivery through the binding. Failed first delivery must not silently activate
ownership.

### Stale Handling

When a binding becomes `stale`:

```text
WorkerBinding: ready/idle -> stale
LaneOwnership: active -> suspended
DeliveryLease: running -> failed_retryable|expired
```

Ownership is preserved but delivery is suspended until recovery, transfer, fork,
release, or fallback is explicit.

### Server/API Created Session

`server_api_created` session metadata is delivery evidence only. It does not
mutate the OpenCode session ledger and does not create a continuous worker
binding. Later Slice E may add explicit host-owned promotion.

### Compacting

When compact starts:

```text
WorkerBinding: ready/idle -> compacting
Delivery selection: blocked for that binding
```

When compact completes:

```text
WorkerBinding: compacting -> ready/idle
compact_context_ref updated
```

Compact events must be secret-safe and should reference compact context bundles
rather than embedding raw worker transcript.

## Follow-Up Slices

### Slice B: Schema Alignment

Extend or add data contracts for:

- lane ownership;
- binding generation;
- durable compact delivery lease records;
- compact policy;
- `private_storage_ref`;
- `private_storage_policy_ref`.

Do not add a boolean field for whether a continuous worker has private storage.
Default ownership is a binding invariant.

### Slice C: Delivery Lease Minimum

Implement the durable compact lease ledger or equivalent audit-backed lease
mechanism so one binding cannot be selected by two concurrent deliveries.

### Slice D: Lane Ownership Tooling

Add host/leader-owned claim, inspect, suspend, resume, transfer, and release
surfaces. Do not invoke providers.

### Slice E: Server/API Session Promotion

Add explicit host-owned promotion from `server_api_created` session metadata to
a continuous worker binding. Do not auto-promote during delivery.

### Slice F: Monitoring Read Model

Expose a read-only state projection for lane ownership, binding lifecycle,
leases, stale/recovery hints, compact context refs, and private storage refs.

### Later: `llm-auto` Compact Policy

Design the model-judged compact policy and forced-compact improvement retention
window. Keep it independent from the first `auto` compact implementation.

## Non-Goals For This Slice

- No Python runtime changes.
- No CLI changes.
- No MCP changes.
- No test changes unless a docs-only check requires it.
- No lease ledger implementation.
- No lane ownership tool implementation.
- No private storage allocation.
- No auto compact implementation.
- No `llm-auto` implementation.
- No UI implementation.

## Completion Evidence

Slice A is complete when:

1. this contract exists and independently describes all three state machines;
2. each state machine has state definitions, allowed transitions, forbidden
   transitions, required inputs, audit events, and error requirements;
3. defaults and global invariants are explicit;
4. private storage is modeled as a continuous-worker binding invariant, not a
   boolean switch;
5. compact defaults to `auto`, `manual` remains an option with fallback, and
   `llm-auto` is deferred;
6. `design_docs/Project Master Checklist.md` points to this contract while
   leaving later implementation slices incomplete;
7. no runtime/schema/CLI/MCP/UI files are touched for this slice;
8. `git diff --check` passes for touched docs, allowing existing LF/CRLF
   warnings only.
