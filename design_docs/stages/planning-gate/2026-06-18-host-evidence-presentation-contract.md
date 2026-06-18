# Planning Gate — Host Evidence Presentation Contract

> Date: 2026-06-18
> Status: COMPLETED

## Trigger

`design_docs/stages/planning-gate/2026-06-18-resource-error-isolation-for-host-evidence.md`
has reached `COMPLETED`.

The follow-up direction analysis recommends this next narrow slice:

- `design_docs/resource-error-isolation-for-host-evidence-followup-direction-analysis.md`

## Problem

`HostEvidenceBundle` is now robust enough for MCP resource and CLI inspection,
but the bundle is still a raw consumer payload. A future UI or host integration
would need to understand evidence summaries, authority split fields, output
refs, stop reasons, and isolated read errors directly.

That would couple visual layers to low-level evidence fields and make UI
changes more fragile. Before binding a VS Code panel or another host surface,
the project needs a small presentation contract that turns evidence bundles
into stable UI/operator-facing rows.

## Scope

### Slice 1 — Presentation Model

Add a pure data presentation layer over `HostEvidenceBundle`.

Expected output shape:

```text
HostEvidencePresentation
  generated_at
  project_root
  evidence_dir
  status
  cards[]
  error_rows[]
  empty_message
```

Each card should expose:

```text
id
title
subtitle
status
severity
timestamp
runtime_providers[]
host_surface
invocation_id
requested_by
stop_reason
stop_detail
run_count
output_count
permission_review_count
key_facts[]
refs[]
authority_clues[]
metadata
```

Each error row should expose:

```text
id
status
severity
evidence_path
error_kind
message
```

### Slice 2 — Stable Status Derivation

Derive presentation status from compact evidence fields without re-reading raw
`host_result`:

1. `failed` when `failed_task_ids` is non-empty or `stop_reason` is
   `task_failed` / `completed_with_failures`.
2. `permission-review` when `permission_review_count > 0`.
3. `partial` when `stop_reason` is `max_runs_reached`, `blocked_tasks`, or
   when blocked tasks remain.
4. `completed` when `stop_reason` is `no_ready_tasks` and there are no failed,
   blocked, or permission-review tasks.
5. `unknown` as the defensive fallback.

Bundle-level status should aggregate cards and isolated read errors:

1. `empty` when there are no cards and no errors.
2. `failed` when any card is failed.
3. `degraded` when any error rows exist or any card is partial /
   permission-review.
4. `ok` when all cards are completed.

### Slice 3 — Resource / CLI Compatibility

The presentation layer should be callable from Python tests and future host
surfaces, but this gate does not need to expose a new MCP resource or CLI
subcommand yet. Existing bundle resource shape remains unchanged.

## Non-Goals

This gate does not:

1. Add VS Code UI binding.
2. Add screenshots or visual validation.
3. Add a new MCP tool.
4. Add a new MCP resource URI.
5. Execute scheduler tasks.
6. Execute Qoder or provision credentials.
7. Install optional SDK packages.
8. Change host evidence writer payload shape.
9. Relax strict runtime evidence validation.

## Acceptance Criteria

The gate may close when:

1. A presentation model can be built from `HostEvidenceBundle`.
2. Empty bundles produce a stable `empty` status and operator-facing empty
   message.
3. Successful evidence summaries produce completed cards with provider,
   invocation, output, ref, and authority clues.
4. Permission-review / failed / partial evidence summaries map to distinct
   card status values.
5. Isolated evidence read errors become error rows without hiding valid cards.
6. Existing MCP resource and CLI bundle tests still pass unchanged.
7. Focused validation and hygiene checks pass.

## Implementation Notes

### 2026-06-18 — Presentation Model

Added `HostEvidencePresentation` over `HostEvidenceBundle`.

The presentation layer now converts compact evidence summaries into stable
UI/operator-facing cards and isolated read errors into error rows. It derives
card status from existing compact summary fields only; it does not re-read or
embed raw `host_result`.

Added:

- `HostEvidencePresentation`
- `HostEvidencePresentationCard`
- `HostEvidencePresentationErrorRow`
- `HostEvidencePresentationFact`
- `HostEvidencePresentationRef`
- `build_host_evidence_presentation()`

Status derivation:

1. failed task IDs or failure stop reasons map to `failed`.
2. permission reviews map to `permission-review`.
3. max-runs / blocked-task states map to `partial`.
4. clean `no_ready_tasks` runs map to `completed`.
5. bundle-level errors or partial cards map the bundle to `degraded`.

The existing MCP resource and CLI bundle payload are unchanged. The new
presentation contract is available as a Python data builder for future host UI
or operator surfaces.

Focused validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "host_evidence"
6 passed, 54 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "host_evidence_bundle or cli_resources or scheduler_mcp_smoke_prompt" tests/test_mcp_prompts_resources.py -k "host_evidence_bundle or resources"
27 passed, 8 deselected

.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py tests/test_runtime_orchestration.py tests/test_progress_graph_trajectory.py tests/test_mcp_prompts_resources.py
231 passed, 1 skipped
```

Close-review evidence:

- `review/host-evidence-presentation-contract-2026-06-18.md`
