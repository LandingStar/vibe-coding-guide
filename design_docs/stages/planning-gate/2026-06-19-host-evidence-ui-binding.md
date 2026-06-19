# Planning Gate - Host Evidence UI Binding

> Date: 2026-06-19
> Status: COMPLETED

## Trigger

`design_docs/host-loop-workflow-evidence-metadata-followup-direction-analysis.md`
recommends moving the completed backend evidence/readback chain into a visible
operator UI surface.

## Problem

The backend now exposes a UI-facing read-only presentation resource:

```text
dbc://host-evidence/presentation
```

That presentation can summarize host scheduler run evidence and scheduler-loop
evidence, including runtime provider, host invocation, queue counts, projection
metadata, authority clues, and malformed evidence error rows.

However, the VS Code product surface still requires users to inspect JSON
resources manually. The operator cannot easily see whether host loop evidence
exists, whether a run refreshed scheduler projection, or whether malformed
evidence was isolated.

## Scope

### Slice 1 - Host Evidence Panel Binding

Add a small read-only host evidence section near the existing progress graph /
local trajectory preview surface. It should consume the existing backend
presentation payload instead of reimplementing evidence parsing in UI code.

The UI should show:

1. overall presentation status;
2. card count and error count;
3. per-card title/status/severity;
4. runtime providers, host surface, invocation id;
5. stop reason/detail and run count;
6. key facts, refs, and authority clues;
7. malformed evidence error rows.

### Slice 2 - Refresh And Empty States

Preserve existing refresh behavior and add host evidence readback to the same
refresh cycle or adjacent panel update path.

The UI should have useful states for:

1. no evidence present;
2. valid cards;
3. malformed evidence rows;
4. backend read errors.

### Slice 3 - Validation

Cover:

1. unit tests for HTML/data mapping;
2. existing VS Code preview tests adjusted for the new section;
3. screenshot validation through Playwright or an equivalent screenshot tool.

## Non-Goals

This gate does not:

1. Execute providers.
2. Add real-provider CLI/MCP surfaces.
3. Start or manage a background daemon service.
4. Mutate scheduler state.
5. Mutate ExchangeArtifact store or admission ledger state.
6. Mutate agent-owned Local Work Trajectory.
7. Change `dbc://host-evidence/presentation` backend schema.
8. Redesign the full progress graph or trajectory UI.

## Acceptance Criteria

The gate may close when:

1. The VS Code preview surface exposes host evidence presentation data in a
   readable operator section.
2. The UI consumes the backend presentation payload as read-only data.
3. Empty, card, and error row states are represented.
4. Tests cover the mapping/rendering behavior.
5. Screenshot validation captures the rendered UI.
6. Review/status docs record that provider execution, daemon lifecycle,
   scheduler mutation, ExchangeArtifact/admission mutation, and Local Work
   Trajectory mutation remain deferred.

## Completion Notes

Completed on 2026-06-19.

Implemented:

1. VS Code progress graph preview now reads the existing read-only
   `dbc://host-evidence/presentation` resource through the same Python runtime
   resolution path used by progress graph artifact refresh.
2. The preview state now carries a presentation-only Host Evidence model with
   empty, card, malformed-row, and backend read-error states.
3. The floating preview chrome renders a Host Evidence operator section near the
   existing runtime control summary without executing providers or mutating
   scheduler / ExchangeArtifact / Local Work Trajectory state.
4. Focused tests cover empty state, scheduler-loop evidence cards, malformed
   evidence rows, backend read errors, and read-only resource wiring.
5. Screenshot validation captured the rendered Host Evidence panel.

Validation:

```text
npm run build
node --test "dist/test/progressGraphPreviewHtml.test.js" "dist/test/progressGraphPreviewPanel.test.js"
.\.venv\Scripts\python.exe -m src resources read dbc://host-evidence/presentation
npx --yes --cache output/playwright/.npm-cache --package playwright playwright screenshot --channel msedge --viewport-size "1440,1100" --full-page --wait-for-selector "#pgHostEvidencePanel" http://127.0.0.1:<temp-port>/host-evidence-fixture.html output/playwright/host-evidence-ui/host-evidence-panel.png
```

Result:

```text
VS Code extension build passed.
Focused preview tests: 21 passed.
Backend resource smoke returned status=empty in the current workspace.
Screenshot artifact: output/playwright/host-evidence-ui/host-evidence-panel.png
```

Deferred:

1. Provider execution.
2. Real-provider CLI/MCP surfaces.
3. Background daemon lifecycle.
4. Scheduler mutation from the UI.
5. ExchangeArtifact store or admission mutation from the UI.
6. Agent-owned Local Work Trajectory mutation from the UI.
7. Backend host evidence schema changes.
