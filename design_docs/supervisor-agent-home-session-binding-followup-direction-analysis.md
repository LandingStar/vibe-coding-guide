# Supervisor Agent Home Session Binding Follow-Up Direction Analysis

> Date: 2026-06-21
> Status: PROPOSED

## Trigger

`design_docs/stages/planning-gate/2026-06-21-supervisor-agent-home-session-binding.md`
closed with a readback-only product binding supervisor run identity to
context-session, home-registration, and scratch-space facts.

Review evidence:

- `review/supervisor-agent-home-session-binding-2026-06-21.md`

## Current Position

The backend scheduler/orchestration line now has:

1. deterministic supervisor dogfood workflow;
2. stable supervisor host/session/run identity;
3. existing agent storage governance products;
4. a binding product that derives storage/context facts from scheduler snapshot
   readback.

The binding is intentionally not durable yet. It is a product object and a
workflow bridge, not a persisted evidence artifact, exchange artifact, MCP
surface, or Host UX surface.

## Candidate A - Durable Supervisor Storage Binding Evidence

### Goal

Persist the binding product as explicit durable evidence with summary readback.

### Why Useful

Host UX, MCP resources, and later audits should not have to reconstruct storage
binding facts from raw workflow results or scheduler snapshots. A durable
evidence product gives them a stable readback surface while preserving the
current no-directory-creation and no-cleanup boundary.

### Boundary

Write evidence only when explicitly requested by a helper/surface. Do not create
agent home directories, scratch directories, cleanup actions, or Host UX.

## Candidate B - Exchange Artifact Projection For Binding Products

### Goal

Represent the binding product as an `ExchangeArtifact` so it can participate in
artifact-centered coordination.

### Why Useful

The agent coordination design expects scheduler-readable intermediate products.
An exchange artifact would let downstream agents consume the exact binding
version. However, it is slightly broader than evidence readback because it
touches artifact lifecycle and possibly admission/inspection behavior.

### Boundary

Do not mark artifacts consumed or use the binding to schedule work in the first
slice.

## Candidate C - Host UX Readback For Binding Products

### Goal

Show supervisor storage/context binding facts in the operator UI.

### Why Useful

Operators need to see which supervisor run owns which context/storage facts, but
UI should consume a stable durable readback product rather than compute facts
from raw workflow internals.

### Boundary

Requires screenshot validation and should remain presentation-only.

## Recommendation

My current preference is Candidate A:

```text
Durable Supervisor Storage Binding Evidence
```

Reason:

1. the binding product exists and is tested;
2. durable evidence gives future UI and MCP resources a stable readback target;
3. it preserves backend-first sequencing;
4. it avoids broadening the next slice into ExchangeArtifact lifecycle or Host
   UX concerns.

## Proposed Next Planning Gate

`design_docs/stages/planning-gate/2026-06-21-supervisor-storage-binding-evidence.md`

Suggested first slice:

1. define a small durable evidence schema for supervisor storage binding;
2. add build/write/read-summary helpers;
3. optionally enrich supervisor dogfood workflow helper with explicit evidence
   write opt-in;
4. add focused tests over persistence, summary readback, and non-goals;
5. preserve no CLI/MCP/Host UX, no directory creation, no cleanup, no scheduler
   projection refresh, and no Local Work Trajectory mutation from runtime code.
