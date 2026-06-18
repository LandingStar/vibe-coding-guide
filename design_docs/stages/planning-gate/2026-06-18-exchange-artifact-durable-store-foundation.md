# Planning Gate — ExchangeArtifact Durable Store Foundation

> Date: 2026-06-18
> Status: COMPLETED

## Trigger

`design_docs/stages/planning-gate/2026-06-18-qoder-host-provisioning-check-guide.md`
has reached `COMPLETED`.

The follow-up direction analysis selects this next narrow slice:

- `design_docs/qoder-host-provisioning-check-guide-followup-direction-analysis.md`

## Problem

The orchestration layer is moving toward artifact-centered multi-agent
coordination, but `ExchangeArtifact` versions are currently only stored in
memory. That is sufficient for unit tests and injected fake-runtime paths, but
not for product-level coordination across agent turns, scheduler submissions,
agent home governance products, or later UI inspection.

The scheduler already accepts task submissions encoded as exchange artifacts,
and agent storage products already map to exchange artifacts. Those products
need a durable local version store before the system can safely depend on
exact consumed versions.

## Scope

### Slice 1 — JSON Durable Store

Add a local JSON-backed store for exchange artifacts:

```text
JsonArtifactVersionStore
```

The store should:

1. Use a caller-provided root/path, not a hard-coded global path.
2. Persist each `(artifact_id, version)` exactly once.
3. Reject duplicate versions.
4. Reuse `validate_exchange_artifact()`.
5. Support:
   - `put()`
   - `get()`
   - `latest()`
   - `list_versions()`
6. Preserve exact artifact shape after round-trip.

### Slice 2 — Serialization Helpers

Add project-owned serialization helpers for exchange artifacts:

```text
exchange_artifact_to_json_dict()
exchange_artifact_from_json_dict()
```

The helpers should cover the current payload parts:

1. text
2. structured
3. ref
4. artifact_delta
5. contract
6. evidence
7. relation
8. storage_manifest
9. log

### Slice 3 — Documentation And Prompt Surface

Update:

1. `design_docs/agent-coordination-exchange-artifact-design-record.md`
2. `design_docs/agent-runtime-layering-and-orchestration-slice-plan.md`
3. scheduler / orchestration prompt guidance if a durable store path is needed

## Non-Goals

This gate does not:

1. Replace scheduler snapshots with exchange artifacts.
2. Make event logs replay artifacts into scheduler state.
3. Add UI rendering.
4. Add a database.
5. Add network or remote artifact storage.
6. Run real Qoder.
7. Change Local Work Trajectory authority.

## Acceptance Criteria

The gate may close when:

1. Durable store round-trip tests pass.
2. Duplicate `(artifact_id, version)` writes fail clearly.
3. Invalid scheduler-relevant artifacts are rejected before persistence.
4. `latest()` and `list_versions()` are deterministic.
5. Serialization covers current exchange payload part types.
6. Existing runtime / scheduler tests still pass for the touched surface.
7. Design docs record the durable store boundary and remaining non-goals.

## Implementation Notes

### 2026-06-18 — Durable Store And Serialization

Added:

```text
JsonArtifactVersionStore
exchange_artifact_to_json_dict()
exchange_artifact_from_json_dict()
EXCHANGE_ARTIFACT_STORE_SCHEMA_VERSION
```

The JSON store uses a caller-provided file path and persists an ordered list of
artifact versions. It validates artifacts before writing, rejects duplicate
`(artifact_id, version)` pairs, supports `get()` / `latest()` /
`list_versions()`, and round-trips the current exchange payload part types.

Updated:

- `design_docs/agent-coordination-exchange-artifact-design-record.md`
- `design_docs/agent-runtime-layering-and-orchestration-slice-plan.md`

Targeted validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "exchange_artifact_json or json_artifact_version_store or exchange_artifact_version_store"
6 passed, 137 deselected
```

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py
143 passed
```
