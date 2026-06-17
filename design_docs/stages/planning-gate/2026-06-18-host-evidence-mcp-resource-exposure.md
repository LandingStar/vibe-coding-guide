# Planning Gate — Host Evidence MCP Resource Exposure

> Date: 2026-06-18
> Status: COMPLETED

## Trigger

`design_docs/stages/planning-gate/2026-06-18-host-evidence-consumer.md`
has reached `COMPLETED`.

The follow-up direction analysis recommends this next narrow slice:

- `design_docs/host-evidence-consumer-followup-direction-analysis.md`

## Problem

`HostEvidenceBundle` can now read persisted host scheduler evidence, but agents
and MCP clients cannot discover or read it through the standard resource
surface. Without a resource, downstream users must either inspect raw JSON paths
or add ad hoc tool calls. That weakens the product boundary created by the
consumer slice.

## Scope

### Slice 1 — Resource Metadata

Expose one read-only MCP resource:

```text
dbc://host-evidence/bundle
```

The resource should appear in `list_resources()` with:

1. name: `host-evidence-bundle`
2. MIME type: `application/json`
3. description stating it is read-only and compact

### Slice 2 — Resource Read

`read_resource("dbc://host-evidence/bundle")` should:

1. call `tools.progress_graph.read_host_evidence_bundle()`
2. return stable JSON with `project_root`, `evidence_dir`, `evidence_count`,
   and compact `summaries`
3. return an empty bundle when the evidence directory does not exist
4. not execute providers
5. not initialize scheduler state
6. not refresh scheduler projection
7. not mutate `.codex/progress-graph/local-work-trajectory.json`

### Slice 3 — Prompt / Review Writeback

Update scheduler MCP prompt guidance so agents can discover and consume the
host evidence resource instead of scraping raw evidence files.

## Non-Goals

This gate does not:

1. Add a new MCP execution tool.
2. Expose Qoder or any real provider through MCP execution.
3. Add VS Code UI binding.
4. Add daemon behavior.
5. Install optional Qoder SDK packages or provision credentials.
6. Synthesize evidence JSON for readiness-negative review docs.

## Acceptance Criteria

The gate may close when:

1. `list_resources()` includes `dbc://host-evidence/bundle`.
2. `read_resource()` returns compact JSON from `HostEvidenceBundle`.
3. Tests prove missing directories return an empty bundle.
4. Tests prove reading the resource does not create scheduler projection or
   local trajectory artifacts.
5. Prompt/status docs are updated.
6. Focused validation and hygiene checks pass.

## Implementation Notes

### 2026-06-18 — Read-only Resource

Added:

- `src.mcp.tools.HOST_EVIDENCE_BUNDLE_RESOURCE_URI`
- `GovernanceTools.list_resources()` entry for
  `dbc://host-evidence/bundle`
- `GovernanceTools.read_resource("dbc://host-evidence/bundle")`

The resource returns stable JSON from `read_host_evidence_bundle()`:

```text
project_root
evidence_dir
evidence_count
summaries[]
```

It is a read-only resource. It does not execute fake or real providers, does
not initialize scheduler state, does not refresh scheduler projection, and does
not mutate Local Work Trajectory.

Validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_mcp_prompts_resources.py -k "host_evidence_bundle or resources"
24 passed

.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "host_evidence_bundle"
2 passed
```

Close-review evidence:

- `review/host-evidence-mcp-resource-exposure-2026-06-18.md`
