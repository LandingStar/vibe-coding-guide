# Scheduler Projection Readability Review Follow-Up Direction Analysis

> Date: 2026-06-19
> Status: direction analysis

## Context

Completed planning gate:

- `design_docs/stages/planning-gate/2026-06-19-scheduler-projection-readability-review.md`

Review evidence:

- `review/scheduler-projection-readability-review-2026-06-19.md`

## Current Position

The deterministic multi-lane Scheduler Operator fixture now produces a
readable scheduler-derived Local Work Trajectory projection:

- fan-in merge projection events sort before their target task events;
- scheduler-state projection lanes sort by earliest projected scheduler task
  event order;
- full-fit scheduler projection rendering is stable in screenshot validation;
- backend and frontend focused validation passed.

This closes the first product-readability pass over fake-runtime multi-lane
scheduler projection.

## Candidate A - Extension-Host Scheduler Projection Lifecycle Smoke

### Shape

Use a narrow VS Code extension-host smoke to open the actual Progress Graph
Preview surface in a seeded temporary workspace and verify the operator path can
refresh and display the scheduler projection without relying only on static
HTML harnesses.

### Pros

1. Covers actual VS Code webview lifecycle, command invocation, and resource
   path resolution.
2. Builds directly on the now-readable projection and existing Host UX workflow
   tests.
3. Keeps provider execution fake-runtime-only while strengthening release-grade
   UI confidence.

### Risks

1. More environment-sensitive than Node and static screenshot tests.
2. Needs careful workspace cleanup and deterministic artifact paths.
3. Should remain separate from live Qoder/provider execution.

### Fit

High when the next priority is release confidence for the Scheduler Operator UI
surface.

## Candidate B - Larger Scheduler Projection Readability Fixture

### Shape

Create a larger deterministic scheduler fixture with more tasks, lanes, and
dependencies, then review projection readability and layout behavior without
adding provider execution.

### Pros

1. Exercises visual density and lane ordering beyond the current four-lane
   fixture.
2. Can expose whether projection readability needs aggregation, filtering, or
   detail-on-demand.
3. Avoids environment-heavy extension-host automation.

### Risks

1. May pull the work toward broader Local Work Trajectory visual design.
2. Could generate UI requirements that should become their own contract-first
   planning gate.

### Fit

Medium. Useful if the current four-lane projection looks good but the next
concern is scale rather than integration lifecycle.

## Candidate C - Credentialed Provider Scheduler Smoke

### Shape

Run a host-authorized credentialed provider smoke adjacent to Scheduler
Operator workflow and durable evidence.

### Pros

1. Starts validating behavior beyond fake runtime.
2. Exercises permission, evidence, and runtime adapter seams.

### Risks

1. Credential and environment dependent.
2. Should not be mixed with projection readability or extension-host lifecycle
   validation.
3. Failures may be runtime/provider issues rather than Scheduler Operator UI
   issues.

### Fit

Later. It is valuable after the fake-runtime Host UX lifecycle has stronger
coverage.

## Recommendation

Prefer Candidate A next. The projection is now readable in a deterministic
static harness, so the next highest confidence gap is whether the actual VS Code
extension-host surface can perform the same refresh/display loop reliably.
Keep Candidate B as the scale-readability follow-up and Candidate C as a
separate credentialed-runtime line.
