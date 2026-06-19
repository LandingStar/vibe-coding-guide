# Scheduler Operator Workflow Dogfood Fixture Follow-Up Direction Analysis

> Date: 2026-06-19
> Status: direction analysis

## Context

The completed planning gate:

- `design_docs/stages/planning-gate/2026-06-19-scheduler-operator-workflow-dogfood-fixture.md`

Review evidence:

- `review/scheduler-operator-workflow-dogfood-fixture-2026-06-19.md`

## Current Position

The Scheduler Operator workflow now has a deterministic seed path:

```text
seed -> resources read -> admit -> inspect -> daemon-loop fake -> project -> host-evidence presentation
```

The seed command creates exactly one ExchangeArtifact admission candidate and
keeps all downstream actions explicit. The full workflow is covered by CLI and
runtime tests.

## Candidate A - MCP/Host Unified Operator Workflow Surface

### Shape

Add a shared backend workflow surface that packages operator intent as a
structured request/result:

```text
inspect candidates
admit exact candidate
run bounded fake loop
refresh projection
read Host Evidence presentation
```

The surface should still keep mutations explicit in the request, return the
same authority clues as the individual commands, and avoid real-provider
execution by default.

### Pros

1. Reduces VS Code-specific CLI glue.
2. Gives Codex/MCP and VS Code/Copilot hosts the same operator workflow
   contract.
3. Preserves the now-proven dogfood fixture as a reusable smoke input.

### Risks

1. Needs careful contract design so a convenience workflow does not become
   implicit auto-admission.
2. Should avoid hiding per-step failures; the result needs step-level status.

### Fit

High. The fixture has proven the product path. The next product-quality step is
to lift the sequence into a reusable host-neutral workflow surface.

## Candidate B - Multi-Lane Scheduler Fixture

### Shape

Add a second dogfood fixture with two or more lanes and at least one dependency
across lanes.

### Pros

1. Better exercises scheduler projection layout and UI readability.
2. Provides a stronger sample for future multi-agent scheduling work.

### Risks

1. It expands fixture scope before the operator workflow API is stable.
2. It may conflate scheduler projection readability with operator command
   ergonomics.

### Fit

Medium. Useful soon, but best after the shared operator workflow contract exists.

## Candidate C - Credentialed Qoder Smoke

### Shape

Run the host-owned scheduler daemon loop with a credentialed Qoder runtime and
write Host Evidence over the same projection/readback chain.

### Pros

1. Produces real-provider evidence.
2. Tests the host-owned runtime injection seam under realistic conditions.

### Risks

1. Environment-dependent.
2. Does not reduce workflow duplication across hosts.

### Fit

Later. This is evidence collection rather than the next contract foundation.

## Recommendation

Choose Candidate A next:

> MCP/Host Unified Operator Workflow Surface

Reasoning:

1. The operator flow now has a deterministic candidate and a passing full CLI
   smoke.
2. The largest remaining product friction is that each host must compose the
   same low-level commands itself.
3. A contract-first shared workflow surface can keep explicit mutation authority
   while making Codex/MCP and VS Code/Copilot behavior converge.

## Proposed Next Planning Gate

```text
2026-06-19-scheduler-operator-unified-workflow-surface.md
```

Recommended acceptance:

1. Define a host-neutral request/result contract for the explicit operator
   workflow.
2. Expose the workflow through a backend helper and, if narrow enough, MCP or
   CLI inspection surface.
3. Preserve per-step status, authority clues, and failure isolation.
4. Keep live provider execution, background daemon lifecycle, automatic
   consumed marking, and Local Work Trajectory mutation out of scope.
