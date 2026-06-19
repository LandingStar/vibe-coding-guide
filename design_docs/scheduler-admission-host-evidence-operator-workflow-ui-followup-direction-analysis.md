# Scheduler Admission Host Evidence Operator Workflow UI Follow-Up Direction Analysis

> Date: 2026-06-19
> Status: direction analysis

## Context

The completed planning gate:

- `design_docs/stages/planning-gate/2026-06-19-scheduler-admission-host-evidence-operator-workflow-ui.md`

Review evidence:

- `review/scheduler-admission-host-evidence-operator-workflow-ui-2026-06-19.md`

## Current Position

The VS Code progress preview now has a Scheduler Operator section that can:

1. inspect stored ExchangeArtifact admission candidates;
2. show scheduler state/event readback when the scheduler snapshot exists;
3. admit an exact candidate through the existing CLI;
4. run a bounded fake-runtime scheduler loop through the existing CLI;
5. refresh scheduler-derived trajectory projection through the existing CLI;
6. show Host Evidence readback beside the workflow.

The current repository state is empty for this workflow: no ExchangeArtifact
store, no admission ledger, no scheduler snapshot, and no host evidence cards.

## Candidate A - Operator Workflow Dogfood Fixture

### Shape

Add a small controlled fixture or helper prompt that creates one
ExchangeArtifact scheduler-admission candidate in a target workspace, then walks
the operator through the UI sequence:

```text
candidate -> admit -> bounded fake loop -> projection refresh -> host evidence readback
```

### Pros

1. Proves the new UI binding over a real candidate instead of only a rendered
   HTML fixture.
2. Keeps provider execution fake and bounded.
3. Gives users a repeatable smoke path for the product surface.

### Risks

1. Needs careful wording so fixture creation is clearly test/demo data.
2. Must not hide admission behind automatic mutation if the goal is UI
   operation validation.

### Fit

High. This is the most direct next step for product confidence.

## Candidate B - MCP/Host Unified Operator Action Surface

### Shape

Add a backend workflow resource or MCP action that packages inspect/admit/run
project/readback as a structured host workflow result while still requiring
explicit action parameters.

### Pros

1. Reduces VS Code-side CLI glue.
2. Makes other hosts able to reuse the same operator workflow.

### Risks

1. Starts shifting from Host UX glue into Portable Runtime API design.
2. Needs a separate contract for multi-host action semantics.

### Fit

Medium. Useful after the current UI workflow has one full dogfood pass.

## Candidate C - Real Provider / Qoder Smoke

### Shape

Use the host-owned scheduler loop projection workflow with a credentialed Qoder
runtime once environment readiness is confirmed.

### Pros

1. Validates real runtime provider behavior over the evidence chain.
2. Produces real-provider Host Evidence.

### Risks

1. Environment-dependent.
2. Does not solve repeatable product workflow testing.

### Fit

Later, after dogfood fixture confidence.

## Recommendation

Choose Candidate A next:

> Operator Workflow Dogfood Fixture

Reasoning:

1. The UI binding now exists, but the current workspace has no candidate to
   exercise it.
2. A repeatable fake-runtime fixture gives the operator workflow a product-level
   smoke path without introducing real-provider risk.
3. Only after that smoke path is stable should the workflow be lifted into a
   shared MCP/backend action surface.

## Proposed Next Planning Gate

```text
2026-06-19-scheduler-operator-workflow-dogfood-fixture.md
```

Recommended acceptance:

1. Create or document a controlled scheduler-admission candidate fixture.
2. Validate the UI sequence over that fixture.
3. Preserve explicit admission/run/project actions.
4. Keep real-provider execution and background daemon lifecycle out of scope.
