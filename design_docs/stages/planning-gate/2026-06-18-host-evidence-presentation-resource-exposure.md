# Planning Gate — Host Evidence Presentation Resource Exposure

> Date: 2026-06-18
> Status: COMPLETED

## Trigger

`design_docs/stages/planning-gate/2026-06-18-host-evidence-presentation-contract.md`
has reached `COMPLETED`.

The follow-up direction analysis recommends this next narrow slice:

- `design_docs/host-evidence-presentation-contract-followup-direction-analysis.md`

## Problem

`HostEvidencePresentation` now provides a stable UI/operator-facing data
contract, but it is only available as a Python builder. Host clients, agents,
and operator scripts still have to either import Python directly or read the
lower-level `dbc://host-evidence/bundle` payload.

Before VS Code UI binding or live Qoder reruns, the presentation view should
be inspectable through the same read-only resource / CLI resource pathway that
already exposes the raw bundle.

## Scope

### Slice 1 — Presentation Resource

Expose a new read-only MCP resource URI:

```text
dbc://host-evidence/presentation
```

The resource should:

1. Call `read_host_evidence_bundle(project_root)`.
2. Call `build_host_evidence_presentation(bundle)`.
3. Return `HostEvidencePresentation.to_json_dict()` as JSON.
4. Avoid provider execution.
5. Avoid scheduler projection refresh.
6. Avoid Local Work Trajectory mutation.

### Slice 2 — CLI Resource Compatibility

Because `doc-based-coding resources read <uri>` already delegates to
`GovernanceTools.read_resource()`, the new URI should be inspectable through:

```text
doc-based-coding resources list
doc-based-coding resources read dbc://host-evidence/presentation
```

No dedicated CLI subcommand is required.

### Slice 3 — Prompt Guidance

Update scheduler smoke prompt guidance so agents know:

1. `dbc://host-evidence/bundle` is the lower-level evidence bundle.
2. `dbc://host-evidence/presentation` is the host/UI/operator-facing view.
3. Both are read-only inspection resources.

## Non-Goals

This gate does not:

1. Add VS Code UI binding.
2. Add screenshot validation.
3. Add provider execution.
4. Add Qoder SDK installation or credential provisioning.
5. Add scheduler daemon behavior.
6. Change the existing bundle resource payload.
7. Change host evidence writer payload shape.

## Acceptance Criteria

The gate may close when:

1. `list_resources()` includes `dbc://host-evidence/presentation`.
2. `read_resource("dbc://host-evidence/presentation")` returns presentation
   JSON with `status`, `cards[]`, `error_rows[]`, and count fields.
3. CLI `resources read dbc://host-evidence/presentation` works.
4. Reading the presentation resource does not create scheduler projection or
   Local Work Trajectory artifacts.
5. Existing bundle resource / CLI tests still pass.
6. Prompt guidance is updated.
7. Focused validation and hygiene checks pass.

## Implementation Notes

### 2026-06-18 — Presentation Resource Exposure

Added read-only resource URI:

```text
dbc://host-evidence/presentation
```

Implementation:

1. `GovernanceTools.list_resources()` now lists
   `host-evidence-presentation`.
2. `GovernanceTools.read_resource("dbc://host-evidence/presentation")`
   reads the existing host evidence bundle and projects it through
   `build_host_evidence_presentation()`.
3. `doc-based-coding resources read dbc://host-evidence/presentation`
   works through the existing CLI resource reader.
4. Scheduler smoke prompt guidance now distinguishes bundle JSON from
   presentation JSON.

The existing bundle resource payload is unchanged.

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "host_evidence or scheduler_mcp_smoke_prompt or cli_resources"
6 passed, 7 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py
209 passed, 1 skipped
```

Close-review evidence:

- `review/host-evidence-presentation-resource-exposure-2026-06-18.md`
