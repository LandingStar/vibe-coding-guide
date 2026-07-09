# Readback Inspection Follow-up Direction Analysis

## Document Position

This direction analysis follows the completed
`Readback Inspection CLI/MCP Surface` gate:

- `design_docs/stages/planning-gate/2026-07-09-readback-inspection-cli-mcp-surface.md`

It chooses the next narrow direction after the platform gained draft readback
envelopes for the current high-value log-like families and a unified read-only
inspection entrypoint.

Date: 2026-07-09

## Current Facts

Completed coverage now includes:

- scheduler event readback envelopes;
- runtime invocation readback envelopes;
- ExchangeArtifact communication readback envelopes;
- worker report / trajectory suggestion readback envelopes;
- validation / doctor / self-check receipt readback envelopes;
- UI screenshot / host evidence readback envelopes;
- unified runtime / CLI / MCP readback inspection surface.

The unified first slice supports:

- `worker-report`
- `validation-receipt`
- `runtime-invocation-log`
- `scheduler-event-log`
- `exchange-artifact`
- `host-evidence`

The completed surface is intentionally read-only. It does not consume worker
reports, run validation/doctor, execute providers, launch browsers, capture
screenshots, mutate scheduler/exchange/evidence/config state, or mutate Local
Work Trajectory.

## Source Documents

- `design_docs/Project Master Checklist.md`
- `design_docs/Global Phase Map and Current Position.md`
- `design_docs/direction-candidates-after-phase-35.md`
- `design_docs/tooling/Log-like Record Standard Draft.md`
- `design_docs/tooling/Log-like Record Family Gap Inventory.md`
- `docs/runtime-log-decoration-contract.md`
- `review/research-compass.md`

## Problem Now

The platform can inspect each supported family through a common readback
surface, but it still cannot answer one common audit question in a single
operator product:

```text
What happened across this task/run/worker/lane, in order, and where should I
look next?
```

Today, the operator or model must still know which family to inspect first,
then manually correlate scheduler event ids, runtime invocation ids, exchange
artifact ids, worker reports, validation receipts, and host evidence paths.

This is a smaller problem than "build a full log index" and larger than "add
one more family envelope." The useful next step is a bounded cross-family
readback product.

## Candidate A: Readback Batch / Timeline Projection

### Goal

Add a read-only batch inspection helper that accepts several explicit sources
or selectors, calls the existing family-specific readback projections, and
returns a normalized timeline of readback envelopes ordered by timestamp with
compact grouping hints.

### Shape

Possible runtime surface:

```text
ReadbackTimelineInspectionRequest
ReadbackTimelineInspectionResult
inspect_readback_timeline()
```

Possible CLI/MCP surface:

```text
doc-based-coding readback timeline ...
readbackTimelineInspect
```

First slice should accept explicit paths / artifact ids only. It should not
scan the whole workspace or introduce a persistent `.dbc` index yet.

### Why This Is Valuable

- It directly builds on the completed `readbackInspect` surface.
- It answers the next practical audit question: "what happened in order?"
- It helps future monitoring UI and agent self-review without requiring a
  storage migration.
- It is compatible with the draft log-like record standard because envelopes
  already expose `timestamp`, `record_kind`, `status`, refs, related ids, and
  `next_hint`.

### Risks

- Timeline ordering can overpromise causality when timestamps are missing,
  coarse, or sourced from different clocks.
- A batch reader can become a hidden workspace scanner if not scoped tightly.
- It may expose gaps in `run_id` / `correlation_id` consistency across
  families.

### Narrow Acceptance

- Read explicit user-provided sources only.
- Return each envelope unchanged plus a compact timeline row projection.
- Include ordering confidence:
  `timestamp`, `source_order`, or `unknown_timestamp`.
- Include grouping hints but do not require global correlation correctness.
- Keep authority split read-only.
- Add focused tests for a mixed scheduler/runtime/exchange/worker sequence.

## Candidate B: Readback Source Index / Manifest

### Goal

Introduce a generated `.dbc` artifact/log manifest so readback tools can
discover known source records without hardcoded path scans.

### Why This Is Valuable

- The Checklist already carries a later todo for a unified `.dbc` artifact/log
  index or manifest layer.
- Many generated runtime products now live under `.dbc`, and discovery is
  becoming more important.
- A manifest would support monitoring UI and future batch readback.

### Risks

- It is broader than the current readback work because it changes how generated
  products are registered and discovered.
- It likely touches scheduler, orchestration, progress graph, host evidence,
  and validation product writers.
- If done too early, it can fossilize paths before the `.dbc` artifact-root
  behavior is fully stable.

### Fit

This is likely a good follow-up after a small explicit-source timeline proves
what fields the manifest actually needs.

## Candidate C: Promote Log-like Record Standard From Draft To Docs Contract

### Goal

Promote stable pieces of
`design_docs/tooling/Log-like Record Standard Draft.md` into an authoritative
`docs/` contract.

### Why This Is Valuable

- Several implementation slices have now used the draft successfully.
- The base envelope and reference contract are no longer purely theoretical.
- A formal docs contract would guide future log families and prevent drift.

### Risks

- If promoted before timeline/readback batch practice, the contract may miss
  cross-family ordering and grouping requirements.
- It is mostly documentation and governance; it does not immediately improve
  operator capability.

### Fit

Promote after at least one cross-family readback product tests the base
envelope in practice.

## Candidate D: Monitoring UI Readback Consumption

### Goal

Bind the new readback envelopes / unified inspection output into the monitoring
UI so operators can inspect scheduler/runtime/communication/evidence records
without using CLI/MCP directly.

### Why This Is Valuable

- `review/research-compass.md` emphasizes tracing, audit, and readable
  multi-agent state as recurring concerns across LangGraph, OpenAI Agents SDK,
  OPA, and related systems.
- The current backend readback products are UI-friendly enough to start a
  compact table/detail view.

### Risks

- It is a frontend slice and would need screenshot-style verification.
- UI design is more likely to churn if the backend does not yet provide a
  timeline/batch product.

### Fit

Better after Candidate A, unless the immediate user need is visual monitoring
instead of backend audit capability.

## Recommendation

Default next gate:

```text
Readback Batch / Timeline Projection
```

Recommended first slice:

- runtime helper only, or runtime + CLI if the helper stays small;
- no MCP in the first cut unless CLI parity is already trivial;
- no persistent manifest/index;
- no workspace scanning;
- no storage migration;
- explicit source list input only.

Reason:

The completed work has solved per-family readability. The next bottleneck is
cross-family audit composition. A narrow explicit-source timeline gives real
practice for ordering, grouping, and source provenance without prematurely
committing to a global index or UI shape.

## Proposed Planning Gate Title

```text
Readback Explicit-Source Timeline Projection
```

## Proposed Gate Scope

In scope:

- add a read-only runtime helper that accepts explicit `ReadbackInspectionRequest`
  entries or equivalent source specs;
- call existing `inspect_readback()` for each source;
- flatten envelopes into timeline rows;
- sort rows by timestamp when present, otherwise preserve source order with
  explicit low ordering confidence;
- report source errors without failing the whole batch unless all sources fail;
- include authority split inherited from the source readbacks.

Out of scope:

- persistent `.dbc` index / manifest;
- workspace-wide discovery scans;
- monitoring UI;
- MCP exposure unless it is a very thin route over the CLI/runtime helper;
- changing readback envelope schemas;
- changing source log persistence;
- provider, browser, validation, doctor, scheduler, ExchangeArtifact, or Local
  Work mutation.

## Suggested Validation

- mixed timeline test with scheduler event log + runtime invocation log +
  ExchangeArtifact + worker report;
- missing timestamp ordering-confidence test;
- partial failure test where one source is invalid and another succeeds;
- authority split test confirming read-only behavior;
- CLI help test if CLI is included.
