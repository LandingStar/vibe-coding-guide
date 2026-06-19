# Agent Orchestration After Release Evidence Direction Analysis

> Date: 2026-06-20
> Status: direction analysis

## Context

The full release evidence line is now closed:

- `design_docs/stages/planning-gate/2026-06-20-full-release-electron-smoke-evidence-run.md`
- `review/full-release-electron-smoke-evidence-run-2026-06-20.md`

The project can return to the agent orchestration line without mixing release
validation work into scheduler design.

Relevant orchestration baseline documents:

- `design_docs/agent-runtime-layering-and-orchestration-slice-plan.md`
- `design_docs/agent-coordination-exchange-artifact-design-record.md`
- `design_docs/qoder-runtime-adapter-requirements.md`
- `design_docs/host-owned-qoder-smoke-runner-helper-followup-direction-analysis.md`
- `design_docs/host-evidence-ui-binding-followup-direction-analysis.md`

## Current Position

The orchestration layer is no longer only a sketch. Existing slices already
cover:

1. runtime adapter contract, fake runtime, mockable Qoder seam, and host-owned
   Qoder wrapper helper;
2. scheduler state, dependency readiness, edit lease and sandbox metadata,
   JSON snapshot persistence, and JSONL scheduler event history;
3. exact-version `ExchangeArtifact` scheduler admission;
4. bounded scheduler tick and repeated bounded daemon loop;
5. host-injected fake / mock-Qoder scheduler loop;
6. scheduler-loop evidence, evidence presentation, Host UX binding, and
   scheduler-derived Local Work Trajectory projection;
7. release-grade Electron smoke evidence for the scheduler projection UI.

The highest-risk remaining gap is persistence discipline under long-running
or repeated orchestration. The code has `recover_scheduler_state()` and
`write_compacted_scheduler_snapshot()`, but compaction currently preserves the
source event log and does not define event-log truncation, rotation, checkpoint
markers, or replay boundaries after compaction.

This matters before a real background daemon or larger agent cluster because a
long-lived scheduler will otherwise accumulate unbounded logs and ambiguous
recovery expectations.

## Candidate A - Scheduler Event-Log Compaction And Replay Hardening

### Shape

Define and implement a narrow persistence hardening slice around existing
scheduler snapshots and JSONL event logs.

Expected scope:

1. define a compaction result contract that states which snapshot was written,
   which source event log was read, and which replay boundary was established;
2. add a non-lossy rotation or archival step for compacted scheduler events;
3. make recovery behavior explicit when both a compacted snapshot and remaining
   post-compaction event log exist;
4. keep strict / non-strict recovery behavior readable in errors and evidence;
5. add focused tests over replay-before-compaction, compacted snapshot readback,
   rotated log readback, unknown event handling, and idempotent no-op behavior.

### Pros

1. Strengthens the scheduler authority store before any longer-lived daemon.
2. Directly addresses a repeatedly deferred gap in existing orchestration docs.
3. Does not depend on Qoder credentials, UI state, or real sandbox providers.
4. Gives later daemon/service work a safer crash-recovery foundation.

### Risks

1. Naming must be precise so "compaction" is not mistaken for deleting history.
2. Rotation policy can grow too broad if it tries to solve retention,
   redaction, or remote storage at the same time.

### Fit

High. This is the best immediate backend slice after release evidence closure.

## Candidate B - Background Scheduler Daemon Lifecycle Protocol

### Shape

Define a real background service lifecycle over the existing bounded daemon
loop: start, heartbeat, cancellation, pause/resume, shutdown, stale-run
detection, and operator readback.

### Pros

1. Moves toward actual agent-cluster operation.
2. Makes scheduler control feel like a service rather than a manual command.

### Risks

1. Larger scope than persistence hardening.
2. Requires stronger recovery semantics before it is comfortable.
3. Can pull in process supervision, host UX, and cancellation policy all at
   once.

### Fit

Later. This should follow Candidate A unless there is an urgent operator need
for a background service.

## Candidate C - Edit Lease Conflict Policy Expansion

### Shape

Upgrade `EditScopeLease` from metadata into a richer conflict policy surface:
overlap classification, lease acquisition/expiration, write-intent checks, and
merge-gate routing.

### Pros

1. Important before high-concurrency agent writes.
2. Ties directly to authority-doc protection and merge safety.

### Risks

1. More valuable after scheduler persistence is durable enough to survive
   conflict-heavy runs.
2. Could couple to sandbox and write-back policy if not scoped tightly.

### Fit

Medium-high, but second after compaction/replay hardening.

## Candidate D - Real Sandbox Provider Spike

### Shape

Select a first real sandbox provider candidate, such as git worktree, Docker,
E2B, Daytona, or a remote VM, and bind it behind the existing
`SandboxProvider` contract.

### Pros

1. Necessary before high-risk or large-scale real agents.
2. Converts current shared-process metadata into enforceable isolation.

### Risks

1. Environment and dependency heavy.
2. Should not be mixed with scheduler persistence changes.
3. Provider choice needs its own security and operational review.

### Fit

Later. It deserves a separate investigation-to-gate path.

## Candidate E - Runtime Subagent Policy

### Shape

Define how runtime-internal subagents, especially Qoder subagents, are reported
back to project-level scheduler artifacts without automatically becoming
project lanes or Local Work Trajectory lanes.

### Pros

1. Clarifies a known boundary before richer runtime usage.
2. Prevents runtime subagent behavior from silently bypassing scheduler
   authority.

### Risks

1. Mostly policy/design until real provider usage produces concrete examples.
2. Could be premature before persistence and edit-lease hardening.

### Fit

Useful soon, but not the next implementation slice.

## Recommendation

Choose Candidate A next:

> Scheduler Event-Log Compaction And Replay Hardening

Reasoning:

1. Release evidence is closed, so the next line should return to orchestration
   core rather than UI or packaging.
2. The scheduler already has bounded loop and host-injected execution paths.
3. Long-running orchestration will stress event history before it stresses
   advanced UX.
4. Compaction/replay hardening is deterministic, local, and testable without
   credentials.

## Proposed Next Planning Gate

```text
2026-06-20-scheduler-event-log-compaction-and-replay-hardening.md
```

Recommended acceptance:

1. Define compaction / rotation / recovery boundary before implementation.
2. Preserve scheduler snapshot as the task-contract authority.
3. Keep event logs as replay and audit material, not task-contract creation
   authority.
4. Add focused tests for compacted snapshot plus post-compaction log recovery.
5. Add readable error messages for replay-boundary mismatches and unsupported
   event shapes.
6. Do not add background daemon service lifecycle, real provider execution,
   real sandbox providers, UI binding, ExchangeArtifact lifecycle mutation, or
   Local Work Trajectory mutation from scheduler code.

## Deferred Direction Order

Recommended order after Candidate A:

1. `Background Scheduler Daemon Lifecycle Protocol`
2. `Edit Lease Conflict Policy Expansion`
3. `Runtime Subagent Policy`
4. `Real Sandbox Provider Spike`

This ordering keeps the scheduler authority store solid before increasing
concurrency, runtime autonomy, or isolation complexity.
