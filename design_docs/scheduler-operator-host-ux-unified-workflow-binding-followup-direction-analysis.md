# Scheduler Operator Host UX Unified Workflow Binding Follow-Up Direction Analysis

> Date: 2026-06-19
> Status: direction analysis

## Context

Completed planning gate:

- `design_docs/stages/planning-gate/2026-06-19-scheduler-operator-host-ux-unified-workflow-binding.md`

Review evidence:

- `review/scheduler-operator-host-ux-unified-workflow-binding-2026-06-19.md`

## Current Position

The Scheduler Operator workflow now has one shared host-neutral operation path:

- backend helper: `tools.progress_graph.run_scheduler_operator_workflow()`
- MCP tool: `schedulerOperatorWorkflow`
- CLI: `doc-based-coding scheduler operator-workflow`
- VS Code Host UX buttons: `scheduler operator-workflow` with explicit action
  flags

The deterministic multi-lane fixture is available for richer operator smoke
tests, and the VS Code panel no longer has a separate admission/loop/projection
command choreography.

## Candidate A - Extension-Host Click Sequence Smoke

### Shape

Run a real VS Code extension-host smoke where a seeded fixture is displayed in
the panel and the three explicit buttons are clicked in sequence.

### Pros

1. Verifies the actual webview message path, not only source-level wiring and
   HTML rendering.
2. Uses the existing deterministic fixture without changing backend contracts.
3. Can catch extension-host environment or Python path resolution issues.

### Risks

1. More environment-sensitive than the current headless HTML screenshot.
2. Requires careful cleanup of temporary workspace state.

### Fit

High as a later product validation slice, but not required to close the current
binding work.

## Candidate B - Scheduler Projection Readability Review

### Shape

Use the multi-lane fixture to inspect scheduler-derived trajectory projection
readability and record model/UI gaps before changing layout.

### Pros

1. Keeps product model issues separate from workflow plumbing.
2. Can reveal whether confusing displays originate in projection semantics or
   front-end rendering.

### Risks

1. Produces less immediate operator automation.
2. May require UI design input if graph readability becomes the bottleneck.

### Fit

Medium. Worth doing before expanding scheduler operator UI controls further.

## Candidate C - Credentialed Provider Smoke

### Shape

Run a host-authorized credentialed Qoder smoke over scheduler operator workflow
or an adjacent host-owned runtime path.

### Pros

1. Moves confidence beyond fake runtime.
2. Exercises evidence, provider, and permission seams.

### Risks

1. Environment-dependent.
2. Should remain separate from UI binding and projection readability.

### Fit

Later. Valuable once the operator surface needs real-provider confidence.

## Recommendation

Prefer Candidate A only when the next objective is release-grade Host UX
validation. If the next objective is product clarity, Candidate B is the better
first cut because the backend/CLI/MCP/Host UX workflow path has now converged
enough and the remaining operator risk is mostly display/readability or real
extension-host integration.
