# Scheduler Loop Host Evidence Binding Follow-Up Direction Analysis

> Date: 2026-06-19
> Status: direction analysis

## Context

The scheduler loop host evidence binding slice added:

- `SchedulerLoopEvidence`
- `SchedulerLoopEvidenceSummary`
- `build_scheduler_loop_evidence()`
- `write_scheduler_loop_evidence()`
- `read_scheduler_loop_evidence_summary()`
- CLI `scheduler daemon-loop --evidence-id`
- mixed read-only support in `dbc://host-evidence/bundle`
- scheduler-loop cards in `dbc://host-evidence/presentation`

Latest implementation review:

- `review/scheduler-loop-host-evidence-binding-2026-06-19.md`

## Current Position

The scheduler now has:

1. Durable task submission.
2. Stored ExchangeArtifact admission through CLI and MCP.
3. Admission ledger and admission-state projection.
4. One bounded scheduler tick.
5. Bounded repeated scheduler loop.
6. Explicit scheduler-loop evidence writing.
7. Read-only evidence bundle/presentation inspection.
8. Explicit projection refresh after tick/loop.

This still does not run real providers from CLI/MCP. Provider authority remains
behind host-owned Python injection seams.

## Candidate A - Host-Injected Runtime Daemon Loop

### Shape

Allow host-owned Python callers to run `run_scheduler_daemon_loop()` with an
explicit injected runtime registry and write scheduler-loop evidence from that
host path.

Minimum expected behavior:

1. Add a host-authorized loop helper or adapter around
   `run_scheduler_daemon_loop()`.
2. Require explicit host invocation metadata for non-fake providers.
3. Validate mock-Qoder path with an injected runtime registry.
4. Write scheduler-loop evidence when requested.
5. Keep CLI/MCP fake-runtime-only.

### Pros

1. Moves toward real multi-agent orchestration without changing CLI/MCP trust
   boundaries.
2. Uses the evidence product just added.
3. Exercises provider authority, scheduler loop, and readback together.

### Risks

1. Must avoid accidentally exposing real providers through CLI/MCP.
2. Mock-Qoder validation can grow into live credential work if not scoped.

### Fit

High. This is the strongest backend next step now that loop evidence exists.

## Candidate B - Scheduler Loop Evidence Presentation Polish

### Shape

Refine presentation cards, severity, and key facts for scheduler-loop evidence.

### Pros

1. Improves operator/UI readability.
2. Keeps provider authority unchanged.

### Risks

1. Lower leverage before actual host-injected loop runs exist.
2. Can drift into UI binding.

### Fit

Medium. Useful after host-injected loop evidence exists.

## Candidate C - Scheduler Projection After Loop Workflow Polish

### Shape

Improve operator workflow around:

```text
daemon-loop --evidence-id -> resources read -> project
```

### Pros

1. Makes manual validation smoother.
2. Keeps projection refresh explicit.

### Risks

1. Mostly guidance/composition, not a new runtime capability.

### Fit

Medium-low.

## Candidate D - UI Binding

### Shape

Bind `dbc://host-evidence/presentation` cards into the host UI.

### Pros

1. Makes scheduler loop progress visible.
2. The data contract is now ready.

### Risks

1. Requires screenshot validation.
2. Current worktree has unrelated UI dirt; avoid mixing with backend provider
   work.

### Fit

Useful later, separate gate.

## Recommendation

Choose Candidate A:

> Host-Injected Runtime Daemon Loop

Reasoning:

1. The scheduler loop and evidence surfaces now cover fake-runtime operator
   flow.
2. The next backend gap is host-owned non-fake runtime execution under explicit
   authority.
3. Keeping CLI/MCP fake-only while adding Python host injection preserves the
   trust boundary.

## Proposed Next Planning Gate

```text
2026-06-19-host-injected-scheduler-daemon-loop.md
```

Recommended acceptance:

1. Define host-authorized loop request/result before implementation.
2. Require host invocation metadata for non-fake runtime providers.
3. Reuse `run_scheduler_daemon_loop()` internally.
4. Support explicit scheduler-loop evidence writing from host path.
5. Validate fake and mock-Qoder injected runtime paths.
6. Do not expose real providers through CLI/MCP, add UI binding, auto-refresh
   projection, mutate ExchangeArtifact lifecycle, or mutate Local Work
   Trajectory from scheduler code.

## Deferred Candidates

1. Scheduler Loop Evidence Presentation Polish.
2. Scheduler Projection After Loop Workflow Polish.
3. UI Binding.
4. Live credentialed provider execution.

