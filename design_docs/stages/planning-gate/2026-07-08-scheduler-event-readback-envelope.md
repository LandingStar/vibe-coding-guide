# Scheduler Event Readback Envelope

## Document Position

This planning gate scopes one narrow alignment slice for log-like record
readability.

Authoritative inputs:

- `design_docs/tooling/Log-like Record Standard Draft.md`
- `design_docs/tooling/Log-like Record Family Gap Inventory.md`
- `docs/runtime-log-decoration-contract.md`

Date: 2026-07-08
Status: Completed

## Problem

`SchedulerEvent` is strong as replay/audit material, but weak as a standalone
human-readable log-like record. Many events expose task ids, state changes,
dependency ids, artifact ids, lease ids, sequence, and metadata, but a reviewer
still has to infer:

- what happened in one sentence;
- whether the event mutates scheduler replay or is audit-only;
- which refs are subjects, inputs, outputs, or evidence;
- where to inspect next.

## This Slice Does

- Add a read-only projection from `SchedulerEvent` into a draft log-like record
  envelope.
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
  - scheduler-specific `replay_effect`
- Add focused tests covering ready, waiting, blocked/failed, running,
  completed, and audit-only scheduler events.
- Keep the projection suitable for CLI/monitoring UI readback.

## This Slice Does Not Do

- Does not change scheduler replay semantics.
- Does not change JSONL persistence for existing or new scheduler events.
- Does not migrate historical scheduler logs.
- Does not add raw transcript persistence.
- Does not align all other log families.
- Does not make `run_id` mandatory for historical records.

## Implementation Targets

Likely touched files:

- `src/runtime/orchestration/scheduler_store.py` or a small adjacent readback
  helper if cleaner.
- `src/runtime/orchestration/__init__.py`
- `tests/test_runtime_orchestration.py`
- this planning gate and compact status docs.

## Acceptance

- A scheduler event can be projected into a draft envelope without mutating the
  event log or scheduler state.
- Waiting/blocked/failed/review-like events include a readable reason.
- Routine success events include a useful generated summary even when
  `SchedulerEvent.reason` is empty.
- Typed refs expose task, dependency, artifact, lease, run, and session clues.
- Audit-only scheduler events are explicitly marked with
  `replay_effect=audit_only`.
- Focused tests pass.

## Validation Plan

- Run focused runtime orchestration tests for the new projection helper.
- Run adjacent scheduler/log-decoration tests if touched.
- Run `git diff --check`.

## Implementation Outputs

- Added `LogRecordRef` and `SchedulerEventReadbackEnvelope` as readback-only
  projection models in `src/runtime/orchestration/scheduler_store.py`.
- Added `scheduler_event_to_readback_envelope()` and helpers for normalized
  status, summary, reason, typed refs, related record ids, next hints, and
  `replay_effect`.
- Exported the projection model and helper from `src/runtime/orchestration`.
- Added focused tests covering ready, running, completed, waiting, blocked,
  review-required, failed, audit-only, and lease lifecycle events.

The implementation intentionally keeps scheduler JSONL persistence and replay
semantics unchanged.

## Validation Results

- `python -m pytest tests/test_runtime_orchestration.py -k "scheduler_event_readback_envelope or log_decoration_adapters_project_scheduler_runtime_and_audit_records or replay_scheduler_events"`
  - Result: `12 passed, 470 deselected`
- `python -m compileall -q src/runtime/orchestration/scheduler_store.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py`
  - Result: passed
- `git diff --check`
  - Result: passed; only Windows LF-to-CRLF working-copy warnings were emitted.

## Close Criteria

Close this gate when the read-only projection is implemented, tested, and this
document records final validation evidence.

Closed on 2026-07-08.
