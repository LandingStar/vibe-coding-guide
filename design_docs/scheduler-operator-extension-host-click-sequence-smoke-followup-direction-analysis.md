# Scheduler Operator Extension-Host Click Sequence Smoke Follow-Up Direction Analysis

> Date: 2026-06-19
> Status: direction analysis

## Context

Completed planning gate:

- `design_docs/stages/planning-gate/2026-06-19-scheduler-operator-extension-host-click-sequence-smoke.md`

Review evidence:

- `review/scheduler-operator-extension-host-click-sequence-smoke-2026-06-19.md`

## Current Position

The Scheduler Operator Host UX now has a testable click/message contract seam:

- webview-shaped `schedulerOperatorAction` messages are coerced by a shared
  helper;
- the panel and workflow runner both reuse that helper;
- the executable smoke covers `Admit -> Run bounded loop -> Refresh projection`
  and verifies each step maps to `doc-based-coding scheduler operator-workflow`
  with one explicit action flag.

This is intentionally lighter than a full Electron extension-host runner. It
targets the brittle Host UX contract boundary without adding environment-heavy
automation.

## Candidate A - Scheduler Projection Readability Review

### Shape

Use the deterministic multi-lane Scheduler Operator fixture to inspect the
scheduler-derived trajectory projection and record whether unreadability comes
from backend projection semantics, Local Work Trajectory mapping, or front-end
layout.

### Pros

1. Addresses the next likely product risk after click/message contract drift.
2. Keeps visual model issues separate from provider/runtime execution.
3. Can produce a narrow UI or projection-model follow-up instead of guessing.

### Risks

1. May require screenshot-heavy iteration.
2. Could expose a need for a front-end model refactor that should not be
   mixed into scheduler workflow plumbing.

### Fit

High if the next objective is product readability and operator usability.

## Candidate B - Full Electron Extension-Host Runner

### Shape

Add a heavier `@vscode/test-electron` smoke that opens the extension host, uses
the actual command/webview path, and verifies Scheduler Operator action
feedback in a seeded temp workspace.

### Pros

1. Provides stronger confidence in actual VS Code extension-host behavior.
2. Can catch workspace path, Python resolution, and webview lifecycle issues.

### Risks

1. More environment-sensitive and slower than the current Node smoke.
2. Requires careful cleanup and stable fixture seeding.
3. Should not be mixed with projection readability or provider execution.

### Fit

Medium. Worth adding before release hardening if extension-host regressions are
suspected, but not the cheapest next product increment.

## Candidate C - Credentialed Provider Smoke

### Shape

Run a host-authorized credentialed provider smoke adjacent to Scheduler Operator
workflow, using explicit host-owned runtime injection and durable evidence.

### Pros

1. Moves confidence beyond fake runtime.
2. Exercises permission, evidence, and provider seams.

### Risks

1. Environment and credential dependent.
2. Should remain isolated from Host UX validation and projection readability.

### Fit

Later. Valuable once the fake-runtime operator path is visually and
semantically clear.

## Recommendation

Prefer Candidate A next. The click/message contract is now covered enough for
near-term iteration, while the remaining user-facing uncertainty is whether
the scheduler-derived trajectory projection is readable and meaningful for
multi-lane operator work.
