# Readback Timeline Follow-up Direction Analysis

## Document Position

This direction analysis follows the completed planning gate:

- `design_docs/stages/planning-gate/2026-07-09-readback-explicit-source-timeline-projection.md`

Date: 2026-07-09

## Current Facts

The platform now has:

- per-family readback envelopes for scheduler events, runtime invocations,
  ExchangeArtifact communication, worker reports, validation receipts, and host
  evidence;
- unified single-source inspection through `inspect_readback()`;
- explicit-source timeline projection through `inspect_readback_timeline()`;
- CLI access through `doc-based-coding readback timeline --source-spec PATH`
  and `--source-json JSON`.

The completed timeline slice is intentionally read-only and explicit-source
only. It does not scan the workspace, write a persistent manifest, expose MCP,
launch UI, run providers, run browsers, run validation/doctor, mutate
scheduler/exchange/evidence/config state, or mutate Local Work Trajectory.

## Source Documents

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/readback-inspection-followup-direction-analysis.md`
- `design_docs/stages/planning-gate/2026-07-09-readback-explicit-source-timeline-projection.md`
- `design_docs/tooling/Log-like Record Standard Draft.md`
- `docs/runtime-log-decoration-contract.md`
- `review/research-compass.md`

## Problem Now

The timeline product answers a practical audit question when the caller already
knows the source files or exact artifact ids. The remaining question is which
surface should consume this product next.

There are two different needs:

- agent-facing use: Codex or another MCP-capable agent should be able to ask for
  the same explicit-source timeline without shelling out through CLI;
- operator-facing use: humans need discovery, saved source sets, and eventually
  a visual monitoring UI.

The first need is narrower. The second need likely requires either a persistent
source manifest or a UI design gate.

## Candidate A: MCP Timeline Parity

### Goal

Expose `inspect_readback_timeline()` through a read-only MCP tool, likely:

```text
readbackTimelineInspect
```

The MCP tool should accept explicit source specs matching the runtime/CLI source
shape and return the same timeline result JSON.

### Why This Is Valuable

- It directly completes parity for the helper just added.
- It lets Codex/agent workflows inspect cross-family audit timelines without
  asking the model to resolve CLI paths or parse command output.
- It is small and does not require source discovery, UI, or storage migration.
- It keeps the same no-mutation authority split.

### Risks

- MCP schema naming can drift from CLI/runtime source fields if not tested.
- It may create pressure to add source auto-discovery too early.

### Narrow Acceptance

- Add MCP route and `GovernanceTools` method only.
- Accept explicit sources only.
- Reuse `ReadbackTimelineInspectionRequest`.
- Return the same `ReadbackTimelineInspectionResult.to_json_dict()` shape.
- Add focused MCP tests for success and missing/invalid source behavior.

## Candidate B: Readback Source Manifest / Index

### Goal

Introduce a generated `.dbc` artifact/log manifest so readback tools can
discover known record sources without hardcoded path lists.

### Why This Is Valuable

- Timeline source selection is currently caller-owned.
- A manifest would make future operator UI and agent audit flows easier.
- It aligns with the existing later todo for a unified `.dbc` artifact/log
  index.

### Risks

- It changes generated runtime product registration and discovery behavior.
- It may touch scheduler, runtime, exchange, evidence, validation, and progress
  graph product writers.
- If done before more timeline practice, it may freeze the wrong metadata.

### Fit

Good after MCP parity or after one more explicit-source dogfood shows the
minimum manifest fields.

## Candidate C: Monitoring UI Readback Consumption

### Goal

Bind readback inspection and timeline output into the monitoring UI as a
record table/detail view.

### Why This Is Valuable

- It turns the audit product into something human operators can inspect
  quickly.
- It can reveal readability gaps in row fields, grouping, and source labels.

### Risks

- It is frontend work and requires screenshot-style validation.
- Without a manifest/source-set story, the UI still needs explicit source input
  or fixture-backed data.

### Fit

Useful after MCP parity if the next priority is visual monitoring, or after the
manifest if discovery is more important.

## Candidate D: Promote Log-like Record Standard

### Goal

Promote stable parts of
`design_docs/tooling/Log-like Record Standard Draft.md` into an authoritative
`docs/` contract.

### Why This Is Valuable

- The base envelope has now supported multiple readback families and one
  cross-family timeline product.
- A formal docs contract would reduce drift for future log-like products.

### Risks

- It is governance/documentation-heavy.
- If promoted before manifest/UI practice, it may miss discovery and display
  requirements.

### Fit

Good after MCP parity, and especially after deciding whether timeline source
sets require stable manifest fields.

## Recommendation

Default next gate:

```text
Readback Timeline MCP Parity
```

Reason:

The runtime helper and CLI are complete, but Codex-facing MCP parity is still
missing. This is the smallest next step that improves real agent usability
without prematurely expanding into manifest/index design or monitoring UI.

## Proposed Gate Scope

In scope:

- add `GovernanceTools.readback_timeline_inspect()` or equivalent;
- add MCP schema/routing for `readbackTimelineInspect`;
- accept explicit source specs only;
- reuse `inspect_readback_timeline()`;
- return the runtime result JSON unchanged except for MCP wrapper metadata, if
  existing MCP conventions require it;
- test success, partial failure, and schema/routing behavior.

Out of scope:

- persistent source manifest/index;
- workspace scanning;
- monitoring UI;
- source schema migration;
- changing timeline row shape unless MCP tests reveal a clear bug;
- provider/browser/validation/doctor/scheduler/exchange/evidence/config/Local
  Work mutation.
