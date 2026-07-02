# Planning Gate - Monitoring UI Frontend Visual

> Date: 2026-06-28
> Status: COMPLETED

## Trigger

The backend monitoring snapshot API (`docs/monitoring-ui-backend-api.md`) was
completed in a prior gate. The frontend visual design session was identified as
the next required step in `design_docs/monitoring-ui-frontend-expectations.md`.

## Scope

Design and implement the first visual monitoring dashboard that consumes the
read-only backend snapshot API through the VS Code extension webview.

## Design Document

`design_docs/stages/planning-gate/2026-06-28-monitoring-ui-frontend-design.md`

## Implementation

### New Files

| File | Purpose |
|------|---------|
| `vscode-extension/src/views/monitoringPanel.ts` | WebviewPanel manager — CLI invocation, message handling, auto-refresh timer |
| `vscode-extension/src/webviews/monitoringDashboard.tsx` | React app — 6 panels, toolbar, filters, expandable rows |
| `vscode-extension/src/webviews/monitoringDashboard.css` | Operational dashboard CSS with VS Code theme variables |
| `vscode-extension/src/test/fixtures/monitoring/healthy-c9-passed.json` | Happy-path fixture (C9 passed, overlap proven) |
| `vscode-extension/src/test/fixtures/monitoring/missing-live-smoke.json` | Missing smoke report fixture |
| `vscode-extension/src/test/fixtures/monitoring/failed-delivery.json` | Failed delivery fixture (2 failed, 2 pending, smoke not passing) |
| `vscode-extension/scripts/generate-monitoring-fixtures.mjs` | Standalone HTML generator for screenshot validation |
| `vscode-extension/scripts/capture-monitoring-screenshots.mjs` | Playwright screenshot capture script |

### Modified Files

| File | Change |
|------|--------|
| `vscode-extension/src/extension.ts` | Import MonitoringPanel + register open/refresh commands |
| `vscode-extension/package.json` | Add 2 commands + `monitoring.autoRefreshIntervalMs` setting |
| `vscode-extension/esbuild.config.mjs` | Add `monitoringDashboard` webview entry point |

### Architecture

- WebviewPanel (ViewColumn.Two) with React 19 + esbuild IIFE bundle
- Extension host runs `python -m src scheduler inspect-monitoring-snapshot` CLI
- JSON payload injected via `<script type="application/json">` on render
- Bidirectional postMessage: refresh, autoRefresh toggle, copyToClipboard, openDocument
- Auto-refresh uses setInterval in extension host, pauses when panel is hidden
- CSS uses VS Code theme variables with operational status color accents

### Six Panels

1. StatusStrip — ok/NOT OK, next_action, top operator signals, authority integrity check
2. Scheduler — task state counts, waiting/review-required IDs, expandable target states
3. Delivery — state counts, pending Codex count, failed/review-required record tables
4. Runtime Invocations (full-width) — count badges, provider/status/lane filters, expandable invocation detail with attempts
5. Live Codex Smoke — verdict, worker counts, first concurrent batch, overlap pairs
6. Worker Reports — mode, procedure/schema doc links, consumer command, boundary note

## Screenshot Validation

Screenshots generated at 1200px and 480px viewports for all 3 fixtures:

```text
node scripts/generate-monitoring-fixtures.mjs
node scripts/capture-monitoring-screenshots.mjs
```

Output: `vscode-extension/output/monitoring-screenshots/`

| Fixture | Viewport | File | Validated |
|---------|----------|------|-----------|
| healthy-c9-passed | 1200px | healthy-1200px.png | ✓ |
| healthy-c9-passed | 480px | healthy-480px.png | ✓ |
| missing-live-smoke | 1200px | missing-smoke-1200px.png | ✓ |
| missing-live-smoke | 480px | missing-smoke-480px.png | ✓ |
| failed-delivery | 1200px | failed-delivery-1200px.png | ✓ |
| failed-delivery | 480px | failed-delivery-480px.png | ✓ |

Validation confirmed:

1. Text is readable at both viewports — no overlap, no truncation of critical info
2. Panel boundaries are clear — each section has distinct uppercase header with border
3. Status colors always paired with text labels (never color-only)
4. Scheduler/delivery/runtime/live-smoke information is visually distinct
5. Tables use overflow-x scroll at narrow widths — no content clipping
6. Failed delivery fixture correctly shows expanded failed delivery table and error signals
7. Missing smoke fixture renders unavailable state with diagnostic message

## Build Validation

```text
npm run build
build complete
```

Output files verified:
- `dist/webviews/monitoringDashboard.js` (213KB IIFE bundle)
- `dist/webviews/monitoringDashboard.css` (9.5KB extracted CSS)

## Non-Goals Confirmed

This slice does not implement:
1. Mutation buttons (no run supervisor, consume report, retry delivery)
2. Local Work Trajectory mutation
3. Worker report consumption
4. Raw transcript viewing
5. WebSocket/streaming
6. Distributed worker lease controls

## Closure

This gate closes the first frontend visual implementation of the monitoring
dashboard. The dashboard is accessible via the command palette:
"Doc-Based Coding: Open Monitoring Dashboard".
