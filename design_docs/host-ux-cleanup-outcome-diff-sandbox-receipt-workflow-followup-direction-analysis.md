# Host UX Cleanup Outcome Diff For Sandbox Receipt Workflow Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-host-ux-cleanup-outcome-diff-sandbox-receipt-workflow.md`
closed with a read-only cleanup outcome diff rendered from visible Host Evidence
sandbox receipt cards.

Review evidence:

- `review/host-ux-cleanup-outcome-diff-sandbox-receipt-workflow-2026-06-21.md`

## Current Position

The Host UX sandbox receipt branch now has:

1. visible receipt evidence candidates;
2. explicit cleanup invocation;
3. full workflow invocation in `run-once` and bounded `daemon-loop`;
4. read-only cleanup outcome diff over visible source/cleanup receipt refs.

The current diff is intentionally presentation-derived. It is useful and safe,
but depends on Host Evidence cards exposing enough source/cleanup refs and
cleanup state metadata.

## Candidate A - Evidence-Aware Workflow Defaults

### Goal

Use visible Host Evidence receipt candidates to prefill workflow path/id fields.

### Narrow Scope

1. Prefill allocation evidence path/id from selected visible receipt refs.
2. Keep cleanup opt-in unchecked by default.
3. Do not auto-run cleanup or workflow actions.
4. Preserve manual input override.

### Why Next

The read-only evidence and diff surfaces now make receipt roles clearer, so
prefill can improve operator ergonomics without hiding cleanup authority.

## Candidate B - Backend-Enriched Cleanup Diff Payload

### Goal

Expose a more structured cleanup diff payload from Host Evidence presentation so
the UI does not infer before/after semantics from generic card facts.

### Why Lower Priority

The current UI diff is already useful and read-only. Backend enrichment should
wait until real evidence samples show the presentation-derived diff is too weak.

## Candidate C - Projection Refresh Follow-Up

### Goal

Offer an explicit projection refresh follow-up after workflow execution.

### Why Lower Priority

Projection refresh already exists as a separate Scheduler Operator action. The
next ergonomic improvement should first reduce manual evidence field entry.

## Recommendation

Choose Candidate A next if continuing the Host UX sandbox branch:

```text
Evidence-Aware Workflow Defaults For Sandbox Receipt Workflow
```

Reason:

1. receipt role visibility is now strong enough to support safe prefill;
2. prefill can remain non-mutating and authority-neutral;
3. it reduces manual path/id copy work;
4. it does not require new backend schema or runtime behavior.
