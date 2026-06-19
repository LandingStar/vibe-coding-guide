# Exchange Artifact Admission State Projection Follow-Up Direction Analysis

> Date: 2026-06-19
> Status: direction analysis

## Context

The admission-state projection slice closed the immediate read-model gap after
MCP admission. `dbc://exchange-artifacts/bundle` now exposes per-version
`admission_state` derived from the durable admission ledger.

Latest implementation review:

- `review/exchange-artifact-admission-state-projection-2026-06-19.md`

Current admission workflow:

1. `doc-based-coding resources read dbc://exchange-artifacts/bundle`
2. `admitExchangeArtifact` or
   `doc-based-coding scheduler admit-exchange-artifact`
3. `doc-based-coding scheduler inspect-admissions`
4. `doc-based-coding resources read dbc://exchange-artifacts/bundle`
5. `doc-based-coding scheduler inspect-state`
6. `doc-based-coding scheduler project`

## Current Position

The chain now has:

1. Durable ExchangeArtifact store.
2. Read-only stored-artifact candidate inspection.
3. Exact-version CLI admission.
4. Exact-version MCP admission.
5. Durable local admission ledger.
6. Read-only ledger inspection.
7. Ledger-derived admission-state projection on the artifact bundle.
8. Read-only scheduler state inspection and explicit scheduler projection.

This is a reasonable stop point for the admission surface. The next meaningful
backend gap is no longer "can an artifact be admitted safely"; it is "how does
queued scheduler work advance under durable, bounded, host-authorized control."

## Candidate A - Scheduler Daemon / Durable Queue Readiness

### Shape

Define the smallest daemon-ready scheduler loop contract without immediately
opening real-provider execution.

Minimum expected behavior:

1. Define a durable queue / daemon state read model around scheduler snapshot
   and event log.
2. Define bounded tick semantics over already-submitted scheduler tasks.
3. Preserve fake-runtime-only execution for first validation, or make execution
   fully injectable from a host-owned runtime.
4. Record stop reasons, retry/cancellation placeholders, and authority clues.
5. Keep provider execution, Qoder credentials, UI binding, and sandbox policy
   expansion as separate follow-up gates unless explicitly admitted.

### Pros

1. Moves the orchestration layer beyond admission into controlled progress.
2. Builds directly on the scheduler snapshot/event-log authority.
3. Lets future multi-agent scheduling work dogfood against a durable loop.

### Risks

1. Broader than read-only admission slices.
2. Needs clear stop-policy and host-authorization boundaries.
3. Can accidentally become real-provider work unless fake/injected runtime
   limits are explicit.

### Fit

High. This is the strongest next backend slice after completing admission
read/write/readback coverage.

## Candidate B - Host Evidence / Scheduler Admission UI Binding

### Shape

Bind exchange artifact candidates, admission state, scheduler readback, and
host evidence presentation into the VS Code / host UX layer.

### Pros

1. Improves operator visibility immediately.
2. Existing read resources are now suitable UI inputs.

### Risks

1. UI work must use screenshot validation.
2. Current worktree has unrelated UI dirt; keep this separate from backend
   daemon contract work.

### Fit

Useful, but not the best next backend slice.

## Candidate C - Exchange Artifact Store Lifecycle Mutation

### Shape

Write consumed/admitted lifecycle state into the exchange artifact store or a
dedicated lifecycle ledger.

### Pros

1. Could make lifecycle queries simpler.
2. Might help future cleanup/archive workflows.

### Risks

1. Blurs read-model projection with source-of-truth mutation.
2. Admission ledger already covers duplicate and audit semantics.

### Fit

Lower priority. Keep as a separate contract-first gate if cleanup/archive
pressure appears.

## Candidate D - Provider Execution / Qoder Runtime Recheck

### Shape

Return to live Qoder readiness once the host environment is provisioned.

### Pros

1. Converts scheduler tasks into live runtime evidence.
2. Exercises the runtime adapter layer.

### Risks

1. Depends on external host credentials and optional SDK availability.
2. Should not be mixed into daemon-readiness if the daemon contract itself is
   not stable.

### Fit

Conditional. Revisit when host readiness is available.

## Recommendation

Choose Candidate A:

> Scheduler Daemon / Durable Queue Readiness

Reasoning:

1. Stored-artifact admission now has a complete safe loop: inspect, admit,
   audit, and inspect projected admission state.
2. The next orchestration bottleneck is durable scheduler advancement, not more
   admission metadata.
3. A daemon-readiness gate can stay narrow if it starts with fake or injected
   host runtime and explicitly defers real-provider authorization and UI.

## Proposed Next Planning Gate

```text
2026-06-19-scheduler-daemon-durable-queue-readiness.md
```

Recommended acceptance:

1. Define daemon/tick contract before implementation.
2. Reuse scheduler snapshot and event log as authority.
3. Preserve explicit host/runtime authorization boundaries.
4. Cover bounded fake-runtime or injected-runtime advancement in tests.
5. Return compact state/progress/readback clues for future UI and host
   surfaces.
6. Do not add real Qoder/provider execution, UI binding, exchange artifact
   lifecycle mutation, or Local Work Trajectory mutation unless a later gate
   explicitly authorizes it.

## Deferred Candidates

1. Host Evidence / Scheduler Admission UI Binding.
2. Provider Execution / Qoder Runtime Recheck.
3. Exchange artifact store lifecycle mutation.
4. Rich scheduler daemon retry/cancellation policy beyond first readiness
   slice.
