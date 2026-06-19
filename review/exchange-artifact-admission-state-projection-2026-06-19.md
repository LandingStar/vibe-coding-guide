# Review - Exchange Artifact Admission State Projection

> Date: 2026-06-19
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-19-exchange-artifact-admission-state-projection.md`

## Scope Reviewed

This slice made prior exact-version scheduler admission state visible from the
existing exchange artifact inspection surface.

Implemented:

1. Runtime read model:
   - `ExchangeArtifactAdmissionStateProjection`
   - `ExchangeArtifactVersionSummary.admission_state`
   - `ExchangeArtifactInspectionBundle.admission_ledger_path`
   - `ExchangeArtifactInspectionBundle.admission_ledger_exists`
2. Runtime inspection behavior:
   - `inspect_exchange_artifact_store(..., admission_ledger_path=...)`
   - ledger grouping by exact `(artifact_id, artifact_version)`
   - malformed ledger isolation as bundle errors
3. MCP/CLI resource wiring:
   - `dbc://exchange-artifacts/bundle` now reads the default admission ledger
     path through `GovernanceTools.read_resource()`
   - `doc-based-coding resources read dbc://exchange-artifacts/bundle` returns
     the same projection
4. Prompt guidance:
   - `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
   - `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
5. Tests covering runtime projection, malformed ledger isolation, resource
   readback, CLI readback field presence, and authority boundaries.

## Evidence

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "exchange_artifact_store_inspection"
5 passed

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py
19 passed

.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_mcp_admission.py tests/test_doc_loop_prompts.py
201 passed
```

## Behavioral Notes

`admission_state` is a read-only projection sourced from
`.codex/orchestration/exchange-artifact-admissions.json`. It is attached to
each exact stored artifact version in `dbc://exchange-artifacts/bundle`.

If no ledger file exists, summaries remain valid and report
`status=not_admitted` with `record_count=0`.

If a ledger exists and contains admitted plus later duplicate-rejection records,
the summary status remains `admitted` because at least one successful admission
already happened. The latest duplicate record remains visible through
`latest_status`, `latest_record_id`, `latest_error_summary`, and
`rejected_duplicate_record_ids`.

Malformed ledger JSON is isolated into the bundle error list. Valid exchange
artifact summaries still appear and default to `not_admitted`.

## Authority Boundary

The authority split remains:

1. Exchange artifact store is the coordination product source.
2. Admission ledger is the admission-state/audit source.
3. Scheduler snapshot and event log remain scheduling authority.
4. The projection is read-only.

## Explicit Non-Goals Preserved

This slice did not add:

1. Exchange-store lifecycle mutation or consumed marking.
2. Scheduler daemon or durable queue behavior.
3. Provider execution through MCP or CLI.
4. Automatic scheduler projection refresh.
5. UI binding.
6. New MCP write tools.
7. Local Work Trajectory mutation from scheduler or exchange artifact
   inspection code.

## Follow-Up

The stored-artifact admission chain now has read, write, audit, and read-model
coverage:

1. `dbc://exchange-artifacts/bundle`
2. `admitExchangeArtifact`
3. `doc-based-coding scheduler admit-exchange-artifact`
4. `doc-based-coding scheduler inspect-admissions`
5. admission-state projection back on the bundle

The next narrow backend candidate should move from admission mechanics toward
bounded scheduler daemon / durable queue readiness. UI binding, provider
execution, and exchange-store lifecycle mutation should remain separate gates.
