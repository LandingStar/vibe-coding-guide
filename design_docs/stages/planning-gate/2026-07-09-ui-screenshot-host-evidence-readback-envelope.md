# UI Screenshot / Host Evidence Readback Envelope

## Document Position

This planning gate records the narrow readback-envelope alignment slice for UI
screenshot clues and host/sandbox evidence products.

Date: 2026-07-09

Source direction:

- `design_docs/validation-readback-followup-direction-analysis.md`
- `design_docs/tooling/Log-like Record Standard Draft.md`
- `design_docs/tooling/Log-like Record Family Gap Inventory.md`

## Goal

Add a read-only draft envelope projection for existing host evidence and
screenshot-style evidence clues so audit tools can inspect them with the same
base record vocabulary used by scheduler, runtime invocation, ExchangeArtifact,
worker report, and validation readbacks.

## Scope

In scope:

- Project existing host evidence summary or presentation-card payloads into a
  `host-evidence-readback-envelope.v1` record.
- Surface evidence product type, evidence path, host surface, provider clues,
  stop reason/detail, status/severity, run/output/review counts, screenshot
  paths, viewport metadata, visual validation summary, typed refs, and next
  hints.
- Project isolated host evidence read errors into the same readback family.
- Keep screenshots as path refs only.

Out of scope:

- Running browsers or Playwright.
- Capturing or generating new screenshots.
- Reading or embedding raw image bytes.
- Executing runtime providers.
- Cleaning sandboxes.
- Mutating scheduler, exchange, evidence, or Local Work Trajectory state.
- Creating a new persistent screenshot evidence schema.
- Exposing the unified CLI/MCP inspection surface; that follows as a separate
  gate.

## Implementation

Code:

- `src/runtime/orchestration/host_evidence_readback.py`
- `src/runtime/orchestration/__init__.py`

Tests:

- `tests/test_runtime_orchestration.py`

New public helpers:

- `HostEvidenceReadbackEnvelope`
- `HostEvidenceErrorReadbackEnvelope`
- `host_evidence_card_to_readback_envelope()`
- `host_evidence_summary_to_readback_envelope()`
- `host_evidence_error_to_readback_envelope()`
- `host_evidence_presentation_to_readback_envelopes()`

## Boundary Notes

The repository currently has durable host evidence JSON products and many
screenshot artifact paths under review/planning evidence, but not a dedicated
runtime screenshot evidence JSON schema. This slice therefore recognizes
screenshot paths and viewport/visual metadata when present, while keeping the
authoritative source as host evidence summary or presentation payloads.

The readback envelope explicitly declares:

- `browser_executed=false`
- `screenshot_captured=false`
- `raw_screenshot_bytes_persisted_inline=false`
- `provider_executed=false`
- `sandbox_cleanup_executed=false`
- no scheduler/exchange/Local Work mutation

## Validation

Focused validation:

```text
python -m pytest tests/test_runtime_orchestration.py -k "host_evidence_readback_envelope or host_evidence_card_readback or host_evidence_summary_readback or host_evidence_presentation_readback" -q
```

Result:

```text
3 passed, 492 deselected
```

Compile validation:

```text
python -m compileall -q src/runtime/orchestration/host_evidence_readback.py src/runtime/orchestration/__init__.py tests/test_runtime_orchestration.py
```

Result: passed.

## Next Gate

`Readback Inspection CLI/MCP Surface`

The next gate should expose already implemented readback projections through a
single read-only operator entrypoint. It should not consume reports, run
providers, mutate trajectory, mutate scheduler/exchange state, or change source
schemas.
