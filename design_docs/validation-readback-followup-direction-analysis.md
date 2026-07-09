# Validation Readback Follow-up Direction Analysis

## Document Position

This direction analysis follows the completed validation / doctor / self-check
readback slice:

- `design_docs/stages/planning-gate/2026-07-09-validation-doctor-self-check-readback-envelope.md`
- `design_docs/stages/planning-gate/2026-07-09-worker-report-trajectory-suggestion-readback-envelope.md`
- `design_docs/stages/planning-gate/2026-07-09-exchange-communication-readback-envelope.md`
- `design_docs/stages/planning-gate/2026-07-09-runtime-invocation-readback-envelope.md`
- `design_docs/stages/planning-gate/2026-07-08-scheduler-event-readback-envelope.md`
- `design_docs/tooling/Log-like Record Standard Draft.md`

It selects the next narrow log-like record alignment gate. It is not an
implementation gate and does not change runtime behavior by itself.

Date: 2026-07-09

## Current Baseline

The scheduler, runtime invocation, ExchangeArtifact communication, worker
report / trajectory suggestion, and validation/doctor/self-check receipt
families now have read-only draft envelope projections:

- `scheduler_event_to_readback_envelope()`
- `runtime_invocation_record_to_readback_envelope()`
- `exchange_artifact_record_to_readback_envelope()`
- `worker_report_to_readback_envelope()`
- `validation_receipt_to_readback_envelope()`
- shared `LogRecordRef`
- typed subject/input/output/evidence refs
- normalized summary/reason/next-hint fields
- explicit raw payload non-persistence declarations

This covers the core orchestration loop and the health/readiness layer without
changing storage, replay, validation, doctor, or mutation semantics.

## Candidate 1 - UI Screenshot / Host Evidence Readback Envelope

### What It Would Do

Add read-only draft envelope projections for UI screenshot evidence and host /
sandbox evidence products.

Expected fields:

- evidence product id/path/type and producer
- UI surface, screenshot path, viewport, and visual validation summary
- host/sandbox allocation or receipt refs
- pass/warn/fail status where available
- next hints for inspecting screenshot or host evidence bundles
- explicit omission of raw screenshots from inline payloads and no cleanup or
  browser execution

### Why It Is Valuable

The project has a strong rule that UI/image work must be screenshot-verified.
Release confidence and monitoring UI would benefit from the same readback
envelope pattern over existing screenshot/host evidence products.

### Source Basis

- `docs/monitoring-ui-backend-api.md`
- `tools/progress_graph/host_evidence.py`
- `tools/progress_graph/trajectory_artifacts.py`
- existing screenshot evidence paths under `output/playwright/`
- `design_docs/tooling/Log-like Record Standard Draft.md`

### Scope Boundary

This should not launch browsers, run Playwright, mutate host evidence, clean
sandboxes, or create screenshots. It should only project existing evidence.

## Candidate 2 - Readback Inspection CLI/MCP Surface

### What It Would Do

Expose the completed readback projections through one or more CLI/MCP
inspection surfaces.

### Why It Is Valuable

The projection helpers now exist, but operators may need a stable command/tool
to inspect worker reports, runtime logs, validation receipts, or exchange
records without writing custom Python.

### Scope Boundary

This should not consume worker trajectory reports, mutate state, run providers,
or alter source schemas.

## Candidate 3 - Readback Envelope Batch / Index View

### What It Would Do

Add a batch/index layer that can collect several envelope families into a
compact ordered readback stream.

### Why It Is Valuable

Monitoring UI and audit review eventually need cross-family timelines.

### Scope Boundary

This should not build a persistent `.dbc` index yet unless separately scoped;
it should remain a read-only aggregation experiment.

## Recommendation

Default next gate: **UI Screenshot / Host Evidence Readback Envelope**.

Reason:

- It addresses the remaining high-value evidence family called out by the
  gap inventory.
- It supports the project's screenshot-verification rule without running new
  screenshot work.
- It keeps the current contract-first, read-only envelope pattern intact.

If the immediate pressure shifts toward operator usability rather than evidence
coverage, the next gate should instead be a small readback inspection CLI/MCP
surface over the already completed helpers.

## Proposed Next Gate

```text
UI Screenshot / Host Evidence Readback Envelope
```

Acceptance outline:

- Add read-only projections from existing screenshot/host evidence products
  into the draft envelope.
- Cover screenshot path/viewport/surface clues, host/sandbox evidence refs, and
  pass/warn/fail-like summaries where available.
- Preserve the rule that the projection does not run browsers, generate
  screenshots, mutate evidence, clean sandboxes, or expose raw image bytes
  inline.
- Add focused tests over fixture evidence products.
