# Validation / Doctor / Self-check Receipt Readback Envelope

## Document Position

This planning gate scopes one narrow alignment slice for log-like record
readability.

Authoritative inputs:

- `design_docs/tooling/Log-like Record Standard Draft.md`
- `design_docs/tooling/Log-like Record Family Gap Inventory.md`
- `design_docs/worker-report-readback-followup-direction-analysis.md`
- `docs/self-check-doctor-contract.md`
- `src/runtime/orchestration/self_check.py`
- `src/workflow/pipeline.py`

Date: 2026-07-09
Status: Completed

## Problem

`validate`, `check`, and `doctor` already produce structured results, but their
operator-facing details are spread across constraint status, profile checks,
counts, remediation, authority split, and evidence payloads. Release,
installation, MCP exposure, workspace relay, and scheduler health reviews need
a compact readback answer for:

- what validation/doctor receipt was produced;
- which profile/check/workspace it applies to;
- whether the outcome is ok, warning, failed, skipped, blocked, or passed;
- which remediation should be inspected next;
- which evidence fields are safe refs instead of raw secret-bearing values;
- whether the receipt was read-only and avoided provider/config mutation.

## This Slice Does

- Add a read-only projection from existing validation/doctor/self-check result
  mappings into the draft log-like readback envelope.
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
- Add validation-specific readback fields for source kind, profile/check id,
  governance/overall status, blocking flag, count summaries, remediation count,
  and authority flags.
- Keep the projection suitable for CLI, monitoring UI, and audit review.

## This Slice Does Not Do

- Does not change validation rules or project constraints.
- Does not change doctor profiles or self-check registration.
- Does not change CLI/MCP output schemas, exit codes, or commands.
- Does not run providers, start MCP servers, or call MCP tools.
- Does not mutate workspace config, host config, scheduler state, exchange
  state, or Local Work Trajectory.
- Does not expose raw environment values, raw transcripts, raw stdout/stderr,
  or secret-bearing evidence payload bodies.
- Does not align UI screenshot evidence or sandbox/host evidence families.

## Implementation Targets

Likely touched files:

- `src/runtime/orchestration/validation_readback.py`
- `src/runtime/orchestration/__init__.py`
- `tests/test_runtime_orchestration.py`
- this planning gate and compact status docs.

## Acceptance

- A doctor `SelfCheckReport` mapping can be projected into a draft envelope
  without rerunning checks or mutating state.
- A single doctor `SelfCheckResult` mapping can be projected into a draft
  envelope with check/profile/remediation refs.
- A validate/check `ConstraintResult.to_dict()` mapping can be projected into a
  draft envelope with governance, blocking, constraint, and state-source refs.
- Warnings, failures, skipped checks, and passed validation outcomes produce
  useful reasons and next hints.
- The projection does not copy raw evidence values that may contain secrets;
  it exposes evidence keys and safe structural clues only.
- Focused tests pass.

## Validation Plan

- Run focused runtime orchestration tests for validation receipt readback.
- Run adjacent self-check and worker report readback tests.
- Run `python -m compileall` on touched Python files.
- Run `python -m src validate`.
- Run `git diff --check`.

## Implementation Outputs

- Added `ValidationReceiptReadbackEnvelope` in
  `src/runtime/orchestration/validation_readback.py`.
- Added `validation_receipt_to_readback_envelope()` as a read-only projection
  for existing validation/doctor/self-check result mappings.
- The projection supports:
  - doctor `SelfCheckReport` mappings;
  - single doctor `SelfCheckResult` mappings;
  - validate/check `ConstraintResult.to_dict()` mappings.
- The projection derives normalized summary, reason, next hint, typed refs,
  related record ids, count summaries, remediation count, evidence key count,
  and authority flags.
- The projection exposes evidence keys and structural clues only; it does not
  copy evidence values that may contain environment values, tokens, raw command
  output, or raw transcript material.
- Exported the new readback model and helper from
  `src/runtime/orchestration`.
- Added focused tests covering doctor report, single self-check result, and
  constraint result projections.

The implementation intentionally keeps validation constraints, doctor profiles,
doctor check registration, CLI/MCP output schemas, exit codes, provider
execution, host configuration, scheduler state, exchange state, and Local Work
Trajectory behavior unchanged.

## Validation Results

- `python -m pytest tests/test_runtime_orchestration.py -k "validation_receipt_readback_envelope or self_check_registry or run_self_check_doctor_codex_profile" -q`
  - Result: `6 passed, 486 deselected`
- `python -m pytest tests/test_runtime_orchestration.py -k "validation_receipt_readback_envelope or worker_report_readback_envelope or worker_trajectory_report_consumer or self_check_registry" -q`
  - Result: `12 passed, 480 deselected`
- `python -m compileall -q src/runtime/orchestration/validation_readback.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py`
  - Result: passed

## Close Criteria

Close this gate when the read-only projection is implemented, tested, and this
document records final validation evidence.

Closed on 2026-07-09.
