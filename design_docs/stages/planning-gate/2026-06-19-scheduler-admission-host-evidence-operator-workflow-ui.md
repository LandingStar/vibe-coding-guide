# Planning Gate - Scheduler Admission And Host Evidence Operator Workflow UI

> Date: 2026-06-19
> Status: COMPLETED

## Trigger

`design_docs/host-evidence-ui-binding-followup-direction-analysis.md` recommends
turning the completed admission / scheduler / projection / host-evidence chain
into one visible operator workflow.

## Problem

The backend already has explicit authority surfaces:

1. read-only ExchangeArtifact inspection through `dbc://exchange-artifacts/bundle`;
2. exact-version scheduler admission through CLI and MCP helper surfaces;
3. bounded fake-runtime scheduler advancement through scheduler tick / daemon-loop;
4. explicit scheduler-derived trajectory projection refresh;
5. read-only host evidence presentation through `dbc://host-evidence/presentation`.

The current VS Code progress preview can show host evidence, but an operator
still has to know the command sequence and inspect multiple JSON surfaces by
hand. This makes the product flow feel fragmented even though the backend chain
is now sufficiently explicit.

## Scope

### Slice 1 - Operator Workflow Contract

Add a UI-facing workflow model that keeps the steps separate:

1. inspect ExchangeArtifact candidates;
2. inspect scheduler admission ledger/state;
3. admit one exact stored artifact version;
4. run a bounded scheduler loop through the existing fake-runtime CLI path;
5. refresh scheduler-derived trajectory projection;
6. read host evidence presentation.

The UI must not infer hidden mutations. Every mutating step remains an explicit
operator action.

### Slice 2 - VS Code Preview Binding

Extend the existing progress graph preview shell with a small Scheduler Operator
section near Host Evidence. It should:

1. read `dbc://exchange-artifacts/bundle` as a read-only candidate summary;
2. read scheduler state/admission summaries when artifacts exist;
3. show default file paths used by the workflow;
4. expose explicit buttons for admit, bounded run, and projection refresh;
5. reload preview/readback after an action completes;
6. surface command stdout/stderr or backend errors without hiding existing graph
   and Host Evidence panels.

### Slice 3 - Narrow Host Command Helpers

Add VS Code-side command helpers that invoke the existing Python CLI entry
points through the resolved runtime. These helpers are host-owned glue only:
they do not create new scheduler semantics.

Default paths:

```text
.codex/orchestration/exchange-artifacts.json
.codex/orchestration/exchange-artifact-admissions.json
.codex/scheduler/scheduler-state.json
.codex/scheduler/scheduler-events.jsonl
.codex/progress-graph/scheduler-work-trajectory.json
```

## Non-Goals

This gate does not:

1. add live Qoder / real-provider execution;
2. create a background daemon lifecycle;
3. add automatic admission or automatic scheduler mutation;
4. mark ExchangeArtifacts consumed;
5. mutate agent-owned Local Work Trajectory;
6. change backend scheduler/admission/evidence schemas;
7. replace MCP tools or CLI commands;
8. redesign the full progress graph / local trajectory UI.

## Authority Boundary

The VS Code extension is Host UX Layer. It may orchestrate explicit user actions
over existing Portable Runtime commands/resources, but it must not redefine
scheduler/admission semantics.

Read-only surfaces:

1. `dbc://exchange-artifacts/bundle`;
2. `dbc://host-evidence/presentation`;
3. scheduler inspect commands.

Mutation surfaces:

1. `scheduler admit-exchange-artifact`;
2. `scheduler daemon-loop` with fake runtime only;
3. `scheduler project`.

Each mutation must show an explicit button and a visible result message.

## Acceptance Criteria

The gate may close when:

1. A narrow Scheduler Operator section is visible in the VS Code progress
   preview shell.
2. The section reads ExchangeArtifact candidate state and Host Evidence readback
   without parsing raw evidence files in UI code.
3. Mutating actions remain explicit and use existing scheduler CLI surfaces.
4. Focused VS Code tests cover read-only resource wiring, button/message wiring,
   and command boundary strings.
5. Screenshot validation captures the Scheduler Operator section.
6. Review/status docs record the preserved non-goals and the next follow-up
   direction.

## Completion Notes

Completed on 2026-06-19.

Implemented:

1. Added a VS Code-side Scheduler Operator workflow helper that reads
   `dbc://exchange-artifacts/bundle`, reads scheduler state through
   `scheduler inspect-state`, and invokes only existing scheduler CLI surfaces
   for explicit actions.
2. Added a Scheduler Operator section to the progress graph preview shell,
   showing ExchangeArtifact candidate counts, scheduler state/event readback,
   default workflow paths, candidate-level Admit buttons, bounded loop action,
   projection refresh action, and last action stdout/stderr/result summary.
3. Kept Host Evidence as the readback panel for durable scheduler-loop evidence.
4. Preserved isolated readback: ExchangeArtifact, scheduler state, and Host
   Evidence failures render independently instead of hiding the full preview.
5. Added focused tests for the Scheduler Operator card and explicit CLI
   boundary wiring.
6. Captured screenshot validation for the Scheduler Operator panel.

Validation:

```text
cd vscode-extension
npm run build
node --test "dist/test/progressGraphPreviewHtml.test.js" "dist/test/progressGraphPreviewPanel.test.js"
```

Result:

```text
VS Code extension build passed.
Focused preview tests: 23 passed.
```

Backend resource smoke:

```text
.\.venv\Scripts\python.exe -m src resources read dbc://exchange-artifacts/bundle
.\.venv\Scripts\python.exe -m src resources read dbc://host-evidence/presentation
.\.venv\Scripts\python.exe -m src scheduler inspect-admissions
```

Result:

```text
ExchangeArtifact bundle: exists=false, admission_candidate_count=0, error_count=0.
Host evidence presentation: status=empty, card_count=0, error_count=0.
Admission ledger inspection: ok=true, exists=false, record_count=0.
```

Current workspace scheduler snapshot smoke:

```text
.\.venv\Scripts\python.exe -m src scheduler inspect-state --snapshot-path .codex/scheduler/scheduler-state.json --event-log-path .codex/scheduler/scheduler-events.jsonl
```

Result:

```text
Expected current-workspace readback absence: scheduler-state.json does not exist.
The UI renders this as scheduler state readback unavailable.
```

Screenshot validation:

```text
output/playwright/scheduler-operator-ui/scheduler-operator-panel.png
```

Change analysis:

```text
impact.direct=[]
impact.transitive=[]
coupling.alerts=[]
```

Non-goals preserved:

1. No live Qoder / real-provider execution.
2. No background daemon lifecycle.
3. No automatic admission or automatic scheduler mutation.
4. No ExchangeArtifact consumed marking.
5. No agent-owned Local Work Trajectory mutation from the UI.
6. No backend scheduler/admission/evidence schema changes.
7. No replacement of MCP tools or CLI commands.
8. No redesign of the full progress graph / local trajectory UI.
