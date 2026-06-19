# Host Loop Workflow Evidence Metadata Follow-Up Direction Analysis

> Date: 2026-06-19
> Status: direction analysis

## Context

The Host Loop Workflow Evidence Metadata slice connected the composed host loop
projection workflow to durable `scheduler_loop_evidence` metadata.

Latest implementation review:

- `review/host-loop-workflow-evidence-metadata-2026-06-19.md`

## Current Position

The backend chain now supports:

1. host-authorized bounded daemon-loop execution;
2. optional `scheduler_loop_evidence` writing;
3. scheduler-derived trajectory projection refresh;
4. compact `projection_summary` workflow readback;
5. durable evidence metadata containing projection path/role/refreshed state
   and compact projection summary;
6. read-only host evidence presentation that can display those clues.

The major remaining gap is product visibility: the richer evidence presentation
is still mostly a CLI/MCP resource product, not an operator UI surface.

## Candidate A - Host Evidence UI Binding

### Shape

Bind `dbc://host-evidence/presentation` into the VS Code progress/trajectory
panel or a nearby operator panel.

### Pros

1. Makes scheduler loop evidence visible to users.
2. Reuses an already compact presentation contract.
3. Can show host runtime, invocation, projection, queue, and authority clues
   without recomputing backend state in the UI.

### Risks

1. Requires screenshot validation.
2. Current worktree still has unrelated UI dirty files.
3. UI layout decisions may compete with ongoing graph/trajectory UI work.

### Fit

High as the next product-facing slice once the UI dirty branch is intentionally
entered.

## Candidate B - Live Credentialed Provider Smoke

### Shape

Run the host loop projection workflow with a live credentialed Qoder provider
when host readiness is available.

### Pros

1. Produces real-provider evidence over the completed backend chain.
2. Validates permission grants, injected client behavior, evidence enrichment,
   and presentation under real runtime conditions.

### Risks

1. Environment dependent.
2. Current host readiness has previously been unavailable.
3. Does not improve product visibility by itself.

### Fit

Medium. Valuable when credentials/SDK are available, but not the best default
blocking path.

## Candidate C - Background Daemon Lifecycle Protocol

### Shape

Define long-running scheduler daemon lifecycle, heartbeat, cancellation,
durability, and recovery.

### Pros

1. Moves toward real service orchestration.
2. Builds on bounded loop and evidence products.

### Risks

1. Larger architecture scope.
2. Premature before operator visibility and live-smoke confidence are stronger.

### Fit

Later, separate design node.

## Recommendation

Choose Candidate A when entering product surface work:

> Host Evidence UI Binding

Reasoning:

1. The backend evidence/readback chain is now coherent enough for UI.
2. Users need to inspect host loop evidence without manually reading JSON
   resources.
3. The existing presentation contract is intentionally UI-facing and should be
   exercised by a real host UX layer.

If the immediate goal remains backend orchestration rather than UI, choose
Candidate B only when live Qoder readiness is actually available.

## Proposed Next Planning Gate

```text
2026-06-19-host-evidence-ui-binding.md
```

Recommended acceptance:

1. Consume `dbc://host-evidence/presentation` without duplicating backend
   evidence logic in UI code.
2. Show scheduler-loop runtime, invocation, queue, projection, and authority
   clues.
3. Preserve malformed evidence error rows.
4. Use screenshot validation.
5. Do not add provider execution, daemon lifecycle, ExchangeArtifact/admission
   mutation, or Local Work Trajectory mutation.

## Deferred Candidates

1. Live credentialed provider smoke.
2. Background daemon/service lifecycle protocol.
