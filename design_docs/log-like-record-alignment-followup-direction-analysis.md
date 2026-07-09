# Log-like Record Alignment Follow-up Direction Analysis

## Document Position

This direction analysis follows the completed scheduler event readback slice:

- `design_docs/stages/planning-gate/2026-07-08-scheduler-event-readback-envelope.md`
- `design_docs/tooling/Log-like Record Standard Draft.md`
- `design_docs/tooling/Log-like Record Family Gap Inventory.md`

It selects the next narrow log-like record alignment gate. It is not an
implementation gate and does not change runtime behavior by itself.

Date: 2026-07-08

## Current Baseline

The scheduler event family now has a read-only draft envelope projection:

- `scheduler_event_to_readback_envelope()`
- typed refs for task, dependency, artifact, lease, run, session, and event
- normalized summary/reason/next-hint fields
- explicit `replay_effect=state_mutating|audit_only`
- focused tests for routine, blocked, failed, review, audit-only, and lease
  events

This gives the internal log-like record draft one concrete implementation
example without changing scheduler JSONL persistence or replay semantics.

## Candidate 1 - Runtime Invocation Readback Envelope

### What It Would Do

Add a read-only draft envelope projection for `RuntimeInvocationRecord`.

Expected fields:

- normalized `record_id`, `record_kind`, `timestamp`, `actor`, `action`,
  `status`
- success and failure `summary`
- failure/retry `reason`
- typed task, agent, provider session, run, output artifact, command/runtime
  refs
- `next_hint` for provider failure, retryability, output inspection, and
  compacted records
- explicit sensitivity/redaction state and `raw_payload_persisted=false`

### Why It Is Valuable

Runtime invocation is the other core execution-path log family. The existing
record is mechanically rich and already safer than many logs, but success
records can still be terse, retry/failure explanation is not always normalized,
and reviewers often need to inspect attempts or metadata to understand what
happened.

### Source Basis

- `design_docs/tooling/Log-like Record Family Gap Inventory.md`
- `src/runtime/orchestration/runtime_invocation_audit.py`
- `src/runtime/orchestration/log_decoration_adapters.py`
- `docs/runtime-log-decoration-contract.md`

### Scope Boundary

This should mirror the scheduler slice: projection first, no JSONL migration,
no raw transcript persistence, no provider execution changes.

## Candidate 2 - ExchangeArtifact Communication History Envelope

### What It Would Do

Add a compact readback envelope for agent communication history and mailbox
records.

Expected fields:

- who produced which artifact for which audience
- artifact lifecycle state
- causality/reply relations
- action expectation or no-action clue
- typed refs for artifact, producer, audience, task, lane, scheduler
  candidate, disposition, and related records

### Why It Is Valuable

Agent-to-agent communication audit is central to the multi-agent direction.
Making communication records readable would directly help leader/worker
history review and future monitoring UI.

### Source Basis

- `src/runtime/orchestration/agent_exchange_history.py`
- `src/runtime/orchestration/agent_communication.py`
- `design_docs/agent-coordination-exchange-artifact-design-record.md`
- `review/research-compass.md`

### Scope Boundary

This should not mutate artifact lifecycle, consume candidates, admit scheduler
tasks, or add raw transcript persistence.

## Candidate 3 - Worker Report / Trajectory Suggestion Envelope

### What It Would Do

Add a readback envelope for worker reports, especially
`Subagent Report.trajectory_update`.

Expected fields:

- worker identity, lane/task scope, assigned context
- completion/block/wait suggestion summary
- validation evidence refs
- changed-surface refs
- explicit authority note that workers suggest trajectory mutations while
  leader/main/supervisor owns actual `localTrajectory` mutation

### Why It Is Valuable

This directly supports the current leader-worker authority split. It would make
worker reports easier to audit before leader-side consumption.

### Source Basis

- `docs/worker-trajectory-update-reporting.md`
- `src/runtime/orchestration/worker_trajectory_report_consumer.py`
- `docs/specs/subagent-report.schema.json`

### Scope Boundary

This should not allow workers to mutate Local Work Trajectory directly and
should not change the report schema without a separate contract gate.

## Recommendation

Default next gate: **Runtime Invocation Readback Envelope**.

Reason:

- It is closest to the completed scheduler readback slice.
- It sits on the same core execution/audit path.
- It already has mature fields and safety constraints, so the gate can stay
  narrow and mostly projection-oriented.
- It will make scheduler failure next-hints more useful, because failed
  scheduler events often point reviewers to runtime invocation records.

ExchangeArtifact communication history should follow after runtime invocation
unless the immediate product pressure shifts back to multi-agent message audit.
Worker report / trajectory suggestions should follow once communication history
and runtime readback are stable enough to share typed refs and redaction
language.

## Proposed Next Gate

```text
Runtime Invocation Readback Envelope
```

Acceptance outline:

- Add a read-only projection from `RuntimeInvocationRecord` into the draft
  envelope.
- Cover success, failed retryable, failed non-retryable, and compacted/readback
  paths.
- Expose typed refs and next hints without persisting raw transcript text.
- Keep JSONL storage, provider execution, retry behavior, and compaction
  semantics unchanged.
