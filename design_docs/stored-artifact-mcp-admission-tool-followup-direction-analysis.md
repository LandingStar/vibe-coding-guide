# Stored-Artifact MCP Admission Tool Follow-Up Direction Analysis

> Date: 2026-06-19
> Status: direction analysis

## Context

The stored-artifact MCP admission slice exposed `admitExchangeArtifact`, a
narrow MCP write tool for admitting one exact stored scheduler submission
artifact into scheduler snapshot/event-log state. CLI and MCP now share the
same durable admission-ledger duplicate policy.

Latest implementation review:

- `review/stored-artifact-mcp-admission-tool-2026-06-19.md`

Current admission workflow:

1. `doc-based-coding resources read dbc://exchange-artifacts/bundle`
2. `admitExchangeArtifact` or
   `doc-based-coding scheduler admit-exchange-artifact`
3. `doc-based-coding scheduler inspect-admissions`
4. `doc-based-coding scheduler inspect-state`
5. `doc-based-coding scheduler project`

## Current Position

The chain now has:

1. Read-only ExchangeArtifact store inspection.
2. CLI exact-version scheduler admission.
3. MCP exact-version scheduler admission.
4. Durable local admission ledger with duplicate detection.
5. Read-only admission-ledger inspection.
6. Read-only scheduler state inspection.
7. Explicit scheduler-derived projection refresh.

This is enough for host/agent admission of stored scheduler submissions without
shelling out, while preserving the scheduler snapshot as scheduling authority.

## Candidate A - Exchange Artifact Lifecycle Consumed Projection

### Shape

Expose admitted/consumed state beside exchange artifact inspection by projecting
admission-ledger records onto exact artifact versions.

Minimum expected behavior:

1. Read `.codex/orchestration/exchange-artifacts.json`.
2. Read `.codex/orchestration/exchange-artifact-admissions.json`.
3. For each exact artifact version, report whether it has prior `admitted`,
   `rejected_duplicate`, or `failed` ledger records.
4. Keep the exchange artifact store immutable in the first slice; derive
   lifecycle/admission state from the ledger rather than mutating artifact
   versions directly.
5. Return compact resource/CLI clues suitable for operator and agent
   admission decisions.

### Pros

1. Makes repeated admission risk visible before a write call.
2. Improves `dbc://exchange-artifacts/bundle` usefulness without changing
   scheduler authority.
3. Gives UI and future daemon work a safer read model.

### Risks

1. Needs crisp wording so "consumed" does not imply the exchange store is the
   scheduler authority.
2. If lifecycle state is later written into the store, that should be a
   separate mutation gate.

### Fit

High. This is the narrowest next read-model improvement after MCP admission.

## Candidate B - Scheduler Daemon / Durable Queue

### Shape

Introduce a bounded scheduler loop that can repeatedly drain ready tasks under
explicit runtime provider, sandbox, retry, and stop-policy constraints.

### Pros

1. Moves toward real multi-agent orchestration.
2. Exercises recovery, cancellation, retry, and provider authorization.

### Risks

1. Broader than the current admission line.
2. Needs sandbox/provider policy and host authorization to be more mature.
3. Should not be mixed with exchange artifact lifecycle read-model work.

### Fit

Important, but not the next narrow gate.

## Candidate C - Host Evidence / Scheduler Admission UI Binding

### Shape

Bind exchange artifact candidates, admission ledger state, scheduler readback,
and projection status into a host UI surface.

### Pros

1. Operators can see candidates, admitted state, and scheduler projection in
   one place.
2. Existing read resources and CLI surfaces are now good data sources.

### Risks

1. UI work must use screenshot validation.
2. The current worktree has unrelated UI dirt, so this should stay separate
   from backend authority slices.

### Fit

Useful later. Keep separate until the read model is cleaner.

## Candidate D - Provider Execution / Qoder Runtime Recheck

### Shape

Return to host-owned Qoder readiness/live smoke once the host environment is
provisioned.

### Pros

1. Converts scheduler admission into executable host-runtime evidence.
2. Builds toward the future agent runtime layer.

### Risks

1. Depends on external host credentials and optional SDK availability.
2. Should not be used to expand MCP provider execution prematurely.

### Fit

Conditional on host readiness. Not the default next step.

## Recommendation

Choose Candidate A:

> Exchange Artifact Lifecycle Consumed Projection

Reasoning:

1. MCP admission now makes stored-artifact scheduler mutation agent-callable.
2. The next safety improvement is to make prior admission state visible before
   mutation, not to start daemon execution.
3. A projection/read-model gate can preserve the current authority split:
   admission ledger records are audit authority, scheduler snapshot is
   scheduling authority, and exchange artifact store remains the coordination
   product source.

## Proposed Next Planning Gate

```text
2026-06-19-exchange-artifact-admission-state-projection.md
```

Recommended acceptance:

1. Define exact artifact-version admission state projection contract.
2. Reuse `JsonArtifactVersionStore` and `JsonExchangeArtifactAdmissionLedger`.
3. Expose admitted/rejected/failed counts and latest record clues per exact
   artifact version.
4. Keep the first slice read-only; do not mutate exchange artifact store
   lifecycle fields.
5. Do not run providers, refresh scheduler projection, launch a daemon, bind
   UI, or mutate Local Work Trajectory.

## Deferred Candidates

1. Scheduler Daemon / Durable Queue.
2. Host Evidence / Scheduler Admission UI Binding.
3. Provider Execution / Qoder Runtime Recheck.
4. Exchange artifact store lifecycle mutation.
