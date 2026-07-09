# Readback Explicit-Source Timeline Projection

## Document Position

This planning gate follows the completed unified readback inspection surface:

- `design_docs/stages/planning-gate/2026-07-09-readback-inspection-cli-mcp-surface.md`
- `design_docs/readback-inspection-followup-direction-analysis.md`

Date: 2026-07-09

Status: `completed`

## Goal

Add a read-only timeline projection over explicit readback sources.

The first implementation must let an operator or agent provide known sources,
reuse the existing `inspect_readback()` family projections, and receive a
single compact timeline row stream without introducing workspace-wide source
discovery or a persistent `.dbc` manifest.

## Execution Order

1. Runtime helper first.
2. Thin CLI second.

This ordering keeps the projection contract testable before adding command-line
syntax.

## Scope

In scope:

- Add a runtime helper:
  `inspect_readback_timeline()`.
- Accept explicit source specs only.
- Call existing `inspect_readback()` for each source.
- Preserve each source result and its original envelopes.
- Flatten source envelopes into compact timeline rows.
- Sort rows by parsed timestamp when available.
- Preserve source/record order for missing or unparseable timestamps, and mark
  ordering confidence explicitly.
- Isolate partial source failures so one bad source does not erase successful
  rows.
- Add a thin CLI:
  `doc-based-coding readback timeline`.

Out of scope:

- Persistent `.dbc` source manifest or index.
- Workspace-wide scanning or auto-discovery.
- MCP exposure.
- Monitoring UI.
- Readback envelope schema migration.
- Source log persistence changes.
- Provider, browser, validation, doctor, scheduler, ExchangeArtifact, evidence,
  config, or Local Work mutation.

## Acceptance Criteria

- Runtime tests cover a mixed explicit-source timeline.
- Runtime tests cover missing or invalid timestamp ordering confidence.
- Runtime tests cover partial failure where at least one source succeeds.
- Runtime result authority split is read-model-only and shows no mutation or
  provider/browser execution.
- CLI help describes explicit-source and read-only boundaries.
- CLI tests cover JSON source specs and timeline output.
- Existing readback inspection tests continue to pass.

## Validation Evidence

- `python -m pytest tests/test_runtime_orchestration.py -k "readback_timeline" -q`
  - `3 passed, 498 deselected`
- `python -m pytest tests/test_cli.py -k "readback_timeline" -q`
  - `2 passed, 184 deselected`
- `python -m pytest tests/test_runtime_orchestration.py -k "readback_timeline or readback_inspection" -q`
  - `6 passed, 495 deselected`
- `python -m pytest tests/test_cli.py -k "readback_timeline or readback_inspect" -q`
  - `4 passed, 182 deselected`
- `python -m compileall src/runtime/orchestration/readback_timeline.py src/__main__.py src/runtime/orchestration/__init__.py`
  - passed
- `python -m src validate`
  - passed, no governance blocks
- `git diff --check`
  - no whitespace errors; Windows line-ending warnings only

## Implementation

Runtime:

- `src/runtime/orchestration/readback_timeline.py`
- `ReadbackTimelineSource`
- `ReadbackTimelineInspectionRequest`
- `ReadbackTimelineRow`
- `ReadbackTimelineInspectionResult`
- `inspect_readback_timeline()`

CLI:

- `doc-based-coding readback timeline --source-spec PATH`
- `doc-based-coding readback timeline --source-json JSON`

The helper preserves original source inspection results and exposes compact
timeline rows with ordering confidence. It remains read-model-only and does not
write a persistent source manifest or scan the workspace.

## Expected Follow-up

Later gates can choose among:

- a persistent `.dbc` source manifest / index;
- promoting the log-like record standard draft into `docs/`;
- monitoring UI consumption of the timeline/readback products;
- MCP exposure for timeline inspection if operators need model-facing parity.
