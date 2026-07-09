# Worker Report / Trajectory Suggestion Readback Envelope

## Document Position

This planning gate scopes one narrow alignment slice for log-like record
readability.

Authoritative inputs:

- `design_docs/tooling/Log-like Record Standard Draft.md`
- `design_docs/tooling/Log-like Record Family Gap Inventory.md`
- `design_docs/exchange-communication-readback-followup-direction-analysis.md`
- `docs/worker-trajectory-update-reporting.md`
- `docs/specs/subagent-report.schema.json`

Date: 2026-07-09
Status: Completed

## Problem

Worker reports now carry the intended worker-to-leader Local Work handoff:
`Subagent Report.trajectory_update` is advisory evidence, while
leader/main/supervisor owns actual `localTrajectory` mutation. The existing
consumer enforces this authority split, but audit and monitoring views still
need a compact readback answer for:

- which worker report, contract, task, and lane is involved;
- whether the worker is completed, partial, blocked, waiting, or still active;
- what trajectory action the worker suggests, if any;
- which changed artifacts and evidence refs should be reviewed;
- why the leader must consume or reject the suggestion instead of letting a
  worker mutate Local Work directly.

## This Slice Does

- Add a read-only projection from an existing Subagent Report mapping into the
  draft log-like readback envelope.
- Derive normalized fields for:
  - `record_id`
  - `record_kind`
  - `timestamp`
  - `actor`
  - `action`
  - `status`
  - `summary`
  - `reason`
  - `run_id`
  - `correlation_id`
  - typed `subject_refs`
  - typed `input_refs`
  - typed `output_refs`
  - typed `evidence_refs`
  - `related_record_ids`
  - `next_hint`
  - `sensitivity`
  - `redaction_state`
  - `raw_payload_persisted`
- Add worker-report-specific fields for contract id, lane id, task id,
  event status, suggested trajectory action, changed artifact count,
  verification count, unresolved item count, and trajectory-update presence.
- Make the authority boundary explicit: worker reports suggest Local Work
  updates; leader/main/supervisor owns mutation.

## This Slice Does Not Do

- Does not change `docs/specs/subagent-report.schema.json`.
- Does not mutate Local Work Trajectory.
- Does not consume `trajectory_update`.
- Does not change `consume_worker_trajectory_report()` behavior.
- Does not admit scheduler tasks, run providers, or write ExchangeArtifact
  records.
- Does not persist or expose raw transcript text, raw command output, or
  `artifact_payloads.content`.
- Does not align validation/doctor receipts, screenshot evidence, or sandbox
  evidence families.

## Implementation Targets

Likely touched files:

- `src/runtime/orchestration/worker_trajectory_report_consumer.py`
- `src/runtime/orchestration/__init__.py`
- `tests/test_runtime_orchestration.py`
- this planning gate and compact status docs.

## Acceptance

- A worker report with `trajectory_update` can be projected into a draft
  envelope without mutating Local Work Trajectory.
- Completed and blocked/partial worker reports produce readable summaries,
  reasons, next hints, and status fields.
- Typed refs expose report, contract, lane, task, changed artifacts, evidence
  refs, verification summaries, and the worker trajectory reporting procedure.
- The envelope does not copy raw `artifact_payloads.content` or arbitrary
  secret-bearing payload body.
- The envelope makes leader-owned consumption authority explicit.
- Focused tests pass.

## Validation Plan

- Run focused runtime orchestration tests for the new projection helper and
  adjacent worker trajectory report consumer behavior.
- Run `python -m compileall` on touched Python files.
- Run `python -m src validate`.
- Run `git diff --check`.

## Implementation Outputs

- Added `WorkerReportReadbackEnvelope` in
  `src/runtime/orchestration/worker_trajectory_report_consumer.py`.
- Added `worker_report_to_readback_envelope()` as a read-only projection from
  existing Subagent Report mappings.
- The projection derives normalized summary, reason, next hint, typed refs,
  related record ids, and worker-report-specific authority/readback fields for
  report id, contract id, lane id, task id, event status, suggested action,
  changed artifact count, verification count, unresolved item count, and
  artifact payload count.
- The projection makes the authority split explicit: worker reports suggest
  Local Work updates, while leader/main/supervisor owns trajectory mutation.
- The projection exposes artifact payload path/operation/content-type clues
  but intentionally omits `artifact_payloads.content` and does not copy raw
  secret-bearing payload body.
- Exported the new readback model and helper from
  `src/runtime/orchestration`.
- Added focused tests covering trajectory update suggestions, blocked/no-op
  reports, artifact payload content omission, and non-mutation of Local Work
  Trajectory.

The implementation intentionally keeps the Subagent Report schema,
`consume_worker_trajectory_report()` behavior, Local Work mutation authority,
provider execution, scheduler state, and ExchangeArtifact storage unchanged.

## Validation Results

- `python -m pytest tests/test_runtime_orchestration.py -k "worker_report_readback_envelope or worker_trajectory_report_consumer" -q`
  - Result: `7 passed, 482 deselected`
- `python -m compileall -q src/runtime/orchestration/worker_trajectory_report_consumer.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py`
  - Result: passed
- `python -m src validate`
  - Result: passed while this gate was active; `state_source=checklist`

## Close Criteria

Close this gate when the read-only projection is implemented, tested, and this
document records final validation evidence.

Closed on 2026-07-09.
