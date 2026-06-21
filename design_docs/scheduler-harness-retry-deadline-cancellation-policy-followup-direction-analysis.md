# Scheduler Harness Retry Deadline Cancellation Policy Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-scheduler-harness-retry-deadline-cancellation-policy.md`
closed with deterministic cancellation, deadline, and explicit retry policy
over the bounded scheduler daemon harness.

Review evidence:

- `review/scheduler-harness-retry-deadline-cancellation-policy-2026-06-21.md`

## Current Position

The backend scheduler/orchestration line now has:

1. durable scheduler snapshot and event-log replay / compaction;
2. bounded daemon tick and daemon loop;
3. lifecycle control file plus CLI/MCP lifecycle control surfaces;
4. bounded host-managed scheduler daemon process harness;
5. host-owned retry / deadline / cancellation policy over harness attempts;
6. git-worktree sandbox receipt workflow and cleanup evidence products.

The policy layer is intentionally deterministic and bounded. It has no sleeps,
no real watcher, no OS service, no MCP surface, and no Host UX binding yet.

## Candidate A - MCP Surface For Policy-Controlled Harness

### Goal

Expose `run_scheduler_daemon_harness_with_policy()` through MCP so Codex and
other MCP hosts can run bounded policy-controlled cycles without shelling out
to the CLI.

### Why Useful

The scheduler lifecycle family already has CLI/MCP pairs. This would make the
new policy result shape available from the same host-neutral interaction layer
and support agent-driven bounded retries with explicit cancellation/deadline
inputs.

### Boundary

Keep fake-runtime-only behavior, explicit paths, bounded attempts, and no
projection refresh or cleanup side effects.

## Candidate B - Host-Managed Daemon Supervisor Contract

### Goal

Define a thin host supervisor contract around repeated policy-controlled
harness invocations.

### Why Useful

The current policy wrapper runs immediately and deterministically. A supervisor
contract could later own scheduling cadence, process lifecycle, cancellation
source, and operator-readable status while keeping runtime execution bounded
and testable.

### Boundary

Do not implement OS service installation, filesystem watching, or unbounded
daemon behavior in the first slice. Start with contract and fake/runtime tests.

## Candidate C - Agent Home / Context Session Binding

### Goal

Bind agent home / scratch governance products to scheduler runtime sessions and
policy-controlled harness attempts.

### Why Useful

Persistent and temporary agent storage need lifecycle hooks before larger agent
clusters can run safely. Harness attempt boundaries are now explicit enough to
serve as context-session lifecycle anchors.

### Boundary

Do not mix storage lifecycle with MCP/Host UX binding in the first slice.

## Recommendation

Default to Candidate A if the next priority is Codex/MCP dogfood over the
completed policy result shape.

My current preference is Candidate A:

```text
MCP Surface For Policy-Controlled Harness
```

Reason:

1. the policy result shape is already stable enough for operator invocation;
2. CLI is available, but Codex mainline should not need to shell out for this
   scheduler control surface;
3. MCP exposure can remain narrow and fake-only, matching existing lifecycle
   precedent;
4. supervisor and agent-home binding are deeper runtime design questions that
   will benefit from a host-neutral invocation surface first.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-21-scheduler-harness-policy-mcp-surface.md`

Suggested first slice:

1. add MCP tool input/output mapping for the policy-controlled harness;
2. keep fake-runtime-only and explicit path fields;
3. add focused MCP tests for cancel/deadline preflight and one executed attempt;
4. preserve no Host UX, no projection refresh, no cleanup, no live provider,
   and no Local Work Trajectory mutation from scheduler code.
