# Host UX Cleanup Evidence Readback Linkage

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/cleanup-runner-cli-mcp-surface-followup-direction-analysis.md`
recommends adding visibility after CLI/MCP cleanup invocation.

Current chain:

```text
sandbox_allocation_receipt_evidence
-> scheduler cleanup-receipts / schedulerCleanupReceipts
-> updated cleanup receipt evidence
-> readback / Host UX visibility (this gate)
```

## Goal

Expose cleanup evidence facts through existing readback and Host UX surfaces so
operators can inspect whether git-worktree cleanup has run, which allocation
receipts still require cleanup, and which updated evidence artifact should be
opened next.

The first slice should prove:

1. readback/presentation can consume one explicit durable
   `sandbox_allocation_receipt_evidence` path;
2. cleanup state counts and git-worktree receipt facts are available as
   JSON-safe read-only data;
3. Host UX can display those facts without invoking cleanup;
4. the path remains side-effect-free for scheduler state, runtime providers,
   daemon loop, projection refresh, and Local Work Trajectory;
5. backend and Host UX tests cover empty/missing and populated cleanup evidence
   states.

## Scope

1. Define the minimal cleanup evidence readback facts needed by Host UX.
2. Reuse existing durable receipt summary helpers instead of creating a new
   evidence contract.
3. Bind explicit cleanup evidence readback into the existing Host Evidence or
   Scheduler Operator presentation path.
4. Add focused backend and Host UX tests.
5. If the VS Code webview is touched, validate with a screenshot-style tool.
6. Update status docs and review evidence on close.

## Non-Goals

1. No Host UX cleanup button.
2. No background cleanup daemon.
3. No daemon-loop git-worktree opt-in.
4. No default evidence discovery or broad filesystem search.
5. No scheduler admission schema changes.
6. No live Qoder/runtime expansion.
7. No Local Work Trajectory mutation from runtime/CLI/MCP/Host UX code.

## Validation

Minimum validation:

1. `python -m py_compile` over touched backend modules.
2. Focused backend tests for cleanup evidence readback.
3. Focused VS Code/Host UX tests if webview files are touched.
4. Screenshot-style validation if any rendered UI changes.

## Write-Back Targets

On close, update:

1. `design_docs/Project Master Checklist.md`
2. `design_docs/Global Phase Map and Current Position.md`
3. `.codex/checkpoints/latest.md`
4. `review/host-ux-cleanup-evidence-readback-linkage-2026-06-21.md`

## Completion Criteria

This gate is complete when cleanup evidence can be read and displayed from an
explicit durable receipt evidence path, the display remains read-only and
side-effect-free, and validation proves both backend product shape and Host UX
rendering behavior.

## Close Summary

Completed on 2026-06-21.

Implemented by extending the existing `dbc://host-evidence/presentation`
readback path rather than adding a new Host UX resource. `HostEvidenceBundle`
now accepts `sandbox_allocation_receipt_evidence` artifacts through the durable
receipt summary helper, and the presentation builder emits read-only
`Sandbox cleanup evidence ...` cards with allocation count, git-worktree count,
cleanup required/completed/failed counts, cleanup execution clue, source
evidence refs, worktree refs, and Local Work Trajectory mutation authority
clues.

The card status is derived from cleanup state facts:

1. failed cleanup receipts render as `failed` / `cleanup_failed`;
2. still-required cleanup renders as `partial` / `cleanup_required`;
3. completed or already-settled allocation evidence renders as `completed` /
   `cleanup_settled`.

This gate did not add a cleanup button, daemon cleanup loop, broad evidence
discovery, scheduler schema change, live runtime expansion, or runtime-owned
Local Work Trajectory mutation.

## Validation Result

Passed:

1. `.\.venv\Scripts\python.exe -m py_compile tools/progress_graph/host_evidence.py tests/test_progress_graph_trajectory.py tests/test_mcp_prompts_resources.py`
2. `.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "sandbox_allocation_cleanup_evidence or cleanup_evidence_failed_state_takes_precedence or host_evidence_bundle_reads_scheduler_loop_evidence_summary" -q`
   - `3 passed, 65 deselected`
3. `.\.venv\Scripts\python.exe -m pytest tests/test_mcp_prompts_resources.py -k "cleanup_receipt_cards or host_evidence_presentation" -q`
   - `4 passed, 24 deselected`
4. `.\.venv\Scripts\python.exe -m pytest tests/test_progress_graph_trajectory.py -k "host_evidence" -q`
   - `8 passed, 59 deselected`
5. `.\.venv\Scripts\python.exe -m pytest tests/test_mcp_prompts_resources.py -k "host_evidence" -q`
   - `7 passed, 21 deselected`
6. `npm run build`
   - workdir: `vscode-extension`
7. `node --test "dist/test/progressGraphPreviewHtml.test.js"`
   - `16 passed`
8. `node --test "dist/test/progressGraphPreviewPanel.test.js"`
   - `11 passed`
9. Screenshot-style validation:
   - full page artifact:
     `output/playwright/host-evidence-ui/cleanup-evidence-panel.png`
   - focused Host Evidence element artifact:
     `output/playwright/host-evidence-ui/cleanup-evidence-panel-element.png`
   - element capture also asserted both completed and failed cleanup evidence
     cards plus `cleanup_failed` rendered text.

## Review And Follow-Up

Review evidence:

- `review/host-ux-cleanup-evidence-readback-linkage-2026-06-21.md`

Follow-up direction:

- `design_docs/host-ux-cleanup-evidence-readback-linkage-followup-direction-analysis.md`
