# ExchangeArtifact Store Inspection And Admission Prep Review — 2026-06-19

## Position

This review audits
`design_docs/stages/planning-gate/2026-06-19-exchange-artifact-store-inspection-and-admission-prep.md`.

Verdict: ready for close.

The slice adds a read-only inspection bundle over the local durable
`ExchangeArtifact` store and exposes it as `dbc://exchange-artifacts/bundle`.
It preserves scheduler snapshot authority and does not submit stored artifacts
into scheduler state.

## Implementation Evidence

Changed:

- `src/runtime/orchestration/exchange_store.py`
  - added `DEFAULT_EXCHANGE_ARTIFACT_STORE_RELATIVE_PATH`
  - added `ExchangeArtifactVersionSummary`
  - added `ExchangeArtifactInspectionBundle`
  - added `ExchangeArtifactAdmissionCandidate`
  - added `JsonArtifactVersionStore.list_records()`
  - added `default_exchange_artifact_store_path()`
  - added `inspect_exchange_artifact_store()`
  - added `build_exchange_artifact_inspection_bundle()`
- `src/runtime/orchestration/__init__.py`
  - exported the inspection models and helpers
- `src/mcp/tools.py`
  - added resource URI `dbc://exchange-artifacts/bundle`
- `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
  - documented exchange artifact store inspection and non-authority boundary
- `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
  - kept bootstrap prompt copy in sync
- `tests/test_runtime_orchestration.py`
  - covered missing store, valid summaries/candidates, and malformed store
- `tests/test_doc_loop_prompts.py`
  - covered resource listing, empty read-only bundle, CLI fallback, and
    prompt/resource guidance

## Acceptance Evidence

| Criterion | Evidence | Verdict |
| --- | --- | --- |
| Missing store returns empty read-only bundle. | `test_exchange_artifact_store_inspection_reports_missing_store_as_empty`; resource tests. | Met |
| Multiple artifacts and versions summarize deterministically. | `test_exchange_artifact_store_inspection_summarizes_versions_and_candidates`. | Met |
| Task and batch submission candidates are distinguished. | Same runtime test plus MCP resource batch test. | Met |
| Malformed JSON is isolated as bundle error. | `test_exchange_artifact_store_inspection_isolates_malformed_store`. | Met |
| Resource is listed. | `test_exchange_artifacts_bundle_resource_is_listed`. | Met |
| CLI resource read works through existing path. | `test_cli_resources_read_exchange_artifacts_bundle`. | Met |
| Scheduler authority remains unchanged. | Bundle `authority_split` reports read-only/admission-prep; no scheduler mutation tools added. | Met |
| Prompt guidance records non-goals. | Scheduler smoke prompt and bootstrap copy mention `dbc://exchange-artifacts/bundle`. | Met |

## Validation

Targeted validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "exchange_artifact_store_inspection or json_artifact_version_store or exchange_artifact_json or exchange_artifact_version_store"
9 passed, 137 deselected
```

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py
243 passed
```

The focused validation returned exit code 0 after reporting `243 passed`. The
Windows Python process also printed access-violation stacks after pytest
reported success. One stack pointed at an existing scheduler event-log test
path; a later targeted rerun printed during dataclass module import. A minimal
direct import smoke and CLI resource read returned normally.

Additional smoke:

```text
.\.venv\Scripts\python.exe -c "from src.runtime.orchestration import inspect_exchange_artifact_store, default_exchange_artifact_store_path; print(inspect_exchange_artifact_store(default_exchange_artifact_store_path('.')).to_json_dict()['exists'])"
False

.\.venv\Scripts\python.exe -m src resources read dbc://exchange-artifacts/bundle
exit code 0, empty bundle JSON
```

## Residual Risk

1. The inspection bundle is still a single local JSON-file reader, not a large
   store index.
2. Candidate detection is intentionally shallow: it identifies known
   `product_type` payloads and basic task IDs, but does not perform scheduler
   admission.
3. There is no write/admission MCP tool yet.
4. The pytest access-violation printout should be watched if it recurs in
   normal CLI/import paths or starts producing non-zero exits.

## Close Recommendation

Close this gate as `COMPLETED`.

Recommended next direction:

1. Add a narrow scheduler admission helper that consumes an exact stored
   artifact version from the durable store and submits it through existing
   scheduler submission adapters.
2. Keep scheduler snapshots as the task-contract authority; the store should
   provide exact source artifacts, not replace scheduler state.
