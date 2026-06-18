# Credentialed Live Qoder Rerun Over Presentation Resources Follow-up Direction Analysis

## Completed Boundary

`design_docs/stages/planning-gate/2026-06-18-credentialed-live-qoder-rerun-over-presentation-resources.md`
has reached `COMPLETED`.

The current boundary proves:

1. The active host remains readiness-negative for live Qoder execution:
   `qoder_agent_sdk` is not importable and `QODER_PERSONAL_ACCESS_TOKEN` is not
   present.
2. `QoderSDKQueryClient.validate_host_ready()` fails closed before scheduler
   execution.
3. `dbc://host-evidence/bundle` can be inspected and honestly reports an empty
   bundle.
4. `dbc://host-evidence/presentation` can be inspected and honestly reports
   `status=empty`.
5. No Qoder smoke snapshot, evidence JSON, or scheduler-derived trajectory
   projection was written.

Evidence review:

- `review/credentialed-live-qoder-rerun-over-presentation-resources-2026-06-18.md`

## Candidate A — Qoder Host Provisioning Check Guide

Do what:

1. Document the host-local steps needed to make `qoder_agent_sdk` importable in
   the intended runtime.
2. Document credential expectations without storing token values.
3. Add a repeatable readiness-check command that prints only booleans and stable
   error kinds.
4. Keep SDK installation and credential provisioning outside project commits.

Why now:

The live path is blocked by host environment readiness, not by project contract
shape. A guide/checklist would make the next live rerun less ad hoc.

## Candidate B — Host Evidence Preview UI Binding

Do what:

1. Add a focused host evidence tab or panel to the progress preview surface.
2. Consume `dbc://host-evidence/presentation` or the equivalent host-side
   helper.
3. Show empty, degraded, failed, permission-review, and completed states.
4. Validate with screenshot-based tooling.

Why not automatic:

The worktree still contains unrelated VS Code/UI dirty files. This is the most
product-visible next step, but it should only start when that branch is
intentionally in scope.

## Candidate C — Presentation Resource Timestamp Polish

Do what:

1. Decide whether `dbc://host-evidence/presentation` should include a generated
   timestamp.
2. If yes, add a deterministic host/resource timestamp policy and focused tests.

Why not first:

The empty/live-resource semantics are already usable. Timestamp polish is a
small product refinement, not a blocker.

## Candidate D — Scheduler Daemon / Durable Queue

Do what:

1. Define polling, retry, cancellation, timeout, and event-log rotation.
2. Promote the one-shot host runner toward durable scheduler operation.
3. Feed daemon outcomes into evidence and presentation surfaces.

Why not first:

Daemon semantics are a larger orchestration commitment. The host environment
and UI/operator visibility surfaces should be stronger before this expansion.

## Current Recommendation

Recommended next gate:

```text
Qoder Host Provisioning Check Guide
```

Reason: the current blocker is concrete host readiness, while the project
resource contracts are already functioning. A narrow guide/check slice would
prepare the next live rerun without mixing in the unrelated UI dirty branch.
