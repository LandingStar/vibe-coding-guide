# Resource Error Isolation For Host Evidence Review — 2026-06-18

## Position

This review audits
`design_docs/stages/planning-gate/2026-06-18-resource-error-isolation-for-host-evidence.md`.

Verdict: ready for close.

The slice adds bundle-level error isolation for host evidence resource
consumers. One malformed evidence JSON file no longer prevents valid summaries
from being returned through `HostEvidenceBundle`, MCP resource reads, or CLI
resource inspection.

The strict runtime evidence readers remain strict and still raise on malformed
evidence. This keeps writer/runtime validation precise while making
UI/resource/operator surfaces more robust.

## Implementation Evidence

Changed:

- `tools/progress_graph/host_evidence.py`
  - added `HostEvidenceReadError`
  - added `HostEvidenceBundle.errors`
  - added `error_count` / `errors` JSON output
  - made `read_host_evidence_bundle()` isolate per-file read errors by default
- `tools/progress_graph/__init__.py`
  - exported `HostEvidenceReadError`
- `tests/test_progress_graph_trajectory.py`
  - added malformed artifact isolation coverage
- `tests/test_doc_loop_prompts.py`
  - updated resource/prompt assertions for `error_count` and `errors`
- `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
  - documented bundle-level error isolation
- `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
  - mirrored the prompt guidance

## Acceptance Evidence

| Criterion | Evidence | Verdict |
| --- | --- | --- |
| Bundle JSON includes `error_count` and `errors`. | Tests assert these fields for empty and CLI-visible bundle payloads. | Met |
| Malformed evidence is isolated without hiding valid summaries. | `test_host_evidence_bundle_isolates_malformed_artifacts` creates one valid file and two malformed files; valid summary remains visible and two errors are reported. | Met |
| Strict runtime reader remains strict. | Existing `test_host_scheduler_run_evidence_summary_rejects_wrong_product_type` still passes. | Met |
| Existing resource/CLI path observes the new payload. | `tests/test_doc_loop_prompts.py` checks resource JSON shape; manual external-workspace CLI read returned `error_count=1`. | Met |
| Error payload remains compact. | `HostEvidenceReadError` includes only path, error kind, and message; no raw file content is copied. | Met |

## Validation

```text
.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "host_evidence_bundle"
3 passed, 54 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "host_evidence_bundle or scheduler_mcp_smoke_prompt or cli_resources"
4 passed, 7 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py
204 passed, 1 skipped
```

Manual CLI checks:

```text
.\.venv\Scripts\python.exe -m src resources read dbc://host-evidence/bundle
returned error_count=0, summaries=[]

external temp workspace with .codex/scheduler/evidence/bad.json
returned error_count=1 with errors[0].error_kind="invalid_evidence"
```

Environment note:

The external-workspace CLI smoke initially exposed a local development
environment issue: `.venv` still had an editable install for
`doc-based-coding-runtime 0.9.3`, whose editable finder only mapped `src` and
not `tools`. Running `pip install -e .` refreshed the local verification
environment to `0.9.8`; this did not change tracked project source.

## Residual Risk

1. No VS Code UI binding yet.
2. No credentialed live Qoder success evidence yet.
3. Error messages include local evidence file paths. That is useful for
   operator inspection; if future UI surfaces need redaction, that should be a
   separate host-facing presentation policy.

## Close Recommendation

Close this gate as `COMPLETED`.

Recommended next direction:

The clean resource/CLI line is now productized enough for the next decision to
choose between:

1. a narrow host evidence UI binding once the VS Code dirty branch is clean, or
2. a credentialed live Qoder rerun after SDK/auth provisioning.
