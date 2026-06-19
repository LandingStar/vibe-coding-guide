# Host Evidence UI Binding Follow-Up Direction Analysis

> Date: 2026-06-19
> Status: direction analysis

## Context

The Host Evidence UI Binding slice made the VS Code progress graph preview
consume the existing read-only `dbc://host-evidence/presentation` resource.

Latest implementation review:

- `review/host-evidence-ui-binding-2026-06-19.md`

## Current Position

The current chain now has:

1. scheduler daemon-loop execution contracts;
2. durable scheduler-loop evidence;
3. host workflow projection refresh;
4. compact projection metadata in evidence;
5. read-only host evidence presentation;
6. VS Code preview visibility for that presentation.

The major remaining gap is operation flow: users can inspect host evidence, but
the product does not yet provide a guided inspect -> admit -> run -> evidence ->
projection workflow in one place.

## Candidate A - Scheduler Admission And Host Evidence Operator Workflow UI

### Shape

Add a narrow operator workflow surface that keeps the same authority split:

1. inspect stored ExchangeArtifact scheduler-admission candidates;
2. run explicit admission;
3. run bounded scheduler advancement through approved host-owned surfaces;
4. refresh projection;
5. show host evidence readback.

### Pros

1. Turns the existing backend chain into a coherent operator workflow.
2. Reuses the host evidence panel as readback instead of adding another JSON
   inspection step.
3. Keeps mutation surfaces explicit and auditable.

### Risks

1. Larger UI/host interaction slice than Host Evidence display.
2. Requires careful command gating so the UI does not blur read-only and
   mutation authority.
3. Needs screenshot validation and probably command-level tests.

### Fit

High when the next goal is product operation.

## Candidate B - Live Credentialed Provider Smoke

### Shape

Run the host loop projection workflow with a credentialed Qoder provider once
host readiness is available.

### Pros

1. Validates real runtime provider behavior over the completed evidence chain.
2. Produces real-provider durable evidence and UI-visible readback.

### Risks

1. Environment dependent.
2. Does not by itself improve operator workflow ergonomics.

### Fit

Medium. Best when credentials and Qoder SDK readiness are confirmed.

## Candidate C - Background Daemon Lifecycle Protocol

### Shape

Define long-running scheduler daemon lifecycle, heartbeat, cancellation,
durability, and recovery.

### Pros

1. Moves orchestration closer to persistent service operation.
2. Builds on bounded loop and durable evidence work.

### Risks

1. Larger architecture scope.
2. Premature if operator workflow and real-provider evidence remain thin.

### Fit

Later, separate design node.

## Recommendation

If staying product-facing, choose Candidate A next:

> Scheduler Admission And Host Evidence Operator Workflow UI

Reasoning:

1. Host Evidence readback is now visible.
2. The missing piece is the operational chain around that readback.
3. The next UI slice should expose explicit mutation boundaries rather than
   silently adding provider execution or daemon lifecycle.

If the next priority shifts back to runtime confidence, choose Candidate B only
after Qoder readiness is confirmed.

## Proposed Next Planning Gate

```text
2026-06-19-scheduler-admission-host-evidence-operator-workflow-ui.md
```

Recommended acceptance:

1. Define UI command boundaries before implementation.
2. Keep read-only inspection, scheduler admission, scheduler advancement, and
   projection refresh as distinct authority surfaces.
3. Reuse the Host Evidence panel for readback.
4. Include focused tests and screenshot validation.
5. Keep background daemon lifecycle and live-provider smoke out of scope unless
   explicitly promoted.
