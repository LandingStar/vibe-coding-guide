# Scheduler Operator Unified Workflow Surface Follow-Up Direction Analysis

> Date: 2026-06-19
> Status: direction analysis

## Context

The completed planning gate:

- `design_docs/stages/planning-gate/2026-06-19-scheduler-operator-unified-workflow-surface.md`

Review evidence:

- `review/scheduler-operator-unified-workflow-surface-2026-06-19.md`

## Current Position

The scheduler operator path now has a host-neutral workflow surface:

```text
inspect candidates
optional exact admission
optional bounded fake loop with evidence
optional scheduler projection refresh
Host Evidence presentation readback
```

The workflow is available through:

- backend helper `run_scheduler_operator_workflow()`;
- MCP `schedulerOperatorWorkflow`;
- CLI `doc-based-coding scheduler operator-workflow`.

The surface keeps mutation flags explicit and returns ordered per-step status.

## Candidate A - Multi-Lane Scheduler Fixture

### Shape

Add a second deterministic dogfood fixture that creates a scheduler-admission
candidate with multiple lanes and at least one cross-lane dependency or fan-in.
Then validate it through `schedulerOperatorWorkflow`.

### Pros

1. Exercises the newly unified workflow over a topology closer to future
   multi-agent scheduling.
2. Gives projection/UI work a stronger sample than the current two-task chain.
3. Stays fake-runtime-only and deterministic.

### Risks

1. May expose projection layout/readability issues that are adjacent to, but
   not part of, workflow contract.
2. Needs careful naming so it does not replace the simpler fixture.

### Fit

High. The unified surface is stable enough; the next useful signal is a richer
repeatable scheduler sample.

## Candidate B - Host UX Simplification Over Unified Workflow

### Shape

Replace VS Code Scheduler Operator panel choreography with the unified backend
workflow call while preserving existing explicit controls.

### Pros

1. Reduces duplicated CLI glue in the Host UX layer.
2. Makes Codex/MCP and VS Code/Copilot behavior converge.

### Risks

1. Touches UI and therefore requires screenshot validation.
2. Best done after a richer fixture exists so UI validation has a meaningful
   topology.

### Fit

Medium. Important, but better after Candidate A gives the UI a stronger test
shape.

## Candidate C - Credentialed Qoder Smoke Over Workflow Evidence

### Shape

Use host-owned runtime injection to run a credentialed Qoder scheduler loop and
read the resulting evidence through the same Host Evidence presentation chain.

### Pros

1. Produces real-provider evidence over the operator workflow product path.
2. Tests runtime permission/evidence seams under realistic conditions.

### Risks

1. Environment-dependent.
2. Requires explicit credential and host permission handling.
3. Should not be mixed with fake-runtime workflow contract expansion.

### Fit

Later. Valuable evidence, but not the next contract foundation.

## Recommendation

Choose Candidate A next:

> Multi-Lane Scheduler Fixture

Reasoning:

1. `schedulerOperatorWorkflow` now gives one stable execution/readback surface.
2. The current dogfood fixture is intentionally minimal and mostly linear.
3. A deterministic multi-lane fixture will test scheduler projection,
   dependency readback, and Host Evidence presentation without needing live
   provider credentials.

## Proposed Next Planning Gate

```text
2026-06-19-scheduler-operator-multilane-dogfood-fixture.md
```

Recommended acceptance:

1. Add a deterministic fake-runtime multi-lane scheduler-admission fixture.
2. Keep the existing simple dogfood fixture unchanged.
3. Validate the new fixture through `schedulerOperatorWorkflow`.
4. Preserve fake-runtime-only execution and explicit mutation flags.
5. Do not bind UI or run live providers in the same gate.
