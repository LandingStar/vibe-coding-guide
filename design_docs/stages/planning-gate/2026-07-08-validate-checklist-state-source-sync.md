# Validate Checklist State Source Sync

## Document Position

This planning gate scopes one narrow consistency fix for current-state
readback.

Related previous gate:

- `design_docs/stages/planning-gate/2026-07-02-next-action-state-source-sync.md`

Date: 2026-07-08
Status: Completed

## Problem

`get_next_action` already prefers the Checklist hot-state over stale checkpoint
or handoff metadata. `doc-based-coding validate` still reports current phase
and active planning gate through `Pipeline.check_constraints()`, which can read
stale `.codex/checkpoints/latest.md` data before the current Checklist state.

Observed symptom:

- Checklist says there is no active planning gate after
  `Scheduler Event Readback Envelope`.
- `get_next_action` reports no active planning gate.
- `validate` still reports the old `Evidence Publish To Consumer Closure`
  checkpoint gate.

## This Slice Does

- Move or duplicate the Checklist hot-state read logic into the workflow
  pipeline layer so `Pipeline.check_constraints()` can resolve current state
  consistently.
- Prefer Checklist `Current Phase` and `Active Planning Gate` when present.
- If Checklist declares no active planning gate and has a latest completed gate,
  clear stale checkpoint-derived active gates.
- Add a `state_source` readback field to constraint output.
- Add focused tests for direct `_check_constraints()` and CLI `validate`.

## This Slice Does Not Do

- Does not rewrite checkpoint or handoff files.
- Does not redesign safe-stop writeback.
- Does not alter `get_next_action` behavior except through shared state
  consistency if it reuses the updated constraint result.
- Does not change planning-gate status scanning beyond avoiding stale active
  gate leakage when Checklist declares the current hot-state.

## Acceptance

- In a workspace with a stale checkpoint active gate and a Checklist with
  latest completed gate plus no active gate, `_check_constraints()` returns:
  - `current_phase` from Checklist
  - `active_planning_gate=""`
  - `state_source="checklist"`
- CLI `validate` reports the same state.
- Existing initial-state and active-project C5 behavior remains intact.
- Focused tests pass.
- `git diff --check` passes.

## Validation Plan

- `python -m pytest tests/test_mcp_tools.py -k "check_constraints" -q`
- `python -m pytest tests/test_cli.py -k "validate" -q`
- `python -m compileall -q src/workflow/pipeline.py src/mcp/tools.py src/__main__.py tests/test_mcp_tools.py tests/test_cli.py`
- `git diff --check`

## Implementation Outputs

- Added shared Checklist hot-state parsing to `src/workflow/pipeline.py`.
- Added `ConstraintResult.state_source` and included it in constraint JSON
  output.
- Updated `_check_constraints()` to prefer Checklist current phase and active
  planning gate over stale checkpoint state.
- When Checklist declares no active gate and has a latest completed planning
  gate, `_check_constraints()` now clears stale checkpoint-derived active gates
  and prevents planning-gate directory guessing from reintroducing them.
- Removed duplicate Checklist parser logic from `src/mcp/tools.py`; MCP
  `get_next_action` now uses `constraints.state_source`.
- Added focused direct constraint and CLI validate tests.

## Validation Results

- `python -m pytest tests/test_mcp_tools.py -k "check_constraints or next_action" -q`
  - Result: `15 passed, 99 deselected`
- `python -m pytest tests/test_cli.py -k "validate or check" -q`
  - Result: `8 passed, 174 deselected`
- `python -m pytest tests/test_workspace_dbc_command_relay.py -q`
  - Result: `3 passed`
- `python -m compileall -q src/workflow/pipeline.py src/mcp/tools.py src/__main__.py src/runtime/orchestration/workspace_dbc_command_relay.py tests/test_mcp_tools.py tests/test_cli.py tests/test_workspace_dbc_command_relay.py`
  - Result: passed
- `python -m src validate`
  - Result: passed and reported `state_source=checklist`,
    `active_planning_gate=design_docs/stages/planning-gate/2026-07-08-validate-checklist-state-source-sync.md`
- `python -m src check`
  - Result: passed and reported the same Checklist-derived active gate.
- `git diff --check`
  - Result: passed; only Windows LF-to-CRLF working-copy warnings were emitted.

## Operational Note

The already-running MCP server process may continue to return stale
`workspaceDbcCommand(validate)` output through the in-process relay until the
MCP host is restarted. Direct CLI execution exercises the updated code path
immediately.

Closed on 2026-07-08.
