# Planning Gate: Scheduler Operator Host UX Unified Workflow Binding

> Date: 2026-06-19
> Status: COMPLETED

## Context

The completed multi-lane dogfood fixture gate produced a stronger deterministic
sample for Scheduler Operator flows:

- `doc-based-coding scheduler seed-dogfood-fixture --fixture multilane`
- four fake-runtime tasks across api/data/client/qa lanes
- validated through shared backend/CLI/MCP `schedulerOperatorWorkflow`

The existing VS Code Scheduler Operator Host UX still performs the workflow as
separate CLI choreography:

```text
scheduler admit-exchange-artifact
scheduler daemon-loop
scheduler project
```

That creates behavior drift risk because Codex/MCP/CLI now have a shared
`scheduler operator-workflow` surface with explicit opt-in mutation flags.

## Scope

This gate binds the Host UX action buttons to the shared workflow surface while
preserving explicit operator control.

The intended mapping is:

| Host UX action | Shared workflow call |
| --- | --- |
| Admit | `scheduler operator-workflow --admit --artifact-id ... --version ...` |
| Run bounded loop | `scheduler operator-workflow --run-loop --evidence-id ...` |
| Refresh projection | `scheduler operator-workflow --refresh-projection` |

The UI should continue to show candidate/readback/evidence state from existing
read-only resources. This gate changes action plumbing, not the visual design
model.

## Acceptance

1. VS Code Scheduler Operator action plumbing calls
   `doc-based-coding scheduler operator-workflow` instead of duplicating the
   underlying admission/loop/projection commands.
2. Each action remains explicit and narrow:
   - Admit only sets `--admit`;
   - Run bounded loop only sets `--run-loop`;
   - Refresh projection only sets `--refresh-projection`.
3. Paths, fake runtime policy, evidence id, actor, guide context, and
   projection readback remain explicit in the Host UX invocation.
4. Existing read-only resource behavior remains unchanged.
5. The multi-lane fixture is used as the validation sample where practical.
6. UI/image validation includes screenshot-style evidence before close.

## Non-Goals

- Do not redesign the Scheduler Operator visual layout.
- Do not change backend scheduler/admission/evidence schemas.
- Do not run live Qoder or any real provider.
- Do not introduce background daemon lifecycle.
- Do not mark ExchangeArtifact versions consumed.
- Do not mutate agent-owned Local Work Trajectory from UI or scheduler workflow
  code.
- Do not clean up unrelated existing UI dirty branch files in this gate.

## Validation Plan

```powershell
npm run build --prefix vscode-extension
node --test vscode-extension/dist/test/progressGraphPreviewPanel.test.js
node --test vscode-extension/dist/test/progressGraphPreviewHtml.test.js
```

Then run a screenshot-style validation using the existing Playwright workflow or
available preview harness, with a multi-lane fixture seeded in a temporary or
test workspace.

## Completion Notes

Completed on 2026-06-19.

Implementation:

- VS Code Scheduler Operator actions now call the shared
  `doc-based-coding scheduler operator-workflow` CLI surface.
- `Admit` passes only `--admit` plus exact artifact id/version.
- `Run bounded loop` passes only `--run-loop` with fake runtime policy,
  explicit bounded loop limits, evidence id, evidence path, and actor.
- `Refresh projection` passes only `--refresh-projection` plus guide context.
- Artifact store, admission ledger, scheduler snapshot/event log, and
  scheduler projection paths are explicit in the Host UX invocation.
- Last-action summaries now understand the nested shared workflow payload while
  preserving compatibility with the older direct command payload shape.

Validation:

```text
npm run build --prefix vscode-extension
build complete
```

```text
node --test vscode-extension/dist/test/progressGraphPreviewPanel.test.js
10 passed
```

```text
node --test vscode-extension/dist/test/progressGraphPreviewHtml.test.js
13 passed
```

```text
.\.venv\Scripts\python.exe -m pytest tests/test_cli.py tests/test_runtime_orchestration.py tests/test_mcp_admission.py -k "scheduler_operator_multilane_dogfood_fixture or scheduler_operator_workflow"
10 passed
```

Screenshot-style validation:

```text
output/playwright/scheduler-operator-ui/scheduler-operator-panel.png
```

The screenshot harness rendered the Scheduler Operator panel with one admission
candidate, the explicit `Admit`, `Run bounded loop`, and `Refresh projection`
controls, last-action feedback, and Host Evidence readback.
