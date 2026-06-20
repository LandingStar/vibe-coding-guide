# Host UX Cleanup Evidence Readback Linkage Review

> Date: 2026-06-21
> Planning Gate: `design_docs/stages/planning-gate/2026-06-21-host-ux-cleanup-evidence-readback-linkage.md`

## Summary

The slice connected durable `sandbox_allocation_receipt_evidence` artifacts to
the existing Host Evidence readback/presentation surface. No new cleanup
execution control was added to Host UX.

The chosen binding point is `dbc://host-evidence/presentation`, because
`tools/progress_graph/host_evidence.py` already owns safe readback from
`.codex/scheduler/evidence/*.json` and the VS Code progress graph preview
already renders backend-shaped Host Evidence cards from that resource.

## Implementation

Backend:

- `tools/progress_graph/host_evidence.py`
  - accepts `SANDBOX_ALLOCATION_RECEIPT_EVIDENCE_PRODUCT_TYPE`;
  - reads artifacts with `read_sandbox_allocation_receipt_evidence_summary()`;
  - renders `Sandbox cleanup evidence <id>` cards;
  - exposes allocation count, git-worktree count, cleanup required/completed/
    failed counts, cleanup execution authority clue, source evidence refs,
    worktree refs, branch refs, and Local Work Trajectory mutation clue;
  - treats failed cleanup receipts as failed before considering
    `cleanup_required`, so a failed cleanup is not misreported as merely
    pending cleanup.

Tests:

- `tests/test_progress_graph_trajectory.py`
  - covers cleanup receipt card presentation;
  - covers failed cleanup state precedence.
- `tests/test_mcp_prompts_resources.py`
  - covers `GovernanceTools.read_resource("dbc://host-evidence/presentation")`
    returning cleanup receipt cards.
- `vscode-extension/src/test/progressGraphPreviewHtml.test.ts`
  - covers rendered Host Evidence HTML for cleanup receipt cards.

## Validation

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

Screenshot-style validation:

- `output/playwright/host-evidence-ui/cleanup-evidence-panel.png`
- `output/playwright/host-evidence-ui/cleanup-evidence-panel-element.png`

The full-page screenshot exposed that the later V2 Graph panel can visually
overlap the lower part of the Host Evidence section in this fixture. A focused
element screenshot was therefore also taken and verified; it shows completed
and failed cleanup cards, including `cleanup_failed`, without relying on manual
DOM inspection.

## Boundary Confirmation

This slice did not:

- add a Host UX cleanup button;
- start a background cleanup daemon;
- enable daemon-loop git-worktree provider opt-in;
- add default evidence discovery;
- change scheduler admission or evidence schemas;
- run live Qoder/runtime paths;
- mutate Local Work Trajectory from runtime, CLI, MCP, or Host UX code.

## Residual Risk

The current Host Evidence panel is still generic card rendering. It is now
factually correct for cleanup receipts, but a future Host UX cleanup action
would need a more explicit selection model before it is safe to expose as a
button.
