# Host UX Daemon-Loop Sandbox Receipt Workflow Mode

> Date: 2026-06-21
> Status: COMPLETED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-host-ux-full-sandbox-receipt-workflow-mode.md`
closed with a `run-once` Host UX binding for
`scheduler sandbox-receipt-workflow`. The follow-up direction recommends adding
the backend's existing `daemon-loop` mode as a separate narrow UI extension.

Sources:

- `design_docs/host-ux-full-sandbox-receipt-workflow-mode-followup-direction-analysis.md`
- `review/host-ux-full-sandbox-receipt-workflow-mode-2026-06-21.md`
- `src/__main__.py`
- `tools/progress_graph/host_sandbox_receipt_workflow.py`

## Goal

Extend the existing Scheduler Operator `Sandbox Receipt Workflow` card to support
explicit `daemon-loop` mode while preserving the existing `run-once` behavior.

## In Scope

- Add a mode selector with `run-once` and `daemon-loop`.
- Keep `fake` runtime only.
- For daemon-loop mode, collect bounded loop parameters:
  - max ticks;
  - max runs per tick;
  - max runtime failures.
- Map daemon-loop mode to existing CLI flags:
  - `--mode daemon-loop`;
  - `--max-ticks`;
  - `--max-runs-per-tick`;
  - `--max-runtime-failures`.
- Keep cleanup opt-in behavior unchanged.
- Add focused TypeScript tests for contract coercion, CLI args, and UI script.
- Use screenshot-style validation for the updated UI.

## Out of Scope

- Real provider / Qoder execution.
- Backend workflow schema changes.
- Cleanup outcome diff view.
- Evidence-aware auto-fill of workflow defaults.
- Scheduler projection refresh as part of the workflow.
- Local Work Trajectory mutation from Host UX/runtime code.

## Completion Criteria

- Host UX exposes both `run-once` and `daemon-loop` mode choices.
- Daemon-loop bounds are sent only for daemon-loop mode.
- Run-once CLI args remain unchanged except for the shared mode field.
- Cleanup output flags remain gated by explicit cleanup checkbox.
- Focused extension build/tests pass.
- Backend daemon-loop workflow regression passes.
- Screenshot artifact shows the daemon-loop controls in Scheduler Operator.
- Checklist, phase map, checkpoint, review evidence, and follow-up direction are
  updated before commit.
