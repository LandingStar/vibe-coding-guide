# Monitoring UI Frontend Expectations

> Date: 2026-06-28
> Status: handoff requirements for a separate frontend visual session

## Purpose

The monitoring UI should let an operator understand the current orchestration
state without opening raw scheduler, delivery, runtime, or smoke files.

The frontend must consume the backend snapshot described in:

- `docs/monitoring-ui-backend-api.md`

The first visual implementation should not read internal JSONL/state files
directly.

## Primary User Questions

The UI should answer these questions quickly:

1. Is the orchestration system healthy?
2. What is currently ready, waiting, failed, or review-required?
3. Are Codex worker invocations running or recently completed?
4. Was live lane-distinct Codex concurrency proven?
5. Which operator action is most relevant next?
6. Are worker report / Local Work Trajectory boundaries being respected?

## Suggested Information Architecture

Use a quiet operational dashboard, not a marketing page.

Recommended top-level regions:

1. Status strip
   - `ok`
   - `next_action`
   - highest-severity `operatorSignals`
2. Scheduler panel
   - task state counts
   - target task states
   - waiting/review-required lists
3. Delivery panel
   - delivery state counts
   - pending Codex deliveries
   - failed/review-required delivery summaries
4. Runtime panel
   - invocation counts
   - latest invocation table
   - lane/provider/status/timing fields
5. Live Codex smoke panel
   - report availability
   - verdict
   - worker counts
   - first concurrent batch
   - overlap pair summary
6. Worker report boundary panel
   - leader-owned consumer mode
   - report schema/doc links
   - clear note that monitoring does not consume reports

## Visual Requirements

The UI should be dense but readable. Prefer compact panels, tables, badges,
and clear grouping over large cards and decorative layouts.

Required states:

- healthy / ok
- warning
- error
- unavailable
- pending / waiting
- review required
- running/recent runtime invocation

Use color as a secondary cue, not the only cue. Every status should also have
text.

## Interaction Requirements

Minimum interactions:

1. Refresh snapshot.
2. Auto-refresh toggle with visible interval.
3. Copy command/path for key artifacts.
4. Expand latest runtime invocation details.
5. Expand live overlap pair details.
6. Filter latest runtime invocations by provider/status/lane.
7. Open documented worker report procedure/schema links.

Avoid mutation buttons in the first visual slice. Commands such as running the
supervisor loop or consuming a worker report should remain separate explicit
operator actions until a later command-authority UI gate.

## Data Contract Notes

Use these snapshot fields:

- `schema_version`
- `ok`
- `next_action`
- `scheduler`
- `delivery`
- `runtimeInvocations`
- `runtimeInvocations.concurrency`
- `liveCodexSmoke`
- `workerReports`
- `operatorSignals`
- `authoritySplit`

Unknown fields should be ignored.

If `liveCodexSmoke.exists` is false, render the panel as unavailable and show
the suggested action from `operatorSignals`.

If `authoritySplit.readModelOnly` is not true or
`authoritySplit.localWorkTrajectoryMutated` is true, show a high-severity
integrity warning.

## Validation Requirement

Because this is UI work, the frontend visual session must validate with a
screenshot-capable tool before acceptance. At minimum capture:

1. healthy C9-passed fixture;
2. missing live smoke report fixture;
3. failed delivery fixture if available;
4. narrow viewport or constrained panel width if this UI is embedded.

Screenshots should verify that text is readable, panels do not overlap, and
the operator can distinguish scheduler state, delivery state, runtime
invocations, and live-smoke evidence.

## Non-Goals For The Frontend Visual Slice

The first frontend slice should not implement:

1. command execution buttons;
2. Local Work Trajectory mutation;
3. worker report consumption;
4. raw transcript viewing;
5. streaming/WebSocket behavior;
6. distributed worker lease controls.

Those require separate authority and safety gates.
