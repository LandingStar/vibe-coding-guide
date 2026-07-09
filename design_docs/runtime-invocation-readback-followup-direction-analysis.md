# Runtime Invocation Readback Follow-up Direction Analysis

## Document Position

This direction analysis follows the completed runtime invocation readback
slice:

- `design_docs/stages/planning-gate/2026-07-09-runtime-invocation-readback-envelope.md`
- `design_docs/stages/planning-gate/2026-07-08-scheduler-event-readback-envelope.md`
- `design_docs/tooling/Log-like Record Standard Draft.md`
- `design_docs/tooling/Log-like Record Family Gap Inventory.md`

It selects the next narrow log-like record alignment gate. It is not an
implementation gate and does not change runtime behavior by itself.

Date: 2026-07-09

## Current Baseline

The scheduler and runtime invocation families now have read-only draft envelope
projections:

- `scheduler_event_to_readback_envelope()`
- `runtime_invocation_record_to_readback_envelope()`
- shared `LogRecordRef`
- typed subject/input/output/evidence refs
- normalized summary/reason/next-hint fields
- explicit raw payload non-persistence declarations

This gives the internal log-like record draft two execution-path examples
without changing scheduler replay, runtime invocation JSONL storage, provider
execution, retry behavior, or compaction semantics.

## Candidate 1 - ExchangeArtifact Communication History Readback Envelope

### What It Would Do

Add a read-only draft envelope projection for ExchangeArtifact communication
history and mailbox-oriented records.

Expected fields:

- normalized `record_id`, `record_kind`, `timestamp`, `actor`, `action`,
  `status`
- producer, audience, artifact lifecycle, intent, and causality clues
- typed artifact, producer, audience, task, lane, scheduler candidate,
  disposition, and related-record refs
- `next_hint` for reply, lifecycle transition, scheduler admission, review,
  blocker, merge, or no-action cases
- explicit sensitivity/redaction state and `raw_payload_persisted=false`

### Why It Is Valuable

Agent-to-agent communication audit is central to the multi-agent direction.
Runtime and scheduler readbacks explain execution, but the next missing layer
is who told whom what, what response was expected, and which communication
product led to scheduler/review/handoff/merge actions.

### Source Basis

- `src/runtime/orchestration/agent_exchange_history.py`
- `src/runtime/orchestration/agent_communication.py`
- `src/runtime/orchestration/agent_exchange_action_candidates.py`
- `design_docs/agent-coordination-exchange-artifact-design-record.md`
- `design_docs/tooling/Log-like Record Standard Draft.md`

### Scope Boundary

This should not mutate artifact lifecycle, consume candidates, admit scheduler
tasks, or add raw transcript persistence.

## Candidate 2 - Worker Report / Trajectory Suggestion Envelope

### What It Would Do

Add a readback envelope for worker reports, especially
`Subagent Report.trajectory_update`.

### Why It Is Valuable

This supports the leader/worker authority split and would make worker reports
easier to audit before leader-side Local Work mutation.

### Scope Boundary

This should not allow workers to mutate Local Work Trajectory directly and
should not change the report schema without a separate contract gate.

## Candidate 3 - Validation / Doctor / Self-check Receipt Envelope

### What It Would Do

Add a compact readback envelope for validation and self-check receipts.

### Why It Is Valuable

Install, release, and workspace health troubleshooting would benefit from
standard pass/fail/warn summaries and remediation next hints.

### Scope Boundary

This should not change validation semantics, doctor checks, or install
behavior.

## Recommendation

Default next gate: **ExchangeArtifact Communication History Readback
Envelope**.

Reason:

- It is the next highest-value log family for multi-agent audit.
- Scheduler and runtime readbacks already provide execution refs that
  communication history can point to.
- It should improve monitoring UI and leader/worker history review without
  changing authority or lifecycle mutation paths.

Worker report / trajectory suggestions should follow after communication
history, because worker report readbacks can reuse the same communication and
typed-ref language.

## Proposed Next Gate

```text
ExchangeArtifact Communication History Readback Envelope
```

Acceptance outline:

- Add a read-only projection from existing ExchangeArtifact communication
  history/mailbox records into the draft envelope.
- Cover routine message, reply/causality, lifecycle/action candidate, and
  no-action readability paths.
- Expose typed refs and next hints without mutating artifact lifecycle or
  persisting raw transcript text.
- Keep existing ExchangeArtifact storage and candidate consumers unchanged.
