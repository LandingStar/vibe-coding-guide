# Planning Gate - Exchange Artifact Admission State Projection

> Date: 2026-06-19
> Status: COMPLETED

## Trigger

`design_docs/stored-artifact-mcp-admission-tool-followup-direction-analysis.md`
recommends making prior admission state visible before agents or operators call
CLI/MCP admission again.

## Problem

`dbc://exchange-artifacts/bundle` can show stored artifact versions and
scheduler-admission candidates, while
`.codex/orchestration/exchange-artifact-admissions.json` records exact-version
admission attempts. Consumers currently need to manually join those two
surfaces to answer a simple question:

```text
Has this exact artifact version already been admitted, rejected as duplicate,
or failed during admission?
```

This becomes more important now that MCP `admitExchangeArtifact` is available:
agent-callable mutation should have a nearby read model that exposes duplicate
risk without mutating scheduler or exchange store state.

## Scope

### Slice 1 - Read Model Contract

Add a ledger-derived, read-only admission state projection to exchange artifact
inspection summaries.

Preferred naming:

```text
admission_state
```

Avoid treating this first slice as exchange-store lifecycle mutation. The
projection may describe "admitted" or "not_admitted" state, but it must be
clearly derived from the admission ledger, not written into the stored
artifact version.

Minimum per-version fields:

```text
admission_state.status
admission_state.record_count
admission_state.status_counts
admission_state.latest_record_id
admission_state.latest_status
admission_state.latest_timestamp
admission_state.latest_actor
admission_state.latest_surface
admission_state.latest_error_summary
admission_state.admitted_record_ids
admission_state.rejected_duplicate_record_ids
admission_state.failed_record_ids
```

Recommended status values:

```text
not_admitted
admitted
failed
rejected_duplicate
mixed
unknown
```

### Slice 2 - Resource / CLI Surface

Extend the existing exchange artifact inspection path rather than introducing
a new write surface:

1. Runtime builder reads the exchange artifact store as before.
2. When an admission ledger path is available, it also reads the admission
   ledger and projects matching records by exact `(artifact_id, version)`.
3. `dbc://exchange-artifacts/bundle` includes the projection.
4. `doc-based-coding resources read dbc://exchange-artifacts/bundle` returns
   the same projection through existing resource CLI readback.
5. Missing ledger means every version has `not_admitted` with zero records.
6. Malformed ledger is isolated as an inspection error and does not mutate any
   state.

### Slice 3 - Authority Boundary

The authority split must remain explicit:

1. Exchange artifact store remains the coordination product source.
2. Admission ledger is the audit/admission-state projection source.
3. Scheduler snapshot/event log remain scheduling authority.
4. The projection is read-only.

## Non-Goals

This gate does not:

1. Mutate exchange artifact store lifecycle fields.
2. Add exchange-store consumed marking.
3. Add a new MCP write tool.
4. Run providers or scheduler tasks.
5. Refresh scheduler-derived projection automatically.
6. Add UI binding.
7. Launch a scheduler daemon or durable queue worker.
8. Mutate `.codex/progress-graph/local-work-trajectory.json` from scheduler or
   exchange artifact inspection code.

## Acceptance Criteria

The gate may close when:

1. Exchange artifact inspection summaries expose ledger-derived
   `admission_state`.
2. Missing admission ledger produces explicit `not_admitted` state without
   errors.
3. Existing `admitted`, `rejected_duplicate`, and `failed` ledger records are
   grouped by exact artifact/version and reflected in counts and latest-record
   clues.
4. Malformed ledger input is isolated as a bundle error and does not hide valid
   store summaries.
5. `dbc://exchange-artifacts/bundle` and CLI resource readback include the new
   projection.
6. Tests cover runtime projection, resource/CLI readback, and non-mutation
   boundaries.
7. Review/status docs record that lifecycle mutation, daemon, provider
   execution, UI binding, and scheduler projection refresh remain deferred.

## Implementation Summary

Completed on 2026-06-19.

This slice added `ExchangeArtifactAdmissionStateProjection` to the read-only
exchange artifact inspection model. Each `ExchangeArtifactVersionSummary` now
includes `admission_state`, derived from exact `(artifact_id, version)` records
in `.codex/orchestration/exchange-artifact-admissions.json` when the ledger is
available.

Implemented behavior:

1. Missing admission ledger keeps every version at
   `admission_state.status=not_admitted` with zero records.
2. Existing `admitted`, `rejected_duplicate`, and `failed` records are grouped
   by exact artifact version.
3. A prior `admitted` record keeps the summary status at `admitted`, while
   `latest_status` / `latest_record_id` still expose the latest ledger event
   such as `rejected_duplicate`.
4. Malformed ledger JSON is isolated into bundle `errors[]` without hiding
   valid exchange artifact summaries.
5. `dbc://exchange-artifacts/bundle` now reads the default admission ledger
   path beside the default artifact store path.
6. CLI resource readback inherits the same projection through the existing
   `doc-based-coding resources read dbc://exchange-artifacts/bundle` path.
7. Scheduler smoke prompts now describe `admission_state` as a ledger-derived
   read model, not exchange artifact lifecycle mutation.

## Validation

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "exchange_artifact_store_inspection"
5 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py
19 passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_mcp_admission.py tests/test_doc_loop_prompts.py
201 passed
```

## Non-Goals Preserved

This slice did not add:

1. Exchange-store consumed marking or lifecycle mutation.
2. New MCP write tools.
3. Scheduler daemon or durable queue execution.
4. Provider execution.
5. Automatic scheduler projection refresh.
6. UI binding.
7. Local Work Trajectory mutation from scheduler or exchange artifact
   inspection code.
