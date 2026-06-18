# ExchangeArtifact Durable Store Foundation Review — 2026-06-18

## Position

This review audits
`design_docs/stages/planning-gate/2026-06-18-exchange-artifact-durable-store-foundation.md`.

Verdict: ready for close.

The slice adds the first local durable version store for coordination
`ExchangeArtifact` products. It keeps the existing in-memory store, preserves
the scheduler-relevant validation rule, and does not make exchange artifacts
the scheduler state authority.

## Implementation Evidence

Changed:

- `src/runtime/orchestration/exchange_store.py`
  - added `EXCHANGE_ARTIFACT_STORE_SCHEMA_VERSION`
  - added `JsonArtifactVersionStore`
  - added `exchange_artifact_to_json_dict()`
  - added `exchange_artifact_from_json_dict()`
- `src/runtime/orchestration/__init__.py`
  - exported the JSON store and serialization helpers
- `tests/test_runtime_orchestration.py`
  - covered all current exchange payload part types round-trip
  - covered durable store version persistence
  - covered duplicate version rejection
  - covered invalid scheduler-relevant artifact rejection before write
  - covered unsupported store schema version reporting
- `design_docs/agent-coordination-exchange-artifact-design-record.md`
  - recorded the local durable store boundary
- `design_docs/agent-runtime-layering-and-orchestration-slice-plan.md`
  - updated O7/O8 implementation status

## Acceptance Evidence

| Criterion | Evidence | Verdict |
| --- | --- | --- |
| Durable store round-trip tests pass. | `test_json_artifact_version_store_persists_versions_and_reads_latest`. | Met |
| Duplicate versions fail clearly. | Same test asserts `already exists`. | Met |
| Invalid scheduler-relevant artifacts are rejected before persistence. | `test_json_artifact_version_store_rejects_invalid_artifact_before_write`. | Met |
| `latest()` and `list_versions()` are deterministic. | Same durable store test asserts insertion order and latest version. | Met |
| Serialization covers current payload part types. | `test_exchange_artifact_json_round_trip_covers_current_payload_parts`. | Met |
| Existing runtime / scheduler tests pass. | `tests/test_runtime_orchestration.py` focused suite passed. | Met |
| Docs record boundary and non-goals. | Design record and orchestration slice plan updated. | Met |

## Validation

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

## Residual Risk

1. The durable store is a single local JSON file and not optimized for large
   artifact volumes.
2. There is not yet an MCP/CLI artifact-store inspection surface.
3. Scheduler snapshots remain the scheduling authority; artifact replay into
   scheduler state is intentionally not implemented.
4. Raw runtime transcript persistence remains out of scope.

## Close Recommendation

Close this gate as `COMPLETED`.

Recommended next direction:

1. Add a narrow artifact-store inspection/admission surface if operators or
   agents need to read stored exchange artifacts directly.
2. Otherwise continue toward scheduler / exchange integration by wiring stored
   task-submission artifacts into persisted scheduler runs without changing
   scheduler authority.

