# Readback Timeline MCP Parity

## Document Position

This planning gate follows:

- `design_docs/stages/planning-gate/2026-07-09-readback-explicit-source-timeline-projection.md`
- `design_docs/readback-timeline-followup-direction-analysis.md`

Date: 2026-07-09

Status: `completed`

## Goal

Expose the completed explicit-source readback timeline projection through a
read-only MCP tool for Codex/agent-facing workflows.

The new MCP surface should reuse `inspect_readback_timeline()` and return the
same runtime result shape while preserving the explicit-source-only and
read-model-only boundary.

## Scope

In scope:

- Add a `GovernanceTools` method for timeline inspection.
- Add MCP tool schema/routing:
  `readbackTimelineInspect`.
- Accept explicit source specs only.
- Reuse `ReadbackTimelineSource` and `ReadbackTimelineInspectionRequest`.
- Return `ReadbackTimelineInspectionResult.to_json_dict()`.
- Add focused MCP tests for method behavior and server schema/routing.

Out of scope:

- Persistent `.dbc` source manifest or index.
- Workspace-wide scanning or auto-discovery.
- Monitoring UI.
- CLI changes beyond the already completed timeline command.
- Timeline row schema changes unless MCP wiring exposes a clear bug.
- Provider, browser, validation, doctor, scheduler, ExchangeArtifact, evidence,
  config, or Local Work mutation.

## Acceptance Criteria

- `GovernanceTools.readback_timeline_inspect()` accepts a `sources` list.
- MCP `readbackTimelineInspect` is listed with an explicit `sources` schema.
- MCP call routes to the runtime helper and returns timeline rows.
- Partial source failure remains isolated.
- Authority split remains read-model-only and reports no workspace scan or
  persistent manifest write.
- Focused MCP tests pass.

## Validation Evidence

- `python -m pytest tests/test_mcp_tools.py -k "ReadbackTimelineInspectMcp or ReadbackInspectMcp" -q`
  - `4 passed, 114 deselected`
- `python -m compileall src/mcp/tools.py src/mcp/server.py`
  - passed
