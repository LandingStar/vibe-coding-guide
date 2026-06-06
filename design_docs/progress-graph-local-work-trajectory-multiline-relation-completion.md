# Progress Graph Local Work Trajectory Multi-Line Relation Completion

## Context

This document records the 2026-06-05 follow-up slice after manual validation of
the previous open-lane and merge alignment changes.

The goal is to complete the narrow multi-line relation layer and match it in the
Local Work Trajectory UI. This is not a scheduler, conflict resolver, grouped
review system, or automatic multi-agent runtime.

## Implemented Scope

1. `localTrajectory relate` records explicit metadata between existing events.
2. Supported explicit relation kinds are `depends_on`, `waits_for`, `unblocks`,
   `hands_off`, `syncs_from`, and `approves_new_line`.
3. Existing lifecycle helpers still own `sequence`, `proposes_new_line`, and
   `merges_into`.
4. `sequence` is rejected by the generic relation writer because append and
   merge lifecycle helpers own ordering edges.
5. Repeating the same source event, target event, and relation kind updates the
   existing relation instead of adding duplicate overlapping edges.

## UI Mapping

1. Forward relation kinds constrain columns so the target event renders after
   the source event.
2. Lane-opening relations align the lane label near the opening or approval
   event instead of starting from the far-left origin.
3. Relation labels distinguish `open lane`, `approved`, `depends`, `waits`,
   `unblocks`, `handoff`, `sync`, and `merge`.
4. The UI continues to show trajectory metadata only. It does not infer true
   parallel execution, scheduling, or review-barrier semantics.

## Validation

Focused validation passed:

1. `python -m pytest tests/test_progress_graph_trajectory.py tests/test_mcp_tools.py tests/test_instructions_generator.py -q`
   reported `102 passed, 1 skipped`.
2. `npm run build` passed in `vscode-extension`.
3. `node --test dist/test/localWorkTrajectory.test.js dist/test/aiChatToolLoop.test.js dist/test/aiChatViewIntegration.test.js`
   reported `9 passed`.

Known validation note: on this Windows/Python environment, pytest still prints a
post-run `Windows fatal exception: access violation` stack after reporting all
selected tests passed with exit code 0. The stack appears in import/cache
machinery and is not tied to the Local Work Trajectory assertions.

## 2026-06-05 Alignment Correction

User validation showed an incorrect alignment case: an explicit dependency edge
could push the lane-open event back against its opener, creating a visual cycle
and misaligned lane start. The corrected rule is:

1. Only lane-opening and merge relations participate in column alignment:
   `proposes_new_line`, `approves_new_line`, and `merges_into`.
2. `depends_on`, `waits_for`, `unblocks`, `hands_off`, and `syncs_from` remain
   visible labeled edges, but they do not move nodes.
3. This keeps the layout anchored by where a lane opens and where it merges
   back, while still allowing auxiliary cross-line semantics to be read.

## 2026-06-05 Auxiliary Relation Display Correction

User validation showed that `depends_on` could still render as a long reverse
edge across the main lane. The corrected display rule is:

1. Auxiliary relation kinds are visually separate from main path relations.
2. `depends_on`, `waits_for`, and `syncs_from` are displayed in the intuitive
   visual direction from the depended-on / waited-for / synced-from event toward
   the consuming event.
3. Auxiliary relations render as lightweight straight, unarrowed edges so they
   do not compete with `sequence`, `proposes_new_line`, or `merges_into` as
   primary flow edges.
4. The stored relation data is unchanged; this is purely a renderer-level
   mapping.

## 2026-06-05 Auxiliary Relation Side-Port Attempt (SUPERSEDED)

This section is retained as historical context only. The side-port/top-bottom
routing attempt below was superseded by the rollback section at the end of this
document.

User validation showed that auxiliary relation edges could still overlap the
left-to-right sequence path because they reused the same default node ports. The
corrected display rule is:

1. Main flow relations keep the default left/right ports.
2. Auxiliary relation kinds use hidden top/bottom event ports.
3. Cross-lane auxiliary relations exit from the side facing the target lane and
   enter from the matching opposite side, reducing overlap with horizontal flow
   edges.
4. Same-lane auxiliary relations use top ports by default so they do not compete
   with the primary sequence line.
5. The stored relation data is unchanged; this is still a renderer-level
   mapping.

## 2026-06-05 Lane Ordering Correction

User validation showed that side-port routing alone could make the display look
more chaotic when lane order was wrong. The renderer had sorted lanes by id, so
`lane:002` could appear above `lane:main`; this inverted parent/child lanes and
forced open, depends, merge, and sequence edges to cross.

The corrected display rule is:

1. `lane:main` is the preferred root lane when present.
2. Lane-opening relations (`proposes_new_line`, `approves_new_line`) define
   parent-to-child lane order for the renderer.
3. Child lanes render after their parent lane instead of being ordered by lane
   id alone.
4. Any lanes not reachable from opening relations still fall back to stable id
   ordering after rooted lanes.
5. Stored trajectory data remains unchanged; this is a renderer-level ordering
   rule.

## 2026-06-05 Auxiliary Relation Badge Correction

Further user validation showed that even with corrected lane order, drawing
`depends_on` as a cross-lane edge made the trajectory harder to read. The local
trajectory view should privilege work progression over every semantic
relationship.

The corrected display rule is:

1. `sequence`, `proposes_new_line`, `approves_new_line`, and `merges_into`
   remain structural edges.
2. `depends_on`, `waits_for`, `unblocks`, `hands_off`, and `syncs_from` no
   longer render as default cross-canvas edges.
3. Auxiliary relations render as compact badges on the event they qualify.
4. The relation data remains present in the artifact; this only changes the
   default renderer projection.
5. A later explicit relation-layer toggle can reintroduce dependency edges if
   the UI has a dedicated routing strategy.

## 2026-06-05 Side-Port / Top-Bottom Routing Rollback

User validation showed that trying to route merge/open-lane or auxiliary
relations through hidden side/top/bottom ports made the Local Work Trajectory
view harder to read. The current renderer intentionally rolls back that routing
experiment while preserving the useful fixes from the same iteration.

Current default:

1. Structural relations (`sequence`, `proposes_new_line`, `approves_new_line`,
   and `merges_into`) use normal React Flow source/target node connections.
2. Structural relation edges no longer use hidden top/bottom or side handles.
3. Auxiliary relation kinds (`depends_on`, `waits_for`, `unblocks`,
   `hands_off`, and `syncs_from`) stay as compact event badges by default.
4. The lane-ordering correction remains: `lane:main` is preferred as the root,
   and opened child lanes render after their parent lane.
5. The dependency-display correction remains: dependency data is still present
   in the artifact, but it does not create cross-canvas dependency edges in the
   default trajectory view.
6. Reintroducing side/top/bottom routing should require a separate routing
   design and visual validation instead of incremental tweaks to the default
   relation edges.

Rollback validation passed:

1. `npm run build` passed in `vscode-extension`.
2. `node --test dist/test/localWorkTrajectory.test.js dist/test/aiChatToolLoop.test.js dist/test/aiChatViewIntegration.test.js`
   reported `9 passed`.

## 2026-06-06 Temporary Reliance Overlay

User validation confirmed that the rollback baseline is readable. The next
temporary correction treats reliance relations as a separate visual overlay:
the main trajectory layer lays out and aligns itself first, then reliance edges
are projected onto the already computed main-layer node coordinates.

This is an explicit temporary solution. It exists to make current testing
readable while avoiding another broad layout model rewrite. A later front-end
model should replace this overlay with a more suitable relation/routing model.

Current behavior:

1. Main-layer alignment is owned only by `sequence`, `proposes_new_line`,
   `approves_new_line`, and `merges_into`.
2. Reliance relations do not participate in `computeEventColumns(...)`,
   `computeLaneStartColumns(...)`, or lane ordering.
3. Reliance overlay currently covers `depends_on`, `waits_for`, and
   `syncs_from`.
4. `unblocks` and `hands_off` remain compact badges only; they are not treated
   as reliance overlay lines in this temporary slice.
5. Overlay edges use hidden top/bottom event handles selected from the source
   and target lane order:
   - source lane above target lane: source bottom -> target top;
   - source lane below target lane: source top -> target bottom;
   - same lane: source top -> target top.
6. Structural open/merge/sequence edges continue to use normal React Flow node
   connections and must not use the reliance handles.

Validation passed:

1. `npm run build` passed in `vscode-extension`.
2. `node --test dist/test/localWorkTrajectory.test.js dist/test/aiChatToolLoop.test.js dist/test/aiChatViewIntegration.test.js`
   reported `9 passed`.

## 2026-06-06 Browser Screenshot Harness And Handle Isolation

User screenshot validation showed apparent line overlap in the temporary
reliance overlay. Browser inspection with the installed Playwright skill showed
the current smoke artifact had no reliance relation at all; the visible overlap
was caused by hidden top/bottom reliance handles becoming the default React Flow
ports for normal sequence edges.

Correction:

1. Lane and event nodes now expose explicit hidden main-flow handles:
   `main-flow-source` on the right and `main-flow-target` on the left.
2. Structural flow edges (`sequence`, `proposes_new_line`,
   `approves_new_line`, `merges_into`) explicitly bind to those main-flow
   handles.
3. Reliance overlay edges continue to bind only to hidden top/bottom reliance
   handles.
4. This preserves the temporary two-layer model:
   main flow = horizontal left/right flow;
   reliance overlay = independent top/bottom layer.

Debugging support:

1. Installed the curated Codex `playwright` skill into
   `C:\Users\16329\.codex\skills\playwright`.
2. Added `vscode-extension/scripts/render-local-work-trajectory-harness.mjs`
   to render a local browser harness from the real
   `local-work-trajectory.json` artifact plus current webview bundle assets.
3. Harness output lives under `output/playwright/local-work-trajectory/`.
4. Playwright CLI was configured to use the existing local Microsoft Edge
   browser (`--browser msedge`) because Chrome was not installed and the Chrome
   installer download failed in this environment.

Validation passed:

1. `npm run build` passed in `vscode-extension`.
2. `node --test dist/test/localWorkTrajectory.test.js dist/test/aiChatToolLoop.test.js dist/test/aiChatViewIntegration.test.js`
   reported `9 passed`.
3. Browser harness rendered through Playwright at
   `http://127.0.0.1:8766/index.html`.
4. DOM inspection showed the current sequence paths as horizontal left/right
   edges, for example `M 171.5,27L 264.5,27`.

Follow-up correction from screenshot review:

1. React Flow default nodes still emitted their own visible default handles even
   after custom main/reliance handles were added.
2. Removed reliance on `sourcePosition` / `targetPosition` and added CSS to hide
   any non-`pg-lwt-*` React Flow handles in the Local Work Trajectory surface.
3. Playwright DOM inspection now reports `visibleHandles: 0` while preserving
   horizontal sequence paths.

## 2026-06-06 UI Binding Completion Checkpoint

User-side validation in the VS Code extension host matched the Playwright
browser harness at the semantic UI level:

1. The main lane remains a left-to-right flow.
2. Later lanes start near their open/approval event instead of from the far
   left.
3. `merges_into` aligns back to the main lane merge point.
4. `depends_on`, `waits_for`, and `syncs_from` render as temporary reliance
   overlay edges without becoming layout constraints.
5. React Flow default handles are no longer visibly rendered.

The real test workspace fixture was written to:

`C:\Users\16329\OneDrive\Desktop\tmp\dbc-test\.codex\progress-graph\local-work-trajectory.json`

The fixture currently contains 3 lanes, 8 events, and 11 relations covering
`sequence`, `proposes_new_line`, `approves_new_line`, `merges_into`,
`depends_on`, `waits_for`, and `syncs_from`.

Current slice status: Local Work Trajectory command/UI binding is complete for
the narrow multi-line lifecycle model. The known remaining limitation is product
polish rather than binding correctness: full-graph fit can make node text small,
and the temporary reliance overlay should later be replaced by a more suitable
front-end relation/routing model.
