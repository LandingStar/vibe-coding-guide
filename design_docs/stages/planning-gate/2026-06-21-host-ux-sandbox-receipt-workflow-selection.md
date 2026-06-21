# Host UX Selection For Sandbox Receipt Workflow

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/host-sandbox-receipt-workflow-cli-mcp-surface-followup-direction-analysis.md`
recommends a Host UX flow over the now-stable sandbox receipt workflow surface.

## Goal

Add a thin Host UX binding that lets an operator provide a sandbox allocation
receipt evidence path, explicitly confirm cleanup, invoke the existing workflow
surface, and refresh/read the Host Evidence presentation after completion.

## First Slice Scope

1. Add a manual evidence path input in the existing Progress Graph Preview /
   Scheduler Operator Host UX area.
2. Add an explicit cleanup action with a confirmation step before invoking
   cleanup.
3. Invoke the existing shared surface rather than duplicating workflow logic in
   the webview.
4. Show the latest action result and refresh Host Evidence readback after the
   action completes.
5. Add focused UI/contract tests.
6. Validate with screenshot-style tooling.

## Non-Goals

1. No automatic evidence file discovery/listing in this first slice.
2. No default cleanup or cleanup daemon.
3. No live Qoder or real-provider expansion.
4. No scheduler admission schema changes.
5. No scheduler projection refresh as part of this action.
6. No Local Work Trajectory mutation from Host UX/CLI/MCP/runtime code.

## Validation

Minimum validation:

1. VS Code extension compile/build for touched TypeScript.
2. Focused webview/contract tests for:
   - manual evidence path state;
   - cleanup confirmation requirement;
   - workflow action message shape;
   - readback refresh after completion.
3. Screenshot-style validation of the Host UX control and readback area.

## Write-Back Targets

On close, update:

1. `design_docs/Project Master Checklist.md`
2. `design_docs/Global Phase Map and Current Position.md`
3. `.codex/checkpoints/latest.md`
4. `review/host-ux-sandbox-receipt-workflow-selection-2026-06-21.md`

## Completion Criteria

This gate is complete when the Host UX exposes a clear, manually supplied
receipt evidence path flow with explicit cleanup confirmation and visible
readback refresh, while the actual workflow execution remains delegated to the
shared CLI/MCP/backend surface.

## Close Summary

Completed 2026-06-21.

Implemented the first thin Host UX slice:

1. added a `Sandbox Receipt Cleanup` control to the existing VS Code Progress
   Graph Preview / Scheduler Operator card;
2. required a manually supplied `sandbox_allocation_receipt_evidence` path and
   an explicit cleanup confirmation checkbox before the webview posts the
   action;
3. added `cleanupReceipts` to the shared Scheduler Operator action contract;
4. mapped the action to the existing CLI cleanup surface
   `doc-based-coding scheduler cleanup-receipts`;
5. summarized cleanup result payloads as cleaned / failed / skipped counts and
   output evidence id;
6. preserved Host Evidence readback as the post-action visible status surface.

This slice intentionally uses the explicit cleanup path for manual existing
receipt evidence. Full allocate/read/cleanup/read workflow selection remains a
future Host UX slice because it needs additional source repo, sandbox root, and
allocation inputs that are outside this first manual evidence path control.

Validation:

1. VS Code extension build passed.
2. Focused Scheduler Operator / Progress Graph Preview node tests passed:
   `32 passed`.
3. CLI cleanup focused pytest passed: `3 passed, 37 deselected`.
4. Host Evidence cleanup readback focused pytest passed:
   `2 passed, 66 deselected`.
5. Screenshot-style validation artifact:
   `output/playwright/host-ux-sandbox-receipt-workflow/host-ux-cleanup-fixture.png`.
