# Scheduler Operator Multi-Lane Dogfood Fixture Follow-Up Direction Analysis

> Date: 2026-06-19
> Status: direction analysis

## Context

The completed planning gate:

- `design_docs/stages/planning-gate/2026-06-19-scheduler-operator-multilane-dogfood-fixture.md`

Review evidence:

- `review/scheduler-operator-multilane-dogfood-fixture-2026-06-19.md`

## Current Position

The scheduler operator dogfood surface now has two deterministic fixtures:

1. `simple` fixture: two tasks on one lane.
2. `multilane` fixture: four fake-runtime tasks across api/data/client/qa
   lanes, with fan-in dependencies and scheduler projection readback.

Both fixtures remain ExchangeArtifact admission candidates until an operator
explicitly admits them. The richer fixture has already passed the shared
`schedulerOperatorWorkflow` path through backend, CLI, and MCP.

## Candidate A - Host UX Reuse Of Unified Workflow

### Shape

Replace VS Code Scheduler Operator panel choreography with the shared backend
workflow surface while keeping explicit operator controls. Use the multi-lane
fixture as the UI validation sample.

### Pros

1. Reduces duplicated command choreography in the Host UX layer.
2. Makes Codex/MCP and VS Code/Copilot behavior converge around the same
   workflow contract.
3. The multi-lane fixture gives UI validation a meaningful topology.

### Risks

1. Touches UI and therefore requires screenshot validation.
2. May expose layout/readability issues that should be handled as UI follow-up,
   not workflow-contract churn.

### Fit

High for the next product-facing slice. The backend sample is now strong enough
to test the UI path.

## Candidate B - Fixture-Driven Scheduler Projection Readability Review

### Shape

Use the multi-lane fixture to inspect only the scheduler-derived trajectory
projection model and document any readability/layout gaps before changing UI.

### Pros

1. Keeps work backend/model-focused.
2. Can isolate whether confusing display comes from projection semantics or
   front-end rendering.

### Risks

1. Produces less immediate product simplification than Candidate A.
2. May duplicate evidence gathered naturally during Host UX binding.

### Fit

Medium. Useful if UI readability issues appear during Candidate A.

## Candidate C - Credentialed Provider Smoke Over Multi-Lane Fixture

### Shape

Run a host-owned credentialed Qoder smoke over a scheduler path that mirrors the
multi-lane topology and read the resulting evidence through Host Evidence
presentation.

### Pros

1. Moves beyond fake-runtime confidence.
2. Tests provider permission/evidence seams under a richer topology.

### Risks

1. Environment-dependent.
2. Requires explicit credential readiness and host authorization.
3. Should not be mixed with UI simplification or fixture-contract expansion.

### Fit

Later. Valuable, but not the next deterministic product slice.

## Recommendation

Choose Candidate A next:

> Host UX Reuse Of Unified Workflow

Reasoning:

1. The unified workflow is already stable across backend, CLI, and MCP.
2. The multi-lane fixture now gives a deterministic sample for UI validation.
3. Reusing the shared workflow in Host UX reduces drift between Codex/MCP and VS
   Code/Copilot surfaces.

## Proposed Next Planning Gate

```text
2026-06-19-scheduler-operator-host-ux-unified-workflow-binding.md
```

Recommended acceptance:

1. Host UX uses the shared scheduler operator workflow surface instead of
   duplicating step choreography where practical.
2. Existing explicit operator controls remain clear.
3. The multi-lane fixture is used for validation.
4. Screenshot-style UI validation is performed before close.
5. No live provider execution or background daemon lifecycle is introduced.
