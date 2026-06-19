# Review - Scheduler Admission And Host Evidence Operator Workflow UI

> Date: 2026-06-19
> Planning gate:
> `design_docs/stages/planning-gate/2026-06-19-scheduler-admission-host-evidence-operator-workflow-ui.md`

## Scope Reviewed

This slice added a narrow VS Code Host UX surface for the existing scheduler
operator workflow.

Implemented:

1. `vscode-extension/src/views/schedulerOperatorWorkflow.ts` as host-owned glue
   over existing runtime resources and CLI commands.
2. Read-only ExchangeArtifact candidate inspection through
   `dbc://exchange-artifacts/bundle`.
3. Read-only scheduler state/event readback through `scheduler inspect-state`.
4. Explicit UI actions for:
   - `scheduler admit-exchange-artifact`;
   - `scheduler daemon-loop` with `--runtime-provider fake`;
   - `scheduler project`.
5. Progress preview rendering for candidate-level Admit buttons, bounded run,
   projection refresh, default paths, scheduler readback, and last action
   stdout/stderr/result summary.

## Evidence

Automated validation:

```text
cd vscode-extension
npm run build
build complete
```

```text
node --test "dist/test/progressGraphPreviewHtml.test.js" "dist/test/progressGraphPreviewPanel.test.js"
23 passed
```

Backend smoke:

```text
.\.venv\Scripts\python.exe -m src resources read dbc://exchange-artifacts/bundle
.\.venv\Scripts\python.exe -m src resources read dbc://host-evidence/presentation
.\.venv\Scripts\python.exe -m src scheduler inspect-admissions
```

Observed current workspace state:

1. ExchangeArtifact store is absent and read-only bundle reports
   `admission_candidate_count=0`.
2. Host Evidence presentation is `empty`.
3. Admission ledger inspection is `ok=true` with `record_count=0`.
4. Scheduler state inspection reports missing scheduler snapshot; this is
   expected for the current workspace and is represented as readback unavailable
   in the UI.

Screenshot validation:

```text
output/playwright/scheduler-operator-ui/scheduler-operator-panel.png
```

The screenshot shows Scheduler Operator, candidate Admit, bounded run,
projection refresh, last action readback, and Host Evidence in the same preview
shell without visible overlap or blank panel failure.

Change analysis:

```text
impact.direct=[]
impact.transitive=[]
coupling.alerts=[]
```

## Authority Boundary

The UI remains Host UX Layer glue. It does not parse raw evidence artifacts and
does not implement scheduler semantics.

The mutating surfaces are still existing CLI commands and are only invoked from
explicit operator buttons.

## Residual Risk

1. This slice validates the UI over a rendered fixture and existing current
   workspace readback. It does not yet dogfood a full ExchangeArtifact candidate
   from inside a real project workspace through the VS Code button sequence.
2. The current workspace has no scheduler snapshot or candidate store, so the
   action flow was not exercised against this repository state.
3. Live Qoder / real-provider execution remains intentionally outside this
   slice.

## Follow-Up

The next useful slice is to add a small operator workflow dogfood fixture or
workspace bootstrap guide that creates a scheduler-admission candidate, then
uses the new UI sequence to admit, run fake runtime, refresh projection, and
read Host Evidence.
