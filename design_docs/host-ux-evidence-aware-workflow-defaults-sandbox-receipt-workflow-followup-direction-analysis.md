# Host UX Evidence-Aware Workflow Defaults For Sandbox Receipt Workflow Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-evidence-aware-workflow-defaults-sandbox-receipt-workflow.md`
closed with an explicit visible receipt candidate action that pre-fills
`Sandbox Receipt Workflow` allocation evidence id/path fields.

Review evidence:

- `review/host-ux-evidence-aware-workflow-defaults-sandbox-receipt-workflow-2026-06-21.md`

## Current Position

The Host UX sandbox receipt branch now has:

1. visible sandbox receipt evidence candidates;
2. cleanup candidate selection for explicit cleanup invocation;
3. run-once and bounded daemon-loop sandbox receipt workflow invocation;
4. read-only cleanup outcome diff from visible receipt refs;
5. explicit workflow allocation evidence prefill from visible receipt refs.

The branch is still conservative: visible evidence can help fill fields, but no
workflow or cleanup action is executed without an operator pressing the explicit
action button.

## Candidate A - Backend-Enriched Cleanup Diff Payload

### Goal

Expose a structured cleanup diff payload from Host Evidence presentation so the
UI no longer infers before/after semantics from generic card facts and refs.

### Why Next

The current diff and prefill surfaces prove the operator workflow, but both are
presentation-derived. A backend-enriched diff payload would make the read-only
comparison more robust without adding new mutation authority.

### Narrow Scope

1. Keep Host UX display-only for the diff.
2. Add structured cleanup diff fields to Host Evidence presentation.
3. Preserve current UI fallback for older generic cards.
4. Do not add workflow/cleanup auto-execution.

## Candidate B - Projection Refresh Follow-Up

### Goal

Offer an explicit projection refresh follow-up after sandbox receipt workflow
execution.

### Why Lower Priority

Projection refresh already exists as a separate Scheduler Operator action. It is
useful, but less urgent than making the evidence comparison contract less
inference-heavy.

## Candidate C - Host UX Sandbox Receipt Branch Pause

### Goal

Pause this Host UX branch and return to scheduler/orchestration backend slices.

### Why Plausible

The current Host UX branch now has a usable operator loop. More UI layering may
be lower value until real host-run samples expose a sharper evidence gap.

## Recommendation

Default to Candidate A only when real receipt evidence samples show that the
presentation-derived cleanup diff is too weak. Otherwise pause the Host UX
sandbox receipt branch and move back to backend scheduler/orchestration work.

Reason:

1. the current operator path is usable and explicitly guarded;
2. more UI affordances risk crowding the Scheduler Operator card;
3. backend-enriched diff payload is the next robustness improvement, not a new
   mutation flow.
