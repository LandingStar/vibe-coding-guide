# Planning Gate - Next Action State Source Sync

Date: 2026-07-02

Status: COMPLETED

## Purpose

Fix `get_next_action` so completion-boundary guidance follows the current
Checklist hot-state instead of stale checkpoint/handoff safe-stop metadata.

After recent completed gates, `get_next_action` still returned the old
`Evidence Publish To Consumer Closure` checkpoint gate. Current project rules
say `.codex/checkpoints/latest.md` and `.codex/handoffs/CURRENT.md` are
auxiliary recovery surfaces and must not override a newer Checklist focus.

## Scope

- Add a narrow Checklist hot-state read path for `get_next_action`.
- Prefer Checklist `Current Phase` / latest completed planning gate when the
  Checklist does not declare an active planning gate.
- Keep `check_constraints` behavior unchanged for this slice.
- Add focused MCP tool tests.
- Update Checklist and Local Work Trajectory.

## Non-Goals

- Do not rewrite checkpoint or handoff files.
- Do not redesign safe-stop writeback bundles.
- Do not change progress graph projection.
- Do not broaden into global state-source architecture.

## Acceptance Criteria

1. In a workspace with a stale checkpoint active gate but a newer Checklist
   latest-completed gate, `get_next_action` reports no active planning gate and
   asks for next direction.
2. The response exposes the Checklist-derived phase and a `state_source`
   indicator.
3. Existing completion-boundary reminder behavior remains intact.
4. Focused tests, `py_compile`, and `git diff --check` pass.

## Completion Notes

Implemented on 2026-07-02.

`get_next_action` now reads the Checklist hot-state before composing the final
recommendation. When the Checklist has a latest completed planning gate and no
active planning gate, it clears stale checkpoint-derived active gates and marks
the response with:

```text
state_source=checklist
```

This keeps `.codex/checkpoints/latest.md` and `.codex/handoffs/CURRENT.md` as
auxiliary recovery surfaces without letting them override the newer Checklist
focus.

Added focused MCP test:

```text
test_next_action_prefers_checklist_hot_state_over_stale_checkpoint
```

Validation passed:

```text
python -m py_compile src/runtime/orchestration/runtime_adapter.py src/runtime/orchestration/runtime_wiring.py src/runtime/orchestration/leader_worker_codex_delivery.py src/mcp/tools.py tests/test_runtime_orchestration.py tests/test_mcp_tools.py

python -m pytest tests/test_mcp_tools.py -k "next_action" -q
5 passed, 105 deselected

python -m pytest -k smoke -q --color=no
52 passed, 1 skipped, 2236 deselected

git diff --check -- pyproject.toml src/runtime/orchestration/runtime_adapter.py src/runtime/orchestration/runtime_wiring.py src/runtime/orchestration/leader_worker_codex_delivery.py src/mcp/tools.py tests/test_runtime_orchestration.py tests/test_mcp_tools.py docs/opencode-host-provisioning-check-guide.md "design_docs/Project Master Checklist.md" design_docs/stages/planning-gate/2026-07-02-pytest-collection-hygiene.md design_docs/stages/planning-gate/2026-07-02-compact-context-hydration-smoke.md design_docs/stages/planning-gate/2026-07-02-next-action-state-source-sync.md .codex/progress-graph/local-work-trajectory.json
```

`git diff --check` reported no whitespace errors; it only emitted Windows
LF/CRLF normalization warnings for already-edited tracked files.

Direct in-process verification on this workspace now returns:

```json
{
  "state_source": "checklist",
  "active_planning_gate": "",
  "ask_user": true
}
```

The already-running MCP server process may still return the stale checkpoint
gate until the host reloads the updated code.
