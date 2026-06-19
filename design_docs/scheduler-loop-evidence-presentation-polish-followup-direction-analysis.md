# Scheduler Loop Evidence Presentation Polish Follow-Up Direction Analysis

> Date: 2026-06-19
> Status: direction analysis

## Context

The scheduler loop evidence presentation polish slice improved
`dbc://host-evidence/presentation` for `scheduler_loop_evidence`.

Latest implementation review:

- `review/scheduler-loop-evidence-presentation-polish-2026-06-19.md`

## Current Position

The read-only presentation surface can now show:

1. runtime provider;
2. host surface;
3. host invocation id;
4. tick/run/event counts;
5. final queue counts;
6. scheduler projection path/role/refreshed state when evidence provides it;
7. authority clues for scheduler state, provider execution, projection refresh,
   and Local Work Trajectory mutation.

The remaining gap is that host loop projection workflow evidence does not yet
durably carry projection path/summary metadata. The workflow result has those
clues, but the evidence artifact may not.

## Candidate A - Host Loop Workflow Evidence Metadata

### Shape

Extend `run_host_authorized_scheduler_daemon_loop_and_refresh_projection()` so
that when it writes `scheduler_loop_evidence`, the evidence metadata includes
projection clues from the composed workflow:

1. scheduler projection path;
2. projection summary or selected compact fields;
3. scheduler projection role;
4. workflow surface marker.

### Pros

1. Makes read-only host evidence presentation useful after an actual composed
   host workflow run.
2. Reuses the presentation polish just completed.
3. Keeps execution and presentation authority separated.

### Risks

1. Requires care because evidence is written before projection refresh in the
   current helper flow unless the helper changes ordering or rewrites evidence.
2. Must avoid bloating evidence with full trajectory JSON.

### Fit

High. This is the strongest next backend slice.

## Candidate B - UI Binding

### Shape

Bind the improved host evidence presentation JSON into the VS Code UI.

### Pros

1. Makes evidence visible in the product surface.
2. Builds on a cleaner presentation contract.

### Risks

1. Requires screenshot validation.
2. Current worktree has unrelated UI dirt.
3. UI binding is more useful after actual host workflow evidence carries
   projection clues durably.

### Fit

Medium, but should follow Candidate A.

## Candidate C - Live Credentialed Provider Smoke

### Shape

Run the host loop projection workflow against live Qoder when credentials and
SDK are available.

### Pros

1. Produces real-provider evidence over the composed workflow and presentation
   surface.

### Risks

1. Environment dependent.
2. Not necessary for the metadata/presentation contract.

### Fit

Low for immediate next work.

## Candidate D - Background Daemon Lifecycle Protocol

### Shape

Define lifecycle, cancellation, heartbeat, and durability rules for a real
background scheduler daemon/service.

### Pros

1. Moves toward a long-lived orchestration service.

### Risks

1. Much larger scope.
2. Premature before evidence/readback products are stable.

### Fit

Later, separate direction.

## Recommendation

Choose Candidate A:

> Host Loop Workflow Evidence Metadata

Reasoning:

1. Presentation now has a place to show projection clues.
2. The composed host workflow already knows projection path and summary.
3. A narrow metadata slice can bridge the two without introducing UI,
   provider execution, or daemon lifecycle scope.

## Proposed Next Planning Gate

```text
2026-06-19-host-loop-workflow-evidence-metadata.md
```

Recommended acceptance:

1. Preserve `scheduler_loop_evidence` schema version and compactness.
2. Add projection path/summary clues to metadata only when the host workflow
   writes evidence.
3. Keep presentation read-only.
4. Do not add provider execution, UI binding, background daemon lifecycle,
   scheduler state mutation beyond the bounded loop, ExchangeArtifact/admission
   mutation, or Local Work Trajectory mutation.

## Deferred Candidates

1. UI Binding.
2. Live credentialed provider smoke.
3. Background daemon/service lifecycle protocol.
