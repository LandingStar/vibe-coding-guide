# Exchange Communication Readback Follow-up Direction Analysis

## Document Position

This direction analysis follows the completed ExchangeArtifact communication
readback slice:

- `design_docs/stages/planning-gate/2026-07-09-exchange-communication-readback-envelope.md`
- `design_docs/stages/planning-gate/2026-07-09-runtime-invocation-readback-envelope.md`
- `design_docs/stages/planning-gate/2026-07-08-scheduler-event-readback-envelope.md`
- `design_docs/tooling/Log-like Record Standard Draft.md`

It selects the next narrow log-like record alignment gate. It is not an
implementation gate and does not change runtime behavior by itself.

Date: 2026-07-09

## Current Baseline

The scheduler, runtime invocation, and ExchangeArtifact communication families
now have read-only draft envelope projections:

- `scheduler_event_to_readback_envelope()`
- `runtime_invocation_record_to_readback_envelope()`
- `exchange_artifact_record_to_readback_envelope()`
- shared `LogRecordRef`
- typed subject/input/output/evidence refs
- normalized summary/reason/next-hint fields
- explicit raw payload non-persistence declarations

This gives the internal log-like record draft coverage across execution,
scheduling, and agent communication without changing source storage or mutation
authority.

## Candidate 1 - Worker Report / Trajectory Suggestion Envelope

### What It Would Do

Add a read-only draft envelope projection for worker reports, especially
`Subagent Report.trajectory_update`.

Expected fields:

- worker identity, lane/task scope, assigned context, and report status
- completion/block/wait suggestion summary
- validation evidence refs
- changed-surface refs
- trajectory suggestion refs and authority notes
- explicit statement that workers suggest Local Work updates while
  leader/main/supervisor owns actual trajectory mutation

### Why It Is Valuable

This directly supports the current leader-worker authority split. Scheduler,
runtime, and ExchangeArtifact readbacks can already tell much of the story; the
next missing link is a compact, auditable worker claim/readback before leader
consumption.

### Source Basis

- `docs/worker-trajectory-update-reporting.md`
- `src/runtime/orchestration/worker_trajectory_report_consumer.py`
- `docs/specs/subagent-report.schema.json`
- `design_docs/tooling/Log-like Record Standard Draft.md`

### Scope Boundary

This should not allow workers to mutate Local Work Trajectory directly and
should not change the report schema without a separate contract gate.

## Candidate 2 - Validation / Doctor / Self-check Receipt Envelope

### What It Would Do

Add a compact readback envelope for validation and self-check receipts.

### Why It Is Valuable

Install, release, and workspace health troubleshooting would benefit from
standard pass/fail/warn summaries and remediation next hints.

### Scope Boundary

This should not change validation semantics, doctor checks, or install
behavior.

## Candidate 3 - UI Screenshot / Host Evidence Envelope

### What It Would Do

Add readback envelopes for UI screenshot evidence and host/sandbox evidence
receipts.

### Why It Is Valuable

Visual validation and host evidence are important for release confidence, but
they are less central than worker report authority for the immediate
multi-agent direction.

## Recommendation

Default next gate: **Worker Report / Trajectory Suggestion Readback
Envelope**.

Reason:

- It is the next closest record family to leader-worker coordination.
- It can reuse scheduler/runtime/exchange typed refs.
- It should make worker claims and Local Work trajectory suggestions auditable
  without changing worker authority.

Validation/doctor receipts should follow if install/release troubleshooting
becomes the immediate pressure.

## Proposed Next Gate

```text
Worker Report / Trajectory Suggestion Readback Envelope
```

Acceptance outline:

- Add a read-only projection from existing worker report structures into the
  draft envelope.
- Cover completed, blocked/waiting, validation-evidence, changed-artifact, and
  trajectory-update suggestion paths.
- Preserve the rule that bounded workers report suggestions while
  leader/main/supervisor owns `localTrajectory` mutation.
- Do not mutate Local Work Trajectory or change worker report schema in this
  gate.
