# Host Evidence Consumer Review — 2026-06-18

## Position

This review audits
`design_docs/stages/planning-gate/2026-06-18-host-evidence-consumer.md`.

Verdict: ready for close review.

The slice adds a read-only consumer contract for persisted
`host_scheduler_run_evidence` JSON. It does not execute providers, mutate
scheduler state, mutate Local Work Trajectory, install Qoder SDKs, or synthesize
evidence for readiness-negative outcomes.

## Implementation Evidence

Runtime consumer:

- `src/runtime/orchestration/scheduler_dogfood.py`
  - `HostSchedulerRunEvidenceSummary`
  - `read_host_scheduler_run_evidence_summary()`
  - `read_host_scheduler_run_evidence_summaries()`

Progress graph helper:

- `tools/progress_graph/host_evidence.py`
  - `HostEvidenceBundle`
  - `host_scheduler_evidence_dir()`
  - `read_host_evidence_bundle()`

Exports:

- `src/runtime/orchestration/__init__.py`
- `tools/progress_graph/__init__.py`

## Acceptance Evidence

| Criterion | Evidence | Verdict |
| --- | --- | --- |
| Runtime reader and bundle are implemented. | New runtime summary reader and progress bundle helper exist. | Met |
| Successful summary reads are tested. | `test_host_scheduler_run_evidence_summary_reads_ui_safe_contract`; `test_host_evidence_bundle_reads_compact_summaries`. | Met |
| Missing evidence directory is tested. | `test_host_scheduler_run_evidence_summaries_missing_directory_is_empty`; `test_host_evidence_bundle_missing_directory_is_empty`. | Met |
| Invalid product/schema rejection is tested. | `test_host_scheduler_run_evidence_summary_rejects_wrong_product_type`. | Met |
| Summary is compact and UI-safe. | Tests assert `host_result` is absent from summary payload. | Met |
| No provider execution path is added. | Consumer only reads JSON files; dogfood runner code remains the execution surface. | Met |

## Validation

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "host_scheduler_run_evidence"
4 passed

.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "host_evidence_bundle or host_runtime_dogfood_harness_fake"
3 passed
```

## Residual Risk

1. No VS Code UI binding yet.
2. No MCP resource/tool exposure yet.
3. No credentialed live Qoder success evidence yet.
4. Readiness-negative evidence remains in review docs, not evidence JSON.
5. The consumer currently fails on malformed JSON instead of returning an
   isolated per-file error bundle; that is acceptable for this first strict
   contract and can be softened in a UI-specific slice later.

## Close Recommendation

Move the planning gate to `COMPLETED` after status writeback.

Recommended next direction:

1. Add a read-only MCP/resource or preview consumer over `HostEvidenceBundle`,
   or
2. provision SDK/auth and rerun credentialed live Qoder smoke.

The first option is lower risk because it productizes existing fake/mock and
readiness-negative evidence before requiring local host credential changes.
