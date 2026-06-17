# Planning Gate — CLI Resource Inspection For Host Evidence

> Date: 2026-06-18
> Status: COMPLETED

## Trigger

`design_docs/stages/planning-gate/2026-06-18-host-evidence-mcp-resource-exposure.md`
has reached `COMPLETED`.

The follow-up direction analysis recommends this next narrow slice:

- `design_docs/host-evidence-mcp-resource-exposure-followup-direction-analysis.md`

## Problem

`dbc://host-evidence/bundle` is now exposed through MCP resources, but users and
scripts still need an MCP host to inspect it. A minimal CLI resource inspection
surface would let operators verify resource visibility, read host evidence
bundles, and debug resource output without starting an MCP client.

## Scope

### Slice 1 — Resource List Command

Add:

```text
doc-based-coding resources list
```

Expected behavior:

1. Print JSON from `GovernanceTools.list_resources()`.
2. Include `dbc://host-evidence/bundle`.
3. Remain read-only.

### Slice 2 — Resource Read Command

Add:

```text
doc-based-coding resources read <uri>
```

Expected behavior:

1. Call `GovernanceTools.read_resource(uri)`.
2. Print resource content as text.
3. Return a clear non-zero error when the resource is not found.
4. Preserve JSON content for `dbc://host-evidence/bundle`.

### Slice 3 — Prompt / Status Writeback

Update prompt guidance so agents can choose CLI inspection when MCP resource
tools are unavailable.

## Non-Goals

This gate does not:

1. Add new MCP tools.
2. Add UI binding.
3. Execute scheduler tasks.
4. Execute Qoder or provision credentials.
5. Install optional SDK packages.
6. Change resource contracts.

## Acceptance Criteria

The gate may close when:

1. `doc-based-coding resources list` exists and includes
   `dbc://host-evidence/bundle`.
2. `doc-based-coding resources read dbc://host-evidence/bundle` prints compact
   bundle JSON.
3. Missing resources return a clear error and non-zero exit.
4. Tests cover the list/read behavior.
5. Prompt/status docs are updated.
6. Focused validation and hygiene checks pass.

## Implementation Notes

### 2026-06-18 — CLI Resource Inspection

Added:

- `src.__main__.cmd_resources()`
- `doc-based-coding resources list`
- `doc-based-coding resources read <uri>`

The CLI reuses the existing read-only resource contract:

```text
GovernanceTools.list_resources()
GovernanceTools.read_resource(uri)
```

It does not add new MCP tools, does not execute providers, does not initialize
scheduler state, and does not change resource payload contracts.

Prompt guidance was updated in both prompt copies so agents can fall back to
CLI inspection when an MCP resource reader is unavailable:

- `.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`
- `doc-loop-vibe-coding/assets/bootstrap/.codex/prompts/doc-loop/07-scheduler-mcp-smoke.md`

Validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_doc_loop_prompts.py -k "cli_resources or host_evidence_bundle or scheduler_mcp_smoke_prompt"
4 passed, 7 deselected

.\.venv\Scripts\python.exe -m src resources list
listed dbc://host-evidence/bundle

.\.venv\Scripts\python.exe -m src resources read dbc://host-evidence/bundle
returned compact bundle JSON with evidence_count=0 and summaries=[]

.\.venv\Scripts\python.exe -m src resources read dbc://missing
returned exit code 1 and "Resource not found: dbc://missing"
```

Close-review evidence:

- `review/cli-resource-inspection-for-host-evidence-2026-06-18.md`

Follow-up direction analysis:

- `design_docs/cli-resource-inspection-for-host-evidence-followup-direction-analysis.md`
