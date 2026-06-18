# ExchangeArtifact Admission Ledger Follow-Up Direction Analysis

> Date: 2026-06-19
> Status: direction analysis

## Context

The admission ledger slice completed the durable local audit layer for exact
stored-artifact scheduler admission.

Latest implementation review:

- `review/exchange-artifact-admission-ledger-2026-06-19.md`

Current operator workflow:

1. `doc-based-coding resources read dbc://exchange-artifacts/bundle`
2. `doc-based-coding scheduler admit-exchange-artifact`
3. `doc-based-coding scheduler inspect-admissions`
4. `doc-based-coding scheduler inspect-state`
5. `doc-based-coding scheduler project`

## Current Position

The chain now has:

1. Read-only stored-artifact candidate inspection.
2. Exact-version CLI admission into scheduler snapshot/event-log state.
3. Durable local admission ledger with duplicate detection.
4. Read-only admission-ledger inspection.
5. Read-only scheduler state readback.
6. Explicit scheduler-derived projection refresh.

This reduces the main audit risk before agent-callable mutation surfaces, but
it still keeps MCP write exposure, daemon loops, provider execution, and UI
binding separate.

## Candidate A - Stored-Artifact MCP Admission Tool

### Shape

Expose an MCP write tool that admits one exact stored scheduler submission
artifact into scheduler state while reusing the admission ledger.

Minimum expected behavior:

1. Require exact `artifact_id` and `version`.
2. Require explicit scheduler snapshot/event-log paths.
3. Default or accept explicit admission ledger path.
4. Reject duplicate exact artifact/version admission by default using the same
   ledger policy as CLI.
5. Accept an explicit duplicate override field distinct from scheduler
   replacement semantics.
6. Return the same authority clues as CLI: submitted task IDs, dependency IDs,
   submission event IDs, ledger path, ledger record ID, duplicate info, and
   non-goals.
7. Do not run providers, refresh projection, mark exchange artifacts consumed,
   or mutate Local Work Trajectory.

### Pros

1. Lets Codex/Copilot hosts admit stored scheduler submissions without shelling
   out to CLI.
2. Now has a durable duplicate/audit layer to lean on.
3. Completes the natural read-resource -> write-tool symmetry for stored
   scheduler submission artifacts.

### Risks

1. Agent-callable scheduler mutation is still a larger trust surface than CLI.
2. Tool permission/review wording must be crisp enough for hosts to expose it
   safely.
3. It should not silently expand into daemon behavior or provider execution.

### Fit

High. This is the strongest next narrow gate after the ledger.

## Candidate B - Exchange Artifact Lifecycle Consumed Marking

### Shape

Add lifecycle or side-ledger semantics that mark stored artifact versions as
consumed/admitted/superseded in a way visible from exchange artifact inspection.

### Pros

1. Improves operator and UI clarity.
2. Makes `dbc://exchange-artifacts/bundle` richer without requiring separate
   admission-ledger inspection.

### Risks

1. Can blur the authority split between exchange store and scheduler state.
2. Needs a careful decision about whether the exchange store itself should be
   mutated or whether lifecycle is projected from the admission ledger.

### Fit

Medium. Valuable, but should follow MCP admission or remain a separate
contract-first slice.

## Candidate C - Scheduler Daemon / Durable Queue

### Shape

Introduce a bounded daemon or repeated runner that evaluates scheduler state
and runs tasks under explicit provider/sandbox policy.

### Pros

1. Moves toward real multi-agent orchestration.
2. Exercises retry, cancellation, timeout, and recovery concerns.

### Risks

1. Still broad relative to the current admission chain.
2. Needs sharper provider authorization and sandbox boundaries.
3. Should not be mixed with first MCP write exposure.

### Fit

Important, but not the next narrow gate.

## Candidate D - Host Evidence / Scheduler Admission UI Binding

### Shape

Bind exchange artifact candidates, admission results, admission ledger state,
scheduler readback, and projection status into a host UI surface.

### Pros

1. Better operator visibility.
2. Existing CLI/resource/readback surfaces are now clean data sources.

### Risks

1. UI work must use screenshot validation.
2. The worktree has unrelated UI dirt and should not be mixed into this
   backend authority line.

### Fit

Useful later. Keep separate.

## Recommendation

Choose Candidate A:

> Stored-Artifact MCP Admission Tool

Reasoning:

1. The ledger was deliberately added before broader mutation surfaces.
2. The next smallest useful mutation surface is an MCP tool that wraps the same
   exact-version admission behavior and returns the same audit clues.
3. A narrow MCP gate can remain contract-first and avoid daemon/provider/UI
   expansion.

## Proposed Next Planning Gate

```text
2026-06-19-stored-artifact-mcp-admission-tool.md
```

Recommended acceptance:

1. Define the MCP tool contract before implementation.
2. Reuse the CLI/runtime exact-version admission path and admission ledger.
3. Prove duplicate admission is rejected before scheduler mutation by default.
4. Prove explicit duplicate override remains separate from scheduler
   `replace_existing` semantics.
5. Return compact authority clues and ledger record IDs.
6. Do not run providers, refresh projection, mutate Local Work Trajectory,
   launch a daemon, bind UI, or mark exchange artifacts consumed.

## Deferred Candidates

1. Exchange Artifact Lifecycle Consumed Marking.
2. Scheduler Daemon / Durable Queue.
3. Host Evidence / Scheduler Admission UI Binding.
4. Provider Execution / Qoder Runtime Recheck.
