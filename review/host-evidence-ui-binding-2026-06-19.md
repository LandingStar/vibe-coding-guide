# Review - Host Evidence UI Binding

> Date: 2026-06-19
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-19-host-evidence-ui-binding.md`

## Scope Reviewed

This slice bound the existing read-only host evidence presentation resource into
the VS Code progress graph preview.

Implemented:

1. Added a VS Code-side resource reader for `dbc://host-evidence/presentation`.
2. Reused the existing runtime/source-root resolution path instead of parsing raw
   evidence artifacts in UI code.
3. Added a presentation-only UI model for Host Evidence cards, facts, refs,
   authority clues, malformed evidence rows, and read errors.
4. Rendered a Host Evidence operator section in the preview control overlay.
5. Added focused HTML and panel tests for empty, card, malformed-row, backend
   read-error, and read-only wiring states.

## Evidence

Automated validation:

```text
npm run build
build complete
```

```text
node --test "dist/test/progressGraphPreviewHtml.test.js" "dist/test/progressGraphPreviewPanel.test.js"
21 passed
```

Backend resource smoke:

```text
.\.venv\Scripts\python.exe -m src resources read dbc://host-evidence/presentation
status=empty
card_count=0
error_count=0
```

Screenshot validation:

```text
output/playwright/host-evidence-ui/host-evidence-panel.png
```

The screenshot fixture showed:

1. degraded host evidence status;
2. scheduler-loop evidence card;
3. runtime provider, host surface, invocation, stop reason, run count;
4. scheduler projection path/role and authority clues;
5. malformed evidence error row.

## Behavioral Notes

The UI consumes `dbc://host-evidence/presentation` as already-shaped read-only
data. It does not inspect raw evidence files directly and does not duplicate the
backend evidence classification rules.

If the resource read fails, the preview still renders a Host Evidence failed
state instead of hiding the section or blocking the rest of the preview.

## Authority Boundary

This slice did not:

1. execute providers;
2. add real-provider CLI/MCP surfaces;
3. start or manage a background daemon;
4. mutate scheduler state from UI;
5. mutate ExchangeArtifact store or admission ledger state;
6. mutate agent-owned Local Work Trajectory;
7. change the backend host evidence presentation schema;
8. redesign the full progress graph or trajectory UI.

## Residual Risk

The current VS Code preview files already had unrelated uncommitted UI work
before this slice. Commit staging must remain scoped to Host Evidence changes or
explicitly acknowledge any accumulated UI baseline commit.

## Follow-Up

The next useful line is not another evidence display tweak. The product surface
now exposes scheduler-loop evidence well enough for operator inspection, so the
next slice should either:

1. add a scheduler admission / host evidence operator workflow surface, if the
   goal remains UI-driven operation; or
2. return to backend orchestration with live credentialed provider smoke, when
   Qoder readiness is available.
