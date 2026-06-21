# Host-Managed Scheduler Daemon Process Harness Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-host-managed-scheduler-daemon-process-harness.md`
closed with a bounded host-managed scheduler daemon process harness and a
minimal CLI smoke.

Review evidence:

- `review/host-managed-scheduler-daemon-process-harness-2026-06-21.md`

## Current Position

The backend scheduler/orchestration line now has:

1. scheduler state, dependency, context, edit lease, and sandbox profile
   objects;
2. durable scheduler snapshot and event-log replay / compaction;
3. bounded daemon tick / loop;
4. lifecycle control file and CLI/MCP lifecycle control surfaces;
5. bounded host-managed harness over lifecycle run-once;
6. git-worktree sandbox receipt workflow and cleanup evidence products.

The harness is intentionally local, bounded, fake-runtime by default, and not a
Host UX surface.

## Candidate A - MCP Surface For Host-Managed Harness

### Goal

Expose the harness through MCP so Codex and other MCP hosts can run bounded
host-managed cycles without shelling out to the CLI.

### Why Useful

The project has established CLI/MCP pairs for scheduler lifecycle surfaces.
Harness MCP would make the new loop reachable from the same host-neutral
interaction layer.

### Why Not Automatic

MCP exposure would make it easier for agents to run scheduler cycles. It should
therefore preserve fake-runtime-only default behavior and explicit path inputs.

## Candidate B - Retry / Deadline / Cancellation Policy Over Harness Results

### Goal

Define retry, timeout, deadline, and cancellation semantics over lifecycle and
harness stop reasons.

### Why Useful

The harness now provides a real repeated-cycle result surface. That makes it a
better foundation for policy than extending the earlier run-once surface.

## Candidate C - Agent Home / Context Session Binding

### Goal

Bind agent home / scratch governance products to scheduler runtime sessions and
harness-driven cycles.

### Why Useful

Persistent and temporary private storage need visible lifecycle hooks before
larger agent clusters can run safely.

## Recommendation

Default to Candidate A if the next priority is Codex/MCP dogfood. Default to
Candidate B if the next priority is scheduler robustness.

My current preference is Candidate B:

```text
Retry / Deadline / Cancellation Policy Over Harness Results
```

Reason:

1. the CLI already gives an operator path for harness use;
2. adding MCP now would mostly mirror CLI plumbing;
3. retry/deadline/cancellation policy is a deeper scheduler capability and will
   shape later MCP/Host UX surfaces;
4. agent home/session binding is important but should wait until lifecycle
   outcomes and failure policy are more explicit.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-21-scheduler-harness-retry-deadline-cancellation-policy.md`

Suggested first slice:

1. define policy request fields and result summary over existing harness stop
   reasons;
2. cover retry count, deadline timestamp, and cancellation precedence in
   deterministic tests;
3. keep runtime provider fake-only and no Host UX/MCP changes in the first
   policy slice.
