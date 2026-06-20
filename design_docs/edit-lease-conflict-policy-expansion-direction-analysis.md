# Edit Lease Conflict Policy Expansion Direction Analysis

> Date: 2026-06-20
> Status: direction analysis

## Context

The scheduler lifecycle and operator surfaces are now closed:

- `design_docs/stages/planning-gate/2026-06-20-scheduler-event-log-compaction-and-replay-hardening.md`
- `design_docs/stages/planning-gate/2026-06-20-background-scheduler-daemon-lifecycle-protocol.md`
- `design_docs/stages/planning-gate/2026-06-20-scheduler-daemon-lifecycle-cli-mcp-surface.md`
- `review/scheduler-daemon-lifecycle-cli-mcp-surface-2026-06-20.md`

The next orchestration risk is no longer whether the scheduler can persist,
run a bounded loop, or expose lifecycle control. The next risk is whether the
scheduler can make safe, explainable decisions when multiple tasks or agents
want overlapping edit authority.

Relevant baseline documents:

- `design_docs/agent-orchestration-after-release-evidence-direction-analysis.md`
- `design_docs/agent-runtime-layering-and-orchestration-slice-plan.md`
- `design_docs/agent-cluster-scheduling-and-isolation-investigation.md`
- `docs/subagent-management.md`
- `docs/core-model.md`

## Current Implementation Baseline

The project already has multiple related but separate guard surfaces:

1. Scheduler task metadata:
   - `ContextScope`
   - `EditScopeLease`
   - `SandboxProfile`
2. Scheduler admission:
   - `evaluate_task_admission()`
   - `_first_edit_lease_conflict()`
3. Parallel subgraph preflight:
   - child `allowed_artifacts` normalization;
   - overlap blocking;
   - same-artifact `shared_review_zone_id` exception;
   - `overlap_decisions` evidence.
4. Write-back planning:
   - payload paths are normalized under project root;
   - payloads outside `contract.allowed_artifacts` are skipped;
   - grouped child write-back can distinguish `all_clear` and
     `shared-review-zone-approved` eligibility.
5. Sandbox metadata:
   - `SharedProcessSandboxProvider` can expose lease-scoped visible mounts;
   - real filesystem/process enforcement is still deferred.

The current scheduler-level conflict check is intentionally coarse:

1. read leases do not conflict;
2. a proposed write lease checks only against `ready` / `running` tasks;
3. conflicts are detected by exact `allowed_artifacts` set intersection;
4. directory/file containment is not classified at scheduler level;
5. `denied_artifacts`, `conflict_policy`, `expires_at`, and `review-zone` are
   data fields, but not active policy;
6. there is no reusable lease-conflict decision object shared by scheduler
   admission, subgraph preflight, and write-back planning.

That is enough for a skeleton, but weak for higher concurrency.

## Problem

Edit authority now appears in at least three forms:

1. scheduler `EditScopeLease`;
2. subgraph child `allowed_artifacts`;
3. write-back `contract.allowed_artifacts`.

These surfaces currently agree at the instruction level but not through a
shared machine-level policy object. That creates several risks:

1. two schedulable tasks may be blocked or allowed for reasons different from
   subgraph preflight;
2. final write-back may enforce a path boundary that scheduler admission did
   not classify;
3. `review-zone` is a declared mode but not a clear scheduler routing decision;
4. lease expiry exists as a string but has no deterministic interpretation;
5. future real sandbox providers will need mount and write boundaries that
   match scheduler lease decisions;
6. conflict evidence is currently a string reason instead of a structured
   result that UI, MCP, review docs, and tests can inspect.

The next slice should improve policy coherence before adding stronger real
isolation.

## Candidate A - Shared Lease Conflict Classifier

### Shape

Introduce a scheduler-owned, pure classifier for edit lease relationships.

Expected contract:

```text
EditLeaseConflictDecision
- state: compatible | waiting | review_required | blocked
- classification:
  - no_overlap
  - exact_path_overlap
  - directory_contains_file
  - directory_overlap
  - denied_artifact_hit
  - expired_lease
  - unsupported_policy
  - review_zone_overlap
- left_task_id
- right_task_id
- left_lease_id
- right_lease_id
- left_path
- right_path
- reason
```

Recommended first behavior:

1. normalize lease paths with the same project-relative safety rule used by
   write-back planning;
2. distinguish exact path overlap from directory containment;
3. make read/read and read/write compatibility explicit;
4. make write/write overlap blocked by default;
5. route `review-zone` overlap to `review_required`, not automatic run;
6. treat unsupported `conflict_policy` values as blocked with clear errors;
7. keep `expires_at` visible but do not implement clock-based expiry unless a
   deterministic `now` is passed.

### Pros

1. Small, local, and testable.
2. Directly improves scheduler admission evidence without changing runtime
   execution.
3. Can be reused later by subgraph preflight and write-back planning.
4. Keeps real sandbox and process isolation deferred.
5. Gives UI/MCP a structured explanation surface later.

### Risks

1. If it immediately rewires every caller, the slice may grow too wide.
2. If expiry is implemented with ambient current time, tests and replay become
   non-deterministic.
3. If `review-zone` semantics are too permissive, it can accidentally become
   automatic merge permission.

### Fit

High. This is the recommended next planning gate.

## Candidate B - Lease Acquisition And Expiration Lifecycle

### Shape

Add explicit acquisition / release / renewal state around edit leases:

```text
lease_requested
lease_acquired
lease_waiting
lease_released
lease_expired
```

This would turn `EditScopeLease` from static task metadata into a scheduler
resource with lifecycle events.

### Pros

1. Moves closer to long-running multi-agent scheduling.
2. Helps with daemon crash recovery and stale task cleanup.
3. Gives cancellation / shutdown a concrete resource cleanup target.

### Risks

1. Larger than the immediate classifier gap.
2. Needs deterministic time and replay behavior.
3. Can pull in daemon lifecycle, cancellation, sandbox cleanup, and UI readback.

### Fit

Later. It should consume the classifier from Candidate A.

## Candidate C - Write-Back Enforcement Unification

### Shape

Make write-back planning consume the same lease policy used by scheduler
admission. The write-back engine would receive a lease decision or active lease
context, then decide whether each payload is planned, skipped, review-routed,
or blocked.

### Pros

1. Closes the gap between "task was allowed to run" and "payload may be
   written".
2. Reduces duplicated path normalization and allowed-artifact logic.
3. Gives grouped child write-back stronger evidence for mixed outcomes.

### Risks

1. Write-back currently supports dry-run and direct planning surfaces that do
   not always know scheduler state.
2. If done before the classifier is stable, it may hard-code premature
   scheduler assumptions into PEP write-back.

### Fit

Second. Useful immediately after Candidate A.

## Candidate D - Sandbox Mount Binding

### Shape

Bind active edit leases to `SandboxRequest.required_mounts` /
`SandboxAllocation.visible_mounts`, and reject runtime execution when sandbox
allocation cannot represent the lease safely.

### Pros

1. Moves edit leases from advisory metadata toward execution isolation.
2. Prepares git-worktree / docker / remote-vm providers.
3. Connects scheduler policy to real agent execution risk.

### Risks

1. `SharedProcessSandboxProvider` is metadata-only, so this cannot yet enforce
   filesystem isolation.
2. Real provider choice is security and environment heavy.
3. Too broad if mixed with lease acquisition or write-back unification.

### Fit

Later. It should follow classifier and write-back unification.

## Candidate E - Host UX / MCP Lease Readback

### Shape

Expose lease conflict decisions and active lease summaries through MCP resources
or Host UX.

### Pros

1. Improves operator diagnosis when tasks block.
2. Helps users understand why multi-line scheduler runs do not advance.

### Risks

1. Premature before the decision object exists.
2. UI can become noisy if conflict classifications are not stable.

### Fit

Later. It should consume backend decision evidence.

## Recommendation

Choose Candidate A next:

> Edit Lease Conflict Classifier And Admission Evidence

Reasoning:

1. The scheduler now has durable state, compaction, lifecycle control, and
   CLI/MCP read-write surfaces, so the next concurrency bottleneck is edit
   authority safety.
2. Existing code already has `EditScopeLease` and basic blocking, but lacks a
   reusable policy result.
3. A pure classifier gives the project a stable seam before lease lifecycle,
   write-back enforcement, sandbox mounts, or UI readback.
4. It keeps the next gate small enough to validate with local tests and without
   credentials, live providers, UI, or real sandboxes.

## Proposed Next Planning Gate

```text
2026-06-20-edit-lease-conflict-classifier-and-admission-evidence.md
```

Recommended scope:

1. Add a pure edit lease conflict classifier and result dataclass.
2. Normalize project-relative lease paths safely.
3. Distinguish exact path overlap, directory containment, denied-artifact hits,
   read/write compatibility, unsupported policies, and review-zone overlap.
4. Integrate the classifier into scheduler admission only.
5. Preserve existing default behavior for simple write/write exact overlap.
6. Add focused tests for scheduler admission evidence and path classification.
7. Update review/status docs after validation.

Recommended non-goals:

1. Do not add persistent lease acquisition / release / renewal lifecycle.
2. Do not implement ambient-time lease expiration.
3. Do not bind real sandbox providers or filesystem enforcement.
4. Do not change write-back execution semantics yet.
5. Do not add Host UX or MCP readback for leases yet.
6. Do not change ExchangeArtifact admission semantics.
7. Do not mutate agent-owned Local Work Trajectory from scheduler code.

## Deferred Direction Order

Recommended order after Candidate A:

1. `Write-Back Enforcement Unification`
2. `Lease Acquisition And Expiration Lifecycle`
3. `Sandbox Mount Binding`
4. `Host UX / MCP Lease Readback`
5. `Real Sandbox Provider Spike`
