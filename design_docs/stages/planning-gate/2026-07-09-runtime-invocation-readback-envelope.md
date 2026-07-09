# Runtime Invocation Readback Envelope

## Document Position

This planning gate scopes one narrow alignment slice for log-like record
readability.

Authoritative inputs:

- `design_docs/tooling/Log-like Record Standard Draft.md`
- `design_docs/tooling/Log-like Record Family Gap Inventory.md`
- `design_docs/log-like-record-alignment-followup-direction-analysis.md`
- `docs/runtime-log-decoration-contract.md`

Date: 2026-07-09
Status: Completed

## Problem

`RuntimeInvocationRecord` already records provider, task, agent, session, retry,
attempt, and redaction-safety information. It is strong as compact audit
material, but still requires a reviewer to inspect attempt arrays and metadata
keys to answer:

- what runtime operation happened in one sentence;
- whether a failure was retryable or terminal;
- which task, worker, provider session, run, or output artifact is involved;
- where to inspect next without reading raw provider output.

## This Slice Does

- Add a read-only projection from `RuntimeInvocationRecord` into the draft
  log-like readback envelope.
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
- Add runtime-specific readback fields for provider, runtime surface, attempt
  count, retryability, retry exhaustion, final error kind, and stdout/stderr
  byte totals.
- Keep the projection suitable for CLI, monitoring UI, and audit review.

## This Slice Does Not Do

- Does not change runtime invocation JSONL persistence.
- Does not migrate historical runtime invocation logs.
- Does not change provider execution behavior.
- Does not change retry or compaction semantics.
- Does not persist raw stdout, stderr, provider transcript, command transcript,
  or secret-bearing payloads.
- Does not align ExchangeArtifact, worker report, validation, or screenshot
  record families.

## Implementation Targets

Likely touched files:

- `src/runtime/orchestration/runtime_invocation_audit.py`
- `src/runtime/orchestration/log_readback.py`
- `src/runtime/orchestration/scheduler_store.py`
- `src/runtime/orchestration/__init__.py`
- `tests/test_runtime_orchestration.py`
- this planning gate and compact status docs.

## Acceptance

- A runtime invocation record can be projected into a draft envelope without
  mutating the invocation log.
- Success records include a useful summary even when top-level
  `final_summary` is empty.
- Failed retryable and failed non-retryable records include readable reasons
  and next hints.
- Typed refs expose invocation, task, agent, provider session, run, provider,
  runtime surface, attempts, and safe output artifact clues when available.
- The readback envelope does not copy raw metadata values, raw stdout/stderr,
  or provider transcript text.
- Compacted/readback paths can still project retained records.
- Focused tests pass.

## Validation Plan

- Run focused runtime orchestration tests for the new projection helper.
- Run adjacent runtime invocation inspection/compaction tests.
- Run `python -m compileall` on touched Python files.
- Run `python -m src validate`.
- Run `git diff --check`.

## Implementation Outputs

- Added shared `LogRecordRef` in
  `src/runtime/orchestration/log_readback.py`.
- Reused the shared ref model from scheduler readback while preserving the
  existing public `LogRecordRef` export.
- Added `RuntimeInvocationReadbackEnvelope` and
  `runtime_invocation_record_to_readback_envelope()` in
  `src/runtime/orchestration/runtime_invocation_audit.py`.
- The projection derives normalized summary, reason, retryability,
  retry-exhaustion, next hints, typed refs, related record ids, and stdout /
  stderr byte totals from existing compact invocation records.
- The projection intentionally exposes safe structured clues only; it does not
  copy arbitrary metadata values, raw stdout/stderr, raw provider transcript, or
  secret-bearing content into the envelope.
- Exported the new readback model and helper from
  `src/runtime/orchestration`.
- Added focused tests covering success, retryable failure, non-retryable
  failure, compaction/readback of retained records, and raw metadata redaction
  boundaries.

The implementation intentionally keeps runtime invocation JSONL persistence,
provider execution, retry behavior, and compaction semantics unchanged.

## Validation Results

- `python -m pytest tests/test_runtime_orchestration.py -k "runtime_invocation_readback_envelope or runtime_invocation_log_inspection or runtime_invocation_audit" -q`
  - Result: `9 passed, 477 deselected`
- `python -m pytest tests/test_runtime_orchestration.py -k "runtime_invocation_readback_envelope or scheduler_event_readback_envelope or runtime_invocation_log_inspection" -q`
  - Result: `9 passed, 477 deselected`
- `python -m compileall -q src/runtime/orchestration/runtime_invocation_audit.py src/runtime/orchestration/log_readback.py src/runtime/orchestration/scheduler_store.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py`
  - Result: passed
- `python -m src validate`
  - Result: passed while this gate was active; `state_source=checklist`
- `git diff --check`
  - Result: passed; only Windows LF-to-CRLF working-copy warnings were emitted.

## Close Criteria

Close this gate when the read-only projection is implemented, tested, and this
document records final validation evidence.

Closed on 2026-07-09.
