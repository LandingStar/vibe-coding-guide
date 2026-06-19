# Extension-Host Scheduler Projection Lifecycle Smoke Follow-Up Direction Analysis

> Date: 2026-06-19
> Status: direction analysis

## Context

Completed planning gate:

- `design_docs/stages/planning-gate/2026-06-19-extension-host-scheduler-projection-lifecycle-smoke.md`

Review evidence:

- `review/extension-host-scheduler-projection-lifecycle-smoke-2026-06-19.md`

## Current Position

The Scheduler Operator Host UX now has a narrow executable lifecycle smoke:

- `schedulerOperatorAction` enters a shared lifecycle helper;
- running state is rendered before execution;
- the shared scheduler operator workflow is invoked by the panel adapter;
- success/failure notification is separated from reload;
- reload happens after action completion;
- generated webview HTML exposes Scheduler Trajectory Projection mount metadata
  with `4 lanes / 6 events / 12 relations`.

This closes the first host-facing fake-runtime lifecycle confidence gap without
introducing live providers or a full Electron runner.

## Candidate A - Electron Webview Runner Spike

### Shape

Introduce the narrowest real VS Code Electron test runner for Progress Graph
Preview that opens a temporary workspace, triggers the scheduler operator
projection path, and inspects the actual webview DOM.

### Pros

1. Covers VS Code command registration, webview creation, extension activation,
   and iframe/webview DOM behavior.
2. Turns the current seam smoke into stronger release-grade validation.
3. Can reuse the deterministic multi-lane fixture and existing lifecycle helper.

### Risks

1. More environment-sensitive than current Node tests.
2. May require additional test bootstrapping, workspace cleanup, and CI policy.
3. Should remain fake-runtime-only and must not become a live-provider smoke.

### Fit

High if the next priority is release confidence for the VS Code extension Host
UX lifecycle.

## Candidate B - Larger Scheduler Projection Fixture

### Shape

Create a larger deterministic scheduler fixture with more tasks, lanes,
fan-in/fan-out dependencies, and scheduler-owned merge events, then review
projection readability and trajectory mount behavior.

### Pros

1. Tests whether the current projection remains understandable beyond the
   four-lane fixture.
2. Can expose whether aggregation or filtering is needed before real multi-agent
   scale.
3. Avoids full Electron infrastructure.

### Risks

1. May drift into broad visual-model redesign.
2. Could require separate UI requirements if the current trajectory model becomes
   too dense.

### Fit

Medium. Useful after host lifecycle confidence is adequate or if product review
finds the current four-lane fixture too small.

## Candidate C - Credentialed Provider Scheduler Smoke

### Shape

Run a credentialed host-authorized provider smoke adjacent to scheduler
workflow/evidence/projection surfaces.

### Pros

1. Starts validating non-fake runtime behavior.
2. Exercises provider readiness, permission, evidence, and projection metadata
   together.

### Risks

1. Credential and local-environment dependent.
2. Failures can be provider readiness issues rather than scheduler projection
   issues.
3. Should not be mixed with Electron/webview lifecycle validation.

### Fit

Later. Keep it independent from the Host UX lifecycle line.

## Recommendation

Prefer Candidate A if continuing toward release-grade VS Code extension
confidence. The current seam smoke is deliberately narrow and cheap; the next
unknown is whether a real Electron runner can be kept similarly narrow and
stable. Keep Candidate B as a product readability line and Candidate C as a
separate runtime readiness line.
