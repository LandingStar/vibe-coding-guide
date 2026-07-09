# Readback Inspection CLI/MCP Surface

## Document Position

This planning gate follows the completed log-like readback coverage slices:

- `design_docs/stages/planning-gate/2026-07-08-scheduler-event-readback-envelope.md`
- `design_docs/stages/planning-gate/2026-07-09-runtime-invocation-readback-envelope.md`
- `design_docs/stages/planning-gate/2026-07-09-exchange-communication-readback-envelope.md`
- `design_docs/stages/planning-gate/2026-07-09-worker-report-trajectory-suggestion-readback-envelope.md`
- `design_docs/stages/planning-gate/2026-07-09-validation-doctor-self-check-readback-envelope.md`
- `design_docs/stages/planning-gate/2026-07-09-ui-screenshot-host-evidence-readback-envelope.md`

Date: 2026-07-09

Status: `completed`

## Goal

Expose the completed readback projections through a single read-only operator
entrypoint, first as runtime helper + CLI + MCP tool.

The surface should let an operator or agent inspect known record families
without writing custom Python and without accidentally triggering a consume,
provider run, scheduler mutation, ExchangeArtifact lifecycle transition, or
Local Work mutation.

## Supported First-Slice Kinds

The first unified surface supports:

- `worker-report`
- `validation-receipt`
- `runtime-invocation-log`
- `scheduler-event-log`
- `exchange-artifact`
- `host-evidence`

Each kind maps to the already implemented envelope helper for that family.

## Scope

In scope:

- Add a runtime request/result helper for readback inspection.
- Add CLI:
  `doc-based-coding readback inspect --kind <kind> ...`
- Add MCP:
  `readbackInspect`
- Return envelope dictionaries and compact source/count/error metadata.
- Provide safe path resolution under the requested project root for relative
  paths.

Out of scope:

- Consuming worker trajectory reports.
- Running validation, doctor, providers, browsers, or screenshots.
- Mutating scheduler, ExchangeArtifact lifecycle, evidence files, config, or
  Local Work Trajectory.
- Adding persistent `.dbc` indexes.
- Building cross-family timeline ordering.
- Changing source record schemas or persistence.

## Acceptance Criteria

- Each supported kind has at least one focused test.
- CLI help clearly states read-only behavior and non-goals.
- MCP tool schema exposes the same kind/path/id/version/latest-limit knobs.
- Readback results include authority split fields showing no mutation and no
  provider/browser execution.
- Unknown kind and missing required selectors produce clear error messages.
- Existing focused readback tests continue to pass.

## Implementation

Runtime:

- `src/runtime/orchestration/readback_inspection.py`
- `src/runtime/orchestration/__init__.py`

CLI:

- `doc-based-coding readback inspect`
- `python -m src readback inspect`
- Implementation in `src/__main__.py`

MCP:

- Tool: `readbackInspect`
- Method: `GovernanceTools.readback_inspect()`
- Schema/routing in `src/mcp/server.py` and `src/mcp/tools.py`

The first surface returns `ReadbackInspectionResult.to_json_dict()` with:

- `ok`, `kind`, `project_root`, `source_path`, `record_count`
- readback `envelopes`
- selector metadata and structured errors
- authority split flags confirming read-model-only behavior and no consume,
  validation/doctor run, provider/browser execution, screenshot capture,
  scheduler/exchange/evidence/config mutation, or Local Work mutation.

Relative paths resolve under the requested project root and are rejected if
they escape that root. Explicit absolute paths remain an operator-selected
path.

## Validation Evidence

- `python -m pytest tests/test_runtime_orchestration.py -k "readback_inspection" -q`
  - `3 passed, 495 deselected`
- `python -m pytest tests/test_cli.py -k "readback_inspect" -q`
  - `2 passed, 182 deselected`
- `python -m pytest tests/test_mcp_tools.py -k "ReadbackInspectMcp" -q`
  - `2 passed, 114 deselected`
- `python -m compileall src/runtime/orchestration/readback_inspection.py src/__main__.py src/mcp/tools.py src/mcp/server.py`
  - passed
- `python -m src validate`
  - passed, no governance blocks
- `git diff --check`
  - no whitespace errors; Windows line-ending warnings only

## Expected Follow-up

After this surface is stable, a later gate can add a batch/index timeline that
aggregates several readback families into one ordered stream. That is not part
of this slice.
