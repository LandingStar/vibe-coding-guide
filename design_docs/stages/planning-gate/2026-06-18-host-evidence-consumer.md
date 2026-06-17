# Planning Gate — Host Evidence Consumer

> Date: 2026-06-18
> Status: COMPLETED

## Trigger

`design_docs/stages/planning-gate/2026-06-17-credentialed-live-qoder-smoke.md`
has closed as readiness-negative evidence.

The previous slices now produce or describe these host-run evidence products:

- `HostSchedulerRunEvidence`
- `run_host_runtime_dogfood_harness()`
- `run_host_owned_qoder_smoke()`
- `review/credentialed-live-qoder-smoke-2026-06-17.md`

## Problem

Host-run evidence JSON exists as a compact review artifact, but consumers still
need a stable read-only projection before UI, MCP, or release tooling can show
it safely. Reading raw evidence JSON directly would expose too much shape,
including the embedded `host_result`, and would make later UI code depend on a
writer product instead of a consumer contract.

## Scope

### Slice 1 — Runtime Evidence Summary

Add a strict reader for persisted `host_scheduler_run_evidence` JSON:

1. Validate `product_type` and `schema_version`.
2. Project only compact host-facing fields.
3. Exclude embedded `host_result` from the summary payload.
4. Fail with field-specific errors for malformed evidence.

### Slice 2 — Progress Graph Bundle

Add a host/progress-side helper:

1. Read `.codex/scheduler/evidence/*.json`.
2. Return an empty bundle when the directory does not exist.
3. Return compact summaries for host preview or future MCP/UI consumers.
4. Do not execute providers, initialize scheduler state, or mutate Local Work
   Trajectory.

### Slice 3 — Prompt / Status Writeback

Update guidance so agents know:

1. Evidence JSON is read through the consumer summary, not through raw UI
   scraping.
2. Readiness-negative live smoke remains review-doc evidence unless an evidence
   JSON artifact actually exists.
3. The consumer is read-only and does not make live-provider readiness true.

## Non-Goals

This gate does not:

1. Add a VS Code webview UI consumer.
2. Expose a new MCP tool.
3. Install `qoder-agent-sdk` or provision Qoder credentials.
4. Add scheduler daemon behavior.
5. Synthesize fake evidence JSON for readiness-negative outcomes.
6. Read raw transcripts, raw SDK logs, or credential material.

## Acceptance Criteria

The gate may close when:

1. Runtime reader and progress-graph bundle are implemented.
2. Tests cover successful summary reads, missing evidence directory, and invalid
   product/schema rejection.
3. Existing host dogfood / Qoder smoke behavior remains unchanged.
4. Prompt/status docs explain the read-only consumer boundary.
5. Focused validation and hygiene checks pass.

## Implementation Notes

### 2026-06-18 — Read-only Consumer

Added:

- `HostSchedulerRunEvidenceSummary`
- `read_host_scheduler_run_evidence_summary()`
- `read_host_scheduler_run_evidence_summaries()`
- `tools.progress_graph.read_host_evidence_bundle()`
- `tools.progress_graph.host_scheduler_evidence_dir()`

The summary payload retains:

- evidence id / timestamp / path
- runtime providers
- host invocation
- run count / stop reason / stop detail
- ready / blocked / failed / permission-review task ids
- output artifact refs
- snapshot / event-log / scheduler-projection paths
- authority split
- history summary
- metadata

It deliberately omits embedded `host_result` so downstream UI or MCP consumers
depend on the compact consumer contract, not the raw writer artifact.

Validation:

```text
.\.venv\Scripts\python.exe -m pytest tests/test_runtime_orchestration.py -k "host_scheduler_run_evidence"
4 passed

.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "host_evidence_bundle or host_runtime_dogfood_harness_fake"
3 passed
```

Close-review evidence:

- `review/host-evidence-consumer-2026-06-18.md`

### 2026-06-18 — Close Review

The gate is closed as `COMPLETED`.

The consumer boundary is accepted because:

1. Runtime and progress-graph read helpers exist.
2. The exposed summary contract omits embedded `host_result`.
3. Missing evidence directories return an empty bundle.
4. Invalid evidence product type is rejected with a clear error.
5. Focused runtime / progress trajectory / prompt-resource validation passed.

Follow-up direction:

- `design_docs/host-evidence-consumer-followup-direction-analysis.md`
