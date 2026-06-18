# Host Evidence Presentation Resource Exposure Review — 2026-06-18

## Position

This review audits
`design_docs/stages/planning-gate/2026-06-18-host-evidence-presentation-resource-exposure.md`.

Verdict: ready for close.

The slice exposes `HostEvidencePresentation` through the existing read-only
resource path as `dbc://host-evidence/presentation`. CLI resource inspection
can read the same URI without adding a dedicated command.

The resource reads existing evidence, builds the presentation model, and
returns JSON. It does not execute providers, refresh scheduler projections, or
mutate Local Work Trajectory artifacts.

## Implementation Evidence

Changed:

- `src/mcp/tools.py`
  - added `HOST_EVIDENCE_PRESENTATION_RESOURCE_URI`
  - listed `dbc://host-evidence/presentation`
  - read presentation JSON through
    `read_host_evidence_bundle()` + `build_host_evidence_presentation()`
- `tests/test_doc_loop_prompts.py`
  - covered prompt guidance
  - covered resource listing
  - covered empty read-only presentation reads
  - covered CLI resource read for the presentation URI
- `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
  - documented bundle vs presentation resource usage
- `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
  - mirrored the prompt guidance

## Acceptance Evidence

| Criterion | Evidence | Verdict |
| --- | --- | --- |
| `list_resources()` includes the presentation URI. | `test_host_evidence_presentation_resource_is_listed_and_read_only_when_empty`. | Met |
| Resource read returns presentation JSON. | `test_host_evidence_presentation_resource_is_listed_and_read_only_when_empty`. | Met |
| CLI resource read works. | `test_cli_resources_read_host_evidence_presentation`. | Met |
| Presentation read is read-only. | Empty read test asserts no scheduler projection or local trajectory artifact is created. | Met |
| Existing bundle resource remains available. | `test_host_evidence_bundle_resource_is_listed_and_read_only_when_empty` and `test_cli_resources_list_and_read_host_evidence_bundle`. | Met |
| Prompt guidance is updated. | `test_scheduler_mcp_smoke_prompt_covers_submit_project_run_lifecycle`. | Met |

## Validation

```text
.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "host_evidence or scheduler_mcp_smoke_prompt or cli_resources"
6 passed, 7 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py
209 passed, 1 skipped
```

## Residual Risk

1. No VS Code UI binding yet.
2. No credentialed live Qoder success evidence yet.
3. Presentation resource currently uses an empty `generated_at` unless future
   callers pass a timestamp through a separate host-facing builder.

## Close Recommendation

Close this gate as `COMPLETED`.

Recommended next direction:

1. VS Code / Preview UI Binding once the unrelated UI dirty branch is clean, or
2. Credentialed Live Qoder Rerun after SDK/auth provisioning.
