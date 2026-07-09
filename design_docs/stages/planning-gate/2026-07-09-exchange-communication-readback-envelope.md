# ExchangeArtifact Communication History Readback Envelope

## Document Position

This planning gate scopes one narrow alignment slice for log-like record
readability.

Authoritative inputs:

- `design_docs/tooling/Log-like Record Standard Draft.md`
- `design_docs/tooling/Log-like Record Family Gap Inventory.md`
- `design_docs/runtime-invocation-readback-followup-direction-analysis.md`
- `docs/runtime-log-decoration-contract.md`

Date: 2026-07-09
Status: Completed

## Problem

ExchangeArtifact records already carry rich agent communication products:
producer, audience, lifecycle, scope, causality, relation, refs, contracts,
logs, and typed payload parts. Existing mailbox/history/action-candidate read
models are useful, but reviewers still need to jump across several views to
answer:

- who told whom what;
- what action or response is expected;
- which task, lane, run, trajectory, artifact, or provider session is involved;
- where to inspect next;
- whether the content is sensitive and must remain redacted.

## This Slice Does

- Add a read-only projection from exact-version `ArtifactVersionRecord` /
  `ExchangeArtifact` into the draft log-like readback envelope.
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
- Add communication-specific readback fields for artifact kind, intent,
  lifecycle state, producer, audience, part types, relation kinds, and action
  expectation.
- Keep the projection suitable for monitoring UI, leader/worker history review,
  and future mailbox/action-candidate readbacks.

## This Slice Does Not Do

- Does not mutate ExchangeArtifact lifecycle state.
- Does not consume action candidates.
- Does not admit scheduler tasks.
- Does not write admission ledger records.
- Does not change ExchangeArtifact storage schema.
- Does not persist raw transcript text.
- Does not expose raw sensitive payload body in the readback envelope.
- Does not align worker reports, validation receipts, screenshot evidence, or
  sandbox evidence families.

## Implementation Targets

Likely touched files:

- `src/runtime/orchestration/agent_exchange_history.py`
- `src/runtime/orchestration/__init__.py`
- `tests/test_runtime_orchestration_agent_communication.py`
- this planning gate and compact status docs.

## Acceptance

- An exact ExchangeArtifact version can be projected into a draft envelope
  without mutating the exchange store.
- Routine message/query records include readable who-to-whom summaries and
  reply/action next hints.
- Reply/causality and relation records expose typed refs and related record ids.
- Review/handoff/blocker/merge/scheduler-submission-like records include useful
  action expectation hints without consuming candidates.
- Sensitive or redaction-required artifacts keep payload body out of the
  envelope and expose redaction state explicitly.
- Focused tests pass.

## Validation Plan

- Run focused agent communication readback tests.
- Run adjacent mailbox/history/action-candidate read-only tests.
- Run `python -m compileall` on touched Python files.
- Run `python -m src validate`.
- Run `git diff --check`.

## Implementation Outputs

- Added `ExchangeCommunicationReadbackEnvelope` in
  `src/runtime/orchestration/agent_exchange_history.py`.
- Added `exchange_artifact_record_to_readback_envelope()` as a read-only
  projection from exact-version `ArtifactVersionRecord`.
- The projection derives normalized summary, reason, run/correlation clues,
  typed subject/input/output/evidence refs, related record ids, next hints,
  sensitivity/redaction state, and communication-specific action expectation
  fields.
- The projection exposes safe structured clues such as artifact id/version,
  producer, audience, scope refs, causality refs, relation refs, contract refs,
  scheduler-submission candidate clues, part types, relation kinds, and compact
  exchange-log summaries.
- The projection intentionally omits raw text payload body, arbitrary
  structured payload values, and sensitive payload content from the envelope.
- Exported the new readback model and helper from
  `src/runtime/orchestration`.
- Added focused tests covering routine query/reply, causality and relation
  refs, scheduler/review/blocker/merge action expectations, redaction state,
  and store non-mutation.

The implementation intentionally keeps ExchangeArtifact storage, lifecycle
transition rules, action-candidate consumers, scheduler admission, and
admission ledger behavior unchanged.

## Validation Results

- `python -m pytest tests/test_runtime_orchestration_agent_communication.py -k "exchange_communication_readback_envelope or agent_exchange_history or agent_exchange_action_candidates" -q`
  - Result: `11 passed, 21 deselected`
- `python -m pytest tests/test_runtime_orchestration_agent_communication.py -q`
  - Result: `32 passed`
- `python -m compileall -q src/runtime/orchestration/agent_exchange_history.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration_agent_communication.py`
  - Result: passed
- `python -m src validate`
  - Result: passed while this gate was active; `state_source=checklist`

## Close Criteria

Close this gate when the read-only projection is implemented, tested, and this
document records final validation evidence.

Closed on 2026-07-09.
