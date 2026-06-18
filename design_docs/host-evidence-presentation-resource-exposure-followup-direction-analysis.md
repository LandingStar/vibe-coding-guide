# Host Evidence Presentation Resource Exposure Follow-up Direction Analysis

## Completed Boundary

`design_docs/stages/planning-gate/2026-06-18-host-evidence-presentation-resource-exposure.md`
has reached `COMPLETED`.

The current boundary now proves:

1. `dbc://host-evidence/bundle` exposes the lower-level robust evidence bundle.
2. `dbc://host-evidence/presentation` exposes host/UI/operator-facing
   presentation JSON.
3. Existing CLI resource inspection can read both URIs.
4. Reads remain provider-free, scheduler-projection-free, and Local Work
   Trajectory-free.
5. Prompt guidance distinguishes bundle vs presentation resources.

Evidence review:

- `review/host-evidence-presentation-resource-exposure-2026-06-18.md`

## Candidate A — VS Code / Preview UI Binding

Do what:

1. Add a focused host evidence tab or panel to the progress preview surface.
2. Consume `dbc://host-evidence/presentation` or its equivalent host-side
   helper rather than binding to raw evidence files.
3. Show status, provider, invocation, outputs, authority clues, and read
   errors.
4. Validate with screenshot-based tooling.

Why now:

The data contract and resource surface are finally stable enough for UI work.
This is the most product-visible next step.

Why not automatic:

The worktree still has unrelated VS Code/UI dirty files. Starting this slice
now is only clean if that branch is intentionally picked up or first cleaned.

## Candidate B — Credentialed Live Qoder Rerun

Do what:

1. Provision optional `qoder-agent-sdk` and host authentication outside
   project commits.
2. Run one bounded `run_host_owned_qoder_smoke()` pass.
3. Inspect generated evidence through both bundle and presentation resources.
4. Record whether the result is live-success, readiness-negative, or
   fail-closed.

Why now:

The inspection surfaces are ready. A live or readiness-negative rerun would
produce stronger end-to-end evidence for the host runtime line without touching
the dirty UI branch.

## Candidate C — Scheduler Daemon / Durable Queue

Do what:

1. Define polling, retry, cancellation, timeout, and event-log rotation.
2. Promote one-shot host runner toward durable scheduler operation.
3. Feed daemon outcomes into evidence and presentation surfaces.

Why not first:

Daemon semantics are a larger orchestration commitment. It is better to first
either show the evidence in UI or prove the real provider path can be inspected.

## Candidate D — Presentation CLI UX Polish

Do what:

1. Add optional table output or filters for presentation cards.
2. Add installation/operator documentation examples.

Why not first:

The existing JSON resource CLI already works. Formatting polish is useful but
less important than UI binding or live-provider validation.

## Current Recommendation

2026-06-18 update: Candidate B was selected and completed as
`design_docs/stages/planning-gate/2026-06-18-credentialed-live-qoder-rerun-over-presentation-resources.md`.
The run was readiness-negative: the active host still lacks both
`qoder_agent_sdk` importability and `QODER_PERSONAL_ACCESS_TOKEN`; bundle and
presentation resources honestly report empty evidence.

Recommended next gate depends on branch cleanliness:

1. If the VS Code/UI dirty branch is intentionally in scope, choose
   `Host Evidence Preview UI Binding`.
2. If the UI branch should remain untouched, choose
   `Credentialed Live Qoder Rerun Over Presentation Resources`.

My default recommendation from the current worktree state is:

```text
Credentialed Live Qoder Rerun Over Presentation Resources
```

Reason: it avoids mixing with unrelated UI dirty files while using the newly
completed bundle and presentation inspection surfaces as end-to-end evidence.
