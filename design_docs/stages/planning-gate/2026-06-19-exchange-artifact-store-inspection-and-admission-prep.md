# Planning Gate — ExchangeArtifact Store Inspection And Admission Prep

> Date: 2026-06-19
> Status: COMPLETED

## Trigger

`design_docs/stages/planning-gate/2026-06-18-exchange-artifact-durable-store-foundation.md`
has reached `COMPLETED`.

The close review recommends the next narrow line:

- `review/exchange-artifact-durable-store-foundation-2026-06-18.md`

## Problem

`JsonArtifactVersionStore` now persists exact `ExchangeArtifact` versions, but
operators and agents still lack a read-only way to inspect what is in the local
store. Without that inspection layer, the next scheduler-admission slice would
either need to reach into store internals or jump directly from "stored JSON
exists" to "scheduler consumes it".

The project needs a small inspection/admission-prep surface that can answer:

1. Which artifact IDs and versions exist?
2. Which version is latest for each artifact?
3. What kind / intent / lifecycle / producer / scope does each artifact have?
4. Does an exact version look like a scheduler task submission or batch
   submission candidate?

## Scope

### Slice 1 — Read-Only Inspection Model

Add runtime helpers over `JsonArtifactVersionStore`:

```text
ExchangeArtifactVersionSummary
ExchangeArtifactInspectionBundle
ExchangeArtifactAdmissionCandidate
build_exchange_artifact_inspection_bundle()
inspect_exchange_artifact_store()
```

The inspection bundle should:

1. Read a caller-provided JSON artifact store path.
2. Return deterministic artifact/version summaries.
3. Include store path, exists flag, schema version, artifact count, version
   count, and errors.
4. Preserve exact-version identity for later admission surfaces.
5. Keep malformed stores isolated as read errors in the bundle.

### Slice 2 — Admission-Prep Candidate Detection

For each stored version, detect whether it contains one of the known scheduler
submission structured payloads:

```text
scheduler_task_submission
scheduler_task_batch_submission
```

This is advisory metadata only. It must not submit tasks, mutate scheduler
state, or mark artifacts consumed.

### Slice 3 — Resource / CLI Inspection

Expose the bundle through the existing read-only resource surface:

```text
dbc://exchange-artifacts/bundle
doc-based-coding resources read dbc://exchange-artifacts/bundle
```

Default store path:

```text
.codex/orchestration/exchange-artifacts.json
```

The default path is an inspection convention for local coordination products,
not a scheduler state path and not a requirement that every workspace must have
the file.

## Non-Goals

This gate does not:

1. Submit stored artifacts into scheduler state.
2. Change scheduler snapshot authority.
3. Mark exchange artifacts consumed, accepted, rejected, or superseded.
4. Add a write/admission MCP tool.
5. Add a database, remote registry, or watcher.
6. Run Qoder or any runtime provider.
7. Mutate Local Work Trajectory or scheduler-derived trajectory projection.
8. Add UI binding.

## Acceptance Criteria

The gate may close when:

1. Inspection returns an empty read-only bundle when the store file is missing.
2. Inspection summarizes multiple artifacts and versions deterministically.
3. Exact-version candidate metadata distinguishes task and batch submissions.
4. Malformed store JSON is reported as a bundle error without scheduler
   mutation.
5. `dbc://exchange-artifacts/bundle` appears in `list_resources()`.
6. CLI `resources read dbc://exchange-artifacts/bundle` works.
7. Focused runtime / MCP / prompt tests pass.
8. Design docs record that this is admission preparation, not admission.

## Implementation Notes

### 2026-06-19 — Inspection Bundle And Resource Exposure

Added:

```text
ExchangeArtifactVersionSummary
ExchangeArtifactInspectionBundle
ExchangeArtifactAdmissionCandidate
DEFAULT_EXCHANGE_ARTIFACT_STORE_RELATIVE_PATH
default_exchange_artifact_store_path()
inspect_exchange_artifact_store()
build_exchange_artifact_inspection_bundle()
JsonArtifactVersionStore.list_records()
dbc://exchange-artifacts/bundle
```

The inspection bundle reads `.codex/orchestration/exchange-artifacts.json` by
default through the MCP/CLI resource path, but the runtime helper still accepts
a caller-provided store path for tests and future host integration. Missing
stores return an empty read-only bundle. Malformed stores are isolated into
`errors[]` / `error_count`.

Admission-prep candidate detection is advisory only. It recognizes structured
payloads with:

```text
scheduler_task_submission
scheduler_task_batch_submission
```

and reports task IDs, batch IDs, task counts, exact artifact IDs, and versions.
It does not submit tasks, mutate scheduler state, mark artifacts consumed, or
refresh Local Work Trajectory / scheduler projections.

Updated:

- `src/runtime/orchestration/exchange_store.py`
- `src/runtime/orchestration/__init__.py`
- `src/mcp/tools.py`
- `tests/test_doc_loop_prompts.py`
- `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
- `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
- `design_docs/agent-coordination-exchange-artifact-design-record.md`
- `design_docs/agent-runtime-layering-and-orchestration-slice-plan.md`

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py tests/test_mcp_tools.py tests/test_doc_loop_prompts.py
243 passed
```

Note: the Windows Python process printed access-violation stacks after pytest
reported success and returned exit code 0. One stack pointed at an existing
scheduler event-log test path; a later targeted rerun printed during dataclass
module import. A minimal direct import smoke and CLI resource read both returned
normally. This is recorded as residual Windows/Python test-process risk, not a
failed assertion.
