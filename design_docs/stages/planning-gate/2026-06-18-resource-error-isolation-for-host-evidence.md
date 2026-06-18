# Planning Gate — Resource Error Isolation For Host Evidence

> Date: 2026-06-18
> Status: COMPLETED

## Trigger

`design_docs/stages/planning-gate/2026-06-18-cli-resource-inspection-for-host-evidence.md`
has reached `COMPLETED`.

The follow-up direction analysis recommends this next narrow slice:

- `design_docs/cli-resource-inspection-for-host-evidence-followup-direction-analysis.md`

## Problem

`dbc://host-evidence/bundle` and the CLI resource reader now provide a useful
inspection surface, but one malformed evidence JSON file can still break the
whole bundle read. That is acceptable for strict runtime validation, but it is
not good enough for UI, release tooling, or operator inspection surfaces where
one bad local artifact should not hide all valid host-run evidence.

## Scope

### Slice 1 — Bundle Error Summary

Extend the progress/resource-facing host evidence bundle so it can report
per-file read errors:

```text
errors[]
error_count
```

Expected behavior:

1. Valid evidence files still appear in `summaries[]`.
2. Invalid evidence files appear in `errors[]`.
3. `evidence_count` continues to count valid summaries only.
4. Error summaries include the evidence path, an error kind, and a compact
   message.
5. Error summaries must not include raw file contents.

### Slice 2 — Strict Reader Boundary

Keep `read_host_scheduler_run_evidence_summary()` and
`read_host_scheduler_run_evidence_summaries()` strict. They should still raise
for malformed evidence. Only the `HostEvidenceBundle` consumer layer should
isolate errors.

### Slice 3 — Resource / CLI Verification

Because MCP resource read and CLI read both call `read_host_evidence_bundle()`,
the same error-isolating payload should be visible through:

```text
GovernanceTools.read_resource("dbc://host-evidence/bundle")
doc-based-coding resources read dbc://host-evidence/bundle
```

## Non-Goals

This gate does not:

1. Add UI binding.
2. Add new MCP tools.
3. Execute scheduler tasks.
4. Execute Qoder or provision credentials.
5. Install optional SDK packages.
6. Change host evidence writer payload shape.
7. Relax strict runtime evidence validation.

## Acceptance Criteria

The gate may close when:

1. Bundle JSON includes `error_count` and `errors`.
2. A malformed evidence file is isolated into `errors[]` while valid summaries
   still appear.
3. Strict runtime evidence reader tests still prove malformed evidence raises.
4. MCP resource and/or CLI tests prove the isolated error payload is observable
   through the existing resource path.
5. Prompt/status docs are updated if behavior guidance changes.
6. Focused validation and hygiene checks pass.

## Implementation Notes

### 2026-06-18 — Bundle-level Error Isolation

Added:

- `tools.progress_graph.host_evidence.HostEvidenceReadError`
- `HostEvidenceBundle.errors`
- `HostEvidenceBundle.to_json_dict()["error_count"]`
- `HostEvidenceBundle.to_json_dict()["errors"]`

`read_host_evidence_bundle()` now isolates malformed per-file reads by default.
Valid evidence artifacts still appear in `summaries[]`; malformed artifacts are
reported in compact `errors[]` entries with path, error kind, and message. Error
entries do not include raw file contents.

Strict runtime readers remain strict:

```text
read_host_scheduler_run_evidence_summary()
read_host_scheduler_run_evidence_summaries()
```

They still raise on malformed evidence. The isolation layer exists only at the
progress/resource-facing bundle boundary.

Validation:

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

During manual external-workspace CLI validation, the local editable install was
refreshed from `0.9.3` to `0.9.8` with `pip install -e .` so the installed
editable mapping includes both `src` and `tools`. This was a host environment
verification fix, not a project source change.

Close-review evidence:

- `review/resource-error-isolation-for-host-evidence-2026-06-18.md`
