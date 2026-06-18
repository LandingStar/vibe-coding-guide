# Planning Gate — Credentialed Live Qoder Rerun Over Presentation Resources

> Date: 2026-06-18
> Status: COMPLETED

## Trigger

`design_docs/stages/planning-gate/2026-06-18-host-evidence-presentation-resource-exposure.md`
has reached `COMPLETED`.

The follow-up direction analysis recommends this next narrow slice:

- `design_docs/host-evidence-presentation-resource-exposure-followup-direction-analysis.md`

## Problem

The project now exposes both host evidence resources:

```text
dbc://host-evidence/bundle
dbc://host-evidence/presentation
```

The remaining question is whether a credentialed host-owned Qoder smoke can now
be inspected through those resources, or whether the current host still fails
closed at SDK/auth readiness. This should be verified without touching the
unrelated VS Code/UI dirty branch and without printing, storing, or committing
credential values.

## Scope

### Slice 1 — Host Readiness Recheck

Check the active Python runtime without exposing secrets:

1. Determine whether `qoder_agent_sdk` is importable.
2. Determine whether `QODER_PERSONAL_ACCESS_TOKEN` is present as a boolean
   only.
3. Call `QoderSDKQueryClient.validate_host_ready()`.
4. Record only project-owned error kind and raw error type.

### Slice 2 — Resource Inspection

Inspect the existing read-only resource surfaces:

```text
doc-based-coding resources read dbc://host-evidence/bundle
doc-based-coding resources read dbc://host-evidence/presentation
```

The resource reads must remain provider-free, scheduler-projection-free, and
Local Work Trajectory-free.

### Slice 3 — Negative Or Live Evidence Classification

If host readiness is satisfied, run one bounded `run_host_owned_qoder_smoke()`
pass and inspect the generated evidence through both resources.

If readiness is not satisfied, record a readiness-negative outcome and prove no
Qoder smoke scheduler snapshot, evidence JSON, or scheduler-derived trajectory
projection was written.

## Non-Goals

This gate does not:

1. Install `qoder-agent-sdk`.
2. Provision or persist Qoder credentials.
3. Expose Qoder execution through MCP.
4. Add a scheduler daemon.
5. Bind VS Code UI to host evidence.
6. Change the bundle or presentation resource contracts.
7. Create fake evidence JSON for a readiness-negative outcome.

## Acceptance Criteria

The gate may close when:

1. Host readiness is checked without credential exposure.
2. The outcome is classified as live-success, readiness-negative, or
   fail-closed.
3. Both bundle and presentation resources are inspected.
4. If readiness is negative, no scheduler/evidence/projection artifacts are
   created for the Qoder smoke.
5. Review evidence records commands and outcomes.
6. Focused validation passes.

## Implementation Notes

### 2026-06-18 — Readiness-Negative Resource Rerun

Credential-safe readiness output from the active `.venv`:

```text
sdk_importable=False
token_present=False
ready=False
error_kind=authentication_failed
raw_error_type=MissingEnvironmentVariable
```

The current host still cannot run a credentialed live Qoder smoke because:

1. `qoder_agent_sdk` is not importable.
2. `QODER_PERSONAL_ACCESS_TOKEN` is not present in the process environment.

No token value was printed or persisted.

Read-only resource inspection:

```text
doc-based-coding resources read dbc://host-evidence/bundle
```

returned:

```text
evidence_count=0
error_count=0
summaries=[]
errors=[]
```

```text
doc-based-coding resources read dbc://host-evidence/presentation
```

returned:

```text
status=empty
card_count=0
error_count=0
empty_message="No host scheduler run evidence has been recorded."
```

Pre-scheduler artifact check:

```text
.codex/scheduler/qoder-smoke-state.json -> absent
.codex/scheduler/evidence/qoder-smoke.json -> absent
.codex/progress-graph/scheduler-work-trajectory.json -> absent
```

This is a readiness-negative rerun over the completed resource surfaces. It is
not a live success, and it does not synthesize evidence JSON merely to populate
the bundle or presentation views.

Close-review evidence:

- `review/credentialed-live-qoder-rerun-over-presentation-resources-2026-06-18.md`
